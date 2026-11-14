import React, { useState } from 'react';
import { X, Gavel, AlertCircle, Check } from 'lucide-react';
import { formatRupees, formatPriceShort } from '../../data/propertiesData';

export default function BiddingModal({
  isOpen,
  onClose,
  property,
  currentHighestBid,
  onSubmitBid,
}) {
  if (!isOpen || !property) return null;

  const minNextBid = (currentHighestBid || property.reserve) + (property.increment || 50000);
  const [bidAmount, setBidAmount] = useState(minNextBid);
  const [error, setError] = useState('');

  const handleIncrement = (inc) => {
    setBidAmount((prev) => Math.max(minNextBid, prev + inc));
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (bidAmount < minNextBid) {
      setError(`Minimum bid must be at least ${formatRupees(minNextBid)} (increment of ${formatRupees(property.increment)})`);
      return;
    }
    onSubmitBid(property, Number(bidAmount));
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close modal">
          <X size={20} />
        </button>

        <div className="modal-head">
          <span className="brand-mark">
            <Gavel size={22} />
          </span>
          <h3>Place Your Bid</h3>
          <p>{property.title} &middot; {property.locality}</p>
        </div>

        <form className="modal-form" onSubmit={handleSubmit}>
          {/* Current Highest Bid Card */}
          <div className="bid-current">
            <small>Current Benchmark Bid</small>
            <strong>{formatPriceShort(currentHighestBid || property.reserve)}</strong>
            <span>Minimum next bid: {formatRupees(minNextBid)}</span>
          </div>

          {/* Quick Increment Pills */}
          <div className="form-field">
            <label>Quick Increment</label>
            <div className="quick-bids">
              <button
                type="button"
                className="quick-bid-pill"
                onClick={() => handleIncrement(property.increment || 50000)}
              >
                +{formatPriceShort(property.increment || 50000)}
              </button>
              <button
                type="button"
                className="quick-bid-pill"
                onClick={() => handleIncrement(100000)}
              >
                +₹1 Lakh
              </button>
              <button
                type="button"
                className="quick-bid-pill"
                onClick={() => handleIncrement(250000)}
              >
                +₹2.5 Lakhs
              </button>
              <button
                type="button"
                className="quick-bid-pill"
                onClick={() => handleIncrement(500000)}
              >
                +₹5 Lakhs
              </button>
            </div>
          </div>

          {/* Amount input */}
          <div className="form-field">
            <label>Your Bid Amount (₹)</label>
            <input
              type="number"
              min={minNextBid}
              step={property.increment || 25000}
              value={bidAmount}
              onChange={(e) => {
                setBidAmount(Number(e.target.value));
                setError('');
              }}
              required
            />
            <span style={{ fontSize: '0.8rem', color: '#64748B', marginTop: 4 }}>
              Preview: <strong style={{ color: '#071D35' }}>{formatRupees(bidAmount)}</strong>
            </span>
          </div>

          {error && (
            <div style={{ color: '#DC2626', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertCircle size={15} />
              {error}
            </div>
          )}

          <button className="btn btn-gold btn-block btn-lg" type="submit">
            <Check size={18} /> Confirm Bid
          </button>

          <p className="demo-note" style={{ justifyContent: 'center' }}>
            <AlertCircle size={14} /> Simulated demo bidding &middot; Updates your live bidder dashboard
          </p>
        </form>
      </div>
    </div>
  );
}
