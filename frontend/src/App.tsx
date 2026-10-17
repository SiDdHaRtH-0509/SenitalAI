import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from './components/layout/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import {
  NavigationPage,
  SecurityEvent,
  DashboardStatistics,
  SystemHealthState,
  CameraInfo,
} from './types';
import {
  fetchRecentEvents,
  fetchDashboardStats,
  fetchSystemHealth,
} from './services/api';
import {
  DEMO_EVENTS,
  DEMO_STATISTICS,
  INITIAL_SYSTEM_HEALTH,
  DEMO_CAMERAS,
} from './data/demoData';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<NavigationPage>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [events, setEvents] = useState<SecurityEvent[]>(DEMO_EVENTS);
  const [stats, setStats] = useState<DashboardStatistics>(DEMO_STATISTICS);
  const [health, setHealth] = useState<SystemHealthState>(INITIAL_SYSTEM_HEALTH);
  const [cameras] = useState<CameraInfo[]>(DEMO_CAMERAS);
  const [isLive, setIsLive] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    try {
      const [eventsRes, statsRes, healthRes] = await Promise.all([
        fetchRecentEvents(),
        fetchDashboardStats(),
        fetchSystemHealth(),
      ]);

      setEvents(eventsRes.data);
      setIsLive(eventsRes.isLive);
      setStats(statsRes.data);
      setHealth(healthRes);
    } catch {
      // Graceful fallback to demonstration state
      setEvents(DEMO_EVENTS);
      setStats(DEMO_STATISTICS);
      setHealth(INITIAL_SYSTEM_HEALTH);
      setIsLive(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const getPageTitle = (page: NavigationPage): string => {
    switch (page) {
      case 'monitoring':
        return 'Live Monitoring';
      case 'events':
        return 'Security Events';
      case 'cameras':
        return 'Cameras';
      case 'zones':
        return 'Restricted Zones';
      case 'analytics':
        return 'Analytics';
      case 'health':
        return 'System Health';
      case 'settings':
        return 'Settings';
      default:
        return 'Overview';
    }
  };

  return (
    <AppShell
      activePage={activePage}
      onNavigate={(page) => setActivePage(page)}
      searchQuery={searchQuery}
      onSearchChange={(q) => setSearchQuery(q)}
    >
      {activePage === 'overview' ? (
        <OverviewPage
          stats={stats}
          events={events}
          health={health}
          cameras={cameras}
          isLive={isLive}
          onRefresh={loadData}
          searchFilter={searchQuery}
        />
      ) : (
        <PlaceholderPage
          pageId={activePage}
          pageName={getPageTitle(activePage)}
          onBackToOverview={() => setActivePage('overview')}
        />
      )}
    </AppShell>
  );
};

export default App;
