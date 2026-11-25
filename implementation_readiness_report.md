# Stage 9: Implementation Readiness Test Report

* **Target Document:** `docs/designs/customer-platform-mvp.md` (Section 12 + Sections 5–11)
* **Reviewers:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Goldfish Context:** `concepts_brief.md`
* **Date:** 2026-11-25

---

## Blockers

1. **Admin Token Format & Auth Verification Contradiction** (`Section 5.3`, `Section 12 Stage 0`):
   * `backend/app.py` and `backend/test_app_security.py` use `skandx-adm-{ts}-{sig}` (24h TTL, no payload) and `ADMIN_EMAIL`/`ADMIN_PASSWORD` env vars without querying `admin_users`. Also, `test_app_security.py` imports `backend.app` at module top level without setting `ADMIN_JWT_SECRET`.
   * **Needed:** Specify whether Stage 0 migrates to `payload_b64.sig` + 8h TTL + `admin_users` lookup or keeps `skandx-adm-{ts}-{sig}`, and fail closed at request/login time (not module import time) so `pytest` collection works.
2. **Stage 0 vs. Phase 1 Status Column & `ReviewStatus` Mismatch** (`Section 5.2`, `Section 12 Stage 0 & Phase 1`):
   * `ReviewStatus` in `backend/ingestion/models/auction_schema.py` only defines `PUBLISHED`, `NEEDS_MANUAL_REVIEW`, `EXPIRED`, `SOLD`, while `004` (`publication_status`) is in Phase 1.
   * **Needed:** Specify that `evaluate_sanity()` returns `ReviewStatus.NEEDS_MANUAL_REVIEW` in Stage 0, and `004` switches to `publication_status` in Phase 1.
3. **Property Update Endpoint & Editable Field Allowlist Unspecified** (`Section 5`, `Section 5.3`, `Section 12 Stage 0`):
   * `backend/app.py` currently uses `POST /api/admin/properties/verify` and `ApiRequestHandler` has no `do_PATCH`.
   * **Needed:** Define `do_PATCH` on `ApiRequestHandler`, exact path (`/api/admin/properties` with `id` in body, keeping `POST /api/admin/properties/verify` as a Stage 0 alias or updating `api.js`), and the exact column allowlist for `persist_property_update()`.
4. **Lead/Agreement RPC Signature, Allowlist Mapping & Agreement Config Missing** (`Section 5.3`, `Section 5.4`, `Section 6`, `Section 12 Phase 3`):
   * `ContactModal.jsx` uses labels like `'Site Inspection'` and `POST /api/contact` exists without JWT/allowlist.
   * **Needed:** Define `POST /api/contact` retirement/mapping, UI-to-enum mapping, SQL signature for `create_lead_with_agreement(...)`, and server config defaults for `agreement_version` and `calculation_basis`.
5. **Stage 0 vs. Phase 3 Dependency Conflict on `PATCH /api/admin/leads`** (`Section 5.3`, `Section 12 Stage 0 & Phase 3`):
   * In Stage 0, `002_create_customer_leads.sql` only has `status` (no `assigned_advisor_id`).
   * **Needed:** Clarify that Stage 0 `PATCH /api/admin/leads` persists `status` (and `notes`) on `002`, while Phase 3 (`006`) adds `assigned_advisor_id` and `GET /api/admin/advisors`.

---

## Major Findings

1. **Missing Query & Response Contracts for Phase 1/2 Public Auction Endpoints:** Specify exact query params (`q`, `district`, `type`, `bank`, `possession`, `min_price`, `max_price`, `deadline`, `include_expired`, `ids`, `sort`, `page`, `limit`), pagination envelope, and `GET /api/auctions` alias.
2. **Migration Schema Gaps (`004`, `005`, `006`):** Trim leading/trailing hyphens in `004` `slug` backfill, drop `idx_auction_properties_status` when retiring `review_status` or keep indexed, clarify `DashboardView.jsx` tabs (`KYC`, `Alerts`) in Phase 2, and add `ENABLE ROW LEVEL SECURITY` + `SELECT` policy (`auth.uid() = user_id`) for `service_agreements` in `006`.
3. **Target Files Omissions in Section 12:** Add `backend/test_app_security.py`, `backend/ingestion/models/auction_schema.py`, `frontend/src/data/propertiesData.js`, `frontend/src/data/initialUserData.js`, `frontend/src/App.jsx`, and backend `/sitemap.xml` route.
4. **Frontend Route Mapping & Legacy Hash Redirects:** Specify `/properties` -> `/auctions` redirect, `/saved` vs `/account` for `DashboardView.jsx`, and `#property/:id` redirect in Stage 0.
5. **`PropertiesView.jsx` Filter Cleanup:** Explicitly state removing `frameworkFilter` and moving from client-side `useMemo` filtering to server-side `GET /api/v1/auctions` queries in Phase 1.

---

## Nits

1. Standardize `:idOrSlug` across Section 5 and Section 7.
2. Use full `frontend/...` paths in Section 12.
3. Note that `backend/test_app_security.py` must be updated in Stage 0 to remove the `skandx-test-token-bypass` assertion.
