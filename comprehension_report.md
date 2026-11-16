# Comprehension Test Report (Stage 6)

**Target Document**: [PROJECT.md](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md)  
**Evaluator**: Naive Reader (`egm-comprehension` persona)  
**Review Scope**: Lines 1–161 (Autonomous review without external context)

---

### Paraphrase First

#### What this proposes
This document proposes "SKANDX", an Indian real estate discovery and lead acquisition platform that aggregates distressed bank auction properties for public buyers while centralizing inquiries through a managed customer desk. It defines an automated ingestion workflow where automated crawlers scrape partner bank portals, extract auction circular metadata using Gemini 2.5 Flash multimodal vision OCR, and feed records into an administrative verification queue before publishing them to the public marketplace. It also specifies a unified single-page React frontend that serves both public buyers and staff administrators from a single deployment by isolating views based on domain hostnames (`skandx.com` vs. `admin.skandx.com`).

#### How the existing system works, per this document
According to the document, the system is composed of a React 19 SPA frontend and a Python 3.12 backend API (`app.py` running on port 8000) that interacts with a Supabase PostgreSQL database (`auction_properties`) alongside local JSON fallback storage. In the frontend, hostname inspection directs requests to either the public property catalog or an admin authentication gate, with local development overrides supporting hash (`/#admin`) and query parameter (`/?portal=admin`) routing. In the backend, bank crawlers (Baanknet, IBAPI) extract auction notices into a `PENDING_REVIEW` queue in Supabase, where authenticated administrators review, edit, approve, or reject listings before they appear on the customer marketplace with a `✓ Verified` badge. Public inquiries submitted via the customer "Contact" modal are recorded as leads with status tracking on an admin lead desk.

---

### Comprehension Findings

