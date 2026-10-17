import React from 'react';
import { BarChart2, TrendingUp, Info } from 'lucide-react';

export const ActivitySummary: React.FC = () => {
  return (
    <div className="activity-summary-panel">
      <div className="panel-header">
        <div className="panel-title">
          <BarChart2 size={16} style={{ color: 'var(--color-accent-blue)' }} />
          <span>Surveillance Activity Trends (Hourly Incursions)</span>
        </div>
        <span className="badge badge-neutral" style={{ fontSize: '10px' }}>
          TELEMETRY PENDING
        </span>
      </div>

      <div className="chart-placeholder">
        <TrendingUp size={24} style={{ opacity: 0.4 }} />
        <span style={{ fontWeight: 500 }}>Temporal Event Distribution Graph</span>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px',
            color: 'var(--color-text-dim)',
          }}
        >
          <Info size={12} />
          <span>
            Hourly trend visualizer will render once time-series aggregation endpoint (<code>GET /api/stats</code>) is deployed.
          </span>
        </div>
      </div>
    </div>
  );
};
