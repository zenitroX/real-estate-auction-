# Goldfish Review & Resolution Report (Stage 9 Implementation Readiness)

**Target Document**: [PROJECT.md](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md)  
**Resolution Mode**: Elephant Context Remediation (`egm-resolve`)  
**Input Report**: [implementation_readiness_report.md](file:///c:/Users/rajkr/Documents/code-base/real%20estate/implementation_readiness_report.md)

---

## 1. Classification & Evaluation of Stage 9 Findings

| Finding ID | Title | Auditor Persona | Severity | Verdict | Resolution Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IR-1** | Schema Drift with `supabase_client.py` & Missing DDL | `egm-implementation-readiness` / `egm-codebase-details` | 🔴 Blocker | **PROPOSE FIX** | Align Section 3.1 & 9.2 with `supabase_client.py` field names (`reserve_price_inr`, `area_sqft`, `village_or_locality`, `auction_event_hash`, `asset_fingerprint`). Embed complete PostgreSQL DDL and RLS policies. |
| **IR-2** | Decoupling Playwright Breaks API Trigger & Admin UI | `egm-implementation-readiness` / `egm-codebase-details` | 🔴 Blocker | **PROPOSE FIX** | Specify migration of `POST /api/scrape/trigger` to dispatch GitHub Actions workflow via GitHub REST API (`workflow_dispatch`), preserving the admin trigger button safely. |
| **IR-3** | `DashboardView.jsx` Runtime Crash on Bidding Purge | `egm-codebase-details` | 🔴 Blocker | **PROPOSE FIX** | Mandate refactoring `DashboardView.jsx` to default `myBids = {}` and purge the active bids tab alongside `BiddingModal.jsx`. |
| **IR-4** | React 19 `<Suspense>` Crash on `React.lazy()` | `egm-codebase-details` | 🔴 Blocker | **PROPOSE FIX** | Mandate enclosing lazy-loaded `AdminLoginView` and `AdminView` inside `<React.Suspense fallback={<LoadingSpinner />}>`. |
| **IR-5** | Proxy IP Blindness in Contact Rate-Limiting | `egm-implementation-readiness` / `egm-codebase-details` | 🟡 Major | **PROPOSE FIX** | Extract client IP from `X-Forwarded-For` with fallback, guard with `threading.Lock()`, and permit 15 req/min burst for offline queue flushes. |
| **IR-6** | `possession_type` Dropped in `api.js` Normalization | `egm-codebase-details` | 🟡 Major | **PROPOSE FIX** | Explicitly mandate mapping `possessionType: item.possession_type` in `fetchLiveAuctions()` in `frontend/src/data/api.js`. |
| **IR-7** | Ephemeral Gemini Token Counter in GitHub Actions | `egm-implementation-readiness` / `egm-codebase-details` | 🟡 Major | **PROPOSE FIX** | Persist daily token usage in Supabase table `gemini_spend_tracker` across ephemeral virtual machines. |
| **IR-8** | Split-Pane PDF Preview Blocked by Bank CORS/Frame Headers | `egm-implementation-readiness` | 🟡 Major | **PROPOSE FIX** | Add authenticated streaming proxy endpoint `GET /api/admin/pdf-proxy?url=...` in `app.py`. |
| **IR-9** | Marketing Headers & Non-Imperative Copy | `egm-style` | 🟢 Nit | **PROPOSE FIX** | Calibrate headings to neutral technical terms and enforce imperative task operations document-wide. |

---

## 2. Execution Log

1. **Section 3.1 & Section 9.2 (Schema & DDL)**:
   - Synchronized column definitions with `backend/ingestion/database/supabase_client.py`.
   - Embedded complete PostgreSQL DDL including indexes and RLS read policies.
2. **Section 9.1 (Auth, Suspense & Rate Limiting)**:
   - Added `<React.Suspense>` boundary requirement for React 19 lazy admin chunks.
   - Specified `X-Forwarded-For` parsing and `threading.Lock()` for the contact rate limiter.
3. **Section 9.2 (Database Persistence & PDF Viewer)**:
   - Added `DashboardView.jsx` refactoring step to eliminate `Object.keys(myBids)` crash.
   - Specified `GET /api/admin/pdf-proxy` proxy endpoint for bank PDF circulars.
4. **Section 9.3 (Scraper Decoupling & Spend Controls)**:
   - Defined GitHub REST API `workflow_dispatch` trigger for `POST /api/scrape/trigger`.
   - Specified persistent Supabase token ledger `gemini_spend_tracker`.
5. **Section 9.4 (Monetization & Possession Badging)**:
   - Added normalization update in `frontend/src/data/api.js` for `possessionType`.
