import React from 'react';
import {
  Scale,
  BadgeDollarSign,
  Compass,
  IndianRupee,
  FileCheck,
  Gavel,
  ArrowRight,
} from 'lucide-react';

export default function ServicesView({ onOpenAuth, onNavigate }) {
  const services = [
    {
      icon: Scale,
      title: 'Empanelled Legal Assistance',
      desc: '30-year title verification, encumbrance certificates (EC), SARFAESI compliance checks, and court case due diligence conducted by veteran advocates.',
    },
    {
      icon: BadgeDollarSign,
      title: 'Independent Valuation Reports',
      desc: 'Third-party certified architectural and market valuation reports providing true replacement cost and realistic rental yield benchmarks.',
    },
    {
      icon: Compass,
      title: 'Accompanied Site Visits',
      desc: 'Scheduled on-site inspections accompanied by our ground officers and bank nodal recovery managers prior to auction day.',
    },
    {
      icon: IndianRupee,
      title: 'Auction Financing & Loans',
      desc: 'Strategic partnerships with leading NBFCs and banks for bridge funding of EMD deposits and rapid loan sanctioning for auction winners.',
    },
    {
      icon: FileCheck,
      title: 'End-to-End Documentation',
      desc: 'Complete post-auction paperwork support: Sale Certificate issuance, Sub-Registrar registration, Patta/Khata mutation, and electricity transfer.',
    },
    {
      icon: Gavel,
      title: 'Live Bidding Concierge',
      desc: 'Dedicated auction desk strategy inputs, incremental bid guidance, and live representation to ensure you acquire target properties at optimal valuations.',
    },
  ];

  return (
    <div className="services-view">
      {/* Header */}
      <div className="page-head">
        <div className="container">
          <h1>
            Our <span className="gold">Services</span>
          </h1>
          <p>Institutional due diligence, financing and physical possession support.</p>
        </div>
      </div>

      {/* Services Grid */}
      <section className="section">
        <div className="container services-grid">
          {services.map((s, idx) => {
            const Icon = s.icon;
            return (
              <div key={idx} className="service-card">
                <Icon size={34} color="#D9A62E" />
                <h4>{s.title}</h4>
                <p>{s.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA Band */}
      <div className="cta-band">
        <div className="container cta-inner">
          <div>
            <h2>Ready to bid on verified bank properties?</h2>
            <p>Register your bidder account today to access published notices and participate in live e-auctions.</p>
          </div>
          <button
            className="btn btn-gold btn-lg"
            onClick={() => onOpenAuth('register')}
          >
            Create Free Account <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
