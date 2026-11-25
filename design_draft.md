# SKANDX Customer-Facing Bank Auction Platform — Formal Design Document

*   **Author:** rajkrish63
*   **Status:** In Review (Revised)
*   **Date:** 2026-11-25
*   **Predecessor Context:** [concepts_brief.md](./concepts_brief.md)

--------------------------------------------------------------------------------

## 1. Overview

This document specifies the architecture, Stage 0 remediation, and MVP Phases 1–3 implementation plan for the customer-facing side of the SKANDX Tamil Nadu Bank Auction Intelligence Platform.

SKANDX aggregates SARFAESI bank auction notices (from `baanknet.com`, individual bank portals, and newspapers) and converts public property discovery into an assisted buyer-acquisition service under a proposed hybrid 5% success-commission model. The system preserves the existing stack: React 19 + Vite 6 JavaScript SPA (`frontend/`), Python REST server (`backend/app.py`), and Supabase PostgreSQL (`backend/migrations/`).

## 2. The Problem & Finalized Product Requirements

Currently, SKANDX's customer-facing experience has critical data-integrity and security defects alongside missing MVP capabilities:

1. **Public PII Exposure & Broken Live Data**: `GET /api/auctions` returns `select=*` (exposing `borrower_name`, `contact_phone`, `authorized_officer_name`, and `raw_extracted_json`), while `frontend/src/data/api.js` maps non-existent column names (`reserve_price`, `city`, `branch`) and mixes hardcoded `INITIAL_PROPERTIES` mock data with live rows.
2. **Broken Approval & Admin Persistence**: `evaluate_sanity()` in `backend/ingestion/database/supabase_client.py` auto-publishes ingested records, `persist_property_update()` drops all edited fields except `review_status` and `reserve_price_inr`, `PATCH /api/admin/leads` does not exist, and `frontend/src/App.jsx` auto-grants `skandx-test-token-bypass` on `admin.*` hostnames.
3. **Missing Customer MVP**: There is no customer authentication, no saved/compared/recently-viewed persistence, no separation between publication status and the 8 verification dimensions, no duplicate-safe lead capture, and no service agreement gate for the proposed 5% success-commission model.

### Goals

*   **Stage 0 (Mandatory Gate)**: Eliminate public PII exposure, fix Supabase-to-frontend field mappings, remove production mock-data mixing, enforce admin-only publication approval, repair admin property and lead persistence, remove hostname-based admin token bypasses, and replace hash routing (`#property/p1`) with clean path-based URLs.
*   **Phase 1 (Discovery)**: Deliver a responsive customer homepage, filtered/paginated auction discovery grid, path-based property detail pages, auction deadline intelligence, an 8-dimension progressive verification checklist, and explicit risk disclosures.
*   **Phase 2 (Customer Accounts)**: Integrate Supabase Auth (registration, login, logout, password recovery, profile) and RLS-protected saved properties, property comparison, and recently viewed history.
*   **Phase 3 (Conversion & 5% Agreement Gate)**: Deliver "Connect with Auction Advisor" with duplicate-lead prevention, explicit 5% service-agreement acceptance before substantive paid assistance, admin lead notifications, and basic advisor assignment.

### Non-Goals (Explicitly Deferred)

*   Migrating `frontend/` from JavaScript to TypeScript.
*   Migrating `frontend/` to Next.js / SSR or adding prerendering (evaluated post-MVP).
*   Full customer dashboard, automated 5% commission calculation/collection, payment gateways, or automated WhatsApp/SMS/email engines.
*   Rewriting the Playwright + Gemini OCR ingestion pipeline or replacing admin HMAC authentication.

## 3. Critical User Journeys (CUJs)

### CUJ 1: Public Auction Discovery & Risk Inspection (Phase 1)

*   **Given**: An unauthenticated visitor opens `skandx.com` or `/auctions`.
*   **When**: They search or filter by district, locality, property type, reserve price, auction deadline, bank, or possession status, and open `/properties/:slugId`.
*   **Then**: Only `publication_status = 'PUBLISHED'` properties appear, with zero borrower/officer PII, accurate INR pricing and deadlines, an 8-dimension verification checklist (Completed, Pending, Unavailable, Flagged), and plain-English risk warnings.

### CUJ 2: Save, Compare & Recently Viewed (Phase 2)

