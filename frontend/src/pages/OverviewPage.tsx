import React, { useState } from 'react';
import { Camera, AlertTriangle, ShieldAlert, AlertOctagon, RefreshCw } from 'lucide-react';
import { StatCard } from '../components/dashboard/StatCard';
import { MonitoringPanel } from '../components/dashboard/MonitoringPanel';
import { SystemHealthPanel } from '../components/dashboard/SystemHealthPanel';
import { RecentEventsTable } from '../components/dashboard/RecentEventsTable';
import { ActivitySummary } from '../components/dashboard/ActivitySummary';
import { EventDetailModal } from '../components/dashboard/EventDetailModal';
import {
  SecurityEvent,
  DashboardStatistics,
  SystemHealthState,
  CameraInfo,
  EventStatus,
} from '../types';

interface OverviewPageProps {
  stats: DashboardStatistics;
  events: SecurityEvent[];
  health: SystemHealthState;
  cameras: CameraInfo[];
  isLive: boolean;
  onRefresh: () => Promise<void>;
  searchFilter: string;
  highlightedEventIds?: Set<string>;
  onStatusChange?: (eventId: string, newStatus: EventStatus) => Promise<{ success: boolean; message: string; isLive: boolean }>;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  stats,
  events,
  health,
  cameras,
  isLive,
  onRefresh,
  searchFilter,
  highlightedEventIds,
  onStatusChange,
}) => {
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="dashboard-container">
      {/* Page Heading & Refresh Affordance */}
      <div className="dashboard-heading-block">
        <div className="heading-title-group">
          <h1>Security Operations Overview</h1>
          <p>
            Consolidated border surveillance telemetry, restricted-zone incursion alerts, and subsystem connectivity status.
          </p>
        </div>

        <div className="heading-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            title="Poll backend for updated surveillance events"
          >
            <RefreshCw size={13} className={isRefreshing ? 'spin-icon' : ''} />
            {isRefreshing ? 'Refreshing Telemetry...' : 'Refresh Telemetry'}
          </button>
        </div>
      </div>

      {/* 4 KPI Metrics Cards */}
      <div className="kpi-grid">
        <StatCard
          title="Active Cameras"
          value={`${stats.active_cameras} / ${stats.total_cameras}`}
          subtitle="Configured surveillance nodes"
          icon={Camera}
          badgeText={stats.active_cameras === 0 ? 'OFFLINE' : 'ONLINE'}
          badgeType={stats.active_cameras === 0 ? 'warning' : 'success'}
        />

        <StatCard
          title="Events Today"
          value={stats.events_today}
          subtitle="Logged perimeter incursions"
          icon={AlertTriangle}
          badgeText={stats.is_mock ? 'DEMO FIXTURES' : 'LIVE'}
          badgeType={stats.is_mock ? 'warning' : 'info'}
        />

        <StatCard
          title="Restricted-Zone Alerts"
          value={stats.restricted_zone_alerts}
          subtitle="Polygon boundary crossings"
          icon={ShieldAlert}
          badgeText="RAY-CASTING"
          badgeType="info"
        />

        <StatCard
          title="Critical Priority"
          value={stats.critical_alerts}
          subtitle="Immediate response required"
          icon={AlertOctagon}
          badgeText="ACTION REQ"
          badgeType="critical"
        />
      </div>

      {/* Row 1: Surveillance Feeds (Live Video Demo) & Subsystem Health */}
      <div className="dashboard-split-row">
        <MonitoringPanel cameras={cameras} onRefresh={onRefresh} />
        <SystemHealthPanel healthState={health} onRefreshHealth={onRefresh} />
      </div>

      {/* Row 2: Recent Security Events Table */}
      <RecentEventsTable
        events={events}
        isLive={isLive}
        onSelectEvent={(evt) => setSelectedEvent(evt)}
        searchFilter={searchFilter}
        highlightedEventIds={highlightedEventIds}
      />

      {/* Row 3: Activity Trends Placeholder */}
      <ActivitySummary />

      {/* Event Details Inspection Modal with Operator Status Workflow */}
      <EventDetailModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        onStatusChange={onStatusChange}
      />
    </div>
  );
};
