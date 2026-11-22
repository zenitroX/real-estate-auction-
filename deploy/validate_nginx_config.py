"""
Verification script for SKANDX Nginx configuration syntax & required directives.
Performs programmatic and regex-based AST/token validation on Nginx configuration files.
"""

import sys
import re
from pathlib import Path

def validate_nginx_syntax(content: str, filename: str) -> list[str]:
    errors = []
    
    # 1. Brace balancing check
    brace_count = 0
    in_quote = False
    quote_char = ''
    
    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        # Skip full comment lines
        if stripped.startswith('#'):
            continue
        
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '#' and not in_quote:
                break  # comment starts, ignore rest of line
            if ch in ('"', "'"):
                if not in_quote:
                    in_quote = True
                    quote_char = ch
                elif quote_char == ch:
                    in_quote = False
            elif not in_quote:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count < 0:
                        errors.append(f"{filename}:{line_num} - Closing brace '}}' without matching open brace")
            i += 1

    if brace_count != 0:
        errors.append(f"{filename} - Unbalanced braces count delta: {brace_count}")

    # 2. Check directive semicolon termination
    for line_num, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        # Remove comments at end of line if outside quotes
        if '#' in line and '"' not in line and "'" not in line:
            line = line.split('#')[0].strip()
        if not line:
            continue
        
        # Valid non-semicolon lines are opening/closing blocks, or multi-line strings
        if line.endswith('{') or line == '}' or line.endswith('\\') or line.startswith('"') or line.endswith(','):
            continue
        if not line.endswith(';'):
            # Check if this line is part of a block header or multi-line format
            if not any(kw in line for kw in ['server {', 'location', 'upstream', 'http {', 'events {', 'log_format']):
                errors.append(f"{filename}:{line_num} - Directive does not end with semicolon: '{line}'")

    return errors

