#!/usr/bin/env python3
"""prep_photos.py <video dir>: resample each photo in timeline.json to cover the frame at 1.15x, so per-frame
drawing is close to 1:1 and slow moves stay clean. Plain Lanczos only: no generative or AI upscaling."""
import json, sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps
ROOT = Path(__file__).resolve().parent.parent
vid = Path(sys.argv[1]).resolve()
tl = json.loads((vid / "timeline.json").read_text())
out = ROOT / "build" / vid.name / "photos"
out.mkdir(parents=True, exist_ok=True)
for key, src in tl.get("photos", {}).items():
    p = ROOT / "assets" / src
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    s = max(tl["width"] / im.width, tl["height"] / im.height) * 1.15
    res = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if s > 1.05:
        res = res.filter(ImageFilter.UnsharpMask(radius=1.6, percent=22, threshold=3))
    res.save(out / f"{key}.jpg", quality=95, subsampling=0)
    print(f"{key:12} {src:58} {im.width}x{im.height}  upscale {s:.2f}x")
