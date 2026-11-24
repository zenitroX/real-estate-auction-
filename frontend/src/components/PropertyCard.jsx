import React from 'react';
import { MapPin, Heart, PhoneCall, Eye, ExternalLink, Building2, Grid2X2, CalendarClock, CalendarCheck, ShieldCheck, Share2 } from 'lucide-react';
import { formatPriceShort, timeRemaining, typeLabel } from '../data/propertiesData';

function fmtAuctionDate(ts) {
  if (!ts) return 'NA';
  const d = new Date(ts);
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const yyyy = d.getFullYear();
  const hh = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${dd}-${mm}-${yyyy} ${hh}:${min}`;
}

export default function PropertyCard({ property, onView, onContact, isWishlisted, onToggleWishlist }) {
  const handleContactAction = onContact || (() => {});
  const tr = timeRemaining(property.auctionEnd);
  const isEnded = tr.total === 0;
  const isBankAuction = (property.badge || '').toUpperCase().includes('BANK');

  const areaLabel = property.area ? `${Number(property.area).toLocaleString('en-IN')} sq feet` : 'NA';
  const possessionType = property.possessionType || 'Physical';
  const legalAction = property.legalAction || 'Under SARFAESI';
  const projectName = property.projectName || 'NA';

  const emdEnd = property.auctionEnd ? property.auctionEnd - 10 * 60 * 1000 : null;
  const inspectionStart = property.auctionEnd ? property.auctionEnd - 15 * 24 * 60 * 60 * 1000 : null;
  const inspectionEnd = property.auctionEnd ? property.auctionEnd - 1 * 24 * 60 * 60 * 1000 : null;

  const badgeClass = isEnded ? 'ended' : (isBankAuction ? 'upcoming' : 'live');
  const badgeLabel = isEnded ? 'Closed' : (isBankAuction ? 'Upcoming Auction' : 'Live E-Auction');

  return (
    <article className="bnc-card" aria-label={property.title}>

      {/* ROW 1: Full-width title + icons */}
      <div className="bnc-title-row">
        <div className="bnc-title-left">
          <h3 className="bnc-title" onClick={() => onView(property.id)}>{property.title}</h3>
          {property.assetCode && (
            <span className="bnc-asset-code">Property ID: {property.assetCode}</span>
          )}
        </div>
        <div className="bnc-title-actions">
          <button
            className="bnc-icon-btn"
            onClick={(e) => { e.stopPropagation(); onToggleWishlist(property.id); }}
            aria-label={isWishlisted ? 'Remove from saved' : 'Save property'}
          >
            <Heart size={18} fill={isWishlisted ? '#E8B849' : 'none'} color={isWishlisted ? '#E8B849' : '#94A3B8'} />
          </button>
          <button className="bnc-icon-btn" aria-label="Share property">
            <Share2 size={16} color="#94A3B8" />
          </button>
        </div>
      </div>

      {/* ROW 2: Image (left) + Info grid (right) */}
      <div className="bnc-middle-row">
        {/* Image thumbnail */}
        <div className="bnc-media" onClick={() => onView(property.id)}>
          <img
            src={property.images[0]}
            alt={property.title}
            loading="lazy"
            onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = './placeholder.svg'; }}
          />
          <span className={`bnc-status-badge ${badgeClass}`}>{badgeLabel}</span>
          {property.verified && (
            <span className="bnc-verified-badge">
              <ShieldCheck size={11} /> Govt Verified
            </span>
          )}
        </div>

        {/* Info grid */}
        <div className="bnc-info-grid">
          <div className="bnc-info-item">
            <span className="bnc-info-label"><Grid2X2 size={12} /> Carpet Area</span>
            <strong>{areaLabel}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><Grid2X2 size={12} /> Built Up Area</span>
            <strong>{property.builtUpArea ? `${property.builtUpArea} sq feet` : 'NA'}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><Building2 size={12} /> Project Name</span>
            <strong title={projectName}>{projectName}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><Grid2X2 size={12} /> Furnished Status</span>
            <strong>NA</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><ShieldCheck size={12} /> Possession Type</span>
            <strong className="bnc-highlight-val">{possessionType}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><ShieldCheck size={12} /> Type of Action</span>
            <strong className="bnc-highlight-val">{legalAction}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><CalendarClock size={12} /> Auction Start Date &amp; Time</span>
            <strong>{property.auctionEnd ? fmtAuctionDate(property.auctionEnd - 4 * 60 * 60 * 1000) : 'NA'}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><CalendarCheck size={12} /> Auction End Date &amp; Time</span>
            <strong>{fmtAuctionDate(property.auctionEnd)}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><CalendarCheck size={12} /> EMD End Date &amp; Time</span>
            <strong>{emdEnd ? fmtAuctionDate(emdEnd) : 'NA'}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><CalendarClock size={12} /> Inspection Start Date &amp; Time</span>
            <strong>{inspectionStart ? fmtAuctionDate(inspectionStart) : 'NA'}</strong>
          </div>
          <div className="bnc-info-item">
            <span className="bnc-info-label"><CalendarCheck size={12} /> Inspection End Date &amp; Time</span>
            <strong>{inspectionEnd ? fmtAuctionDate(inspectionEnd) : 'NA'}</strong>
          </div>
        </div>
      </div>

      {/* ROW 3: Reserve price + action buttons — full width, below image */}
      <div className="bnc-footer-row">
        <div className="bnc-reserve-block">
          <span className="bnc-reserve-label">Reserve price</span>
          <strong className="bnc-reserve-price">{formatPriceShort(property.reserve)}</strong>
        </div>
        <div className="bnc-action-btns">
          <button
            className="bnc-btn bnc-btn-contact"
            onClick={(e) => { e.stopPropagation(); handleContactAction(property); }}
          >
            <PhoneCall size={13} /> Contact Us
          </button>
          <button
            className="bnc-btn bnc-btn-details"
            onClick={(e) => { e.stopPropagation(); onView(property.id); }}
          >
            <Eye size={13} /> View Details
          </button>
          <button
            className="bnc-btn bnc-btn-auction"
            onClick={(e) => { e.stopPropagation(); onView(property.id); }}
          >
            <ExternalLink size={13} /> View Auction
          </button>
        </div>
      </div>

      {/* ROW 4: Meta strip — Type | Bank | Location */}
      <div className="bnc-meta-strip">
        <span className="bnc-meta-cell">
          <Grid2X2 size={12} /> {typeLabel(property.type)}{property.beds ? `, ${property.beds} BHK` : ''}
        </span>
        <span className="bnc-meta-cell">
          <Building2 size={12} /> {property.bank}
        </span>
        <span className="bnc-meta-cell">
          <MapPin size={12} /> {property.locality}
        </span>
      </div>
    </article>
  );
}
