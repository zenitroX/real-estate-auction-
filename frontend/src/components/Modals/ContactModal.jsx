import React, { useState, useEffect } from 'react';
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
  initialInquiryType = 'Site Inspection',
}) {
  const [name, setName] = useState(currentUser?.name || '');
  const [phone, setPhone] = useState(currentUser?.phone || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [inquiryType, setInquiryType] = useState(initialInquiryType || 'Site Inspection');
  const [message, setMessage] = useState('');
  const [submittedData, setSubmittedData] = useState(null);

  useEffect(() => {
    if (isOpen) {
      if (initialInquiryType) {
        setInquiryType(initialInquiryType);
      }
      setSubmittedData(null);
      setName(currentUser?.name || '');
      setPhone(currentUser?.phone || '');
      setEmail(currentUser?.email || '');
      setMessage('');
    }
  }, [isOpen, initialInquiryType, currentUser]);

  if (!isOpen || !property) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const refCode = `#SK-${Math.floor(1000 + Math.random() * 9000)}`;
    const submission = {
      propertyId: property.id,
      propertyTitle: property.title,
      locality: property.locality,
      bank: property.bank,
      customerName: name || 'Interested Bidder',
      phone,
      email,
      inquiryType,
      message,
      refCode,
    };
    onSubmitContact(submission);
    setSubmittedData(submission);
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

        {submittedData ? (
          /* STEP 2: In-Modal Success Confirmation */
          <div className="modal-success-view">
            <div className="modal-head" style={{ textAlign: 'center', marginBottom: 20 }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: '#DCFCE7',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: 12,
                  boxShadow: '0 0 0 6px #F0FDF4',
                }}
              >
                <CheckCircle2 size={36} color="#16A34A" />
              </div>
              <h3 style={{ fontSize: '1.45rem', color: '#071D35', margin: 0 }}>
                Inquiry Successfully Registered!
              </h3>
              <p style={{ marginTop: 6, color: '#64748B', fontSize: '0.9rem' }}>
                Your request for <strong>{property.title}</strong> has been routed to our recovery desk.
              </p>
            </div>

            <div
              style={{
                background: '#F8FAFC',
                borderRadius: 12,
                padding: '18px 20px',
                border: '1px solid #E2E8F0',
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 12,
                  paddingBottom: 10,
                  borderBottom: '1px solid #E2E8F0',
                }}
              >
                <span style={{ fontSize: '0.85rem', color: '#64748B' }}>Reference ID</span>
                <span
                  style={{
                    fontFamily: 'monospace',
                    fontSize: '1.05rem',
                    fontWeight: 800,
                    color: '#071D35',
                    background: '#FEF3C7',
                    padding: '3px 12px',
                    borderRadius: 6,
                    border: '1px solid #FDE68A',
                  }}
                >
                  {submittedData.refCode}
                </span>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 12,
                  paddingBottom: 10,
                  borderBottom: '1px solid #E2E8F0',
                }}
              >
                <span style={{ fontSize: '0.85rem', color: '#64748B' }}>Inquiry Type</span>
                <strong style={{ fontSize: '0.9rem', color: '#071D35' }}>
                  {submittedData.inquiryType}
                </strong>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: 12,
                }}
              >
                <span style={{ fontSize: '0.85rem', color: '#64748B', flexShrink: 0 }}>
                  Estimated Callback
                </span>
                <strong style={{ fontSize: '0.9rem', color: '#16A34A', textAlign: 'right' }}>
                  Within 15 minutes by {property.bank || 'Canara/SBI'} Recovery Liaison
                </strong>
              </div>
            </div>

            {/* Direct WhatsApp button and Close */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <a
                href={`https://api.whatsapp.com/send?phone=919176011223&text=${encodeURIComponent(
                  `Hello SKANDX! I just registered inquiry ${submittedData.refCode} for ${property.title} (${property.bank}). Please connect me with the bank recovery liaison.`
                )}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline btn-lg"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  background: '#22C55E',
                  color: '#fff',
                  borderColor: '#22C55E',
                  fontWeight: 700,
                  boxShadow: '0 2px 8px rgba(34, 197, 94, 0.25)',
                }}
              >
                <MessageSquare size={18} color="#fff" />
                Chat Directly on WhatsApp
              </a>

              <button
                className="btn btn-outline btn-block"
                onClick={onClose}
                style={{ marginTop: 4 }}
              >
                Done & Return to Listing
              </button>
            </div>
          </div>
        ) : (
          /* STEP 1: Callback Form */
          <>
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
                  <option value="Download Notice">Download Official Auction Notice</option>
                  <option value="Legal Title Search Report">Request 30-Year Legal Title Search Pack</option>
                  <option value="Site Inspection">Schedule Physical Site Inspection</option>
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
          </>
        )}
      </div>
    </div>
  );
}