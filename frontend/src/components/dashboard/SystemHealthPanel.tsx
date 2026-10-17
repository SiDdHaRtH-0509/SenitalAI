import React, { useState } from 'react';
import { Activity, RefreshCw, Server, Cpu, Database, Monitor } from 'lucide-react';
import { SystemHealthState } from '../../types';
import { StatusBadge } from '../ui/StatusBadge';

interface SystemHealthPanelProps {
  healthState: SystemHealthState;
  onRefreshHealth: () => Promise<void>;
}

export const SystemHealthPanel: React.FC<SystemHealthPanelProps> = ({
  healthState,
  onRefreshHealth,
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefreshHealth();
    } finally {
      setIsRefreshing(false);
    }
  };

  const getServiceIcon = (id: string) => {
    switch (id) {
      case 'cv_engine':
        return <Cpu size={15} style={{ color: 'var(--color-accent-cyan)' }} />;
      case 'backend_api':
        return <Server size={15} style={{ color: 'var(--color-accent-blue)' }} />;
      case 'database':
        return <Database size={15} style={{ color: 'var(--color-warning)' }} />;
      case 'dashboard':
      default:
        return <Monitor size={15} style={{ color: 'var(--color-success)' }} />;
    }
  };

  return (
    <div className="system-health-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Activity size={16} style={{ color: 'var(--color-accent-cyan)' }} />
          <span>Subsystem Health & Connectivity</span>
        </div>
        <button
          type="button"
          className="btn-secondary"
          onClick={handleRefresh}
          disabled={isRefreshing}
          style={{ padding: '3px 8px', fontSize: '11px' }}
          title="Probe backend health endpoints"
        >
          <RefreshCw size={11} className={isRefreshing ? 'spin-icon' : ''} />
          {isRefreshing ? 'Checking...' : 'Probe Subsystems'}
        </button>
      </div>

      <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>
        Live system statuses are verified against <code>/api/health</code>. Unconnected services are honestly indicated.
      </p>

      <div className="health-list">
        {Object.values(healthState).map((svc) => (
          <div key={svc.id} className="health-card">
            <div className="health-card-top">
              <div className="health-card-name">
                {getServiceIcon(svc.id)}
                <span>{svc.name}</span>
              </div>
              <StatusBadge type="health" value={svc.status} label={svc.label} />
            </div>

            <p className="health-card-desc">{svc.description}</p>

            <div className="health-card-footer">
              <span>{svc.details || 'Component: Local'}</span>
              <span>Updated: {svc.lastChecked}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
