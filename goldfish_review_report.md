# Goldfish Review Resolution Log (`goldfish_review_report.md`)

* **Target Document:** `docs/designs/customer-platform-mvp.md`
* **Date:** 2026-11-25

All Blockers and Major findings from Stages 5–9 (`zoom_out_report.md`, `comprehension_report.md`, `critic_report.md`, `intermediate_zoom_out_report.md`, `implementation_readiness_report.md`) were evaluated and resolved in `docs/designs/customer-platform-mvp.md`:

| Source | Finding | Resolution |
| :--- | :--- | :--- |
| Stage 5–7 | Dual status, `authenticated` PII read, `notes` leak, non-atomic writes, `compared_properties` bloat, acronyms | Standardized on `publication_status` after `004`, revoked `anon`/`authenticated` `SELECT` on `auction_properties` & `customer_leads`, added `create_lead_with_agreement` RPC, dropped `compared_properties` & billing columns, expanded acronyms. |
| Stage 8 Major 1 | `leads.jsonl` dual-store & unauthenticated `POST /api/leads` / `POST /api/contact` | Removed `leads.jsonl` fallback in Stage 0, aliased `GET /api/auctions` to `GET /api/v1/auctions`, retired `POST /api/contact` in Phase 3. |
| Stage 8 Nits 2–4 | Legal sign-off gate, new-insert `slug`, `ON DELETE RESTRICT` | Added legal sign-off as Phase 3 prod go-live gate, added `slug` generation in `supabase_client.py`, documented soft-delete/anonymization for `service_agreements` retention. |
| Stage 9 Blocker 1 | Admin token format & `pytest` import fail-closed | Retained `skandx-adm-{ts}-{sig}` (8h TTL) in Stage 0; fail closed at request/login/verify time so `pytest` collection works with fixture-injected `ADMIN_JWT_SECRET`. |
| Stage 9 Blocker 2 | `ReviewStatus` in Stage 0 vs. `publication_status` in Phase 1 | Stage 0 uses `ReviewStatus.NEEDS_MANUAL_REVIEW` in `evaluate_sanity()`; Phase 1 (`004`) transitions to `publication_status`. |
| Stage 9 Blocker 3 | `do_PATCH` & editable field allowlist | Added `do_PATCH` to `ApiRequestHandler`, `PATCH /api/admin/properties` (with `POST /api/admin/properties/verify` alias), and explicit `ADMIN_EDITABLE_PROPERTY_COLUMNS`. |
| Stage 9 Blocker 4 | `inquiry_type` allowlist, RPC signature, server config | Defined UI-to-enum mapping, full `create_lead_with_agreement(...)` SQL signature, and `AGREEMENT_VERSION` / `AGREEMENT_CALCULATION_BASIS` defaults. |
| Stage 9 Blocker 5 | Stage 0 vs. Phase 3 `PATCH /api/admin/leads` | Stage 0 persists `status` & `notes` on `002`; Phase 3 (`006`) adds `assigned_advisor_id` + `GET /api/admin/advisors`. |
| Stage 9 Majors 1–5 | Query/pagination contract, `004`/`006` fixes, target files, route redirects, `frameworkFilter` | Added query/pagination contract, trimmed `slug` backfill + dropped `idx_auction_properties_status`, added `service_agreements` RLS, listed all target files, added `/properties` & `#property/:id` redirects, and removed `frameworkFilter`. |
