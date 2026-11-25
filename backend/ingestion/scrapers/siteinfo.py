"""Analyse a loaded page: is it reachable, blocked, behind a login, how is it built?

The result is shown in the panel's "Site info" box and stored with each run.
"""

import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from playwright.async_api import Error as PlaywrightError, Page

from .browser import LoginExpired, PageLoad, ScrapeError

# Runs inside the page before scripts are stripped, so frameworks can still be seen.
_ANALYZE_JS = """
() => {
  const q = (s) => document.querySelector(s);
  const visible = (el) => !!el && !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const any = (sels) => sels.some((s) => q(s));

  const captcha = [];
  if (any(['.g-recaptcha', 'iframe[src*="recaptcha"]'])) captcha.push('reCAPTCHA');
  if (any(['.h-captcha', 'iframe[src*="hcaptcha"]'])) captcha.push('hCaptcha');
  if (any(['.cf-turnstile', 'iframe[src*="challenges.cloudflare.com"]', '#challenge-form', '#challenge-running'])) captcha.push('Cloudflare challenge');
  if (any(['iframe[src*="captcha-delivery.com"]'])) captcha.push('DataDome CAPTCHA');
  if (any(['#px-captcha'])) captcha.push('PerimeterX CAPTCHA');
  if (any(['iframe[src*="arkoselabs"]', 'iframe[src*="funcaptcha"]'])) captcha.push('Arkose / FunCaptcha');
  if (any(['form[action*="validateCaptcha"]'])) captcha.push('Amazon CAPTCHA');

  const tech = [];
  const add = (name, test) => { try { if (test()) tech.push(name); } catch {} };
  add('Next.js', () => window.__NEXT_DATA__ || q('#__next') || q('script[src*="/_next/"]'));
  add('Nuxt', () => window.__NUXT__ || q('#__nuxt'));
  add('React', () => q('[data-reactroot]') || q('#root') && Object.keys(q('#root')).some((k) => k.startsWith('__react')) || tech.includes('Next.js'));
  add('Vue', () => window.Vue || q('[data-v-app]') || [...document.querySelectorAll('*')].slice(0, 500).some((e) => [...e.attributes].some((a) => a.name.startsWith('data-v-'))));
  add('Angular', () => q('[ng-version]'));
  add('Svelte', () => q('[class*="svelte-"]'));
  add('Gatsby', () => q('#___gatsby'));
  add('jQuery', () => window.jQuery);
  add('WordPress', () => q('link[href*="wp-content"], script[src*="wp-content"], script[src*="wp-includes"]'));
  add('Shopify', () => window.Shopify);
  add('Wix', () => q('meta[name="generator"][content*="Wix"]'));
  add('Squarespace', () => q('meta[name="generator"][content*="Squarespace"]') || window.Static && window.Static.SQUARESPACE_CONTEXT);
  add('Magento', () => q('script[type="text/x-magento-init"]'));
  add('MediaWiki', () => q('meta[name="generator"][content*="MediaWiki"]'));
  const generator = q('meta[name="generator"]')?.content || null;

  const structured = [];
  for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      const data = JSON.parse(s.textContent);
      for (const item of [data, ...(data['@graph'] || [])].flat()) {
        const t = item && item['@type'];
        if (t) structured.push(...[t].flat());
      }
    } catch {}
  }

  const pagination = [];
  if (q('link[rel="next"], a[rel="next"]')) pagination.push('rel="next" link');
  const clickable = [...document.querySelectorAll('a, button')].slice(0, 3000);
  const label = (el) => (el.innerText || el.getAttribute('aria-label') || '').trim().toLowerCase();
  if (clickable.some((el) => /^(next|next page|›|»|→|>)$/.test(label(el)))) pagination.push('"Next" button');
  if (clickable.some((el) => /^(load|show|view) more/.test(label(el)))) pagination.push('"Load more" button');
  if (q('.pagination, [class*="pagination"], nav[aria-label*="agination"]')) pagination.push('page numbers');

  const password = [...document.querySelectorAll('input[type="password"]')].some(visible);
  const consent = [...document.querySelectorAll('[id*="cookie" i], [class*="cookie" i], [id*="consent" i], [class*="consent" i]')]
    .some((el) => visible(el) && el.innerText && el.innerText.length > 40);

  const body = document.body;
  return {
    title: document.title,
    lang: document.documentElement.lang || null,
    textLength: body ? body.innerText.length : 0,
    elements: document.querySelectorAll('*').length,
    links: document.links.length,
    images: document.images.length,
    forms: document.forms.length,
    iframes: document.querySelectorAll('iframe').length,
    passwordField: password,
    captcha,
    tech,
    generator,
    structured: [...new Set(structured)].slice(0, 10),
    pagination,
    cookieBanner: consent,
    metaRobots: q('meta[name="robots"]')?.content || null,
  };
}
"""

