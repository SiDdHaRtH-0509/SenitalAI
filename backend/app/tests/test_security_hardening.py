"""Security Hardening (Phase 1.1) Test Suite.

Verifies:
1. Sensitive Read Endpoints Protection:
   - GET /api/events requires authentication (401 without token)
   - GET /api/events/{id} requires authentication (401 without token)
   - GET /api/stats requires authentication (401 without token)
   - GET /api/cameras requires authentication (401 without token)
   - GET /api/zones requires authentication (401 without token)
2. Public Health Check Preservation:
   - GET /api/health remains publicly accessible (200 OK without token)
3. Cookie-Based Authentication:
   - Login sets HttpOnly, SameSite=Lax cookie
   - Requests with sentinel_token cookie are authenticated
   - Logout clears the session cookie
4. Audit Trail Integrity & Immutability:
   - Dedicated audit records created for logins, failures, event reviews, camera/zone registrations
   - Audit log query endpoint strictly restricted to ADMIN
   - Verification that no API endpoint exists to update or delete audit records
5. Production Environment Secret Validation:
   - Settings validation raises RuntimeError if default secrets are used in production
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.core.security import ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE, create_access_token
from app.models.audit import AuditLog


def test_public_health_check_preserved(unauth_client: TestClient):
    """Verify GET /api/health remains 100% public without credentials."""
    resp = unauth_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_sensitive_read_endpoints_require_authentication(unauth_client: TestClient):
    """Verify sensitive surveillance endpoints reject unauthenticated access with 401."""
    endpoints = [
        "/api/events",
        "/api/events/evt-demo-0001",
        "/api/stats",
        "/api/cameras",
        "/api/zones",
    ]
    for ep in endpoints:
        resp = unauth_client.get(ep)
        assert resp.status_code == 401, f"Expected 401 on {ep}, got {resp.status_code}"
        assert "detail" in resp.json()


def test_authenticated_operator_can_access_read_endpoints(operator_client: TestClient):
    """Verify authenticated OPERATOR can access sensitive surveillance read endpoints."""
    endpoints = [
        "/api/events",
        "/api/stats",
        "/api/cameras",
        "/api/zones",
    ]
    for ep in endpoints:
        resp = operator_client.get(ep)
        assert resp.status_code == 200, f"Expected 200 on {ep}, got {resp.status_code}"


def test_login_sets_httponly_cookie(unauth_client: TestClient):
    """Verify POST /api/auth/login sets an HttpOnly session cookie."""
    resp = unauth_client.post(
        "/api/auth/login",
        json={"username": "operator", "password": settings.OPERATOR_DEFAULT_PASSWORD},
    )
    assert resp.status_code == 200
    assert "sentinel_token" in resp.cookies
    # Inspect Set-Cookie header attributes
    set_cookie_hdr = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_hdr or "httponly" in set_cookie_hdr
    assert "samesite=lax" in set_cookie_hdr.lower()


def test_cookie_based_authentication(unauth_client: TestClient):
    """Verify protected endpoints accept authentication via sentinel_token cookie."""
    # Obtain token and CSRF token
    login_resp = unauth_client.post(
        "/api/auth/login",
        json={"username": "operator", "password": settings.OPERATOR_DEFAULT_PASSWORD},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    token = data["access_token"]
    csrf_token = data.get("csrf_token")
    assert csrf_token is not None

    # Request without Authorization header, but with cookie
    unauth_client.cookies.set("sentinel_token", token)
    unauth_client.cookies.set("sentinel_csrf_token", csrf_token)
    resp = unauth_client.get("/api/events")
    assert resp.status_code == 200

    # Logout with X-CSRF-Token header clears cookie
    logout_resp = unauth_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})
    assert logout_resp.status_code == 200
    # Cookie should be cleared (empty or expired)
    assert unauth_client.cookies.get("sentinel_token") is None or logout_resp.headers.get("set-cookie")


def test_csrf_protection_rejects_missing_or_invalid_header(unauth_client: TestClient, service_client: TestClient):
    """Verify state-changing requests authenticated via cookies require valid X-CSRF-Token header."""
    # 1. Create an event to patch
    event_id = "evt-csrf-test-99"
    service_client.post(
        "/api/events",
        json={
            "event_id": event_id,
            "camera_id": "cam-north-01",
            "timestamp": "2026-10-17T18:00:00Z",
            "severity": "HIGH",
            "confidence": 0.88,
        },
    )

    # 2. Login via cookie
    login_resp = unauth_client.post(
        "/api/auth/login",
        json={"username": "operator", "password": settings.OPERATOR_DEFAULT_PASSWORD},
    )
    assert login_resp.status_code == 200
    csrf_token = login_resp.json()["csrf_token"]

    # 3. State-changing PATCH with cookie auth but WITHOUT X-CSRF-Token header -> 403 Forbidden
    r_no_csrf = unauth_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "ACKNOWLEDGED", "notes": "No CSRF header"},
    )
    assert r_no_csrf.status_code == 403
    assert "CSRF validation failed" in r_no_csrf.json()["detail"]

    # 4. State-changing PATCH with INVALID X-CSRF-Token header -> 403 Forbidden
    r_bad_csrf = unauth_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "ACKNOWLEDGED", "notes": "Bad CSRF header"},
        headers={"X-CSRF-Token": "completely_wrong_csrf_token"},
    )
    assert r_bad_csrf.status_code == 403
    assert "CSRF validation failed" in r_bad_csrf.json()["detail"]

    # 5. State-changing PATCH with VALID matching X-CSRF-Token header -> 200 OK
    r_valid_csrf = unauth_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "ACKNOWLEDGED", "notes": "Valid CSRF header"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert r_valid_csrf.status_code == 200
    assert r_valid_csrf.json()["status"] == "ACKNOWLEDGED"


def test_bearer_token_and_api_key_exempt_from_csrf(operator_client: TestClient, service_client: TestClient):
    """Verify Bearer token and X-API-Key clients (M2M) are exempt from browser CSRF checks."""
    event_id = "evt-bearer-exempt-01"
    # Service client uses Authorization: Bearer <service_token>
    resp = service_client.post(
        "/api/events",
        json={
            "event_id": event_id,
            "camera_id": "cam-north-01",
            "timestamp": "2026-10-17T18:00:00Z",
            "severity": "MEDIUM",
            "confidence": 0.85,
        },
    )
    assert resp.status_code == 201

    # Operator client uses Authorization: Bearer <token>
    patch_resp = operator_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "RESOLVED", "notes": "Reviewed via Bearer token"},
    )
    assert patch_resp.status_code == 200


def test_audit_records_created_on_security_actions(
    unauth_client: TestClient,
    operator_client: TestClient,
    admin_client: TestClient,
    service_client: TestClient,
    test_db_session: Session,
):
    """Verify separate audit records are written on login, failures, and event reviews."""
    initial_audit_count = test_db_session.query(AuditLog).count()

    # 1. Failed login creates audit log
    fail_resp = unauth_client.post(
        "/api/auth/login",
        json={"username": "intruder", "password": "WrongPassword!"},
    )
    assert fail_resp.status_code == 401

    failed_logs = test_db_session.query(AuditLog).filter(AuditLog.action == "USER_LOGIN_FAILED").all()
    assert len(failed_logs) >= 1
    latest_fail = failed_logs[-1]
    assert latest_fail.actor_username == "intruder"
    assert latest_fail.outcome == "FAILURE"

    # 2. Ingest an event via service client
    event_id = "evt-audit-test-101"
    ingest_resp = service_client.post(
        "/api/events",
        json={
            "event_id": event_id,
            "camera_id": "cam-north-01",
            "timestamp": "2026-10-17T18:00:00Z",
            "severity": "CRITICAL",
            "confidence": 0.95,
        },
    )
    assert ingest_resp.status_code == 201

    ingest_logs = test_db_session.query(AuditLog).filter(
        AuditLog.action == "EVENT_INGESTED",
        AuditLog.target_id == event_id,
    ).all()
    assert len(ingest_logs) >= 1
    assert ingest_logs[-1].outcome == "SUCCESS"

    # 3. Update status via operator client
    patch_resp = operator_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "RESOLVED", "notes": "Audited review by patrol officer"},
    )
    assert patch_resp.status_code == 200

    status_logs = test_db_session.query(AuditLog).filter(
        AuditLog.action == "EVENT_STATUS_UPDATED",
        AuditLog.target_id == event_id,
    ).all()
    assert len(status_logs) >= 1
    latest_status_log = status_logs[-1]
    assert latest_status_log.actor_username == "operator"
    assert latest_status_log.outcome == "SUCCESS"
    assert "RESOLVED" in latest_status_log.details


def test_audit_logs_endpoint_rbac_and_immutability(
    unauth_client: TestClient,
    operator_client: TestClient,
    service_client: TestClient,
    admin_client: TestClient,
):
    """Verify GET /api/audit-logs is restricted to ADMIN and cannot be modified via API."""
    # 1. Unauthenticated -> 401
    assert unauth_client.get("/api/audit-logs").status_code == 401

    # 2. OPERATOR -> 403
    assert operator_client.get("/api/audit-logs").status_code == 403

    # 3. SERVICE -> 403
    assert service_client.get("/api/audit-logs").status_code == 403

    # 4. ADMIN -> 200
    r_admin = admin_client.get("/api/audit-logs")
    assert r_admin.status_code == 200
    logs = r_admin.json()
    assert isinstance(logs, list)

    # 5. Immutability verification: No DELETE or POST or PUT on /api/audit-logs
    r_post = admin_client.post("/api/audit-logs", json={"action": "FORGED"})
    assert r_post.status_code in (404, 405)

    r_delete = admin_client.delete("/api/audit-logs/1")
    assert r_delete.status_code in (404, 405)

    r_put = admin_client.put("/api/audit-logs/1", json={"details": "Tampered"})
    assert r_put.status_code in (404, 405)


def test_production_secret_validation_rejects_insecure_defaults(monkeypatch):
    """Verify Settings raises RuntimeError if running in production with insecure/default secrets."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "sentinel-ai-insecure-dev-secret-change-in-production-2026")
    monkeypatch.setenv("SENTINEL_SERVICE_API_KEY", "sentinel-cv-service-secret-key-2026")

    with pytest.raises(RuntimeError) as exc_info:
        Settings()
    assert "CRITICAL SECURITY VALIDATION FAILURE" in str(exc_info.value)


