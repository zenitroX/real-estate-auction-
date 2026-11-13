"""
Baanknet / IBAPI portal scraper.
Navigates to https://baanknet.com/property-listing, intercepts background JSON XHR/Fetch
responses, extracts property summary items, downloads corresponding SARFAESI Sale Notice PDFs,
and yields items for multimodal OCR pipeline processing.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger("auction_engine.scrapers.baanknet")

BAANKNET_LISTING_URL = "https://baanknet.com/property-listing"


class BaanknetScraper(BaseScraper):
    """XHR / Fetch JSON interceptor and PDF fetcher for Baanknet auctions."""

    def __init__(
        self,
        target_state: str = "Tamil Nadu",
        max_pages: int = 5,
        headless: Optional[bool] = None,
        tmp_dir: Optional[str] = None,
    ):
        super().__init__(headless=headless, tmp_dir=tmp_dir)
        self.target_state = target_state
        self.max_pages = max_pages
        self.intercepted_records: List[Dict[str, Any]] = []

    async def _handle_response(self, response):
        """Intercept and parse JSON responses containing property listing arrays."""
        try:
            url = response.url
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type and any(
                term in url.lower() for term in ("property", "listing", "search", "auction")
            ):
                text_body = await response.text()
                data = json.loads(text_body)

                # Check common API response payload shapes
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    for key in ("data", "properties", "listings", "results", "content"):
                        if isinstance(data.get(key), list):
                            items = data[key]
                            break

                for item in items:
                    if isinstance(item, dict):
                        # Filter for target state if state field is present
                        item_state = str(item.get("state") or item.get("stateName") or "").lower()
                        if not item_state or self.target_state.lower() in item_state:
                            self.intercepted_records.append(item)
                            logger.debug("Intercepted Baanknet property: %s", item.get("id") or item.get("title"))

        except Exception as e:
            logger.debug("Error while inspecting network response: %s", e)

    async def scrape(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute Baanknet scrape:
          1. Launch page with response interceptor.
          2. Navigate to property listing URL.
          3. Apply State filter and paginate.
          4. For each intercepted record with a PDF notice URL, download notice.
          5. Yield record with local PDF path and metadata.
        """
        page = await self.new_page()

        try:
            # Register response interceptor
            page.on("response", self._handle_response)

            logger.info("Navigating to %s", BAANKNET_LISTING_URL)
            await page.goto(BAANKNET_LISTING_URL, wait_until="networkidle", timeout=60000)
            await self.polite_sleep(2.0, 3.5)

            # Attempt to select state in UI dropdown if present
            try:
                state_select = await page.query_selector("select[name*='state'], input[placeholder*='State']")
                if state_select:
                    tag = await state_select.evaluate("el => el.tagName.toLowerCase()")
                    if tag == "select":
                        await state_select.select_option(label=self.target_state)
                    else:
                        await state_select.fill(self.target_state)
                        await page.keyboard.press("Enter")
                    await self.polite_sleep(2.0, 3.0)
            except Exception as e:
                logger.debug("State selector interaction skipped: %s", e)

            # Paginate through listing pages
            for current_page in range(1, self.max_pages + 1):
                logger.info("Processing Baanknet page %d of %d", current_page, self.max_pages)
                await self.polite_sleep(1.5, 3.0)

                # Look for 'Next' button
                next_btn = await page.query_selector(
                    "button:has-text('Next'), a:has-text('Next'), .pagination-next, [aria-label='Next page']"
                )
                if not next_btn or not await next_btn.is_enabled():
                    logger.info("No further pagination buttons found on Baanknet.")
                    break

                await next_btn.click()
                await page.wait_for_load_state("networkidle", timeout=15000)

        except Exception as e:
            logger.warning("Baanknet navigation encountered an error: %s", e)
        finally:
            await page.close()

        # Yield collected records and download referenced PDFs
        logger.info("Total Baanknet property records intercepted: %d", len(self.intercepted_records))
        for item in self.intercepted_records:
            # Discover PDF link inside item
            pdf_url = (
                item.get("noticeUrl")
                or item.get("pdfUrl")
                or item.get("saleNoticeUrl")
                or item.get("documentUrl")
                or item.get("attachment")
            )

            pdf_path = None
            if pdf_url and isinstance(pdf_url, str) and pdf_url.startswith("http"):
                try:
                    pdf_path = await self.download_file(pdf_url, source_tag="baanknet")
                except Exception as e:
                    logger.warning("Failed downloading PDF for Baanknet item %s: %s", pdf_url, e)

            yield {
                "source": "baanknet",
                "portal_url": BAANKNET_LISTING_URL,
                "listing_data": item,
                "pdf_url": pdf_url,
                "pdf_path": str(pdf_path) if pdf_path else None,
            }

