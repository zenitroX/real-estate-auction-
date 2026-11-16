import React, { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  Mail,
  Building2,
  ArrowRight,
  AlertCircle,
  KeyRound,
  FileCheck2,
  CheckCircle2,
} from 'lucide-react';
import { loginAdminApi } from '../data/api';

export default function AdminLoginView({ onLoginSuccess, onReturnToCustomer }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const data = await loginAdminApi(email.trim(), password);
      if (data && data.status === 'success' && data.token) {
        const user = data.admin || data.user || {
          name: 'Chief Auction Officer',
          email: email.trim().toLowerCase(),
          role: 'SUPER_ADMIN',
        };
        const adminSession = {
          token: data.token,
          name: user.name || 'Chief Auction Officer',
          email: user.email || email,
          role: user.role || 'SUPER_ADMIN',
          loginTime: Date.now(),
        };
        sessionStorage.setItem('skandx_admin_session', JSON.stringify(adminSession));
        setIsLoading(false);
        onLoginSuccess(data.token, user);
      } else {
        setIsLoading(false);
        setError(data?.message || 'Invalid administrative credentials.');
      }
    } catch (err) {
      setIsLoading(false);
      setError(err.message || 'Authentication server unreachable. Please verify network connection or wait for backend to wake up.');
    }
  };

  const handleUseDemoCreds = () => {
    setEmail('admin@skandx.com');
    setPassword('skandx@admin2026');
    setError('');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'radial-gradient(ellipse at top, #0A2540 0%, #030D1B 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        color: '#fff',
      }}
    >
      <div
        style={{
          width: 'min(460px, 100%)',
          background: 'rgba(255, 255, 255, 0.04)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: 20,
          padding: '40px 32px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        }}
      >
        {/* Brand Mark & Shield */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div
            style={{
              width: 56,
              height: 56,
              margin: '0 auto 16px',
              borderRadius: 14,
              background: 'linear-gradient(135deg, var(--gold), var(--gold-2))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--navy)',
              boxShadow: '0 10px 25px -5px rgba(217, 166, 46, 0.4)',
            }}
          >
            <ShieldCheck size={32} />
          </div>

          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }}>
            SKANDX <span style={{ color: 'var(--gold)' }}>Admin Gateway</span>
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '0.86rem', marginTop: 8 }}>
            Authorized SARFAESI Verification & Crawler Operations
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '12px 14px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 10,
              color: '#FCA5A5',
              fontSize: '0.85rem',
              marginBottom: 20,
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#CBD5E1',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: 6,
              }}
            >
              Admin Email
            </label>
            <div style={{ position: 'relative' }}>
              <Mail
                size={18}
                style={{
                  position: 'absolute',
                  left: 14,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#64748B',
                }}
              />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  width: '100%',
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  borderRadius: 10,
                  padding: '12px 14px 12px 42px',
                  color: '#fff',
                  fontSize: '0.95rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#CBD5E1',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: 6,
              }}
            >
              Security Key / Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={18}
                style={{
                  position: 'absolute',
                  left: 14,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#64748B',
                }}
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  borderRadius: 10,
                  padding: '12px 14px 12px 42px',
                  color: '#fff',
                  fontSize: '0.95rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          {/* Quick Demo Credentials Autofill */}
          <button
            type="button"
            onClick={handleUseDemoCreds}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--gold)',
              fontSize: '0.78rem',
              textAlign: 'left',
              cursor: 'pointer',
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <KeyRound size={13} /> Autofill demo credentials
          </button>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-gold btn-block btn-lg"
            style={{ marginTop: 6 }}
          >
            {isLoading ? 'Authenticating...' : (
              <>
                Unlock Verification Console <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Security badges */}
        <div
          style={{
            marginTop: 32,
            paddingTop: 20,
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
            fontSize: '0.74rem',
            color: '#64748B',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle2 size={13} color="#22C55E" />
            <span>256-Bit TLS End-to-End Encrypted Session</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <FileCheck2 size={13} color="#22C55E" />
            <span>SARFAESI Act 2002 Compliant Audit Trail Logging</span>
          </div>
        </div>

        {/* Return to Customer Portal */}
        {onReturnToCustomer && (
          <div style={{ textAlign: 'center', marginTop: 20 }}>
            <button
              onClick={onReturnToCustomer}
              style={{
                background: 'none',
                border: 'none',
                color: '#94A3B8',
                fontSize: '0.82rem',
                cursor: 'pointer',
                textDecoration: 'underline',
              }}
            >
              &larr; Switch to Public Customer Marketplace
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
