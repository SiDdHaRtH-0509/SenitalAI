/**
 * SentinelAI Frontend API Client Integration & Contract Tests
 * 
 * Verifies all 12 Phase 3 contract test scenarios:
 * 1. Successful API response parsing (health, stats, events)
 * 2. Non-2xx HTTP response handling (404, 500 error translation)
 * 3. Network failure handling (fetch rejection, offline fallback)
 * 4. Request timeout handling (AbortController timeout, status 408)
 * 5. Invalid/malformed response handling (plain text, non-JSON)
 * 6. Empty event list handling (clean empty array without crash)
 * 7. Missing optional fields in event payloads (risk_score, reasons, etc.)
 * 8. Client-side filtering and sorting logic
 * 9. Loading and offline fallback states (demo fixtures, isLive: false)
 * 10. Error message normalization and user-friendly translation
 * 11. Status update persistence via PATCH /api/events/{id}/status
 * 12. Configurable base URL and query parameter serialization
 */

import { test, describe, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  ApiClient,
  ApiClientError,
  getHealth,
  getDashboardStatistics,
  getSecurityEvents,
  getSecurityEventById,
  updateSecurityEventStatus,
  getCameras,
  getRestrictedZones,
  getSystemHealth,
} from '../src/services/apiClient';
import type { SecurityEvent } from '../src/types';

