import React, { useState } from 'react';
import { X, Calendar, Clock, MapPin, Check } from 'lucide-react';

export default function SiteVisitModal({ isOpen, onClose, property, onSubmitVisit }) {
  if (!isOpen || !property) return null;

  const [date, setDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 2);
    return d.toISOString().split('T')[0];
  });
  const [slot, setSlot] = useState('11:00 AM - 1:00 PM');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmitVisit({
      propertyId: property.id,
      title: property.title,
      date,
      slot,
      notes,
    });
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
            <Calendar size={22} />
          </span>
          <h3>Schedule Site Visit</h3>
          <p>{property.title} &middot; {property.locality}</p>
        </div>

        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Inspection Date</label>
            <input
              type="date"
              value={date}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          <div className="form-field">
            <label>Preferred Time Slot</label>
            <select value={slot} onChange={(e) => setSlot(e.target.value)}>
              <option value="10:00 AM - 12:00 PM">Morning: 10:00 AM - 12:00 PM</option>
              <option value="11:00 AM - 1:00 PM">Late Morning: 11:00 AM - 1:00 PM</option>
              <option value="2:00 PM - 4:00 PM">Afternoon: 2:00 PM - 4:00 PM</option>
              <option value="4:00 PM - 6:00 PM">Evening: 4:00 PM - 6:00 PM</option>
            </select>
          </div>

          <div className="form-field">
            <label>Nodal Officer Assigned</label>
            <input
              type="text"
              readOnly
              value={`${property.officer || 'R. Meenakshi'} (${property.bank})`}
              style={{ background: '#F8FAFC', color: '#64748B' }}
            />
          </div>

          <div className="form-field">
            <label>Special Notes (Optional)</label>
            <textarea
              rows={2}
              placeholder="e.g. Need to inspect rooftop, require legal counsel accompany..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <button className="btn btn-gold btn-block btn-lg" type="submit">
            <Check size={18} /> Confirm Inspection Booking
          </button>
        </form>
      </div>
    </div>
  );
}
