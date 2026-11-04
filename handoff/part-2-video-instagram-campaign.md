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
- **Saba Snack "Price Reduced" post — built, not scheduled.** After the price cut
  ($320,000 → $220,000; site live, sabanrealty PR #17), a social card with a coral "PRICE
  REDUCED" top band was made at Dad's request, in both **horizontal and vertical** versions,
  saved in `~/Downloads/` (`Saba Snack — Price Reduced $220K (horizontal).jpg` and
  `(vertical).jpg`). It is **not** queued on Instagram and no Facebook channel was chosen
  (auto cross-post vs. manual). Needs the user's go-ahead + that FB decision, then upload to
  R2 and `add_post.py`.

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
i.e. **daily**) that posts any `schedule.json` entry whose `datetime` has passed.
**Fixed 19 Oct (PR #58, commit 91eb004):** `run_due.py` used to catch every publish error
and exit 0, so the job went green while nothing posted — which hid a week-long outage after
the old token expired on 9 Oct. It now writes successes first (so they are never re-posted),
then exits non-zero with a summary if anything failed, and the workflow's portal + commit
steps are `if: always()`. So a **green run now really does mean every due post went out**,
and any failure turns the run red and emails an alert. Instagram can still return a transient
400 on `media_publish`; that entry stays unposted and retries on the next daily run (or a
manual re-run). The cron often lands a few hours after 14:00 UTC — that scheduler lag is
normal, not a fault.

## Outside the repo (in addition to part 1)
- `~/GitHub/ig-auto` — the Instagram scheduler, its own git repo, pushed and clean.
  GitHub secrets: `IG_ACCESS_TOKEN`, `IG_USER_ID`. **The token is now a permanent Meta
  system-user token (installed 16 Oct, `expires_at: 0` — never expires)**, so the old
  ~60-day `ig-token-refresh` routine is only a fallback if it is ever revoked. One known
  gap: this token lacks `instagram_manage_insights`, so the separate analytics job
  (`ig-insights.yml` / `insights.py`) will fail — now visibly, thanks to the fail-loudly fix
  above — until Jeff adds that sixth permission to the system user in Meta Business settings
  and a fresh token is written to `.env` + the GitHub secret. Publishing is unaffected. The
  token also lives in `ig-auto/.env` (gitignored): `IG_APP_ID`, `IG_APP_SECRET`,
  `IG_ACCESS_TOKEN`, `IG_USER_ID`, `IG_GRAPH_VERSION` — move it to the new computer by hand.
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
