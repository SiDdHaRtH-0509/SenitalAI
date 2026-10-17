import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AppShell } from './components/layout/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { EventsPage } from './pages/EventsPage';
import { CamerasPage } from './pages/CamerasPage';
import { ZonesPage } from './pages/ZonesPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { SettingsPage } from './pages/SettingsPage';
import { EventDetailModal } from './components/dashboard/EventDetailModal';
import {
  NavigationPage,
  SecurityEvent,
  DashboardStatistics,
  SystemHealthState,
  CameraInfo,
  ClientSettings,
  ConnectionState,
  SecurityNotification,
  EventStatus,
} from './types';
import {
  fetchDashboardStats,
  fetchSystemHealth,
  fetchCameras,
  loadClientSettings,
  updateSecurityEventStatus,
  globalEventStream,
  getStoredReadNotificationIds,
  saveReadNotificationIds,
  createNotificationFromEvent,
  mergeNotifications,
  playGentleAudioAlert,
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
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    globalEventStream.getConnectionState()
  );
  const [lastRefreshTime, setLastRefreshTime] = useState<string | null>(null);
  const [settings, setSettings] = useState<ClientSettings>(DEFAULT_CLIENT_SETTINGS);
  const [readNotificationIds, setReadNotificationIds] = useState<Set<string>>(
    getStoredReadNotificationIds()
  );
  const [notifications, setNotifications] = useState<SecurityNotification[]>(() => {
    const stored = getStoredReadNotificationIds();
    return DEMO_EVENTS.map((e) => createNotificationFromEvent(e, stored.has(`notif-${e.event_id}`)));
  });
  const [highlightedEventIds, setHighlightedEventIds] = useState<Set<string>>(new Set());
  const [inspectedEvent, setInspectedEvent] = useState<SecurityEvent | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const highlightTimeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // Load client preferences on mount
  useEffect(() => {
    const loaded = loadClientSettings();
    setSettings(loaded);
    globalEventStream.setPollingIntervalSec(loaded.auto_refresh_interval);
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

  // Status Change Handler with Graceful Fallback
  const handleStatusChange = useCallback(
    async (eventId: string, newStatus: EventStatus) => {
      const result = await updateSecurityEventStatus(eventId, newStatus);

      // Apply update locally for review session
      setEvents((prev) =>
        prev.map((e) => (e.event_id === eventId ? { ...e, status: newStatus } : e))
      );

      if (inspectedEvent && inspectedEvent.event_id === eventId) {
        setInspectedEvent((prev) => (prev ? { ...prev, status: newStatus } : null));
      }

      return result;
    },
    [inspectedEvent]
  );

  // Mark single notification read
  const handleMarkNotificationAsRead = useCallback((notifId: string) => {
    setReadNotificationIds((prev) => {
      const next = new Set(prev);
      next.add(notifId);
      saveReadNotificationIds(next);
      return next;
    });
    setNotifications((prev) =>
      prev.map((n) => (n.id === notifId ? { ...n, read: true } : n))
    );
  }, []);

  // Mark all notifications read
  const handleMarkAllNotificationsAsRead = useCallback(() => {
    setNotifications((prev) => {
      const allIds = new Set<string>();
      const updated = prev.map((n) => {
        allIds.add(n.id);
        return { ...n, read: true };
      });
      setReadNotificationIds(allIds);
      saveReadNotificationIds(allIds);
      return updated;
    });
  }, []);

  // Select event from notification
  const handleSelectEventById = useCallback(
    (eventId: string) => {
      const match = events.find((e) => e.event_id === eventId);
      if (match) {
        setInspectedEvent(match);
      }
    },
    [events]
  );

  // Subscribe to real-time event stream
  useEffect(() => {
    globalEventStream.setPollingIntervalSec(settings.auto_refresh_interval);
    globalEventStream.connect();

    const unsubscribe = globalEventStream.subscribe((payload) => {
      setConnectionState(globalEventStream.getConnectionState());
      setLastRefreshTime(globalEventStream.getLastUpdateTime());

      if (payload.type === 'NEW_EVENT' && payload.event) {
        const newEvt = payload.event;
        // Audio alert if enabled
        if (settings.enable_audio_alerts) {
          playGentleAudioAlert();
        }

        // Highlight row briefly
        setHighlightedEventIds((prev) => {
          const next = new Set(prev);
          next.add(newEvt.event_id);
          return next;
        });

        // Set 3-second auto un-highlight timer
        const timer = setTimeout(() => {
          setHighlightedEventIds((prev) => {
            const next = new Set(prev);
            next.delete(newEvt.event_id);
            return next;
          });
          highlightTimeoutsRef.current.delete(newEvt.event_id);
        }, 3000);
        highlightTimeoutsRef.current.set(newEvt.event_id, timer);

        // Add to notifications
        const notif = createNotificationFromEvent(newEvt, false);
        setNotifications((prev) => mergeNotifications(prev, [notif], readNotificationIds));
      }

      if (payload.type === 'EVENT_BATCH' && payload.events) {
        setEvents(payload.events);
        setIsLive(payload.events.length > 0 && !payload.events[0].is_demo);
        if (payload.stats) {
          setStats(payload.stats);
        }
      }
    });

    return () => {
      unsubscribe();
      globalEventStream.disconnect();
      // Clean up all pending row highlight timers
      highlightTimeoutsRef.current.forEach((t) => clearTimeout(t));
      highlightTimeoutsRef.current.clear();
    };
  }, [settings.auto_refresh_interval, settings.enable_audio_alerts, readNotificationIds]);

  // Full Refresh Trigger
  const loadData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        globalEventStream.refreshNow(),
        fetchDashboardStats().then((res) => setStats(res.data)),
        fetchSystemHealth().then((res) => setHealth(res)),
        fetchCameras().then((res) => setCameras(res.data)),
      ]);
      setConnectionState(globalEventStream.getConnectionState());
      setLastRefreshTime(globalEventStream.getLastUpdateTime());
    } finally {
      setIsRefreshing(false);
    }
  }, []);

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
            highlightedEventIds={highlightedEventIds}
            onStatusChange={handleStatusChange}
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
            highlightedEventIds={highlightedEventIds}
            onStatusChange={handleStatusChange}
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
            onUpdateSettings={(newSettings) => {
              setSettings(newSettings);
              globalEventStream.setPollingIntervalSec(newSettings.auto_refresh_interval);
            }}
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
            highlightedEventIds={highlightedEventIds}
            onStatusChange={handleStatusChange}
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
      connectionState={connectionState}
      isLive={isLive}
      lastRefreshTime={lastRefreshTime}
      notifications={notifications}
      onMarkNotificationAsRead={handleMarkNotificationAsRead}
      onMarkAllNotificationsAsRead={handleMarkAllNotificationsAsRead}
      onSelectEventById={handleSelectEventById}
      onManualRefresh={loadData}
      isRefreshing={isRefreshing}
    >
      {renderActivePage()}

      {/* Global Event Detail Modal (when triggered via notifications or direct inspect) */}
      <EventDetailModal
        event={inspectedEvent}
        onClose={() => setInspectedEvent(null)}
        onStatusChange={handleStatusChange}
      />
    </AppShell>
  );
};

export default App;
