"""
Pydantic V2 schemas for LLM structured output and database validation.
Defines data contracts for bank auction notices, asset categories, boundaries,
and area conversion helpers.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class PossessionType(str, Enum):
    """Legal possession status held by the secured creditor under SARFAESI Act."""
    PHYSICAL = "PHYSICAL"
    SYMBOLIC = "SYMBOLIC"
    UNKNOWN = "UNKNOWN"


class AssetCategory(str, Enum):
    """Categorization of immovable or movable property under auction."""
    LAND_PLOT = "LAND_PLOT"
    HOUSE_VILLA = "HOUSE_VILLA"
    FLAT_APARTMENT = "FLAT_APARTMENT"
    COMMERCIAL = "COMMERCIAL"
    AGRICULTURAL = "AGRICULTURAL"
    INDUSTRIAL = "INDUSTRIAL"
    OTHER = "OTHER"


class ReviewStatus(str, Enum):
    """Verification and publishing lifecycle status in Supabase."""
    PUBLISHED = "PUBLISHED"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"
    EXPIRED = "EXPIRED"
    SOLD = "SOLD"


class PropertyBoundaries(BaseModel):
    """Four-sided boundary descriptions translated to English."""
    north: Optional[str] = Field(None, description="Boundary on the North side")
    south: Optional[str] = Field(None, description="Boundary on the South side")
    east: Optional[str] = Field(None, description="Boundary on the East side")
    west: Optional[str] = Field(None, description="Boundary on the West side")


class ExtractedAuctionProperty(BaseModel):
    """Pydantic V2 schema for a single extracted auction property record."""
    bank_name: str = Field(
        description="Standardized English name of the bank (e.g., 'State Bank of India', 'Canara Bank')"
    )
    branch_name: Optional[str] = Field(None, description="Branch name or SARB/ARMB recovery branch")
    borrower_name: Optional[str] = Field(None, description="Name of the borrower, proprietor, or guarantor")
    asset_category: AssetCategory
    possession_type: PossessionType = Field(
        description="Whether bank has Physical or Symbolic/Constructive possession"
    )

    survey_numbers: List[str] = Field(
        description="Every Survey No, S.F. No, R.S. No, T.S. No, or Ward/Block No as separate strings"
    )
    patta_or_door_no: Optional[str] = Field(None, description="Patta No, Plot No, Flat No, or Door No if mentioned")
    village_or_locality: str = Field(description="Village, Nagar, or locality name translated to English")
    taluk: Optional[str] = Field(None, description="Taluk name in English")
    district: str = Field(
        description="Standardized District name in English (e.g., 'Coimbatore', 'Chennai', 'Madurai')"
    )
    state: str = Field(default="Tamil Nadu", description="State name in English")
    pincode: Optional[str] = Field(None, description="6-digit Indian PIN code if present")

    area_description: str = Field(
        description="Original area string from notice, e.g., '2400 Sq.ft' or '1 Acre 25 Cents'"
    )
    area_sqft: Optional[float] = Field(
        None,
        description="Total land/plinth area converted to Square Feet (1 Cent = 435.6 sqft, 1 Acre = 43560 sqft, 1 Ground = 2400 sqft)",
    )
    boundaries: Optional[PropertyBoundaries] = None

    reserve_price_inr: int = Field(
        description="Reserve Price converted to full integer in INR (e.g., 'Rs. 34.50 Lakhs' -> 3450000)"
    )
    emd_amount_inr: int = Field(
        description="Earnest Money Deposit (EMD) converted to full integer in INR"
    )
    bid_increment_inr: Optional[int] = Field(
        None, description="Bid multiplier / increment amount in full INR integer"
    )

    emd_last_date: Optional[str] = Field(None, description="ISO 8601 format YYYY-MM-DDTHH:MM:SS")
    inspection_date_info: Optional[str] = Field(None, description="Date and time window for physical inspection")
    auction_date: str = Field(description="Auction start date and time in ISO 8601 format YYYY-MM-DDTHH:MM:SS")

    authorized_officer_name: Optional[str] = None
    contact_phone: Optional[str] = Field(
        None, description="Phone or mobile numbers of the Authorized Officer or branch"
    )
    bidding_portal_url: Optional[str] = Field(
        None, description="Portal URL mentioned in notice, e.g., baanknet.com or mstcecommerce.com"
    )
    images: List[str] = Field(
        default_factory=list,
        description="Direct URLs or local paths to property photographs extracted from portal or notice",
    )

    @field_validator("survey_numbers", mode="before")
    @classmethod
    def split_comma_separated_surveys(cls, v: Any) -> List[str]:
        """Normalize survey numbers if passed as a single comma-separated string or list."""
        if isinstance(v, str):
            parts = [p.strip() for p in re.split(r"[,;]+", v) if p.strip()]
            return parts or [v.strip()]
        if isinstance(v, list):
            flattened = []
            for item in v:
                if isinstance(item, str):
                    for sub in re.split(r"[,;]+", item):
                        cleaned = sub.strip()
                        if cleaned:
                            flattened.append(cleaned)
                else:
                    flattened.append(str(item).strip())
            return flattened
        return []

    @model_validator(mode="after")
    def populate_area_sqft_if_missing(self) -> "ExtractedAuctionProperty":
        """If area_sqft is not provided by LLM, try computing from area_description."""
        if self.area_sqft is not None and self.area_sqft > 0:
            self.area_sqft = round(self.area_sqft, 2)
            return self
        if self.area_description:
            computed = convert_area_description_to_sqft(self.area_description)
            if computed:
                self.area_sqft = round(computed, 2)
        return self


class NoticeExtractionBatch(BaseModel):
    """Root model returned by Gemini structured outputs parsing multi-property sale notices."""
    properties: List[ExtractedAuctionProperty] = Field(
        description="List of all distinct properties found in the auction sale notice document or image"
    )


class AuctionPropertyRecord(BaseModel):
    """Representation of the complete database record stored in Supabase."""
    id: Optional[str] = None
    asset_fingerprint: str
    auction_event_hash: str

    bank_name: str
    branch_name: Optional[str] = None
    borrower_name: Optional[str] = None
    asset_category: AssetCategory
    possession_type: PossessionType

    survey_numbers: List[str]
    patta_or_door_no: Optional[str] = None
    village_or_locality: str
    taluk: Optional[str] = None
    district: str
    state: str = "Tamil Nadu"
    pincode: Optional[str] = None

    area_description: str
    area_sqft: Optional[float] = None
    boundaries: Optional[Dict[str, Any]] = None

    reserve_price_inr: int
    previous_reserve_price_inr: Optional[int] = None
    price_drop_percentage: Optional[float] = None
    emd_amount_inr: int
    bid_increment_inr: Optional[int] = None

    emd_last_date: Optional[str] = None
    inspection_date_info: Optional[str] = None
    auction_date: str

    authorized_officer_name: Optional[str] = None
    contact_phone: Optional[str] = None
    source_portal: str
    source_pdf_url: Optional[str] = None
    bidding_portal_url: Optional[str] = None

    review_status: ReviewStatus = ReviewStatus.PUBLISHED
    review_notes: Optional[str] = None
    raw_extracted_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def convert_area_description_to_sqft(area_description: str) -> Optional[float]:
    """
    Convert Indian & regional land area measurements into square feet.
    Standard Tamil Nadu conversion units:
      - 1 Cent = 435.6 sq.ft
      - 1 Ground = 2,400 sq.ft
      - 1 Acre = 43,560 sq.ft
      - 1 Hectare = 107,639 sq.ft
      - 1 Sq. Meter = 10.7639 sq.ft
      - 1 Sq. Yard = 9 sq.ft
      - 1 Sq. Foot = 1 sq.ft
    """
    if not area_description:
        return None

    clean = area_description.strip()
    total_sqft = 0.0
    matched = False

    # Check for combined "X Acre(s) Y Cent(s)" or "X Acre(s) and Y Cent(s)"
    combined_acre_cent = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:acre|acres|ac)\b.*?(?:and\s*)?(\d+(?:\.\d+)?)\s*(?:cent|cents|cts)\b",
        clean,
        re.IGNORECASE,
    )
    if combined_acre_cent:
        acres = float(combined_acre_cent.group(1))
        cents = float(combined_acre_cent.group(2))
        return round((acres * 43560.0) + (cents * 435.6), 2)

    # Check standalone units
    acre_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acre|acres|ac)\b", clean, re.IGNORECASE)
    cent_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cent|cents|cts)\b", clean, re.IGNORECASE)
    ground_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ground|grounds|grd)\b", clean, re.IGNORECASE)
    sqft_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*f(?:ee)?t|sqft|square\s*f(?:ee|oo)?t)\b", clean, re.IGNORECASE)
    sqm_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*(?:meters?|m(?:tr)?s?)|sqm|square\s*meters?)\b", clean, re.IGNORECASE)
    sqyd_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*(?:yards?|yds?)|sqyd|square\s*yards?)\b", clean, re.IGNORECASE)
    hectare_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hectare|hectares|ha)\b", clean, re.IGNORECASE)

    if acre_match:
        total_sqft += float(acre_match.group(1)) * 43560.0
        matched = True
    if cent_match:
        total_sqft += float(cent_match.group(1)) * 435.6
        matched = True
    if ground_match:
        total_sqft += float(ground_match.group(1)) * 2400.0
        matched = True
    if sqft_match and not matched:
        total_sqft += float(sqft_match.group(1))
        matched = True
    if sqm_match and not matched:
        total_sqft += float(sqm_match.group(1)) * 10.7639
        matched = True
    if sqyd_match and not matched:
        total_sqft += float(sqyd_match.group(1)) * 9.0
        matched = True
    if hectare_match and not matched:
        total_sqft += float(hectare_match.group(1)) * 107639.0
        matched = True

    # Fallback: check if the string is just a numeric value e.g. "2400"
    if not matched:
        num_only = re.match(r"^(\d+(?:\.\d+)?)$", clean)
        if num_only:
            return float(num_only.group(1))

    return round(total_sqft, 2) if matched else None
