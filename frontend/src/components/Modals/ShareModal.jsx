import React, { useState } from 'react';
import { X, Copy, Check, Share2 } from 'lucide-react';

export default function ShareModal({ isOpen, onClose, property, onCopyLink }) {
  const [copied, setCopied] = useState(false);
  if (!isOpen || !property) return null;

  const url = `${window.location.origin}/#property/${property.id}`;

  const handleCopy = () => {
    navigator.clipboard?.writeText(url);
    setCopied(true);
    onCopyLink();
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        <div className="modal-head">
          <span className="brand-mark">
            <Share2 size={22} />
          </span>
          <h3>Share Property Auction</h3>
          <p>{property.title} &middot; {property.locality}</p>
        </div>

        <div className="modal-form">
          <div className="form-field">
            <label>Direct Listing URL</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="text"
                readOnly
                value={url}
                style={{ flex: 1, background: '#F8FAFC' }}
              />
              <button className="btn btn-gold btn-sm" onClick={handleCopy}>
                {copied ? <Check size={16} /> : <Copy size={16} />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
            <a
              href={`https://api.whatsapp.com/send?text=${encodeURIComponent(`Check out this Bank Auction listing: ${property.title} (${property.locality}) on SKANDX: ${url}`)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline"
              style={{ justifyContent: 'center' }}
            >
              WhatsApp
            </a>
            <a
              href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(`Live Bank Auction: ${property.title} in ${property.locality} via @SKANDX`)}&url=${encodeURIComponent(url)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline"
              style={{ justifyContent: 'center' }}
            >
              Twitter / 𝕏
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
