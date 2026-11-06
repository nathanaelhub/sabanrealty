#!/usr/bin/env python3
"""still_sheet.py <video dir> <out.jpg> [columns]: tile every QC still, with safe zones on vertical videos."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent
import os
d = ROOT / "build" / Path(sys.argv[1]).name / os.environ.get("STILLS", "stills")
fs = sorted(d.glob("*.png")); C = int(sys.argv[3]) if len(sys.argv) > 3 else 4
first = Image.open(fs[0]); v = first.height > first.width
tw = 330 if v else 640; th = round(tw * first.height / first.width)
sheet = Image.new("RGB", (tw * C, (th + 22) * ((len(fs) + C - 1) // C)), "#333"); dr = ImageDraw.Draw(sheet)
k = tw / first.width
for i, f in enumerate(fs):
    x, y = (i % C) * tw, (i // C) * (th + 22)
    sheet.paste(Image.open(f).convert("RGB").resize((tw - 4, th), Image.LANCZOS), (x, y))
    if v:
        dr.line((x, y + 220 * k, x + tw - 4, y + 220 * k), fill="#f00"); dr.line((x, y + 1520 * k, x + tw - 4, y + 1520 * k), fill="#f00")
    dr.text((x + 4, y + th + 4), f.stem, fill="#fff")
sheet.save(sys.argv[2], quality=90)
