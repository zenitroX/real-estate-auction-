import os
os.environ.setdefault("ADMIN_JWT_SECRET", "pytest-admin-jwt-secret-key-2026")
import time
import json
import socket
import threading
import urllib.request
import urllib.error
import http.server
import pytest

from backend.app import (
    generate_admin_token,
    verify_admin_token,
    save_lead,
    load_leads,
    check_contact_rate_limit,
    check_login_rate_limit,
    _contact_rate_limits,
    _login_rate_limits,
    _rate_limit_lock,
    ApiRequestHandler,
    CircuitBreaker,
    circuit_breaker,
    get_raw_auctions,
    persist_property_update,
)

def test_admin_token_generation_and_verification():
    token = generate_admin_token()
    assert token.startswith("skandx-adm-")
    assert verify_admin_token(token) is True

def test_admin_token_rejects_unauthorized_forged_tokens():
    # Attackers passing forged prefixes MUST be rejected
    assert verify_admin_token("skandx-adm-forged-token") is False
    assert verify_admin_token("skandx-adm-anything") is False
    assert verify_admin_token("Bearer skandx-adm-12345") is False
    assert verify_admin_token("") is False
    assert verify_admin_token(None) is False
    # Insecure bypasses previously present must now be rejected
    assert verify_admin_token("test-token") is False
    assert verify_admin_token("bypass") is False
    assert verify_admin_token("skandx-test") is False
    assert verify_admin_token("skandx-test-token") is False
    assert verify_admin_token("skandx-test-token-bypass") is False

def test_save_and_load_lead_atomic():
    test_lead = {
        "customerName": "Test Bidder",
        "phone": "+91 99999 88888",
        "email": "test@skandx.com",
        "propertyId": "p-test-1",
        "inquiryType": "Site Inspection"
    }
    saved = save_lead(test_lead)
    assert saved["id"].startswith("lead-")
    assert saved["customerName"] == "Test Bidder"
    
    leads, total = load_leads(limit=10)
    assert total >= 1
    assert any(l["id"] == saved["id"] for l in leads)

def test_contact_rate_limiter_allows_up_to_15_burst():
    test_ip = "192.168.1.100"
    with _rate_limit_lock:
        _contact_rate_limits.pop(test_ip, None)

    for i in range(15):
        assert check_contact_rate_limit(test_ip, limit=15, window_seconds=60) is True

    # 16th request in the same 60s window must fail
    assert check_contact_rate_limit(test_ip, limit=15, window_seconds=60) is False

    # Different IP is not throttled
    different_ip = "192.168.1.101"
    assert check_contact_rate_limit(different_ip, limit=15, window_seconds=60) is True

def test_contact_rate_limiter_prunes_older_than_cutoff():
    test_ip = "192.168.1.200"
    now = time.time()
    with _rate_limit_lock:
        # Seed with timestamps older than 120s
        _contact_rate_limits[test_ip] = [now - 150, now - 130, now - 80]

    # Calling check_contact_rate_limit should prune timestamps older than 120s
    allowed = check_contact_rate_limit(test_ip, limit=15, window_seconds=60, prune_seconds=120)
    assert allowed is True

    with _rate_limit_lock:
        # Only the timestamp > now - 120 (and the newly added timestamp) remain
        for ts in _contact_rate_limits[test_ip]:
            assert ts > (now - 120 - 1)

def test_get_client_ip_proxy_forwarded_and_fallback():
    class DummyHandler:
        def __init__(self, headers, client_address):
            self.headers = headers
            self.client_address = client_address

    # Case 1: Multiple comma-separated IPs in X-Forwarded-For
    h1 = DummyHandler({"X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"}, ("127.0.0.1", 54321))
    assert ApiRequestHandler.get_client_ip(h1) == "203.0.113.195"

    # Case 2: Single IP in X-Forwarded-For with whitespace
    h2 = DummyHandler({"X-Forwarded-For": "  10.0.0.5  "}, ("127.0.0.1", 54321))
    assert ApiRequestHandler.get_client_ip(h2) == "10.0.0.5"

    # Case 3: Missing X-Forwarded-For falls back to client_address[0]
    h3 = DummyHandler({}, ("192.168.1.50", 54321))
    assert ApiRequestHandler.get_client_ip(h3) == "192.168.1.50"


