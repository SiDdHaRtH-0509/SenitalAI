import React, { useState, useEffect } from 'react';
import { X, Camera, VideoOff, Server, Play, Square } from 'lucide-react';
import { CameraInfo, CameraWorkerStatus } from '../../types';
import { getApiBaseUrl } from '../../services/apiClient';

interface CameraDetailModalProps {
  camera: CameraInfo | null;
  workerStatus?: CameraWorkerStatus;
  onClose: () => void;
  onStartWorker?: (cameraId: string, replayMode: boolean) => Promise<void>;
  onStopWorker?: (cameraId: string) => Promise<void>;
  isProcessing?: boolean;
}

export const CameraDetailModal: React.FC<CameraDetailModalProps> = ({
  camera,
  workerStatus,
  onClose,
  onStartWorker,
  onStopWorker,
  isProcessing = false,
}) => {
  const [snapshotTimestamp, setSnapshotTimestamp] = useState<number>(Date.now());
  const [snapshotError, setSnapshotError] = useState<boolean>(false);

  // Auto-refresh live snapshot every 2 seconds if worker is active
  useEffect(() => {
    if (!camera || !workerStatus?.is_running) return;
    const interval = setInterval(() => {
      setSnapshotTimestamp(Date.now());
      setSnapshotError(false);
    }, 2000);
    return () => clearInterval(interval);
  }, [camera, workerStatus?.is_running]);

  if (!camera) return null;

  const isRunning = workerStatus?.is_running ?? false;
  const connState = workerStatus?.connection_state ?? (camera.status === 'ONLINE' ? 'READY' : 'OFFLINE');
  const snapshotUrl = `${getApiBaseUrl()}/api/cameras/${camera.camera_id}/snapshot?t=${snapshotTimestamp}`;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '640px' }}>
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
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Worker Connection State Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor:
                    connState === 'CONNECTED'
                      ? 'var(--color-risk-low)'
                      : connState === 'CONNECTING' || connState === 'RECONNECTING'
                      ? 'var(--color-warning)'
                      : connState === 'FAILED' || connState === 'ERROR'
                      ? 'var(--color-risk-critical)'
                      : 'var(--color-text-dim)',
                  display: 'inline-block',
                }}
              />
              <div>
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  Worker State: {connState}
                </span>
                <span style={{ display: 'block', fontSize: '10px', color: 'var(--color-text-dim)' }}>
                  {isRunning ? 'Continuous YOLOv8n inference loop active' : 'Analytics processing stopped'}
                </span>
              </div>
            </div>

            {/* Start / Stop Controls */}
            <div style={{ display: 'flex', gap: '6px' }}>
              {isRunning ? (
                <button
                  type="button"
                  className="btn-secondary"
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderColor: 'rgba(239, 68, 68, 0.4)',
                    color: 'var(--color-risk-critical)',
                    fontSize: '11px',
                    padding: '5px 10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                  disabled={isProcessing}
                  onClick={() => onStopWorker && onStopWorker(camera.camera_id)}
                >
                  <Square size={12} />
                  Stop Analytics
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="btn-primary"
                    style={{
                      fontSize: '11px',
                      padding: '5px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                    disabled={isProcessing}
                    onClick={() => onStartWorker && onStartWorker(camera.camera_id, false)}
                  >
                    <Play size={12} />
                    Start Live RTSP
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{
                      fontSize: '11px',
                      padding: '5px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                    disabled={isProcessing}
                    onClick={() => onStartWorker && onStartWorker(camera.camera_id, true)}
                  >
                    Demo Replay
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Video Preview / Live Inspection Snapshot */}
          <div
            style={{
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-sm)',
              aspectRatio: '16 / 9',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              textAlign: 'center',
              overflow: 'hidden',
            }}
          >
            {isRunning && !snapshotError ? (
              <img
                src={snapshotUrl}
                alt={`Live inspection preview for ${camera.camera_id}`}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={() => setSnapshotError(true)}
              />
            ) : (
              <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <VideoOff size={32} style={{ color: 'var(--color-text-dim)', marginBottom: '8px' }} />
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                  {isRunning ? 'Acquiring Real-Time Snapshot...' : 'Analytics Processing Inactive'}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', maxWidth: '380px', marginTop: '4px' }}>
                  {isRunning
                    ? 'Frame decoded on edge pipeline. Polling live preview snapshot.'
                    : 'Click "Start Live RTSP" or "Demo Replay" above to activate continuous video analytics.'}
                </span>
              </div>
            )}

            {/* Overlay Badges */}
            <div
              style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                fontSize: '10px',
                fontWeight: 600,
                color: '#fff',
                backgroundColor: isRunning ? 'rgba(34, 197, 94, 0.85)' : 'rgba(100, 116, 139, 0.85)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              {isRunning && <span className="pulse-indicator" />}
              {isRunning ? 'AI ANALYTICS ONLINE' : 'INACTIVE'}
            </div>

            <div
              style={{
                position: 'absolute',
                bottom: '10px',
                left: '10px',
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-text-dim)',
                backgroundColor: 'rgba(0, 0, 0, 0.75)',
                padding: '2px 6px',
                borderRadius: '2px',
              }}
            >
              SPEC: {camera.resolution} @ {camera.fps} FPS
            </div>
          </div>

          {/* Real-time Telemetry Stats (if worker active) */}
          {isRunning && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '8px',
                padding: '10px',
                backgroundColor: 'var(--color-bg-secondary)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border-subtle)',
              }}
            >
              <div>
                <span style={{ fontSize: '10px', color: 'var(--color-text-dim)', textTransform: 'uppercase' }}>Inference FPS</span>
                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                  {workerStatus?.fps?.toFixed(1) || '0.0'}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: 'var(--color-text-dim)', textTransform: 'uppercase' }}>Latency</span>
                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {workerStatus?.latency_ms?.toFixed(0) || '0'} ms
                </div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: 'var(--color-text-dim)', textTransform: 'uppercase' }}>Frames Processed</span>
                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {workerStatus?.frames_processed || 0}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: 'var(--color-text-dim)', textTransform: 'uppercase' }}>Alerts Emitted</span>
                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-warning)', fontFamily: 'var(--font-mono)' }}>
                  {workerStatus?.events_emitted || 0}
                </div>
              </div>
            </div>
          )}

          {/* Technical Specifications */}
          <div>
            <h4 style={{ fontSize: '12px', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Edge Hardware & Stream Metadata
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
              <span className="detail-label">Stream URI (Masked):</span>
              <span className="detail-value" style={{ wordBreak: 'break-all', fontFamily: 'var(--font-mono)' }}>
                {camera.stream_uri || 'Pending configuration'}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Monitored Zone:</span>
              <span className="detail-value" style={{ color: 'var(--color-accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {camera.zone_id}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Reconnect Attempts:</span>
              <span className="detail-value">{workerStatus?.reconnect_count ?? 0}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Last Ingested Frame:</span>
              <span className="detail-value">{workerStatus?.last_frame_timestamp || camera.last_ping || 'Awaiting activation'}</span>
            </div>
          </div>

          {/* Architecture Boundary Note */}
          <div
            style={{
              backgroundColor: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px',
              fontSize: '11px',
              color: 'var(--color-text-muted)',
              display: 'flex',
              gap: '8px',
            }}
          >
            <Server size={14} style={{ color: 'var(--color-accent-blue)', flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong style={{ color: 'var(--color-text-primary)' }}>Continuous Analytics Gateway:</strong> Video is ingested via <code style={{ color: 'var(--color-accent-cyan)' }}>RTSPVideoSource</code> with TCP transport and safe credential redaction. Incursions are verified via polygonal spatial intersection and submitted to <code style={{ color: 'var(--color-accent-cyan)' }}>/api/events</code>.
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
