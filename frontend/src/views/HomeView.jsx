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
  ChevronRight,
} from 'lucide-react';
import { timeRemaining, pad2, formatPriceShort, typeLabel } from '../data/propertiesData';

const CITIES = [
  {
    name: 'Chennai',
    img: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=400&q=80',
    state: 'Tamil Nadu',
    count: 42,
  },
  {
    name: 'Kolkata',
    img: 'https://images.unsplash.com/photo-1558431382-27e303142255?w=400&q=80',
    state: 'West Bengal',
    count: 28,
  },
  {
    name: 'Bengaluru',
    img: 'https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?w=400&q=80',
    state: 'Karnataka',
    count: 56,
  },
  {
    name: 'Mumbai',
    img: 'https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?w=400&q=80&sig=2',
    state: 'Maharashtra',
    count: 74,
  },
  {
    name: 'Hyderabad',
    img: 'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=400&q=80',
    state: 'Telangana',
    count: 33,
  },
  {
    name: 'Pune',
    img: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=400&q=80',
    state: 'Maharashtra',
    count: 21,
  },
  {
    name: 'Delhi NCR',
    img: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=400&q=80&sig=2',
    state: 'Delhi',
    count: 61,
  },
  {
    name: 'Ahmedabad',
    img: 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400&q=80',
    state: 'Gujarat',
    count: 19,
  },
];

function ExploreByCitySection({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('property');

  return (
    <section className="section ebc-section">
      <div className="container">
        {/* Header */}
        <div className="ebc-header">
          <h2 className="ebc-heading">Explore by <span className="gold">City</span></h2>
          <div className="ebc-toggle">
            <button
              className={`ebc-tab ${activeTab === 'property' ? 'active' : ''}`}
              onClick={() => setActiveTab('property')}
            >
              Property
            </button>
            <button
              className={`ebc-tab ${activeTab === 'movable' ? 'active' : ''}`}
              onClick={() => setActiveTab('movable')}
            >
              Movable Asset
            </button>
          </div>
        </div>

        {/* City grid */}
        <div className="ebc-grid">
          {CITIES.map((city) => (
            <button
              key={city.name}
              className="ebc-city-card"
              onClick={() => onNavigate('properties')}
              aria-label={`Browse ${activeTab === 'property' ? 'properties' : 'movable assets'} in ${city.name}`}
            >
              <div className="ebc-img-wrap">
                <img
                  src={city.img}
                  alt={city.name}
                  loading="lazy"
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src = `https://source.unsplash.com/400x260/?${city.name},landmark`;
                  }}
                />
                <span className="ebc-count">{city.count}+ listings</span>
              </div>
              <span className="ebc-city-name">{city.name}</span>
            </button>
          ))}
        </div>

        {/* See All */}
        <div className="ebc-footer">
          <button className="ebc-see-all" onClick={() => onNavigate('properties')}>
            See All <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </section>
  );
}

const ASSET_CATEGORIES = [
  {
    count: '56152',
    name: 'Residential',
    typeKey: 'residential',
    img: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=600&q=80',
  },
  {
    count: '8257',
    name: 'Commercial',
    typeKey: 'commercial',
    img: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&q=80',
  },
  {
    count: '398',
    name: 'Agricultural',
    typeKey: 'land',
    img: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&q=80',
  },
  {
    count: '4122',
    name: 'Industrial',
    typeKey: 'industrial',
    img: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=600&q=80',
  },
  {
    count: '7481',
    name: 'Others',
    typeKey: 'all',
    img: 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=600&q=80',
  },
];