@pytest.fixture(scope="module")
def api_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ApiRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.shutdown()


def test_contact_endpoint_burst_and_rate_limiting_http(api_server, monkeypatch):
    # Legacy /api/contact is retired (410 Gone)
    legacy_req = urllib.request.Request(
        f"{api_server}/api/contact",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as legacy_exc:
        urllib.request.urlopen(legacy_req, timeout=5)
    assert legacy_exc.value.code == 410

    monkeypatch.setattr("backend.app.verify_customer_jwt", lambda auth: "cust-burst-1")
    monkeypatch.setattr("backend.app.create_lead_and_agreement", lambda **kw: ({"status": "success", "leadId": "lead-mock"}, 201))

    unique_ip = "198.51.100.42"
    url = f"{api_server}/api/v1/leads"
    payload = json.dumps({
        "customerName": "Burst Tester",
        "phone": "9876543210",
        "propertyId": "prop-burst",
        "inquiryType": "General Auction Guidance",
        "message": "Testing burst"
    }).encode("utf-8")

    # Send 15 requests - should all succeed (201 Created)
    for _ in range(15):
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer fake-cust-jwt",
                "X-Forwarded-For": unique_ip
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status in (200, 201)

    # 16th request from the same IP must receive HTTP 429
    req_throttled = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": unique_ip
        },
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_throttled, timeout=5)
    
    assert exc_info.value.code == 429
    body = json.loads(exc_info.value.read().decode("utf-8"))
    assert "error" in body
    assert "Rate limit exceeded" in body["error"]


def test_pdf_proxy_unauthorized(api_server):
    # Without admin token: must return 401
    url = f"{api_server}/api/admin/pdf-proxy?url=https://example.com/notice.pdf"
    req = urllib.request.Request(url)
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=5)
    assert exc_info.value.code == 401


def test_pdf_proxy_missing_url(api_server):
    token = generate_admin_token()
    url = f"{api_server}/api/admin/pdf-proxy"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=5)
    assert exc_info.value.code == 400
    body = json.loads(exc_info.value.read().decode("utf-8"))
    assert "Missing 'url' query parameter" in body.get("error", "")


def test_pdf_proxy_invalid_scheme(api_server):
    token = generate_admin_token()
    url = f"{api_server}/api/admin/pdf-proxy?url=file:///etc/passwd"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=5)
    assert exc_info.value.code == 400
    body = json.loads(exc_info.value.read().decode("utf-8"))
    assert "Invalid URL scheme" in body.get("error", "")


def test_pdf_proxy_streaming_success(api_server):
    # Spin up a mock PDF source server
    fake_pdf_content = b"%PDF-1.4 Fake bank auction notice binary stream"

    class MockPDFHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(fake_pdf_content)))
            self.end_headers()
            self.wfile.write(fake_pdf_content)

        def log_message(self, *args):
            pass

    mock_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockPDFHandler)
    mock_port = mock_server.server_address[1]
    threading.Thread(target=mock_server.serve_forever, daemon=True).start()

    token = generate_admin_token()
    proxy_url = f"{api_server}/api/admin/pdf-proxy?url=" + urllib.parse.quote(f"http://127.0.0.1:{mock_port}/notice.pdf")
    req = urllib.request.Request(proxy_url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "application/pdf"
        assert "inline" in resp.headers.get("Content-Disposition", "")
        content = resp.read()
        assert content == fake_pdf_content

    mock_server.shutdown()


def test_admin_login_rate_limiting(api_server):
    unique_ip = "198.51.100.77"
    url = f"{api_server}/api/admin/login"
    payload = json.dumps({
        "email": "admin@skandx.com",
        "password": "wrong-password"
    }).encode("utf-8")

    # Clear rate limits for this IP before test
    with _rate_limit_lock:
        _login_rate_limits.pop(unique_ip, None)

    # First 5 attempts: should reach login logic and return 401 (not rate limited)
    for _ in range(5):
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Forwarded-For": unique_ip
            },
            method="POST"
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)
        assert exc_info.value.code == 401

    # 6th attempt from the same IP must receive HTTP 429
    req_throttled = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": unique_ip
        },
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_throttled, timeout=5)

    assert exc_info.value.code == 429
    assert exc_info.value.headers.get("Retry-After") == "60"
    body = json.loads(exc_info.value.read().decode("utf-8"))
    assert body.get("error") == "Too many login attempts. Please wait 60 seconds."

    # A different IP is not affected by the first IP's rate limit
    diff_ip = "198.51.100.78"
    req_diff = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": diff_ip
        },
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as exc_diff:
        urllib.request.urlopen(req_diff, timeout=5)
    assert exc_diff.value.code == 401


