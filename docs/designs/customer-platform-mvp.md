# SKANDX Customer-Facing Bank Auction Platform — Formal Design Document

*   **Author:** rajkrish63
*   **Status:** Proposed
*   **Date:** 2026-11-25
*   **Predecessor Context:** [concepts_brief.md](../../concepts_brief.md)

--------------------------------------------------------------------------------

## 1. Overview

This document specifies the architecture, Stage 0 remediation, and MVP Phases 1–3 implementation plan for the customer-facing side of the SKANDX Tamil Nadu Bank Auction Intelligence Platform.

SKANDX aggregates bank auction notices issued under SARFAESI (Securitisation and Reconstruction of Financial Assets and Enforcement of Security Interest Act) from `baanknet.com`, individual bank portals, and newspapers, and converts public property discovery into an assisted buyer-acquisition service under a proposed hybrid 5% success-commission model. The system preserves the existing stack: React 19 + Vite 6 JavaScript SPA (`frontend/`), Python REST server (`backend/app.py`), and Supabase PostgreSQL (`backend/migrations/`).

## 2. The Problem & Finalized Product Requirements

Currently, SKANDX's customer-facing experience has critical data-integrity and security defects alongside missing MVP capabilities:

1. **Public PII Exposure & Broken Live Data**: `GET /api/auctions` returns `select=*` (exposing `borrower_name`, `contact_phone`, `authorized_officer_name`, and `raw_extracted_json`), while `frontend/src/data/api.js` maps non-existent column names (`reserve_price`, `city`, `branch`) and mixes hardcoded `INITIAL_PROPERTIES` mock data with live rows.
2. **Broken Approval & Admin Persistence**: `evaluate_sanity()` in `backend/ingestion/database/supabase_client.py` auto-publishes ingested records, `persist_property_update()` drops all edited fields except `review_status` and `reserve_price_inr`, `PATCH /api/admin/leads` does not exist, `load_leads()` mixes `leads.jsonl` with Supabase, and `frontend/src/App.jsx` auto-grants `skandx-test-token-bypass` on `admin.*` hostnames.
3. **Missing Customer MVP**: There is no customer authentication, no saved/recently-viewed persistence, no separation between publication status and the 8 verification dimensions, no duplicate-safe lead capture, and no fee-disclosure/service-agreement gate for the proposed 5% success-commission model.

### Goals

*   **Stage 0 (Mandatory Gate)**: Eliminate public PII exposure, fix Supabase-to-frontend field mappings, remove production mock-data mixing and `leads.jsonl` dual-store fallback, enforce admin-only publication approval, repair admin property and lead persistence (`do_PATCH`), remove hostname-based admin token bypasses, and replace hash routing (`#property/p1`) with clean path-based URLs.
*   **Phase 1 (Discovery)**: Deliver a responsive customer homepage, server-filtered/paginated auction discovery grid, path-based property detail pages, auction deadline intelligence, an 8-dimension progressive verification checklist, and explicit risk disclosures.
*   **Phase 2 (Customer Accounts)**: Integrate Supabase Auth (registration, login, logout, password recovery, profile) and RLS-protected saved properties and recently viewed history, plus URL-based property comparison (`/compare?ids=...`).
*   **Phase 3 (Conversion & 5% Agreement Gate)**: Deliver "Connect with Auction Advisor" with duplicate-lead prevention, explicit 5% service-agreement acceptance before substantive paid assistance, admin lead notifications (surfaced in `AdminView.jsx` Leads Desk), and basic advisor assignment.

### Non-Goals (Explicitly Deferred)

*   Migrating `frontend/` from JavaScript to TypeScript.
*   Migrating `frontend/` to Next.js / SSR or adding prerendering (evaluated post-MVP).
*   Full customer dashboard (KYC/Documents and Alerts tabs in `DashboardView.jsx` are deferred), automated 5% commission calculation/collection, payment gateways, or automated WhatsApp/SMS/email engines.
*   Rewriting the Playwright + Gemini OCR ingestion pipeline or replacing admin HMAC authentication.

## 3. Critical User Journeys (CUJs)

### CUJ 1: Public Auction Discovery & Risk Inspection (Phase 1)

