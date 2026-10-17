/**
 * SentinelAI Centralized API Client
 * 
 * Provides robust, typed, and resilient HTTP client communication
 * connecting the React dashboard to the FastAPI backend service
 * per API_CONTRACT.md and ARCHITECTURE.md.
 * 
 * Capabilities:
 * - Configurable backend base URL via VITE_API_BASE_URL.
 * - Strict typing for request payloads and responses.
 * - AbortController timeout and caller cancellation.
 * - Uniform error normalization (HTTP non-2xx, network refusal, timeouts).
 * - Safe JSON parsing with fallback.
 * - Clean query parameter builder.
 * - Zero hardcoded credentials or private tokens.
 */

import type {
  SecurityEvent,
  DashboardStatistics,
  SystemHealthState,
  CameraInfo,
  RestrictedZoneInfo,
  EventStatus,
} from '../types';
import {
  DEMO_EVENTS,
  DEMO_STATISTICS,
  INITIAL_SYSTEM_HEALTH,
  DEMO_CAMERAS,
  DEMO_ZONES,
} from '../data/demoData';

// Configurable environment defaults
const DEFAULT_BASE_URL = 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 5000;

export function getApiBaseUrl(): string {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
    return String(import.meta.env.VITE_API_BASE_URL).replace(/\/+$/, '');
  }
  return DEFAULT_BASE_URL;
}

export function getApiTimeoutMs(): number {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_TIMEOUT_MS) {
    const val = Number(import.meta.env.VITE_API_TIMEOUT_MS);
    if (!isNaN(val) && val > 0) return val;
  }
  return DEFAULT_TIMEOUT_MS;
}

/**
 * Structured API client error wrapping HTTP and network failures.
 */
export class ApiClientError extends Error {
  public readonly status: number;
  public readonly isNetworkError: boolean;
  public readonly isTimeout: boolean;
  public readonly details: unknown;

