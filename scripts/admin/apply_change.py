#!/usr/bin/env python3
"""
Apply one admin-page change to the repo. This is the only code that edits
listings on behalf of the admin page (admin/index.html -> Cloudflare Worker ->
.github/workflows/admin-publish.yml -> here).

    ADMIN_CHANGE='{"action": ...}' python3 scripts/admin/apply_change.py
    python3 scripts/admin/apply_change.py --payload change.json

Actions (for-sale listings only):
    add         {"action":"add","kind":"sale","listing":{...}}
    set-price   {"action":"set-price","id":"...","price":425000}
    set-status  {"action":"set-status","id":"...","status":"available|under-contract|sold","price":N}
    set-hidden  {"action":"set-hidden","id":"...","hidden":true|false}

Nothing in the payload is trusted: every field is validated here and the
description is run through a tag allowlist (it is rendered with innerHTML).
After any change it rewrites data/listings.json, regenerates the listing pages
and brings sitemap.xml in line. Nothing is written if validation fails.
"""
import argparse
import datetime
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

SITE = "https://sabanrealty.com"
PUBLIC_BASE = "https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev"
TYPES = ("villa", "cottage", "land", "commercial")
ISLANDS = {"saba": "Saba", "statia": "St. Eustatius"}   # text the island filters match on
ALLOWED_TAGS = ("h2", "h3", "p", "strong", "ul", "li", "br")
ADD_FIELDS = {"id", "title", "village", "island", "type", "price", "bedrooms", "bathrooms",
              "acreage", "description", "images", "videoId", "isNew", "onHomepage"}
MAX_IMAGES = 60


class ChangeError(Exception):
    """The change was refused; the message is safe to show to the person who sent it."""


# ---------- small helpers ----------

def format_price(n):
    return f"${n:,}"


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _plain_text(value, name, lo, hi):
    if not isinstance(value, str):
        raise ChangeError(f"{name} is missing")
    value = " ".join(value.split())
    if not lo <= len(value) <= hi:
        raise ChangeError(f"{name} must be {lo}-{hi} characters")
    if re.search(r'[<>"]', value):
        raise ChangeError(f'{name} cannot contain < > or "')
    return value


def _price(value):
    if not _is_int(value) or not 1 <= value <= 100_000_000:
        raise ChangeError("price must be a whole number of dollars greater than zero")
    return value


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.open, self.skip = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif self.skip:
            return
        elif tag == "br":
            self.out.append("<br>")
        elif tag in ALLOWED_TAGS:
            self.out.append(f"<{tag}>")
            self.open.append(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif not self.skip and tag in self.open:
            while self.open:
                t = self.open.pop()
                self.out.append(f"</{t}>")
                if t == tag:
                    break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data, quote=False))


def sanitize_description(text):
    """Keep only bare h2/h3/p/strong/ul/li/br tags; escape everything else."""
    s = _Sanitizer()
    s.feed(text)
    s.close()
    while s.open:
        s.out.append(f"</{s.open.pop()}>")
    return "".join(s.out).strip()


def default_image_exists(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "sabanrealty-admin"})
    try:
        return urllib.request.urlopen(req, timeout=15).status == 200
    except (urllib.error.URLError, OSError):
        return False


def default_fetch_upload_date(video_id):
    """Real publish date from the YouTube watch page; now() if YouTube won't say."""
    try:
        req = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}",
                                     headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
        page = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
        m = re.search(r'"uploadDate":"([^"]+)"', page)
        if m:
            return m.group(1)
    except (urllib.error.URLError, OSError):
        pass
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def regenerate_pages(root):
    subprocess.run([sys.executable, os.path.join(root, "scripts", "generate-listing-pages.py")],
                   check=True, stdout=subprocess.DEVNULL)


# ---------- listing edits (in memory) ----------

def _find(data, pid):
    for p in data["properties"]:
        if p["id"] == pid:
            return p
    raise ChangeError(f"no for-sale listing with id '{pid}'")


def _retitle_heading(p, label):
    """Old-style descriptions end their <h2> in ' - $price|SOLD|Under Contract'; keep that current."""
    p["description"] = re.sub(r"^(<h2>.*?) - (?:\$[\d,]+|SOLD|Under Contract)(</h2>)",
                              lambda m: f"{m.group(1)} - {label}{m.group(2)}", p["description"], count=1)


