# Handoff: sabanrealty.com (session 1 Oct – 6 Nov 2026)

Updated: 2026-11-06. Covers 4–6 Nov too: the Statia Day blog post, and fixes and reordering of the Instagram queue.

## What this is
sabanrealty.com is a static real-estate site for RE/MAX Saba / Statia (Saban Realty): plain HTML, CSS and JS, hosted on GitHub Pages from `main` of `nathanaelhub/sabanrealty`. Every push to `main` deploys in 1–2 minutes. Listing data is in `data/listings.json`, and photos are on Cloudflare R2.

This session covered SEO and site upkeep, plus marketing assets kept outside the repo:
- keyword map from Search Console, and new titles for Buy, Rent and the guides
- Dutch page `/wonen-op-saba/`, redirects from the old site, and the renting guide
- mobile nav fixes, favicon, much lighter pages (shrunk R2 photos and `thumbs/` copies)
- photo and wording changes (always "Caribbean Netherlands"), homepage stats, Sell page layout
- Google Business Profile photos and description, banners, a Facebook video thumbnail, tidying the R_E_V folder
- House on the Path lot size, the Google Business Profile link, and fixes to the test tool
- 4–6 Nov: published the Statia Day post, split the handoff into `handoff/`, and fixed facts and order in the Instagram queue

