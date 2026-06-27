#!/usr/bin/env python3
"""
Improved sportsbook logo fetcher - fetch_logos_v2.py
Targets the 117 failed books from build_logo_proof.py with better strategy.
"""
import os, json, hashlib, time, pathlib, threading
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "logos"
PROOF_DIR = ROOT / "proofs" / "20260627"
MANIFEST = ROOT / "manifest.json"
REPORT = PROOF_DIR / "verification_report_v2.json"
FAIL_LOG = PROOF_DIR / "fail_reasons.json"

LOGOS_DIR.mkdir(parents=True, exist_ok=True)
PROOF_DIR.mkdir(parents=True, exist_ok=True)

existing_manifest = json.loads(MANIFEST.read_text())
failed_books = {k: v for k, v in existing_manifest.items() if v.get("status") == "failed"}

books_list = json.loads((ROOT / "books.json").read_text())
books_dict = {b["name"]: b["url"] for b in books_list}

print(f"Targeting {len(failed_books)} failed books...")

PATHS = [
    "/favicon.ico", "/favicon.png",
    "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png",
    "/logo.svg", "/logo.png", "/logo.jpg",
    "/images/logo.svg", "/images/logo.png",
    "/static/logo.svg", "/static/logo.png",
    "/static/images/logo.svg", "/static/images/logo.png",
    "/assets/logo.svg", "/assets/logo.png",
    "/assets/images/logo.svg", "/assets/images/logo.png",
    "/assets/brand/logo.svg", "/assets/brand/logo.png",
    "/img/logo.svg", "/img/logo.png",
    "/images/brand-logo.svg", "/images/brand-logo.png",
    "/images/primary-logo.svg", "/images/primary-logo.png",
    "/cdn/images/logo.svg", "/cdn/images/logo.png",
    "/uploads/logo.svg", "/uploads/logo.png",
    "/media/logo.svg", "/media/logo.png",
    "/content/dam/logo.svg", "/content/dam/logo.png",
    "/-/media/logo.svg", "/-/media/logo.png",
    "/-/media/brand/logo.svg", "/-/media/brand/logo.png",
    "/dist/images/logo.svg", "/dist/images/logo.png",
    "/public/images/logo.svg", "/public/images/logo.png",
    "/build/images/logo.svg", "/build/images/logo.png",
    "/wp-content/uploads/logo.svg", "/wp-content/uploads/logo.png",
    "/images/brand/logo.svg", "/images/logo-main.svg", "/images/logo-main.png",
    "/img/brand-logo.svg", "/img/brand-logo.png",
    "/assets/img/logo.svg", "/assets/img/logo.png",
    "/themes/logo.svg", "/themes/logo.png",
    "/styles/logo.svg", "/styles/logo.png",
    "/img/brand/logo.svg", "/img/brand/logo.png",
    "/-/media/brand/logo/main.svg", "/-/media/brand/logo/main.png",
    "/content/dam/betmgm/rebrand/logo/betmgm-logo.svg",
    "/-/media/betway/global/header/betway-logo.svg",
    "/etc/designs/unibetcom/images/unibet-logo.svg",
    "/themes/winamax/images/logo-winamax.svg",
    "/favicons/favicon.ico", "/favicons/favicon.png",
    "/images/favicon.ico", "/images/favicon.png",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
}

MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"<svg": "image/svg+xml",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",
    b"<!DOCTYPE": "text/html",
    b"<!doctype": "text/html",
    b"<!-- ": "text/html",
    b"<?xml": "image/svg+xml",
}

lock = threading.Lock()
results = {"saved": 0, "failed": 0, "items": [], "fail_reasons": []}
counter = {"idx": 0, "total": len(failed_books)}


def detect_magic(data):
    s = data[:16]
    for head, mime in MAGIC.items():
        if s[:len(head)] == head:
            return mime
    b = data[:500].lower()
    if b"html" in b or b"<!doctype" in b or b"<html" in b:
        return "text/html"
    if b"svg" in b or b"xml" in b:
        return "image/svg+xml"
    return "application/octet-stream"


def ext_from_mime(mime):
    return {"image/png": ".png", "image/svg+xml": ".svg", "image/jpeg": ".jpg",
            "image/gif": ".gif", "image/webp": ".webp", "image/x-icon": ".ico",
            "image/vnd.microsoft.icon": ".ico"}.get(mime, ".bin")


def fetch_url(session, url, timeout=20):
    try:
        r = session.get(url, timeout=(8, timeout), allow_redirects=True, stream=True)
        cl = r.headers.get("Content-Length")
        if cl and int(cl) > 5_000_000:
            return None, "too_large", 0
        data = r.content
        return r, data, len(data)
    except requests.exceptions.Timeout:
        return None, "timeout", 0
    except requests.exceptions.ConnectionError:
        return None, "connection_error", 0
    except requests.exceptions.TooManyRedirects:
        return None, "too_many_redirects", 0
    except Exception as e:
        return None, f"error: {str(e)[:80]}", 0


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
            if prop in ("og:image", "twitter:image") or name in ("twitter:image", "og:image"):
                if content:
                    self._meta.setdefault(prop or name, []).append(content)
        elif tag == "link":
            rel = attrs.get("rel", "").lower()
            href = attrs.get("href", "")
            if rel in ("icon", "apple-touch-icon", "shortcut icon", "mask-icon") and href:
                self.candidates.append(("link:" + rel, href))
        elif tag == "img":
            src = attrs.get("src", "")
            alt = (attrs.get("alt", "") + " " + attrs.get("class", "") + " " + attrs.get("id", "")).lower()
            if src and any(k in alt for k in ["logo", "brand", "icon", "site-logo", "navbar-logo", "header-logo"]):
                self.candidates.append(("img:" + attrs.get("class", ""), src))

    def get_candidates(self, base_url):
        out = []
        seen = set()
        for v in self._meta.values():
            for u in v:
                abs_url = urljoin(base_url, u)
                if abs_url not in seen:
                    seen.add(abs_url)
                    out.append(abs_url)
        for _, u in self.candidates:
            abs_url = urljoin(base_url, u)
            if abs_url not in seen:
                seen.add(abs_url)
                out.append(abs_url)
        return out