*   **Given**: A customer browsing `/auctions` or `/properties/:slugId`.
*   **When**: They click Save or Compare, authenticate via Supabase Auth, and open `/saved` or `/compare`.
*   **Then**: Saved, compared, and recently viewed records persist in Supabase under RLS (`auth.uid() = user_id`) and survive reloads without exposing other customers' data.

### CUJ 3: Connect with Auction Advisor & Proposed 5% Service Agreement (Phase 3)

*   **Given**: An authenticated customer on `/properties/:slugId` who wants assistance.
*   **When**: They click "Connect with Auction Advisor", choose an assistance category, review and accept the disclosed proposed 5% service-agreement terms (mandatory before substantive paid assistance), and submit.
*   **Then**: `backend/app.py` verifies their Supabase JWT, checks for active duplicate leads on `(user_id, property_id)`, records `service_agreements` and `customer_leads` (`status='Request received'`), notifies the admin leads desk, and returns confirmation.

--------------------------------------------------------------------------------

## 4. Existing Architecture & Codebase Assessment

| Layer | Current State | Assessment & Gap |
| :--- | :--- | :--- |
| **Frontend (`frontend/`)** | React 19 + Vite 6 JS SPA (`App.jsx`, `views/`, `components/`, `data/api.js`). `vercel.json` and `nginx.conf` already have SPA fallback rules. | Hash routing (`#property/p1`) hurts SEO; `api.js` reads wrong DB column names and merges `INITIAL_PROPERTIES`; `App.jsx` auto-sets `skandx-test-token-bypass`; `PropertiesView.jsx` has unwired `possessionFilter` and `frameworkFilter`. |
| **Backend (`backend/app.py`)** | Python 3.12 REST server with HMAC-SHA256 admin auth (`skandx-adm-...`), `get_raw_auctions()`, `persist_property_update()`, `save_lead()`, `load_leads()`. | `GET /api/auctions` leaks PII via `select=*`; `persist_property_update()` drops most fields; `PATCH /api/admin/leads` is missing; hardcoded fallback `ADMIN_SECRET` and `?token=` query auth exist; `load_leads()` mixes `leads.jsonl` and Supabase. |
| **Database (`backend/migrations/`)** | `001_create_auction_properties.sql`, `002_create_customer_leads.sql`, `003_create_admin_roles_and_audit.sql`. | `auction_properties` uses single `review_status` and `"Public Read Published"` allows `SELECT *` if queried via anon key; `customer_leads` has `"Public Insert Leads" WITH CHECK (true)`, uses colliding `#SK-XXXX` PK, and lacks `user_id`, `assigned_advisor_id`, and duplicate prevention. |
| **Ingestion (`backend/ingestion/`)** | Playwright + Gemini 2.5 Flash OCR pipeline writing to Supabase via `supabase_client.py`. | `evaluate_sanity()` auto-publishes (`ReviewStatus.PUBLISHED`) instead of queuing for admin approval. |

--------------------------------------------------------------------------------

## 5. Technical Plan (Architecture)

```text
+-------------------------------------------------------------------------+
|                    React 19 + Vite 6 JS SPA (frontend/)                 |
|  Path Router (react-router-dom) | @supabase/supabase-js (Customer Auth) |
|  Public: /, /auctions, /properties/:slugId | Auth: /saved, /compare     |
|  Admin Subdomain (admin.*): AdminLoginView + AdminView (HMAC Token)     |
+--------------------+---------------------------------+------------------+
                     | HTTPS REST                      | Supabase RLS (JWT)
                     v                                 v
+----------------------------------------+   +----------------------------+
|   Python Backend (backend/app.py)      |   |   Supabase PostgreSQL      |
| • GET /api/v1/auctions (safe columns)  |   | • auction_properties       |
| • GET /api/v1/auctions/:id             |   | • customer_leads           |
| • POST /api/v1/leads (JWT + agreement) |   | • service_agreements       |
| • PATCH /api/admin/properties (HMAC)   |   | • saved_properties (RLS)   |
| • PATCH /api/admin/leads (HMAC)        |   | • compared_properties (RLS)|
+--------------------+-------------------+   | • recently_viewed (RLS)    |
                     | Service Role Key      | • property_audit_logs      |
                     +---------------------->+----------------------------+
```

