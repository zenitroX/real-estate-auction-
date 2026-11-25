import { INITIAL_PROPERTIES, GALLERY_POOL } from './propertiesData';
import { supabase } from '../lib/supabaseClient';

// Support external backend URL when frontend is hosted separately (e.g. Vercel -> Render)
export const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const ENABLE_DEMO_DATA = import.meta.env.DEV && import.meta.env.VITE_ENABLE_DEMO_DATA === 'true';

export function getAdminAuthHeader() {
  try {
    const sess = sessionStorage.getItem('skandx_admin_session');
    if (sess) {
      const parsed = JSON.parse(sess);
      if (parsed.token) return { Authorization: `Bearer ${parsed.token}` };
    }
  } catch {
    // Ignore session parse error
  }
  return {};
}

function mapAssetCategoryToUiType(assetCategory) {
  const raw = String(assetCategory || '').toLowerCase();
  if (raw.includes('commercial') || raw.includes('office') || raw.includes('shop')) return 'commercial';
  if (raw.includes('plot') || raw.includes('land') || raw.includes('agricultural')) return 'land';
  if (raw.includes('industrial') || raw.includes('shed') || raw.includes('factory')) return 'industrial';
  return 'residential';
}

function mapAuctionItem(item, index) {
  const reserve = item.reserve_price_inr != null ? Number(item.reserve_price_inr) : null;
  const emd = item.emd_amount_inr != null ? Number(item.emd_amount_inr) : null;
  const auctionTime = item.auction_date ? new Date(item.auction_date).getTime() : null;
  const daysAhead = auctionTime != null ? (auctionTime - Date.now()) / 86400000 : null;
  const type = mapAssetCategoryToUiType(item.asset_category);
  const localityParts = [item.village_or_locality, item.district, item.state].filter(Boolean);
  const locality = localityParts.length > 0 ? localityParts.join(', ') : 'Tamil Nadu';

  const heroImg = GALLERY_POOL[index % GALLERY_POOL.length];
  const secondaryImg = GALLERY_POOL[(index + 1) % GALLERY_POOL.length];

  return {
    id: String(item.id || `auction-${index}`),
    slug: item.slug || null,
    title: item.property_title || `${item.bank_name || 'Bank'} Auction Property`,
    badge: 'BANK AUCTION',
    type,
    assetCategory: item.asset_category || null,
    possessionType: item.possession_type || null,
    locality,
    district: item.district || null,
    taluk: item.taluk || null,
    pincode: item.pincode || null,
    address: item.area_description || locality,
    bank: item.bank_name || 'Not available',
    branch: item.branch_name || 'Not available',
    assetCode: item.patta_or_door_no || String(item.id || ''),
    contact: '1800 - 202 - SKANDX',
    officer: 'Auction Advisory Desk',
    reserve,
    previousReserve: item.previous_reserve_price_inr != null ? Number(item.previous_reserve_price_inr) : null,
    priceDropPct: item.price_drop_percentage != null ? Number(item.price_drop_percentage) : null,
    increment: item.bid_increment_inr != null ? Number(item.bid_increment_inr) : null,
    emdPct: reserve && emd ? Math.round((emd / reserve) * 100) : null,
    emd,
    emdLastDate: item.emd_last_date || null,
    inspectionDateInfo: item.inspection_date_info || null,
    area: item.area_sqft != null ? Number(item.area_sqft) : null,
    areaDescription: item.area_description || null,
    surveyNumbers: Array.isArray(item.survey_numbers) ? item.survey_numbers : [],
    boundaries: item.boundaries || null,
    daysAhead,
    auctionEnd: auctionTime,
    auctionDateIso: item.auction_date || null,
    featured: index < 4,
    verified: (item.publication_status || item.review_status) === 'PUBLISHED',
    status: item.publication_status || item.review_status || 'PENDING_ADMIN_APPROVAL',
    verifiedDate: item.created_at ? new Date(item.created_at).toLocaleDateString('en-IN') : 'Not yet confirmed',
    images: [heroImg, secondaryImg, GALLERY_POOL[0]],
    desc: item.area_description || `SARFAESI bank auction notice issued by ${item.bank_name || 'authorized bank'}. Review verification status and risk disclosures before participating.`,
    isLiveApi: true,
    sourcePortal: item.source_portal || null,
    sourceUrl: item.source_pdf_url || null,
    biddingPortalUrl: item.bidding_portal_url || null,
    verificationDimensions: item.verification_dimensions || {},
    riskDisclosures: Array.isArray(item.risk_disclosures) ? item.risk_disclosures : [],
    lastSourceConfirmedAt: item.last_source_confirmed_at || null,
  };
}

/**
 * Fetch live bank auction listings for customers (published only, no mock mixing in production).
 */
