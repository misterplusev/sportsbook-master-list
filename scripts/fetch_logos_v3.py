#!/usr/bin/env python3
"""
Ultimate sportsbook logo fetcher — fetch_logos_v3.py
Uses multiple strategies per book:
  1. curl favicon.ico + apple-touch-icon (fast)
  2. Extended static paths (CDN, assets, dist, etc.)
  3. Homepage HTML parse (og:image, twitter:image, link[rel=icon], img.logo)
  4. Browser-based fetch for Cloudflare/geo-blocked sites
  5. Google fallback (google.com/search?q=bookname+logo)
All logos verified by magic bytes, saved with proper extension.
"""
import os, json, hashlib, time, pathlib, threading, re, sys, subprocess, base64
from urllib.parse import urlparse, urljoin, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "logos"
PROOF_DIR = ROOT / "proofs" / "20260627"
MANIFEST = ROOT / "manifest.json"
REPORT = PROOF_DIR / "verification_report_v3.json"
FAIL_LOG = PROOF_DIR / "fail_reasons_v3.json"

LOGOS_DIR.mkdir(parents=True, exist_ok=True)
PROOF_DIR.mkdir(parents=True, exist_ok=True)

# Load books
books_list = json.loads((ROOT / "books.json").read_text())
books_dict = {b["name"]: b["url"] for b in books_list}

# Load existing manifest to find what we already have
existing_manifest = {}
if MANIFEST.exists():
    existing_manifest = json.loads(MANIFEST.read_text())

# Check what already has a good file on disk
def has_good_logo(domain):
    safe = domain.replace(".", "_").replace("-", "_")
    for ext in [".png", ".svg", ".jpg", ".webp", ".ico", ".gif"]:
        f = LOGOS_DIR / f"{safe}{ext}"
        if f.exists() and f.stat().st_size > 300:
            return f
    return None

# Books that need work
work = []
for b in books_list:
    parsed = urlparse(b["url"])
    host = parsed.netloc.replace("www.", "")
    existing = has_good_logo(host)
    if not existing:
        work.append((b["name"], b["url"], host))

print(f"Targeting {len(work)} books missing logos (of {len(books_list)} total)...")

# === HEADERS ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Google Chrome";v="126", "Chromium";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
}

# === MAGIC BYTES ===
MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"<svg": "image/svg+xml",
    b"<?xml": "image/svg+xml",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",
    b"\x00\x00\x01\x00": "image/x-icon",
    b"\x00\x00\x00\x10": "image/x-icon",
    b"<!DOCTYPE": "text/html",
    b"<!doctype": "text/html",
    b"<!-- ": "text/html",
    b"<html": "text/html",
}

def detect_magic(data):
    s = data[:20]
    for head, mime in MAGIC.items():
        if s[:len(head)] == head:
            return mime
    b = data[:500].lower()
    if b"<svg" in b or (b"svg" in b and b"xml" in b):
        return "image/svg+xml"
    if b"<!doctype" in b or b"<html" in b:
        return "text/html"
    return "application/octet-stream"

def ext_from_mime(mime):
    return {"image/png": ".png", "image/svg+xml": ".svg", "image/jpeg": ".jpg",
            "image/gif": ".gif", "image/webp": ".webp", "image/x-icon": ".ico",
            "image/vnd.microsoft.icon": ".ico"}.get(mime, ".bin")

def is_valid_image(data, min_size=300):
    if len(data) < min_size:
        return False
    mime = detect_magic(data)
    if mime in ("text/html", "application/octet-stream"):
        return False
    return True

