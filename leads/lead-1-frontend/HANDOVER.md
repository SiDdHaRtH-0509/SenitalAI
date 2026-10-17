# SentinelAI Frontend Handover & Demonstration Guide
**Project:** SentinelAI — AI-Based Intelligent Video Analytics Platform for Border Surveillance  
**Component:** Frontend Security Operations Command Center (`frontend/`)  
**Lead Role:** Lead 1 — Frontend Engineer  
**Handover Status:** Complete (Phases 1 through 5 fully implemented and verified)  
**Date:** October 17, 2026  

---

## 1. Executive Summary

The SentinelAI frontend command center is a responsive, crash-resilient Single Page Application (SPA) engineered with **React 18**, **TypeScript**, and **Vite**. It provides border surveillance operators and security commanders with real-time situational awareness, event triage, camera device registry tracking, restricted-zone polygon visualization, and historical analytics.

All 5 development phases are complete:
- **Phase 1:** Core layout shell, responsive styling, navigation, KPI cards, and baseline UI tokens.
- **Phase 2:** 7 dedicated operational views (Overview, Monitoring, Events, Cameras, Zones, Analytics, System Health).
- **Phase 3:** Typed API client (`ApiClient`), contract enforcement, resilient error normalization, and mock fallback.
- **Phase 4:** Real-time event streaming (`EventStreamService`), non-overlapping polling, audio alerts, and event review drawer.
- **Phase 5:** Final QA audit, universal `ErrorBoundary`, crash-resilient formatters, WCAG accessibility, 51 automated tests, and handover documentation.

---

## 2. Demonstration Guide for the IBM Datathon

This section provides a recommended script and screen progression for live judging or recorded demonstration.

### Recommended 3-Minute Demonstration Flow

#### Minute 0:00 – 0:45 | Overview & Executive Dashboard
1. Launch dashboard at `http://localhost:3000`.
2. Highlight the **Top Header Telemetry Badge**: point out the clear distinction between `"Backend Live"` and `"Offline / Demonstration Mode"`. Emphasize that the UI transparently informs operators of system connectivity.
3. Review the **Executive KPI Cards**:
   - Active Cameras (4 configured)
   - Events Recorded
   - Restricted Zone Incursions
   - System Subsystem Health
4. Walk through the **Recent Incidents Table**:
   - Point out risk-coded badges: `CRITICAL` (red), `HIGH` (orange), `MEDIUM` (yellow), `LOW` (green).
   - Click on an incident row to expand the **Event Detail Drawer**.
   - Show the detected bounding box, confidence score, camera metadata, and event timestamp formatted in UTC.

#### Minute 0:45 – 1:30 | Real-Time Monitoring & Event Triage
1. Navigate to **Live Monitoring** via the sidebar.
2. Select Camera **CAM-01 (Sector Alpha North Ridge)**.
3. Show the camera feed placeholder with the **Restricted Zone Overlay**:
   - The calibrated polygon boundary is visually drawn directly over the viewport.
   - Explain that when live streaming is wired via the media gateway, the video feed renders underneath this calibrated polygon.
4. Show the **Event Review Drawer**:
   - Demonstrate the status progression: `UNREVIEWED` ➔ `INVESTIGATING` ➔ `RESOLVED` / `FALSE_POSITIVE`.
   - Point out the review feedback banner and operator notes field.
   - Toggle audio alert notifications using the bell icon in the top header.

#### Minute 1:30 – 2:15 | Restricted Zones & Camera Registry
1. Navigate to **Restricted Zones**:
   - Show the 4 configured security zones: Perimeter Primary Buffer, Sector Alpha Buffer, Sector Bravo East Corridor, and Sector Delta Checkpoint.
   - Explain the polygon coordinates: normalized coordinates $[0, 1]$ mapped across camera frame aspect ratios.
   - Show the assigned reference strategy: `bottom_center` reference point aligned with the Computer Vision engine's feet-contact grounding.
2. Navigate to **Camera Registry**:
   - Toggle between **Grid View** and **Table View**.
   - Use the live search bar to filter cameras by sector or ID (e.g. typing `"Sector Alpha"` or `"CAM-01"`).
   - Click **View Technical Details** on a camera card to inspect RTSP stream URI, capture FPS, resolution, and hardware status.

#### Minute 2:15 – 3:00 | Surveillance Analytics & System Health
1. Navigate to **Analytics**:
   - Point out the 24-hour temporal incursion frequency distribution chart.
   - Highlight the mean detection confidence metric (derived deterministically from real event detections without random figures).
   - Review the risk distribution breakdown and per-camera incident volume.
2. Navigate to **System Health**:
   - Review the 4 operational subsystems:
     - **CV Engine:** Local YOLOv8n + Zone engine tested (122 tests passed).
     - **Backend API:** FastAPI REST service link.
     - **Database:** Persistent SQLite ledger.
     - **Frontend Dashboard:** React SPA (active).
   - Highlight the auto-refresh toggle and manual diagnostics check.

---

## 3. Demonstration Integrity & Truthfulness Rules

To maintain absolute academic and professional integrity during the IBM Datathon evaluation:

