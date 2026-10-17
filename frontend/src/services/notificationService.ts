/**
 * SentinelAI Security Notification Service
 * 
 * Manages operator notifications for perimeter security events:
 * - Converts raw SecurityEvent payloads into SecurityNotification items.
 * - Deduplicates notifications using stable event IDs (prevents notification spam).
 * - Persists read IDs to browser localStorage (client-side review state only).
 * - Caps notification list size to avoid unbounded memory growth.
 * - Supports opt-in gentle synthesized audio chime (Web Audio API).
 */

import { SecurityEvent, SecurityNotification } from '../types';

const STORAGE_KEY_READ_NOTIFICATIONS = 'sentinel_read_notifications_v1';
const MAX_NOTIFICATIONS = 50;

/**
 * Loads the set of notification IDs marked as read by the operator in localStorage.
 */
export function getStoredReadNotificationIds(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_READ_NOTIFICATIONS);
    if (raw) {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)) {
        return new Set(arr);
      }
    }
  } catch {
    // Graceful fallback on storage access issues
  }
  return new Set();
}

/**
 * Persists read notification IDs to localStorage.
 */
export function saveReadNotificationIds(readIds: Set<string>): void {
  try {
    const arr = Array.from(readIds).slice(-100); // retain last 100
    localStorage.setItem(STORAGE_KEY_READ_NOTIFICATIONS, JSON.stringify(arr));
  } catch {
    // Ignore storage quota or disabled storage errors
  }
}

/**
 * Converts a SecurityEvent into a SecurityNotification.
 */
export function createNotificationFromEvent(
  event: SecurityEvent,
  isRead: boolean = false
): SecurityNotification {
  const notifId = `notif-${event.event_id}`;
  const zoneText = event.zone_id ? ` in ${event.zone_id}` : '';
  const message = `${event.event_type} on ${event.camera_id}${zoneText}`;

  return {
    id: notifId,
    event_id: event.event_id,
    event_type: event.event_type,
    timestamp: event.timestamp,
    camera_id: event.camera_id,
    zone_id: event.zone_id,
    risk_level: event.risk_level,
    severity: event.severity,
    message,
    read: isRead,
    created_at: new Date().toISOString(),
    is_demo: Boolean(event.is_demo),
  };
}

/**
 * Merges new notifications into an existing list, deduplicating by notification ID
 * and maintaining newest-first order.
 */
export function mergeNotifications(
  current: SecurityNotification[],
  newItems: SecurityNotification[],
  readIds: Set<string>
): SecurityNotification[] {
  const seenIds = new Set<string>();
  const merged: SecurityNotification[] = [];

  // Add new items first
  for (const item of newItems) {
    if (!seenIds.has(item.id)) {
      seenIds.add(item.id);
      merged.push({
        ...item,
        read: readIds.has(item.id) || item.read,
      });
    }
  }

  // Add current items
  for (const item of current) {
    if (!seenIds.has(item.id)) {
      seenIds.add(item.id);
      merged.push({
        ...item,
        read: readIds.has(item.id) || item.read,
      });
    }
  }

  // Sort descending by timestamp
  merged.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  // Cap size
  return merged.slice(0, MAX_NOTIFICATIONS);
}

/**
 * Plays a subtle, non-disruptive audio tone for critical notifications if enabled.
 * Uses Web Audio API without requiring any external audio files.
 */
export function playGentleAudioAlert(): void {
  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtx) return;

    const ctx = new AudioCtx();
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {});
    }

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    // Two-tone gentle chime: 587.33 Hz (D5) to 880 Hz (A5)
    osc.frequency.setValueAtTime(587.33, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.1);

    gain.gain.setValueAtTime(0.04, ctx.currentTime); // low volume
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch {
    // Autoplay restrictions or headless environment - gracefully ignore
  }
}
