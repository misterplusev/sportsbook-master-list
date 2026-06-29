#!/usr/bin/env python3
"""Final manifest rebuild with aggressive matching"""
import json, hashlib, pathlib, re
from urllib.parse import urlparse

ROOT = pathlib.Path("D:/sportsbook-master-list")
LOGOS_DIR = ROOT / "logos"
books = json.loads((ROOT / "books.json").read_text())

def detect_mime(data):
    s = data[:16]
    if s[:4] == b'\x89PNG': return 'image/png'
    if s[:5] in (b'<svg ', b'<svg\n'): return 'image/svg+xml'
    if s[:4] == b'<?xm': return 'image/svg+xml'
    if s[:4] == b'GIF8': return 'image/gif'
    if s[:3] == b'\xff\xd8\xff': return 'image/jpeg'
    if s[:4] == b'RIFF': return 'image/webp'
    if s[:4] == b'\x00\x00\x01\x00': return 'image/x-icon'
    low = data[:500].lower()
    if b'<svg' in low and (b'viewbox' in low or b'<path' in low): return 'image/svg+xml'
    if b'<!doctype' in low or b'<html' in low: return 'text/html'
    return 'application/octet-stream'

def file_to_domains(f):
    """Given a filename, return list of possible domains it could match"""
    stem = f.stem.lower()
    # Remove suffixes
    for suffix in ['.favicon', '_favicon', '_alt', '_tmp', '_f', '_probe']:
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
    
    # Base domain: underscores -> dots
    base = stem.replace('_', '.')
    domains = [base]
    
    # Also add variant without TLD parts for partial matching
    parts = stem.split('_')
    if len(parts) >= 2:
        domains.append(f"{parts[0]}.{parts[1]}")  # e.g. betmgm.com from betmgm_com_uk
    
    # Handle co_uk, co_nz, com_au, com etc
    if 'co_uk' in stem:
        domains.append(base.replace('co_uk', 'co.uk'))
    if 'co_nz' in stem:
        domains.append(base.replace('co_nz', 'co.nz'))
    if 'com_au' in stem:
        domains.append(base.replace('com_au', 'com.au'))
    if 'com' in parts and parts[-1] == 'com':
        domains.append('.'.join(parts))
    
    return list(set(domains))

# Priority for mime types (higher = better)
PRIORITY = {'image/svg+xml': 6, 'image/png': 5, 'image/webp': 4, 'image/jpeg': 3, 'image/x-icon': 2, 'image/gif': 1}

# Build domain->best_logo mapping
domain_best = {}  # normalized_domain -> (f, data, mime, sha)

for f in sorted(LOGOS_DIR.iterdir()):
    if not f.is_file() or f.stat().st_size < 300: continue
    data = f.read_bytes()
    mime = detect_mime(data)
    if mime in ('text/html', 'application/octet-stream'): continue
    sha = hashlib.sha256(data).hexdigest()
    
    domains = file_to_domains(f)
    for domain in domains:
        norm = domain.lower().strip()
        existing = domain_best.get(norm)
        if existing is None or PRIORITY.get(mime, 0) > PRIORITY.get(existing[2], 0):
            domain_best[norm] = (f, data, mime, sha)

# Also build a "fuzzy" lookup: alphanumeric only
fuzzy_map = {}  # alphanumeric_only -> domain
for domain in domain_best:
    key = re.sub(r'[^a-z0-9]', '', domain.lower())
    fuzzy_map[key] = domain

print(f"Valid image files: {sum(1 for f in LOGOS_DIR.iterdir() if f.is_file() and f.stat().st_size > 300 and detect_mime(f.read_bytes()) not in ('text/html', 'application/octet-stream'))}")
print(f"Unique domains mapped: {len(domain_best)}")

# Build manifest
manifest = {}
verified = 0
missing_list = []

for b in books:
    host = urlparse(b['url']).netloc.replace('www.', '').lower()
    
    # Try exact
    logo_info = domain_best.get(host)
    
    # Try fuzzy
    if not logo_info:
        host_fuzzy = re.sub(r'[^a-z0-9]', '', host)
        matched_domain = fuzzy_map.get(host_fuzzy)
        if matched_domain:
            logo_info = domain_best[matched_domain]
    
    # Try stem-based: host with _ instead of . and -
    if not logo_info:
        stem_key = host.replace('.', '_').replace('-', '_')
        for domain, val in domain_best.items():
            domain_stem = domain.replace('.', '_').replace('-', '_')
            if domain_stem == stem_key:
                logo_info = val
                break
    
    # Try without TLD
    if not logo_info:
        host_no_tld = host.rsplit('.', 1)[0] if '.' in host else host
        for domain, val in domain_best.items():
            dom_no_tld = domain.rsplit('.', 1)[0] if '.' in domain else domain
            if dom_no_tld == host_no_tld:
                logo_info = val
                break
    
    if logo_info:
        f, data, mime, sha = logo_info
        manifest[b['name']] = {
            'name': b['name'], 'domain': host, 'status': 'verified',
            'size': len(data), 'content_type': mime, 'sha256': sha,
            'source_url': f'logos/{f.name}', 'file': f.name,
        }
        verified += 1
    else:
        manifest[b['name']] = {
            'name': b['name'], 'domain': host, 'status': 'missing',
            'size': 0, 'content_type': '', 'sha256': '', 'source_url': '', 'file': '',
        }
        missing_list.append(b)

(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print(f"\n✓ Manifest: {len(manifest)} entries")
print(f"✓ Verified: {verified}/214 ({100*verified/214:.1f}%)")
print(f"✗ Missing: {len(missing_list)}")

if missing_list:
    print(f"\n--- Still missing ({len(missing_list)}) ---")
    for b in missing_list:
        host = urlparse(b['url']).netloc.replace('www.', '')
        print(f"  {b['name']:45} {host}")
