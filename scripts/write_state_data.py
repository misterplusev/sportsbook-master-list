import json

# Build state data structure
us_states = {}
books_to_states = {}
international = {}

# Action Network data + other sources (verified)
STATE_DATA = {
    "AL": ("Alabama", "none", []),
    "AK": ("Alaska", "none", ["Betly"]),
    "AZ": ("Arizona", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","BetFred","Bally Bet","Sporttrade","Desert Diamond"]),
    "AR": ("Arkansas", "online", ["DraftKings","FanDuel"]),
    "CA": ("California", "none", ["Kalshi","Polymarket"]),
    "CO": ("Colorado", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","BetFred","Bally Bet","Circa","Sporttrade","SBK","BetWildwood","BetMonarch","DRF","BetSafe"]),
    "CT": ("Connecticut", "online", ["Fanatics","FanDuel"]),
    "DC": ("Washington DC", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars"]),
    "DE": ("Delaware", "retail_only", []),
    "FL": ("Florida", "online", ["Hard Rock"]),
    "GA": ("Georgia", "none", []),
    "HI": ("Hawaii", "none", []),
    "IA": ("Iowa", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","BetFred","Bally Bet","Circa","Sporttrade","Q Sportsbook","DRF"]),
    "ID": ("Idaho", "none", []),
    "IL": ("Illinois", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","Circa"]),
    "IN": ("Indiana", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","Bally Bet"]),
    "KS": ("Kansas", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock"]),
    "KY": ("Kentucky", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","Circa"]),
    "LA": ("Louisiana", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","BetFred"]),
    "MA": ("Massachusetts", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","Bally Bet"]),
    "MD": ("Maryland", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","BetParx","Crab Sports"]),
    "ME": ("Maine", "online", ["Caesars"]),
    "MI": ("Michigan", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","BetRivers","WynnBET","Four Winds","FireKeepers","Eagle Sports","BetParx"]),
    "MN": ("Minnesota", "none", []),
    "MO": "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Bally Bet","Circa"]),
    "MS": ("Mississippi", "retail_only", ["BetMGM"]),
    "MT": ("Montana", "retail_only", []),
    "NC": ("North Carolina", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Underdog"]),
    "ND": ("North Dakota", "retail_only", []),
    "NE": ("Nebraska", "none", []),
    "NH": ("New Hampshire", "online", ["DraftKings"]),
    "NJ": ("New Jersey", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","BetRivers","Borgata","Sporttrade","Prime Sportsbook"]),
    "NM": ("New Mexico", "none", []),
    "NV": ("Nevada", "online", ["Caesars","Hard Rock","BetFred","Circa","SuperBook"]),
    "NY": ("New York", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Bally Bet","WynnBET","Resorts World"]),
    "OH": ("Ohio", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","BetFred","Bally Bet","BetRivers","Betr","BetJACK","MVGBet","Prime Sportsbook","Betly"]),
    "OK": ("Oklahoma", "none", []),
    "OR": ("Oregon", "none", []),
    "PA": ("Pennsylvania", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","BetFred","BetRivers","BetParx","Bally Bet","Hard Rock"]),
    "RI": ("Rhode Island", "online", [" "DraftKings"]),
    "SC": ("South Carolina", "none", []),
    "SD": ("South Dakota", "retail_only", []),
    "TN": ("Tennessee", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","Action 24/7","Betly"]),
    "TX": ("Texas", "none", ["Kalshi","Polymarket"]),
    "UT": ("Utah", "none", []),
    "VA": ("Virginia", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","bet365","Hard Rock","Bally Bet","Sporttrade","Betr"]),
    "VT": ("Vermont", "online", ["Fanatics","DraftKings","FanDuel"]),
    "WA": ("Washington", "tribal_only", ["BetFred"]),
    "WI": ("Wisconsin", "none", []),
    "WV": ("West Virginia", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","theScore","BetRivers","Betly"]),
    "WY": ("Wyoming", "online", ["Fanatics","DraftKings","FanDuel","BetMGM","Caesars","Hard Rock"])
}

for code, (name, typ, books_list) in STATE_DATA.items():
    us_states[code] = {"name": name, "type": typ, "books": books_list}
    for b in books_list:
        books_to_states.setdefault(b, []).append(code)

# International assignments (key non-US books)
INTL = {
    "1xBet": "international", "888sport": "GB,other_EU", "BC.GAME": "international,crypto",
    "Bet-at-home": "DE,AT,CH", "Betano": "BR,LATAM", "Betcity": "NL",
    "Betway": "GB,international", "Betsson": "SE,EU", "Bwin": "DE,EU",
    "Coral": "GB", "Crystalbet": "GR", "Danske Spil": "DK", "Eurobet": "IT",
    "Fonbet": "RU", "GGBet": "CY", "Interwetten": "DE,AT,CH",
    "Jugabet": "AR,CL", "Ladbrokes": "GB,AU", "Ladbrokes Australia": "AU",
    "LeoVegas": "SE,GB", "Linebet": "RU", "Marathonbet": "international",
    "Melbet": "RU", "Neds": "AU", "Parimatch": "RU,international",
    "Pinnacle": "international", "SBOBET": "international,Asia",
    "Sportingbet": "international", "Sportsbet.com.au": "AU", "STS": "PL",
    "SuperSport": "HR,Balkan", "TAB": "NZ", "TABtouch": "AU-WA",
    "Unibet": "GB,DK,SE,AU,EU", "Casumo": "GB,SE,EU", "Coolbet": "EE,EU",
    "BetSafe": "SE,EU", "Veikkaus": "FI", "Svenska Spel": "SE",
    "Tipsport": "CZ", "Fortuna": "CZ", "Tipico": "DE",
    "TwinSpires": "US", "YouWager": "US", "MyBookie": "US",
    "Bovada": "US", "BetOnline": "US", "Sportsbetting.ag": "US",
    "Everygame": "US", "Jackpot.bet": "international", "Snoqualmie": "US-WA",
    "BetNation": "AU", "BetDeluxe": "international", "BetMania": "international",
    "BetGRW": "RU", "Goldbet": "IT", "Galera.bet": "BR", "HotStreak": "US-CA",
    "Jazz Sports": "US-LA", "JustBet": "US", "Lucky Casino": "US",
    "Mise-o-jeu": "CA-QC", "Ninja Casino": "EU", "Oddin": "EU,ESports",
    "Opinion Labs": "US", "ParlayPlay": "US", "Play Alberta": "CA-AB",
    "Playdoit": "US", "Proline": "CA", "Props Builder": "US",
    "PS3838": "international", "Rizk": "MT,EU", "RushBet": "US",
    "SugarHouse": "US", "Superbet": "RO,PL", "SurgeBet": "US",
    "ThriveFantasy": "US", "Tipsport": "CZ", "TonyBet": "LT,EU",
    "Winpot": "?", "YouWager": "US",
}

data = {
    "last_updated": "2026-06-29",
    "source": "Action Network, RG.org, operator sites",
    "us_states": us_states,
    "books_to_states": books_to_states,
    "international": INTL,
    "type_legend": {
        "online": "legal statewide online/mobile sports betting",
        "retail_only": "in-person only at casinos/racetracks",
        "tribal_only": "tribal casinos only",
        "none": "no legal sports betting"
    }
}

json.dump(data, open("data/state_availability.json", "w"), indent=2)
print(f"OK: {len(us_states)} states, {len(books_to_states)} US books, {len(INTL)} international")
