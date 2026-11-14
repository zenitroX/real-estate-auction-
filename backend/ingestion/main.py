"""
CLI and Cron entrypoint for Bank Auction Scraping & Multimodal OCR Microservice.
Supports folder ingestion, live portal scraping, and dry-run verification with Rich terminal UI.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Ensure ingestion directory is always on python sys.path
_INGESTION_DIR = Path(__file__).resolve().parent
if str(_INGESTION_DIR) not in sys.path:
    sys.path.insert(0, str(_INGESTION_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from config.settings import get_settings
from database.supabase_client import AuctionDatabaseClient, prepare_auction_record
from models.auction_schema import ExtractedAuctionProperty, NoticeExtractionBatch
from ocr_pipeline.gemini_extractor import GeminiAuctionExtractor
from ocr_pipeline.pdf_router import RoutePath, route_document

console = Console()
logger = logging.getLogger("auction_engine")


def setup_logging(log_level: str = "INFO"):
    """Configure structured logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def render_properties_table(properties: List[ExtractedAuctionProperty], dry_run: bool = False):
    """Render extracted auction properties in a formatted Rich table."""
    table = Table(
        title=f"Extracted Auction Properties ({len(properties)} records) {'[DRY RUN]' if dry_run else ''}",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Bank / Branch", style="bold white", width=18)
    table.add_column("District & Locality", style="green", width=20)
    table.add_column("Survey Nos", style="yellow", width=16)
    table.add_column("Category", style="magenta", width=14)
    table.add_column("Possession", style="cyan", width=10)
    table.add_column("Reserve (INR)", justify="right", style="bold green", width=14)
    table.add_column("EMD (INR)", justify="right", style="dim", width=12)
    table.add_column("Auction Date", justify="center", width=12)
    table.add_column("Status", justify="center", width=18)

    for prop in properties:
        prepared = prepare_auction_record(prop, source_portal="CLI")
        status_str = prepared["review_status"]
        if status_str == "PUBLISHED":
            status_display = "[bold green]PUBLISHED[/bold green]"
        else:
            status_display = f"[bold red]NEEDS_REVIEW[/bold red]\n[dim]{prepared.get('review_notes') or ''}[/dim]"

        survey_display = ", ".join(prop.survey_numbers[:3])
        if len(prop.survey_numbers) > 3:
            survey_display += f" (+{len(prop.survey_numbers) - 3})"

        table.add_row(
            f"{prop.bank_name}\n[dim]{prop.branch_name or ''}[/dim]",
            f"{prop.district}\n[dim]{prop.village_or_locality}[/dim]",
            survey_display or "[dim]None[/dim]",
            prop.asset_category.value,
            prop.possession_type.value,
            f"₹{prop.reserve_price_inr:,}",
            f"₹{prop.emd_amount_inr:,}",
            prop.auction_date[:10],
            status_display,
        )

    console.print(table)


def process_file(
    file_path: Path,
    extractor: GeminiAuctionExtractor,
    db_client: AuctionDatabaseClient,
    source_portal: str = "Folder Ingestion",
    dry_run: bool = False,
) -> List[ExtractedAuctionProperty]:
    """Process a single notice file: route document -> Gemini extraction -> Supabase upsert."""
    console.print(f"\n[bold blue]Processing file:[/bold blue] {file_path.name}")

    # 1. Route document (digital vs vision)
    routed = route_document(file_path)
    console.print(
        f"  Route: [bold]{routed.route.value}[/bold] (MIME: {routed.mime_type}, Pages: {routed.page_count})"
    )
    console.print(f"  Reason: [dim]{routed.reason}[/dim]")

    # 2. Extract structured properties
    console.print("  [cyan]Extracting SARFAESI properties via Gemini 2.5 Flash...[/cyan]")
    batch: NoticeExtractionBatch = extractor.extract(routed)

    console.print(f"  Extracted [bold green]{len(batch.properties)}[/bold green] distinct property record(s).")

    # 3. Upsert or dry-run
    for prop in batch.properties:
        record = db_client.upsert_property(
            property_data=prop,
            source_portal=source_portal,
            source_pdf_url=str(file_path.name),
        )
        if not dry_run and record:
            console.print(
                f"  [bold green]✓ Upserted to Supabase[/bold green] "
                f"(Event: [cyan]{record.get('auction_event_hash', '')[:12]}[/cyan], "
                f"Status: [yellow]{record.get('review_status', 'PUBLISHED')}[/yellow])"
            )

    return batch.properties


def run_folder_mode(
    input_dir: Path,
    extractor: GeminiAuctionExtractor,
    db_client: AuctionDatabaseClient,
    dry_run: bool = False,
):
    """Scan and process all PDFs and newspaper images in a local folder."""
    if not input_dir.exists() or not input_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] Folder '{input_dir}' does not exist.")
        return

    # Find supported files
    supported_extensions = (".pdf", ".jpg", ".jpeg", ".png", ".webp")
    files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    if not files:
        console.print(f"[yellow]No supported files found in '{input_dir}'. Supported: {supported_extensions}[/yellow]")
        return

    console.print(
        Panel(
            f"Found [bold cyan]{len(files)}[/bold cyan] notice document(s) in [bold]{input_dir}[/bold]\n"
            f"Mode: {'[bold yellow]DRY RUN (No DB Writes)[/bold yellow]' if dry_run else '[bold green]LIVE SUPABASE INGESTION[/bold green]'}",
            title="Folder Ingestion",
            border_style="cyan",
        )
    )

    all_extracted: List[ExtractedAuctionProperty] = []
    for file_path in files:
        try:
            extracted = process_file(
                file_path=file_path,
                extractor=extractor,
                db_client=db_client,
                source_portal=f"Local Folder ({input_dir.name})",
                dry_run=dry_run,
            )
            all_extracted.extend(extracted)
        except Exception as e:
            console.print(f"[bold red]Failed processing {file_path.name}:[/bold red] {e}")
            logger.exception("Error processing %s", file_path)

    if all_extracted:
        render_properties_table(all_extracted, dry_run=dry_run)
        if dry_run:
            console.print("\n[bold]Raw Extracted JSON Sample (First Property):[/bold]")
            sample_json = all_extracted[0].model_dump(mode="json")
            console.print_json(json.dumps(sample_json, indent=2))