def test_audit_hash_chain_integrity_verification(test_db_session: Session):
    """Verify cryptographic SHA-256 hash chaining on audit records."""
    from app.services.audit_service import record_audit, verify_audit_trail_integrity

    # Create multiple sequential records
    record_audit(db=test_db_session, action="TEST_ACT_1", target_type="t", actor_username="admin")
    record_audit(db=test_db_session, action="TEST_ACT_2", target_type="t", actor_username="operator")
    record_audit(db=test_db_session, action="TEST_ACT_3", target_type="t", actor_username="cv_service")

    result = verify_audit_trail_integrity(test_db_session)
    assert result["valid"] is True
    assert result["total_records"] >= 3
    assert result["tampered_record_id"] is None


def test_audit_tampering_detection(test_db_session: Session):
    """Verify tampering with an audit record's content is immediately detected."""
    from app.services.audit_service import record_audit, verify_audit_trail_integrity

    entry = record_audit(
        db=test_db_session,
        action="LEGITIMATE_ACTION",
        target_type="user",
        actor_username="operator",
        details="Original untampered details",
    )

    # Verify initial integrity passes
    assert verify_audit_trail_integrity(test_db_session)["valid"] is True

    # Simulate unauthorized direct database tampering
    entry.details = "MALICIOUSLY_ALTERED_CONTENT"
    test_db_session.commit()

    tampered_result = verify_audit_trail_integrity(test_db_session)
    assert tampered_result["valid"] is False
    assert tampered_result["tampered_record_id"] == entry.id
    assert tampered_result["reason"] == "CONTENT_HASH_MISMATCH"


