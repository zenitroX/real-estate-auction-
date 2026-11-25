"""
Open-source SARFAESI notice extractor (PyMuPDF text + optional Tesseract OCR + regex parser).
Replaces proprietary Gemini Vision API calls with local deterministic extraction.
"""

import io
import logging
import re
from typing import List, Optional

from models.auction_schema import (
    AssetCategory,
    ExtractedAuctionProperty,
    NoticeExtractionBatch,
    PossessionType,
)
from ocr_pipeline.pdf_router import RoutePath, RoutedDocument

logger = logging.getLogger("auction_engine.opensource_extractor")

KNOWN_BANKS = (
    "State Bank of India",
    "Indian Bank",
    "Indian Overseas Bank",
    "Canara Bank",
    "Bank of Baroda",
    "Punjab National Bank",
    "Union Bank of India",
    "Central Bank of India",
    "UCO Bank",
    "Bank of India",
    "ICICI Bank",
    "HDFC Bank",
    "Axis Bank",
)

TN_DISTRICTS = (
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Trichy", "Salem",
    "Tirunelveli", "Tiruppur", "Erode", "Vellore", "Thoothukudi", "Thanjavur",
    "Dindigul", "Kanchipuram", "Chengalpattu", "Thiruvallur", "Cuddalore",
    "Villupuram", "Karur", "Namakkal", "Hosur", "Krishnagiri", "Nagercoil",
)


def _extract_ocr_text_if_available(routed: RoutedDocument) -> str:
    """Fallback to local Tesseract OCR for scanned PDFs/images when installed."""
    if routed.text_content:
        return routed.text_content
    if not routed.file_bytes:
        return ""
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        logger.warning("pytesseract/Pillow not installed; skipping scanned image OCR.")
        return ""

    try:
        if routed.mime_type == "application/pdf":
            import pymupdf as fitz
            doc = fitz.open(stream=routed.file_bytes, filetype="pdf")
            pages = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                pages.append(pytesseract.image_to_string(img))
            return "\n".join(pages)
        img = Image.open(io.BytesIO(routed.file_bytes))
        return pytesseract.image_to_string(img)
    except Exception as exc:
        logger.warning("Tesseract OCR failed: %s", exc)
        return ""


def _parse_inr_amount(text: str, labels: tuple) -> Optional[int]:
    for label in labels:
        pattern = rf"{label}\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr)?"
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            num = float(m.group(1).replace(",", ""))
            unit = (m.group(2) or "").lower()
            if "crore" in unit or unit == "cr":
                num *= 10000000
            elif "lakh" in unit or "lac" in unit:
                num *= 100000
            return int(round(num))
    return None


class OpenSourceAuctionExtractor:
    """Deterministic open-source SARFAESI notice parser."""

    def extract(self, routed: RoutedDocument) -> NoticeExtractionBatch:
        text = routed.text_content or ""
        if routed.route == RoutePath.MULTIMODAL_VISION and not text:
            text = _extract_ocr_text_if_available(routed)

        if not text.strip():
            return NoticeExtractionBatch(properties=[])

        bank_name = next((b for b in KNOWN_BANKS if b.lower() in text.lower()), "Public Sector Bank")
        district = next((d for d in TN_DISTRICTS if d.lower() in text.lower()), "Chennai")

        reserve = _parse_inr_amount(text, ("reserve price", "upset price")) or 1000000
        emd = _parse_inr_amount(text, ("earnest money", "emd")) or int(round(reserve * 0.1))

        survey_matches = re.findall(r"(?:S\.?No\.?|Survey\s*No\.?)\s*[:\-]?\s*([0-9]+(?:/[0-9A-Za-z]+)*)", text, flags=re.IGNORECASE)
        survey_numbers: List[str] = list(dict.fromkeys(survey_matches))[:10]

        possession = PossessionType.SYMBOLIC if "symbolic" in text.lower() else PossessionType.PHYSICAL

        lower_t = text.lower()
        if "flat" in lower_t or "apartment" in lower_t:
            category = AssetCategory.FLAT_APARTMENT
        elif "commercial" in lower_t or "shop" in lower_t or "office" in lower_t:
            category = AssetCategory.COMMERCIAL
        elif "industrial" in lower_t or "factory" in lower_t:
            category = AssetCategory.INDUSTRIAL
        elif "house" in lower_t or "villa" in lower_t:
            category = AssetCategory.HOUSE_VILLA
        else:
            category = AssetCategory.LAND_PLOT

        date_m = re.search(r"auction\s*date\s*[:\-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", text, flags=re.IGNORECASE)
        auction_date = "2026-12-31T11:00:00"
        if date_m:
            parts = re.split(r"[-/]", date_m.group(1))
            if len(parts) == 3:
                d, m_val, y = parts
                y = f"20{y}" if len(y) == 2 else y
                auction_date = f"{y}-{int(m_val):02d}-{int(d):02d}T11:00:00"

        area_m = re.search(r"(\d[\d,\.]*\s*(?:sq\.?\s*ft|sqft|cents|acres|grounds?))", text, flags=re.IGNORECASE)
        area_desc = area_m.group(1) if area_m else "See auction notice"

        prop = ExtractedAuctionProperty(
            bank_name=bank_name,
            asset_category=category,
            possession_type=possession,
            survey_numbers=survey_numbers,
            village_or_locality=district,
            district=district,
            area_description=area_desc,
            reserve_price_inr=reserve,
            emd_amount_inr=emd,
            auction_date=auction_date,
        )
        return NoticeExtractionBatch(properties=[prop])
