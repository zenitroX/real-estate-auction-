"""
High-Performance, Multi-Threaded Web Server & Supabase Proxy.
Features:
- Windows reverse-DNS freeze fix (0ms localhost latency)
- Protected server-to-server Supabase REST proxy (bypasses browser Origin restrictions)
- 60-second in-memory caching for instant (<1ms) repeat responses
- Multi-threaded non-blocking HTTP handling
"""

import http.server
import json
import os
import time
import urllib.request
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env directly from project root
load_dotenv(BASE_DIR / ".env")

PORT = 3000
WEB_DIR = BASE_DIR / "web"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pxviudwphxclnhzbglej.supabase.co").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")

# In-memory auction cache
_cache = {
    "data": None,
    "timestamp": 0
}

def get_auctions():
    """Retrieve auctions from in-memory cache, Supabase, or local fallback."""
    now = time.time()
    # Cache hit within 60s
    if _cache["data"] is not None and (now - _cache["timestamp"]) < 60:
        return _cache["data"], "MEMORY_CACHE"

    # Fetch from Supabase REST API server-to-server
    # Use newest auctions first so the dashboard defaults to the most recent listings.
    url = f"{SUPABASE_URL}/rest/v1/auction_properties?select=*&order=auction_date.desc&limit=50"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "User-Agent": "AuctionEngine-Backend/1.0"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            _cache["data"] = data
            _cache["timestamp"] = now
            # Persist local snapshot so offline / direct double-click always works
            try:
                (WEB_DIR / "auctions_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                pass
            return data, "SUPABASE_LIVE"
    except Exception as e:
        print(f"[Supabase Fetch Error]: {e}")
        # Try local backup snapshot
        fallback_file = WEB_DIR / "auctions_data.json"
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
        return [], "ERROR"

class FastAuctionRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    # CRITICAL FOR WINDOWS: Avoid socket.getfqdn() timeout that freezes localhost
    def address_string(self):
        return self.client_address[0]

    def log_message(self, format, *args):
        # High performance brief logging
        print(f"[{time.strftime('%H:%M:%S')}] {format % args}")

    def do_GET(self):
        if self.path == "/api/auctions" or self.path.startswith("/api/auctions?"):
            t0 = time.time()
            data, source = get_auctions()
            elapsed_ms = (time.time() - t0) * 1000

            payload = json.dumps({
                "status": "success",
                "source": source,
                "count": len(data),
                "latency_ms": round(elapsed_ms, 2),
                "data": data
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(payload)
            return

        elif self.path == "/api/health":
            body = b'{"status":"healthy","service":"auction-web-server"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Serve static files from web/
        super().do_GET()

def main():
    server_address = ("127.0.0.1", PORT)
    with http.server.ThreadingHTTPServer(server_address, FastAuctionRequestHandler) as httpd:
        url = f"http://127.0.0.1:{PORT}"
        print("=" * 65)
        print("Bank Auction High-Speed Web Server is Ready!")
        print(f"Local URL      : {url}")
        print(f"Offline Direct : Open web/index.html in any browser")
        print(f"Database       : Supabase ({SUPABASE_URL})")
        print("=" * 65)
        print("Press Ctrl+C to stop the server.\n")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nGracefully stopped web server.")

if __name__ == "__main__":
    main()
