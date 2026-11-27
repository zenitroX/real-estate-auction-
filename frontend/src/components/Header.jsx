import React, { useState, useRef, useEffect } from 'react';
import {
  Building2,
  Search,
  Bell,
  Menu,
  X,
  Gavel,
  Clock,
  ShieldCheck,
  Trophy,
  CheckCheck,
  User,
  SlidersHorizontal,
  LogOut,
  ExternalLink,
  Users,
  Play,
} from 'lucide-react';

export default function Header({
  activePage,
  setActivePage,
  onOpenSearch,
  user,
  onOpenAuth,
  notifications,
  onMarkAllRead,
  viewMode,
  onSetViewMode,
  pendingCount = 0,
  isAdminPortal = false,
  adminSession = null,
  onAdminLogout,
  showDevSwitcher = true,
  adminActiveTab = 'verification',
  onSetAdminTab,
}) {
  const [showNotifs, setShowNotifs] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const notifRef = useRef(null);

  const unreadCount = notifications ? notifications.filter((n) => n.unread).length : 0;

  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifs(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const customerNavItems = [
    { id: 'home', label: 'Home' },
    { id: 'properties', label: 'Properties' },
    { id: 'auctions', label: 'Auctions' },
    { id: 'services', label: 'Services' },
    { id: 'about', label: 'About Us' },
  ];

  const adminNavItems = [
    { id: 'verification', label: 'Verification Queue', count: pendingCount },
    { id: 'published', label: 'Verified Inventory' },
    { id: 'leads', label: 'Buyer Leads' },
    { id: 'scrapers', label: 'Scraper Engine' },
  ];

  return (
    <header className="site-header">
      <div className="header-inner">
        {/* Brand */}
        <button
          className="brand"
          onClick={() => {
            if (isAdminPortal) {
              if (onSetAdminTab) onSetAdminTab('verification');
              return;
            }
            onSetViewMode('customer');
            setActivePage('home');
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          aria-label="SKANDX home"
        >
          {isAdminPortal && (
            <span className="brand-mark" style={{ background: '#16A34A' }}>
              <ShieldCheck size={22} color="#fff" />
            </span>
          )}
          <span className="brand-text">
            <span>
              SKAN<span className="gold">D<span className="brand-x">X</span></span>
            </span>
            <small>{isAdminPortal ? 'Admin Verification Desk' : 'The Future of Property Auctions'}</small>
          </span>
        </button>

        {/* Desktop Navigation */}
        <nav className="main-nav" aria-label="Primary navigation">
          {isAdminPortal ? (
            adminNavItems.map((item) => (
              <button
                key={item.id}
                className={`nav-link ${adminActiveTab === item.id ? 'active' : ''}`}
                onClick={() => {
                  if (onSetAdminTab) onSetAdminTab(item.id);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                {item.label}
                {item.count !== undefined && item.count > 0 && (
                  <span
                    style={{
                      background: adminActiveTab === item.id ? '#D97706' : 'rgba(217, 119, 6, 0.25)',
                      color: adminActiveTab === item.id ? '#fff' : '#F59E0B',
                      fontSize: '0.62rem',
                      padding: '1px 6px',
                      borderRadius: 10,
                      marginLeft: 6,
                      fontWeight: 800,
                    }}
                  >
                    {item.count}
                  </span>
                )}
              </button>
            ))
          ) : (
            customerNavItems.map((item) => (
              <button
                key={item.id}
                className={`nav-link ${viewMode === 'customer' && activePage === item.id ? 'active' : ''}`}
                onClick={() => {
                  onSetViewMode('customer');
                  setActivePage(item.id);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                {item.label}
              </button>
            ))
          )}
        </nav>

        {/* Actions & Role Switcher */}
        <div className="header-actions">
          {/* Admin Portal Header Status & Logout */}
          {isAdminPortal ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '5px 12px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  borderRadius: 20,
                  fontSize: '0.8rem',
                  color: '#CBD5E1',
                }}
              >
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22C55E' }}></span>
                <span>{adminSession?.name || 'Chief Officer'}</span>
              </div>

              {onAdminLogout && (
                <button
                  onClick={onAdminLogout}
                  className="btn btn-outline btn-sm"
                  style={{ borderColor: 'rgba(255,255,255,0.2)', color: '#FCA5A5' }}
                  title="Logout from admin session"
                >
                  <LogOut size={14} /> Logout
                </button>
              )}
            </div>
          ) : (
            <>
              {/* Dev Switcher: Only visible in local development, hidden in production customer site */}
              {showDevSwitcher && (
                <div
                  className="dev-switcher-wrap"
                  style={{
                    display: 'flex',
                    background: 'rgba(255, 255, 255, 0.08)',
                    borderRadius: 24,
                    padding: 3,
                    border: '1px solid rgba(255, 255, 255, 0.16)',
                  }}
                >
                  <button
                    onClick={() => onSetViewMode('customer')}
                    style={{
                      padding: '5px 11px',
                      borderRadius: 20,
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      background: viewMode === 'customer' ? 'linear-gradient(135deg, var(--gold), var(--gold-2))' : 'transparent',
                      color: viewMode === 'customer' ? 'var(--navy)' : '#CBD5E1',
                      transition: 'all 0.2s',
                    }}
                    title="Browse as customer"
                  >
                    <User size={13} /> Customer
                  </button>

                  <button
                    onClick={() => onSetViewMode('admin')}
                    style={{
                      padding: '5px 11px',
                      borderRadius: 20,
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      background: viewMode === 'admin' ? '#22C55E' : 'transparent',
                      color: viewMode === 'admin' ? '#fff' : '#CBD5E1',
                      transition: 'all 0.2s',
                    }}
                    title="Switch to admin verification desk"
                  >
                    <ShieldCheck size={13} /> Admin
                    {pendingCount > 0 && (
                      <span
                        style={{
                          background: viewMode === 'admin' ? '#166534' : '#E8B849',
                          color: viewMode === 'admin' ? '#fff' : '#071D35',
                          fontSize: '0.62rem',
                          padding: '1px 5px',
                          borderRadius: 10,
                        }}
                      >
                        {pendingCount}
                      </span>
                    )}
                  </button>
                </div>
              )}

              {/* Login / Register / Account */}
              {user && user.isLoggedIn ? (
                <button
                  className="nav-link"
                  onClick={() => {
                    onSetViewMode('customer');
                    setActivePage('dashboard');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  title={`Account (${user.name})`}
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <User size={16} /> Account
                </button>
              ) : (
                <>
                  <button
                    className="nav-link"
                    onClick={() => onOpenAuth('login')}
                  >
                    Login
                  </button>
                  <button
                    className="btn btn-gold btn-sm"
                    onClick={() => onOpenAuth('register')}
                    style={{ fontWeight: 600 }}
                  >
                    Register
                  </button>
                </>
              )}

              {/* Mobile hamburger */}
              <button
                className="icon-btn hamburger"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle mobile menu"
              >
                {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileMenuOpen && (
        <nav className="mobile-nav open">
          {isAdminPortal ? (
            adminNavItems.map((item) => (
              <button
                key={item.id}
                className={`nav-link ${adminActiveTab === item.id ? 'active' : ''}`}
                onClick={() => {
                  if (onSetAdminTab) onSetAdminTab(item.id);
                  setMobileMenuOpen(false);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                {item.label}
              </button>
            ))
          ) : (
            <>
              {showDevSwitcher && (
                <div style={{ display: 'flex', gap: 10, padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: 8 }}>
                  <button
                    className="btn btn-sm"
                    onClick={() => {
                      onSetViewMode('customer');
                      setMobileMenuOpen(false);
                    }}
                    style={{
                      flex: 1,
                      background: viewMode === 'customer' ? 'var(--gold)' : 'rgba(255,255,255,0.1)',
                      color: viewMode === 'customer' ? 'var(--navy)' : '#fff',
                    }}
                  >
                    Customer Portal
                  </button>
                  <button
                    className="btn btn-sm"
                    onClick={() => {
                      onSetViewMode('admin');
                      setMobileMenuOpen(false);
                    }}
                    style={{
                      flex: 1,
                      background: viewMode === 'admin' ? '#22C55E' : 'rgba(255,255,255,0.1)',
                      color: '#fff',
                    }}
                  >
                    Admin Console
                  </button>
                </div>
              )}

              {customerNavItems.map((item) => (
                <button
                  key={item.id}
                  className={`nav-link ${viewMode === 'customer' && activePage === item.id ? 'active' : ''}`}
                  onClick={() => {
                    onSetViewMode('customer');
                    setActivePage(item.id);
                    setMobileMenuOpen(false);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                >
                  {item.label}
                </button>
              ))}
              <button
                className={`nav-link ${activePage === 'dashboard' ? 'active' : ''}`}
                onClick={() => {
                  onSetViewMode('customer');
                  setActivePage('dashboard');
                  setMobileMenuOpen(false);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                <User size={16} /> Buyer Dashboard
              </button>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
