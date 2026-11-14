import React, { useState } from 'react';
import { X, Building2, User, Mail, Phone, Lock } from 'lucide-react';

export default function AuthModal({ isOpen, onClose, initialMode = 'login', onLogin }) {
  const [mode, setMode] = useState(initialMode);
  const [name, setName] = useState('Udhaya Kumar R');
  const [email, setEmail] = useState('udhaya.kumar@skandx.demo');
  const [phone, setPhone] = useState('+91 98407 22110');
  const [password, setPassword] = useState('demo1234');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin({
      name: mode === 'register' ? name : (name || 'Udhaya Kumar R'),
      email,
      phone,
      initials: (mode === 'register' ? name : 'Udhaya Kumar R')
        .split(' ')
        .map((w) => w[0])
        .slice(0, 2)
        .join('')
        .toUpperCase(),
      city: 'Chennai',
      isLoggedIn: true,
      memberSince: 'Jan 2024',
      isVerified: true,
    });
    onClose();
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
          <h3>{mode === 'login' ? 'Welcome Back' : 'Create Account'}</h3>
          <p>
            {mode === 'login'
              ? 'Log in to your SKANDX bidder portal to track and place bids.'
              : 'Join 15,000+ registered bidders across India.'}
          </p>
        </div>

        <form className="modal-form" onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="form-field">
              <label>Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Udhaya Kumar R"
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
              <label>Mobile Number (for Auction OTP)</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98407 22110"
                required
              />
            </div>
          )}

          <div className="form-field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button className="btn btn-gold btn-block btn-lg" type="submit">
            {mode === 'login' ? 'Login to Portal' : 'Register Free Account'}
          </button>

          <p className="modal-alt">
            {mode === 'login' ? (
              <>
                New to SKANDX?{' '}
                <button type="button" onClick={() => setMode('register')}>
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already registered?{' '}
                <button type="button" onClick={() => setMode('login')}>
                  Login instead
                </button>
              </>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}
