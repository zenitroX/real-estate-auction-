"""
Supabase client integration for auction ingestion engine.
Handles automated sanity checks, deduplication, price drop calculation,
and conflict-free upserts into PostgreSQL.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from config.settings import get_settings
from database.fingerprint import generate_asset_fingerprint, generate_auction_event_hash
from models.auction_schema import ExtractedAuctionProperty, ReviewStatus

logger = logging.getLogger("auction_engine.database")


def evaluate_sanity(property_data: ExtractedAuctionProperty) -> Tuple[ReviewStatus, Optional[str]]:
    """
    Evaluate automated sanity checks on an extracted auction property.
    Flags 'NEEDS_MANUAL_REVIEW' if:
      - EMD > 25% of reserve price or EMD <= 0 (standard SARFAESI EMD is 10%, max ~20-25%)
      - Reserve price < 50,000 INR (likely failed Lakh/Crore conversion)
      - Survey numbers list is empty
    Otherwise returns 'PUBLISHED'.
    """
    reasons: List[str] = []

    # 1. EMD validation
    max_allowed_emd = property_data.reserve_price_inr * 0.25
    if property_data.emd_amount_inr > max_allowed_emd:
        reasons.append(
            f"EMD ({property_data.emd_amount_inr}) exceeds 25% of reserve price ({property_data.reserve_price_inr})"
        )
    elif property_data.emd_amount_inr <= 0:
        reasons.append(f"Invalid non-positive EMD amount: {property_data.emd_amount_inr}")

    # 2. Reserve price sanity
    if property_data.reserve_price_inr < 50000:
        reasons.append(
            f"Reserve price ({property_data.reserve_price_inr}) is below 50,000 INR threshold"
        )

    # 3. Survey numbers presence
    if not property_data.survey_numbers or len(property_data.survey_numbers) == 0:
        reasons.append("No survey numbers or identification numbers extracted")

    if reasons:
        return ReviewStatus.NEEDS_MANUAL_REVIEW, "; ".join(reasons)

    return ReviewStatus.PUBLISHED, None


def prepare_auction_record(
    property_data: ExtractedAuctionProperty,
    source_portal: str,
    source_pdf_url: Optional[str] = None,
    previous_price: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Format and prepare an extracted auction property record into a database-ready dictionary.
    Computes fingerprint, event hash, review status, and price drop percentage.
    """
    asset_fp = generate_asset_fingerprint(
        bank_name=property_data.bank_name,
        district=property_data.district,
        survey_numbers=property_data.survey_numbers,
    )
    event_hash = generate_auction_event_hash(
        asset_fingerprint=asset_fp,
        auction_date_iso=property_data.auction_date,
    )

    review_status, review_notes = evaluate_sanity(property_data)

    price_drop_pct: Optional[float] = None
    prev_reserve: Optional[int] = None

    if previous_price is not None and previous_price > property_data.reserve_price_inr:
        prev_reserve = previous_price
        diff = previous_price - property_data.reserve_price_inr
        price_drop_pct = round((diff / previous_price) * 100.0, 2)

    boundaries_dict = None
    if property_data.boundaries:
        boundaries_dict = property_data.boundaries.model_dump(exclude_none=True)

    record: Dict[str, Any] = {
        "asset_fingerprint": asset_fp,
        "auction_event_hash": event_hash,
        "bank_name": property_data.bank_name,
        "branch_name": property_data.branch_name,
        "borrower_name": property_data.borrower_name,
        "asset_category": property_data.asset_category.value,
        "possession_type": property_data.possession_type.value,
        "survey_numbers": property_data.survey_numbers,
        "patta_or_door_no": property_data.patta_or_door_no,
        "village_or_locality": property_data.village_or_locality,
        "taluk": property_data.taluk,
        "district": property_data.district,
        "state": property_data.state,
        "pincode": property_data.pincode,
        "area_description": property_data.area_description,
        "area_sqft": property_data.area_sqft,
        "boundaries": boundaries_dict,
        "reserve_price_inr": property_data.reserve_price_inr,
        "previous_reserve_price_inr": prev_reserve,
        "price_drop_percentage": price_drop_pct,
        "emd_amount_inr": property_data.emd_amount_inr,
        "bid_increment_inr": property_data.bid_increment_inr,
        "emd_last_date": property_data.emd_last_date,
        "inspection_date_info": property_data.inspection_date_info,
        "auction_date": property_data.auction_date,
        "authorized_officer_name": property_data.authorized_officer_name,
        "contact_phone": property_data.contact_phone,
        "source_portal": source_portal,
        "source_pdf_url": source_pdf_url,
        "bidding_portal_url": property_data.bidding_portal_url,
        "review_status": review_status.value,
        "review_notes": review_notes,
        "raw_extracted_json": property_data.model_dump(mode="json"),
    }
    return record


