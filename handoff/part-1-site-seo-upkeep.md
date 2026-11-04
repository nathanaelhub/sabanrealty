# Handoff: sabanrealty.com (session 1–26 Oct 2026)

## What this is
sabanrealty.com is a static real-estate site for RE/MAX Saba / Statia (Saban Realty): plain HTML, CSS and JS, hosted on GitHub Pages from `main` of `nathanaelhub/sabanrealty`. Every push to `main` deploys in 1–2 minutes. Listing data is in `data/listings.json`, and photos are on Cloudflare R2.

This session covered SEO and site upkeep, plus marketing assets kept outside the repo:
- keyword map from Search Console, and new titles for Buy, Rent and the guides
- Dutch page `/wonen-op-saba/`, redirects from the old site, and the renting guide
- mobile nav fixes, favicon, much lighter pages (shrunk R2 photos and `thumbs/` copies)
- photo and wording changes (always "Caribbean Netherlands"), homepage stats, Sell page layout
- Google Business Profile photos and description, banners, a Facebook video thumbnail, tidying the R_E_V folder
- House on the Path lot size, the Google Business Profile link, and fixes to the test tool

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
- Marketing files in `~/Desktop/Desktop/R_E_V/`: Business Profile photos and covers (`Google Business Profile/`), banners (`Social Posts/Banners/`, editable HTML in `_source/`; Facebook and YouTube both read "RE/MAX Saba / Statia"), and a Facebook thumbnail in `Videos/`.

## In progress / unfinished
- **Statia Day blog post**: drafted on remote branch `blog/statia-day-november` (commit 23cf0cd), not on main. It's planned to go live about 2 Nov, before Statia Day week (10–16 Nov). Before merging, recheck the Villa Frangipani ($1,399,000) and Union Estate ($650,000) prices and the event programme. The history facts (Rodney 1781, FDR plaque 1939) came from Claude's own knowledge and haven't been checked against a source.
- **Statia Day Instagram campaign** (built in another session, in the `ig-auto` repo): fully scheduled through 24 Nov. As of 26 Oct, 61 posts have gone out and 35 remain queued; the automation is self-running and the Statia block builds to Statia Day (16 Nov). See `part-2-video-instagram-campaign.md` for the Instagram automation (ig-auto).
- **Google review link**: the Contact link opens the profile. The direct "Ask for reviews" link from the Business Profile hasn't been provided yet; when it is, replace the kgmid URL in `contact/index.html`. Add rating schema once reviews exist.
- Not yet checked: the Dutch page text by a native speaker; banners on the live Facebook and YouTube pages; two dead image URLs on the hidden `statia-poolhouse` listing.

## Exact next steps
1. About 2 Nov: `git fetch && git checkout blog/statia-day-november && git rebase origin/main`, then check prices and the programme, run `bash scripts/site-test/run.sh`, fast-forward main and push. Verify with `bash scripts/site-test/run.sh prod`.
2. When the user sends the "Ask for reviews" link, swap it into `contact/index.html`.
3. Mid-November: compare a fresh Search Console export with the October data in `docs/keyword-map.md` (exports are in `R_E_V/SEO/Search Console/`).
4. December blog post: suggested "Living on Saba" guide. Use the `add-blog-post` skill; keep the date the same in all four places.

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
- Tools used: `gh` (logged in), Python 3 with Pillow, Node 24, ffmpeg, and Brave or Chrome for tests and image renders.
