#!/usr/bin/env python3
"""
Find logos for blocked sportsbooks by searching the web for hotlinkable URLs.
Uses curl to fetch pages from review/news sites, extracts logo image URLs,
and downloads them. The key insight: curl can SEND requests to review sites
(just not to the sportsbooks themselves).
"""
import subprocess, pathlib, time, re, json, sys

ROOT = pathlib.Path("D:/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())

# Get missing books
from urllib.parse import urlparse
missing = []
for b in books:
    if manifest.get(b["name"], {}).get("status") != "verified":
        host = urlparse(b["url"]).netloc.replace("www.", "")
        missing.append((b["name"], host))

print(f"Missing: {len(missing)} books")
sys.stdout.flush()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def curl_get(url, timeout=8):
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", str(timeout),
             "-H", f"User-Agent: {UA}",
             "-H", "Accept: text/html,*/*;q=0.5",
             url],
            capture_output=True, timeout=timeout+3
        )
        return r.stdout.decode("utf-8", errors="replace")
    except:
        return ""

def is_good_image(data):
    if not data or len(data) < 500: return False
    s = data[:16]
    if s[:4] == b'\x89PNG': return True
    if s[:3] == b'\xff\xd8\xff': return True
    if s[:4] == b'RIFF': return True
    if s[:4] == b'GIF8': return True
    if s[:4] == b'\x00\x00\x01\x00': return True
    if s[:5] in (b'<svg ', b'<svg\n'): return True
    low = data[:500].lower()
    if b'<svg' in low and (b'viewbox' in low or b'<path' in low): return True
    if b'<!doctype' in low or b'<html' in low: return False
    return False

def ext_from_data(data):
    s = data[:16]
    if s[:4] == b'\x89PNG': return '.png'
    if s[:3] == b'\xff\xd8\xff': return '.jpg'
    if s[:4] == b'RIFF': return '.webp'
    if s[:4] == b'GIF8': return '.gif'
    if s[:4] == b'\x00\x00\x01\x00': return '.ico'
    if s[:5] in (b'<svg ', b'<svg\n'): return '.svg'
    low = data[:500].lower()
    if b'<svg' in low: return '.svg'
    return '.bin'

def fetch_image(url, timeout=12):
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", str(timeout),
             "-H", f"User-Agent: {UA}",
             "-H", "Accept: image/*,*/*;q=0.5",
             url],
            capture_output=True, timeout=timeout+4
        )
        return r.stdout
    except:
        return b""

def resolve_url(url, base):
    from urllib.parse import urlparse
    p = urlparse(base)
    base_prefix = f"{p.scheme}://{p.netloc}"
    if url.startswith("http"): return url
    if url.startswith("//"): return f"https:{url}"
    if url.startswith("/"): return f"{base_prefix}{url}"
    return f"{base_prefix}/{url}"

def try_review_sites(name, host):
    """Try to find logos on review/news/CDN sites"""
    safe = host.replace(".", "_").replace("-", "_")
    
    # List of review/news sites that typically have sportsbook logos
    search_targets = [
        # iGaming business
        ("https://igamingbusiness.com/?s=" + name.replace(" ", "+"), "igb"),
        # GamblersPost
        ("https://gamblerspost.com/?s=" + name.replace(" ", "+"), "gp"),
        # Covers.com
        ("https://www.covers.com/sportsbooks", "covers"),
        # RG.org reviews  
        ("https://rg.org/sportsbooks/review/" + host.split('.')[0], "rg"),
    ]
    
    # Also try CDN/s3 buckets directly (common patterns for casinos)
    direct_logo_urls = [
        f"https://cdn.{host}/logo.png",
        f"https://cdn.{host}/logo.svg",
        f"https://cdn.{host}/favicon.ico",
        f"https://static.{host}/logo.png",
        f"https://static.{host}/logo.svg",
        f"https://static.{host}/images/logo.png",
        f"https://images.{host}/logo.png",
        f"https://assets.{host}/logo.png",
        f"https://media.{host}/logo.png",
        f"https://www.{host}/wp-content/uploads/logo.png",
        f"https://www.{host}/wp-content/uploads/logo.svg",
        f"https://i.imgur.com/{host.split('.')[0]}logo.png",  # some use imgur
    ]
    
    # Also check common CDN patterns
    for url in direct_logo_urls:
        data = fetch_image(url)
        if is_good_image(data):
            ext = ext_from_data(data)
            out = LOGOS_DIR / f"{safe}{ext}"
            out.write_bytes(data)
            return {"status": "saved", "source": url, "size": len(data), "method": "direct_cdn"}
    
    # Try review sites
    for url, tag in search_targets:
        html = curl_get(url)
        if not html or len(html) < 500: continue
        
        # Look for logo images with the sportsbook name
        name_lower = name.lower().replace(" ", "")
        patterns = [
            rf'src=["\']([^"\']*{host.split(".")[0]}[^"\']*\.(?:png|svg|jpg|webp))["\']',
            rf'src=["\']([^"\']*logo[^"\']*{host.split(".")[0]}[^"\']*)["\']',
            rf'src=["\']([^"\']*{host.split(".")[0]}[^"\']*logo[^"\']*)["\']',
            rf'href=["\']([^"\']*{host.split(".")[0]}[^"\']*\.(?:png|svg|jpg|webp))["\']',
            # Any image containing book name
            rf'src=["\']([^"\']*(?:{name_lower}|{host.split(".")[0]})[^"\']*\.(?:png|svg|jpg|webp))["\']',
        ]
        
        img_urls = []
        for pat in patterns:
            for m in re.finditer(pat, html, re.I):
                img_url = m.group(1)
                if img_url.startswith("http"):
                    img_urls.append(img_url)
        
        for img_url in img_urls:
            data = fetch_image(img_url)
            if is_good_image(data):
                ext = ext_from_data(data)
                out = LOGOS_DIR / f"{safe}{ext}"
                out.write_bytes(data)
                return {"status": "saved", "source": img_url, "size": len(data), "method": f"review_{tag}"}
    
    return {"status": "failed"}


# Process each missing book
results = []
saved_count = 0

for i, (name, host) in enumerate(missing):
    print(f"[{i+1}/{len(missing)}] {name}...", end=" ", flush=True)
    r = try_review_sites(name, host)
    r["name"] = name
    r["domain"] = host
    results.append(r)
    if r["status"] == "saved":
        saved_count += 1
        print(f"✓ {r['method']} {r['source'][:60]} ({r['size']}b)")
    else:
        print("✗")
    sys.stdout.flush()

print(f"\n{'='*60}")
print(f"RESULT: {saved_count}/{len(missing)} recovered from review sites")
print(f"{'='*60}")

# Save report
report_path = ROOT / "proofs" / "review_site_logos.json"
report_path.write_text(json.dumps(results, indent=2))