def _build_listing(data, listing, image_exists, fetch_upload_date):
    if not isinstance(listing, dict):
        raise ChangeError("listing is missing")
    unknown = sorted(set(listing) - ADD_FIELDS)
    if unknown:
        raise ChangeError(f"unexpected field(s): {', '.join(unknown)}")

    pid = listing.get("id")
    if not isinstance(pid, str) or len(pid) > 60 or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", pid):
        raise ChangeError("id must be lowercase letters, numbers and hyphens")
    if pid in [p["id"] for p in data["properties"] + data["rentals"]]:
        raise ChangeError(f"a listing with id '{pid}' already exists; change the title slightly")

    title = _plain_text(listing.get("title"), "title", 3, 80)
    village = _plain_text(listing.get("village"), "village", 2, 60)
    if listing.get("island") not in ISLANDS:
        raise ChangeError("island must be saba or statia")
    if listing.get("type") not in TYPES:
        raise ChangeError(f"type must be one of {', '.join(TYPES)}")
    price = _price(listing.get("price"))

    beds, baths = listing.get("bedrooms", 0), listing.get("bathrooms", 0)
    if not _is_int(beds) or not 0 <= beds <= 30:
        raise ChangeError("bedrooms must be a whole number")
    if not _is_num(baths) or not 0 <= baths <= 30 or (baths * 2) % 1:
        raise ChangeError("bathrooms must be a number like 2 or 2.5")
    baths = int(baths) if float(baths).is_integer() else float(baths)

    acreage = listing.get("acreage")
    if acreage is not None and (not _is_num(acreage) or not 0 < acreage <= 10_000):
        raise ChangeError("acreage must be a positive number")

    desc = listing.get("description")
    if not isinstance(desc, str) or len(desc) > 20_000:
        raise ChangeError("description is missing or too long")
    desc = sanitize_description(desc)
    if not desc:
        raise ChangeError("description is empty")

    images = listing.get("images")
    if not isinstance(images, list) or not 1 <= len(images) <= MAX_IMAGES:
        raise ChangeError(f"a listing needs between 1 and {MAX_IMAGES} photos")
    image_re = re.compile(re.escape(f"{PUBLIC_BASE}/listings/{pid}/") + r"[a-z0-9-]+\.jpg")
    if len(set(map(str, images))) != len(images) or \
            not all(isinstance(u, str) and image_re.fullmatch(u) for u in images):
        raise ChangeError("every image must be a distinct .jpg uploaded to this listing's own folder")
    for u in images:
        if not image_exists(u):
            raise ChangeError(f"photo not found in storage (upload did not finish?): {u}")

    vid = listing.get("videoId")
    if vid is not None and (not isinstance(vid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid)):
        raise ChangeError("video must be an 11-character YouTube id")
    for flag in ("isNew", "onHomepage"):
        if not isinstance(listing.get(flag, False), bool):
            raise ChangeError(f"{flag} must be true or false")

    entry = {"id": pid}
    if listing.get("isNew"):
        entry["new"] = True
    if vid:
        entry["videos"] = [{"label": "Property Tour", "id": vid, "uploadDate": fetch_upload_date(vid)}]
    entry.update({
        "title": title,
        "location": f"{village}, {ISLANDS[listing['island']]}",
        "price": price,
        "priceFormatted": format_price(price),
        "status": "for-sale",
        "type": listing["type"],
        "bedrooms": beds,
        "bathrooms": baths,
    })
    if acreage is not None:
        entry["acreage"] = acreage
    entry["description"] = desc
    entry["images"] = images
    return entry


def _set_price(p, change):
    if p.get("status") == "sold" or p.get("detailStatus") == "under-contract":
        raise ChangeError("this listing is sold or under contract; use 'Back to available' to set a price")
    p["price"] = _price(change.get("price"))
    p["priceFormatted"] = format_price(p["price"])
    _retitle_heading(p, p["priceFormatted"])
    return f"change price of {p['title']} to {p['priceFormatted']}"


def _set_status(p, change):
    status = change.get("status")
    if status == "available":
        if "price" not in change:
            raise ChangeError("a price is needed to put a listing back on the market")
        p["status"], p["price"] = "for-sale", _price(change["price"])
        p["priceFormatted"] = format_price(p["price"])
        p.pop("detailStatus", None)
        _retitle_heading(p, p["priceFormatted"])
        return f"mark {p['title']} available at {p['priceFormatted']}"
    if status == "under-contract":
        p["status"], p["detailStatus"], p["price"], p["priceFormatted"] = "for-sale", "under-contract", 0, "Under Contract"
        _retitle_heading(p, "Under Contract")
        return f"mark {p['title']} under contract"
    if status == "sold":
        p["status"], p["price"], p["priceFormatted"] = "sold", 0, "SOLD"
        for k in ("detailStatus", "new", "featured"):
            p.pop(k, None)
        _retitle_heading(p, "SOLD")
        return f"mark {p['title']} sold"
    raise ChangeError("status must be available, under-contract or sold")


# ---------- files other than listings.json ----------

FEATURED_RE = re.compile(r"const featuredIds = \[([^\]]*)\];")


def _featured_ids(index_html):
    matches = FEATURED_RE.findall(index_html)
    if len(matches) != 1:
        raise ChangeError("could not find the homepage featuredIds list in index.html")
    return re.findall(r"'([^']+)'", matches[0])


def _feature_on_homepage(index_html, pid):
    ids = ([pid] + [i for i in _featured_ids(index_html) if i != pid])[:3]
    return FEATURED_RE.sub("const featuredIds = [" + ", ".join(f"'{i}'" for i in ids) + "];", index_html)


