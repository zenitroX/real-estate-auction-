# Project Overview: Indian Bank Auction Discovery Platform (SKANDX)

SKANDX is a decoupled, production-ready real estate auction discovery and lead acquisition platform for Indian SARFAESI bank assets. It is split into an independent **React Frontend SPA** and a **Unified Python Backend** (REST API + Playwright Crawler & Gemini 2.5 Flash Multimodal OCR Ingestion Engine) connected to Supabase Cloud PostgreSQL.

---

## 1. Domain & Subdomain Architecture

For bank-grade security, access control, and clean brand separation, SKANDX uses **subdomain isolation**:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SKANDX CLOUD ECOSYSTEM                                 │
│                                                                                        │
│  ┌──────────────────────────────┐              ┌────────────────────────────────────┐  │
│  │   Customer Marketplace       │              │      Admin Verification Desk       │  │
│  │       skandx.com             │              │         admin.skandx.com           │  │
│  │  (or www.skandx.com)         │              │                                    │  │
│  │                              │              │                                    │  │
│  │ • Public buyers & investors  │              │ • Protected by Admin Security Gate │  │
│  │ • Only "✓ Verified" assets   │              │ • Audit-trail session management   │  │
│  │ • "Contact" action & hotline │              │ • PENDING_REVIEW crawler queue     │  │
│  │ • WhatsApp chat & inquiries  │              │ • Instant [✓ Verify & Publish]     │  │
│  │ • No admin controls exposed  │              │ • Buyer Leads manager              │  │
│  │ • Lightweight & fast for SEO │              │ • Playwright crawler live stream   │  │
│  └──────────────┬───────────────┘              └─────────────────┬──────────────────┘  │
│                 │                                                │                     │
│                 │               HTTPS / REST API                 │                     │
│                 └───────────────────────┬────────────────────────┘                     │
│                                         │                                              │
│                                         ▼                                              │
│                        ┌─────────────────────────────────┐                             │
│                        │       Backend REST Server       │                             │
│                        │         api.skandx.com          │                             │
│                        │     (Python 3.12 / Port 8000)   │                             │
│                        └────────────────┬────────────────┘                             │
│                                         │                                              │
│                                         ▼                                              │
│                        ┌─────────────────────────────────┐                             │
│                        │      Supabase PostgreSQL        │                             │
│                        │      auction_properties         │                             │
│                        └─────────────────────────────────┘                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Automatic Domain Routing
* The frontend ([frontend/src/utils/domain.js](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/utils/domain.js)) automatically detects the current hostname:
  * When accessed via `admin.*` (e.g. `admin.skandx.com` or `admin.localhost`), it enforces the **Admin Security Gateway** ([AdminLoginView.jsx](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/src/views/AdminLoginView.jsx)).
  * When accessed via `skandx.com`, it loads the **Customer Marketplace**; admin features and unverified notices are completely hidden.

---

## 2. Implemented Customer & Admin Experience

### A. Customer Website (`skandx.com`)
1. **"Contact" Action (Replaced "Bid Now"):**
   - Every property card and details view features a prominent **"Contact"** button.
   - Triggers the **Contact Property Desk Modal**, allowing buyers to schedule site inspections, request title search packs, or submit callback inquiries.
2. **Hidden Officer Personal Numbers:**
   - Raw officer phone numbers are shielded from public spam.
   - Customers reach the desk via the **Central Toll-Free Hotline** (`1800 - 202 - SKANDX`), direct **WhatsApp Chat**, or the inquiry lead form.
3. **Strict "✓ Verified" Tag & Filtering:**
   - **Only Admin-Verified properties** appear on the customer portal, stamped with a green **`✓ Verified`** seal tag.

### B. Admin Portal (`admin.skandx.com`)
1. **Admin Security Gate:**
   - 256-bit encrypted authentication screen requiring admin credentials.
   - Session management with logout control.
