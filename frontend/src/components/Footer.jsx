import React from 'react';
import {
  Building2,
  MapPin,
  Phone,
  Mail,
  ShieldCheck,
  Scale,
  Award,
} from 'lucide-react';

export default function Footer({ setActivePage }) {
  const navigate = (page) => {
    setActivePage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        {/* Brand statement */}
        <div className="f-brand">
          <div className="brand" style={{ cursor: 'pointer' }} onClick={() => navigate('home')}>
            <span className="brand-mark">
              <Building2 size={24} />
            </span>
            <span className="brand-text">
              <span>
                SKAN<span className="gold">DX</span>
              </span>
              <small>The Future of Property Auctions</small>
            </span>
          </div>
          <p>
            India's premier digital marketplace for bank auction, SARFAESI and distressed real estate assets. Complete transparency, empanelled legal due diligence, and direct bank inventory.
          </p>
          <div className="f-social">
            <a href="#facebook" aria-label="Facebook">
              <span style={{ fontWeight: 700 }}>f</span>
            </a>
            <a href="#twitter" aria-label="Twitter">
              <span style={{ fontWeight: 700 }}>𝕏</span>
            </a>
            <a href="#linkedin" aria-label="LinkedIn">
              <span style={{ fontWeight: 700 }}>in</span>
            </a>
          </div>
        </div>

        {/* Quick Links */}
        <div className="f-col">
          <h4>Quick Links</h4>
          <a href="#home" onClick={(e) => { e.preventDefault(); navigate('home'); }}>Home Marketplace</a>
          <a href="#properties" onClick={(e) => { e.preventDefault(); navigate('properties'); }}>Auction Properties</a>
          <a href="#auctions" onClick={(e) => { e.preventDefault(); navigate('auctions'); }}>Live E-Auctions</a>
          <a href="#dashboard" onClick={(e) => { e.preventDefault(); navigate('dashboard'); }}>Bidder Portal</a>
          <a href="#about" onClick={(e) => { e.preventDefault(); navigate('about'); }}>About SKANDX</a>
        </div>

        {/* Services */}
        <div className="f-col">
          <h4>Our Services</h4>
          <a href="#services" onClick={(e) => { e.preventDefault(); navigate('services'); }}>Legal Title Scrutiny</a>
          <a href="#services" onClick={(e) => { e.preventDefault(); navigate('services'); }}>Physical Site Visits</a>
          <a href="#services" onClick={(e) => { e.preventDefault(); navigate('services'); }}>Independent Valuation</a>
          <a href="#services" onClick={(e) => { e.preventDefault(); navigate('services'); }}>Auction Bridge Finance</a>
          <a href="#services" onClick={(e) => { e.preventDefault(); navigate('services'); }}>Sale Certificate Mutation</a>
        </div>

        {/* Contact */}
        <div className="f-col">
          <h4>Corporate Headquarters</h4>
          <span>
            <MapPin size={18} />
            7th Floor, Tidel Park, Rajiv Gandhi Salai, Taramani, Chennai – 600113, Tamil Nadu
          </span>
          <span>
            <Phone size={18} />
            1800 - 202 - SKANDX (Toll-Free)
          </span>
          <span>
            <Mail size={18} />
            auctions@skandx.in
          </span>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container fb-inner">
          <span>&copy; {new Date().getFullYear()} SKANDX Technologies Pvt. Ltd. All rights reserved.</span>
          <span>Empanelled with SBI, Canara Bank, ICICI Bank, Indian Bank, and Axis Bank.</span>
        </div>
      </div>
    </footer>
  );
}