*   **Given**: An unauthenticated visitor opens `skandx.com` or `/auctions`.
*   **When**: They search or filter by district, locality, property type, reserve price, auction deadline, bank, or possession status, and open `/properties/:idOrSlug`.
*   **Then**: Only `publication_status = 'PUBLISHED'` and non-expired (`auction_date >= NOW()`) properties appear by default (with `?include_expired=true` showing an `EXPIRED` label), with zero borrower/officer PII, accurate INR pricing and deadlines, an 8-dimension verification checklist (Completed, Pending, Unavailable, Flagged), and plain-English risk warnings.

### CUJ 2: Save, Compare & Recently Viewed (Phase 2)

*   **Given**: A customer browsing `/auctions` or `/properties/:idOrSlug`.
*   **When**: They click Save (persisted via Supabase Auth + RLS) or Compare (via `/compare?ids=...` URL state), and open `/saved` or `/compare`.
*   **Then**: Saved and recently viewed IDs persist in Supabase under RLS (`auth.uid() = user_id`), property details are hydrated through `backend/app.py` (`GET /api/v1/auctions?ids=...`), and other customers' data is never exposed.

### CUJ 3: Connect with Auction Advisor & Proposed 5% Service Agreement (Phase 3)

*   **Given**: An authenticated customer on `/properties/:idOrSlug` who wants assistance.
*   **When**: They click "Connect with Auction Advisor", choose an assistance category, review and accept the disclosed proposed 5% service-agreement terms (mandatory before substantive paid assistance), and submit.
*   **Then**: `backend/app.py` verifies their Supabase JWT, executes a single PostgreSQL RPC (`create_lead_with_agreement`) that prevents active duplicate leads on `(user_id, property_id)` and records `service_agreements` + `customer_leads` (`status = 'REQUEST_RECEIVED'`), surfaces the lead in `AdminView.jsx`, and returns confirmation.

--------------------------------------------------------------------------------

## 4. Existing Architecture & Codebase Assessment

| Layer | Current State | Assessment & Gap |
| :--- | :--- | :--- |
| **Frontend (`frontend/`)** | React 19 + Vite 6 JS SPA (`App.jsx`, `views/`, `components/`, `data/api.js`). `vercel.json` and `nginx.conf` already have SPA fallback rules. | Hash routing (`#property/p1`) hurts SEO; `api.js` reads wrong DB column names and merges `INITIAL_PROPERTIES`; `App.jsx` auto-sets `skandx-test-token-bypass`; `PropertiesView.jsx` has unwired `possessionFilter` and dead `frameworkFilter` UI. |
| **Backend (`backend/app.py`)** | Python 3.12 `BaseHTTPRequestHandler` (`ApiRequestHandler`) with HMAC-SHA256 admin auth (`skandx-adm-{ts}-{sig}`), `POST /api/admin/properties/verify`, `POST /api/contact`, `get_raw_auctions()`, `persist_property_update()`, `save_lead()`, `load_leads()`. | `GET /api/auctions` leaks PII via `select=*`; no `do_PATCH` handler; `persist_property_update()` drops most fields; `PATCH /api/admin/leads` is missing; hardcoded fallback `ADMIN_SECRET` and `?token=` query auth exist; `load_leads()` mixes `leads.jsonl` and Supabase. |
| **Database (`backend/migrations/`)** | `001_create_auction_properties.sql`, `002_create_customer_leads.sql`, `003_create_admin_roles_and_audit.sql`. | `auction_properties` uses `review_status` and `"Public Read Published"` allows `SELECT *` for both `anon` and `authenticated`; `customer_leads` has `"Public Insert Leads" WITH CHECK (true)`, uses colliding `#SK-XXXX` PK, and lacks `user_id`, `assigned_advisor_id`, and duplicate prevention. |
| **Ingestion (`backend/ingestion/`)** | Playwright + Gemini 2.5 Flash OCR pipeline writing to Supabase via `supabase_client.py` and `ReviewStatus` in `auction_schema.py`. | `evaluate_sanity()` auto-publishes (`ReviewStatus.PUBLISHED`) instead of returning `ReviewStatus.NEEDS_MANUAL_REVIEW`. |

--------------------------------------------------------------------------------

## 5. Technical Plan (Architecture)

