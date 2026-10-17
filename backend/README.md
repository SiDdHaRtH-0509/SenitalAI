# SentinelAI — FastAPI Backend Service (Overall Project Lead)

**Component Owner:** Senior Python Backend Engineer & Overall Project Lead  
**Phase:** Phase 1 — FastAPI Backend Implementation & System Integration  
**Framework:** FastAPI 0.110+ / Pydantic V2 / SQLAlchemy 2.0 / SQLite  
**Port:** `8000` (configurable via `PORT` environment variable)  

---

## 1. Overview

The SentinelAI backend provides high-performance, validated, and persistent REST API services for the SentinelAI Border Surveillance platform. It integrates:
1. **The Computer Vision Pipeline:** Ingests structured `SecurityEvent` detections via `POST /api/events` and bulk batches via `POST /api/events/batch` with strict duplicate idempotency.
2. **The Deterministic Risk Engine:** Evaluates visual severity, detector confidence, and zone sensitivity into an explainable 0–100 risk score and categorical risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
3. **The SQLite Event Ledger:** Persists incidents, review status transitions, and operator notes across server restarts.
4. **The React Command Dashboard:** Serves real-time incident feeds, aggregate KPI statistics, camera hardware inventory, and calibrated restricted-zone boundary polygons.

---

## 2. Prerequisites & Python Environment

- **Python Version:** Python 3.10 to 3.14 (verified on Python 3.14.2)
- **SQLite:** 3.35+ (standard with Python)
- **PowerShell (Windows)** or **Bash (Linux / IBM LinuxONE s390x)**

---

## 3. Installation & Setup

Navigate to the `backend/` directory:

```powershell
# Windows PowerShell
cd backend
```

```bash
# Linux / macOS
cd backend
```

### Create and Activate Virtual Environment (Recommended)

**Windows PowerShell:**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / IBM LinuxONE:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Configuration (`.env`)

Copy `.env.example` to `.env` to customize settings:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# Linux
cp .env.example .env
```

Key environment variables:
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port for FastAPI uvicorn server |
| `HOST` | `0.0.0.0` | Bind address |
| `DATABASE_URL` | `sqlite:///./sentinel.db` | SQLite database URI |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed frontend origins (comma-separated) |
| `SEED_CONFIGURED_ASSETS` | `true` | Seed default cameras and zones if DB empty |
| `LOG_LEVEL` | `INFO` | Console logging verbosity |

---

## 5. Starting the Backend Server

Start the server using `uvicorn`:

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Linux / IBM LinuxONE:**
```bash
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Alternatively using the Python runner:
```powershell
py -m uvicorn app.main:app --port 8000 --reload
```

The server will be available at: **`http://localhost:8000`**

---

## 6. Interactive API Documentation (Swagger & ReDoc)

Once the backend is running, open your web browser:
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc UI:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON Schema:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 7. Running Backend Automated Tests

The backend test suite uses `pytest` and runs completely offline with a dedicated temporary SQLite database. Tests never modify your development database:

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="."
py -m pytest app/tests -v
```

**Linux / IBM LinuxONE:**
```bash
PYTHONPATH=. pytest app/tests -v
```

### Test Suite Coverage (25 Automated Tests):
1. `test_health.py`: Liveness probe (`GET /api/health`) and root endpoint.
2. `test_stats.py`: Aggregate statistics on empty and populated database (`GET /api/stats`).
3. `test_events.py`: Event creation, retrieval, filtering, pagination, 404 handling, duplicate prevention (HTTP 409), invalid payload rejection (HTTP 422), and batch ingestion.
4. `test_status.py`: Operator review workflow (`PATCH /api/events/{id}/status`), valid status transitions, notes appending, and alias normalization.
5. `test_cameras_zones.py`: Camera device registry and restricted zone polygon endpoints.
6. `test_persistence.py`: Validates database persistence and recovery across full application restarts.
7. `test_cv_integration.py`: 7 end-to-end integration tests between CVPipeline and FastAPI backend covering deterministic replay mode, genuine YOLOv8 neural network inference on video frames, blank-frame honest negative verification, schema conformance, risk computation, duplicate handling, DB restart recovery, and backend network failure resilience.

---

## 8. Connecting Frontend to the Backend

The React command dashboard automatically connects to `http://localhost:8000` by default.

To point the frontend to a custom backend address (e.g. when deployed on LinuxONE or remote host):
1. Navigate to `frontend/`:
   ```bash
   cd ../frontend
   ```
2. Update `.env`:
   ```env
   VITE_API_BASE_URL=http://your-server-ip:8000
   ```
3. Restart frontend dev server:
   ```bash
   npm run dev
   ```

---

## 9. Implemented Endpoints Matrix

| Endpoint | Method | Status | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | ✅ Implemented | Root metadata & service links |
| `/api/health` | `GET` | ✅ Implemented | Service liveness probe (`{"status": "ok", ...}`) |
| `/api/stats` | `GET` | ✅ Implemented | Surveillance metrics derived from SQLite ledger |
| `/api/events` | `GET` | ✅ Implemented | Paginated event list with filters (newest first) |
| `/api/events` | `POST` | ✅ Implemented | Event ingestion with risk calculation & idempotency |
| `/api/events/{id}` | `GET` | ✅ Implemented | Single incident detail inspection |
| `/api/events/{id}/status` | `PATCH` | ✅ Implemented | Incident review status triage & operator notes |
| `/api/events/batch` | `POST` | ✅ Implemented | Bulk ingestion for CV processors/replay streams |
| `/api/cameras` | `GET` | ✅ Implemented | CCTV hardware inventory & streaming specs |
| `/api/cameras` | `POST` | ✅ Implemented | Register or update camera edge node |
| `/api/zones` | `GET` | ✅ Implemented | Restricted boundary polygons & reference strategy |
| `/api/zones` | `POST` | ✅ Implemented | Register or calibrate restricted boundary |

---

## 10. Integration Status & Remaining Blockers

### Verified Integrations:
- **CV Engine Adapter:** Successfully verified against `cv-engine/src/sentinel_cv/backend_client.py`. Event submission, response parsing, and duplicate handling (HTTP 409) pass 100%.
- **Frontend Contract:** Aligned with `frontend/src/services/apiClient.ts` schemas.
- **SQLite Persistence:** Validated persistence and idempotency across simulated server reboots.

### Pending Integrations (For Subsequent Phases):
- **Live RTSP Video Gateway:** Native browsers require WebRTC/HLS. The backend does not stream raw video files; an RTSP gateway (e.g., go2rtc, MediaMTX) remains to be deployed by Infrastructure Lead.
- **Production Authentication (RBAC):** Current phase prototype allows local operator triage without JWT/OAuth tokens. Production auth should be wired before public deployment.
