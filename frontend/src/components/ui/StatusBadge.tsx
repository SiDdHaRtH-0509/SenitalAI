import React from 'react';
import { RiskLevel, SeverityLevel, EventStatus, HealthStatusType } from '../../types';

interface StatusBadgeProps {
  type?: 'risk' | 'severity' | 'status' | 'health';
  value: RiskLevel | SeverityLevel | EventStatus | HealthStatusType | string;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type = 'status', value, label }) => {
  const displayLabel = label || value;
  const normalized = String(value).toUpperCase();

  let badgeClass = 'badge badge-neutral';

  if (normalized === 'CRITICAL') {
    badgeClass = 'badge badge-critical';
  } else if (normalized === 'HIGH') {
    badgeClass = 'badge badge-high';
  } else if (normalized === 'MEDIUM' || normalized === 'WARNING' || normalized === 'DEGRADED') {
    badgeClass = 'badge badge-medium';
  } else if (normalized === 'LOW' || normalized === 'OPERATIONAL' || normalized === 'RESOLVED') {
    badgeClass = 'badge badge-success';
  } else if (normalized === 'NEW' || normalized === 'INTEGRATION_PENDING') {
    badgeClass = 'badge badge-pending';
  } else if (normalized === 'ACKNOWLEDGED') {
    badgeClass = 'badge badge-warning';
  } else if (normalized === 'DISCONNECTED' || normalized === 'OFFLINE') {
    badgeClass = 'badge badge-disconnected';
  }

  return (
    <span className={badgeClass} title={`${type}: ${displayLabel}`}>
      <span className="badge-dot" />
      {displayLabel}
    </span>
  );
};
