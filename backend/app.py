"""
SKANDX Backend API Server
High-Performance, Multi-Threaded REST API & Supabase Proxy.

Features:
- Decoupled REST API service for public customer browsing and admin verification
- GET /api/auctions : Public endpoint (returns only PUBLISHED / verified properties)
- GET /api/admin/properties : Protected admin verification queue
- POST /api/admin/properties/verify : Approves, updates, & persists property status
- POST /api/contact : Thread-safe public lead capture from "Contact" button (Rate limited)
- GET /api/admin/leads : Protected admin feed of customer inquiries with pagination
- GET /api/admin/pdf-proxy : Protected streaming proxy for remote tender notice PDFs
- POST /api/scrape/trigger : Concurrency-controlled scraper job runner
- Full CORS support with OPTIONS preflight handling
"""

import http.server
import json
import os
import sys
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import hmac
import hashlib
import socket
import ipaddress
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env from backend folder or project root
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

PORT = int(os.getenv("PORT", "8000"))
DATA_DIR = BASE_DIR / "data"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
ADMIN_SECRET = os.getenv("ADMIN_JWT_SECRET", "")
ADMIN_TOKEN_TTL_SECONDS = 28800  # 8 hours

PUBLIC_AUCTION_COLUMNS = (
    "id",
    "property_title",
    "bank_name",
    "branch_name",
    "asset_category",
    "possession_type",
    "survey_numbers",
    "patta_or_door_no",
    "village_or_locality",
    "taluk",
    "district",
    "state",
    "pincode",
    "area_description",
    "area_sqft",
    "boundaries",
    "reserve_price_inr",
    "previous_reserve_price_inr",
    "price_drop_percentage",
    "emd_amount_inr",
    "bid_increment_inr",
    "emd_last_date",
    "inspection_date_info",
    "auction_date",
    "source_portal",
    "source_pdf_url",
    "bidding_portal_url",
    "review_status",
    "publication_status",
    "verification_dimensions",
    "risk_disclosures",
    "slug",
    "last_source_confirmed_at",
    "created_at",
)

ADMIN_EDITABLE_PROPERTY_FIELDS = {
    "title": "property_title",
    "property_title": "property_title",
    "bank": "bank_name",
    "bank_name": "bank_name",
    "branch": "branch_name",
    "branch_name": "branch_name",
    "category": "asset_category",
    "asset_category": "asset_category",
    "possession": "possession_type",
    "possession_type": "possession_type",
    "survey_numbers": "survey_numbers",
    "patta_or_door_no": "patta_or_door_no",
    "locality": "village_or_locality",
    "village_or_locality": "village_or_locality",
    "taluk": "taluk",
    "district": "district",
    "state": "state",
    "pincode": "pincode",
    "area_description": "area_description",
    "area": "area_sqft",
    "areaSqft": "area_sqft",
    "area_sqft": "area_sqft",
    "boundaries": "boundaries",
    "reserve": "reserve_price_inr",
    "reserve_price": "reserve_price_inr",
    "reserve_price_inr": "reserve_price_inr",
    "previous_reserve_price_inr": "previous_reserve_price_inr",
    "price_drop_percentage": "price_drop_percentage",
    "emd": "emd_amount_inr",
    "emd_amount_inr": "emd_amount_inr",
    "bidIncrement": "bid_increment_inr",
    "bid_increment_inr": "bid_increment_inr",
    "emdLastDate": "emd_last_date",
    "emd_last_date": "emd_last_date",
    "inspection_date_info": "inspection_date_info",
    "auctionDate": "auction_date",
    "auction_date": "auction_date",
    "source_portal": "source_portal",
    "sourcePdfUrl": "source_pdf_url",
    "source_pdf_url": "source_pdf_url",
    "biddingPortalUrl": "bidding_portal_url",
    "bidding_portal_url": "bidding_portal_url",
    "reviewNotes": "review_notes",
    "review_notes": "review_notes",
    "publicationStatus": "publication_status",
    "publication_status": "publication_status",
    "verificationDimensions": "verification_dimensions",
    "verification_dimensions": "verification_dimensions",
    "riskDisclosures": "risk_disclosures",
    "risk_disclosures": "risk_disclosures",
}

PUBLIC_VERIFICATION_KEYS = ("status", "reviewed_at", "review_period")

VALID_LEAD_STATUSES = {
    "NEW",
    "IN_REVIEW",
    "SCHEDULED",
    "REQUEST_RECEIVED",
    "CONTACTED",
    "IN_PROGRESS",
    "CLOSED",
}

INQUIRY_TYPE_MAP = {
    "General Auction Guidance": "GENERAL_GUIDANCE",
    "GENERAL_GUIDANCE": "GENERAL_GUIDANCE",
    "Site Inspection": "PHYSICAL_INSPECTION",
    "Physical Property Inspection": "PHYSICAL_INSPECTION",
    "PHYSICAL_INSPECTION": "PHYSICAL_INSPECTION",
    "Document Review": "DOCUMENT_REVIEW",
    "Legal Title Search Report": "DOCUMENT_REVIEW",
    "Download Notice": "GENERAL_GUIDANCE",
    "DOCUMENT_REVIEW": "DOCUMENT_REVIEW",
    "Legal Coordination": "LEGAL_COORDINATION",
    "LEGAL_COORDINATION": "LEGAL_COORDINATION",
    "Auction Guidance": "AUCTION_GUIDANCE",
    "AUCTION_GUIDANCE": "AUCTION_GUIDANCE",
    "Complete Buyer Assistance": "COMPLETE_ASSISTANCE",
    "COMPLETE_ASSISTANCE": "COMPLETE_ASSISTANCE",
}
AGREEMENT_REQUIRED_TYPES = {
    "PHYSICAL_INSPECTION",
    "DOCUMENT_REVIEW",
    "LEGAL_COORDINATION",
    "AUCTION_GUIDANCE",
    "COMPLETE_ASSISTANCE",
}
AGREEMENT_VERSION = "v1.0-proposed"
AGREEMENT_CALCULATION_BASIS = "5% of final successful auction hammer price (proposed; subject to formal written mandate)"
AGREEMENT_COMMISSION_RATE = 5.00

_in_memory_leads = []
_in_memory_agreements = []

