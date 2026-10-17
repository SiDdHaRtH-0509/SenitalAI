import React, { useState } from 'react';
import { Save, RotateCcw, Check, Info, Monitor, Sliders } from 'lucide-react';
import { ClientSettings } from '../types';
import { saveClientSettings } from '../services/api';
import { DEFAULT_CLIENT_SETTINGS } from '../data/demoData';

interface SettingsPageProps {
  settings: ClientSettings;
  onUpdateSettings: (newSettings: ClientSettings) => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  settings,
  onUpdateSettings,
}) => {
  const [formData, setFormData] = useState<ClientSettings>(settings);
  const [savedNotice, setSavedNotice] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    saveClientSettings(formData);
    onUpdateSettings(formData);
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  const handleReset = () => {
    setFormData(DEFAULT_CLIENT_SETTINGS);
    saveClientSettings(DEFAULT_CLIENT_SETTINGS);
    onUpdateSettings(DEFAULT_CLIENT_SETTINGS);
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  return (
    <div className="dashboard-container" style={{ maxWidth: '800px' }}>
      {/* Header */}
      <div className="dashboard-heading-block">
        <div className="heading-title-group">
          <h1>Command Dashboard Settings</h1>
          <p>
            Configure local client presentation preferences, table density, and telemetry polling frequencies.
          </p>
        </div>

        <div className="heading-actions">
          {savedNotice && (
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                color: 'var(--color-success)',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              <Check size={14} /> Preferences Saved Locally
            </span>
          )}
        </div>
      </div>

      {/* Scope Disclaimer Banner */}
      <div
        style={{
          backgroundColor: 'rgba(14, 165, 233, 0.08)',
          border: '1px solid rgba(14, 165, 233, 0.25)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '12px',
          color: 'var(--color-accent-blue)',
        }}
      >
        <Info size={16} />
        <span>
          <strong>Local Client Scope:</strong> Settings configured on this screen are persisted to your browser&apos;s <code>localStorage</code>. Platform-wide CV thresholds and camera credentials are intentionally isolated on the backend.
        </span>
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
        {/* Section 1: Display & Layout Preferences */}
        <div className="card-base" style={{ padding: 'var(--space-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: '10px' }}>
            <Monitor size={16} style={{ color: 'var(--color-accent-blue)' }} />
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Display & Table Presentation
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Table Density */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  Table Row Density
                </label>
                <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Controls vertical cell padding in the Security Events ledger
                </p>
              </div>
              <select
                value={formData.table_density}
                onChange={(e) => setFormData({ ...formData, table_density: e.target.value as any })}
                className="search-input"
                style={{ width: 'auto', padding: '6px 12px' }}
              >
                <option value="comfortable">Comfortable (Standard)</option>
                <option value="compact">Compact (High Information Density)</option>
              </select>
            </div>

            {/* Demo Notices Banner Toggle */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  Persistent Demo Data Notice Banner
                </label>
                <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Display the top amber notice indicating synthetic fixtures during offline testing
                </p>
              </div>
              <input
                type="checkbox"
                checked={formData.show_demo_notices}
                onChange={(e) => setFormData({ ...formData, show_demo_notices: e.target.checked })}
                style={{ width: '16px', height: '16px', accentColor: 'var(--color-accent-blue)', cursor: 'pointer' }}
              />
            </div>
          </div>
        </div>

        {/* Section 2: Telemetry Polling & Alerts */}
        <div className="card-base" style={{ padding: 'var(--space-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--color-border-subtle)', paddingBottom: '10px' }}>
            <Sliders size={16} style={{ color: 'var(--color-accent-cyan)' }} />
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Telemetry Polling & Audio Signals
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Auto-Refresh Interval */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  Backend Polling Frequency
                </label>
                <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Automatic polling rate for <code>GET /api/events</code> and <code>GET /api/stats</code>
                </p>
              </div>
              <select
                value={formData.auto_refresh_interval}
                onChange={(e) => setFormData({ ...formData, auto_refresh_interval: Number(e.target.value) as any })}
                className="search-input"
                style={{ width: 'auto', padding: '6px 12px' }}
              >
                <option value={0}>Manual Only (Disabled)</option>
                <option value={10}>Every 10 Seconds</option>
                <option value={30}>Every 30 Seconds (Recommended)</option>
                <option value={60}>Every 60 Seconds</option>
              </select>
            </div>

            {/* Audio Alerts */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  Audible Alarm on Critical Incursions
                </label>
                <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Play browser chime when a CRITICAL risk-level security event arrives
                </p>
              </div>
              <input
                type="checkbox"
                checked={formData.enable_audio_alerts}
                onChange={(e) => setFormData({ ...formData, enable_audio_alerts: e.target.checked })}
                style={{ width: '16px', height: '16px', accentColor: 'var(--color-accent-blue)', cursor: 'pointer' }}
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleReset}
            style={{ color: 'var(--color-text-dim)' }}
          >
            <RotateCcw size={13} />
            Reset Defaults
          </button>

          <button
            type="submit"
            className="btn-secondary"
            style={{
              backgroundColor: 'var(--color-accent-blue)',
              color: '#fff',
              borderColor: 'var(--color-accent-blue)',
              padding: '8px 18px',
            }}
          >
            <Save size={13} />
            Save Preferences
          </button>
        </div>
      </form>
    </div>
  );
};
