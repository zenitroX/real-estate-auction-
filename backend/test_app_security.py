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
    _contact_rate_limits,
    _rate_limit_lock,
    ApiRequestHandler,
)

def test_admin_token_generation_and_verification():
    token = generate_admin_token()
    assert token.startswith("skandx-adm-")
    assert verify_admin_token(token) is True

def test_admin_token_rejects_unauthorized_forged_tokens():
    # Vector 1 test: Attackers passing forged prefixes MUST be rejected
    assert verify_admin_token("skandx-adm-forged-token") is False
    assert verify_admin_token("skandx-adm-anything") is False
    assert verify_admin_token("Bearer skandx-adm-12345") is False
    assert verify_admin_token("") is False
    assert verify_admin_token(None) is False

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
    # Mock save_lead to avoid synchronous Supabase cloud network calls during local burst test
    monkeypatch.setattr("backend.app.save_lead", lambda data: {"id": "lead-mock", **data})

    unique_ip = "198.51.100.42"
    url = f"{api_server}/api/contact"
    payload = json.dumps({
        "customerName": "Burst Tester",
        "phone": "9876543210",
        "message": "Testing burst"
    }).encode("utf-8")

    # Send 15 requests - should all succeed (201 Created)
    for _ in range(15):
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
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
