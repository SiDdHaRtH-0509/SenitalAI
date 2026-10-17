import React, { useState } from 'react';
import { VideoOff, Radio, Eye, Filter, RefreshCw, Info } from 'lucide-react';
import { CameraInfo } from '../types';
import { StatusBadge } from '../components/ui/StatusBadge';
import { CameraDetailModal } from '../components/dashboard/CameraDetailModal';
import { EmptyState } from '../components/ui/EmptyState';

interface MonitoringPageProps {
  cameras: CameraInfo[];
  onRefresh: () => Promise<void>;
  searchFilter: string;
}

export const MonitoringPage: React.FC<MonitoringPageProps> = ({
  cameras,
  onRefresh,
  searchFilter,
}) => {
  const [selectedCamera, setSelectedCamera] = useState<CameraInfo | null>(null);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ONLINE' | 'DISCONNECTED'>('ALL');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredCameras = cameras.filter((cam) => {
    const matchesSearch =
      !searchFilter.trim() ||
      cam.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      cam.camera_id.toLowerCase().includes(searchFilter.toLowerCase()) ||
      cam.location.toLowerCase().includes(searchFilter.toLowerCase()) ||
      cam.zone_id.toLowerCase().includes(searchFilter.toLowerCase());

    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'ONLINE' && cam.status === 'ONLINE') ||
      (statusFilter === 'DISCONNECTED' && (cam.status === 'DISCONNECTED' || cam.status === 'OFFLINE'));

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="dashboard-heading-block">
        <div className="heading-title-group">
          <h1>Live Surveillance Monitoring</h1>
          <p>
            Real-time CCTV edge camera feeds across perimeter sectors. Video stream forwarding and live bounding box rendering.
          </p>
        </div>

        <div className="heading-actions">
          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Filter size={13} style={{ color: 'var(--color-text-dim)' }} />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="search-input"
              style={{ width: 'auto', padding: '6px 10px', fontSize: '11px' }}
              aria-label="Filter cameras by status"
            >
              <option value="ALL">All Nodes ({cameras.length})</option>
              <option value="DISCONNECTED">Disconnected (4)</option>
              <option value="ONLINE">Online (0)</option>
            </select>
          </div>

          <button
            type="button"
            className="btn-secondary"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw size={13} className={isRefreshing ? 'spin-icon' : ''} />
            {isRefreshing ? 'Polling Streams...' : 'Poll Feeds'}
          </button>
        </div>
      </div>

      {/* Honest Technical Status Notice */}
      <div
        style={{
          backgroundColor: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: 'var(--color-warning)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={16} />
          <span>
            <strong>Stream Ingestion Status:</strong> No live CCTV video streams are currently broadcasting to this browser. The CV engine processes video files on edge nodes via OpenCV; web streaming integration is scheduled for later phases.
          </span>
        </div>
        <span className="badge badge-disconnected" style={{ whiteSpace: 'nowrap' }}>
          0 OF {cameras.length} FEEDS ACTIVE
        </span>
      </div>

      {/* Camera Feeds Grid */}
      {filteredCameras.length === 0 ? (
        <EmptyState
          icon={VideoOff}
          title="No Cameras Found"
          description="No camera edge nodes match the selected search or status criteria."
          actionText="Clear Filters"
          onAction={() => setStatusFilter('ALL')}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: 'var(--space-lg)',
          }}
        >
          {filteredCameras.map((cam) => (
            <div
              key={cam.camera_id}
              className="card-base"
              style={{
                padding: 'var(--space-md)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-sm)',
                cursor: 'pointer',
              }}
              onClick={() => setSelectedCamera(cam)}
              title="Click to view stream specifications"
            >
              {/* Card Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                      {cam.name}
                    </span>
                    {cam.is_demo && (
                      <span
                        style={{
                          fontSize: '9px',
                          backgroundColor: 'var(--color-bg-subtle)',
                          color: 'var(--color-text-dim)',
                          padding: '1px 4px',
                          borderRadius: '2px',
                        }}
                      >
                        DEMO
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                    ID: {cam.camera_id} • {cam.location}
                  </span>
                </div>
                <StatusBadge type="status" value={cam.status} />
              </div>

              {/* Video Feed Area (Truthful Disconnected Wireframe) */}
              <div className="feed-slot" style={{ marginTop: '4px' }}>
                <span className="feed-slot-badge">{cam.camera_id}</span>
                <VideoOff size={32} className="feed-slot-icon" />
                <span className="feed-slot-label">No camera stream connected</span>
                <span className="feed-slot-status">
                  Target: {cam.resolution} @ {cam.fps} FPS
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
                  <span>Stream integration pending</span>
                </div>
              </div>

              {/* Card Footer */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '11px',
                  color: 'var(--color-text-dim)',
                  paddingTop: '6px',
                  borderTop: '1px solid var(--color-border-subtle)',
                }}
              >
                <span>Assigned Zone: <code>{cam.zone_id}</code></span>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ padding: '2px 8px', fontSize: '10px' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedCamera(cam);
                  }}
                >
                  Inspect Node
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Global Empty State Notice */}
      <EmptyState
        icon={Eye}
        title="Surveillance Gateway Connection Pending"
        description="Edge nodes running SentinelAI Computer Vision can ingest local files or RTSP streams. In Phase 3, low-latency video tunneling will stream encoded H.264 frames to this monitoring interface."
        technicalNote="Planned Ingestion Protocol: WebRTC / RTSP-over-WebSocket Bridge"
      />

      {/* Camera Detail Inspector Modal */}
      <CameraDetailModal
        camera={selectedCamera}
        onClose={() => setSelectedCamera(null)}
      />
    </div>
  );
};
