#!/usr/bin/env python3
"""Copy existing logos from E:/abet/dashboard/public/logos/books/ into the master list logos dir."""
import pathlib, shutil, json

ROOT = pathlib.Path("C:/Users/chris/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
SOURCE = pathlib.Path("E:/abet/dashboard/public/logos/books")

# Map filenames to domain patterns
# The E: drive uses human-readable names like "betrivers.png", "ATG.svg"
# We need to match these to the master list's "host_ext" naming

manifest = json.loads((ROOT / "manifest.json").read_text())
books = json.loads((ROOT / "books.json").read_text())

# Build reverse map: domain -> possible filename patterns
copied = 0
skipped = 0

# First, let's just copy ALL files from E: drive and rename to match master list naming
for src_file in SOURCE.iterdir():
    if not src_file.is_file():
        continue
    if src_file.stat().st_size < 300:
        continue
    if "backup" in src_file.name.lower() or "temp" in src_file.name.lower():
        continue
    
    name = src_file.stem  # e.g. "betrivers", "ATG", "ballybet"
    ext = src_file.suffix  # e.g. ".png", ".svg", ".ico"
    
    # Try to find a matching entry in manifest
    matched = False
    for key, info in manifest.items():
        domain = info.get("domain", "")
        safe_domain = domain.replace(".", "_").replace("-", "_")
        # Check if name matches domain pattern
        if (name.lower() == info.get("name", "").lower() or 
            name.lower().replace("_", "") == info.get("name", "").lower().replace(" ", "").replace("(", "").replace(")", "") or
            safe_domain.lower() in name.lower() or
            name.lower() in safe_domain.lower()):
            # Copy with the proper naming
            dest = LOGOS_DIR / f"{safe_domain}{ext}"
            if not dest.exists() or dest.stat().st_size < 300:
                shutil.copy2(src_file, dest)
                print(f"  COPIED: {src_file.name} -> {dest.name} ({src_file.stat().st_size}b)")
                copied += 1
            else:
                skipped += 1
            matched = True
            break
    
    if not matched:
        # Try to find domain from the filename
        for book in books:
            book_name = book["name"]
            if (name.lower().replace("_", "").replace(" ", "") == 
                book_name.lower().replace(" ", "").replace("(", "").replace(")", "").replace(".", "")):
                parsed = __import__('urllib.parse').parse.urlparse(book["url"])
                host = parsed.netloc
                safe_domain = host.replace(".", "_").replace("-", "_")
                dest = LOGOS_DIR / f"{safe_domain}{ext}"
                if not dest.exists() or dest.stat().st_size < 300:
                    shutil.copy2(src_file, dest)
                    print(f"  COPIED: {src_file.name} -> {dest.name}")
                    copied += 1
                else:
                    skipped += 1
                break

print(f"\nCopied: {copied}, Skipped (already exists): {skipped}")