_BLOCK_TITLE = re.compile(
    r"just a moment|attention required|access denied|are you a robot|robot check|"
    r"security check|pardon our interruption|request blocked|sorry! something went wrong|"
    r"verify you are human|unusual traffic|bot detection|^403 forbidden|^forbidden$|"
    r"captcha|too many requests",
    re.IGNORECASE,
)
_BLOCK_STATUS = {401, 403, 407, 429, 503}
_LOGIN_PATH = re.compile(r"log-?in|sign-?in|auth|sso|session|account", re.IGNORECASE)


def _protection(headers: dict[str, str], cookies: list[str]) -> list[str]:
    h = {k.lower(): v.lower() for k, v in headers.items()}
    found = []
    if "cf-ray" in h or h.get("server") == "cloudflare":
        found.append("Cloudflare")
    if "akamai" in h.get("server", "") or any(k.startswith("x-akamai") for k in h) or any(
        c in ("_abck", "bm_sz", "ak_bmsc") for c in cookies
    ):
        found.append("Akamai")
    if "x-datadome" in h or "datadome" in cookies:
        found.append("DataDome")
    if any(c.startswith("_px") for c in cookies):
        found.append("PerimeterX / HUMAN")
    if "x-iinfo" in h or any(c.startswith(("incap_ses", "visid_incap")) for c in cookies):
        found.append("Imperva")
    if "x-sucuri-id" in h:
        found.append("Sucuri")
    if any(c.startswith("aws-waf-token") for c in cookies):
        found.append("AWS WAF")
    if "x-amz-cf-id" in h:
        found.append("Amazon CloudFront (CDN)")
    return found


def _visible_text_length(html: str) -> int:
    html = re.sub(r"(?is)<(script|style|noscript|template)\b.*?</\1>", " ", html)
    return len(re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html)).strip())


async def _robots(page: Page, url: str) -> dict:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        res = await page.context.request.get(robots_url, timeout=5000)
    except PlaywrightError:
        return {"url": robots_url, "found": None, "allowed": None}
    if res.status >= 400:
        return {"url": robots_url, "found": False, "allowed": True}
    parser = RobotFileParser()
    parser.parse((await res.text()).splitlines())
    return {"url": robots_url, "found": True, "allowed": parser.can_fetch("*", url)}


