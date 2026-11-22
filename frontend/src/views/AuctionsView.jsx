import React, { useMemo } from 'react';
import {
  Gavel,
  Clock,
  Building2,
  UserCheck,
  IndianRupee,
  KeyRound,
  ArrowRight,
} from 'lucide-react';
import PropertyCard from '../components/PropertyCard';

export default function AuctionsView({
  properties,
  onNavigate,
  onViewProperty,
  onContact,
  wishlist,
  onToggleWishlist,
}) {
  // Sort verified properties strictly by time remaining
  const sortedLiveAuctions = useMemo(() => {
    return properties
      .filter((p) => p.verified && p.status === 'PUBLISHED')
      .sort((a, b) => a.auctionEnd - b.auctionEnd);
  }, [properties]);

  return (
    <div className="auctions-view">
      {/* Hero */}
      <div className="auctions-hero">
        <div className="container">
          <h1>
            Live <span className="gold">E-Auctions</span>
          </h1>
          <p>
            Discover and review bank-owned assets under SARFAESI & DRT recovery. All reserve prices are statutory published, and our concierge desk provides assisted bidding on official bank portals.
          </p>
          <div className="auc-chips">
            <span className="chip">
              <span className="dot-live"></span> Auctions Live Now
            </span>
            <span className="chip">
              <Clock size={14} color="#E8B849" /> Ending Within 7 Days
            </span>
            <span className="chip">
              <Building2 size={14} color="#E8B849" /> 20+ Empanelled Banks
            </span>
          </div>
        </div>
      </div>

      {/* Live Auctions Grid */}
      <section className="section">
        <div className="container">
          <div className="section-head">
            <div>
              <h2>
                All Live <span className="gold">E-Auctions</span>
              </h2>
              <p>Ranked strictly by time remaining — participate before the digital gavel falls.</p>
            </div>
            <button className="btn btn-outline" onClick={() => onNavigate('properties')}>
              Browse All Properties <ArrowRight size={16} />
            </button>
          </div>

          <div className="prop-grid">
            {sortedLiveAuctions.map((p) => (
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

      {/* 4 Step Process Grid */}
      <section className="section process-section">
        <div className="container">
          <div className="center">
            <h2>
              How Electronic Bidding <span className="gold">Works</span>
            </h2>
            <p style={{ color: '#64748B', marginTop: 4 }}>
              Four simple transparent steps from listing discovery to key handover.
            </p>
          </div>

          <div className="process-grid">
            <div className="process-step">
              <span className="ps-num">01</span>
              <UserCheck size={26} color="#071D35" />
              <h4>Register & KYC</h4>
              <p>Create your bidder account and verify your PAN and identity documents in 2 minutes.</p>
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
