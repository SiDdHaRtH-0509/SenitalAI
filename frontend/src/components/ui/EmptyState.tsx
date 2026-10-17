import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  technicalNote?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionText,
  onAction,
  technicalNote,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '36px 20px',
        textAlign: 'center',
        backgroundColor: 'var(--color-bg-primary)',
        borderRadius: 'var(--radius-sm)',
        border: '1px dashed var(--color-border-default)',
        margin: '8px 0',
      }}
    >
      <div
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          backgroundColor: 'var(--color-bg-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-text-dim)',
          marginBottom: '12px',
          border: '1px solid var(--color-border-subtle)',
        }}
      >
        <Icon size={20} />
      </div>
      <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px' }}>
        {title}
      </h4>
      <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', maxWidth: '420px', lineHeight: 1.5 }}>
        {description}
      </p>

      {technicalNote && (
        <span
          style={{
            marginTop: '12px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-text-dim)',
            backgroundColor: 'var(--color-bg-secondary)',
            padding: '3px 8px',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          {technicalNote}
        </span>
      )}

      {actionText && onAction && (
        <button
          onClick={onAction}
          className="btn-secondary"
          style={{ marginTop: '16px' }}
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