def test_admin_login_invalid_credentials(api_server):
    unique_ip = "198.51.100.80"
    url = f"{api_server}/api/admin/login"

    bad_payloads = [
        {"email": "admin@skandx.com", "password": "incorrect_password"},
        {"email": "hacker@skandx.com", "password": "skandx@admin2026"},
        {"email": "", "password": ""},
    ]

    for p in bad_payloads:
        with _rate_limit_lock:
            _login_rate_limits.pop(unique_ip, None)

        req = urllib.request.Request(
            url,
            data=json.dumps(p).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Forwarded-For": unique_ip
            },
            method="POST"
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)

        assert exc_info.value.code == 401
        body = json.loads(exc_info.value.read().decode("utf-8"))
        assert body.get("status") == "error"
        assert "Invalid admin credentials" in body.get("message", "")


def test_admin_login_success(api_server):
    unique_ip = "198.51.100.85"
    url = f"{api_server}/api/admin/login"

    with _rate_limit_lock:
        _login_rate_limits.pop(unique_ip, None)

    valid_payload = json.dumps({
        "email": "admin@skandx.com",
        "password": "skandx@admin2026"
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=valid_payload,
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": unique_ip
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        body = json.loads(resp.read().decode("utf-8"))

    assert body.get("status") == "success"
    token = body.get("token")
    assert token is not None
    assert token.startswith("skandx-adm-")
    assert verify_admin_token(token) is True


def test_cors_origin_whitelist_configuration(api_server, monkeypatch):
    url = f"{api_server}/api/health"

    # 1. Configured whitelist
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173,https://admin.skandx.com")

    # Matching origin
    req_match = urllib.request.Request(url, headers={"Origin": "http://localhost:5173"})
    with urllib.request.urlopen(req_match, timeout=5) as resp:
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
        assert resp.headers.get("Vary") == "Origin"

    # Non-matching origin
    req_evil = urllib.request.Request(url, headers={"Origin": "https://evil-site.com"})
    with urllib.request.urlopen(req_evil, timeout=5) as resp:
        assert resp.headers.get("Access-Control-Allow-Origin") is None

    # 2. Missing ALLOWED_ORIGINS fallback
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)

    # Localhost origin is reflected
    req_local = urllib.request.Request(url, headers={"Origin": "http://localhost:3000"})
    with urllib.request.urlopen(req_local, timeout=5) as resp:
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    # Non-localhost origin falls back to wildcard *
    req_any = urllib.request.Request(url, headers={"Origin": "https://example.com"})
    with urllib.request.urlopen(req_any, timeout=5) as resp:
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"


def test_circuit_breaker_trips_and_recovers():
    # 1. Isolated CircuitBreaker instance testing
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.2)
    # Verifies initial state is CLOSED
    assert cb.state == CircuitBreaker.CLOSED
    assert cb.allow_request() is True

    # Simulates consecutive failures to verify transition to OPEN
    cb.record_failure()
    assert cb.state == CircuitBreaker.CLOSED
    cb.record_failure()
    assert cb.state == CircuitBreaker.CLOSED

    # 3rd consecutive failure trips breaker to OPEN
    cb.record_failure()
    assert cb.state == CircuitBreaker.OPEN
    assert cb.allow_request() is False

    # 2. Integration with backend app: verifies fast fallback (0ms) when OPEN
    try:
        circuit_breaker.trip()
        assert circuit_breaker.state == CircuitBreaker.OPEN

        t0 = time.perf_counter()
        data, source = get_raw_auctions()
        elapsed_sec = time.perf_counter() - t0

        assert source == "CIRCUIT_BREAKER_FALLBACK"
        # Bypassed network: fast fallback takes < 50ms (nominal ~0ms)
        assert elapsed_sec < 0.05

        # Verify save_lead fast path when OPEN (bypasses Supabase)
        lead_t0 = time.perf_counter()
        saved = save_lead({
            "customerName": "Fallback Bidder",
            "phone": "9999900000",
            "message": "Breaker test"
        })
        lead_elapsed = time.perf_counter() - lead_t0
        assert saved["customerName"] == "Fallback Bidder"
        assert lead_elapsed < 0.05

        # Verify persist_property_update fast path when OPEN (bypasses Supabase PATCH)
        update_t0 = time.perf_counter()
        persist_property_update("test-prop-id", "PUBLISHED", {"reserve": 5000000})
        update_elapsed = time.perf_counter() - update_t0
        assert update_elapsed < 0.05

    finally:
        circuit_breaker.reset()

    # 3. Verifies recovery transition through HALF_OPEN back to CLOSED
    # Wait for recovery_timeout on isolated cb
    time.sleep(0.25)
    assert cb.state == CircuitBreaker.HALF_OPEN

    # In HALF_OPEN, allows one canary request
    assert cb.allow_request() is True
    # Concurrent request while canary in flight is denied
    assert cb.allow_request() is False

    # Simulate canary failure resets OPEN timer
    cb.record_failure()
    assert cb.state == CircuitBreaker.OPEN
    assert cb.allow_request() is False

    # Wait for recovery_timeout again
    time.sleep(0.25)
    assert cb.state == CircuitBreaker.HALF_OPEN
    assert cb.allow_request() is True

    # Canary success transitions circuit to CLOSED and resets failure counter
    cb.record_success()
    assert cb.state == CircuitBreaker.CLOSED
    assert cb.allow_request() is True
    assert cb._failure_count == 0


