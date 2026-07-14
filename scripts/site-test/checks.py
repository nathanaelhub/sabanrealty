#!/usr/bin/env python3
"""
Static checks for the Saban Realty site. No browser needed.
Run from repo root:  python3 scripts/site-test/checks.py
Exit code 0 = all pass. Prints PASS/FAIL per check.

Checks: listings.json parse, sitemap XML + filesystem consistency,
JSON-LD validity on every page, noindex isolation (engine yes / generated
pages no / redirect stubs yes), CSS brace balance + min sync heuristic,
internal broken-link sweep (spins its own local server, honors <base href>).
"""
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
FAILURES = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}: {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")


def real_pages():
    """Hand-authored + generated pages that should be valid, indexable HTML."""
    pages = ["index.html", "404.html", "property-detail.html"]
    pages += sorted(glob.glob("*/index.html"))          # buy/ rent/ sell/ about/ contact/ st-eustatius/ blog/
    pages += sorted(glob.glob("blog/*/index.html"))
    pages += sorted(glob.glob("properties/*/index.html"))
    pages += sorted(glob.glob("rentals/*/index.html"))
    return pages


# ---------- 1. listings.json ----------
try:
    data = json.load(open("data/listings.json"))
    check("listings.json parses", True)
    ids = [p["id"] for p in data["properties"]] + [p["id"] for p in data["rentals"]]
    check("listing ids unique", len(ids) == len(set(ids)))
except Exception as e:
    check("listings.json parses", False, str(e))
    data = {"properties": [], "rentals": []}

# ---------- 2. sitemap ----------
try:
    xml.dom.minidom.parse("sitemap.xml")
    check("sitemap.xml valid XML", True)
except Exception as e:
    check("sitemap.xml valid XML", False, str(e))
sm = open("sitemap.xml").read()
sm_urls = re.findall(r"<loc>https://sabanrealty\.com(/[^<]*)</loc>", sm)
missing_files = []
for u in sm_urls:
    path = u.lstrip("/")
    f = (path + "index.html") if (u.endswith("/") or u == "/") else path
    if u == "/":
        f = "index.html"
    if not os.path.isfile(f):
        missing_files.append(u)
check("every sitemap URL has a file", not missing_files, str(missing_files))

visible = [p for p in data["properties"] if not p.get("hidden")]
missing_sm = [p["id"] for p in visible if f"/properties/{p['id']}/" not in sm_urls]
missing_sm += [p["id"] for p in data["rentals"] if not p.get("hidden") and f"/rentals/{p['id']}/" not in sm_urls]
check("every visible listing is in sitemap", not missing_sm, str(missing_sm))

# ---------- 3. JSON-LD everywhere ----------
bad_ld = []
n_ld = 0
for f in real_pages():
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', open(f, encoding="utf-8").read(), re.S):
        n_ld += 1
        try:
            json.loads(m.group(1))
        except Exception as e:
            bad_ld.append(f"{f}: {e}")
check(f"JSON-LD parses ({n_ld} blocks)", not bad_ld, "; ".join(bad_ld[:3]))

# ---------- 4. noindex isolation ----------
check("engine property-detail.html has noindex",
      'content="noindex"' in open("property-detail.html").read())
leaked = [f for f in glob.glob("properties/*/index.html") + glob.glob("rentals/*/index.html")
          if 'content="noindex"' in open(f).read()]
check("generated listing pages have NO noindex", not leaked, str(leaked))
stubs = [f for f in glob.glob("*.html") if f not in ("index.html", "404.html", "property-detail.html")]
stubs += glob.glob("blog/*.html")
stubs = [s for s in stubs if s != "blog/index.html"]
unstubbed = [s for s in stubs if 'content="noindex"' not in open(s).read()]
check("redirect stubs are noindex", not unstubbed, str(unstubbed))

# ---------- 5. CSS ----------
css = open("css/styles.css").read()
check("styles.css braces balanced", css.count("{") == css.count("}"))
mincss = open("css/styles.min.css").read()
sample = re.findall(r"(?m)^\.([a-zA-Z][\w-]+)\s*[,{]", css)
missing_min = [c for c in set(sample) if c not in mincss]
check("styles.min.css in sync (all top-level classes present)", not missing_min, str(sorted(missing_min)[:8]))

# ---------- 6. broken internal links (local server) ----------
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8899"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
try:
    base = "http://localhost:8899/"
    sweep = ["", "buy/", "rent/", "sell/", "about/", "contact/", "st-eustatius/", "blog/"]
    sweep += [u.lstrip("/") for u in sm_urls if "/blog/" in u][:2]
    sweep += [u.lstrip("/") for u in sm_urls if "/properties/" in u][:3]
    sweep += [u.lstrip("/") for u in sm_urls if "/rentals/" in u][:1]

    def status(u):
        try:
            return urllib.request.urlopen(u, timeout=5).status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception as e:
            return str(e)[:40]

    seen, broken = set(), []
    for pg in sweep:
        html = urllib.request.urlopen(base + pg, timeout=5).read().decode("utf-8", "ignore")
        bm = re.search(r'<base href="([^"]+)"', html)
        pbase = urllib.parse.urljoin(base + pg, bm.group(1)) if bm else base + pg
        for m in re.findall(r'(?:href|src)="([^"]+)"', html):
            if m.startswith(("http", "mailto:", "tel:", "#", "data:", "javascript:")) or "${" in m or not m.strip():
                continue
            full = urllib.parse.urljoin(pbase, m)
            if not full.startswith(base) or full in seen:
                continue
            seen.add(full)
            st = status(full)
            if st != 200:
                broken.append(f"[{st}] {m} (on {pg or 'home'})")
    check(f"no broken internal links ({len(seen)} checked)", not broken, "; ".join(broken[:5]))
finally:
    srv.terminate()

# ---------- result ----------
print()
if FAILURES:
    print(f"RESULT: {len(FAILURES)} FAILURE(S)")
    sys.exit(1)
print("RESULT: ALL STATIC CHECKS PASS")
