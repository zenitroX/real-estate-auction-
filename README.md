# SKANDX — Indian Bank Auction Discovery & Verification Platform

[![React](https://img.shields.io/badge/React-19.0-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.2-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.49-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/)
[![Gemini OCR](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-Cloud%20PostgreSQL-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](#license)

**SKANDX** is an institutional discovery, legal diligence, and lead acquisition platform for Indian bank auction & distressed properties (under the SARFAESI Act, 2002 & DRT).

It features a decoupled architecture with an independent **React 19 Frontend SPA** and a **Unified Python Backend** (multi-threaded REST API server + Playwright crawler & Gemini 2.5 Flash Multimodal AI Vision OCR engine) connected to a managed Supabase Cloud PostgreSQL database.

---

## 1. Domain & Architecture Overview

For bank-grade security, access control, and clean brand separation, SKANDX enforces **Subdomain Isolation**:

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
│  │ • Officer phone masked       │              │ • Buyer Leads manager              │  │
│  │ • No admin controls exposed  │              │ • Playwright crawler live stream   │  │
│  │ • Lightweight & fast for SEO │              │                                    │  │
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

---

## 2. Core Business Logic & Workflow

In Indian bank auctions, buyers **do not bid directly on third-party broker websites**; statutory bidding legally occurs only on government/bank empanelled auction portals (e-Bikray, IBAPI, MSTC, C1 India) after depositing Earnest Money (EMD). SKANDX serves as the trusted discovery, verification, and buyer facilitation desk.

1. **"Contact" Replaces "Bid Now":**  
   Every property features a prominent **"Contact"** button opening the *Contact Property Desk Modal* with:
   * **Central Toll-Free Hotline:** `1800 - 202 - SKANDX` (1-click call).
   * **Instant WhatsApp Chat:** Pre-filled message with property title and reserve price.
   * **Callback & Inspection Lead Form:** Collects buyer name, phone, email, and requested service (*Site Visit Inspection*, *Legal Title Search*, *EMD / Financing Guidance*).
2. **Hidden Officer Personal Numbers:**  
   Raw personal mobile numbers are shielded to prevent public spam; calls route through the central desk and WhatsApp liaison.
3. **Admin Verification Gateway (`admin.skandx.com`):**  
   * **Verification Queue:** Scraped notices land in `PENDING_REVIEW`. Admins can inspect extracted fields, edit OCR details, and click **`[✓ Verify & Publish]`** to push properties live to the public site.
   * **Strict `✓ Verified` Badge:** Customers only see listings verified by the back-office team.
   * **Buyer Leads Desk:** Real-time feed of buyer inquiries with interactive follow-up status tracking (`NEW`, `IN_REVIEW`, `CONTACTED`, `SITE_VISIT_BOOKED`, `CLOSED`).
   * **Crawler Engine Controller:** On-demand Playwright crawler trigger with live terminal execution stream.

---

## 3. Repository Layout

```text
.
├── backend/                       # Python Backend Service
│   ├── app.py                     # Multi-threaded REST API server (Port 8000)
│   │                              # Routes: /api/auctions, /api/admin/properties,
│   │                              #         /api/admin/login, /api/contact, /api/scrape/trigger
│   ├── ingestion/                 # Scrapers & Multimodal AI OCR Engine
│   │   ├── main.py                # Crawler & pipeline CLI
│   │   ├── scrapers/              # Bank portal crawlers (Baanknet, IBAPI, SBI)
│   │   ├── ocr_pipeline/          # Gemini 2.5 Flash Vision & PyMuPDF router
│   │   ├── database/              # Supabase client, schema & fingerprinting
│   │   └── models/                # Validated Pydantic auction schemas
│   ├── data/                      # Local fallback snapshots & leads.json storage
│   ├── Dockerfile                 # Production container with Playwright Chromium
│   ├── requirements.txt           # Unified backend dependencies
│   └── .env.example               # Backend environment variables
├── frontend/                      # Decoupled React 19 SPA
│   ├── src/
│   │   ├── components/            # Header, Footer, PropertyCard, Modals (ContactModal)
│   │   ├── views/                 # Customer views (Home, Properties, Details, Dashboard)
│   │   │                          # Admin views (AdminView, AdminLoginView)
│   │   ├── utils/domain.js        # Subdomain detector (admin.* vs customer)
│   │   ├── data/                  # API client, initial properties, leads, initial user
│   │   ├── App.jsx                # Domain router, auth guard, state coordination
│   │   └── main.jsx
│   ├── public/                    # Offline fallback data & SVG assets
│   ├── dist/                      # Standalone production build
│   ├── vercel.json                # SPA routing rewrites for Vercel
│   ├── package.json
│   └── vite.config.js
├── serve.py                       # Local dev API runner (delegates to backend/app.py)
├── run_web.bat                    # Windows 1-click API launcher
├── PROJECT.md                     # Comprehensive architecture and workflow blueprint
└── README.md                      # Project documentation
```

---

## 4. Quick Start (Run Locally)

### Step 1: Start the Backend REST API Server

```powershell
.\.venv\Scripts\python.exe serve.py
# Or double-click run_web.bat
# Running on http://127.0.0.1:8000
```

### Step 2: Start the React Frontend

In a second terminal:

```powershell
cd frontend
npm run dev
# Running on http://localhost:5173
```

### Step 3: Test Both Portals Locally

* **Customer Marketplace (`skandx.com` simulation):**  
  Open **`http://localhost:5173`** &rarr; Browse verified properties, filter by budget/bank, and click **"Contact"** to submit a callback lead.
* **Admin Verification Desk (`admin.skandx.com` simulation):**  
  Open **`http://admin.localhost:5173`** *(or `http://localhost:5173/#admin`)*.
* **Admin Login Credentials:**  
  Click **"Autofill demo credentials"** (`admin@skandx.com` / `skandx@admin2026`) &rarr; Click **"Unlock Verification Console"**.
* **Verify a Listing:**  
  Under the *Verification Queue*, click **`[✓ Verify & Publish]`** &rarr; The property instantly goes live on the customer site with the green `✓ Verified` badge.

---

## 5. How to Deploy Online

### 1. Deploy Backend to Render (Docker Web Service)

1. Sign in to **[Render.com](https://render.com/)** and click **New +** &rarr; **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   * **Root Directory:** `backend`
   * **Runtime:** Select **Docker** (Render detects [backend/Dockerfile](backend/Dockerfile)).
4. Add Environment Variables:
   ```text
   PORT = 8000
   SUPABASE_URL = https://pxviudwphxclnhzbglej.supabase.co
   SUPABASE_KEY = your_supabase_service_role_key
   GEMINI_API_KEY = your_google_gemini_api_key
   ADMIN_EMAIL = admin@skandx.com
   ADMIN_PASSWORD = your_strong_admin_password
   ```
5. Click **Deploy Web Service** &rarr; Copy your live backend URL (e.g. `https://skandx-backend.onrender.com`).

---

### 2. Deploy Frontend to Vercel

1. Sign in to **[Vercel.com](https://vercel.com/)** &rarr; Click **Add New...** &rarr; **Project**.
2. Import your GitHub repository.
3. Configure settings:
   * **Framework Preset:** `Vite`
   * **Root Directory:** `frontend`
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
4. Add Environment Variable:
   ```text
   VITE_API_URL = https://skandx-backend.onrender.com
   ```
5. Click **Deploy** &rarr; Copy your live URL (e.g. `https://skandx.vercel.app`).

---

### 3. Setup Custom Domains (Free & Standard)

In Vercel &rarr; **Settings** &rarr; **Domains**:

1. **Customer Domain (`skandx.com`):**
   * Add `skandx.com` and `www.skandx.com`.
   * In your domain DNS (GoDaddy, Namecheap, Cloudflare), set an **A** record to `76.76.21.21`.
2. **Admin Subdomain (`admin.skandx.com`):**
   * Add `admin.skandx.com`.
   * In your domain DNS, set a **CNAME** record for `admin` pointing to `cname.vercel-dns.com`.

> Both domains point to the **same deployment**. The built-in domain detector automatically routes customers to the public marketplace and staff to the security gateway.

---

## 6. Testing & Quality Verification

### Run Ingestion Pipeline Unit Tests
```powershell
.\.venv\Scripts\python.exe -m pytest backend\ingestion\tests\test_pipeline.py
# Result: 9 passed in 0.68s (100% pass rate)
```

### Build Frontend for Production
```powershell
cd frontend
npm run build
# Result: 2,121 modules transformed into frontend/dist/ in 4.35s (0 errors)
```

---

## 7. Security & Compliance

* **Admin Authentication:** Protected back-office endpoints (`/api/admin/properties`, `/api/admin/leads`, `/api/scrape/trigger`) require valid bearer tokens.
* **Thread-Safe Data Layer:** `ThreadingHTTPServer` endpoints use mutex locks (`threading.Lock`) preventing race conditions during concurrent lead capture.
* **Payload Size Ceiling:** POST requests are bounded to a maximum of 10MB to protect against memory exhaustion.
* **Compliance:** SARFAESI Act 2002 regulatory guidelines followed with physical vs symbolic possession classification.

---

## License

Proprietary — All rights reserved.
