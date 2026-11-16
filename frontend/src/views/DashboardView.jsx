import React, { useState } from 'react';
import {
  LayoutDashboard,
  Gavel,
  Heart,
  Bell,
  User,
  ShieldCheck,
  Headset,
  LogOut,
  Trophy,
  Cog,
  Eye,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Upload,
  ArrowRight,
  ChevronDown,
  Building2,
} from 'lucide-react';
import PropertyCard from '../components/PropertyCard';
import {
  formatPrice,
  formatRupees,
  timeRemaining,
  pad2,
} from '../data/propertiesData';
import { FAQS } from '../data/initialUserData';

export default function DashboardView({
  user,
  myBids = {},
  wishlist = [],
  notifications = [],
  properties = [],
  onNavigate,
  onViewProperty,
  onContact,
  onBidProperty,
  onToggleWishlist,
  onMarkAllNotificationsRead,
  onUpdateProfile,
  onUploadKyc,
  onLogout,
  activeTab = 'overview',
  setActiveTab,
}) {
  const [profileName, setProfileName] = useState(user.name);
  const [profileEmail, setProfileEmail] = useState(user.email);
  const [profilePhone, setProfilePhone] = useState(user.phone);
  const [profileCity, setProfileCity] = useState(user.city || 'Chennai');
  const [expandedFaq, setExpandedFaq] = useState(0);

  const currentDate = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  // Watchlisted properties
  const savedProperties = (properties || []).filter((p) => (wishlist || []).includes(p.id));

  const handleProfileSubmit = (e) => {
    e.preventDefault();
    onUpdateProfile({
      name: profileName,
      email: profileEmail,
      phone: profilePhone,
      city: profileCity,
    });
  };

  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'saved', label: 'Saved Properties', icon: Heart },
    { id: 'alerts', label: 'Alerts & Notifications', icon: Bell },
    { id: 'profile', label: 'My Profile', icon: User },
    { id: 'kyc', label: 'KYC & Documents', icon: ShieldCheck },
    { id: 'support', label: 'Support', icon: Headset },
  ];

  return (
    <div className="dash-layout">
      {/* Left Sidebar */}
      <aside className="dash-sidebar">
        <div className="dash-brand">
          <span className="brand-mark" style={{ width: 36, height: 36 }}>
            <Building2 size={20} />
          </span>
          <span className="brand-text" style={{ fontSize: '1.15rem' }}>
            <span>
              SKAN<span className="gold">DX</span>
            </span>
            <small>Bidder Portal</small>
          </span>
        </div>

        <nav className="dash-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`dash-link ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}

          <button className="dash-link logout" onClick={onLogout}>
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </nav>

        {/* Support hotline card */}
        <div className="dash-help">
          <strong>Need help bidding?</strong>
          <span>Call our auction desk</span>
          <em>1800 - 202 - SKANDX</em>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="dash-content">
        <header className="dash-header">
          <div>
            <h2>
              {navItems.find((n) => n.id === activeTab)?.label || 'Dashboard'}
            </h2>
            <p className="dash-date">{currentDate}</p>
          </div>

          <div className="dash-user">
            <div className="dash-user-info">
              <strong>Welcome back, {user.name}</strong>
              <span>Verified Bidder &middot; Member since {user.memberSince}</span>
            </div>
            <div className="avatar">{user.initials}</div>
          </div>
        </header>

        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div>
            {/* 4 Stat Cards */}
            <div className="stat-cards">
              <div className="s-card">
                <div className="s-icon heart">
                  <Heart size={22} />
                </div>
                <div>
                  <small>Watched Properties</small>
                  <strong>{savedProperties.length}</strong>
                </div>
              </div>

              <div className="s-card">
                <div className="s-icon gear">
                  <Building2 size={22} />
                </div>
                <div>
                  <small>Live Bank Auctions</small>
                  <strong>{(properties || []).length}</strong>
                </div>
              </div>

              <div className="s-card">
                <div className="s-icon trophy">
                  <Trophy size={22} />
                </div>
                <div>
                  <small>Won / In Process</small>
                  <strong>2</strong>
                </div>
              </div>

              <div className="s-card">
                <div className="s-icon gavel">
                  <ShieldCheck size={22} />
                </div>
                <div>
                  <small>KYC Status</small>
                  <strong>Level 2 Verified</strong>
                </div>
              </div>
            </div>

            {/* Saved & Tracked Properties Panel */}
            <div className="dash-panel">
              <div className="panel-head">
                <h3>Tracked Bank Auctions</h3>
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => setActiveTab('saved')}
                >
                  View All Saved <ArrowRight size={14} />
                </button>
              </div>

              <div className="table-scroll">
                <table className="bids-table">
                  <thead>
                    <tr>
                      <th>Property</th>
                      <th>Location</th>
                      <th>Reserve Price</th>
                      <th>EMD (10%)</th>
                      <th>Auction Closes</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {savedProperties.length > 0 ? (
                      savedProperties.slice(0, 5).map((property) => {
                        const tr = timeRemaining(property.auctionEnd);
                        const timeRemainingText = tr.total === 0 ? 'Closed' : `${tr.d}d ${pad2(tr.h)}h ${pad2(tr.m)}m`;
                        return (
                          <tr key={property.id}>
                            <td>
                              <div className="t-prop">
                                <img src={(property.images && property.images[0]) || './placeholder.svg'} alt="" />
                                <div>
                                  <strong>{property.title}</strong>
                                  <small>{property.bank} &middot; {property.badge || 'BANK AUCTION'}</small>
                                </div>
                              </div>
                            </td>
                            <td>{property.locality}</td>
                            <td className="navy-val">{formatPrice(property.reserve)}</td>
                            <td className="gold-val">{formatPrice(property.emd || Math.round(property.reserve * 0.1))}</td>
                            <td className="red-val">{timeRemainingText}</td>
                            <td>
                              <span className="badge badge-green">Verified</span>
                            </td>
                            <td>
                              <button
                                className="btn btn-gold btn-sm"
                                onClick={() => {
                                  if (onContact) onContact(property);
                                  else if (onViewProperty) onViewProperty(property.id);
                                }}
                              >
                                Contact Desk
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={7} style={{ textAlign: 'center', padding: '30px' }}>
                          No saved properties yet. Click the heart icon on any auction listing to bookmark it here!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: SAVED PROPERTIES */}
        {activeTab === 'saved' && (
          <div className="dash-panel">
            <div className="panel-head">
              <h3>Saved Properties</h3>
              <span className="badge badge-gold">{savedProperties.length} Saved</span>
            </div>

            {savedProperties.length > 0 ? (
              <div className="prop-grid">
                {savedProperties.map((p) => (
                  <PropertyCard
                    key={p.id}
                    property={p}
                    onView={onViewProperty}
                    onContact={onContact}
                    isWishlisted={true}
                    onToggleWishlist={onToggleWishlist}
                  />
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <Heart size={36} color="#94A3B8" />
                <h3>No saved properties yet</h3>
                <p>Click the heart icon on any auction listing to bookmark and monitor it here.</p>
                <button className="btn btn-gold" onClick={() => onNavigate('properties')}>
                  Browse Properties
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: ALERTS & NOTIFICATIONS */}
        {activeTab === 'alerts' && (
          <div className="dash-panel">
            <div className="panel-head">
              <h3>Alerts & Notifications</h3>
              <button className="btn btn-outline btn-sm" onClick={onMarkAllNotificationsRead}>
                Mark all read
              </button>
            </div>

            <div className="notif-list" style={{ border: '1px solid #E2E8F0', borderRadius: 8 }}>
              {notifications.map((n) => (
                <div key={n.id} className={`notif-item ${n.unread ? 'unread' : ''}`}>
                  <div className="notif-icon">
                    {n.type === 'bid' && <Gavel size={16} />}
                    {n.type === 'ending' && <Clock size={16} />}
                    {n.type === 'kyc' && <ShieldCheck size={16} />}
                    {n.type === 'win' && <Trophy size={16} />}
                    {n.type === 'bank' && <Building2 size={16} />}
                  </div>
                  <div className="notif-body">
                    <strong>{n.title}</strong>
                    <p>{n.text}</p>
                    <span>{n.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 5: MY PROFILE */}
        {activeTab === 'profile' && (
          <div className="dash-panel">
            <div className="panel-head">
              <h3>My Profile</h3>
              <span className="badge badge-gold">Verified Institutional Bidder</span>
            </div>

            <form onSubmit={handleProfileSubmit} style={{ maxWidth: 600 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div className="form-field">
                  <label>Full Legal Name</label>
                  <input
                    type="text"
                    value={profileName}
                    onChange={(e) => setProfileName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-field">
                  <label>Email Address</label>
                  <input
                    type="email"
                    value={profileEmail}
                    onChange={(e) => setProfileEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                <div className="form-field">
                  <label>Mobile Number</label>
                  <input
                    type="text"
                    value={profilePhone}
                    onChange={(e) => setProfilePhone(e.target.value)}
                    required
                  />
                </div>
                <div className="form-field">
                  <label>Registered City</label>
                  <input
                    type="text"
                    value={profileCity}
                    onChange={(e) => setProfileCity(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button className="btn btn-gold" type="submit">
                Save Changes
              </button>
            </form>
          </div>
        )}

        {/* TAB 6: KYC & DOCUMENTS */}
        {activeTab === 'kyc' && (
          <div className="dash-panel">
            <div className="panel-head">
              <h3>KYC & Regulatory Documents</h3>
              <span className="badge badge-green">KYC Level 2 Active</span>
            </div>

            <div className="kyc-grid">
              <div className="kyc-card">
                <FileText color="#16A34A" />
                <div>
                  <strong>PAN Card</strong>
                  <span>{user.pan} &middot; Verified</span>
                </div>
                <span className="kyc-status ok">Verified</span>
              </div>

              <div className="kyc-card">
                <FileText color="#16A34A" />
                <div>
                  <strong>Aadhaar UID</strong>
                  <span>{user.aadhaar} &middot; Verified</span>
                </div>
                <span className="kyc-status ok">Verified</span>
              </div>

              <div className="kyc-card">
                <FileText color="#D9A62E" />
                <div>
                  <strong>Bank Account Proof</strong>
                  <span>Cancelled Cheque &middot; Pending</span>
                </div>
                <span className="kyc-status pending">Pending</span>
              </div>
            </div>

            <button className="btn btn-gold" onClick={onUploadKyc}>
              <Upload size={16} /> Upload Bank Proof (Simulated Demo)
            </button>
          </div>
        )}

        {/* TAB 7: SUPPORT */}
        {activeTab === 'support' && (
          <div className="dash-panel">
            <div className="panel-head">
              <h3>Auction Help Desk & FAQs</h3>
            </div>

            <div className="faq-list">
              {FAQS.map((faq, idx) => (
                <div key={idx} className="faq-item">
                  <button
                    className="faq-q"
                    onClick={() => setExpandedFaq(expandedFaq === idx ? -1 : idx)}
                  >
                    <span>{faq.q}</span>
                    <ChevronDown
                      size={18}
                      style={{
                        transform: expandedFaq === idx ? 'rotate(180deg)' : 'none',
                        transition: 'transform 0.2s',
                      }}
                    />
                  </button>
                  {expandedFaq === idx && (
                    <div className="faq-a">
                      <p>{faq.a}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="support-cta">
              <Headset size={32} />
              <div>
                <strong>Auction Concierge Hotline</strong>
                <p style={{ color: '#64748B', fontSize: '0.85rem' }}>
                  1800 - 202 - SKANDX &middot; support@skandx.in &middot; Mon – Sat (9 AM – 7 PM)
                </p>
              </div>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => alert('Support ticket raised. Our auction officer will contact you within 15 minutes.')}
              >
                Raise Ticket
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
