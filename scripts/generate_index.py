#!/usr/bin/env python3
"""
generate_index.py — read books.json + manifest.json + state_availability.json + book_categories.json,
generate index.html with embedded state + category data for filtering.
"""
import json, pathlib, re

ROOT = pathlib.Path("D:/sportsbook-master-list")
books = json.loads((ROOT / "books.json").read_text())
manifest = json.loads((ROOT / "manifest.json").read_text())
state_data = json.loads((ROOT / "data/state_availability.json").read_text())
categories_data = json.loads((ROOT / "data/book_categories.json").read_text())

BOOKS_TO_STATES = state_data["books_to_states"]
STATE_NAMES = state_data["state_names"]
INTERNATIONAL = state_data["international"]
CATEGORY_EMOJIS = categories_data.get("category_emojis", {})
BOOKS_CATEGORIES = categories_data.get("books", {})

def normalize_name(n):
    return re.sub(r'[^a-z0-9]', '', n.lower())

norm_to_states = {}
for book, states in BOOKS_TO_STATES.items():
    key = normalize_name(book)
    norm_to_states[key] = states

for book in books:
    name = book["name"]
    n = normalize_name(name)
    states = norm_to_states.get(n, [])
    
    # Try partial matches
    if not states:
        for key, st in norm_to_states.items():
            if n[:5] in key or key[:5] in n:
                states = st
                break
    
    # Check international
    is_intl = name in INTERNATIONAL or not states
    
    # Get categories
    cats = BOOKS_CATEGORIES.get(name, [])
    if not cats:
        # Try name normalization match
        for bk_name, bk_cats in BOOKS_CATEGORIES.items():
            if normalize_name(bk_name) == n:
                cats = bk_cats
                break
    
    book["states"] = states
    book["is_international"] = is_intl
    book["categories"] = cats

# Generate HTML
books_json = json.dumps(books, ensure_ascii=False)
# Generate HTML using string replacement (not f-string to avoid JS brace conflicts)
books_json = json.dumps(books, ensure_ascii=False)
manifest_json = json.dumps(manifest, ensure_ascii=False)
state_names_json = json.dumps(STATE_NAMES, ensure_ascii=False)
international_json = json.dumps(INTERNATIONAL, ensure_ascii=False)
categories_json = json.dumps(BOOKS_CATEGORIES, ensure_ascii=False)
category_emojis_json = json.dumps(CATEGORY_EMOJIS, ensure_ascii=False)

# State options for dropdown
state_options = ['<option value="all">All States / International</option>']
for code in sorted(STATE_NAMES):
    state_options.append('<option value="' + code + '">' + code + ' - ' + STATE_NAMES[code] + '</option>')
state_options_html = "\n".join(state_options)

# Read the template from a separate file to avoid f-string issues
template_path = ROOT / "scripts" / "index_template.html"
if template_path.exists():
    html = template_path.read_text(encoding='utf-8')
    html = html.replace('__BOOKS_JSON__', books_json)
    html = html.replace('__MANIFEST_JSON__', manifest_json)
    html = html.replace('__STATE_NAMES__', state_names_json)
    html = html.replace('__INTERNATIONAL__', international_json)
    html = html.replace('__STATE_OPTIONS__', state_options_html)
    html = html.replace('__BOOKS__', books_json)
    html = html.replace('__MANIFEST__', manifest_json)
    html = html.replace('__STATENAMES__', state_names_json)
    html = html.replace('__CATS__', categories_json)
    html = html.replace('__CATEEMOJIS__', category_emojis_json)
else:
    # Fallback: write data as separate JS file and patch the existing index.html
    print("WARNING: index_template.html not found, falling back to data JS file")
    # Write state data to a separate JS file
    js_content = f"const BOOKS_DATA = {books_json};\nconst MANIFEST_DATA = {manifest_json};\nconst STATE_NAMES = {state_names_json};\nconst INTERNATIONAL_DATA = {international_json};\n"
    (ROOT / "data" / "app_data.js").write_text(js_content, encoding='utf-8')
    # Fall back to the existing index.html with state filter added via patch
    pass

(ROOT / "index.html").write_text(html, encoding='utf-8')
print(f"Generated index.html: {len(html)} bytes")
print(f"Books: {len(books)}")
print(f"States in dropdown: {len(STATE_NAMES)}")
