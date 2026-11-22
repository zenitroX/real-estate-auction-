# SKANDX Production Reverse Proxy & Web Infrastructure Deployment Guide

## Architecture Overview

This deployment infrastructure configures a production-hardened **Nginx** reverse proxy acting as the TLS termination, rate-limiting, and static asset gateway for **SKANDX** (India Bank Property Auction Discovery Platform).

```
                      +-----------------------------------+
                      |      Client / Browser / CDN       |
                      +-----------------+-----------------+
                                        |
                      HTTPS (443) / HTTP (80) [Auto 301]
                                        |
                                        v
                      +-----------------------------------+
                      |       Nginx Reverse Proxy         |
                      |   - TLS 1.2 / 1.3 Termination     |
                      |   - Rate Limiting Zones           |
                      |   - Security Headers (HSTS, CSP)  |
                      |   - Slowloris & DoS Protection    |
                      +---------+---------------+---------+
                                |               |
             Static Assets &    |               | API Reverse Proxy
             Vite SPA Fallback  |               | (Keepalive Pool)
                                v               v
            +---------------------+   +---------------------+
            | /var/www/skandx/    |   | FastAPI Backend     |
            | frontend/dist       |   | 127.0.0.1:8000      |
            +---------------------+   +---------------------+
```

---

## Key Features & Hardening Specifications

1. **Dual Upstream Keepalive Pool**:
   - `upstream backend_api` mapped to `127.0.0.1:8000` with `max_fails=3 fail_timeout=10s` and 32 pooled keepalive connections.
2. **ACME HTTP-01 Let's Encrypt Pass-through**:
   - Automated 301 HTTPS redirects on port 80 for all hostnames, preserving `/.well-known/acme-challenge/` for zero-downtime certificate renewal.
3. **Modern SSL/TLS Protocols & Ciphers**:
   - TLSv1.2 & TLSv1.3 exclusively. Obsolete protocols (SSLv2/v3, TLS 1.0, 1.1) disabled.
   - High-security modern ECDHE/AES-GCM/DHE cipher suites without weak or legacy 3DES/RC4.
   - 10MB SSL session cache (~160,000 sessions) with 24h lifetime and ticket disabled for forward secrecy.
   - OCSP Stapling enabled with Cloudflare/Google DNS resolvers.
4. **Defense-in-Depth Security Headers**:
   - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (HSTS).
   - `X-Frame-Options: SAMEORIGIN` (prevents external clickjacking while allowing internal notice frames).
   - `X-Content-Type-Options: nosniff`.
   - `Referrer-Policy: strict-origin-when-cross-origin`.
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
   - `Content-Security-Policy`: Custom tuned for React/Vite builds, font CDNs, bank auction portals (`ibapi.in`, `bankeauctions.com`), and `blob:` object frames for the PDF notice viewer.
5. **Multi-Tier Rate Limiting**:
   - `/api/admin/login`: Restricted to **5 requests per minute** with burst of 3 and `nodelay` (`zone=admin_login_zone:10m`). Returns `429 Too Many Requests`.
   - `/api/`: Public API bounded to **30 requests per second** with burst of 20 (`zone=api_general_zone:10m`).
   - Connection Limiting: Maximum 50 concurrent connections per client IP address.
6. **Dedicated Streaming PDF Proxy Route**:
   - `/api/admin/pdf-proxy`: Buffering disabled (`proxy_buffering off;`), 30MB client payload limit (`client_max_body_size 30M;`), and 60-second read timeouts for real-time document streaming without Nginx memory exhaustion.
7. **DoS & Slowloris Mitigation**:
   - Header timeout: 10s.
   - Body timeout: 10s.
   - Keepalive timeout: 65s.
   - Send timeout: 10s.
   - Version disclosure disabled (`server_tokens off;`).

---

## Prerequisites