describe('SentinelAI ApiClient & Contract Integration Suite', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // ============================================================================
  // 1. Successful API Response Handling
  // ============================================================================
  test('1. Successful API response - getHealth(), getDashboardStatistics(), and getSecurityEvents()', async () => {
    const mockHealth = { status: 'ok' };
    const mockStats = {
      total_events: 14,
      by_risk_level: { LOW: 2, MEDIUM: 4, HIGH: 6, CRITICAL: 2 },
      active_cameras: 4,
      total_cameras: 4,
    };
    const mockEvents = [
      {
        event_id: 'EVT-TEST-001',
        timestamp: '2026-10-17T12:00:00Z',
        camera_id: 'CAM-01',
        risk_level: 'HIGH',
        risk_score: 82,
        zone_id: 'ZONE-A',
        reasons: ['Person detected inside restricted polygon'],
        recommended_action: 'Dispatch patrol to Sector 1',
        person_count: 1,
        status: 'PENDING',
      },
    ];

    globalThis.fetch = async (url: string | URL | Request) => {
      const urlStr = url.toString();
      if (urlStr.includes('/api/health')) {
        return new Response(JSON.stringify(mockHealth), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      if (urlStr.includes('/api/stats')) {
        return new Response(JSON.stringify(mockStats), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      if (urlStr.includes('/api/events')) {
        return new Response(JSON.stringify(mockEvents), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response('Not Found', { status: 404 });
    };

    // Health
    const healthResult = await getHealth();
    assert.strictEqual(healthResult.isConnected, true);
    assert.match(healthResult.message, /operational/i);
    assert.ok(typeof healthResult.latencyMs === 'number');

    // Stats
    const statsResult = await getDashboardStatistics();
    assert.strictEqual(statsResult.isLive, true);
    assert.strictEqual(statsResult.statusCode, 200);
    assert.strictEqual(statsResult.data.events_today, 14);
    assert.strictEqual(statsResult.data.restricted_zone_alerts, 6);
    assert.strictEqual(statsResult.data.critical_alerts, 2);

    // Events
    const eventsResult = await getSecurityEvents();
    assert.strictEqual(eventsResult.isLive, true);
    assert.strictEqual(eventsResult.data.length, 1);
    assert.strictEqual(eventsResult.data[0].event_id, 'EVT-TEST-001');
    assert.strictEqual(eventsResult.data[0].is_demo, false);
  });

  // ============================================================================
  // 2. Non-2xx HTTP Response Handling
  // ============================================================================
  test('2. Non-2xx HTTP response - wraps 404 and 500 in ApiClientError with status code and detail', async () => {
    const client = new ApiClient('http://localhost:8000');

    // Mock 404 Not Found
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ detail: 'Incident EVT-999 not located' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });

    await assert.rejects(
      async () => {
        await client.get('/api/events/EVT-999');
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual(err.status, 404);
        assert.match(err.message, /EVT-999 not located/);
        return true;
      }
    );

    // Mock 500 Internal Server Error
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ detail: 'Database connection pool exhausted' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });

    await assert.rejects(
      async () => {
        await client.get('/api/stats');
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual(err.status, 500);
        assert.match(err.message, /Database connection pool exhausted/);
        return true;
      }
    );
  });

  // ============================================================================
  // 3. Network Failure Handling & Flagging
  // ============================================================================
  test('3. Network failure handling - network refusal flags isNetworkError: true and triggers offline fallback', async () => {
    const client = new ApiClient('http://localhost:8000');

    // Simulate network connection refused
    globalThis.fetch = async () => {
      throw new TypeError('Failed to fetch: Connection refused (ECONNREFUSED)');
    };

    await assert.rejects(
      async () => {
        await client.get('/api/health');
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual(err.isNetworkError, true);
        assert.strictEqual(err.status, 0);
        assert.match(err.message, /Network connection failure/);
        return true;
      }
    );

    // High-level wrapper gracefully falls back
    const healthResult = await getHealth();
    assert.strictEqual(healthResult.isConnected, false);
    assert.strictEqual(healthResult.latencyMs, null);
    assert.match(healthResult.message, /Backend unreachable/);

    const statsResult = await getDashboardStatistics();
    assert.strictEqual(statsResult.isLive, false);
    assert.ok(statsResult.data.events_today > 0); // Demo data returned
    assert.match(statsResult.error || '', /unavailable/);
  });

  // ============================================================================
  // 4. Request Timeout Handling
  // ============================================================================
  test('4. Request timeout handling - aborts slow request and flags isTimeout: true with status 408', async () => {
    const client = new ApiClient('http://localhost:8000', 50); // 50ms timeout

    globalThis.fetch = async (_url: string | URL | Request, init?: RequestInit) => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          resolve(new Response('{}', { status: 200 }));
        }, 300);

        if (init?.signal) {
          init.signal.addEventListener('abort', () => {
            clearTimeout(timeout);
            const err = new Error('The operation was aborted');
            err.name = 'AbortError';
            reject(err);
          });
        }
      });
    };

    await assert.rejects(
      async () => {
        await client.get('/api/events');
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual(err.isTimeout, true);
        assert.strictEqual(err.status, 408);
        assert.match(err.message, /timed out after 50ms/);
        return true;
      }
    );
  });

  // ============================================================================
  // 5. Invalid / Non-JSON Response Handling
  // ============================================================================
  test('5. Invalid response handling - safely extracts plain text HTML error page without syntax crashes', async () => {
    const client = new ApiClient('http://localhost:8000');

    // Simulate 502 Bad Gateway with HTML text body
    globalThis.fetch = async () =>
      new Response('<html><body>502 Bad Gateway: Nginx upstream error</body></html>', {
        status: 502,
        headers: { 'Content-Type': 'text/html' },
      });

    await assert.rejects(
      async () => {
        await client.get('/api/events');
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual(err.status, 502);
        assert.match(err.message, /HTTP 502/);
        assert.match(String(err.details), /502 Bad Gateway/);
        return true;
      }
    );
  });

  // ============================================================================
  // 6. Empty Event List Handling
  // ============================================================================
  test('6. Empty event list handling - returns empty array cleanly without crashing UI contracts', async () => {
    globalThis.fetch = async () =>
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });

    const res = await getSecurityEvents();
    assert.strictEqual(res.isLive, true);
    assert.strictEqual(res.statusCode, 200);
    assert.deepStrictEqual(res.data, []);
    assert.strictEqual(res.error, undefined);
  });

  // ============================================================================
  // 7. Missing Optional Fields Handling
  // ============================================================================
  test('7. Missing optional fields handling - gracefully tolerates partial event records', async () => {
    const minimalEvent = {
      event_id: 'EVT-MINIMAL-01',
      timestamp: '2026-10-17T14:15:00Z',
      camera_id: 'CAM-02',
      risk_level: 'MEDIUM',
      // Missing risk_score, reasons, recommended_action, person_count
    };

    globalThis.fetch = async () =>
      new Response(JSON.stringify([minimalEvent]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });

    const res = await getSecurityEvents();
    assert.strictEqual(res.isLive, true);
    assert.strictEqual(res.data.length, 1);
    const event = res.data[0];
    assert.strictEqual(event.event_id, 'EVT-MINIMAL-01');
    assert.strictEqual(event.risk_score, undefined);
    assert.strictEqual(event.reasons, undefined);
    assert.strictEqual(event.recommended_action, undefined);
    assert.strictEqual(event.is_demo, false);
  });

  // ============================================================================
  // 8. Event Filtering and Sorting Logic
  // ============================================================================
  test('8. Event filtering and sorting logic - filters by status, risk_level, and sorts by timestamp', () => {
    const testEvents: SecurityEvent[] = [
      {
        event_id: 'EVT-A',
        timestamp: '2026-10-17T08:00:00Z',
        camera_id: 'CAM-01',
        risk_level: 'LOW',
        status: 'RESOLVED',
      },
      {
        event_id: 'EVT-B',
        timestamp: '2026-10-17T10:00:00Z',
        camera_id: 'CAM-02',
        risk_level: 'CRITICAL',
        status: 'PENDING',
      },
      {
        event_id: 'EVT-C',
        timestamp: '2026-10-17T09:00:00Z',
        camera_id: 'CAM-01',
        risk_level: 'HIGH',
        status: 'ACKNOWLEDGED',
      },
    ];

    // Filter by risk level
    const criticalEvents = testEvents.filter((e) => e.risk_level === 'CRITICAL');
    assert.strictEqual(criticalEvents.length, 1);
    assert.strictEqual(criticalEvents[0].event_id, 'EVT-B');

    // Filter by camera
    const cam1Events = testEvents.filter((e) => e.camera_id === 'CAM-01');
    assert.strictEqual(cam1Events.length, 2);

    // Filter by status
    const pendingEvents = testEvents.filter((e) => e.status === 'PENDING');
    assert.strictEqual(pendingEvents.length, 1);

    // Sort descending by timestamp (newest first)
    const sortedDesc = [...testEvents].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    assert.strictEqual(sortedDesc[0].event_id, 'EVT-B');
    assert.strictEqual(sortedDesc[1].event_id, 'EVT-C');
    assert.strictEqual(sortedDesc[2].event_id, 'EVT-A');

    // Sort ascending by timestamp (oldest first)
    const sortedAsc = [...testEvents].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
    assert.strictEqual(sortedAsc[0].event_id, 'EVT-A');
    assert.strictEqual(sortedAsc[2].event_id, 'EVT-B');
  });

  // ============================================================================
  // 9. Loading and Offline States (Graceful Fallback)
  // ============================================================================
  test('9. Loading and offline states - safely provides demo fixtures and marks isLive: false', async () => {
    // When fetch fails completely
    globalThis.fetch = async () => {
      throw new Error('Failed to connect to backend server on port 8000');
    };

    const [eventsRes, statsRes, camerasRes, zonesRes, healthRes] = await Promise.all([
      getSecurityEvents(),
      getDashboardStatistics(),
      getCameras(),
      getRestrictedZones(),
      getSystemHealth(),
    ]);

    // Events fallback
    assert.strictEqual(eventsRes.isLive, false);
    assert.ok(eventsRes.data.length > 0);
    assert.match(eventsRes.error || '', /Displaying demonstration audit fixtures/);

    // Stats fallback
    assert.strictEqual(statsRes.isLive, false);
    assert.strictEqual(statsRes.data.is_mock, true);

    // Cameras fallback
    assert.strictEqual(camerasRes.isLive, false);
    assert.ok(camerasRes.data.length >= 4);

    // Zones fallback
    assert.strictEqual(zonesRes.isLive, false);
    assert.ok(zonesRes.data.length >= 3);

    // Health fallback
    assert.strictEqual(healthRes.backend_api.status, 'DISCONNECTED');
    assert.match(healthRes.backend_api.description, /unreachable/);
  });

  // ============================================================================
  // 10. Error State Translation
  // ============================================================================
  test('10. Error state translation - extracts detail or provides human-readable message', async () => {
    const client = new ApiClient('http://localhost:8000');

    // Structured backend error
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ detail: 'Token signature invalid or expired' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });

    try {
      await client.get('/api/secure-endpoint');
      assert.fail('Should have thrown ApiClientError');
    } catch (err: unknown) {
      assert.ok(err instanceof ApiClientError);
      assert.strictEqual(err.status, 401);
      assert.strictEqual(err.message, 'Token signature invalid or expired');
    }

    // Generic HTTP error without detail field
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ error: 'Service Unavailable' }), {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' },
      });

    try {
      await client.get('/api/heavy-job');
      assert.fail('Should have thrown ApiClientError');
    } catch (err: unknown) {
      assert.ok(err instanceof ApiClientError);
      assert.strictEqual(err.status, 503);
      assert.match(err.message, /HTTP 503 \(Service Unavailable\)/);
    }
  });

  // ============================================================================
  // 11. Status Update via PATCH /api/events/{id}/status
  // ============================================================================
  test('11. Status update persistence - executes PATCH and captures live or offline status', async () => {
    let capturedMethod = '';
    let capturedBody = '';

    // Success path
    globalThis.fetch = async (url: string | URL | Request, init?: RequestInit) => {
      capturedMethod = init?.method || '';
      capturedBody = String(init?.body || '');
      return new Response(JSON.stringify({ status: 'ACKNOWLEDGED' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const successRes = await updateSecurityEventStatus('EVT-001', 'ACKNOWLEDGED');
    assert.strictEqual(successRes.success, true);
    assert.strictEqual(successRes.isLive, true);
    assert.strictEqual(capturedMethod, 'PATCH');
    assert.deepStrictEqual(JSON.parse(capturedBody), { status: 'ACKNOWLEDGED' });

    // Offline failure path
    globalThis.fetch = async () => {
      throw new Error('Connection refused');
    };

    const failRes = await updateSecurityEventStatus('EVT-001', 'RESOLVED');
    assert.strictEqual(failRes.success, false);
    assert.strictEqual(failRes.isLive, false);
    assert.match(failRes.message, /could not be persisted to backend/);
  });

  // ============================================================================
  // 12. Configurable Base URL & Query Parameter Serialization
  // ============================================================================
  test('12. Base URL and query parameter building - normalizes URL slashes and formats query string', () => {
    const client = new ApiClient('http://test-server:9000///');
    assert.strictEqual(client.getBaseUrl(), 'http://test-server:9000');

    client.setBaseUrl('https://api.sentinelai.internal/v1//');
    assert.strictEqual(client.getBaseUrl(), 'https://api.sentinelai.internal/v1');

    // Build URL with params, ignoring null and undefined
    const builtUrl = client.buildUrl('/api/events', {
      limit: 25,
      offset: 50,
      risk_level: 'HIGH',
      active: true,
      empty_str: '',
      null_val: null,
      undefined_val: undefined,
    });

    const expected =
      'https://api.sentinelai.internal/v1/api/events?limit=25&offset=50&risk_level=HIGH&active=true';
    assert.strictEqual(builtUrl, expected);
  });
});