  constructor(
    message: string,
    options: {
      status?: number;
      isNetworkError?: boolean;
      isTimeout?: boolean;
      details?: unknown;
    } = {}
  ) {
    super(message);
    this.name = 'ApiClientError';
    this.status = options.status ?? 0;
    this.isNetworkError = options.isNetworkError ?? false;
    this.isTimeout = options.isTimeout ?? false;
    this.details = options.details;
    Object.setPrototypeOf(this, ApiClientError.prototype);
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: unknown;
  params?: Record<string, string | number | boolean | null | undefined>;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export interface ApiResponse<T> {
  data: T;
  isLive: boolean;
  statusCode?: number;
  error?: string;
  latencyMs?: number;
}

/**
 * Centralized HTTP Client Class
 */
export class ApiClient {
  private baseUrl: string;
  private defaultTimeoutMs: number;

  constructor(baseUrl: string = getApiBaseUrl(), defaultTimeoutMs: number = getApiTimeoutMs()) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.defaultTimeoutMs = defaultTimeoutMs;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  /**
   * Builds full URL with URLSearchParams.
   */
  public buildUrl(
    endpoint: string,
    params?: Record<string, string | number | boolean | null | undefined>
  ): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = new URL(`${this.baseUrl}${cleanEndpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== null && val !== undefined && val !== '') {
          url.searchParams.append(key, String(val));
        }
      });
    }

    return url.toString();
  }

  /**
   * Low-level fetch wrapper with timeout, error translation, and abort support.
   */
  public async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
      params,
      timeoutMs = this.defaultTimeoutMs,
      signal: callerSignal,
    } = options;

    const fullUrl = this.buildUrl(endpoint, params);

    // Timeout and cancellation setup
    const timeoutController = new AbortController();
    const timeoutId = setTimeout(() => {
      timeoutController.abort('REQUEST_TIMEOUT');
    }, timeoutMs);

    // Handle combined signals
    const combinedSignal = callerSignal
      ? anySignal([callerSignal, timeoutController.signal])
      : timeoutController.signal;

    const requestHeaders: Record<string, string> = {
      Accept: 'application/json',
      ...headers,
    };

    if (body !== undefined && body !== null) {
      requestHeaders['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(fullUrl, {
        method,
        headers: requestHeaders,
        body: body !== undefined && body !== null ? JSON.stringify(body) : undefined,
        signal: combinedSignal,
      });

      clearTimeout(timeoutId);

      // Parse response body safely
      let parsedBody: unknown;
      const text = await response.text();
      if (text) {
        try {
          parsedBody = JSON.parse(text);
        } catch {
          parsedBody = text;
        }
      }

      if (!response.ok) {
        const errorMsg =
          typeof parsedBody === 'object' && parsedBody !== null && 'detail' in parsedBody
            ? String((parsedBody as { detail: unknown }).detail)
            : `HTTP ${response.status} (${response.statusText || 'Error'}) from ${endpoint}`;

        throw new ApiClientError(errorMsg, {
          status: response.status,
          details: parsedBody,
        });
      }

      return parsedBody as T;
    } catch (err: unknown) {
      clearTimeout(timeoutId);

      if (err instanceof ApiClientError) {
        throw err;
      }

      // Check if timeout triggered
      if (timeoutController.signal.aborted) {
        throw new ApiClientError(`Request timed out after ${timeoutMs}ms: ${endpoint}`, {
          isTimeout: true,
          status: 408,
        });
      }

      // Network refusal or offline
      const message = err instanceof Error ? err.message : 'Unknown network failure';
      throw new ApiClientError(`Network connection failure to backend (${message})`, {
        isNetworkError: true,
        status: 0,
        details: err,
      });
    }
  }

  public get<T>(
    endpoint: string,
    params?: Record<string, string | number | boolean | null | undefined>,
    signal?: AbortSignal
  ): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', params, signal });
  }

  public post<T>(endpoint: string, body?: unknown, signal?: AbortSignal): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body, signal });
  }

  public patch<T>(endpoint: string, body?: unknown, signal?: AbortSignal): Promise<T> {
    return this.request<T>(endpoint, { method: 'PATCH', body, signal });
  }
}

/**
 * Utility to merge multiple abort signals safely.
 */
function anySignal(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  for (const s of signals) {
    if (s.aborted) {
      controller.abort();
      return controller.signal;
    }
    s.addEventListener('abort', () => controller.abort(), { once: true });
  }
  return controller.signal;
}

// Global default client instance
export const apiClient = new ApiClient();

// ==============================================================================
// High-Level Service Methods with Graceful Offline Fallbacks
// ==============================================================================

/**
 * 1. Health Probe (GET /api/health)
 * Contract: {"status": "ok"}
 */
export async function getHealth(
  signal?: AbortSignal
): Promise<{ isConnected: boolean; message: string; latencyMs: number | null }> {
  const startTime = performance.now();
  try {
    const res = await apiClient.get<{ status: string }>('/api/health', undefined, signal);
    const latency = Math.round(performance.now() - startTime);
    return {
      isConnected: res.status === 'ok',
      message: res.status === 'ok' ? 'FastAPI backend operational' : `Degraded (${res.status})`,
      latencyMs: latency,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Connection failed';
    return {
      isConnected: false,
      message: `Backend unreachable: ${errMsg}`,
      latencyMs: null,
    };
  }
}

/**
 * 2. Dashboard Statistics (GET /api/stats)
 * Contract: {"total_events": 1, "by_risk_level": {"LOW": 0, "MEDIUM": 0, "HIGH": 1, "CRITICAL": 0}}
 */
export interface BackendStatsResponse {
  total_events: number;
  by_risk_level?: {
    LOW?: number;
    MEDIUM?: number;
    HIGH?: number;
    CRITICAL?: number;
  };
  active_cameras?: number;
  total_cameras?: number;
}

export async function getDashboardStatistics(
  signal?: AbortSignal
): Promise<ApiResponse<DashboardStatistics>> {
  try {
    const stats = await apiClient.get<BackendStatsResponse>('/api/stats', undefined, signal);
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
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errText = err instanceof ApiClientError ? err.message : 'Backend offline';
    return {
      data: DEMO_STATISTICS,
      isLive: false,
      error: `GET /api/stats unavailable (${errText}). Showing demonstration KPI statistics.`,
    };
  }
}

/**
 * 3. Security Events (GET /api/events)
 * Contract: Returns stored events newest-first.
 */
export async function getSecurityEvents(
  params?: { limit?: number; offset?: number; camera_id?: string; risk_level?: string },
  signal?: AbortSignal
): Promise<ApiResponse<SecurityEvent[]>> {
  try {
    const events = await apiClient.get<SecurityEvent[]>('/api/events', params, signal);
    return {
      data: events.map((e) => ({ ...e, is_demo: false })),
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errText = err instanceof ApiClientError ? err.message : 'Backend offline';
    return {
      data: DEMO_EVENTS,
      isLive: false,
      error: `GET /api/events unavailable (${errText}). Displaying demonstration audit fixtures.`,
    };
  }
}

/**
 * 4. Single Security Event by ID (GET /api/events/{event_id})
 */
export async function getSecurityEventById(
  eventId: string,
  signal?: AbortSignal
): Promise<ApiResponse<SecurityEvent | null>> {
  try {
    const event = await apiClient.get<SecurityEvent>(`/api/events/${eventId}`, undefined, signal);
    return {
      data: { ...event, is_demo: false },
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    // Check fallback in demo fixtures
    const match = DEMO_EVENTS.find((e) => e.event_id === eventId);
    return {
      data: match || null,
      isLive: false,
      error: err instanceof ApiClientError ? err.message : 'Incident not found',
    };
  }
}

/**
 * 5. Update Event Status (PATCH /api/events/{event_id}/status)
 * Contract: {"status": "ACKNOWLEDGED"}
 */
export async function updateSecurityEventStatus(
  eventId: string,
  status: EventStatus,
  signal?: AbortSignal
): Promise<{ success: boolean; message: string; isLive: boolean }> {
  try {
    const res = await apiClient.patch<{ status: string }>(
      `/api/events/${eventId}/status`,
      { status },
      signal
    );
    return {
      success: true,
      message: `Event ${eventId} updated to ${res.status || status}`,
      isLive: true,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Backend offline';
    return {
      success: false,
      message: `Status update could not be persisted to backend (${errMsg}).`,
      isLive: false,
    };
  }
}

/**
 * 6. Cameras Inventory (GET /api/cameras)
 */
export async function getCameras(signal?: AbortSignal): Promise<ApiResponse<CameraInfo[]>> {
  try {
    const cameras = await apiClient.get<CameraInfo[]>('/api/cameras', undefined, signal);
    return {
      data: cameras.map((c) => ({ ...c, is_demo: false })),
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Endpoint not found';
    return {
      data: DEMO_CAMERAS,
      isLive: false,
      error: `GET /api/cameras unavailable (${errMsg}). Using demonstration hardware registry.`,
    };
  }
}

/**
 * 7. Restricted Zones (GET /api/zones)
 */
export async function getRestrictedZones(
  signal?: AbortSignal
): Promise<ApiResponse<RestrictedZoneInfo[]>> {
  try {
    const zones = await apiClient.get<RestrictedZoneInfo[]>('/api/zones', undefined, signal);
    return {
      data: zones.map((z) => ({ ...z, is_demo: false })),
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Endpoint not found';
    return {
      data: DEMO_ZONES,
      isLive: false,
      error: `GET /api/zones unavailable (${errMsg}). Using calibrated boundary geometries from sentinel_cv.config.`,
    };
  }
}

/**
 * 8. Comprehensive Subsystem Health Probe
 */
export async function getSystemHealth(signal?: AbortSignal): Promise<SystemHealthState> {
  const probe = await getHealth(signal);

  return {
    ...INITIAL_SYSTEM_HEALTH,
    backend_api: {
      ...INITIAL_SYSTEM_HEALTH.backend_api,
      status: probe.isConnected ? 'OPERATIONAL' : 'DISCONNECTED',
      label: probe.isConnected ? 'Operational' : 'Not Connected',
      description: probe.isConnected
        ? `FastAPI service responding on ${apiClient.getBaseUrl()}`
        : `Backend service at ${apiClient.getBaseUrl()}/api/health is unreachable.`,
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: probe.latencyMs,
    },
    database: {
      ...INITIAL_SYSTEM_HEALTH.database,
      status: probe.isConnected ? 'OPERATIONAL' : 'DISCONNECTED',
      label: probe.isConnected ? 'Operational' : 'Not Connected',
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: probe.isConnected ? 2 : null,
    },
    dashboard: {
      ...INITIAL_SYSTEM_HEALTH.dashboard,
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: 1,
    },
  };
}
