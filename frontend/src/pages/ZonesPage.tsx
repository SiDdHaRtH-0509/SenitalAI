import React, { useState, useEffect } from 'react';
import { MapPin, Search, Info, RefreshCw } from 'lucide-react';
import { RestrictedZoneInfo } from '../types';
import { fetchRestrictedZones } from '../services/api';
import { DEMO_ZONES } from '../data/demoData';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ZonePolygonSchematic } from '../components/dashboard/ZonePolygonSchematic';
import { EmptyState } from '../components/ui/EmptyState';

export const ZonesPage: React.FC = () => {
  const [zones, setZones] = useState<RestrictedZoneInfo[]>(DEMO_ZONES);
  const [search, setSearch] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadZones = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetchRestrictedZones();
      setZones(res.data);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadZones();
  }, []);

  const filteredZones = zones.filter((z) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      z.name.toLowerCase().includes(q) ||
      z.zone_id.toLowerCase().includes(q) ||
      z.camera_id.toLowerCase().includes(q) ||
      z.description.toLowerCase().includes(q)
    );
  });

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-heading-block">
        <div className="heading-title-group">
          <h1>Restricted Zones & Boundary Geometries</h1>
          <p>
            Calibrated polygon boundaries evaluated by the pure Python Ray-Casting algorithm in SentinelAI Computer Vision.
          </p>
        </div>

        <div className="heading-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={loadZones}
            disabled={isRefreshing}
          >
            <RefreshCw size={13} className={isRefreshing ? 'spin-icon' : ''} />
            {isRefreshing ? 'Reloading...' : 'Reload Geometries'}
          </button>
        </div>
      </div>

      {/* Geometry Calibration Architecture Notice */}
      <div
        style={{
          backgroundColor: 'rgba(14, 165, 233, 0.08)',
          border: '1px solid rgba(14, 165, 233, 0.25)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: 'var(--color-accent-blue)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={16} />
          <span>
            <strong>Mathematical Ray-Casting Geometry:</strong> Zones represent real polygon coordinates configured in <code>sentinel_cv.config</code> (e.g. <code>zone-restricted-01</code>). Incursions are verified when a detected person's ground-plane anchor (<code>bottom_center</code>) intersects the polygon.
          </span>
        </div>
        <span className="badge badge-pending">READ-ONLY CONFIG</span>
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
            placeholder="Search zones by ID, name, or camera..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
            style={{ width: '100%' }}
            aria-label="Search restricted zones"
          />
        </div>
        <span style={{ fontSize: '12px', color: 'var(--color-text-dim)' }}>
          Showing {filteredZones.length} of {zones.length} calibrated zones
        </span>
      </div>

      {/* Zones Grid */}
      {filteredZones.length === 0 ? (
        <EmptyState
          icon={MapPin}
          title="No Restricted Zones Found"
          description="No zone boundaries match your search query."
          actionText="Clear Search"
          onAction={() => setSearch('')}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
            gap: 'var(--space-lg)',
          }}
        >
          {filteredZones.map((zone) => (
            <div
              key={zone.zone_id}
              className="card-base"
              style={{
                padding: 'var(--space-lg)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-md)',
              }}
            >
              {/* Card Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--color-critical)',
                    }}
                  >
                    <MapPin size={16} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                      {zone.name}
                    </h3>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {zone.zone_id}
                    </span>
                  </div>
                </div>
                <StatusBadge type="status" value={zone.status} label="RAY-CASTING ACTIVE" />
              </div>

              {/* Description */}
              <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                {zone.description}
              </p>

              {/* Visual Coordinate Polygon Schematic Canvas */}
              <ZonePolygonSchematic
                vertices={zone.vertices}
                zoneName={zone.name}
                zoneId={zone.zone_id}
              />

              {/* Vertex Coordinates Table */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-secondary)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '8px 12px',
                  border: '1px solid var(--color-border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                  <span>Polygon Vertex</span>
                  <span>Normalized [X, Y]</span>
                </div>
                {zone.vertices.map(([vx, vy], i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--color-text-secondary)',
                      padding: '2px 0',
                    }}
                  >
                    <span>P{i + 1} Point</span>
                    <span style={{ color: 'var(--color-accent-cyan)' }}>
                      ({vx.toFixed(2)}, {vy.toFixed(2)})
                    </span>
                  </div>
                ))}
              </div>

              {/* Footer Meta */}
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
                <span>Assigned Node: <code>{zone.camera_id}</code></span>
                <span>Incursions Logged: <strong style={{ color: 'var(--color-critical)' }}>{zone.incursions_today}</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
