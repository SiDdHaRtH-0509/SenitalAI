"""Configuration settings for SentinelAI FastAPI backend.

Loads environment variables with robust fallback defaults for development,
testing, and deployment on local and LinuxONE environments.
Supports loading .env files without external dependencies.
Enforces strict production security validation.
"""

import os
from pathlib import Path
import secrets
from typing import List, Set


def load_dotenv_if_present() -> None:
    """Load key-value pairs from .env file into os.environ if not already set.
    
    Checks current directory and parent directories up to repo root.
    Uses standard library only for 100% LinuxONE (s390x) portability.
    """
    search_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",  # repo root
        Path(__file__).resolve().parents[1] / ".env",  # backend root
    ]
    for env_path in search_paths:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val
                break
            except Exception:
                pass


# Load .env before initializing Settings
load_dotenv_if_present()

# Known insecure/disclosed credentials that MUST NOT be used in production
DISCLOSED_DEFAULTS: Set[str] = {
    # Phase 1 disclosed defaults
    "sentinel-ai-insecure-dev-secret-change-in-production-2026",
    "sentinel-cv-service-secret-key-2026",
    "SentinelAdmin2026!",
    "SentinelOp2026!",
    "SentinelService2026!",
    # Phase 1.1 disclosed defaults
    "sentinel-ai-dev-secret-key-rotate-2026-phase1-1-hardening-token",
    "sentinel-cv-m2m-service-key-2026-phase1-1-rotated",
    "SentinelAdmin2026!RotatedSecure",
    "SentinelOp2026!RotatedSecure",
    "SentinelService2026!RotatedSecure",
    # Generic placeholder secrets
    "replace_with_a_secure_random_secret_in_production",
    "replace_with_a_secure_service_key_in_production",
    "replace_with_secure_admin_password",
    "replace_with_secure_operator_password",
    "replace_with_secure_service_password",
    "secret",
    "changeme",
    "password",
    "admin",
    "sentinel",
}


class Settings:
    """Application configuration settings with production validation."""

    def __init__(self) -> None:
        self.APP_NAME: str = os.getenv("APP_NAME", "SentinelAI Backend")
        self.APP_ENV: str = os.getenv("APP_ENV", "development").lower()
        self.DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # Database configuration (default to local SQLite file)
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")

        # CORS origins: comma-separated list of allowed frontend hosts
        cors_raw = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:5173",
        )
        self.CORS_ORIGINS: List[str] = [
            origin.strip() for origin in cors_raw.split(",") if origin.strip()
        ]

        # Asset seeding (seeds configured cameras and zones on startup if empty)
        self.SEED_CONFIGURED_ASSETS: bool = os.getenv(
            "SEED_CONFIGURED_ASSETS", "true"
        ).lower() in ("1", "true", "yes")

        # Logging level
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

        # Authentication and Security settings (Phase 1, 1.1, 1.2)
        self.AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "true").lower() in ("1", "true", "yes")

        # JWT Secret Key: load from env or generate dynamic ephemeral secret in development
        env_jwt = os.getenv("JWT_SECRET_KEY")
        if env_jwt and (not self.is_production or env_jwt not in DISCLOSED_DEFAULTS):
            self.JWT_SECRET_KEY: str = env_jwt
        elif self.is_production:
            self.JWT_SECRET_KEY: str = env_jwt or ""
        else:
            self.JWT_SECRET_KEY: str = secrets.token_urlsafe(32)

        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.SERVICE_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("SERVICE_TOKEN_EXPIRE_MINUTES", "1440"))

        # Machine-to-Machine (M2M) Service API key
        env_service_key = os.getenv("SENTINEL_SERVICE_API_KEY") or os.getenv("SENTINEL_API_KEY")
        if env_service_key and (not self.is_production or env_service_key not in DISCLOSED_DEFAULTS):
            self.SERVICE_API_KEY: str = env_service_key
        elif self.is_production:
            self.SERVICE_API_KEY: str = env_service_key or ""
        else:
            self.SERVICE_API_KEY: str = secrets.token_urlsafe(32)

        # Initial account passwords (loaded from .env or generated dynamically outside source control)
        env_admin_pwd = os.getenv("ADMIN_DEFAULT_PASSWORD")
        self.ADMIN_DEFAULT_PASSWORD: str = env_admin_pwd if env_admin_pwd else (
            "" if self.is_production else secrets.token_urlsafe(16)
        )

        env_op_pwd = os.getenv("OPERATOR_DEFAULT_PASSWORD")
        self.OPERATOR_DEFAULT_PASSWORD: str = env_op_pwd if env_op_pwd else (
            "" if self.is_production else secrets.token_urlsafe(16)
        )

        env_svc_pwd = os.getenv("SERVICE_DEFAULT_PASSWORD")
        self.SERVICE_DEFAULT_PASSWORD: str = env_svc_pwd if env_svc_pwd else (
            "" if self.is_production else secrets.token_urlsafe(16)
        )

        # Cookie security settings
        self.COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
        if self.is_production:
            self.COOKIE_SECURE = True

        # Enforce production security check
        self.validate_production_secrets()

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV in ("production", "prod")

    def validate_production_secrets(self) -> None:
        """Enforce strict secret hygiene when running in production.
        
        Never logs or reveals secret values in failure messages.
        """
        if not self.is_production:
            return

        violations: List[str] = []

        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY in DISCLOSED_DEFAULTS or len(self.JWT_SECRET_KEY) < 32:
            violations.append("JWT_SECRET_KEY must be an uncompromised high-entropy secret (>=32 chars).")

        if not self.SERVICE_API_KEY or self.SERVICE_API_KEY in DISCLOSED_DEFAULTS or len(self.SERVICE_API_KEY) < 32:
            violations.append("SENTINEL_SERVICE_API_KEY must be an uncompromised high-entropy secret (>=32 chars).")

        if not self.ADMIN_DEFAULT_PASSWORD or self.ADMIN_DEFAULT_PASSWORD in DISCLOSED_DEFAULTS:
            violations.append("ADMIN_DEFAULT_PASSWORD must not use known default values in production.")

        if not self.OPERATOR_DEFAULT_PASSWORD or self.OPERATOR_DEFAULT_PASSWORD in DISCLOSED_DEFAULTS:
            violations.append("OPERATOR_DEFAULT_PASSWORD must not use known default values in production.")

        if not self.SERVICE_DEFAULT_PASSWORD or self.SERVICE_DEFAULT_PASSWORD in DISCLOSED_DEFAULTS:
            violations.append("SERVICE_DEFAULT_PASSWORD must not use known default values in production.")

        if violations:
            raise RuntimeError(
                "CRITICAL SECURITY VALIDATION FAILURE:\n"
                + "\n".join(f"- {v}" for v in violations)
                + "\nPlease set non-default environment variables or consult .env.example."
            )


settings = Settings()
