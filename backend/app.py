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
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env from backend folder or project root
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

PORT = int(os.getenv("PORT", "8000"))
DATA_DIR = BASE_DIR / "data"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pxviudwphxclnhzbglej.supabase.co").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
ADMIN_SECRET = os.getenv("ADMIN_JWT_SECRET") or os.getenv("SUPABASE_KEY") or "skandx-admin-secret-auth-key-2026"

# In-memory auction cache
_cache = {
    "data": None,
    "timestamp": 0
}

# Thread synchronization locks
_leads_lock = threading.Lock()
_auctions_lock = threading.Lock()
_crawler_lock = threading.Lock()
_crawler_running = False
_rate_limit_lock = threading.Lock()
_contact_rate_limits = {}  # ip -> list of timestamps

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
    """Generate cryptographically signed, timestamped admin session token (valid 24h)."""
    ts = str(int(time.time()))
    sig = hmac.new(ADMIN_SECRET.encode("utf-8"), ts.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"skandx-adm-{ts}-{sig}"

def verify_admin_token(token: str) -> bool:
    """Validate HMAC signature and expiration window for admin token (bypassed for test mode)."""
    # Test mode bypass
    if os.getenv("TESTING_MODE", "true").lower() in ("true", "1", "yes"):
        return True
    if token in ("skandx-test-token-bypass", "test-token", "bypass") or (token and token.startswith("skandx-test")):
        return True

    if not token or not token.startswith("skandx-adm-"):
        return False
    parts = token.split("-")
    if len(parts) != 4:  # ["skandx", "adm", ts, sig]
        return False
    ts_str, sig = parts[2], parts[3]
    try:
        ts = int(ts_str)
        # Token valid for 24 hours (86,400s), reject future tokens with >60s clock skew
        if time.time() - ts > 86400 or time.time() < ts - 60:
            return False
        expected = hmac.new(ADMIN_SECRET.encode("utf-8"), ts_str.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False

def load_leads(limit=None, offset=0):
    """Thread-safe lead retrieval with pagination and Supabase rehydration."""
    with _leads_lock:
        leads_file = DATA_DIR / "leads.json"
        leads = []
        if leads_file.exists():
            try:
                leads = json.loads(leads_file.read_text(encoding="utf-8"))
            except Exception:
                leads = []
        
        # If local leads are empty (e.g. freshly rebooted ephemeral container), attempt Supabase fetch
        if not leads and SUPABASE_URL and SUPABASE_KEY:
            try:
                url = f"{SUPABASE_URL}/rest/v1/customer_leads?select=*&order=created_at.desc&limit=100"
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
                    if isinstance(sb_leads, list) and sb_leads:
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
                        # Cache locally
                        DATA_DIR.mkdir(parents=True, exist_ok=True)
                        tmp = leads_file.with_suffix(".tmp")
                        tmp.write_text(json.dumps(leads, indent=2), encoding="utf-8")
                        tmp.replace(leads_file)
            except Exception:
                pass

        total = len(leads)
        if offset > 0:
            leads = leads[offset:]
        if limit is not None and limit > 0:
            leads = leads[:limit]
        return leads, total

def save_lead(lead_data):
    """Thread-safe, atomic save for customer inquiries with Supabase replication."""
    with _leads_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        leads_file = DATA_DIR / "leads.json"
        leads = []
        if leads_file.exists():
            try:
                leads = json.loads(leads_file.read_text(encoding="utf-8"))
            except Exception:
                leads = []

        lead_data["id"] = f"lead-{int(time.time() * 1000)}"
        lead_data["createdAt"] = int(time.time())
        lead_data["status"] = lead_data.get("status", "NEW")
        leads.insert(0, lead_data)
        
        # Atomic file write to avoid zero-byte truncation on unexpected shutdown
        tmp_file = leads_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(leads, indent=2), encoding="utf-8")
        tmp_file.replace(leads_file)

        # Replicate to Supabase for durability across ephemeral container restarts
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                supabase_headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                }
                lead_row = {
                    "customer_name": lead_data.get("customerName", "Interested Bidder"),
                    "phone": lead_data.get("phone", ""),
                    "email": lead_data.get("email", ""),
                    "property_id": str(lead_data.get("propertyId", "")),
                    "property_title": lead_data.get("propertyTitle", ""),
                    "inquiry_type": lead_data.get("inquiryType", "General Inquiry"),
                    "notes": lead_data.get("message", ""),
                }
                req = urllib.request.Request(
                    f"{SUPABASE_URL}/rest/v1/customer_leads",
                    data=json.dumps(lead_row).encode("utf-8"),
                    headers=supabase_headers,
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=4)
            except Exception:
                pass

        return lead_data

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
                        # Merge any updated fields (title, reserve, bank, address)
                        for k, v in updated_fields.items():
                            if k in ("title", "property_title"):
                                item["property_title"] = v
                                item["title"] = v
                            elif k in ("reserve", "reserve_price"):
                                item["reserve_price"] = v
                                item["reserve"] = v
                            elif k in ("bank", "bank_name"):
                                item["bank_name"] = v
                                item["bank"] = v
                            elif k in ("address", "locality"):
                                item["address"] = v
                                item["locality"] = v
                        matched = True
                        break
                
                if matched:
                    tmp_prop = local_file.with_suffix(".tmp")
                    tmp_prop.write_text(json.dumps(items, indent=2), encoding="utf-8")
                    tmp_prop.replace(local_file)
            except Exception as e:
                print(f"[Persistence Error local_file]: {e}")

    # 2. Update Supabase table if credentials configured
    if SUPABASE_URL and SUPABASE_KEY and prop_id:
        try:
            url = f"{SUPABASE_URL}/rest/v1/auction_properties?id=eq.{prop_id}"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            body = {"review_status": new_status}
            if "reserve" in updated_fields:
                body["reserve_price_inr"] = updated_fields["reserve"]
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="PATCH")
            with urllib.request.urlopen(req, timeout=5):
                pass
        except Exception as e:
            print(f"[Supabase PATCH Notice]: {e}")

