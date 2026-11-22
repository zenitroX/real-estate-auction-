# SKANDX Staging Functional Test Results

**Document ID:** `ENG-TEST-007`  
**Classification:** Quality Assurance & Functional Reliability Verification  
**Evaluation Date:** November 2026  
**Auditor:** Principal Reliability Engineer & Full-Stack QA Lead  

---

## 1. Test Overview & Execution Context

Functional operational testing was executed against the live backend server (`SilentHandler` derived from `ApiRequestHandler`) running in staging mode on loopback socket. All tests exercised real HTTP requests, headers, and serialization logic.

- **Target Engine:** Python 3.12 `http.server.ThreadingHTTPServer`
- **Execution Harness:** `scripts/test_staging_operations.py`
- **Environment:** `ENVIRONMENT=staging`, `ALLOW_TEST_TOKEN=false`
- **Total Functional Tests:** 7
- **Passed:** 7 (100%)
- **Failed:** 0 (0%)

---

## 2. Functional Test Verification Matrix

| Test ID | Endpoint / Feature | Request Details & Parameters | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FUNC-01** | Auction Listing Retrieval | `GET /api/auctions` | HTTP 200, array of verified properties | HTTP 200, 5 verified auction properties returned ($86.8\text{ms}$) | **`VERIFIED`** |
| **FUNC-02** | Auction Query Filtering | `GET /api/auctions?limit=2` | HTTP 200, length restricted to $\le 2$ | HTTP 200, query string parsed correctly ($2.32\text{ms}$) | **`VERIFIED`** |
| **FUNC-03** | Buyer Enquiry Lead Capture | `POST /api/contact`<br>Body: valid phone & property | HTTP 201, `status: success`, unique `leadId` | HTTP 201, generated `lead-1795358434338` ($24.9\text{ms}$) | **`VERIFIED`** |
| **FUNC-04** | Admin Authentication | `POST /api/admin/login`<br>Body: staging credentials | HTTP 200, signed HMAC token | HTTP 200, valid token `skandx-adm-...` ($2.32\text{ms}$) | **`VERIFIED`** |
| **FUNC-05** | Lead Management Feed | `GET /api/admin/leads?limit=10`<br>Header: `Bearer <token>` | HTTP 200, lead feed with total count | HTTP 200, 40 leads returned, newly submitted lead present ($21.47\text{ms}$) | **`VERIFIED`** |
| **FUNC-06** | Property Status Verification | `POST /api/admin/properties/verify`<br>Body: `PROP-STG-404`, status `PUBLISHED` | HTTP 200, cache invalidated, status updated | HTTP 200, persisted status `PUBLISHED` ($18.53\text{ms}$) | **`VERIFIED`** |
| **FUNC-07** | Offline Fallback Durability | `POST /api/contact`<br>CircuitBreaker state `OPEN` | HTTP 201, zero silent drop, written to disk WAL | HTTP 201, lead preserved in `data/leads.jsonl` without DB call | **`VERIFIED`** |

---

## 3. Deep Dive Test Findings

### 3.1 Lead Capture Durability & Offline Replay
When the backend is disconnected from Supabase (or when `circuit_breaker.state == CircuitBreaker.OPEN`):
- `backend/app.py` writes the lead immediately to `backend/data/leads.jsonl` using a thread-safe `_leads_lock`.
- The circuit breaker prevents socket timeouts by bypassing the remote Supabase API call.
- The client receives an immediate `HTTP 201 Created` with a unique lead ID.
- **Result:** $0\%$ lead discard under database network failure.

### 3.2 Cache Invalidation on Admin Review
- When an administrator approves an auction via `POST /api/admin/properties/verify`, the backend updates both the disk storage and executes `_cache["data"] = None`.
- The subsequent read to `GET /api/auctions` rehydrates fresh data without requiring server restart.

---

## 4. Conclusion
All core operational user journeys (browsing, inquiry submission, administrator login, verification, and offline degradation) are **`VERIFIED`** and functionally reliable.
