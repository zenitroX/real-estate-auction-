import React, { useState, useMemo } from 'react';
import { SlidersHorizontal, RotateCcw, Search, House, X } from 'lucide-react';
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
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);

  // Available banks
  const availableBanks = ['Canara Bank', 'SBI', 'ICICI Bank', 'Others'];

  // Calculate dynamic counts from real properties inventory
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
    const counts = { 'Canara Bank': 0, SBI: 0, 'ICICI Bank': 0, Others: 0 };
    (properties || []).forEach((p) => {
      const b = p.bank || '';
      if (b.includes('Canara')) counts['Canara Bank'] += 1;
      else if (b.includes('State Bank') || b.includes('SBI')) counts['SBI'] += 1;
      else if (b.includes('ICICI')) counts['ICICI Bank'] += 1;
      else counts['Others'] += 1;
    });
    return counts;
  }, [properties]);

  // Filter and sort verified published properties for public customers
  const filteredProperties = useMemo(() => {
    // Only verified listings are served to public customers
    let result = properties.filter((p) => p.verified && p.status === 'PUBLISHED');

    // Location query
    if (filters.location && filters.location.trim()) {
      const q = filters.location.toLowerCase().trim();
      result = result.filter(
        (p) =>
          (p.locality || '').toLowerCase().includes(q) ||
          (p.address || '').toLowerCase().includes(q) ||
          (p.title || '').toLowerCase().includes(q) ||
          (p.bank || '').toLowerCase().includes(q)
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
          return !['Canara Bank', 'SBI', 'ICICI Bank'].includes(p.bank);
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
      maxBudget: 100000000, // 10 Cr
      banks: ['Canara Bank', 'SBI', 'ICICI Bank', 'Others'],
      sort: 'ending',
    });
  };

  return (
    <div className="properties-view">
      {/* Page Title */}
      <div className="page-head">
        <div className="container">
          <h1>
            Auction <span className="gold">Properties</span>
          </h1>
          <p>Explore bank auction and e-auction properties across India.</p>
        </div>
      </div>

      <div className="container listing-layout">
        {/* Left Filter Sidebar */}
        <aside className={`filters-sidebar ${mobileFilterOpen ? 'mobile-open' : ''}`}>
          <div className="filters-head">
            <strong>
              <SlidersHorizontal size={18} /> Filter Properties
            </strong>
            <button onClick={handleResetFilters} title="Reset all filters">
              Reset
            </button>
            {mobileFilterOpen && (
              <button
                className="icon-btn"
                style={{ marginLeft: 'auto' }}
                onClick={() => setMobileFilterOpen(false)}
              >
                <X size={20} />
              </button>
            )}
          </div>

          {/* Location search */}
          <div className="filter-group">
            <label className="fg-title">Location</label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Search location..."
                value={filters.location}
                onChange={(e) => setFilters({ ...filters, location: e.target.value })}
              />
              <Search
                size={16}
                color="#94A3B8"
                style={{ position: 'absolute', right: 12, top: 12, pointerEvents: 'none' }}
              />
            </div>
          </div>

          {/* Property Types */}
          <div className="filter-group">
            <span className="fg-title">Property Type</span>
            {[
              { id: 'residential', label: 'Residential', count: typeCounts.residential },
              { id: 'commercial', label: 'Commercial', count: typeCounts.commercial },
              { id: 'land', label: 'Land / Plot', count: typeCounts.land },
              { id: 'industrial', label: 'Industrial', count: typeCounts.industrial },
            ].map((item) => (
              <label key={item.id} className="check">
                <span className="check-label">
                  <input
                    type="checkbox"
                    checked={filters.types.includes(item.id)}
                    onChange={() => handleToggleType(item.id)}
                  />
                  <span>{item.label}</span>
                </span>
                <span className="count-pill">({item.count})</span>
              </label>
            ))}
          </div>

          {/* Budget Range */}
          <div className="filter-group">
            <span className="fg-title">Budget Range</span>
            <div className="range-wrap">
              <input
                type="range"
                min="1000000"
                max="100000000"
                step="2500000"
                value={filters.maxBudget}
                onChange={(e) => setFilters({ ...filters, minBudget: 0, maxBudget: Number(e.target.value) })}
              />
              <div className="range-vals">
                <span>₹ 10 Lakh</span>
                <strong>
                  {filters.minBudget > 0
                    ? `Above ${formatPriceShort(filters.minBudget)}`
                    : (filters.maxBudget >= 100000000 ? '₹ 10 Crore+' : `Up to ${formatPriceShort(filters.maxBudget)}`)}
                </strong>
              </div>
            </div>
          </div>

          {/* Banks */}
          <div className="filter-group">
            <span className="fg-title">Bank</span>
            {availableBanks.map((bank) => (
              <label key={bank} className="check">
                <span className="check-label">
                  <input
                    type="checkbox"
                    checked={filters.banks.includes(bank)}
                    onChange={() => handleToggleBank(bank)}
                  />
                  <span>{bank}</span>
                </span>
                <span className="count-pill">({bankCounts[bank] || 45})</span>
              </label>
            ))}
          </div>

          <button className="btn btn-outline btn-block" onClick={handleResetFilters}>
            <RotateCcw size={16} /> Reset Filters
          </button>
        </aside>

        {/* Main Content Area */}
        <div className="listing-main">
          {/* Toolbar */}
          <div className="listing-toolbar">
            <span>
              Showing 1 – {filteredProperties.length} of 549 Properties
            </span>

            <div className="toolbar-right">
              <button
                className="btn btn-outline btn-sm filter-toggle-btn"
                onClick={() => setMobileFilterOpen(true)}
              >
                <SlidersHorizontal size={15} /> Filters
              </button>

              <select
                className="sort-select"
                value={filters.sort}
                onChange={(e) => setFilters({ ...filters, sort: e.target.value })}
                aria-label="Sort listings"
              >
                <option value="ending">Sort by: Ending Soon</option>
                <option value="featured">Sort by: Featured</option>
                <option value="price-asc">Price: Low &rarr; High</option>
                <option value="price-desc">Price: High &rarr; Low</option>
              </select>
            </div>
          </div>

          {/* Grid */}
          {filteredProperties.length > 0 ? (
            <div className="prop-grid">
              {filteredProperties.map((p) => (
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
          ) : (
            <div className="empty-state">
              <div className="empty-icon">
                <House size={32} />
              </div>
              <h3>No properties found matching your criteria</h3>
              <p>
                Try widening your location query, selecting additional property types, or increasing the maximum budget slider.
              </p>
              <button className="btn btn-gold" onClick={handleResetFilters}>
                <RotateCcw size={16} /> Reset All Filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