### What the Demonstrator CAN Truthfully Claim:
- **Frontend Architecture:** The dashboard is a complete, production-grade React 18 + Vite SPA with zero external UI bloat, built strictly according to `API_CONTRACT.md`.
- **CV Engine Verification:** The team has independently implemented and audited a 5-phase Computer Vision engine in `cv-engine/` with 122 passing unit tests (YOLOv8n person detector, polygon ray-casting incursion logic, event payload generation).
- **Resilient Fallback Mode:** In the absence of a live backend service, the frontend gracefully operates in offline demonstration mode, clearly notifying the user with banners rather than crashing or throwing unhandled errors.
- **Contract Adherence:** The frontend API service and state management are 100% prepared to connect to `http://localhost:8000` as soon as the backend service is started.
- **Crash Resilience:** The frontend implements an Error Boundary, safe UTC date formatters, safe float percentage guards, and nullish search filters.

### What the Demonstrator CANNOT Claim:
- **DO NOT** claim that live RTSP surveillance video is currently streaming into the browser. RTSP streams require an RTSP-to-WebRTC/HLS/MSE media gateway (e.g., go2rtc, MediaMTX), which is documented as pending infrastructure deployment.
- **DO NOT** claim that live backend events are being pushed from a running FastAPI server on port 8000 until the Overall Lead launches the backend service.
- **DO NOT** pretend demo data is live data. The interface explicitly badges all demonstration records with `DEMO` and `OFFLINE` indicators.

---

## 4. Setup & Launch Instructions for Localhost

### Prerequisites
- **Node.js:** v18.0.0 or higher (tested on Node v24.11.1)
- **npm:** v9.0.0 or higher

### Step 1: Install Dependencies
```bash
cd frontend
npm install
```

### Step 2: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Default `.env` configuration:
```env
# SentinelAI Frontend Environment Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_MOCK=true
VITE_STREAM_REFRESH_INTERVAL=5000
```

### Step 3: Run Automated Test Suites
Run all 51 automated tests (Phase 3 contract tests, Phase 4 real-time tests, Phase 5 QA tests):
```bash
npm test
```
*Expected result:* 51 tests passed, 0 failures, execution time < 400ms.

### Step 4: Run TypeScript Verification & Production Build
```bash
npm run typecheck
npm run build
```
*Expected result:* Clean TypeScript compilation, production bundle generated in `dist/` (~270 kB JS, ~24 kB CSS).

### Step 5: Start the Development Server
```bash
npm run dev
```
Open your browser at: **`http://localhost:3000`** (or the port displayed in your terminal).

---

## 5. Required Backend Endpoints (For Overall Project Lead)

The frontend is fully wired to consume the following REST endpoints as defined in `API_CONTRACT.md`. As soon as the backend service implements these routes, the frontend will automatically switch from demonstration mode to live mode:

| Endpoint | Method | Purpose | Response Model |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | System liveness probe | `{"status": "ok", "service": "sentinel-api"}` |
| `/api/stats` | `GET` | Dashboard KPI summary | `{"total_events": int, "by_risk_level": {...}, "active_cameras": int}` |
| `/api/events` | `GET` | Paginated event ledger | `{"events": [SecurityEvent], "total": int}` |
| `/api/events/{id}` | `GET` | Specific event detail | `SecurityEvent` payload with bounding box |
| `/api/events/{id}/status` | `PATCH` | Update triage status | `{"status": "INVESTIGATING", "notes": "..."}` |
| `/api/cameras` | `GET` | Registered CCTV cameras | `{"cameras": [CameraInfo]}` |
| `/api/zones` | `GET` | Restricted zone polygons | `{"zones": [RestrictedZoneInfo]}` |

---

## 6. Media Gateway Requirements (For Infrastructure Lead)

HTML5 browsers (`<video>` tags and WebRTC) cannot directly ingest raw `rtsp://` video streams due to protocol limitations. To achieve sub-second live video playback in the frontend:

1. **Recommended Gateway:** Deploy **go2rtc** or **MediaMTX** alongside the CV engine edge node.
2. **Transcoding / Remuxing:**
   - Ingest RTSP stream from CCTV camera (e.g. `rtsp://edge-node-01:554/live/north_ridge`).
   - Remux H.264/H.265 video packets into WebRTC or WebSocket MSE stream.
3. **Frontend Integration:**
   - The frontend `MonitoringPage.tsx` accepts an HTTP/WebRTC playback URL.
   - If WebRTC is supplied, it initializes standard `RTCPeerConnection` or HLS.js player.

---

## 7. QA & Accessibility Compliance Matrix

| Requirement | Implementation | Verification Status |
| :--- | :--- | :--- |
| **Crash Resilience** | `ErrorBoundary.tsx` wrapping application root | Verified |
| **Safe Timestamp Parsing** | `formatUtcTimestamp()` & `formatRelativeTime()` | Verified (0 unhandled RangeErrors) |
| **Safe Number Parsing** | `formatConfidencePercent()` NaN protection | Verified |
| **Nullish Filter Safety** | `safeLower()` across camera and event searches | Verified |
| **Keyboard Accessibility** | Skip-to-content anchor, universal `:focus-visible` | Verified |
| **Responsive Design** | CSS Grid & Flexbox, mobile breakpoints `<768px` | Verified |
| **Data Integrity** | Strict TypeScript interfaces matching `API_CONTRACT.md` | Verified |
| **Automated Testing** | 51 automated unit/contract tests | Verified (100% pass) |

---
*Document prepared and verified by Lead 1 (Frontend Engineer) — SentinelAI Project.*