async def run_scrape_mode(
    extractor: GeminiAuctionExtractor,
    db_client: AuctionDatabaseClient,
    portal: str = "all",
    dry_run: bool = False,
):
    """Run Playwright scrapers, download notices, and process through OCR pipeline."""
    from scrapers.baanknet_scraper import BaanknetScraper
    from scrapers.bank_notice_crawler import BankNoticeCrawler
    console.print(
        Panel(
            f"Starting Bank Auction Scraping Pipeline (Target: [bold cyan]{portal}[/bold cyan])\n"
            f"Mode: {'[bold yellow]DRY RUN[/bold yellow]' if dry_run else '[bold green]LIVE INGESTION[/bold green]'}",
            title="Live Web Scraping",
            border_style="magenta",
        )
    )

    existing_urls = db_client.get_existing_pdf_urls()
    all_extracted: List[ExtractedAuctionProperty] = []

    # 1. Scrape Baanknet if selected
    if portal in ("baanknet", "all"):
        console.print("\n[bold cyan]=== Scraping Baanknet / IBAPI Portal ===[/bold cyan]")
        try:
            async with BaanknetScraper() as baanknet:
                async for item in baanknet.scrape():
                    pdf_path = item.get("pdf_path")
                    if pdf_path and Path(pdf_path).exists():
                        extracted = process_file(
                            file_path=Path(pdf_path),
                            extractor=extractor,
                            db_client=db_client,
                            source_portal="Baanknet",
                            dry_run=dry_run,
                        )
                        all_extracted.extend(extracted)
        except Exception as e:
            console.print(f"[bold red]Baanknet scraper error:[/bold red] {e}")

    # 2. Scrape Bank Notice Foreclosure Tables if selected
    if portal in ("canara", "iob", "sbi", "c1", "banks", "all"):
        console.print("\n[bold cyan]=== Scraping Bank Foreclosure Tables ===[/bold cyan]")
        try:
            async with BankNoticeCrawler(existing_pdf_urls=existing_urls) as crawler:
                async for item in crawler.scrape():
                    pdf_path = item.get("pdf_path")
                    if pdf_path and Path(pdf_path).exists():
                        extracted = process_file(
                            file_path=Path(pdf_path),
                            extractor=extractor,
                            db_client=db_client,
                            source_portal=item.get("source", "Bank Table"),
                            dry_run=dry_run,
                        )
                        all_extracted.extend(extracted)
        except Exception as e:
            console.print(f"[bold red]Bank crawler error:[/bold red] {e}")

    if all_extracted:
        render_properties_table(all_extracted, dry_run=dry_run)


def main():
    """CLI argument parsing and execution."""
    parser = argparse.ArgumentParser(
        description="Bank Auction Scraping & Multimodal OCR Microservice (SARFAESI Ingestion Engine)"
    )
    parser.add_argument(
        "--mode",
        choices=["scrape", "folder"],
        default=None,
        help="Operation mode: 'scrape' to crawl web portals, 'folder' to ingest local notices",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Path to directory containing local PDF notices or newspaper images",
    )
    parser.add_argument(
        "--scrape-all",
        action="store_true",
        help="Trigger scraping across all supported bank auction portals",
    )
    parser.add_argument(
        "--portal",
        type=str,
        default="all",
        choices=["all", "baanknet", "canara", "iob", "sbi", "c1", "banks"],
        help="Target auction portal to scrape",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and validate records without committing writes to Supabase",
    )

    args = parser.parse_args()
    settings = get_settings()
    setup_logging(settings.log_level)

    # Determine mode
    mode = args.mode
    if args.scrape_all:
        mode = "scrape"
    elif args.input_dir:
        mode = "folder"
    elif not mode:
        mode = "folder"  # Default if no arguments

    extractor = GeminiAuctionExtractor()
    db_client = AuctionDatabaseClient(dry_run=args.dry_run)

    if mode == "folder":
        input_folder = Path(args.input_dir or "./sample_notices")
        run_folder_mode(input_folder, extractor, db_client, dry_run=args.dry_run)
    elif mode == "scrape":
        asyncio.run(run_scrape_mode(extractor, db_client, portal=args.portal, dry_run=args.dry_run))


if __name__ == "__main__":
    main()

