#!/usr/bin/env python3
"""Logo fetcher v6 - uses curl to get homepage HTML, extracts logo URLs, downloads them"""
import json, hashlib, pathlib, re, subprocess, time
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "logos"
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())
missing = [b for b in books if manifest.get(b["name"], {}).get("status") != "verified"]

print(f"Missing: {len(missing)} books")

MAGIC = {b"\x89PNG\r\n\x1a\n":"png", b"<svg":"svg", b"<?xml":"svg", b"GIF87a":"gif",
         b"GIF89a":"gif", b"\xff\xd8\xff":"jpg", b"RIFF":"webp", b"\x00\x00\x01\x00":"ico"}

def is_img(data):
    if len(data) < 300: return False
    s = data[:16]
    for h, ext in MAGIC.items():
        if s[:len(h)] == h: return ext
    low = data[:500].lower()
    if b"<svg" in low: return "svg"
    if b"<!doctype" in low or b"<html" in low: return False
    return False

def curl_get(url, timeout=10):
    try:
        r = subprocess.run(
            ["curl", "-sS", "-o", "-", "-w", "%{http_code}", "--max-time", str(timeout),
             "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
             "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
             "-H", "Accept-Language: en-US,en;q=0.5",
             url],
            capture_output=True, timeout=timeout+3)
        code = r.stdout.decode().strip()[-3:]
        return r.stdout, code
    except:
        return b"", "000"

def extract_logo_urls(html, base_url):
    """Extract logo URLs from HTML meta tags and common patterns"""
    urls = []
    # og:image
    for m in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        urls.append(urljoin(base_url, m.group(1)))
    # twitter:image
    for m in re.finditer(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        urls.append(urljoin(base_url, m.group(1)))
    # link rel=icon
    for m in re.finditer(r'<link[^>]+rel=["\'](?:icon|shortcut icon|apple-touch-icon|mask-icon)["\'][^>]+href=["\']([^"\']+)["\']', html, re.I):
        urls.append(urljoin(base_url, m.group(1)))
    # img with logo in class/id/alt
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html, re.I):
        src = m.group(1)
        full = html[max(0,m.start()-100):m.end()]
        if any(k in full.lower() for k in ['logo', 'brand', 'site-logo', 'navbar-logo', 'header-logo']):
            urls.append(urljoin(base_url, src))
    # SVG logo inline or referenced
    for m in re.finditer(r'(?:src|href|url)\(["\']?([^"\')]+\.svg)["\']?\)', html, re.I):
        urls.append(urljoin(base_url, m.group(1)))
    # data-src lazy loaded
    for m in re.finditer(r'data-src=["\']([^"\']+)["\']', html, re.I):
        full = html[max(0,m.start()-50):m.end()]
        if any(k in full.lower() for k in ['logo', 'brand']):
            urls.append(urljoin(base_url, m.group(1)))
    return urls

def fetch_one(b):
    host = urlparse(b["url"]).netloc.replace("www.", "")
    safe = host.replace(".","_").replace("-","_")
    
    # Check if already has a file
    for ext in [".png",".svg",".jpg",".webp",".ico"]:
        if (LOGOS_DIR / f"{safe}{ext}").exists():
            return None
    
    base_url = f"https://{host}/"
    
    # Strategy 1: Try static paths first (fast)
    static_paths = [
        "/favicon.ico", "/favicon.png", "/apple-touch-icon.png",
        "/logo.svg", "/logo.png", "/logo.jpg",
        "/images/favicon.ico", "/images/logo.svg", "/images/logo.png",
        "/static/favicon.ico", "/static/logo.svg", "/static/logo.png",
        "/assets/favicon.ico", "/assets/logo.svg", "/assets/logo.png",
        "/img/favicon.ico", "/img/logo.svg", "/img/logo.png",
        "/favicons/favicon.ico", "/favicons/favicon.png",
        "/images/brand-logo.svg", "/images/brand-logo.png",
        "/images/primary-logo.svg", "/images/primary-logo.png",
        "/cdn/images/logo.svg", "/cdn/images/logo.png",
        "/uploads/logo.svg", "/uploads/logo.png",
        "/content/dam/logo.svg", "/content/dam/logo.png",
        "/-/media/logo.svg", "/-/media/logo.png",
        "/-/media/brand/logo.svg", "/-/media/brand/logo.png",
        "/dist/images/logo.svg", "/dist/images/logo.png",
        "/public/images/logo.svg", "/public/images/logo.png",
        "/build/images/logo.svg", "/build/images/logo.png",
        "/wp-content/uploads/logo.svg", "/wp-content/uploads/logo.png",
        "/themes/logo.svg", "/themes/logo.png",
        "/styles/logo.svg", "/styles/logo.png",
        "/brand/logo.svg", "/brand/logo.png",
        "/-/media/brand/logo/main.svg", "/-/media/brand/logo/main.png",
        "/logo-dark.svg", "/logo-dark.png",
        "/logo-light.svg", "/logo-light.png",
        "/logo-white.svg", "/logo-white.png",
        "/images/logo-main.svg", "/images/logo-main.png",
        "/img/brand-logo.svg", "/img/brand-logo.png",
        "/assets/img/logo.svg", "/assets/img/logo.png",
        "/img/brand/logo.svg", "/img/brand/logo.png",
    ]
    
    for p in static_paths:
        data, code = curl_get(f"https://{host}{p}")
        ext = is_img(data)
        if ext:
            out = LOGOS_DIR / f"{safe}.{ext}"
            out.write_bytes(data)
            return (b["name"], p, len(data), ext)
    
    # Strategy 2: Parse homepage HTML for logo URLs
    html_data, html_code = curl_get(base_url)
    if html_code == "200" and html_data:
        try:
            html = html_data[:500000].decode("utf-8", errors="ignore")
        except:
            html = ""
        if html:
            logo_urls = extract_logo_urls(html, base_url)
            for logo_url in logo_urls[:15]:
                data2, code2 = curl_get(logo_url)
                ext = is_img(data2)
                if ext:
                    out = LOGOS_DIR / f"{safe}.{ext}"
                    out.write_bytes(data2)
                    return (b["name"], f"html_parse:{logo_url}", len(data2), ext)
    
    # Strategy 3: Try www variant
    if not host.startswith("www."):
        for p in ["/favicon.ico", "/logo.svg", "/logo.png"]:
            data, code = curl_get(f"https://www.{host}{p}")
            ext = is_img(data)
            if ext:
                out = LOGOS_DIR / f"{safe}.{ext}"
                out.write_bytes(data)
                return (b["name"], f"www{p}", len(data), ext)
    
    return None

saved = 0
t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as ex:
    futures = {ex.submit(fetch_one, b): b for b in missing}
    done = 0
    for f in as_completed(futures):
        done += 1
        result = f.result()
        if result:
            name, path, size, ext = result
            print(f"  + {name:40} {path} ({size}b {ext})")
            saved += 1
        if done % 10 == 0:
            print(f"  ... {done}/{len(missing)} checked, {saved} saved so far")

elapsed = time.time() - t0
print(f"\nDone in {elapsed:.0f}s — saved {saved} new logos")
