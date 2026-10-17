import React, { useState } from 'react';
import { X, Lock, User, Shield, AlertCircle, CheckCircle, LogOut } from 'lucide-react';
import { UserProfile } from '../../types';
import { loginUser, logoutUser } from '../../services/api';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfile | null;
  onAuthSuccess: (user: UserProfile) => void;
  onLogoutSuccess: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onAuthSuccess,
  onLogoutSuccess,
}) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await loginUser(username.trim(), password);
      setSuccessMessage(`Authenticated successfully as ${response.data.user.username} (${response.data.user.role})`);
      onAuthSuccess(response.data.user);
      setTimeout(() => {
        onClose();
      }, 800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials or backend unreachable.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectProfile = (user: string) => {
    setUsername(user);
    setPassword('');
    setErrorMessage(null);
  };

  const handleLogout = async () => {
    setIsLoading(true);
    try {
      await logoutUser();
      onLogoutSuccess();
      setSuccessMessage('Logged out successfully.');
      setTimeout(() => {
        onClose();
      }, 500);
    } catch {
      onLogoutSuccess();
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        backgroundColor: 'rgba(5, 10, 20, 0.75)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          color: '#f8fafc',
          fontFamily: 'inherit',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1rem 1.25rem',
            borderBottom: '1px solid #1e293b',
            backgroundColor: '#090d16',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Shield size={20} color="#38bdf8" />
            <h2 id="auth-modal-title" style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>
              SentinelAI Identity & Access
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              padding: '4px',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '1.25rem' }}>
          {currentUser && (
            <div
              style={{
                backgroundColor: '#1e293b',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                marginBottom: '1.25rem',
                border: '1px solid #334155',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Currently Authenticated
                </div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#38bdf8' }}>
                  {currentUser.username} ({currentUser.role})
                </div>
                <div style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                  {currentUser.full_name || 'Active Personnel'}
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                disabled={isLoading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  backgroundColor: '#ef4444',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.4rem 0.75rem',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  opacity: isLoading ? 0.7 : 1,
                }}
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          )}

          {errorMessage && (
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid #ef4444',
                color: '#fca5a5',
                padding: '0.6rem 0.8rem',
                borderRadius: '6px',
                marginBottom: '1rem',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div
              style={{
                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                border: '1px solid #22c55e',
                color: '#86efac',
                padding: '0.6rem 0.8rem',
                borderRadius: '6px',
                marginBottom: '1rem',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <CheckCircle size={16} />
              <span>{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label
                htmlFor="auth-username"
                style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}
              >
                Username
              </label>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  backgroundColor: '#020617',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '0.5rem 0.75rem',
                  gap: '0.5rem',
                }}
              >
                <User size={16} color="#64748b" />
                <input
                  id="auth-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. operator or admin"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    color: '#f8fafc',
                    width: '100%',
                    fontSize: '0.9rem',
                  }}
                  disabled={isLoading}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="auth-password"
                style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}
              >
                Password
              </label>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  backgroundColor: '#020617',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '0.5rem 0.75rem',
                  gap: '0.5rem',
                }}
              >
                <Lock size={16} color="#64748b" />
                <input
                  id="auth-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter security password"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    color: '#f8fafc',
                    width: '100%',
                    fontSize: '0.9rem',
                  }}
                  disabled={isLoading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                backgroundColor: '#0284c7',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '0.65rem 1rem',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1,
                marginTop: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
              }}
            >
              {isLoading ? 'Verifying...' : 'Authenticate & Sign In'}
            </button>
          </form>

          {/* Quick-Fill Profiles for Inspection & Demo */}
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid #1e293b' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
              Select Identity Profile:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <button
                type="button"
                onClick={() => handleSelectProfile('operator')}
                style={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '0.5rem',
                  color: '#94a3b8',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ fontWeight: 600, color: '#38bdf8' }}>Operator</div>
                <div>Fill &apos;operator&apos;</div>
              </button>
              <button
                type="button"
                onClick={() => handleSelectProfile('admin')}
                style={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '0.5rem',
                  color: '#94a3b8',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ fontWeight: 600, color: '#a855f7' }}>Administrator</div>
                <div>Fill &apos;admin&apos;</div>
              </button>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.7rem', color: '#94a3b8' }}>
              Configure deployment secrets and account credentials securely via local uncommitted .env file.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