class AuctionDatabaseClient:
    """Supabase client wrapper handling queries, price-drop checks, and upserts."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        dry_run: bool = False,
    ):
        settings = get_settings()
        self.url = supabase_url or settings.supabase_url
        self.key = supabase_key or settings.effective_supabase_key or settings.supabase_key
        self.dry_run = dry_run
        self.client = None

        if not self.dry_run and self.url and self.key:
            try:
                from supabase import create_client

                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.warning("Could not initialize Supabase client: %s. Operating in offline mode.", e)
        else:
            if not self.dry_run:
                logger.info("Supabase credentials not configured. Running in offline/dry-run mode.")

    def get_latest_prior_asset(
        self, asset_fingerprint: str, auction_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query auction_properties for the latest prior auction of the same asset.
        Selects row where asset_fingerprint matches and auction_date < current auction_date,
        ordered by auction_date DESC LIMIT 1.
        """
        if not self.client or self.dry_run:
            return None

        try:
            response = (
                self.client.table("auction_properties")
                .select("id, reserve_price_inr, auction_date")
                .eq("asset_fingerprint", asset_fingerprint)
                .lt("auction_date", auction_date)
                .order("auction_date", desc=True)
                .limit(1)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.error("Failed querying prior asset for fingerprint %s: %s", asset_fingerprint, e)

        return None

    def get_existing_pdf_urls(self) -> Set[str]:
        """Fetch all previously processed source PDF URLs to avoid re-scraping."""
        if not self.client or self.dry_run:
            return set()

        try:
            response = (
                self.client.table("auction_properties")
                .select("source_pdf_url")
                .not_.is_("source_pdf_url", "null")
                .execute()
            )
            return {
                row["source_pdf_url"]
                for row in (response.data or [])
                if row.get("source_pdf_url")
            }
        except Exception as e:
            logger.error("Failed fetching existing PDF URLs: %s", e)
            return set()

    def upsert_property(
        self,
        property_data: ExtractedAuctionProperty,
        source_portal: str,
        source_pdf_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate price drops from prior auctions, format record, and upsert into Supabase.
        """
        asset_fp = generate_asset_fingerprint(
            property_data.bank_name, property_data.district, property_data.survey_numbers
        )

        prior_asset = self.get_latest_prior_asset(asset_fp, property_data.auction_date)
        prev_price = prior_asset.get("reserve_price_inr") if prior_asset else None

        record = prepare_auction_record(
            property_data=property_data,
            source_portal=source_portal,
            source_pdf_url=source_pdf_url,
            previous_price=prev_price,
        )

        if self.dry_run or not self.client:
            logger.info(
                "[DRY-RUN] Record prepared for event %s (Bank: %s, District: %s, Reserve: ₹%s)",
                record["auction_event_hash"][:12],
                record["bank_name"],
                record["district"],
                f"{record['reserve_price_inr']:,}",
            )
            return record

        try:
            res = (
                self.client.table("auction_properties")
                .upsert(record, on_conflict="auction_event_hash")
                .execute()
            )
            logger.info("Successfully upserted auction event %s", record["auction_event_hash"][:12])
            return res.data[0] if (res.data and len(res.data) > 0) else record
        except Exception as e:
            logger.error("Failed to upsert auction event %s: %s", record["auction_event_hash"], e)
            raise e

    def batch_upsert(
        self,
        properties: List[ExtractedAuctionProperty],
        source_portal: str,
        source_pdf_url: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Process and upsert a batch of extracted auction properties."""
        results = []
        for prop in properties:
            res = self.upsert_property(
                property_data=prop,
                source_portal=source_portal,
                source_pdf_url=source_pdf_url,
            )
            results.append(res)
        return results

