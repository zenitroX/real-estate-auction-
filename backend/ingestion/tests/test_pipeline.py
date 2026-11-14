"""
Unit and integration test suite for Bank Auction Scraping & Multimodal OCR Microservice.
Verifies:
  1. Pydantic schema validation for bilingual SARFAESI notices.
  2. area_sqft land unit conversion logic (Cents, Acres, Grounds, Sq.m).
  3. Deterministic asset fingerprinting across heterogeneous survey number formats.
  4. Sanity auto-moderation checks (EMD threshold, low reserve price, missing surveys).
  5. Repeat auction price drop calculation and history tracking.
  6. Document router pathway selection (Digital Text vs Multimodal Vision).
"""

import pytest
from database.fingerprint import (
    generate_asset_fingerprint,
    generate_auction_event_hash,
    normalize_survey_number,
)
from database.supabase_client import evaluate_sanity, prepare_auction_record
from models.auction_schema import (
    AssetCategory,
    ExtractedAuctionProperty,
    NoticeExtractionBatch,
    PossessionType,
    PropertyBoundaries,
    ReviewStatus,
    convert_area_description_to_sqft,
)
from ocr_pipeline.pdf_router import RoutePath, route_document

# Sample bilingual (Tamil + English) SARFAESI sale notice text mock
SAMPLE_BILINGUAL_SARFAESI_TEXT = """
STATE BANK OF INDIA - STRESSED ASSETS RECOVERY BRANCH (SARB), COIMBATORE
இ-ஏல விற்பனை அறிவிப்பு (E-Auction Sale Notice under SARFAESI Act, 2002)

Borrower: Thiru. K. Rangarajan, S/o. Kandasamy
Property 1:
All that piece and parcel of land and residential building situated at Coimbatore District,
Sulur Taluk, No. 24, Irugur Village, S.F. No. 124/2A and S.F. No. 125, Patta No. 452.
Extent: Land measuring 5 Cents (2178 Sq.ft) with 1200 Sq.ft RCC building.
Boundaries:
North by: 20 feet East-West Road (வடக்கு: 20 அடி ரோடு)
South by: Property of Murugesan (தெற்கு: முருகேசன் இடம்)
East by: S.F. No. 124/2B land (கிழக்கு: க.ச.எண் 124/2B நிலம்)
West by: Panchayat Pipe Line (மேற்கு: பஞ்சாயத்து குழாய்)
Possession Type: நேரடி சுவாதீனம் (Physical Possession)
Reserve Price: Rs. 45,00,000/- (Rupees Forty Five Lakhs Only)
EMD Amount: Rs. 4,50,000/- (10% of Reserve Price)
Bid Increment: Rs. 50,000/-
Auction Date & Time: 25-11-2026 from 11:00 AM to 01:00 PM
EMD Submission Last Date: 23-11-2026 up to 5:00 PM

Borrower: M/s. Annur Agro Enterprises
Property 2:
Commercial warehouse situated at Annur Village, S.F. No. 89/1, Door No. 12/B.
Extent: 1 Acre 25 Cents.
Possession Type: அடையாள சுவாதீனம் (Symbolic Possession)
Reserve Price: Rs. 1,20,00,000/-
EMD Amount: Rs. 12,00,000/-
Auction Date & Time: 25-11-2026 from 02:00 PM to 04:00 PM
Portal: https://baanknet.com
"""


