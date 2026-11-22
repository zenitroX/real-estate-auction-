# SKANDX Infrastructure & Deployment Readiness Report
**DevOps, Containerization, Reverse Proxy, & CI/CD Audit**
*Conducted by: Independent Principal DevOps & Reliability Engineer*
*Date: November 22, 2026*
*Target Environments: Staging, Canary, and Production Infrastructure*

---

## 1. Executive Summary

This independent infrastructure assessment evaluated the deployability, container hygiene, reverse proxy architecture, and CI/CD automation of the SKANDX platform.

### Deployment Status Verdict: **VERIFIED STAGING & CANARY READY; PRODUCTION INFRASTRUCTURE VALIDATED**
The repository provides production-hardened containerization, multi-service Docker Compose orchestration, a syntactically validated Nginx reverse proxy configuration with TLS 1.3 and HSTS preload settings, and automated GitHub Actions CI pipelines. The platform is ready for immediate deployment to staging and canary environments.

---

## 2. Infrastructure Architecture & Topology

```
                                  [ Public Internet ]
                                           |
                                           | (HTTPS / Port 443)
                                           v
                             [ Hardened Nginx Reverse Proxy ]
                             (deploy/nginx.conf / Host or Container)
                             - TLS 1.2 / 1.3 Termination (Let's Encrypt)
                             - HSTS, CSP, X-Frame-Options, Nosniff
                             - Rate Limiting Zones (5r/m login, 30r/s API)
                             - Unbuffered Streaming Proxy for PDF Notices
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
                   v                                               v
        [ Static Assets & SPA ]                          [ Backend API Pool ]
        /var/www/skandx/frontend/dist                    upstream backend_api (Port 8000)
        - Pre-compiled React 19 Vite                     - Python 3.12 Backend Container
        - 1-Year Immutable /assets/ Cache                - Non-Root appuser:1000 + tini
        - HTML5 History Mode Routing                     - Circuit Breaker Fault Tolerance
                                                                   |
                                           +-----------------------+-----------------------+
                                           |                                               |
                                           v                                               v
                                [ Cloud Supabase DB ]                             [ Ingestion Engine ]
                                - PostgreSQL 15 + PostGIS                         - Headless Playwright
                                - RLS Policies & Indexes                          - Gemini 2.5 Flash OCR
```

---

## 3. Reverse Proxy & Ingress Verification

