#!/usr/bin/env python3
"""
Generate clean-URL pages for every (visible) listing.

For each property it writes  properties/<id>/index.html   (for-sale listings)
and for each rental           rentals/<id>/index.html       (vacation rentals)

Each generated page is a copy of property-detail.html with:
  - <base href="/"> so all the template's root-relative paths still resolve
  - real baked <head> SEO (title, description, canonical, OG/Twitter, JSON-LD)
    so crawlers and social scrapers get correct data without running JS
  - window.__LISTING__ injected so the existing renderer knows which listing
    to load (content is still fetched live from data/listings.json at runtime,
    so price/status changes never go stale — only ADD/REMOVE needs a re-run)

Re-run this after adding or removing a listing:
    python3 scripts/generate-listing-pages.py
Then update sitemap.xml (this script prints the <url> block for you).
"""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = open(os.path.join(ROOT, "property-detail.html")).read()
DATA = json.load(open(os.path.join(ROOT, "data", "listings.json")))
SITE = "https://sabanrealty.com"


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def sub_attr(s, pattern, value):
    """Replace the content/href value inside a tag, escaping the value."""
    return re.sub(pattern, lambda m: m.group(1) + html.escape(value, quote=True) + m.group(2), s, count=1)


def build_page(p, kind):
    """kind = 'sale' | 'rental'"""
    is_rental = kind == "rental"
    clean = f"{'rentals' if is_rental else 'properties'}/{p['id']}/"
    url = f"{SITE}/{clean}"
    title = f"{p['title']} | Saban Realty"
    price = p.get("nightlyRateFormatted") if is_rental else p.get("priceFormatted")
    desc = f"{p['title']} - {p.get('location','Saba')}. {price}. View details, photos, and inquire about this {p.get('type','property')} on Saba Island."
    img = (p.get("images") or [f"{SITE}/images/website-photos/saba-island-drone.jpg"])[0]

    h = TEMPLATE

    # 0. The bare engine template carries a noindex (it shouldn't be indexed itself) —
    #    generated listing pages MUST be indexable, so strip it here.
    noindex = ('  <!-- Bare engine template: not for indexing. '
               'generate-listing-pages.py strips this on generated pages. -->\n'
               '  <meta name="robots" content="noindex">\n')
    assert noindex in h, "noindex block not found in template — check property-detail.html head"
    h = h.replace(noindex, "", 1)

    # 1. <base> + window.__LISTING__ right after the viewport meta
    inject = (
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '  <base href="/">\n'
        f'  <script>window.__LISTING__ = {{"id":"{p["id"]}","type":"{kind}"}};</script>'
    )
    h = h.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">', inject, 1)

    # 2. baked head SEO
    h = re.sub(r"<title>.*?</title>", lambda m: f"<title>{html.escape(title)}</title>", h, count=1)
    h = sub_attr(h, r'(<meta name="description" content=")[^"]*(">)', desc)
    h = sub_attr(h, r'(<meta property="og:title" content=")[^"]*(">)', title)
    h = sub_attr(h, r'(<meta property="og:description" content=")[^"]*(">)', desc)
    h = sub_attr(h, r'(<meta property="og:image" content=")[^"]*(">)', img)
    h = sub_attr(h, r'(<meta property="og:url" content=")[^"]*(">)', url)
    h = sub_attr(h, r'(<meta property="og:type" content=")[^"]*(">)', "article")
    h = sub_attr(h, r'(<meta name="twitter:title" content=")[^"]*(">)', title)
    h = sub_attr(h, r'(<meta name="twitter:description" content=")[^"]*(">)', desc)
    h = sub_attr(h, r'(<meta name="twitter:image" content=")[^"]*(">)', img)
    h = sub_attr(h, r'(<link rel="canonical" href=")[^"]*(">)', url)

    # 3. baked RealEstateListing / LodgingBusiness JSON-LD (no-JS fallback)
    ld = {
        "@context": "https://schema.org",
        "@type": "LodgingBusiness" if is_rental else "RealEstateListing",
        "name": p["title"],
        "description": strip_html(p.get("description")),
        "url": url,
        "image": p.get("images", [])[:10],
        "address": {"@type": "PostalAddress", "addressLocality": p.get("location", "Saba"),
                    "addressRegion": "Saba", "addressCountry": "BQ"},
    }
    if not is_rental and p.get("price", 0) > 0:
        avail = ("https://schema.org/SoldOut" if p.get("status") == "sold"
                 else "https://schema.org/LimitedAvailability" if p.get("detailStatus") == "under-contract"
                 else "https://schema.org/InStock")
        ld["offers"] = {"@type": "Offer", "price": p["price"], "priceCurrency": "USD",
                        "url": url, "availability": avail}
    if p.get("bedrooms", 0) > 0:
        ld["numberOfRooms"] = p["bedrooms"]
    blocks = '  <script type="application/ld+json">\n  ' + json.dumps(ld, ensure_ascii=False) + "\n  </script>\n"

    # VideoObject schema for property tours (eligible for video rich results).
    # uploadDate comes from each video's real YouTube publish date (in listings.json).
    for v in (p.get("videos") or []):
        vid = v.get("id")
        if not vid:
            continue
        vo = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": f"{p['title']} — {v.get('label', 'Property Tour')}",
            "description": f"Video tour of {p['title']} in {p.get('location', 'Saba')}, Caribbean Netherlands, from Saban Realty.",
            "thumbnailUrl": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "embedUrl": f"https://www.youtube.com/embed/{vid}",
            "contentUrl": f"https://www.youtube.com/watch?v={vid}",
        }
        if v.get("uploadDate"):
            vo["uploadDate"] = v["uploadDate"]
        blocks += '  <script type="application/ld+json">\n  ' + json.dumps(vo, ensure_ascii=False) + "\n  </script>\n"

    h = h.replace("</head>", blocks + "</head>", 1)

    # 4. skip-link must not be hijacked by <base>
    h = h.replace('<a href="#main-content" class="skip-to-content">',
                  f'<a href="/{clean}#main-content" class="skip-to-content">', 1)

    out_dir = os.path.join(ROOT, *clean.rstrip("/").split("/"))
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "index.html"), "w").write(h)
    return clean


def main():
    pages = []
    for p in DATA["properties"]:
        if p.get("hidden"):
            continue
        pages.append((build_page(p, "sale"), 0.8 if p.get("status") != "sold" else 0.5))
    for p in DATA["rentals"]:
        if p.get("hidden"):
            continue
        pages.append((build_page(p, "rental"), 0.7))

    print(f"Generated {len(pages)} listing pages.\n")
    print("Sitemap <url> entries (replace the old property-detail.html?id= block):\n")
    for clean, prio in pages:
        print(f"  <url>\n    <loc>{SITE}/{clean}</loc>\n    <lastmod>2026-06-10</lastmod>\n"
              f"    <changefreq>monthly</changefreq>\n    <priority>{prio}</priority>\n  </url>")


if __name__ == "__main__":
    main()
