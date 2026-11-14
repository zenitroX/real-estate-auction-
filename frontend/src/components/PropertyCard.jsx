import React from 'react';
import { MapPin, Clock, Heart, PhoneCall, ShieldCheck } from 'lucide-react';
import { formatPriceShort, timeRemaining, typeLabel, pad2 } from '../data/propertiesData';

export default function PropertyCard({
  property,
  onView,
  onContact,
  onBid,
  isWishlisted,
  onToggleWishlist,
}) {
  const handleContactAction = onContact || onBid || (() => {});
  const tr = timeRemaining(property.auctionEnd);
  const isEnded = tr.total === 0;

  const countdownText = isEnded
    ? 'Auction Closed'
    : `Ends in ${tr.d}d ${pad2(tr.h)}h ${pad2(tr.m)}m`;

  const isBankAuction = (property.badge || '').toUpperCase().includes('BANK');

  return (
    <div className="prop-card">
      <div className="pc-media" onClick={() => onView(property.id)}>
        <img
          src={property.images[0]}
          alt={property.title}
          loading="lazy"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = './placeholder.svg';
          }}
        />

        {/* Bank / Auction Badge */}
        <span className={`badge ${isBankAuction ? 'badge-gold' : 'badge-blue'}`}>
          {property.badge || 'BANK AUCTION'}
        </span>

        {/* Admin Verified Tag */}
        {property.verified && (
          <span
            className="badge badge-green"
            style={{
              position: 'absolute',
              right: 54,
              top: 12,
              zIndex: 2,
              background: 'rgba(240, 253, 244, 0.95)',
              borderColor: '#86EFAC',
              color: '#166534',
              fontWeight: 800,
              boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
            }}
          >
            <ShieldCheck size={13} /> Verified
          </span>
        )}

        {/* Property Type */}
        <span className="type-tag">{typeLabel(property.type)}</span>

        {/* Wishlist toggle */}
        <button
          className={`wish-btn ${isWishlisted ? 'active' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onToggleWishlist(property.id);
          }}
          aria-label={isWishlisted ? 'Remove from saved' : 'Save property'}
          title={isWishlisted ? 'Remove from saved' : 'Save property'}
        >
          <Heart size={16} fill={isWishlisted ? '#DC2626' : 'none'} color={isWishlisted ? '#DC2626' : '#071D35'} />
        </button>
      </div>

      <div className="pc-body">
        <h3 onClick={() => onView(property.id)} title={property.title}>
          {property.title}
        </h3>

        <div className="pc-loc">
          <MapPin size={14} />
          <span>{property.locality}</span>
        </div>

        <div className="pc-count">
          <Clock size={14} />
          <span>{countdownText}</span>
        </div>

        <div className="pc-footer">
          <div className="pc-price">
            <small>Reserve Price</small>
            <strong>{formatPriceShort(property.reserve)}</strong>
          </div>

          <button
            className="btn btn-gold btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              handleContactAction(property);
            }}
          >
            <PhoneCall size={14} />
            Contact
          </button>
        </div>
      </div>
    </div>
  );
}