```text
+-------------------------------------------------------------------------+
|                    React 19 + Vite 6 JS SPA (frontend/)                 |
|  Path Router (react-router-dom) | @supabase/supabase-js (Customer Auth) |
|  Public: /, /auctions, /properties/:idOrSlug, /compare | Auth: /saved   |
|  Admin Subdomain (admin.*): AdminLoginView + AdminView (HMAC Token)     |
+--------------------+---------------------------------+------------------+
                     | HTTPS REST                      | Supabase RLS (JWT)
                     v                                 v
+----------------------------------------+   +----------------------------+
|   Python Backend (backend/app.py)      |   |   Supabase PostgreSQL      |
| • GET /api/v1/auctions (+ /api/auctions)|  | • auction_properties       |
| • GET /api/v1/auctions/:idOrSlug       |   | • customer_leads           |
| • GET /api/v1/districts, /sitemap.xml  |   | • service_agreements       |
| • POST /api/v1/leads (JWT + RPC)       |   | • customer_profiles (RLS)  |
| • GET /api/v1/me/leads (JWT, no notes) |   | • saved_properties (RLS)   |
| • POST /api/admin/login                |   | • recently_viewed (RLS)    |
| • GET /api/admin/advisors (HMAC)       |   | • property_audit_logs      |
| • PATCH /api/admin/properties (HMAC)   |   +----------------------------+
| • PATCH /api/admin/leads (HMAC)        |
+--------------------+-------------------+
                     | Service Role Key
                     +---------------------------------> Supabase
```

### 5.1 Public Data Security & Explicit Response Schema

*   **Approved Public Columns (`PUBLIC_AUCTION_COLUMNS`)**: `id`, `slug`, `property_title`, `bank_name`, `branch_name`, `asset_category`, `possession_type`, `survey_numbers`, `patta_or_door_no`, `village_or_locality`, `taluk`, `district`, `state`, `pincode`, `area_description`, `area_sqft`, `boundaries`, `reserve_price_inr`, `previous_reserve_price_inr`, `price_drop_percentage`, `emd_amount_inr` (Earnest Money Deposit), `bid_increment_inr`, `emd_last_date`, `inspection_date_info`, `auction_date`, `source_portal`, `source_pdf_url` (public bank/newspaper notice URLs only; internal unredacted PDFs excluded), `bidding_portal_url`, `publication_status`, `verification_dimensions` (projected to public-safe fields only), `risk_disclosures`, `last_source_confirmed_at`, `created_at`.
*   **Explicitly Excluded from Public Endpoints**: `borrower_name`, `contact_phone`, `authorized_officer_name`, `raw_extracted_json`, `review_notes`, `asset_fingerprint`, `auction_event_hash`.
*   **Verification Projection Rule**: In `backend/app.py`, each entry in `verification_dimensions` is projected to `{ status, reviewed_at, review_period }` only. `reviewer`, `evidence_ref`, and internal `notes` are stripped from all public responses.
*   **Single Public Read Path (Database-Level Defense)**: `004` unconditionally runs `DROP POLICY IF EXISTS "Public Read Published" ON auction_properties;` and `REVOKE SELECT ON auction_properties FROM anon, authenticated;`. Only `service_role` reads `auction_properties`; all public reads and saved/recent property hydration flow through `backend/app.py` (`GET /api/v1/auctions` and `GET /api/auctions` as a safe-projected alias).
*   **Public Query & Pagination Contract (`GET /api/v1/auctions`)**: Supports `q`, `district`, `type`, `bank`, `possession`, `min_price`, `max_price`, `deadline` (`7d` | `14d` | `30d`), `include_expired` (`false` default), `ids` (comma-separated for saved/compare hydration), `sort` (`deadline_asc` | `newest` | `price_asc` | `price_desc`), `page` (`1` default), `limit` (`20` default, max `50`). Returns `{ status: "success", data: [...], pagination: { page, limit, total, total_pages } }`.

### 5.2 Publication vs. 8-Dimension Verification

