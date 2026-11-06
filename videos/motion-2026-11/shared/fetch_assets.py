#!/usr/bin/env python3
"""Fill assets/<listing>/ once per photo. Skips anything already there, so r2.dev is never refetched.
The 2026-10-03 originals backup is preferred because R2 listing photos were shrunk to 1600 px;
R2 is only used for photos newer than the backup, with a delay between requests."""
import json, shutil, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
BACKUP = Path.home() / "Documents/sabanrealty-photo-originals-2026-10-03"
DELAY = 1.5

data = json.loads((REPO / "data/listings.json").read_text())
rows = data if isinstance(data, list) else data.get("listings") or data.get("properties")
listings = {p["id"]: p for p in rows}

for lid in sys.argv[1:]:
    out = ROOT / "assets" / lid
    out.mkdir(parents=True, exist_ok=True)
    for url in listings[lid]["images"]:
        name = urllib.parse.unquote(url.rsplit("/", 1)[1])
        dest = out / name
        if dest.exists():
            continue
        src = BACKUP / "listings" / lid / name
        if src.exists():
            shutil.copy2(src, dest)
            print("backup", dest.relative_to(ROOT))
        else:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            print("r2    ", dest.relative_to(ROOT))
            time.sleep(DELAY)
