#!/usr/bin/env python3
"""
find_logo_smart.py — given a homepage URL, find its logo/favicon by:
  1. Fetch homepage HTML, extract <link rel=icon|apple-touch-image> and <meta og:image>
  2. Try common favicon paths
  3. Try logo on Wikimedia Commons (via search by brand name)
Usage: python find_logo_smart.py <url> <output_file.png|ico|svg>
Example: python find_logo_smart.py https://www.veikkaus.fi veikkaus_fi.png
"""
import sys, re, os, pathlib, subprocess, json, time

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TIMEOUT = 10

def curl_save(url, outfile, headers=None):
    """Download URL to outfile, return (success_bool, is_image_bool, size)"""
    cmd = ["curl", "-sSL", "--max-time", str(TIMEOUT),
           "-H", f"User-Agent: {UA}",
           "-H", "Accept: image/*,*/*;q=0.9",
           "-o", outfile, url]
    try:
        r = subprocess.run(cmd, timeout=TIMEOUT+5, capture_output=True)
        if os.path.exists(outfile) and os.path.getsize(outfile) > 100:
            with open(outfile, 'rb') as f:
                head = f.read(500)
            if b'<!DOCTYPE' in head or (b'<html' in head and b'<svg' not in head[:50]):
                return False, False, 0  # HTML
            if head[:4] == b'\x89PNG': return True, True, os.path.getsize(outfile)
            if head[:3] == b'\xff\xd8\xff': return True, True, os.path.getsize(outfile)
            if head[:4] == b'RIFF': return True, True, os.path.getsize(outfile)
            if head[:4] == b'GIF8': return True, True, os.path.getsize(outfile)
            if head[:4] == b'\x00\x00\x01\x00': return True, True, os.path.getsize(outfile)
            if head[:5] in (b'<svg ', b'<svg\n'): return True, True, os.path.getsize(outfile)
            if head[:4] == b'<?xm': return True, True, os.path.getsize(outfile)
            low = head.lower()
            if b'<svg' in low and (b'viewbox' in low or b'<path' in low): return True, True, os.path.getsize(outfile)
            return True, False, os.path.getsize(outfile)  # might be image, unknown format
    except:
        pass
    return False, False, 0

def curl_get(url):
    """GET URL and return HTML text"""
    try:
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", str(TIMEOUT),
             "-H", f"User-Agent: {UA}",
             "-H", "Accept: text/html,*/*;q=0.9", url],
            timeout=TIMEOUT+5, capture_output=True)
        text = r.stdout.decode('utf-8', errors='replace')
        lower = text[:500].lower()
        if 'just a moment' in lower or 'cf-browser-verification' in lower:
            return ""  # Cloudflare
        return text
    except:
        return ""

