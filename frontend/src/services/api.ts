/**
 * SentinelAI Frontend API Service
 * 
 * Provides centralized data access layer connecting the dashboard
 * to the backend REST API specified in API_CONTRACT.md.
 * 
 * Gracefully handles disconnected backend state by returning clearly
 * labelled demonstration fixtures without crashing the user interface.
 */

import { SecurityEvent, DashboardStatistics, SystemHealthState } from '../types';
import { DEMO_EVENTS, DEMO_STATISTICS, INITIAL_SYSTEM_HEALTH } from '../data/demoData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data: T;
  isLive: boolean;
  error?: string;
}

/**
 * Checks connectivity to the backend health endpoint (GET /api/health).
 */
export async function checkBackendHealth(): Promise<{ isConnected: boolean; message: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      return {
        isConnected: data.status === 'ok',
        message: data.status === 'ok' ? 'Backend operational' : 'Backend degraded',
      };
    }
    return {
      isConnected: false,
      message: `Backend returned status ${res.status}`,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'Connection failed';
    return {
      isConnected: false,
      message: `Backend unreachable (${errorMsg})`,
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
    // Expected in Phase 1 before backend service is launched
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
          total_cameras: stats.total_cameras ?? 4,
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
    },
    database: {
      ...INITIAL_SYSTEM_HEALTH.database,
      status: backendCheck.isConnected ? 'OPERATIONAL' : 'DISCONNECTED',
      label: backendCheck.isConnected ? 'Operational' : 'Not Connected',
      lastChecked: new Date().toLocaleTimeString(),
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