- **Operating System**: Ubuntu 22.04 LTS / 24.04 LTS or Debian 11 / 12 (Bookworm).
- **Network & DNS**: Public IPv4/IPv6 address with DNS `A` / `AAAA` records pointing `skandx.com` and `www.skandx.com` to the server.
- **Port Access**: Ports 80 and 443 open on cloud security groups / firewall (UFW).

---

## Deployment Walkthrough

### Step 1: Install Nginx, Certbot & Core Dependencies

Run on the target Ubuntu/Debian server:

```bash
# Update package repositories
sudo apt update && sudo apt upgrade -y

# Install Nginx, Certbot, and Python Certbot Nginx plugin
sudo apt install -y nginx certbot python3-certbot-nginx curl ufw

# Configure UFW firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### Step 2: Establish File System Directories & Permissions

Create the webroot directories for the frontend build and the ACME webroot challenge:

```bash
# Create directory for the React SPA distribution
sudo mkdir -p /var/www/skandx/frontend/dist

# Create ACME challenge webroot
sudo mkdir -p /var/www/certbot

# Set proper ownership and permissions
sudo chown -R www-data:www-data /var/www/skandx
sudo chown -R www-data:www-data /var/www/certbot
sudo chmod -R 755 /var/www/skandx
sudo chmod -R 755 /var/www/certbot
```

### Step 3: Deploy Frontend Build

On your local workstation or CI/CD runner:

```bash
# Build production React assets
cd frontend
npm install
npm run build

# Deploy assets to the server (replace user@server_ip with your target host)
rsync -avz --delete dist/ user@server_ip:/tmp/dist/

