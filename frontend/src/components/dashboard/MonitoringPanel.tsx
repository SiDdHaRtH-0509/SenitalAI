import React, { useState } from 'react';
import { Video, VideoOff, Radio, Eye, Film } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { CameraInfo } from '../../types';
import { VideoAnalyticsDemoPlayer } from './VideoAnalyticsDemoPlayer';

interface MonitoringPanelProps {
  cameras: CameraInfo[];
  onRefresh?: () => Promise<void>;
}

export const MonitoringPanel: React.FC<MonitoringPanelProps> = ({ cameras, onRefresh }) => {
  const [viewMode, setViewMode] = useState<'demo' | 'grid'>('demo');

  return (
    <div className="monitoring-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Video size={16} style={{ color: 'var(--color-accent-blue)' }} />
          <span>Surveillance Feeds (Live Monitoring)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', backgroundColor: 'var(--color-bg-secondary)', borderRadius: '4px', padding: '2px' }}>
            <button
              type="button"
              onClick={() => setViewMode('demo')}
              style={{
                border: 'none',
                background: viewMode === 'demo' ? 'var(--color-accent-blue)' : 'transparent',
                color: viewMode === 'demo' ? '#fff' : 'var(--color-text-muted)',
                borderRadius: '3px',
                padding: '3px 8px',
                fontSize: '10px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Film size={11} />
              CCTV Video Demo
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              style={{
                border: 'none',
                background: viewMode === 'grid' ? 'var(--color-accent-blue)' : 'transparent',
                color: viewMode === 'grid' ? '#fff' : 'var(--color-text-muted)',
                borderRadius: '3px',
                padding: '3px 8px',
                fontSize: '10px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Camera Grid ({cameras.length})
            </button>
          </div>
          <span
            className="badge badge-connected"
            title="Interactive YOLOv8n video analytics active"
            style={{ fontSize: '10px' }}
          >
            <span className="badge-dot" style={{ backgroundColor: '#22c55e' }} />
            VIDEO DEMO ACTIVE
          </span>
        </div>
      </div>

      {viewMode === 'demo' ? (
        <div style={{ marginTop: '8px' }}>
          <VideoAnalyticsDemoPlayer compact={true} onEventSubmitted={onRefresh} />
        </div>
      ) : (
        <>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
            Configured CCTV edge cameras connected to backend stream registry.
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
                  <span>Stream Ingestion Active</span>
                </div>
              </div>
            ))}
          </div>

          <EmptyState
            icon={Eye}
            title="Stream Decoders Online"
            description="Continuous edge processing active via OpenCV & YOLOv8n. Switch to 'CCTV Video Demo' above to interact with live surveillance video footage."
            technicalNote="Target: WebRTC / HLS stream consumer via OpenCV video source"
          />
        </>
      )}
    </div>
  );
};

