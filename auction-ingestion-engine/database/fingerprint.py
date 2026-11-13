"""
Deterministic SHA-256 fingerprinting for bank auction assets and auction events.
Enables cross-auction deduplication, tracking repeat auctions of the same property,
and calculating price drops.
"""

import hashlib
import re
from typing import List, Union


def normalize_survey_number(survey_str: str) -> str:
    """
    Normalize an individual survey number string.
    Strips common legal notice prefixes (e.g., 'S.F. No.', 'SFNO', 'Survey No.', 'R.S. No.')
    and retains only lowercase alphanumeric characters.
    """
    cleaned = survey_str.lower().strip()

    # Remove common prefix keywords with optional punctuation and spacing
    cleaned = re.sub(
        r"^(?:s\.?\s*f\.?|r\.?\s*s\.?|t\.?\s*s\.?|sy|survey|ward|block|plot|patta|door|d)\s*(?:no\.?|nos\.?|number)?\s*[:\.\-]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Remove standalone "no" / "nos" prefix if leftover
    cleaned = re.sub(r"^(?:no\.?|nos\.?|number)\s*[:\.\-]?\s*", "", cleaned, flags=re.IGNORECASE)

    # Strip all non-alphanumeric characters (e.g., '/', '-', '.', spaces)
    cleaned = re.sub(r"[^a-z0-9]", "", cleaned)
    return cleaned


def extract_and_normalize_surveys(survey_inputs: Union[List[str], str]) -> List[str]:
    """
    Process survey number inputs, splitting comma/semicolon-separated tokens,
    normalizing each token, deduplicating, and returning a sorted list.
    """
    if isinstance(survey_inputs, str):
        raw_items = re.split(r"[,;&\n]+", survey_inputs)
    else:
        raw_items = []
        for item in survey_inputs:
            if isinstance(item, str):
                raw_items.extend(re.split(r"[,;&\n]+", item))
            else:
                raw_items.append(str(item))

    normalized_set = set()
    for raw in raw_items:
        norm = normalize_survey_number(raw)
        if norm:
            normalized_set.add(norm)

    return sorted(normalized_set)


def generate_asset_fingerprint(
    bank_name: str, district: str, survey_numbers: Union[List[str], str]
) -> str:
    """
    Generate deterministic SHA-256 hash identifying the physical real estate asset.
    Rule:
      1. Lowercase and strip all non-alphanumeric characters from bank_name, district.
      2. Normalize, deduplicate, and sort survey numbers alphabetically.
      3. Return sha256(f"{clean_bank}|{clean_district}|{clean_surveys}").
    """
    clean_bank = re.sub(r"[^a-z0-9]", "", bank_name.lower())
    clean_district = re.sub(r"[^a-z0-9]", "", district.lower())

    normalized_surveys = extract_and_normalize_surveys(survey_numbers)
    clean_surveys = ",".join(normalized_surveys)

    payload = f"{clean_bank}|{clean_district}|{clean_surveys}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_auction_event_hash(asset_fingerprint: str, auction_date_iso: str) -> str:
    """
    Generate deterministic SHA-256 hash for a specific auction event on an asset.
    Rule:
      sha256(f"{asset_fingerprint}|{auction_date_iso[:10]}")
    """
    date_prefix = auction_date_iso[:10] if len(auction_date_iso) >= 10 else auction_date_iso
    payload = f"{asset_fingerprint}|{date_prefix}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