# On the server, move to the target directory:
sudo cp -r /tmp/dist/* /var/www/skandx/frontend/dist/
sudo chown -R www-data:www-data /var/www/skandx/frontend/dist/
```

### Step 4: Obtain Let's Encrypt TLS Certificate

Before loading the HTTPS configuration, obtain free SSL/TLS certificates via Certbot.

#### Option A: Automatic Nginx Plugin (Recommended)
```bash
sudo certbot --nginx -d skandx.com -d www.skandx.com
```

#### Option B: Webroot Verification (Zero Downtime)
If bootstrapping on port 80 first:
```bash
sudo certbot certonly --webroot -w /var/www/certbot -d skandx.com -d www.skandx.com
```

Certificates will be saved to:
- Certificate: `/etc/letsencrypt/live/skandx.com/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/skandx.com/privkey.pem`
- Chain: `/etc/letsencrypt/live/skandx.com/chain.pem`

---

### Step 5: Install Nginx Configuration

You can deploy the configuration using either the **Monolithic** method (`nginx.conf`) or the **Modular** method (`sites-available`).

#### Method 1: Modular Site Configuration (Standard Ubuntu/Debian)

1. Copy `deploy/skandx.site.conf` to `/etc/nginx/sites-available/skandx.conf`:
   ```bash
   sudo cp deploy/skandx.site.conf /etc/nginx/sites-available/skandx.conf
   ```
2. Enable the site and disable default site:
   ```bash
   sudo ln -sf /etc/nginx/sites-available/skandx.conf /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   ```

#### Method 2: Monolithic Configuration

If replacing the main server configuration:
```bash
# Backup existing nginx.conf
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak

# Deploy SKANDX nginx.conf
sudo cp deploy/nginx.conf /etc/nginx/nginx.conf
```

---

## Configuration Validation & Testing

### 1. Test Nginx Configuration Syntax
Run `nginx -t` to ensure all directives, SSL paths, and upstream definitions are valid:

```bash
sudo nginx -t
```
*Expected output:*
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 2. Apply Configuration (Zero Downtime Reload)
```bash
sudo systemctl reload nginx
```

### 3. Verify Systemd Service Status
```bash
sudo systemctl status nginx
```

To enable Nginx to start automatically upon server reboot:
```bash
sudo systemctl enable nginx
```

---

## Verification & Hardening Audit Runbook

### 1. Verify HTTP to HTTPS Automated 301 Redirect
```bash
curl -I http://skandx.com/
```
*Expected response:*
```http
HTTP/1.1 301 Moved Permanently
Location: https://skandx.com/
```

### 2. Verify Security Headers
```bash
curl -I https://skandx.com/
```
Verify the following response headers are present:
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy: ...`

### 3. Verify Admin Login Rate Limiting (5 requests/min)
Execute a rapid sequence of 5 POST requests to the login endpoint:
```bash
for i in {1..6}; do
  echo -n "Request $i: "
  curl -s -o /dev/null -w "%{http_code}\n" -X POST https://skandx.com/api/admin/login
done
```
*Expected behavior:*
- Requests 1 to 4: `200` / `401` / `422` (handled by backend).
- Request 5+: `429 Too Many Requests`.

### 4. Verify PDF Streaming Proxy Headers
```bash
curl -I https://skandx.com/api/admin/pdf-proxy?url=https%3A%2F%2Fwww.ibapi.in%2Fassets%2Fsample.pdf
```
Confirm streaming behavior: `X-Accel-Buffering: no` or upstream chunked transfer with no 504 gateway timeout.

---

## Automated SSL/TLS Certificate Renewal

Let's Encrypt certificates are valid for 90 days. Certbot installs a systemd timer that automatically checks and renews certificates twice daily.

1. **Verify Certbot Timer**:
   ```bash
   sudo systemctl status certbot.timer
   ```

2. **Simulate Renewal (Dry Run)**:
   ```bash
   sudo certbot renew --dry-run
   ```

3. **Renewal Hook**:
   Certbot automatically reloads Nginx upon renewal. You can verify or configure this hook in `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh`:
   ```bash
   #!/bin/bash
   systemctl reload nginx
   ```
   ```bash
   sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
   ```

---

## Systemd Service Management Reference

| Command | Action | Description |
|---|---|---|
| `sudo nginx -t` | Validate | Checks config syntax without affecting runtime |
| `sudo systemctl status nginx` | Status | Checks if Nginx daemon is active & view recent logs |
| `sudo systemctl reload nginx` | Hot-Reload | Gracefully reloads configuration without dropping active connections |
| `sudo systemctl restart nginx` | Restart | Full process restart (brief interruption) |
| `sudo systemctl stop nginx` | Stop | Shuts down Nginx web server |
| `sudo systemctl start nginx` | Start | Starts Nginx web server |
| `sudo journalctl -u nginx -f` | Follow Logs | Streams systemd logs for Nginx |

---

## Troubleshooting Guide

### 1. `502 Bad Gateway`
- **Cause**: Backend FastAPI server on `127.0.0.1:8000` is down or unreachable.
- **Check**:
  ```bash
  sudo systemctl status skandx-backend
  curl -I http://127.0.0.1:8000/api/health
  ```
- **Remedy**: Start or restart backend service:
  ```bash
  sudo systemctl restart skandx-backend
  ```

### 2. `429 Too Many Requests`
- **Cause**: IP exceeded the `admin_login_zone` (5 req/min) or `api_general_zone` (30 req/sec) rate limits.
- **Remedy**: Check `/var/log/nginx/access.log` to investigate client IP traffic. In test environments, increase the rate or burst in `/etc/nginx/sites-available/skandx.conf`.

### 3. `404 Not Found` on SPA Client Routes
- **Cause**: Nginx is looking for physical files for URLs like `/admin` or `/property/123`.
- **Check**: Verify `try_files $uri $uri/ /index.html;` exists in `location /`.

### 4. `SSL_ERROR_RX_RECORD_TOO_LONG`
- **Cause**: Nginx received plain HTTP on an SSL-configured port or certificate files are missing/corrupted.
- **Check**: Verify `ssl_certificate` and `ssl_certificate_key` exist and point to valid files.
