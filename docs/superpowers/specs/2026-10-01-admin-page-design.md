# Admin page for adding listings without Claude CLI

## Context

Adding a listing today needs Nathanael at a terminal: upload photos with `scripts/r2-manage.js`, hand-edit `data/listings.json`, run `scripts/generate-listing-pages.py`, paste a `<url>` block into `sitemap.xml`, commit, push. There is no backend and no CI in this repo (GitHub Pages legacy build from `main`, public repo, DNS not on Cloudflare).

Goal: a page at `sabanrealty.com/admin/` where a non-technical person (dad) can add a for-sale listing (photos, details, YouTube link) and make quick status changes, and have it go live in a few minutes with no one touching a terminal.

Decisions already made with the user:
- **Access:** one shared passphrase, typed once per device. No accounts.
- **Publishing:** goes live right away after an in-page preview; Nathanael gets an email.
- **Scope v1:** add a for-sale listing, plus change price / mark under contract / mark sold / back to available / hide / unhide.
- **Out of scope v1:** vacation rentals, editing descriptions or photos of existing listings, deleting listings. The payload carries a `kind` field so rentals can be added later.

## Architecture

```
admin/index.html  ──(passphrase, CORS)──▶  Cloudflare Worker  ──▶ R2 bucket (photos, via binding)
 (static, on Pages)                              │
        ▲                                        └──▶ GitHub repository_dispatch
        │ polls live data/listings.json                       │
        └───────────────────────────────  GitHub Action: apply change, regenerate,
                                           sitemap, static tests, commit, push
```

Three units, each with one job:

| Unit | Job | Trusts |
|---|---|---|
| `admin/index.html` | Form, photo resize, preview, progress. Builds the description HTML. | Nothing; it is public |
| Worker (`scripts/admin-worker/`) | Checks passphrase, writes photos to R2, forwards the change request to GitHub | Passphrase holder |
| Action + `scripts/admin/apply_change.py` | The only thing that edits the repo. Validates and sanitizes everything again. | Nothing in the payload |

Why this shape: the generator is Python and must run somewhere, so the repo mutation lives in an Action rather than in the Worker. The Worker uses an R2 **binding**, so no S3 keys leave the laptop. Both pieces are free tier.

## Components

### 1. `admin/index.html` (new)

Copy the `/links/` pattern (`links/index.html`): folder page, `<base href="/">`, `<meta name="robots" content="noindex">`, self-contained inline `<style>` and `<script>`, not in the sitemap, not linked anywhere, **no GA snippet**. Mobile-first with large controls. Use the `frontend-design` skill when building it.

Screens:
1. **Passphrase gate.** Calls Worker `GET /auth`; on success stores the passphrase in `localStorage`.
2. **Home.** Two choices: "Add a property" and "Update a property".
3. **Add a property** form:
   - Title; village (text with datalist) + island select (Saba / St. Eustatius) → `location` as `"<village>, Saba"` or `"<village>, St. Eustatius"` (the island regex in `buy/index.html:313` depends on this text).
   - Type (Villa / Cottage / Land / Commercial), price, bedrooms, bathrooms (hidden for land), optional acreage, optional property-size line, optional MLS number.
   - Overview textarea (blank line = new paragraph). Key features textarea (one per line; `Label: text` becomes a bold label).
   - YouTube link (id extracted in the page; shows the `i.ytimg.com` thumbnail as confirmation).
   - Photos: multi-select / drag-drop, thumbnails, reorder, first photo = cover. Each photo is resized in the browser to max 1600 px JPEG (~0.82 quality) via `createImageBitmap(..., {imageOrientation:'from-image'})` + canvas. This fixes rotation, strips EXIF/GPS, and keeps uploads small for island connections. Undecodable files (e.g. HEIC on desktop Chrome) get a plain-language error.
   - Checkboxes: "Show New ribbon" (default on), "Show on homepage" (default off).
   - Text fields auto-save to `localStorage` as a draft.
4. **Preview.** Renders the listing card and description using `css/styles.min.css` so it looks like the real site. Buttons: Back / Publish.
5. **Publishing.** Uploads photos one at a time with a progress bar and per-file retry, then sends the change. Polls Worker `/status`, then polls live `data/listings.json?t=<now>` until the id appears. Ends with "It's live" and a link, or "Something went wrong. Nathanael has been notified."
6. **Update a property.** Lists listings from live `data/listings.json` (hidden ones greyed). Per listing: Change price, Under contract, Sold, Back to available, Hide/Unhide. Each asks for confirmation. Hide doubles as undo for a mistaken add.