#### 1. 🔴 Blocker: Client-Side "Subdomain Isolation" and "Bank-Grade Security" Architectural Contradiction
* **Affected Scope:** [PROJECT.md#L7-L50](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L7-L50), [PROJECT.md#L66-L68](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L66-L68), [PROJECT.md#L140-L141](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L140-L141), [PROJECT.md#L151-L161](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L151-L161)
* **Discrepancy Description & Rationale:**
  * **Mechanism:** Section 1 promises "bank-grade security, access control, and clean brand separation" via "subdomain isolation" where "No admin controls exposed" and "admin features and unverified notices are completely hidden" on `skandx.com`. However, Section 4 and Section 5 specify that `admin.skandx.com` and `skandx.com` map to the exact same deployment bundle (`Both route to the same app build`), and that admin views are accessible on the public domain simply by loading `/#admin` or `/?portal=admin`. Furthermore, the document never specifies any backend session validation, JWT enforcement, or role-based access control (RBAC) protecting the administrative REST endpoints (`/api/admin/properties`, `/api/scrape/trigger`).
  * **Concrete Risk:** A new engineer reading this will assume physical/network subdomain isolation and bank-grade isolation are in place. In reality, all admin JavaScript components, state, and endpoints are bundled directly into the public client bundle. If backend endpoints do not validate cryptographically signed tokens regardless of hostname, any visitor can manipulate client-side routing or call administrative mutation endpoints directly.

#### 2. 🔴 Blocker: Undefined Crawler Execution, Streaming Architecture, and Concurrency Model
* **Affected Scope:** [PROJECT.md#L25](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L25), [PROJECT.md#L77-L78](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L77-L78), [PROJECT.md#L88-L95](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L88-L95)
* **Discrepancy Description & Rationale:**
  * **Mechanism:** The document states that the admin portal features a "Playwright crawler live stream" and a "live trigger button and execution log terminal for partner bank crawlers", managed by `/api/scrape/trigger` on the Python backend server (`app.py`, port 8000). However, the document does not specify the runtime execution model or streaming transport protocol.
  * **Concrete Risk:** Playwright crawlers are resource-heavy, long-running browser processes. Executing them directly within a synchronous or threaded REST API worker will block HTTP request loops or time out gateway connections. Moreover, the document leaves completely undefined how log outputs are streamed to the browser (e.g., WebSockets, Server-Sent Events, or polling), and how concurrent crawl triggers are prevented or queued. An engineer cannot implement or maintain this pipeline without knowing the asynchronous task/process architecture.

#### 3. 🟡 Major: Undefined Storage and Document Lifecycle for Raw Scraped Notices (PDFs / Images)
* **Affected Scope:** [PROJECT.md#L39-L42](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L39-L42), [PROJECT.md#L69-L73](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L69-L73), [PROJECT.md#L90-L95](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L90-L95)
* **Discrepancy Description & Rationale:**
  * **Mechanism:** The workflow specifies that Gemini 2.5 Flash Vision OCR extracts notices into a `PENDING_REVIEW` queue, where an admin uses "[Edit Extracted Details]" to "correct OCR text, dates, or prices before approving". However, the document mentions only the PostgreSQL table `auction_properties` and provides no definition of where the underlying source files (scanned circulars, PDFs, or photos) are stored.
  * **Concrete Risk:** For an administrator to verify or correct OCR-extracted data, they must visually inspect the original auction notice. If the document does not specify blob/object storage (e.g., Supabase Storage bucket, AWS S3, or local disk volume), developers cannot know where raw documents reside, how URLs are generated, or how the admin UI displays the source notice alongside the edit form.

#### 4. 🟡 Major: Ambiguous Source of Truth: Supabase Cloud PostgreSQL vs. Local JSON Files
* **Affected Scope:** [PROJECT.md#L39-L42](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L39-L42), [PROJECT.md#L96](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L96), [PROJECT.md#L106-L109](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L106-L109)
* **Discrepancy Description & Rationale:**
  * **Mechanism:** The document depicts Supabase PostgreSQL as the primary persistence layer for `auction_properties`. Concurrently, the repository layout introduces `backend/data/ # Local fallback snapshots & leads.json` and `frontend/public/ # Offline fallback data & assets`.
  * **Concrete Risk:** The document does not define the failover or synchronization conditions between Supabase and the local JSON files. For example, when a lead is captured via `/api/contact`, does the server write to Supabase, append to `leads.json`, or both? If Supabase is unreachable, does the system operate in read-only mode or silently degrade to local disk? A fresh reader cannot determine the authoritative source of truth or state persistence lifecycle.

#### 5. 🟡 Major: Undefined Domain Jargon and External Integration Targets (SARFAESI, Baanknet, IBAPI)
* **Affected Scope:** [PROJECT.md#L3](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L3), [PROJECT.md#L92](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L92)
* **Discrepancy Description & Rationale:**
  * **Mechanism:** The document introduces several domain-specific legal terms and portal targets without definition or documentation links:
    1. **SARFAESI** ([L3](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L3)): Used without defining the act, its legal implications, or the specialized schema requirements of Indian bank distress sales (e.g., Reserve Price, Earnest Money Deposit [EMD], physical vs. symbolic possession, auction cutoff dates).
    2. **Baanknet & IBAPI** ([L92](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L92)): Introduced as target crawlers without clarifying whether they are public auction aggregators (e.g., IBAPI - Indian Banks Auctions Mortgaged Properties Information Portal), proprietary partner APIs, or mock targets.
  * **Concrete Risk:** A developer unfamiliar with Indian banking regulations has no context on what fields are legally mandated, how crawler sessions interface with these portals (e.g., bot protection, CAPTCHAs, session cookies), or what legal liabilities exist when scraping these notices.

#### 6. 🟢 Nit: Imprecise Security Terminology ("256-bit encrypted authentication screen")
* **Affected Scope:** [PROJECT.md#L67](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L67)
* **Discrepancy Description & Rationale:**
  * **Mechanism:** Section 2.B.1 describes the admin gate as a "256-bit encrypted authentication screen requiring admin credentials".
  * **Concrete Risk:** In modern web security, an "authentication screen" is not itself 256-bit encrypted; transport layer security (TLS) negotiates cipher suites (e.g., AES-256-GCM), while credentials are hashed (e.g., bcrypt, Argon2) on the server. Phrasing this as a "256-bit encrypted authentication screen" sounds like non-technical marketing copy and obscures whether client-side payload encryption is actually implemented or if standard HTTPS is being described.

#### 7. 🟢 Nit: Unclarified Intermediary Role and Routing of Recovery Officer Contact Details
* **Affected Scope:** [PROJECT.md#L59-L61](file:///c:/Users/rajkr/Documents/code-base/real%20estate/PROJECT.md#L59-L61)
* **Discrepancy Description & Rationale:**
  * **Mechanism:** Section 2.A.2 states that "Raw officer phone numbers are shielded from public spam" and replaced with a central toll-free hotline and WhatsApp desk.
  * **Concrete Risk:** The document does not define who the "officer" is (presumably the bank's Authorized Officer under SARFAESI rules), where these numbers are preserved in the schema, or how the central SKANDX desk relays buyer inquiries and site inspection bookings back to the bank's actual authorized officers once a lead transitions through the Buyer Leads Desk.
