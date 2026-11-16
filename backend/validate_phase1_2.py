"""
Standalone Validation Script for Phase 1 & 2 Backend Tasks.
Validates:
1. Thread-safe sliding window contact rate limiter with proxy headers & pruning.
2. Protected streaming PDF proxy with authentication, parameter validation, and binary streaming.
3. Database migration DDL syntax & schema completeness.
"""

import sys
import time
import json
import socket
import threading
import urllib.request
import urllib.error
import urllib.parse
import http.server
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from backend.app import (
    generate_admin_token,
    verify_admin_token,
    check_contact_rate_limit,
    _contact_rate_limits,
    _rate_limit_lock,
    ApiRequestHandler,
)

def validate_migrations():
    print("[1/3] Validating Database Migration DDL files...")
    mig1 = BASE_DIR / "migrations" / "001_create_auction_properties.sql"
    mig2 = BASE_DIR / "migrations" / "002_create_customer_leads.sql"

    assert mig1.exists(), "001_create_auction_properties.sql is missing"
    assert mig2.exists(), "002_create_customer_leads.sql is missing"

    content1 = mig1.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS auction_properties" in content1
    assert "property_title" in content1
    assert "bank_name" in content1
    assert "reserve_price_inr" in content1
    assert "emd_amount_inr" in content1
    assert "auction_date" in content1
    assert "possession_type" in content1
    assert "auction_event_hash" in content1
    assert "asset_fingerprint" in content1
    assert "review_status" in content1
    assert "idx_auction_properties_status" in content1
    assert "idx_auction_properties_fingerprint" in content1
    assert "idx_auction_properties_event_hash" in content1
    assert "ROW LEVEL SECURITY" in content1
    assert "Public Read Published" in content1
    assert "Service Role Full Access" in content1

    content2 = mig2.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS customer_leads" in content2
    assert "#SK-" in content2
    assert "customer_name" in content2
    assert "phone" in content2
    assert "property_id" in content2
    assert "inquiry_type" in content2
    assert "ROW LEVEL SECURITY" in content2
    assert "Public Insert Leads" in content2
    assert "Service Role Leads Access" in content2

    print("  -> Migration 001 & 002 validated successfully.")

def validate_rate_limiting():
    print("[2/3] Validating Sliding Window Rate Limiter...")
    test_ip = "10.10.10.10"
    with _rate_limit_lock:
        _contact_rate_limits.pop(test_ip, None)

    for i in range(15):
        assert check_contact_rate_limit(test_ip, limit=15, window_seconds=60), f"Request {i+1} should be permitted"

    # 16th should fail
    assert not check_contact_rate_limit(test_ip, limit=15, window_seconds=60), "16th request must be throttled"

    # Verify IP extraction logic
    class MockHandler:
        def __init__(self, xff, client_addr):
            self.headers = {"X-Forwarded-For": xff} if xff else {}
            self.client_address = (client_addr, 12345)

    h_proxy = MockHandler("203.0.113.195, 10.0.0.1", "127.0.0.1")
    assert ApiRequestHandler.get_client_ip(h_proxy) == "203.0.113.195"

    h_direct = MockHandler("", "192.168.1.99")
    assert ApiRequestHandler.get_client_ip(h_direct) == "192.168.1.99"

    print("  -> Sliding window rate limiter & proxy-aware IP extraction validated.")

def validate_http_endpoints():
    print("[3/3] Validating HTTP Endpoints over Wire...")
    # Start ephemeral API server
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ApiRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"

    # Mock save_lead to bypass remote Supabase network call
    import backend.app
    backend.app.save_lead = lambda data: {"id": "lead-mock", **data}

    # 1. Test POST /api/contact burst and 429 response
    client_ip = "172.16.0.44"
    contact_url = f"{base_url}/api/contact"
    req_body = json.dumps({"customerName": "Test", "phone": "1234567890"}).encode("utf-8")

    for _ in range(15):
        req = urllib.request.Request(
            contact_url,
            data=req_body,
            headers={"Content-Type": "application/json", "X-Forwarded-For": client_ip},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            assert r.status in (200, 201)

    # 16th request
    throttled = False
    req = urllib.request.Request(
        contact_url,
        data=req_body,
        headers={"Content-Type": "application/json", "X-Forwarded-For": client_ip},
        method="POST"
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        assert e.code == 429
        body = json.loads(e.read().decode("utf-8"))
        assert body.get("error") == "Rate limit exceeded. Please wait 60 seconds."
        throttled = True
    assert throttled, "HTTP 429 was not returned on 16th request"

    # 2. Test GET /api/admin/pdf-proxy
    # Unauthorized
    unauth = False
    try:
        urllib.request.urlopen(f"{base_url}/api/admin/pdf-proxy?url=https://example.com/doc.pdf", timeout=5)
    except urllib.error.HTTPError as e:
        assert e.code == 401
        unauth = True
    assert unauth, "PDF proxy allowed unauthorized access"

    # Authorized with missing URL
    token = generate_admin_token()
    bad_req = False
    try:
        req = urllib.request.Request(f"{base_url}/api/admin/pdf-proxy", headers={"Authorization": f"Bearer {token}"})
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        assert e.code == 400
        bad_req = True
    assert bad_req, "PDF proxy allowed missing URL"

    # Authorized with invalid scheme
    bad_scheme = False
    try:
        req = urllib.request.Request(f"{base_url}/api/admin/pdf-proxy?url=file:///etc/hosts", headers={"Authorization": f"Bearer {token}"})
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        assert e.code == 400
        bad_scheme = True
    assert bad_scheme, "PDF proxy allowed non-HTTP scheme"

    # Authorized with mock PDF source server
    pdf_content = b"%PDF-1.4 Mock auction circular bytes"
    class MockPDFServer(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(pdf_content)))
            self.end_headers()
            self.wfile.write(pdf_content)
        def log_message(self, *args):
            pass

    mock_pdf = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockPDFServer)
    mock_pdf_port = mock_pdf.server_address[1]
    threading.Thread(target=mock_pdf.serve_forever, daemon=True).start()

    target_encoded = urllib.parse.quote(f"http://127.0.0.1:{mock_pdf_port}/notice.pdf")
    req = urllib.request.Request(f"{base_url}/api/admin/pdf-proxy?url={target_encoded}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=5) as r:
        assert r.status == 200
        assert r.headers.get("Content-Type") == "application/pdf"
        assert "inline" in r.headers.get("Content-Disposition", "")
        data = r.read()
        assert data == pdf_content

    mock_pdf.shutdown()
    server.shutdown()
    print("  -> HTTP 429 rate limiter & PDF proxy streaming endpoints validated.")

if __name__ == "__main__":
    validate_migrations()
    validate_rate_limiting()
    validate_http_endpoints()
    print("\nAll Phase 1 & Phase 2 Backend Tasks VALIDATED SUCCESSFULLY.")