*   **Stage 0 -> Phase 1 Status Transition**: In Stage 0, `evaluate_sanity()` in `supabase_client.py` returns `ReviewStatus.NEEDS_MANUAL_REVIEW` (never `PUBLISHED`), and `AdminView.jsx` / `App.jsx` treat `NEEDS_MANUAL_REVIEW` and `PENDING_REVIEW` uniformly. In Phase 1, `004` adds `publication_status` (`DRAFT`, `PENDING_ADMIN_APPROVAL`, `PUBLISHED`, `UNPUBLISHED`, `EXPIRED`, `CANCELLED`), backfills from `review_status`, and makes `publication_status` the sole canonical status across `backend/app.py`, `supabase_client.py`, and `frontend/`.
*   **8 Verification Dimensions (`verification_dimensions` `JSONB`)**: `source_checked`, `auction_details_checked`, `documents_reviewed`, `ec_reviewed` (Encumbrance Certificate check for registered mortgages/claims), `revenue_records_reviewed` (Patta/Chitta/FMB land ownership records), `physical_inspection_completed`, `possession_assessed`, `legal_review_completed`. Each stores `{ status: "PENDING" | "COMPLETED" | "UNAVAILABLE" | "FLAGGED", reviewer, reviewed_at, evidence_ref, notes, review_period }` (where `review_period` is a string such as `"12-year EC"` or `"2014-2026"`).
*   **Ingestion Slug & Upsert Guard**: `supabase_client.py` generates `slug` on new inserts and uses `ON CONFLICT (auction_event_hash) DO UPDATE` preserving existing `publication_status`, `verification_dimensions`, and `risk_disclosures` so admin decisions are never overwritten.
*   **Minimum Admin Publication Gate**: Before an admin can set `publication_status = 'PUBLISHED'`, `backend/app.py` enforces:
    1. `source_portal` or `source_pdf_url` is present and `source_checked.status == 'COMPLETED'`.
    2. Core auction fields (`bank_name`, `district`, `village_or_locality`, `reserve_price_inr`, `emd_amount_inr`) are populated and `auction_details_checked.status == 'COMPLETED'`.
    3. `auction_date` is in the future (or an explicit `AUCTION_RECONFIRMATION_REQUIRED` risk flag is attached).
    4. Material known risks are recorded in `risk_disclosures`.
*   **Admin Property Update Allowlist (`PATCH /api/admin/properties`)**: `ApiRequestHandler` adds `do_PATCH` (keeping `POST /api/admin/properties/verify` as a Stage 0 alias). `persist_property_update()` accepts `id` in the JSON body and restricts updates to `ADMIN_EDITABLE_PROPERTY_COLUMNS`: `property_title`, `bank_name`, `branch_name`, `asset_category`, `possession_type`, `survey_numbers`, `patta_or_door_no`, `village_or_locality`, `taluk`, `district`, `state`, `pincode`, `area_description`, `area_sqft`, `boundaries`, `reserve_price_inr`, `previous_reserve_price_inr`, `price_drop_percentage`, `emd_amount_inr`, `bid_increment_inr`, `emd_last_date`, `inspection_date_info`, `auction_date`, `source_portal`, `source_pdf_url`, `bidding_portal_url`, `review_status` (Stage 0), `publication_status`, `verification_dimensions`, `risk_disclosures` (Phase 1+), logging diffs to `property_audit_logs`.

### 5.3 Customer Auth, Leads & Ownership Isolation

*   **Customer Auth (`@supabase/supabase-js`)**: Uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (never `service_role`). Supports email/password registration, login, logout, session persistence, and password recovery.
*   **Admin Auth Preservation**: Admin HMAC-SHA256 tokens (`skandx-adm-{ts}-{sig}`) remain strictly separate for `admin.*` routes with an 8h TTL (`28800`s). `backend/app.py` fails closed at request/login/verify time (not module import time, so `pytest` collection works cleanly with fixture-injected `ADMIN_JWT_SECRET`) whenever `ADMIN_JWT_SECRET` is unset, removes `?token=` query auth, and removes `skandx-test-token-bypass` from `App.jsx`.
*   **Lead Deduplication, Ownership & Admin Persistence**:
    *   In Stage 0, `backend/app.py` removes `leads.jsonl` dual-store reads/writes and adds `PATCH /api/admin/leads` (ID in body) to persist `status` (`NEW` | `IN_REVIEW` | `SCHEDULED` | `CLOSED`) and `notes` in Supabase `customer_leads`.
    *   In Phase 3, unauthenticated `POST /api/contact` is retired; `POST /api/v1/leads` requires a valid Supabase customer JWT (verified via `{SUPABASE_URL}/auth/v1/user`), derives `user_id` exclusively from the verified JWT, validates `inquiry_type` against the server allowlist, and calls PostgreSQL RPC `create_lead_with_agreement` (mapping `23505` unique violation on `(user_id, property_id)` where `status <> 'CLOSED'` to HTTP `409 Conflict`).
    *   `GET /api/v1/me/leads` filters strictly by `user_id = verified_jwt.sub` and excludes internal `notes`. Direct `SELECT` on `customer_leads` is revoked from `anon` and `authenticated`.
    *   In Phase 3, `PATCH /api/admin/leads` persists `status` (`REQUEST_RECEIVED` | `CONTACTED` | `IN_PROGRESS` | `CLOSED`), `notes`, and `assigned_advisor_id`, and `GET /api/admin/advisors` returns active `admin_users` (`is_active = true`).

