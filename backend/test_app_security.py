import time
from backend.app import generate_admin_token, verify_admin_token, save_lead, load_leads

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
