# SentinelAI API Contract v1.0

This is the source of truth for inter-module communication across the Computer Vision engine, FastAPI backend, and React command dashboard. Overall Lead owns changes; all affected leads must agree before changing a field or endpoint.

## Base URL
`http://localhost:8000` locally. On LinuxONE use the configured reachable host/port, not this local default.

---

## 1. `GET /api/health`
Return operational liveness of the FastAPI backend.
Response:
```json
{
  "status": "ok",
  "service": "sentinel-api"
}
```

---

## 2. `POST /api/events`
Submit a validated security incident from the Computer Vision pipeline.
Request:
```json
{
  "event_id": "evt-demo-0001",
  "camera_id": "cam-demo-01",
  "event_type": "RESTRICTED_ZONE_ENTRY",
  "timestamp": "2026-10-17T09:30:00Z",
  "severity": "HIGH",
  "confidence": 0.91,
  "zone_id": "zone-restricted-01",
  "description": "Detection entered the configured zone",
  "evidence": {
    "class_name": "person",
    "track_id": null,
    "frame_number": 420
  }
}
```

Response (HTTP 201 Created):
```json
{
  "event_id": "evt-demo-0001",
  "camera_id": "cam-demo-01",
  "event_type": "RESTRICTED_ZONE_ENTRY",
  "timestamp": "2026-10-17T09:30:00Z",
  "severity": "HIGH",
  "confidence": 0.91,
  "zone_id": "zone-restricted-01",
  "description": "Detection entered the configured zone",
  "evidence": {
    "class_name": "person",
    "track_id": null,
    "frame_number": 420
  },
  "risk_score": 80,
  "risk_level": "HIGH",
  "reasons": [
    "Base severity set to HIGH (60 pts)",
    "Restricted-zone boundary breached (zone-restricted-01) (+10 pts)",
    "High detector confidence (0.91 >= 0.85) (+10 pts)"
  ],
  "recommended_action": "Request human verification and alert nearest patrol unit",
  "status": "NEW",
  "operator_notes": null,
  "created_at": "2026-10-17T12:00:00Z"
}
```

### Idempotency & Duplicate Handling
If an event with an existing `event_id` is submitted again, the backend returns **HTTP 409 Conflict**:
```json
{
  "event_id": "evt-demo-0001",
  "status": "NEW",
  "message": "Duplicate event ID acknowledged",
  "detail": "Event 'evt-demo-0001' already recorded; no duplicate created.",
  "risk_score": 80,
  "risk_level": "HIGH"
}
```
No duplicate rows are created in the database.

---

## 3. `GET /api/events`
Returns stored security events ordered newest-first (timestamp DESC).

