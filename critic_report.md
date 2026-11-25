# Stage 7: Critic Review Report

* **Target Document:** `docs/designs/customer-platform-mvp.md` (FeatureRange: lines 1–205)
* **Reviewers:** `egm-design`, `egm-structural`, `egm-style`
* **Goldfish Context:** `concepts_brief.md`, `backend/migrations/001..003.sql`
* **Date:** 2026-11-25

---

## Blockers

### 1. `authenticated` role can still read borrower PII from `auction_properties` (and ambiguous view security in `004`)
* **Scope:** Lines 98, 147 (vs. `001_create_auction_properties.sql` lines 52–54)
* **Issue:** `"Public Read Published"` in `001` has no `TO anon` clause, so it applies to both `anon` and `authenticated`. Revoking only `anon` `SELECT` leaves logged-in customers able to run `supabase.from('auction_properties').select('*')` and read `borrower_name`, `contact_phone`, `authorized_officer_name`, `raw_extracted_json`, and `review_notes`. Leaving an optional `public_auction_listings` view is also unsafe without `security_invoker`.
* **Recommendation:** Unconditionally `DROP POLICY "Public Read Published"` and `REVOKE SELECT ON auction_properties FROM anon, authenticated`, routing all public reads through `backend/app.py`'s `PUBLIC_AUCTION_COLUMNS` serializer.

### 2. `"Customer Read Own Leads"` RLS policy exposes internal admin `notes`
* **Scope:** Lines 119, 156 (vs. `002_create_customer_leads.sql` line 13)
* **Issue:** `GET /api/v1/me/leads` excludes internal admin notes, but `"Customer Read Own Leads"` (`FOR SELECT USING (auth.uid() = user_id)`) on `customer_leads` lets any authenticated customer query `supabase.from('customer_leads').select('*')` directly and read `notes`.
* **Recommendation:** Revoke `SELECT` on `customer_leads` from `authenticated` (routing all customer reads through `GET /api/v1/me/leads`) or isolate internal admin notes in a `service_role`-only column/table.

### 3. Non-atomic `customer_leads` and `service_agreements` writes over PostgREST
* **Scope:** Lines 56, 157, 203
* **Issue:** Two separate PostgREST inserts are not transactional and can leave a paid-assistance lead without a `service_agreements` row or an orphaned agreement row on `409` duplicate-lead failure.
* **Recommendation:** Execute paid-assistance lead + agreement creation inside a single PostgreSQL RPC function (`CREATE FUNCTION`) called by `backend/app.py`, mapping `23505` unique-violation errors to HTTP `409`.

---

## Major

### 4. Unstandardized `customer_leads.status` breaks duplicate-lead prevention
* **Scope:** Lines 56, 155 (`002` line 14)
* **Recommendation:** Define a canonical `status` `CHECK` constraint/enum (e.g., `REQUEST_RECEIVED`, `CONTACTED`, `IN_PROGRESS`, `CLOSED`) aligned across CUJ 3, `006`, and `backend/app.py`.

### 5. `service_agreements` terms and `inquiry_type` gate must be enforced server-side
* **Scope:** Lines 126–127, 157, 203
* **Recommendation:** Validate `inquiry_type` against an explicit server-side allowlist and populate `commission_rate_pct`, `calculation_basis`, and `agreement_version` strictly on the server.

### 6. Missing `customer_profiles` schema and inconsistent `auth.users` foreign keys
* **Scope:** Lines 149–151, 153, 157
* **Recommendation:** Define `customer_profiles` columns explicitly (`user_id` PK) and add `REFERENCES auth.users(id)` + `ON DELETE` rules to `customer_leads.user_id` and `service_agreements.user_id`.

### 7. Re-ingestion upsert behavior can overwrite `publication_status` and `verification_dimensions`
* **Scope:** Line 105 (`001` line 36)
* **Recommendation:** Ensure `ON CONFLICT (auction_event_hash) DO UPDATE` preserves existing `publication_status`, `verification_dimensions`, and `risk_disclosures`.

### 8. Admin HMAC identity/role mapping and "in production" fail-closed trigger are underspecified
* **Scope:** Lines 116, 120, 192
* **Recommendation:** Fail closed unconditionally when `ADMIN_JWT_SECRET` is unset (test override via `pytest` fixture only) and specify how HMAC tokens map to `admin_users.id` / `email` and `is_active`.

### 9. Rollback instructions omit restoring dropped RLS policies
* **Scope:** Lines 147, 156, 162
* **Recommendation:** Explicitly include restoring `"Public Read Published"` and `"Public Insert Leads"` (or full snapshot restore) in rollback steps.

### 10. `slug` column in `004` lacks uniqueness, backfill, and route resolution contract
* **Scope:** Lines 85, 144, 169
* **Recommendation:** Define `:slugId` lookup/parsing (e.g., trailing `id` extraction) or enforce unique indexed `slug` with backfill in `004`.

---

## Nits

11. **Expired auction lifecycle** (Lines 103, 109): Clarify query-time `auction_date >= NOW()` filtering vs. `EXPIRED` status sync.
12. **Legacy `GET /api/auctions` status** (Lines 20, 84, 198): State explicitly that `/api/auctions` remains as a safe-column alias.
13. **External `source_pdf_url` PII risk** (Line 96): Note that `source_pdf_url` only links to public bank/newspaper notices.
14. **Formatting dividers** (Lines 183–205): Add `---` dividers before Sections 9–11.
