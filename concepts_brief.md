# SKANDX Customer-Facing Bank Auction Platform (Stage 0 + MVP Phases 1–3)

* **Author:** rajkrish63
* **Date:** 2026-11-25

## Overview

Build the customer-facing MVP (Phases 1–3) of the SKANDX Tamil Nadu bank-auction discovery and buyer-assistance platform on the existing React + Vite JavaScript SPA (`frontend/`), Python REST backend (`backend/app.py`), and Supabase PostgreSQL stack.

Implementation is strictly gated: **Stage 0** resolves existing critical security, data-integrity, and routing defects first. Once Stage 0 acceptance checks pass, **Phases 1–3** deliver free public auction discovery with an 8-dimension verification checklist and risk disclosures, Supabase Auth customer accounts with saved/compared/recently-viewed properties, and a "Connect with Auction Advisor" conversion workflow gated by an explicit 5% success-commission service agreement. Admin HMAC authentication remains separate and intact.

---

## Analysis

### Stage 0 — Mandatory Critical Fixes (Pre-MVP Gate)

1. **Public API PII Exposure (`backend/app.py`)**: `GET /api/auctions` currently runs `select=*`, exposing `borrower_name`, `contact_phone`, `authorized_officer_name`, and `raw_extracted_json`. Replace with explicit public column projection and a safe serializer; restrict private fields to authorized admin endpoints and audit logs/errors.
2. **Supabase Field Mapping & Mock Mixing (`frontend/src/data/api.js`)**: `api.js` reads non-existent keys (`reserve_price`, `emd_amount`, `property_type`, `branch`, `city`, `address`, `source_url`) instead of actual schema columns (`reserve_price_inr`, `emd_amount_inr`, `asset_category`, `branch_name`, `village_or_locality`, `district`, `source_pdf_url`, `emd_last_date`, `possession_type`), and silently merges `INITIAL_PROPERTIES` mock data with live rows. Fix all mappings, remove production mock mixing, and surface explicit error/empty/retry states.
3. **Admin-Only Publication Approval (`backend/ingestion/database/supabase_client.py`)**: `evaluate_sanity()` currently auto-assigns `ReviewStatus.PUBLISHED`. Ingestion must default new records to `PENDING_REVIEW` / `PENDING_ADMIN_APPROVAL`; only an authorized admin may publish.
4. **Admin Persistence & Auth Bypass (`backend/app.py`, `frontend/src/App.jsx`, `frontend/src/data/api.js`)**: `persist_property_update()` drops all edited fields except `review_status` and `reserve_price_inr`; `handleUpdateLeadStatus()` mutates only React state because `PATCH /api/admin/leads` is missing; `App.jsx` auto-creates `skandx-test-token-bypass` on `admin.*` hosts; and `api.js` swallows 401/network failures. Repair full property/lead persistence, remove hostname-based bypasses and synthetic 401 fallbacks, and keep admin HMAC auth separate from customer Supabase Auth.
5. **Path-Based Routing (`frontend/src/App.jsx`, hosting config)**: Replace hash URLs (`#property/p1`) with clean path-based URLs supporting direct navigation, refresh, back/forward, 404s, and SPA server fallback.

### MVP Architectural Assessment (Phases 1–3)

