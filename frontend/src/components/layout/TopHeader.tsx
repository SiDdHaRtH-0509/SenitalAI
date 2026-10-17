import React, { useState } from 'react';
import { Search, Bell, Menu, ShieldAlert, CheckCircle2, AlertTriangle, X } from 'lucide-react';
import { NavigationPage } from '../../types';

interface TopHeaderProps {
  activePage: NavigationPage;
  onOpenMobileMenu: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

const PAGE_TITLES: Record<NavigationPage, { title: string; subtitle: string }> = {
  overview: {
    title: 'Security Operations Overview',
    subtitle: 'Consolidated border surveillance telemetry, restricted-zone alerts, and subsystem status',
  },
  monitoring: {
    title: 'Live Camera Feeds',
    subtitle: 'Real-time video surveillance streams across monitored perimeter sectors',
  },
  events: {
    title: 'Security Incident Ledger',
    subtitle: 'Historical and active restricted-zone incursions detected by CV engine',
  },
  cameras: {
    title: 'Camera Device Registry',
    subtitle: 'Configured CCTV edge nodes, resolutions, frame rates, and assigned zones',
  },
  zones: {
    title: 'Restricted-Zone Boundaries',
    subtitle: 'Perimeter polygon coordinate configuration and calibration',
  },
  analytics: {
    title: 'Surveillance Analytics & Insights',
    subtitle: 'Incursion frequencies, detector confidence distributions, and trend analysis',
  },
  health: {
    title: 'Subsystem Health & Connectivity',
    subtitle: 'Telemetry links between CV engine, backend API, database, and client dashboard',
  },
  settings: {
    title: 'System Settings & Thresholds',
    subtitle: 'Detection confidence thresholds, cooldown intervals, and API endpoints',
  },
};

export const TopHeader: React.FC<TopHeaderProps> = ({
  activePage,
  onOpenMobileMenu,
  searchQuery,
  onSearchChange,
}) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const pageMeta = PAGE_TITLES[activePage] || {
    title: 'Security Operations',
    subtitle: 'Border Surveillance Command Platform',
  };

  return (
    <header className="app-header" role="banner">
      {/* Left: Mobile Toggle & Page Headings */}
      <div className="header-left">
        <button
          type="button"
          className="mobile-menu-btn"
          onClick={onOpenMobileMenu}
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>

        <div className="header-title-block">
          <h2 className="header-title">{pageMeta.title}</h2>
          <span className="header-subtitle">{pageMeta.subtitle}</span>
        </div>
      </div>

      {/* Right: Search, Status, Notifications, Demo Operator */}
      <div className="header-right">
        {/* Search Input Affordance */}
        <div className="header-search">
          <Search size={14} className="search-icon" aria-hidden="true" />
          <input
            type="search"
            placeholder="Search events, cameras, zones..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="search-input"
            aria-label="Search events and cameras"
          />
        </div>

        {/* System Health Status Indicator */}
        <div className="system-status-pill" title="Backend integration pending deployment">
          <span className="status-pulse-dot" />
          <span>Integration Pending</span>
        </div>

        {/* Notifications Icon & Popover */}
        <div className="notification-container">
          <button
            type="button"
            className="icon-btn"
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label="System notifications"
            aria-expanded={showNotifications}
          >
            <Bell size={18} />
            <span className="notification-badge" />
          </button>

          {showNotifications && (
            <div className="notifications-popover" role="dialog" aria-label="Notifications panel">
              <div className="popover-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldAlert size={15} style={{ color: 'var(--color-warning)' }} />
                  <h4>System Notifications (3)</h4>
                </div>
                <button
                  type="button"
                  style={{ background: 'transparent', color: 'var(--color-text-dim)', padding: '2px' }}
                  onClick={() => setShowNotifications(false)}
                  aria-label="Close notifications"
                >
                  <X size={14} />
                </button>
              </div>

              <div className="notification-list">
                <div className="notification-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <AlertTriangle size={13} style={{ color: 'var(--color-critical)' }} />
                    <div className="notification-item-title">CRITICAL Incursion Alert</div>
                  </div>
                  <p style={{ color: 'var(--color-text-secondary)', margin: '2px 0' }}>
                    Sector Alpha North Ridge (cam-north-01) demo entry logged.
                  </p>
                  <div className="notification-item-time">09:30:00 UTC • Demo Fixture</div>
                </div>

                <div className="notification-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={13} style={{ color: 'var(--color-success)' }} />
                    <div className="notification-item-title">CV Engine Standalone Ready</div>
                  </div>
                  <p style={{ color: 'var(--color-text-secondary)', margin: '2px 0' }}>
                    All 122 CV tests passed. Replay & YOLOv8n inference operational.
                  </p>
                  <div className="notification-item-time">09:15:00 UTC • Localhost Node</div>
                </div>

                <div className="notification-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <AlertTriangle size={13} style={{ color: 'var(--color-warning)' }} />
                    <div className="notification-item-title">Backend API Offline</div>
                  </div>
                  <p style={{ color: 'var(--color-text-secondary)', margin: '2px 0' }}>
                    Awaiting FastAPI service launch on http://localhost:8000.
                  </p>
                  <div className="notification-item-time">Active • Fallback Mode</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Demo User Profile */}
        <div className="user-profile">
          <div className="user-avatar" aria-hidden="true">
            OP
          </div>
          <div className="user-meta">
            <span className="user-name">Operator 04</span>
            <span className="user-role">Watch Officer (Demo)</span>
          </div>
        </div>
      </div>
    </header>
  );
};
