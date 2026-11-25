import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { Scale, ArrowLeft, PhoneCall } from 'lucide-react';
import { formatPriceShort, formatSqft, typeLabel } from '../data/propertiesData';

export default function CompareView({ properties, onNavigate, onViewProperty, onContact }) {
  const [searchParams] = useSearchParams();
  const idsParam = searchParams.get('ids') || '';
  const selectedIds = idsParam.split(',').map((s) => s.trim()).filter(Boolean);
  const compared =
    selectedIds.length > 0
      ? properties.filter((p) => selectedIds.includes(String(p.id)))
      : properties.slice(0, 3);

  return (
    <div className="container" style={{ padding: '2.5rem 1.5rem 4rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '1.75rem', margin: 0 }}>
            <Scale size={24} color="#E8B849" /> Compare Auction Properties
          </h1>
          <p style={{ color: '#64748B', marginTop: 4, fontSize: '0.9rem' }}>
            Side-by-side factual comparison. Pending checks and risks are shown transparently without safety rankings.
          </p>
        </div>
        <button className="btn btn-outline" onClick={() => onNavigate('auctions')}>
          <ArrowLeft size={16} /> Back to Auctions
        </button>
      </div>

      {compared.length === 0 ? (
        <div style={{ padding: '3rem', textAlign: 'center', background: '#F8FAFC', borderRadius: 12, border: '1px solid #E2E8F0' }}>
          <p style={{ color: '#64748B', marginBottom: '1rem' }}>No properties selected for comparison.</p>
          <button className="btn btn-primary" onClick={() => onNavigate('auctions')}>
            Browse Auctions
          </button>
        </div>
      ) : (
        <div style={{ overflowX: 'auto', border: '1px solid #E2E8F0', borderRadius: 12, background: '#fff' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 640 }}>
            <thead>
              <tr style={{ background: '#071D35', color: '#fff', textAlign: 'left' }}>
                <th style={{ padding: 14, width: 180 }}>Attribute</th>
                {compared.map((p) => (
                  <th key={p.id} style={{ padding: 14 }}>
                    <button
                      onClick={() => onViewProperty(p.id)}
                      style={{ background: 'none', border: 'none', color: '#E8B849', fontWeight: 700, cursor: 'pointer', textAlign: 'left', padding: 0 }}
                    >
                      {p.title}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ['Reserve Price', (p) => (p.reserve ? formatPriceShort(p.reserve) : 'Not available')],
                ['EMD Amount', (p) => (p.emd ? formatPriceShort(p.emd) : 'Not available')],
                ['Property Type', (p) => typeLabel(p.type)],
                ['Location', (p) => p.locality || 'Not available'],
                ['Area', (p) => (p.area ? formatSqft(p.area) : 'Not available')],
                ['Auction Date', (p) => (p.auctionEnd ? new Date(p.auctionEnd).toLocaleDateString('en-IN') : 'Not yet confirmed')],
                ['Possession', (p) => p.possessionType || 'Not yet confirmed'],
                ['Bank', (p) => p.bank || 'Not available'],
                ['Verification Summary', (p) => {
                  const dims = p.verificationDimensions || {};
                  const completed = Object.values(dims).filter((d) => d?.status === 'COMPLETED').length;
                  return `${completed}/8 checks completed`;
                }],
                ['Disclosed Risks', (p) => (p.riskDisclosures?.length ? p.riskDisclosures.join(', ') : 'See property detail')],
              ].map(([label, getter]) => (
                <tr key={label} style={{ borderTop: '1px solid #E2E8F0' }}>
                  <td style={{ padding: 12, fontWeight: 600, color: '#334155', background: '#F8FAFC' }}>{label}</td>
                  {compared.map((p) => (
                    <td key={p.id} style={{ padding: 12, color: '#1E293B', fontSize: '0.9rem' }}>
                      {getter(p)}
                    </td>
                  ))}
                </tr>
              ))}
              <tr style={{ borderTop: '1px solid #E2E8F0' }}>
                <td style={{ padding: 12, fontWeight: 600, background: '#F8FAFC' }}>Action</td>
                {compared.map((p) => (
                  <td key={p.id} style={{ padding: 12 }}>
                    <button className="btn btn-gold btn-sm" onClick={() => onContact(p)}>
                      <PhoneCall size={14} /> Connect with Advisor
                    </button>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
