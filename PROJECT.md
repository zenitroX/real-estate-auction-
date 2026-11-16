# Technical Specification: Indian Bank Auction Discovery Platform (SKANDX)

SKANDX is an auction discovery and lead acquisition platform for Indian SARFAESI bank assets. The system comprises a React SPA frontend and a Python backend service (REST API, Playwright web crawler, and Gemini 2.5 Flash multimodal OCR pipeline) backed by Supabase PostgreSQL.

---

## 1. System Architecture & Topology

SKANDX separates customer discovery from administrative verification using subdomain-based routing:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       SKANDX CLOUD ECOSYSTEM                                     │
│                                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        Unified React 19 SPA Deployment (Vercel)                          │   │
│   │                                                                                          │   │
│   │   Incoming Request ──► [ Subdomain Router (domain.js) ]                                  │   │
│   │                                │                                                         │   │
│   │               ┌────────────────┴────────────────┐                                        │   │
│   │               ▼                                 ▼                                        │   │
│   │   [ Customer Marketplace ]           [ Admin Verification Desk ]                         │   │
│   │   • Host: skandx.com                 • Host: admin.skandx.com                            │   │
│   │   • Verified assets filter           • Session-authenticated gate                        │   │
│   │   • Inquiries & WhatsApp routing     • NEEDS_MANUAL_REVIEW notice queue                  │   │
│   │   • Toll-free concierge desk         • Listing verification & edit desk                  │   │
│   └───────────────┬─────────────────────────────────┬────────────────────────────────────────┘   │
│                   │                                 │                                            │
│                   │         HTTPS / REST API        │ (Bearer HMAC Token)                        │
│                   └────────────────┬────────────────┘                                            │
│                                    ▼                                                             │
│                   ┌─────────────────────────────────┐                                            │
│                   │       Backend REST Server       │                                            │
│                   │         api.skandx.com          │                                            │
│                   │    (Python 3.12 / Port 8000)    │                                            │
│                   └────────────────┬────────────────┘                                            │
│                                    │                                                             │
│                                    ▼                                                             │
│                   ┌─────────────────────────────────┐      ┌─────────────────────────────────┐   │
│                   │      Supabase PostgreSQL        │◄─────┤     Asynchronous Ingestion      │   │
│                   │  • auction_properties           │      │    Worker (Playwright + OCR)    │   │
│                   │  • customer_leads               │      │  • Bank Crawlers (IBAPI, etc.)  │   │
│                   │  • gemini_spend_tracker         │      │  • Gemini 2.5 Flash Vision OCR  │   │
│                   └─────────────────────────────────┘      └─────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Subdomain Routing Engine
The frontend client router ([frontend/src/utils/domain.js](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/utils/domain.js)) evaluates the runtime hostname:
- **Administrative Context**: Requests matching `admin.*` (e.g. `admin.skandx.com` or `admin.localhost`) render the admin authentication view ([AdminLoginView.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/views/AdminLoginView.jsx)).
- **Customer Context**: Requests matching the base domain (`skandx.com` or `localhost`) render the public marketplace; unverified notices and administrative mutation controls are excluded from this view.
- **Local Development Overrides**: Hash routing (`/#admin`) and query parameters (`/?portal=admin`) are supported for offline and developer testing environments.

### 1.2 Ingestion & Processing Pipeline
Scraping and OCR workloads run asynchronously from user-facing REST request loops:
1. **Scraper Workers**: Playwright headless browser instances crawl scheduled bank auction notices from public auction repositories (e.g. IBAPI and partner gazettes).
2. **Multimodal OCR**: Scanned document images and PDF circulars are processed via Gemini 2.5 Flash Vision to extract statutory metadata (Reserve Price, EMD, auction date, survey numbers, possession status).
3. **Staging Persistence**: Parsed records are validated against Pydantic schemas and written to Supabase in a `NEEDS_MANUAL_REVIEW` state.

---

## 2. Customer & Admin Workflows

### 2.1 Customer Marketplace (`skandx.com`)
1. **Contact & Lead Capture Action**:
   - Every property card and details view provides a primary **Contact** action (replacing live bidding controls, as official bidding must occur on statutory bank portals under SARFAESI guidelines).
   - Prompts the **Contact Property Desk Modal**, allowing buyers to request property briefs, schedule inspections, or order legal title search packs.
