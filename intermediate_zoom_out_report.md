# Stage 8: Intermediate Zoom Out Review Report

* **Target Document:** `docs/designs/customer-platform-mvp.md` (lines 1–227)
* **Reviewer:** `egm-zoom-out`
* **Goldfish Context:** `concepts_brief.md`, `zoom_out_report.md`
* **Date:** 2026-11-25

---

## Verdict

All Stage 5/6/7 blockers are resolved without introducing schema bloat (`compared_properties` and post-MVP billing columns were removed, and `review_status` vs. `publication_status` dual-sync was eliminated). Four remaining findings (1 Major, 3 Nits) are listed below.

---

## Remaining Findings

### 1. Legacy Unauthenticated `POST /api/leads` and `leads.jsonl` Dual-Store Not Explicitly Retired — **Major**
* **Scope:** Sections 4, 5.3, 6, 11, 12
* **Issue:** The plan notes that `load_leads()` mixes `leads.jsonl` and Supabase, but does not explicitly state removing `leads.jsonl` reads/writes, retiring unauthenticated `POST /api/leads` when `POST /api/v1/leads` ships, or confirming `GET /api/auctions` is an alias to `GET /api/v1/auctions` with `PUBLIC_AUCTION_COLUMNS`.
* **Recommendation:** Explicitly remove `leads.jsonl` fallback in Stage 0, alias `GET /api/auctions` to `GET /api/v1/auctions`, and retire unauthenticated `POST /api/leads` in Phase 3.

### 2. Phase 3 `service_agreements` Production Go-Live Dependency — **Nit**
* **Scope:** Sections 5.4, 6, 9, 12
* **Recommendation:** Add legal sign-off (Section 9.1) as an explicit Phase 3 production go-live gate in Section 12.

### 3. New Ingestion Inserts Missing `slug` Generation — **Nit**
* **Scope:** Sections 5.2, 6, 7
* **Recommendation:** Note in Section 5.2 that `supabase_client.py` (or a DB trigger/default) generates `slug` on new property inserts.

### 4. `service_agreements.user_id` `ON DELETE RESTRICT` Blocks Auth User Deletion — **Nit**
* **Scope:** Section 6
* **Recommendation:** Document that account deletion anonymizes/soft-deletes rather than hard-deleting `auth.users`, or align with `ON DELETE SET NULL`.
