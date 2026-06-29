#!/usr/bin/env python3
"""Bulk parallel favicon.ico fetch using Python subprocess"""
import subprocess, os, pathlib, time

LOGOS_DIR = pathlib.Path("D:/sportsbook-master-list/logos")

DOMAINS = [
    "22bet.com", "4cx.com", "bet105.io", "bet99.ca", "betcris.com", "betdeluxe.com",
    "betgrw.com", "betmania.com", "betnation.com", "betnation.com.au", "betplay.com",
    "betvictor.com", "betwhale.com", "boomers.bet", "borgata.com", "boylesports.com",
    "bracco.bet", "bwin.com", "campobet.com", "casumo.com", "codere.com", "coolbet.com",
    "coral.co.uk", "courtside.com", "crabsports.com", "dansk-spil.dk",
    "desertdiamondcasino.com", "dogghouse.com", "elite-bet.com", "epick.com",
    "fonbet.com", "fourwinds.com", "galera.bet", "ggbet.com", "goldbet.it",
    "heritage.com", "hotstreak.com", "jazzsports.com", "jugabet.com", "justbet.com",
    "ladbrokes.com", "ladbrokes.com.au", "luckycasino.com", "melbet.com", "miseojeu.com",
    "neds.com.au", "ninjacasino.com", "northstarbets.com", "oddin.com", "opinionlabs.com",
    "overtime.com", "ozoon.com", "parimatch.com", "parlayplay.com", "partypoker.com",
    "playalberta.com", "playdoit.com", "pointsbet.com", "proline.ca", "propsbuilder.com",
    "ps3838.com", "rizk.com", "rushbet.com", "spinbet.com", "sportingbet.com",
    "sugarhouse.com", "supabets.co.za", "superbet.com", "surgebet.com", "sxbet.com",
    "tab.co.nz", "thrivefantasy.com", "tipsport.com"
]

def fetch_favicon(domain):
    safe = domain.replace(".", "_").replace("-", "_")
    out = LOGOS_DIR / f"{safe}.favicon.ico"
    try:
        subprocess.run(
            ["curl", "-sSL", "-o", str(out), "--max-time", "10",
             "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             f"https://{domain}/favicon.ico"],
            timeout=14, capture_output=True
        )
        return out
    except:
        return None

print(f"Fetching favicon.ico for {len(DOMAINS)} domains...")
procs = []
start = time.time()

# Launch all curls
for domain in DOMAINS:
    safe = domain.replace(".", "_").replace("-", "_")
    out = LOGOS_DIR / f"{safe}.favicon.ico"
    p = subprocess.Popen(
        ["curl", "-sSL", "-o", str(out), "--max-time", "10",
         "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
         f"https://{domain}/favicon.ico"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    procs.append((domain, safe, out, p))

# Wait for all
for domain, safe, out, p in procs:
    try:
        p.wait(timeout=14)
    except:
        p.kill()
        try:
            out.unlink(missing_ok=True)
        except:
            pass

elapsed = time.time() - start

# Check results
found = 0
failed_domains = []
for domain, safe, out, p in procs:
    if out.exists() and out.stat().st_size > 300:
        print(f"  ✓ {domain} ({out.stat().st_size}b)")
        found += 1
    else:
        if out.exists():
            out.unlink(missing_ok=True)
        failed_domains.append(domain)

print(f"\nDone in {elapsed:.1f}s")
print(f"Found: {found}/{len(DOMAINS)}")
print(f"Failed: {len(failed_domains)}")

if failed_domains:
    print(f"\nFailed domains:")
    for d in failed_domains:
        print(f"  {d}")