## Finished (all live on main)
- SEO retitles: Buy, Rent, "How to Buy Property on Saba", "Is Saba Expensive?". Homepage heading "Saba Island Real Estate". Findings are in `docs/keyword-map.md`.
- `/wonen-op-saba/` (Dutch), linked from footers. Redirect stubs `about-saba.html`, `listings.html`, `buy-detail.html`, `rental-detail.html`.
- Blog: renting guide (October 2026). The September post is the Statia buying guide, from another session.
- Mobile nav close button and the More menu toggle (`js/main.min.js`). Favicon set (`favicon.png`, `favicon.ico`, `apple-touch-icon.png`).
- Page weight: 206 R2 listing photos shrunk to 1600px q78. Originals are backed up in `~/Documents/sabanrealty-photo-originals-2026-10-03/` and in R2 under `originals/`. Card thumbnails are in R2 under `thumbs/` (900px), with a fallback to the full photo. Use `scripts/prepare-photos.py` for new photos.
- Homepage stats (2,270 residents; runway 1,312 ft vs St Barths 2,100 ft). Sell page shows the whole airport photo with the steps below it. Troy Hill photo replaced.
- House on the Path: `acreage: 0.66`, plus a "Lot: 2,680 m²" line in the description (e136cd1).
- Google Business Profile: `https://www.google.com/search?kgmid=/g/11zy17s84f` is in every JSON-LD `sameAs`, and there's a "Review us on Google" line on `/contact/`.
- Site tests: `scripts/site-test/browser-test.mjs` uses Chrome, else Brave, Edge or Chromium (`CHROME_BIN` overrides). It runs one browser per run with a tab per page. Google Chrome is not installed on the old Mac; Brave passes everything.
- **Statia Day blog post (4 Nov):** live at `/blog/statia-day-first-salute/` (sabanrealty PR #22, issue #21). Checked against Royal House, statiagovernment.com, 721news and USNI Proceedings. Corrected the meaning of the 11-gun reply and the 1781 aftermath, added the real nightly programme, and removed claims with no source. It missed the planned 2 Nov because nothing was set to publish it.
- **Handoff split (4 Nov):** the old root `HANDOFF.md` is now `handoff/`, one file per session. `handoff/` is excluded from the published site in `_config.yml`. These commits are only on the old Mac's local `main` and were never pushed.
- **Instagram queue (ig-auto PRs #62 and #63, 4 Nov):** Statia is "eight square miles" (11 and 16 Nov); 14 Nov is Culture Night in the caption and a new `statia-culture-night-v2.jpg`; "Caribbean Netherlands" replaces "Dutch Caribbean" in queued captions, all 27 queued hashtag sets and 3 images (`the-quiet-island-v2.jpg`, `anslyn-estate-reel-cover-v2.jpg`, `saba-unspoiled-lifestyle-v2.jpg`). `make_thumbnail.py`'s default running head now says CARIBBEAN NETHERLANDS. The campaign caption files in R_E_V were updated the same way.
- **Reel order (4 Nov):** the queue runs 3 picture posts then a reel, which is the user's standing rule. Reels: Villa Frangipani 9 Nov (moved from 5 Nov), The Pool 13 Nov, Anslyn 18 Nov, Iguana Rock 25 Nov, View Villa 4 Dec. Statia posts tied to dates kept their dates (10, 14, 15, 16 Nov). As of 6 Nov, posting is on schedule: Treasured Horseshoe reel (4 Nov) and By the Numbers: 1 Road (5 Nov) went out.
- Marketing files in `~/Desktop/Desktop/R_E_V/`: Business Profile photos and covers (`Google Business Profile/`), banners (`Social Posts/Banners/`, editable HTML in `_source/`; Facebook and YouTube both read "RE/MAX Saba / Statia"), and a Facebook thumbnail in `Videos/`.

## In progress / unfinished
- **Instagram, waiting on the user** (focus is Instagram only; the user said Facebook is fine, so leave it):
  - **14 Dec reel slot is empty.** It is meant for the Troy Villa aerial reel, held at 31 Dec because its end card says "private viewing". Plan, pending the user's OK: rebuild Troy Villa, or else schedule the finished Villa Frangipani short reel "The Kitchen". If neither happens, the last two pictures (16 and 18 Dec) run with no reel after 4 Dec.
  - **"The Pool" reel (13 Nov) ends on a photo with no contact card**, which breaks the dad's rule. Plan, pending OK: add the card.
  - `#CaribbeanNetherlands` may reach fewer people than `#DutchCaribbean`; the user can ask to switch back.
- **Unpushed local commits:** the old Mac's `main` was 8 commits ahead (the handoff split) and 3 behind. The repo is public, so don't push `handoff/` without the user's OK; a private copy is safer. That checkout also has another session's uncommitted `.gitignore` edit and `videos/` folder.
- Campaign PDFs in `R_E_V/Statia Day 2026 Campaign/` still show the old text and dates; `ig-auto/schedule.json` is the live order.
- **Google review link**: the Contact link opens the profile. The direct "Ask for reviews" link from the Business Profile hasn't been provided yet; when it is, replace the kgmid URL in `contact/index.html`. Add rating schema once reviews exist.
- Not yet checked: the Dutch page text by a native speaker; banners on the live Facebook and YouTube pages; two dead image URLs on the hidden `statia-poolhouse` listing.

## Exact next steps
1. Ask the user to answer the two Instagram questions above (14 Dec slot, The Pool contact card), then do them. Keep 3 pictures then a reel, and check the order with a script before merging any schedule change.
2. When the user sends the "Ask for reviews" link, swap it into `contact/index.html`.
3. Mid-November: compare a fresh Search Console export with the October data in `docs/keyword-map.md` (exports are in `R_E_V/SEO/Search Console/`).
4. December blog post: suggested "Living on Saba" guide. Use the `add-blog-post` skill; keep the date the same in all four places.
5. Before any queued image ships: read the text in the image itself, not just the caption. On macOS, Vision OCR via a small Swift script works.

## Commands
```bash
python3 -m http.server 8000                       # local preview at http://localhost:8000
bash scripts/site-test/run.sh                     # static + browser tests (needs Chrome/Brave/Edge/Chromium)
bash scripts/site-test/run.sh static              # static only
bash scripts/site-test/run.sh prod                # after pushing, from a main checkout
python3 scripts/generate-listing-pages.py         # after adding/removing a listing (then update sitemap.xml)
python3 scripts/prepare-photos.py <src> <out>     # shrink photos + thumbs before upload
node scripts/r2-manage.js upload <dir> <prefix>   # R2 upload (reads .env); needs `npm install` for aws-sdk
gh api repos/nathanaelhub/sabanrealty/pages/builds/latest --jq '.status+" "+.commit[0:7]'   # deploy status
```
CSS: edit `css/styles.css`, then regenerate `css/styles.min.css` (Python one-liner in `.claude/skills/site-conventions/SKILL.md`). `js/main.min.js` is the only JS file. Other sessions may leave this checkout on a feature branch, so run `git branch --show-current` before committing.

## Outside the repo
- `.env` (gitignored, not copied by git): `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_R2_ACCESS_KEY_ID`, `CLOUDFLARE_R2_SECRET_ACCESS_KEY`, `CLOUDFLARE_R2_BUCKET`. Move it to the new computer by hand.
- `.claude/` (gitignored): project skills (`add-listing`, `add-blog-post`, `site-test`, `site-conventions`) and agents. Copy it by hand.
- Admin Worker `sabanrealty-admin` (`scripts/admin-worker`, deployed with wrangler; R2 bucket binding `sabanreality`). Secrets and vars: `ADMIN_PASSPHRASE`, `GITHUB_TOKEN`, `ALLOWED_ORIGINS`, `REPO`, `WORKFLOW`, `PUBLIC_BASE`, `DRY_RUN`. The GitHub workflow `.github/workflows/admin-publish.yml` uses the built-in token.
- Cloudflare R2 bucket (public at `pub-78b56158b83942189fa28a4d5939bb79.r2.dev`, rate-limited; use the S3 API for bulk work). DNS is on Google Cloud DNS.
- Sister repo `~/GitHub/ig-auto`: Instagram scheduler. It needs the `IG_ACCESS_TOKEN` and `IG_USER_ID` GitHub secrets. **As of 16 Oct the token is a permanent Meta system-user token that never expires** — the old 60-day `ig-token-refresh` routine is now only a fallback if it is ever revoked. See part 2 below for details.
- `~/Desktop/Desktop/R_E_V/`: all marketing assets (Listings, Social Posts, Videos, SEO, Statia Day 2026 Campaign, Google Business Profile).
- `~/Documents/sabanrealty-photo-originals-2026-10-03/`: original listing photos (backup).
- Claude memory: `~/.claude/projects/-Users-nathanaeljohnson-GitHub-sabanrealty/memory/` holds project notes. Copy it to keep context.
- ig-auto is in `~/GitHub/ig-auto`. Its Python image tools run with `.venv/bin/python` (has Pillow and numpy). Change the queue on a branch with a pull request; the daily publish job commits to `main`, so re-read `schedule.json` on a fresh base before editing.
- Tools used: `gh` (logged in), Python 3 with Pillow, Node 24, ffmpeg, and Brave or Chrome for tests and image renders.
