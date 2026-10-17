import React from 'react';
import { Construction, ArrowLeft, ShieldAlert } from 'lucide-react';
import { NavigationPage } from '../types';

interface PlaceholderPageProps {
  pageId: NavigationPage;
  pageName: string;
  onBackToOverview: () => void;
}

const PAGE_DETAILS: Record<
  NavigationPage,
  { scheduledPhase: string; owner: string; description: string }
> = {
  overview: {
    scheduledPhase: 'Phase 1 (Active)',
    owner: 'Lead 1 (Frontend)',
    description: 'Operational overview dashboard',
  },
  monitoring: {
    scheduledPhase: 'Phase 2 (Video Feeds & Ingestion)',
    owner: 'Lead 1 (Frontend) & Lead 2 (CV Engine)',
    description: 'Multi-camera CCTV streaming viewer with interactive bounding boxes and zone overlay layers.',
  },
  events: {
    scheduledPhase: 'Phase 3 (Event Management)',
    owner: 'Lead 1 (Frontend) & Overall Lead (Backend API)',
    description: 'Full event audit history with filtering by camera, severity, status, and temporal range.',
  },
  cameras: {
    scheduledPhase: 'Phase 3 (Device Provisioning)',
    owner: 'Lead 1 (Frontend) & Lead 2 (CV Engine)',
    description: 'Management interface for adding, testing, and calibrating CCTV RTSP streams and resolutions.',
  },
  zones: {
    scheduledPhase: 'Phase 3 (Zone Geometry Calibration)',
    owner: 'Lead 1 (Frontend) & Lead 2 (CV Engine)',
    description: 'Interactive polygon drawing tool for defining restricted boundary areas on video feeds.',
  },
  analytics: {
    scheduledPhase: 'Phase 4 (Advanced Telemetry)',
    owner: 'Lead 1 (Frontend) & Overall Lead (Backend)',
    description: 'Aggregated statistical metrics, hourly distribution charts, and false-positive rates.',
  },
  health: {
    scheduledPhase: 'Phase 4 (System Operations)',
    owner: 'Lead 1 & Lead 3 (LinuxONE / Deployment)',
    description: 'Deep health probing, latency telemetry, memory metrics, and container status on IBM LinuxONE.',
  },
  settings: {
    scheduledPhase: 'Phase 5 (Handover & Config)',
    owner: 'Overall Lead & Lead 1',
    description: 'Threshold adjustments, API keys, webhook destinations, and operator role privileges.',
  },
};

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  pageId,
  pageName,
  onBackToOverview,
}) => {
  const details = PAGE_DETAILS[pageId] || {
    scheduledPhase: 'Future Phase',
    owner: 'Engineering Team',
    description: 'Under active development per SentinelAI roadmap.',
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 20px',
        textAlign: 'center',
        maxWidth: '640px',
        margin: '0 auto',
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '12px',
          backgroundColor: 'var(--color-bg-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-warning)',
          marginBottom: '16px',
          border: '1px solid var(--color-border-default)',
        }}
      >
        <Construction size={28} />
      </div>

      <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '8px' }}>
        {pageName} Module Not Implemented
      </h2>

      <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.6, marginBottom: '24px' }}>
        {details.description}
      </p>

      {/* Honest Phase Boundary Card */}
      <div
        style={{
          width: '100%',
          backgroundColor: 'var(--color-bg-card)',
          border: '1px solid var(--color-border-default)',
          borderRadius: 'var(--radius-md)',
          padding: '16px',
          textAlign: 'left',
          marginBottom: '24px',
          fontSize: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-text-highlight)', marginBottom: '8px' }}>
          <ShieldAlert size={14} />
          <strong>Project Phase Boundaries (IBM Datathon)</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--color-border-subtle)' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Target Phase:</span>
          <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>{details.scheduledPhase}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--color-border-subtle)' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Module Ownership:</span>
          <span style={{ color: 'var(--color-text-primary)' }}>{details.owner}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Current Status:</span>
          <span className="badge badge-pending">PENDING PHASE AUTHORIZATION</span>
        </div>
      </div>

      <button
        type="button"
        className="btn-secondary"
        onClick={onBackToOverview}
        style={{ padding: '8px 16px', fontSize: '13px' }}
      >
        <ArrowLeft size={14} />
        Return to Overview Dashboard
      </button>
    </div>
  );
};