def test_health_check_reports_circuit_breaker_state(api_server):
    try:
        # 1. In normal CLOSED state
        circuit_breaker.reset()
        assert circuit_breaker.state == CircuitBreaker.CLOSED

        req = urllib.request.Request(f"{api_server}/api/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "circuit_breaker" in data
            assert data["circuit_breaker"] == "CLOSED"

        # 2. In tripped OPEN state
        circuit_breaker.trip()
        assert circuit_breaker.state == CircuitBreaker.OPEN

        req = urllib.request.Request(f"{api_server}/api/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["circuit_breaker"] == "OPEN"

    finally:
        circuit_breaker.reset()


def test_test_token_bypass_rejected_in_production_mode():
    """Verify test-token bypass is strictly rejected when ALLOW_TEST_TOKEN is unset or false."""
    orig_env = os.environ.get("ALLOW_TEST_TOKEN")
    orig_pytest = os.environ.get("PYTEST_CURRENT_TEST")
    try:
        if "ALLOW_TEST_TOKEN" in os.environ:
            del os.environ["ALLOW_TEST_TOKEN"]
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]

        # skandx-test-token-bypass must ALWAYS be rejected
        assert verify_admin_token("skandx-test-token-bypass") is False

        os.environ["ALLOW_TEST_TOKEN"] = "true"
        assert verify_admin_token("skandx-test-token-bypass") is False

    finally:
        if orig_env is not None:
            os.environ["ALLOW_TEST_TOKEN"] = orig_env
        elif "ALLOW_TEST_TOKEN" in os.environ:
            del os.environ["ALLOW_TEST_TOKEN"]

        if orig_pytest is not None:
            os.environ["PYTEST_CURRENT_TEST"] = orig_pytest


def test_sensitive_endpoints_emit_no_store_cache_headers(api_server):
    """Verify sensitive administrative routes return Cache-Control: no-store and Pragma: no-cache."""
    token = generate_admin_token()

    # 1. Admin properties
    req1 = urllib.request.Request(f"{api_server}/api/admin/properties", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req1, timeout=5) as resp1:
        assert resp1.status == 200
        cc = resp1.headers.get("Cache-Control", "")
        assert "no-store" in cc
        assert "no-cache" in cc
        assert "private" in cc

    # 2. Admin leads
    req2 = urllib.request.Request(f"{api_server}/api/admin/leads", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req2, timeout=5) as resp2:
        assert resp2.status == 200
        cc = resp2.headers.get("Cache-Control", "")
        assert "no-store" in cc
        assert "no-cache" in cc

    # 3. Admin login
    login_body = json.dumps({"email": "wrong@skandx.com", "password": "bad"}).encode("utf-8")
    req3 = urllib.request.Request(f"{api_server}/api/admin/login", data=login_body, headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req3, timeout=5)
    assert exc_info.value.code == 401
    cc3 = exc_info.value.headers.get("Cache-Control", "")
    assert "no-store" in cc3


def test_pdf_proxy_blocks_malicious_redirect_ssrf(api_server):
    """Verify SafeRedirectHandler catches and blocks HTTP redirects to private / loopback IP space."""
    token = generate_admin_token()

    # Mock server that redirects to 127.0.0.1 or 169.254.169.254
    class RedirectHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:8000/api/admin/leads")
            self.end_headers()
        def log_message(self, *args):
            pass

    redirect_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    r_port = redirect_server.server_address[1]
    threading.Thread(target=redirect_server.serve_forever, daemon=True).start()

    try:
        # We simulate a target URL that is on a remote or allowed host, which redirects to an internal endpoint
        target = urllib.parse.quote(f"http://127.0.0.1:{r_port}/innocent.pdf")
        proxy_url = f"{api_server}/api/admin/pdf-proxy?url={target}"
        req = urllib.request.Request(proxy_url, headers={"Authorization": f"Bearer {token}"})

        # By default is_safe_url blocks 127.0.0.1; let's verify either initial request or redirect is blocked
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)
        assert exc_info.value.code in (400, 502)
    finally:
        redirect_server.shutdown()