### 5.1 Public Data Security & Explicit Response Schema

*   **Approved Public Columns (`PUBLIC_AUCTION_COLUMNS`)**: `id`, `slug`, `property_title`, `bank_name`, `branch_name`, `asset_category`, `possession_type`, `survey_numbers`, `patta_or_door_no`, `village_or_locality`, `taluk`, `district`, `state`, `pincode`, `area_description`, `area_sqft`, `boundaries`, `reserve_price_inr`, `previous_reserve_price_inr`, `price_drop_percentage`, `emd_amount_inr`, `bid_increment_inr`, `emd_last_date`, `inspection_date_info`, `auction_date`, `source_portal`, `source_pdf_url`, `bidding_portal_url`, `publication_status`, `verification_dimensions`, `risk_disclosures`, `last_source_confirmed_at`, `created_at`.
*   **Explicitly Excluded from Public Endpoints**: `borrower_name`, `contact_phone`, `authorized_officer_name`, `raw_extracted_json`, `review_notes`, `asset_fingerprint`, `auction_event_hash`.
*   **Database-Level Defense**: Revoke direct `anon` `SELECT` on `auction_properties` (or restrict via column-safe view) so even direct Supabase anon-key queries cannot read borrower PII; all public reads flow through `backend/app.py`'s `PUBLIC_AUCTION_COLUMNS` serializer.

### 5.2 Publication vs. 8-Dimension Verification

*   **Independent States**:
    *   `publication_status`: `DRAFT`, `PENDING_ADMIN_APPROVAL`, `PUBLISHED`, `UNPUBLISHED`, `EXPIRED`, `CANCELLED`.
    *   `verification_dimensions` (`JSONB`): 8 independent keys (`source_checked`, `auction_details_checked`, `documents_reviewed`, `ec_reviewed`, `revenue_records_reviewed`, `physical_inspection_completed`, `possession_assessed`, `legal_review_completed`), each storing `{ status: "PENDING" | "COMPLETED" | "UNAVAILABLE" | "FLAGGED", reviewer, reviewed_at, evidence_ref, notes, review_period }`.
*   **Ingestion Guard**: `evaluate_sanity()` in `supabase_client.py` defaults new records to `PENDING_ADMIN_APPROVAL` (synced with `review_status = 'NEEDS_MANUAL_REVIEW'`).
*   **Minimum Admin Publication Gate**: Before an admin can set `publication_status = 'PUBLISHED'`, `backend/app.py` enforces:
    1. `source_portal` or `source_pdf_url` is present and `source_checked.status == 'COMPLETED'`.
    2. Core auction fields (`bank_name`, `district`, `village_or_locality`, `reserve_price_inr`, `emd_amount_inr`) are populated and `auction_details_checked.status == 'COMPLETED'`.
    3. `auction_date` is set (or an explicit `AUCTION_RECONFIRMATION_REQUIRED` risk flag is attached).
    4. Material known risks are recorded in `risk_disclosures`.
*   **Honest Display**: Property pages show each of the 8 dimensions with its exact status and timestamp, and prominently display pending/flagged risks. No listing is ever labeled "legally verified" or "guaranteed safe."

### 5.3 Customer Auth, Leads & Ownership Isolation

*   **Customer Auth (`@supabase/supabase-js`)**: Uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (never `service_role`). Supports email/password registration, login, logout, session persistence, and password recovery.
*   **Admin Auth Preservation**: Admin HMAC-SHA256 tokens (`skandx-adm-{ts}-{sig}`) remain strictly separate for `admin.*` routes. `backend/app.py` fails closed if `ADMIN_JWT_SECRET` is unset in production, removes `?token=` query auth, and removes `skandx-test-token-bypass` from `App.jsx`.
*   **Lead Deduplication & Ownership**:
    *   `POST /api/v1/leads` requires a valid Supabase customer JWT (verified via `{SUPABASE_URL}/auth/v1/user`), derives `user_id` exclusively from the verified JWT (never trusting frontend-supplied `user_id`), and checks for an existing active lead on `(user_id, property_id)` where `status <> 'CLOSED'`.
    *   `GET /api/v1/me/leads` filters strictly by `user_id = verified_jwt.sub` and excludes internal admin notes.
    *   `PATCH /api/admin/leads` requires valid Admin HMAC auth and persists `status` transitions and `assigned_advisor_id`.

