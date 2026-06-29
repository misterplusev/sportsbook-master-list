#!/usr/bin/env python3
"""Rebuild manifest from disk — fixed domain matching"""
import json, hashlib, pathlib, re
from urllib.parse import urlparse

ROOT = pathlib.Path("D:/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
books = json.loads((ROOT / "books.json").read_text())

def detect_mime(data):
    s = data[:16]
    if s[:4] == b'\x89PNG\r\n\x1a\n': return 'image/png'
    if s[:5] in (b'<svg ', b'<svg\n'): return 'image/svg+xml'
    if s[:4] == b'<?xm': return 'image/svg+xml'
    if s[:5] in (b'GIF87a', b'GIF89a'): return 'image/gif'
    if s[:3] == b'\xff\xd8\xff': return 'image/jpeg'
    if s[:4] == b'RIFF': return 'image/webp'
    if s[:4] == b'\x00\x00\x01\x00': return 'image/x-icon'
    low = data[:500].lower()
    if b'<svg' in low: return 'image/svg+xml'
    if b'<!doctype' in low or b'<html' in low: return 'text/html'
    return 'application/octet-stream'

def stem_to_domain(stem):
    """Convert filename stem to domain. e.g. '4cx_com.favicon' -> '4cx.com', 'bet99_ca' -> 'bet99.ca'"""
    s = stem.lower()
    # Remove common suffixes
    for suffix in ['.favicon', '_favicon', '_alt', '_tmp', '_f']:
        if s.endswith(suffix):
            s = s[:-len(suffix)]
    # Replace underscores with dots
    return s.replace('_', '.')

# Build host->logo mapping from disk
host_to_logo = {}
for f in sorted(LOGOS_DIR.iterdir()):
    if not f.is_file() or f.stat().st_size < 300: continue
    data = f.read_bytes()
    mime = detect_mime(data)
    if mime in ('text/html', 'application/octet-stream'): continue
    sha = hashlib.sha256(data).hexdigest()
    
    domain = stem_to_domain(f.stem)
    
    # Store best logo per domain (prefer svg > png > webp > jpg > ico > gif)
    priority = {'image/svg+xml': 6, 'image/png': 5, 'image/webp': 4, 'image/jpeg': 3, 'image/x-icon': 2, 'image/gif': 1}
    existing = host_to_logo.get(domain)
    if existing is None or priority.get(mime, 0) > priority.get(existing[2], 0):
        host_to_logo[domain] = (f, data, mime, sha)

print(f'Unique domains with logos on disk: {len(host_to_logo)}')
print("Sample domains:", sorted(list(host_to_logo.keys()))[:20])

# Build manifest: EVERY book gets an entry
manifest = {}
verified_count = 0
missing_books = []
for b in books:
    host = urlparse(b['url']).netloc.replace('www.', '').lower()
    
    # Try exact match
    logo_info = host_to_logo.get(host)
    
    # Try without dashes
    if not logo_info:
        logo_info = host_to_logo.get(host.replace('-', ''))
    
    # Try replacing dots and dashes differently
    if not logo_info:
        for key, val in host_to_logo.items():
            # Normalize both for comparison
            norm_key = key.replace('.', '').replace('-', '').lower()
            norm_host = host.replace('.', '').replace('-', '').lower()
            if norm_key == norm_host:
                logo_info = val
                break
    
    if logo_info:
        f, data, mime, sha = logo_info
        manifest[b['name']] = {
            'name': b['name'], 'domain': host, 'status': 'verified',
            'size': len(data), 'content_type': mime, 'sha256': sha,
            'source_url': f'logos/{f.name}', 'file': f.name,
        }
        verified_count += 1
    else:
        manifest[b['name']] = {
            'name': b['name'], 'domain': host, 'status': 'missing',
            'size': 0, 'content_type': '', 'sha256': '', 'source_url': '', 'file': '',
        }
        missing_books.append(b)

(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print(f'\nManifest: {len(manifest)} entries')
print(f'Verified: {verified_count}/214 ({100*verified_count/214:.1f}%)')
print(f'Missing: {len(missing_books)}')

if missing_books:
    print(f'\nMissing ({len(missing_books)}):')
    for b in missing_books:
        host = urlparse(b['url']).netloc.replace('www.', '')
        print(f'  {b["name"]:45} {host}')
