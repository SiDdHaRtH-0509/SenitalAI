/**
 * SentinelAI Frontend Type Definitions
 * Source of truth: API_CONTRACT.md and ARCHITECTURE.md
 */

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type EventStatus = 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface BoundingBoxObject {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface EventEvidence {
  class_name?: string;
  track_id?: number | null;
  frame_number?: number;
  person_count?: number;
  bbox?: [number, number, number, number];
  bounding_box?: BoundingBoxObject;
  reference_point?: [number, number];
  bottom_center?: [number, number];
  [key: string]: unknown;
}

export interface SecurityEvent {
  event_id: string;
  camera_id: string;
  event_type: string;
  timestamp: string;
  severity: SeverityLevel;
  confidence: number;
  zone_id: string | null;
  description: string;
  evidence: EventEvidence;
  person_count?: number;
  risk_score?: number;
  risk_level?: RiskLevel;
  reasons?: string[];
  recommended_action?: string;
  status: EventStatus;
  is_demo?: boolean;
}

// Global Connection State Enum per Section 6
export type ConnectionState =
  | 'CONNECTED'
  | 'CONNECTING'
  | 'RECONNECTING'
  | 'DISCONNECTED'
  | 'DEGRADED'
  | 'UNKNOWN'
  | 'INTEGRATION_PENDING';

// Camera Stream State Enum per Section 12
export type CameraStreamState =
  | 'STREAM_CONNECTED'
  | 'CONNECTING'
  | 'STREAM_UNAVAILABLE'
  | 'CAMERA_DISCONNECTED'
  | 'STREAM_INTEGRATION_PENDING'
  | 'UNKNOWN';

// Operator Security Notification Item per Section 7
export interface SecurityNotification {
  id: string; // 'notif-' + event_id
  event_id: string;
  event_type: string;
  timestamp: string;
  camera_id: string;
  zone_id?: string | null;
  risk_level?: RiskLevel;
  severity: SeverityLevel;
  message: string;
  read: boolean;
  created_at: string;
  is_demo: boolean;
}

// Real-Time Transport Payload per Section 4
export interface StreamEventPayload {
  type: 'EVENT_BATCH' | 'NEW_EVENT' | 'HEALTH_PING' | 'ERROR';
  events?: SecurityEvent[];
  event?: SecurityEvent;
  stats?: DashboardStatistics;
  timestamp: string;
  message?: string;
  isLive?: boolean;
}

// Small Reusable Transport Interface per Section 4
export interface EventStreamService {
  connect(): void;
  disconnect(): void;
  getConnectionState(): ConnectionState;
  subscribe(callback: (payload: StreamEventPayload) => void): () => void;
  refreshNow(): Promise<void>;
  getLastUpdateTime(): string | null;
}

export type HealthStatusType = 'OPERATIONAL' | 'DEGRADED' | 'DISCONNECTED' | 'INTEGRATION_PENDING';

export interface ServiceHealthItem {
  id: string;
  name: string;
  status: HealthStatusType;
  label: string;
  description: string;
  lastChecked: string;
  details?: string;
  endpoint?: string;
  latencyMs?: number | null;
}

export interface SystemHealthState {
  cv_engine: ServiceHealthItem;
  backend_api: ServiceHealthItem;
  database: ServiceHealthItem;
  dashboard: ServiceHealthItem;
}

export interface DashboardStatistics {
  active_cameras: number;
  total_cameras: number;
  events_today: number;
  restricted_zone_alerts: number;
  critical_alerts: number;
  is_mock: boolean;
}

export interface CameraWorkerStatus {
  camera_id: string;
  is_running: boolean;
  connection_state: string; // 'CONNECTED' | 'CONNECTING' | 'RECONNECTING' | 'STOPPED' | 'FAILED' | 'ERROR'
  fps: number;
  latency_ms: number;
  frames_processed: number;
  events_emitted: number;
  reconnect_count: number;
  last_frame_timestamp?: string | null;
  error_message?: string | null;
  stream_uri_redacted?: string | null;
  is_demo?: boolean;
}

export interface CameraInfo {
  camera_id: string;
  name: string;
  location: string;
  status: 'ONLINE' | 'OFFLINE' | 'DISCONNECTED';
  resolution: string;
  fps: number;
  zone_id: string;
  stream_uri?: string;
  last_ping?: string;
  is_demo?: boolean;
  worker_status?: CameraWorkerStatus;
}

export interface RestrictedZoneInfo {
  zone_id: string;
  name: string;
  camera_id: string;
  status: 'ACTIVE' | 'CALIBRATING' | 'INACTIVE';
  vertices: Array<[number, number]>; // normalized [x, y] in [0, 1]
  reference_strategy: string; // 'bottom_center' | 'center'
  incursions_today: number;
  description: string;
  is_demo?: boolean;
}

export interface ClientSettings {
  table_density: 'comfortable' | 'compact';
  auto_refresh_interval: 0 | 10 | 30 | 60; // 0 = off, seconds
  show_demo_notices: boolean;
  enable_audio_alerts: boolean;
  theme: 'dark-navy';
}

export type NavigationPage = 
  | 'overview'
  | 'monitoring'
  | 'events'
  | 'cameras'
  | 'zones'
  | 'analytics'
  | 'health'
  | 'settings';

export type UserRole = 'ADMIN' | 'OPERATOR' | 'SERVICE';

export interface UserProfile {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login?: string | null;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  token: string | null;
}
