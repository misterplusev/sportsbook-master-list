#!/usr/bin/env python3
import json, hashlib, pathlib, time
from urllib.parse import urlparse

ROOT = pathlib.Path(r'C:\Users\chris\sportsbook-master-list')
LOGOS_DIR = ROOT / 'logos'
PROOF_DIR = ROOT / 'proofs' / '20260627'
MANIFEST = ROOT / 'manifest.json'
REPORT = PROOF_DIR / 'verification_report.json'

PROOF_DIR.mkdir(parents=True, exist_ok=True)

MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"<svg": "image/svg+xml",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",
    b"<!DOCTYPE": "text/html",
    b"<!doctype": "text/html",
    b"<!-- ": "text/html",
    b"<?xml": "image/svg+xml",
}

books = [
("1XBet","https://1xbet.com"),("20bet","https://20bet.com"),("22bet","https://22bet.com"),("4Cx","https://4cx.com"),
("888sport","https://888sport.com"),("ATG","https://atg.se"),("Bally Bet","https://ballybet.com"),("Batery","https://batery.bet"),
("BC.GAME","https://bc.game"),("bet105","https://bet105.io"),("bet365","https://bet365.com"),("BET99","https://bet99.ca"),
("BetAmapola","https://betamapola.com"),("Betano","https://betano.com"),("Betano (Argentina)","https://betano.com"),("Betano (Chile)","https://betano.com"),
("BetAnything","https://betanything.com"),("BetCorrect","https://betcorrect.com"),("Betcris","https://betcris.com"),("BetDeluxe","https://betdeluxe.com"),
("BetDEX","https://betdex.com"),("BetDSI","https://betdsi.eu"),("Betfair","https://betfair.com"),("Betfair Exchange","https://betfair.com"),
("Betfair Exchange (Australia)","https://betfair.com"),("Betfair Exchange (Australia) (Lay)","https://betfair.com"),("Betfair Exchange (Lay)","https://betfair.com"),
("BetGRW","https://betgrw.com"),("betJACK","https://betjack.com"),("BetMania","https://betmania.com"),("BetMGM","https://betmgm.com"),("BetMGM (UK)","https://betmgm.co.uk"),
("Betnacional","https://betnacional.com"),("BetNation","https://betnation.com"),("BetNation (Australia)","https://betnation.com.au"),("BetNow","https://betnow.eu"),
("BetOnline","https://betonline.ag"),("BetOpenly","https://betopenly.com"),("betPARX","https://betparx.com"),("Betplay","https://betplay.com"),
("Betr","https://betr.app"),("Betr (Australia)","https://betr.com.au"),("BetRivers","https://betrivers.com"),("BetRivers (New York)","https://betrivers.com"),
("Betr Picks","https://betr.app"),("Betr Picks (All)","https://betr.app"),("Betr Picks (BOOSTED)","https://betr.app"),("Betsafe","https://betsafe.com"),
("Bets IO","https://bets.io"),("Betsson","https://betsson.com"),("Betsson (Chile)","https://betsson.com"),("BetUS","https://betus.com"),("BetVictor","https://betvictor.com"),
("Betway","https://betway.com"),("Betway (Alaska)","https://betway.com"),("betwhale","https://betwhale.com"),("Bodog","https://bodog.eu"),("BookMaker","https://bookmaker.eu"),
("Boomers","https://boomers.bet"),("Boom Fantasy (5 Pick Insured)","https://boomfantasy.com"),("Borgata","https://borgata.com"),("Bovada","https://bovada.lv"),
("Boyle Sports","https://boylesports.com"),("Bracco","https://bracco.bet"),("bwin","https://bwin.com"),("Caesars","https://caesars.com"),("Campeonbet","https://campeonbet.com"),
("CampoBet","https://campobet.com"),("Casumo","https://casumo.com"),("Circa Sports","https://circasports.com"),("Circa Vegas","https://circavegas.com"),("Codere","https://codere.com"),
("Coolbet","https://coolbet.com"),("Coral","https://coral.co.uk"),("Courtside","https://courtside.com"),("Crab Sports","https://crabsports.com"),("crypto.com","https://crypto.com"),
("Dabble (3 or 5 Pick)","https://dabble.com"),("Dabble (3 or 5 Pick Multipliers)","https://dabble.com"),("Dabble (Australia)","https://dabble.com.au"),("Dafabet","https://dafabet.com"),
("Danske Spil","https://dansk-spil.dk"),("DAZN Bet","https://daznbet.com"),("Desert Diamond","https://desertdiamondcasino.com"),("Dogg House","https://dogghouse.com"),
("DraftKings","https://draftkings.com"),("DraftKings (Pick 2)","https://draftkings.com"),("DraftKings (Pick 3)","https://draftkings.com"),("DraftKings (Pick 6)","https://draftkings.com"),
("DraftKings (Pick 6 Multipliers)","https://draftkings.com"),("DraftKings Predictions","https://draftkings.com"),("Elite Bet","https://elite-bet.com"),("EPICK","https://epick.com"),
("EPICK 50/50","https://epick.com"),("Eurobet","https://eurobet.it"),("Everygame","https://everygame.com"),("Fanatics","https://fanatics.com"),("Fanatics Markets","https://fanatics.com"),
("FireKeepers","https://firekeepers.com"),("Fliff","https://getfliff.com"),("Fliff Superstars","https://getfliff.com"),("Fonbet","https://fonbet.com"),("Four Winds","https://fourwinds.com"),
("Galera.bet","https://galera.bet"),("GGBet","https://ggbet.com"),("Goldbet","https://goldbet.it"),("Granawin","https://granawin.com"),("Heritage","https://heritage.com"),
("HotStreak","https://hotstreak.com"),("iBet","https://ibet.com"),("Jackpot.bet","https://jackpot.bet"),("Jazz Sports","https://jazzsports.com"),("Jugabet (Argentina)","https://jugabet.com"),
("Jugabet (Chile)","https://jugabet.com"),("JustBet","https://justbet.com"),("Kalshi","https://kalshi.com"),("Ladbrokes","https://ladbrokes.com"),("Ladbrokes (Australia)","https://ladbrokes.com.au"),
("LeoVegas","https://leovegas.com"),("Limitless Exchange","https://limitless.exchange"),("Lottoland","https://lottoland.com"),("LowVig","https://lowvig.ag"),("Lucky Casino","https://luckycasino.com"),
("Marathonbet","https://marathonbet.com"),("Melbet","https://melbet.com"),("Midnite","https://midnite.com"),("Mise-o-jeu","https://miseojeu.com"),("MyBookie","https://mybookie.com"),
("Neds","https://neds.com.au"),("Ninja Casino","https://ninjacasino.com"),("NorthStar Bets","https://northstarbets.com"),("Novig","https://novig.com"),("Oddin","https://oddin.com"),
("Onyx Odds","https://onyxodds.com"),("Opinion Labs","https://opinionlabs.com"),("OpticOdds AI","https://opticodds.com"),("OpticOdds AI DFS","https://opticodds.com"),("Overtime","https://overtime.com"),
("OwnersBox","https://ownersbox.com"),("OwnersBox (6 Pick Insured)","https://ownersbox.com"),("Ozoon","https://ozoon.com"),("Parimatch (Brazil)","https://parimatch.com"),("Parimatch (India)","https://parimatch.com"),
("Parlaye","https://parlaye.com"),("ParlayPlay","https://parlayplay.com"),("partypoker","https://partypoker.com"),("Picklebet","https://picklebet.com"),("Play Alberta","https://playalberta.com"),
("Playdoit","https://playdoit.com"),("Play Eagle","https://playeagle.com"),("PlayNow","https://playnow.com"),("PointsBet (Australia)","https://pointsbet.com"),("PointsBet (Ontario)","https://pointsbet.com"),
("Polymarket","https://polymarket.com"),("Polymarket (USA)","https://polymarket.com"),("Prime Sports","https://primesports.com"),("PrizePicks","https://prizepicks.com"),
("PrizePicks (5 or 6 Pick Flex)","https://prizepicks.com"),("PrizePicks (Demons and Goblins)","https://prizepicks.com"),("Proline","https://proline.ca"),("Prophet X","https://prophetx.com"),
("Props Builder","https://propsbuilder.com"),("PS3838","https://ps3838.com"),("Rebet","https://rebet.com"),("Rebet Props City","https://rebet.com"),("Rivalry","https://rivalry.com"),
("Rizk","https://rizk.com"),("Robinhood","https://robinhood.com"),("RushBet","https://rushbet.com"),("SABA Sports","https://sabasports.com"),("SBOBET","https://sbobet.com"),
("Sharp","https://sharp.com"),("Sleeper","https://sleeper.com"),("Smarkets","https://smarkets.com"),("SpinBet","https://spinbet.com"),("Sportingbet","https://sportingbet.com"),
("Sportsbet","https://sportsbet.com"),("Sportsbetting.ag","https://sportsbetting.ag"),("Sports Interaction","https://sportsinteraction.com"),("Sporttrade","https://sporttrade.com"),
("Sportzino","https://sportzino.com"),("Stake","https://stake.com"),("STN Sports","https://stnsports.com"),("SugarHouse","https://sugarhouse.com"),("Supabets","https://supabets.co.za"),
("Superbet","https://superbet.com"),("SurgeBet","https://surgebet.com"),("Svenskaspel","https://svenskaspel.se"),("SX Bet","https://sxbet.com"),("TAB","https://tab.co.nz"),
("TAB (New Zealand)","https://tab.co.nz"),("TABtouch","https://tabtouch.com.au"),("Team Mexico","https://teammexico.com"),("theScore","https://thescore.com"),
("Thrillzz","https://thrillzz.com"),("ThriveFantasy","https://thrivefantasy.com"),("Thunderpick","https://thunderpick.com"),("Tipsport","https://tipsport.com"),("TonyBet","https://tonybet.com"),
("TwinSpires","https://twinspires.com"),("Underdog Fantasy (2 Pick)","https://underdogfantasy.com"),("Underdog Fantasy (3 or 5 Pick)","https://underdogfantasy.com"),
("Underdog Fantasy (Multipliers)","https://underdogfantasy.com"),("Underdog Predictions","https://underdogfantasy.com"),("Unibet","https://unibet.com"),("Unibet (Australia)","https://unibet.com"),("Unibet (Denmark)","https://unibet.com"),
("Unibet (Sweden)","https://unibet.com"),("Unibet (United Kingdom)","https://unibet.com"),("Veikkaus","https://veikkaus.fi"),("Wanna Parlay","https://wannaparlay.com"),("William Hill","https://williamhill.com"),
("Winpot","https://winpot.com"),("YouWager","https://youwager.com"),
]