1. **Supabase Auth & Admin Separation**: Add `@supabase/supabase-js` (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`) for customer sessions (`auth.uid()`) and RLS-protected customer tables (`saved_properties`, `recently_viewed`, `compared_properties`). Keep admin HMAC tokens (`skandx-adm-...`) separate; validate customer JWTs in `backend/app.py` via `{SUPABASE_URL}/auth/v1/user` when needed.
2. **Property & Auction Models**: `001_create_auction_properties.sql` already includes core discovery fields. Extend `backend/app.py` for server-side filtering, pagination, and expired-auction handling (`auction_date < NOW()`), and wire `possessionFilter` / `frameworkFilter` in `PropertiesView.jsx`.
3. **Publication vs. 8 Verification Dimensions**: Separate `publication_status` (`DRAFT`, `PENDING_ADMIN_APPROVAL`, `PUBLISHED`, `UNPUBLISHED`, `EXPIRED`, `CANCELLED`) from `verification_dimensions` (`JSONB` for the 8 checks) and `risk_disclosures` (`JSONB`). Admin-approved listings may be published with pending checks as long as material risks and pending dimensions are disclosed.
4. **Admin Leads & 5% Service Agreement**: Upgrade `customer_leads` from colliding 4-digit `#SK-XXXX` IDs to `gen_random_uuid()::TEXT` + non-colliding display code, `user_id`, `assigned_advisor_id`, and a partial unique index for duplicate prevention. Add `service_agreements` (`commission_rate_pct DEFAULT 5.00`, `agreement_version`, `accepted_name`, `accepted_at`, `ip_address`, `user_agent`) to gate paid advisor assistance without building automated payment collection.
5. **Frontend Language & SEO Limits**: Keep JavaScript (`.js`/`.jsx`) for MVP speed. Add dynamic titles, meta descriptions, canonical URLs, `sitemap.xml`, `robots.txt`, and `JSON-LD` where factual. Document that client-rendered OpenGraph tags do not guarantee WhatsApp/LinkedIn link previews without future prerendering/SSR.

---

## Goals vs. Non-Goals

* **In-Scope Goals:**
  * **Stage 0:** Fix PII exposure in `GET /api/auctions`, fix `api.js` schema mappings, remove production mock mixing, stop scraper auto-publishing, repair `persist_property_update()` and add `PATCH /api/admin/leads`, remove `skandx-test-token-bypass`, switch to clean path-based routes, and pass backend/frontend/security tests.
  * **Phase 1:** Customer homepage, auction discovery grid with filters/pagination, path-based property detail pages, deadline intelligence, 8-dimension verification summary, and risk disclosures.
  * **Phase 2:** Supabase Auth (register, login, logout, profile, password recovery), saved properties, comparison, and recently viewed properties.
  * **Phase 3:** Connect with Auction Advisor flow, duplicate-lead prevention, `service_agreements` (5% proposed rate disclosure), admin lead notification, and basic advisor assignment.
* **Out-of-Scope Non-Goals (Deferred):**
  * TypeScript migration and Next.js / SSR / prerendering migration (evaluated post-MVP).
  * Full customer dashboard, automated 5% commission calculation/collection, and automated WhatsApp/SMS/email engines.
  * Rewriting the Playwright + Gemini OCR ingestion pipeline or replacing admin HMAC auth.

---

## Alternatives Weighed

* **Migrate frontend to TypeScript before MVP:** Rejected by author to avoid delaying Stage 0 critical fixes and MVP delivery; JSDoc and explicit API contracts will be used instead.
* **Migrate frontend to Next.js for SSR SEO:** Rejected by author for MVP; clean path-based routing + client metadata/sitemap will be shipped first, with prerendering/SSR evaluated separately later.
* **Custom customer auth in `backend/app.py`:** Rejected in favor of Supabase Auth + RLS to reuse existing Supabase infrastructure and keep customer auth isolated from admin HMAC auth.
* **Block publication until all 8 verification dimensions pass:** Rejected by author due to short SARFAESI auction windows; admin approval gates publication while pending checks are disclosed transparently.

---

## Key Decisions & Staging for Next Steps

1. **Stage 0 (Mandatory Gate):** Inspect & plan → fix PII projection, `api.js` mappings, mock mixing, scraper auto-publish, admin property/lead persistence, hostname token bypass, and path-based routing → pass backend, frontend, build, and security regression checks.
2. **Phase 1 (Customer Discovery):** Public homepage, filtered/paginated discovery, property detail pages, 8-dimension verification + risk disclosures, deadline intelligence, and SPA SEO metadata/sitemap.
3. **Phase 2 (Customer Accounts):** `@supabase/supabase-js` Auth, customer profile, and RLS-backed saved, compared, and recently viewed properties.
4. **Phase 3 (Customer Conversion):** Connect with Auction Advisor modal, 5% service agreement acceptance, duplicate-safe lead creation, and admin/advisor assignment workflow.
