# SKANDX Staging Deployment Guide

**Document ID:** `ENG-OPS-001`  
**Classification:** Internal Engineering & Operations  
**Target Environment:** Staging / Pre-Production Validation  
**Last Updated:** November 2026  
**Audience:** DevOps Engineers, Site Reliability Engineers, Platform Architects

---

## 1. Overview & Architecture

The SKANDX staging environment mirrors production topology to validate application behavior, external integrations (Supabase PostgreSQL, Gemini OCR, Bank Auction Portals), and security boundaries before production promotion.

```
                           +----------------------------------------+
                           |   DNS: staging.skandx.com              |
                           |   DNS: staging-admin.skandx.com        |
                           +-------------------+--------------------+
                                               |
                                               v
                           +----------------------------------------+
                           |  Edge / Reverse Proxy (Nginx / Cloud)  |
                           |  TLS 1.2/1.3 Termination               |
                           |  Rate Limiting, HSTS, WAF              |
                           +-------------------+--------------------+
                                               |
                     +-------------------------+-------------------------+
                     |                                                   |
                     v (Port 3000 -> :8080)                              v (Port 8000)
    +----------------------------------+               +----------------------------------+
    | Container: skandx-frontend       |               | Container: skandx-backend        |
    | Non-root user: nginx (UID 101)   |               | Non-root user: skandx (UID 10001)|
    | Alpine 3.19 + Nginx Unprivileged |               | Python 3.12 Slim                 |
    | SPA Static Asset Serving         |               | ThreadingHTTPServer Core Engine  |
    +----------------------------------+               +-----------------+----------------+
                                                                         |
                                                                         v
                                                       +----------------------------------+
                                                       | Staging Supabase PostgreSQL      |
                                                       | - auction_properties             |
                                                       | - customer_leads                 |
                                                       | - admin_roles & audit_logs       |
                                                       +----------------------------------+
```

---

## 2. Environment Configuration Matrix

The staging environment **must never inherit development defaults or fallbacks**. Create an isolated `.env.staging` file in the project root:

```ini
# ==============================================================================
# SKANDX STAGING ENVIRONMENT CONFIGURATION (.env.staging)
# ==============================================================================

# Core Application Gating
ENVIRONMENT=staging
PORT=8000
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Security & Token Bypass Restrictions
# CRITICAL: Must be false to block "skandx-test-token-bypass" in staging
ALLOW_TEST_TOKEN=false

# Administrative Authentication Credentials
# In staging/production, backend will return HTTP 503 if these are empty or default
ADMIN_EMAIL=staging-admin@skandx.com
ADMIN_PASSWORD=ReplaceWithStrongStagingPassword2026!
ADMIN_JWT_SECRET=ReplaceWithSecureRandomHexKey64CharactersLongForStagingHMAC2026

# Database & External Services (Isolated Staging Project)
SUPABASE_URL=https://staging-project-ref.supabase.co
SUPABASE_KEY=staging_service_role_key_secret_here
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key_secret_here

# Ingestion & AI Services
GEMINI_API_KEY=staging_gemini_api_key_here
SCRAPER_PROXY_URL=https://staging-proxy.skandx.internal:8080

# CORS Whitelist (Explicit Origins Only)
CORS_ALLOWED_ORIGINS=https://staging.skandx.com,https://staging-admin.skandx.com,http://localhost:3000
```

> [!CAUTION]
> Never populate `.env.staging` with production database URLs or production service role keys. Staging customer lead testing must occur on isolated staging database instances.

---

## 3. Pre-Flight Deployment Checklist

Before initiating container orchestration, verify all prerequisite criteria:

| Checkpoint | Requirement | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Docker Engine** | Version $\ge 24.0.0$ | `docker --version` | `VERIFIED` |
| **Compose Plugin** | Compose v2 installed | `docker compose version` | `VERIFIED` |
| **Non-Root Images** | UID != 0 in Dockerfile | Inspect `backend/Dockerfile` and `frontend/Dockerfile` | `VERIFIED` |
| **Bypass Disabled** | `ALLOW_TEST_TOKEN=false` | Inspect `.env.staging` | `VERIFIED` |
| **DB Migrations** | 001, 002, 003 applied | Run verification queries on staging DB | `VERIFIED` |
| **Port Conflicts** | 8000 and 3000 free | `netstat -ano \| findstr :8000` | `VERIFIED` |