### 5.4 Proposed 5% Service Agreement & Commission Model

*   **Commercial Status**: 5% is strictly a **proposed commercial rate**, not a finalized legal obligation or automated charge. No payment gateway or automated commission collection is built in MVP.
*   **UI-to-Enum `inquiry_type` Mapping & Mandatory Gate**:
    *   *Free / No Agreement Required*: `GENERAL_GUIDANCE` ("General Auction Guidance").
    *   *Agreement Mandatory*: `PHYSICAL_INSPECTION` ("Site Inspection"), `DOCUMENT_REVIEW` ("Document Review"), `LEGAL_COORDINATION` ("Legal Coordination"), `AUCTION_GUIDANCE` ("Auction Guidance"), `COMPLETE_ASSISTANCE` ("Complete Buyer Assistance").
*   **Server-Controlled Terms**: `backend/app.py` ignores client-supplied rate/terms and passes `commission_rate_pct = 5.00`, `AGREEMENT_VERSION = "v1.0-proposed"`, and `AGREEMENT_CALCULATION_BASIS = "5% of final successful auction hammer price (proposed; subject to formal written mandate)"` into `create_lead_with_agreement`.
*   **Legal & Tax Validation Flags**: Calculation basis, 7-business-day post-Sale-Certificate trigger, GST applicability, RERA (Real Estate Regulatory Authority) / Tamil Nadu brokerage rules, clickwrap enforceability under the IT Act 2000 (Information Technology Act, 2000), and cancellation/dispute clauses are flagged for independent Indian legal and tax review **as a mandatory Phase 3 production go-live gate**.

--------------------------------------------------------------------------------

## 6. Database Schema Changes & Migration Strategy

Migrations execute strictly in order (`004` -> `005` -> `006`) **before** deploying code that depends on each migration's columns/tables.

*   **`004_publication_and_verification.sql`** (Phase 1):
    *   `ALTER TABLE auction_properties ADD COLUMN IF NOT EXISTS publication_status TEXT NOT NULL DEFAULT 'PENDING_ADMIN_APPROVAL', ADD COLUMN IF NOT EXISTS verification_dimensions JSONB NOT NULL DEFAULT '{}'::JSONB, ADD COLUMN IF NOT EXISTS risk_disclosures JSONB NOT NULL DEFAULT '[]'::JSONB, ADD COLUMN IF NOT EXISTS slug TEXT, ADD COLUMN IF NOT EXISTS last_source_confirmed_at TIMESTAMPTZ;`
    *   Backfill `publication_status` from `review_status` (`PUBLISHED` -> `PUBLISHED`, `REJECTED` -> `UNPUBLISHED`, else `PENDING_ADMIN_APPROVAL`) and backfill `slug` as `trim(both '-' from regexp_replace(lower(coalesce(property_title, 'auction')), '[^a-z0-9]+', '-', 'g')) || '-' || left(id, 8)`.
    *   Drop `idx_auction_properties_status`; add unique index `idx_auction_slug ON auction_properties (slug)` and query indexes on `(publication_status, auction_date)`, `district`, `asset_category`, and `reserve_price_inr`.
    *   `DROP POLICY IF EXISTS "Public Read Published" ON auction_properties;` and `REVOKE SELECT ON auction_properties FROM anon, authenticated;`.
