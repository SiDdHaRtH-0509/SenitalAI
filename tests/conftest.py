"""Conftest for root-level tests, importing fixtures from backend test configuration."""

from app.tests.conftest import client, test_db_path, test_db_session

__all__ = ["client", "test_db_path", "test_db_session"]