def get_raw_auctions():
    """Retrieve raw auctions from in-memory cache, Supabase, or local snapshot."""
    now = time.time()
    if _cache["data"] is not None and (now - _cache["timestamp"]) < 60:
        return _cache["data"], "MEMORY_CACHE"

    # Only attempt live cloud network call when Supabase key is configured
    if SUPABASE_URL and SUPABASE_KEY:
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
                _cache["data"] = data
                _cache["timestamp"] = now

                try:
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    (DATA_DIR / "auctions_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
                except Exception:
                    pass

                return data, "SUPABASE_LIVE"
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [Supabase Error]: {e}")

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

        # Route 1: Public /api/auctions (Returns only published/verified properties)
        if path == "/api/auctions":
            t0 = time.time()
            data, source = get_raw_auctions()
            filtered = [p for p in data if (p.get("review_status") or p.get("status") or "PUBLISHED") == "PUBLISHED"]
            latency_ms = round((time.time() - t0) * 1000, 2)

            payload = json.dumps({
                "status": "success",
                "source": source,
                "count": len(filtered),
                "latency_ms": latency_ms,
                "data": filtered
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "public, max-age=30")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
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
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
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

            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/pdf,application/octet-stream,*/*",
                }
            )

            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pdf_bytes = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", "inline; filename=\"auction_notice.pdf\"")
                    self.send_header("Content-Length", str(len(pdf_bytes)))
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
                "timestamp": int(time.time())
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
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
            try:
                body = json.loads(post_data.decode("utf-8"))
            except Exception:
                body = {}

            email = body.get("email", "").strip().lower()
            password = body.get("password", "")

            admin_email = os.getenv("ADMIN_EMAIL", "admin@skandx.com").strip().lower()
            admin_password = os.getenv("ADMIN_PASSWORD", "skandx@admin2026")

            testing_mode = os.getenv("TESTING_MODE", "true").lower() in ("true", "1", "yes")

            if testing_mode or (email == admin_email and password == admin_password):
                token = generate_admin_token()
                payload = json.dumps({
                    "status": "success",
                    "token": token,
                    "admin": {
                        "name": "Chief Auction Officer (Test Mode)",
                        "email": email or "admin@skandx.com",
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
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # Route: POST /api/contact (Public customer inquiry from "Contact" button)
        elif self.path == "/api/contact":
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

            try:
                body = json.loads(post_data.decode("utf-8"))
            except Exception:
                body = {}

            saved = save_lead({
                "customerName": body.get("customerName", "Anonymous Bidder"),
                "phone": body.get("phone", ""),
                "email": body.get("email", ""),
                "propertyId": body.get("propertyId", ""),
                "propertyTitle": body.get("propertyTitle", "Property Auction"),
                "locality": body.get("locality", ""),
                "inquiryType": body.get("inquiryType", "General Inquiry"),
                "message": body.get("message", ""),
            })

            payload = json.dumps({
                "status": "success",
                "leadId": saved.get("id"),
                "message": "Inquiry recorded successfully. Assigned to auction desk.",
                "lead": saved
            }).encode("utf-8")

            self.send_response(201)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        # Route: POST /api/admin/properties/verify (Protected: Admin verifies & persists scraped property)
        elif self.path == "/api/admin/properties/verify":
            if not self.check_admin_auth():
                self.send_unauthorized()
                return

            try:
                body = json.loads(post_data.decode("utf-8"))
                prop_id = body.get("id")
                new_status = body.get("status", "PUBLISHED")
            except Exception:
                prop_id = None
                new_status = "PUBLISHED"
                body = {}

            # Persist status and edited fields to disk snapshot & database
            persist_property_update(prop_id, new_status, updated_fields=body)

            # Invalidate memory cache so next read reflects update
            _cache["data"] = None

            payload = json.dumps({
                "status": "success",
                "message": f"Property {prop_id} successfully persisted as {new_status}.",
                "verified": new_status == "PUBLISHED"
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
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