2. **Privacy & Masked Bank Contacts**:
   - Direct personal mobile numbers of bank recovery officers are excluded from public responses to prevent spam and preserve attribution.
   - Buyers connect through a centralized concierge desk (`1800 - 202 - SKANDX`), WhatsApp routing, or the web callback intake form.
3. **Verification Filter**:
   - The public marketplace renders only records whose `review_status` is explicitly set to `PUBLISHED` (stamped with a green `✓ Verified` badge).

### 2.2 Admin Verification Desk (`admin.skandx.com`)
1. **Admin Authentication**:
   - Form-based authentication view requiring administrator credentials (`admin@skandx.com`).
   - Authenticates against `POST /api/admin/login`, which returns a cryptographically signed HMAC-SHA256 session token with timestamp expiration.
2. **Verification Queue (`NEEDS_MANUAL_REVIEW`)**:
   - Staff review OCR-extracted records from the ingestion pipeline.
   - **[✓ Verify & Publish]**: Updates status to `PUBLISHED`, exposing the property on the public marketplace.
   - **[Edit Extracted Details]**: Allows correction of title, reserve price, bank branch, auction cutoff dates, EMD amount, area, and possession status.
   - **[✕ Reject]**: Marks records as `REJECTED` with confirmation to prevent accidental loss.
3. **Buyer Leads Desk**:
   - Displays incoming inquiries submitted via customer contact forms.
   - Tracks operational status (`NEW`, `IN_REVIEW`, `SCHEDULED`, `CLOSED`).
4. **Ingestion Engine Status**:
   - Monitors background ingestion status and dispatches asynchronous crawler sync batches.

---

## 3. Data Models & Schema

