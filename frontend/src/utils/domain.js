/**
 * Domain & Subdomain Detection Utility for SKANDX
 * 
 * Supports:
 * - Production Customer Domain: skandx.com, www.skandx.com
 * - Production Admin Subdomain: admin.skandx.com, ops.skandx.com
 * - Local Development: admin.localhost:5173, localhost:5173/#admin, localhost:5173/?portal=admin
 */

export function isSubdomainAdmin() {
  if (typeof window === 'undefined') return false;
  
  const hostname = window.location.hostname.toLowerCase();
  const search = new URLSearchParams(window.location.search);
  const hash = window.location.hash.toLowerCase();

  // 1. Explicit subdomain in production or local dev (e.g. admin.skandx.com or admin.localhost)
  if (hostname.startsWith('admin.') || hostname.startsWith('ops.')) {
    return true;
  }

  // 2. Query parameter override (e.g. ?portal=admin or ?mode=admin)
  if (search.get('portal') === 'admin' || search.get('mode') === 'admin') {
    return true;
  }

  // 3. Hash route override (e.g. #admin or #/admin)
  if (hash.startsWith('#admin') || hash.startsWith('#/admin')) {
    return true;
  }

  return false;
}

export function isLocalDev() {
  if (typeof window === 'undefined') return false;
  const host = window.location.hostname;
  return host === 'localhost' || host === '127.0.0.1';
}

/**
 * Returns the target customer or admin portal URL depending on current environment.
 */
export function getPortalUrl(target = 'customer') {
  if (typeof window === 'undefined') return '/';
  
  const { protocol, host, hostname, port } = window.location;
  
  if (isLocalDev()) {
    if (target === 'admin') {
      return `${protocol}//admin.localhost${port ? `:${port}` : ''}`;
    }
    return `${protocol}//localhost${port ? `:${port}` : ''}`;
  }

  // Production domain mapping
  const baseDomain = hostname.replace(/^(admin\.|www\.|ops\.)/, '');
  if (target === 'admin') {
    return `${protocol}//admin.${baseDomain}`;
  }
  return `${protocol}//${baseDomain}`;
}
