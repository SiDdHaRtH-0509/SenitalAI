import React from 'react';
import { Video, VideoOff, Radio, Eye } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { CameraInfo } from '../../types';

interface MonitoringPanelProps {
  cameras: CameraInfo[];
}

export const MonitoringPanel: React.FC<MonitoringPanelProps> = ({ cameras }) => {
  return (
    <div className="monitoring-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Video size={16} style={{ color: 'var(--color-accent-blue)' }} />
          <span>Surveillance Feeds (Live Monitoring)</span>
        </div>
        <span
          className="badge badge-disconnected"
          title="Video streaming pipeline integration pending"
        >
          <span className="badge-dot" />
          0 FEEDS ACTIVE
        </span>
      </div>

      <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
        Live video ingestion and real-time bounding box overlays will appear once CCTV stream endpoints are connected in Phase 2.
      </p>

      {/* Wireframe Grid Representing Configured Edge Camera Slots */}
      <div className="feed-placeholder-grid">
        {cameras.map((cam) => (
          <div key={cam.camera_id} className="feed-slot">
            <span className="feed-slot-badge">{cam.camera_id}</span>
            <div className="feed-slot-icon">
              <VideoOff size={28} />
            </div>
            <span className="feed-slot-label">{cam.name}</span>
            <span className="feed-slot-status">
              {cam.location} • {cam.resolution} @ {cam.fps} FPS
            </span>
            <div
              style={{
                marginTop: '8px',
                fontSize: '10px',
                color: 'var(--color-text-dim)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Radio size={10} />
              <span>Awaiting Stream Source</span>
            </div>
          </div>
        ))}
      </div>

      {/* Honest Empty State Summary */}
      <EmptyState
        icon={Eye}
        title="Live Monitoring Integration Pending"
        description="The CV engine currently supports file and deterministic replay ingestion. Live RTSP/HLS surveillance stream decoding will be connected to the UI in Phase 2."
        technicalNote="Target: WebRTC / HLS stream consumer via OpenCV video source"
      />
    </div>
  );
};
