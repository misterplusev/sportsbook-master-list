#!/usr/bin/env python3
"""
wikimedia_mass_search.py — for each remaining missing brand, search Wikimedia Commons
API. Try multiple name variations. Download first valid result.
"""
import json, pathlib, subprocess, time, re

ROOT = pathlib.Path("D:/sportsbook-master-list")
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())
LOGOS = ROOT / "logos"

missing = []
for b in books:
    name = b["name"]
    url = b["url"]
    if manifest.get(name, {}).get("status") != "verified":
        from urllib.parse import urlparse
        host = urlparse(url).netloc.replace("www.", "")
        brand = host.split("."")[0].title()
        missing.append({"name": name, "hostname": host, "brand": brand})

# Also try manual name->brand mapping for common ones
brand_aliases = {
    "4Cx": ["4cx logo", "4Cx sweepstakes"],
    "BET99": ["bet99"],
    "BetDeluxe": ["betdeluxe"],
    "BetGRW": ["betgrw"],
    "BetMania": ["betmania"],
    "BetNation": ["betnation"],
    "betwhale": ["betwhale"],
    "Boomers": ["boomers bet"],
    "Bracco": ["bracco bet"],
    "CampoBet": ["campobet"],
    "Casumo": ["casumo"],
    "Codere": ["codere"],
    "Coolbet": ["coolbet"],
    "Coral": ["coral bookmaker"],
    "Courtside": ["courtside"],
    "Danske Spil": ["danske spil"],
    "Desert Diamond": ["desert diamond casino"],
    "Dogg House": ["dogg house"],
    "Fanatics": ["fanatics sportsbook"],
    "Four Winds": ["four winds casino"],
    "Galera.bet": ["galera bet"],
    "GGBet": ["ggbet"],
    "Goldbet": ["goldbet"],
    "Heritage": ["heritage sports"],
    "HotStreak": ["hotstreak"],
    "Jazz Sports": ["jazz sports betting"],
    "Jugabet": ["jugabet"],
    "JustBet": ["justbet"],
    "Ladbrokes (Australia)": ["ladbroLucky Casino": ["lucky casino"],
    "Melbet": ["melbet"],
    "Mise-o-jeu": ["miseojeu"],
    "Neds": ["neds"],
    "Ninja Casino": ["ninjacasino"],
    "Oddin": ["oddin"],
    "Opinion Labs": ["opinionlabs"],
    "Overtime": ["overtime sports"],
    "Parimatch": ["parimatch"],
    "ParlayPlay": ["parlayplay"],
    "Play Alberta": ["play alberta"],
    "Playdoit": ["playdoit"],
    "PointsBet": ["pointsbet"],
    "Proline": ["proline plus"],
    "Props Builder": ["props builder"],
    "PS3838": ["ps3838"],
    "Rizk": ["rizk casino"],
    "RushBet": ["rushbet"],
    "Sportingbet": ["sportingbet"],
    "SugarHouse": ["sugarhouse"],
    "Superbet": ["superbet"],
    "SurgeBet": ["surgebet"],
    "TAB": ["tab new zealand betting"],
    "ThriveFantasy": ["thrivefantasy"],
    "Tipsport": ["tipsport"],
    "WynnBET": ["wynnbet sportsbook"],
    "SuperBook": ["superbook sportsbook"],
    "Betfred": ["betfred sportsbook"],
    "Betly": ["betly sportsbook"],
    "SBK": ["sbk smarkets betting"],
    "Resorts World": ["resorts world casino"],
    "Action 24/7": ["action 247 betting"],
    "Q Sportsbook": ["q sportsbook"],
    "BetMonarch": ["betmonarch"],
    "DRF Sportsbook": ["daily racing form sportsbook"],
    "BetWildwood": ["betwildwood"],
    "Eagle Sports": ["eagle sportsbook"],
    "MVGBet": ["mvgbet"],
    "Snoqualmie": ["snoqualmie casino betting"],
    "Pinnacle": ["pinnacle sportsbook"],
    "Hard Rock Bet": ["hard rock sportsbook"],
    "Fanatics Sportsbook": ["fanatics sportsbook"],
    "FanDuel Sportsbook": ["fanduel sportsbook"],
}

results_found = 0

for entry in missing:
    name = entry["name"]
    if manifest.get(name, {}).get("status") == "verified":
        continue
    
    safe = entry["hostname"].replace(".", "_").replace("-", "_")
    aliases = brand_aliases.get(name, [entry["brand"].lower()])
    
    found = False
    for alias in aliases[:3]:  # Top 3 aliases
        # Search Wikimedia API
        import urllib.parse
        query = urllib.parse)
        api_url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={query}+logo&srnamespace=6&format=json&srlimit=5"
        
        try:
            r = subprocess.run(
                ["curl", "-sSL", "--max-time", "8", api_url],
                timeout=12, capture_output=True
            )
            data = json.loads(r.stdout)
            for item in data.get("query", {}).get("search", []):
                title = item["title"][5:] if item["title"].startswith("File:") else item["title"]
                if not any(title.lower().endswith(ext) for ext in ['.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    continue
                
                # Download
                dl_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{title.replace(' ', '_')}"
                r2 = subprocess.run(
                    ["curl", "-sSL", "--max-time", "10", "-o", f"/tmp/wm_dl.bin", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)", dl_url],
                    timeout=15, capture_output=True
                )
                if pathlib.Path("/tmp/wm_dl.bin").exists():
                    size = pathlib.Path("/tmp/wm_dl.bin").stat.st_size
                    if size > 300:
                        data_bytes = pathlib.Path("/tmp/wm_dl.bin").read_bytes()
                        if not (b'<!DOCTYPE' in data_bytes[:500] or b'<html' in data_bytes[:500]):
                            ext_map = {'.svg': '.svg', '.png': '.png', '.jpg': '.jpg', '.jpeg': '.jpg', '.gif': '.gif', '.webp': '.webp'}
                            ext = '.svg'
                            for e in ext_map:
                                if title.lower().endswith(e):
                                    ext = ext_map[e]
                                    break
                            outfile = LOGOS / f"{safe}{ext}"
                            outfile.write_bytes(data_bytes)
                            print(f"✓ {name:30} {title:30} {size}b")
                            results_found += 1
                            found = True
                            break
                    pathlib.Path("/tmp/wm_dl.bin").unlink(missing_ok=True)
        except:
            pass
        
        if found:
            break
        time.sleep(0.3)
    
    if not found:
        print(f"✗ {name:30} (tried {len(aliases)} aliases)")
    
    sys.stdout.flush()

print(f"\n{'='*60}")
print(f"WIKIMEDIA FOUND: {results_found}/{len(missing)}")
print(f"{'='*60}")