def test_audit_broken_chain_detection(test_db_session: Session):
    """Verify broken hash link in the audit chain is detected."""
    from app.services.audit_service import record_audit, verify_audit_trail_integrity

    r1 = record_audit(db=test_db_session, action="BLOCK_1", target_type="t", actor_username="admin")
    r2 = record_audit(db=test_db_session, action="BLOCK_2", target_type="t", actor_username="admin")

    # Tamper with prev_hash link
    r2.prev_hash = "f" * 64
    test_db_session.commit()

    tampered_result = verify_audit_trail_integrity(test_db_session)
    assert tampered_result["valid"] is False
    assert tampered_result["tampered_record_id"] == r2.id
    assert tampered_result["reason"] == "BROKEN_CHAIN_LINK"


def test_audit_verify_integrity_api_endpoint(
    unauth_client: TestClient,
    operator_client: TestClient,
    admin_client: TestClient,
):
    """Verify GET /api/audit-logs/verify-integrity requires ADMIN and reports chain status."""
    # 1. Unauthenticated -> 401
    assert unauth_client.get("/api/audit-logs/verify-integrity").status_code == 401

    # 2. Operator -> 403
    assert operator_client.get("/api/audit-logs/verify-integrity").status_code == 403

    # 3. Admin -> 200 with valid integrity
    resp = admin_client.get("/api/audit-logs/verify-integrity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert "total_records" in data
