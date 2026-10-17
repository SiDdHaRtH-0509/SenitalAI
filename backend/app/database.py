"""Database configuration and session management for SentinelAI.

Uses SQLAlchemy 2.0 with SQLite for reliable local persistent storage,
supporting safe thread operations and transactional integrity.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings

# SQLite requires check_same_thread=False for FastAPI concurrency
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a managed SQLAlchemy database session.

    Ensures the session is cleanly closed upon request completion or error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