def _get_admin_secret() -> str:
    """Return configured ADMIN_JWT_SECRET or fail closed."""
    secret = ADMIN_SECRET or os.getenv("ADMIN_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("ADMIN_JWT_SECRET is not configured.")
    return secret

def serialize_public_auction(row: dict) -> dict:
    """Return only approved public auction fields, stripping borrower/officer PII and internal verification notes."""
    out = {col: row[col] for col in PUBLIC_AUCTION_COLUMNS if col in row}
    dims = out.get("verification_dimensions")
    if isinstance(dims, dict):
        out["verification_dimensions"] = {
            k: {pk: v[pk] for pk in PUBLIC_VERIFICATION_KEYS if pk in v}
            for k, v in dims.items()
            if isinstance(v, dict)
        }
    return out

def _is_published_auction(row: dict) -> bool:
    status = row.get("publication_status") or row.get("review_status") or row.get("status") or "PUBLISHED"
    return status == "PUBLISHED"

def _filter_and_paginate_auctions(data: list, query_params: dict):
    """Apply Phase 1 discovery filters, sorting, and pagination."""
    from datetime import datetime, timezone
    now_ts = time.time()
    include_expired = query_params.get("include_expired", ["false"])[0].lower() in ("true", "1")
    ids_raw = query_params.get("ids", [""])[0].strip()
    ids_filter = {i.strip() for i in ids_raw.split(",") if i.strip()} if ids_raw else None

    q = query_params.get("q", [""])[0].strip().lower()
    district = query_params.get("district", [""])[0].strip().lower()
    prop_type = query_params.get("type", [""])[0].strip().lower()
    bank = query_params.get("bank", [""])[0].strip().lower()
    possession = query_params.get("possession", [""])[0].strip().lower()
    min_price = query_params.get("min_price", [""])[0].strip()
    max_price = query_params.get("max_price", [""])[0].strip()
    deadline = query_params.get("deadline", [""])[0].strip().lower()
    sort_by = query_params.get("sort", ["deadline_asc"])[0].strip().lower()

    def parse_ts(val):
        if not val:
            return None
        try:
            return datetime.fromisoformat(str(val).replace("Z", "+00:00")).timestamp()
        except Exception:
            return None

    filtered = []
    for row in data:
        if not _is_published_auction(row):
            continue
        if ids_filter is not None and str(row.get("id")) not in ids_filter:
            continue
        auc_ts = parse_ts(row.get("auction_date"))
        if not include_expired and auc_ts is not None and auc_ts < now_ts and ids_filter is None:
            continue
        if q:
            hay = " ".join(str(row.get(k) or "") for k in ("property_title", "district", "village_or_locality", "bank_name", "patta_or_door_no")).lower()
            if q not in hay:
                continue
        if district and district != "all" and district not in str(row.get("district") or "").lower():
            continue
        if prop_type and prop_type != "all" and prop_type not in str(row.get("asset_category") or "").lower():
            continue
        if bank and bank != "all" and bank not in str(row.get("bank_name") or "").lower():
            continue
        if possession and possession != "all" and possession not in str(row.get("possession_type") or "").lower():
            continue
        price = float(row.get("reserve_price_inr") or 0)
        if min_price:
            try:
                if price < float(min_price):
                    continue
            except ValueError:
                pass
        if max_price:
            try:
                if price > float(max_price):
                    continue
            except ValueError:
                pass
        if deadline in ("7d", "14d", "30d") and auc_ts is not None:
            days = int(deadline[:-1])
            if auc_ts > now_ts + days * 86400:
                continue
        filtered.append(serialize_public_auction(row))

    if sort_by == "price_asc":
        filtered.sort(key=lambda r: float(r.get("reserve_price_inr") or 0))
    elif sort_by == "price_desc":
        filtered.sort(key=lambda r: float(r.get("reserve_price_inr") or 0), reverse=True)
    elif sort_by == "newest":
        filtered.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    else:
        filtered.sort(key=lambda r: str(r.get("auction_date") or "9999"))

    try:
        page = max(1, int(query_params.get("page", ["1"])[0]))
    except ValueError:
        page = 1
    try:
        limit = min(50, max(1, int(query_params.get("limit", ["20"])[0])))
    except ValueError:
        limit = 20

    total = len(filtered)
    total_pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    return filtered[start:start + limit], {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }

# In-memory auction cache
_cache = {
    "data": None,
    "timestamp": 0
}

class CircuitBreaker:
    """
    In-memory thread-safe circuit breaker pattern for external network calls (Supabase).

    States:
    - CLOSED: Normal operation. Requests to Supabase proceed. Success resets error counters.
    - OPEN: Tripped after failure_threshold (e.g. 3 consecutive timeouts/network errors).
      In this state, external requests to Supabase are IMMEDIATELY bypassed (0ms delay)
      and fall back to local snapshot/cache.
    - HALF_OPEN: After recovery_timeout (e.g. 30 seconds), allows one canary request to test
      if Supabase has recovered. If successful, transitions to CLOSED; if failed, resets the OPEN timer.
    """
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_in_flight = False
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == self.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = self.HALF_OPEN
            return self._state

    def allow_request(self) -> bool:
        """
        Determines whether a remote request should be attempted.
        - In CLOSED: returns True.
        - In OPEN: transitions to HALF_OPEN if recovery_timeout elapsed, allowing one canary.
          Otherwise returns False (bypass external call).
        - In HALF_OPEN: returns True for a single canary request, False for concurrent requests.
        """
        with self._lock:
            now = time.time()
            if self._state == self.OPEN:
                if now - self._last_failure_time >= self.recovery_timeout:
                    self._state = self.HALF_OPEN
                    self._half_open_in_flight = True
                    return True
                return False
            elif self._state == self.HALF_OPEN:
                if not self._half_open_in_flight:
                    self._half_open_in_flight = True
                    return True
                return False
            else:  # CLOSED
                return True

    def record_success(self):
        """Record successful external call: resets failure counter and closes circuit."""
        with self._lock:
            self._failure_count = 0
            self._state = self.CLOSED
            self._half_open_in_flight = False

    def record_failure(self):
        """Record failed external call: increments failure counter and trips or resets OPEN timer."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._half_open_in_flight = False
            if self._state == self.HALF_OPEN:
                self._state = self.OPEN
            elif self._failure_count >= self.failure_threshold:
                self._state = self.OPEN

    def trip(self):
        """Manually trip circuit to OPEN state."""
        with self._lock:
            self._state = self.OPEN
            self._last_failure_time = time.time()
            self._half_open_in_flight = False

    def reset(self):
        """Manually reset circuit to CLOSED state with cleared counters."""
        with self._lock:
            self._state = self.CLOSED
            self._failure_count = 0
            self._last_failure_time = 0.0
            self._half_open_in_flight = False

# Global circuit breaker instance
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

# Thread synchronization locks
_leads_lock = threading.Lock()
_auctions_lock = threading.Lock()
_crawler_lock = threading.Lock()
_crawler_running = False
_rate_limit_lock = threading.Lock()
_contact_rate_limits = {}  # ip -> list of timestamps
_login_rate_limits = {}  # ip -> list of timestamps

def check_login_rate_limit(client_ip: str, limit: int = 5, window_seconds: int = 60, prune_seconds: int = 120) -> bool:
    """
    Thread-safe sliding window rate limiter for POST /api/admin/login.
    Allows up to `limit` requests within `window_seconds`.
    Prunes timestamps older than `prune_seconds` to reclaim memory.
    Returns True if request allowed, False if exceeded.
    """
    now = time.time()
    cutoff = now - window_seconds
    prune_cutoff = now - prune_seconds

    with _rate_limit_lock:
        timestamps = _login_rate_limits.get(client_ip, [])
        # Prune timestamps older than prune_seconds (120s)
        timestamps = [ts for ts in timestamps if ts > prune_cutoff]

        # Count active window timestamps (60s)
        recent_count = sum(1 for ts in timestamps if ts > cutoff)

        if recent_count >= limit:
            _login_rate_limits[client_ip] = timestamps
            return False

        timestamps.append(now)
        _login_rate_limits[client_ip] = timestamps

        # Periodic dictionary cleanup of dormant IPs
        if len(_login_rate_limits) > 200:
            stale_keys = [k for k, v in _login_rate_limits.items() if not v or v[-1] <= prune_cutoff]
            for k in stale_keys:
                del _login_rate_limits[k]

        return True

def check_contact_rate_limit(client_ip: str, limit: int = 15, window_seconds: int = 60, prune_seconds: int = 120) -> bool:
    """
    Thread-safe sliding window rate limiter for POST /api/contact.
    Allows up to `limit` requests within `window_seconds`.
    Prunes timestamps older than `prune_seconds` to reclaim memory.
    Returns True if request allowed, False if exceeded.
    """
    now = time.time()
    cutoff = now - window_seconds
    prune_cutoff = now - prune_seconds

    with _rate_limit_lock:
        timestamps = _contact_rate_limits.get(client_ip, [])
        # Prune timestamps older than prune_seconds (120s)
        timestamps = [ts for ts in timestamps if ts > prune_cutoff]

        # Count active window timestamps (60s)
        recent_count = sum(1 for ts in timestamps if ts > cutoff)

        if recent_count >= limit:
            _contact_rate_limits[client_ip] = timestamps
            return False

        timestamps.append(now)
        _contact_rate_limits[client_ip] = timestamps

        # Periodic dictionary cleanup of dormant IPs
        if len(_contact_rate_limits) > 200:
            stale_keys = [k for k, v in _contact_rate_limits.items() if not v or v[-1] <= prune_cutoff]
            for k in stale_keys:
                del _contact_rate_limits[k]

        return True

def generate_admin_token() -> str:
    """Generate cryptographically signed, timestamped admin session token (valid 8h)."""
    secret = _get_admin_secret()
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode("utf-8"), ts.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"skandx-adm-{ts}-{sig}"

def is_safe_url(url_str: str) -> bool:
    """SSRF protection: verify URL scheme and ensure IP is not private, loopback, or cloud-metadata."""
    try:
        parsed = urllib.parse.urlparse(url_str)
        if parsed.scheme.lower() not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Explicit cloud metadata hostnames
        if hostname.lower() in ("169.254.169.254", "metadata.google.internal", "instance-data"):
            return False

        addr_info = socket.getaddrinfo(hostname, None)
        is_testing = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("ALLOW_LOCAL_PROXY", "").lower() in ("true", "1"))

        for item in addr_info:
            ip_str = item[4][0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
            if ip.is_private and not is_testing:
                return False
            if ip.is_loopback and not is_testing:
                return False
        return True
    except Exception:
        return False

class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Enforce SSRF safe URL inspection on HTTP redirects."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_safe_url(newurl):
            raise urllib.error.HTTPError(newurl, 400, "Redirect to forbidden network address blocked.", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def verify_admin_token(token: str) -> bool:
    """Validate HMAC signature and expiration window for admin token."""
    if not token or not token.startswith("skandx-adm-"):
        return False
    parts = token.split("-")
    if len(parts) != 4:  # ["skandx", "adm", ts, sig]
        return False
    ts_str, sig = parts[2], parts[3]
    try:
        secret = _get_admin_secret()
        ts = int(ts_str)
        # Token valid for 8 hours (28,800s), reject future tokens with >60s clock skew
        if time.time() - ts > ADMIN_TOKEN_TTL_SECONDS or time.time() < ts - 60:
            return False
        expected = hmac.new(secret.encode("utf-8"), ts_str.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False

def load_leads(limit=None, offset=0):
    """Thread-safe lead retrieval from Supabase (with in-memory fallback when offline/unconfigured)."""
    with _leads_lock:
        leads = []

        # 1. Authoritative fetch from Supabase if configured and breaker allows
        if SUPABASE_URL and SUPABASE_KEY and circuit_breaker.allow_request():
            try:
                url = f"{SUPABASE_URL}/rest/v1/customer_leads?select=*&order=created_at.desc&limit=200"
                req = urllib.request.Request(
                    url,
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Accept": "application/json"
                    }
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    sb_leads = json.loads(response.read().decode("utf-8"))
                    circuit_breaker.record_success()
                    if isinstance(sb_leads, list):
                        leads = [
                            {
                                "id": item.get("id"),
                                "customerName": item.get("customer_name"),
                                "phone": item.get("phone"),
                                "email": item.get("email"),
                                "propertyId": item.get("property_id"),
                                "propertyTitle": item.get("property_title"),
                                "inquiryType": item.get("inquiry_type"),
                                "message": item.get("notes"),
                                "createdAt": item.get("created_at"),
                                "status": item.get("status", "NEW")
                            }
                            for item in sb_leads
                        ]
            except Exception:
                circuit_breaker.record_failure()

        # 2. In-memory fallback only when Supabase is unconfigured or offline
        if not leads and _in_memory_leads:
            leads = list(reversed(_in_memory_leads))

        total = len(leads)
        if offset > 0:
            leads = leads[offset:]
        if limit is not None and limit > 0:
            leads = leads[:limit]
        return leads, total

def save_lead(lead_data):
    """Thread-safe save for customer inquiries to Supabase (or in-memory when unconfigured)."""
    with _leads_lock:
        lead_data["id"] = f"lead-{int(time.time() * 1000)}"
        lead_data["createdAt"] = int(time.time())
        lead_data["status"] = lead_data.get("status", "NEW")
        _in_memory_leads.append(dict(lead_data))

        if circuit_breaker.state == CircuitBreaker.OPEN:
            return lead_data

        if SUPABASE_URL and SUPABASE_KEY and circuit_breaker.allow_request():
            try:
                supabase_headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }
                lead_row = {
                    "customer_name": lead_data.get("customerName", "Interested Bidder"),
                    "phone": lead_data.get("phone", ""),
                    "email": lead_data.get("email", ""),
                    "property_id": str(lead_data.get("propertyId", "")),
                    "property_title": lead_data.get("propertyTitle", ""),
                    "inquiry_type": lead_data.get("inquiryType", "General Inquiry"),
                    "notes": lead_data.get("message", ""),
                    "status": lead_data["status"],
                }
                req = urllib.request.Request(
                    f"{SUPABASE_URL}/rest/v1/customer_leads",
                    data=json.dumps(lead_row).encode("utf-8"),
                    headers=supabase_headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    inserted = json.loads(resp.read().decode("utf-8"))
                    if isinstance(inserted, list) and inserted:
                        lead_data["id"] = inserted[0].get("id", lead_data["id"])
                circuit_breaker.record_success()
            except Exception:
                circuit_breaker.record_failure()

        return lead_data

def verify_customer_jwt(auth_header: str):
    """Verify Supabase customer JWT against {SUPABASE_URL}/auth/v1/user and return user_id or None."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token or not SUPABASE_URL:
        return None
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            user_obj = json.loads(resp.read().decode("utf-8"))
            return user_obj.get("id")
    except Exception:
        return None

def create_lead_and_agreement(user_id: str, body: dict, client_ip: str, user_agent: str):
    """Create lead (and service agreement when required) atomically, enforcing active-lead dedup."""
    prop_id = str(body.get("propertyId") or "").strip()
    raw_type = str(body.get("inquiryType") or "General Auction Guidance").strip()
    canonical_type = INQUIRY_TYPE_MAP.get(raw_type)
    if not canonical_type:
        return {"error": "Validation failed", "message": "Unsupported inquiryType."}, 400

    require_agreement = canonical_type in AGREEMENT_REQUIRED_TYPES
    accepted_name = str(body.get("acceptedName") or body.get("customerName") or "").strip()
    if require_agreement and (not body.get("agreementAccepted") or not accepted_name):
        return {
            "error": "Agreement required",
            "message": "Explicit acceptance of the proposed 5% service agreement is required for substantive assistance.",
        }, 400

    with _leads_lock:
        for existing in _in_memory_leads:
            if (
                existing.get("userId") == user_id
                and str(existing.get("propertyId")) == prop_id
                and existing.get("status") != "CLOSED"
            ):
                return {"error": "Duplicate lead", "message": "An active request already exists for this property."}, 409

        if SUPABASE_URL and SUPABASE_KEY and circuit_breaker.allow_request():
            try:
                rpc_payload = {
                    "p_user_id": user_id,
                    "p_property_id": prop_id,
                    "p_property_title": body.get("propertyTitle", "Property Auction"),
                    "p_customer_name": body.get("customerName", "SKANDX Buyer"),
                    "p_phone": body.get("phone", ""),
                    "p_email": body.get("email", ""),
                    "p_preferred_contact": body.get("preferredContact", "PHONE"),
                    "p_inquiry_type": canonical_type,
                    "p_notes": body.get("message", ""),
                    "p_require_agreement": require_agreement,
                    "p_commission_rate": AGREEMENT_COMMISSION_RATE,
                    "p_calculation_basis": AGREEMENT_CALCULATION_BASIS,
                    "p_agreement_version": AGREEMENT_VERSION,
                    "p_accepted_name": accepted_name,
                    "p_ip": client_ip,
                    "p_ua": user_agent[:250],
                }
                req = urllib.request.Request(
                    f"{SUPABASE_URL}/rest/v1/rpc/create_lead_with_agreement",
                    data=json.dumps(rpc_payload).encode("utf-8"),
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    rpc_res = json.loads(resp.read().decode("utf-8"))
                circuit_breaker.record_success()
                return {
                    "status": "success",
                    "leadId": rpc_res.get("lead_id"),
                    "leadCode": rpc_res.get("lead_code"),
                    "agreementId": rpc_res.get("agreement_id"),
                    "leadStatus": "REQUEST_RECEIVED",
                }, 201
            except urllib.error.HTTPError as he:
                if he.code == 409 or "23505" in he.read().decode("utf-8", errors="ignore"):
                    return {"error": "Duplicate lead", "message": "An active request already exists for this property."}, 409
                circuit_breaker.record_failure()
            except Exception:
                circuit_breaker.record_failure()

        lead_id = f"lead-{int(time.time() * 1000)}"
        lead_code = f"SK-{int(time.time()) % 1000000:06d}"
        record = {
            "id": lead_id,
            "leadCode": lead_code,
            "userId": user_id,
            "customerName": body.get("customerName", "SKANDX Buyer"),
            "phone": body.get("phone", ""),
            "email": body.get("email", ""),
            "propertyId": prop_id,
            "propertyTitle": body.get("propertyTitle", "Property Auction"),
            "inquiryType": canonical_type,
            "message": body.get("message", ""),
            "status": "REQUEST_RECEIVED",
            "createdAt": int(time.time()),
        }
        _in_memory_leads.append(record)
        agreement_id = None
        if require_agreement:
            agreement_id = f"agr-{int(time.time() * 1000)}"
            _in_memory_agreements.append({
                "id": agreement_id,
                "userId": user_id,
                "propertyId": prop_id,
                "leadId": lead_id,
                "commissionRatePct": AGREEMENT_COMMISSION_RATE,
                "agreementVersion": AGREEMENT_VERSION,
                "acceptedName": accepted_name,
            })
        return {
            "status": "success",
            "leadId": lead_id,
            "leadCode": lead_code,
            "agreementId": agreement_id,
            "leadStatus": "REQUEST_RECEIVED",
        }, 201

def persist_lead_update(lead_id, new_status, notes=None, assigned_advisor_id=None):
    """Persist admin lead status, advisor assignment, and optional notes."""
    with _leads_lock:
        for item in _in_memory_leads:
            if str(item.get("id")) == str(lead_id):
                item["status"] = new_status
                if notes is not None:
                    item["message"] = notes
                if assigned_advisor_id is not None:
                    item["assignedAdvisorId"] = assigned_advisor_id

    if SUPABASE_URL and SUPABASE_KEY and lead_id and circuit_breaker.allow_request():
        try:
            encoded_id = urllib.parse.quote(str(lead_id), safe="")
            url = f"{SUPABASE_URL}/rest/v1/customer_leads?id=eq.{encoded_id}"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            body = {"status": new_status}
            if notes is not None:
                body["notes"] = notes
            if assigned_advisor_id is not None:
                body["assigned_advisor_id"] = assigned_advisor_id
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="PATCH")
            with urllib.request.urlopen(req, timeout=5):
                pass
            circuit_breaker.record_success()
        except Exception as e:
            circuit_breaker.record_failure()
            print(f"[Supabase Lead PATCH Notice]: {e}")

def persist_property_update(prop_id, new_status, updated_fields=None):
    """Persist verified status and edited details to local storage and Supabase."""
    updated_fields = updated_fields or {}
    local_file = DATA_DIR / "auctions_data.json"
    
    # 1. Update local snapshot file if present (thread-safe and atomic)
    with _auctions_lock:
        if local_file.exists():
            try:
                items = json.loads(local_file.read_text(encoding="utf-8"))
                matched = False
                for item in items:
                    # Match by string ID or asset_id
                    item_id = str(item.get("id") or item.get("asset_id") or "")
                    if item_id == str(prop_id) or str(prop_id).endswith(item_id):
                        item["review_status"] = new_status
                        item["status"] = new_status
                        item["verified"] = (new_status == "PUBLISHED")
                        # Merge updated fields using canonical mapping
                        field_aliases = {
                            "title": ("title", "property_title"),
                            "property_title": ("title", "property_title"),
                            "reserve": ("reserve", "reserve_price"),
                            "reserve_price": ("reserve", "reserve_price"),
                            "bank": ("bank", "bank_name"),
                            "bank_name": ("bank", "bank_name"),
                            "address": ("address", "locality"),
                            "locality": ("address", "locality"),
                        }
                        for k, v in updated_fields.items():
                            targets = field_aliases.get(k, (k,))
                            for t in targets:
                                item[t] = v
                        matched = True
                        break
                
                if matched:
                    tmp_prop = local_file.with_suffix(".tmp")
                    tmp_prop.write_text(json.dumps(items, indent=2), encoding="utf-8")
                    tmp_prop.replace(local_file)
            except Exception as e:
                print(f"[Persistence Error local_file]: {e}")

    # Circuit breaker fast bypass: if OPEN, update local file and bypass blocking PATCH request
    if circuit_breaker.state == CircuitBreaker.OPEN:
        return

    # 2. Update Supabase table if credentials configured
    if SUPABASE_URL and SUPABASE_KEY and prop_id and circuit_breaker.allow_request():
        try:
            url = f"{SUPABASE_URL}/rest/v1/auction_properties?id=eq.{prop_id}"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            body = {"review_status": new_status}
            for k, v in updated_fields.items():
                db_col = ADMIN_EDITABLE_PROPERTY_FIELDS.get(k)
                if db_col and v is not None:
                    body[db_col] = v
            encoded_id = urllib.parse.quote(str(prop_id), safe="")
            url = f"{SUPABASE_URL}/rest/v1/auction_properties?id=eq.{encoded_id}"
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="PATCH")
            with urllib.request.urlopen(req, timeout=5):
                pass
            circuit_breaker.record_success()
        except Exception as e:
            circuit_breaker.record_failure()
            print(f"[Supabase PATCH Notice]: {e}")

