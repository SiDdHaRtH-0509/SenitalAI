/**
 * SentinelAI Frontend Type Definitions
 * Source of truth: API_CONTRACT.md and ARCHITECTURE.md
 */

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type EventStatus = 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface EventEvidence {
  class_name: string;
  track_id: number | null;
  frame_number: number;
  person_count?: number;
  bbox?: [number, number, number, number];
  reference_point?: [number, number];
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
