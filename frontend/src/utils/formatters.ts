/**
 * SentinelAI Safe Formatting Utilities
 * 
 * Provides crash-resilient formatters for timestamps, numbers, and strings,
 * protecting the UI from RangeError: Invalid time value and null dereferences.
 */

/**
 * Safely formats an ISO date string or timestamp into UTC display format.
 * Never throws RangeError on invalid or null dates.
 */
export function formatUtcTimestamp(isoOrString?: string | null, fallback?: string): string {
  if (!isoOrString || typeof isoOrString !== 'string' || !isoOrString.trim()) {
    return fallback !== undefined ? fallback : 'Pending timestamp';
  }

  try {
    const d = new Date(isoOrString);
    if (isNaN(d.getTime())) {
      return fallback !== undefined ? fallback : 'Invalid Date';
    }
    return d.toISOString().slice(0, 19).replace('T', ' ') + ' UTC';
  } catch {
    return fallback !== undefined ? fallback : String(isoOrString);
  }
}

/**
 * Safely formats a timestamp into relative time (e.g., "Just now", "5m ago", "2h ago").
 * Never throws on invalid dates.
 */
export function formatRelativeTime(isoOrString?: string | null, fallback: string = 'Recently'): string {
  if (!isoOrString || typeof isoOrString !== 'string' || !isoOrString.trim()) {
    return fallback;
  }

  try {
    const d = new Date(isoOrString);
    if (isNaN(d.getTime())) {
      return fallback;
    }

    const diffMs = Date.now() - d.getTime();
    if (diffMs < 0 || diffMs < 60 * 1000) {
      return 'Just now';
    }
    const diffMinutes = Math.floor(diffMs / (60 * 1000));
    if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    }
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) {
      return `${diffHours}h ago`;
    }
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch {
    return fallback;
  }
}

/**
 * Safely formats a decimal float into a percentage string (e.g. 0.942 -> "94%").
 */
export function formatConfidencePercent(conf?: number | null, decimals: number = 0): string {
  if (typeof conf !== 'number' || isNaN(conf)) {
    return 'N/A';
  }
  return `${(conf * 100).toFixed(decimals)}%`;
}

/**
 * Safely extracts a query-safe lowercase string.
 */
export function safeLower(val?: unknown): string {
  if (val === null || val === undefined) return '';
  return String(val).toLowerCase();
}