*   **`005_customer_accounts_and_lists.sql`** (Phase 2):
    *   Create `customer_profiles (user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE, full_name TEXT, phone TEXT, preferred_contact TEXT DEFAULT 'PHONE', created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())`.
    *   Create `saved_properties (id UUID PK DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, property_id TEXT NOT NULL REFERENCES auction_properties(id) ON DELETE CASCADE, created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(user_id, property_id))`.
    *   Create `recently_viewed (id UUID PK DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, property_id TEXT NOT NULL REFERENCES auction_properties(id) ON DELETE CASCADE, viewed_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(user_id, property_id))`.
    *   Enable RLS on all 3 tables: `FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)`.
*   **`006_leads_upgrade_and_service_agreements.sql`** (Phase 3):
    *   `ALTER TABLE customer_leads`: add `lead_code TEXT UNIQUE`, `user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL`, `preferred_contact TEXT`, `consent_to_contact BOOLEAN NOT NULL DEFAULT false`, `consent_at TIMESTAMPTZ`, `assigned_advisor_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
    *   Standardize `status` (`UPDATE customer_leads SET status = 'REQUEST_RECEIVED' WHERE status IN ('NEW', 'IN_REVIEW', 'SCHEDULED');` and `ADD CONSTRAINT chk_lead_status CHECK (status IN ('REQUEST_RECEIVED', 'CONTACTED', 'IN_PROGRESS', 'CLOSED'))`, default `'REQUEST_RECEIVED'`).
    *   Change `id` default from `#SK-XXXX` to `gen_random_uuid()::TEXT` (existing `#SK-XXXX` rows remain untouched).
    *   Add partial unique index `idx_leads_dedup_user ON customer_leads (user_id, property_id) WHERE user_id IS NOT NULL AND status <> 'CLOSED'`.
    *   `DROP POLICY IF EXISTS "Public Insert Leads" ON customer_leads;` and `REVOKE ALL ON customer_leads FROM anon, authenticated;`.
    *   Create `service_agreements (id UUID PK DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT, property_id TEXT NOT NULL REFERENCES auction_properties(id), lead_id TEXT NOT NULL REFERENCES customer_leads(id), commission_rate_pct NUMERIC(4,2) NOT NULL DEFAULT 5.00, calculation_basis TEXT NOT NULL, agreement_version TEXT NOT NULL, accepted_name TEXT NOT NULL, accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), ip_address TEXT, user_agent TEXT)`. Enable RLS on `service_agreements` (`FOR SELECT USING (auth.uid() = user_id)`). Note: because `user_id` uses `ON DELETE RESTRICT` for legal audit retention, customer account deletion must anonymize/soft-delete rather than hard-delete `auth.users`.
    *   Create PostgreSQL RPC `create_lead_with_agreement(p_user_id UUID, p_property_id TEXT, p_customer_name TEXT, p_phone TEXT, p_email TEXT, p_preferred_contact TEXT, p_inquiry_type TEXT, p_notes TEXT, p_require_agreement BOOLEAN, p_commission_rate NUMERIC, p_calculation_basis TEXT, p_agreement_version TEXT, p_accepted_name TEXT, p_ip TEXT, p_ua TEXT) RETURNS JSONB` to insert `customer_leads` (generating `lead_code := 'SK-' || to_char(NOW(), 'YYMMDD') || '-' || substr(gen_random_uuid()::TEXT, 1, 6)`) and `service_agreements` atomically.

### Migration Ordering & Rollback / Recovery

1. **Forward Order**: Take Supabase snapshot -> Stage 0 code deploy -> apply `004` + Phase 1 backend/frontend -> apply `005` + Phase 2 frontend -> apply `006` + Phase 3 backend/frontend.
2. **Rollback**: Because `004`–`006` drop/revoke `"Public Read Published"` and `"Public Insert Leads"` RLS policies, rolling back schema requires either restoring the pre-migration Supabase snapshot or re-creating those two policies after reverting code and dropping new tables/columns.

--------------------------------------------------------------------------------

## 7. Frontend Architecture, Routing & SEO

