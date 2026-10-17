import React from 'react';
import {
  Shield,
  LayoutDashboard,
  Video,
  AlertTriangle,
  Camera,
  MapPin,
  BarChart3,
  Activity,
  Settings,
  Server,
  X,
  LucideIcon,
} from 'lucide-react';
import { NavigationPage } from '../../types';

interface SidebarProps {
  activePage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

interface NavItemDef {
  id: NavigationPage;
  label: string;
  icon: LucideIcon;
  badge?: string;
}

const NAV_ITEMS: NavItemDef[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'monitoring', label: 'Live Monitoring', icon: Video },
  { id: 'events', label: 'Security Events', icon: AlertTriangle },
  { id: 'cameras', label: 'Cameras', icon: Camera },
  { id: 'zones', label: 'Restricted Zones', icon: MapPin },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'health', label: 'System Health', icon: Activity },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  isOpenMobile,
  onCloseMobile,
}) => {
  return (
    <>
      <div
        className={`sidebar-overlay ${isOpenMobile ? 'mobile-open' : ''}`}
        onClick={onCloseMobile}
        aria-hidden="true"
      />
      <aside className={`app-sidebar ${isOpenMobile ? 'mobile-open' : ''}`} aria-label="Main Navigation">
        {/* Brand Header */}
        <div className="sidebar-brand">
          <div className="brand-icon" aria-hidden="true">
            <Shield size={18} />
          </div>
          <div className="brand-info">
            <span className="brand-title">
              Sentinel<span>AI</span>
            </span>
            <span className="brand-subtitle">Border Surveillance</span>
          </div>
          <button
            className="mobile-menu-btn"
            style={{ marginLeft: 'auto', display: isOpenMobile ? 'flex' : 'none' }}
            onClick={onCloseMobile}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          <div className="nav-section-label">Operations Center</div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;

            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => {
                  onNavigate(item.id);
                  onCloseMobile();
                }}
                aria-current={isActive ? 'page' : undefined}
              >
                <div className="nav-item-left">
                  <Icon size={16} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="nav-badge-pending">{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer Deployment Node Info */}
        <div className="sidebar-footer">
          <div className="node-status-card">
            <div className="node-status-header">
              <span className="node-label">Platform Node</span>
              <span className="node-badge">LOCAL / IBM z</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-secondary)' }}>
              <Server size={11} />
              <span style={{ fontSize: '11px', fontWeight: 500 }}>Phase 2 Complete</span>
            </div>
            <div className="node-location">Sector Alpha • Command Center</div>
          </div>
        </div>
      </aside>
    </>
  );
};
