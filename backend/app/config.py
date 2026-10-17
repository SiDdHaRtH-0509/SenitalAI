"""Configuration settings for SentinelAI FastAPI backend.

Loads environment variables with robust fallback defaults for development,
testing, and deployment on local and LinuxONE environments.
"""

import os
from typing import List


class Settings:
    """Application configuration settings."""

    def __init__(self) -> None:
        self.APP_NAME: str = os.getenv("APP_NAME", "SentinelAI Backend")
        self.APP_ENV: str = os.getenv("APP_ENV", "development")
        self.DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # Database configuration (default to local SQLite file)
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")

        # CORS origins: comma-separated list of allowed frontend hosts
        cors_raw = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
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


settings = Settings()
