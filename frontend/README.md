# SentinelAI — Frontend Command Operations Dashboard (Lead 1)

**Component Owner:** Lead 1 — Frontend Engineer  
**Current Phase:** Phase 5 — Final QA, Performance Optimization & Demonstration Handover (Complete)  
**Target Environment:** Localhost / IBM LinuxONE (s390x) Web Client  
**Verification:** 51 Automated Tests Passing, 0 Type Errors, Production Build Verified  

---

## 1. Frontend Purpose

SentinelAI is an AI-based intelligent video analytics platform for border surveillance using existing CCTV infrastructure. The frontend provides a centralized, professional command-center interface designed for border watch officers and surveillance operators.

In Phase 2, the frontend implements all 8 primary application routes:
1. **Overview Dashboard (`/`):** KPI summary, surveillance monitoring wireframe, subsystem health, recent security incident ledger, and activity trends.
2. **Live Monitoring (`/monitoring`):** Responsive edge camera feed grid with honest stream disconnection states and technical stream inspector modals.
3. **Security Incident Ledger (`/events`):** Full incident table matching `API_CONTRACT.md` schema with text search, risk-level filtering, lifecycle status filtering, multi-field sorting, and incident inspection modals.
4. **Camera Device Registry (`/cameras`):** Camera node inventory with grid/table view toggle, RTSP stream specifications, capture resolutions, frame rates, and assigned restricted zones.
5. **Restricted Zones (`/zones`):** Boundary geometries evaluated by the pure Python Ray-Casting algorithm (`sentinel_cv`), featuring normalized $[0, 1]$ SVG polygon schematics and vertex coordinates.
6. **Surveillance Analytics (`/analytics`):** Deterministic event analytics displaying severity breakdown progress bars, camera distribution, mean detector confidence, and a 24-hour UTC temporal incursion histogram.
7. **Platform Subsystem Health (`/system-health`):** Comprehensive telemetry verification across Computer Vision, Backend API, Database, and Web Dashboard, with a live "Probe Subsystems Live" network tester.
8. **Client Settings (`/settings`):** Local client preferences (table density, telemetry polling frequency, audio alarms, persistent demo banners) persisted to browser `localStorage`.

---

## 2. Technology Stack

- **Framework:** React 18 (TypeScript)
- **Build Tool:** Vite 5 (ESNext, lightning-fast HMR)
- **Type Checking:** TypeScript 5.6 (strict mode enabled)
- **Design System:** Custom command-center CSS tokens (`variables.css`, `global.css`, `layout.css`, `dashboard.css`)
- **Iconography:** Lucide React (vector SVG command-center icons; no emojis as primary UI icons)
- **API Client:** Native `fetch` with AbortController timeouts and automatic offline fallback
- **Routing:** Browser history and URL hash synchronization (`#/monitoring`, `#/events`, `#/cameras`, `#/zones`, `#/analytics`, `#/system-health`, `#/settings`)

---

## 3. Prerequisites

- **Node.js:** v18.0.0 or later (tested on v24.11.1)
- **npm:** v9.0.0 or later (tested on v11.6.2)
- Modern web browser (Chrome, Edge, Firefox, Safari)

---

## 4. Installation Instructions

Navigate to the `frontend/` directory from the repository root:

```bash
cd frontend
npm install
```

---

## 5. Development Command

To start the local development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The application will be served at:
- **Local:** `http://localhost:3000`
- **Network:** Accessible across local subnet (`host: true` configured)

---

## 6. Production Build & Verification Commands

To typecheck and compile the production bundle:

```bash
# Execute test suite (32 contract, real-time, and integration test cases)
npm test

# Type check without emitting files
npm run typecheck

# Full production build (tsc + vite build)
npm run build

# Preview the production build locally
npm run preview
```

Production output is compiled into `frontend/dist/` in ~1.5 seconds with zero warnings or errors.

---

## 7. Real-Time Telemetry & Event Monitoring Architecture (Phase 4)

Phase 4 implements a decoupled real-time event ingestion and operator notification system built upon the `EventStreamService` interface.

### Transport Strategy
- **Preferred Order:** Server-Sent Events (SSE) $\rightarrow$ WebSockets $\rightarrow$ Controlled HTTP Polling $\rightarrow$ Integration Pending.
- **Current Operational Reality:** Because the backend implementation is pending deployment by the Overall Lead, the frontend operates in **INTEGRATION_PENDING** mode with safe, non-overlapping polling fallback.
- **Polling Configuration:** Respects `VITE_POLLING_INTERVAL_SEC` (default: 30s). A value of `0` cleanly disables background timers and activates manual-only refresh mode.
- **Concurrency Locking:** Reusable `PollingEventStreamService` uses active request locking to eliminate overlapping HTTP requests when network latency exceeds polling frequency.

