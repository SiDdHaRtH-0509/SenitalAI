/**
 * SentinelAI Frontend API Service
 * 
 * Provides centralized data access layer connecting the dashboard
 * to the backend REST API specified in API_CONTRACT.md.
 * 
 * Gracefully handles disconnected backend state by returning clearly
 * labelled demonstration fixtures without crashing the user interface.
 */

import {
  SecurityEvent,
  DashboardStatistics,
  SystemHealthState,
  CameraInfo,
  RestrictedZoneInfo,
  ClientSettings,
} from '../types';
import {
  DEMO_EVENTS,
  DEMO_STATISTICS,
  INITIAL_SYSTEM_HEALTH,
  DEMO_CAMERAS,
  DEMO_ZONES,
  DEFAULT_CLIENT_SETTINGS,
} from '../data/demoData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const SETTINGS_STORAGE_KEY = 'sentinel_client_settings_v1';

export interface ApiResponse<T> {
  data: T;
  isLive: boolean;
  error?: string;
}

/**
 * Checks connectivity to the backend health endpoint (GET /api/health).
 */
export async function checkBackendHealth(): Promise<{ isConnected: boolean; message: string; latencyMs: number | null }> {
  const startTime = performance.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    const latencyMs = Math.round(performance.now() - startTime);

    if (res.ok) {
      const data = await res.json();
      return {
        isConnected: data.status === 'ok',
        message: data.status === 'ok' ? 'Backend operational' : 'Backend degraded',
        latencyMs,
      };
    }
    return {
      isConnected: false,
      message: `Backend returned status ${res.status}`,
      latencyMs: null,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Connection failed';
    return {
      isConnected: false,
      message: `Backend unreachable (${errorMsg})`,
      latencyMs: null,
    };
  }
}

/**
 * Fetches recent security events (GET /api/events).
 * Falls back to explicitly flagged demo events when backend is not yet running.
 */
export async function fetchRecentEvents(): Promise<ApiResponse<SecurityEvent[]>> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const res = await fetch(`${API_BASE_URL}/api/events`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const events: SecurityEvent[] = await res.json();
      return {
        data: events.map((e) => ({ ...e, is_demo: false })),
        isLive: true,
      };
    }
    return {
      data: DEMO_EVENTS,
      isLive: false,
      error: `Backend error: HTTP ${res.status}. Showing demonstration fixtures.`,
    };
  } catch {
    // Expected before backend service is launched
    return {
      data: DEMO_EVENTS,
      isLive: false,
      error: 'Backend API not running at localhost:8000. Displaying demonstration records.',
    };
  }
}

/**
 * Fetches dashboard KPI statistics (GET /api/stats).
 * Falls back to demo statistics if backend is offline.
 */
export async function fetchDashboardStats(): Promise<ApiResponse<DashboardStatistics>> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const res = await fetch(`${API_BASE_URL}/api/stats`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const stats = await res.json();
      return {
        data: {
          active_cameras: stats.active_cameras ?? 0,
          total_cameras: stats.total_cameras ?? DEMO_CAMERAS.length,
          events_today: stats.total_events ?? 0,
          restricted_zone_alerts: stats.by_risk_level?.HIGH ?? 0,
          critical_alerts: stats.by_risk_level?.CRITICAL ?? 0,
          is_mock: false,
        },
        isLive: true,
      };
    }
    return {
      data: DEMO_STATISTICS,
      isLive: false,
      error: 'Backend stats unavailable; showing demonstration counts.',
    };
  } catch {
    return {
      data: DEMO_STATISTICS,
      isLive: false,
      error: 'Backend offline; displaying demonstration statistics.',
    };
  }
}

/**
 * Fetches camera inventory.
 */
export async function fetchCameras(): Promise<ApiResponse<CameraInfo[]>> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${API_BASE_URL}/api/cameras`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data: CameraInfo[] = await res.json();
      return { data, isLive: true };
    }
    return { data: DEMO_CAMERAS, isLive: false, error: 'Cameras endpoint not found. Using demo inventory.' };
  } catch {
    return { data: DEMO_CAMERAS, isLive: false };
  }
}

/**
 * Fetches restricted zone boundaries.
 */
export async function fetchRestrictedZones(): Promise<ApiResponse<RestrictedZoneInfo[]>> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${API_BASE_URL}/api/zones`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data: RestrictedZoneInfo[] = await res.json();
      return { data, isLive: true };
    }
    return { data: DEMO_ZONES, isLive: false, error: 'Zones endpoint not found. Using demo boundaries.' };
  } catch {
    return { data: DEMO_ZONES, isLive: false };
  }
}

/**
 * Retrieves the current health state across platform subsystems.
 */
export async function fetchSystemHealth(): Promise<SystemHealthState> {
  const backendCheck = await checkBackendHealth();

  return {
    ...INITIAL_SYSTEM_HEALTH,
    backend_api: {
      ...INITIAL_SYSTEM_HEALTH.backend_api,
      status: backendCheck.isConnected ? 'OPERATIONAL' : 'DISCONNECTED',
      label: backendCheck.isConnected ? 'Operational' : 'Not Connected',
      description: backendCheck.isConnected
        ? 'FastAPI service connected and responding on localhost:8000'
        : 'API service at http://localhost:8000/api/health is offline.',
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: backendCheck.latencyMs,
    },
    database: {
      ...INITIAL_SYSTEM_HEALTH.database,
      status: backendCheck.isConnected ? 'OPERATIONAL' : 'DISCONNECTED',
      label: backendCheck.isConnected ? 'Operational' : 'Not Connected',
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: backendCheck.isConnected ? 2 : null,
    },
    dashboard: {
      ...INITIAL_SYSTEM_HEALTH.dashboard,
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: 1,
    },
  };
}

/**
 * Sends event status update if agreed endpoint is available.
 */
export async function updateEventStatus(
  eventId: string,
  newStatus: 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED'
): Promise<{ success: boolean; message: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events/${eventId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });

    if (res.ok) {
      return { success: true, message: `Event ${eventId} updated to ${newStatus}` };
    }
    return { success: false, message: `Server returned status ${res.status}` };
  } catch {
    return {
      success: false,
      message: 'Backend is offline; status update cannot be persisted to database.',
    };
  }
}

/**
 * Local Settings Management
 */
export function loadClientSettings(): ClientSettings {
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_CLIENT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch {
    // Fall back to defaults if localStorage is disabled
  }
  return DEFAULT_CLIENT_SETTINGS;
}

export function saveClientSettings(settings: ClientSettings): void {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Silently handle storage quota/permission issues
  }
}
