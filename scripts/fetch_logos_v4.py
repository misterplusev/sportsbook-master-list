#!/usr/bin/env python3
"""
Fast parallel logo fetcher — fetch_logos_v4.py
Strategy:
  1. Generate curl commands for all missing books (favicon + apple-touch-icon only)
  2. Run them in parallel (20 workers) with 8s timeout
  3. Validate magic bytes on success
  4. For books that fail, try extended paths
  5. For books that still fail, output them for browser-based recovery
"""
import os, json, hashlib, time, pathlib, subprocess, sys
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "logos"
PROOF_DIR = ROOT / "proofs" / "20260627"
REPORT = PROOF_DIR / "verification_report_v4.json"

LOGOS_DIR.mkdir(parents=True, exist_ok=True)
PROOF_DIR.mkdir(parents=True, exist_ok=True)

# Load books
books_list = json.loads((ROOT / "books.json").read_text())

# Check if book already has a good logo
def has_good_logo(host):
    safe = host.replace(".", "_").replace("-", "_")
    for ext in [".png", ".svg", ".jpg", ".webp", ".ico", ".gif"]:
        f = LOGOS_DIR / f"{safe}{ext}"
        if f.exists() and f.stat().st_size > 300:
            return f
    return None

# Build work list
work = []
for b in books_list:
    host = urlparse(b["url"]).netloc.replace("www.", "")
    if not has_good_logo(host):
        work.append((b["name"], host))

print(f"Missing logos: {len(work)} books")

# Magic bytes check
def is_image(data):
    if len(data) < 300:
        return False
    head = data[:20]
    if head[:4] == b"\x89PNG":
        return True
    if head[:4] == b"\xff\xd8\xff":
        return True
    if head[:4] == b"RIFF":
        return True
    if head[:4] == b"GIF8":
        return True
    if head[:5] == b"<svg " or head[:5] == b"<svg\n":
        return True
    if head[:4] == b"\x00\x00\x01\x00":
        return True
    if head[:4] == b"<?xm":
        return True
    low = data[:500].lower()
    if b"<svg" in low and b"svg" in low:
        return True
    if b"<!doctype" in low or b"<html" in low:
        return False
    return False

def ext_from_data(data):
    head = data[:20]
    if head[:4] == b"\x89PNG": return ".png"
    if head[:4] == b"\xff\xd8\xff": return ".jpg"
    if head[:4] == b"RIFF": return ".webp"
    if head[:4] == b"GIF8": return ".gif"
    if head[:4] == b"\x00\x00\x01\x00": return ".ico"
    if head[:5] == b"<svg " or head[:5] == b"<svg\n": return ".svg"
    if head[:4] == b"<?xm": return ".svg"
    low = data[:500].lower()
    if b"<svg" in low: return ".svg"
    return ".bin"

# === FAST CURL FETCH ===
def fetch_fast(host, path):
    url = f"https://{host}{path}"
    try:
        r = subprocess.run(
            ["curl", "-sS", "-o", "-", "-w", "%{http_code}", "--max-time", "8",
             "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             "-H", "Accept: image/*,*/*;q=0.8",
             url],
            capture_output=True, timeout=12
        )
        code = r.stdout.decode().strip()[-3:]
        data = r.stdout
        return data, code, url
    except:
        return b"", "000", url

def fetch_one(name, host):
    # Try fast paths first
    for path in ["/favicon.ico", "/apple-touch-icon.png", "/favicon.png", "/logo.svg", "/logo.png"]:
        data, code, url = fetch_fast(host, path)
        if code == "200" and is_image(data):
            ext = ext_from_data(data)
            safe = host.replace(".", "_").replace("-", "_")
            out = LOGOS_DIR / f"{safe}{ext}"
            out.write_bytes(data)
            return {
                "name": name, "domain": host, "status": "saved",
                "size": len(data), "source_url": url, "file": out.name,
                "sha256": hashlib.sha256(data).hexdigest(),
            }

    # Try extended paths
    extended = [
        "/images/favicon.ico", "/images/favicon.png",
        "/static/favicon.ico", "/static/favicon.png",
        "/assets/favicon.ico", "/assets/favicon.png",
        "/img/favicon.ico", "/img/favicon.png",
        "/favicons/favicon.ico", "/favicons/favicon.png",
        "/images/logo.svg", "/images/logo.png",
        "/static/logo.svg", "/static/logo.png",
        "/assets/logo.svg", "/assets/logo.png",
        "/img/logo.svg", "/img/logo.png",
        "/logo-dark.svg", "/logo-dark.png",
        "/logo-light.svg", "/logo-light.png",
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
    ]
    for path in extended:
        data, code, url = fetch_fast(host, path)
        if code == "200" and is_image(data):
            ext = ext_from_data(data)
            safe = host.replace(".", "_").replace("-", "_")
            out = LOGOS_DIR / f"{safe}{ext}"
            out.write_bytes(data)
            return {
                "name": name, "domain": host, "status": "saved",
                "size": len(data), "source_url": url, "file": out.name,
                "sha256": hashlib.sha256(data).hexdigest(),
            }

    # Try www variant
    if not host.startswith("www."):
        for path in ["/favicon.ico", "/logo.svg", "/logo.png"]:
            data, code, url = fetch_fast(f"www.{host}", path)
            if code == "200" and is_image(data):
                ext = ext_from_data(data)
                safe = host.replace(".", "_").replace("-", "_")
                out = LOGOS_DIR / f"{safe}{ext}"
                out.write_bytes(data)
                return {
                    "name": name, "domain": host, "status": "saved",
                    "size": len(data), "source_url": url, "file": out.name,
                    "sha256": hashlib.sha256(data).hexdigest(),
                }

    return {"name": name, "domain": host, "status": "failed"}

# === RUN ===
print(f"\nFast-fetching {len(work)} books with 20 parallel curl workers...\n")

results = []
with ThreadPoolExecutor(max_workers=20) as ex:
    futures = {ex.submit(fetch_one, name, host): name for name, host in work}
    done = 0
    for f in as_completed(futures):
        done += 1
        r = f.result()
        results.append(r)
        if r["status"] == "saved":
            print(f"  ✓ {r['name']:35} {r['source_url']} ({r['size']}b)")
        if done % 20 == 0:
            saved = sum(1 for r in results if r["status"] == "saved")
            print(f"  --- {done}/{len(work)} done, {saved} saved ---")

# Summary
saved = [r for r in results if r["status"] == "saved"]
failed = [r for r in results if r["status"] == "failed"]

print(f"\n{'='*60}")
print(f"RESULT: Saved={len(saved)}, Failed={len(failed)}")
print(f"{'='*60}")

if failed:
    print(f"\nFAILED (need browser recovery):")
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
