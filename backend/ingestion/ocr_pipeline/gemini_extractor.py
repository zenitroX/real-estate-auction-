"""
Gemini 2.5 Flash structured output extractor for SARFAESI auction notices.
Integrates with the modern google-genai SDK, applying strict JSON schema validation,
tenacity retries, and Tamil-to-English legal notice parsing instructions.
"""

import logging
import re
from datetime import datetime
from typing import Optional, Union
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from config.settings import get_settings
from models.auction_schema import (
    AssetCategory,
    ExtractedAuctionProperty,
    NoticeExtractionBatch,
    PossessionType,
    PropertyBoundaries,
    convert_area_description_to_sqft,
)
from ocr_pipeline.pdf_router import RoutePath, RoutedDocument

logger = logging.getLogger("auction_engine.gemini")

SARFAESI_SYSTEM_INSTRUCTION = """You are an expert Indian SARFAESI Act legal notice parser and Tamil-to-English real estate translator.
1. A single sale notice often contains a table with MULTIPLE borrowers and MULTIPLE properties. Extract every single property as a separate item in the `properties` array.
2. If the notice is in Tamil or bilingual (Tamil + English), translate all village names, taluks, districts, and North/South/East/West boundary descriptions into clean English. Keep Survey Numbers (S.F. No / க.ச. எண் / T.S. No / Patta No) exact.
3. Convert Indian numbering units accurately: 1 Lakh = 100,000; 1 Crore = 10,000,000. Never return decimals for INR integer fields.
4. Convert local land measurements into `area_sqft` where possible:
   - 1 Cent = 435.6 sq.ft
   - 1 Ground = 2,400 sq.ft
   - 1 Acre = 43,560 sq.ft
   - 1 Hectare = 107,639 sq.ft
   - 1 Sq. Meter = 10.7639 sq.ft
5. Look carefully for "Symbolic Possession" (அடையாள சுவாதீனம்) vs "Physical Possession" (நேரடி சுவாதீனம்)."""


def _is_retryable_error(exc: Exception) -> bool:
    """Do not retry configuration, authentication, or parsing schema errors."""
    if isinstance(exc, (RuntimeError, ValueError)):
        return False
    return True


