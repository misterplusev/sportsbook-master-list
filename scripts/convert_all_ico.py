# Convert all ICO files to PNG for better browser rendering
import json, os
from PIL import Image

logos_dir = "logos"
converted = []
for f in sorted(os.listdir(logos_dir)):
    if f.endswith('.ico') and not f.endswith('.png'):
        ico_path = os.path.join(logos_dir, f)
        png_path = ico_path.replace('.ico', '.png')
        if os.path.exists(png_path):
            continue
        try:
            img = Image.open(ico_path)
            # Get largest resolution from multi-icon ICO
            sizes = []
            try:
                # PIL can extract sizes from ICO
                for size in img.encoderinfo.get('sizes', []):
                    sizes.append(size)
            except:
                pass
            if sizes:
                best = max(sizes, key=lambda s: s[0]*s[1])
                img = img.resize(best)
            img.save(png_path)
            converted.append(f"{f} -> {os.path.basename(png_path)}")
        except Exception as e:
            print(f"FAIL {f}: {e}")

print(f"Converted {len(converted)} files:")
for c in converted:
    print(f"  {c}")
