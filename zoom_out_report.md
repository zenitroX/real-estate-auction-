# Stage 5: Initial Zoom Out Review Report

* **Target Document:** `docs/designs/customer-platform-mvp.md` (lines 1–217)
* **Reviewers:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Goldfish Context:** `concepts_brief.md`
* **Date:** 2026-11-25

---

## Prioritized Findings

### 1. Dual Status Column (`review_status` vs. `publication_status`) Creates Split-Brain Risk — **Blocker**
* **Lenses:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** Lines 103–105, 144–145, 161–162 (`Section 5.2`, `Section 6`)
* **Issue:** Adding `publication_status` while keeping `review_status` and dual-syncing in `backend/app.py` and `supabase_client.py` risks split-brain between `001`'s RLS policy (`review_status = 'PUBLISHED'`) and the API (`publication_status = 'PUBLISHED'`).
* **Recommendation:** Use a single status column (`review_status` extended with the needed states, or a one-time rename after dropping `001`'s RLS policy) instead of maintaining two synchronized status columns.

### 2. Unresolved Public Read Path & PostgREST Join Contradiction — **Blocker**
* **Lenses:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** Lines 44, 96–98, 147, 149–151 (`Section 5.1`, `Section 6`)
* **Issue:** The doc leaves open revoking `anon` `SELECT` on `auction_properties` vs. adding a `public_auction_listings` view. If `SELECT` is revoked without a view, direct PostgREST joins from `saved_properties` fail; if a view is added alongside `backend/app.py`, two public read paths must be maintained. Also, line 44 vs. line 211 is unclear on whether `EXPIRED` rows are filtered out or shown with an expired label.
* **Recommendation:** Pick one public read path (revoke `anon`/`authenticated` `SELECT` on `auction_properties` and hydrate saved/recent IDs via `backend/app.py` or `GET /api/v1/auctions?ids=...`) and explicitly define `EXPIRED` filtering/labeling.

### 3. `verification_dimensions` Public Projection Leaks Internal Reviewer Notes — **Major**
* **Lenses:** `egm-zoom-out`
* **Affected Scope:** Lines 96–97, 104 (`Section 5.1`, `Section 5.2`)
* **Issue:** `PUBLIC_AUCTION_COLUMNS` includes `verification_dimensions` in full, and each dimension object contains `reviewer`, `evidence_ref`, and `notes`, which risks leaking internal staff identifiers or unredacted legal notes.
* **Recommendation:** Project only `status`, `reviewed_at`, and `review_period` in the `backend/app.py` public serializer.

### 4. Unvalidated 5% Service Agreement Enforced as Mandatory Clickwrap Gate — **Major**
* **Lenses:** `egm-inventive-catalyst`
* **Affected Scope:** Lines 124–135, 157, 185 (`Section 5.4`, `Section 6`, `Section 9`)
* **Issue:** The design flags the 5% terms (calculation basis, GST, Tamil Nadu brokerage/RERA, clickwrap enforceability) as unresolved for legal review, yet makes clickwrap acceptance of those terms mandatory before requesting inspection or document review.
* **Recommendation:** Use a plain-English fee disclosure acknowledgment on `customer_leads` for MVP (confirming the customer was informed of the proposed 5% model and that a separate signed mandate applies before engagement), or obtain legal sign-off before shipping `service_agreements`.

### 5. Over-Engineered MVP Schema (`compared_properties`, Post-MVP Billing Columns) — **Major**
* **Lenses:** `egm-zoom-out`
* **Affected Scope:** Lines 35, 149–151, 157 (`Section 2`, `Section 6`)
* **Issue:** `compared_properties` in Postgres duplicates URL/client comparison state (`/compare?ids=...`), and `acquisition_outcome` / `payment_status` / `legal_review_status` in `service_agreements` belong to deferred post-MVP commission tracking.
* **Recommendation:** Drop `compared_properties` from `005` and defer billing columns from `006`.

### 6. Lead Status, Auth Requirement, and Foreign Key Inconsistencies — **Major**
* **Lenses:** `egm-zoom-out`
* **Affected Scope:** Lines 56, 118, 126–127, 153–157 (`Section 3`, `Section 5.3`, `Section 5.4`, `Section 6`)
* **Issue:** `customer_leads.status` mixes `'NEW'`, `'Request received'`, and `'CLOSED'` without an explicit state list; `POST /api/v1/leads` requires a JWT while `user_id` is nullable; `service_agreements` lacks `REFERENCES auth.users(id) ON DELETE CASCADE` and could orphan rows if lead creation returns `409`.
* **Recommendation:** Standardize `customer_leads.status` values, make `user_id` consistent with JWT auth, add `ON DELETE CASCADE` on `service_agreements.user_id`, and run duplicate checks before inserting any agreement row.

### 7. Deployment Ordering Contradiction & Missing `slug` Backfill — **Major**
* **Lenses:** `egm-zoom-out`
* **Affected Scope:** Lines 144, 161 (`Section 6`)
* **Issue:** Line 161 deploys `backend/app.py` before `005` and `006` are applied, and `004` adds `slug TEXT` without backfill or index while `/properties/:slugId` and `/sitemap.xml` rely on it.
* **Recommendation:** Apply each migration before deploying code that queries its columns/tables, and backfill `slug` (or parse `<slug>-<id>` using `id`) in `004`.

### 8. `PYTEST_CURRENT_TEST` Auth Bypass & Unspecified Admin Advisor Identity — **Major**
* **Lenses:** `egm-zoom-out`
* **Affected Scope:** Lines 116, 120, 192 (`Section 5.3`, `Section 10`)
* **Issue:** Line 192 implies branching auth on `PYTEST_CURRENT_TEST`, and `PATCH /api/admin/leads` sets `assigned_advisor_id` without specifying how `skandx-adm-...` HMAC tokens resolve `admin_users.id` or enforce TTL.
* **Recommendation:** Inject a test `ADMIN_JWT_SECRET` in `pytest` fixtures instead of branching auth code, and document HMAC payload (`admin_id`, `exp`) and TTL checks.

### 9. Unwired `frameworkFilter` & Route Parameter Naming Drift — **Nit**
* **Lenses:** `egm-zoom-out`
* **Affected Scope:** Lines 64, 169, 210 (`Section 4`, `Section 7`, `Section 12`)
* **Issue:** `frameworkFilter` has no DB column or Phase 1 requirement, and routes alternate between `/properties/:slugId` and `/properties/:id`.
* **Recommendation:** Remove `frameworkFilter` as dead UI and standardize on one route parameter convention.

### 10. Outbound Auth Verification Hop on Every Authenticated Backend Request — **Nit**
* **Lenses:** `egm-zoom-out`
* **Affected Scope:** Line 118 (`Section 5.3`)
* **Issue:** Calling `{SUPABASE_URL}/auth/v1/user` on every `POST /api/v1/leads` and `GET /api/v1/me/leads` adds latency.
* **Recommendation:** Acceptable for MVP; note local JWT verification (`SUPABASE_JWT_SECRET`) as a future optimization.