def validate_skandx_requirements(content: str, filename: str) -> list[str]:
    failures = []
    
    required_checks = [
        # Upstream
        ("Upstream backend_api definition", r'upstream\s+backend_api\s*\{[^}]*server\s+127\.0\.0\.1:8000[^}]*max_fails=3\s+fail_timeout=10s;[^}]*keepalive\s+32;'),
        
        # Port 80 & ACME challenge
        ("Port 80 listen", r'listen\s+80;'),
        ("ACME challenge location", r'location\s+/\.well-known/acme-challenge/\s*\{[^}]*root\s+/var/www/certbot;'),
        ("Port 80 redirect to HTTPS", r'return\s+301\s+https://\$host\$request_uri;'),
        
        # Port 443 & TLS
        ("Port 443 SSL listen", r'listen\s+443\s+ssl'),
        ("TLS protocols (1.2 & 1.3 only)", r'ssl_protocols\s+TLSv1\.2\s+TLSv1\.3;'),
        ("Modern SSL ciphers", r'ssl_ciphers\s+[\'"]?[^\'";]+AES128-GCM-SHA256'),
        ("SSL session cache", r'ssl_session_cache\s+shared:SSL:10m;'),
        ("SSL session timeout", r'ssl_session_timeout\s+1d;'),
        
        # Security Headers
        ("HSTS Header", r'add_header\s+Strict-Transport-Security\s+"max-age=63072000;\s*includeSubDomains;\s*preload"\s+always;'),
        ("X-Frame-Options Header", r'add_header\s+X-Frame-Options\s+"SAMEORIGIN"\s+always;'),
        ("X-Content-Type-Options Header", r'add_header\s+X-Content-Type-Options\s+"nosniff"\s+always;'),
        ("Referrer-Policy Header", r'add_header\s+Referrer-Policy\s+"strict-origin-when-cross-origin"\s+always;'),
        ("Permissions-Policy Header", r'add_header\s+Permissions-Policy\s+"camera=\(\),\s*microphone=\(\),\s*geolocation=\(\)"\s+always;'),
        ("Content-Security-Policy Header", r'add_header\s+Content-Security-Policy\s+"default-src\s+\'self\';.*blob:.*"'),
        
        # Rate Limiting Zones
        ("Admin login rate limit zone (5r/m)", r'limit_req_zone\s+\$binary_remote_addr\s+zone=admin_login_zone:10m\s+rate=5r/m;'),
        ("API general rate limit zone (30r/s)", r'limit_req_zone\s+\$binary_remote_addr\s+zone=api_general_zone:10m\s+rate=30r/s;'),
        
        # Route: /api/admin/login
        ("Route /api/admin/login with burst 3 & status 429", r'location\s*=?\s*/api/admin/login\s*\{[^}]*limit_req\s+zone=admin_login_zone\s+burst=3\s+nodelay;[^}]*limit_req_status\s+429;'),
        
        # Route: /api/admin/pdf-proxy
        ("Route /api/admin/pdf-proxy with chunked streaming settings", r'location\s+/api/admin/pdf-proxy\s*\{[^}]*proxy_buffering\s+off;[^}]*client_max_body_size\s+30M;[^}]*proxy_read_timeout\s+60s;'),
        
        # Route: /api/
        ("Route /api/ with keepalive and proxy headers", r'location\s+/api/\s*\{[^}]*proxy_pass\s+http://backend_api;[^}]*proxy_http_version\s+1\.1;[^}]*proxy_set_header\s+Connection\s+"";'),
        
        # Static Assets & SPA
        ("Frontend root path", r'root\s+/var/www/skandx/frontend/dist;'),
        ("SPA try_files fallback", r'try_files\s+\$uri\s+\$uri/\s+/index\.html;'),
        ("Assets 1y immutable cache", r'location\s+/assets/\s*\{[^}]*expires\s+1y;[^}]*add_header\s+Cache-Control\s+"public,\s*immutable";'),
        
        # Slowloris & DoS Protection
        ("Slowloris client_body_timeout", r'client_body_timeout\s+10s;'),
        ("Slowloris client_header_timeout", r'client_header_timeout\s+10s;'),
        ("Slowloris keepalive_timeout", r'keepalive_timeout\s+65s;'),
        ("Slowloris send_timeout", r'send_timeout\s+10s;'),
    ]
    
    for desc, pattern in required_checks:
        if not re.search(pattern, content, re.DOTALL):
            failures.append(f"Missing requirement in {filename}: {desc} (Pattern: {pattern})")

    return failures

def main():
    root = Path(__file__).resolve().parent
    nginx_conf = root / "nginx.conf"
    site_conf = root / "skandx.site.conf"
    
    all_passed = True
    
    for conf_path in [nginx_conf, site_conf]:
        if not conf_path.exists():
            print(f"[FAIL] Configuration file not found: {conf_path}")
            all_passed = False
            continue
            
        content = conf_path.read_text(encoding="utf-8")
        print(f"\n========================================================")
        print(f"Validating {conf_path.name}...")
        print(f"========================================================")
        
        syntax_errors = validate_nginx_syntax(content, conf_path.name)
        if syntax_errors:
            print(f"[ERROR] Syntax Errors in {conf_path.name}:")
            for err in syntax_errors:
                print(f"  - {err}")
            all_passed = False
        else:
            print(f"[PASS] Syntax & balanced braces check passed for {conf_path.name}.")
            
        req_failures = validate_skandx_requirements(content, conf_path.name)
        if req_failures:
            print(f"[ERROR] Requirement Failures in {conf_path.name}:")
            for err in req_failures:
                print(f"  - {err}")
            all_passed = False
        else:
            print(f"[PASS] All P1 Reverse Proxy requirements verified in {conf_path.name}.")
            
    if all_passed:
        print("\n>>> ALL NGINX CONFIGURATIONS VERIFIED & VALIDATED SUCCESSFULLY! <<<")
        sys.exit(0)
    else:
        print("\n>>> VALIDATION FAILED WITH ERRORS <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()
