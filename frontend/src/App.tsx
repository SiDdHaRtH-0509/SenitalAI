import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from './components/layout/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { EventsPage } from './pages/EventsPage';
import { CamerasPage } from './pages/CamerasPage';
import { ZonesPage } from './pages/ZonesPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { SettingsPage } from './pages/SettingsPage';
import {
  NavigationPage,
  SecurityEvent,
  DashboardStatistics,
  SystemHealthState,
  CameraInfo,
  ClientSettings,
} from './types';
import {
  fetchRecentEvents,
  fetchDashboardStats,
  fetchSystemHealth,
  fetchCameras,
  loadClientSettings,
} from './services/api';
import {
  DEMO_EVENTS,
  DEMO_STATISTICS,
  INITIAL_SYSTEM_HEALTH,
  DEMO_CAMERAS,
  DEFAULT_CLIENT_SETTINGS,
} from './data/demoData';

// Map between URL hash/paths and NavigationPage keys
const ROUTE_MAP: Record<string, NavigationPage> = {
  '': 'overview',
  'overview': 'overview',
  'monitoring': 'monitoring',
  'events': 'events',
  'cameras': 'cameras',
  'zones': 'zones',
  'analytics': 'analytics',
  'health': 'health',
  'system-health': 'health',
  'settings': 'settings',
};

export const App: React.FC = () => {
  // Determine initial page from window.location.hash or pathname
  const getInitialPage = (): NavigationPage => {
    const hash = window.location.hash.replace(/^#\/?/, '').toLowerCase();
    if (hash && ROUTE_MAP[hash]) {
      return ROUTE_MAP[hash];
    }
    const path = window.location.pathname.replace(/^\//, '').toLowerCase();
    if (path && ROUTE_MAP[path]) {
      return ROUTE_MAP[path];
    }
    return 'overview';
  };

  const [activePage, setActivePage] = useState<NavigationPage>(getInitialPage);
  const [searchQuery, setSearchQuery] = useState('');
  const [events, setEvents] = useState<SecurityEvent[]>(DEMO_EVENTS);
  const [stats, setStats] = useState<DashboardStatistics>(DEMO_STATISTICS);
  const [health, setHealth] = useState<SystemHealthState>(INITIAL_SYSTEM_HEALTH);
  const [cameras, setCameras] = useState<CameraInfo[]>(DEMO_CAMERAS);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [settings, setSettings] = useState<ClientSettings>(DEFAULT_CLIENT_SETTINGS);

  // Load client preferences on mount
  useEffect(() => {
    const loaded = loadClientSettings();
    setSettings(loaded);
  }, []);

  // Listen to browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      setActivePage(getInitialPage());
    };
    window.addEventListener('popstate', handlePopState);
    window.addEventListener('hashchange', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('hashchange', handlePopState);
    };
  }, []);

  // Navigate and sync URL
  const handleNavigate = (page: NavigationPage) => {
    setActivePage(page);
    window.location.hash = page === 'overview' ? '' : `#/${page}`;
  };

  const loadData = useCallback(async () => {
    try {
      const [eventsRes, statsRes, healthRes, camerasRes] = await Promise.all([
        fetchRecentEvents(),
        fetchDashboardStats(),
        fetchSystemHealth(),
        fetchCameras(),
      ]);

      setEvents(eventsRes.data);
      setIsLive(eventsRes.isLive);
      setStats(statsRes.data);
      setHealth(healthRes);
      setCameras(camerasRes.data);
    } catch {
      // Graceful fallback to demonstration state
      setEvents(DEMO_EVENTS);
      setStats(DEMO_STATISTICS);
      setHealth(INITIAL_SYSTEM_HEALTH);
      setCameras(DEMO_CAMERAS);
      setIsLive(false);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Telemetry auto-polling interval
  useEffect(() => {
    if (settings.auto_refresh_interval <= 0) return;

    const intervalId = setInterval(() => {
      loadData();
    }, settings.auto_refresh_interval * 1000);

    return () => clearInterval(intervalId);
  }, [settings.auto_refresh_interval, loadData]);

  const renderActivePage = () => {
    switch (activePage) {
      case 'overview':
        return (
          <OverviewPage
            stats={stats}
            events={events}
            health={health}
            cameras={cameras}
            isLive={isLive}
            onRefresh={loadData}
            searchFilter={searchQuery}
          />
        );
      case 'monitoring':
        return (
          <MonitoringPage
            cameras={cameras}
            onRefresh={loadData}
            searchFilter={searchQuery}
          />
        );
      case 'events':
        return (
          <EventsPage
            events={events}
            isLive={isLive}
            onRefresh={loadData}
            initialSearchFilter={searchQuery}
          />
        );
      case 'cameras':
        return (
          <CamerasPage
            cameras={cameras}
            onRefresh={loadData}
            searchFilter={searchQuery}
          />
        );
      case 'zones':
        return <ZonesPage />;
      case 'analytics':
        return (
          <AnalyticsPage
            events={events}
            isLive={isLive}
          />
        );
      case 'health':
        return (
          <SystemHealthPage
            health={health}
            onRefresh={loadData}
          />
        );
      case 'settings':
        return (
          <SettingsPage
            settings={settings}
            onUpdateSettings={(newSettings) => setSettings(newSettings)}
          />
        );
      default:
        return (
          <OverviewPage
            stats={stats}
            events={events}
            health={health}
            cameras={cameras}
            isLive={isLive}
            onRefresh={loadData}
            searchFilter={searchQuery}
          />
        );
    }
  };

  return (
    <AppShell
      activePage={activePage}
      onNavigate={handleNavigate}
      searchQuery={searchQuery}
      onSearchChange={(q) => setSearchQuery(q)}
    >
      {renderActivePage()}
    </AppShell>
  );
};

export default App;