2. **Verification Queue (`PENDING_REVIEW`):**
   - Review incoming notices extracted by Gemini 2.5 Flash Vision OCR.
   - **[✓ Verify & Publish]**: Approves and instantly publishes to `skandx.com`.
   - **[Edit Extracted Details]**: Inline editor for correcting OCR text, dates, or prices before approving.
   - **[✕ Reject]**: Discards invalid or duplicate notices.
3. **Buyer Leads Desk:**
   - Real-time stream of inquiries submitted from the customer "Contact" modal.
   - Status updates (`NEW`, `IN_REVIEW`, `SCHEDULED`, `CLOSED`) with direct contact actions.
4. **Crawler Engine Controller:**
   - Live trigger button and execution log terminal for partner bank crawlers.

---

## 3. Repository Layout

```text
.
├── backend/                       # Python Backend Service
│   ├── app.py                     # REST API server (port 8000) with full CORS
│   │                              # Routes: /api/auctions, /api/admin/properties,
│   │                              #         /api/admin/login, /api/contact, /api/scrape/trigger
│   ├── ingestion/                 # Scrapers & Multimodal AI OCR Engine
│   │   ├── main.py                # Crawler & pipeline CLI
│   │   ├── scrapers/              # Bank portal crawlers (Baanknet, IBAPI)
│   │   ├── ocr_pipeline/          # Gemini 2.5 Flash Vision OCR
│   │   ├── database/              # Supabase client & deduplication engine
│   │   └── models/                # Pydantic schemas
│   ├── data/                      # Local fallback snapshots & leads.json
│   ├── Dockerfile                 # Container image with Playwright Chromium
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Backend environment variables
├── frontend/                      # React 19 SPA
│   ├── src/
│   │   ├── components/            # Header, Footer, PropertyCard, Modals (ContactModal)
│   │   ├── views/                 # Customer views (Home, Properties, Details, Dashboard)
│   │   │                          # Admin views (AdminView, AdminLoginView)
│   │   ├── utils/domain.js        # Subdomain detector (admin.* vs customer)
│   │   ├── data/                  # API client, initial properties, leads, initial user
│   │   ├── App.jsx                # Domain router, auth guard, state coordination
│   │   └── main.jsx
│   ├── public/                    # Offline fallback data & assets
│   ├── dist/                      # Standalone production build
│   ├── package.json
│   └── vite.config.js
├── serve.py                       # Local dev API runner (delegates to backend/app.py)
├── run_web.bat                    # Windows 1-click API launcher
└── PROJECT.md                     # Comprehensive architecture and workflow guide
```

---

## 4. Quick Start & Execution

### Run Backend API
```powershell
.\.venv\Scripts\python.exe serve.py
# Server running at http://127.0.0.1:8000
```

### Run Frontend Dev Server
```powershell
cd frontend
npm run dev
# Vite dev server running at http://localhost:5173
```

### How to Test Locally:
* **Customer Marketplace:**  
  Open `http://localhost:5173`
* **Admin Subdomain (Simulated via Subdomain):**  
  Open `http://admin.localhost:5173` *(modern Chrome, Edge, and Firefox natively resolve `*.localhost` to 127.0.0.1!)*
* **Admin Subdomain (Simulated via Hash/Query):**  
  Open `http://localhost:5173/#admin` OR `http://localhost:5173/?portal=admin`
* **Demo Admin Credentials:**  
  - Email: `admin@skandx.com`
  - Password: `skandx@admin2026`  
  *(Or click the 1-click **Autofill demo credentials** button on the login screen)*

---

## 5. Production DNS Configuration (Free & Standard)

When hosting in production (e.g. Vercel, Netlify, Cloudflare):
1. **Customer Domain:**  
   Map `skandx.com` and `www.skandx.com` &rarr; Frontend Deployment.
2. **Admin Subdomain:**  
   In your domain registrar (GoDaddy, Namecheap, Cloudflare DNS), add:
   ```text
   Type:  CNAME
   Host:  admin
   Value: cname.vercel-dns.com (or your frontend deployment URL)
   ```
   *No second domain purchase needed.* Both route to the same app build, and the application automatically routes to the Admin Gateway!
