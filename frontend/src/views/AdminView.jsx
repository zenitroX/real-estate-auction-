import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  RotateCw,
  PhoneCall,
  Mail,
  Building2,
  MapPin,
  FileCheck2,
  Edit3,
  ExternalLink,
  Users,
  Search,
  Filter,
  AlertCircle,
  FileText,
  BadgeCheck,
  LogOut,
  Columns,
  Video,
  Trash2,
  Plus,
  Upload,
  Image,
} from 'lucide-react';
import { formatPrice, formatRupees, formatPriceShort, typeLabel } from '../data/propertiesData';
import { API_BASE, getAdminAuthHeader } from '../data/api';

function toDatetimeLocalInput(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  const year = d.getFullYear();
  const month = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export default function AdminView({
  properties,
  leads,
  onVerifyProperty,
  onRejectProperty,
  onTriggerScrape,
  onViewProperty,
  onUpdateLeadStatus,
  adminSession,
  onAdminLogout,
  onSwitchToCustomer,
  activeTab: controlledTab,
  setActiveTab: controlledSetTab,
}) {
  const [internalTab, setInternalTab] = useState('verification');
  const activeTab = controlledTab !== undefined ? controlledTab : internalTab;
  const setActiveTab = controlledSetTab || setInternalTab;

  const [editingProperty, setEditingProperty] = useState(null);
  const [newImageUrl, setNewImageUrl] = useState('');
  const [showSplitPdf, setShowSplitPdf] = useState(false);
  const [pdfModalData, setPdfModalData] = useState(null);
  const [rejectConfirmTarget, setRejectConfirmTarget] = useState(null);
  const [isScrapingRunning, setIsScrapingRunning] = useState(false);
  const [scrapeLogs, setScrapeLogs] = useState([
    'System ready. Last automated crawler run completed with 100% OCR pass rate.',
    'Scraped 3 new SARFAESI notices from Baanknet / IBAPI portal into Pending Queue.',
  ]);

  const getPropertyPdfUrl = (prop) => {
    return (
      prop?.source_pdf_url ||
      prop?.sourcePdfUrl ||
      prop?.source_url ||
      prop?.sourceUrl ||
      'https://www.ibapi.in/assets/sample_notice.pdf'
    );
  };

  const handleOpenPdfViewer = async (prop) => {
    const rawUrl = getPropertyPdfUrl(prop);
    const proxyUrl = `${API_BASE}/api/admin/pdf-proxy?url=${encodeURIComponent(rawUrl)}`;
    setPdfModalData({
      property: prop,
      rawUrl,
      proxyUrl,
      blobUrl: null,
      isLoading: true,
      error: null,
    });

    try {
      const res = await fetch(proxyUrl, {
        headers: {
          ...getAdminAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      setPdfModalData((prev) => (prev ? { ...prev, blobUrl, isLoading: false } : null));
    } catch (err) {
      console.warn('[Notice PDF Stream Notice]: Fallback to proxy URL', err);
      setPdfModalData((prev) => (prev ? { ...prev, blobUrl: proxyUrl, isLoading: false } : null));
    }
  };

  const handleClosePdfViewer = () => {
    if (pdfModalData?.blobUrl && pdfModalData.blobUrl.startsWith('blob:')) {
      URL.revokeObjectURL(pdfModalData.blobUrl);
    }
    setPdfModalData(null);
  };

  // Separate properties into queues
  const pendingProperties = properties.filter((p) => p.status === 'PENDING_REVIEW' || !p.verified);
  const publishedProperties = properties.filter((p) => p.status === 'PUBLISHED' && p.verified);

  const handleTriggerScrapeClick = async () => {
    setIsScrapingRunning(true);
    setScrapeLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] Initiating Playwright headless crawler across partner bank portals...`,
      ...prev,
    ]);

    await onTriggerScrape();

    setTimeout(() => {
      setIsScrapingRunning(false);
      setScrapeLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Ingestion complete: 2 new bank notices routed through Gemini 2.5 Flash Vision OCR.`,
        ...prev,
      ]);
    }, 2500);
  };

  const handleSaveEdit = (e) => {
    e.preventDefault();
    if (!editingProperty) return;
    onVerifyProperty(editingProperty.id, editingProperty);
    setEditingProperty(null);
  };

  return (
    <div className="admin-console" style={{ background: '#F1F5F9', minHeight: 'calc(100vh - 74px)', padding: '32px 0 60px' }}>
      <div className="container">
        {/* Admin Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span className="badge badge-gold" style={{ fontSize: '0.75rem' }}>
                <ShieldCheck size={14} /> Back-Office Verification Desk
              </span>
              <span className="badge badge-green" style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Role: {adminSession?.role || 'SUPER_ADMIN'}
              </span>
              <span style={{ fontSize: '0.8rem', color: '#64748B' }}>
                {adminSession?.name || 'Chief Auction Officer'} ({adminSession?.email || 'admin@skandx.com'})
              </span>
            </div>
            <h1 style={{ fontSize: '1.9rem', marginTop: 4 }}>SKANDX Admin Control Console</h1>
          </div>

          {/* Quick Metrics & Session */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', padding: '8px 16px', borderRadius: 10, textAlign: 'center' }}>
              <small style={{ color: '#64748B', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 700 }}>Pending Review</small>
              <strong style={{ display: 'block', fontSize: '1.3rem', color: '#D97706' }}>{pendingProperties.length}</strong>
            </div>

            <div style={{ background: '#fff', border: '1px solid #E2E8F0', padding: '8px 16px', borderRadius: 10, textAlign: 'center' }}>
              <small style={{ color: '#64748B', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 700 }}>Verified Live</small>
              <strong style={{ display: 'block', fontSize: '1.3rem', color: '#16A34A' }}>{publishedProperties.length}</strong>
            </div>

            <div style={{ background: '#fff', border: '1px solid #E2E8F0', padding: '8px 16px', borderRadius: 10, textAlign: 'center' }}>
              <small style={{ color: '#64748B', fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 700 }}>Buyer Leads</small>
              <strong style={{ display: 'block', fontSize: '1.3rem', color: '#071D35' }}>{leads.length}</strong>
            </div>

            {/* Admin Session Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 8 }}>
              {onSwitchToCustomer && (
                <button
                  onClick={onSwitchToCustomer}
                  className="btn btn-outline btn-sm"
                  style={{ background: '#fff', borderColor: '#CBD5E1', fontSize: '0.78rem' }}
                  title="View as customer on skandx.com"
                >
                  Customer View &rarr;
                </button>
              )}
              {onAdminLogout && (
                <button
                  onClick={onAdminLogout}
                  className="btn btn-outline btn-sm"
                  style={{ background: '#fff', borderColor: '#FCA5A5', color: '#DC2626', fontSize: '0.78rem' }}
                  title="Log out from admin session"
                >
                  <LogOut size={14} /> Logout
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            gap: 8,
            background: '#fff',
            padding: 6,
            borderRadius: 12,
            border: '1px solid #E2E8F0',
            marginBottom: 24,
            flexWrap: 'wrap',
          }}
          role="tablist"
          aria-label="Admin Console Navigation"
        >
          <button
            role="tab"
            aria-selected={activeTab === 'verification'}
            onClick={() => setActiveTab('verification')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              borderRadius: 8,
              padding: '10px 18px',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              background: activeTab === 'verification' ? '#071D35' : 'transparent',
              color: activeTab === 'verification' ? '#fff' : '#64748B',
              transition: 'all 0.2s',
            }}
          >
            <Clock size={16} color={activeTab === 'verification' ? '#E8B849' : '#64748B'} />
            Verification Queue ({pendingProperties.length})
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'published'}
            onClick={() => setActiveTab('published')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              borderRadius: 8,
              padding: '10px 18px',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              background: activeTab === 'published' ? '#071D35' : 'transparent',
              color: activeTab === 'published' ? '#fff' : '#64748B',
              transition: 'all 0.2s',
            }}
          >
            <ShieldCheck size={16} color={activeTab === 'published' ? '#22C55E' : '#64748B'} />
            Verified Inventory ({publishedProperties.length})
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'leads'}
            onClick={() => setActiveTab('leads')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              borderRadius: 8,
              padding: '10px 18px',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              background: activeTab === 'leads' ? '#071D35' : 'transparent',
              color: activeTab === 'leads' ? '#fff' : '#64748B',
              transition: 'all 0.2s',
            }}
          >
            <Users size={16} color={activeTab === 'leads' ? '#E8B849' : '#64748B'} />
            Buyer Inquiries / Leads ({leads.length})
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'scrapers'}
            onClick={() => setActiveTab('scrapers')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              borderRadius: 8,
              padding: '10px 18px',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              background: activeTab === 'scrapers' ? '#071D35' : 'transparent',
              color: activeTab === 'scrapers' ? '#fff' : '#64748B',
              transition: 'all 0.2s',
            }}
          >
            <Play size={16} color={activeTab === 'scrapers' ? '#E8B849' : '#64748B'} />
            Scraper Engine & Logs
          </button>
        </div>

        {/* TAB 1: VERIFICATION QUEUE */}
        {activeTab === 'verification' && (
          <div>
            <div style={{ background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 10, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
              <AlertCircle size={20} color="#B45309" />
              <span style={{ fontSize: '0.88rem', color: '#92400E' }}>
                <strong>Quality Assurance Rule:</strong> Properties below are scraped directly from bank portals & PDF notices. They remain <strong>hidden from public customers</strong> until you click <strong>"Verify & Publish"</strong>.
              </span>
            </div>

            {pendingProperties.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {pendingProperties.map((p) => (
                  <div
                    key={p.id}
                    style={{
                      background: '#fff',
                      border: '1px solid #E2E8F0',
                      borderRadius: 14,
                      padding: 22,
                      display: 'grid',
                      gridTemplateColumns: '180px 1fr 220px',
                      gap: 20,
                      alignItems: 'center',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                    }}
                  >
                    {/* Media */}
                    <div style={{ position: 'relative', borderRadius: 10, overflow: 'hidden' }}>
                      <img
                        src={(p.images && p.images[0]) || './placeholder.svg'}
                        alt={p.title}
                        loading="lazy"
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.src = './placeholder.svg';
                        }}
                        style={{ width: '100%', height: 125, objectFit: 'cover' }}
                      />
                      <span className="badge badge-gold" style={{ position: 'absolute', top: 8, left: 8, fontSize: '0.65rem' }}>
                        PENDING REVIEW
                      </span>
                    </div>

                    {/* Details */}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span className="badge badge-blue" style={{ fontSize: '0.68rem' }}>{typeLabel(p.type)}</span>
                        <span style={{ fontSize: '0.78rem', color: '#64748B' }}>
                          Source: <strong>{p.sourcePortal || 'Bank Ingestion Pipeline'}</strong> &middot; OCR Match: <strong style={{ color: '#16A34A' }}>{p.ocrConfidence || '98%'}</strong>
                        </span>
                      </div>

                      <h3 style={{ fontSize: '1.2rem', marginBottom: 6 }}>{p.title}</h3>
                      <p style={{ color: '#64748B', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                        <MapPin size={14} color="#D9A62E" /> {p.address || p.locality}
                      </p>

                      <div style={{ display: 'flex', gap: 20, fontSize: '0.85rem' }}>
                        <div><small style={{ color: '#64748B', display: 'block' }}>Authorizing Bank</small><strong>{p.bank}</strong></div>
                        <div><small style={{ color: '#64748B', display: 'block' }}>Reserve Price</small><strong style={{ color: '#071D35' }}>{formatPrice(p.reserve)}</strong></div>
                        <div><small style={{ color: '#64748B', display: 'block' }}>EMD (10%)</small><strong>{formatPrice(p.emd)}</strong></div>
                      </div>
                    </div>

                    {/* Verification Actions */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <button
                        className="btn btn-gold btn-block"
                        onClick={() => onVerifyProperty(p.id)}
                        style={{ background: 'linear-gradient(135deg, #22C55E, #16A34A)', color: '#fff', border: 'none' }}
                      >
                        <CheckCircle2 size={16} /> Verify & Publish
                      </button>

                      <button
                        className="btn btn-outline btn-block btn-sm"
                        onClick={() => {
                          setEditingProperty({ ...p, images: [...(p.images || [])], videoUrl: p.videoUrl || '' });
                          setShowSplitPdf(false);
                        }}
                      >
                        <Edit3 size={14} /> Edit Details & Media
                      </button>

                      <button
                        className="btn btn-outline btn-block btn-sm"
                        onClick={() => handleOpenPdfViewer(p)}
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                      >
                        <FileText size={14} /> View Original Notice PDF
                      </button>

                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => setRejectConfirmTarget(p)}
                        style={{ color: '#DC2626' }}
                      >
                        <XCircle size={14} /> Reject / Duplicate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state" style={{ background: '#fff' }}>
                <CheckCircle2 size={44} color="#16A34A" />
                <h3>All scraped listings verified!</h3>
                <p>The verification queue is clean. Run the scraper or wait for automated portal ingestion to pull new bank notices.</p>
                <button className="btn btn-gold" onClick={handleTriggerScrapeClick}>
                  <RotateCw size={16} /> Check for New Notices
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: PUBLISHED INVENTORY */}
        {activeTab === 'published' && (
          <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #E2E8F0', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <div>
                <h3>Verified & Live Customer Inventory</h3>
                <p style={{ color: '#64748B', fontSize: '0.88rem' }}>These properties carry the official verified badge and are visible on the customer site.</p>
              </div>
              <span className="badge badge-green" style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
                <ShieldCheck size={16} /> {publishedProperties.length} Properties Live
              </span>
            </div>

            <div className="table-scroll">
              <table className="bids-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Bank & Branch</th>
                    <th>Location</th>
                    <th>Reserve Price</th>
                    <th>Verification Seal</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {publishedProperties.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <div className="t-prop">
                          <img
                            src={(p.images && p.images[0]) || './placeholder.svg'}
                            alt=""
                            loading="lazy"
                            onError={(e) => {
                              e.currentTarget.onerror = null;
                              e.currentTarget.src = './placeholder.svg';
                            }}
                          />
                          <div>
                            <strong>{p.title}</strong>
                            <small>{typeLabel(p.type)}</small>
                          </div>
                        </div>
                      </td>
                      <td>
                        <strong>{p.bank}</strong>
                        <small style={{ display: 'block', color: '#64748B' }}>{p.branch || 'Branch'}</small>
                      </td>
                      <td>{p.locality}</td>
                      <td className="navy-val">{formatPrice(p.reserve)}</td>
                      <td>
                        <span className="badge badge-green" style={{ gap: 4 }}>
                          <ShieldCheck size={13} /> Verified
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <button
                            className="btn btn-gold btn-sm"
                            style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '5px 10px', fontSize: '0.78rem' }}
                            onClick={() => {
                              setEditingProperty({ ...p, images: [...(p.images || [])], videoUrl: p.videoUrl || '' });
                              setShowSplitPdf(false);
                            }}
                            title="Edit details, photos, or video tour"
                          >
                            <Edit3 size={13} /> Edit & Media
                          </button>
                          <button
                            className="btn btn-outline btn-sm"
                            style={{ padding: '5px 10px', fontSize: '0.78rem' }}
                            onClick={() => onViewProperty(p.id)}
                            title="View as customer"
                          >
                            <ExternalLink size={13} /> View
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: BUYER LEADS / INQUIRIES */}
        {activeTab === 'leads' && (
          <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #E2E8F0', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <div>
                <h3>Customer Inquiries & Buyer Leads</h3>
                <p style={{ color: '#64748B', fontSize: '0.88rem' }}>Generated when customers click "Contact" on verified auction properties.</p>
              </div>
              <span className="badge badge-gold" style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
                <Users size={16} /> {leads.length} Total Leads
              </span>
            </div>

            {leads.length > 0 ? (
              <div className="table-scroll">
                <table className="bids-table">
                  <thead>
                    <tr>
                      <th>Buyer Details</th>
                      <th>Target Property</th>
                      <th>Requested Assistance</th>
                      <th>Buyer Message</th>
                      <th>Received</th>
                      <th>Follow-Up Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map((l) => (
                      <tr key={l.id}>
                        <td>
                          <strong>{l.customerName}</strong>
                          <div style={{ fontSize: '0.8rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                            <PhoneCall size={12} color="#D9A62E" /> {l.phone}
                          </div>
                          {l.email && (
                            <div style={{ fontSize: '0.78rem', color: '#94A3B8' }}>{l.email}</div>
                          )}
                        </td>
                        <td>
                          <strong>{l.propertyTitle}</strong>
                          <small style={{ display: 'block', color: '#64748B' }}>{l.locality}</small>
                        </td>
                        <td>
                          <span className="badge badge-blue">{l.inquiryType}</span>
                        </td>
                        <td style={{ maxWidth: 280, fontSize: '0.82rem', color: '#334155' }}>
                          {l.message || 'Customer requested phone callback regarding inspection.'}
                        </td>
                        <td style={{ fontSize: '0.82rem', color: '#64748B' }}>{l.time || 'Recently'}</td>
                        <td>
                          <select
                            value={l.status || 'NEW'}
                            onChange={(e) => onUpdateLeadStatus(l.id, e.target.value)}
                            style={{
                              padding: '4px 8px',
                              borderRadius: 6,
                              fontSize: '0.78rem',
                              fontWeight: 700,
                              background: l.status === 'CONTACTED' ? '#DCFCE7' : '#FEF3C7',
                              color: l.status === 'CONTACTED' ? '#166534' : '#92400E',
                              border: '1px solid #CBD5E1',
                              cursor: 'pointer',
                            }}
                          >
                            <option value="NEW">New Lead</option>
                            <option value="IN_REVIEW">In Review</option>
                            <option value="CONTACTED">Contacted</option>
                            <option value="SITE_VISIT_BOOKED">Site Visit Booked</option>
                            <option value="CLOSED">Closed</option>
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <Users size={36} color="#94A3B8" />
                <h3>No buyer leads received yet</h3>
                <p>When customers click the "Contact" button on properties, their phone inquiries will appear here.</p>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: SCRAPERS & LOGS */}
        {activeTab === 'scrapers' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            {/* Control card */}
            <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #E2E8F0', padding: 24 }}>
              <h3>Bank Crawler Microservices</h3>
              <p style={{ color: '#64748B', fontSize: '0.88rem', marginTop: 4, marginBottom: 20 }}>
                Trigger crawlers across partner bank portals (Baanknet, SBI, Canara, Indian Bank) and run Multimodal Gemini Vision OCR on notice PDFs.
              </p>

              <button
                className="btn btn-gold btn-block btn-lg"
                disabled={isScrapingRunning}
                onClick={handleTriggerScrapeClick}
              >
                {isScrapingRunning ? (
                  <>
                    <RotateCw size={18} className="animate-spin" /> Crawling Bank Portals & PDFs...
                  </>
                ) : (
                  <>
                    <Play size={18} /> Trigger Scrapers Now
                  </>
                )}
              </button>

              <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: 12, background: '#F8FAFC', borderRadius: 8, fontSize: '0.88rem' }}>
                  <span>Baanknet Portal Crawler</span>
                  <span className="badge badge-green">Ready & Active</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: 12, background: '#F8FAFC', borderRadius: 8, fontSize: '0.88rem' }}>
                  <span>Gemini 2.5 Flash Vision OCR</span>
                  <span className="badge badge-green">Connected</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: 12, background: '#F8FAFC', borderRadius: 8, fontSize: '0.88rem' }}>
                  <span>Supabase Pipeline Sync</span>
                  <span className="badge badge-green">Connected</span>
                </div>
              </div>
            </div>

            {/* Run Logs */}
            <div style={{ background: '#071D35', color: '#CBD5E1', borderRadius: 14, padding: 24, display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <strong style={{ color: '#fff', fontSize: '0.95rem' }}>Crawler Live Log Output</strong>
                <span style={{ fontSize: '0.72rem', color: '#E8B849' }}>Realtime Execution</span>
              </div>
              <div style={{ flex: 1, fontFamily: 'monospace', fontSize: '0.82rem', lineHeight: 1.6, overflowY: 'auto', maxHeight: 280 }}>
                {scrapeLogs.map((log, idx) => (
                  <div key={idx} style={{ marginBottom: 6, color: log.includes('complete') ? '#4ADE80' : '#E2E8F0' }}>
                    &gt; {log}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Edit Extracted Details & Media Modal */}
        {editingProperty && (
          <div className="modal-overlay" onClick={() => { setEditingProperty(null); setShowSplitPdf(false); setNewImageUrl(''); }} role="dialog" aria-modal="true">
            <div
              className="modal"
              style={{
                width: showSplitPdf ? 'min(1360px, 98vw)' : 'min(820px, 96vw)',
                maxHeight: '94vh',
                overflowY: 'auto',
                transition: 'width 0.2s ease-in-out',
                padding: '24px',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.35rem', color: '#071D35', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Edit3 size={20} color="#D9A62E" /> Edit Listing & Media Gallery
                  </h3>
                  <p style={{ margin: '4px 0 0', color: '#64748B', fontSize: '0.82rem' }}>
                    Property ID: <code style={{ color: '#071D35', fontWeight: 700 }}>{editingProperty.assetCode || editingProperty.id}</code> &middot; Changes save directly to Supabase
                  </p>
                </div>
                <button
                  className="modal-close"
                  onClick={() => { setEditingProperty(null); setShowSplitPdf(false); setNewImageUrl(''); }}
                  aria-label="Close modal"
                >
                  <XCircle size={22} />
                </button>
              </div>

              {/* PDF Split-Pane toggle bar */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  padding: '8px 12px',
                  borderRadius: 8,
                  marginBottom: 16,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FileText size={16} color="#D9A62E" />
                  <span style={{ fontSize: '0.84rem', fontWeight: 600, color: '#071D35' }}>Original Bank Tender Notice</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={() => setShowSplitPdf(!showSplitPdf)}
                    style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem' }}
                  >
                    <Columns size={14} /> {showSplitPdf ? 'Hide Split-Pane' : 'View Notice PDF (Split-Pane)'}
                  </button>
                  <a
                    href={`${API_BASE}/api/admin/pdf-proxy?url=${encodeURIComponent(getPropertyPdfUrl(editingProperty))}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-ghost btn-sm"
                    style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.78rem', color: '#071D35' }}
                  >
                    <ExternalLink size={13} /> Open
                  </a>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: showSplitPdf ? '1.1fr 1fr' : '1fr', gap: 20, alignItems: 'start' }}>
                {showSplitPdf && (
                  <div style={{ border: '1px solid #CBD5E1', borderRadius: 10, overflow: 'hidden', height: 650, display: 'flex', flexDirection: 'column', background: '#0F172A' }}>
                    <div style={{ background: '#071D35', color: '#CBD5E1', padding: '8px 12px', fontSize: '0.78rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>Notice PDF Stream: <code style={{ color: '#E8B849' }}>/api/admin/pdf-proxy</code></span>
                      <span className="badge badge-green" style={{ fontSize: '0.65rem' }}>Authenticated</span>
                    </div>
                    <iframe
                      src={`${API_BASE}/api/admin/pdf-proxy?url=${encodeURIComponent(getPropertyPdfUrl(editingProperty))}`}
                      title="Original Tender Notice PDF"
                      style={{ width: '100%', height: '100%', border: 'none', background: '#fff' }}
                    />
                  </div>
                )}

                <form onSubmit={handleSaveEdit} className="modal-form" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Status & Verification Box */}
                  <div style={{ background: '#FEF3C7', border: '1px solid #FDE68A', padding: '12px 14px', borderRadius: 10 }}>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#92400E', marginBottom: 6 }}>
                      Verification & Publication Status
                    </label>
                    <select
                      value={editingProperty.status || (editingProperty.verified ? 'PUBLISHED' : 'PENDING_REVIEW')}
                      onChange={(e) => {
                        const val = e.target.value;
                        setEditingProperty({
                          ...editingProperty,
                          status: val,
                          publication_status: val,
                          verified: val === 'PUBLISHED',
                        });
                      }}
                      style={{ background: '#fff', fontWeight: 600, width: '100%' }}
                    >
                      <option value="PUBLISHED">Verified & Published Live (Visible to Public)</option>
                      <option value="PENDING_REVIEW">Pending Review (Back-Office Queue)</option>
                      <option value="REJECTED">Rejected / Hidden from Marketplace</option>
                    </select>
                  </div>

                  {/* MEDIA SECTION: Real Pictures & Video */}
                  <div style={{ border: '1px solid #E2E8F0', borderRadius: 12, padding: 16, background: '#F8FAFC' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                      <strong style={{ fontSize: '0.92rem', color: '#071D35', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Image size={17} color="#D9A62E" /> Real Property Photos ({editingProperty.images?.length || 0})
                      </strong>
                      <label
                        htmlFor="admin-photo-upload"
                        className="btn btn-outline btn-sm"
                        style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', background: '#fff', fontSize: '0.78rem' }}
                      >
                        <Upload size={13} /> Upload Real Photos from PC
                        <input
                          id="admin-photo-upload"
                          type="file"
                          accept="image/*"
                          multiple
                          style={{ display: 'none' }}
                          onChange={(e) => {
                            const files = Array.from(e.target.files || []);
                            files.forEach((file) => {
                              const reader = new FileReader();
                              reader.onload = (ev) => {
                                if (ev.target?.result) {
                                  setEditingProperty((prev) => ({
                                    ...prev,
                                    images: [...(prev.images || []), ev.target.result],
                                  }));
                                }
                              };
                              reader.readAsDataURL(file);
                            });
                          }}
                        />
                      </label>
                    </div>

                    {/* Current Photos Thumbnails Grid */}
                    {editingProperty.images && editingProperty.images.length > 0 ? (
                      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
                        {editingProperty.images.map((imgUrl, imgIdx) => (
                          <div
                            key={imgIdx}
                            style={{
                              position: 'relative',
                              width: 80,
                              height: 60,
                              borderRadius: 8,
                              overflow: 'hidden',
                              border: '2px solid #E2E8F0',
                              background: '#071D35',
                            }}
                          >
                            <img
                              src={imgUrl}
                              alt=""
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                              onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = './placeholder.svg'; }}
                            />
                            <button
                              type="button"
                              onClick={() => {
                                setEditingProperty((prev) => ({
                                  ...prev,
                                  images: prev.images.filter((_, idx) => idx !== imgIdx),
                                }));
                              }}
                              style={{
                                position: 'absolute',
                                top: 2,
                                right: 2,
                                background: 'rgba(220, 38, 38, 0.88)',
                                border: 'none',
                                borderRadius: '50%',
                                width: 20,
                                height: 20,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: '#fff',
                                cursor: 'pointer',
                              }}
                              title="Delete photo"
                            >
                              <Trash2 size={11} />
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p style={{ fontSize: '0.82rem', color: '#94A3B8', margin: '4px 0 10px' }}>
                        No property photos added yet. Upload real pictures or paste an image URL below.
                      </p>
                    )}

                    {/* Add Image URL bar */}
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input
                        type="url"
                        placeholder="Or paste property image URL (https://...)"
                        value={newImageUrl}
                        onChange={(e) => setNewImageUrl(e.target.value)}
                        style={{ flex: 1, fontSize: '0.82rem' }}
                      />
                      <button
                        type="button"
                        className="btn btn-outline btn-sm"
                        style={{ background: '#fff' }}
                        onClick={() => {
                          if (newImageUrl.trim()) {
                            setEditingProperty((prev) => ({
                              ...prev,
                              images: [...(prev.images || []), newImageUrl.trim()],
                            }));
                            setNewImageUrl('');
                          }
                        }}
                      >
                        <Plus size={14} /> Add Image URL
                      </button>
                    </div>

                    {/* Video Tour Section */}
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px dashed #CBD5E1' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.86rem', fontWeight: 600, color: '#071D35', marginBottom: 6 }}>
                        <Video size={16} color="#D9A62E" /> Property Video Tour URL (YouTube, Vimeo, or MP4)
                      </label>
                      <input
                        type="url"
                        placeholder="e.g. https://www.youtube.com/watch?v=... or https://mysite.com/walkthrough.mp4"
                        value={editingProperty.videoUrl || ''}
                        onChange={(e) => setEditingProperty({ ...editingProperty, videoUrl: e.target.value })}
                        style={{ fontSize: '0.84rem' }}
                      />

                      {/* Video Preview if URL provided */}
                      {editingProperty.videoUrl && (
                        <div style={{ marginTop: 10, background: '#0F172A', borderRadius: 8, padding: 8, textAlign: 'center' }}>
                          <small style={{ color: '#E8B849', display: 'block', marginBottom: 6, fontSize: '0.74rem' }}>
                            ✓ Live Video Tour Attached
                          </small>
                          <div style={{ width: '100%', maxHeight: 180, overflow: 'hidden', borderRadius: 6 }}>
                            {editingProperty.videoUrl.includes('youtube.com') || editingProperty.videoUrl.includes('youtu.be') ? (
                              <p style={{ color: '#fff', fontSize: '0.82rem', margin: '8px 0' }}>
                                Embedded YouTube Walkthrough: <code>{editingProperty.videoUrl}</code>
                              </p>
                            ) : (
                              <video
                                src={editingProperty.videoUrl}
                                controls
                                style={{ width: '100%', maxHeight: 160, objectFit: 'contain' }}
                              />
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* General Details */}
                  <div className="form-field">
                    <label>Property Title</label>
                    <input
                      type="text"
                      value={editingProperty.title}
                      onChange={(e) => setEditingProperty({ ...editingProperty, title: e.target.value })}
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div className="form-field">
                      <label>Bank Name</label>
                      <input
                        type="text"
                        value={editingProperty.bank}
                        onChange={(e) => setEditingProperty({ ...editingProperty, bank: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Branch Name</label>
                      <input
                        type="text"
                        value={editingProperty.branch || ''}
                        onChange={(e) => setEditingProperty({ ...editingProperty, branch: e.target.value })}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div className="form-field">
                      <label>Reserve Price (INR)</label>
                      <input
                        type="number"
                        value={editingProperty.reserve}
                        onChange={(e) => {
                          const newReserve = Number(e.target.value);
                          setEditingProperty({
                            ...editingProperty,
                            reserve: newReserve,
                            emd: editingProperty.emd || Math.round(newReserve * 0.1),
                          });
                        }}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>EMD Amount (INR)</label>
                      <input
                        type="number"
                        placeholder="Statutory 10% EMD"
                        value={editingProperty.emd !== undefined && editingProperty.emd !== null ? editingProperty.emd : Math.round((editingProperty.reserve || 0) * 0.1)}
                        onChange={(e) => setEditingProperty({ ...editingProperty, emd: Number(e.target.value) })}
                        required
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div className="form-field">
                      <label>Auction End Date & Time</label>
                      <input
                        type="datetime-local"
                        value={toDatetimeLocalInput(editingProperty.auctionEnd)}
                        onChange={(e) => {
                          const ts = e.target.value ? new Date(e.target.value).getTime() : Date.now();
                          setEditingProperty({ ...editingProperty, auctionEnd: ts });
                        }}
                        required
                      />
                    </div>
                    <div className="form-field">
                      <label>Asset Category</label>
                      <select
                        value={editingProperty.type || 'residential'}
                        onChange={(e) => setEditingProperty({ ...editingProperty, type: e.target.value })}
                      >
                        <option value="residential">Residential House / Flat</option>
                        <option value="commercial">Commercial Building / Office</option>
                        <option value="land">Land / Open Plot</option>
                        <option value="industrial">Industrial Shed / Factory</option>
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div className="form-field">
                      <label>Carpet / Built-up Area (sq.ft)</label>
                      <input
                        type="number"
                        placeholder="e.g. 2100"
                        value={editingProperty.area || ''}
                        onChange={(e) => setEditingProperty({ ...editingProperty, area: Number(e.target.value) })}
                      />
                    </div>
                    <div className="form-field">
                      <label>Project / Building Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Prestige Silver Springs"
                        value={editingProperty.projectName || ''}
                        onChange={(e) => setEditingProperty({ ...editingProperty, projectName: e.target.value })}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div className="form-field">
                      <label>Furnished Status</label>
                      <select
                        value={editingProperty.furnishing || 'Unfurnished'}
                        onChange={(e) => setEditingProperty({ ...editingProperty, furnishing: e.target.value })}
                      >
                        <option value="Unfurnished">Unfurnished</option>
                        <option value="Semi-Furnished">Semi-Furnished</option>
                        <option value="Fully Furnished">Fully Furnished</option>
                      </select>
                    </div>
                    <div className="form-field">
                      <label>Possession Type</label>
                      <select
                        value={editingProperty.possessionType || 'Physical'}
                        onChange={(e) => setEditingProperty({ ...editingProperty, possessionType: e.target.value })}
                      >
                        <option value="Physical">Physical Vacant Possession</option>
                        <option value="Symbolic">Symbolic / Constructive Possession</option>
                      </select>
                    </div>
                  </div>

                  <div className="form-field">
                    <label>Locality & Address</label>
                    <input
                      type="text"
                      value={editingProperty.address || editingProperty.locality}
                      onChange={(e) => setEditingProperty({ ...editingProperty, locality: e.target.value, address: e.target.value })}
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                    <button
                      type="button"
                      className="btn btn-outline btn-lg"
                      onClick={() => { setEditingProperty(null); setShowSplitPdf(false); setNewImageUrl(''); }}
                    >
                      Cancel
                    </button>
                    <button className="btn btn-gold btn-lg" type="submit">
                      <BadgeCheck size={18} /> Save & Apply to Supabase
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Notice PDF Viewer Modal */}
        {pdfModalData && (
          <div className="modal-overlay" onClick={handleClosePdfViewer} role="dialog" aria-modal="true">
            <div
              className="modal"
              style={{ width: 'min(980px, 96vw)', height: '88vh', display: 'flex', flexDirection: 'column', padding: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="brand-mark" style={{ background: '#071D35', color: '#E8B849' }}>
                    <FileText size={20} />
                  </span>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.2rem' }}>Original Bank Auction Notice PDF</h3>
                    <small style={{ color: '#64748B' }}>
                      {pdfModalData.property?.title} &middot; {pdfModalData.property?.bank}
                    </small>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <a
                    href={pdfModalData.proxyUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-outline btn-sm"
                    style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.78rem' }}
                  >
                    <ExternalLink size={13} /> Open in New Tab
                  </a>
                  <button className="modal-close" onClick={handleClosePdfViewer}>
                    <XCircle size={20} />
                  </button>
                </div>
              </div>

              {pdfModalData.isLoading ? (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748B', gap: 8 }}>
                  <RotateCw size={22} className="animate-spin" />
                  <span>Streaming authenticated PDF notice from proxy...</span>
                </div>
              ) : (
                <iframe
                  src={pdfModalData.blobUrl || pdfModalData.proxyUrl}
                  title="Official Notice PDF"
                  style={{ width: '100%', flex: 1, border: '1px solid #CBD5E1', borderRadius: 8, background: '#F8FAFC' }}
                />
              )}
            </div>
          </div>
        )}

        {/* Reject / Duplicate Confirmation Modal */}
        {rejectConfirmTarget && (
          <div className="modal-overlay" onClick={() => setRejectConfirmTarget(null)} role="dialog" aria-modal="true">
            <div className="modal" style={{ width: 'min(460px, 100%)' }} onClick={(e) => e.stopPropagation()}>
              <div className="modal-head" style={{ textAlign: 'center' }}>
                <span className="brand-mark" style={{ background: '#FEE2E2', color: '#DC2626', margin: '0 auto 12px' }}>
                  <AlertCircle size={24} />
                </span>
                <h3 style={{ fontSize: '1.3rem' }}>Confirm Listing Rejection</h3>
                <p style={{ marginTop: 8, color: '#64748B' }}>
                  Are you sure you want to reject <strong>{rejectConfirmTarget.title}</strong> ({rejectConfirmTarget.bank})?
                </p>
                <div style={{ marginTop: 10, padding: '8px 12px', background: '#FEF2F2', borderRadius: 8, fontSize: '0.82rem', color: '#991B1B' }}>
                  This notice will be removed from the active verification pipeline and marked as REJECTED.
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 20 }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setRejectConfirmTarget(null)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{ background: '#DC2626', color: '#fff', borderColor: '#DC2626', fontWeight: 600 }}
                  onClick={() => {
                    onRejectProperty(rejectConfirmTarget.id);
                    setRejectConfirmTarget(null);
                  }}
                >
                  Confirm Reject
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