### 5.4 Proposed 5% Service Agreement & Commission Model

*   **Commercial Status**: 5% is strictly a **proposed commercial rate**, not a finalized legal obligation or automated charge. No payment gateway or automated commission collection is built in MVP.
*   **Mandatory Acceptance Gate**:
    *   *Free / No Agreement Required*: Browsing listings, viewing verification summaries/risks, saving, comparing, and submitting a general inquiry (`General auction guidance`).
    *   *Agreement Mandatory*: Requesting substantive paid assistance (`Physical property inspection`, `Document review coordination`, `Legal consultation coordination`, `Auction participation guidance`, `Complete buyer assistance`).
*   **Proposed Terms Recorded in `service_agreements`**:
    *   `commission_rate_pct`: `5.00` (proposed).
    *   `calculation_basis`: Proposed percentage of final successful bid/hammer price (subject to final written agreement).
    *   `commission_trigger`: Issuance of Bank Sale Certificate / confirmed acquisition outcome through platform assistance.
    *   `payment_deadline`: Proposed 7 business days post-Sale Certificate issuance (manually tracked by admin).
    *   `cancellation_and_dispute`: Written notice prior to auction participation; disputes governed by Indian Contract Act / Chennai jurisdiction (placeholder pending legal sign-off).
    *   `tax_note`: Exclusive of applicable GST/taxes (requires Indian tax validation).
*   **Legal & Tax Validation Flags**: All commercial terms—calculation basis, GST applicability, RERA/brokerage licensing implications in Tamil Nadu, enforceability of clickwrap acceptance under the IT Act 2000, and non-exclusivity/bypass clauses—are flagged for independent Indian legal and tax review prior to commercial launch.

--------------------------------------------------------------------------------

## 6. Database Schema Changes & Migration Strategy

Migrations execute strictly in order (`004` -> `005` -> `006`). All changes are additive and preserve existing `auction_properties`, `customer_leads`, `admin_users`, and `property_audit_logs` rows.

*   **`004_publication_and_verification.sql`**:
    *   `ALTER TABLE auction_properties ADD COLUMN IF NOT EXISTS publication_status TEXT NOT NULL DEFAULT 'PENDING_ADMIN_APPROVAL', ADD COLUMN IF NOT EXISTS verification_dimensions JSONB NOT NULL DEFAULT '{}'::JSONB, ADD COLUMN IF NOT EXISTS risk_disclosures JSONB NOT NULL DEFAULT '[]'::JSONB, ADD COLUMN IF NOT EXISTS slug TEXT, ADD COLUMN IF NOT EXISTS last_source_confirmed_at TIMESTAMPTZ;`
    *   Backfill `publication_status` from `review_status` (`PUBLISHED` -> `PUBLISHED`, `REJECTED` -> `UNPUBLISHED`, else `PENDING_ADMIN_APPROVAL`).
    *   Add indexes: `idx_auction_pub_date ON auction_properties (publication_status, auction_date)`, `idx_auction_district ON auction_properties (district)`, `idx_auction_category ON auction_properties (asset_category)`, `idx_auction_price ON auction_properties (reserve_price_inr)`.
    *   Revoke direct `anon` `SELECT` on `auction_properties` (or replace `"Public Read Published"` with `service_role`-only table access + safe `public_auction_listings` view) so PII columns cannot be queried via the anon key.
*   **`005_customer_accounts_and_lists.sql`**:
    *   Create `customer_profiles`, `saved_properties`, `compared_properties`, `recently_viewed` with `UUID` foreign keys to `auth.users(id) ON DELETE CASCADE` and `TEXT` foreign keys to `auction_properties(id) ON DELETE CASCADE`.
    *   Unique constraints on `(user_id, property_id)` for `saved_properties`, `compared_properties`, and `recently_viewed`.
    *   Enable RLS on all 4 tables: `FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)`.
