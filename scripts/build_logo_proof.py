#!/usr/bin/env python3
import os, json, hashlib, requests, time, pathlib, threading, re
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "logos"
PROOF_DIR = ROOT / "proofs" / "20260627"
MANIFEST = ROOT / "manifest.json"
REPORT = PROOF_DIR / "verification_report.json"

LOGOS_DIR.mkdir(parents=True, exist_ok=True)
PROOF_DIR.mkdir(parents=True, exist_ok=True)

BOOKS = [
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

PATHS = [
    "/favicon.ico",
    "/apple-touch-icon.png",
    "/apple-touch-icon-precomposed.png",
    "/images/logo.png",
    "/images/logo.svg",
    "/static/images/logo.png",
    "/assets/logo.png",
    "/assets/images/logo.png",
    "/logo.png",
    "/logo.svg",
    "/img/logo.png",
    "/favicons/favicon.ico",
    "/images/favicon.ico",
    "/-/media/logo.svg",
    "/-/media/logo.png",
    "/-/media/brand/logo.svg",
    "/-/media/brand/logo.png",
    "/dist/images/logo.png",
    "/dist/images/logo.svg",
    "/public/images/logo.png",
    "/public/images/logo.svg",
    "/static/logo.png",
    "/static/logo.svg",
    "/assets/brand/logo.png",
    "/assets/brand/logo.svg",
    "/cdn/images/logo.png",
    "/cdn/images/logo.svg",
    "/uploads/logo.png",
    "/uploads/logo.svg",
    "/media/logo.png",
    "/media/logo.svg",
    "/img/logo.svg",
    "/images/brand-logo.png",
    "/images/brand-logo.svg",
    "/images/primary-logo.png",
    "/images/primary-logo.svg",
    "/wp-content/uploads/logo.png",
    "/wp-content/uploads/logo.svg",
    "/content/dam/logo.png",
    "/content/dam/logo.svg",
]

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/*,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
}

lock = threading.Lock()
manifest = {}
report = {
    "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "total": len(BOOKS),
    "saved": 0,
    "skipped": 0,
    "failed": 0,
    "items": [],
}
counter = {"idx": 0}
stop_event = threading.Event()


class MetaImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self._meta_content = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            prop = attrs.get("property", "").lower()
            name = attrs.get("name", "").lower()
            content = attrs.get("content", "")
            if prop in ("og:image", "twitter:image") or name in ("twitter:image", "og:image"):
                if content:
                    self._meta_content.setdefault(prop or name, []).append(content)
        elif tag == "img":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "").lower()
            cls = attrs.get("class", "").lower()
            if src and any(k in (alt + " " + cls) for k in ["logo", "brand", "icon"]):
                self.images.append(src)
        elif tag == "link":
            rel = attrs.get("rel", "").lower()
            href = attrs.get("href", "")
            if rel in ("icon", "apple-touch-icon", "shortcut icon") and href:
                self.images.append(href)

    def get_candidates(self, base_url):
        metas = []
        for v in self._meta_content.values():
            metas.extend(v)
        candidates = metas + self.images
        seen = set()
        out = []
        for c in candidates:
            abs_url = urljoin(base_url, c)
            if abs_url not in seen:
                seen.add(abs_url)
                out.append(abs_url)
        return out


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


def fetch_url(session, url, timeout=12):
    try:
        r = session.get(url, timeout=(6, timeout), allow_redirects=True, stream=True)
        cl = r.headers.get("Content-Length")
        if cl and int(cl) > 2_500_000:
            return None, "too_large"
        data = r.content
        return r, data
    except Exception:
        return None, "error"


def fetch_one(args):
    idx, (name, domain) = args
    if stop_event.is_set():
        return None

    parsed = urlparse(domain)
    host = parsed.netloc or parsed.path
    safe = host.replace(".", "_").replace("-", "_")
    out = LOGOS_DIR / f"{safe}.bin"

    status = "failed"
    content_type = ""
    size = 0
    source_url = ""

    if out.exists() and out.stat().st_size > 300:
        status = "existing"
        size = out.stat().st_size
        content_type = detect_magic(out.read_bytes())
    else:
        session = requests.Session()
        session.headers.update(HEADERS)
        found = False

        # Try static paths first
        for p in PATHS:
            if found or stop_event.is_set():
                break
            url = f"{parsed.scheme}://{host}{p}"
            r, data = fetch_url(session, url, timeout=10)
            if r is None:
                continue
            mime = detect_magic(data)
            if r.status_code == 200 and len(data) > 300 and mime not in ("text/html", "application/octet-stream"):
                out.write_bytes(data)
                status = "saved"
                content_type = mime
                size = len(data)
                source_url = url
                found = True
                break

        # Fallback: homepage HTML parsing
        if not found and not stop_event.is_set():
            try:
                r, html_data = fetch_url(session, f"{parsed.scheme}://{host}/", timeout=12)
                if r and r.status_code == 200 and html_data:
                    text = html_data[:200_000].decode("utf-8", errors="ignore")
                    parser = MetaImageParser()
                    parser.feed(text)
                    candidates = parser.get_candidates(f"{parsed.scheme}://{host}/")
                    for cand in candidates[:8]:
                        if stop_event.is_set():
                            break
                        r2, data2 = fetch_url(session, cand, timeout=10)
                        if r2 is None:
                            continue
                        mime = detect_magic(data2)
                        if r2.status_code == 200 and len(data2) > 300 and mime not in ("text/html", "application/octet-stream"):
                            out.write_bytes(data2)
                            status = "saved"
                            content_type = mime
                            size = len(data2)
                            source_url = cand
                            found = True
                            break
            except Exception:
                pass

        if not found:
            status = "failed"

    sha = ""
    if out.exists() and out.stat().st_size > 0:
        sha = hashlib.sha256(out.read_bytes()).hexdigest()

    entry = {
        "name": name,
        "domain": host,
        "status": status,
        "size": size,
        "content_type": content_type,
        "sha256": sha,
        "source_url": source_url,
    }
    with lock:
        manifest[name] = entry
        report["items"].append(entry)
        if status == "saved":
            report["saved"] += 1
        elif status == "existing":
            report["skipped"] += 1
        else:
            report["failed"] += 1
        counter["idx"] += 1
        print(f"[{counter['idx']:03}/214] {name:35} {status:7} {size:>8}")
    return entry


with ThreadPoolExecutor(max_workers=10) as ex:
    list(ex.map(fetch_one, enumerate(BOOKS, 1)))

MANIFEST.write_text(json.dumps(manifest, indent=2))
REPORT.write_text(json.dumps(report, indent=2))
print(f"\nSaved={report['saved']} Existing={report['skipped']} Failed={report['failed']}")