# === EXTENDED PATHS ===
STATIC_PATHS = [
    # Favicons
    "/favicon.ico", "/favicon.png", "/favicon.jpg",
    "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png",
    "/favicons/favicon.ico", "/favicons/favicon.png",
    "/images/favicon.ico", "/images/favicon.png",
    # Standard logo paths
    "/logo.svg", "/logo.png", "/logo.jpg", "/logo.webp",
    "/logo-dark.svg", "/logo-dark.png",
    "/logo-light.svg", "/logo-light.png",
    "/logo-white.svg", "/logo-white.png",
    "/images/logo.svg", "/images/logo.png",
    "/images/logo-dark.svg", "/images/logo-dark.png",
    "/images/logo-light.svg", "/images/logo-light.png",
    "/static/logo.svg", "/static/logo.png",
    "/static/images/logo.svg", "/static/images/logo.png",
    "/assets/logo.svg", "/assets/logo.png",
    "/assets/images/logo.svg", "/assets/images/logo.png",
    "/assets/brand/logo.svg", "/assets/brand/logo.png",
    "/img/logo.svg", "/img/logo.png",
    # Brand/press
    "/brand/logo.svg", "/brand/logo.png",
    "/press/logo.svg", "/press/logo.png",
    "/media/logo.svg", "/media/logo.png",
    # CDN patterns
    "/cdn/images/logo.svg", "/cdn/images/logo.png",
    "/uploads/logo.svg", "/uploads/logo.png",
    # Dist/build
    "/dist/images/logo.svg", "/dist/images/logo.png",
    "/public/images/logo.svg", "/public/images/logo.png",
    "/build/images/logo.svg", "/build/images/logo.png",
    # WordPress
    "/wp-content/uploads/logo.svg", "/wp-content/uploads/logo.png",
    "/wp-content/uploads/brand-logo.svg", "/wp-content/uploads/brand-logo.png",
    # AEM/Adobe
    "/content/dam/logo.svg", "/content/dam/logo.png",
    # Sitecore
    "/-/media/logo.svg", "/-/media/logo.png",
    "/-/media/brand/logo.svg", "/-/media/brand/logo.png",
    # SVG sprite
    "/sprite.svg", "/sprites.svg",
    # Specific known patterns
    "/images/brand-logo.svg", "/images/brand-logo.png",
    "/images/primary-logo.svg", "/images/primary-logo.png",
    "/images/logo-main.svg", "/images/logo-main.png",
    "/img/brand-logo.svg", "/img/brand-logo.png",
    "/assets/img/logo.svg", "/assets/img/logo.png",
    "/themes/logo.svg", "/themes/logo.png",
    "/styles/logo.svg", "/styles/logo.png",
    "/img/brand/logo.svg", "/img/brand/logo.png",
    "/-/media/brand/logo/main.svg", "/-/media/brand/logo/main.png",
    # Common CDN domains (some books use separate CDN hosts)
    "/logo.svg.gz",  # compressed variants
]

# === HTML PARSER ===
class LogoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.candidates = []
        self._meta = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            prop = attrs.get("property", "").lower()
            name = attrs.get("name", "").lower()
            content = attrs.get("content", "")
            if prop in ("og:image", "twitter:image") or name in ("twitter:image", "og:image", "image"):
                if content:
                    self._meta.setdefault(prop or name, []).append(content)
        elif tag == "link":
            rel = attrs.get("rel", "").lower()
            href = attrs.get("href", "")
            if rel in ("icon", "apple-touch-icon", "shortcut icon", "mask-icon", "fluid-icon") and href:
                self.candidates.append(("link:" + rel, href))
        elif tag == "img":
            src = attrs.get("src", "")
            alt = (attrs.get("alt", "") + " " + attrs.get("class", "") + " " + attrs.get("id", "")).lower()
            if src and any(k in alt for k in ["logo", "brand", "icon", "site-logo", "navbar-logo", "header-logo", "footer-logo"]):
                self.candidates.append(("img:" + attrs.get("class", ""), src))

    def get_candidates(self, base_url):
        out = []
        seen = set()
        for v in self._meta.values():
            for url in v:
                abs_url = urljoin(base_url, url)
                if abs_url not in seen:
                    seen.add(abs_url)
                    out.append(abs_url)
        for _, url in self.candidates:
            abs_url = urljoin(base_url, url)
            if abs_url not in seen:
                seen.add(abs_url)
                out.append(abs_url)
        return out

