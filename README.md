# SentinelAI — AI-Based Intelligent Video Analytics Platform for Border Surveillance Using Existing CCTV Infrastructure

[![Platform](https://img.shields.io/badge/Platform-Distributed%20Edge%20%2B%20LinuxONE-blue.svg)](#system-architecture)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python-009688.svg)](#technology-stack)
[![Computer Vision](https://img.shields.io/badge/CV-YOLOv8n%20%7C%20OpenCV-FF6F00.svg)](#technology-stack)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20TypeScript%20%7C%20Vite-61DAFB.svg)](#technology-stack)
[![Security](https://img.shields.io/badge/Security-JWT%20%7C%20RBAC%20%7C%20SHA--256%20Audit-red.svg)](#security-considerations)
[![Architecture](https://img.shields.io/badge/Architecture-x86__64%20%2F%20ARM64%20(Edge)%20%2B%20s390x%20(Backend)-green.svg)](#linuxone-deployment)

> **Important Scope & Compliance Notice:** SentinelAI is a functional, human-in-the-loop video event intelligence platform built for the **IBM Z Datathon 2026**. It serves as an intelligent decision-support prototype, not a certified operational border defense system. Incursion detection represents an **observable geometric condition** evaluated against configured polygonal security boundaries — it does not perform automated intent classification or autonomous enforcement. Human operator triage remains essential.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Repository Structure](#5-repository-structure)
6. [Prerequisites](#6-prerequisites)
7. [Local Setup](#7-local-setup)
8. [Configuration and Secrets](#8-configuration-and-secrets)
9. [Running Computer Vision](#9-running-computer-vision)
10. [Example Surveillance Videos](#10-example-surveillance-videos)
11. [API and Integration](#11-api-and-integration)
12. [LinuxONE Deployment](#12-linuxone-deployment)
13. [Testing](#13-testing)
14. [Security Considerations](#14-security-considerations)
15. [Demonstration Guide](#15-demonstration-guide)
16. [Current Limitations](#16-current-limitations)
17. [Team Collaboration](#17-team-collaboration)
18. [License](#18-license)

---

## 1. Project Overview

Modern border security and perimeter protection infrastructure relies heavily on legacy CCTV networks. Human operators monitoring dozens of simultaneous video feeds inevitably suffer from visual fatigue, resulting in delayed incident responses and undetected perimeter breaches.

**SentinelAI** transforms existing CCTV cameras into intelligent, automated surveillance nodes without requiring costly hardware retrofits. By combining:
- Edge-based **YOLOv8n** person detection,
- Ray-casting **polygonal restricted-zone geometry**,
- Temporal confirmation debouncing and deduplication,
- Transparent rule-based **risk scoring**, and
- Cryptographically verifiable **audit logging**,

SentinelAI provides real-time situational awareness to security personnel while maintaining complete decision transparency and human oversight.

---

## 2. Key Features

All features listed below are implemented and verified in the repository:

- **Dual-Mode Video Ingestion:** Seamless processing of live RTSP camera feeds (`RTSPVideoSource`) with automated reconnection handling, as well as local recorded MP4 surveillance files (`OpenCVVideoSource`).
- **Edge Person Detection:** Real-time pedestrian detection powered by Ultralytics YOLOv8n (filtering strictly for COCO person class 0) optimized for CPU/edge deployment.
- **Polygonal Zone Analysis:** Arbitrary 2D polygon restricted-zone definitions evaluated via pure-Python, zero-dependency ray casting.
- **Ground-Plane Contact Approximation:** Uses the `bottom_center` of detection bounding boxes to estimate feet contact on the ground plane, preventing false alarms when a subject's torso occludes a zone while standing outside it.
- **Temporal Debouncing & Deduplication:** Configurable temporal confirmation windows (`debounce`) and per-zone cooldown intervals (`cooldown`) prevent transient detection spikes and notification flooding.
- **Multi-Factor Risk Scoring:** Central risk engine evaluating observable factors (zone security tier, nighttime lighting, persistent presence, and trajectory) to assign risk scores (0.0 to 1.0) with plain-text explanatory reasons.
- **Authenticated Edge-to-Backend Submission:** Computer vision engine authenticates against the central API using dedicated M2M service tokens (`X-Service-Token` or Bearer JWT).
- **Role-Based Access Control (RBAC):** Backend-enforced role authorization (`admin`, `operator`, `service`) protecting sensitive surveillance feeds, camera configurations, and triage workflows.
- **Cryptographic Audit Hash Chain:** Every security event, status update, and operator action is recorded into a tamper-evident, SHA-256 HMAC hash-chained `audit_logs` ledger.
- **Operator Command Dashboard:** Single-page React/Vite interface featuring live event alerts, polygon schematics, camera feeds, operator triage modals, and system health monitors.
- **IBM LinuxONE Compatibility:** Central backend designed with zero architecture-specific dependencies, running portably on standard Linux as well as IBM LinuxONE (s390x) containers.
- **Zero-PyTorch Replay Fallback:** Built-in deterministic replay mode (`--replay`) allowing complete end-to-end pipeline verification without requiring PyTorch or GPU hardware.

---

## 3. System Architecture

SentinelAI employs an **edge-to-cloud distributed architecture** designed to optimize bandwidth, latency, and enterprise reliability:

```
+-----------------------------------------------------------------------------------+
|                                 EDGE SENSOR NODE                                  |
|   (x86_64 / ARM64 Edge Appliance, Security Operations Laptop, or Local Gateway)    |
|                                                                                   |
|  +--------------------+      +--------------------+      +---------------------+  |
|  |   CCTV / RTSP /    | ---> | YOLOv8n Detector   | ---> | Geometric Polygon   |  |
|  |   Local MP4 Feed   |      | (Person Class 0)   |      | Ray-Casting Zone    |  |
|  +--------------------+      +--------------------+      +---------------------+  |
|                                                                     |             |
|                                                                     v             |
|                                                          +---------------------+  |
|                                                          | Temporal Debouncing |  |
|                                                          | & Deduplication     |  |
|                                                          +---------------------+  |
|                                                                     |             |
+---------------------------------------------------------------------|-------------+
                                                                      |
                              Authenticated HTTP (JSON / Bearer Token)|
                                                                      v
+-----------------------------------------------------------------------------------+
|                        CENTRAL BACKEND (IBM LinuxONE / s390x)                     |
|                                                                                   |
|  +-----------------------+     +----------------------+     +------------------+  |
|  | FastAPI REST Gateway  | --> | Multi-Factor Risk    | --> | SQLite Database  |  |
|  | (Auth, RBAC, Rate-Lim)|     | Engine (0.0 - 1.0)   |     | (WAL Persistence)|  |
|  +-----------------------+     +----------------------+     +------------------+  |
|              |                            |                          |            |
|              v                            v                          v            |
|  +-----------------------+     +----------------------+     +------------------+  |
|  | Camera Worker Thread  |     | SHA-256 Audit Hash   |     | Event Triage &   |  |
|  | Lifecycle Manager     |     | Chaining Service     |     | Status Updates   |  |
|  +-----------------------+     +----------------------+     +------------------+  |
+-----------------------------------------------------------------------------------+
                                                                      ^
                                            Live REST / Polling Stream|
                                                                      v
+-----------------------------------------------------------------------------------+
|                              OPERATOR DASHBOARD                                   |
|                          (React 18 + Vite Frontend)                               |
|                                                                                   |
|  +---------------------+   +----------------------+   +------------------------+  |
|  | Real-Time Event Feed|   | Zone Polygon Canvas  |   | Operator Triage Modal  |  |
|  | & Severity Badges   |   | & Camera Grid        |   | (ACK / RESOLVE / ESC)  |  |
|  +---------------------+   +----------------------+   +------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Architectural Responsibilities:
1. **Edge Node:** Executes compute-intensive video decoding and neural-network inference close to the cameras. Emits structured lightweight event JSON over HTTPS, saving network bandwidth.
2. **Central Backend (LinuxONE Target):** Handles enterprise business logic, event correlation, persistence, security enforcement, cryptographic audit chaining, and operator API services.
3. **Frontend Dashboard:** Provides an intuitive command center for security personnel to review alerts, acknowledge warnings, and inspect historical incident records.

---

## 4. Technology Stack

| Layer | Component | Version / Technology | Purpose |
|---|---|---|---|
| **Edge Vision** | Object Detection | Ultralytics YOLOv8n (PyTorch) | Pretrained pedestrian detection (COCO class 0) |
| **Edge Vision** | Video Processing | OpenCV (`opencv-python` 4.10+) | RTSP streaming, video decoding, coordinate mapping |
| **Edge Vision** | Computational Geometry | Pure Python 3 | Ray-casting polygon intersection algorithm |
| **Backend** | Web Framework | FastAPI 0.115+ | High-performance asynchronous REST API |
| **Backend** | Validation & Settings | Pydantic v2 | Strict schema validation and typed configurations |
| **Backend** | ORM & Persistence | SQLAlchemy 2.0 + SQLite | Relational event storage with WAL concurrency |
| **Security** | Authentication | PyJWT + Passlib (bcrypt) | Stateless tokens, password hashing, and RBAC |
| **Security** | Audit Integrity | Python `hashlib` (SHA-256) | Tamper-evident cryptographic hash chain ledger |
| **Frontend** | Application Framework | React 18 + TypeScript | Component-based surveillance dashboard UI |
| **Frontend** | Tooling & Bundler | Vite 5 | Fast development server and production builds |
| **Frontend** | UI & Icons | Lucide React + Pure CSS | Responsive layouts, theme variables, polygon canvas |
| **Enterprise** | Server Target | IBM LinuxONE (s390x) | Central backend host leveraging IBM Z security |
| **Containers** | Packaging | Docker (Multi-Arch) | Containerized deployment for x86_64 and s390x |

---

## 5. Repository Structure

```text
sentinel-ai/
├── README.md                           # Main project documentation and quickstart
├── API_CONTRACT.md                     # Canonical REST API schemas and event contracts
├── ARCHITECTURE.md                     # System architecture and deployment topology
├── CONTRIBUTING.md                     # Development workflows and PR guidelines
├── DEMO_GUIDE.md                       # Comprehensive operator demonstration guide
├── DEMO_SCRIPT.md                      # Step-by-step presentation script for evaluators
├── ENVIRONMENT_SETUP.md                # Environment preparation for Windows and Linux
├── EXECUTION_PLAN.md                   # Phased project delivery plan and milestones
├── GITHUB_SETUP.md                     # Team GitHub repository instructions
├── IBM_Z_PLAN.md                       # IBM Z and LinuxONE integration strategy
├── INTEGRATION_TESTING.md              # End-to-end integration testing guide
├── LINUXONE_DEPLOYMENT.md              # LinuxONE containerization and setup instructions
├── PROJECT_CONTEXT.md                  # Mission context, background, and objectives
├── PROJECT_LEAD_PLAYBOOK.md            # Team leadership and delivery guidelines
├── RELEASE_CHECKLIST.md                # Pre-release validation and readiness checklist
├── REPOSITORY_STATUS.md                # High-level repository health summary
├── TASK_BOARD.md                       # Live task tracking across project phases
├── TEAM_ROLES.md                       # Ownership matrix for Workstreams and Leads
├── pytest.ini                          # Root pytest configuration
├── .env.example                        # Root environment variables template
├── .gitignore                          # Git exclusion rules
├── backend/                            # FastAPI Central Backend
│   ├── app/
│   │   ├── api/                        # REST endpoint routers (auth, cameras, events, stats, zones, audit)
│   │   ├── core/                       # Security utilities (JWT, password hashing, RBAC)
│   │   ├── models/                     # SQLAlchemy database models
│   │   ├── schemas/                    # Pydantic request/response schemas
│   │   ├── services/                   # Business logic (event service, risk engine, audit chain, camera workers)
│   │   ├── config.py                   # Typed settings and environment validation
│   │   ├── database.py                 # SQLite session factory and engine
│   │   └── main.py                     # FastAPI application factory and lifespan hooks
│   ├── tests/                          # Backend unit and integration test suite
│   ├── requirements.txt                # Backend Python dependencies
│   └── README.md                       # Backend documentation
├── cv-engine/                          # Edge Computer Vision Pipeline
│   ├── src/sentinel_cv/
│   │   ├── backend_client.py           # Authenticated HTTP client for event submission
│   │   ├── cli.py                      # CLI entry point (`py -m sentinel_cv`)
│   │   ├── config.py                   # CV engine runtime configuration
│   │   ├── detector.py                 # YOLOv8n and deterministic Mock/Replay detectors
│   │   ├── event_generator.py          # Temporal debouncer and event builder
│   │   ├── pipeline.py                 # Master CV pipeline coordinator
│   │   ├── rtsp_source.py              # Continuous RTSP video ingestion adapter
│   │   ├── video_source.py             # OpenCV video file and device reader
│   │   └── zone.py                     # Polygonal computational geometry and ray caster
│   ├── sample-data/
│   │   └── examples/                   # Verified surveillance benchmark videos for judges
│   ├── tests/                          # Computer vision unit and component tests
│   ├── requirements.txt                # CV engine Python dependencies
│   └── README.md                       # CV engine guide and CLI documentation
├── frontend/                           # React + Vite Operator Command Dashboard
│   ├── src/
│   │   ├── components/                 # UI components (auth, dashboard, monitoring, layouts)
│   │   ├── pages/                      # Dashboard views (Overview, Events, Cameras, Zones, Analytics, Health)
│   │   ├── services/                   # API client, event polling, notifications
│   │   ├── styles/                     # CSS stylesheets and theme variables
│   │   └── types/                      # TypeScript domain interfaces
│   ├── tests/                          # Vitest / Node test runner test suites
│   ├── package.json                    # Node dependencies and scripts
│   └── README.md                       # Frontend documentation
├── deploy/                             # Container and Deployment Assets
│   ├── Dockerfile.linuxone             # s390x / LinuxONE multi-arch Dockerfile
│   └── README.md                       # Container build and execution guide
├── docs/                               # Phase Reports & Compatibility Audits
│   ├── linuxone-compatibility.md       # s390x architecture audit report
│   ├── PHASE_2_REPORT.md               # Continuous RTSP ingestion engineering report
│   ├── PHASE_2_ACCEPTANCE_TEST_REPORT.md # Live event pipeline verification report
│   ├── PHASE_3_LINUXONE_REPORT.md      # LinuxONE deployment validation report
│   └── PHASE_4_RELEASE_READINESS.md    # Release readiness and security audit report
├── leads/                              # Workstream Lead Guides & Prompts
│   ├── lead-1-frontend/
│   ├── lead-2-computer-vision/
│   ├── lead-3-linuxone/
│   └── lead-4-support/
├── prompts/                            # Prompt engineering reference templates
├── scripts/                            # Operational utilities (e.g., RTSP stream simulator)
└── tests/                              # Shared end-to-end integration tests
```

---

## 6. Prerequisites

### Edge Node (Computer Vision):
- **Operating System:** Windows 10/11, Ubuntu 20.04/22.04 LTS, or macOS (x86_64 or ARM64).
- **Python:** Python 3.10 to 3.12 (tested also on 3.14).
- **Hardware:** Standard CPU (Intel Core i5/i7 or AMD Ryzen) or GPU (CUDA optional).
- **Network:** Outbound HTTP connectivity to Central Backend.

### Central Backend & LinuxONE Host:
- **Operating System:** Any Linux distribution (RHEL, Ubuntu, Rocky Linux) on x86_64 or **IBM LinuxONE (s390x)**.
- **Python:** Python 3.10+ (standard library + FastAPI; zero PyTorch requirement).
- **Container Engine (Optional):** Docker or Podman.

### Operator Dashboard:
- **Node.js:** Node.js 18.x or 20.x LTS.
- **Package Manager:** `npm` 9+.
- **Browser:** Any modern Chromium-based browser (Chrome, Edge, Brave) or Firefox.

---

## 7. Local Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/SiDdHaRtH-0509/SenitalAI.git sentinel-ai
cd sentinel-ai
```

### Step 2: Configure Environment
Copy the template configuration files:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Step 3: Launch Central Backend (Terminal 1)
```bash
cd backend
python -m pip install -r requirements.txt
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- **REST API:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Health Check Endpoint:** `http://127.0.0.1:8000/api/health`

### Step 4: Launch Operator Dashboard (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```
- **Operator Dashboard URL:** `http://localhost:3000`
- Default Operator Credential: `operator` / `SentinelOp2026!`

---

## 8. Configuration and Secrets

SentinelAI enforces strict secret hygiene:
- Configuration values are loaded via typed Pydantic settings from environment variables or local `.env` files.
- `.env` files and local database files are excluded by `.gitignore` and are **never committed to Git**.
- When `APP_ENV=production` is set, the backend actively validates secrets on startup and **refuses to boot** if default, disclosed, or weak credentials are detected.

### Key Environment Variables

| Variable | Default (Development) | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Application mode (`development` or `production`). |
| `DATABASE_URL` | `sqlite:///./sentinel.db` | Database connection string. |
| `JWT_SECRET_KEY` | *(Ephemeral dynamic secret)* | HMAC-SHA256 signing key for authentication tokens. |
| `CV_SERVICE_TOKEN` | *(Rotated service key)* | Machine-to-machine service key for CV engine ingestion. |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed origins for cross-origin frontend requests. |
| `AUTH_ENABLED` | `true` | Enforces authentication on sensitive surveillance endpoints. |

---

## 9. Running Computer Vision

The CV engine can be run against local video files or live network cameras using the `sentinel_cv` CLI.

Ensure `PYTHONPATH` points to `cv-engine/src`:

### Windows (PowerShell):
```powershell
cd cv-engine
$env:PYTHONPATH="src"
py -m sentinel_cv --video sample-data/examples/restricted_zone_entry.mp4 --model yolov8n.pt --camera-id cam-north-01 --zone-id zone-restricted-01 --zone-vertices "[(550,200),(768,200),(768,450),(550,450)]" --backend-url http://127.0.0.1:8000 --json
```

### Linux / macOS (Bash):
```bash
cd cv-engine
export PYTHONPATH=src
python3 -m sentinel_cv --video sample-data/examples/restricted_zone_entry.mp4 --model yolov8n.pt --camera-id cam-north-01 --zone-id zone-restricted-01 --zone-vertices "[(550,200),(768,200),(768,450),(550,450)]" --backend-url http://127.0.0.1:8000 --json
```

### Key CLI Flags:
- `--video <path>`: Path to local MP4 video file or RTSP stream URL (`rtsp://...`).
- `--model <path>`: YOLO model weights (default: `yolov8n.pt`) or `mock` for testing.
- `--zone-vertices "<coords>"`: Polygon vertices formatted as a Python list or JSON of `(x, y)` tuples.
- `--strategy bottom_center`: Evaluates foot contact point against the polygon boundary.
- `--debounce <int>`: Consecutive frames required before triggering an event (default: `1`).
- `--cooldown <float>`: Seconds to suppress duplicate alarms for the same zone (default: `5.0`).
- `--backend-url <url>`: Target Central Backend address (default: `http://localhost:8000`).
- `--disable-events`: Runs offline computer vision analysis without posting to backend.
- `--replay`: Runs deterministic synthetic replay (no PyTorch or GPU required).

---

## 10. Example Surveillance Videos

SentinelAI includes a lightweight suite of three verified example surveillance videos under `cv-engine/sample-data/examples/` (~3.27 MB total, Apache 2.0 licensed from OpenCV Foundation):

| File | Scenario | Duration | Expected Observations |
|---|---|---|---|
| `normal_patrol.mp4` | Open-Area Patrol | 15.0s (150 frames) | Continuous person detection; **0 zone incursions**; no false alarms. |
| `restricted_zone_entry.mp4` | Perimeter Breach | 15.0s (150 frames) | Person crosses into corridor polygon; **emits HTTP 201 SecurityEvent** to backend with risk score. |
| `multiple_people.mp4` | High-Density Crowd | 15.0s (150 frames) | Multi-target detection (**peak 9 concurrent persons**); 1,000+ bounding boxes processed. |

For detailed scenario guides and copy-paste commands, see the [Example Videos Guide](cv-engine/sample-data/examples/README.md).

---

## 11. API and Integration

SentinelAI implements a RESTful API contract documented in [API_CONTRACT.md](API_CONTRACT.md).

### Core Endpoints:

| Method | Endpoint | Access Level | Description |
|---|---|---|---|
| `GET` | `/api/health` | Public | System status, database health, and active version. |
| `POST` | `/api/auth/login` | Public | Authenticates user; issues JWT and HttpOnly cookie. |
| `POST` | `/api/auth/logout` | Authenticated | Clears active authentication session. |
| `GET` | `/api/auth/me` | Authenticated | Retrieves current operator profile and permissions. |
| `GET` | `/api/events` | Operator / Admin | Retrieves surveillance events with pagination and filtering. |
| `POST` | `/api/events` | CV Service / Admin | Ingests structured `SecurityEvent` from edge camera. |
| `GET` | `/api/events/{id}` | Operator / Admin | Retrieves individual event details and risk breakdown. |
| `PATCH` | `/api/events/{id}/status` | Operator / Admin | Updates triage status (`ACKNOWLEDGED`, `RESOLVED`, `ESCALATED`). |
| `GET` | `/api/cameras` | Operator / Admin | Lists registered surveillance cameras and stream status. |
| `POST` | `/api/cameras/{id}/start` | Admin | Initiates continuous background worker thread for camera. |
| `POST` | `/api/cameras/{id}/stop` | Admin | Terminates camera background worker thread. |
| `GET` | `/api/zones` | Operator / Admin | Retrieves configured polygon boundaries and risk ratings. |
| `GET` | `/api/stats/dashboard` | Operator / Admin | Aggregates high-level metrics for dashboard cards. |
| `GET` | `/api/audit-logs` | Admin | Retrieves immutable audit trail records. |
| `GET` | `/api/audit-logs/verify` | Admin | Verifies SHA-256 cryptographic hash-chain integrity. |

---

## 12. LinuxONE Deployment

SentinelAI adopts a **hybrid distributed edge-inference / LinuxONE-backend** model:
- **Edge Devices (x86_64 / ARM64):** Run local camera capture and YOLOv8n inference where native wheels and camera hardware reside.
- **IBM LinuxONE (s390x):** Runs the central FastAPI backend, multi-factor risk scoring engine, relational persistence, and cryptographic audit hashing inside an s390x Linux container.

### Building & Running on LinuxONE (s390x):
```bash
# Build multi-arch container image
docker build -t sentinel-ai-backend:linuxone -f deploy/Dockerfile.linuxone .

# Run container on LinuxONE node
docker run -d --name sentinel-backend -p 8000:8000 \
  -e APP_ENV=production \
  -e JWT_SECRET_KEY="<secure-random-secret>" \
  -e CV_SERVICE_TOKEN="<secure-service-key>" \
  sentinel-ai-backend:linuxone
```

> **Hardware Disclosure:** Container compatibility with IBM LinuxONE (s390x) has been validated via multi-arch container emulation and s390x Linux container test passes (see [docs/linuxone-compatibility.md](docs/linuxone-compatibility.md) and [docs/PHASE_3_LINUXONE_REPORT.md](docs/PHASE_3_LINUXONE_REPORT.md)). Native execution on physical IBM LinuxONE enterprise hardware remains an unverified deployment target pending physical access.

---

## 13. Testing

SentinelAI maintains strict test coverage across all three modules:

### 1. Backend Test Suite (Pytest)
```bash
py -m pytest backend/app/tests -q
```
- **Coverage:** Authentication, RBAC, camera worker lifecycle, event ingestion, risk scoring, SQLite persistence, and audit hash chaining.
- **Status:** **57 passed** (0 failures).

### 2. Computer Vision Test Suite (Pytest)
```bash
# PowerShell:
$env:PYTHONPATH="cv-engine/src"; py -m pytest cv-engine/tests -q

# Linux/Bash:
PYTHONPATH=cv-engine/src python3 -m pytest cv-engine/tests -q
```
- **Coverage:** Video sources, RTSP reconnect logic, YOLO detector adapters, mock/replay detectors, polygon ray-casting geometry, event generation, debouncing, and backend client HTTP retries.
- **Status:** **134 passed** (0 failures).

### 3. Frontend Test Suite (Vitest / Node.js)
```bash
cd frontend
npm test -- --run
```
- **Coverage:** API client contracts, error wrapping, authentication token transmission, live polling transitions, unread notification counters, status triage transitions, and formatters.
- **Status:** **59 passed** (0 failures).

### 4. End-to-End Integration Suite
```bash
py -m pytest tests/test_e2e_cv_backend.py -q
```
- **Status:** **Passed**.

---

## 14. Security Considerations

- **Authentication:** Stateless JSON Web Tokens (JWT) using HS256 algorithms with configurable expiration.
- **Cookie Security:** Web browser sessions store tokens in `HttpOnly`, `SameSite=Strict`, `Secure` cookies to mitigate XSS-based token theft.
- **CSRF Protection:** State-changing requests validate `X-CSRF-Token` headers.
- **Service-to-Service Security:** The computer vision engine uses dedicated machine-to-machine service keys (`X-Service-Token`) separate from user credentials.
- **Audit Integrity:** Security audit records are linked using a cryptographic hash chain:
  $$\text{hash}_n = \text{SHA256}(\text{hash}_{n-1} \,\|\, \text{action} \,\|\, \text{actor} \,\|\, \text{timestamp} \,\|\, \text{details})$$
  Any manual alteration or tampering of previous records immediately invalidates the chain verification check (`GET /api/audit-logs/verify`).

---

## 15. Demonstration Guide

For evaluators and judges seeking to observe SentinelAI in action, follow this concise sequence:

1. **Start Backend & Frontend:** Launch both services as shown in [Local Setup](#7-local-setup).
2. **Access Dashboard:** Open `http://localhost:3000` and sign in with the default operator credentials (`operator` / `SentinelOp2026!`).
3. **Trigger Incursion Video:** Open a terminal and run the restricted zone entry example clip:
   ```powershell
   cd cv-engine
   $env:PYTHONPATH="src"
   py -m sentinel_cv --video sample-data/examples/restricted_zone_entry.mp4 --model yolov8n.pt --camera-id cam-perimeter-02 --zone-id zone-corridor-east --zone-vertices "[(550,200),(768,200),(768,450),(550,450)]" --backend-url http://127.0.0.1:8000 --json
   ```
4. **Observe Live Triage:**
   - Watch the new `RESTRICTED_ZONE_ENTRY` alert appear in real-time on the dashboard.
   - Click the event to inspect the detection confidence, timestamp, and rule-based risk reasons.
   - Change the event status to `ACKNOWLEDGED` or `RESOLVED` and submit triage notes.
5. **Verify Audit Trail:** Open `http://127.0.0.1:8000/docs#/Audit/verify_audit_log_chain_api_audit_logs_verify_get` to confirm the unbroken cryptographic SHA-256 audit log.

For a complete walkthrough script, refer to [`DEMO_GUIDE.md`](DEMO_GUIDE.md) and [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

---

## 16. Current Limitations

In adherence to datathon transparency standards, the following boundaries and operational limitations are documented:

1. **Edge Hardware Dependency:** Neural network inference with PyTorch/Ultralytics requires standard x86_64 or ARM64 architectures. Native YOLO inference is not validated on IBM s390x mainframe architecture due to PyTorch wheel constraints on LinuxONE; the s390x node is intended for central backend operations.
2. **Physical CCTV Hardware:** Real physical IP cameras were not integrated due to facility hardware constraints; stream ingestion was verified using local benchmark video files and simulated RTSP streams (`scripts/simulate_rtsp_stream.py`).
3. **2D Perspective Distortion:** Ground-contact evaluation utilizes the bottom-center of 2D bounding boxes as an approximation of the 3D ground plane. Extreme camera angles or steep elevations may introduce perspective distortion.
4. **Adverse Weather & Lighting:** The system is evaluated on daylight benchmark CCTV footage. Night operations, heavy fog, or thermal surveillance require specialized model training.
5. **Human-in-the-Loop Requirement:** This platform is an assistive triage tool. It does not replace trained human security operators.

---

## 17. Team Collaboration

SentinelAI was built using a multi-lead collaborative structure documented in the repository:
- **Project Lead:** Architecture, shared contracts, backend risk engine, integration.
- **Lead 1 (Frontend):** Operator dashboard, real-time UI components, triage modal ([leads/lead-1-frontend/](leads/lead-1-frontend/)).
- **Lead 2 (Computer Vision):** Video sources, YOLOv8n detector, polygon zone geometry ([leads/lead-2-computer-vision/](leads/lead-2-computer-vision/)).
- **Lead 3 (LinuxONE):** Container packaging, s390x compatibility, deployment assets ([leads/lead-3-linuxone/](leads/lead-3-linuxone/)).
- **Lead 4 (QA & Support):** Test suites, verification scripts, documentation, and demo support ([leads/lead-4-support/](leads/lead-4-support/)).

For branching rules and contribution guidelines, see [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`TEAM_ROLES.md`](TEAM_ROLES.md).

---

## 18. License

The SentinelAI project license is to be formally designated by the repository owner and hackathon organizers.

*Note on Third-Party Assets:*
- Sample surveillance video clips in `cv-engine/sample-data/examples/` are derived from the OpenCV Foundation benchmark dataset and redistributed under the terms of the **Apache License 2.0 / 3-Clause BSD License**.
