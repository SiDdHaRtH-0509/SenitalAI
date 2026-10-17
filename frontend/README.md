# SentinelAI — Frontend Command Operations Dashboard (Lead 1)

**Component Owner:** Lead 1 — Frontend Engineer  
**Current Phase:** Phase 1 — Frontend Foundation & Dashboard Skeleton  
**Target Environment:** Localhost / IBM LinuxONE (s390x) Web Client  

---

## 1. Frontend Purpose

SentinelAI is an AI-based intelligent video analytics platform for border surveillance using existing CCTV infrastructure. The frontend provides a centralized, professional command-center interface designed for border watch officers and surveillance operators.

In Phase 1, the frontend establishes the primary application shell, responsive navigation, typography, dark command-center design system, KPI cards, honest subsystem health telemetry indicators, and a structured security incident ledger with detailed event inspection modals.

---

## 2. Technology Stack

- **Framework:** React 18 (TypeScript)
- **Build Tool:** Vite 5 (ESNext, lightning-fast HMR)
- **Type Checking:** TypeScript 5.6 (strict mode enabled)
- **Design System:** Custom command-center CSS tokens (`variables.css`, `global.css`, `layout.css`, `dashboard.css`)
- **Iconography:** Lucide React (vector SVG command-center icons; no emojis as primary UI icons)
- **API Client:** Native `fetch` with AbortController timeouts and automatic offline fallback

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
- **Network:** Accessible across local subnet (host: true configured)

---

## 6. Production Build & Verification Commands

To typecheck and compile the production bundle:

```bash
# Type check without emitting files
npm run typecheck

# Full production build (tsc + vite build)
npm run build

# Preview the production build locally
npm run preview
```

Production output will be generated into `frontend/dist/`.

---

## 7. Current Functionality (Phase 1)

1. **Command-Center Application Shell:**
   - Dark command-center theme (deep navy, charcoal, restrained cyan/blue accents).
   - Sidebar with SentinelAI brand header, navigation items, and deployment platform status.
   - Responsive mobile navigation drawer with backdrop overlay.
2. **Top Operations Header:**
   - Active page title and contextual subtitle breadcrumb.
   - Real-time search filter affordance.
   - Interactive notification popover displaying system alerts.
   - Global system status indicator ("Integration Pending").
   - Generic demonstration operator identity ("Operator 04 — Watch Officer").
3. **KPI Metrics Grid:**
   - **Active Cameras:** Real-time online/offline camera counts (0/4 active in Phase 1).
   - **Events Today:** Logged perimeter incursions.
   - **Restricted-Zone Alerts:** Polygon boundary crossings.
   - **Critical Priority:** High-severity alerts requiring immediate response.
4. **Surveillance Monitoring Panel:**
   - Wireframe grid representing CCTV camera feed slots (Sector Alpha, Sector Bravo, Sector Delta, Sector Charlie).
   - Honest empty state explaining that video streaming integration is scheduled for Phase 2.
5. **Subsystem Health & Connectivity Panel:**
   - Displays real-time operational status for:
     - **Computer Vision Engine:** "Integration Pending" (Local tests pass; backend telemetry pending).
     - **Backend API:** "Not Connected" (Probed at `http://localhost:8000/api/health`).
     - **Database:** "Not Connected" (Schema initialized once backend launches).
     - **Dashboard:** "Operational" (Vite client application running cleanly).
   - Includes interactive **"Probe Subsystems"** button to re-check backend endpoints live.
6. **Recent Security Events Table:**
   - Structured table matching `API_CONTRACT.md` v1.0 schema: Event ID, Camera ID, Event Type, Timestamp, Confidence, Risk Level, Status, and Action.
   - Row-level search filtering across camera ID, zone ID, and risk level.
7. **Incident Deep-Dive Modal:**
   - Clicking any event row opens a detailed view showing detector confidence, bounding box coordinates, heuristic risk determinants (`reasons`), and recommended action.
8. **Navigation Routing & Honest Placeholders:**
   - Non-implemented pages (Live Monitoring, Security Events, Cameras, Restricted Zones, Analytics, System Health, Settings) display informative placeholder screens detailing the target phase and component ownership.

---

## 8. Known Limitations

- **Backend API Integration Pending:** The FastAPI backend service (`http://localhost:8000`) is currently unbuilt; the dashboard operates in graceful offline fallback mode.
- **Video Streams Inactive:** RTSP/HLS surveillance feeds are not yet streamed to the browser; feed slots display honest placeholder empty states.
- **Incident Acknowledgement Persistence:** Status changes simulate locally in the UI; database persistence will activate once the backend `PATCH /api/events/{id}/status` endpoint is live.
- **No Production Authentication:** Phase 1 uses a static demonstration profile ("Operator 04"). Production RBAC/OAuth is out of scope.

---

## 9. Identification of Demonstration Data

Demonstration records are strictly segregated and visibly identified:
- Demo fixtures reside in `src/data/demoData.ts` and are never mixed with live event storage.
- An amber **Notice Banner** is rendered persistently across the top of the application: `"Phase 1 UI Demonstration: DEMO DATA — For UI Layout & Evaluation Only"`.
- The Recent Events table features an explicit badge: `EXPLICIT DEMO DATA`.
- Individual demo records display a `DEMO` badge beside their Event ID.
- Event inspection modals display an amber demonstration warning box.

---

## 10. Planned Features for Later Phases

- **Phase 2 (Video Feeds & Ingestion):** Interactive CCTV video streaming (HLS/WebRTC), live bounding box canvas overlays, and zone boundary drawing.
- **Phase 3 (Event Ledger & Zone Management):** Historical event filtering, pagination, and restricted-zone polygon calibration tools.
- **Phase 4 (Advanced Analytics & LinuxONE Telemetry):** Hourly incursion trend charts, detector confidence distribution graphs, and s390x system performance telemetry.
- **Phase 5 (Hardening & Handover):** End-to-end integration with live FastAPI backend, persistent incident acknowledgement, and deployment validation.