def _refuse_hide_if_linked(root, pid, index_html):
    if pid in _featured_ids(index_html):
        raise ChangeError("this listing is on the homepage; ask Nathanael to swap it out before hiding it")
    pages = ["index.html"] + sorted(glob.glob("*/index.html", root_dir=root)) \
        + sorted(glob.glob("blog/*/index.html", root_dir=root))
    for rel in pages:
        if f"properties/{pid}/" in _read(os.path.join(root, rel)):
            raise ChangeError(f"this listing is linked from {rel}; ask Nathanael to remove the link before hiding it")


def _url_block(pid, lastmod, priority):
    return (f"  <url>\n    <loc>{SITE}/properties/{pid}/</loc>\n    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n    <priority>{priority}</priority>\n  </url>\n")


def sync_sitemap(text, data, today, touched):
    """Add/remove property blocks to match visibility; re-date the touched one."""
    for p in data["properties"]:
        block_re = re.compile(r"  <url>\n    <loc>" + re.escape(f"{SITE}/properties/{p['id']}/")
                              + r"</loc>\n.*?  </url>\n", re.S)
        present = block_re.search(text)
        if p.get("hidden"):
            text = block_re.sub("", text)
        elif not present or p["id"] == touched:
            block = _url_block(p["id"], today, 0.5 if p.get("status") == "sold" else 0.8)
            if present:
                text = block_re.sub(lambda m: block, text, count=1)
            else:
                if "</urlset>" not in text:
                    raise ChangeError("sitemap.xml has no closing </urlset>")
                text = text.replace("</urlset>", block + "</urlset>", 1)
    return text


# ---------- entry point ----------

def apply_change(root, change, today=None, image_exists=default_image_exists,
                 fetch_upload_date=default_fetch_upload_date):
    today = today or datetime.date.today().isoformat()
    if not isinstance(change, dict):
        raise ChangeError("change must be a JSON object")
    path = lambda rel: os.path.join(root, rel)  # noqa: E731
    data = json.loads(_read(path("data/listings.json")))
    index_html = new_index = _read(path("index.html"))
    action = change.get("action")

    if action == "add":
        if change.get("kind", "sale") != "sale":
            raise ChangeError("only for-sale listings can be added from the admin page")
        p = _build_listing(data, change.get("listing"), image_exists, fetch_upload_date)
        if change["listing"].get("onHomepage"):
            new_index = _feature_on_homepage(index_html, p["id"])
        data["properties"].append(p)
        what = f"add {p['title']}"
    elif action in ("set-price", "set-status", "set-hidden"):
        p = _find(data, change.get("id"))
        if action == "set-price":
            what = _set_price(p, change)
        elif action == "set-status":
            what = _set_status(p, change)
        else:
            if not isinstance(change.get("hidden"), bool):
                raise ChangeError("hidden must be true or false")
            if change["hidden"]:
                _refuse_hide_if_linked(root, p["id"], index_html)
                p["hidden"] = True
                what = f"hide {p['title']}"
            else:
                p.pop("hidden", None)
                what = f"unhide {p['title']}"
    else:
        raise ChangeError(f"unknown action '{action}'")

    sitemap = sync_sitemap(_read(path("sitemap.xml")), data, today, p["id"])

    # Everything validated; write.
    with open(path("data/listings.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    with open(path("sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)
    if new_index != index_html:
        with open(path("index.html"), "w", encoding="utf-8") as f:
            f.write(new_index)
    # Always regenerate: the generated <head> bakes price, cover image and video.
    regenerate_pages(root)
    for q in data["properties"]:      # the generator never deletes pages of hidden listings
        if q.get("hidden"):
            shutil.rmtree(path(os.path.join("properties", q["id"])), ignore_errors=True)

    url = f"{SITE}/properties/{p['id']}/"
    return {"commit_message": f"Admin: {what}", "id": p["id"], "title": p["title"], "url": url,
            "hidden": bool(p.get("hidden"))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--payload", help="JSON file with the change (default: $ADMIN_CHANGE)")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("--skip-image-check", action="store_true",
                    help="local testing only: don't require the photos to exist on R2")
    args = ap.parse_args()
    try:
        raw = _read(args.payload) if args.payload else os.environ.get("ADMIN_CHANGE", "")
        try:
            change = json.loads(raw)
        except ValueError:
            raise ChangeError("the change is not valid JSON")
        kwargs = {"image_exists": lambda url: True} if args.skip_image_check else {}
        result = apply_change(args.root, change, **kwargs)
    except ChangeError as e:
        print(f"::error::{e}")
        sys.exit(1)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            for k in ("commit_message", "url", "title"):
                f.write(f"{k}={result[k]}\n")
            f.write(f"hidden={'true' if result['hidden'] else 'false'}\n")


if __name__ == "__main__":
    main()
