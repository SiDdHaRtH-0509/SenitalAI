import React from 'react';
import { AlertTriangle, ExternalLink, ShieldCheck, Info } from 'lucide-react';
import { SecurityEvent } from '../../types';
import { StatusBadge } from '../ui/StatusBadge';

interface RecentEventsTableProps {
  events: SecurityEvent[];
  isLive: boolean;
  onSelectEvent: (event: SecurityEvent) => void;
  searchFilter: string;
  highlightedEventIds?: Set<string>;
}

export const RecentEventsTable: React.FC<RecentEventsTableProps> = ({
  events,
  isLive,
  onSelectEvent,
  searchFilter,
  highlightedEventIds,
}) => {
  const filteredEvents = events.filter((evt) => {
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      evt.event_id.toLowerCase().includes(q) ||
      evt.camera_id.toLowerCase().includes(q) ||
      evt.event_type.toLowerCase().includes(q) ||
      (evt.zone_id && evt.zone_id.toLowerCase().includes(q)) ||
      (evt.risk_level && evt.risk_level.toLowerCase().includes(q))
    );
  });

  return (
    <div className="events-section">
      <div className="events-table-header-block">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} style={{ color: 'var(--color-critical)' }} />
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Recent Security Events
          </h3>
          <span style={{ fontSize: '12px', color: 'var(--color-text-dim)' }}>
            ({filteredEvents.length} records)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {!isLive && (
            <span
              className="badge badge-warning"
              title="Showing mock records for UI testing. Backend integration pending."
            >
              <Info size={11} />
              EXPLICIT DEMO DATA
            </span>
          )}
          {isLive && (
            <span className="badge badge-success">
              <ShieldCheck size={11} />
              LIVE TELEMETRY
            </span>
          )}
        </div>
      </div>

      <div className="events-table-container">
        <table className="events-table">
          <thead>
            <tr>
              <th>Event ID</th>
              <th>Camera ID</th>
              <th>Event Type</th>
              <th>Timestamp (UTC)</th>
              <th>Confidence</th>
              <th>Risk Level</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-text-dim)' }}>
                  No security events match the current search filter.
                </td>
              </tr>
            ) : (
              filteredEvents.map((evt) => (
                <tr
                  key={evt.event_id}
                  className={highlightedEventIds?.has(evt.event_id) ? 'event-row-new' : ''}
                  onClick={() => onSelectEvent(evt)}
                >
                  <td className="event-id-cell">
                    <span>{evt.event_id}</span>
                    {evt.is_demo && (
                      <span
                        style={{
                          marginLeft: '6px',
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
                  </td>
                  <td className="camera-cell">{evt.camera_id}</td>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-text-primary)' }}>
                      {evt.event_type}
                    </span>
                  </td>
                  <td className="timestamp-cell">
                    {new Date(evt.timestamp).toISOString().replace('T', ' ').replace('Z', ' UTC')}
                  </td>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--color-text-highlight)' }}>
                      {(evt.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>
                    <StatusBadge type="risk" value={evt.risk_level || evt.severity} />
                  </td>
                  <td>
                    <StatusBadge type="status" value={evt.status} />
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: '3px 8px', fontSize: '11px' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectEvent(evt);
                      }}
                    >
                      <ExternalLink size={11} />
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div
        style={{
          marginTop: '10px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '11px',
          color: 'var(--color-text-dim)',
        }}
      >
        <span>
          Schema source: <code>API_CONTRACT.md</code> v1.0 • Endpoint: <code>GET /api/events</code>
        </span>
        <span>Click any event record to inspect AI risk explanations & recommended action</span>
      </div>
    </div>
  );
};
