#!/usr/bin/env python3
"""
Logo-Finding Loop — Phase 2 (agent-callable workflow).
The agent runs this workflow for EACH missing brand:

1. Agent uses web_search for: "site:commons.wikimedia.org BRAND logo file"
2. If found, extract File:FILENAME, download via API imageinfo
3. If not on Wikimedia, agent searches "BRAND.com favicon ico png svg"
4. If found CDN path, curl download + verify
5. If still nothing, mark as "permanually_blocked"

This file documents the CANONICAL search workflow per remaining brand.
Each step uses tools the agent has (web_search, terminal, browser).
"""
# This script doesn't run standalone — it's a prompt/playbook for the agent.
# Run: agent follows these steps per brand.

import json, pathlib

ROOT = pathlib.Path("D:/sportsbook-master-list")
manifest = json.loads((ROOT / "manifest.json").read_text())
books = json.loads((ROOT / "books.json").read_text())

missing = []
for b in books:
    if manifest.get(b["name"], {}).get("status") != "verified":
        from urllib.parse import urlparse
        host = urlparse(b["url"]).netloc.replace("www.", "")
        safe = host.replace(".", "_").replace("-", "_")
        # Check existing quality
        existing = list((ROOT / "logos").glob(f"{safe}.*"))
        good = [f for f in existing if f.stat().st_size > 400 and f.suffix != '.bin']
        if good:
            continue
        missing.append({"name": b["name"], "url": b["url"], "host": host, "safe": safe})

print(f"Missing quality logos: {len(missing)}")
print("\nPrioritized list (biggest brands first):")

priority_brands = [
    'Fanatics', 'Hard Rock Bet', 'WynnBET', 'SuperBook', 'Betfred', 
    'Pinnacle', 'TAB', 'Tab', 'Rizk', 'Melbet', 'GGBet', 'Goldbet',
    'Jugabet', 'Codere', 'Sportingbet', 'Coral', 'Coolbet', 'Casumo',
    'betwhale', 'BetDeluxe', 'Boomers', 'Desert Diamond', 'Courtside',
]

remaining = []
for p in priority_brands:
    for m in missing:
        if p.lower() in m["name"].lower():
            print(f"  HIGH: {m['name']}")
            remaining.append(m)
            break

for m in missing:
    if m not in remaining:
        print(f"  LOW: {m['name']}")
