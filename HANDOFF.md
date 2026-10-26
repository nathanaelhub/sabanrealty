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
- **Statia Day Instagram campaign** (built in another session, in the `ig-auto` repo): fully scheduled 26 Oct to 24 Nov. Posted so far: 8, 15 and 22 Oct.
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
- Sister repo `~/GitHub/ig-auto`: Instagram scheduler. It needs the `IG_ACCESS_TOKEN` and `IG_USER_ID` GitHub secrets; the token lasts about 60 days (skill `ig-token-refresh`).
- `~/Desktop/Desktop/R_E_V/`: all marketing assets (Listings, Social Posts, Videos, SEO, Statia Day 2026 Campaign, Google Business Profile).
- `~/Documents/sabanrealty-photo-originals-2026-10-03/`: original listing photos (backup).
- Claude memory: `~/.claude/projects/-Users-nathanaeljohnson-GitHub-sabanrealty/memory/` holds project notes. Copy it to keep context.
- Tools used: `gh` (logged in), Python 3 with Pillow, Node 24, ffmpeg, and Brave or Chrome for tests and image renders.

---

# Admin page (separate session, 1–24 Oct 2026)

## What this is
`https://sabanrealty.com/admin/` lets a non-technical person (Nathanael's dad) publish without Claude or a terminal. It has a shared passphrase and no accounts. How a change flows:

1. `admin/index.html`: a noindex page that is not linked anywhere. It shrinks photos in the browser and shows a preview.
2. Cloudflare Worker `sabanrealty-admin` (`scripts/admin-worker/`, live at `https://sabanrealty-admin.njdj.workers.dev`): checks the passphrase, writes photos to R2 (never overwrites), and sends a `repository_dispatch`.
3. `.github/workflows/admin-publish.yml` runs `scripts/admin/apply_change.py`, the only code that edits the repo. It validates the change, edits `listings.json`, regenerates the listing pages and updates the sitemap. It then runs the static checks as a gate, commits as "Admin: …", pushes, and posts a commit comment mentioning @nathanaelhub.

The design spec is `docs/superpowers/specs/2026-10-01-admin-page-design.md`. Operating notes are in `ADDING-PROPERTIES.md` → "Admin page".

## Finished (all live)
- Add a for-sale listing: photos, details, description, YouTube link, "New" ribbon, homepage spot.
- Update a listing: price, under contract, sold (both remove the price automatically), back on the market, hide, unhide.
- "Edit details and description" (f489987): the description is edited as plain text (`#`, `##`, `- `, `**bold**`), and only changed fields are sent.
- First real publish worked on 23 Oct: "Admin: mark Daphne Cottage sold" (cb9886d). The push started the Pages build, and the commit comment was posted.
- 24 Oct (f53ba0a, f254914; Worker redeployed):
  - New photos also get 900px card copies in R2 under `thumbs/listings/<id>/`.
  - Worker `GET /health` and a home-screen warning when the GitHub token is within 14 days of expiry or broken.
  - A daily Worker cron (13:00 UTC) triggers `.github/workflows/admin-token-reminder.yml`, which opens or comments on an issue 14, 7, 3 and 1 days before expiry. Tested with a fake date (issue #18, closed).
  - The workflow now requests a Pages build only if the push didn't start one.
- Tests: 69 unit tests in `scripts/admin/test_apply_change.py`; full `/site-test` passes.

## Unfinished / open
- **Open question for the user:** the design checker flags the thick left border on the `.problems` and `.note` alert boxes in `admin/index.html`. Those styles predate the token-expiry work. Ask whether to restyle them; nothing has been changed.
- The real token's expiry date has never been observed. On the next visit to `/admin/`, no warning should appear if the token has more than 14 days left.
- Waiting on the dad's feedback. Ideas offered but not built: photo management for existing listings, a recent-changes list with undo, choosing the homepage listings, rentals, and a "call Nathanael" line on the error screen.

## Next steps
1. Open `/admin/` and confirm no warning shows, which means `/health` works with the real token.
2. Answer the alert-box styling question.
3. Build whatever the dad asks for next.

## Commands
```bash
python3 -m unittest scripts/admin/test_apply_change.py
python3 scripts/admin/apply_change.py --payload change.json --skip-image-check   # local apply
cd scripts/admin-worker && npx wrangler deploy                                   # redeploy the Worker
cd scripts/admin-worker && npx wrangler dev --port 8787 --local                  # local Worker (needs .dev.vars)
python3 -m http.server 8899                                                      # then open http://localhost:8899/admin/
npx wrangler secret put GITHUB_TOKEN        # renew the token (fine-grained PAT, this repo only: Contents RW, Actions read)
npx wrangler secret put ADMIN_PASSPHRASE    # change the passphrase (16+ characters)
```
- `wrangler login` on a new machine: in a non-interactive shell, use `script -q /dev/null npx wrangler login` and approve in the default browser.
- Before deploying the Worker from a worktree, move `.dev.vars` aside so local values don't leak into the deploy.

## Outside the repo (admin)
- Worker secrets, held in Cloudflare and not in the repo: `ADMIN_PASSPHRASE`, `GITHUB_TOKEN`.
- `scripts/admin-worker/.dev.vars` (gitignored; local testing only): `ADMIN_PASSPHRASE`, `ALLOWED_ORIGINS=http://localhost:8899`, `DRY_RUN=1`. Recreate it from `.dev.vars.example`.
- The wrangler OAuth login is per machine and has to be redone on the new computer.
- The fine-grained PAT is in GitHub settings; it expires, and the reminder issue will flag that.

---

# Handoff, part 2: video + Instagram campaign (session 16–26 Oct 2026)

A second session ran in parallel on the same project. Almost none of it touches this
repo — it lives in `~/GitHub/ig-auto` and `~/Desktop/Desktop/R_E_V/` — but it is the work
most likely to need attention in the next two weeks, so it is recorded here.

## What it was about
Building the Villa Frangipani reel, planning the Statia Day 2026 campaign around it, and
then enforcing the client's standing content rules across everything already scheduled.

## Finished
- **Villa Frangipani reel** — 70.6 s, 1080×1920, 30 fps, −16 LUFS, burned-in subtitles,
  ElevenLabs voiceover, "Dreams Become Real" (Kevin MacLeod, CC BY 4.0).
  `R_E_V/video-tool-test/renders/Villa Frangipani/`. Approved. Build log in `BUILD-NOTES.md`
  there; the scripts under `captions/` are the real record of how it was made.
  Two faults were found and fixed during the build and are worth knowing: this ffmpeg has
  **no `drawtext`/libass**, so subtitles are PIL-rendered PNGs overlaid via the concat
  demuxer; and the 24 fps source duplicated every 4th frame until every segment was run
  through `minterpolate`.
- **Statia Day 2026 campaign** — `R_E_V/Statia Day 2026 Campaign/`: README (plan, calendar,
  rule banner), REELS.md, Instagram and Facebook captions, a shareable PDF (`make-pdf.py`
  rebuilds it), and `Posts/` with every rendered image. 16 Nov 2026 is the 250th anniversary
  of the First Salute, with a royal visit; the campaign runs 8 Oct – 24 Nov. All 17 Statia
  entries are queued in `ig-auto/schedule.json`. Posted so far: 8, 15 and 22 Oct.
- **Statia buying guide** — `blog/buying-property-on-st-eustatius/`, live, dated Sept 2026.
  `st-eustatius/index.html` links to it (d9e5c15).
- **Standing-rule enforcement.** Three breaches of the dad's "never mention volcanoes" rule
  were found and fixed, plus one of "never say private viewing":
  1. 22 Oct carousel, slide 3 read "A volcano, a fort, 250 years" — taken down, fixed,
     re-uploaded over the same R2 key, re-posted the same day.
  2. 25 Oct caption, "red volcanic cliffs" → "red rock cliffs".
  3. **13 Nov "Fort Oranje" image** (fixed 25 Oct, the subtlest one): it was rendered from
     the full Rijksmuseum scan rather than the trimmed plate, so the lithograph's own
     printed caption — *"GEZIGT OP HET FORT ORANJE, DE KRATER, GENOMEN VAN DE PASTORIJ"* —
     was legible along the bottom edge. *De Krater* is Dutch for "The Crater", so no English
     word search would ever have caught it. Re-rendered from a source with the margin
     painted out and re-uploaded over `posts/statia-fort-oranje.jpg`; the composition is
     otherwise identical and `schedule.json` needed no change. Details in
     `R_E_V/Statia Day 2026 Campaign/images/CREDITS.md`.
  - "Private viewing" turned out to be **hard-coded in two generators**, so every image and
    reel they made carried it: `ig-auto/make_thumbnail.py` `render_magazine()` footer and
    `ig-auto/build_reel.py`'s outro card. Both patched (`b068161`), along with two unposted
    captions. The unposted queue is now verified clean of both rules.
- Facebook thumbnails for the reel: `R_E_V/Social Posts/Villa Frangipani FB thumbnail/`
  (three 16:9 treatments plus a 9:16 split — an aspect ratio still needs picking).

## In progress / unfinished
- **Four scheduled images still carry the old `PRIVATE VIEWINGS · SABANREALTY.COM` footer.**
  The generator is fixed but these were rendered before the fix: Villa Frangipani teaser
  (**27 Oct — the soonest**), Johnny's Ground Secret (30 Oct), The Quiet Island (9 Nov),
  Anslyn Estate (23 Nov). They need regenerating and re-uploading over their existing R2
  keys. **Not started deliberately** — another session generated them and the exact source
  photo, title and dek were not recorded, so they have to be reverse-engineered from the
  rendered image and may drift visually from what is scheduled. Worth confirming with the
  user before doing it.
- **A question for the user, not a breach:** the 19 Nov "Villa Frangipani Still For Sale"
  image shows **$1,399,000**. The no-price instruction was given for the *reel*, and the
  house convention is that Instagram keeps the price, so it was left alone.
- **No present-day Statia b-roll.** Two reel concepts in REELS.md (#3 "250 Years Ago, This
  Island Fired Back" and #7 "Statia in 60 Seconds") are blocked on roughly 10 minutes of
  footage from Fort Oranje, the Oranjestad waterfront and The Quill trailhead. Needed before
  10 Nov or those two get cut. Ask Jeff who is on-island with a camera.
- Longer-standing: pick a Facebook thumbnail aspect ratio.

## Exact next steps
1. **Decide on the four magazine images** (the 27 Oct one is immediate). If yes: identify
   each source photo and its title/dek, re-render with the patched `make_thumbnail.py`, and
   upload over the same R2 key with `node scripts/r2-manage.js upload <dir> posts`.
2. Answer the $1,399,000 question for the 19 Nov post.
3. Chase Jeff about Statia b-roll before 10 Nov.
4. Before anything else ships: **inspect every image at full resolution, not on a contact
   sheet**, and read any lettering inside source artwork — including in other languages.
   That is what the Fort Oranje miss cost.

## Commands
```bash
cd ~/GitHub/ig-auto
python3 add_post.py --name … --when <UTC-ISO> --type photo --url <r2-url> --caption …
python3 make_thumbnail.py <photo> --title … --tag … --style editorial --size ig --no-price --out …
python3 build_portal.py                                  # rebuild the preview portal
gh workflow run ig-publish.yml --ref main                # publish anything now due
python3 -c "import json;d=json.load(open('schedule.json'));print(sum(1 for e in d if not e.get('posted')),'unposted')"
cd "~/Desktop/Desktop/R_E_V/Statia Day 2026 Campaign" && python3 make-pdf.py   # rebuild the plan PDF
```
The publisher is a GitHub Actions cron (`.github/workflows/ig-publish.yml`, `0 14 * * *`,
i.e. **daily**) that posts any `schedule.json` entry whose `datetime` has passed. A
workflow run succeeding is **not** proof a post went out — check the entry has `posted:
true` and a `media_id`. Instagram sometimes returns a transient 400 on `media_publish`;
re-running the workflow has always worked.

## Outside the repo (in addition to part 1)
- `~/GitHub/ig-auto` — the Instagram scheduler, its own git repo, pushed and clean.
  GitHub secrets: `IG_ACCESS_TOKEN`, `IG_USER_ID`. The token lasts ~60 days — the
  `ig-token-refresh` skill rolls it forward.
- `~/Desktop/Desktop/R_E_V/` — all video and campaign assets, **not under version control
  and not backed up anywhere else**. The renders, the campaign folder and the source photos
  only exist here. Copy this folder to the new computer before wiping the old one.
- `R_E_V/video-tool-test/remotion/.env` — `ELEVENLABS_API_KEY` for the voiceover. The key in
  use is scoped to TTS and STT only (`/v1/models` and `/v2/voices` return
  `missing_permissions`, which is expected, not a broken key). The three keys in
  `.env.bak-20260916` are key *IDs*, not keys, and do not work.
- Standing client rules live in Claude memory at
  `~/.claude/projects/-Users-nathanaeljohnson-GitHub-sabanrealty/memory/listing-video-rules.md`.
  **Read it before producing anything.** In short: never "private viewing"; never anything
  to do with volcanoes (The Quill and Mount Scenery may be named, never *called* one);
  end videos on the contact card; low-opacity logo bottom-right; hold stills longer; vary
  the music between listings.
- An earlier, more detailed reel write-up is at `~/Downloads/Reel 2 Handoff.md`.
