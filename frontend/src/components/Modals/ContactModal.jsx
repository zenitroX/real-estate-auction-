import React, { useState } from 'react';
import {
  X,
  PhoneCall,
  MessageSquare,
  Calendar,
  FileCheck,
  Send,
  Building2,
  CheckCircle2,
  Headset,
} from 'lucide-react';
import { formatPriceShort } from '../../data/propertiesData';

export default function ContactModal({
  isOpen,
  onClose,
  property,
  onSubmitContact,
  currentUser,
}) {
  const [name, setName] = useState(currentUser?.name || '');
  const [phone, setPhone] = useState(currentUser?.phone || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [inquiryType, setInquiryType] = useState('Site Visit Inspection');
  const [message, setMessage] = useState('');

  if (!isOpen || !property) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmitContact({
      propertyId: property.id,
      propertyTitle: property.title,
      locality: property.locality,
      customerName: name || 'Interested Bidder',
      phone,
      email,
      inquiryType,
      message,
    });
    onClose();
  };

  const whatsappMessage = encodeURIComponent(
    `Hello SKANDX Team! I am interested in verified bank property: ${property.title} in ${property.locality} (Reserve: ${formatPriceShort(property.reserve)}). Please provide inspection and legal assistance.`
  );

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal" style={{ width: 'min(540px, 100%)' }} onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        <div className="modal-head" style={{ marginBottom: 16 }}>
          <span className="brand-mark">
            <Building2 size={24} />
          </span>
          <h3 style={{ fontSize: '1.4rem' }}>Contact Property Desk</h3>
          <p style={{ marginTop: 4 }}>
            <strong>{property.title}</strong> &middot; {property.locality}
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 6, background: '#FEF3C7', color: '#B45309', padding: '3px 10px', borderRadius: 20, fontSize: '0.78rem', fontWeight: 700 }}>
            Reserve Price: {formatPriceShort(property.reserve)} &middot; {property.bank}
          </div>
        </div>

        {/* Quick Instant Channels: Hotline & WhatsApp */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 18 }}>
          <a
            href="tel:18002027526"
            className="btn btn-outline"
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px 10px', gap: 4 }}
          >
            <PhoneCall size={18} color="#D9A62E" />
            <strong style={{ fontSize: '0.85rem' }}>Call Toll-Free</strong>
            <span style={{ fontSize: '0.72rem', color: '#64748B' }}>1800 - 202 - SKANDX</span>
          </a>

          <a
            href={`https://api.whatsapp.com/send?phone=919176011223&text=${whatsappMessage}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-outline"
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px 10px', gap: 4, borderColor: '#86EFAC', background: '#F0FDF4' }}
          >
            <MessageSquare size={18} color="#16A34A" />
            <strong style={{ fontSize: '0.85rem', color: '#166534' }}>Chat on WhatsApp</strong>
            <span style={{ fontSize: '0.72rem', color: '#16A34A' }}>Instant Live Response</span>
          </a>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '14px 0', color: '#94A3B8', fontSize: '0.78rem' }}>
          <div style={{ flex: 1, height: 1, background: '#E2E8F0' }}></div>
          <span>OR REQUEST OFFICIAL CALLBACK</span>
          <div style={{ flex: 1, height: 1, background: '#E2E8F0' }}></div>
        </div>

        {/* Callback Form */}
        <form className="modal-form" onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-field">
              <label>Your Name</label>
              <input
                type="text"
                placeholder="e.g. Ramesh Kumar"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-field">
              <label>Mobile Number</label>
              <input
                type="tel"
                placeholder="+91 98400 ..."
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-field">
            <label>Service / Assistance Required</label>
            <select value={inquiryType} onChange={(e) => setInquiryType(e.target.value)}>
              <option value="Site Visit Inspection">Schedule Physical Site Visit</option>
              <option value="Legal Search Report">Request 30-Year Legal Title Search Pack</option>
              <option value="EMD & Financing Guidance">EMD Deposit & Auction Loan Assistance</option>
              <option value="General Property Inquiry">General Property & Tender Inquiries</option>
            </select>
          </div>

          <div className="form-field">
            <label>Message / Notes (Optional)</label>
            <textarea
              rows={2}
              placeholder="e.g. Preferred inspection day, boundary verification questions..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>

          <button className="btn btn-gold btn-block btn-lg" type="submit">
            <Send size={16} /> Submit Contact Request
          </button>

          <p className="demo-note" style={{ justifyContent: 'center' }}>
            <CheckCircle2 size={13} color="#16A34A" /> Direct lead assigned to authorized liaison desk &middot; Zero agent spam
          </p>
        </form>
      </div>
    </div>
  );
}
