/**
 * SentinelAI Event Stream & Real-Time Transport Service
 * 
 * Implements the reusable EventStreamService interface per Phase 4 requirements:
 * - Transport strategy: HTTP Polling with Integration-Pending and Offline Fallbacks.
 * - Respects VITE_POLLING_INTERVAL_SEC (0 = manual refresh only).
 * - Prevents overlapping requests via active request locking.
 * - Provides AbortController request cancellation and timer cleanup.
 * - Deduplicates incoming security events using stable event IDs.
 * - Tracks connection status: CONNECTED, CONNECTING, RECONNECTING, DISCONNECTED, INTEGRATION_PENDING.
 */

import type {
  EventStreamService,
  ConnectionState,
  StreamEventPayload,
  SecurityEvent,
} from '../types';
import {
  getHealth,
  getDashboardStatistics,
  getSecurityEvents,
} from './apiClient';

export interface PollingStreamOptions {
  intervalSec?: number;
  autoStart?: boolean;
}

export function getDefaultPollingIntervalSec(): number {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_POLLING_INTERVAL_SEC) {
    const val = Number(import.meta.env.VITE_POLLING_INTERVAL_SEC);
    if (!isNaN(val) && val >= 0) return val;
  }
  return 30; // 30-second default conservative datathon interval
}

export class PollingEventStreamService implements EventStreamService {
  private connectionState: ConnectionState = 'INTEGRATION_PENDING';
  private pollingIntervalSec: number;
  private timerId: ReturnType<typeof setTimeout> | null = null;
  private isRequestInProgress: boolean = false;
  private abortController: AbortController | null = null;
  private lastUpdateTime: string | null = null;
  private knownEventIds: Set<string> = new Set();
  private subscribers: Set<(payload: StreamEventPayload) => void> = new Set();
  private isConnectedOrConnecting: boolean = false;

  constructor(options: PollingStreamOptions = {}) {
    this.pollingIntervalSec = options.intervalSec ?? getDefaultPollingIntervalSec();
    if (options.autoStart) {
      this.connect();
    }
  }

  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  public getLastUpdateTime(): string | null {
    return this.lastUpdateTime;
  }

  public getPollingIntervalSec(): number {
    return this.pollingIntervalSec;
  }

  public setPollingIntervalSec(seconds: number): void {
    const safeSec = Math.max(0, Math.floor(seconds));
    this.pollingIntervalSec = safeSec;
    // Reschedule if currently polling
    if (this.isConnectedOrConnecting) {
      this.clearTimer();
      if (this.pollingIntervalSec > 0) {
        this.scheduleNextPoll();
      }
    }
  }

  public subscribe(callback: (payload: StreamEventPayload) => void): () => void {
    this.subscribers.add(callback);
    return () => {
      this.subscribers.delete(callback);
    };
  }

  private notify(payload: StreamEventPayload): void {
    this.subscribers.forEach((cb) => {
      try {
        cb(payload);
      } catch (err) {
        console.error('[EventStreamService] Subscriber error:', err);
      }
    });
  }

  public connect(): void {
    if (this.isConnectedOrConnecting) return;
    this.isConnectedOrConnecting = true;

    // Initial check
    this.connectionState = 'CONNECTING';
    this.notify({
      type: 'HEALTH_PING',
      timestamp: new Date().toISOString(),
      message: 'Connecting to backend telemetry stream...',
    });

    // Execute first poll immediately
    this.refreshNow().finally(() => {
      // Schedule subsequent polling if interval > 0
      if (this.isConnectedOrConnecting && this.pollingIntervalSec > 0) {
        this.scheduleNextPoll();
      }
    });
  }

  public disconnect(): void {
    this.isConnectedOrConnecting = false;
    this.clearTimer();

    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }

    this.isRequestInProgress = false;
    this.connectionState = 'DISCONNECTED';
    this.notify({
      type: 'HEALTH_PING',
      timestamp: new Date().toISOString(),
      message: 'Telemetry polling disconnected.',
    });
  }

  private clearTimer(): void {
    if (this.timerId !== null) {
      clearTimeout(this.timerId);
      this.timerId = null;
    }
  }

  private scheduleNextPoll(): void {
    this.clearTimer();
    if (!this.isConnectedOrConnecting || this.pollingIntervalSec <= 0) return;

    this.timerId = setTimeout(() => {
      if (!this.isConnectedOrConnecting) return;
      this.refreshNow().finally(() => {
        if (this.isConnectedOrConnecting && this.pollingIntervalSec > 0) {
          this.scheduleNextPoll();
        }
      });
    }, this.pollingIntervalSec * 1000);
  }

  /**
   * Performs an immediate, non-overlapping fetch of events, stats, and health.
   */
  public async refreshNow(): Promise<void> {
    // Prevent overlapping requests per Section 5
    if (this.isRequestInProgress) {
      return;
    }

    this.isRequestInProgress = true;
    this.abortController = new AbortController();
    const signal = this.abortController.signal;

    try {
      const [healthProbe, statsResponse, eventsResponse] = await Promise.all([
        getHealth(signal),
        getDashboardStatistics(signal),
        getSecurityEvents(undefined, signal),
      ]);

      const nowIso = new Date().toISOString();
      this.lastUpdateTime = nowIso;

      if (healthProbe.isConnected && eventsResponse.isLive) {
        this.connectionState = 'CONNECTED';
      } else {
        // Backend offline or unreachable
        this.connectionState = 'INTEGRATION_PENDING';
      }

      const events = eventsResponse.data || [];
      const stats = statsResponse.data;

      // Detect genuinely new events (for notification & visual highlight)
      const newlyDiscoveredEvents: SecurityEvent[] = [];
      events.forEach((evt) => {
        if (!this.knownEventIds.has(evt.event_id)) {
          this.knownEventIds.add(evt.event_id);
          newlyDiscoveredEvents.push(evt);
        }
      });

      // Dispatch individual NEW_EVENT triggers for new arrivals
      newlyDiscoveredEvents.forEach((evt) => {
        this.notify({
          type: 'NEW_EVENT',
          event: evt,
          timestamp: nowIso,
        });
      });

      // Dispatch comprehensive batch
      this.notify({
        type: 'EVENT_BATCH',
        events,
        stats,
        timestamp: nowIso,
        isLive: eventsResponse.isLive,
        message: eventsResponse.isLive
          ? 'Live telemetry retrieved.'
          : 'Backend unreachable. Showing demonstration audit fixtures.',
      });
    } catch (err: unknown) {
      if (signal.aborted) {
        return; // Request was cleanly cancelled
      }

      this.connectionState =
        this.connectionState === 'CONNECTED' ? 'RECONNECTING' : 'DISCONNECTED';

      this.notify({
        type: 'ERROR',
        timestamp: new Date().toISOString(),
        message: err instanceof Error ? err.message : 'Telemetry polling error',
      });
    } finally {
      this.isRequestInProgress = false;
      this.abortController = null;
    }
  }

  /**
   * Resets internal known event cache (useful for testing and reset scenarios).
   */
  public clearKnownEventIds(): void {
    this.knownEventIds.clear();
  }
}

// Global default stream instance
export const globalEventStream = new PollingEventStreamService();
