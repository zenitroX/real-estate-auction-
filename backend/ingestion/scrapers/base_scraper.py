"""
Abstract base scraper module providing Playwright browser management,
anti-bot stealth headers, polite rate-limiting, and async PDF download helpers.
"""

import asyncio
import hashlib
import logging
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.settings import get_settings

logger = logging.getLogger("auction_engine.scrapers.base")

# Realistic browser headers for Chromium requests
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
    "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


class BaseScraper(ABC):
    """Abstract base scraper with Playwright browser session and HTTP download capabilities."""

    def __init__(self, headless: Optional[bool] = None, tmp_dir: Optional[str] = None):
        settings = get_settings()
        self.headless = headless if headless is not None else settings.playwright_headless
        self.tmp_dir = Path(tmp_dir or settings.tmp_download_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = None
        self.browser = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def get_http_client(self) -> httpx.AsyncClient:
        """Retrieve or create persistent async HTTP client with browser headers."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                follow_redirects=True,
                timeout=30.0,
            )
        return self._http_client

    async def start(self):
        """Initialize Playwright browser session."""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-zygote",
                    "--single-process",
                    "--disable-background-networking",
                ],
            )
            logger.info("Playwright Chromium browser launched (headless=%s)", self.headless)
        except Exception as e:
            logger.error("Failed to launch Playwright browser: %s", e)
            raise e

    async def new_page(self):
        """Create a new browser context and page configured with realistic stealth viewport and headers."""
        if not self.browser:
            await self.start()

        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=DEFAULT_HEADERS["User-Agent"],
            locale="en-US",
            timezone_id="Asia/Kolkata",
        )
        page = await context.new_page()
        # Set extra HTTP headers
        await page.set_extra_http_headers(DEFAULT_HEADERS)
        stealth_path = Path(__file__).resolve().parent / "stealth.js"
        if stealth_path.exists():
            stealth_js = stealth_path.read_text(encoding="utf-8").replace("__LANGUAGES__", '["en-US", "en", "ta"]')
            await page.add_init_script(stealth_js)
        return page

    async def polite_sleep(self, min_seconds: float = 1.5, max_seconds: float = 3.5):
        """Introduce randomized delay between scraper interactions to emulate human traffic."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def download_file(self, url: str, source_tag: str) -> Optional[Path]:
        """
        Download a PDF or notice image and persist into ./tmp_notices/{source}_{hash}.pdf.
        Deduplicates local downloads if file already exists.
        """
        if not url or not url.startswith("http"):
            logger.warning("Invalid URL for download: %s", url)
            return None

        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        file_ext = Path(url.split("?")[0]).suffix.lower() or ".pdf"
        dest_filename = f"{source_tag}_{url_hash}{file_ext}"
        dest_path = self.tmp_dir / dest_filename

        if dest_path.exists() and dest_path.stat().st_size > 0:
            logger.debug("Reusing cached notice file: %s", dest_path)
            return dest_path

        client = await self.get_http_client()
        logger.info("Downloading notice from %s to %s", url, dest_path.name)
        response = await client.get(url)
        response.raise_for_status()

        dest_path.write_bytes(response.content)
        logger.info("Successfully downloaded %d bytes to %s", len(response.content), dest_path.name)
        return dest_path

    async def close(self):
        """Teardown browser session and HTTP clients."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("BaseScraper resources released.")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def scrape(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Abstract generator yielding scraped notice items with metadata and PDF file paths."""
        pass

