# Stage 6: Comprehension Test Report

* **Target Document:** `docs/designs/customer-platform-mvp.md` (FeatureRange: lines 1–205, DetailedRange: lines 206–217)
* **Reviewer:** `egm-comprehension`
* **Date:** 2026-11-25

---

**What this proposes**
This document proposes a four-stage remediation and MVP implementation plan (Stage 0 and Phases 1–3) for the customer-facing side of the SKANDX Tamil Nadu Bank Auction Intelligence Platform. Stage 0 fixes security and data-integrity bugs by removing public PII exposure, repairing database-to-frontend field mappings, removing mock-data mixing and admin token bypasses, enforcing manual admin publication approval, and switching from hash routing to path-based URLs. Phases 1–3 add public auction discovery with an 8-dimension verification checklist and risk disclosures, Supabase customer accounts with RLS-protected saved, compared, and recently viewed lists, and an advisor-connection workflow gated by a proposed 5% success-commission service agreement for substantive paid assistance. The implementation sequence in Section 12 defines the dependencies, target files, and acceptance criteria for each stage across the React/Vite frontend, Python REST backend, and Supabase PostgreSQL migrations (`004`–`006`).

**How the existing system works, per this document**
According to this document, SKANDX aggregates bank auction notices using a Playwright and Gemini 2.5 Flash OCR ingestion pipeline into a Supabase PostgreSQL database, served by a Python 3.12 REST backend (`backend/app.py`) to a React 19 + Vite 6 JavaScript single-page application (`frontend/`). Currently, `GET /api/auctions` exposes PII via `select=*`, `frontend/src/data/api.js` maps non-existent column names and mixes hardcoded `INITIAL_PROPERTIES` mock data with live rows, and `frontend/src/App.jsx` uses hash routing (`#property/p1`) and auto-grants a test admin bypass token on `admin.*` hostnames. On the backend and database side, `evaluate_sanity()` auto-publishes ingested records, `persist_property_update()` drops most edited fields, `PATCH /api/admin/leads` is missing, `load_leads()` mixes a `leads.jsonl` file with Supabase, and `customer_leads` allows unrestricted public inserts with colliding `#SK-XXXX` primary keys. There is currently no customer authentication, no saved/compared/recently-viewed persistence, no separation between publication status and verification checks, and no service agreement gate.

---

### Findings (Undefined Terms, Acronyms, Ambiguities, and Comprehension Gaps)

1. **Major — `:slugId` vs `:id` routing and `slug` generation** (`Section 3`, `Section 5`, `Section 7`, `Section 12`): Frontend route alternates between `/properties/:slugId` and `/properties/:id`, and `004` adds `slug TEXT` without explaining backfill or `:slugId` parsing.
2. **Major — `review_status` dual-sync** (`Section 5.2`, `Section 6`): Full mapping between the 6 `publication_status` values and legacy `review_status` values during transition is not defined.
3. **Major — `customer_profiles` schema** (`Section 6`, `005`): `customer_profiles` is listed in `005` without its columns, constraints, or usage.
4. **Major — Undefined domain acronyms** (`SARFAESI`, `EMD`, `EC`, `RERA`, `IT Act 2000`): Used without inline expansion or plain-English explanation of what `ec_reviewed` and `revenue_records_reviewed` verify.
5. **Nit — `review_period` in `verification_dimensions`** (`Section 5.2`): Purpose, data type, and expected values are not explained.
6. **Nit — Endpoint list completeness & `PATCH` URL convention** (`Section 5`, `Section 5.3`, `Section 10`): `GET /api/v1/me/leads` and `POST /api/admin/login` are omitted from the Section 5 diagram, and `PATCH /api/admin/properties` / `PATCH /api/admin/leads` do not state whether IDs go in the path or body.
7. **Nit — "Admin Leads Desk" and in-app notifications** (`Section 3`, `Section 9`): Unclear whether notification is a row appearing in `AdminView.jsx` or an active alert.
8. **Nit — `PYTEST_CURRENT_TEST`** (`Section 10`): Unexplained what `PYTEST_CURRENT_TEST` controls in `backend/app.py`.
9. **Nit — `EGM` acronym** (Footer): `*Drafted with EGM*` is undefined.