export async function fetchLiveAuctions(params = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
  });
  const query = qs.toString();
  const endpoint = `${API_BASE}/api/v1/auctions${query ? `?${query}` : ''}`;

  try {
    const res = await fetch(endpoint, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();

    if (json.status === 'success' && Array.isArray(json.data)) {
      const mapped = json.data.map(mapAuctionItem);
      return {
        source: json.source || 'BACKEND_LIVE',
        latencyMs: json.latency_ms || 0,
        properties: mapped,
        error: null,
      };
    }

    throw new Error('Unexpected API response format');
  } catch (err) {
    if (ENABLE_DEMO_DATA) {
      return {
        source: 'DEMO_MODE',
        latencyMs: 0,
        properties: INITIAL_PROPERTIES,
        error: null,
      };
    }
    return {
      source: 'ERROR',
      latencyMs: 0,
      properties: [],
      error: err instanceof Error ? err.message : 'Failed to load auction listings',
    };
  }
}

const OFFLINE_LEADS_KEY = 'skandx_pending_leads';

function getOfflineLeads() {
  try {
    return JSON.parse(localStorage.getItem(OFFLINE_LEADS_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveOfflineLead(lead) {
  try {
    const existing = getOfflineLeads();
    existing.push({ ...lead, queuedAt: Date.now() });
    localStorage.setItem(OFFLINE_LEADS_KEY, JSON.stringify(existing));
  } catch (e) {
    console.warn('Could not cache offline lead', e);
  }
}

export async function flushOfflineLeads() {
  const pending = getOfflineLeads();
  if (!pending.length) return;
  try {
    for (const lead of pending) {
      const res = await fetch(`${API_BASE}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lead),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    }
    localStorage.removeItem(OFFLINE_LEADS_KEY);
  } catch {
    // Keep in storage for next connection
  }
}

/**
 * Admin: Authenticate for admin.skandx.com portal (fails closed on invalid credentials or network error).
 */
export async function loginAdminApi(email, password) {
  const res = await fetch(`${API_BASE}/api/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || data.error || `Login failed (HTTP ${res.status})`);
  }
  return data;
}

export const adminLoginApi = loginAdminApi;

async function getCustomerAuthHeader() {
  if (!supabase) return {};
  try {
    const { data } = await supabase.auth.getSession();
    const token = data?.session?.access_token;
    if (token) return { Authorization: `Bearer ${token}` };
  } catch {
    // Ignore session lookup error
  }
  return {};
}

/**
 * Submit customer inquiry / advisor connection request via POST /api/v1/leads.
 */
export async function submitLeadApi(leadData) {
  const authHeaders = await getCustomerAuthHeader();
  const res = await fetch(`${API_BASE}/api/v1/leads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
    },
    body: JSON.stringify(leadData),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

/**
 * Fetch authenticated customer's own leads via GET /api/v1/me/leads.
 */
export async function fetchMyLeadsApi() {
  const authHeaders = await getCustomerAuthHeader();
  const res = await fetch(`${API_BASE}/api/v1/me/leads`, {
    headers: { ...authHeaders },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

/**
 * Admin: Fetch active advisors from GET /api/admin/advisors.
 */
export async function fetchAdminAdvisorsApi() {
  const res = await fetch(`${API_BASE}/api/admin/advisors`, {
    headers: { ...getAdminAuthHeader() },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

/**
 * Admin: Verify, edit, and publish or reject a scraped property via PATCH /api/admin/properties.
 */
export async function verifyPropertyApi(id, status = 'PUBLISHED', updatedFields = {}) {
  const res = await fetch(`${API_BASE}/api/admin/properties`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAdminAuthHeader(),
    },
    body: JSON.stringify({ id, status, ...updatedFields }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

/**
 * Admin: Persist lead status and optional notes via PATCH /api/admin/leads.
 */
export async function updateLeadStatusApi(id, status, notes = undefined) {
  const body = { id, status };
  if (notes !== undefined) body.notes = notes;
  const res = await fetch(`${API_BASE}/api/admin/leads`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAdminAuthHeader(),
    },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

/**
 * Admin: Trigger on-demand scraper run.
 */
export async function triggerScrapeApi() {
  const res = await fetch(`${API_BASE}/api/scrape/trigger`, {
    method: 'POST',
    headers: {
      ...getAdminAuthHeader(),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

/**
 * Admin: Fetch leads with pagination support.
 */
export async function fetchAdminLeadsApi(limit = 100, offset = 0) {
  const res = await fetch(`${API_BASE}/api/admin/leads?limit=${limit}&offset=${offset}`, {
    headers: {
      ...getAdminAuthHeader(),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.error || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}