def detect_magic(data):
    s = data[:16]
    for head, mime in MAGIC.items():
        if s[: len(head)] == head:
            return mime
    b = data[:200].lower()
    if b"html" in b or b"<!doctype" in b or b"<html" in b:
        return "text/html"
    if b"svg" in b or b"xml" in b:
        return "image/svg+xml"
    return "application/octet-stream"

manifest = {}
report = {
    "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "total": len(books),
    "saved": 0,
    "skipped": 0,
    "failed": 0,
    "items": [],
}

for name, domain in books:
    parsed = urlparse(domain)
    host = parsed.netloc or parsed.path
    safe = host.replace(".", "_").replace("-", "_")
    out = LOGOS_DIR / f"{safe}.bin"
    status = "failed"
    size = 0
    content_type = ""
    sha = ""
    source_url = ""
    if out.exists() and out.stat().st_size > 300:
        status = "existing"
        size = out.stat().st_size
        data = out.read_bytes()
        content_type = detect_magic(data)
        sha = hashlib.sha256(data).hexdigest()
    item = {
        "name": name,
        "domain": host,
        "status": status,
        "size": size,
        "content_type": content_type,
        "sha256": sha,
        "source_url": source_url,
    }
    manifest[name] = item
    report["items"].append(item)
    if status == "saved":
        report["saved"] += 1
    elif status == "existing":
        report["skipped"] += 1
    else:
        report["failed"] += 1

MANIFEST.write_text(json.dumps(manifest, indent=2))
REPORT.write_text(json.dumps(report, indent=2))
print(f"Saved={report['saved']} Existing={report['skipped']} Failed={report['failed']}")
