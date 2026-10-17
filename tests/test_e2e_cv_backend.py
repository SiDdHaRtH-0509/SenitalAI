"""Root End-to-End Test Suite for SentinelAI CV Engine & FastAPI Backend.

Provides root-level test discovery verifying:
1. End-to-end CV video processing and event emission to FastAPI backend.
2. SQLite persistence and schema conformance per API_CONTRACT.md.
3. Automated risk scoring and classification.
4. HTTP 409 Conflict idempotent duplicate handling.
5. SQLite persistence across server/database restarts.
"""

import sys
from pathlib import Path

# Add backend and cv-engine/src to path
repo_root = Path(__file__).resolve().parents[1]
backend_path = repo_root / "backend"
cv_path = repo_root / "cv-engine" / "src"

for p in (str(backend_path), str(cv_path)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.tests.test_cv_integration import TestCVBackendIntegration

__all__ = ["TestCVBackendIntegration"]