def fetch_one(name, domain_url):
    parsed = urlparse(domain_url)
    host = parsed.netloc or parsed.path
    safe = host.replace(".", "_").replace("-", "_")

    session = requests.Session()
    session.headers.update(HEADERS)
    found = False
    fail_reason = "no_image_found"

    # Strategy 1: Try static paths
    for p in PATHS:
        if found:
            break
        url = f"{parsed.scheme}://{host}{p}"
        r, data, size = fetch_url(session, url, timeout=15)
        if r is None:
            fail_reason = data
            continue
        if r.status_code != 200:
            fail_reason = f"http_{r.status_code}"
            continue
        mime = detect_magic(data)
        if size > 300 and mime not in ("text/html", "application/octet-stream"):
            ext = ext_from_mime(mime)
            out = LOGOS_DIR / f"{safe}{ext}"
            out.write_bytes(data)
            with lock:
                counter["idx"] += 1
                idx = counter["idx"]
                results["saved"] += 1
                entry = {"name": name, "domain": host, "status": "saved",
                         "size": size, "content_type": mime,
                         "sha256": hashlib.sha256(data).hexdigest(), "source_url": url}
                results["items"].append(entry)
                print(f"[{idx:03}/{counter['total']}] {name:35} saved {mime} ({size}b) <- {p}")
            found = True
            return entry

    # Strategy 2: Parse homepage for logo candidates
    if not found:
        try:
            homepage = f"{parsed.scheme}://{host}/"
            r, html_data, _ = fetch_url(session, homepage, timeout=20)
            if r and r.status_code == 200 and html_data:
                text = html_data[:300_000].decode("utf-8", errors="ignore")
                parser = LogoHTMLParser()
                parser.feed(text)
                candidates = parser.get_candidates(homepage)

                for cand in candidates[:15]:
                    if found:
                        break
                    r2, data2, size2 = fetch_url(session, cand, timeout=15)
                    if r2 is None:
                        continue
                    if r2.status_code != 200:
                        continue
                    mime = detect_magic(data2)
                    if size2 > 300 and mime not in ("text/html", "application/octet-stream"):
                        ext = ext_from_mime(mime)
                        out = LOGOS_DIR / f"{safe}{ext}"
                        out.write_bytes(data2)
                        with lock:
                            counter["idx"] += 1
                            idx = counter["idx"]
                            results["saved"] += 1
                            entry = {"name": name, "domain": host, "status": "saved",
                                     "size": size2, "content_type": mime,
                                     "sha256": hashlib.sha256(data2).hexdigest(),
                                     "source_url": cand}
                            results["items"].append(entry)
                            print(f"[{idx:03}/{counter['total']}] {name:35} saved {mime} ({size2}b) <- html")
                        found = True
                        return entry
            else:
                fail_reason = f"homepage_{r.status_code if r else 'unreachable'}"
        except Exception as e:
            fail_reason = f"homepage_error: {str(e)[:60]}"

    if not found:
        with lock:
            counter["idx"] += 1
            idx = counter["idx"]
            results["failed"] += 1
            entry = {"name": name, "domain": host, "status": "failed",
                     "size": 0, "content_type": "", "sha256": "", "source_url": ""}
            results["items"].append(entry)
            results["fail_reasons"].append({"name": name, "domain": host, "reason": fail_reason})
            print(f"[{idx:03}/{counter['total']}] {name:35} FAILED ({fail_reason})")
        return entry


# Build work list
work = []
for name, info in failed_books.items():
    domain = info.get("domain", "")
    url = books_dict.get(name, f"https://{domain}")
    work.append((name, url))

print(f"\nStarting fetch of {len(work)} books with 5 workers...\n")

with ThreadPoolExecutor(max_workers=5) as ex:
    futures = {ex.submit(fetch_one, name, url): name for name, url in work}
    for f in as_completed(futures):
        try:
            f.result()
        except Exception as e:
            print(f"  ERROR: {futures[f]}: {e}")

REPORT.write_text(json.dumps({
    "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "total": len(work),
    "saved": results["saved"],
    "failed": results["failed"],
    "items": results["items"],
}, indent=2))

FAIL_LOG.write_text(json.dumps(results["fail_reasons"], indent=2))

print(f"\n{'='*60}")
print(f"COMPLETE: Saved={results['saved']}, Still Failed={results['failed']}")
print(f"Report: {REPORT}")
print(f"Fail log: {FAIL_LOG}")
