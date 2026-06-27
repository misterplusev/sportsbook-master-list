#!/usr/bin/env python3
"""
Rebuild manifest.json from the actual logos/ directory.
This regenerates a clean manifest based on what files actually exist on disk,
with proper extensions based on magic bytes.
"""
import json, hashlib, pathlib, time

ROOT = pathlib.Path("C:/Users/chris/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
MANIFEST = ROOT / "manifest.json"

MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"<svg": "image/svg+xml",
    b"<?xml": "image/svg+xml",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",
}

def detect_mime(data):
    s = data[:16]
    for head, mime in MAGIC.items():
        if s[:len(head)] == head:
            return mime
    b = data[:500].lower()
    if b"<svg" in b or b"svg" in b:
        return "image/svg+xml"
    if b"html" in b or b"<!doctype" in b:
        return "text/html"
    return "application/octet-stream"

def ext_from_mime(mime):
    return {"image/png": ".png", "image/svg+xml": ".svg", "image/jpeg": ".jpg",
            "image/gif": ".gif", "image/webp": ".webp"}.get(mime, ".bin")

# Load books.json for reverse-lookup
books = json.loads((ROOT / "books.json").read_text())
# Build domain -> book name map (lowercase for matching)
domain_to_book = {}
for b in books:
    from urllib.parse import urlparse
    parsed = urlparse(b["url"])
    host = parsed.netloc.replace("www.", "")
    domain_to_book[host.lower()] = b["name"]
    # Also without TLD
    parts = host.split(".")
    if len(parts) >= 2:
        domain_to_book[parts[0].lower()] = b["name"]

# Scan logos directory
manifest = {}
for f in sorted(LOGOS_DIR.iterdir()):
    if not f.is_file():
        continue
    if f.stat().st_size < 300:
        continue
    
    data = f.read_bytes()
    mime = detect_mime(data)
    if mime in ("text/html", "application/octet-stream"):
        continue  # Skip non-image files
    
    # Determine domain from filename
    stem = f.stem  # e.g. "betrivers_com" -> "betrivers.com"
    domain = stem.replace("_", ".")
    # Fix known patterns
    domain = domain.replace(".com.au", ".com.au")  # keep TLDs
    
    sha = hashlib.sha256(data).hexdigest()
    
    # Try to find matching book name
    book_name = domain_to_book.get(domain.lower(), domain_to_book.get(domain.split(".")[0].lower(), domain))
    
    manifest[book_name] = {
        "name": book_name,
        "domain": domain,
        "status": "existing",
        "size": f.stat().st_size,
        "content_type": mime,
        "sha256": sha,
        "source_url": f"logos/{f.name}",
        "file": f.name,
    }

# Write manifest
MANIFEST.write_text(json.dumps(manifest, indent=2))

# Also write a simple lookup JSON for the HTML
total_books = len(books)
total_logos = len(manifest)

print(f"Manifest rebuilt: {total_logos} logos on disk for {total_books} books")
print(f"Coverage: {total_logos}/{total_books} = {100*total_logos/total_books:.1f}%")
