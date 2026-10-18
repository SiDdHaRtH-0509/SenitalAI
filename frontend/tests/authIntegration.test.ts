/**
 * SentinelAI Frontend Authentication Integration Tests
 *
 * Verifies Phase 1 authentication contracts:
 * 1. ApiClient sets and transmits Authorization Bearer headers
 * 2. loginUser successfully authenticates and updates ApiClient token
 * 3. loginUser handles 401 unauthorized errors with ApiClientError
 * 4. logoutUser clears token and local storage state
 * 5. getCurrentUserProfile returns profile when authenticated
 * 6. getCurrentUserProfile falls back safely to demo operator context when unauthenticated
 */

import { test, describe, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  ApiClient,
  ApiClientError,
  apiClient,
  loginUser,
  registerUser,
  logoutUser,
  getCurrentUserProfile,
} from '../src/services/apiClient';

describe('SentinelAI Frontend Authentication & RBAC Suite', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    apiClient.setAuthToken(null);
  });

  test('1. ApiClient transmits Authorization: Bearer header when token is set', async () => {
    let capturedHeader: string | undefined;

    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const headers = (init?.headers as Record<string, string>) || {};
      capturedHeader = headers['Authorization'];
      return new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const client = new ApiClient('http://localhost:8000');
    client.setAuthToken('test-bearer-token-12345');
    assert.strictEqual(client.isAuthenticated(), true);

    await client.get('/api/health');
    assert.strictEqual(capturedHeader, 'Bearer test-bearer-token-12345');
  });

  test('2. loginUser successfully signs in and records JWT token', async () => {
    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/api/auth/login')) {
        return new Response(
          JSON.stringify({
            access_token: 'mock-jwt-token-xyz',
            token_type: 'bearer',
            role: 'OPERATOR',
            username: 'operator',
            expires_in_seconds: 28800,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }
      if (url.includes('/api/auth/me')) {
        return new Response(
          JSON.stringify({
            id: 2,
            username: 'operator',
            role: 'OPERATOR',
            full_name: 'Border Security Officer',
            is_active: true,
            created_at: '2026-10-17T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response('Not found', { status: 404 });
    };

    const res = await loginUser('operator', 'operator123');
    assert.strictEqual(res.isLive, true);
    assert.strictEqual(res.data.token, 'mock-jwt-token-xyz');
    assert.strictEqual(res.data.user.username, 'operator');
    assert.strictEqual(res.data.user.role, 'OPERATOR');
    assert.strictEqual(apiClient.getAuthToken(), 'mock-jwt-token-xyz');
  });

  test('3. loginUser throws ApiClientError on 401 invalid credentials', async () => {
    globalThis.fetch = async () => {
      return new Response(
        JSON.stringify({ detail: 'Invalid username or password.' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    };

    await assert.rejects(
      async () => {
        await loginUser('baduser', 'wrongpass');
      },
      (err: unknown) => {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual((err as ApiClientError).status, 401);
        return true;
      }
    );
  });

  test('4. logoutUser clears authentication state', async () => {
    apiClient.setAuthToken('token-to-clear');
    assert.strictEqual(apiClient.isAuthenticated(), true);

    globalThis.fetch = async () => {
      return new Response(JSON.stringify({ message: 'Logged out' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    await logoutUser();
    assert.strictEqual(apiClient.isAuthenticated(), false);
    assert.strictEqual(apiClient.getAuthToken(), null);
  });

  test('5. getCurrentUserProfile returns active profile when authenticated', async () => {
    apiClient.setAuthToken('valid-admin-token');

    globalThis.fetch = async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/api/auth/me')) {
        return new Response(
          JSON.stringify({
            id: 1,
            username: 'admin',
            role: 'ADMIN',
            full_name: 'System Administrator',
            is_active: true,
            created_at: '2026-10-17T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response('Not found', { status: 404 });
    };

    const res = await getCurrentUserProfile();
    assert.strictEqual(res.isLive, true);
    assert.strictEqual(res.data.username, 'admin');
    assert.strictEqual(res.data.role, 'ADMIN');
  });

  test('6. getCurrentUserProfile provides safe demo operator fallback when unauthenticated', async () => {
    apiClient.setAuthToken(null);

    const res = await getCurrentUserProfile();
    assert.strictEqual(res.isLive, false);
    assert.strictEqual(res.data.username, 'operator');
    assert.strictEqual(res.data.role, 'OPERATOR');
    assert.ok(res.error?.includes('Unauthenticated'));
  });

  test('7. ApiClient strictly avoids storing tokens in localStorage', () => {
    const mockStorage: Record<string, string> = {};
    (globalThis as unknown as { window?: { localStorage?: Storage } }).window = {
      localStorage: {
        getItem: (k: string) => mockStorage[k] || null,
        setItem: (k: string, v: string) => { mockStorage[k] = v; },
        removeItem: (k: string) => { delete mockStorage[k]; },
        clear: () => {},
        key: () => null,
        length: 0,
      } as unknown as Storage,
    } as unknown as Window & typeof globalThis;

    const client = new ApiClient('http://localhost:8000');
    client.setAuthToken('token-in-memory-only');
    assert.strictEqual(mockStorage['sentinel_auth_token'], undefined);
    assert.strictEqual(client.getAuthToken(), 'token-in-memory-only');
  });

  test('8. ApiClient transmits X-CSRF-Token header on state-changing requests', async () => {
    let capturedCsrfHeader: string | undefined;

    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const headers = (init?.headers as Record<string, string>) || {};
      capturedCsrfHeader = headers['X-CSRF-Token'];
      return new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const client = new ApiClient('http://localhost:8000');
    client.setAuthToken('mock-token', 'csrf-secret-token-777');
    assert.strictEqual(client.getCsrfToken(), 'csrf-secret-token-777');

    await client.post('/api/events/evt-01/status', { status: 'RESOLVED' });
    assert.strictEqual(capturedCsrfHeader, 'csrf-secret-token-777');
  });

  test('9. registerUser successfully posts registration and returns UserProfile', async () => {
    let capturedBody: any;
    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/api/auth/register')) {
        capturedBody = JSON.parse(String(init?.body));
        return new Response(
          JSON.stringify({
            id: 10,
            username: capturedBody.username,
            role: 'OPERATOR',
            full_name: capturedBody.full_name,
            email: capturedBody.email,
            is_active: true,
            created_at: '2026-10-18T10:00:00Z',
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response('Not found', { status: 404 });
    };

    const res = await registerUser('new_guard', 'securepass123', 'Officer New Guard', 'guard@sentinel.local');
    assert.strictEqual(res.isLive, true);
    assert.strictEqual(res.statusCode, 201);
    assert.strictEqual(res.data.username, 'new_guard');
    assert.strictEqual(res.data.role, 'OPERATOR');
    assert.strictEqual(capturedBody.username, 'new_guard');
    assert.strictEqual(capturedBody.password, 'securepass123');
  });
});
