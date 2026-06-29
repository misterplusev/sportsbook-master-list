#!/usr/bin/env python3
"""
fetch_logos_v5.py — aggressive parallel logo recovery for missing books.
Uses curl with many paths, HTML og:image/twitter:image extraction,
and subdomain/CDN fallbacks.
"""
import os, json, hashlib, time, pathlib, subprocess, sys, re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "logos"
REPORT = ROOT / "proofs" / "fetch_v5_report.json"
LOGOS_DIR.mkdir(parents=True, exist_ok=True)
(REPORT.parent).mkdir(parents=True, exist_ok=True)

# Load books + manifest to find what's missing
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())

# Build work list: all missing books
work = []
for b in books:
    host = urlparse(b["url"]).netloc.replace("www.", "")
    if manifest.get(b["name"], {}).get("status") != "verified":
        work.append((b["name"], host))

print(f"Missing logos: {len(work)} books")

# Magic bytes
def is_image(data):
    if len(data) < 300: return False
    head = data[:20]
    if head[:4] == b"\x89PNG": return True
    if head[:3] == b"\xff\xd8\xff": return True
    if head[:4] == b"RIFF": return True
    if head[:4] == b"GIF8": return True
    if head[:4] == b"\x00\x00\x01\x00": return True
    if head[:5] in (b"<svg ", b"<svg\n"): return True
    if head[:4] == b"<?xm": return True
    low = data[:500].lower()
    if b"<svg" in low and b"svg" in low: return True
    if b"<!doctype" in low or b"<html" in low: return False
    return False

def ext_from_data(data):
    head = data[:20]
    if head[:4] == b"\x89PNG": return ".png"
    if head[:3] == b"\xff\xd8\xff": return ".jpg"
    if head[:4] == b"RIFF": return ".webp"
    if head[:4] == b"GIF8": return ".gif"
    if head[:4] == b"\x00\x00\x01\x00": return ".ico"
    if head[:5] in (b"<svg ", b"<svg\n"): return ".svg"
    if head[:4] == b"<?xm": return ".svg"
    low = data[:500].lower()
    if b"<svg" in low: return ".svg"
    return ".bin"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def curl_fetch(url, max_time=8):
    """Fetch URL with curl, return (data, http_code)"""
    try:
        r = subprocess.run(
            ["curl", "-sSL",  # follow redirects
             "-o", "-", "-w", "\n%{http_code}",
             "--max-time", str(max_time),
             "-H", f"User-Agent: {UA}",
             "-H", "Accept: image/*,*/*;q=0.8",
             "-H", "Accept-Language: en-US,en;q=0.9",
             url],
            capture_output=True, timeout=max_time + 4
        )
        out = r.stdout.decode("latin-1", errors="replace")
        lines = out.rsplit("\n", 1)
        if len(lines) == 2:
            data = lines[0].encode("latin-1")
            code = lines[1].strip()
        else:
            data = r.stdout
            code = "200"
        return data, code
    except:
        return b"", "000"

def curl_fetch_html(url, max_time=10):
    """Fetch HTML page and return text"""
    try:
        r = subprocess.run(
            ["curl", "-sSL",
             "--max-time", str(max_time),
             "-H", f"User-Agent: {UA}",
             "-H", "Accept: text/html,application/xhtml+xml,*/*;q=0.8",
             "-H", "Accept-Language: en-US,en;q=0.9",
             url],
            capture_output=True, timeout=max_time + 4
        )
        return r.stdout.decode("utf-8", errors="replace")
    except:
        return ""

