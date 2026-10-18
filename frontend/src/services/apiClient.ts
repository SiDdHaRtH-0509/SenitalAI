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
  CameraWorkerStatus,
  RestrictedZoneInfo,
  EventStatus,
  UserProfile,
  UserRole,
} from '../types';
import {
  DEMO_EVENTS,
  DEMO_STATISTICS,
  INITIAL_SYSTEM_HEALTH,
  DEMO_CAMERAS,
  DEMO_ZONES,
  DEMO_OPERATOR_USER,
} from '../data/demoData';

// Configurable environment defaults
const DEFAULT_BASE_URL = 'http://127.0.0.1:8001';
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
  private authToken: string | null = null;
  private csrfToken: string | null = null;

  constructor(baseUrl: string = getApiBaseUrl(), defaultTimeoutMs: number = getApiTimeoutMs()) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.defaultTimeoutMs = defaultTimeoutMs;
    // Security Hardening: Ensure sensitive JWT session tokens are never stored in or loaded from localStorage
    if (typeof window !== 'undefined' && window.localStorage) {
      try {
        window.localStorage.removeItem('sentinel_auth_token');
      } catch {
        // ignore storage errors
      }
    }
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  public setAuthToken(token: string | null, csrfToken: string | null = null): void {
    this.authToken = token;
    this.csrfToken = csrfToken;
    if (!token && typeof window !== 'undefined' && window.localStorage) {
      try {
        window.localStorage.removeItem('sentinel_auth_token');
        window.localStorage.removeItem('sentinel_auth_user');
      } catch {
        // ignore storage errors
      }
    }
  }

  public getAuthToken(): string | null {
    return this.authToken;
  }

  public getCsrfToken(): string | null {
    if (this.csrfToken) {
      return this.csrfToken;
    }
    if (typeof document !== 'undefined' && document.cookie) {
      const match = document.cookie.match(/(?:^|;\s*)sentinel_csrf_token=([^;]+)/);
      if (match) {
        return decodeURIComponent(match[1]);
      }
    }
    return null;
  }

  public isAuthenticated(): boolean {
    return Boolean(this.authToken);
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

    if (this.authToken) {
      requestHeaders['Authorization'] = `Bearer ${this.authToken}`;
    }

    const isStateChanging = ['POST', 'PATCH', 'PUT', 'DELETE'].includes(method.toUpperCase());
    if (isStateChanging) {
      const csrf = this.getCsrfToken();
      if (csrf) {
        requestHeaders['X-CSRF-Token'] = csrf;
      }
    }

    if (body !== undefined && body !== null) {
      requestHeaders['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(fullUrl, {
        method,
        headers: requestHeaders,
        body: body !== undefined && body !== null ? JSON.stringify(body) : undefined,
        signal: combinedSignal,
        credentials: 'include',
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
    const apiError = err instanceof ApiClientError ? err : null;
    const errText = apiError?.message ?? 'Unexpected backend error';

    // Authentication/authorization failures mean the API responded; they do not
    // mean the backend is offline. Avoid presenting synthetic records as real data.
    if (apiError?.status === 401 || apiError?.status === 403) {
      return {
        data: [],
        isLive: false,
        statusCode: apiError.status,
        error: `Live events require an authorized session (${apiError.status}). Sign in with an account permitted to view events.`,
      };
    }

    return {
      data: DEMO_EVENTS.map((event) => ({ ...event, is_demo: true })),
      isLive: false,
      statusCode: apiError?.status,
      error: `GET /api/events unavailable (${errText}). Showing clearly marked demonstration fixtures; these are not live incidents.`,
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
 * 6.1 Start Camera Processing Worker (POST /api/cameras/{camera_id}/start)
 */
export async function startCameraWorker(
  cameraId: string,
  replayMode: boolean = false,
  signal?: AbortSignal
): Promise<ApiResponse<CameraWorkerStatus>> {
  try {
    const status = await apiClient.post<CameraWorkerStatus>(
      `/api/cameras/${cameraId}/start`,
      { replay_mode: replayMode },
      signal
    );
    return {
      data: status,
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Worker start failed';
    return {
      data: {
        camera_id: cameraId,
        is_running: false,
        connection_state: 'FAILED',
        fps: 0,
        latency_ms: 0,
        frames_processed: 0,
        events_emitted: 0,
        reconnect_count: 0,
        error_message: errMsg,
      },
      isLive: false,
      error: errMsg,
    };
  }
}

/**
 * 6.2 Stop Camera Processing Worker (POST /api/cameras/{camera_id}/stop)
 */
export async function stopCameraWorker(
  cameraId: string,
  signal?: AbortSignal
): Promise<ApiResponse<CameraWorkerStatus>> {
  try {
    const status = await apiClient.post<CameraWorkerStatus>(
      `/api/cameras/${cameraId}/stop`,
      {},
      signal
    );
    return {
      data: status,
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Worker stop failed';
    return {
      data: {
        camera_id: cameraId,
        is_running: false,
        connection_state: 'STOPPED',
        fps: 0,
        latency_ms: 0,
        frames_processed: 0,
        events_emitted: 0,
        reconnect_count: 0,
        error_message: errMsg,
      },
      isLive: false,
      error: errMsg,
    };
  }
}

/**
 * 6.3 Get Camera Worker Status (GET /api/cameras/{camera_id}/status)
 */
export async function getCameraWorkerStatus(
  cameraId: string,
  signal?: AbortSignal
): Promise<ApiResponse<CameraWorkerStatus>> {
  try {
    const status = await apiClient.get<CameraWorkerStatus>(
      `/api/cameras/${cameraId}/status`,
      undefined,
      signal
    );
    return {
      data: status,
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Status query failed';
    return {
      data: {
        camera_id: cameraId,
        is_running: false,
        connection_state: 'STOPPED',
        fps: 0,
        latency_ms: 0,
        frames_processed: 0,
        events_emitted: 0,
        reconnect_count: 0,
        error_message: errMsg,
      },
      isLive: false,
      error: errMsg,
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
      status: 'INTEGRATION_PENDING',
      label: 'Not Independently Verified',
      description: 'The API heartbeat does not test database connectivity. Database status remains unverified until a dedicated database health probe is available.',
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: null,
    },
    dashboard: {
      ...INITIAL_SYSTEM_HEALTH.dashboard,
      lastChecked: new Date().toLocaleTimeString(),
      latencyMs: 1,
    },
  };
}

/**
 * 9. User Authentication (POST /api/auth/login)
 */
export async function loginUser(
  username: string,
  password: string
): Promise<ApiResponse<{ token: string; user: UserProfile }>> {
  try {
    const tokenResponse = await apiClient.post<{
      access_token: string;
      token_type: string;
      role: UserRole;
      username: string;
      expires_in_seconds: number;
      csrf_token?: string;
    }>('/api/auth/login', { username, password });

    apiClient.setAuthToken(tokenResponse.access_token, tokenResponse.csrf_token || null);

    // Fetch user profile or synthesize from login response
    let profile: UserProfile;
    try {
      profile = await apiClient.get<UserProfile>('/api/auth/me');
    } catch {
      profile = {
        id: tokenResponse.role === 'ADMIN' ? 1 : 2,
        username: tokenResponse.username,
        role: tokenResponse.role,
        full_name: tokenResponse.role === 'ADMIN' ? 'System Administrator' : 'Border Security Officer',
        is_active: true,
        created_at: new Date().toISOString(),
      };
    }

    if (typeof window !== 'undefined' && window.localStorage) {
      try {
        window.localStorage.setItem('sentinel_auth_user', JSON.stringify(profile));
      } catch {
        // ignore storage errors
      }
    }

    return {
      data: { token: tokenResponse.access_token, user: profile },
      isLive: true,
      statusCode: 200,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Authentication failed';
    throw new ApiClientError(errMsg, {
      status: err instanceof ApiClientError ? err.status : 401,
      details: err,
    });
  }
}

/**
 * 9.1 User Registration (POST /api/auth/register)
 */
export async function registerUser(
  username: string,
  password: string,
  fullName?: string,
  email?: string
): Promise<ApiResponse<UserProfile>> {
  try {
    const user = await apiClient.post<UserProfile>('/api/auth/register', {
      username: username.trim().toLowerCase(),
      password,
      full_name: fullName?.trim() || null,
      email: email?.trim() || null,
    });
    return {
      data: user,
      isLive: true,
      statusCode: 201,
    };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Registration failed';
    throw new ApiClientError(errMsg, {
      status: err instanceof ApiClientError ? err.status : 400,
      details: err,
    });
  }
}

/**
 * 10. Logout (POST /api/auth/logout or local token clearance)
 */
export async function logoutUser(): Promise<void> {
  try {
    if (apiClient.isAuthenticated()) {
      await apiClient.post('/api/auth/logout', {});
    }
  } catch {
    // Ignore network errors on logout
  } finally {
    apiClient.setAuthToken(null, null);
  }
}

/**
 * 11. Current User Profile (GET /api/auth/me)
 */
export async function getCurrentUserProfile(
  signal?: AbortSignal
): Promise<ApiResponse<UserProfile>> {
  if (!apiClient.isAuthenticated()) {
    if (typeof window !== 'undefined' && window.localStorage) {
      const cached = window.localStorage.getItem('sentinel_auth_user');
      if (cached) {
        try {
          return { data: JSON.parse(cached), isLive: false, statusCode: 200 };
        } catch {
          // ignore parsing error
        }
      }
    }
    return {
      data: DEMO_OPERATOR_USER,
      isLive: false,
      error: 'Unauthenticated. Using local operator context.',
    };
  }

  try {
    const profile = await apiClient.get<UserProfile>('/api/auth/me', undefined, signal);
    return { data: profile, isLive: true, statusCode: 200 };
  } catch (err: unknown) {
    const errMsg = err instanceof ApiClientError ? err.message : 'Failed to retrieve profile';
    return {
      data: DEMO_OPERATOR_USER,
      isLive: false,
      error: `Auth verification unavailable (${errMsg}). Using local operator context.`,
    };
  }
}

