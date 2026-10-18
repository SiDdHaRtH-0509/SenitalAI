import React, { useState } from 'react';
import {
  X,
  Lock,
  User,
  Shield,
  AlertCircle,
  CheckCircle,
  LogOut,
  LogIn,
  UserPlus,
  Mail,
  Eye,
  EyeOff,
  Zap,
} from 'lucide-react';
import { UserProfile } from '../../types';
import { loginUser, logoutUser, registerUser } from '../../services/api';

// Pre-seeded evaluation credentials for local development & demonstration
const DEMO_PRESETS = {
  operator: {
    username: 'operator',
    password: 'OpPass_6cXBbV-XgrPyjBIW7k5OaA!',
    role: 'OPERATOR',
    label: 'Watch Officer',
  },
  admin: {
    username: 'admin',
    password: 'AdminPass_IzemiPKl-hbe_v0c7PC8xA!',
    role: 'ADMIN',
    label: 'Administrator',
  },
};

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
  const [mode, setMode] = useState<'login' | 'signup'>('login');

  // Login form state
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Signup form state
  const [signupFullName, setSignupFullName] = useState('');
  const [signupUsername, setSignupUsername] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirmPassword, setSignupConfirmPassword] = useState('');
  const [showSignupPassword, setShowSignupPassword] = useState(false);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLogin = async (
    e?: React.FormEvent,
    overrideUsername?: string,
    overridePassword?: string
  ) => {
    if (e) e.preventDefault();

    const u = (overrideUsername ?? loginUsername).trim();
    const p = overridePassword ?? loginPassword;

    if (!u || !p) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await loginUser(u, p);
      const user = response.data.user;
      setSuccessMessage(`Authenticated successfully as ${user.username} (${user.role})!`);
      onAuthSuccess(user);
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid username or password.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    const cleanUsername = signupUsername.trim().toLowerCase();
    const cleanFullName = signupFullName.trim();
    const cleanEmail = signupEmail.trim();

    if (!cleanUsername) {
      setErrorMessage('Username is required.');
      return;
    }
    if (cleanUsername.length < 3) {
      setErrorMessage('Username must be at least 3 characters long.');
      return;
    }
    if (!signupPassword) {
      setErrorMessage('Password is required.');
      return;
    }
    if (signupPassword.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }
    if (signupPassword !== signupConfirmPassword) {
      setErrorMessage('Passwords do not match. Please verify.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      // 1. Create the user account via POST /api/auth/register
      await registerUser(
        cleanUsername,
        signupPassword,
        cleanFullName || undefined,
        cleanEmail || undefined
      );

      setSuccessMessage(`Account created! Authenticating ${cleanUsername}...`);

      // 2. Automatically log the newly registered user in
      const loginResponse = await loginUser(cleanUsername, signupPassword);
      const user = loginResponse.data.user;

      setSuccessMessage(`Account created & verified! Welcome, ${user.username} (${user.role}).`);
      onAuthSuccess(user);

      setTimeout(() => {
        onClose();
      }, 800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed. Please check inputs.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = (presetKey: 'operator' | 'admin') => {
    const preset = DEMO_PRESETS[presetKey];
    setLoginUsername(preset.username);
    setLoginPassword(preset.password);
    handleLogin(undefined, preset.username, preset.password);
  };

  const handleFillCredentials = (presetKey: 'operator' | 'admin') => {
    const preset = DEMO_PRESETS[presetKey];
    setLoginUsername(preset.username);
    setLoginPassword(preset.password);
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
        backgroundColor: 'rgba(5, 10, 20, 0.78)',
        backdropFilter: 'blur(5px)',
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
          maxWidth: '460px',
          backgroundColor: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                backgroundColor: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Shield size={18} color="#38bdf8" />
            </div>
            <div>
              <h2 id="auth-modal-title" style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600 }}>
                SentinelAI Security Access
              </h2>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Identity, RBAC Authentication & Operator Onboarding
              </span>
            </div>
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
              padding: '6px',
              borderRadius: '6px',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Mode Switcher Tabs */}
        <div
          style={{
            display: 'flex',
            backgroundColor: '#090d16',
            borderBottom: '1px solid #1e293b',
            padding: '4px',
            gap: '4px',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setErrorMessage(null);
              setSuccessMessage(null);
            }}
            style={{
              flex: 1,
              padding: '0.6rem',
              backgroundColor: mode === 'login' ? '#1e293b' : 'transparent',
              color: mode === 'login' ? '#38bdf8' : '#94a3b8',
              border: 'none',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.45rem',
              transition: 'all 0.15s ease',
            }}
          >
            <LogIn size={15} />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('signup');
              setErrorMessage(null);
              setSuccessMessage(null);
            }}
            style={{
              flex: 1,
              padding: '0.6rem',
              backgroundColor: mode === 'signup' ? '#1e293b' : 'transparent',
              color: mode === 'signup' ? '#38bdf8' : '#94a3b8',
              border: 'none',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.45rem',
              transition: 'all 0.15s ease',
            }}
          >
            <UserPlus size={15} />
            Sign Up (Register)
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.25rem', maxHeight: '80vh', overflowY: 'auto' }}>
          {/* Active Session Card (if user is currently logged in) */}
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '8px',
                    backgroundColor: currentUser.role === 'ADMIN' ? '#7e22ce' : '#0284c7',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                  }}
                >
                  {currentUser.role === 'ADMIN' ? 'AD' : 'OP'}
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Active Identity Session
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '0.92rem', color: '#38bdf8' }}>
                    {currentUser.username} <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>({currentUser.role})</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                    {currentUser.full_name || 'Active Personnel'}
                  </div>
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
                  padding: '0.45rem 0.8rem',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  opacity: isLoading ? 0.7 : 1,
                }}
              >
                <LogOut size={13} />
                Logout
              </button>
            </div>
          )}

          {/* Feedback Messages */}
          {errorMessage && (
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid #ef4444',
                color: '#fca5a5',
                padding: '0.65rem 0.85rem',
                borderRadius: '6px',
                marginBottom: '1rem',
                fontSize: '0.83rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div
              style={{
                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                border: '1px solid #22c55e',
                color: '#86efac',
                padding: '0.65rem 0.85rem',
                borderRadius: '6px',
                marginBottom: '1rem',
                fontSize: '0.83rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <CheckCircle size={16} style={{ flexShrink: 0 }} />
              <span>{successMessage}</span>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 1: SIGN IN MODE                                      */}
          {/* ======================================================== */}
          {mode === 'login' ? (
            <div>
              <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                <div>
                  <label
                    htmlFor="login-username"
                    style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}
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
                      padding: '0.55rem 0.75rem',
                      gap: '0.5rem',
                    }}
                  >
                    <User size={15} color="#64748b" />
                    <input
                      id="login-username"
                      type="text"
                      value={loginUsername}
                      onChange={(e) => setLoginUsername(e.target.value)}
                      placeholder="e.g. operator or admin"
                      autoComplete="username"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: '#f8fafc',
                        width: '100%',
                        fontSize: '0.88rem',
                      }}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="login-password"
                    style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}
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
                      padding: '0.55rem 0.75rem',
                      gap: '0.5rem',
                    }}
                  >
                    <Lock size={15} color="#64748b" />
                    <input
                      id="login-password"
                      type={showLoginPassword ? 'text' : 'password'}
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      placeholder="Enter security password"
                      autoComplete="current-password"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: '#f8fafc',
                        width: '100%',
                        fontSize: '0.88rem',
                      }}
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowLoginPassword(!showLoginPassword)}
                      aria-label={showLoginPassword ? 'Hide password' : 'Show password'}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#64748b',
                        cursor: 'pointer',
                        padding: 0,
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      {showLoginPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
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
                    padding: '0.7rem 1rem',
                    fontSize: '0.88rem',
                    fontWeight: 600,
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    opacity: isLoading ? 0.7 : 1,
                    marginTop: '0.3rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    transition: 'background 0.15s ease',
                  }}
                >
                  <LogIn size={15} />
                  {isLoading ? 'Verifying Credentials...' : 'Authenticate & Sign In'}
                </button>
              </form>

              {/* Quick-Fill & 1-Click Evaluation Identities */}
              <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid #1e293b' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    1-Click Evaluation Identities:
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#38bdf8' }}>Click to sign in instantly</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  <button
                    type="button"
                    onClick={() => handleQuickLogin('operator')}
                    disabled={isLoading}
                    title="1-click sign in as Watch Officer"
                    style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '0.6rem 0.75rem',
                      color: '#94a3b8',
                      fontSize: '0.75rem',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      textAlign: 'left',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: 600, color: '#38bdf8' }}>Operator</span>
                      <Zap size={11} color="#38bdf8" />
                    </div>
                    <div style={{ color: '#cbd5e1', fontSize: '0.7rem', marginTop: '2px' }}>
                      Watch Officer (RBAC)
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleQuickLogin('admin')}
                    disabled={isLoading}
                    title="1-click sign in as System Administrator"
                    style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '0.6rem 0.75rem',
                      color: '#94a3b8',
                      fontSize: '0.75rem',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      textAlign: 'left',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: 600, color: '#a855f7' }}>Administrator</span>
                      <Zap size={11} color="#a855f7" />
                    </div>
                    <div style={{ color: '#cbd5e1', fontSize: '0.7rem', marginTop: '2px' }}>
                      System Admin (Full)
                    </div>
                  </button>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem', fontSize: '0.72rem', color: '#64748b' }}>
                  <span>Or fill fields only:</span>
                  <button
                    type="button"
                    onClick={() => handleFillCredentials('operator')}
                    style={{ background: 'transparent', border: 'none', color: '#38bdf8', cursor: 'pointer', padding: 0, fontSize: '0.72rem', textDecoration: 'underline' }}
                  >
                    Operator
                  </button>
                  <span>•</span>
                  <button
                    type="button"
                    onClick={() => handleFillCredentials('admin')}
                    style={{ background: 'transparent', border: 'none', color: '#a855f7', cursor: 'pointer', padding: 0, fontSize: '0.72rem', textDecoration: 'underline' }}
                  >
                    Admin
                  </button>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '0.75rem' }}>
                  <button
                    type="button"
                    onClick={() => setMode('signup')}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#38bdf8',
                      fontSize: '0.78rem',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                    }}
                  >
                    Need a new operator account? Register here &rarr;
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* ======================================================== */
            /* TAB 2: SIGN UP (REGISTRATION) MODE                       */
            /* ======================================================== */
            <div>
              <form onSubmit={handleSignup} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div>
                  <label
                    htmlFor="signup-fullname"
                    style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}
                  >
                    Full Name <span style={{ color: '#64748b' }}>(Optional)</span>
                  </label>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      backgroundColor: '#020617',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '0.55rem 0.75rem',
                      gap: '0.5rem',
                    }}
                  >
                    <User size={15} color="#64748b" />
                    <input
                      id="signup-fullname"
                      type="text"
                      value={signupFullName}
                      onChange={(e) => setSignupFullName(e.target.value)}
                      placeholder="e.g. Officer Alex Vance"
                      autoComplete="name"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: '#f8fafc',
                        width: '100%',
                        fontSize: '0.88rem',
                      }}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="signup-username"
                    style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}
                  >
                    Username <span style={{ color: '#ef4444' }}>*</span>
                  </label>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      backgroundColor: '#020617',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '0.55rem 0.75rem',
                      gap: '0.5rem',
                    }}
                  >
                    <User size={15} color="#64748b" />
                    <input
                      id="signup-username"
                      type="text"
                      value={signupUsername}
                      onChange={(e) => setSignupUsername(e.target.value)}
                      placeholder="At least 3 characters (e.g. avance)"
                      autoComplete="username"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: '#f8fafc',
                        width: '100%',
                        fontSize: '0.88rem',
                      }}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="signup-email"
                    style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}
                  >
                    Email Address <span style={{ color: '#64748b' }}>(Optional)</span>
                  </label>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      backgroundColor: '#020617',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '0.55rem 0.75rem',
                      gap: '0.5rem',
                    }}
                  >
                    <Mail size={15} color="#64748b" />
                    <input
                      id="signup-email"
                      type="email"
                      value={signupEmail}
                      onChange={(e) => setSignupEmail(e.target.value)}
                      placeholder="e.g. avance@sentinel.local"
                      autoComplete="email"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: '#f8fafc',
                        width: '100%',
                        fontSize: '0.88rem',
                      }}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="signup-password"
                    style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}
                  >
                    Password <span style={{ color: '#ef4444' }}>*</span>{' '}
                    <span style={{ color: '#64748b', fontSize: '0.72rem' }}>(min. 6 characters)</span>
                  </label>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      backgroundColor: '#020617',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '0.55rem 0.75rem',
                      gap: '0.5rem',
                    }}
                  >
                    <Lock size={15} color="#64748b" />
                    <input
                      id="signup-password"
                      type={showSignupPassword ? 'text' : 'password'}
                      value={signupPassword}
                      onChange={(e) => setSignupPassword(e.target.value)}
                      placeholder="Enter strong password"
                      autoComplete="new-password"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: '#f8fafc',
                        width: '100%',
                        fontSize: '0.88rem',
                      }}
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowSignupPassword(!showSignupPassword)}
                      aria-label={showSignupPassword ? 'Hide password' : 'Show password'}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#64748b',
                        cursor: 'pointer',
                        padding: 0,
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      {showSignupPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="signup-confirm-password"
                    style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}
                  >
                    Confirm Password <span style={{ color: '#ef4444' }}>*</span>
                  </label>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      backgroundColor: '#020617',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '0.55rem 0.75rem',
                      gap: '0.5rem',
                    }}
                  >
                    <Lock size={15} color="#64748b" />
                    <input
                      id="signup-confirm-password"
                      type={showSignupPassword ? 'text' : 'password'}
                      value={signupConfirmPassword}
                      onChange={(e) => setSignupConfirmPassword(e.target.value)}
                      placeholder="Re-enter password"
                      autoComplete="new-password"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: '#f8fafc',
                        width: '100%',
                        fontSize: '0.88rem',
                      }}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {/* Role policy badge */}
                <div
                  style={{
                    backgroundColor: 'rgba(56, 189, 248, 0.08)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    fontSize: '0.72rem',
                    color: '#94a3b8',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '6px',
                  }}
                >
                  <Shield size={13} color="#38bdf8" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <span>
                    New sign-ups are assigned the <strong style={{ color: '#38bdf8' }}>OPERATOR</strong> role with permissions to monitor CCTV feeds, track incursion alerts, and resolve security events.
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  style={{
                    backgroundColor: '#0284c7',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '0.7rem 1rem',
                    fontSize: '0.88rem',
                    fontWeight: 600,
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    opacity: isLoading ? 0.7 : 1,
                    marginTop: '0.3rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    transition: 'background 0.15s ease',
                  }}
                >
                  <UserPlus size={15} />
                  {isLoading ? 'Creating Account...' : 'Create Account & Sign In'}
                </button>
              </form>

              <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#38bdf8',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  Already have an account? Sign in here &rarr;
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
