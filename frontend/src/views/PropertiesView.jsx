import React, { useState, useMemo } from 'react';
import {
  SlidersHorizontal,
  RotateCcw,
  Search,
  House,
  X,
  MapPin,
  Building2,
  Check,
  ChevronDown,
} from 'lucide-react';
import PropertyCard from '../components/PropertyCard';
import { formatPriceShort } from '../data/propertiesData';

export default function PropertiesView({
  properties,
  onViewProperty,
  onContact,
  wishlist,
  onToggleWishlist,
  filters,
  setFilters,
}) {
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [activeAssetCategory, setActiveAssetCategory] = useState('property'); // 'property' or 'movable'
  const [possessionFilter, setPossessionFilter] = useState('all'); // 'all', 'physical', 'symbolic'
  const [frameworkFilter, setFrameworkFilter] = useState('all'); // 'all', 'sarfaesi', 'drt'

  // Available banks
  const availableBanks = ['Canara Bank', 'SBI', 'ICICI Bank', 'Indian Bank', 'Others'];

  // States list for quick Baanknet filtering
  const indianStates = [
    { id: 'all', label: 'All States' },
    { id: 'tn', label: 'Tamil Nadu (Chennai)' },
    { id: 'ka', label: 'Karnataka (Bengaluru)' },
    { id: 'ts', label: 'Telangana (Hyderabad)' },
    { id: 'dl', label: 'Delhi NCR' },
    { id: 'mh', label: 'Maharashtra (Mumbai)' },
  ];

  // Dynamic counts from current verified inventory
  const typeCounts = useMemo(() => {
    const counts = { residential: 0, commercial: 0, land: 0, industrial: 0 };
    (properties || []).forEach((p) => {
      const t = (p.type || '').toLowerCase();
      if (counts[t] !== undefined) {
        counts[t] += 1;
      }
    });
    return counts;
  }, [properties]);

  const bankCounts = useMemo(() => {
    const counts = { 'Canara Bank': 0, SBI: 0, 'ICICI Bank': 0, 'Indian Bank': 0, Others: 0 };
    (properties || []).forEach((p) => {
      const b = p.bank || '';
      if (b.includes('Canara')) counts['Canara Bank'] += 1;
      else if (b.includes('State Bank') || b.includes('SBI')) counts['SBI'] += 1;
      else if (b.includes('ICICI')) counts['ICICI Bank'] += 1;
      else if (b.includes('Indian Bank')) counts['Indian Bank'] += 1;
      else counts['Others'] += 1;
    });
    return counts;
  }, [properties]);

  // Filter and sort verified published properties for public customers
  const filteredProperties = useMemo(() => {
    let result = properties.filter((p) => p.verified && p.status === 'PUBLISHED');

    // Location query
    if (filters.location && filters.location.trim()) {
      const q = filters.location.toLowerCase().trim();
      result = result.filter(
        (p) =>
          (p.locality || '').toLowerCase().includes(q) ||
          (p.address || '').toLowerCase().includes(q) ||
          (p.title || '').toLowerCase().includes(q) ||
          (p.bank || '').toLowerCase().includes(q) ||
          (p.assetCode || '').toLowerCase().includes(q)
      );
    }

    // Property Types
    if (filters.types.length > 0) {
      result = result.filter((p) => filters.types.includes(p.type));
    }

    // Budget range
    if (filters.minBudget) {
      result = result.filter((p) => p.reserve >= filters.minBudget);
    }
    if (filters.maxBudget) {
      result = result.filter((p) => p.reserve <= filters.maxBudget);
    }

    // Bank filter
    if (filters.banks.length > 0) {
      result = result.filter((p) => {
        if (filters.banks.includes(p.bank)) return true;
        if (filters.banks.includes('Others')) {
          return !['Canara Bank', 'SBI', 'ICICI Bank', 'Indian Bank'].includes(p.bank);
        }
        return false;
      });
    }

    // Sorting
    if (filters.sort === 'ending') {
      result.sort((a, b) => a.auctionEnd - b.auctionEnd);
    } else if (filters.sort === 'price-asc') {
      result.sort((a, b) => a.reserve - b.reserve);
    } else if (filters.sort === 'price-desc') {
      result.sort((a, b) => b.reserve - a.reserve);
    } else {
      // featured
      result.sort((a, b) => (b.featured ? 1 : 0) - (a.featured ? 1 : 0));
    }

    return result;
  }, [properties, filters]);

  // Count active filter constraints
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.location) count += 1;
    if (filters.types.length < 4) count += filters.types.length;
    if (filters.banks.length < availableBanks.length) count += filters.banks.length;
    if (filters.minBudget > 0 || filters.maxBudget < 100000000) count += 1;
    if (possessionFilter !== 'all') count += 1;
    if (frameworkFilter !== 'all') count += 1;
    return count;
  }, [filters, possessionFilter, frameworkFilter, availableBanks.length]);

  const handleToggleType = (type) => {
    setFilters((prev) => {
      const exists = prev.types.includes(type);
      return {
        ...prev,
        types: exists ? prev.types.filter((t) => t !== type) : [...prev.types, type],
      };
    });
  };

  const handleToggleBank = (bank) => {
    setFilters((prev) => {
      const exists = prev.banks.includes(bank);
      return {
        ...prev,
        banks: exists ? prev.banks.filter((b) => b !== bank) : [...prev.banks, bank],
      };
    });
  };

  const handleResetFilters = () => {
    setFilters({
      location: '',
      types: ['residential', 'commercial', 'land', 'industrial'],
      minBudget: 0,
      maxBudget: 100000000,
      banks: availableBanks,
      sort: 'ending',
    });
    setPossessionFilter('all');
    setFrameworkFilter('all');
  };

  // Reusable Filter Sections for both Desktop Left Sidebar & Mobile Drawer
  const renderFilterSections = () => (
    <>
      {/* 1. Category Switcher */}
      <div className="bn-filter-section">
        <label className="bn-section-label">Category</label>
        <div className="bn-category-toggle">
          <button
            className={`bn-cat-btn ${activeAssetCategory === 'property' ? 'active' : ''}`}
            onClick={() => setActiveAssetCategory('property')}
          >
            Property
          </button>
          <button
            className={`bn-cat-btn ${activeAssetCategory === 'movable' ? 'active' : ''}`}
            onClick={() => setActiveAssetCategory('movable')}
          >
            Movable Asset
          </button>
        </div>
      </div>

      {/* 2. State & Location */}
      <div className="bn-filter-section">
        <label className="bn-section-label">Location / State</label>
        <div className="bn-input-wrap">
          <MapPin size={16} className="bn-field-icon" />
          <input
            type="text"
            placeholder="Enter City, Locality..."
            value={filters.location}
            onChange={(e) => setFilters({ ...filters, location: e.target.value })}
          />
        </div>

        <div className="bn-chip-group">
          {indianStates.map((st) => (
            <button
              key={st.id}
              className={`bn-chip ${filters.location.toLowerCase().includes(st.label.split(' ')[0].toLowerCase()) ? 'active' : ''}`}
              onClick={() =>
                setFilters({
                  ...filters,
                  location: st.id === 'all' ? '' : st.label.split(' ')[0],
                })
              }
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Property Type Chips */}
      <div className="bn-filter-section">
        <label className="bn-section-label">Property Type</label>
        <div className="bn-chip-group">
          {[
            { id: 'residential', label: 'Residential' },
            { id: 'commercial', label: 'Commercial' },
            { id: 'land', label: 'Land / Plots' },
            { id: 'industrial', label: 'Industrial' },
          ].map((item) => {
            const isChecked = filters.types.includes(item.id);
            return (
              <button
                key={item.id}
                className={`bn-chip ${isChecked ? 'active' : ''}`}
                onClick={() => handleToggleType(item.id)}
              >
                {isChecked && <Check size={14} />} {item.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Reserve Price Budget Range */}
      <div className="bn-filter-section">
        <div className="bn-section-label-row">
          <label className="bn-section-label">Reserve Price Range</label>
          <strong className="bn-range-indicator">
            {filters.minBudget > 0
              ? `Above ${formatPriceShort(filters.minBudget)}`
              : (filters.maxBudget >= 100000000 ? '₹ 10 Crore+' : `Up to ${formatPriceShort(filters.maxBudget)}`)}
          </strong>
        </div>

        <div className="bn-range-slider-wrap">
          <input
            type="range"
            min="1000000"
            max="100000000"
            step="2500000"
            value={filters.maxBudget}
            onChange={(e) =>
              setFilters({ ...filters, minBudget: 0, maxBudget: Number(e.target.value) })
            }
            className="bn-range-slider"
          />
          <div className="bn-range-presets">
            <span onClick={() => setFilters({ ...filters, minBudget: 0, maxBudget: 5000000 })}>
              ₹50 L
            </span>
            <span onClick={() => setFilters({ ...filters, minBudget: 0, maxBudget: 10000000 })}>
              ₹1 Cr
            </span>
            <span onClick={() => setFilters({ ...filters, minBudget: 0, maxBudget: 25000000 })}>
              ₹2.5 Cr
            </span>
            <span onClick={() => setFilters({ ...filters, minBudget: 0, maxBudget: 100000000 })}>
              ₹10 Cr+
            </span>
          </div>
        </div>
      </div>

      {/* 5. Empanelled Banks */}
      <div className="bn-filter-section">
        <label className="bn-section-label">Empanelled Banks</label>
        <div className="bn-chip-group">
          {availableBanks.map((bank) => {
            const isChecked = filters.banks.includes(bank);
            return (
              <button
                key={bank}
                className={`bn-chip ${isChecked ? 'active' : ''}`}
                onClick={() => handleToggleBank(bank)}
              >
                {isChecked && <Check size={14} />} {bank} ({bankCounts[bank] || 0})
              </button>
            );
          })}
        </div>
      </div>

      {/* 6. Possession Type */}
      <div className="bn-filter-section">
        <label className="bn-section-label">Possession Type</label>
        <div className="bn-chip-group">
          {[
            { id: 'all', label: 'All Possessions' },
            { id: 'physical', label: 'Physical Possession' },
            { id: 'symbolic', label: 'Symbolic Possession' },
          ].map((pos) => (
            <button
              key={pos.id}
              className={`bn-chip ${possessionFilter === pos.id ? 'active' : ''}`}
              onClick={() => setPossessionFilter(pos.id)}
            >
              {pos.label}
            </button>
          ))}
        </div>
      </div>

      {/* 7. Legal Action Framework */}
      <div className="bn-filter-section">
        <label className="bn-section-label">Legal Framework</label>
        <div className="bn-chip-group">
          {[
            { id: 'all', label: 'All Statutory' },
            { id: 'sarfaesi', label: 'SARFAESI Act 2002' },
            { id: 'drt', label: 'DRT Recovery Orders' },
          ].map((frm) => (
            <button
              key={frm.id}
              className={`bn-chip ${frameworkFilter === frm.id ? 'active' : ''}`}
              onClick={() => setFrameworkFilter(frm.id)}
            >
              {frm.label}
            </button>
          ))}
        </div>
      </div>
    </>
  );

  return (
    <div className="properties-view bn-theme">
      {/* BAANKNET HEADER BAR */}
      <div className="bn-page-head">
        <div className="container">
          <div className="bn-head-content">
            <div>
              <span className="bn-eyebrow">
                <Building2 size={15} /> Official Bank Asset Auction Network
              </span>
              <h1>
                Bank Auction <span className="gold">Properties</span>
              </h1>
              <p>
                Centralized discovery of SARFAESI bank auctions, NPA properties, and DRT recovery listings across 20+ public & private sector banks.
              </p>
            </div>

            <div className="bn-head-stats">
              <div className="bn-head-stat">
                <strong>{filteredProperties.length}</strong>
                <span>Active Listings</span>
              </div>
              <div className="bn-head-stat">
                <strong>20+</strong>
                <span>Partner Banks</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container bn-main-container">
        {/* QUICK CATEGORY PILLS STRIP */}
        <div className="bn-quick-pills-strip">
          <div className="bn-pills-list">
            <button
              className={`bn-pill ${filters.types.length === 4 ? 'active-navy' : ''}`}
              onClick={() =>
                setFilters((prev) => ({
                  ...prev,
                  types: ['residential', 'commercial', 'land', 'industrial'],
                }))
              }
            >
              All Assets ({properties.length})
            </button>
            {[
              { id: 'residential', label: 'Residential', count: typeCounts.residential },
              { id: 'commercial', label: 'Commercial', count: typeCounts.commercial },
              { id: 'land', label: 'Land / Plots', count: typeCounts.land },
              { id: 'industrial', label: 'Industrial Sheds', count: typeCounts.industrial },
            ].map((cat) => {
              const isOnlyThis = filters.types.length === 1 && filters.types[0] === cat.id;
              return (
                <button
                  key={cat.id}
                  className={`bn-pill ${isOnlyThis ? 'active-gold' : (filters.types.includes(cat.id) && filters.types.length < 4 ? 'active-outline' : '')}`}
                  onClick={() => {
                    setFilters((prev) => ({
                      ...prev,
                      types: isOnlyThis
                        ? ['residential', 'commercial', 'land', 'industrial']
                        : [cat.id],
                    }));
                  }}
                >
                  {cat.label} ({cat.count})
                </button>
              );
            })}
          </div>

          {/* Mobile Filter Button */}
          <button
            className="btn bn-mobile-filter-trigger"
            onClick={() => setFilterDrawerOpen(true)}
          >
            <SlidersHorizontal size={15} />
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <span className="bn-filter-badge">{activeFilterCount}</span>
            )}
          </button>
        </div>

        {/* BAANKNET TWO-COLUMN LAYOUT: LEFT SIDE FILTER, RIGHT SIDE PROPERTIES ONE BY ONE */}
        <div className="bn-split-layout">
          {/* LEFT SIDE: Filter Card (Desktop Persistent Sidebar) */}
          <aside className="bn-filter-sidebar">
            <div className="bn-sidebar-card">
              <div className="bn-sidebar-head">
                <div className="bn-sidebar-title">
                  <SlidersHorizontal size={18} color="var(--gold)" />
                  <h3>Filters</h3>
                </div>
                {activeFilterCount > 0 && (
                  <button className="bn-clear-all-btn" onClick={handleResetFilters}>
                    Clear All ({activeFilterCount})
                  </button>
                )}
              </div>

              <div className="bn-sidebar-body">
                {renderFilterSections()}
              </div>

              {activeFilterCount > 0 && (
                <div className="bn-sidebar-foot">
                  <button className="btn bn-btn-outline w-100" onClick={handleResetFilters}>
                    <RotateCcw size={14} /> Reset Filters
                  </button>
                </div>
              )}
            </div>
          </aside>

          {/* RIGHT SIDE: Properties Feed (Listed One by One) */}
          <main className="bn-listings-main">
            {/* Top Search & Filter Bar */}
            <div className="bn-top-filter-bar">
              {/* Search Input Box */}
              <div className="bn-search-box">
                <Search size={18} className="bn-search-icon" />
                <input
                  type="text"
                  placeholder="Search by Locality, City, or Bank..."
                  value={filters.location}
                  onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                />
                {filters.location && (
                  <button
                    className="bn-clear-search-btn"
                    onClick={() => setFilters({ ...filters, location: '' })}
                    title="Clear query"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>

              {/* Dedicated Bank Filter Dropdown */}
              <div className="bn-bank-select-wrap">
                <Building2 size={16} className="bn-bank-select-icon" />
                <select
                  className="bn-bank-select"
                  value={
                    filters.banks.length === 1
                      ? filters.banks[0]
                      : (filters.banks.length === availableBanks.length ? 'all' : 'custom')
                  }
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === 'all') {
                      setFilters({ ...filters, banks: availableBanks });
                    } else {
                      setFilters({ ...filters, banks: [val] });
                    }
                  }}
                  aria-label="Filter by Empanelled Bank"
                >
                  <option value="all">All Empanelled Banks ({availableBanks.length})</option>
                  {availableBanks.map((b) => (
                    <option key={b} value={b}>
                      {b} ({bankCounts[b] || 0})
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="bn-select-chevron" />
              </div>

              {/* Sort Dropdown */}
              <div className="bn-sort-wrap">
                <select
                  className="bn-sort-select"
                  value={filters.sort}
                  onChange={(e) => setFilters({ ...filters, sort: e.target.value })}
                  aria-label="Sort listings"
                >
                  <option value="ending">Sort: Ending Soon</option>
                  <option value="featured">Sort: Featured First</option>
                  <option value="price-asc">Reserve: Low to High</option>
                  <option value="price-desc">Reserve: High to Low</option>
                </select>
              </div>
            </div>

            {/* Results Header Meta */}
            <div className="bn-results-summary">
              <span>Showing <strong>{filteredProperties.length}</strong> bank auction properties</span>
              {activeFilterCount > 0 && (
                <button className="bn-reset-link" onClick={handleResetFilters}>
                  <RotateCcw size={13} /> Reset Filters
                </button>
              )}
            </div>

            {/* PROPERTIES LISTED ONE BY ONE (Stacked List) */}
            <div className="bn-cards-stack-list">
              {filteredProperties.length > 0 ? (
                filteredProperties.map((p) => (
                  <PropertyCard
                    key={p.id}
                    property={p}
                    onView={onViewProperty}
                    onContact={onContact}
                    isWishlisted={wishlist.includes(p.id)}
                    onToggleWishlist={onToggleWishlist}
                  />
                ))
              ) : (
                <div className="empty-state bn-empty">
                  <div className="empty-icon bn-empty-icon">
                    <House size={34} />
                  </div>
                  <h3>No Bank Properties Match Your Selection</h3>
                  <p>
                    Try widening your location query or adjusting your reserve price filters.
                  </p>
                  <button className="btn bn-btn-solid" onClick={handleResetFilters}>
                    <RotateCcw size={16} /> Reset All Filters
                  </button>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

      {/* MOBILE FILTER DRAWER */}
      {filterDrawerOpen && (
        <div className="bn-drawer-overlay" onClick={() => setFilterDrawerOpen(false)}>
          <div className="bn-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="bn-drawer-head">
              <div className="bn-drawer-title">
                <SlidersHorizontal size={20} color="var(--gold)" />
                <h3>Filters</h3>
              </div>
              <div className="bn-drawer-head-actions">
                <button className="bn-clear-all-btn" onClick={handleResetFilters}>
                  Clear All
                </button>
                <button
                  className="icon-btn bn-close-btn"
                  onClick={() => setFilterDrawerOpen(false)}
                  aria-label="Close filters"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            <div className="bn-drawer-body">
              {renderFilterSections()}
            </div>

            <div className="bn-drawer-foot">
              <button className="btn bn-btn-outline" onClick={handleResetFilters}>
                Clear All
              </button>
              <button
                className="btn bn-btn-solid bn-btn-flex"
                onClick={() => setFilterDrawerOpen(false)}
              >
                Apply Filters ({filteredProperties.length} Results)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
