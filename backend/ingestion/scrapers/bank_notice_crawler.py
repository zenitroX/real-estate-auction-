"""
Direct PDF link crawler for bank foreclosure and auction notice tables.
Supports portals such as Canara Bank, Indian Overseas Bank (IOB), State Bank of India (SBI),
and C1 India.
"""

import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from urllib.parse import urljoin
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger("auction_engine.scrapers.bank_crawler")

# Standard public Indian bank auction / SARFAESI notice portals
DEFAULT_BANK_TARGETS = [
    {
        "bank_name": "Canara Bank",
        "url": "https://canarabank.com/eauction",
        "link_pattern": r"(?:sarfaesi|auction|sale[-_]?notice|possession).*\.pdf$",
    },
    {
        "bank_name": "Indian Overseas Bank",
        "url": "https://www.iob.in/Tender_Eauction",
        "link_pattern": r"(?:eauction|auction|notice).*\.pdf$",
    },
    {
        "bank_name": "State Bank of India",
        "url": "https://bank.sbi/web/sbi-in-the-news/auction-notices/sarfaesi-and-others",
        "link_pattern": r"\.pdf$",
    },
    {
        "bank_name": "C1 India",
        "url": "https://www.bankeauctions.com",
        "link_pattern": r"(?:download|notice|sale).*\.pdf$",
    },
]


class BankNoticeCrawler(BaseScraper):
    """Configurable table & anchor scraper for direct bank foreclosure PDF links."""

    def __init__(
        self,
        targets: Optional[List[Dict[str, str]]] = None,
        existing_pdf_urls: Optional[Set[str]] = None,
        headless: Optional[bool] = None,
        tmp_dir: Optional[str] = None,
    ):
        super().__init__(headless=headless, tmp_dir=tmp_dir)
        self.targets = targets or DEFAULT_BANK_TARGETS
        self.existing_pdf_urls = existing_pdf_urls or set()

    async def scrape(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Iterate over configured bank auction portals, locate all anchor tags linking to PDFs,
        filter by SARFAESI notice patterns, skip already crawled URLs, download new files,
        and yield items for OCR extraction.
        """
        page = await self.new_page()

        try:
            for target in self.targets:
                bank_name = target.get("bank_name", "Unknown Bank")
                portal_url = target["url"]
                pattern = target.get("link_pattern", r"\.pdf$")
                tag_slug = re.sub(r"[^a-z0-9]", "", bank_name.lower())

                logger.info("Crawling %s auction portal at %s", bank_name, portal_url)

                try:
                    await page.goto(portal_url, wait_until="domcontentloaded", timeout=45000)
                    await self.polite_sleep(2.0, 3.5)

                    # Extract all anchor tags
                    anchors = await page.query_selector_all("a[href]")
                    pdf_candidates = []

                    for anchor in anchors:
                        href = await anchor.get_attribute("href")
                        text = (await anchor.inner_text() or "").strip()
                        if not href:
                            continue

                        full_url = urljoin(portal_url, href)

                        # Match PDF extension and notice regex pattern
                        is_pdf = full_url.lower().endswith(".pdf") or ".pdf?" in full_url.lower()
                        matches_pattern = re.search(pattern, full_url, re.IGNORECASE) or (
                            re.search(r"(?:auction|sarfaesi|sale|notice)", text, re.IGNORECASE) and is_pdf
                        )

                        if is_pdf and matches_pattern:
                            pdf_candidates.append({"url": full_url, "link_text": text})

                    logger.info("Found %d candidate PDF notice links on %s", len(pdf_candidates), bank_name)

                    for cand in pdf_candidates:
                        pdf_url = cand["url"]

                        # Skip already ingested notices
                        if pdf_url in self.existing_pdf_urls:
                            logger.debug("Skipping already indexed PDF URL: %s", pdf_url)
                            continue

                        # Download PDF
                        pdf_path = None
                        try:
                            pdf_path = await self.download_file(pdf_url, source_tag=tag_slug)
                        except Exception as e:
                            logger.warning("Error downloading notice from %s: %s", pdf_url, e)

                        if pdf_path:
                            yield {
                                "source": bank_name,
                                "portal_url": portal_url,
                                "link_text": cand["link_text"],
                                "pdf_url": pdf_url,
                                "pdf_path": str(pdf_path),
                            }

                except Exception as e:
                    logger.warning("Failed crawling bank %s (%s): %s", bank_name, portal_url, e)

        finally:
            await page.close()