def test_bilingual_pydantic_schema_validation():
    """Verify that structured properties extracted from bilingual notice validate cleanly against Pydantic V2 schema."""
    prop1 = ExtractedAuctionProperty(
        bank_name="State Bank of India",
        branch_name="SARB Coimbatore",
        borrower_name="Thiru. K. Rangarajan",
        asset_category=AssetCategory.HOUSE_VILLA,
        possession_type=PossessionType.PHYSICAL,
        survey_numbers=["S.F. No. 124/2A", "125"],
        patta_or_door_no="Patta No. 452",
        village_or_locality="Irugur",
        taluk="Sulur",
        district="Coimbatore",
        state="Tamil Nadu",
        pincode="641103",
        area_description="5 Cents with 1200 Sq.ft RCC building",
        area_sqft=2178.0,
        boundaries=PropertyBoundaries(
            north="20 feet East-West Road",
            south="Property of Murugesan",
            east="S.F. No. 124/2B land",
            west="Panchayat Pipe Line",
        ),
        reserve_price_inr=4500000,
        emd_amount_inr=450000,
        bid_increment_inr=50000,
        emd_last_date="2026-11-23T17:00:00",
        auction_date="2026-11-25T11:00:00",
        bidding_portal_url="https://baanknet.com",
    )

    prop2 = ExtractedAuctionProperty(
        bank_name="State Bank of India",
        borrower_name="M/s. Annur Agro Enterprises",
        asset_category=AssetCategory.COMMERCIAL,
        possession_type=PossessionType.SYMBOLIC,
        survey_numbers=["89/1"],
        patta_or_door_no="Door No. 12/B",
        village_or_locality="Annur",
        district="Coimbatore",
        state="Tamil Nadu",
        area_description="1 Acre 25 Cents",
        reserve_price_inr=12000000,
        emd_amount_inr=1200000,
        auction_date="2026-11-25T14:00:00",
        bidding_portal_url="https://baanknet.com",
    )

    batch = NoticeExtractionBatch(properties=[prop1, prop2])

    assert len(batch.properties) == 2
    assert batch.properties[0].possession_type == PossessionType.PHYSICAL
    assert batch.properties[1].possession_type == PossessionType.SYMBOLIC
    assert batch.properties[0].reserve_price_inr == 4500000
    assert batch.properties[1].reserve_price_inr == 12000000
    # Auto-computed area_sqft for prop2 (1 Acre 25 Cents: 43560 + 25 * 435.6 = 54450)
    assert batch.properties[1].area_sqft == 54450.0


def test_area_sqft_conversion_logic():
    """Verify accurate conversion of diverse Indian and regional Tamil Nadu land units to square feet."""
    # 1 Cent = 435.6 sqft
    assert convert_area_description_to_sqft("10 Cents") == pytest.approx(4356.0, rel=1e-3)
    assert convert_area_description_to_sqft("5.5 Cents") == pytest.approx(2395.8, rel=1e-3)

    # 1 Ground = 2,400 sqft
    assert convert_area_description_to_sqft("2 Grounds") == pytest.approx(4800.0, rel=1e-3)

    # 1 Acre = 43,560 sqft
    assert convert_area_description_to_sqft("2 Acres") == pytest.approx(87120.0, rel=1e-3)

    # Combined: 1 Acre 25 Cents -> 43560 + 10890 = 54,450 sqft
    assert convert_area_description_to_sqft("1 Acre 25 Cents") == pytest.approx(54450.0, rel=1e-3)
    assert convert_area_description_to_sqft("1 Acre and 25 Cents") == pytest.approx(54450.0, rel=1e-3)

    # Square Feet
    assert convert_area_description_to_sqft("2400 Sq.ft") == pytest.approx(2400.0, rel=1e-3)
    assert convert_area_description_to_sqft("1500 sqft") == pytest.approx(1500.0, rel=1e-3)

    # 1 Sq. Meter = 10.7639 sqft
    assert convert_area_description_to_sqft("100 Sq. Meters") == pytest.approx(1076.39, rel=1e-3)

    # 1 Hectare = 107,639 sqft
    assert convert_area_description_to_sqft("1 Hectare") == pytest.approx(107639.0, rel=1e-3)


def test_asset_fingerprint_deterministic_and_fuzzy_format_matching():
    """
    Verify that generate_asset_fingerprint produces identical hashes even when
    survey numbers have varied prefixes, punctuation, spacing, or ordering:
    e.g. 'S.F. No. 124/2A, 125' vs '125, sfno 124/2a'.
    """
    bank = "Canara Bank"
    district = "Coimbatore"

    # Variant A: comma-separated with legal prefixes
    surveys_a = ["S.F. No. 124/2A, 125"]
    hash_a = generate_asset_fingerprint(bank, district, surveys_a)

    # Variant B: reversed order, lowercase prefix 'sfno'
    surveys_b = ["125, sfno 124/2a"]
    hash_b = generate_asset_fingerprint(bank, district, surveys_b)

    # Variant C: individual list items with different casing and spacing
    surveys_c = ["SF No: 124/2A", "Survey Number 125"]
    hash_c = generate_asset_fingerprint("canara bank", "COIMBATORE", surveys_c)

    assert hash_a == hash_b, f"Hash mismatch between variant A ({hash_a}) and B ({hash_b})"
    assert hash_a == hash_c, f"Hash mismatch between variant A ({hash_a}) and C ({hash_c})"


