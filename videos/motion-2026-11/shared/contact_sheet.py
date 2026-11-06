#!/usr/bin/env python3
"""contact_sheet.py <listing> <out.jpg>: numbered thumbnails with pixel sizes, for picking shots."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
d = Path(__file__).resolve().parent.parent / "assets" / sys.argv[1]
fs = sorted(p for p in d.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
W, H, C = 480, 330, 5
sheet = Image.new("RGB", (W * C, H * ((len(fs) + C - 1) // C)), "#111")
dr = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    size = im.size
    im.thumbnail((W - 8, H - 30))
    x, y = (i % C) * W + 4, (i // C) * H + 4
    sheet.paste(im, (x, y))
    dr.text((x, y + H - 26), f"{f.name[:42]} {size[0]}x{size[1]}", fill="#fff")
sheet.save(sys.argv[2], quality=85)