Description HTML built by the page matches the newest listings (`scenery-trail-land`):
`<h2>Title — Village, Island</h2>`, `<p><strong>Location:</strong> …</p>`, optional `<p><strong>Property Size:</strong> …</p>`, optional MLS line, `<h3>Property Overview:</h3>` + `<p>` paragraphs, `<h3>Key Features:</h3>` + `<ul><li>`. All user text is escaped. No price in the heading, so price changes never leave it stale.

### 2. Cloudflare Worker (new, `scripts/admin-worker/`)

`scripts/` is already excluded from the published site by `_config.yml`. Files: `wrangler.toml`, `src/index.js` (no dependencies; run with `npx wrangler`).

- Config: R2 binding `BUCKET` → the existing bucket (name is the `CLOUDFLARE_R2_BUCKET` value in `.env`). Secrets: `ADMIN_PASSPHRASE`, `GITHUB_TOKEN`. Vars: `ALLOWED_ORIGIN=https://sabanrealty.com`, `REPO=nathanaelhub/sabanrealty`, `PUBLIC_BASE=https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev`.
- Every route requires `Authorization: Bearer <passphrase>`, compared by SHA-256 digest with a timing-safe compare. CORS limited to `ALLOWED_ORIGIN`. The Worker refuses to run with a passphrase shorter than 16 characters. (As built: no rate-limit binding. The binding has no way to count only failed attempts, and a long passphrase cannot be guessed within the free plan's daily request cap.)
- Routes:
  - `GET /auth` → 204.
  - `PUT /upload/listings/<id>/<file>`: key must match `^listings/[a-z0-9-]+/[a-z0-9-]+\.jpg$`, body ≤ 5 MB, JPEG magic bytes checked, stored with `contentType: image/jpeg`. **Never overwrites**: an existing key returns 409. File names carry a random tag per photo (`<id>-<tag>.jpg`; order comes from the `images` array), so a 409 on retry means "already uploaded" and existing listings' photos cannot be replaced.
  - `POST /change`: size-capped JSON, adds a `request_id`, sends `repository_dispatch` (`event_type: admin-change`, everything under one `client_payload.change` key).
  - `GET /status?request_id=…`: looks up the workflow run by `run-name` and returns queued / running / success / failed.
- `GITHUB_TOKEN` is a fine-grained PAT limited to this one repo: Contents read/write (required for dispatch), Actions read (status). It expires; note the date like the Instagram token.

### 3. `scripts/admin/apply_change.py` (new, Python stdlib only)

Single entry point for every repo mutation; reads the payload from an env var or `--payload file.json`, so the CLI `/add-listing` flow can reuse it.

- **Validation (authoritative):** allowed actions and fields only; id is a slug of the title and unique across `properties` and `rentals`; `type` in villa/cottage/land/commercial; price a positive int; every image URL must be `PUBLIC_BASE/listings/<id>/…jpg` and return 200 on HEAD; YouTube id is 11 chars `[A-Za-z0-9_-]`.
- **Description sanitizer:** `html.parser` allowlist of `h2 h3 p strong ul li br`, no attributes, everything else escaped. The description is rendered with `innerHTML` (`property-detail.html:895`), so this is the XSS barrier.
- **Actions:**
  - `add`: append to `properties[]` with key order matching recent entries (`id`, `new`, `videos`, `title`, …). `priceFormatted` = `$1,234,567`. Video `uploadDate` scraped from the YouTube watch page, falling back to the current time. If "Show on homepage": rewrite the `featuredIds` array at `index.html:443` (new id first, keep three), asserting exactly one match.
  - `set-price`: `price`, `priceFormatted`.
  - `set-status` using the existing conventions: available (`for-sale`, drop `detailStatus`, needs a price); under contract (`for-sale` + `detailStatus:"under-contract"`, `price:0`, `"Under Contract"`); sold (`status:"sold"`, `price:0`, `"SOLD"`, drop `new`/`featured`/`detailStatus`). If the `<h2>` ends in the old ` - $price|SOLD|Under Contract` pattern, rewrite that suffix; otherwise leave it.
  - `set-hidden`: set or clear `hidden`. On hide, delete `properties/<id>/` and the sitemap block. Refuse if the id is in `featuredIds` or linked from `blog/` or `links/` (would create broken links).
- **After any action:** write JSON with 2-space indent and `ensure_ascii=False`; run `scripts/generate-listing-pages.py` (always, because the generated `<head>` bakes price, image and video); update `sitemap.xml` by text edit (insert before `</urlset>`, or update `lastmod`/`priority`: 0.8 active, 0.5 sold); remove orphan page folders.

### 4. `.github/workflows/admin-publish.yml` (new)

- Triggers: `repository_dispatch: [admin-change]`, plus `workflow_dispatch` with `payload` and `dry_run` inputs for testing.
- `run-name: admin ${{ github.event.client_payload.change.request_id }}`; `concurrency: admin-publish` with no cancel, so changes apply one at a time.
- `permissions: contents: write, pages: write`.
- Steps: checkout `main` → `python3 scripts/admin/apply_change.py` (payload passed through `env:`, never interpolated into a shell line) → `bash scripts/site-test/run.sh static` as a gate → commit as "Admin: add <title>" etc. → push (rebase and retry once) → request a Pages build → post a commit comment mentioning `@nathanaelhub` with a summary and the live link.
- In `dry_run`, print the diff and stop before commit.
- Failures: GitHub emails the PAT owner (Nathanael) for failed runs; the admin page shows the failed state.

### 5. Small edits to existing files

- `scripts/site-test/checks.py`: add a check that `admin/index.html` has `noindex` and that `/admin/` is not in the sitemap.
- `ADDING-PROPERTIES.md`: add an "Admin page" section (how it works, how to rotate the passphrase and PAT, how to redeploy the Worker) and fix the stale `youtubeLink` / missing-generator notes.
- Save this design to `docs/superpowers/specs/2026-10-01-admin-page-design.md` (`docs/` is excluded from the published site).

## Build order

1. `apply_change.py` with unit tests first (`scripts/admin/test_apply_change.py`, stdlib `unittest`, fixture copy of the JSON/sitemap): add, each status transition, hide/unhide, id collision, sanitizer stripping `<script>` and attributes, sitemap edits, `featuredIds` rewrite.
2. Workflow; exercise with `workflow_dispatch` + `dry_run`.
3. Worker; test with `npx wrangler dev` and curl.
4. Admin page against the local Worker, then the deployed one.
5. Docs, checks.py addition, full `/site-test`.

## Things Nathanael does by hand (one time)

- `! npx wrangler login`, then deploy and `wrangler secret put ADMIN_PASSPHRASE` / `GITHUB_TOKEN`.
- Create the fine-grained PAT in GitHub settings.
- Choose the passphrase (four or more random words) and give it to dad.

## Verification

- **Unit:** `python3 -m unittest scripts/admin/test_apply_change.py` passes.
- **Local apply:** run `apply_change.py --payload sample.json` on a scratch branch; `git diff` should touch only `data/listings.json`, one new `properties/<id>/index.html`, and `sitemap.xml`; then `bash scripts/site-test/run.sh` (static + browser) passes.
- **Worker:** with `wrangler dev`: wrong passphrase → 401; valid JPEG → 200 and object present; same key again → 409; non-JPEG → 415; oversized → 413; request from another origin gets no CORS headers.
- **Workflow dry run:** `workflow_dispatch` with a sample payload and `dry_run: true`; the printed diff matches the local one.
- **End to end on production:** add a clearly named test listing from a phone through `/admin/`, confirm the commit, the email, the live page at `/properties/<id>/`, the Buy grid card and the sitemap entry. Then exercise price change → under contract → sold → hide from the admin page, and finally remove the test entry with a normal commit and `r2-manage.js delete-folder`. The test listing is publicly visible for a few minutes.
- **Confirm during the first real run:** that a push made with the workflow's `GITHUB_TOKEN` triggers the Pages deploy. The explicit build request covers it; if neither works, push with the PAT stored as a repo secret instead. Also confirm the commit-comment mention produces an email; if not, comment on a pinned "Admin activity" issue instead.
- `bash scripts/site-test/run.sh prod` after the final push.

## Known limits

- Video means a YouTube link; dad uploads the video to YouTube himself. The site has no self-hosted video player.
- Anyone with the passphrase can publish. Rotation is one `wrangler secret put`.
- Abandoned uploads leave orphan files in R2; clean up occasionally with `r2-manage.js`.
- The admin page source and Worker source are public (public repo). Security rests on the passphrase and the Action's validation, not on the URL being secret.
