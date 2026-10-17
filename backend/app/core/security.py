"""Security and cryptographic utility module for SentinelAI.

Provides NIST SP 800-132 compliant PBKDF2-HMAC-SHA256 password hashing,
timing-safe credential verification, and short-lived HS256 JWT access token
generation/validation without external native binary C-extension dependencies,
ensuring 100% portability to IBM LinuxONE (s390x).
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional
import jwt

from app.config import settings

# Canonical Role Definitions
ROLE_ADMIN = "ADMIN"
ROLE_OPERATOR = "OPERATOR"
ROLE_SERVICE = "SERVICE"
VALID_ROLES = {ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE}

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Generate a salted PBKDF2-HMAC-SHA256 hash for a plaintext password."""
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash using timing-safe comparison."""
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        algo, iterations_str, salt, expected_hex = parts
        if algo != f"pbkdf2_{PBKDF2_ALGORITHM}":
            return False
        iterations = int(iterations_str)
        key = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token containing subject, role, and expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": str(role).upper(),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(8),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed JWT access token.
    
    Returns payload dict if valid and non-expired; returns None on failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.PyJWTError:
        return None