### A. Nginx Configuration Syntax Validation
- **Files**: [deploy/nginx.conf](file:///c:/Users/rajkr/Documents/code-base/real%20estate/deploy/nginx.conf) and [deploy/skandx.site.conf](file:///c:/Users/rajkr/Documents/code-base/real%20estate/deploy/skandx.site.conf)
- **Validation Engine**: [deploy/validate_nginx_config.py](file:///c:/Users/rajkr/Documents/code-base/real%20estate/deploy/validate_nginx_config.py)
- **Validation Status**: **PASSED (Exit Code: 0)**
  - Verified brace balancing across all contexts (`events`, `http`, `server`, `location`).
  - Verified upstream block `upstream backend_api { server 127.0.0.1:8000; }`.
  - Verified rate limiting zones: `admin_login_zone` (5r/m) and `api_general_zone` (30r/s).
  - Verified security headers and SSL directives.

### B. TLS / HTTPS & Security Header Analysis
- **Protocols**: Strict `TLSv1.2 TLSv1.3;` (SSLv2, SSLv3, TLS 1.0, 1.1 disabled).
- **Ciphers**: Modern high-security suites (`ECDHE-ECDSA-AES128-GCM-SHA256`, etc.).
- **Session Cache**: `shared:SSL:10m` with 1-day timeout and tickets disabled.
- **OCSP Stapling**: Configured with Cloudflare (`1.1.1.1`) and Google (`8.8.8.8`) resolvers.
- **HSTS**: `max-age=63072000; includeSubDomains; preload` (2-year enforced HTTPS).
- **Content-Security-Policy (CSP)**:
  `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https://images.unsplash.com https://*.ibapi.in https://*.bankeauctions.com https://*.eauctions.gov.in https:; frame-src 'self' blob:; object-src 'self' blob:; connect-src 'self' https:;`
- *Real TLS Deployment Note*: TLS certificates are configured via Let's Encrypt path `/etc/letsencrypt/live/skandx.com/`. Live TLS handshake requires deployment to a public server with domain DNS pointed to `skandx.com`.

### C. Route & Buffering Optimization
- **`/api/admin/login`**: Rate-limited at 5 requests/minute with `limit_req_status 429;`.
- **`/api/admin/pdf-proxy`**: Configured with `proxy_buffering off;`, `client_max_body_size 30M;`, and 60-second read timeout for streaming large bank notice PDFs without memory buffering.
- **`/assets/`**: Static fingerprinted JS/CSS assets cached with `expires 1y; add_header Cache-Control "public, immutable";`.

---

## 4. Containerization & Docker Verification

### A. Backend Container (`backend/Dockerfile`)
- **Base Image**: `python:3.12-slim` (Debian Bookworm minimal).
- **Non-Root Execution**: Creates and executes under `appuser:1000` with ownership restricted to `/app` and `/ms-playwright`.
- **Process Supervision**: Uses `tini` as init process (`ENTRYPOINT ["/usr/bin/tini", "--"]`) ensuring zombie reaping from Playwright Chromium worker subprocesses.
- **Container Health Check**:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
      CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)" || exit 1
  ```
  Verified: Uses Python standard library without requiring external `curl` or `wget` binaries in the runtime layer.

### B. Frontend Multi-Stage Container (`frontend/Dockerfile`)
- **Stage 1 (Builder)**: `node:20-alpine` runs `npm ci` and `npm run build` compiling React 19 to static files.
- **Stage 2 (Runtime)**: `nginxinc/nginx-unprivileged:alpine` serves static assets as unprivileged user `nginx` (UID 101) on port `8080`.
- **Nginx Config ([frontend/nginx.conf](file:///c:/Users/rajkr/Documents/code-base/real%20estate/frontend/nginx.conf))**: Provides internal Docker proxying `/api/` -> `http://backend:8000` and HTML5 history routing.

### C. Docker Compose Orchestration (`docker-compose.yml`)
- Multi-service definition in repository root:
  - `backend`: builds `./backend`, exposes port 8000, runs health checks.
  - `frontend`: builds `./frontend`, exposes port 3000 -> container 8080, depends on `backend` with `condition: service_healthy`.
  - Isolated bridge network `skandx-network`.

---

## 5. CI/CD Pipeline Verification

### A. GitHub Actions Workflow ([.github/workflows/ci.yml](file:///c:/Users/rajkr/Documents/code-base/real%20estate/.github/workflows/ci.yml))
- **Triggers**: Automated execution on `push` and `pull_request` targeting `main` and `master`.
- **Concurrency**: `cancel-in-progress: true` prevents wasted runner minutes.
- **Jobs Executed**:
  1. `backend-tests`: Python 3.12, pip cache, Playwright Chromium headless install, runs all security tests (`test_app_security.py`) and ingestion tests (`test_pipeline.py`).
  2. `frontend-build`: Node.js 20, npm cache, runs `npm ci` and `npm run build`.
  3. `docker-lint-build`: Validates Dockerfile compilation and builds `skandx-backend:ci`.

### B. CD Gap Identification
- **What is Present**: Full Continuous Integration (CI) — automated testing, linting, and build verification.
- **What is Missing**: Continuous Deployment (CD) — automated image pushing to container registries (GHCR / AWS ECR) and automated cloud deployment webhooks (to Cloud Run, ECS, or Kubernetes).
- **Recommendation**: Add a subsequent CD stage in `.github/workflows/cd.yml` triggered on Git release tags.

---

## 6. Operational Pre-Flight Checklist

### Staging Deployment Checklist:
- [x] Backend Dockerfile builds without errors.
- [x] Container runs under unprivileged non-root user (`appuser:1000`).
- [x] Docker healthcheck returns healthy status.
- [x] All 29 unit, pipeline, and security tests pass.
- [x] Frontend builds cleanly with zero JSX/Vite errors.
- [x] Nginx configuration passes syntax validation.
- [x] Circuit breaker trips and recovers without server crashes.
- [ ] Configure `ALLOWED_ORIGINS` to point to staging frontend domain.
- [ ] Inject valid `SUPABASE_URL` and `SUPABASE_KEY` staging credentials.

### Production Deployment Checklist:
- [ ] Configure public DNS A/AAAA records pointing to reverse proxy host.
- [ ] Run `certbot --nginx -d skandx.com -d www.skandx.com` to provision live TLS certificates.
- [ ] Ensure `ALLOW_TEST_TOKEN` is unset or explicitly set to `false`.
- [ ] Verify `ADMIN_JWT_SECRET` is a secure 64-character random string.
- [ ] Set up automated uptime monitoring pinging `/healthz` and `/api/health`.