*   **`006_leads_upgrade_and_service_agreements.sql`**:
    *   `ALTER TABLE customer_leads`: add `lead_code TEXT UNIQUE`, `user_id UUID`, `preferred_contact TEXT`, `consent_to_contact BOOLEAN NOT NULL DEFAULT false`, `consent_at TIMESTAMPTZ`, `assigned_advisor_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
    *   Change `id` default from colliding `#SK-XXXX` to `gen_random_uuid()::TEXT` (existing `#SK-XXXX` rows remain untouched).
    *   Add partial unique indexes: `idx_leads_dedup_user ON customer_leads (user_id, property_id) WHERE user_id IS NOT NULL AND status <> 'CLOSED'`.
    *   Drop `"Public Insert Leads"` policy on `customer_leads`; add `"Customer Read Own Leads"` (`FOR SELECT USING (auth.uid() = user_id)`) and keep `service_role` full access so all writes go through `backend/app.py`.
    *   Create `service_agreements` (`id UUID PK DEFAULT gen_random_uuid()`, `user_id UUID NOT NULL`, `property_id TEXT NOT NULL REFERENCES auction_properties(id)`, `lead_id TEXT REFERENCES customer_leads(id)`, `commission_rate_pct NUMERIC(4,2) NOT NULL DEFAULT 5.00`, `calculation_basis TEXT NOT NULL`, `agreement_version TEXT NOT NULL`, `accepted_name TEXT NOT NULL`, `accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `ip_address TEXT`, `user_agent TEXT`, `acquisition_outcome TEXT`, `payment_status TEXT DEFAULT 'PENDING'`, `legal_review_status TEXT DEFAULT 'PENDING_VALIDATION'`). Enable RLS (`SELECT` own rows for `auth.uid() = user_id`; writes `service_role` only).

### Migration Ordering & Rollback / Recovery

1. **Forward Order**: Take Supabase snapshot -> apply `004` -> deploy `backend/app.py` (with `review_status` dual-sync) + `supabase_client.py` -> apply `005` -> apply `006` -> deploy `frontend/`.
2. **Rollback**: Because `004`–`006` are additive (`ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`), rolling back application code leaves existing `review_status` and `customer_leads` intact. If schema rollback is required, restore from the pre-migration snapshot or drop only the newly added tables (`service_agreements`, `recently_viewed`, `compared_properties`, `saved_properties`, `customer_profiles`) and new columns after reverting code.

--------------------------------------------------------------------------------

## 7. Frontend Architecture, Routing & SEO

*   **Language**: JavaScript (`.js`/`.jsx`) with JSDoc; no TypeScript migration.
*   **Routing**: `react-router-dom` `BrowserRouter` (`/`, `/auctions`, `/properties/:slugId`, `/saved`, `/compare`, `/about`, `/services`, `*` 404). `vercel.json` and `nginx.conf` already rewrite non-API routes to `/index.html`.
*   **SEO**: Dynamic `<title>`, `<meta name="description">`, `<link rel="canonical">`, OpenGraph tags, `JSON-LD` (`RealEstateListing` / `Offer` using factual fields only), `public/robots.txt`, and `/sitemap.xml` generated from `PUBLISHED` listings.
*   **SEO Limitation**: Client-rendered per-property OpenGraph tags do not guarantee rich link previews on crawlers that do not execute JavaScript (WhatsApp, LinkedIn). Prerendering/SSR is deferred to post-MVP evaluation.

--------------------------------------------------------------------------------

## 8. Alternatives Considered

*   **TypeScript + Next.js SSR Now**: Rejected by author to avoid delaying Stage 0 security fixes and MVP delivery.
*   **Custom Customer Auth in `backend/app.py`**: Rejected by author in favor of Supabase Auth + RLS to avoid duplicating session/recovery infrastructure.
*   **Block Publication Until All 8 Checks Pass**: Rejected by author due to 15–30 day SARFAESI timelines; admin-approved publication with transparent pending/risk disclosure is used instead.

--------------------------------------------------------------------------------

## 9. Unresolved Architectural Decisions

1. **Legal & Tax Sign-Off on `service_agreements` Text**: Exact wording for calculation basis, GST, and Tamil Nadu brokerage compliance is pending legal counsel.
2. **Advisor Notification Transport**: MVP notifies the Admin Leads Desk in-app; whether Phase 3 also fires an email/WhatsApp webhook depends on provisioned SMTP/WhatsApp credentials.
3. **Production Environment Provisioning**: `ADMIN_JWT_SECRET`, `ALLOWED_ORIGINS`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY` must be configured in deployment environments before Stage 0/Phase 2 go-live.

## 10. Potential Breaking Changes

1. **Removing `INITIAL_PROPERTIES` Mixing**: Environments without a running backend or Supabase connection will now show an explicit empty/error/retry state instead of mock properties (unless `VITE_ENABLE_DEMO_DATA=true` in dev).
2. **Removing `skandx-test-token-bypass` & `?token=` Auth**: Local admin testing must use `POST /api/admin/login` with valid credentials; automated tests must set `PYTEST_CURRENT_TEST` or explicit test config.
3. **Dropping `"Public Insert Leads"` RLS Policy**: Any client attempting direct Supabase `POST` to `customer_leads` will be rejected; all lead creation must go through `POST /api/v1/leads`.
4. **Replacing Hash URLs (`#property/...`)**: Old bookmarked hash URLs will need a one-time redirect handler in `App.jsx` if backward compatibility for shared links is desired.

## 11. Security Acceptance Checklist

- [ ] `GET /api/auctions` and `GET /api/v1/auctions` return zero `borrower_name`, `contact_phone`, `authorized_officer_name`, `raw_extracted_json`, or `review_notes`.
- [ ] Direct Supabase anon-key query cannot `SELECT` PII columns from `auction_properties` or `INSERT` into `customer_leads`.
- [ ] `evaluate_sanity()` never sets `PUBLISHED`; only HMAC-authenticated admins can publish.
- [ ] `ADMIN_JWT_SECRET` has no hardcoded fallback in production; `skandx-test-token-bypass` is removed from `App.jsx`.
- [ ] `saved_properties`, `compared_properties`, `recently_viewed`, `customer_leads`, and `service_agreements` enforce `auth.uid() = user_id` isolation (verified by cross-user negative tests).
- [ ] `POST /api/v1/leads` derives `user_id` from verified JWT, rejects duplicate active leads, and rejects requests for paid assistance without accepted `service_agreements`.
- [ ] `frontend/dist/` contains zero occurrences of `SERVICE_ROLE` or `ADMIN_JWT_SECRET`.

## 12. Final Implementation Sequence & Acceptance Criteria

| Stage | Dependencies | Target Files | Measurable Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Stage 0: Critical Fixes** | None (Mandatory Gate) | `backend/app.py`, `backend/ingestion/database/supabase_client.py`, `frontend/src/data/api.js`, `frontend/src/App.jsx`, `frontend/src/views/AdminView.jsx`, `frontend/package.json` | `pytest backend/test_app_security.py` passes (PII excluded, 401 on unauth admin, `PATCH /api/admin/leads` & full property `PATCH` persist, `evaluate_sanity()` != `PUBLISHED`); `npm run build` succeeds; path routes (`/auctions`, `/properties/:id`, 404) work on refresh; zero mock mixing or token bypass. |
| **Phase 1: Discovery & Verification** | Stage 0 passed; `004` migrated | `backend/migrations/004_publication_and_verification.sql`, `backend/app.py`, `frontend/src/views/{HomeView,PropertiesView,PropertyDetailsView}.jsx`, `PropertyCard.jsx`, `public/robots.txt` | Filters (`district`, `type`, `bank`, `possession`, `price`, `deadline`), pagination, and `EXPIRED` handling return live DB rows; property detail renders 8 verification dimensions + risk disclosures; admin publish blocked unless minimum checks pass. |
| **Phase 2: Customer Auth & Lists** | Phase 1; `005` migrated; Supabase Auth env vars | `backend/migrations/005_customer_accounts_and_lists.sql`, `frontend/package.json`, `frontend/src/lib/supabaseClient.js`, `AuthModal.jsx`, `DashboardView.jsx`, `CompareView.jsx` | Register/login/logout/reset work; saved/compare/recently-viewed persist across reloads; RLS blocks cross-user reads/writes. |
| **Phase 3: Connect & 5% Agreement** | Phase 2; `006` migrated | `backend/migrations/006_leads_upgrade_and_service_agreements.sql`, `backend/app.py`, `frontend/src/components/Modals/ContactModal.jsx`, `AdminView.jsx` | Duplicate active lead returns 409; paid assistance requires accepted `service_agreements`; admin assigns advisor via `PATCH /api/admin/leads`; customer sees `Request received` status without internal admin notes. |

--------------------------------------------------------------------------------

*Drafted with EGM*
