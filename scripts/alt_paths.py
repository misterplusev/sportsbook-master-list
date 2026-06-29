#!/usr/bin/env python3
"""Try alternative paths for domains that failed favicon.ico"""
import subprocess, pathlib, time, os

LOGOS_DIR = pathlib.Path("D:/sportsbook-master-list/logos")

FAILED = [
    "22bet.com", "bet105.io", "betdeluxe.com", "betgrw.com", "betmania.com",
    "betnation.com", "betplay.com", "boomers.bet", "boylesports.com", "bracco.bet",
    "bwin.com", "codere.com", "coral.co.uk", "courtside.com", "crabsports.com",
    "dansk-spil.dk", "desertdiamondcasino.com", "dogghouse.com", "elite-bet.com",
    "epick.com", "fourwinds.com", "ggbet.com", "heritage.com", "hotstreak.com",
    "justbet.com", "ladbrokes.com", "ladbrokes.com.au", "melbet.com", "miseojeu.com",
    "neds.com.au", "oddin.com", "opinionlabs.com", "overtime.com", "parlayplay.com",
    "partypoker.com", "playalberta.com", "proline.ca", "propsbuilder.com",
    "rushbet.com", "sportingbet.com", "sugarhouse.com", "surgebet.com",
    "tab.co.nz", "tipsport.com",
]

# Additional paths to try
PATHS = [
    "/favicon.png", "/favicon.svg", "/apple-touch-icon.png",
    "/logo.svg", "/logo.png", "/images/favicon.ico", "/images/favicon.png",
    "/images/logo.svg", "/images/logo.png", "/static/favicon.ico",
    "/static/logo.svg", "/static/logo.png", "/assets/favicon.ico",
    "/assets/logo.svg", "/assets/logo.png",
]

def is_good_image(path):
    try:
        if not path.exists(): return False
        size = path.stat().st_size
        if size < 300: return False
        data = path.read_bytes()[:20]
        if data[:4] == b'\x89PNG': return True
        if data[:3] == b'\xff\xd8\xff': return True
        if data[:4] == b'RIFF': return True
        if data[:4] == b'GIF8': return True
        if data[:4] == b'\x00\x00\x01\x00': return True
        if data[:5] in (b'<svg ', b'<svg\n'): return True
        if data[:4] == b'<?xm': return True
        low = path.read_bytes()[:500].lower()
        if b'<svg' in low: return True
        return False
    except:
        return False

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def ext_from_data(data):
    head = data[:20]
    if head[:4] == b"\x89PNG": return ".png"
    if head[:3] == b"\xff\xd8\xff": return ".jpg"
    if head[:4] == b"RIFF": return ".webp"
    if head[:4] == b"GIF8": return ".gif"
    if head[:4] == b"\x00\x00\x01\x00": return ".ico"
    if head[:5] in (b"<svg ", b"<svg\n"): return ".svg"
    if head[:4] == b"<?xm": return ".svg"
    return ".bin"

print(f"Trying alternative paths for {len(FAILED)} domains...")
found = 0
still_failed = []

for domain in FAILED:
    safe = domain.replace(".", "_").replace("-", "_")
    recovered = False
    
    for path_url in PATHS:
        out = LOGOS_DIR / f"{safe}_alt.tmp"
        try:
            subprocess.run(
                ["curl", "-sSL", "-o", str(out), "--max-time", "8",
                 "-H", f"User-Agent: {UA}",
                 f"https://{domain}{path_url}"],
                timeout=12, capture_output=True
            )
            if is_good_image(out):
                ext = ext_from_data(out.read_bytes())
                final = LOGOS_DIR / f"{safe}{ext}"
                out.rename(final)
                print(f"  ✓ {domain} via {path_url} ({final.stat().st_size}b)")
                found += 1
                recovered = True
                break
            else:
                if out.exists(): out.unlink(missing_ok=True)
        except:
            if out.exists(): out.unlink(missing_ok=True)
    
    # Try www variant
    if not recovered and not domain.startswith("www."):
        for path_url in ["/favicon.ico", "/favicon.png", "/logo.svg", "/logo.png"]:
            out = LOGOS_DIR / f"{safe}_alt.tmp"
            try:
                subprocess.run(
                    ["curl", "-sSL", "-o", str(out), "--max-time", "8",
                     "-H", f"User-Agent: {UA}",
                     f"https://www.{domain}{path_url}"],
                    timeout=12, capture_output=True
                )
                if is_good_image(out):
                    ext = ext_from_data(out.read_bytes())
                    final = LOGOS_DIR / f"{safe}{ext}"
                    out.rename(final)
                    print(f"  ✓ {domain} via www.{path_url} ({final.stat().st_size}b)")
                    found += 1
                    recovered = True
                    break
                else:
                    if out.exists(): out.unlink(missing_ok=True)
            except:
                if out.exists(): out.unlink(missing_ok=True)
    
    if not recovered:
        still_failed.append(domain)

print(f"\nAlt path results: {found} recovered")
print(f"Still failed: {len(still_failed)}")
for d in still_failed:
    print(f"  {d}")
