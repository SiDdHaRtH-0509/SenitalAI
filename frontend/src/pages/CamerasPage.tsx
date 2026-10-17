import React, { useState } from 'react';
import { Camera, Search, RefreshCw, Info, ExternalLink } from 'lucide-react';
import { CameraInfo } from '../types';
import { StatusBadge } from '../components/ui/StatusBadge';
import { CameraDetailModal } from '../components/dashboard/CameraDetailModal';
import { EmptyState } from '../components/ui/EmptyState';

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

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredCameras = cameras.filter((cam) => {
    if (!localSearch.trim()) return true;
    const q = localSearch.toLowerCase();
    return (
      cam.name.toLowerCase().includes(q) ||
      cam.camera_id.toLowerCase().includes(q) ||
      cam.location.toLowerCase().includes(q) ||
      cam.zone_id.toLowerCase().includes(q)
    );
  });

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-heading-block">
        <div className="heading-title-group">
          <h1>Camera Device Registry</h1>
          <p>
            Configured CCTV surveillance edge nodes, capture resolutions, frame rates, and assigned restricted zones.
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
            {isRefreshing ? 'Checking Nodes...' : 'Probe Nodes'}
          </button>
        </div>
      </div>

      {/* Demo Notice Banner */}
      <div
        style={{
          backgroundColor: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: 'var(--radius-sm)',
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: 'var(--color-warning)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={15} />
          <span>
            <strong>Device Inventory Notice:</strong> Displaying {cameras.length} demonstration edge camera specifications. Adding, updating, or calibrating physical CCTV nodes requires backend provisioning services.
          </span>
        </div>
        <span className="badge badge-warning">DEMO INVENTORY</span>
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
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 'var(--space-md)',
          }}
        >
          {filteredCameras.map((cam) => (
            <div
              key={cam.camera_id}
              className="card-base"
              style={{
                padding: 'var(--space-lg)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-sm)',
                cursor: 'pointer',
              }}
              onClick={() => setSelectedCamera(cam)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--color-bg-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--color-accent-blue)',
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
                <StatusBadge type="status" value={cam.status} />
              </div>

              <div style={{ padding: '8px 0', borderTop: '1px solid var(--color-border-subtle)', borderBottom: '1px solid var(--color-border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Location:</span>
                  <span style={{ color: 'var(--color-text-primary)' }}>{cam.location}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Assigned Zone:</span>
                  <span style={{ color: 'var(--color-accent-cyan)', fontFamily: 'var(--font-mono)' }}>{cam.zone_id}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Capture Spec:</span>
                  <span style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>{cam.resolution} @ {cam.fps} FPS</span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '4px' }}>
                <span style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>
                  Protocol: RTSP / Edge OpenCV
                </span>
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
                  Specifications
                </button>
              </div>
            </div>
          ))}
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
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredCameras.map((cam) => (
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
                      <StatusBadge type="status" value={cam.status} />
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
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Camera Detail Inspector Modal */}
      <CameraDetailModal
        camera={selectedCamera}
        onClose={() => setSelectedCamera(null)}
      />
    </div>
  );
};
