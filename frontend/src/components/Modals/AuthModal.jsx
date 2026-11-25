import React, { useState, useEffect } from 'react';
import { X, Building2 } from 'lucide-react';
import { supabase } from '../../lib/supabaseClient';

export default function AuthModal({ isOpen, onClose, initialMode = 'login', onLogin }) {
  const [mode, setMode] = useState(initialMode);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMode(initialMode);
    setError('');
    setInfo('');
  }, [initialMode, isOpen]);

  if (!isOpen) return null;

  const toAppUser = (sbUser, fallbackName, fallbackPhone) => {
    const fullName = sbUser?.user_metadata?.full_name || fallbackName || sbUser?.email || 'SKANDX Buyer';
    return {
      id: sbUser?.id || null,
      name: fullName,
      email: sbUser?.email || email,
      phone: sbUser?.user_metadata?.phone || fallbackPhone || '',
      initials: fullName
        .split(' ')
        .map((w) => w[0])
        .slice(0, 2)
        .join('')
        .toUpperCase(),
      isLoggedIn: true,
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');

    if (!supabase) {
      setError('Customer authentication is not configured (missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY).');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'reset') {
        const { error: resetErr } = await supabase.auth.resetPasswordForEmail(email.trim());
        if (resetErr) throw resetErr;
        setInfo('Password reset link sent to your email.');
        return;
      }

      if (mode === 'register') {
        const { data, error: signUpErr } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { data: { full_name: name.trim(), phone: phone.trim() } },
        });
        if (signUpErr) throw signUpErr;
        if (data.user && data.session) {
          onLogin(toAppUser(data.user, name, phone));
          onClose();
        } else {
          setInfo('Account created. Please check your email to confirm your address before signing in.');
        }
        return;
      }

      const { data, error: signInErr } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });
      if (signInErr) throw signInErr;
      if (data.user) {
        onLogin(toAppUser(data.user));
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        <div className="modal-head">
          <span className="brand-mark">
            <Building2 size={24} />
          </span>
          <h3>
            {mode === 'login' ? 'Sign In' : mode === 'register' ? 'Create Buyer Account' : 'Reset Password'}
          </h3>
          <p>
            {mode === 'login'
              ? 'Access saved properties, comparisons, and advisor requests.'
              : mode === 'register'
                ? 'Create an account to save properties and connect with auction advisors.'
                : 'Enter your registered email to receive a password recovery link.'}
          </p>
        </div>

        {error && (
          <div style={{ marginBottom: 12, padding: '10px 12px', borderRadius: 8, background: '#FEF2F2', color: '#991B1B', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}
        {info && (
          <div style={{ marginBottom: 12, padding: '10px 12px', borderRadius: 8, background: '#F0FDF4', color: '#166534', fontSize: '0.85rem' }}>
            {info}
          </div>
        )}

        <form className="modal-form" onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="form-field">
              <label>Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your full name"
                required
              />
            </div>
          )}

          <div className="form-field">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>

          {mode === 'register' && (
            <div className="form-field">
              <label>Mobile Number</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98400 00000"
                required
              />
            </div>
          )}

          {mode !== 'reset' && (
            <div className="form-field">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                minLength={6}
                required
              />
            </div>
          )}

          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading
              ? 'Please wait...'
              : mode === 'login'
                ? 'Sign In'
                : mode === 'register'
                  ? 'Create Account'
                  : 'Send Recovery Link'}
          </button>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, fontSize: '0.84rem' }}>
            {mode === 'login' ? (
              <>
                <button type="button" onClick={() => setMode('register')} style={{ background: 'none', border: 'none', color: '#0A2540', cursor: 'pointer', textDecoration: 'underline' }}>
                  Create account
                </button>
                <button type="button" onClick={() => setMode('reset')} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer' }}>
                  Forgot password?
                </button>
              </>
            ) : (
              <button type="button" onClick={() => setMode('login')} style={{ background: 'none', border: 'none', color: '#0A2540', cursor: 'pointer', textDecoration: 'underline' }}>
                Back to Sign In
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
