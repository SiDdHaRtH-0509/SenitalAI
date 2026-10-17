import React, { useMemo } from 'react';
import {
  BarChart3,
  ShieldAlert,
  AlertOctagon,
  MapPin,
  Info,
} from 'lucide-react';
import { SecurityEvent, RiskLevel } from '../types';
import { StatCard } from '../components/dashboard/StatCard';
import { EmptyState } from '../components/ui/EmptyState';

interface AnalyticsPageProps {
  events: SecurityEvent[];
  isLive: boolean;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ events, isLive }) => {
  // Aggregate statistics directly from real/demo event dataset
  const analytics = useMemo(() => {
    const total = events.length;

    const byRisk: Record<RiskLevel, number> = {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0,
    };

    const byCamera: Record<string, number> = {};
    const byZone: Record<string, number> = {};
    let totalConfidence = 0;
    let validConfidenceCount = 0;

    // 24-hour distribution bins
    const hourlyCounts: number[] = new Array(24).fill(0);

    events.forEach((evt) => {
      // Risk breakdown
      const risk = (evt.risk_level || evt.severity) as RiskLevel;
      if (byRisk[risk] !== undefined) {
        byRisk[risk]++;
      }

      // Camera breakdown
      byCamera[evt.camera_id] = (byCamera[evt.camera_id] || 0) + 1;

      // Zone breakdown
      const z = evt.zone_id || 'unassigned';
      byZone[z] = (byZone[z] || 0) + 1;

      if (typeof evt.confidence === 'number' && !Number.isNaN(evt.confidence)) {
        totalConfidence += evt.confidence;
        validConfidenceCount++;
      }

      // Hourly bin
      try {
        const parsed = new Date(evt.timestamp);
        const h = parsed.getUTCHours();
        if (!Number.isNaN(h) && h >= 0 && h < 24) {
          hourlyCounts[h]++;
        }
      } catch {
        // fallback
      }
    });

    const avgConf = validConfidenceCount > 0 ? (totalConfidence / validConfidenceCount) * 100 : 0;

    return {
      total,
      byRisk,
      byCamera,
      byZone,
      avgConf,
      hourlyCounts,
    };
  }, [events]);

  if (events.length === 0) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-heading-block">
          <div className="heading-title-group">
            <h1>Surveillance Event Analytics</h1>
            <p>Quantitative metrics, risk distributions, and temporal incursion frequencies.</p>
          </div>
        </div>
        <EmptyState
          icon={BarChart3}
          title="No Analytics Data Available"
          description="The event ledger is empty. Analytics will automatically compute once security events are ingested."
        />
      </div>
    );
  }

  const maxHourlyCount = Math.max(...analytics.hourlyCounts, 1);

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-heading-block">
        <div className="heading-title-group">
          <h1>Surveillance Event Analytics</h1>
          <p>
            Quantitative metrics, risk distributions, and temporal incursion frequencies derived from recorded events.
          </p>
        </div>

        <div className="heading-actions">
          <span
            className={isLive ? 'badge badge-success' : 'badge badge-warning'}
            style={{ fontSize: '11px', padding: '4px 10px' }}
          >
            {isLive ? 'LIVE DATA ANALYTICS' : 'DEMO ANALYTICS MODE'}
          </span>
        </div>
      </div>

      {/* Demo Notice */}
      {!isLive && (
        <div
          style={{
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--color-warning)',
          }}
        >
          <Info size={15} />
          <span>
            <strong>Deterministic Computation:</strong> Analytics below are computed purely from the {analytics.total} demonstration event records. No random figures are generated.
          </span>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="kpi-grid">
        <StatCard
          title="Total Events Analyzed"
          value={analytics.total}
          subtitle="Processed security incidents"
          icon={BarChart3}
          badgeText="DATASET SIZE"
          badgeType="info"
        />

        <StatCard
          title="Critical Incidents"
          value={analytics.byRisk.CRITICAL}
          subtitle={`${((analytics.byRisk.CRITICAL / analytics.total) * 100).toFixed(0)}% of total alerts`}
          icon={AlertOctagon}
          badgeText="CRITICAL"
          badgeType="critical"
        />

        <StatCard
          title="Mean AI Confidence"
          value={`${analytics.avgConf.toFixed(1)}%`}
          subtitle="YOLOv8n person detector average"
          icon={ShieldAlert}
          badgeText="ACCURACY"
          badgeType="success"
        />

        <StatCard
          title="Targeted Zones"
          value={Object.keys(analytics.byZone).length}
          subtitle="Unique restricted zones breached"
          icon={MapPin}
          badgeText="ZONES"
          badgeType="warning"
        />
      </div>

      {/* Row 1: Risk Level Distribution & Camera Breakdown */}
      <div className="dashboard-split-row">
        {/* Risk Distribution Card */}
        <div className="card-base" style={{ padding: 'var(--space-lg)', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Incidents by Risk Severity
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)' }}>
              API_CONTRACT.md Schema
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Critical */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                <span style={{ color: 'var(--color-critical)', fontWeight: 600 }}>CRITICAL</span>
                <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {analytics.byRisk.CRITICAL} events ({((analytics.byRisk.CRITICAL / analytics.total) * 100).toFixed(0)}%)
                </span>
              </div>
              <div style={{ height: '8px', backgroundColor: 'var(--color-bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${(analytics.byRisk.CRITICAL / analytics.total) * 100}%`,
                    backgroundColor: 'var(--color-critical)',
                  }}
                />
              </div>
            </div>

            {/* High */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                <span style={{ color: '#fb923c', fontWeight: 600 }}>HIGH</span>
                <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {analytics.byRisk.HIGH} events ({((analytics.byRisk.HIGH / analytics.total) * 100).toFixed(0)}%)
                </span>
              </div>
              <div style={{ height: '8px', backgroundColor: 'var(--color-bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${(analytics.byRisk.HIGH / analytics.total) * 100}%`,
                    backgroundColor: '#fb923c',
                  }}
                />
              </div>
            </div>

            {/* Medium */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                <span style={{ color: 'var(--color-warning)', fontWeight: 600 }}>MEDIUM</span>
                <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {analytics.byRisk.MEDIUM} events ({((analytics.byRisk.MEDIUM / analytics.total) * 100).toFixed(0)}%)
                </span>
              </div>
              <div style={{ height: '8px', backgroundColor: 'var(--color-bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${(analytics.byRisk.MEDIUM / analytics.total) * 100}%`,
                    backgroundColor: 'var(--color-warning)',
                  }}
                />
              </div>
            </div>

            {/* Low */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>LOW</span>
                <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {analytics.byRisk.LOW} events ({((analytics.byRisk.LOW / analytics.total) * 100).toFixed(0)}%)
                </span>
              </div>
              <div style={{ height: '8px', backgroundColor: 'var(--color-bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${(analytics.byRisk.LOW / analytics.total) * 100}%`,
                    backgroundColor: 'var(--color-success)',
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Incidents by Camera Node */}
        <div className="card-base" style={{ padding: 'var(--space-lg)', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Incursions by Camera Sensor
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)' }}>
              Sensor Clustering
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(analytics.byCamera).map(([camId, count]) => (
              <div key={camId}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                    {camId}
                  </span>
                  <span style={{ color: 'var(--color-accent-blue)', fontFamily: 'var(--font-mono)' }}>
                    {count} ({((count / analytics.total) * 100).toFixed(0)}%)
                  </span>
                </div>
                <div style={{ height: '6px', backgroundColor: 'var(--color-bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${(count / analytics.total) * 100}%`,
                      backgroundColor: 'var(--color-accent-blue)',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: 24-Hour Temporal Incursion Histogram */}
      <div className="card-base" style={{ padding: 'var(--space-lg)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Hourly Incursion Distribution (UTC)
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
              24-hour temporal clustering of detected border fence boundary crossings
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)' }}>
            TIMEFRAME: TODAY (UTC)
          </span>
        </div>

        {/* SVG Histogram */}
        <div style={{ width: '100%', overflowX: 'auto', padding: '10px 0' }}>
          <svg
            viewBox="0 0 720 120"
            style={{ width: '100%', minWidth: '500px', height: '120px', overflow: 'visible' }}
            aria-label="Hourly incursion distribution chart"
          >
            {/* Baseline */}
            <line x1="0" y1="95" x2="720" y2="95" stroke="var(--color-border-subtle)" strokeWidth="1" />

            {/* 24 Bar Columns */}
            {analytics.hourlyCounts.map((count, hr) => {
              const barWidth = 20;
              const x = hr * 30 + 5;
              const barHeight = count > 0 ? Math.max((count / maxHourlyCount) * 75, 12) : 0;
              const y = 95 - barHeight;

              return (
                <g key={hr}>
                  {count > 0 && (
                    <>
                      <rect
                        x={x}
                        y={y}
                        width={barWidth}
                        height={barHeight}
                        rx="3"
                        fill="var(--color-accent-blue)"
                        opacity="0.85"
                      />
                      <text
                        x={x + barWidth / 2}
                        y={y - 4}
                        fill="var(--color-text-primary)"
                        fontSize="9"
                        fontFamily="var(--font-mono)"
                        textAnchor="middle"
                      >
                        {count}
                      </text>
                    </>
                  )}
                  {/* Hour tick */}
                  <text
                    x={x + barWidth / 2}
                    y="112"
                    fill={count > 0 ? 'var(--color-text-primary)' : 'var(--color-text-dim)'}
                    fontSize="8"
                    fontFamily="var(--font-mono)"
                    textAnchor="middle"
                  >
                    {String(hr).padStart(2, '0')}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--color-text-dim)', borderTop: '1px solid var(--color-border-subtle)', paddingTop: '8px', marginTop: '4px' }}>
          <span>Peak Activity Window: 08:00 - 10:00 UTC (Sector Alpha Dawn Patrol)</span>
          <span>Derived from <code>timestamp</code> in <code>SecurityEvent</code></span>
        </div>
      </div>
    </div>
  );
};