---

## 4. Staging Database Migration Execution

Apply migrations sequentially against the staging Supabase PostgreSQL database using the `psql` CLI or Supabase Management Console:

### Step 1: Apply Initial Schema (`001_create_auction_properties.sql`)
```bash
psql "postgresql://postgres:[PASSWORD]@[STAGING_HOST]:5432/postgres" \
  -f backend/migrations/001_create_auction_properties.sql
```
*Creates `auction_properties` table with asset fingerprints, geospatial indexes, and full-text search.*

### Step 2: Apply Customer Leads Schema (`002_create_customer_leads.sql`)
```bash
psql "postgresql://postgres:[PASSWORD]@[STAGING_HOST]:5432/postgres" \
  -f backend/migrations/002_create_customer_leads.sql
```
*Creates `customer_leads` table, indexes on `(phone, property_id)`, and RLS policies for anonymous inquiry submission.*

### Step 3: Apply Admin Roles & Audit Schema (`003_create_admin_roles_and_audit.sql`)
```bash
psql "postgresql://postgres:[PASSWORD]@[STAGING_HOST]:5432/postgres" \
  -f backend/migrations/003_create_admin_roles_and_audit.sql
```
*Creates `admin_roles`, `audit_logs`, and immutable audit trail triggers.*

### Step 4: Validate Migration State
```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```
*Expected Tables: `admin_roles`, `auction_properties`, `audit_logs`, `customer_leads`.*

---

## 5. Container Orchestration & Launch

Launch the staging multi-container stack using Docker Compose with the staging environment file:

```bash
# 1. Pull base images and build with build-kit optimization
docker compose --env-file .env.staging build --no-cache

# 2. Boot services in detached mode
docker compose --env-file .env.staging up -d

# 3. Verify container lifecycle and health checks
docker compose --env-file .env.staging ps
```

Expected output:
```text
NAME                IMAGE               COMMAND                  SERVICE             CREATED             STATUS                    PORTS
skandx-backend      skandx-backend      "python -u app.py"       backend             10 seconds ago      Up 9 seconds (healthy)    0.0.0.0:8000->8000/tcp
skandx-frontend     skandx-frontend     "/docker-entrypoint.…"   frontend            10 seconds ago      Up 9 seconds              0.0.0.0:3000->8080/tcp
```

---

## 6. Post-Deployment Smoke Tests

Execute these validation requests against the staging endpoint:

### 1. Health & Readiness Probe
```bash
curl -i http://localhost:8000/api/health
```
**Verification:** HTTP 200 OK, JSON response with `"status": "healthy"` and `"circuit_breaker": "CLOSED"`.

### 2. Admin Security Verification (Bypass Disabled)
```bash
curl -i -H "Authorization: Bearer skandx-test-token-bypass" http://localhost:8000/api/admin/properties
```
**Verification:** HTTP 401 Unauthorized (must reject bypass token when `ENVIRONMENT=staging`).

### 3. Rate Limiter Validation
```bash
# Execute 6 rapid requests to login
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/admin/login \
    -H "Content-Type: application/json" \
    -d '{"email":"bad@skandx.com","password":"wrong"}'
done
```
**Verification:** First 5 return `401 Unauthorized`; 6th returns `429 Too Many Requests` with `Retry-After: 60`.

### 4. Cache-Control Header Audit
```bash
curl -i http://localhost:8000/api/admin/leads -H "Authorization: Bearer VALID_STAGING_TOKEN"
```
**Verification:** Response must contain `Cache-Control: no-store, no-cache, must-revalidate, private`.

---

## 7. Rollback & Teardown Procedures

If post-deployment smoke tests fail:

```bash
# 1. Stop staging containers immediately
docker compose --env-file .env.staging down

# 2. Revert staging database if migration rolled back
# (Restore staging snapshot via Supabase Console)

# 3. Clean untagged artifacts
docker system prune -f
```
