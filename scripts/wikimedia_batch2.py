#!/usr/bin/env python3
"""
search_wikimedia_batch.py — search Wikimedia Commons API for ALL remaining brands.
Uses the MediaWiki API search that's NOT blocked.
Then we batch download via Special:FilePath.
"""
import subprocess, pathlib, time, json, sys

ROOT = pathlib.Path("D:/sportsbook-master-list")
books_list = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())

from urllib.parse import urlparse

missing = []
for b in books_list:
    if manifest.get(b["name"], {}).get("status") != "verified":
        host = urlparse(b["url"]).netloc.replace("www.", "")
        brand = host.split(".")[0]
        missing.append({"name": b["name"], "host": host, "brand": brand})

print(f"Missing: {len(missing)} books")
sys.stdout.flush()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

def search_wikimedia_api(query):
    """Search Wikimedia Commons API directly"""
    url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={query}+logo+sportsbook&srnamespace=6&format=json&srlimit=10"
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "10",
             "-H", f"User-Agent: {UA}",
             "-H", "Api-User-Agent: SportsbookLogoFinder/1.0",
             url],
            capture_output=True, timeout=15
        )
        data = json.loads(r.stdout)
        results = []
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            if title.startswith("File:"):
                fname = title[5:]
                # Skip non-image files
                if any(fname.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.svg', '.gif', '.webp']):
                    results.append(fname)
        return results
    except:
        return []

def download_wmf_file(filename):
    """Download from Wikimedia via Special:FilePath with the actual filename"""
    # Encode filename for URL
    encoded = filename.replace(" ", "_")
    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}"
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "15",
             "-H", f"User-Agent: {UA}",
             url],
            capture_output=True, timeout=20
        )
        data = r.stdout
        if len(data) < 300:
            return None
        s = data[:20]
        # Check it's really an image
        if s[:4] == b'\x89PNG': return data
        if s[:3] == b'\xff\xd8\xff': return data
        if s[:4] == b'RIFF': return data
        if s[:4] == b'GIF8': return data
        if s[:5] in (b'<svg ', b'<svg\n'): return data
        if s[:4] == b'<?xm': return data
        low = data[:500].lower()
        if b'<svg' in low and (b'viewbox' in low or b'<path' in low): return data
        if b'<!doctype' in low or (b'<html' in low and b'<svg' not in low[:50]): return None
        return None
    except:
        return None

def ext_from_data(data):
    if not data: return '.bin'
    s = data[:20]
    if s[:4] == b'\x89PNG': return '.png'
    if s[:3] == b'\xff\xd8\xff': return '.jpg'
    if s[:4] == b'RIFF': return '.webp'
    if s[:4] == b'GIF8': return '.gif'
    if s[:5] in (b'<svg ', b'<svg\n'): return '.svg'
    low = data[:800].lower()
    if b'<svg' in low: return '.svg'
    return '.bin'

LOGOS_DIR = ROOT / "logos"
results = []
saved = 0

for i, item in enumerate(missing):
    name = item["name"]
    host = item["host"]
    brand = item["brand"]
    safe = host.replace(".", "_").replace("-", "_")
    
    print(f"[{i+1}/{len(missing)}] {name}...", end=" ", flush=True)
    
    # Try various search queries
    queries = [
        f"{brand} logo",
        f"{name} logo", 
        f"{brand} sportsbook",
        host.split(".")[0].replace("-", " ") + " betting logo",
    ]
    
    found = False
    for query in queries:
        files = search_wikimedia_api(query)
        for filename in files:
            data = download_wmf_file(filename)
            if data:
                ext = ext_from_data(data)
                out = LOGOS_DIR / f"{safe}{ext}"
                out.write_bytes(data)
                saved += 1
                found = True
                print(f"✓ {filename} ({len(data)}b)")
                results.append({"name": name, "host": host, "status": "saved", "source": f"wikimedia:{filename}", "size": len(data)})
                break
        if found:
            break
        time.sleep(0.5)
    
    if not found:
        print("�")
        results.append({"name": name, "host": host, "status": "failed"})
    
    sys.stdout.flush()
    time.sleep(0.4)

print(f"\n{'='*60}")
print(f"WIKIMEDIA: {saved}/{len(missing)} recovered")
print(f"{'='*60}")

report_path = ROOT / "proofs" / "wikimedia_batch2.json"
report_path.write_text(json.dumps(results, indent=2))
print(f"Report: {report_path}")
