"""Authentication and User management service for SentinelAI."""

from datetime import datetime, timezone
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    ROLE_ADMIN,
    ROLE_OPERATOR,
    ROLE_SERVICE,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserCreate

logger = logging.getLogger("sentinel.auth")


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieve user record by exact username."""
    return db.query(User).filter(User.username == username.strip().lower()).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate credentials against stored password hash.
    
    Returns the User record upon success, or None if authentication fails.
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not user.is_active:
        logger.warning("Authentication attempted for inactive user: %s", username)
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning("Invalid password attempt for user: %s", username)
        return None

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def create_user(db: Session, user_in: UserCreate, is_admin_creation: bool = False) -> User:
    """Register a new user account with secure password hashing.
    
    Enforces least privilege: if not created by an administrator, the role
    is strictly forced to OPERATOR, preventing privilege escalation.
    """
    clean_username = user_in.username.strip().lower()
    existing = get_user_by_username(db, clean_username)
    if existing:
        raise ValueError(f"Username '{clean_username}' is already registered.")

    # Prevent non-admins from self-granting ADMIN or SERVICE roles
    assigned_role = ROLE_OPERATOR
    if is_admin_creation and user_in.role:
        assigned_role = user_in.role.value.upper()

    hashed = hash_password(user_in.password)
    user = User(
        username=clean_username,
        email=user_in.email.strip().lower() if user_in.email else None,
        full_name=user_in.full_name.strip() if user_in.full_name else None,
        hashed_password=hashed,
        role=assigned_role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created user '%s' with role '%s'.", user.username, user.role)
    return user


def seed_default_users(db: Session) -> None:
    """Seed initial administrator, operator, and CV service accounts if missing."""
    seed_specs = [
        (
            "admin",
            settings.ADMIN_DEFAULT_PASSWORD,
            ROLE_ADMIN,
            "System Administrator",
            "admin@sentinel.local",
        ),
        (
            "operator",
            settings.OPERATOR_DEFAULT_PASSWORD,
            ROLE_OPERATOR,
            "Border Surveillance Watch Officer",
            "operator@sentinel.local",
        ),
        (
            "cv_service",
            settings.SERVICE_DEFAULT_PASSWORD,
            ROLE_SERVICE,
            "CV Inference Engine Service Identity",
            "cv_service@sentinel.local",
        ),
    ]

    for username, password, role, full_name, email in seed_specs:
        existing = get_user_by_username(db, username)
        if not existing:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                role=role,
                is_active=True,
            )
            db.add(user)
            db.commit()
            logger.info("Seeded initial user '%s' with role '%s'.", username, role)
        else:
            # Sync password with rotated environment credentials
            existing.hashed_password = hash_password(password)
            existing.role = role
            db.commit()
