import json

books = json.loads(open('books_comprehensive.json').read())

# ABET baseline data for books with scrapers
abet_data = {
    "ATG": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["SE"]},
    "BetAnything": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["BE"]},
    "BetOnline": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US", "International"]},
    "BetOpenly": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US"]},
    "BetPARX": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US-PA", "US-NJ", "US-MI"]},
    "Betr (Australia)": {"scraper": "built", "offer": ["Moneyline"], "markets": ["Moneyline"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["AU"]},
    "BetRivers": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US-MI", "US-NJ", "US-PA", "US-WV"]},
    "Betsson": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["SE", "EU", "International"]},
    "Betway": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK", "EU", "International"]},
    "Bovada": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Spread", "Total"], "markets": ["Moneyline", "Run Line", "Spread", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US", "International"]},
    "DraftKings (Pick 6)": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US"]},
    "Everygame": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US", "International"]},
    "Fliff": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US"]},
    "Kalshi": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US (Prediction Market)"]},
    "Ladbrokes": {"scraper": "built", "offer": ["Moneyline", "Total"], "markets": ["Moneyline", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK", "AU"]},
    "Marathonbet": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["International", "UK"]},
    "MyBookie": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US", "International"]},
    "Novig": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US"]},
    "Polymarket": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US (Prediction Market)", "International"]},
    "PrizePicks": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US (DFS)"]},
    "Smarkets": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK", "EU", "International"]},
    "Sporttrade": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US-NJ", "US-CO", "US-IA", "US-VA", "US-AZ"]},
    "Svenskaspel": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["SE"]},
    "TABtouch": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["AU-WA"]},
    "Unibet": {"scraper": "built", "offer": ["Moneyline"], "markets": ["Moneyline"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK", "EU", "International", "SE", "DK", "FR", "AU"]},
    "Unibet (Australia)": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["AU"]},
    "FanDuel": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US"]},
    "Pinnacle": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["International", "US (Limited)"]},
    "Hard Rock Bet": {"scraper": "built", "offer": ["11 other"], "markets": ["Moneyline", "Spread", "Total", "Props"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US-FL", "US-AZ", "US-IN", "US-VA", "US-OH", "US-TN", "US-CO", "US-MI"]},
    "Grosvenor": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK"]},
    "LiveScore Bet": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK"]},
    "Matchbook": {"scraper": "built", "offer": ["Moneyline", "Total"], "markets": ["Moneyline", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK", "IE", "International"]},
    "PlayUp": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["AU"]},
    "Unibet (France)": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["FR"]},
    "Virgin Bet": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK"]},
    "Winamax": {"scraper": "built", "offer": ["Moneyline"], "markets": ["Moneyline"], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["FR", "ES"]},
    "NetBet": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["UK", "EU", "International"]},
    "PMU": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["FR"]},
    "Bally Bet": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US-AZ", "US-CO", "US-IA", "US-IN", "US-MA", "US-NY", "US-OH", "US-VA"]},
    "BetMGM": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total"], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US-AZ", "US-CO", "US-DC", "US-IA", "US-IL", "US-IN", "US-KS", "US-KY", "US-LA", "US-MA", "US-MD", "US-MI", "US-MO", "US-NC", "US-NJ", "US-OH", "US-PA", "US-TN", "US-VA", "US-WV", "US-WY"]},
    "Coral": {"scraper": "built", "offer": ["Moneyline", "Total"], "markets": ["Moneyline", "Total"], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["UK"]},
    "DraftKings": {"scraper": "built", "offer": ["Moneyline", "Run Line", "Total"], "markets": ["Moneyline", "Run Line", "Total", "Props", "Futures"], "proof": {"cf": False, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US"]},
    "Fanatics": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": False, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US-AZ", "US-CO", "US-CT", "US-DC", "US-IA", "US-IL", "US-IN", "US-KS", "US-KY", "US-LA", "US-MA", "US-MD", "US-MI", "US-MO", "US-NC", "US-NJ", "US-NY", "US-OH", "US-PA", "US-TN", "US-VA", "US-VT", "US-WV", "US-WY"]},
    "Fanatics Markets": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": False, "hf": True, "oracle": True, "github": True}, "jurisdictions": ["US"]},
    "Prophet X": {"scraper": "built", "offer": ["Moneyline"], "markets": ["Moneyline"], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US"]},
    "theScore": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US"]},
    "Underdog Fantasy (2 Pick)": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US (DFS)"]},
    "Underdog Fantasy (3 or 5 Pick)": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US (DFS)"]},
    "Underdog Fantasy (Multipliers)": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US (DFS)"]},
    "Underdog Predictions": {"scraper": "built", "offer": [], "markets": [], "proof": {"cf": True, "hf": True, "oracle": False, "github": True}, "jurisdictions": ["US (DFS)"]},
}

# Extra variants mapping
extra_map = {
    "Grosvenor": "Grosvenor",
    "LiveScore Bet": "LiveScore Bet",
    "Matchbook": "Matchbook",
    "PlayUp": "PlayUp",
    "Unibet (France)": "Unibet (France)",
    "Virgin Bet": "Virgin Bet",
    "Winamax": "Winamax",
    "NetBet": "NetBet",
    "PMU": "PMU",
}

# Apply to books
books = json.loads(open('books_comprehensive.json').read())

matched = 0
for b in books:
    name = b['name']
    if name in abet_data:
        data = abet_data[name]
        b['scraper_status'] = data.get('scraper', 'none')
        b['offer_types'] = data.get('offer', [])
        b['markets'] = data.get('markets', [])
        b['scraper_proof'] = data.get('proof', {"cf": False, "hf": False, "oracle": False, "github": False})
        if data.get('jurisdictions'):
            b['jurisdictions'] = data['jurisdictions']
        matched += 1
    else:
        for aname, adata in abet_data.items():
            if aname.lower() == name.lower():
                b['scraper_status'] = adata.get('scraper', 'none')
                b['offer_types'] = adata.get('offer', [])
                b['markets'] = adata.get('markets', [])
                b['scraper_proof'] = adata.get('proof', {"cf": False, "hf": False, "oracle": False, "github": False})
                if adata.get('jurisdictions'):
                    b['jurisdictions'] = adata['jurisdictions']
                matched += 1
                break

# Handle EXTRA variants
for b in books:
    if b['name'] in extra_map and extra_map[b['name']] in abet_data:
        data = abet_data[extra_map[b['name']]]
        b['scraper_status'] = data.get('scraper', 'none')
        b['offer_types'] = data.get('offer', [])
        b['markets'] = data.get('markets', [])
        b['scraper_proof'] = data.get('proof', {"cf": False, "hf": False, "oracle": False, "github": False})
        if data.get('jurisdictions'):
            b['jurisdictions'] = data['jurisdictions']
        matched += 1

print(f"Matched {matched} books with ABET data")

# Save
json.dump(books, open('books_comprehensive.json', 'w'), indent=2, ensure_ascii=False)
print("Saved books_comprehensive.json")

with_scraper = sum(1 for b in books if b.get('scraper_status') == 'built')
print(f"Books with scrapers: {with_scraper}")
print(f"Total books: {len(books)}")

EOF