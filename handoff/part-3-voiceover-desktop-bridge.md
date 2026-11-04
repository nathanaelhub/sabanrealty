# Handoff, part 3: free-draft voiceover + the Claude Desktop bridge (session 23–26 Oct 2026)

A short session appended to parts 1–2. It touched **no site files** — everything here is
either in `~/GitHub/ig-auto`, in the un-versioned `R_E_V` folder, or in user-scope
`~/.claude/`. Read part 2 first; this does not repeat it.

## What it was about
Three things: cut the cost of iterating voiceover copy, evaluate three third-party content
tools the user had heard were free, and find out whether Claude Code can drive the Claude
Desktop app the way it drives an MCP server.

## Finished
- **`VO_ENGINE=local` — a free drafting engine for the micro-cut builder.** Iterating
  wording used to cost one ElevenLabs call per sentence per attempt, because
  `build_micro.py` hard-exits when the voiceover overruns the picture and the only way to
  learn the length was to synthesize it. `build_micro.py` now takes a second engine that
  reads through a local **VoiceStudio** server (`localhost:3900`, OpenAI-compatible, no key,
  no quota): `POST /v1/audio/speech` for audio, `POST /v1/audio/transcriptions` with
  `timestamp_granularities[]=word` for timings. A new `align_from_words()` rebuilds
  ElevenLabs' character-alignment shape from those words, so the caption code never learns
  which engine spoke. Two guards, because a draft reaching the feed is worse than no draft:
  drafts cache in `vo/<slug>-draft/` (never the real `vo/<slug>/`), and output is written to
  `… [DRAFT].mp4`, never the real filename. Documented in that folder's `BUILD-NOTES.md`.
- **`build_reel.py:label_overlay` orphan-mark fix** — it drew its little accent rule even
  when the room label was empty, leaving a stray dash bottom-left on every unlabelled
  segment. Now guarded by `if text:`. Pushed in `ig-auto` as part of `b068161`, along with
  the outro card's `"DM us for a private viewing"` → `"DM us for more details"`.
- **A `claude-desktop-bridge` skill** at `~/.claude/skills/claude-desktop-bridge/SKILL.md`
  (user scope, so it is **not** in any repo — copy it by hand). See the warning below.
- **Vendor pricing, checked against the vendors' own pages** (aggregator figures were
  wrong): **CreatorBerry** Starter **$23/mo billed annually** (not the $29 quoted around the
  web), 7-day trial, 100 credits/mo, 3 workspaces. **Flick** Solo **£11/mo billed yearly**,
  7-day trial, 4 social profiles, +£4/mo per extra — and Hashtags, Scheduling and Analytics
  are all in the cheapest tier, so hashtag research is not upsell-gated. **Faceless was not
  reached.** None of the three is free; "free" was a free *trial* in every case.

## In progress / unfinished
- **`VO_ENGINE=local` has never been run end to end.** VoiceStudio is not installed — the
  disk was 94% full (13 GB free) and the model is ~2.3 GB on top of a torch stack. The
  unreachable-backend path is tested and exits with a clear message, and the default
  ElevenLabs path was re-run after the change and is unchanged in behaviour (22.22 s,
  −16.6 LUFS, 10 caption chunks, zero API calls off cache). But the local branch itself is
  **written and reviewed, not exercised.** Treat its first run as a test, not as production.
- **Faceless** was never priced. The other two make it unlikely to be free either.
- **The Pool micro-cut still does not match its two siblings** (no contact card, no voice,
  no captions, barely any motion) and is scheduled **12 Nov**. Rebuild it through
  `build_micro.py` or accept the mismatch knowingly. Covered in `BUILD-NOTES.md`.
- The two finished micro-cuts (The Kitchen, Waking Up Here) are **built but unscheduled** —
  nothing uploaded to R2, no dates chosen.

## Exact next steps
1. **The 27 Oct Villa Frangipani teaser publishes tomorrow at 14:00 UTC** and still carries
   the old `PRIVATE VIEWINGS` footer. It is the one item here with a deadline. Part 2's
   "Exact next steps" #1 covers what to do; the only new fact is that the clock has nearly
   run out. Doing nothing is a choice to let it go out with the old footer.
2. If the local voiceover engine matters, install VoiceStudio and run
   `VO_ENGINE=local … build_micro.py kitchen.json` once, then compare `[DRAFT]` output
   timings against an ElevenLabs build of the same spec before trusting it.
3. Decide on CreatorBerry/Flick, or drop them. If one is wanted, the cheap play is one
   month of Flick Solo to harvest hashtag sets, then cancel — nothing in either tool is
   load-bearing for the pipeline.
4. Choose dates for the two unscheduled micro-cuts, or shelve them.

## ⚠️ The Claude Desktop bridge — read before using it
There is **no MCP connection to Claude Desktop and one could not be made.** Claude.app has
`NSAppleScriptEnabled = false`, no scripting dictionary and no tool surface. The skill
drives it with synthetic keystrokes through System Events — GUI automation and a
screen-scrape, not an API. It is genuinely fragile, and it misfired during this session:

- `tell application "Claude" to activate` **reports success and does nothing.** Only
  `open -a Claude` actually raises the window.
- `keystroke` inside `tell process "Claude"` **does not target Claude.** System Events sends
  to whatever has focus; the enclosing block is decorative. On the first attempt this pasted
  a 53-line prompt into a *different Claude Code session's* input box. Nothing was sent, and
  no file was touched, but only because the procedure screenshots before pressing Enter.
- **Several Claude sessions share one machine, one clipboard and one Desktop app.** Taking
  Desktop over also overwrote the clipboard of a concurrent session that was mid-task, which
  stopped itself and said so. The skill now refuses to run when other sessions are active.

The skill encodes all of the above plus per-keystroke focus re-verification and a
screenshot-before-Enter step. It forbids sending credentials or payment details across the
bridge. **If the new computer has a working MCP or API route to the same capability, prefer
it and delete the skill.**

## Outside the repo (in addition to parts 1–2)
- `R_E_V/video-tool-test/renders/Villa Frangipani/micro-cuts/` — `build_micro.py` (the
  patched builder) and `BUILD-NOTES.md` (the whole rationale: loudness numbers, the music
  calibration trap, the `VO_ENGINE` notes) **exist only here.** `R_E_V` is ~2.1 GB, is not a
  git repo and is backed up nowhere. Part 2 already says copy the folder; this is the piece
  of it that is *source code* rather than assets, so losing it loses work, not just output.
- `~/.claude/skills/claude-desktop-bridge/SKILL.md` — user scope, not in any repo.
- `~/.claude/projects/-Users-nathanaeljohnson-GitHub-sabanrealty/memory/` — project memory,
  already noted in part 1. Also `~/.claude/skill-observations/` (user scope) holds the
  task-observer backlog, 20 entries. Neither is version-controlled.
- Python: `/usr/local/bin/python3` is the only interpreter here with Pillow, and it needs
  `SSL_CERT_FILE=/etc/ssl/cert.pem` for any HTTPS call. This ffmpeg (8.1.1) has **no**
  `drawtext`, `subtitles` or `ass` filter, so burned-in captions go through PIL-rendered
  PNGs and `overlay`. Both facts will bite on a fresh machine.