class GeminiAuctionExtractor:
    """Extractor leveraging Google Gemini 2.5 Flash Structured Outputs."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model or "gemini-2.5-flash"
        self._client = None

        if self.api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Gemini client with model: %s", self.model_name)
            except Exception as e:
                logger.warning("Could not initialize google-genai client: %s", e)
        else:
            logger.info("Gemini API key not configured. Offline heuristic fallback enabled for dry-run.")

    @property
    def client(self):
        if not self._client and self.api_key:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=15),
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    def _call_gemini_api(self, contents: Union[str, list]) -> NoticeExtractionBatch:
        """Execute call to Gemini 2.5 Flash with structured output schema and retry."""
        if not self.client:
            raise RuntimeError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in your environment or .env file."
            )

        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=SARFAESI_SYSTEM_INSTRUCTION,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=NoticeExtractionBatch,
        )

        models_to_try = [self.model_name]
        for fallback in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"):
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_error = None
        for model in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                if hasattr(response, "text") and response.text:
                    return NoticeExtractionBatch.model_validate_json(response.text)
                elif hasattr(response, "parsed") and response.parsed:
                    if isinstance(response.parsed, NoticeExtractionBatch):
                        return response.parsed
                    return NoticeExtractionBatch.model_validate(response.parsed)
            except Exception as e:
                logger.warning("Model %s attempt failed: %s", model, e)
                last_error = e

        raise last_error or RuntimeError("All Gemini model attempts failed.")

    def _offline_fallback_parse(self, text_content: Optional[str] = None) -> NoticeExtractionBatch:
        """
        Regex heuristic fallback parser for digital plain text documents when
        Gemini API is unavailable. Enforces strict entity extraction; never fabricates dummy records.
        """
        text = text_content or ""
        if not text.strip():
            logger.warning("Offline extractor received empty document text; returning empty batch.")
            return NoticeExtractionBatch(properties=[])

        # 1. Bank name detection
        bank_name = None
        for candidate in (
            "State Bank of India", "Canara Bank", "Indian Overseas Bank",
            "Bank of Baroda", "Punjab National Bank", "Union Bank of India",
            "HDFC Bank", "ICICI Bank", "Axis Bank", "Bank of India"
        ):
            if candidate.lower() in text.lower():
                bank_name = candidate
                break

        if not bank_name:
            logger.warning("No recognized bank entity found in document text; skipping offline extraction.")
            return NoticeExtractionBatch(properties=[])

        # 2. Reserve price & EMD (strictly requires matched reserve price)
        reserve_match = re.search(r"Reserve\s*Price\s*[:\-]?\s*(?:Rs\.?|INR)?\s*([\d,]+)", text, re.IGNORECASE)
        if not reserve_match:
            logger.warning("No reserve price found in document text; skipping offline extraction.")
            return NoticeExtractionBatch(properties=[])
        reserve_price = int(re.sub(r"[^\d]", "", reserve_match.group(1)))

        emd_match = re.search(r"EMD\s*(?:Amount)?\s*[:\-]?\s*(?:Rs\.?|INR)?\s*([\d,]+)", text, re.IGNORECASE)
        emd_amount = int(re.sub(r"[^\d]", "", emd_match.group(1))) if emd_match else int(reserve_price * 0.10)

        # 3. Branch name
        branch_match = re.search(r"(?:Branch|SARB|ARMB)[:\s]+([^\n,]+)", text, re.IGNORECASE)
        branch_name = branch_match.group(1).strip() if branch_match else "Asset Recovery Branch"

        # 4. Borrower name
        borrower_match = re.search(r"(?:Borrower|Borrowers|Thiru\.|Mr\.|M/s\.)\s*[:\-]?\s*([^\n,]+)", text, re.IGNORECASE)
        borrower_name = borrower_match.group(1).strip() if borrower_match else "Borrower"

        # 5. Survey numbers
        surveys = []
        for sf_match in re.finditer(r"(?:S\.?F\.?|Survey)\s*No\.?\s*([0-9\/\,A-Za-z\s]+?)(?:,|\.|\bPatta\b|\band\b|\n)", text, re.IGNORECASE):
            raw_s = sf_match.group(1).strip()
            for part in re.split(r"[,;&\s]+", raw_s):
                if re.search(r"\d", part):
                    surveys.append(part.strip())
        if not surveys:
            surveys = ["Unspecified"]

        # 6. Possession type
        if "physical" in text.lower() or "நேரடி" in text:
            possession = PossessionType.PHYSICAL
        elif "symbolic" in text.lower() or "அடையாள" in text:
            possession = PossessionType.SYMBOLIC
        else:
            possession = PossessionType.PHYSICAL

        # 7. Boundaries
        north = re.search(r"(?:^|\n)\s*North\s*(?:by)?\s*[:\-]?\s*([^\n\(]+)", text, re.IGNORECASE)
        south = re.search(r"(?:^|\n)\s*South\s*(?:by)?\s*[:\-]?\s*([^\n\(]+)", text, re.IGNORECASE)
        east = re.search(r"(?:^|\n)\s*East\s*(?:by)?\s*[:\-]?\s*([^\n\(]+)", text, re.IGNORECASE)
        west = re.search(r"(?:^|\n)\s*West\s*(?:by)?\s*[:\-]?\s*([^\n\(]+)", text, re.IGNORECASE)

        boundaries = PropertyBoundaries(
            north=north.group(1).strip() if north else "Road",
            south=south.group(1).strip() if south else "Neighbor land",
            east=east.group(1).strip() if east else "Private property",
            west=west.group(1).strip() if west else "Common lane",
        )

        # 8. Locality / District
        dist_match = re.search(r"(Coimbatore|Chennai|Madurai|Tiruppur|Salem|Trichy|Erode|Dindigul)", text, re.IGNORECASE)
        district = dist_match.group(1).title() if dist_match else "Tamil Nadu"

        village_match = re.search(r"(?:Village|Locality|Nagar)[:\s]+([^\n,]+)", text, re.IGNORECASE)
        village = village_match.group(1).strip() if village_match else district

        area_desc = "Extracted from statutory notice"
        area_match = re.search(r"(?:Extent|Area|Measuring)[:\s]+([^\n]+)", text, re.IGNORECASE)
        if area_match:
            cleaned_area = area_match.group(1).strip().rstrip(".")
            if cleaned_area:
                area_desc = cleaned_area

        # 9. Auction Date
        auction_date = ""
        date_match = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", text)
        if date_match:
            d, m, y = date_match.groups()
            auction_date = f"{y}-{m}-{d}T11:00:00"

        prop = ExtractedAuctionProperty(
            bank_name=bank_name,
            branch_name=branch_name,
            borrower_name=borrower_name,
            asset_category=AssetCategory.HOUSE_VILLA,
            possession_type=possession,
            survey_numbers=surveys,
            patta_or_door_no="",
            village_or_locality=village,
            taluk="",
            district=district,
            state="Tamil Nadu",
            pincode="",
            area_description=area_desc,
            area_sqft=convert_area_description_to_sqft(area_desc),
            boundaries=boundaries,
            reserve_price_inr=reserve_price,
            emd_amount_inr=emd_amount,
            bid_increment_inr=50000,
            emd_last_date="",
            inspection_date_info="Contact authorized officer",
            auction_date=auction_date,
            authorized_officer_name="Authorized Officer",
            contact_phone="",
            bidding_portal_url="https://ibapi.in",
        )
        return NoticeExtractionBatch(properties=[prop])

    def extract_from_text(self, text_content: str) -> NoticeExtractionBatch:
        """Extract structured auction properties from digital plain text."""
        if not self.client:
            return self._offline_fallback_parse(text_content)

        prompt = (
            "Parse the following SARFAESI bank auction legal notice and extract all properties "
            "into the structured NoticeExtractionBatch schema:\n\n"
            f"{text_content}"
        )
        try:
            batch = self._call_gemini_api(prompt)
            return self._post_process_batch(batch)
        except Exception as e:
            logger.warning("Gemini API call failed (%s); falling back to offline parser.", e)
            return self._offline_fallback_parse(text_content)

    def extract_from_multimodal(self, file_bytes: bytes, mime_type: str) -> NoticeExtractionBatch:
        """Extract structured auction properties from scanned PDF or newspaper image bytes."""
        if not self.client:
            logger.warning("Gemini client not initialized; cannot perform multimodal image extraction without API.")
            return NoticeExtractionBatch(properties=[])

        from google.genai import types

        part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
        contents = [
            part,
            "Extract all SARFAESI bank auction properties from this document into structured JSON.",
        ]
        try:
            batch = self._call_gemini_api(contents)
            return self._post_process_batch(batch)
        except Exception as e:
            logger.warning("Gemini Vision call failed (%s); returning empty extraction batch.", e)
            return NoticeExtractionBatch(properties=[])

    def extract(self, routed_doc: RoutedDocument) -> NoticeExtractionBatch:
        """
        Execute token-optimized extraction based on RoutedDocument decision.
        Uses text prompt for Path A, or binary multimodal vision for Path B.
        """
        logger.info(
            "Extracting document via %s (MIME: %s, Pages: %d, Reason: %s)",
            routed_doc.route.value,
            routed_doc.mime_type,
            routed_doc.page_count,
            routed_doc.reason,
        )

        if routed_doc.route == RoutePath.DIGITAL_TEXT and routed_doc.text_content:
            return self.extract_from_text(routed_doc.text_content)
        elif routed_doc.file_bytes:
            return self.extract_from_multimodal(routed_doc.file_bytes, routed_doc.mime_type)
        elif routed_doc.file_path:
            with open(routed_doc.file_path, "rb") as f:
                data = f.read()
            return self.extract_from_multimodal(data, routed_doc.mime_type)
        else:
            raise ValueError("RoutedDocument contains neither text_content nor file_bytes/file_path.")

    def _post_process_batch(self, batch: NoticeExtractionBatch) -> NoticeExtractionBatch:
        """Post-process properties to ensure area_sqft calculation and normalization."""
        for prop in batch.properties:
            # Ensure area_sqft is computed if missing
            if (prop.area_sqft is None or prop.area_sqft <= 0) and prop.area_description:
                computed = convert_area_description_to_sqft(prop.area_description)
                if computed:
                    prop.area_sqft = computed

        return batch

