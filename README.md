# Indian Bank Auction Tracker

A searchable web dashboard for reviewing Indian bank property auctions, backed by a Python API that reads listings from Supabase. The repository also contains an ingestion engine for collecting bank auction notices, extracting property details from PDFs and images, tracking repeat auctions and price changes, and saving reviewed records.

> **Public data notice:** This repository is public. The checked-in `web/auctions_data.json` file is served as a fallback snapshot and may contain borrower names, property details, and auction information. Review the snapshot before sharing or publishing this project. Never commit `.env` files, API keys, or Supabase service-role credentials.

## Features

- Search and filter auction listings by bank, borrower, locality, survey number, category, and district.
- Sort by auction date, reserve price, or price drop.
- View reserve price, EMD, auction dates, location, possession, and source links.
- Fetch recent listings through the Python API, with an in-memory cache and local JSON fallback.
- Ingest local auction notices or crawl supported bank portals with the separate ingestion engine.
- Route digital and scanned PDFs through text extraction or Gemini vision OCR.
- Deduplicate property and auction records, detect repeat-auction price drops, and flag records needing review.

## Repository layout

```text
.
├── serve.py                         # Web server and Supabase API proxy
├── run_web.bat                      # Windows launcher
├── web/
│   ├── index.html                   # Dashboard
│   └── auctions_data.json           # Local fallback data snapshot
├── auction-ingestion-engine/
│   ├── main.py                      # Ingestion CLI
│   ├── requirements.txt
│   ├── .env.example                 # Configuration template
│   ├── config/                      # Runtime settings
│   ├── database/                    # Supabase schema and persistence
│   ├── models/                      # Validated auction data models
│   ├── ocr_pipeline/                # PDF routing and Gemini extraction
│   ├── scrapers/                    # Portal and bank notice crawlers
│   ├── sample_notices/              # Example notice PDFs
│   └── tests/                       # Pipeline tests
└── docs/
    └── Baanknet_Bank_Auction_Business_Blueprint.docx
```

## Run the dashboard

### Requirements

- Python 3.10 or later.
- The `python-dotenv` package, included in `auction-ingestion-engine/requirements.txt`.

### Windows

From the repository root, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r auction-ingestion-engine\requirements.txt
.\.venv\Scripts\python.exe serve.py
```

Alternatively, after installing the dependencies, double-click `run_web.bat`.

Open [http://127.0.0.1:3000](http://127.0.0.1:3000).

### macOS or Linux

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r auction-ingestion-engine/requirements.txt
python serve.py
```

Then open [http://127.0.0.1:3000](http://127.0.0.1:3000).

The server attempts to fetch up to 50 records from the configured Supabase project, ordered by auction date newest first. If the request fails, it serves the checked-in `web/auctions_data.json` snapshot. The API endpoints are:

- `GET /api/auctions` — auction data, source, count, and request latency.
- `GET /api/health` — server health status.

The local server binds to `127.0.0.1` and is intended for local use. It is **not configured for direct public hosting** as-is.

## Configure Supabase

The dashboard server loads a root `.env` file when present. Create it from PowerShell:

```powershell
Copy-Item auction-ingestion-engine\.env.example .env
```

Set the project URL and a server-side key in `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_server_side_key
```

The server prefers `SUPABASE_SERVICE_ROLE_KEY` if set, then falls back to `SUPABASE_KEY`. Treat either value as a secret. The service-role key bypasses Row Level Security and must never be embedded in the frontend or committed to Git. Add secrets through your hosting provider's environment-variable settings if deploying.

Without a configured key, the server may be unable to fetch live records; it will try the local JSON snapshot instead.

## Auction ingestion engine

The ingestion engine is a separate command-line tool. Install dependencies and configure its environment:

```bash
cd auction-ingestion-engine
python -m venv .venv
```

Activate the environment (`.venv\Scripts\Activate.ps1` in PowerShell, or `source .venv/bin/activate` on macOS/Linux), then:

```bash
python -m pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` inside `auction-ingestion-engine/` and set credentials as needed:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_server_side_key
```

Other supported settings include `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_MODEL`, `PLAYWRIGHT_HEADLESS`, `RATE_LIMIT_REQUESTS_PER_MINUTE`, `SCRAPE_STATE`, `TMP_DOWNLOAD_DIR`, `LOG_LEVEL`, and `REQUEST_TIMEOUT_SECONDS`. See [`config/settings.py`](auction-ingestion-engine/config/settings.py) and [`.env.example`](auction-ingestion-engine/.env.example).

### Database setup

Run [`database/schema.sql`](auction-ingestion-engine/database/schema.sql) in the Supabase SQL Editor before using the ingestion engine. It creates the auction table, required types, indexes, and update trigger.

### CLI examples

Run these commands from `auction-ingestion-engine/`:

```bash
# Extract local PDFs/images without writing records to Supabase
python main.py --input-dir ./sample_notices --dry-run

# Process local notices and write records to Supabase
python main.py --input-dir ./sample_notices

# Crawl all supported portals
python main.py --scrape-all

# Crawl a selected portal
python main.py --mode scrape --portal baanknet
python main.py --mode scrape --portal canara
python main.py --mode scrape --portal iob
python main.py --mode scrape --portal sbi
```

Portal crawling makes external network requests and may require Chromium, valid credentials, and changes to the source sites. Verify the source websites' terms and applicable laws before running crawlers. Live ingestion writes to the configured Supabase database; use `--dry-run` to avoid database writes.

## Tests

From `auction-ingestion-engine/`, install the dependencies and run:

```bash
pytest tests/ -v
```

## Deployment

For a public deployment, use a Python-capable host such as Render and configure it to start `serve.py`. The server binds to `0.0.0.0` and reads the port from the host-provided `PORT` environment variable (defaulting to `3000` for local development). Configure Supabase credentials as host secrets; do not commit them.

Because the dashboard includes personal and property information, inspect or remove the fallback snapshot before deploying publicly. A public deployment can expose both the local snapshot and any records returned by Supabase.

## Security

- Keep all `.env` files and credentials out of version control; `.gitignore` excludes them.
- Rotate any key that was accidentally exposed, even if it has since been removed from the current files.
- Never send the Supabase service-role key to browser code.
- Use a restricted Supabase key and appropriate Row Level Security policies whenever possible.
- Do not publish personal borrower/property details unless you have confirmed you are permitted to share them.

## License

See [`LICENSE`](LICENSE) in the GitHub repository.
