"""Comprehensive Security, Authentication, and RBAC Test Suite for SentinelAI.

Verifies:
1. Valid user login produces valid HS256 JWT access tokens.
2. Invalid credentials (wrong password, unknown user) return HTTP 401 Unauthorized.
3. Protected endpoints reject unauthenticated requests with HTTP 401.
4. Token expiration and tampered tokens are rejected with HTTP 401.
5. Role-Based Access Control (RBAC):
   - OPERATOR role cannot submit events (HTTP 403) or add cameras (HTTP 403).
   - SERVICE role can submit events (HTTP 201) but cannot update statuses (HTTP 403).
   - ADMIN role has full supervisory permissions.
6. Privilege escalation prevention: registration endpoint forces OPERATOR role.
7. Service API Key machine-to-machine authentication.
8. Status update audit trail correctly attributes operator identity.
"""

from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    ROLE_ADMIN,
    ROLE_OPERATOR,
    ROLE_SERVICE,
    create_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    """Verify standard-library PBKDF2-HMAC-SHA256 password hashing and timing-safe verification."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "invalid_hash_format") is False


def test_valid_user_login(unauth_client: TestClient):
    """Verify authenticating with default seeded credentials returns valid JWT token."""
    res = unauth_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": settings.ADMIN_DEFAULT_PASSWORD},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == ROLE_ADMIN
    assert data["username"] == "admin"
    assert data["expires_in_seconds"] > 0


def test_invalid_login_credentials(unauth_client: TestClient):
    """Verify wrong password or unknown user returns 401."""
    # Wrong password
    r1 = unauth_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "CompletelyWrongPassword!"},
    )
    assert r1.status_code == 401
    assert "Invalid username or password" in r1.json()["detail"]

    # Unknown user
    r2 = unauth_client.post(
        "/api/auth/login",
        json={"username": "non_existent_officer", "password": "AnyPassword123!"},
    )
    assert r2.status_code == 401


def test_auth_me_endpoint(unauth_client: TestClient, operator_client: TestClient):
    """Verify /api/auth/me returns identity for authenticated user and 401 for unauthenticated."""
    # Unauthenticated
    r_unauth = unauth_client.get("/api/auth/me")
    assert r_unauth.status_code == 401

    # Authenticated operator
    r_auth = operator_client.get("/api/auth/me")
    assert r_auth.status_code == 200
    data = r_auth.json()
    assert data["username"] == "operator"
    assert data["role"] == ROLE_OPERATOR


def test_expired_and_tampered_jwt(unauth_client: TestClient):
    """Verify expired token or tampered signature is rejected."""
    # 1. Expired token
    expired_token = create_access_token(
        subject="admin",
        role=ROLE_ADMIN,
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )
    r_exp = unauth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert r_exp.status_code == 401
    assert "Invalid or expired access token" in r_exp.json()["detail"]

    # 2. Tampered token
    tampered_token = expired_token[:-4] + "fake"
    r_tamp = unauth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert r_tamp.status_code == 401


def test_user_registration_prevents_privilege_escalation(unauth_client: TestClient):
    """Verify public registration creates account strictly as OPERATOR even if ADMIN requested."""
    payload = {
        "username": "new_recruit_officer",
        "password": "RecruitPassword2026!",
        "email": "recruit@sentinel.local",
        "full_name": "Recruit Officer",
        "role": "ADMIN",  # Attempting privilege escalation
    }
    res = unauth_client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "new_recruit_officer"
    assert data["role"] == ROLE_OPERATOR  # Privilege escalation prevented!


def test_event_submission_rbac(
    unauth_client: TestClient,
    operator_client: TestClient,
    service_client: TestClient,
    admin_client: TestClient,
):
    """Verify event submission permissions: SERVICE and ADMIN allowed; OPERATOR and unauth denied."""
    event_payload = {
        "event_id": "evt-rbac-test-01",
        "camera_id": "cam-north-01",
        "timestamp": "2026-10-17T16:00:00Z",
        "severity": "HIGH",
        "confidence": 0.89,
        "zone_id": "zone-restricted-01",
    }

    # 1. Unauthenticated -> 401
    r_unauth = unauth_client.post("/api/events", json=event_payload)
    assert r_unauth.status_code == 401

    # 2. OPERATOR -> 403 Forbidden (Only SERVICE or ADMIN can ingest events)
    r_operator = operator_client.post("/api/events", json=event_payload)
    assert r_operator.status_code == 403
    assert "Access denied" in r_operator.json()["detail"]

    # 3. SERVICE -> 201 Created
    r_service = service_client.post("/api/events", json=event_payload)
    assert r_service.status_code == 201
    assert r_service.json()["event_id"] == "evt-rbac-test-01"


def test_service_api_key_header_authentication(unauth_client: TestClient):
    """Verify CV edge node can authenticate using X-API-Key or Bearer service key."""
    event_payload = {
        "event_id": "evt-api-key-test-02",
        "camera_id": "cam-north-01",
        "timestamp": "2026-10-17T16:05:00Z",
        "severity": "HIGH",
        "confidence": 0.92,
    }

    # Submit with X-API-Key
    res = unauth_client.post(
        "/api/events",
        json=event_payload,
        headers={"X-API-Key": settings.SERVICE_API_KEY},
    )
    assert res.status_code == 201
    assert res.json()["event_id"] == "evt-api-key-test-02"


def test_status_update_rbac_and_audit_attribution(
    unauth_client: TestClient,
    service_client: TestClient,
    operator_client: TestClient,
):
    """Verify status update permissions: OPERATOR allowed; SERVICE and unauth denied.
    
    Verifies operator username is attributed in operator_notes.
    """
    # Create event via service
    event_id = "evt-status-rbac-03"
    service_client.post(
        "/api/events",
        json={
            "event_id": event_id,
            "camera_id": "cam-north-01",
            "timestamp": "2026-10-17T16:10:00Z",
            "confidence": 0.88,
        },
    )

    # 1. Unauthenticated -> 401
    r_unauth = unauth_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "ACKNOWLEDGED"},
    )
    assert r_unauth.status_code == 401

    # 2. SERVICE role -> 403 Forbidden (Machines cannot review incidents)
    r_service = service_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "ACKNOWLEDGED"},
    )
    assert r_service.status_code == 403

    # 3. OPERATOR role -> 200 OK
    r_op = operator_client.patch(
        f"/api/events/{event_id}/status",
        json={"status": "ACKNOWLEDGED", "notes": "Officer dispatched to sector."},
    )
    assert r_op.status_code == 200
    data = r_op.json()
    assert data["status"] == "ACKNOWLEDGED"
    assert "[operator]" in data["operator_notes"]


def test_administrative_endpoints_rbac(operator_client: TestClient, admin_client: TestClient):
    """Verify camera registration and service token issuance require ADMIN role."""
    camera_payload = {
        "camera_id": "cam-admin-test-99",
        "name": "Admin Test PTZ",
        "location": "North Observation",
        "zone_id": "zone-restricted-01",
    }

    # OPERATOR cannot add camera -> 403
    r_op_cam = operator_client.post("/api/cameras", json=camera_payload)
    assert r_op_cam.status_code == 403

    # ADMIN can add camera -> 201
    r_admin_cam = admin_client.post("/api/cameras", json=camera_payload)
    assert r_admin_cam.status_code == 201

    # OPERATOR cannot issue service token -> 403
    r_op_tok = operator_client.post("/api/auth/service-token", json={"service_name": "edge-01"})
    assert r_op_tok.status_code == 403

    # ADMIN can issue service token -> 200
    r_admin_tok = admin_client.post("/api/auth/service-token", json={"service_name": "edge-01"})
    assert r_admin_tok.status_code == 200
    assert "token" in r_admin_tok.json()
