/**
 * SentinelAI Demonstration Data
 * 
 * IMPORTANT:
 * This file contains strictly labelled DEMONSTRATION FIXTURES.
 * These records are used to validate UI components, table layouts,
 * and badge formatting prior to live backend and CV integration.
 * They are NOT live surveillance events.
 */

import { SecurityEvent, DashboardStatistics, SystemHealthState, CameraInfo } from '../types';

export const IS_DEMO_MODE = true;
export const DEMO_DATA_NOTICE = 'DEMO DATA — For UI Layout & Evaluation Only';

export const DEMO_STATISTICS: DashboardStatistics = {
  active_cameras: 0,
  total_cameras: 4,
  events_today: 3,
  restricted_zone_alerts: 3,
  critical_alerts: 1,
  is_mock: true,
};

export const DEMO_EVENTS: SecurityEvent[] = [
  {
    event_id: 'evt-demo-0001',
    camera_id: 'cam-north-01',
    event_type: 'RESTRICTED_ZONE_ENTRY',
    timestamp: '2026-10-17T09:30:00Z',
    severity: 'CRITICAL',
    confidence: 0.94,
    zone_id: 'zone-restricted-perimeter-a',
    description: 'Person detected crossing restricted border line Alpha-1',
    evidence: {
      class_name: 'person',
      track_id: 1,
      frame_number: 420,
      bbox: [0.42, 0.55, 0.52, 0.78],
      reference_point: [0.47, 0.78],
    },
    risk_score: 88,
    risk_level: 'CRITICAL',
    reasons: [
      'Restricted-zone incursion confirmed by CV Ray-Casting',
      'Persistent detection across consecutive frames (debounced)',
      'High detector confidence (> 0.90)',
    ],
    recommended_action: 'Dispatch Sector Alpha patrol and alert watch commander',
    status: 'NEW',
    is_demo: true,
  },
  {
    event_id: 'evt-demo-0002',
    camera_id: 'cam-east-02',
    event_type: 'RESTRICTED_ZONE_ENTRY',
    timestamp: '2026-10-17T09:12:30Z',
    severity: 'HIGH',
    confidence: 0.86,
    zone_id: 'zone-restricted-buffer-east',
    description: 'Person detected lingering near border buffer fence',
    evidence: {
      class_name: 'person',
      track_id: 4,
      frame_number: 1850,
      bbox: [0.61, 0.40, 0.70, 0.68],
      reference_point: [0.655, 0.68],
    },
    risk_score: 72,
    risk_level: 'HIGH',
    reasons: [
      'Zone proximity threshold exceeded',
      'Dwell time in secondary warning zone > 15s',
    ],
    recommended_action: 'Monitor feed closely and notify perimeter outpost',
    status: 'ACKNOWLEDGED',
    is_demo: true,
  },
  {
    event_id: 'evt-demo-0003',
    camera_id: 'cam-south-04',
    event_type: 'RESTRICTED_ZONE_ENTRY',
    timestamp: '2026-10-17T08:45:12Z',
    severity: 'MEDIUM',
    confidence: 0.76,
    zone_id: 'zone-restricted-service-gate',
    description: 'Movement detected near authorized maintenance corridor',
    evidence: {
      class_name: 'person',
      track_id: null,
      frame_number: 890,
      bbox: [0.22, 0.60, 0.31, 0.85],
      reference_point: [0.265, 0.85],
    },
    risk_score: 46,
    risk_level: 'MEDIUM',
    reasons: [
      'Corridor boundary contact registered',
      'Moderate confidence detection in low-light shadow',
    ],
    recommended_action: 'Verify maintenance schedule with checkpoint logs',
    status: 'RESOLVED',
    is_demo: true,
  },
];

export const DEMO_CAMERAS: CameraInfo[] = [
  {
    camera_id: 'cam-north-01',
    name: 'Sector Alpha — North Ridge CCTV',
    location: 'Perimeter Boundary Mile 14.2',
    status: 'DISCONNECTED',
    resolution: '1920x1080',
    fps: 15,
    zone_id: 'zone-restricted-perimeter-a',
    is_demo: true,
  },
  {
    camera_id: 'cam-east-02',
    name: 'Sector Bravo — East Valley Fixed Cam',
    location: 'East Buffer Zone Post 3',
    status: 'DISCONNECTED',
    resolution: '1920x1080',
    fps: 20,
    zone_id: 'zone-restricted-buffer-east',
    is_demo: true,
  },
  {
    camera_id: 'cam-south-04',
    name: 'Sector Delta — South Gate Overview',
    location: 'Border Checkpoint Service Road',
    status: 'DISCONNECTED',
    resolution: '1280x720',
    fps: 10,
    zone_id: 'zone-restricted-service-gate',
    is_demo: true,
  },
  {
    camera_id: 'cam-west-03',
    name: 'Sector Charlie — River Crossing IR',
    location: 'River Bed Watchtower',
    status: 'DISCONNECTED',
    resolution: '1920x1080',
    fps: 15,
    zone_id: 'zone-restricted-river',
    is_demo: true,
  },
];

export const INITIAL_SYSTEM_HEALTH: SystemHealthState = {
  cv_engine: {
    id: 'cv_engine',
    name: 'Computer Vision Engine',
    status: 'INTEGRATION_PENDING',
    label: 'Integration Pending',
    description: 'Local YOLOv8n + Zone engine tested (122 tests passed); backend telemetry link pending deployment.',
    lastChecked: '2026-10-17 14:30:00 UTC',
    details: 'Module: sentinel_cv on localhost/edge node',
  },
  backend_api: {
    id: 'backend_api',
    name: 'FastAPI Backend API',
    status: 'DISCONNECTED',
    label: 'Not Connected',
    description: 'API endpoint http://localhost:8000/api/health is currently unreachable.',
    lastChecked: 'Just now',
    details: 'Awaiting implementation and deployment by Overall Lead',
  },
  database: {
    id: 'database',
    name: 'Event Storage (SQLite / DB)',
    status: 'DISCONNECTED',
    label: 'Not Connected',
    description: 'Persistent database storage will initialize once the backend service starts.',
    lastChecked: 'Just now',
    details: 'Schema: SQLite event ledger per API_CONTRACT.md',
  },
  dashboard: {
    id: 'dashboard',
    name: 'Frontend Command Dashboard',
    status: 'OPERATIONAL',
    label: 'Operational',
    description: 'React / Vite SPA running cleanly in browser (localhost execution).',
    lastChecked: 'Active',
    details: 'Phase 1 Frontend Foundation Active',
  },
};
