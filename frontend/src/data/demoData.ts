/**
 * SentinelAI Demonstration Data
 * 
 * IMPORTANT:
 * This file contains strictly labelled DEMONSTRATION FIXTURES.
 * These records are used to validate UI components, table layouts,
 * and badge formatting prior to live backend and CV streaming integration.
 * They are NOT live surveillance events.
 */

import type {
  SecurityEvent,
  DashboardStatistics,
  SystemHealthState,
  CameraInfo,
  RestrictedZoneInfo,
  ClientSettings,
  UserProfile,
} from '../types';

export const DEMO_OPERATOR_USER: UserProfile = {
  id: 2,
  username: 'operator',
  email: 'operator@sentinel.local',
  full_name: 'Border Security Officer',
  role: 'OPERATOR',
  is_active: true,
  created_at: '2026-10-17T00:00:00Z',
  last_login: '2026-10-17T08:00:00Z',
};

export const DEMO_ADMIN_USER: UserProfile = {
  id: 1,
  username: 'admin',
  email: 'admin@sentinel.local',
  full_name: 'System Administrator',
  role: 'ADMIN',
  is_active: true,
  created_at: '2026-10-17T00:00:00Z',
  last_login: '2026-10-17T08:00:00Z',
};

export const IS_DEMO_MODE = true;
export const DEMO_DATA_NOTICE = 'DEMO DATA — For UI Layout & Evaluation Only';

export const DEFAULT_CLIENT_SETTINGS: ClientSettings = {
  table_density: 'comfortable',
  auto_refresh_interval: 30,
  show_demo_notices: true,
  enable_audio_alerts: false,
  theme: 'dark-navy',
};

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
    zone_id: 'zone-restricted-01',
    description: 'Person detected crossing primary boundary line Alpha-1',
    evidence: {
      class_name: 'person',
      track_id: 1,
      frame_number: 420,
      person_count: 1,
      bbox: [0.42, 0.55, 0.52, 0.78],
      reference_point: [0.47, 0.78],
    },
    person_count: 1,
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
      person_count: 1,
      bbox: [0.61, 0.40, 0.70, 0.68],
      reference_point: [0.655, 0.68],
    },
    person_count: 1,
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
      person_count: 1,
      bbox: [0.22, 0.60, 0.31, 0.85],
      reference_point: [0.265, 0.85],
    },
    person_count: 1,
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
    zone_id: 'zone-restricted-01',
    stream_uri: 'rtsp://edge-node-01.local:554/live/north_ridge',
    last_ping: 'Never (Integration Pending)',
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
    stream_uri: 'rtsp://edge-node-02.local:554/live/east_valley',
    last_ping: 'Never (Integration Pending)',
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
    stream_uri: 'rtsp://edge-node-04.local:554/live/south_gate',
    last_ping: 'Never (Integration Pending)',
    is_demo: true,
  },
  {
    camera_id: 'cam-west-03',
    name: 'Sector Charlie — River Crossing IR',
    location: 'River Bed Watchtower',
    status: 'DISCONNECTED',
    resolution: '1920x1080',
    fps: 15,
    zone_id: 'zone-restricted-01',
    stream_uri: 'rtsp://edge-node-03.local:554/live/river_ir',
    last_ping: 'Never (Integration Pending)',
    is_demo: true,
  },
];

export const DEMO_ZONES: RestrictedZoneInfo[] = [
  {
    zone_id: 'zone-restricted-01',
    name: 'Perimeter Primary Buffer (Default CV Zone)',
    camera_id: 'cam-north-01',
    status: 'ACTIVE',
    vertices: [
      [0.30, 0.50],
      [0.70, 0.50],
      [0.70, 0.90],
      [0.30, 0.90],
    ],
    reference_strategy: 'bottom_center',
    incursions_today: 2,
    description: 'Calibrated boundary configured in sentinel_cv.config. Polygon coordinates normalized to [0, 1] frame dimensions.',
    is_demo: true,
  },
  {
    zone_id: 'zone-restricted-perimeter-a',
    name: 'Sector Alpha North Ridge Buffer',
    camera_id: 'cam-north-01',
    status: 'ACTIVE',
    vertices: [
      [0.25, 0.40],
      [0.85, 0.40],
      [0.85, 0.85],
      [0.25, 0.85],
    ],
    reference_strategy: 'bottom_center',
    incursions_today: 1,
    description: 'North ridge boundary zone covering unpaved approach corridor.',
    is_demo: true,
  },
  {
    zone_id: 'zone-restricted-buffer-east',
    name: 'Sector Bravo East Valley Corridor',
    camera_id: 'cam-east-02',
    status: 'ACTIVE',
    vertices: [
      [0.50, 0.30],
      [0.95, 0.30],
      [0.95, 0.80],
      [0.50, 0.80],
    ],
    reference_strategy: 'bottom_center',
    incursions_today: 1,
    description: 'Secondary buffer line between fence boundary and outer road.',
    is_demo: true,
  },
  {
    zone_id: 'zone-restricted-service-gate',
    name: 'Sector Delta Checkpoint Service Gate',
    camera_id: 'cam-south-04',
    status: 'ACTIVE',
    vertices: [
      [0.15, 0.50],
      [0.45, 0.50],
      [0.45, 0.90],
      [0.15, 0.90],
    ],
    reference_strategy: 'bottom_center',
    incursions_today: 1,
    description: 'Controlled maintenance corridor restricting unauthorized personnel traversal.',
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
    endpoint: 'In-process CLI / Python module',
    latencyMs: null,
  },
  backend_api: {
    id: 'backend_api',
    name: 'FastAPI Backend API',
    status: 'DISCONNECTED',
    label: 'Not Connected',
    description: 'API endpoint http://localhost:8000/api/health is currently unreachable.',
    lastChecked: 'Just now',
    details: 'Awaiting implementation and deployment by Overall Lead',
    endpoint: 'http://localhost:8000/api/health',
    latencyMs: null,
  },
  database: {
    id: 'database',
    name: 'Event Storage (SQLite / DB)',
    status: 'DISCONNECTED',
    label: 'Not Connected',
    description: 'Persistent database storage will initialize once the backend service starts.',
    lastChecked: 'Just now',
    details: 'Schema: SQLite event ledger per API_CONTRACT.md',
    endpoint: 'Managed by backend service',
    latencyMs: null,
  },
  dashboard: {
    id: 'dashboard',
    name: 'Frontend Command Dashboard',
    status: 'OPERATIONAL',
    label: 'Operational',
    description: 'React / Vite SPA running cleanly in browser (localhost execution).',
    lastChecked: 'Active',
    details: 'Phase 2 Complete Dashboard Interfaces Active',
    endpoint: 'http://localhost:3000',
    latencyMs: 1,
  },
};
