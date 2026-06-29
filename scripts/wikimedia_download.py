#!/usr/bin/env python3
"""
Rapid Wikimedia logo downloader.
Reads search results from stdin (filename per line) and downloads each.
"""
import subprocess, pathlib, sys

LOGOS_DIR = pathlib.Path("D:/sportsbook-master-list/logos")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def download(filename, safe_name):
    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}"
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "12",
             "-H", f"User-Agent: {UA}",
             url],
            capture_output=True, timeout=16
        )
        data = r.stdout
        if len(data) < 300:
            return False
        s = data[:20]
        if s[:4] == b'\x89PNG': ext = '.png'
        elif s[:3] == b'\xff\xd8\xff': ext = '.jpg'
        elif s[:4] == b'RIFF': ext = '.webp'
        elif s[:4] == b'GIF8': ext = '.gif'
        elif s[:5] in (b'<svg ', b'<svg\n'): ext = '.svg'
        elif s[:4] == b'<?xm': ext = '.svg'
        else:
            low = data[:500].lower()
            if b'<!doctype' in low or (b'<html' in low and b'<svg' not in low[:50]): return False
            if b'<svg' in low: ext = '.svg'
            else: return False
        out = LOGOS_DIR / f"{safe_name}{ext}"
        out.write_bytes(data)
        return True
    except:
        return False

# Read filenames from arguments or stdin
# Usage: python script.py "File1.png" safe1 "File2.svg" safe2 ...
args = sys.argv[1:]
if len(args) < 2:
    print("Usage: python wikimedia_download.py File1 safe1 File2 safe2 ...")
    sys.exit(1)

for i in range(0, len(args), 2):
    filename = args[i]
    safe = args[i+1] if i+1 < len(args) else args[i].replace(" ", "_").replace("File:", "").rsplit(".", 1)[0]
    ok = download(filename, safe)
    if ok:
        f = list(LOGOS_DIR.glob(f"{safe}.*"))
        if f:
            print(f"OK {filename} -> {f[-1].name} ({f[-1].stat().st_size}b)")
        else:
            print(f"OK {filename}")
    else:
        print(f"FAIL {filename}")
