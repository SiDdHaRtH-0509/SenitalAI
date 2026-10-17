# SentinelAI API Contract v1.0

This is the source of truth for inter-module communication. Overall Lead owns changes; all affected leads must agree before changing a field or endpoint.

## Base URL
`http://localhost:8000` locally. On LinuxONE use the configured reachable host/port, not this local default.

## `GET /api/health`
Response:
```json
{"status":"ok"}
```

## `POST /api/events`
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

Response (example values are illustrative):
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
  "risk_score": 65,
  "risk_level": "HIGH",
  "reasons": ["Restricted-zone entry rule triggered"],
  "recommended_action": "Request human verification",
  "status": "NEW"
}
```

## `GET /api/events`
Returns stored events newest-first. Do not invent pagination parameters without updating this contract.

## `GET /api/stats`
Returns counts computed from stored events, for example:
```json
{"total_events":1,"by_risk_level":{"LOW":0,"MEDIUM":0,"HIGH":1,"CRITICAL":0}}
```

## Optional status update
Only implement after Overall Lead confirms it and updates the contract:
`PATCH /api/events/{event_id}/status`
Request: `{"status":"ACKNOWLEDGED"}`; allowed statuses: `NEW`, `ACKNOWLEDGED`, `RESOLVED`.

## Field rules
- `event_id`: unique string; duplicate submission must be idempotent.
- `camera_id`: string.
- `event_type`: initially only `RESTRICTED_ZONE_ENTRY`.
- `timestamp`: ISO-8601 with timezone.
- `severity`: `LOW|MEDIUM|HIGH|CRITICAL`; do not confuse it with `risk_score`.
- `confidence`: number 0–1 representing detector confidence, not threat probability.
- `zone_id`: string or null.
- `description`: factual concise description.
- `evidence`: JSON object.
- `risk_score`: integer 0–100, heuristic priority only.
- `risk_level`: `LOW|MEDIUM|HIGH|CRITICAL`.
- `reasons`: array of strings.
- `recommended_action`: human review recommendation.
- `status`: `NEW|ACKNOWLEDGED|RESOLVED`.

## Error behavior
- Invalid request: useful 4xx response.
- Duplicate event ID: return the existing record or an agreed idempotent response; never create duplicates.
- Unexpected error: safe 5xx response; log details server-side.
- Never return secrets or stack traces to the browser.

## Ownership
- CV producer creates observable event fields.
- Backend validates, stores and calculates risk.
- Frontend presents backend results.
- Lead 3 configures/deploys but does not fork business logic.
