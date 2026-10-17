/**
 * SentinelAI Frontend API Service Bridge
 * 
 * Re-exports the centralized ApiClient and high-level service functions
 * from apiClient.ts, maintaining backward compatibility for existing
 * dashboard pages while providing strict typed contracts.
 */

export * from './apiClient';
export * from './eventStreamService';
export * from './notificationService';

import {
  getHealth,
  getDashboardStatistics,
  getSecurityEvents,
  getSecurityEventById,
  getCameras,
  getRestrictedZones,
  getSystemHealth,
  updateSecurityEventStatus,
} from './apiClient';

// Aliases matching earlier Phase 1 & 2 naming conventions
export const checkBackendHealth = getHealth;
export const fetchDashboardStats = getDashboardStatistics;
export const fetchRecentEvents = getSecurityEvents;
export const fetchEventById = getSecurityEventById;
export const fetchCameras = getCameras;
export const fetchRestrictedZones = getRestrictedZones;
export const fetchSystemHealth = getSystemHealth;
export const updateEventStatus = updateSecurityEventStatus;

import { ClientSettings } from '../types';
import { DEFAULT_CLIENT_SETTINGS } from '../data/demoData';

const SETTINGS_STORAGE_KEY = 'sentinel_client_settings_v1';

export function loadClientSettings(): ClientSettings {
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_CLIENT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch {
    // Fall back to defaults
  }
  return DEFAULT_CLIENT_SETTINGS;
}

export function saveClientSettings(settings: ClientSettings): void {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Silently ignore storage errors
  }
}
