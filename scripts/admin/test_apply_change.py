#!/usr/bin/env python3
"""
Tests for apply_change.py. Stdlib only:
    python3 -m unittest scripts/admin/test_apply_change.py

Each test builds a throwaway copy of the bits of the repo apply_change touches
(listings.json, sitemap.xml, index.html, the real generator + engine template)
and runs the real code against it. Only the two network lookups are injected.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import apply_change as ac  # noqa: E402

BASE = "https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev"
TODAY = "2026-10-01"

LISTINGS = {
    "properties": [
        {
            "id": "alpha-villa", "new": True, "title": "Alpha Villa", "location": "Windwardside, Saba",
            "price": 500000, "priceFormatted": "$500,000", "status": "for-sale", "type": "villa",
            "bedrooms": 3, "bathrooms": 2,
            "description": "<h2>Alpha Villa - $500,000</h2>\n<p>Nice.</p>",
            "images": [f"{BASE}/listings/alpha-villa/a.jpg"],
        },
        {
            "id": "beta-land", "hidden": True, "title": "Beta Land", "location": "The Bottom, Saba",
            "price": 100000, "priceFormatted": "$100,000", "status": "for-sale", "type": "land",
            "bedrooms": 0, "bathrooms": 0, "description": "<h2>Beta Land — The Bottom, Saba</h2>",
            "images": [f"{BASE}/listings/beta-land/b.jpg"],
        },
        {
            "id": "gamma-cottage", "title": "Gamma Cottage", "location": "Zion's Hill, Saba",
            "price": 300000, "priceFormatted": "$300,000", "status": "for-sale", "type": "cottage",
            "bedrooms": 2, "bathrooms": 1, "description": "<h2>Gamma Cottage — Zion's Hill, Saba</h2>",
            "images": [f"{BASE}/listings/gamma-cottage/g.jpg"],
        },
        {
            "id": "delta-land", "title": "Delta Land", "location": "Lodi, St. Eustatius",
            "price": 90000, "priceFormatted": "$90,000", "status": "for-sale", "type": "land",
            "bedrooms": 0, "bathrooms": 0, "description": "<h2>Delta Land — Lodi, St. Eustatius</h2>",
            "images": [f"{BASE}/listings/delta-land/d.jpg"],
        },
    ],
    "rentals": [
        {
            "id": "rho-rental", "title": "Rho Rental", "location": "Windwardside", "nightlyRate": 200,
            "nightlyRateFormatted": "$200/night", "status": "available", "type": "villa",
            "bedrooms": 2, "bathrooms": 1, "maxGuests": 4, "description": "Plain.", "features": [],
            "images": [f"{BASE}/rentals/rho-rental/r.jpg"],
        }
    ],
}


def url_block(path, lastmod, prio):
    return (f"  <url>\n    <loc>https://sabanrealty.com/{path}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n    <priority>{prio}</priority>\n  </url>\n")


SITEMAP = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + url_block("", "2026-06-26", "1.0")
    + "  <!-- Listings -->\n"
    + url_block("properties/alpha-villa/", "2026-06-10", "0.8")
    + url_block("properties/gamma-cottage/", "2026-06-10", "0.8")
    + url_block("properties/delta-land/", "2026-06-10", "0.8")
    + url_block("rentals/rho-rental/", "2026-06-10", "0.7")
    + "</urlset>\n"
)

INDEX_HTML = (
    "<html><body><script>\n"
    "        const featuredIds = ['gamma-cottage', 'alpha-villa', 'delta-land'];\n"
    "</script></body></html>\n"
)

NEW_DESC = ("<h2>Echo House — Windwardside, Saba</h2>\n"
            "<p><strong>Location:</strong> Windwardside, Saba</p>\n"
            "<h3>Property Overview:</h3>\n<p>Views &amp; breezes.</p>")


def add_change(**overrides):
    listing = {
        "id": "echo-house", "title": "Echo House", "village": "Windwardside", "island": "saba",
        "type": "villa", "price": 425000, "bedrooms": 2, "bathrooms": 2.5,
        "description": NEW_DESC,
        "images": [f"{BASE}/listings/echo-house/echo-house-ab12-01.jpg",
                   f"{BASE}/listings/echo-house/echo-house-ab12-02.jpg"],
        "isNew": True, "onHomepage": False,
    }
    listing.update(overrides)
    return {"request_id": "t1", "action": "add", "kind": "sale", "listing": listing}


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="admin-test-")
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, "data"))
        os.makedirs(os.path.join(self.root, "scripts"))
        os.makedirs(os.path.join(self.root, "links"))
        self.write("data/listings.json", json.dumps(LISTINGS, indent=2, ensure_ascii=False) + "\n")
        self.write("sitemap.xml", SITEMAP)
        self.write("index.html", INDEX_HTML)
        self.write("links/index.html", '<a href="properties/alpha-villa/">Alpha</a>\n')
        shutil.copy(os.path.join(REPO, "property-detail.html"), self.root)
        shutil.copy(os.path.join(REPO, "scripts", "generate-listing-pages.py"),
                    os.path.join(self.root, "scripts"))
        # Start from the same state the real repo is always in: pages already generated.
        ac.regenerate_pages(self.root)

    def write(self, rel, text):
        with open(os.path.join(self.root, rel), "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def exists(self, rel):
        return os.path.exists(os.path.join(self.root, rel))

    def prop(self, pid):
        data = json.loads(self.read("data/listings.json"))
        return next(p for p in data["properties"] if p["id"] == pid)

    def apply(self, change, image_exists=lambda url: True,
              fetch_upload_date=lambda vid: "2026-09-30T12:00:00+00:00"):
        return ac.apply_change(self.root, change, today=TODAY,
                               image_exists=image_exists, fetch_upload_date=fetch_upload_date)


class AddTests(Base):
    def test_add_appends_entry_in_site_format(self):
        self.apply(add_change())
        data = json.loads(self.read("data/listings.json"))
        entry = data["properties"][-1]
        self.assertEqual(list(entry.keys()),
                         ["id", "new", "title", "location", "price", "priceFormatted", "status",
                          "type", "bedrooms", "bathrooms", "description", "images"])
        self.assertEqual(entry["id"], "echo-house")
        self.assertEqual(entry["location"], "Windwardside, Saba")
        self.assertEqual(entry["price"], 425000)
        self.assertEqual(entry["priceFormatted"], "$425,000")
        self.assertEqual(entry["status"], "for-sale")
        self.assertEqual(entry["bathrooms"], 2.5)
        self.assertEqual(len(entry["images"]), 2)

    def test_add_statia_location_matches_island_filter_text(self):
        self.apply(add_change(village="Lodi", island="statia"))
        self.assertEqual(self.prop("echo-house")["location"], "Lodi, St. Eustatius")

    def test_add_generates_page_and_sitemap_entry(self):
        self.apply(add_change())
        self.assertTrue(self.exists("properties/echo-house/index.html"))
        self.assertNotIn('content="noindex"', self.read("properties/echo-house/index.html"))
        self.assertIn(url_block("properties/echo-house/", TODAY, "0.8"), self.read("sitemap.xml"))
        self.assertTrue(self.read("sitemap.xml").endswith("</urlset>\n"))

    def test_add_keeps_listings_json_formatting(self):
        self.apply(add_change(title="Café Écho"))
        text = self.read("data/listings.json")
        self.assertIn('"title": "Café Écho"', text)          # not \u-escaped
        self.assertEqual(text, json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n")

    def test_add_without_new_ribbon_omits_flag(self):
        self.apply(add_change(isNew=False))
        self.assertNotIn("new", self.prop("echo-house"))

    def test_add_with_acreage(self):
        self.apply(add_change(type="land", bedrooms=0, bathrooms=0, acreage=0.7))
        self.assertEqual(self.prop("echo-house")["acreage"], 0.7)

    def test_add_with_video_records_upload_date(self):
        self.apply(add_change(videoId="H2hvZM2YD9o"))
        entry = self.prop("echo-house")
        self.assertEqual(entry["videos"], [{"label": "Property Tour", "id": "H2hvZM2YD9o",
                                            "uploadDate": "2026-09-30T12:00:00+00:00"}])
        self.assertEqual(list(entry.keys())[:3], ["id", "new", "videos"])
        self.assertIn("VideoObject", self.read("properties/echo-house/index.html"))

    def test_add_on_homepage_puts_id_first_and_keeps_three(self):
        self.apply(add_change(onHomepage=True))
        self.assertIn("const featuredIds = ['echo-house', 'gamma-cottage', 'alpha-villa'];",
                      self.read("index.html"))

    def test_add_off_homepage_leaves_index_untouched(self):
        self.apply(add_change())
        self.assertEqual(self.read("index.html"), INDEX_HTML)

    def test_add_rejects_id_already_used_by_a_property(self):
        with self.assertRaisesRegex(ac.ChangeError, "already"):
            self.apply(add_change(id="alpha-villa",
                                  images=[f"{BASE}/listings/alpha-villa/alpha-villa-zz-01.jpg"]))

    def test_add_rejects_id_already_used_by_a_rental(self):
        with self.assertRaisesRegex(ac.ChangeError, "already"):
            self.apply(add_change(id="rho-rental",
                                  images=[f"{BASE}/listings/rho-rental/rho-rental-zz-01.jpg"]))

    def test_add_rejects_non_slug_id(self):
        with self.assertRaises(ac.ChangeError):
            self.apply(add_change(id="../evil"))

    def test_add_rejects_image_outside_its_own_folder(self):
        with self.assertRaisesRegex(ac.ChangeError, "image"):
            self.apply(add_change(images=[f"{BASE}/listings/alpha-villa/a.jpg"]))

    def test_add_rejects_image_on_another_host(self):
        with self.assertRaisesRegex(ac.ChangeError, "image"):
            self.apply(add_change(images=["https://evil.example/listings/echo-house/x-01.jpg"]))

    def test_add_rejects_image_that_was_not_uploaded(self):
        with self.assertRaisesRegex(ac.ChangeError, "not found"):
            self.apply(add_change(), image_exists=lambda url: False)

    def test_add_rejects_no_images(self):
        with self.assertRaises(ac.ChangeError):
            self.apply(add_change(images=[]))

    def test_add_rejects_markup_in_title(self):
        with self.assertRaises(ac.ChangeError):
            self.apply(add_change(title="Echo <img src=x onerror=alert(1)>"))

    def test_add_rejects_unknown_type(self):
        with self.assertRaises(ac.ChangeError):
            self.apply(add_change(type="castle"))

    def test_add_rejects_non_positive_price(self):
        with self.assertRaises(ac.ChangeError):
            self.apply(add_change(price=0))

    def test_add_rejects_unknown_field(self):
        with self.assertRaisesRegex(ac.ChangeError, "hidden"):
            self.apply(add_change(hidden=True))

    def test_add_rejects_bad_video_id(self):
        with self.assertRaises(ac.ChangeError):
            self.apply(add_change(videoId='x"><script>'))

    def test_add_sanitizes_description(self):
        self.apply(add_change(description=NEW_DESC + '<script>alert(1)</script><p onclick="x()">Hi</p>'))
        desc = self.prop("echo-house")["description"]
        self.assertNotIn("script", desc)
        self.assertNotIn("onclick", desc)
        self.assertIn("<p>Hi</p>", desc)

    def test_failed_add_changes_nothing_on_disk(self):
        before = self.read("data/listings.json")
        with self.assertRaises(ac.ChangeError):
            self.apply(add_change(price=-5))
        self.assertEqual(self.read("data/listings.json"), before)
        self.assertEqual(self.read("sitemap.xml"), SITEMAP)
        self.assertFalse(self.exists("properties/echo-house"))


class SanitizerTests(unittest.TestCase):
    def test_keeps_allowed_tags(self):
        html = "<h2>T</h2>\n<p><strong>A:</strong> b</p>\n<h3>K</h3>\n<ul>\n<li>one</li>\n</ul>"
        self.assertEqual(ac.sanitize_description(html), html)

    def test_drops_attributes(self):
        self.assertEqual(ac.sanitize_description('<p style="x" onclick="y">a</p>'), "<p>a</p>")

    def test_drops_script_with_its_content(self):
        self.assertEqual(ac.sanitize_description("<p>a</p><script>alert(1)</script>"), "<p>a</p>")

    def test_drops_disallowed_tag_but_keeps_text(self):
        self.assertEqual(ac.sanitize_description('<p><a href="javascript:x">link</a></p>'), "<p>link</p>")

    def test_escapes_text_once(self):
        self.assertEqual(ac.sanitize_description("<p>Pool & deck &amp; 2 &lt; 3</p>"),
                         "<p>Pool &amp; deck &amp; 2 &lt; 3</p>")

    def test_closes_unclosed_tags(self):
        self.assertEqual(ac.sanitize_description("<ul><li>one"), "<ul><li>one</li></ul>")


class PriceAndStatusTests(Base):
    def test_set_price_updates_price_and_old_style_heading(self):
        self.apply({"action": "set-price", "id": "alpha-villa", "price": 475000})
        p = self.prop("alpha-villa")
        self.assertEqual((p["price"], p["priceFormatted"]), (475000, "$475,000"))
        self.assertTrue(p["description"].startswith("<h2>Alpha Villa - $475,000</h2>"))

    def test_set_price_leaves_new_style_heading_alone(self):
        self.apply({"action": "set-price", "id": "gamma-cottage", "price": 310000})
        self.assertTrue(self.prop("gamma-cottage")["description"]
                        .startswith("<h2>Gamma Cottage — Zion's Hill, Saba</h2>"))

    def test_set_price_refreshes_baked_page_and_sitemap_date(self):
        self.apply({"action": "set-price", "id": "alpha-villa", "price": 475000})
        self.assertIn("$475,000", self.read("properties/alpha-villa/index.html"))
        self.assertIn(url_block("properties/alpha-villa/", TODAY, "0.8"), self.read("sitemap.xml"))

    def test_set_price_rejected_while_sold(self):
        self.apply({"action": "set-status", "id": "alpha-villa", "status": "sold"})
        with self.assertRaises(ac.ChangeError):
            self.apply({"action": "set-price", "id": "alpha-villa", "price": 1})

    def test_under_contract_uses_site_convention(self):
        self.apply({"action": "set-status", "id": "alpha-villa", "status": "under-contract"})
        p = self.prop("alpha-villa")
        self.assertEqual((p["status"], p["detailStatus"], p["price"], p["priceFormatted"]),
                         ("for-sale", "under-contract", 0, "Under Contract"))
        self.assertTrue(p["description"].startswith("<h2>Alpha Villa - Under Contract</h2>"))

    def test_sold_uses_site_convention_and_drops_ribbons(self):
        self.apply({"action": "set-status", "id": "alpha-villa", "status": "under-contract"})
        self.apply({"action": "set-status", "id": "alpha-villa", "status": "sold"})
        p = self.prop("alpha-villa")
        self.assertEqual((p["status"], p["price"], p["priceFormatted"]), ("sold", 0, "SOLD"))
        self.assertNotIn("detailStatus", p)
        self.assertNotIn("new", p)
        self.assertTrue(p["description"].startswith("<h2>Alpha Villa - SOLD</h2>"))
        self.assertIn(url_block("properties/alpha-villa/", TODAY, "0.5"), self.read("sitemap.xml"))

    def test_back_to_available_restores_price(self):
        self.apply({"action": "set-status", "id": "alpha-villa", "status": "sold"})
        self.apply({"action": "set-status", "id": "alpha-villa", "status": "available", "price": 450000})
        p = self.prop("alpha-villa")
        self.assertEqual((p["status"], p["price"], p["priceFormatted"]), ("for-sale", 450000, "$450,000"))
        self.assertNotIn("detailStatus", p)
        self.assertTrue(p["description"].startswith("<h2>Alpha Villa - $450,000</h2>"))
        self.assertIn(url_block("properties/alpha-villa/", TODAY, "0.8"), self.read("sitemap.xml"))

    def test_back_to_available_requires_price(self):
        with self.assertRaisesRegex(ac.ChangeError, "price"):
            self.apply({"action": "set-status", "id": "alpha-villa", "status": "available"})

    def test_unknown_listing_rejected(self):
        with self.assertRaisesRegex(ac.ChangeError, "nope"):
            self.apply({"action": "set-price", "id": "nope", "price": 1})

    def test_rental_ids_are_not_editable(self):
        with self.assertRaises(ac.ChangeError):
            self.apply({"action": "set-price", "id": "rho-rental", "price": 1})

    def test_unknown_action_rejected(self):
        with self.assertRaises(ac.ChangeError):
            self.apply({"action": "delete", "id": "alpha-villa"})

    def test_other_listings_are_untouched(self):
        before = self.prop("gamma-cottage")
        self.apply({"action": "set-status", "id": "alpha-villa", "status": "sold"})
        self.assertEqual(self.prop("gamma-cottage"), before)
        self.assertIn(url_block("properties/gamma-cottage/", "2026-06-10", "0.8"), self.read("sitemap.xml"))


class HiddenTests(Base):
    def test_hide_removes_page_and_sitemap_entry(self):
        self.write("index.html", INDEX_HTML.replace("'delta-land'", "'zeta'"))
        self.apply({"action": "set-hidden", "id": "delta-land", "hidden": True})
        self.assertIs(self.prop("delta-land")["hidden"], True)
        self.assertFalse(self.exists("properties/delta-land"))
        self.assertNotIn("properties/delta-land/", self.read("sitemap.xml"))

    def test_hide_refused_when_on_homepage(self):
        with self.assertRaisesRegex(ac.ChangeError, "homepage"):
            self.apply({"action": "set-hidden", "id": "gamma-cottage", "hidden": True})

    def test_hide_refused_when_linked_from_another_page(self):
        self.write("index.html", INDEX_HTML.replace("'alpha-villa'", "'zeta'"))
        with self.assertRaisesRegex(ac.ChangeError, "links/index.html"):
            self.apply({"action": "set-hidden", "id": "alpha-villa", "hidden": True})

    def test_unhide_restores_page_and_sitemap_entry(self):
        self.apply({"action": "set-hidden", "id": "beta-land", "hidden": False})
        self.assertNotIn("hidden", self.prop("beta-land"))
        self.assertTrue(self.exists("properties/beta-land/index.html"))
        self.assertIn(url_block("properties/beta-land/", TODAY, "0.8"), self.read("sitemap.xml"))


class SummaryTests(Base):
    def test_add_summary_names_listing_and_url(self):
        out = self.apply(add_change())
        self.assertEqual(out["commit_message"], "Admin: add Echo House")
        self.assertEqual(out["url"], "https://sabanrealty.com/properties/echo-house/")

    def test_status_summary(self):
        out = self.apply({"action": "set-status", "id": "alpha-villa", "status": "sold"})
        self.assertEqual(out["commit_message"], "Admin: mark Alpha Villa sold")


if __name__ == "__main__":
    unittest.main()
