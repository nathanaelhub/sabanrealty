# Handoff, part 5: bath counts, stale blog prices, style-frame posts (4–6 Nov 2026)

Updated: 2026-11-06

Nathanael's dad found wrong bathroom counts on the live site. This session fixed them, traced
why they happened, fixed the same error in other places it had spread to, and updated two
out-of-date blog posts. Near the end, another session asked it to turn six Saba "style frames"
into Instagram posts. They are built but **not scheduled**.

## Why the bath counts were wrong
The source spreadsheet (`R_E_V/Saba realty website/Website data.csv`) has a Bedrooms column
but **no Bathrooms column**. Commit `3bdf309` (1 Feb 2026) left all 11 homes with
baths == beds. Those numbers were later copied into descriptions, Instagram captions and
thumbnail images. Treat `bathrooms` in `data/listings.json` as unverified unless the broker
has confirmed it. This is also saved in auto-memory as `bathroom-counts-unverified.md`.

## Finished
- **Bath counts (sabanrealty PR #20, issue #19), live:** View Villa 3 → 4, Anslyn Estate
  4 → 2, House on the Path 2 → 1. The House on the Path description line and its generated page
  metadata were corrected too.
- **Blog (PR #24, issue #23), live:**
  - `blog/saba-property-prices`: land now starts at $106K and lists only current parcels.
    Commercial is now "from about $220K". House on the Path is "a five-minute hike from
    Windwardside". Dated November 2026.
  - `blog/where-to-live-on-saba`: the Zion's Hill land line reflects what is still available.
  - The blog card and sitemap `lastmod` dates are updated.
- **ig-auto (PR #60, issue #59):** the 6 Nov House on the Path post now says 2 bed / 1 bath.
  Its image is regenerated as `posts/house-on-the-path-v2.jpg` ("2BD | 1 BT"). The posted reel's
  record now matches the caption Nathanael corrected by hand on Instagram.
- **GitHub Pages outage, 4 Nov:** deploys sat queued with no runner for about 20 minutes while
  githubstatus.com said all was well. A cancel and a re-requested build through
  `gh api -X POST repos/nathanaelhub/sabanrealty/pages/builds` were followed by recovery; whether
  they caused it is unclear.

## Unfinished
1. **Six posted captions still have wrong bath counts.** Instagram's API can't edit captions,
   so they must be changed by hand in the app.
   - Anslyn, "4 bed / 4 bath" → "4 bed / 2 bath":
     - [featured](https://www.instagram.com/p/DagHuwGD_jf/)
     - [reel](https://www.instagram.com/reel/DalDFALEdbM/)
     - [voiceover reel](https://www.instagram.com/reel/DbTYyQlimFO/)
   - Anslyn [carousel](https://www.instagram.com/p/Dbvjd70EgWJ/): "Four bedrooms, four baths"
     → "Four bedrooms, two baths".
   - View Villa, 3 baths → 4:
     - [$980,000 View](https://www.instagram.com/p/Db3SgI6G782/)
     - [tour reel](https://www.instagram.com/reel/Db8b-WBDBpv/)

   All of these except the carousel also say "private viewing", which is banned; change it to
   "to book a viewing". The `schedule.json` records for these posts still hold the old text.
2. **Wrong counts printed on posted images:** Anslyn featured ("4BD | 4 BT") and the $980,000 View
   post ("3BD | 3BT"). The only fix is to delete and repost. Nathanael hasn't decided.
3. **Questions for the broker:**
   - **Iguana Rock:** the site says 2 baths, but the description says "three bathrooms" plus a
     one-bed guest apartment. Its Dec 2 reel and captions say 2 / 2.
   - **Unconfirmed counts:** Troy Hill's half bath; View Villa's "three half baths"; the
     Statia Poolhouse (hidden, 5/5, but described as 9 bungalows); and the three rentals'
     bath counts, which nothing confirms.
4. **Style-frame posts: built, waiting on Nathanael's approval, not uploaded or scheduled.**
   - **Files:** `~/Desktop/reelkit/reels/_saban/styleframes-ig/saba-frame-1.jpg` … `6.jpg`,
     with `grid.jpg` as a preview.
   - **Source:** `styleframes_ig.py` and `shoot_ig.mjs` in that same folder. `reels/_saban` is
     git-ignored in reelkit, so these files are only on the old Mac. Copy them across.
   - **Proposed slots:**
     - Mon 21 Dec: 5 square miles
     - Mon 4 Jan: Find your place
     - Wed 6 Jan: Map
     - Fri 8 Jan: Homes on Saba
     - Wed 13 Jan: Mt Scenery
     - Fri 15 Jan: 4 villages
   - **Reel slot:** these dates need a reel reserved on Mon 11 Jan, to keep one reel after
     every three pictures.
   - **Open questions:**
     - Is frame 2's photo really Mt Scenery?
     - Is the Jan 11 reel slot OK?
     - The "Windwardside" and "St. Johns" photos are unconfirmed, so no frame labels any photo
       with a village. The "The Bottom" photo matches the site's labeled photo.
   - **The queue has been changing:** another session moved posts on 4 Nov, and the Troy Villa
     reel is on hold. Re-read the queue before scheduling.
   - The request came from session `sabanrealty-c1`.
5. **Not this session's work:** `.gitignore` (motion-video ignores) and `videos/motion-2026-11/`
   (520 MB on disk) are uncommitted from the motion-videos session. They were left alone.
6. **Local `main`** is 12 commits ahead of origin (handoff notes and the motion-video sources) and 3 behind. Pull with
   rebase before pushing.

## Next steps
1. Get Nathanael's yes on the six style frames and the frame 2 photo. Then follow `/ig-batch`:
   upload with `node scripts/r2-manage.js upload <dir> posts` from sabanrealty, add entries
   with `python3 add_post.py`, rebuild the portal, and open a PR.
2. Ask the broker the questions in item 3, then update `data/listings.json` and any
   captions and images that use those counts.
3. Have Nathanael edit the six captions (item 1). Then copy the live captions into
   `ig-auto/schedule.json`.

## Commands
- Site tests: `bash scripts/site-test/run.sh` (add `static` for static checks only).
  `run.sh prod` waits for a Pages build of the **local** HEAD, so it never finishes while local
  `main` has unpushed commits. Check the live site with curl instead.
- Regenerate listing pages after editing a description: `python3 scripts/generate-listing-pages.py`.
  The generator copies each description into the page's metadata. The `site-conventions`
  skill says description edits don't need this, which is wrong; this is logged as task-observer
  observation 0108.
- Style frames: `cd ~/Desktop/reelkit/reels/_saban && python3 styleframes_ig.py && node shoot_ig.mjs`.
- Instagram thumbnails: `make_thumbnail.py` needs Pillow, which the system Python doesn't have.
  This session used a throwaway virtual environment.

## Outside the repo
- **sabanrealty `.env`:** `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_R2_ACCESS_KEY_ID`,
  `CLOUDFLARE_R2_SECRET_ACCESS_KEY`, `CLOUDFLARE_R2_BUCKET`.
- **ig-auto `.env`:** `IG_ACCESS_TOKEN`, `IG_USER_ID`, `IG_GRAPH_VERSION`, `R2_ACCESS_KEY_ID`,
  `R2_SECRET_ACCESS_KEY`, `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_PUBLIC_BASE`.
- **Files outside the repo:**
  - **On R2:** `posts/house-on-the-path-v2.jpg` (new). The old `posts/house-on-the-path.jpg`
    is still there.
  - **Auto-memory:** `bathroom-counts-unverified.md`.
  - **Task-observer log:** observations 0108 (the regeneration rule) and 0110 (the `prod` check).
