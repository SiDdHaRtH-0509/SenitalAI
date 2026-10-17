"""Pydantic schemas for User management, Authentication, and RBAC."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RoleEnum(str, Enum):
    """Supported Role-Based Access Control (RBAC) roles."""

    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    SERVICE = "SERVICE"


class UserBase(BaseModel):
    """Base user attributes."""

    username: str = Field(..., min_length=3, max_length=64, description="Unique account username")
    email: Optional[str] = Field(None, max_length=128, description="Contact email address")
    full_name: Optional[str] = Field(None, max_length=128, description="Operator display name")


class UserCreate(UserBase):
    """Registration request payload."""

    password: str = Field(..., min_length=6, max_length=128, description="Account password")
    role: Optional[RoleEnum] = Field(default=RoleEnum.OPERATOR, description="Requested role (default: OPERATOR)")


class UserResponse(UserBase):
    """Public user identity representation."""

    id: int
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Login credentials payload."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Plaintext password")


class Token(BaseModel):
    """Bearer access token response."""

    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    expires_in_seconds: int
    csrf_token: Optional[str] = None


class ServiceTokenRequest(BaseModel):
    """Request to generate a dedicated machine-to-machine service token."""

    service_name: str = Field("cv-engine", description="Identifier for machine service")
    valid_hours: int = Field(24, ge=1, le=8760, description="Token validity window in hours")


class ServiceTokenResponse(BaseModel):
    """Generated service token details."""

    token: str
    token_type: str = "bearer"
    service_name: str
    role: str = "SERVICE"
    expires_in_hours: int
