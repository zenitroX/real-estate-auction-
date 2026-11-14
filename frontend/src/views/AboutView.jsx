import React from 'react';
import { Eye, Lock, Users2, Check } from 'lucide-react';

export default function AboutView({ onNavigate }) {
  return (
    <div className="about-view">
      <div className="page-head">
        <div className="container">
          <h1>
            About <span className="gold">SKANDX</span>
          </h1>
          <p>Democratizing access to institutional bank property auctions across India.</p>
        </div>
      </div>

      <section className="section">
        <div className="container about-grid">
          <div className="about-visual">
            <img
              src="https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1000&q=80"
              alt="SKANDX legal and auction property team"
            />
          </div>

          <div className="about-copy">
            <h2>
              Built for <span className="gold">transparent</span> property acquisitions
            </h2>
            <p>
              SKANDX is a technology-first digital auction marketplace that transitions bank auction, SARFAESI, and stressed corporate properties out of opaque back-office tender files into an open, institutional digital ecosystem.
            </p>
            <p>
              We partner directly with leading public and private banks to digitize legal auction notices, conduct rigorous on-site verification, and provide buyers with end-to-end transaction security.
            </p>

            <ul className="about-points">
              <li>
                <Check size={18} /> 100% statutory bank-owned inventory (no retail broker listings)
              </li>
              <li>
                <Check size={18} /> Published official reserve prices with zero hidden commission markups
              </li>
              <li>
                <Check size={18} /> Comprehensive pan-India coverage across Tier-1 & Tier-2 industrial belts
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Navy Stats Band */}
      <div className="stats-band navy">
        <div className="container stats-grid">
          <div className="stat">
            <div className="stat-info">
              <strong>2019</strong>
              <span>Year Founded</span>
            </div>
          </div>
          <div className="stat">
            <div className="stat-info">
              <strong>26+</strong>
              <span>Cities Covered</span>
            </div>
          </div>
          <div className="stat">
            <div className="stat-info">
              <strong>₹ 480 Cr</strong>
              <span>Assets Transacted</span>
            </div>
          </div>
          <div className="stat">
            <div className="stat-info">
              <strong>98.4%</strong>
              <span>Clear Title Satisfaction</span>
            </div>
          </div>
        </div>
      </div>

      {/* Values Grid */}
      <section className="section">
        <div className="container">
          <div className="center">
            <h2>Our Core <span className="gold">Principles</span></h2>
            <p style={{ color: '#64748B', marginTop: 4 }}>
              The pillars behind India's fastest-growing auction intelligence platform.
            </p>
          </div>

          <div className="values-grid">
            <div className="value-card">
              <Eye size={32} />
              <h4>Transparency First</h4>
              <p>Every tender and auction notice is published with complete case history, encumbrance disclosure, and bank contact officers.</p>
            </div>

            <div className="value-card">
              <Lock size={32} />
              <h4>Institutional Security</h4>
              <p>Bank-grade data encryption, RBI and SARFAESI compliance protocols, and legally verified escrow accounts for all EMD deposits.</p>
            </div>

            <div className="value-card">
              <Users2 size={32} />
              <h4>Dedicated Concierge</h4>
              <p>Every registered bidder is assigned a specialized relationship manager who coordinates inspection, bidding, and title conveyance.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
