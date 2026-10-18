import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Bell,
  Menu,
  ShieldAlert,
  CheckCircle2,
  X,
  RefreshCw,
  Check,
} from 'lucide-react';
import { NavigationPage, ConnectionState, SecurityNotification, UserProfile } from '../../types';
import { StatusBadge } from '../ui/StatusBadge';

interface TopHeaderProps {
  activePage: NavigationPage;
  onOpenMobileMenu: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  connectionState: ConnectionState;
  isLive: boolean;
  lastRefreshTime: string | null;
  notifications: SecurityNotification[];
  onMarkNotificationAsRead: (id: string) => void;
  onMarkAllNotificationsAsRead: () => void;
  onSelectEventById: (eventId: string) => void;
  onManualRefresh: () => Promise<void>;
  isRefreshing: boolean;
  currentUser?: UserProfile | null;
  onOpenLoginModal?: () => void;
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
  connectionState,
  isLive,
  lastRefreshTime,
  notifications,
  onMarkNotificationAsRead,
  onMarkAllNotificationsAsRead,
  onSelectEventById,
  onManualRefresh,
  isRefreshing,
  currentUser,
  onOpenLoginModal,
}) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const bellButtonRef = useRef<HTMLButtonElement>(null);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const pageMeta = PAGE_TITLES[activePage] || {
    title: 'Security Operations',
    subtitle: 'Border Surveillance Command Platform',
  };

  // Close notifications on outside click or Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showNotifications) {
        setShowNotifications(false);
        bellButtonRef.current?.focus();
      }
    };

    const handleOutsideClick = (e: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        bellButtonRef.current &&
        !bellButtonRef.current.contains(e.target as Node)
      ) {
        setShowNotifications(false);
      }
    };

    if (showNotifications) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [showNotifications]);

  // Map ConnectionState to human-readable label and CSS class
  const getConnectionMeta = (state: ConnectionState) => {
    switch (state) {
      case 'CONNECTED':
        return {
          label: 'Telemetry Live',
          className: 'connected',
          title: `FastAPI backend active on port 8000. Last update: ${lastRefreshTime ? new Date(lastRefreshTime).toLocaleTimeString() : 'now'}`,
        };
      case 'CONNECTING':
        return {
          label: 'Connecting...',
          className: 'connecting',
          title: 'Establishing link to backend API...',
        };
      case 'RECONNECTING':
        return {
          label: 'Reconnecting...',
          className: 'reconnecting',
          title: 'Connection interrupted. Re-probing backend...',
        };
      case 'DEGRADED':
        return {
          label: 'Degraded',
          className: 'degraded',
          title: 'Subsystem latency or partial error reported.',
        };
      case 'DISCONNECTED':
        return {
          label: 'Backend Offline',
          className: 'disconnected',
          title: 'Backend unreachable. Operating in offline demonstration mode.',
        };
      case 'INTEGRATION_PENDING':
      default:
        return {
          label: 'Integration Pending',
          className: 'integration-pending',
          title: 'FastAPI service offline. Operating in demonstration mode per datathon roadmap.',
        };
    }
  };

  const connMeta = getConnectionMeta(connectionState);

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

      {/* Right: Search, Status, Refresh, Notifications, Profile */}
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

        {/* Manual Refresh Affordance */}
        <button
          type="button"
          className="icon-btn"
          onClick={onManualRefresh}
          disabled={isRefreshing}
          title={isRefreshing ? 'Refreshing telemetry...' : 'Manually poll backend telemetry'}
          aria-label="Refresh telemetry data"
          style={{ padding: '6px' }}
        >
          <RefreshCw size={14} className={isRefreshing ? 'spin-icon' : ''} />
        </button>

        {/* Global Connection Status Indicator Pill per Section 6 */}
        <div
          className={`system-status-pill ${connMeta.className}`}
          title={connMeta.title}
          role="status"
          aria-live="polite"
        >
          <span className="status-pulse-dot" />
          <span>{connMeta.label}</span>
          {!isLive && (
            <span
              style={{
                fontSize: '9px',
                opacity: 0.8,
                borderLeft: '1px solid rgba(255,255,255,0.2)',
                paddingLeft: '4px',
                marginLeft: '2px',
              }}
            >
              DEMO
            </span>
          )}
        </div>

        {/* Notifications Icon & Popover per Section 7 */}
        <div className="notification-container">
          <button
            ref={bellButtonRef}
            type="button"
            className="icon-btn"
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label={`${unreadCount} unread security notifications`}
            aria-expanded={showNotifications}
            aria-haspopup="dialog"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="notification-badge" aria-hidden="true">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div
              ref={popoverRef}
              className="notifications-popover"
              role="dialog"
              aria-label="Security incident notifications"
            >
              <div className="popover-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldAlert size={15} style={{ color: 'var(--color-critical)' }} />
                  <h4>Security Alerts ({notifications.length})</h4>
                  {unreadCount > 0 && (
                    <span
                      style={{
                        fontSize: '10px',
                        backgroundColor: 'var(--color-critical-bg)',
                        color: 'var(--color-critical)',
                        padding: '1px 5px',
                        borderRadius: 'var(--radius-xs)',
                        fontWeight: 600,
                      }}
                    >
                      {unreadCount} New
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {unreadCount > 0 && (
                    <button
                      type="button"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--color-accent-blue)',
                        fontSize: '11px',
                        cursor: 'pointer',
                        padding: '2px 4px',
                      }}
                      onClick={onMarkAllNotificationsAsRead}
                      title="Mark all notifications as read"
                    >
                      Mark all read
                    </button>
                  )}
                  <button
                    type="button"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--color-text-dim)',
                      padding: '2px',
                      cursor: 'pointer',
                    }}
                    onClick={() => setShowNotifications(false)}
                    aria-label="Close notifications"
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>

              <div className="notification-list" role="feed" aria-busy="false">
                {notifications.length === 0 ? (
                  <div
                    style={{
                      padding: '24px 16px',
                      textAlign: 'center',
                      color: 'var(--color-text-dim)',
                      fontSize: '12px',
                    }}
                  >
                    <CheckCircle2 size={24} style={{ color: 'var(--color-success)', marginBottom: '8px' }} />
                    <p style={{ margin: 0, fontWeight: 500, color: 'var(--color-text-primary)' }}>
                      No Security Alerts
                    </p>
                    <span style={{ fontSize: '11px' }}>
                      All perimeter sectors are currently calm.
                    </span>
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`notification-item ${notif.read ? 'read' : 'unread'}`}
                      onClick={() => {
                        onSelectEventById(notif.event_id);
                        onMarkNotificationAsRead(notif.id);
                        setShowNotifications(false);
                      }}
                      role="article"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          onSelectEventById(notif.event_id);
                          onMarkNotificationAsRead(notif.id);
                          setShowNotifications(false);
                        }
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '6px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <StatusBadge type="risk" value={notif.risk_level || notif.severity} />
                          <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                            {notif.event_type}
                          </span>
                        </div>
                        {!notif.read && (
                          <button
                            type="button"
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: 'var(--color-text-dim)',
                              padding: '2px',
                              cursor: 'pointer',
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              onMarkNotificationAsRead(notif.id);
                            }}
                            title="Mark as read"
                            aria-label={`Mark notification ${notif.id} as read`}
                          >
                            <Check size={12} />
                          </button>
                        )}
                      </div>

                      <p style={{ color: 'var(--color-text-secondary)', margin: '4px 0', fontSize: '11px' }}>
                        {notif.message}
                      </p>

                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginTop: '4px',
                          fontSize: '10px',
                          color: 'var(--color-text-dim)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        <span>
                          {new Date(notif.timestamp).toLocaleTimeString()} UTC
                          {notif.is_demo ? ' • DEMO' : ' • LIVE'}
                        </span>
                        <span style={{ color: 'var(--color-accent-blue)', textDecoration: 'underline' }}>
                          View Details &rarr;
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Authenticated User Profile & Identity Switcher */}
        <div
          className="user-profile"
          onClick={onOpenLoginModal}
          role="button"
          tabIndex={0}
          aria-label="User identity profile. Click to sign in or switch roles."
          style={{ cursor: 'pointer' }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onOpenLoginModal?.();
            }
          }}
          title="Click to authenticate, switch account, or log out"
        >
          <div
            className="user-avatar"
            aria-hidden="true"
            style={{
              backgroundColor: currentUser
                ? currentUser.role === 'ADMIN'
                  ? '#7e22ce'
                  : '#0284c7'
                : '#475569',
              color: '#ffffff',
              fontWeight: 700,
            }}
          >
            {currentUser ? (currentUser.role === 'ADMIN' ? 'AD' : 'OP') : '??'}
          </div>
          <div className="user-meta">
            <span className="user-name">
              {currentUser ? currentUser.username : 'Not Authenticated'}
            </span>
            <span className="user-role">
              {currentUser
                ? `${currentUser.role === 'ADMIN' ? 'Administrator' : 'Watch Officer'} (${currentUser.role})`
                : 'Click to Sign In / Up'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
