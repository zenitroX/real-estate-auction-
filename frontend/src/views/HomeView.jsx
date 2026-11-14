import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Building2,
  Scale,
  Headset,
  ArrowRight,
  MapPin,
  Building,
  IndianRupee,
  Search,
  Gavel,
  Users,
  FileCheck2,
  Clock,
} from 'lucide-react';
import PropertyCard from '../components/PropertyCard';
import { timeRemaining, pad2 } from '../data/propertiesData';

export default function HomeView({
  properties,
  onNavigate,
  onViewProperty,
  onContact,
  wishlist,
  onToggleWishlist,
  onApplySearchFilters,
}) {
  const [activeTab, setActiveTab] = useState('all');
  const [locationInput, setLocationInput] = useState('');
  const [typeInput, setTypeInput] = useState('all');
  const [budgetInput, setBudgetInput] = useState('all');

  // Next E-Auction Ends Live Countdown for Hero Floating Card (Property p2)
  const heroProperty = properties.find((p) => p.id === 'p2') || properties[0];
  const [heroCountdown, setHeroCountdown] = useState(() => timeRemaining(heroProperty.auctionEnd));

  useEffect(() => {
    const timer = setInterval(() => {
      setHeroCountdown(timeRemaining(heroProperty.auctionEnd));
    }, 1000);
    return () => clearInterval(timer);
  }, [heroProperty]);

  // Only show verified published properties on public customer home
  const featuredListings = properties.filter((p) => p.featured && p.verified).slice(0, 6);

  const handleQuickSearch = (e) => {
    e.preventDefault();
    onApplySearchFilters({
      locality: locationInput,
      type: typeInput !== 'all' ? typeInput : (activeTab !== 'all' ? activeTab : 'all'),
      budget: budgetInput,
    });
    onNavigate('properties');
  };

  return (
    <div className="home-view">
      {/* HERO */}
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
            <span className="hero-eyebrow">
              <ShieldCheck size={16} /> India's Trusted Bank Auction Marketplace
            </span>

            <h1 className="hero-title">
              Discover. Bid. <span className="gold">Own.</span>
            </h1>

            <p className="hero-sub">
              Bank Auction & Distressed Properties with Complete Transparency. Verified titles, SARFAESI direct bank inventory, and end-to-end possession assistance.
            </p>

            <ul className="hero-features">
              <li>
                <span className="hf-icon"><Building2 size={16} /></span>
                <span>Bank Auction Properties</span>
              </li>
              <li>
                <span className="hf-icon"><ShieldCheck size={16} /></span>
                <span>Verified Listings</span>
              </li>
              <li>
                <span className="hf-icon"><Scale size={16} /></span>
                <span>Legal Assistance</span>
              </li>
              <li>
                <span className="hf-icon"><Headset size={16} /></span>
                <span>End-to-End Support</span>
              </li>
            </ul>

            <div className="hero-cta">
              <button
                className="btn btn-gold btn-lg"
                onClick={() => onNavigate('properties')}
              >
                Explore Auctions <ArrowRight size={18} />
              </button>
              <button
                className="btn btn-outline-light btn-lg"
                onClick={() => onNavigate('about')}
              >
                How It Works
              </button>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-img-wrap">
              <img
                src="https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1100&q=80"
                alt="Luxury modern villa and auction asset"
                loading="eager"
              />
              <div className="hero-float-card">
                <span className="hfc-label">Next E-Auction Ends In</span>
                <strong className="hfc-count">
                  {heroCountdown.d}d {pad2(heroCountdown.h)}h {pad2(heroCountdown.m)}m {pad2(heroCountdown.s)}s
                </strong>
                <span className="hfc-prop">
                  {heroProperty.title} &middot; {heroProperty.locality}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* QUICK SEARCH FLOATING PANEL */}
      <div className="search-panel-wrap">
        <div className="search-panel">
          <div className="sp-tabs">
            {[
              { id: 'all', label: 'All Properties' },
              { id: 'residential', label: 'Residential' },
              { id: 'commercial', label: 'Commercial' },
              { id: 'land', label: 'Land / Plot' },
              { id: 'industrial', label: 'Industrial' },
            ].map((tab) => (
              <button
                key={tab.id}
                className={`sp-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(tab.id);
                  if (tab.id !== 'all') setTypeInput(tab.id);
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <form className="sp-fields" onSubmit={handleQuickSearch}>
            <div className="sp-field">
              <label>
                <MapPin size={15} /> Enter Location (e.g. Chennai)
              </label>
              <input
                type="text"
                placeholder="City, locality or pincode..."
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
              />
            </div>

            <div className="sp-field">
              <label>
                <Building size={15} /> Property Type
              </label>
              <select value={typeInput} onChange={(e) => setTypeInput(e.target.value)}>
                <option value="all">Any Type</option>
                <option value="residential">Residential</option>
                <option value="commercial">Commercial</option>
                <option value="land">Land / Plot</option>
                <option value="industrial">Industrial</option>
              </select>
            </div>

            <div className="sp-field">
              <label>
                <IndianRupee size={15} /> Budget Range
              </label>
              <select value={budgetInput} onChange={(e) => setBudgetInput(e.target.value)}>
                <option value="all">Any Budget</option>
                <option value="under50">Under ₹50 Lakhs</option>
                <option value="50to1cr">₹50 L – ₹1 Cr</option>
                <option value="1crto2cr">₹1 Cr – ₹2 Cr</option>
                <option value="above2cr">Above ₹2 Cr</option>
              </select>
            </div>

            <button className="btn btn-navy btn-lg" type="submit">
              <Search size={18} /> Search
            </button>
          </form>
        </div>
      </div>

      {/* STATS BAND */}
      <section className="stats-band">
        <div className="container stats-grid">
          <div className="stat">
            <div className="stat-icon">
              <Building2 size={26} />
            </div>
            <div className="stat-info">
              <strong>5,000+</strong>
              <span>Properties Listed</span>
            </div>
          </div>

          <div className="stat">
            <div className="stat-icon">
              <Gavel size={26} />
            </div>
            <div className="stat-info">
              <strong>1,200+</strong>
              <span>Auctions Completed</span>
            </div>
          </div>

          <div className="stat">
            <div className="stat-icon">
              <Users size={26} />
            </div>
            <div className="stat-info">
              <strong>15,000+</strong>
              <span>Registered Bidders</span>
            </div>
          </div>

          <div className="stat">
            <div className="stat-icon">
              <Building size={26} />
            </div>
            <div className="stat-info">
              <strong>20+</strong>
              <span>Partner Banks</span>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURED AUCTION PROPERTIES */}
      <section className="section">
        <div className="container">
          <div className="section-head">
            <div>
              <h2>Featured Auction <span className="gold">Properties</span></h2>
              <p>Hand-picked bank-owned assets across India's prime metropolitan locations.</p>
            </div>
            <button className="btn btn-outline" onClick={() => onNavigate('properties')}>
              View All Properties <ArrowRight size={16} />
            </button>
          </div>

          <div className="prop-grid">
            {featuredListings.map((p) => (
              <PropertyCard
                key={p.id}
                property={p}
                onView={onViewProperty}
                onContact={onContact}
                isWishlisted={wishlist.includes(p.id)}
                onToggleWishlist={onToggleWishlist}
              />
            ))}
          </div>
        </div>
      </section>

      {/* TRUST STRIP */}
      <section className="section trust-section">
        <div className="container">
          <div className="center">
            <h2>Why Institutional Bidders Choose <span className="gold">SKANDX</span></h2>
            <p style={{ color: '#64748B', marginTop: 4 }}>
              Direct integration with India's top public & private sector banking recovery wings.
            </p>
          </div>

          <div className="trust-grid">
            <div className="trust-card">
              <div className="trust-icon">
                <FileCheck2 size={24} />
              </div>
              <h4>Complete Legal Check</h4>
              <p>
                Every listing passes 30-year title search, encumbrance verification (EC), and court-case scrutiny by empanelled High Court advocates.
              </p>
            </div>

            <div className="trust-card">
              <div className="trust-icon">
                <Building2 size={24} />
              </div>
              <h4>Direct From Partner Banks</h4>
              <p>
                Official listings from 20+ partner banks including SBI, Canara Bank, ICICI Bank, Indian Bank, and Axis Bank with zero intermediary markup.
              </p>
            </div>

            <div className="trust-card">
              <div className="trust-icon">
                <Gavel size={24} />
              </div>
              <h4>Transparent Bidding Engine</h4>
              <p>
                Real-time electronic auction engine with published reserve prices, verified EMD custody, and clear timestamped bid records.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