def test_auction_event_hash_deterministic():
    """Verify that auction event hash incorporates asset fingerprint and auction date (YYYY-MM-DD)."""
    fp = "abc123assetfingerprint"
    date_a = "2026-11-25T11:00:00+05:30"
    date_b = "2026-11-25T14:30:00Z"  # Same date prefix, different time
    date_c = "2026-12-10T11:00:00"

    hash_a = generate_auction_event_hash(fp, date_a)
    hash_b = generate_auction_event_hash(fp, date_b)
    hash_c = generate_auction_event_hash(fp, date_c)

    assert hash_a == hash_b
    assert hash_a != hash_c


def test_sanity_checker_catches_invalid_emd():
    """
    Verify that evaluate_sanity flags 'NEEDS_MANUAL_REVIEW' when:
      - EMD > 25% of reserve price (or EMD > reserve price)
      - EMD <= 0
      - Reserve price < 50,000 INR
      - Survey numbers are empty
    """
    # 1. Invalid EMD exceeding 25% (here EMD is 100% of reserve price)
    invalid_prop = ExtractedAuctionProperty(
        bank_name="Indian Overseas Bank",
        asset_category=AssetCategory.LAND_PLOT,
        possession_type=PossessionType.SYMBOLIC,
        survey_numbers=["45/2"],
        village_or_locality="Udumalpet",
        district="Tiruppur",
        area_description="10 Cents",
        reserve_price_inr=2000000,
        emd_amount_inr=2000000,  # Invalid: 100% instead of standard ~10%
        auction_date="2026-12-01T11:00:00",
    )
    status, reason = evaluate_sanity(invalid_prop)
    assert status == ReviewStatus.NEEDS_MANUAL_REVIEW
    assert "exceeds 25%" in (reason or "")

    # 2. Non-positive EMD
    invalid_prop.emd_amount_inr = 0
    status, reason = evaluate_sanity(invalid_prop)
    assert status == ReviewStatus.NEEDS_MANUAL_REVIEW
    assert "non-positive EMD" in (reason or "")

    # 3. Unusually low reserve price (< 50,000 INR)
    invalid_prop.emd_amount_inr = 3000
    invalid_prop.reserve_price_inr = 30000
    status, reason = evaluate_sanity(invalid_prop)
    assert status == ReviewStatus.NEEDS_MANUAL_REVIEW
    assert "below 50,000 INR" in (reason or "")

    # 4. Missing survey numbers
    valid_amounts_prop = ExtractedAuctionProperty(
        bank_name="Indian Overseas Bank",
        asset_category=AssetCategory.LAND_PLOT,
        possession_type=PossessionType.SYMBOLIC,
        survey_numbers=[],
        village_or_locality="Udumalpet",
        district="Tiruppur",
        area_description="10 Cents",
        reserve_price_inr=2000000,
        emd_amount_inr=200000,
        auction_date="2026-12-01T11:00:00",
    )
    status, reason = evaluate_sanity(valid_amounts_prop)
    assert status == ReviewStatus.NEEDS_MANUAL_REVIEW
    assert "No survey numbers" in (reason or "")

    # 5. Clean, valid property -> PUBLISHED
    valid_prop = ExtractedAuctionProperty(
        bank_name="Indian Overseas Bank",
        asset_category=AssetCategory.LAND_PLOT,
        possession_type=PossessionType.SYMBOLIC,
        survey_numbers=["45/2"],
        village_or_locality="Udumalpet",
        district="Tiruppur",
        area_description="10 Cents",
        reserve_price_inr=2000000,
        emd_amount_inr=200000,  # Exactly 10%
        auction_date="2026-12-01T11:00:00",
    )
    status, reason = evaluate_sanity(valid_prop)
    assert status == ReviewStatus.PUBLISHED
    assert reason is None