*   **Language**: JavaScript (`.js`/`.jsx`) with JSDoc; no TypeScript migration.
*   **Routing**: `react-router-dom` `BrowserRouter`:
    *   `/` (`HomeView.jsx`), `/auctions` (`PropertiesView.jsx`, with `/properties` redirecting to `/auctions`), `/properties/:idOrSlug` (`PropertyDetailsView.jsx`), `/saved` (`DashboardView.jsx` with `KYC` and `Alerts` tabs hidden/deferred), `/compare` (`CompareView.jsx` via `?ids=...`), `/about` (`AboutView.jsx`), `/services` (`ServicesView.jsx`), `*` (404).
    *   One-time hash redirect in `App.jsx`: `#property/:id` -> `/properties/:id`.
    *   `vercel.json` and `nginx.conf` already rewrite non-API routes to `/index.html`.
*   **SEO**: Dynamic `<title>`, `<meta name="description">`, `<link rel="canonical">`, OpenGraph tags, `JSON-LD` (`RealEstateListing` / `Offer` using factual fields only), `frontend/public/robots.txt`, and backend-served `GET /sitemap.xml` generated from `PUBLISHED` listings.
*   **SEO Limitation**: Client-rendered per-property OpenGraph tags do not guarantee rich link previews on crawlers that do not execute JavaScript (WhatsApp, LinkedIn). Prerendering/SSR is deferred to post-MVP evaluation.

--------------------------------------------------------------------------------

## 8. Alternatives Considered

*   **TypeScript + Next.js SSR Now**: Rejected by author to avoid delaying Stage 0 security fixes and MVP delivery.
*   **Custom Customer Auth in `backend/app.py`**: Rejected by author in favor of Supabase Auth + RLS to avoid duplicating session/recovery infrastructure.
*   **Block Publication Until All 8 Checks Pass**: Rejected by author due to 15–30 day SARFAESI timelines; admin-approved publication with transparent pending/risk disclosure is used instead.

--------------------------------------------------------------------------------

## 9. Unresolved Architectural Decisions

--------------------------------------------------------------------------------

1. **Legal & Tax Sign-Off on `service_agreements` Text**: Exact wording for calculation basis, GST, and Tamil Nadu brokerage compliance is pending legal counsel (mandatory before Phase 3 production go-live).
2. **Advisor Notification Transport**: MVP surfaces new leads in `AdminView.jsx` Leads Desk; whether Phase 3 also fires an email/WhatsApp webhook depends on provisioned SMTP/WhatsApp credentials.
3. **Production Environment Provisioning**: `ADMIN_JWT_SECRET`, `ALLOWED_ORIGINS`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY` must be configured in deployment environments before Stage 0/Phase 2 go-live.

--------------------------------------------------------------------------------

## 10. Potential Breaking Changes

1. **Removing `INITIAL_PROPERTIES` Mixing**: Environments without a running backend or Supabase connection will now show an explicit empty/error/retry state instead of mock properties (unless `VITE_ENABLE_DEMO_DATA=true` in dev).
2. **Removing `skandx-test-token-bypass`, `?token=` Auth & `leads.jsonl`**: Local admin testing must use `POST /api/admin/login` with valid credentials; `pytest` injects `ADMIN_JWT_SECRET` via fixtures.
3. **Revoking Direct `anon`/`authenticated` Access to `auction_properties` & `customer_leads`**: Any client attempting direct Supabase queries on those two tables will be rejected; all reads/writes flow through `backend/app.py`.
4. **Replacing Hash URLs (`#property/...`) & Retiring `POST /api/contact`**: Old hash URLs redirect via `App.jsx`; Phase 3 retires unauthenticated `POST /api/contact` in favor of `POST /api/v1/leads`.

--------------------------------------------------------------------------------

## 11. Security Acceptance Checklist

