#!/usr/bin/env python3
"""
mass_wikimedia_search.py — search Wikimedia Commons for all missing sportsbooks.
Uses web_search to find file names, then downloads via Special:FilePath.
"""
import subprocess, pathlib, time, json, sys, re

ROOT = pathlib.Path("D:/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
books_list = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())

from urllib.parse import urlparse

missing = []
for b in books_list:
    if manifest.get(b["name"], {}).get("status") != "verified":
        host = urlparse(b["url"]).netloc.replace("www.", "")
        # Generate search terms from name and host
        brand = host.split(".")[0]  # e.g. "betvictor" from "betvictor.com"
        missing.append({
            "name": b["name"],
            "host": host,
            "brand": brand,
            "search_terms": [brand, host.split(".")[0], b["name"]]
        })

print(f"Missing: {len(missing)} books")
print("Will search Wikimedia Commons for each brand using curl.")
sys.stdout.flush()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def search_wikimedia(brand):
    """Search Wikimedia Commons API for a brand logo"""
    url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={brand}+logo&srnamespace=6&format=json&srlimit=5"
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "8",
             "-H", f"User-Agent: {UA}",
             url],
            capture_output=True, timeout=12
        )
        data = json.loads(r.stdout)
        results = []
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            if title.startswith("File:"):
                results.append(title[5:])  # Remove "File:" prefix
        return results
    except:
        return []

def download_wikimedia(filename):
    """Download a file from Wikimedia Commons"""
    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}"
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "10",
             "-H", f"User-Agent: {UA}",
             url],
            capture_output=True, timeout=14
        )
        data = r.stdout
        if len(data) < 500: return None
        s = data[:20]
        # Check it's an actual image
        if s[:4] == b'\x89PNG': return data
        if s[:3] == b'\xff\xd8\xff': return data
        if s[:4] == b'RIFF': return data
        if s[:4] == b'GIF8': return data
        if s[:4] in (b'\x00\x00\x01\x00', b'\x00\x00\x02\x00'): return data
        if s[:5] in (b'<svg ', b'<svg\n') or (s[:4] == b'<?xm'): return data
        low = data[:500].lower()
        if b'<!doctype' in low or (b'<html' in low and b'<svg' not in low[:50]): return None
        if b'<svg' in low and (b'viewbox' in low or b'<path' in low): return data
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
    low = data[:500].lower()
    if b'<svg' in low: return '.svg'
    return '.bin'

# Process eachbook
results = []
saved = 0

for i, item in enumerate(missing):
    name = item["name"]
    host = item["host"]
    brand = item["brand"]
    safe = host.replace(".", "_").replace("-", "_")
    
    print(f"[{i+1}/{len(missing)}] {name} ({host})...", end=" ", flush=True)
    
    # Search Wikimedia Commons
    files = search_wikimedia(brand)
    
    found = False
    for filename in files:
        data = download_wikimedia(filename)
        if data:
            ext = ext_from_data(data)
            out = LOGOS_DIR / f"{safe}{ext}"
            out.write_bytes(data)
            saved += 1
            found = True
            print(f"✓ {filename} ({len(data)}b)")
            results.append({"name": name, "host": host, "status": "saved", "source": f"wikimedia:{filename}", "size": len(data)})
            break
    
    if not found:
        # Try alternative brand name from the actual book name
        alt_brand = name.lower().split(" ")[0]  # e.g. "betvictor" from "BetVictor Exchange"
        if alt_brand != brand:
            files = search_wikimedia(alt_brand)
            for filename in files:
                data = download_wikimedia(filename)
                if data:
                    ext = ext_from_data(data)
                    out = LOGOS_DIR / f"{safe}{ext}"
                    out.write_bytes(data)
                    saved += 1
                    found = True
                    print(f"✓ {filename} ({len(data)}b) via alt_brand")
                    results.append({"name": name, "host": host, "status": "saved", "source": f"wikimedia:{filename}", "size": len(data)})
                    break
    
    if not found:
        print("✗")
        results.append({"name": name, "host": host, "status": "failed"})
    
    sys.stdout.flush()
    time.sleep(0.3)  # Be polite to Wikimedia API

print(f"\n{'='*60}")
print(f"RESULT: {saved}/{len(missing)} from Wikimedia Commons")
print(f"{'='*60}")

report_path = ROOT / "proofs" / "wikimedia_logos.json"
report_path.write_text(json.dumps(results, indent=2))