async def analyze(page: Page, load: PageLoad, *, check_robots: bool = True) -> dict:
    try:
        js = await page.evaluate(_ANALYZE_JS)
    except PlaywrightError:
        js = {"title": "", "textLength": 0, "captcha": [], "tech": [], "passwordField": False}
    cookies = [c["name"] for c in await page.context.cookies()]

    status = load.status
    blocked_reason = None
    if status in _BLOCK_STATUS:
        blocked_reason = f"The site answered HTTP {status}"
    elif _BLOCK_TITLE.search(js.get("title") or ""):
        blocked_reason = f'The page is a block/challenge page ("{js["title"]}")'
    elif js["captcha"] and js["textLength"] < 2000:
        blocked_reason = f"The page shows a CAPTCHA ({', '.join(js['captcha'])})"

    redirected_to_login = load.final_url != load.requested_url and bool(
        _LOGIN_PATH.search(urlparse(load.final_url).path)
    )
    login_wall = js["passwordField"] and (redirected_to_login or js["textLength"] < 3000)

    js_rendered = None
    if load.raw_html is not None and js["textLength"] > 200:
        js_rendered = _visible_text_length(load.raw_html) < js["textLength"] * 0.5

    site = {
        "requested_url": load.requested_url,
        "final_url": load.final_url,
        "redirects": load.redirects,
        "status": status,
        "load_ms": load.load_ms,
        "html_kb": round(load.html_bytes / 1024, 1) if load.html_bytes else None,
        "server": load.headers.get("server"),
        "title": js.get("title"),
        "lang": js.get("lang"),
        "protection": _protection(load.headers, cookies),
        "captcha": js["captcha"],
        "blocked": blocked_reason is not None,
        "blocked_reason": blocked_reason,
        "login_wall": login_wall,
        "password_field": js["passwordField"],
        "js_rendered": js_rendered,
        "tech": js["tech"],
        "generator": js.get("generator"),
        "structured_data": js.get("structured", []),
        "pagination": js.get("pagination", []),
        "cookie_banner": js.get("cookieBanner", False),
        "meta_robots": js.get("metaRobots"),
        "stats": {
            "elements": js.get("elements"),
            "links": js.get("links"),
            "images": js.get("images"),
            "forms": js.get("forms"),
            "iframes": js.get("iframes"),
            "text_chars": js.get("textLength"),
        },
        "robots": await _robots(page, load.requested_url) if check_robots else None,
    }
    site["verdict"], site["notes"] = _verdict(site)
    return site


def _verdict(site: dict) -> tuple[str, list[str]]:
    """Overall rating plus plain-language notes for the user."""
    notes = []
    verdict = "good"
    if site["blocked"]:
        verdict = "blocked"
        notes.append(f"{site['blocked_reason']}. The site is blocking automated access.")
        if site["protection"]:
            notes.append(f"Protected by {', '.join(site['protection'])}. Proxies or a login may help.")
    elif site["status"] and site["status"] >= 400:
        verdict = "blocked"
        notes.append(f"The site answered HTTP {site['status']}.")
    if site["login_wall"]:
        verdict = "blocked" if verdict == "blocked" else "warning"
        notes.append("The page asks you to log in. Add a login profile to this template.")
    if verdict == "good":
        if site["protection"]:
            verdict = "warning"
            notes.append(f"Uses bot protection ({', '.join(site['protection'])}); frequent runs may get blocked.")
        if site["captcha"]:
            verdict = "warning"
            notes.append(f"Has a CAPTCHA widget ({', '.join(site['captcha'])}).")
    robots = site.get("robots") or {}
    if robots.get("allowed") is False:
        if verdict == "good":
            verdict = "warning"
        notes.append("robots.txt asks crawlers not to visit this page.")
    if site["final_url"].rstrip("/") != site["requested_url"].rstrip("/"):
        notes.append(f"Redirected to {site['final_url']}.")
    if site["js_rendered"]:
        notes.append("Content is built by JavaScript; a full browser is needed (we use one).")
    if site["pagination"]:
        notes.append(f"Has more pages ({', '.join(site['pagination'])}).")
    if site["structured_data"]:
        notes.append(f"Contains structured data: {', '.join(site['structured_data'][:5])}.")
    if site["cookie_banner"]:
        notes.append("Shows a cookie consent banner.")
    if verdict == "good":
        notes.insert(0, "Page loaded normally. Scraping should work.")
    return verdict, notes


def check_access(site: dict, using_login: bool) -> None:
    """Raise if the page can't be scraped as loaded."""
    if using_login and site["login_wall"]:
        raise LoginExpired("The saved login has expired. Log in again to continue.", site)
    if site["blocked"]:
        # Blocks are often temporary (rate limits, a flagged IP); worth a retry
        raise ScrapeError(f"Blocked by the site: {site['blocked_reason']}", site, retryable=True)
    if site["status"] and site["status"] >= 400:
        raise ScrapeError(f"The site answered HTTP {site['status']}", site, retryable=site["status"] >= 500)
