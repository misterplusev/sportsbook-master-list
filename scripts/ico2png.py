from PIL import Image
import pathlib

# Convert granawin ICO to PNG
img = Image.open('logos/granawin_com.ico')
# Get the largest size from multi-resolution ICO
try:
    sizes = img.info.get('sizes', [])
    if sizes:
        best = max(sizes, key=lambda s: s[0]*s[1])
        img = img.resize(best)
    else:
        img = img.resize((128,128))
except:
    pass
img.save('logos/granawin_com.png')
print(f"Saved granawin_com.png: {img.size}")
