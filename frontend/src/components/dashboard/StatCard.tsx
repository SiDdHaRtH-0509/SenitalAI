import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  icon: LucideIcon;
  badgeText?: string;
  badgeType?: 'critical' | 'warning' | 'success' | 'neutral' | 'info';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeText,
  badgeType = 'neutral',
}) => {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        <div className="stat-card-icon">
          <Icon size={16} />
        </div>
      </div>
      <div className="stat-card-value">{value}</div>
      <div className="stat-card-footer">
        <span className="stat-card-subtitle">{subtitle}</span>
        {badgeText && (
          <span className={`badge badge-${badgeType} stat-card-badge`}>
            {badgeText}
          </span>
        )}
      </div>
    </div>
  );
};
