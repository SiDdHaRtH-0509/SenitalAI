"""Pytest test configuration and fixtures.

Sets up an isolated, temporary SQLite database file for tests to guarantee
that tests never touch or mutate the user's development database.
Provides authenticated and role-scoped TestClient fixtures.
"""

from datetime import timedelta
import os
import tempfile
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.core.security import ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE, create_access_token
from app.database import Base, get_db
from app.main import app
from app.services.auth_service import seed_default_users
from app.services.camera_service import seed_default_cameras
from app.services.zone_service import seed_default_zones

# Synchronize machine-to-machine service key in test environment
os.environ["SENTINEL_SERVICE_API_KEY"] = settings.SERVICE_API_KEY


@pytest.fixture(scope="function")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary SQLite database file and delete it after the test."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    path = temp_file.name

    yield path

    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def test_db_session(test_db_path: str) -> Generator[Session, None, None]:
    """Create a fresh database schema and seeded users/assets on the temporary DB file."""
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        seed_default_users(db)
        seed_default_cameras(db)
        seed_default_zones(db)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """Default TestClient authenticated with admin token for backward-compatible test suites."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    admin_token = create_access_token(
        subject="admin",
        role=ROLE_ADMIN,
        expires_delta=timedelta(hours=2),
    )

    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {admin_token}"
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_client(client: TestClient) -> TestClient:
    """Fixture alias explicitly named admin_client."""
    return client


@pytest.fixture(scope="function")
def unauth_client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient without any authorization headers."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def operator_client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient authenticated with OPERATOR role token."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject="operator",
        role=ROLE_OPERATOR,
        expires_delta=timedelta(hours=2),
    )

    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def service_client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient authenticated with SERVICE role token."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject="cv_service",
        role=ROLE_SERVICE,
        expires_delta=timedelta(hours=2),
    )

    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client

    app.dependency_overrides.clear()
