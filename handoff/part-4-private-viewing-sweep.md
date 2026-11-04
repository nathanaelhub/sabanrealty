# Handoff, part 4: the "private viewing" sweep through the reels (26 Oct 2026)

Part 2 said four magazine images needed regenerating. That was the visible edge of a
much larger problem, found while answering "should we fix those first?".

## What it turned out to be
The phrase was hard-coded in **three** generators, not one. The first two were already
patched (`ig-auto/make_thumbnail.py`, `ig-auto/build_reel.py`). The third was
**`R_E_V/video-tool-test/remotion/scripts/make_endcard.py`**, which printed
*"Book a private viewing"* on the Hyperframes end card — so **every reel built with it
carried the banned phrase on screen**, where no text search of captions or schedule would
ever find it.

**Seven of the nine unposted reels were affected**, including **Union Estate, which was due
at 14:00 UTC that day and still unpublished** — the daily cron fires around 17:15–18:25 UTC,
so it was inside the hour. It was held first, before anything else.

## Finished
- **`make_endcard.py` patched** — `cta` is now "Book a viewing".
- **Six reels fixed and re-uploaded over their existing R2 keys**: Union Estate,
  Johnny's Ground Secret, Treasured Horseshoe, Anslyn Estate, Iguana Rock, View Villa.
  Method: re-render the 5-second end card with the patched generator, then splice it onto
  the original body in one ffmpeg pass (`trim` + `concat`, CRF 18). Nothing above the join
  is touched and the body is re-encoded once; the junction was checked frame by frame.
  All six verified to read "Book a viewing" on their final frame. Dates restored.
- **The four magazine images regenerated and re-uploaded** — Villa Frangipani teaser,
  The Quiet Island, and the Johnny's Ground Secret and Anslyn Estate reel covers.
  The original source photos were not recorded anywhere, so each was recovered by
  matching edge structure between the rendered image and every candidate listing photo
  (the matcher scored the true source at 0.99 against 0.2 or less for everything else).
  Side-by-side checks confirm only the footer changed.
- **A fourth hard-coded string fixed**: `render_magazine()` always printed
  `SABA · DUTCH CARIBBEAN`, so the Villa Frangipani teaser — a **St. Eustatius** listing —
  read "SABA". It is now a `--running-head` option, and the teaser says ST. EUSTATIUS.
- **Treasured Horseshoe caption**: `$150,000` → `Open to Offers`, matching listings.json.
  The old end card had the stale price baked in; the new one reads from live data.
- Unposted queue re-verified: **zero** "private viewing", volcano or stale-price hits
  except the one item below.

## Unfinished — two things, both held or flagged
1. **Troy Villa aerial reel (11 Dec) — still says "DM us for a private viewing".**
   It is **held at 2026-12-31 with a `hold_reason` in `schedule.json`**, so it cannot
   publish by accident. It is the one reel whose end card comes from `build_reel.py`
   (green card), not the Hyperframes end card, so the splice recipe above does not apply
   unchanged. `build_reel.py` is already patched, but re-running it needs the original
   `--clip` list, which was not recorded. Options: rebuild it from the source clips if
   they can be found, or regenerate just the outro with `build_reel.py`'s `outro_card()`
   and redo the 0.5 s crossfade against the body. **Restore `2026-12-11T14:00:00Z` after.**
2. **"The Pool" micro-reel (12 Nov) ends on a photograph, with no contact card.** That
   breaks the standing "end on the contact card" rule, and `REELS.md` says these
   micro-cuts should go "straight out to the contact card". Not a banned phrase, so it
   was left alone rather than restructured without a decision — but it should either get
   the card appended or be a deliberate exception.

## The lesson worth keeping
Three separate generators, each with the phrase hard-coded, found one at a time over four
days. **When a client rule is broken, grep the tools that produce the artifacts, not just
the artifacts** — and remember the artifacts include frames inside videos and lettering
inside source artwork, neither of which any text search will reach.

## Commands
```bash
# re-render an end card after editing make_endcard.py
cd ~/Desktop/Desktop/R_E_V/video-tool-test/remotion
python3 scripts/make_endcard.py <listing-id> -o /tmp/<id>-endcard.mp4   # ~12 s, needs network

# splice a new end card onto an existing reel (replaces the last 5 s)
ffmpeg -y -i reel.mp4 -i endcard.mp4 -f lavfi -t 5 -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -filter_complex "[0:v]trim=0:<dur-5>,setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1[v0];\
[1:v]fps=30,scale=1080:1920,setsar=1[v1];[0:a]atrim=0:<dur-5>,asetpts=PTS-STARTPTS[a0];\
[2:a]asetpts=PTS-STARTPTS[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -c:a aac -b:a 160k out.mp4

# magazine image with a non-Saba running head
python3 ~/GitHub/ig-auto/make_thumbnail.py photo.jpg --title "..." --subtitle "..." \
  --style magazine --size ig --no-price --running-head "ST. EUSTATIUS · DUTCH CARIBBEAN" --out x.jpg

# check every unposted item for banned text (captions only -- NOT the pixels)
cd ~/GitHub/ig-auto && python3 -c "import json;d=json.load(open('schedule.json'));\
print([e['name'] for e in d if not e.get('posted') and 'private viewing' in json.dumps(e).lower()])"
```
To audit the **pixels**, pull each image and each reel's final frame and look at them at full
size — contact sheets at a few hundred pixels hid a banned word once already.