def get_raw_auctions():
    """Retrieve raw auctions from in-memory cache, Supabase, or local snapshot."""
    now = time.time()

    # 1. Fast circuit breaker check: if OPEN, immediately return local snapshot / cache
    if circuit_breaker.state == CircuitBreaker.OPEN:
        fallback_file = DATA_DIR / "auctions_data.json"
        if fallback_file.exists():
            try:
                data = json.loads(fallback_file.read_text(encoding="utf-8"))
                _cache["data"] = data
                _cache["timestamp"] = now
                return data, "CIRCUIT_BREAKER_FALLBACK"
            except Exception:
                pass
        if _cache["data"] is not None:
            return _cache["data"], "CIRCUIT_BREAKER_FALLBACK"
        return [], "CIRCUIT_BREAKER_FALLBACK"

    # 2. In CLOSED state, return memory cache if fresh (<60s)
    # (In HALF_OPEN state, we bypass memory cache to allow canary request to probe Supabase)
    if circuit_breaker.state == CircuitBreaker.CLOSED:
        if _cache["data"] is not None and (now - _cache["timestamp"]) < 60:
            return _cache["data"], "MEMORY_CACHE"

    # 3. Only attempt live cloud network call when Supabase key is configured and breaker allows it
    if SUPABASE_URL and SUPABASE_KEY and circuit_breaker.allow_request():
        url = f"{SUPABASE_URL}/rest/v1/auction_properties?select=*&order=auction_date.desc&limit=100"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "User-Agent": "SKANDX-Backend/2.0"
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                circuit_breaker.record_success()
                _cache["data"] = data
                _cache["timestamp"] = now

                try:
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    (DATA_DIR / "auctions_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
                except Exception:
                    pass

                return data, "SUPABASE_LIVE"
        except Exception as e:
            circuit_breaker.record_failure()
            print(f"[{time.strftime('%H:%M:%S')}] [Supabase Error]: {e}")
            if circuit_breaker.state == CircuitBreaker.OPEN:
                fallback_file = DATA_DIR / "auctions_data.json"
                if fallback_file.exists():
                    try:
                        data = json.loads(fallback_file.read_text(encoding="utf-8"))
                        _cache["data"] = data
                        _cache["timestamp"] = now
                        return data, "CIRCUIT_BREAKER_FALLBACK"
                    except Exception:
                        pass
                if _cache["data"] is not None:
                    return _cache["data"], "CIRCUIT_BREAKER_FALLBACK"
                return [], "CIRCUIT_BREAKER_FALLBACK"

    # Fallback to local snapshot file
    fallback_file = DATA_DIR / "auctions_data.json"
    if fallback_file.exists():
        try:
            data = json.loads(fallback_file.read_text(encoding="utf-8"))
            _cache["data"] = data
            _cache["timestamp"] = now
            return data, "LOCAL_SNAPSHOT"
        except Exception:
            pass

    if _cache["data"] is not None:
        return _cache["data"], "STALE_CACHE"

    return [], "OFFLINE_EMPTY"

class ApiRequestHandler(http.server.BaseHTTPRequestHandler):
    def address_string(self):
        # Windows reverse-DNS freeze fix (instant 0ms localhost latency)
        return self.client_address[0]

    def get_client_ip(self) -> str:
        """
        Extract client IP: inspect self.headers.get('X-Forwarded-For') taking
        the first comma-separated IP. If missing, fall back to self.client_address[0].
        """
        forwarded_for = self.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            first_ip = forwarded_for.split(",")[0].strip()
            if first_ip:
                return first_ip
        if hasattr(self, "client_address") and self.client_address:
            return self.client_address[0]
        return "127.0.0.1"

    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {format % args}")

    def send_cors_headers(self):
        allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
        origin = self.headers.get("Origin", "").strip()

        if allowed_origins_env:
            allowed_origins = [o.strip().rstrip("/") for o in allowed_origins_env.split(",") if o.strip()]
            clean_origin = origin.rstrip("/")
            if origin and clean_origin in allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            elif not origin and allowed_origins:
                self.send_header("Access-Control-Allow-Origin", allowed_origins[0])
        else:
            if origin:
                parsed_origin = urllib.parse.urlparse(origin)
                if parsed_origin.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
                    self.send_header("Access-Control-Allow-Origin", origin)
                    self.send_header("Vary", "Origin")
                else:
                    self.send_header("Access-Control-Allow-Origin", "*")
            else:
                self.send_header("Access-Control-Allow-Origin", "*")

        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept, X-Requested-With, X-Admin-Token")
        self.send_header("Access-Control-Max-Age", "86400")

    def check_admin_auth(self):
        """Validate admin bearer token for protected back-office endpoints."""
        auth_header = self.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        elif "X-Admin-Token" in self.headers:
            token = self.headers["X-Admin-Token"].strip()

        return verify_admin_token(token)

    def send_unauthorized(self):
        err = json.dumps({
            "error": "Unauthorized",
            "message": "Valid admin authentication token required."
        }).encode("utf-8")
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(err)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(err)

    def do_OPTIONS(self):
        """Handle CORS preflight requests from separately hosted frontend."""
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Route 1: Public /api/auctions & /api/v1/auctions (Returns only published/verified properties, PII-stripped)
        if path in ("/api/auctions", "/api/v1/auctions"):
            t0 = time.time()
            data, source = get_raw_auctions()
            filtered, pagination = _filter_and_paginate_auctions(data, query_params)
            latency_ms = round((time.time() - t0) * 1000, 2)

            payload = json.dumps({
                "status": "success",
                "source": source,
                "count": len(filtered),
                "latency_ms": latency_ms,
                "data": filtered,
                "pagination": pagination,
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "public, max-age=30")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # Route 1b: Public /api/v1/auctions/<idOrSlug>
        elif path.startswith("/api/v1/auctions/"):
            id_or_slug = urllib.parse.unquote(path[len("/api/v1/auctions/"):]).strip("/")
            data, _ = get_raw_auctions()
            match = next(
                (
                    serialize_public_auction(p)
                    for p in data
                    if _is_published_auction(p) and (str(p.get("id")) == id_or_slug or p.get("slug") == id_or_slug)
                ),
                None,
            )
            if not match:
                self._send_json(404, {"error": "Not Found", "message": "Auction listing not found."})
                return
            self._send_json(200, {"status": "success", "data": match}, cache_private=False)
            return

        # Route 1c: Public /api/v1/districts
        elif path == "/api/v1/districts":
            data, _ = get_raw_auctions()
            counts = {}
            for p in data:
                if _is_published_auction(p) and p.get("district"):
                    d = str(p["district"]).strip()
                    counts[d] = counts.get(d, 0) + 1
            districts = [{"district": k, "count": v} for k, v in sorted(counts.items())]
            self._send_json(200, {"status": "success", "data": districts}, cache_private=False)
            return

        # Route 1d: Public /sitemap.xml
        elif path == "/sitemap.xml":
            data, _ = get_raw_auctions()
            base_url = os.getenv("PUBLIC_SITE_URL", "https://skandx.com").rstrip("/")
            urls = [f"{base_url}/", f"{base_url}/auctions", f"{base_url}/about", f"{base_url}/services"]
            for p in data:
                if _is_published_auction(p):
                    slug_or_id = p.get("slug") or p.get("id")
                    if slug_or_id:
                        urls.append(f"{base_url}/properties/{urllib.parse.quote(str(slug_or_id))}")
            xml_items = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
            xml_body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml_items}</urlset>'.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.send_header("Content-Length", str(len(xml_body)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(xml_body)
            return

        # Route 2: Admin /api/admin/properties (Protected: Returns all properties including PENDING_REVIEW)
        elif path == "/api/admin/properties":
            if not self.check_admin_auth():
                self.send_unauthorized()
                return

            t0 = time.time()
            data, source = get_raw_auctions()
            latency_ms = round((time.time() - t0) * 1000, 2)

            payload = json.dumps({
                "status": "success",
                "source": source,
                "count": len(data),
                "latency_ms": latency_ms,
                "data": data
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
            self.send_header("Pragma", "no-cache")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # Route 3b: Customer /api/v1/me/leads (Protected by customer Supabase JWT, excludes internal notes)
        elif path == "/api/v1/me/leads":
            user_id = verify_customer_jwt(self.headers.get("Authorization", ""))
            if not user_id:
                self._send_json(401, {"error": "Unauthorized", "message": "Valid customer session required."})
                return
            all_leads, _ = load_leads(limit=200)
            mine = [
                {
                    "id": l.get("id"),
                    "leadCode": l.get("leadCode"),
                    "propertyId": l.get("propertyId"),
                    "propertyTitle": l.get("propertyTitle"),
                    "inquiryType": l.get("inquiryType"),
                    "status": l.get("status"),
                    "createdAt": l.get("createdAt"),
                }
                for l in all_leads
                if l.get("userId") == user_id
            ]
            self._send_json(200, {"status": "success", "leads": mine})
            return

        # Route 3c: Admin /api/admin/advisors (Protected: Returns active admin_users for lead assignment)
        elif path == "/api/admin/advisors":
            if not self.check_admin_auth():
                self.send_unauthorized()
                return
            advisors = []
            if SUPABASE_URL and SUPABASE_KEY and circuit_breaker.allow_request():
                try:
                    req = urllib.request.Request(
                        f"{SUPABASE_URL}/rest/v1/admin_users?select=id,full_name,email,role&is_active=eq.true",
                        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                    )
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        advisors = json.loads(resp.read().decode("utf-8"))
                    circuit_breaker.record_success()
                except Exception:
                    circuit_breaker.record_failure()
            self._send_json(200, {"status": "success", "advisors": advisors})
            return

        # Route 3: Admin /api/admin/leads (Protected: Returns customer inquiries with pagination)
        elif path == "/api/admin/leads":
            if not self.check_admin_auth():
                self.send_unauthorized()
                return

            limit = int(query_params.get("limit", [100])[0])
            offset = int(query_params.get("offset", [0])[0])
            limit = min(500, max(1, limit))
            offset = max(0, offset)

            leads_slice, total = load_leads(limit=limit, offset=offset)
            payload = json.dumps({
                "status": "success",
                "total": total,
                "count": len(leads_slice),
                "limit": limit,
                "offset": offset,
                "leads": leads_slice
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
            self.send_header("Pragma", "no-cache")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # Route 4: Admin /api/admin/pdf-proxy (Protected: Streaming Notice PDF Proxy Endpoint)
        elif path == "/api/admin/pdf-proxy":
            if not self.check_admin_auth():
                self.send_unauthorized()
                return

            target_url = query_params.get("url", [""])[0].strip()
            if not target_url:
                err = json.dumps({"error": "Missing 'url' query parameter."}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err)
                return

            parsed_target = urllib.parse.urlparse(target_url)
            if parsed_target.scheme.lower() not in ("http", "https") or not parsed_target.netloc:
                err = json.dumps({
                    "error": "Invalid URL scheme or format. Only http and https URLs are permitted."
                }).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err)
                return

            if not is_safe_url(target_url):
                err = json.dumps({
                    "error": "Access to local or private network addresses is forbidden."
                }).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err)
                return

            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/pdf,application/octet-stream,*/*",
                }
            )

            opener = urllib.request.build_opener(SafeRedirectHandler())
            try:
                with opener.open(req, timeout=10) as resp:
                    chunks = []
                    total_bytes = 0
                    max_bytes = 25 * 1024 * 1024  # 25 MB safety ceiling
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        total_bytes += len(chunk)
                        if total_bytes > max_bytes:
                            err = json.dumps({"error": "Remote PDF exceeded 25MB safety ceiling."}).encode("utf-8")
                            self.send_response(413)
                            self.send_header("Content-Type", "application/json; charset=utf-8")
                            self.send_header("Content-Length", str(len(err)))
                            self.send_cors_headers()
                            self.end_headers()
                            self.wfile.write(err)
                            return
                        chunks.append(chunk)

                    pdf_bytes = b"".join(chunks)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", "inline; filename=\"auction_notice.pdf\"")
                    self.send_header("Content-Length", str(len(pdf_bytes)))
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
                    self.send_header("Pragma", "no-cache")
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(pdf_bytes)
                    return
            except urllib.error.HTTPError as e:
                status_code = e.code if e.code in (400, 401, 403, 404, 410, 500, 502, 503) else 502
                err = json.dumps({
                    "error": f"Remote server returned HTTP {e.code}: {e.reason}",
                    "status_code": e.code
                }).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err)
                return
            except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
                is_timeout = isinstance(e, (TimeoutError, socket.timeout)) or "timed out" in str(e).lower()
                status_code = 504 if is_timeout else 502
                err = json.dumps({
                    "error": "Remote PDF fetch timed out after 10 seconds." if is_timeout else f"Failed to connect to remote PDF host: {e}"
                }).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err)
                return
            except Exception as e:
                err = json.dumps({
                    "error": f"Unexpected error streaming PDF: {str(e)}"
                }).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err)
                return

        # Route 5: Health Check /api/health
        elif path == "/api/health" or path == "/":
            with _crawler_lock:
                crawling = _crawler_running

            payload = json.dumps({
                "status": "healthy",
                "service": "skandx-auction-backend-api",
                "version": "2.2.0",
                "crawler_active": crawling,
                "supabase_connected": bool(SUPABASE_URL and SUPABASE_KEY),
                "circuit_breaker": circuit_breaker.state,
                "timestamp": int(time.time())
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
            self.send_header("Pragma", "no-cache")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # 404 Not Found
        err_body = b'{"error":"Not Found","message":"Endpoint does not exist."}'
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(err_body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(err_body)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        
        # Max payload ceiling: 10 MB to prevent unbounded memory allocation
        if content_length > 10 * 1024 * 1024:
            err = b'{"error":"Payload Too Large","message":"Request body exceeds 10MB limit."}'
            self.send_response(413)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(err)
            return

        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        # Route: POST /api/admin/login (Admin authentication for admin.skandx.com)
        if self.path == "/api/admin/login":
            client_ip = self.get_client_ip()
            if not check_login_rate_limit(client_ip, limit=5, window_seconds=60, prune_seconds=120):
                err_payload = json.dumps({
                    "error": "Too many login attempts. Please wait 60 seconds."
                }).encode("utf-8")
                self.send_response(429)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_payload)))
                self.send_header("Retry-After", "60")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err_payload)
                return

            try:
                body = json.loads(post_data.decode("utf-8")) if post_data else {}
            except Exception:
                body = {}

            email = str(body.get("email", "")).strip().lower()
            password = str(body.get("password", ""))

            admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
            admin_password = os.getenv("ADMIN_PASSWORD", "")
            current_env = os.getenv("ENVIRONMENT", ENVIRONMENT).lower()

            # Strict security gate: in staging & production, default credentials are strictly forbidden
            if (not admin_password or not admin_email) and current_env in ("staging", "production"):
                payload = json.dumps({
                    "status": "error",
                    "message": "Admin authentication is disabled: ADMIN_EMAIL and ADMIN_PASSWORD must be explicitly configured in staging and production."
                }).encode("utf-8")
                self.send_response(503)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
                self.send_header("Pragma", "no-cache")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(payload)
                return

            # Development fallback
            admin_email = admin_email or "admin@skandx.com"
            admin_password = admin_password or "skandx@admin2026"

            # Constant-time comparison to prevent timing attacks
            is_valid_email = hmac.compare_digest(email.encode("utf-8"), admin_email.encode("utf-8"))
            is_valid_password = hmac.compare_digest(password.encode("utf-8"), admin_password.encode("utf-8"))

            if is_valid_email and is_valid_password:
                token = generate_admin_token()
                payload = json.dumps({
                    "status": "success",
                    "token": token,
                    "admin": {
                        "name": "Chief Auction Officer",
                        "email": admin_email,
                        "role": "SUPER_ADMIN"
                    }
                }).encode("utf-8")
                self.send_response(200)
            else:
                payload = json.dumps({
                    "status": "error",
                    "message": "Invalid admin credentials."
                }).encode("utf-8")
                self.send_response(401)

            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
            self.send_header("Pragma", "no-cache")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # Route: POST /api/contact (Retired in Phase 3 in favor of POST /api/v1/leads)
        elif self.path == "/api/contact":
            self._send_json(410, {
                "error": "Gone",
                "message": "POST /api/contact has been retired. Use POST /api/v1/leads with customer authentication.",
            })
            return

        # Route: POST /api/v1/leads (Authenticated customer lead + optional 5% service agreement)
        elif self.path == "/api/v1/leads":
            client_ip = self.get_client_ip()
            if not check_contact_rate_limit(client_ip, limit=15, window_seconds=60, prune_seconds=120):
                err_payload = json.dumps({
                    "error": "Rate limit exceeded. Please wait 60 seconds."
                }).encode("utf-8")
                self.send_response(429)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_payload)))
                self.send_header("Retry-After", "60")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err_payload)
                return

            user_id = verify_customer_jwt(self.headers.get("Authorization", ""))
            if not user_id:
                self._send_json(401, {"error": "Unauthorized", "message": "Please sign in to connect with an advisor."})
                return

            try:
                body = json.loads(post_data.decode("utf-8"))
            except Exception:
                body = {}

            phone = str(body.get("phone", "")).strip()
            if not phone or len(phone) < 7:
                self._send_json(400, {
                    "error": "Validation failed",
                    "message": "A valid phone number (at least 7 digits) is required.",
                })
                return

            res_body, code = create_lead_and_agreement(
                user_id=user_id,
                body=body,
                client_ip=client_ip,
                user_agent=self.headers.get("User-Agent", ""),
            )
            self._send_json(code, res_body)
            return

        # Route: POST /api/admin/properties/verify (Protected: Admin verifies & persists scraped property)
        elif self.path == "/api/admin/properties/verify":
            self._handle_admin_property_update(post_data)
            return

        # Route: POST /api/scrape/trigger (Protected: Triggers crawler job with concurrency lock)
        elif self.path == "/api/scrape/trigger":
            if not self.check_admin_auth():
                self.send_unauthorized()
                return

            global _crawler_running
            with _crawler_lock:
                if _crawler_running:
                    conflict_body = json.dumps({
                        "status": "already_running",
                        "message": "Crawler microservice is already actively executing."
                    }).encode("utf-8")
                    self.send_response(409)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(conflict_body)))
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(conflict_body)
                    return
                _crawler_running = True

            def run_crawler():
                global _crawler_running
                try:
                    script = BASE_DIR / "ingestion" / "main.py"
                    subprocess.run([sys.executable, str(script), "--scrape-all"], check=False)
                except Exception as e:
                    print(f"[Crawler Run Error]: {e}")
                finally:
                    with _crawler_lock:
                        _crawler_running = False

            threading.Thread(target=run_crawler, daemon=True).start()

            payload = json.dumps({
                "status": "started",
                "message": "Background web scraping job triggered across partner bank portals.",
                "timestamp": int(time.time())
            }).encode("utf-8")

            self.send_response(202)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
            self.send_header("Pragma", "no-cache")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # 404 Not Found
        err_body = b'{"error":"Not Found","message":"Invalid POST endpoint."}'
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(err_body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(err_body)

    def _send_json(self, status_code: int, body_obj: dict, cache_private: bool = True):
        payload = json.dumps(body_obj).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        if cache_private:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, private")
            self.send_header("Pragma", "no-cache")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _handle_admin_property_update(self, raw_body: bytes):
        if not self.check_admin_auth():
            self.send_unauthorized()
            return
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "Invalid JSON payload."})
            return

        prop_id = body.get("id")
        if not prop_id:
            self._send_json(400, {"error": "Missing required field 'id'."})
            return

        new_status = body.get("publication_status") or body.get("status", "PUBLISHED")
        if new_status == "PUBLISHED" and isinstance(body.get("verification_dimensions"), dict):
            dims = body["verification_dimensions"]
            src_ok = (dims.get("source_checked") or {}).get("status") == "COMPLETED"
            auc_ok = (dims.get("auction_details_checked") or {}).get("status") == "COMPLETED"
            if not (src_ok and auc_ok):
                self._send_json(400, {
                    "error": "Publication gate failed",
                    "message": "source_checked and auction_details_checked must be COMPLETED before publishing.",
                })
                return
        persist_property_update(prop_id, new_status, updated_fields=body)
        _cache["data"] = None
        self._send_json(200, {
            "status": "success",
            "message": f"Property {prop_id} successfully persisted as {new_status}.",
            "verified": new_status == "PUBLISHED",
        })

    def do_PATCH(self):
        """Handle PATCH requests for admin property and lead updates."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 1048576:
            self._send_json(413, {"error": "Payload Too Large"})
            return

        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/admin/properties":
            self._handle_admin_property_update(raw_body)
            return

        if path == "/api/admin/leads":
            if not self.check_admin_auth():
                self.send_unauthorized()
                return
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except Exception:
                self._send_json(400, {"error": "Invalid JSON payload."})
                return

            lead_id = body.get("id")
            new_status = str(body.get("status", "")).strip()
            if not lead_id or new_status not in VALID_LEAD_STATUSES:
                self._send_json(400, {
                    "error": "Validation failed",
                    "message": f"Valid 'id' and 'status' in {sorted(VALID_LEAD_STATUSES)} required.",
                })
                return

            notes = body.get("notes")
            assigned_advisor_id = body.get("assigned_advisor_id")
            persist_lead_update(lead_id, new_status, notes=notes, assigned_advisor_id=assigned_advisor_id)
            self._send_json(200, {
                "status": "success",
                "id": lead_id,
                "leadStatus": new_status,
                "assignedAdvisorId": assigned_advisor_id,
            })
            return

        self._send_json(404, {"error": "Not Found", "message": "Invalid PATCH endpoint."})

def main():
    server_address = ("0.0.0.0", PORT)
    with http.server.ThreadingHTTPServer(server_address, ApiRequestHandler) as httpd:
        print("=" * 65)
        print("SKANDX Decoupled REST API Server (v2.2.0)")
        print(f"Listening on   : 0.0.0.0:{PORT}")
        print(f"Public API     : http://127.0.0.1:{PORT}/api/auctions (Verified only)")
        print(f"Admin API      : http://127.0.0.1:{PORT}/api/admin/properties (Protected)")
        print(f"Leads API      : http://127.0.0.1:{PORT}/api/admin/leads (Protected)")
        print(f"PDF Proxy      : http://127.0.0.1:{PORT}/api/admin/pdf-proxy (Protected)")
        print(f"CORS           : Enabled (Supports separate frontend hosting)")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nGracefully stopped API server.")

if __name__ == "__main__":
    main()
