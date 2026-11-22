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
  UserCheck,
  KeyRound,
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
  const heroProperty = properties.find((p) => p.id === 'p2') || properties[0] || null;
  const [heroCountdown, setHeroCountdown] = useState(() =>
    timeRemaining(heroProperty?.auctionEnd || Date.now() + 86400000)
  );

  useEffect(() => {
    if (!heroProperty) return;
    const timer = setInterval(() => {
      setHeroCountdown(timeRemaining(heroProperty?.auctionEnd || Date.now() + 86400000));
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
              India's Premier <span className="gold">Bank Auction Concierge</span>
            </h1>

            <p className="hero-sub">
              Discover Verified Distressed Assets & Bid with Complete Legal Confidence. Comprehensive 30-year title checks, SARFAESI direct bank inventory, and assisted bidding on official government portals.
            </p>

            <ul className="hero-features">
              <li>
                <span className="hf-icon"><Building2 size={16} /></span>
                <span>Direct Bank Inventory</span>
              </li>
              <li>
                <span className="hf-icon"><ShieldCheck size={16} /></span>
                <span>Verified Clean Titles</span>
              </li>
              <li>
                <span className="hf-icon"><Scale size={16} /></span>
                <span>Legal Due Diligence</span>
              </li>
              <li>
                <span className="hf-icon"><Headset size={16} /></span>
                <span>Assisted Bidding Concierge</span>
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
              {heroProperty && (
                <div className="hero-float-card">
                  <span className="hfc-label">Next E-Auction Ends In</span>
                  <strong className="hfc-count">
                    {heroCountdown.d}d {pad2(heroCountdown.h)}h {pad2(heroCountdown.m)}m {pad2(heroCountdown.s)}s
                  </strong>
                  <span className="hfc-prop">
                    {heroProperty.title} &middot; {heroProperty.locality}
                  </span>
                </div>
              )}
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
              <h4>Assisted Bank Bidding</h4>
              <p>
                Expert guidance on EMD deposits and live bidding representation on official bank portals including e-Bikray, IBAPI, and MSTC.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4 STEP ASSISTED BIDDING PROCESS */}
      <section className="section process-section">
        <div className="container">
          <div className="center">
            <h2>
              How Assisted Bank Bidding <span className="gold">Works</span>
            </h2>
            <p style={{ color: '#64748B', marginTop: 4 }}>
              Four simple transparent steps from listing discovery to key handover.
            </p>
          </div>

          <div className="process-grid">
            <div className="process-step">
              <span className="ps-num">01</span>
              <UserCheck size={26} color="#071D35" />
              <h4>Discover & Verify</h4>
              <p>Explore verified bank notices with 30-year legal search reports and schedule physical site visits.</p>
            </div>

            <div className="process-step">
              <span className="ps-num">02</span>
              <IndianRupee size={26} color="#071D35" />
              <h4>Deposit EMD (10%)</h4>
              <p>Transfer the statutory Earnest Money Deposit into the bank escrow to obtain bidding authorization.</p>
            </div>

            <div className="process-step">
              <span className="ps-num">03</span>
              <Gavel size={26} color="#071D35" />
              <h4>Assisted Bank Portal Bidding</h4>
              <p>Assisted Bidding on Official Bank Portals: Expert guidance on EMD deposit and live bidding on e-Bikray/IBAPI.</p>
            </div>

            <div className="process-step">
              <span className="ps-num">04</span>
              <KeyRound size={26} color="#071D35" />
              <h4>Win & Take Possession</h4>
              <p>Receive your Sale Certificate, settle balance funds, and receive physical possession supported by our legal team.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