- [ ] `GET /api/auctions` and `GET /api/v1/auctions` return zero `borrower_name`, `contact_phone`, `authorized_officer_name`, `raw_extracted_json`, `review_notes`, or internal `verification_dimensions` fields (`reviewer`, `evidence_ref`, `notes`).
- [ ] Direct Supabase `anon` or `authenticated` queries cannot `SELECT` from `auction_properties` or `SELECT`/`INSERT` on `customer_leads`.
- [ ] `evaluate_sanity()` never sets `PUBLISHED`, and re-ingestion upserts preserve admin-set `publication_status`, `verification_dimensions`, and `risk_disclosures`.
- [ ] `ADMIN_JWT_SECRET` fails closed unconditionally when unset; `skandx-test-token-bypass` is removed from `App.jsx`.
- [ ] `customer_profiles`, `saved_properties`, `recently_viewed`, and `service_agreements` enforce `auth.uid() = user_id` isolation (verified by cross-user negative tests).
- [ ] `POST /api/v1/leads` derives `user_id` from verified JWT, validates `inquiry_type`, enforces atomic lead + agreement creation via RPC, and returns `409` on duplicate active leads.
- [ ] `frontend/dist/` contains zero occurrences of `SERVICE_ROLE` or `ADMIN_JWT_SECRET`.

--------------------------------------------------------------------------------

## 12. Detailed Implementation Plan (Traceable Sequence)

### Target Files & Sequence

| Stage | Dependencies | Target Files | Measurable Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Stage 0: Critical Fixes** | None (Mandatory Gate) | `backend/app.py`, `backend/test_app_security.py`, `backend/ingestion/database/supabase_client.py`, `frontend/package.json`, `frontend/src/data/api.js`, `frontend/src/data/propertiesData.js`, `frontend/src/App.jsx`, `frontend/src/views/AdminView.jsx` | Updated `pytest backend/test_app_security.py` passes (PII excluded, 401 on unauth admin, `do_PATCH` for `/api/admin/leads` & `/api/admin/properties` persist, `leads.jsonl` removed, `evaluate_sanity()` returns `NEEDS_MANUAL_REVIEW`); `npm run build` succeeds; path routes (`/auctions`, `/properties/:idOrSlug`, `/properties`->`/auctions`, `#property/:id` redirect, 404) work on refresh; zero mock mixing or token bypass. |
| **Phase 1: Discovery & Verification** | Stage 0 passed; `004` migrated | `backend/migrations/004_publication_and_verification.sql`, `backend/app.py`, `frontend/src/App.jsx`, `frontend/src/views/HomeView.jsx`, `frontend/src/views/PropertiesView.jsx`, `frontend/src/views/PropertyDetailsView.jsx`, `frontend/src/components/PropertyCard.jsx`, `frontend/public/robots.txt` | `PropertiesView.jsx` removes `frameworkFilter` and queries `GET /api/v1/auctions` with server-side filters, pagination, and `auction_date >= NOW()` / `EXPIRED` handling; `GET /sitemap.xml` serves `PUBLISHED` URLs; `PropertyDetailsView.jsx` renders 8 verification dimensions (public projection only) + risk disclosures; admin publish blocked unless minimum checks pass. |
| **Phase 2: Customer Auth & Lists** | Phase 1; `005` migrated; Supabase Auth env vars | `backend/migrations/005_customer_accounts_and_lists.sql`, `frontend/package.json`, `frontend/src/lib/supabaseClient.js`, `frontend/src/App.jsx`, `frontend/src/components/Modals/AuthModal.jsx`, `frontend/src/views/DashboardView.jsx`, `frontend/src/views/CompareView.jsx`, `frontend/src/data/initialUserData.js` | Register/login/logout/reset work; saved/recently-viewed persist in Supabase and hydrate via `backend/app.py`; `/compare?ids=...` works; deferred `KYC`/`Alerts` tabs hidden; RLS blocks cross-user reads/writes. |
| **Phase 3: Connect & 5% Agreement** | Phase 2; `006` migrated; Legal sign-off (Sec 9.1) for prod launch | `backend/migrations/006_leads_upgrade_and_service_agreements.sql`, `backend/app.py`, `frontend/src/data/api.js`, `frontend/src/App.jsx`, `frontend/src/components/Modals/ContactModal.jsx`, `frontend/src/views/AdminView.jsx` | `POST /api/contact` retired; `POST /api/v1/leads` validates `inquiry_type`, returns 409 on duplicate active lead, and executes `create_lead_with_agreement` RPC atomically; admin fetches `GET /api/admin/advisors` and assigns advisor via `PATCH /api/admin/leads`; `GET /api/v1/me/leads` returns `REQUEST_RECEIVED` without internal `notes`. |

--------------------------------------------------------------------------------

*Drafted with EGM (Elephant & Goldfish Model)*