### Security Notification Center
- **Header Bell Indicator:** Dynamic badge displaying live unread counts (`aria-label`).
- **Deduplication Engine:** Stable `notif-{event_id}` IDs guarantee events are never notified twice across repeated polls.
- **Operator Review Tracking:** Browser-local read status persisted in `localStorage` without mutating server-side incident states.
- **Operator Incident Inspection:** Direct modal trigger from notifications with full YOLOv8n detection telemetry and recommended actions.
- **Audio Chime:** Gentle, opt-in synthesized chime via Web Audio API (zero external audio files).

### Visual Feedback & Operator Workflow
- **Row Arrival Glow:** Newly arrived events flash briefly with `.event-row-new` (respecting `prefers-reduced-motion`).
- **Status Workflow:** Permitted transitions (`NEW` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`) with honest offline feedback when the backend is unreachable.
- **Camera Stream States:** Explicitly reports `STREAM_INTEGRATION_PENDING` or `CAMERA_DISCONNECTED` without fabricated CCTV video.

---

## 8. Backend API Integration & Architecture (Phase 3)

Phase 3 introduces a centralized, typed, and resilient HTTP client layer (`src/services/apiClient.ts`) strictly mapped to `API_CONTRACT.md` v1.0.

### Environment Configuration (`.env.example`)
Create a `.env` file in `frontend/` (or rely on defaults):
```bash
# FastAPI backend base endpoint
VITE_API_BASE_URL=http://localhost:8000

# Client request timeout in milliseconds
VITE_API_TIMEOUT_MS=5000

# Background telemetry polling interval in seconds
VITE_POLLING_INTERVAL_SEC=30
```

### API Client Capabilities
- **Strictly Typed Contracts:** Comprehensive TypeScript interfaces for request bodies and response payloads.
- **Timeout & Cancellation:** Native `AbortController` timeout handling with automatic signal merging.
- **Standardized Error Translation:** Normalizes HTTP non-2xx status codes, fetch refusals (`isNetworkError`), and timeouts (`isTimeout`) into `ApiClientError`.
- **Zero-Crash Offline Fallback:** When the backend server is unreachable or offline, the client cleanly falls back to calibrated demonstration fixtures with an explicit `isLive: false` flag and human-readable banner notices.
- **Security & Hygiene:** Zero hardcoded credentials or private tokens.

### Contract Test Coverage
Run `npm test` to execute the full test suite (`tests/apiClient.test.ts`), covering:
1. `GET /api/health`, `GET /api/stats`, and `GET /api/events` successful response parsing.
2. HTTP 404 and 500 error propagation with structured details.
3. Network connection refusal (`ECONNREFUSED`) handling and offline fallback.
4. Slow request timeouts (50ms abort with status 408).
5. Non-JSON / HTML error response handling without syntax errors.
6. Empty event lists (`[]`) handled safely without crashing.
7. Missing optional fields (`risk_score`, `reasons`, `recommended_action`, `person_count`).
8. Client-side risk level, camera, status filtering and timestamp sorting.
9. Loading and offline fallback states with demo fixtures.
10. Error translation and human-readable messaging.
11. `PATCH /api/events/{id}/status` status persistence.
12. Configurable base URL normalization and query parameter serialization.

---

## 8. Implemented Pages & Features

### A. Overview Dashboard (`/`)
- Consolidated KPI cards (Active Cameras 0/4, Events Today, Restricted-Zone Alerts, Critical Priority).
- Surveillance Feeds wireframe overview.
- Subsystem Health connectivity cards.
- Recent Security Events table with explicit DEMO DATA badges.
- Hourly incursion trends summary.

### B. Live Monitoring (`/monitoring`)
- Grid layout representing CCTV edge nodes (Sector Alpha, Sector Bravo, Sector Delta, Sector Charlie).
- Status filtering (All, Disconnected, Online).
- Truthful empty stream state: `"No camera stream connected — stream integration pending"`.
- Clicking any camera card opens the **Camera Specifications Inspector** modal displaying capture specs and RTSP URIs.

### C. Security Events Ledger (`/events`)
- Search filter across Event ID, Camera ID, Event Type, Zone ID, and description.
- Multi-dimensional filters: Risk Level (All, CRITICAL, HIGH, MEDIUM, LOW), Status (All, NEW, ACKNOWLEDGED, RESOLVED), and Event Type.
- Multi-field sorting: Timestamp (newest/oldest), Risk Score (high to low), Confidence (high to low).
- Reset Filters button that restores standard view in one click.
- Row click opens **Incident Details Modal** displaying detector confidence, normalized bounding box, rule reasons, and recommended actions.

### D. Cameras Inventory (`/cameras`)
- Grid and Table view toggles.
- Real-time search across camera ID, location, name, and zone.
- Full hardware capture specs (1920x1080 @ 15-20 FPS, 1280x720 @ 10 FPS).

### E. Restricted Zones (`/zones`)
- Calibrated polygon boundary definitions matching `sentinel_cv.config` (`zone-restricted-01`, `zone-restricted-perimeter-a`, etc.).
- Normalized $[0, 1]$ SVG coordinate polygon schematic rendering vertex pins and boundary lines.
- Vertex coordinates table detailing each $(x, y)$ coordinate pair.
- Honest disclaimer noting that interactive polygon drawing requires backend persistence.

### F. Surveillance Analytics (`/analytics`)
- Pure SVG / CSS visualizations computed deterministically from recorded events.
- Risk level breakdown progress bars (Critical, High, Medium, Low).
- Camera sensor incursion distribution.
- 24-hour UTC temporal incursion histogram.
- Average AI detection confidence calculation.

### G. System Health (`/system-health`)
- In-depth telemetry status across all 4 components (Frontend, CV Engine, Backend API, Database).
- Interactive **"Probe Subsystems Live"** button testing `GET /api/health` with real-time probe activity console.
- Truthful reporting: unverified services remain marked "Not Connected".

### H. Settings (`/settings`)
- Table row density preference: Comfortable vs Compact.
- Telemetry auto-polling interval: Disabled / 10s / 30s / 60s.
- Persistent demo notice banner toggle.
- Audible critical alarm toggle.
- Preferences automatically saved to `localStorage` with a "Reset Defaults" option.

---

## 8. Known Limitations

- **Backend API Offline:** The FastAPI service (`http://localhost:8000`) is pending deployment by the Overall Lead; the frontend operates in offline fallback mode.
- **Video Streams Inactive:** RTSP/HLS camera streams are not active in Phase 2; camera cards display truthful empty stream states.
- **Incident Acknowledgement Persistence:** Status changes simulate locally; database persistence requires the backend `PATCH /api/events/{id}/status` endpoint.
- **No Production Authentication:** Phase 2 uses a static demonstration profile ("Operator 04"). Production RBAC/OAuth is out of scope.

---

## 9. Identification of Demonstration Data

Demonstration records are strictly segregated and visibly identified:
- Demo fixtures reside in `src/data/demoData.ts` and are never mixed with live event storage.
- An amber **Notice Banner** is rendered persistently across the top of the application: `"Phase 1 UI Demonstration: DEMO DATA — For UI Layout & Evaluation Only"`.
- The Recent Events table features an explicit badge: `EXPLICIT DEMO DATA`.
- Individual demo records display a `DEMO` badge beside their Event ID.
- Event inspection modals display an amber demonstration warning box.

---

## 10. Completed Development Roadmap (Phases 1 - 5)

- **Phase 1 (Foundation & Shell):** React 18 + Vite foundation, sidebar navigation, top header, KPI stat cards, and dark theme design tokens.
- **Phase 2 (Dashboard Pages):** Complete interfaces for Live Monitoring, Security Events, Camera Registry, Restricted Zones, Surveillance Analytics, and System Health.
- **Phase 3 (Backend Integration & Contracts):** Centralized `ApiClient`, typed error wrappers, configurable `VITE_API_BASE_URL`, and 12 contract tests.
- **Phase 4 (Real-Time Monitoring & Telemetry):** `EventStreamService` polling loop, event deduplication, notification drawer, audio alert preference, and 20 real-time tests.
- **Phase 5 (Final QA, Hardening & Handover):** Universal `ErrorBoundary`, crash-resilient formatters, WCAG keyboard accessibility, skip-to-content links, 51 passing automated tests, and comprehensive handover guide (`leads/lead-1-frontend/HANDOVER.md`).

---

## 11. Automated Testing Suite

The frontend includes 51 automated tests executing via Node.js native test runner and `tsx`:
- **Contract Tests (`tests/apiClient.test.ts`):** 12 integration tests covering HTTP status translations, timeouts, offline fallbacks, and payload normalization.
- **Real-Time Tests (`tests/phase4Realtime.test.ts`):** 20 tests covering polling locks, deduplication, chronological sorting, audio preferences, and telemetry indicators.
- **QA & Resilience Tests (`tests/phase5FinalQa.test.ts`):** 19 tests verifying UTC formatters, NaN protection, nullish search filters, demo schema conformance, and error boundary logic.

Run the entire suite:
```bash
npm test
```

