#!/bin/bash
# Fast logo triage - tries favicon.ico and apple-touch-icon.png with curl
# Outputs a list of books that CAN be recovered quickly

MANIFEST="/c/Users/chris/sportsbook-master-list/manifest.json"
LOGOS_DIR="/c/Users/chris/sportsbook-master-list/logos"
TRIAGE_FILE="/c/Users/chris/sportsbook-master-list/proofs/20260627/triage_results.jsonl"

mkdir -p "$(dirname "$TRIAGE_FILE")"

# Extract failed book names and domains from manifest
# Use python just for JSON parsing (one-shot, fast)
"/c/Users/chris/AppData/Local/hermes/hermes-agent/venv/Scripts/python" -c "
import json
m = json.load(open('$MANIFEST'))
failed = [(k,v) for k,v in m.items() if v.get('status') == 'failed']
for k,v in failed:
    print(f'{k}\t{v.get(\"domain\",\"\")}')
" | while IFS=$'\t' read -r name domain; do
    [ -z "$domain" ] && continue
    safe=$(echo "$domain" | tr '.' '_' | tr '-' '_')
    
    # Skip if already has a good file
    found=0
    for ext in .png .svg .jpg .webp .ico; do
        if [ -f "$LOGOS_DIR/${safe}${ext}" ] && [ "$(stat -c%s "$LOGOS_DIR/${safe}${ext}" 2>/dev/null)" -gt 300 ]; then
            found=1
            break
        fi
    done
    [ "$found" = "1" ] && continue
    
    # Try favicon.ico
    status="failed"
    url="https://${domain}/favicon.ico"
    tmpfile=$(mktemp)
    http_code=$(curl -sS -o "$tmpfile" -w "%{http_code}" --max-time 15 -H "User-Agent: Mozilla/5.0" "$url" 2>/dev/null)
    
    if [ "$http_code" = "200" ]; then
        size=$(stat -c%s "$tmpfile" 2>/dev/null || echo 0)
        if [ "$size" -gt 300 ]; then
            # Check magic bytes
            magic=$(head -c 4 "$tmpfile" | xxd -p 2>/dev/null)
            if [[ "$magic" == "89504e47" ]] || [[ "$magic" == "3c3f786d" ]] || [[ "$magic" == "3c737667" ]] || [[ "$magic" == "47494638" ]] || [[ "$magic" == "52494646" ]] || [[ "$magic" == "00000100" ]] || [[ "$magic" == "ffd8ffe0" ]] || [[ "$magic" == "ffd8ffe1" ]]; then
                # Determine ext from magic
                ext=".bin"
                [[ "$magic" == "89504e47" ]] && ext=".png"
                [[ "$magic" == "3c3f786d" || "$magic" == "3c737667" ]] && ext=".svg"
                [[ "$magic" == "47494638" ]] && ext=".gif"
                [[ "$magic" == "52494646" ]] && ext=".webp"
                [[ "$magic" == "00000100" ]] && ext=".ico"
                [[ "$magic" == "ffd8ffe0" || "$magic" == "ffd8ffe1" ]] && ext=".jpg"
                cp "$tmpfile" "$LOGOS_DIR/${safe}${ext}"
                echo "{\"name\":\"$name\",\"domain\":\"$domain\",\"status\":\"saved\",\"source\":\"favicon.ico\",\"size\":$size,\"ext\":\"$ext\"}" >> "$TRIAGE_FILE"
                echo "OK: $name -> favicon.ico (${size}b, $ext)"
                status="saved"
            fi
        fi
    fi
    
    if [ "$status" = "failed" ]; then
        # Try apple-touch-icon.png
        url2="https://${domain}/apple-touch-icon.png"
        http_code2=$(curl -sS -o "$tmpfile" -w "%{http_code}" --max-time 15 -H "User-Agent: Mozilla/5.0" "$url2" 2>/dev/null)
        
        if [ "$http_code2" = "200" ]; then
            size=$(stat -c%s "$tmpfile" 2>/dev/null || echo 0)
            if [ "$size" -gt 300 ]; then
                magic=$(head -c 4 "$tmpfile" | xxd -p 2>/dev/null)
                ext=".png"
                cp "$tmpfile" "$LOGOS_DIR/${safe}${ext}"
                echo "{\"name\":\"$name\",\"domain\":\"$domain\",\"status\":\"saved\",\"source\":\"apple-touch-icon.png\",\"size\":$size,\"ext\":\"$ext\"}" >> "$TRIAGE_FILE"
                echo "OK: $name -> apple-touch-icon.png (${size}b)"
                status="saved"
            fi
        fi
    fi
    
    if [ "$status" = "failed" ]; then
        echo "{\"name\":\"$name\",\"domain\":\"$domain\",\"status\":\"failed\",\"http_favicon\":$http_code}" >> "$TRIAGE_FILE"
        echo "FAIL: $name (favicon HTTP $http_code)"
    fi
    
    rm -f "$tmpfile"
done

echo "=== TRIAGE COMPLETE ==="
echo "Saved: $(grep -c '\"status\":\"saved\"' "$TRIAGE_FILE" 2>/dev/null || echo 0)"
echo "Failed: $(grep -c '\"status\":\"failed\"' "$TRIAGE_FILE" 2>/dev/null || echo 0)"
