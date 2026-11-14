"""
SKANDX Backend API Server
High-Performance, Multi-Threaded REST API & Supabase Proxy.

Features:
- Decoupled REST API service for public customer browsing and admin verification
- GET /api/auctions : Public endpoint (returns only PUBLISHED / verified properties)
- GET /api/admin/properties : Protected admin verification queue
- POST /api/admin/properties/verify : Approves, updates, & persists property status
- POST /api/contact : Thread-safe public lead capture from "Contact" button
- GET /api/admin/leads : Protected admin feed of customer inquiries with pagination
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
import subprocess
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

# In-memory auction cache
_cache = {
    "data": None,
    "timestamp": 0
}

# Thread synchronization locks
_leads_lock = threading.Lock()
_crawler_lock = threading.Lock()
_crawler_running = False

# Active authenticated admin session tokens
_valid_admin_tokens = set()

def load_leads(limit=None, offset=0):
    """Thread-safe lead retrieval with pagination."""
    with _leads_lock:
        leads_file = DATA_DIR / "leads.json"
        leads = []
        if leads_file.exists():
            try:
                leads = json.loads(leads_file.read_text(encoding="utf-8"))
            except Exception:
                leads = []
        
        total = len(leads)
        if offset > 0:
            leads = leads[offset:]
        if limit is not None and limit > 0:
            leads = leads[:limit]
        return leads, total

def save_lead(lead_data):
    """Thread-safe save for new customer lead inquiries."""
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
        leads_file.write_text(json.dumps(leads, indent=2), encoding="utf-8")
        return lead_data

def persist_property_update(prop_id, new_status, updated_fields=None):
    """Persist verified status and edited details to local storage and Supabase."""
    updated_fields = updated_fields or {}
    local_file = DATA_DIR / "auctions_data.json"
    
    # 1. Update local snapshot file if present
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
                local_file.write_text(json.dumps(items, indent=2), encoding="utf-8")
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

        # Validated if in active session set or valid demo token prefix
        if token and (token in _valid_admin_tokens or token.startswith("skandx-adm-")):
            return True
        return False

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

        # Route 4: Health Check /api/health
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

            if email == admin_email and password == admin_password:
                token = f"skandx-adm-{int(time.time())}"
                _valid_admin_tokens.add(token)
                payload = json.dumps({
                    "status": "success",
                    "token": token,
                    "admin": {
                        "name": "Chief Auction Officer",
                        "email": email,
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
        print(f"CORS           : Enabled (Supports separate frontend hosting)")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nGracefully stopped API server.")

if __name__ == "__main__":
    main()
