import React, { useState, useEffect } from 'react';
import { Camera, Search, RefreshCw, Info, ExternalLink, Play, Square } from 'lucide-react';
import { CameraInfo, CameraWorkerStatus } from '../types';
import { CameraDetailModal } from '../components/dashboard/CameraDetailModal';
import { EmptyState } from '../components/ui/EmptyState';
import { startCameraWorker, stopCameraWorker, getCameraWorkerStatus } from '../services/apiClient';
import { safeLower } from '../utils/formatters';

interface CamerasPageProps {
  cameras: CameraInfo[];
  onRefresh: () => Promise<void>;
  searchFilter: string;
}

export const CamerasPage: React.FC<CamerasPageProps> = ({
  cameras,
  onRefresh,
  searchFilter,
}) => {
  const [selectedCamera, setSelectedCamera] = useState<CameraInfo | null>(null);
  const [localSearch, setLocalSearch] = useState(searchFilter);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [processingCameraId, setProcessingCameraId] = useState<string | null>(null);
  const [workerStatuses, setWorkerStatuses] = useState<Record<string, CameraWorkerStatus>>({});

  // Sync initial worker statuses from cameras
  useEffect(() => {
    const initialMap: Record<string, CameraWorkerStatus> = {};
    for (const cam of cameras) {
      if (cam.worker_status) {
        initialMap[cam.camera_id] = cam.worker_status;
      }
    }
    setWorkerStatuses((prev) => ({ ...initialMap, ...prev }));
  }, [cameras]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
      // Also query live worker status for each camera
      const statusUpdates: Record<string, CameraWorkerStatus> = {};
      await Promise.all(
        cameras.map(async (cam) => {
          const res = await getCameraWorkerStatus(cam.camera_id);
          if (res.data) {
            statusUpdates[cam.camera_id] = res.data;
          }
        })
      );
      setWorkerStatuses((prev) => ({ ...prev, ...statusUpdates }));
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleStart = async (cameraId: string, replayMode: boolean = false) => {
    setProcessingCameraId(cameraId);
    try {
      const res = await startCameraWorker(cameraId, replayMode);
      if (res.data) {
        setWorkerStatuses((prev) => ({ ...prev, [cameraId]: res.data }));
      }
      await onRefresh();
    } finally {
      setProcessingCameraId(null);
    }
  };

  const handleStop = async (cameraId: string) => {
    setProcessingCameraId(cameraId);
    try {
      const res = await stopCameraWorker(cameraId);
      if (res.data) {
        setWorkerStatuses((prev) => ({ ...prev, [cameraId]: res.data }));
      }
      await onRefresh();
    } finally {
      setProcessingCameraId(null);
    }
  };

  const filteredCameras = cameras.filter((cam) => {
    if (!localSearch.trim()) return true;
    const q = localSearch.toLowerCase();
    return (
      safeLower(cam.name).includes(q) ||
      safeLower(cam.camera_id).includes(q) ||
      safeLower(cam.location).includes(q) ||
      safeLower(cam.zone_id).includes(q)
    );
  });

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-heading-block">
        <div className="heading-title-group">
          <h1>CCTV Camera Management & Analytics</h1>
          <p>
            Continuous RTSP surveillance video ingestion, YOLOv8n edge analytics, and real-time perimeter incursion monitoring.
          </p>
        </div>

        <div className="heading-actions">
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: 'var(--color-bg-secondary)', padding: '2px', borderRadius: 'var(--radius-sm)' }}>
            <button
              type="button"
              className="btn-secondary"
              style={{
                backgroundColor: viewMode === 'grid' ? 'var(--color-bg-card)' : 'transparent',
                borderColor: viewMode === 'grid' ? 'var(--color-border-default)' : 'transparent',
                padding: '4px 10px',
                fontSize: '11px',
              }}
              onClick={() => setViewMode('grid')}
            >
              Grid
            </button>
            <button
              type="button"
              className="btn-secondary"
              style={{
                backgroundColor: viewMode === 'table' ? 'var(--color-bg-card)' : 'transparent',
                borderColor: viewMode === 'table' ? 'var(--color-border-default)' : 'transparent',
                padding: '4px 10px',
                fontSize: '11px',
              }}
              onClick={() => setViewMode('table')}
            >
              Table
            </button>
          </div>

          <button
            type="button"
            className="btn-secondary"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw size={13} className={isRefreshing ? 'spin-icon' : ''} />
            {isRefreshing ? 'Probing Streams...' : 'Probe Streams'}
          </button>
        </div>
      </div>

      {/* Notice Banner */}
      <div
        style={{
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          borderRadius: 'var(--radius-sm)',
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: 'var(--color-accent-cyan)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={15} />
          <span>
            <strong>Continuous Analytics Active:</strong> Each camera node supports continuous ingestion via RTSP or deterministic demo replay. Credential masking is enforced across all streams.
          </span>
        </div>
        <span className="badge badge-info">RTSP & REPLAY READY</span>
      </div>

      {/* Search Input Bar */}
      <div
        className="card-base"
        style={{
          padding: 'var(--space-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-md)',
        }}
      >
        <div style={{ position: 'relative', maxWidth: '400px', width: '100%' }}>
          <Search size={14} className="search-icon" aria-hidden="true" />
          <input
            type="search"
            placeholder="Search cameras by ID, name, location, or zone..."
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            className="search-input"
            style={{ width: '100%' }}
            aria-label="Search camera registry"
          />
        </div>
        <span style={{ fontSize: '12px', color: 'var(--color-text-dim)' }}>
          Total registered nodes: {filteredCameras.length} of {cameras.length}
        </span>
      </div>

      {/* Grid or Table View */}
      {filteredCameras.length === 0 ? (
        <EmptyState
          icon={Camera}
          title="No Camera Nodes Found"
          description="No camera records match the current filter query."
          actionText="Clear Search Filter"
          onAction={() => setLocalSearch('')}
        />
      ) : viewMode === 'grid' ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
            gap: 'var(--space-md)',
          }}
        >
          {filteredCameras.map((cam) => {
            const ws = workerStatuses[cam.camera_id] || cam.worker_status;
            const isRunning = ws?.is_running ?? false;
            const isProcessing = processingCameraId === cam.camera_id;
            const connState = ws?.connection_state ?? (cam.status === 'ONLINE' ? 'READY' : 'OFFLINE');

            return (
              <div
                key={cam.camera_id}
                className="card-base"
                style={{
                  padding: 'var(--space-lg)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-sm)',
                  cursor: 'pointer',
                  border: isRunning ? '1px solid rgba(34, 197, 94, 0.4)' : undefined,
                }}
                onClick={() => setSelectedCamera(cam)}
              >
                {/* Header row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: isRunning ? 'rgba(34, 197, 94, 0.15)' : 'var(--color-bg-secondary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: isRunning ? 'var(--color-risk-low)' : 'var(--color-accent-blue)',
                      }}
                    >
                      <Camera size={16} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {cam.name}
                      </h3>
                      <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {cam.camera_id}
                      </span>
                    </div>
                  </div>

                  {/* Worker State Badge */}
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor:
                        connState === 'CONNECTED'
                          ? 'rgba(34, 197, 94, 0.15)'
                          : connState === 'CONNECTING' || connState === 'RECONNECTING'
                          ? 'rgba(245, 158, 11, 0.15)'
                          : connState === 'FAILED' || connState === 'ERROR'
                          ? 'rgba(239, 68, 68, 0.15)'
                          : 'var(--color-bg-secondary)',
                      color:
                        connState === 'CONNECTED'
                          ? 'var(--color-risk-low)'
                          : connState === 'CONNECTING' || connState === 'RECONNECTING'
                          ? 'var(--color-warning)'
                          : connState === 'FAILED' || connState === 'ERROR'
                          ? 'var(--color-risk-critical)'
                          : 'var(--color-text-dim)',
                      border: '1px solid currentColor',
                    }}
                  >
                    {connState === 'CONNECTED'
                      ? 'AI ACTIVE'
                      : connState === 'CONNECTING' || connState === 'RECONNECTING'
                      ? 'CONNECTING'
                      : connState === 'FAILED' || connState === 'ERROR'
                      ? 'FAULT'
                      : 'STOPPED'}
                  </span>
                </div>

                {/* Specs rows */}
                <div style={{ padding: '8px 0', borderTop: '1px solid var(--color-border-subtle)', borderBottom: '1px solid var(--color-border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Location:</span>
                    <span style={{ color: 'var(--color-text-primary)' }}>{cam.location}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Monitored Zone:</span>
                    <span style={{ color: 'var(--color-accent-cyan)', fontFamily: 'var(--font-mono)' }}>{cam.zone_id}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Capture Spec:</span>
                    <span style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>{cam.resolution} @ {cam.fps} FPS</span>
                  </div>
                  {cam.stream_uri && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--color-text-muted)' }}>Stream URI:</span>
                      <span style={{ color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)', fontSize: '10px', wordBreak: 'break-all' }}>
                        {cam.stream_uri}
                      </span>
                    </div>
                  )}
                </div>

                {/* Worker Live Telemetry (if active) */}
                {isRunning && (
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      backgroundColor: 'rgba(34, 197, 94, 0.06)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '6px 10px',
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    <span style={{ color: 'var(--color-accent-cyan)' }}>
                      {ws?.fps?.toFixed(1) || '0.0'} FPS
                    </span>
                    <span style={{ color: 'var(--color-text-muted)' }}>
                      {ws?.latency_ms?.toFixed(0) || '0'}ms latency
                    </span>
                    <span style={{ color: 'var(--color-text-primary)' }}>
                      {ws?.frames_processed || 0} frames
                    </span>
                    <span style={{ color: 'var(--color-warning)' }}>
                      {ws?.events_emitted || 0} alerts
                    </span>
                  </div>
                )}

                {/* Controls & Inspection */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '6px', gap: '8px' }}>
                  <div style={{ display: 'flex', gap: '6px' }} onClick={(e) => e.stopPropagation()}>
                    {isRunning ? (
                      <button
                        type="button"
                        className="btn-secondary"
                        style={{
                          padding: '4px 10px',
                          fontSize: '11px',
                          color: 'var(--color-risk-critical)',
                          borderColor: 'rgba(239, 68, 68, 0.4)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                        disabled={isProcessing}
                        onClick={() => handleStop(cam.camera_id)}
                      >
                        <Square size={11} />
                        Stop
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="btn-primary"
                          style={{
                            padding: '4px 10px',
                            fontSize: '11px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                          disabled={isProcessing}
                          onClick={() => handleStart(cam.camera_id, false)}
                        >
                          <Play size={11} />
                          Start RTSP
                        </button>
                        <button
                          type="button"
                          className="btn-secondary"
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                          }}
                          disabled={isProcessing}
                          onClick={() => handleStart(cam.camera_id, true)}
                        >
                          Demo
                        </button>
                      </>
                    )}
                  </div>

                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ padding: '4px 10px', fontSize: '11px' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCamera(cam);
                    }}
                  >
                    <ExternalLink size={11} />
                    Inspect
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table View */
        <div className="card-base" style={{ padding: 'var(--space-md)' }}>
          <div className="events-table-container">
            <table className="events-table">
              <thead>
                <tr>
                  <th>Camera ID</th>
                  <th>Designation</th>
                  <th>Location</th>
                  <th>Assigned Zone</th>
                  <th>Resolution / FPS</th>
                  <th>AI Analytics</th>
                  <th>Controls</th>
                  <th>Inspect</th>
                </tr>
              </thead>
              <tbody>
                {filteredCameras.map((cam) => {
                  const ws = workerStatuses[cam.camera_id] || cam.worker_status;
                  const isRunning = ws?.is_running ?? false;
                  const isProcessing = processingCameraId === cam.camera_id;
                  const connState = ws?.connection_state ?? (cam.status === 'ONLINE' ? 'READY' : 'OFFLINE');

                  return (
                    <tr key={cam.camera_id} onClick={() => setSelectedCamera(cam)}>
                      <td className="event-id-cell">{cam.camera_id}</td>
                      <td style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{cam.name}</td>
                      <td>{cam.location}</td>
                      <td>
                        <code style={{ color: 'var(--color-accent-cyan)' }}>{cam.zone_id}</code>
                      </td>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                          {cam.resolution} @ {cam.fps} FPS
                        </span>
                      </td>
                      <td>
                        <span
                          style={{
                            fontSize: '10px',
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor:
                              connState === 'CONNECTED'
                                ? 'rgba(34, 197, 94, 0.15)'
                                : connState === 'CONNECTING' || connState === 'RECONNECTING'
                                ? 'rgba(245, 158, 11, 0.15)'
                                : 'var(--color-bg-secondary)',
                            color:
                              connState === 'CONNECTED'
                                ? 'var(--color-risk-low)'
                                : connState === 'CONNECTING' || connState === 'RECONNECTING'
                                ? 'var(--color-warning)'
                                : 'var(--color-text-dim)',
                            border: '1px solid currentColor',
                          }}
                        >
                          {connState}
                        </span>
                      </td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {isRunning ? (
                            <button
                              type="button"
                              className="btn-secondary"
                              style={{ padding: '2px 6px', fontSize: '10px', color: 'var(--color-risk-critical)' }}
                              disabled={isProcessing}
                              onClick={() => handleStop(cam.camera_id)}
                            >
                              Stop
                            </button>
                          ) : (
                            <>
                              <button
                                type="button"
                                className="btn-primary"
                                style={{ padding: '2px 6px', fontSize: '10px' }}
                                disabled={isProcessing}
                                onClick={() => handleStart(cam.camera_id, false)}
                              >
                                Start
                              </button>
                              <button
                                type="button"
                                className="btn-secondary"
                                style={{ padding: '2px 6px', fontSize: '10px' }}
                                disabled={isProcessing}
                                onClick={() => handleStart(cam.camera_id, true)}
                              >
                                Demo
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-secondary"
                          style={{ padding: '3px 8px', fontSize: '11px' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedCamera(cam);
                          }}
                        >
                          <ExternalLink size={11} />
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Camera Detail Inspector Modal */}
      <CameraDetailModal
        camera={selectedCamera}
        workerStatus={selectedCamera ? (workerStatuses[selectedCamera.camera_id] || selectedCamera.worker_status) : undefined}
        onClose={() => setSelectedCamera(null)}
        onStartWorker={handleStart}
        onStopWorker={handleStop}
        isProcessing={processingCameraId !== null}
      />
    </div>
  );
};
