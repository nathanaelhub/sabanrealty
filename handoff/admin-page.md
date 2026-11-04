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
