# Intermediate Zoom Out Review Report (Stage 8)

**Evaluator**: Skeptical Architect (`egm-zoom-out` persona)  
**Target Document**: [PROJECT.md](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md) (lines 1–276)  
**Standard**: Zoom-Out Standard / Minimal-Complexity Standard  
**Verdict**: **COHERENT & MINIMAL (NO BLOCKERS)**

---

## 1. High-Altitude Architectural Assessment

The Stage 7 remediation successfully grounded `PROJECT.md`:
- **Hype Elimination**: Purged ungrounded claims ("bank-grade security", "256-bit encrypted authentication screen", "production-ready") and replaced them with factual technical specifications.
- **Structural Integrity**: Formal Data Models (Section 3), API Specifications (Section 4), and Security Architecture (Section 5) now define clear system interfaces.
- **Topological Truth**: Honestly documents the single React SPA deployment and client-side hostname detection (`domain.js`) without claiming network perimeter isolation.

No speculative bloat or unnecessary complexity was introduced. The document now functions as a viable engineering specification.

---

## 2. Residual Findings & Recommended Minor Adjustments

### 🟡 Major Residuals
1. **Phantom `admin_sessions` Table in Diagram**:
   - The Section 1 ASCII diagram displays `• admin_sessions` under Supabase PostgreSQL, but Section 5 specifies a stateless HMAC-SHA256 session token validated entirely in-memory.
   - *Adjustment*: Remove `• admin_sessions` from the diagram to prevent confusion between stateful database sessions and stateless cryptographic tokens.
2. **Ingestion Worker Topology Alignment**:
   - The Section 1 diagram depicts the Ingestion Worker as an independent external service, while the repository layout and Dockerfile co-locate it with `backend/app.py`.
   - *Adjustment*: Clarify that the crawler runs as an asynchronous background worker process (with a minimum $\ge 1\text{GB}$ RAM container allocation recommendation for Playwright Chromium).
3. **Explicit Threat Model Protection for Administrative Read Endpoints**:
   - Section 5 mentions that "Mutation routes require valid HMAC token verification".
   - *Adjustment*: Explicitly state that **all** `/api/admin/*` routes (including `GET /api/admin/leads` which exports buyer PII) strictly enforce HMAC Bearer token validation.

### 🟢 Nit Residuals
4. **Token Issuance Authority**: Clarify that the frontend does not mint HMAC tokens; it sends credentials to `POST /api/admin/login`, which returns the signed token.
5. **HTTP 202 Accepted on Scrape Trigger**: Update Section 4.2 response code for `POST /api/scrape/trigger` from `200 OK` to `202 Accepted` to match REST standards and actual `backend/app.py` implementation.
6. **Schema Enum Literal Alignment**: Align Section 3.1 enum naming with Pydantic model literals (`PHYSICAL`, `SYMBOLIC`).

---

## 3. Summary Scorecard

| Criterion | Evaluation | Status |
| :--- | :--- | :--- |
| **Stage 7 Additions Verification** | Data models, API specs, and threat model verified. | **PASSED** |
| **YAGNI / Anti-Overengineering** | Zero speculative services or excessive middleware added. | **PASSED** |
| **Architectural Coherence** | Client-side routing and backend REST contracts align. | **PASSED** |
| **Residual Risk** | 3 minor synchronization items, 0 blockers. | **PASSED** |
