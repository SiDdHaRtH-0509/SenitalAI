import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopHeader } from './TopHeader';
import { NavigationPage } from '../../types';
import { DEMO_DATA_NOTICE } from '../../data/demoData';
import { Info } from 'lucide-react';

interface AppShellProps {
  activePage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
  children: React.ReactNode;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  activePage,
  onNavigate,
  children,
  searchQuery,
  onSearchChange,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="app-container">
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
            <span className="demo-banner-badge">Notice</span>
            <Info size={14} />
            <span>
              <strong>Phase 1 UI Demonstration:</strong> {DEMO_DATA_NOTICE}. Real-time backend & CV streaming integration will connect in subsequent phases.
            </span>
          </div>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
            Status: Frontend Operational (Local)
          </span>
        </div>

        {/* Top Header */}
        <TopHeader
          activePage={activePage}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
          searchQuery={searchQuery}
          onSearchChange={onSearchChange}
        />

        {/* Page Content Body */}
        <main className="page-content" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
};