### 3.1 Table: `auction_properties`
Aligned with [backend/ingestion/database/supabase_client.py](file:///c:/Users/rajkr/Documents/code-base/real%20estate/backend/ingestion/database/supabase_client.py):

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `TEXT` / `UUID` | Primary Key | Generated asset identifier. |
| `property_title` | `TEXT` | NOT NULL | Headline property title. |
| `bank_name` | `TEXT` | NOT NULL | Foreclosing institution (e.g., SBI, Canara Bank). |
| `branch_name` | `TEXT` | NULLABLE | Originating bank branch. |
| `reserve_price_inr` | `NUMERIC(14,2)` | NOT NULL | Statutory minimum auction price in INR. |
| `emd_amount_inr` | `NUMERIC(14,2)` | NOT NULL | Earnest Money Deposit in INR (10% of reserve). |
| `auction_date` | `TIMESTAMPTZ` | NOT NULL | Scheduled bidding event timestamp. |
| `emd_last_date` | `TIMESTAMPTZ` | NULLABLE | EMD caution deposit deadline. |
| `possession_type` | `TEXT` | NOT NULL | `'PHYSICAL'` or `'SYMBOLIC'`. |
| `area_sqft` | `NUMERIC(10,2)`| NULLABLE | Structure / land area in sq.ft. |
| `village_or_locality`| `TEXT` | NOT NULL | Locality, village, or taluk. |
| `state` | `TEXT` | NOT NULL | Indian state (e.g., `'Tamil Nadu'`). |
| `auction_event_hash` | `TEXT` | UNIQUE | Primary conflict key for deduplication. |
| `asset_fingerprint` | `TEXT` | NOT NULL | Deterministic asset hash for price drop detection. |
| `source_pdf_url` | `TEXT` | NULLABLE | URL to source scanned tender circular PDF. |
| `price_drop_percentage`| `NUMERIC(5,2)`| DEFAULT 0.0 | Calculated reduction from prior auction. |
| `review_status` | `TEXT` | NOT NULL | `'NEEDS_MANUAL_REVIEW'`, `'PUBLISHED'`, or `'REJECTED'`. |
| `created_at` | `TIMESTAMPTZ` | DEFAULT `NOW()` | Ingestion timestamp. |

```sql
-- DDL Migration: 001_create_auction_properties.sql
CREATE TABLE IF NOT EXISTS auction_properties (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    property_title TEXT NOT NULL,
    bank_name TEXT NOT NULL,
    branch_name TEXT,
    reserve_price_inr NUMERIC(14,2) NOT NULL,
    emd_amount_inr NUMERIC(14,2) NOT NULL,
    auction_date TIMESTAMPTZ NOT NULL,
    emd_last_date TIMESTAMPTZ,
    possession_type TEXT NOT NULL DEFAULT 'PHYSICAL',
    area_sqft NUMERIC(10,2),
    village_or_locality TEXT NOT NULL,
    state TEXT NOT NULL,
    auction_event_hash TEXT UNIQUE,
    asset_fingerprint TEXT NOT NULL,
    source_pdf_url TEXT,
    price_drop_percentage NUMERIC(5,2) DEFAULT 0.0,
    review_status TEXT NOT NULL DEFAULT 'NEEDS_MANUAL_REVIEW',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auction_properties_status ON auction_properties (review_status);
CREATE INDEX IF NOT EXISTS idx_auction_properties_fingerprint ON auction_properties (asset_fingerprint);

-- Enable RLS & Public Read Policy
ALTER TABLE auction_properties ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public Read Published" ON auction_properties 
    FOR SELECT USING (review_status = 'PUBLISHED');
CREATE POLICY "Service Role Full Access" ON auction_properties 
    FOR ALL USING (auth.role() = 'service_role');
```

### 3.2 Table: `customer_leads`
| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `TEXT` / `UUID` | Primary Key | Unique lead reference code (e.g., `#SK-8492`). |
| `customer_name` | `TEXT` | NOT NULL | Prospective buyer full name. |
| `phone` | `TEXT` | NOT NULL | 10-digit primary mobile contact number. |
| `email` | `TEXT` | NULLABLE | Email address for title document delivery. |
| `property_id` | `TEXT` | NOT NULL | Referenced `auction_properties.id`. |
| `property_title`| `TEXT` | NULLABLE | Snapshot title of referenced asset. |
| `inquiry_type` | `TEXT` | NOT NULL | `'Callback'`, `'Download Notice'`, `'Site Inspection'`, `'Legal Search Pack'`. |
| `notes` | `TEXT` | NULLABLE | Buyer requirement remarks or budget context. |
| `status` | `TEXT` | DEFAULT `'NEW'`| Operational status: `'NEW'`, `'IN_REVIEW'`, `'SCHEDULED'`, `'CLOSED'`. |
| `created_at` | `TIMESTAMPTZ` | DEFAULT `NOW()` | Submission timestamp. |

```sql
-- DDL Migration: 002_create_customer_leads.sql
CREATE TABLE IF NOT EXISTS customer_leads (
    id TEXT PRIMARY KEY DEFAULT ('#SK-' || LPAD(FLOOR(RANDOM() * 10000)::TEXT, 4, '0')),
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    property_id TEXT NOT NULL,
    property_title TEXT,
    inquiry_type TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'NEW',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customer_leads_created ON customer_leads (created_at DESC);
ALTER TABLE customer_leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public Insert Leads" ON customer_leads FOR INSERT WITH CHECK (true);
CREATE POLICY "Service Role Leads Access" ON customer_leads FOR ALL USING (auth.role() = 'service_role');
```

---

## 4. API Specification

Base URL: `https://api.skandx.com` (or `http://127.0.0.1:8000` in local development).

### 4.1 Public Endpoints
* **`GET /api/auctions`**
  - **Auth**: None
  - **Query Params**: `limit` (integer, default 100), `state` (string)
  - **Response 200**: `[ { "id": "CAN-001", "property_title": "...", "reserve_price_inr": 4500000, ... } ]`
* **`POST /api/contact`**
  - **Auth**: None
  - **Request Body**:
    ```json
    {
      "customerName": "Ramesh Kumar",
      "phone": "9876543210",
      "email": "ramesh@example.com",
      "propertyId": "CAN-001",
      "inquiryType": "Site Inspection",
      "message": "Interested in site inspection on Saturday."
    }
    ```
  - **Response 200**: `{ "status": "success", "leadId": "#SK-8492", "message": "Inquiry recorded" }`
  - **Response 400**: `{ "error": "Missing customerName or phone" }`
  - **Response 429**: `{ "error": "Rate limit exceeded. Please wait 60 seconds." }`

### 4.2 Administrative Endpoints
* **`POST /api/admin/login`**
  - **Auth**: None (Body credentials)
  - **Request Body**: `{ "email": "admin@skandx.com", "password": "..." }`
  - **Response 200**: `{ "status": "success", "token": "skandx-adm-1773582000-a1b2c3d4..." }`
  - **Response 401**: `{ "error": "Invalid administrative credentials" }`
* **`GET /api/admin/properties`**
  - **Auth**: `Authorization: Bearer <token>`
  - **Query Params**: `status` (e.g. `'NEEDS_MANUAL_REVIEW'`)
  - **Response 200**: List of all property records including pending items.
* **`POST /api/admin/properties/verify`**
  - **Auth**: `Authorization: Bearer <token>`
  - **Request Body**:
    ```json
    {
      "id": "CAN-001",
      "status": "PUBLISHED",
      "fields": {
        "property_title": "Corrected Title",
        "reserve_price": 4800000
      }
    }
    ```
  - **Response 200**: `{ "status": "success", "id": "CAN-001", "new_status": "PUBLISHED" }`
* **`GET /api/admin/leads`**
  - **Auth**: `Authorization: Bearer <token>`
  - **Query Params**: `limit` (default 100), `offset` (default 0)
  - **Response 200**: `{ "leads": [ ... ], "total": 24 }`
* **`GET /api/admin/pdf-proxy`**
  - **Auth**: `Authorization: Bearer <token>`
  - **Query Params**: `url` (encoded external PDF URL)
  - **Response 200**: Streams raw PDF bytes with `Content-Type: application/pdf` to bypass bank CORS / `X-Frame-Options`.
* **`POST /api/scrape/trigger`**
  - **Auth**: `Authorization: Bearer <token>`
  - **Response 202 Accepted**: `{ "status": "triggered", "message": "Crawler workflow dispatched" }`
  - **Response 409**: `{ "error": "Crawler already active" }`

---

## 5. Security Architecture & Threat Model

1. **Session Authentication Handshake**:
   - The backend signs tokens using HMAC-SHA256: `skandx-adm-{timestamp}-{signature}` using an uncommitted `ADMIN_JWT_SECRET`.
   - The server verifies that tokens are valid for $\le 24$ hours and that signatures match.
   - Requests without valid headers return HTTP 401.
2. **Access Control Policy**:
   - Public visitors have read-only access to records with `review_status = 'PUBLISHED'`.
   - **All** administrative endpoints (`/api/admin/*`, including `GET /api/admin/leads` which exports buyer PII, and mutation routes) strictly enforce HMAC Bearer token validation.
3. **CORS, Rate Limiting & Input Validation**:
   - Reverse-proxy-aware sliding window rate limiter on `POST /api/contact`: extracts client IP via `X-Forwarded-For` with fallback to `client_address[0]`, guarded by `threading.Lock()`, allowing up to 15 req/min burst.
   - The REST server enforces a 10MB payload ceiling to prevent memory denial-of-service attacks.
   - Input fields in `POST /api/contact` are validated and sanitized prior to database persistence.

---

## 6. Repository Layout

```text
.
├── backend/                       # Python Backend Service
│   ├── app.py                     # REST API server (port 8000) with CORS middleware
│   │                              # Routes: /api/auctions, /api/admin/properties,
│   │                              #         /api/admin/login, /api/contact, /api/scrape/trigger
│   ├── ingestion/                 # Scrapers & Multimodal AI OCR Engine
│   │   ├── main.py                # Crawler & pipeline CLI entrypoint
│   │   ├── scrapers/              # Bank portal crawlers (Baanknet, IBAPI)
│   │   ├── ocr_pipeline/          # Gemini 2.5 Flash Vision OCR extractor
│   │   ├── database/              # Supabase client & duplicate record filtering
│   │   └── models/                # Pydantic data schemas
│   ├── data/                      # Local storage snapshots & leads.json cache
│   ├── Dockerfile                 # Lightweight container image for REST API
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Backend environment template
├── frontend/                      # React 19 Single Page Application
│   ├── src/
│   │   ├── components/            # Header, Footer, PropertyCard, Modals (ContactModal)
│   │   ├── views/                 # Customer views (Home, Properties, Details, Dashboard)
│   │   │                          # Admin views (AdminView, AdminLoginView)
│   │   ├── utils/domain.js        # Subdomain detector (admin.* vs customer)
│   │   ├── data/                  # API client, initial properties, leads, initial user
│   │   ├── App.jsx                # Domain router, auth guard, state coordination
│   │   └── main.jsx
│   ├── public/                    # Static assets & fallback data
│   ├── dist/                      # Standalone production build
│   ├── package.json
│   └── vite.config.js
├── serve.py                       # Local dev API runner (delegates to backend/app.py)
├── run_web.bat                    # Windows 1-click launcher
└── PROJECT.md                     # Technical specification and architecture guide
```

---

## 7. Production DNS & Deployment Configuration

When deploying the frontend to hosting providers (e.g., Vercel, Cloudflare Pages):
1. **Primary Domain**: Point `skandx.com` and `www.skandx.com` to the frontend deployment.
2. **Admin Subdomain**: Add a CNAME record in the domain registrar:
   ```text
   Type:  CNAME
   Host:  admin
   Value: cname.vercel-dns.com (or deployment host CNAME)
   ```
Both records route to the same frontend build; client-side routing resolves the admin view when the incoming hostname matches `admin.*`.

---

## 8. Local Development & Testing

### 8.1 Backend API Execution
```powershell
.\.venv\Scripts\python.exe serve.py
# Server running at http://127.0.0.1:8000
```

### 8.2 Frontend Dev Server Execution
```powershell
cd frontend
npm run dev
# Vite dev server running at http://localhost:5173
```

### 8.3 Local Verification
* **Customer Marketplace**: Open `http://localhost:5173`
* **Admin Subdomain (Simulated via Subdomain)**: Open `http://admin.localhost:5173` (Chromium and Firefox resolve `*.localhost` to 127.0.0.1 per RFC 6761)
* **Admin Subdomain (Simulated via Hash/Query)**: Open `http://localhost:5173/#admin` or `http://localhost:5173/?portal=admin`
* **Demo Credentials**:
  - Email: `admin@skandx.com`
  - Password: `skandx@admin2026`

---

## 9. Detailed Implementation Plan

Execution roadmap across five delivery phases:

### Phase 1: Security & Auth Hardening (Immediate P0)
1. **Unify Admin Authentication**:
   - Update [frontend/src/views/AdminLoginView.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/views/AdminLoginView.jsx) to submit credentials to `POST /api/admin/login`.
   - Store the issued HMAC token (`skandx-adm-{ts}-{sig}`) in browser `sessionStorage`.
   - Remove client-side mock credential matching and strip hardcoded passwords from `AdminLoginView.jsx`.
   - Update [frontend/src/data/api.js](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/data/api.js) to throw on HTTP 401 instead of returning synthetic `{ status: 'success', local: true }`.
   - In `App.jsx`, catch 401 exceptions in `handleVerifyProperty`, roll back optimistic state updates, and invoke `handleAdminLogout()`.
2. **Code-Split Admin Routes with React 19 Suspense**:
   - Refactor [frontend/src/App.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/App.jsx) to dynamically import `AdminView` and `AdminLoginView` via `React.lazy()`.
   - Enclose lazy admin components inside `<React.Suspense fallback={<div className="view-loading">Loading Admin Desk...</div>}>` to satisfy React 19 requirements.
   - Verify administrative modules are excluded from the public vendor chunk.
3. **Proxy-Aware Contact Rate-Limiting**:
   - In `backend/app.py`, implement an in-memory sliding window rate limiter on `POST /api/contact`.
   - Extract client IP from `headers.get("X-Forwarded-For", "").split(",")[0].strip() or self.client_address[0]`.
   - Guard dictionary access with `threading.Lock()` and enforce a 15 req/min limit to allow burst offline queue syncs without throttling.

### Phase 2: Database Persistence & Verification Review UI
1. **Execute Supabase SQL Migrations**:
   - Run DDL migrations for `auction_properties` and `customer_leads` in Supabase SQL editor using schemas defined in Section 3.1 and 3.2.
   - Verify Row Level Security policies allow public reads for `review_status = 'PUBLISHED'` and service-role write operations.
   - Deprecate local `backend/data/leads.json` dual-writes; make Supabase the primary persistent store.
2. **Client Offline Queue Event Registration**:
   - Export `flushOfflineLeads()` from `frontend/src/data/api.js`.
   - In `frontend/src/App.jsx`, attach `window.addEventListener('online', flushOfflineLeads)` and `window.addEventListener('focus', flushOfflineLeads)`.
3. **Split-Pane Notice PDF Viewer & Proxy Endpoint**:
   - Add `GET /api/admin/pdf-proxy` in `backend/app.py` to stream remote bank notice PDFs with `Content-Type: application/pdf`, bypassing bank portal `X-Frame-Options` restrictions.
   - Update [frontend/src/views/AdminView.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/views/AdminView.jsx) to render a split-pane preview pane displaying the source PDF circular alongside editable OCR fields.
4. **Remove Deprecated Bidding Module & Prevent Dashboard Crash**:
   - Delete `frontend/src/components/Modals/BiddingModal.jsx`.
   - In [frontend/src/views/DashboardView.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/views/DashboardView.jsx), set default `myBids = {}` and remove the active bids tab to prevent `TypeError: Cannot convert undefined or null to object` on `Object.keys(myBids)`.
   - Clean up vestigial `onBid` props in `PropertyCard.jsx` and `App.jsx`.

### Phase 3: Scraper Decoupling & Automated Scheduling
1. **Decouple Crawlers to GitHub Actions**:
   - Create `.github/workflows/daily_crawler.yml` executing `python -m ingestion.main --scrape-all` on scheduled cron (02:00 AM IST) using repository secrets `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `GEMINI_API_KEY`.
   - Update `POST /api/scrape/trigger` in `backend/app.py` to dispatch `.github/workflows/daily_crawler.yml` via GitHub REST API (`workflow_dispatch`), returning `HTTP 202 Accepted`.
   - Remove Playwright Chromium system packages from `backend/Dockerfile` to keep web API container memory usage within the 512MB Render RAM allocation.
2. **Durable Gemini OCR Spend Controls**:
   - Create Supabase table `gemini_spend_tracker` (`usage_date DATE PRIMARY KEY, token_count INT DEFAULT 0, cost_usd NUMERIC(8,4)`).
   - In `backend/ingestion/ocr_pipeline/gemini_extractor.py`, query today's accumulated tokens before API invocation; abort with log notification if exceeding 500,000 tokens/day.

### Phase 4: Monetization & Notification Features
1. **Possession Risk Badges**:
   - Update `fetchLiveAuctions()` in [frontend/src/data/api.js](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/data/api.js) to normalize `possessionType: item.possession_type || 'PHYSICAL'`.
   - Update [frontend/src/components/PropertyCard.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/components/PropertyCard.jsx) to render possession badges:
     - `PHYSICAL`: Green badge labeled **"Physical Vacant Possession — Direct Handover"**.
     - `SYMBOLIC`: Amber badge labeled **"Symbolic Possession — DRT / Section 14 Diligence Advised"**.
2. **15-Day Pre-Auction Bridge Loan Financing Calculator**:
   - Implement a pre-auction financing calculator on [frontend/src/views/PropertyDetailsView.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/views/PropertyDetailsView.jsx) calculating the mandatory 25% Day-1 deposit and 75% 15-day settlement balance, routing pre-qualified leads to partnering NBFCs.
3. **Price-Drop WhatsApp Notifications**:
   - In `backend/ingestion/database/supabase_client.py`, check `record.get("price_drop_percentage") >= 10.0` following property upsert.
   - Dispatch template alert payloads via WhatsApp Business API webhook to subscribed investor leads.

### Phase 5: Production Domain Launch & Smoke Verification
1. **Custom Domain Binding & Vercel Environment Variables**:
   - Configure `VITE_API_URL=https://api.skandx.com` in Vercel project environment settings.
   - Bind `skandx.com` and `admin.skandx.com` in Vercel.
   - Bind `api.skandx.com` in Render.
2. **End-to-End Verification Pipeline**:
   - Execute complete smoke test: Crawl notice &rarr; Gemini OCR parse &rarr; Admin review & edit &rarr; Publish &rarr; Customer portal rendering &rarr; Lead inquiry submission &rarr; Supabase persistence verification.