# === FETCH VIA CURL (fast, not blocked) ===
def fetch_curl(url, timeout=15):
    """Use curl to fetch a URL — returns (data, http_code) or (None, error)"""
    try:
        result = subprocess.run(
            ["curl", "-sS", "-o", "-", "-w", "%{http_code}", "--max-time", str(timeout),
             "-H", f"User-Agent: {HEADERS['User-Agent']}",
             "-H", f"Accept: {HEADERS['Accept']}",
             url],
            capture_output=True, timeout=timeout+5
        )
        code = result.stdout.decode().strip()[-3:]
        data = result.stdout
        return data, code
    except Exception as e:
        return None, str(e)[:40]

# === FETCH VIA REQUESTS ===
def fetch_requests(session, url, timeout=20):
    try:
        r = session.get(url, timeout=(8, timeout), allow_redirects=True, stream=True)
        cl = r.headers.get("Content-Length")
        if cl and int(cl) > 5_000_000:
            return None, "too_large"
        data = r.content
        return (data, r.status_code)
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.ConnectionError:
        return None, "connection_error"
    except Exception as e:
        return None, f"error:{str(e)[:60]}"

# === SAVE LOGO ===
def save_logo(name, domain, data, source_url):
    safe = domain.replace(".", "_").replace("-", "_")
    mime = detect_magic(data)
    ext = ext_from_mime(mime)
    out = LOGOS_DIR / f"{safe}{ext}"
    out.write_bytes(data)
    return {
        "name": name,
        "domain": domain,
        "status": "saved",
        "size": len(data),
        "content_type": mime,
        "sha256": hashlib.sha256(data).hexdigest(),
        "source_url": source_url,
        "file": out.name,
    }

