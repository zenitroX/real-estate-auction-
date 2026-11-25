import React, { useState, useEffect } from 'react';
import { X, CheckCircle2, ShieldAlert } from 'lucide-react';
import { formatPriceShort } from '../../data/propertiesData';

const ASSISTANCE_OPTIONS = [
  { value: 'General Auction Guidance', paid: false, label: 'General Auction Guidance (Free)' },
  { value: 'Physical Property Inspection', paid: true, label: 'Physical Property Inspection' },
  { value: 'Document Review', paid: true, label: 'Document Review Coordination' },
  { value: 'Legal Coordination', paid: true, label: 'Legal Consultation Coordination' },
  { value: 'Auction Guidance', paid: true, label: 'Auction Participation Guidance' },
  { value: 'Complete Buyer Assistance', paid: true, label: 'Complete Buyer Assistance' },
];

export default function ContactModal({
  isOpen,
  onClose,
  property,
  onSubmitContact,
  currentUser,
  initialInquiryType = 'General Auction Guidance',
}) {
  const [name, setName] = useState(currentUser?.name || '');
  const [phone, setPhone] = useState(currentUser?.phone || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [preferredContact, setPreferredContact] = useState('PHONE');
  const [inquiryType, setInquiryType] = useState(initialInquiryType || 'General Auction Guidance');
  const [message, setMessage] = useState('');
  const [consentChecked, setConsentChecked] = useState(false);
  const [agreementAccepted, setAgreementAccepted] = useState(false);
  const [acceptedName, setAcceptedName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [submittedData, setSubmittedData] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setInquiryType(initialInquiryType || 'General Auction Guidance');
      setSubmittedData(null);
      setError('');
      setName(currentUser?.name || '');
      setPhone(currentUser?.phone || '');
      setEmail(currentUser?.email || '');
      setAcceptedName(currentUser?.name || '');
      setMessage('');
      setConsentChecked(false);
      setAgreementAccepted(false);
      setSubmitting(false);
    }
  }, [isOpen, initialInquiryType, currentUser]);

  if (!isOpen || !property) return null;

  const selectedOption = ASSISTANCE_OPTIONS.find((o) => o.value === inquiryType) || ASSISTANCE_OPTIONS[0];
  const requiresAgreement = selectedOption.paid;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;
    setError('');

    if (!consentChecked) {
      setError('Please confirm consent to be contacted regarding this property.');
      return;
    }
    if (requiresAgreement && (!agreementAccepted || !acceptedName.trim())) {
      setError('Please review and accept the proposed 5% service agreement and enter your full name.');
      return;
    }

    setSubmitting(true);
    try {
      const submission = {
        propertyId: property.id,
        propertyTitle: property.title,
        locality: property.locality,
        bank: property.bank,
        customerName: name.trim(),
        phone: phone.trim(),
        email: email.trim(),
        preferredContact,
        inquiryType,
        message: message.trim(),
        agreementAccepted: requiresAgreement ? agreementAccepted : false,
        acceptedName: requiresAgreement ? acceptedName.trim() : '',
      };
      const res = await onSubmitContact(submission);
      setSubmittedData({
        ...submission,
        refCode: res?.leadCode || res?.leadId || 'REQUEST_RECEIVED',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to submit request.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal" style={{ width: 'min(560px, 100%)', maxHeight: '90vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        {submittedData ? (
          <div className="modal-success-view" style={{ textAlign: 'center', padding: '1rem 0' }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#DCFCE7', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
              <CheckCircle2 size={36} color="#16A34A" />
            </div>
            <h3>Assistance Request Received</h3>
            <p style={{ color: '#64748B', fontSize: '0.9rem', margin: '8px 0 16px' }}>
              Reference: <strong>{submittedData.refCode}</strong> · Status: <strong>Request received</strong>
            </p>
            <button className="btn btn-primary" onClick={onClose}>
              Done
            </button>
          </div>
        ) : (
          <>
            <div className="modal-head">
              <h3>Connect with Auction Advisor</h3>
              <p style={{ fontSize: '0.86rem', color: '#64748B' }}>
                {property.title} · Reserve: {property.reserve ? formatPriceShort(property.reserve) : 'Not available'}
              </p>
            </div>

            {error && (
              <div style={{ marginBottom: 12, padding: '10px 12px', borderRadius: 8, background: '#FEF2F2', color: '#991B1B', fontSize: '0.85rem' }}>
                {error}
              </div>
            )}

            <form className="modal-form" onSubmit={handleSubmit}>
              <div className="form-field">
                <label>Assistance Category</label>
                <select value={inquiryType} onChange={(e) => setInquiryType(e.target.value)}>
                  {ASSISTANCE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-field">
                  <label>Full Name</label>
                  <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
                </div>
                <div className="form-field">
                  <label>Phone Number</label>
                  <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} minLength={7} required />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-field">
                  <label>Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                </div>
                <div className="form-field">
                  <label>Preferred Contact</label>
                  <select value={preferredContact} onChange={(e) => setPreferredContact(e.target.value)}>
                    <option value="PHONE">Phone Call</option>
                    <option value="WHATSAPP">WhatsApp</option>
                    <option value="EMAIL">Email</option>
                  </select>
                </div>
              </div>

              <div className="form-field">
                <label>Notes (Optional)</label>
                <textarea rows={2} value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Questions about inspection, EC, or auction participation..." />
              </div>

              {requiresAgreement && (
                <div style={{ padding: 12, borderRadius: 10, background: '#FFFBEB', border: '1px solid #FDE68A', marginBottom: 12, fontSize: '0.82rem', color: '#78350F' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, marginBottom: 6 }}>
                    <ShieldAlert size={16} /> Proposed 5% Success-Commission Service Agreement
                  </div>
                  <p style={{ margin: '0 0 8px' }}>
                    <strong>Proposed Terms:</strong> 5.00% of final successful auction hammer price upon Sale Certificate issuance (payable within 7 business days, exclusive of applicable GST). Public listings remain free; this fee applies only upon successful acquisition with our substantive assistance and is subject to formal written mandate and legal/tax validation.
                  </p>
                  <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, cursor: 'pointer', marginBottom: 8 }}>
                    <input type="checkbox" checked={agreementAccepted} onChange={(e) => setAgreementAccepted(e.target.checked)} />
                    <span>I have read and accept the proposed 5% service agreement disclosure.</span>
                  </label>
                  <input
                    type="text"
                    value={acceptedName}
                    onChange={(e) => setAcceptedName(e.target.value)}
                    placeholder="Type your full name to confirm"
                  />
                </div>
              )}

              <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: '0.82rem', color: '#475569', marginBottom: 14, cursor: 'pointer' }}>
                <input type="checkbox" checked={consentChecked} onChange={(e) => setConsentChecked(e.target.checked)} />
                <span>I consent to be contacted by SKANDX auction advisors regarding this property.</span>
              </label>

              <button className="btn btn-gold btn-block" type="submit" disabled={submitting}>
                {submitting ? 'Submitting...' : 'Submit Advisor Request'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
