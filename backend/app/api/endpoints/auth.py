"""Authentication and Identity endpoints for SentinelAI."""

from datetime import timedelta
import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.config import settings
from app.core.security import ROLE_ADMIN, ROLE_SERVICE, create_access_token
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    RoleEnum,
    ServiceTokenRequest,
    ServiceTokenResponse,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import authenticate_user, create_user, get_user_by_username
from app.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    summary="User login and token issuance",
)
def login(
    login_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate with username and password.
    
    Sets an HttpOnly, SameSite=Lax cookie for browser session security,
    and returns a signed Bearer JWT token in the JSON body.
    Logs successful and failed attempts to the immutable audit ledger.
    """
    client_ip = request.client.host if request.client else None
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        record_audit(
            db=db,
            action="USER_LOGIN_FAILED",
            target_type="user",
            actor_username=login_data.username,
            outcome="FAILURE",
            details="Invalid credentials provided.",
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.username,
        role=user.role,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"email": user.email, "full_name": user.full_name},
    )

    csrf_token = secrets.token_urlsafe(32)

    # Set HttpOnly, SameSite=Lax cookie for secure browser clients
    response.set_cookie(
        key="sentinel_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Set CSRF cookie for client header double-submit verification
    response.set_cookie(
        key="sentinel_csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    record_audit(
        db=db,
        action="USER_LOGIN_SUCCESS",
        target_type="user",
        actor_username=user.username,
        actor_role=user.role,
        target_id=str(user.id),
        outcome="SUCCESS",
        ip_address=client_ip,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        csrf_token=csrf_token,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new operator account",
)
def register(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new operator user account.
    
    Non-administrator sign-ups are strictly constrained to OPERATOR role,
    preventing self-assignment of administrative privileges.
    """
    client_ip = request.client.host if request.client else None
    try:
        new_user = create_user(db, user_in, is_admin_creation=False)
        record_audit(
            db=db,
            action="USER_REGISTERED",
            target_type="user",
            actor_username=new_user.username,
            actor_role=new_user.role,
            target_id=str(new_user.id),
            outcome="SUCCESS",
            ip_address=client_ip,
        )
        return UserResponse.model_validate(new_user)
    except ValueError as exc:
        record_audit(
            db=db,
            action="USER_REGISTRATION_FAILED",
            target_type="user",
            actor_username=user_in.username,
            outcome="FAILURE",
            details=str(exc),
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve identity and active role permissions of currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/service-token",
    response_model=ServiceTokenResponse,
    summary="Issue dedicated machine-to-machine service token",
)
def generate_service_token(
    token_request: ServiceTokenRequest,
    current_admin: User = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
) -> ServiceTokenResponse:
    """Generate a scoped service token for automated CV edge nodes (Admin only)."""
    valid_hours = max(1, min(token_request.valid_hours, 8760))
    token = create_access_token(
        subject=f"service:{token_request.service_name}",
        role=ROLE_SERVICE,
        expires_delta=timedelta(hours=valid_hours),
        extra_claims={"service_name": token_request.service_name},
    )
    record_audit(
        db=db,
        action="SERVICE_TOKEN_ISSUED",
        target_type="service_token",
        actor_username=current_admin.username,
        actor_role=current_admin.role,
        target_id=token_request.service_name,
        outcome="SUCCESS",
        details=f"Issued token valid for {valid_hours} hours",
    )
    return ServiceTokenResponse(
        token=token,
        token_type="bearer",
        service_name=token_request.service_name,
        role=ROLE_SERVICE,
        expires_in_hours=valid_hours,
    )


@router.post(
    "/logout",
    summary="Operator logout acknowledgment",
)
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Client logout acknowledgment endpoint: clears HttpOnly session and CSRF cookies."""
    response.delete_cookie(key="sentinel_token", path="/")
    response.delete_cookie(key="sentinel_csrf_token", path="/")
    record_audit(
        db=db,
        action="USER_LOGOUT",
        target_type="user",
        actor_username=current_user.username,
        actor_role=current_user.role,
        target_id=str(current_user.id),
        outcome="SUCCESS",
    )
    return {
        "status": "success",
        "message": f"User '{current_user.username}' session terminated.",
    }