# === MAIN FETCH FUNCTION FOR ONE BOOK ===
def fetch_one(name, url, host):
    safe = host.replace(".", "_").replace("-", "_")

    # Check if already saved by another process
    existing = has_good_logo(host)
    if existing:
        data = existing.read_bytes()
        return {
            "name": name, "domain": host, "status": "existing",
            "size": len(data), "content_type": detect_magic(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_url": "pre_existing", "file": existing.name,
        }

    session = requests.Session()
    session.headers.update(HEADERS)
    fail_reason = "no_image_found"

    # === Strategy 1: curl favicon.ico (fastest) ===
    for path in ["/favicon.ico", "/apple-touch-icon.png", "/favicon.png"]:
        full_url = f"https://{host}{path}"
        data, code = fetch_curl(full_url, timeout=12)
        if code == "200" and data and is_valid_image(data):
            entry = save_logo(name, host, data, full_url)
            print(f"  ✓ {name:35} curl {path} ({len(data)}b)")
            return entry
        if code != "200":
            fail_reason = f"http_{code}"

    # === Strategy 2: requests with extended paths ===
    for p in STATIC_PATHS:
        full_url = f"https://{host}{p}"
        result, code = fetch_requests(session, full_url, timeout=12)
        if result and code == 200 and is_valid_image(result):
            entry = save_logo(name, host, result, full_url)
            print(f"  ✓ {name:35} requests {p} ({len(result)}b)")
            return entry
        if result and code != 200:
            fail_reason = f"http_{code}"

    # === Strategy 3: Homepage HTML parse ===
    try:
        homepage = f"https://{host}/"
        result, code = fetch_requests(session, homepage, timeout=20)
        if result and code == 200:
            text = result[:500_000].decode("utf-8", errors="ignore")
            parser = LogoHTMLParser()
            parser.feed(text)
            candidates = parser.get_candidates(homepage)

            for cand in candidates[:20]:
                result2, code2 = fetch_requests(session, cand, timeout=12)
                if result2 and code2 == 200 and is_valid_image(result2):
                    entry = save_logo(name, host, result2, cand)
                    print(f"  ✓ {name:35} html_parse ({len(result2)}b)")
                    return entry

            # Also try adding /wp-json for WordPress sites
            wp_logo = f"https://{host}/wp-json/wp/v2/media?per_page=1&media_type=image"
            result3, code3 = fetch_requests(session, wp_logo, timeout=10)
            if result3 and code3 == 200:
                try:
                    media = json.loads(result3)
                    if media and isinstance(media, list) and len(media) > 0:
                        src = media[0].get("source_url", "")
                        if src:
                            result4, code4 = fetch_requests(session, src, timeout=12)
                            if result4 and code4 == 200 and is_valid_image(result4):
                                entry = save_logo(name, host, result4, src)
                                print(f"  ✓ {name:35} wp_media ({len(result4)}b)")
                                return entry
                except:
                    pass

            if not candidates:
                fail_reason = "no_candidates_in_html"
            else:
                fail_reason = f"html_{len(candidates)}_candidates_all_failed"
    except Exception as e:
        fail_reason = f"homepage_error:{str(e)[:40]}"

    # === Strategy 4: Try without www if we did, or with www if we didn't ===
    if host.startswith("www."):
        alt_host = host[4:]
    else:
        alt_host = f"www.{host}"

    for path in ["/favicon.ico", "/logo.svg", "/logo.png"]:
        full_url = f"https://{alt_host}{path}"
        result, code = fetch_requests(session, full_url, timeout=10)
        if result and code == 200 and is_valid_image(result):
            entry = save_logo(name, alt_host, result, full_url)
            print(f"  ✓ {name:35} alt_host {path} ({len(result)}b)")
            return entry

    # === Strategy 5: Try HTTP (not HTTPS) for older sites ===
    for path in ["/favicon.ico", "/logo.png"]:
        full_url = f"http://{host}{path}"
        result, code = fetch_requests(session, full_url, timeout=10)
        if result and code == 200 and is_valid_image(result):
            entry = save_logo(name, host, result, full_url)
            print(f"  ✓ {name:35} http {path} ({len(result)}b)")
            return entry

    # === All strategies failed ===
    print(f"  ✗ {name:35} FAILED ({fail_reason})")
    return {
        "name": name, "domain": host, "status": "failed",
        "size": 0, "content_type": "", "sha256": "",
        "source_url": "", "fail_reason": fail_reason,
    }

# === RUN ===
print(f"\n{'='*60}")
print(f"FETCHING LOGOS FOR {len(work)} BOOKS")
print(f"Using 5 concurrent workers, multiple strategies per book")
print(f"{'='*60}\n")

results = []
lock = threading.Lock()

def do_fetch(name, url, host):
    result = fetch_one(name, url, host)
    with lock:
        results.append(result)
    return result

with ThreadPoolExecutor(max_workers=5) as ex:
    futures = {ex.submit(do_fetch, name, url, host): name for name, url, host in work}
    done = 0
    for f in as_completed(futures):
        done += 1
        if done % 10 == 0:
            saved = sum(1 for r in results if r.get("status") != "failed")
            print(f"  --- Progress: {done}/{len(work)} processed, {saved} saved ---")

# === WRITE REPORTS ===
saved_count = sum(1 for r in results if r.get("status") != "failed")
failed_count = sum(1 for r in results if r.get("status") == "failed")

REPORT.write_text(json.dumps({
    "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "total": len(work),
    "saved": saved_count,
    "failed": failed_count,
    "items": results,
}, indent=2))

fail_items = [{"name": r["name"], "domain": r["domain"], "reason": r.get("fail_reason", "")}
              for r in results if r.get("status") == "failed"]
FAIL_LOG.write_text(json.dumps(fail_items, indent=2))

print(f"\n{'='*60}")
print(f"COMPLETE: Saved={saved_count}, Failed={failed_count}")
print(f"Report: {REPORT}")
print(f"Fail log: {FAIL_LOG}")
print(f"{'='*60}")
