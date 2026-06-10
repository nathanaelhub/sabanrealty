# Saban Realty — Off-Page SEO Checklist

The website's on-page SEO is now strong (meta, structured data, FAQ, sitemap, fast images, clean signals). The remaining gains come from **off-page** work — things done outside the codebase, in your own accounts. These are the highest-leverage moves for outranking competitors, but they require *you* (account access, business verification, outreach). Work top to bottom.

---

## 1. Google Search Console (do this first — it's free and foundational)
Without this you have no visibility into how Google sees the site.

1. Go to **search.google.com/search-console** and add the property `sabanrealty.com`.
2. Verify ownership. Easiest options:
   - **DNS verification** (recommended): add the TXT record Google gives you at your domain registrar. This verifies the whole domain (apex + www).
   - Or **HTML tag**: Google gives you a `<meta name="google-site-verification" ...>` tag — paste it into the `<head>` of `index.html` and tell me; I'll add it.
3. Once verified: **Sitemaps → submit** `https://sabanrealty.com/sitemap.xml`.
4. Use **URL Inspection** to request indexing of the homepage, the buy page, and the new blog guide.
5. Check **Pages** (index coverage) weekly for errors, and **Performance** to see which queries you're ranking for.

## 2. Bing Webmaster Tools (5 minutes, feeds Bing + ChatGPT search)
1. Go to **bing.com/webmasters**, sign in, "Import from Google Search Console" (one click once GSC is set up).
2. Submit the same sitemap.

## 3. Google Business Profile (HUGE for a local real-estate agent)
This is what puts you in the Google Maps "local pack" and builds your Knowledge Panel — often more valuable than organic rankings for local intent.

1. Create/claim the profile at **business.google.com**.
2. **Category:** "Real Estate Agency" (primary) + "Real Estate Agents" if available.
3. Fill in **NAP exactly as on the site** (consistency matters — Google cross-checks):
   - Name: **Saban Realty**
   - Phone: **+599 416 5497**
   - Email: **jeffsabarealty@gmail.com**
   - Area / address: **Zion's Hill, Saba, Caribbean Netherlands**
   - Website: **https://sabanrealty.com**
4. Add **service areas** (Saba and St. Eustatius), hours (Mon–Fri 9–5, Sat 10–2 — matches the site), and a description.
5. Upload **photos** — the scenic island shots and a few listings. Profiles with photos get far more engagement.
6. **Ask past clients for reviews.** Reviews are a major local-ranking factor. Even 5–10 genuine reviews would stand out in this niche.
7. Post occasional updates (new listings, the blog guide) via GBP posts.

> Once you have GBP reviews, tell me — I can add `Review`/`AggregateRating` schema to the site so star ratings can appear in search results too.

## 4. Backlinks & citations (the real competitive moat)
In a niche this small, even a handful of quality links makes you dominant. Target, in rough priority:

- **RE/MAX network listings/directory.** As a RE/MAX affiliate, make sure your agent profile on RE/MAX corporate sites links to `sabanrealty.com`. This is an authoritative, on-topic link — get it first.
- **Saba & Statia tourism / government sites** (e.g., the official Saba tourism board, island directories). Ask to be listed as a local real-estate resource.
- **Expat & relocation communities** — forums, "moving to the Caribbean Netherlands" guides, expat blogs. Offer your new buying guide as a resource.
- **Dive & eco-travel sites** — Saba is a world dive destination; dive operators and travel blogs are natural link partners for vacation-rental content.
- **Caribbean real-estate aggregators / portals** — list properties where it makes sense and link back.
- **Local business citations** — any Caribbean or Dutch business directory (consistent NAP each time).
- **Digital PR** — a short "state of the Saba property market" note pitched to Caribbean news outlets can earn editorial links.

**Rule of thumb:** a few relevant, trusted links beat dozens of low-quality ones. Never buy spammy links.

## 5. Social & brand signals
- Keep **Facebook, Instagram, YouTube** active and linked to the site (already in your `sameAs` structured data).
- The **YouTube channel** is an asset: each property tour video can be embedded on its listing and titled with target keywords ("Saba villa for sale — [name] tour"). Tell me when you want video embeds + `VideoObject` schema added.
- Consistent NAP everywhere you appear online.

---

## Quick measurement targets (check monthly in Search Console)
- Impressions & clicks trending up for "Saba real estate", "property for sale Saba", "buy property Caribbean Netherlands".
- The blog guide ranking for "can foreigners buy property in Saba" and similar.
- Zero index-coverage errors; sitemap fully indexed.
- Core Web Vitals "Good" on mobile (the recent image work should help here).

## Things I can do in-code once you act
- Add the GSC `google-site-verification` meta tag (if you choose HTML verification).
- Add `Review`/`AggregateRating` schema once you have reviews.
- Add `VideoObject` schema + on-page video embeds from your YouTube tours.
- Write more cornerstone guides (cost of living, residency, investment, Saba vs Statia).