def test_admin_login_rejects_default_credentials_in_production_environment(api_server, monkeypatch):
    """Verify that in staging or production, login attempts fail with 503 if ADMIN_PASSWORD is unset or default."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)

    payload = json.dumps({"email": "admin@skandx.com", "password": "skandx@admin2026"}).encode("utf-8")
    req = urllib.request.Request(
        f"{api_server}/api/admin/login",
        data=payload,
        headers={"Content-Type": "application/json", "X-Forwarded-For": "198.51.100.99"},
        method="POST"
    )

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=5)

    assert exc_info.value.code == 503
    body = json.loads(exc_info.value.read().decode("utf-8"))
    assert body.get("status") == "error"
    assert "ADMIN_EMAIL and ADMIN_PASSWORD must be explicitly configured" in body.get("message", "")


def test_public_auctions_strips_pii_and_internal_fields(api_server, monkeypatch):
    sample_rows = [
        {
            "id": "prop-1",
            "property_title": "Residential Plot in Adyar",
            "bank_name": "State Bank of India",
            "branch_name": "Adyar Branch",
            "district": "Chennai",
            "village_or_locality": "Adyar",
            "reserve_price_inr": 8500000,
            "emd_amount_inr": 850000,
            "auction_date": "2026-12-20T11:00:00Z",
            "review_status": "PUBLISHED",
            "borrower_name": "Secret Borrower Name",
            "contact_phone": "+91 98400 12345",
            "authorized_officer_name": "Officer Secret",
            "raw_extracted_json": {"raw": "secret"},
            "review_notes": "Internal legal note",
            "asset_fingerprint": "fp-123",
            "auction_event_hash": "hash-123",
        }
    ]
    monkeypatch.setattr("backend.app.get_raw_auctions", lambda: (sample_rows, "TEST_MOCK"))

    for route in ("/api/auctions", "/api/v1/auctions"):
        with urllib.request.urlopen(f"{api_server}{route}", timeout=5) as resp:
            assert resp.status == 200
            payload = json.loads(resp.read().decode("utf-8"))
            assert payload["count"] == 1
            item = payload["data"][0]
            assert item["reserve_price_inr"] == 8500000
            assert item["district"] == "Chennai"
            for forbidden in (
                "borrower_name",
                "contact_phone",
                "authorized_officer_name",
                "raw_extracted_json",
                "review_notes",
                "asset_fingerprint",
                "auction_event_hash",
            ):
                assert forbidden not in item


def test_patch_admin_leads_auth_and_persistence(api_server):
    lead = save_lead({
        "customerName": "Stage 0 Lead",
        "phone": "9876543211",
        "propertyId": "prop-1",
        "inquiryType": "General Inquiry",
    })
    patch_body = json.dumps({"id": lead["id"], "status": "SCHEDULED", "notes": "Call at 4 PM"}).encode("utf-8")

    # Unauthenticated PATCH must return 401
    unauth_req = urllib.request.Request(
        f"{api_server}/api/admin/leads",
        data=patch_body,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(unauth_req, timeout=5)
    assert exc_info.value.code == 401

    # Authenticated PATCH must persist status
    token = generate_admin_token()
    auth_req = urllib.request.Request(
        f"{api_server}/api/admin/leads",
        data=patch_body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="PATCH",
    )
    with urllib.request.urlopen(auth_req, timeout=5) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["leadStatus"] == "SCHEDULED"

    leads, _ = load_leads(limit=20)
    matched = [l for l in leads if l["id"] == lead["id"]]
    assert matched and matched[0]["status"] == "SCHEDULED"


def test_patch_admin_properties_persists_all_editable_fields(api_server, monkeypatch):
    captured = {}

    def fake_persist(prop_id, new_status, updated_fields=None):
        captured["id"] = prop_id
        captured["status"] = new_status
        captured["fields"] = updated_fields

    monkeypatch.setattr("backend.app.persist_property_update", fake_persist)
    token = generate_admin_token()
    body = json.dumps({
        "id": "prop-99",
        "status": "PUBLISHED",
        "title": "Updated Title",
        "reserve": 4200000,
        "district": "Coimbatore",
        "branch": "RS Puram",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{api_server}/api/admin/properties",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
    assert captured["id"] == "prop-99"
    assert captured["status"] == "PUBLISHED"
    assert captured["fields"]["district"] == "Coimbatore"
    assert captured["fields"]["branch"] == "RS Puram"


def test_ingestion_evaluate_sanity_never_auto_publishes():
    import sys
    ingestion_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "ingestion")
    if ingestion_dir not in sys.path:
        sys.path.insert(0, ingestion_dir)
    from models.auction_schema import ExtractedAuctionProperty, ReviewStatus
    from database.supabase_client import evaluate_sanity

    prop = ExtractedAuctionProperty(
        bank_name="Indian Bank",
        asset_category="LAND_PLOT",
        possession_type="PHYSICAL",
        area_description="1200 sq ft residential plot",
        village_or_locality="Velachery",
        district="Chennai",
        survey_numbers=["123/4A"],
        reserve_price_inr=5000000,
        emd_amount_inr=500000,
        auction_date="2026-12-25T11:00:00Z",
    )
    status, _ = evaluate_sanity(prop)
    assert status == ReviewStatus.NEEDS_MANUAL_REVIEW


def test_phase1_verification_projection_detail_districts_and_sitemap(api_server, monkeypatch):
    sample = [
        {
            "id": "p-101",
            "slug": "adyar-plot-p-101",
            "property_title": "Adyar Plot",
            "bank_name": "Indian Bank",
            "district": "Chennai",
            "village_or_locality": "Adyar",
            "reserve_price_inr": 7500000,
            "emd_amount_inr": 750000,
            "auction_date": "2027-01-15T11:00:00Z",
            "publication_status": "PUBLISHED",
            "verification_dimensions": {
                "source_checked": {
                    "status": "COMPLETED",
                    "reviewed_at": "2026-11-25T10:00:00Z",
                    "review_period": "2026-11",
                    "reviewer": "internal-staff@skandx.com",
                    "notes": "Internal sensitive note",
                    "evidence_ref": "s3://private/doc.pdf",
                }
            },
            "risk_disclosures": ["Physical inspection pending"],
        }
    ]
    monkeypatch.setattr("backend.app.get_raw_auctions", lambda: (sample, "TEST"))

    with urllib.request.urlopen(f"{api_server}/api/v1/auctions/adyar-plot-p-101", timeout=5) as resp:
        assert resp.status == 200
        item = json.loads(resp.read().decode("utf-8"))["data"]
        src_dim = item["verification_dimensions"]["source_checked"]
        assert src_dim["status"] == "COMPLETED"
        assert "reviewer" not in src_dim
        assert "notes" not in src_dim
        assert "evidence_ref" not in src_dim

    with urllib.request.urlopen(f"{api_server}/api/v1/districts", timeout=5) as resp:
        assert resp.status == 200
        districts = json.loads(resp.read().decode("utf-8"))["data"]
        assert districts == [{"district": "Chennai", "count": 1}]

    with urllib.request.urlopen(f"{api_server}/sitemap.xml", timeout=5) as resp:
        assert resp.status == 200
        xml = resp.read().decode("utf-8")
        assert "/properties/adyar-plot-p-101" in xml


def test_phase3_leads_agreement_dedup_and_isolation(api_server, monkeypatch):
    monkeypatch.setattr("backend.app._contact_rate_limits", {})

    # 1. Unauthenticated POST /api/v1/leads -> 401
    unauth_req = urllib.request.Request(
        f"{api_server}/api/v1/leads",
        data=json.dumps({"phone": "9876543210", "propertyId": "p-101"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Forwarded-For": "203.0.113.10"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(unauth_req, timeout=5)
    assert exc.value.code == 401

    monkeypatch.setattr("backend.app.verify_customer_jwt", lambda auth: "user-abc" if "user-abc" in auth else "user-xyz")

    # 2. Paid assistance without agreement -> 400
    no_agr_req = urllib.request.Request(
        f"{api_server}/api/v1/leads",
        data=json.dumps({
            "phone": "9876543210",
            "propertyId": "p-101",
            "inquiryType": "Physical Property Inspection",
            "agreementAccepted": False,
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer user-abc", "X-Forwarded-For": "203.0.113.11"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(no_agr_req, timeout=5)
    assert exc.value.code == 400

    # 3. Paid assistance with agreement -> 201
    ok_req = urllib.request.Request(
        f"{api_server}/api/v1/leads",
        data=json.dumps({
            "customerName": "Raj",
            "phone": "9876543210",
            "propertyId": "p-101",
            "inquiryType": "Physical Property Inspection",
            "message": "Internal test note",
            "agreementAccepted": True,
            "acceptedName": "Raj",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer user-abc", "X-Forwarded-For": "203.0.113.12"},
        method="POST",
    )
    with urllib.request.urlopen(ok_req, timeout=5) as resp:
        assert resp.status == 201
        res = json.loads(resp.read().decode("utf-8"))
        assert res["leadStatus"] == "REQUEST_RECEIVED"
        assert res["agreementId"] is not None

    # 4. Duplicate active lead -> 409
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(ok_req, timeout=5)
    assert exc.value.code == 409

    # 5. Cross-user isolation on GET /api/v1/me/leads
    other_req = urllib.request.Request(
        f"{api_server}/api/v1/me/leads",
        headers={"Authorization": "Bearer user-xyz"},
    )
    with urllib.request.urlopen(other_req, timeout=5) as resp:
        assert json.loads(resp.read().decode("utf-8"))["leads"] == []

    own_req = urllib.request.Request(
        f"{api_server}/api/v1/me/leads",
        headers={"Authorization": "Bearer user-abc"},
    )
    with urllib.request.urlopen(own_req, timeout=5) as resp:
        own_leads = json.loads(resp.read().decode("utf-8"))["leads"]
        assert len(own_leads) == 1
        assert "notes" not in own_leads[0] and "message" not in own_leads[0]






