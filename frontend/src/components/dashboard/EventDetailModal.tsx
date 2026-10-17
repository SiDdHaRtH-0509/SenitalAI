import React from 'react';
import { X, AlertOctagon, CheckCircle2, Shield, Info } from 'lucide-react';
import { SecurityEvent } from '../../types';
import { StatusBadge } from '../ui/StatusBadge';

interface EventDetailModalProps {
  event: SecurityEvent | null;
  onClose: () => void;
  onAcknowledge?: (eventId: string) => void;
}

export const EventDetailModal: React.FC<EventDetailModalProps> = ({
  event,
  onClose,
  onAcknowledge,
}) => {
  if (!event) return null;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertOctagon size={18} style={{ color: 'var(--color-critical)' }} />
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Incident Details: {event.event_id}
              </h3>
              <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                Contract Schema: <code>API_CONTRACT.md</code> v1.0
              </span>
            </div>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {event.is_demo && (
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
                <strong>Demonstration Record:</strong> This is a synthetic event fixture for UI evaluation.
              </span>
            </div>
          )}

          {/* Risk Level & Score Banner */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--color-bg-secondary)',
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <div>
              <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', textTransform: 'uppercase' }}>
                Assessed Risk Priority
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                <StatusBadge type="risk" value={event.risk_level || event.severity} />
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  Score: {event.risk_score ?? 'N/A'}/100
                </span>
              </div>
            </div>

            <div>
              <span style={{ fontSize: '11px', color: 'var(--color-text-dim)', textTransform: 'uppercase' }}>
                Lifecycle Status
              </span>
              <div style={{ marginTop: '2px' }}>
                <StatusBadge type="status" value={event.status} />
              </div>
            </div>
          </div>

          {/* Telemetry Details */}
          <div>
            <h4 style={{ fontSize: '12px', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
              Core Telemetry
            </h4>
            <div className="detail-row">
              <span className="detail-label">Camera Identifier:</span>
              <span className="detail-value">{event.camera_id}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Restricted Zone ID:</span>
              <span className="detail-value">{event.zone_id || 'N/A'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Event Type:</span>
              <span className="detail-value">{event.event_type}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Detection Confidence:</span>
              <span className="detail-value">{(event.confidence * 100).toFixed(1)}% (YOLOv8n Class 0)</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Detection Frame Number:</span>
              <span className="detail-value">{event.evidence.frame_number}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Normalized Bounding Box:</span>
              <span className="detail-value">
                {event.evidence.bbox ? `[${event.evidence.bbox.map((v) => v.toFixed(2)).join(', ')}]` : 'N/A'}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Event Timestamp:</span>
              <span className="detail-value">{event.timestamp}</span>
            </div>
          </div>

          {/* Heuristic Reasons */}
          {event.reasons && event.reasons.length > 0 && (
            <div className="reasons-box">
              <h5>Backend Risk Determinants</h5>
              <ul>
                {event.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended Action */}
          {event.recommended_action && (
            <div
              style={{
                backgroundColor: 'rgba(14, 165, 233, 0.08)',
                border: '1px solid rgba(14, 165, 233, 0.25)',
                borderRadius: 'var(--radius-sm)',
                padding: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-accent-blue)', marginBottom: '4px' }}>
                <Shield size={14} />
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' }}>
                  Recommended Action
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--color-text-primary)' }}>
                {event.recommended_action}
              </p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Dismiss
            </button>
            {event.status === 'NEW' && onAcknowledge && (
              <button
                type="button"
                className="btn-secondary"
                style={{
                  backgroundColor: 'var(--color-accent-blue)',
                  color: '#fff',
                  borderColor: 'var(--color-accent-blue)',
                }}
                onClick={() => onAcknowledge(event.event_id)}
              >
                <CheckCircle2 size={13} />
                Acknowledge Incident
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
