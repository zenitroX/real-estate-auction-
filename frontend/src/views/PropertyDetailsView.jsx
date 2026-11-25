import React, { useState, useEffect } from 'react';
import {
  ChevronRight,
  ChevronLeft,
  Share2,
  Heart,
  MapPin,
  Ruler,
  Maximize2,
  Building,
  Clock,
  PhoneCall,
  MessageSquare,
  FileDown,
  FolderOpen,
  Calendar,
  CheckCircle2,
  Building2,
  ShieldCheck,
  Headset,
  Info,
} from 'lucide-react';
import PropertyCard from '../components/PropertyCard';
import {
  formatPrice,
  formatRupees,
  formatPriceShort,
  formatSqft,
  typeLabel,
  timeRemaining,
  pad2,
} from '../data/propertiesData';

export default function PropertyDetailsView({
  property,
  allProperties,
  onNavigate,
  onViewProperty,
  onContact,
  wishlist,
  onToggleWishlist,
  onOpenShare,
  onOpenSiteVisit,
  onDownloadBrochure,
  onViewDocuments,
}) {
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  // Live countdown timer state
  const [countdown, setCountdown] = useState(() =>
    timeRemaining(property?.auctionEnd || Date.now() + 86400000)
  );

  useEffect(() => {
    if (!property?.id) return;
    setActiveImageIndex(0);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    const pageTitle = `${property.title} — Bank Auction in ${property.locality || 'Tamil Nadu'} | SKANDX`;
    document.title = pageTitle;

    const descText = `${property.bank || 'Bank'} auction property in ${property.locality || 'Tamil Nadu'}. Reserve price: ${property.reserve ? formatPriceShort(property.reserve) : 'Not available'}.`;
    let metaDesc = document.querySelector('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement('meta');
      metaDesc.setAttribute('name', 'description');
      document.head.appendChild(metaDesc);
    }
    metaDesc.setAttribute('content', descText);

    const canonicalUrl = `${window.location.origin}/properties/${encodeURIComponent(property.slug || property.id)}`;
    let canonicalLink = document.querySelector('link[rel="canonical"]');
    if (!canonicalLink) {
      canonicalLink = document.createElement('link');
      canonicalLink.setAttribute('rel', 'canonical');
      document.head.appendChild(canonicalLink);
    }
    canonicalLink.setAttribute('href', canonicalUrl);

    let ldScript = document.getElementById('skandx-property-jsonld');
    if (!ldScript) {
      ldScript = document.createElement('script');
      ldScript.id = 'skandx-property-jsonld';
      ldScript.type = 'application/ld+json';
      document.head.appendChild(ldScript);
    }
    ldScript.textContent = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'RealEstateListing',
      name: property.title,
      description: descText,
      url: canonicalUrl,
      ...(property.reserve ? { offers: { '@type': 'Offer', price: property.reserve, priceCurrency: 'INR' } } : {}),
    });
  }, [property]);

  useEffect(() => {
    if (!property?.auctionEnd) return;
    const timer = setInterval(() => {
      setCountdown(timeRemaining(property.auctionEnd));
    }, 1000);
    return () => clearInterval(timer);
  }, [property?.auctionEnd]);

  const isWishlisted = wishlist.includes(property.id);
  const images = property.images && property.images.length > 0 ? property.images : ['./placeholder.svg'];

  const prevImage = () => {
    setActiveImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const nextImage = () => {
    setActiveImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  // Only suggest verified published properties as similar
  const similarProperties = allProperties
    .filter((p) => p.id !== property.id && p.verified && (p.type === property.type || p.bank === property.bank))
    .slice(0, 3);

  const isBankAuction = (property.badge || '').toUpperCase().includes('BANK');
  const whatsappMsg = encodeURIComponent(
    `Hello SKANDX! I am interested in verified bank property: ${property.title} in ${property.locality} (Reserve: ${formatPriceShort(property.reserve)}). Please assist me with legal inspection.`
  );

  return (
    <div className="property-details-view">
      <div className="container">
        {/* Breadcrumb */}
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <a href="#home" onClick={(e) => { e.preventDefault(); onNavigate('home'); }}>
            Home
          </a>
          <ChevronRight size={14} />
          <a href="#properties" onClick={(e) => { e.preventDefault(); onNavigate('properties'); }}>
            Auction Properties
          </a>
          <ChevronRight size={14} />
          <span>{property.title}</span>
        </nav>

        {/* Gallery + Info Header Grid */}
        <div className="detail-layout">
          {/* Left: Interactive Gallery */}
          <div className="detail-gallery">
            <div className="gallery-main">
              <img
                src={images[activeImageIndex]}
                alt={`${property.title} view ${activeImageIndex + 1}`}
                onError={(e) => {
                  e.currentTarget.onerror = null;
                  e.currentTarget.src = './placeholder.svg';
                }}
              />

              <button className="gal-nav gal-prev" onClick={prevImage} aria-label="Previous photo">
                <ChevronLeft size={22} />
              </button>
              <button className="gal-nav gal-next" onClick={nextImage} aria-label="Next photo">
                <ChevronRight size={22} />
              </button>

              <span className={`badge ${isBankAuction ? 'badge-gold' : 'badge-blue'} gal-badge`}>
                {property.badge || 'BANK AUCTION'}
              </span>

              {/* Verified seal overlay */}
              {property.verified && (
                <span
                  className="badge badge-green"
                  style={{
                    position: 'absolute',
                    top: 16,
                    left: 140,
                    zIndex: 2,
                    background: 'rgba(240, 253, 244, 0.95)',
                    borderColor: '#86EFAC',
                    color: '#166534',
                    fontWeight: 800,
                  }}
                >
                  <ShieldCheck size={14} /> Admin Verified
                </span>
              )}

              <div className="gal-actions">
                <button
                  className={`wish-btn ${isWishlisted ? 'active' : ''}`}
                  onClick={() => onToggleWishlist(property.id)}
                  aria-label="Wishlist"
                >
                  <Heart size={16} fill={isWishlisted ? '#DC2626' : 'none'} color={isWishlisted ? '#DC2626' : '#071D35'} />
                </button>
                <button
                  className="icon-btn"
                  style={{ background: 'rgba(255,255,255,0.92)', color: '#071D35' }}
                  onClick={() => onOpenShare(property)}
                  aria-label="Share listing"
                >
                  <Share2 size={16} />
                </button>
              </div>

              <div className="gal-counter">
                {activeImageIndex + 1} / {images.length}
              </div>
            </div>

            {/* Thumbnail Strip */}
            <div className="gallery-thumbs">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  className={idx === activeImageIndex ? 'active' : ''}
                  onClick={() => setActiveImageIndex(idx)}
                >
                  <img src={img} alt="" />
                </button>
              ))}
            </div>
          </div>

          {/* Right: Property Details & Contact Box */}
          <div className="detail-info">
            <div className="detail-title-row">
              <div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                  <span className={`badge ${isBankAuction ? 'badge-gold' : 'badge-blue'}`}>
                    {property.badge || 'BANK AUCTION'}
                  </span>
                  {property.verified && (
                    <span className="badge badge-green">
                      <ShieldCheck size={13} /> Verified Asset
                    </span>
                  )}
                </div>
                <h1>{property.title}</h1>
              </div>
            </div>

            <p className="detail-loc">
              <MapPin size={18} />
              <span>{property.address || property.locality}</span>
            </p>

            {/* Specs Grid */}
            <div className="spec-grid">
              <div className="spec">
                <Ruler size={22} />
                <div>
                  <small>Built-up Area</small>
                  <strong>{formatSqft(property.area)}</strong>
                </div>
              </div>

              <div className="spec">
                <Maximize2 size={22} />
                <div>
                  <small>Land Area</small>
                  <strong>{formatSqft(property.landArea)}</strong>
                </div>
              </div>

              <div className="spec">
                <Building size={22} />
                <div>
                  <small>Property Type</small>
                  <strong>{typeLabel(property.type)}</strong>
                </div>
              </div>
            </div>

            {/* Pricing & Contact Box */}
            <div className="pricing-card">
              <div className="pc-row">
                <div>
                  <small>Reserve Price</small>
                  <strong>{formatPrice(property.reserve)}</strong>
                </div>
                <div>
                  <small>EMD (10%)</small>
                  <strong>{formatPrice(property.emd)}</strong>
                </div>
                <div>
                  <small>Incremental Bid</small>
                  <strong>{formatRupees(property.increment)}</strong>
                </div>
              </div>

              <div className="pc-divider"></div>

              <small className="pc-label">
                <Clock size={15} /> E-Auction Closes In
              </small>

              {/* 4 Box Digits Countdown */}
              <div className="countdown">
                <div className="cd-unit">
                  <strong>{countdown.d}</strong>
                  <span>Days</span>
                </div>
                <div className="cd-unit">
                  <strong>{pad2(countdown.h)}</strong>
                  <span>Hours</span>
                </div>
                <div className="cd-unit">
                  <strong>{pad2(countdown.m)}</strong>
                  <span>Minutes</span>
                </div>
                <div className="cd-unit">
                  <strong>{pad2(countdown.s)}</strong>
                  <span>Seconds</span>
                </div>
              </div>

              {/* Primary Contact CTA */}
              <button
                className="btn btn-gold btn-lg btn-block"
                onClick={() => onContact(property)}
              >
                <PhoneCall size={18} /> Connect with Auction Advisor
              </button>

              {/* Instant Channel Options */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <a
                  href="tel:18002027526"
                  className="btn btn-outline btn-sm"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                >
                  <PhoneCall size={14} color="#D9A62E" /> 1800 - 202 - SKANDX
                </a>

                <a
                  href={`https://api.whatsapp.com/send?phone=919176011223&text=${whatsappMsg}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-outline btn-sm"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, color: '#166534', borderColor: '#86EFAC', background: '#F0FDF4' }}
                >
                  <MessageSquare size={14} color="#16A34A" /> WhatsApp Chat
                </a>
              </div>

              <p className="demo-note">
                <Info size={14} /> Free to browse. Substantive buyer assistance carries a proposed 5% success fee upon acquisition.
              </p>
            </div>
          </div>
        </div>

        {/* Highlights & Bank Details Grid */}
        <div className="detail-below">
          {/* 8-Dimension Progressive Verification & Risk Disclosures */}
          <div className="detail-card">
            <h3>
              <CheckCircle2 size={20} color="#E8B849" /> Verification Status & Risk Disclosures
            </h3>
            <p style={{ fontSize: '0.82rem', color: '#64748B', marginBottom: 12 }}>
              Admin-approved for publication. Individual checks below show what has and has not been verified; this is not legal title certification.
            </p>
            <div style={{ display: 'grid', gap: 8, marginBottom: 16 }}>
              {[
                ['source_checked', 'Original Auction Source Checked'],
                ['auction_details_checked', 'Core Auction Details Checked'],
                ['documents_reviewed', 'Auction Documents Reviewed'],
                ['ec_reviewed', 'Encumbrance Certificate (EC) Reviewed'],
                ['revenue_records_reviewed', 'Revenue Records (Patta/Chitta) Reviewed'],
                ['physical_inspection_completed', 'Physical Site Inspection'],
                ['possession_assessed', 'Possession Status Assessed'],
                ['legal_review_completed', 'Legal Title Review'],
              ].map(([key, label]) => {
                const dim = (property.verificationDimensions || {})[key] || {};
                const status = dim.status || 'PENDING';
                const badgeColor =
                  status === 'COMPLETED'
                    ? '#166534'
                    : status === 'FLAGGED'
                      ? '#991B1B'
                      : '#92400E';
                const badgeBg =
                  status === 'COMPLETED'
                    ? '#DCFCE7'
                    : status === 'FLAGGED'
                      ? '#FEE2E2'
                      : '#FEF3C7';
                return (
                  <div
                    key={key}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 10px',
                      borderRadius: 8,
                      background: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                      fontSize: '0.84rem',
                    }}
                  >
                    <span>
                      {label}
                      {dim.review_period ? ` (${dim.review_period})` : ''}
                    </span>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: 999,
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: badgeColor,
                        background: badgeBg,
                      }}
                    >
                      {status}
                    </span>
                  </div>
                );
              })}
            </div>

            <div style={{ padding: '10px 12px', borderRadius: 8, background: '#FFFBEB', border: '1px solid #FDE68A', fontSize: '0.82rem', color: '#92400E' }}>
              <strong>Disclosed Risks:</strong>{' '}
              {(property.riskDisclosures && property.riskDisclosures.length > 0
                ? property.riskDisclosures
                : [
                    `Possession: ${property.possessionType || 'Not yet confirmed'}`,
                    'Physical inspection & independent legal review should be completed before bidding.',
                  ]
              ).join(' · ')}
            </div>
          </div>

          {/* Bank Details Card (With Masked Officer Personal Contact) */}
          <div className="detail-card">
            <h3>
              <Building2 size={20} color="#E8B849" /> Authorizing Bank Information
            </h3>
            <table className="bank-table">
              <tbody>
                <tr>
                  <td>Authorizing Bank</td>
                  <td>{property.bank}</td>
                </tr>
                <tr>
                  <td>Asset Code</td>
                  <td>{property.assetCode}</td>
                </tr>
                <tr>
                  <td>Recovery Branch</td>
                  <td>{property.branch || 'Asset Recovery Management Branch'}</td>
                </tr>
                <tr>
                  <td>Dedicated Hotline</td>
                  <td>
                    <strong style={{ color: '#071D35' }}>1800 - 202 - SKANDX</strong> (Toll-Free)
                  </td>
                </tr>
                <tr>
                  <td>Nodal Liaison Officer</td>
                  <td style={{ color: '#16A34A', fontWeight: 600 }}>
                    Assigned upon inquiry verification
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="detail-actions">
          <button
            className="btn btn-outline"
            onClick={() => onContact ? onContact(property, 'Download Notice') : onDownloadBrochure(property)}
          >
            <FileDown size={17} /> Download Official Notice
          </button>
          <button
            className="btn btn-outline"
            onClick={() => onContact ? onContact(property, 'Legal Title Search Report') : onViewDocuments(property)}
          >
            <FolderOpen size={17} /> Request Title Search Pack
          </button>
          <button
            className="btn btn-outline"
            onClick={() => onContact ? onContact(property, 'Site Inspection') : onOpenSiteVisit(property)}
          >
            <Calendar size={17} /> Schedule Physical Site Inspection
          </button>
        </div>

        {/* Detailed Description */}
        <div className="detail-desc">
          <h3>
            <Building size={20} color="#E8B849" /> Statutory Asset Description
          </h3>
          <p>{property.desc}</p>
        </div>

        {/* Similar Verified Auctions */}
        {similarProperties.length > 0 && (
          <section className="section" style={{ paddingTop: 30 }}>
            <div className="section-head">
              <div>
                <h2>
                  Similar Verified <span className="gold">Auctions</span>
                </h2>
                <p>Other verified bank auctions currently matching this property class.</p>
              </div>
              <button className="btn btn-outline btn-sm" onClick={() => onNavigate('properties')}>
                Browse All Properties
              </button>
            </div>

            <div className="prop-grid">
              {similarProperties.map((p) => (
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
          </section>
        )}
      </div>
    </div>
  );
}
