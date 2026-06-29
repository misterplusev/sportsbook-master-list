#!/usr/bin/env python3
"""
Fetch logos by parsing HTML og:image / twitter:image / link[rel=icon] tags.
Many sites that 403 on favicon will serve their homepage with proper meta tags.
Also tries Google-like approaches: common CDN paths, press kit pages.
"""
import subprocess, pathlib, time, re, json

ROOT = pathlib.Path("D:/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())
REPORT = ROOT / "proofs" / "html_parse_report.json"
REPORT.parent.mkdir(exist_ok=True)

# Only work on missing books
work = []
for b in books:
    if manifest.get(b["name"], {}).get("status") != "verified":
        from urllib.parse import urlparse
        host = urlparse(b["url"]).netloc.replace("www.", "")
        work.append((b["name"], host))

print(f"Missing: {len(work)} books")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def curl_get(url, max_time=10, accept="text/html,application/xhtml+xml,*/*;q=0.9"):
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", str(max_time),
             "-H", f"User-Agent: {UA}",
             "-H", f"Accept: {accept}",
             "-H", "Accept-Language: en-US,en;q=0.9,en-GB;q=0.8",
             "-H", "Accept-Encoding: identity",
             "-H", "Cache-Control: no-cache",
             "-H", "Pragma: no cache",
             url],
            capture_output=True, timeout=max_time + 5
        )
        return r.stdout.decode("utf-8", errors="replace")
    except:
        return ""

def is_good_image(data):
    if len(data) < 500: return False
    s = data[:20]
    if s[:4] == b'\x89PNG': return True
    if s[:3] == b'\xff\xd8\xff': return True
    if s[:4] == b'RIFF': return True
    if s[:4] == b'GIF8': return True
    if s[:4] == b'\x00\x00\x01\x00': return True
    if s[:5] in (b'<svg ', b'<svg\n'): return True
    if s[:4] == b'<?xm': return True
    low = data[:800].lower()
    if b'<svg' in low and (b'viewbox' in low or b'<path' in low or b'<circle' in low or b'<rect' in low):
        return True
    if b'<!doctype' in low or b'<html' in low: return False
    return False

def ext_from_data(data):
    s = data[:20]
    if s[:4] == b'\x89PNG': return '.png'
    if s[:3] == b'\xff\xd8\xff': return '.jpg'
    if s[:4] == b'RIFF': return '.webp'
    if s[:4] == b'GIF8': return '.gif'
    if s[:4] == b'\x00\x00\x01\x00': return '.ico'
    if s[:5] in (b'<svg ', b'<svg\n'): return '.svg'
    if s[:4] == b'<?xm': return '.svg'
    low = data[:800].lower()
    if b'<svg' in low: return '.svg'
    return '.bin'

def extract_meta_images(html, base_url):
    """Extract image URLs from og:image, twitter:image, link[rel=icon]"""
    from urllib.parse import urlparse
    urls = []
    
    # og:image
    for m in re.finditer(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        urls.append(("og:image", m.group(1)))
    for m in re.finditer(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']', html, re.I):
        urls.append(("og:image", m.group(1)))
    
    # twitter:image / twitter:image:src
    for m in re.finditer(r'<meta[^>]+(?:property|name)=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        urls.append(("twitter:image", m.group(1)))
    for m in re.finditer(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']twitter:image(?::src)?["\']', html, re.I):
        urls.append(("twitter:image", m.group(1)))
    
    # link rel=icon
    for m in re.finditer(r'<link[^>]+rel=["\'](?:icon|shortcut\s+icon|apple-touch-icon|apple-touch-icon-precomposed)["\'][^>]+href=["\']([^"\']+)["\']', html, re.I):
        urls.append(("link-icon", m.group(1)))
    for m in re.finditer(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\'](?:icon|shortcut\s+icon|apple-touch-icon)["\']', html, re.I):
        urls.append(("link-icon", m.group(1)))
    
    # Schema.org ImageObject
    for m in re.finditer(r'"logo"\s*:\s*["\']([^"\']+)["\']', html, re.I):
        urls.append(("json-ld-logo", m.group(1)))
    for m in re.finditer(r'"url"\s*:\s*["\']([^"\']+\.(?:png|svg|jpg|webp|ico))["\']', html, re.I):
        urls.append(("json-ld-url", m.group(1)))
    
    # Resolve relative URLs
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    resolved = []
    for tag, url in urls:
        if url.startswith("http"):
            resolved.append((tag, url))
        elif url.startswith("//"):
            resolved.append((tag, f"https:{url}"))
        elif url.startswith("/"):
            resolved.append((tag, f"{base}{url}"))
        else:
            resolved.append((tag, f"{base}/{url}"))
    
    return resolved

def download_image(url):
    """Download image from URL, return bytes"""
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "12",
             "-H", f"User-Agent: {UA}",
             "-H", "Accept: image/*=0.8",
             url],
            capture_output=True, timeout=16
        )
        return r.stdout
    except:
        return b""

def try_fetch_logo(name, host):
    """Try to fetch logo via HTML meta tags, common paths, CDN fallbacks"""
    safe = host.replace(".", "_").replace("-", "_")
    
    # Strategy 1: Fetch homepage and parse meta tags
    for url in [f"https://{host}", f"https://www.{host}"]:
        html = curl_get(url, max_time=10)
        if not html or len(html) < 200:
            continue
        
        # Check if it's actually HTML (not a redirect page)
        low = html[:500].lower()
        if 'cf-browser-verification' in low or 'just a moment' in low:
            print(f"  [CF] {host}: Cloudflare challenge")
            continue
        
        img_urls = extract_meta_images(html, url)
        if img_urls:
            for tag, img_url in img_urls:
                data = download_image(img_url)
                if is_good_image(data):
                    ext = ext_from_data(data)
                    out = LOGOS_DIR / f"{safe}{ext}"
                    out.write_bytes(data)
                    return {"status": "saved", "method": tag, "source": img_url, "size": len(data)}
    
    # Strategy 2: Try common CDN/logo endpoints
    cdn_urls = [
        f"https://{host}/logo.png",
        f"https://{host}/logo.svg",
        f"https://{host}/images/logo.png",
        f"https://{host}/images/logo.svg",
        f"https://{host}/assets/logo.png",
        f"https://{host}/assets/logo.svg",
        f"https://static.{host}/logo.png",
        f"https://{host}/cdn/logo.png",
        f"https://{host}/uploads/logo.png",
    ]
    
    for url in cdn_urls:
        data = download_image(url)
        if is_good_image(data):
            ext = ext_from_data(data)
            out = LOGOS_DIR / f"{safe}{ext}"
            out.write_bytes(data)
            return {"status": "saved", "method": "cdn_path", "source": url, "size": len(data)}
    
    return {"status": "failed"}

# Process all missing books
results = []
saved_count = 0

for i, (name, host) in enumerate(work):
    print(f"[{i+1}/{len(work)}] {name} ({host})...", end=" ")
    r = try_fetch_logo(name, host)
    r["name"] = name
    r["domain"] = host
    results.append(r)
    if r["status"] == "saved":
        saved_count += 1
        print(f"✓ {r['method']} {r['source']} ({r['size']}b)")
    else:
        print("✗")

print(f"\n{'='*60}")
print(f"RESULT: {saved_count}/{len(work)} recovered via HTML parse")
print(f"{'='*60}")

REPORT.write_text(json.dumps(results, indent=2))
