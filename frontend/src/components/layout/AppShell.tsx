import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopHeader } from './TopHeader';
import { NavigationPage, ConnectionState, SecurityNotification, UserProfile } from '../../types';
import { DEMO_DATA_NOTICE } from '../../data/demoData';
import { Info } from 'lucide-react';

interface AppShellProps {
  activePage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
  children: React.ReactNode;
  searchQuery: string;
  onSearchChange: (q: string) => void;
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

export const AppShell: React.FC<AppShellProps> = ({
  activePage,
  onNavigate,
  children,
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="app-container">
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        onNavigate={onNavigate}
        isOpenMobile={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        {/* Global Demo Notice Banner */}
        <div className="demo-banner" role="status">
          <div className="demo-banner-content">
            <span className="demo-banner-badge">Phase 4 Notice</span>
            <Info size={14} />
            <span>
              <strong>SentinelAI Telemetry:</strong>{' '}
              {isLive ? (
                <span style={{ color: 'var(--color-success)' }}>
                  Connected to live backend stream. Real-time events active.
                </span>
              ) : (
                <>
                  {DEMO_DATA_NOTICE}. Real-time monitoring engine active in offline demonstration fallback mode.
                </>
              )}
            </span>
          </div>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
            Status: {isLive ? 'Backend Live' : 'Offline / Demonstration Mode'}
          </span>
        </div>

        {/* Top Header */}
        <TopHeader
          activePage={activePage}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
          searchQuery={searchQuery}
          onSearchChange={onSearchChange}
          connectionState={connectionState}
          isLive={isLive}
          lastRefreshTime={lastRefreshTime}
          notifications={notifications}
          onMarkNotificationAsRead={onMarkNotificationAsRead}
          onMarkAllNotificationsAsRead={onMarkAllNotificationsAsRead}
          onSelectEventById={onSelectEventById}
          onManualRefresh={onManualRefresh}
          isRefreshing={isRefreshing}
          currentUser={currentUser}
          onOpenLoginModal={onOpenLoginModal}
        />

        {/* Page Content Body */}
        <main className="page-content" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
};