def extract_linked_images(html, base_url):
    """Extract image URLs from <link> and <meta> tags"""
    images = []
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # <link rel="icon|shortcut icon|apple-touch-icon" href="...">
    for m in re.finditer(r'<link[^>]+rel=["\'](?:icon|shortcut\s+icon|apple-touch-icon|apple-touch-icon-precomposed)["\'][^>]+href=["\']([^"\']+)["\']', html, re.I):
        images.append(("link-icon", m.group(1)))
    for m in re.finditer(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\'](?:icon|shortcut\s+icon|apple-touch-icon)["\']', html, re.I):
        images.append(("link-icon", m.group(1)))
    for m in re.finditer(r'<link[^>]+rel=["\'](?:mask-icon)["\'][^>]+href=["\']([^"\']+)["\']', html, re.I):
        images.append(("mask-icon", m.group(1)))
    
    # <meta property="og:image" content="...">
    for m in re.finditer(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        images.append(("og:image", m.group(1)))
    for m in re.finditer(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']', html, re.I):
        images.append(("og:image", m.group(1)))
    
    # twitter:image
    for m in re.finditer(r'<meta[^>]+(?:name|property)=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        images.append(("twitter:image", m.group(1)))
    
    # img src with logo/brand in path
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I):
        src = m.group(1)
        if any(k in src.lower() for k in ['logo', 'brand', 'header-logo', 'main-logo', 'site-logo']):
            images.append(("img-logo", src))
    
    # Resolve relative URLs
    resolved = []
    for tag, url in images:
        if url.startswith("http"):
            resolved.append((tag, url))
        elif url.startswith("//"):
            resolved.append((tag, f"https:{url}"))
        elif url.startswith("/"):
            resolved.append((tag, f"{base}{url}"))
        else:
            resolved.append((tag, f"{base}/{url}"))
    
    return resolved

def get_common_favicon_urls(hostname):
    """Generate common favicon URLs"""
    base = f"https://{hostname}"
    common_names = ["favicon", "favicon.ico", "icon", "apple-touch-icon", "apple-touch-icon-precomposed",
                    "android-icon-192x192", "favicon-32x32", "favicon-96x96", "favicon-16x16"]
    common_paths = [
        "/favicon.ico", "/favicon.png", "/favicon.svg",
        "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png",
        "/safari-pinned-tab.svg",
        "/images/favicon.ico", "/images/favicon.png", "/images/favicon.svg",
        "/images/logo.svg", "/images/logo.png", "/images/icon.png",
        "/assets/favicon.ico", "/assets/favicon.png", "/assets/favicon.svg",
        "/assets/logo.svg", "/assets/logo.png", "/assets/icons/favicon.ico",
        "/static/favicon.ico", "/static/favicon.png", "/static/favicon.svg",
        "/static/logo.svg", "/static/logo.png",
        "/img/favicon.ico", "/img/favicon.png", "/img/logo.svg",
        "/icons/favicon.ico", "/icons/favicon.png", "/icons/icon-192.png",
        "/uploads/favicon.ico", "/uploads/logo.png",
        "/content/dam/logo.png", "/-/media/logo.png", "/-/media/logo.svg",
        "/brand/logo.svg", "/brand/logo.png",
        "/logo.png", "/logo.svg",
    ]
    # Multi-size apple icons
    for size in ["120x120", "152x152", "180x180", "192x192", "512x512"]:
        common_paths.append(f"/apple-touch-icon-{size}.png")
    
    return [f"{base}{p}" for p in common_paths] + [f"{base}/{name}.png" for name in common_names] + [f"{base}/{name}.ico" for name in common_names]

def try_wikimedia_brand(brand_name):
    """Search Wikimedia Commons for a brand's logo, return download URL or None"""
    import urllib.parse
    query = urllib.parse.quote(f"{brand_name} logo")
    api_url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={query}&srnamespace=6&format=json&srlimit=5"
    try:
        r = subprocess.run(["curl", "-sSL", "--max-time", "10", "-H", f"User-Agent: {UA}", api_url], timeout=15, capture_output=True)
        data = json.loads(r.stdout)
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            if title.startswith("File:"):
                fname = title[5:]
                if any(fname.lower().endswith(ext) for ext in ['.svg', '.png', '.jpg', '.jpeg', '.gif']):
                    return fname
    except:
        pass
    return None

# === MAIN ===
if len(sys.argv) < 3:
    print("Usage: python find_logo_smart.py <homepage_url> <output_file>")
    sys.exit(1)

url = sys.argv[1]
outfile = sys.argv[2]
import tempfile
from urllib.parse import urlparse

hostname = urlparse(url).netloc.replace("www.", "")
brand = hostname.split(".")[0].title()

print(f"🔍 Finding logo for {hostname}...")
tmp = os.path.join(os.path.dirname(os.path.abspath(outfile)), ".tmp_find_logo")

# Strategy 1: Fetch homepage, parse <link>/<meta> tags
print(f"   [1/4] Checking homepage HTML for linked images...")
html = curl_get(url)
if html:
    images = extract_linked_images(html, url)
    print(f"       Found {len(images)} linked images")
    for tag, img_url in images[:8]:
        ok, is_img, size = curl_save(img_url, tmp)
        if ok and is_img:
            os.rename(tmp, outfile)
            print(f"   ✓ Got {size}b {tag}: {img_url}")
            sys.exit(0)
        elif os.path.exists(tmp): os.remove(tmp)
else:
    print("       (blocked or empty)")

# Strategy 2: Try common favicon paths
print(f"   [2/4] Trying common favicon paths ({len(get_common_favicon_urls(hostname))} URLs)...")
for fav_url in get_common_favicon_urls(hostname):
    ok, is_img, size = curl_save(fav_url, tmp)
    if ok and is_img and size > 200:
        os.rename(tmp, outfile)
        print(f"   ✓ Got {size}b from: {fav_url}")
        sys.exit(0)
    if os.path.exists(tmp): os.remove(tmp)

# Strategy 3: Wikimedia Commons
print(f"   [3/4] Searching Wikimedia Commons...")
wm_file = try_wikimedia_brand(brand)
if wm_file:
    wm_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{wm_file}"
    ok, is_img, size = curl_save(wm_url, tmp)
    if ok and is_img:
        os.rename(tmp, outfile)
        print(f"   ✓ Wikimedia: {wm_file} ({size}b)")
        sys.exit(0)
    if os.path.exists(tmp): os.remove(tmp)

# Strategy 4: Try Wikimedia with brand variations
for variant in [brand, hostname.split(".")[0], brand.replace(" ", ""), urlparse(url).netloc]:
    wm_file = try_wikimedia_brand(variant)
    if wm_file:
        wm_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{wm_file}"
        ok, is_img, size = curl_save(wm_url, tmp)
        if ok and is_img:
            os.rename(tmp, outfile)
            print(f"   ✓ Wikimedia ({variant}): {wm_file} ({size}b)")
            sys.exit(0)
        if os.path.exists(tmp): os.remove(tmp)

print(f"   ✗ No logo found for {hostname}")
if os.path.exists(tmp): os.remove(tmp)
sys.exit(1)