FAST_PATHS = [
    "/favicon.ico", "/favicon.png", "/favicon.svg",
    "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png",
    "/logo.svg", "/logo.png", "/logo.jpg", "/logo.webp",
    "/logo-dark.svg", "/logo-dark.png", "/logo-light.svg", "/logo-light.png",
    "/images/favicon.ico", "/images/favicon.png", "/images/favicon.svg",
    "/images/logo.svg", "/images/logo.png", "/images/logo.jpg",
    "/static/favicon.ico", "/static/favicon.png",
    "/static/logo.svg", "/static/logo.png",
    "/assets/favicon.ico", "/assets/favicon.png",
    "/assets/logo.svg", "/assets/logo.png", "/assets/logo.jpg",
    "/img/favicon.ico", "/img/favicon.png",
    "/img/logo.svg", "/img/logo.png",
    "/brand/logo.svg", "/brand/logo.png",
    "/images/brand-logo.svg", "/images/brand-logo.png",
    "/cdn/images/logo.svg", "/cdn/images/logo.png",
    "/uploads/logo.svg", "/uploads/logo.png",
    "/content/dam/logo.svg", "/content/dam/logo.png",
    "/-/media/logo.svg", "/-/media/logo.png",
    "/-/media/brand/logo.svg", "/-/media/brand/logo.png",
    "/dist/images/logo.svg", "/dist/images/logo.png",
    "/public/images/logo.svg", "/public/images/logo.png",
    "/wp-content/uploads/logo.svg", "/wp-content/uploads/logo.png",
    "/sprite.svg", "/sprites.svg",
    "/logo-header.svg", "/logo-header.png",
    "/logo-footer.svg", "/logo-footer.png",
    "/images/header-logo.svg", "/images/header-logo.png",
    "/images/main-logo.svg", "/images/main-logo.png",
    "/assets/img/logo.svg", "/assets/img/logo.png",
    "/img/brand/logo.svg", "/img/brand/logo.png",
    "/media/logo.svg", "/media/logo.png",
    "/pictures/logo.svg", "/pictures/logo.png",
    "/resources/logo.svg", "/resources/logo.png",
    "/img/Logo.svg", "/img/Logo.png",  # case variants
    "/Images/logo.svg", "/Images/logo.png",
    "/graphics/logo.svg", "/graphics/logo.png",
]

EXTENDED_PATHS = [
    "/sites/default/files/logo.svg",  # Drupal
    "/application/images/logo.png",
    "/uploads/settings/logo.png",
    "/uploads/images/logo.png",
    "/storage/images/logo.png",
    "/img/logo@2x.png",
    "/img/logo@2x.svg",
    "/images/logo@2x.png",
    "/images/logo-white.png",
    "/images/logo-black.png",
    "/images/logo-color.png",
    "/logos/logo.svg", "/logos/logo.png",
    "/img/logos/logo.svg", "/img/logos/logo.png",
]

SUBDOMAINS = ["www", "cdn", "static", "assets", "media", "img", "api", "app"]

def extract_image_urls_from_html(html, base_url):
    """Extract all image URLs from HTML, prioritize og:image and twitter:image"""
    urls = []
    # og:image
    for match in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        urls.append(("og:image", match.group(1)))
    for match in re.finditer(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I):
        urls.append(("og:image", match.group(1)))
    # twitter:image
    for match in re.finditer(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        urls.append(("twitter:image", match.group(1)))
    # link rel=icon
    for match in re.finditer(r'<link[^>]+rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'][^>]+href=["\']([^"\']+)["\']', html, re.I):
        urls.append(("link-icon", match.group(1)))
    for match in re.finditer(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\']', html, re.I):
        urls.append(("link-icon", match.group(1)))
    # img src with logo in path
    for match in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I):
        src = match.group(1)
        if any(k in src.lower() for k in ['logo', 'brand', 'header-logo', 'main-logo']):
            urls.append(("img-logo", src))
    return urls

def resolve_url(url, base_url):
    """Resolve relative URL against base"""
    if url.startswith("http"):
        return url
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{url}"
    return url

