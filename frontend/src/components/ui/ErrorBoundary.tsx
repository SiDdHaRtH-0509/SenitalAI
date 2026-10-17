import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  errorMessage: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      errorMessage: '',
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      errorMessage: error.message || 'An unexpected client component error occurred.',
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[SentinelAI ErrorBoundary] Caught component error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, errorMessage: '' });
    window.location.hash = '';
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: '400px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '32px',
            backgroundColor: 'var(--color-bg-base)',
          }}
          role="alert"
          aria-live="assertive"
        >
          <div
            className="card-base"
            style={{
              maxWidth: '540px',
              width: '100%',
              padding: '24px',
              borderLeft: '4px solid var(--color-critical)',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertOctagon size={24} style={{ color: 'var(--color-critical)' }} />
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {this.props.fallbackTitle || 'Surveillance Dashboard Render Fault'}
                </h3>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                  Component Exception Caught
                </span>
              </div>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
              A rendering issue was intercepted in the security console UI. Telemetry polling and core
              background services were halted safely to preserve data integrity.
            </p>

            <div
              style={{
                backgroundColor: 'var(--color-bg-secondary)',
                padding: '10px 12px',
                borderRadius: 'var(--radius-xs)',
                fontSize: '11px',
                color: 'var(--color-text-dim)',
                fontFamily: 'var(--font-mono)',
                overflowX: 'auto',
              }}
            >
              Error: {this.state.errorMessage}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={this.handleReset}
                style={{
                  backgroundColor: 'var(--color-accent-blue)',
                  color: '#fff',
                  borderColor: 'var(--color-accent-blue)',
                }}
              >
                <RotateCcw size={12} />
                Reload Command Center
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
