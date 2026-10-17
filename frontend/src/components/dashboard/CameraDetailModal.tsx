import React from 'react';
import { X, Camera, VideoOff, Server, Info } from 'lucide-react';
import { CameraInfo } from '../../types';
import { StatusBadge } from '../ui/StatusBadge';

interface CameraDetailModalProps {
  camera: CameraInfo | null;
  onClose: () => void;
}

export const CameraDetailModal: React.FC<CameraDetailModalProps> = ({ camera, onClose }) => {
  if (!camera) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '580px' }}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Camera size={18} style={{ color: 'var(--color-accent-blue)' }} />
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Camera Details: {camera.camera_id}
              </h3>
              <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                {camera.name}
              </span>
            </div>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close modal">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {camera.is_demo && (
            <div
              style={{
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '11px',
                color: 'var(--color-warning)',
              }}
            >
              <Info size={14} />
              <span>
                <strong>Demonstration Node:</strong> Camera record configured for datathon prototype verification.
              </span>
            </div>
          )}

          {/* Feed Preview Wireframe (Honest Disconnected State) */}
          <div
            style={{
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px dashed var(--color-border-default)',
              borderRadius: 'var(--radius-sm)',
              aspectRatio: '16 / 9',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              textAlign: 'center',
              padding: '20px',
            }}
          >
            <VideoOff size={32} style={{ color: 'var(--color-text-dim)', marginBottom: '8px' }} />
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              No Camera Stream Connected
            </span>
            <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', maxWidth: '360px', marginTop: '4px' }}>
              Real-time WebRTC / HLS feed bridge is pending edge CCTV gateway deployment.
            </span>
            <div
              style={{
                position: 'absolute',
                bottom: '10px',
                left: '10px',
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-text-dim)',
                backgroundColor: 'rgba(0, 0, 0, 0.6)',
                padding: '2px 6px',
                borderRadius: '2px',
              }}
            >
              SOURCE: {camera.resolution} @ {camera.fps} FPS
            </div>
          </div>

          {/* Technical Specifications */}
          <div>
            <h4 style={{ fontSize: '12px', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
              Hardware & Ingestion Specifications
            </h4>
            <div className="detail-row">
              <span className="detail-label">Camera Identifier:</span>
              <span className="detail-value">{camera.camera_id}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Geographic Location:</span>
              <span className="detail-value">{camera.location}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Connection Status:</span>
              <span className="detail-value">
                <StatusBadge type="status" value={camera.status} />
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Target Stream URI:</span>
              <span className="detail-value" style={{ wordBreak: 'break-all' }}>
                {camera.stream_uri || 'Pending edge provisioning'}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Assigned Detection Zone:</span>
              <span className="detail-value">{camera.zone_id}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Target FPS / Resolution:</span>
              <span className="detail-value">{camera.fps} FPS • {camera.resolution}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Heartbeat Ping:</span>
              <span className="detail-value">{camera.last_ping || 'Awaiting live edge agent'}</span>
            </div>
          </div>

          {/* Architecture Boundary Note */}
          <div
            style={{
              backgroundColor: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
              fontSize: '11px',
              color: 'var(--color-text-muted)',
              display: 'flex',
              gap: '8px',
            }}
          >
            <Server size={14} style={{ color: 'var(--color-accent-blue)', flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong style={{ color: 'var(--color-text-primary)' }}>Ingestion Architecture:</strong> The Python CV engine (<code style={{ color: 'var(--color-accent-cyan)' }}>sentinel_cv</code>) ingests authorized video via <code style={{ color: 'var(--color-accent-cyan)' }}>OpenCVVideoSource</code> on the edge gateway. Video stream forwarding to this browser UI is scheduled for Phase 3.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