def fetch_one(name, host):
    """Try to fetch logo for a single book"""
    safe = host.replace(".", "_").replace("-", "_")
    out_file = None
    source_url = ""
    
    # Phase 1: Fast paths
    for path in FAST_PATHS:
        url = f"https://{host}{path}"
        data, code = curl_fetch(url)
        if code == "200" and is_image(data):
            ext = ext_from_data(data)
            out_file = LOGOS_DIR / f"{safe}{ext}"
            out_file.write_bytes(data)
            source_url = url
            return {"name": name, "domain": host, "status": "saved",
                    "size": len(data), "source_url": source_url,
                    "file": out_file.name, "sha256": hashlib.sha256(data).hexdigest(),
                    "method": "fast_path"}
    
    # Phase 2: HTML parse for og:image/twitter:image
    html = curl_fetch_html(f"https://{host}")
    if not html:
        html = curl_fetch_html(f"https://www.{host}")
    
    if html:
        img_urls = extract_image_urls_from_html(html, f"https://{host}")
        for tag, img_url in img_urls:
            resolved = resolve_url(img_url, f"https://{host}")
            data, code = curl_fetch(resolved, max_time=10)
            if code == "200" and is_image(data) and len(data) > 500:
                ext = ext_from_data(data)
                out_file = LOGOS_DIR / f"{safe}{ext}"
                out_file.write_bytes(data)
                source_url = resolved
                return {"name": name, "domain": host, "status": "saved",
                        "size": len(data), "source_url": source_url,
                        "file": out_file.name, "sha256": hashlib.sha256(data).hexdigest(),
                        "method": f"html_{tag}"}
    
    # Phase 3: Extended paths
    for path in EXTENDED_PATHS:
        url = f"https://{host}{path}"
        data, code = curl_fetch(url)
        if code == "200" and is_image(data):
            ext = ext_from_data(data)
            out_file = LOGOS_DIR / f"{safe}{ext}"
            out_file.write_bytes(data)
            source_url = url
            return {"name": name, "domain": host, "status": "saved",
                    "size": len(data), "source_url": source_url,
                    "file": out_file.name, "sha256": hashlib.sha256(data).hexdigest(),
                    "method": "extended_path"}
    
    # Phase 4: Try www subdomain with fast paths
    if not host.startswith("www."):
        for path in FAST_PATHS[:10]:
            url = f"https://www.{host}{path}"
            data, code = curl_fetch(url)
            if code == "200" and is_image(data):
                ext = ext_from_data(data)
                out_file = LOGOS_DIR / f"{safe}{ext}"
                out_file.write_bytes(data)
                source_url = url
                return {"name": name, "domain": host, "status": "saved",
                        "size": len(data), "source_url": source_url,
                        "file": out_file.name, "sha256": hashlib.sha256(data).hexdigest(),
                        "method": "www_subdomain"}
        
        # Try subdomain variations
        for sub in SUBDOMAINS:
            for path in ["/favicon.ico", "/logo.svg", "/logo.png"]:
                url = f"https://{sub}.{host}{path}"
                data, code = curl_fetch(url)
                if code == "200" and is_image(data):
                    ext = ext_from_data(data)
                    out_file = LOGOS_DIR / f"{safe}{ext}"
                    out_file.write_bytes(data)
                    source_url = url
                    return {"name": name, "domain": host, "status": "saved",
                            "size": len(data), "source_url": source_url,
                            "file": out_file.name, "sha256": hashlib.sha256(data).hexdigest(),
                            "method": "subdomain"}
    
    return {"name": name, "domain": host, "status": "failed"}

# === RUN ===
print(f"\nFetching {len(work)} books with 25 parallel curl workers...\n")

results = []
saved_count = 0
with ThreadPoolExecutor(max_workers=25) as ex:
    futures = {ex.submit(fetch_one, name, host): (name, host) for name, host in work}
    done = 0
    for f in as_completed(futures):
        done += 1
        try:
            r = f.result()
        except Exception as e:
            name, host = futures[f]
            r = {"name": name, "domain": host, "status": "error", "error": str(e)}
        results.append(r)
        if r["status"] == "saved":
            saved_count += 1
            print(f"  ✓ {r['name']:45} {r['method']:20} {r['source_url']} ({r['size']}b)")
        if done % 10 == 0:
            print(f"  --- {done}/{len(work)} done, {saved_count} saved ---")

# Summary
saved = [r for r in results if r["status"] == "saved"]
failed = [r for r in results if r["status"] == "failed"]

print(f"\n{'='*60}")
print(f"RESULT: Saved={len(saved)}, Failed={len(failed)}")
print(f"{'='*60}")

if failed:
    print(f"\nFAILED (browser recovery needed):")
    for r in failed:
        print(f"  {r['name']} — {r['domain']}")

# Save report
REPORT.write_text(json.dumps({
    "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "total": len(work),
    "saved": len(saved),
    "failed": len(failed),
    "items": results,
}, indent=2))

print(f"\nReport: {REPORT}")
