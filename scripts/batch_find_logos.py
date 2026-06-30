#!/usr/bin/env python3
"""
batch_find_logos.py — run find_logo_smart against ALL missing books.
Reads books.json + manifest.json, attempts logo download for each missing book.
"""
import json, pathlib, subprocess, sys, os, time

ROOT = pathlib.Path("D:/sportsbook-master-list")
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())
LOGOS = ROOT / "logs"
LOGOS.mkdir(exist_ok=True)

# Get missing books
missing = []
for b in books:
    name = b["name"]
    url = b["url"]
    if manifest.get(name, {}).get("status") != "verified":
        missing.append((name, url))

print(f"Missing: {len(missing)} books")
print()

script = ROOT / "scripts" / "find_logo_smart.py"
results = {"saved": [], "failed": []}

for i, (name, url) in enumerate(missing):
    # Determine output filename from URL hostname
    from urllib.parse import urlparse
    host = urlparse(url).netloc.replace("www.", "")
    safe = host.replace(".", "_").replace("-", "_")
    outfile = str(ROOT / "logos" / f"{safe}.png")
    
    print(f"[{i+1}/{len(missing)}] {name} ({host})...")
    
    try:
        r = subprocess.run(
            ["/c/Users/chris/AppData/Local/hermes/hermes-agent/venv/Scripts/python", str(script), url, outfile],
            capture_output=True, text=True, timeout=60
        )
        output = r.stdout.strip()
        if os.path.exists(outfile) and os.path.getsize(outfile) > 300:
            size = os.path.getsize(outfile)
            print(f"  ✓ {size}b")
            results["saved"].append({"name": name, "url": url, "file": outfile, "size": size})
        else:
            # Check what extension actually got the file
            found = False
            for ext in ['.png', '.ico', '.svg', '.jpg', '.webp', '.gif', '.bin']:
                for f in os.listdir(ROOT / "logos"):
                    if f.startswith(safe) and f.endswith(ext):
                        fpath = ROOT / "logos" / f
                        if fpath.stat().st_size > 300:
                            print(f"  ✓ {fpath.stat().st_size}b ({f})")
                            results["saved"].append({"name": name, "url": url, "file": str(f), "size": fpath.stat().st_size})
                            found = True
                            break
                    if found: break
                if found: break
            if not found:
                print(f"  ✗ Not found")
                results["failed"].append({"name": name, "url": url})
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout")
        results["failed"].append({"name": name, "url": url, "reason": "timeout"})
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results["failed"].append({"name": name, "url": url, "reason": str(e)})
    
    time.sleep(0.5)

print(f"\n{'='*60}")
print(f"SAVED: {len(results['saved'])} / {len(missing)}")
print(f"FAILED: {len(results['failed'])}")
print(f"{'='*60}")

# Save report
(ROOT / "proofs" / "batch_find_logos_report.json").write_text(json.dumps(results, indent=2))
print(f"\nReport: proofs/batch_find_logos_report.json")

print(f"\nFailed brands:")
for f in results["failed"]:
    print(f"  {f['name']} — {f['url']}")
