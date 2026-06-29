#!/usr/bin/env python3
"""
Try common CDN/media paths for blocked sportsbooks.
Also download from known logo aggregator CDNs.
"""
import subprocess, pathlib, time, re, json, sys

ROOT = pathlib.Path("D:/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())

from urllib.parse import urlparse
missing = []
for b in books:
    if manifest.get(b["name"], {}).get("status") != "verified":
        host = urlparse(b["url"]).netloc.replace("www.", "")
        missing.append((b["name"], host))

print(f"Missing: {len(missing)} books")
sys.stdout.flush()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Known CDN patterns from iGaming industry
CDN_PATTERNS = [
    "https://cdn.{host}/logo{suffix}",
    "https://cdn.{host}/images/logo{suffix}",
    "https://cdn.{host}/assets/logo{suffix}",
    "https://static.{host}/logo{suffix}",
    "https://static.{host}/images/logo{suffix}",
    "https://static.{host}/img/logo{suffix}",
    "https://static.{host}/assets/logo{suffix}",
    "https://images.{host}/logo{suffix}",
    "https://assets.{host}/logo{suffix}",
    "https://media.{host}/logo{suffix}",
    "https://www.{host}/media/logo{suffix}",
    "https://www.{host}/images/logo{suffix}",
    "https://www.{host}/img/logo{suffix}",
    "https://www.{host}/assets/logo{suffix}",
    "https://www.{host}/static/logo{suffix}",
    "https://www.{host}/content/dam/{tld}/logo{suffix}",
    "https://www.{host}/-/media/logo{suffix}",
    "https://www.{host}/uploads/logo{suffix}",
    "https://www.{host}/wp-content/uploads/2024/01/logo{suffix}",
    "https://www.{host}/wp-content/uploads/2024/logo{suffix}",
    "https://www.{host}/wp-content/themes/{tld}/images/logo{suffix}",
]

EXTENSIONS = [".png", ".svg", ".jpg", ".webp", ".ico"]

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

def fetch_img(url, timeout=8):
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", str(timeout),
             "-H", f"User-Agent: {UA}",
             url],
            capture_output=True, timeout=timeout+4
        )
        return r.stdout
    except:
        return b""

results = []
saved_count = 0

for i, (name, host) in enumerate(missing):
    safe = host.replace(".", "_").replace("-", "_")
    tld = host.split(".")[0]
    found = False
    
    for pattern in CDN_PATTERNS:
        for ext in EXTENSIONS:
            url = pattern.format(host=host, suffix=ext, tld=tld)
            data = fetch_img(url, timeout=6)
            if is_good_image(data):
                e = ext_from_data(data)
                out = LOGOS_DIR / f"{safe}{e}"
                out.write_bytes(data)
                saved_count += 1
                found = True
                print(f"[{i+1}/{len(missing)}] {name} -> {url} ({len(data)}b)")
                results.append({"name": name, "domain": host, "status": "saved", "source": url})
                break
        if found:
            break
    
    if not found:
        print(f"[{i+1}/{len(missing)}] {name} -> ✗")
        results.append({"name": name, "domain": host, "status": "failed"})
    
    sys.stdout.flush()

print(f"\n{'='*60}")
print(f"RESULT: {saved_count}/{len(missing)} recovered")
print(f"{'='*60}")

report_path = ROOT / "proofs" / "cdn_path_logos.json"
report_path.write_text(json.dumps(results, indent=2))