Query parameters:
- `limit`: integer (1-200, default: 50)
- `offset`: integer (default: 0)
- `camera_id`: optional string filter
- `risk_level`: optional string filter (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `status`: optional string filter (`NEW`, `ACKNOWLEDGED`, `RESOLVED`)
- `event_type`: optional string filter

Response: Array of `SecurityEventResponse` objects.

---

## 4. `GET /api/events/{event_id}`
Returns a single security event by ID. Returns HTTP 404 if not found.

---

## 5. `PATCH /api/events/{event_id}/status`
Allows an authorized operator to update incident triage status and commentary notes.
Request:
```json
{
  "status": "ACKNOWLEDGED",
  "notes": "Guard patrol dispatched to Sector Alpha."
}
```

Response (HTTP 200 OK):
Returns the updated `SecurityEventResponse` with the updated status and appended operator notes.

### Canonical Status Enum & Backward Compatibility
The **canonical status enum** is strictly:
- `NEW`: Incident received from CV engine; unreviewed.
- `ACKNOWLEDGED`: Operator has reviewed incident and initiated triage/investigation.
- `RESOLVED`: Incident confirmed and resolved, or cleared as false alert.

**Accepted Aliases:** For backward compatibility with legacy draft interfaces, the API normalizes:
- `UNREVIEWED` ➔ `NEW`
- `INVESTIGATING` ➔ `ACKNOWLEDGED`
- `REVIEWED` ➔ `ACKNOWLEDGED`
- `RESOLVED` ➔ `RESOLVED`
- `FALSE_POSITIVE` ➔ `RESOLVED`
- `DISMISSED` ➔ `RESOLVED`

Invalid status strings return HTTP 422 Unprocessable Content.

---

## 6. `GET /api/stats`
Returns live aggregate surveillance counts computed from stored database records:
```json
{
  "total_events": 14,
  "by_risk_level": {
    "LOW": 2,
    "MEDIUM": 4,
    "HIGH": 6,
    "CRITICAL": 2
  },
  "active_cameras": 3,
  "total_cameras": 4
}
```

---

## 7. `GET /api/cameras`
Returns configured CCTV camera edge nodes. Returns an empty array `[]` if no cameras are configured.
Response:
```json
[
  {
    "camera_id": "cam-north-01",
    "name": "Sector Alpha — North Ridge Primary PTZ",
    "location": "North Perimeter Observation Tower Alpha",
    "status": "ONLINE",
    "resolution": "1920x1080",
    "fps": 20.0,
    "zone_id": "zone-restricted-01",
    "stream_uri": "rtsp://edge-node-01.local:554/live/north_ridge",
    "last_ping": "2026-10-17T12:00:00Z"
  }
]
```

---

## 8. `GET /api/zones`
Returns calibrated restricted-zone boundary polygons:
Response:
```json
[
  {
    "zone_id": "zone-restricted-01",
    "name": "Perimeter Primary Buffer (Default CV Zone)",
    "camera_id": "cam-north-01",
    "status": "ACTIVE",
    "vertices": [
      [0.30, 0.50],
      [0.70, 0.50],
      [0.70, 0.90],
      [0.30, 0.90]
    ],
    "reference_strategy": "bottom_center",
    "incursions_today": 2,
    "description": "Calibrated boundary configured in sentinel_cv.config."
  }
]
```

---

## 9. `POST /api/events/batch`
Ingest multiple events in a single HTTP request from CV bulk processors or replay pipelines.
Request: `{"events": [...]}`
Response: `{"total": int, "created": int, "duplicates": int, "errors": [], "events": [...]}`

---

## 10. Field Rules & Constraints
- `event_id`: Unique non-empty string; duplicate submissions are strictly idempotent.
- `camera_id`: Non-empty string.
- `event_type`: Categorical string; initially `RESTRICTED_ZONE_ENTRY`.
- `timestamp`: ISO-8601 UTC string with timezone (`YYYY-MM-DDTHH:MM:SSZ` or offset).
- `severity`: `LOW|MEDIUM|HIGH|CRITICAL`; initial base severity from detection rules.
- `confidence`: Finite float strictly in $[0.0, 1.0]$.
- `zone_id`: String identifier or null.
- `description`: Concise factual text.
- `evidence`: JSON object containing detector telemetry metadata. Supported formats:
  - `bounding_box`: Object with `{ x1: float, y1: float, x2: float, y2: float }` (native CV engine and backend format)
  - `bbox`: 4-element array `[x1, y1, x2, y2]` (client coordinate format)
  - `reference_point` / `bottom_center`: 2-element array `[x, y]` representing foot ground-contact coordinate
  - `frame_number`: integer frame index
  - `track_id`: optional integer tracker ID or null
  - `class_name`: detection classification (`"person"`)
- `risk_score`: Heuristic integer in $[0, 100]$, computed deterministically by backend.
- `risk_level`: Categorical risk classification (`LOW|MEDIUM|HIGH|CRITICAL`).
- `reasons`: Array of human-readable explanation strings.
- `recommended_action`: Actionable security response guidance.
- `status`: Canonical enum `NEW|ACKNOWLEDGED|RESOLVED`.

---

## 11. Error Behavior
- Invalid request payload: HTTP 422 with structured field error path details.
- Duplicate event ID: HTTP 409 with duplicate acknowledgment details.
- Missing resource: HTTP 404 with descriptive detail message.
- Safe 5xx responses: Internal details logged server-side; zero secrets or stack traces exposed to clients.
