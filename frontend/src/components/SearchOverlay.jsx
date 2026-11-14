import React, { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';

export default function SearchOverlay({ isOpen, onClose, onSearch }) {
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      onClose();
    }
  };

  return (
    <div className="search-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="search-box" onClick={(e) => e.stopPropagation()}>
        <Search size={22} color="#071D35" />
        <form onSubmit={handleSubmit} style={{ flex: 1, display: 'flex' }}>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search by city (e.g. Chennai, Bengaluru), bank, or property type…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>
        <button className="btn btn-gold btn-sm" onClick={handleSubmit}>
          Search
        </button>
        <button className="search-close" onClick={onClose} aria-label="Close search">
          <X size={20} />
        </button>
      </div>
    </div>
  );
}