def test_price_drop_calculation_on_repeat_auction():
    """Verify that when an asset is re-auctioned with a price drop, previous price and drop % are captured."""
    property_data = ExtractedAuctionProperty(
        bank_name="Canara Bank",
        asset_category=AssetCategory.FLAT_APARTMENT,
        possession_type=PossessionType.PHYSICAL,
        survey_numbers=["201/1"],
        patta_or_door_no="Flat No. 3B",
        village_or_locality="R.S. Puram",
        district="Coimbatore",
        area_description="1250 Sq.ft",
        reserve_price_inr=4500000,  # Dropped from 50,00,000
        emd_amount_inr=450000,
        auction_date="2026-12-15T11:00:00",
    )

    # Simulate prior auction at Rs. 50 Lakhs
    record = prepare_auction_record(
        property_data=property_data,
        source_portal="Baanknet",
        source_pdf_url="notice_dec.pdf",
        previous_price=5000000,
    )

    assert record["reserve_price_inr"] == 4500000
    assert record["previous_reserve_price_inr"] == 5000000
    # Drop: ((50,00,000 - 45,00,000) / 50,00,000) * 100 = 10.00%
    assert record["price_drop_percentage"] == 10.0
    assert record["review_status"] == ReviewStatus.PUBLISHED.value


def test_document_router_image_handling(tmp_path):
    """Verify that image files (newspaper clippings) route directly to Multimodal Vision."""
    sample_img = tmp_path / "newspaper_notice.jpg"
    sample_img.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 50)

    routed = route_document(sample_img)
    assert routed.route == RoutePath.MULTIMODAL_VISION
    assert "image" in routed.mime_type
    assert "newspaper clipping" in routed.reason


def test_document_router_digital_pdf_handling(tmp_path):
    """Verify that a genuine digital text PDF with SARFAESI keywords routes to DIGITAL_TEXT."""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF (fitz) not available")

    pdf_path = tmp_path / "digital_sale_notice.pdf"
    doc = fitz.open()
    page = doc.new_page()
    sample_text = (
        "SARFAESI ACT 2002 SALE NOTICE. State Bank of India E-Auction Sale. "
        "The undersigned authorized officer hereby gives notice that the property "
        "bearing Survey No. 45/1 is put for auction. Reserve price is Rs. 50,00,000. "
        "EMD amount is Rs. 5,00,000. Possession type is Physical Possession. "
        "Auction date is 25-11-2026. Bidding portal is baanknet.com. "
        "Detailed terms and conditions are available at the bank portal. "
    ) * 3  # Ensure > 300 characters
    page.insert_textbox(fitz.Rect(50, 50, 550, 800), sample_text)
    doc.save(str(pdf_path))
    doc.close()

    routed = route_document(pdf_path)
    assert routed.route == RoutePath.DIGITAL_TEXT
    assert "Digital PDF" in routed.reason
    assert "sarfaesi" in (routed.text_content or "").lower()


def test_batch_json_parsing_and_pydantic_export():
    """Verify serialization and deserialization of NoticeExtractionBatch."""
    data = {
        "properties": [
            {
                "bank_name": "Canara Bank",
                "borrower_name": "R. Kumar",
                "asset_category": "LAND_PLOT",
                "possession_type": "PHYSICAL",
                "survey_numbers": ["102/1A", "102/1B"],
                "village_or_locality": "Perur",
                "district": "Coimbatore",
                "state": "Tamil Nadu",
                "area_description": "2400 Sq.ft",
                "reserve_price_inr": 3500000,
                "emd_amount_inr": 350000,
                "auction_date": "2026-11-30T10:00:00",
            }
        ]
    }
    batch = NoticeExtractionBatch.model_validate(data)
    assert len(batch.properties) == 1
    assert batch.properties[0].area_sqft == 2400.0

    # Ensure json export works
    json_str = batch.model_dump_json()
    assert "Canara Bank" in json_str
    assert "3500000" in json_str