function ExploreAssetsByCategorySection({ properties, onViewProperty, onNavigate }) {
  const [activeTab, setActiveTab] = useState('property');
  const [startIndex, setStartIndex] = useState(0);

  const displayList = properties && properties.length > 0 ? properties : [];
  const currentItems = displayList.slice(startIndex, startIndex + 4);

  const handleNext = () => {
    if (startIndex + 4 < displayList.length) {
      setStartIndex((prev) => prev + 1);
    } else {
      setStartIndex(0);
    }
  };

  return (
    <section className="eac-section">
      <div className="container">
        <div className="eac-header">
          <h2 className="eac-heading">Explore Assets by Category</h2>
          <div className="ebc-toggle">
            <button
              className={`ebc-tab ${activeTab === 'property' ? 'active' : ''}`}
              onClick={() => setActiveTab('property')}
            >
              Property
            </button>
            <button
              className={`ebc-tab ${activeTab === 'movable' ? 'active' : ''}`}
              onClick={() => setActiveTab('movable')}
            >
              Movable Asset
            </button>
          </div>
        </div>

        <div className="eac-card-container">
          <div className="eac-grid">
            {currentItems.map((p) => (
              <div
                key={p.id}
                className="eac-item-card"
                onClick={() => onViewProperty(p.id)}
                role="button"
                tabIndex={0}
              >
                <div className="eac-img-wrap">
                  <img
                    src={p.images?.[0] || './placeholder.svg'}
                    alt={p.title}
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = './placeholder.svg';
                    }}
                  />
                </div>
                <div className="eac-body">
                  <h4 className="eac-item-title" title={p.title}>
                    {p.title}
                  </h4>
                  <span className="eac-item-type">{typeLabel(p.type)}</span>
                  <div className="eac-item-bank">
                    <span className="eac-bank-name">{p.bank}</span>
                    <span className="eac-asset-code">{p.assetCode || `ID: #${p.id}`}</span>
                  </div>
                  <div className="eac-item-foot">
                    <span className="eac-locality">
                      <MapPin size={12} /> {p.locality ? p.locality.split(',')[0] : 'India'}
                    </span>
                    <strong className="eac-price">{formatPriceShort(p.reserve)}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {displayList.length > 4 && (
            <button className="eac-next-btn" onClick={handleNext} aria-label="Next properties">
              <ChevronRight size={20} />
            </button>
          )}

          <div className="eac-view-all-wrap">
            <button className="eac-view-all-btn" onClick={() => onNavigate('properties')}>
              View all &gt;
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function AssetsAvailableSection({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('property');

  return (
    <section className="aa-section">
      <div className="container">
        <div className="aa-header">
          <h2 className="aa-heading">Assets Available</h2>
          <div className="ebc-toggle">
            <button
              className={`ebc-tab ${activeTab === 'property' ? 'active' : ''}`}
              onClick={() => setActiveTab('property')}
            >
              Property
            </button>
            <button
              className={`ebc-tab ${activeTab === 'movable' ? 'active' : ''}`}
              onClick={() => setActiveTab('movable')}
            >
              Movable Asset
            </button>
          </div>
        </div>

        <div className="aa-grid">
          {ASSET_CATEGORIES.map((cat) => (
            <div
              key={cat.name}
              className="aa-card"
              onClick={() => onNavigate('properties')}
              role="button"
              tabIndex={0}
            >
              <img
                src={cat.img}
                alt={cat.name}
                loading="lazy"
                onError={(e) => {
                  e.currentTarget.onerror = null;
                  e.currentTarget.src = './placeholder.svg';
                }}
              />
              <div className="aa-overlay">
                <strong className="aa-count">{cat.count}</strong>
                <span className="aa-name">{cat.name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

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
                className="btn btn-outline-navy btn-lg"
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
                  <span className="hfc-label">
                    <span className="live-pulse-dot" aria-hidden="true"></span> Next E-Auction Ends In
                  </span>
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

      {/* EXPLORE BY CITY */}
      <ExploreByCitySection onNavigate={onNavigate} />

      {/* EXPLORE ASSETS BY CATEGORY */}
      <ExploreAssetsByCategorySection
        properties={properties}
        onViewProperty={onViewProperty}
        onNavigate={onNavigate}
      />

      {/* ASSETS AVAILABLE */}
      <AssetsAvailableSection onNavigate={onNavigate} />

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
