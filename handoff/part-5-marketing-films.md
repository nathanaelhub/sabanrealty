# Handoff, part 5: marketing films and reelkit (1 to 6 Nov 2026)

Updated: 6 Nov 2026 (wrap-up for the move to the new computer).

## What this session was about
Making professional, non-generic marketing videos for Saban Realty, first in this repo
(`videos/motion-2026-11/`) and then in **reelkit**, an open-source reel maker at
`~/Desktop/reelkit` (public at github.com/nathanaelhub/reelkit). The Saban films themselves
are private: they live in reelkit but are excluded from git through
`.git/info/exclude` (`reels/_saban/`, `reels/saban-*/`), so **they exist only on the old
computer's disk**. Copy `~/Desktop/reelkit/reels/` and `~/Desktop/reelkit/out/` across by hand.

Standing rules for every film: real photos only (never AI imagery), approved facts only
(5 sq mi; four villages Windwardside, The Bottom, St. Johns, Hell's Gate; Mt Scenery 887 m;
2,270 residents; listings.json), never "private viewing", nothing about volcanoes, no dashes
in on-screen text, end card held at least 3 s with sabanrealty.com and +599 416 5497, no
price or size on listing reels, H.264 yuv420p faststart 30 fps about -15 LUFS.

## Finished
- **This repo:** `videos/motion-2026-11/` canvas series sources (L1 The Mill, V1 CatsEye,
  L1_sample website-UI sample, shared synth and render tools). Committed in this wrap-up;
  heavy `assets/`, `build/`, `output/`, `.venv/` stay gitignored. The user rejected all
  three looks, so the series is parked, not in progress.
- **reelkit (public, all merged through github-flow, main protected, check `check`):**
  #4 CI, #5 springs + design lint, #6 taste references, #8 yuv420p tv range,
  #10 `<video data-clip>`, #12 pronunciation map, #14 ignore ERR_ABORTED in check,
  #16 9:16 / 16:9 / 1:1 formats, phoneme pronunciations, final two-pass loudnorm.
- **Saban films in reelkit (private), with the user's verdict:**

  | Film | Verdict |
  |---|---|
  | saban-mill-type / -scrapbook / -mosaic | rejected, "no hook" |
  | saban-saba (YouTube footage) | "ok, not the best" |
  | saban-doc (ElevenLabs voice) | rejected: low-quality footage, voice said "Sai-ba" |
  | style frames + saban-film (16:9) | liked, "a bit better" |
  | saban-stick (stick figure) | "gives off AI direction" |
  | saban-prints (silkscreen poster, lemo-opuscar) | delivered, no verdict |
  | saban-sketch "Five Days on Saba" (urban sketch) | liked the style and story "a bit" |
  | **saban-window "One Window"** (urban sketch) | **delivered 6 Nov, awaiting verdict** |

  "One Window": one window in Windwardside from 6 am to 9 pm, ink drawn once at dawn, each
  hour glazed over it as a new wash; cup steam hook, hummingbird, rain drips, rainbow,
  village lights, candle, "Saba. Find your window." 52.5 s, -14.8 LUFS, readcheck passes.
  Copy at `~/Desktop/reelkit/out/saban-window.mp4`; story and changes in its `TREATMENT.md`.
- **lemo-opuscar** installed and vetted (Claude plugin `lemo-opuscar@lemolab`, library at
  `~/lemo-opuscar`): 66 code-made film styles plus the DIRECTOR.md method.

## In progress or unfinished
- Waiting on the user's verdict for "One Window" (and the silkscreen film).
- reelkit skills for hooks, script structure (Hook, Problem, Solution, Proof, CTA) and the
  voice CLI: planned, not started. Remaining reelkit plan items: sound ducking/SFX,
  Whisper timing, video clips then raw-footage editing, a scored check.
- IG posts of the six style frames were handed to session sabanrealty-65, which was asking
  the user to confirm the village labels on the photos first (they were guesses).
- `reels/airplane-food/voice.mp3` in reelkit is untracked on purpose (macOS `say` demo).

## Next steps
1. On the new computer: install Node, ffmpeg (with loudnorm), Python 3 with numpy, and
   Playwright Chromium; clone reelkit; reinstall lemo-opuscar (`~/lemo-opuscar`, `npm install`).
   The private material is archived in iCloud Drive as
   `reelkit-private-2026-11-06.zip` (1.4 GB, 443 files, integrity tested): unzip it inside
   the reelkit folder to restore `reels/_saban/`, `reels/saban-*/`, `out/`, `taste/` and the
   airplane-food `voice.mp3`, then add the `.git/info/exclude` lines `reels/_saban/` and
   `reels/saban-*/` again. The `.env` is **not** in the archive: recreate it by hand.
2. Ask the user for the "One Window" verdict (remind them to watch with sound: Claude can't
   hear the audio). If they like it, cut 9:16 and 1:1 versions; if not, take the next angle
   in the same urban-sketch style.
3. Then the hook/script/voice skills for reelkit, each through github-flow
   (issue, branch, PR, CI, squash-merge).

## Commands
```bash
# reelkit
cd ~/Desktop/reelkit && npm test                  # the CI check
npm run doctor                                    # dependency check
# lemo-opuscar films (urban sketch): rebuild end to end
cd ~/Desktop/reelkit/reels/saban-window && ./build.sh
#   inside: node ~/lemo-opuscar/core/render/events.mjs . --q 'strokes=1'
#           node ~/lemo-opuscar/core/render/video.mjs . --fps 30 --workers 2 --out out/video.mp4
#           node ~/lemo-opuscar/core/render/readcheck.mjs .
#           python3 mix.py, then two-pass loudnorm to -15
# stills for review
node ~/lemo-opuscar/core/render/still.mjs . 5 20 40 --out stills
# this repo's motion series
cd videos/motion-2026-11 && <video>/render.sh && .venv/bin/python shared/check.py
```
Gotchas: use `--workers 2` on an 8 GB Mac; in zsh write `${VAR}` before a `:` inside ffmpeg
filter strings; ElevenLabs phoneme tags work only on `eleven_turbo_v2` / `eleven_flash_v2`.

## Outside the repo
- `~/Desktop/reelkit/.env`: `ELEVENLABS_API_KEY` (copied from reel-forge `remotion/.env`),
  optional `ELEVENLABS_VOICE_ID`, `OPENAI_API_KEY`, `PIPER_MODEL`. Never print or commit it.
- Private Saban material in reelkit: `reels/_saban/` (photos, fonts, build scripts, footage,
  island outline) and every `reels/saban-*/`, excluded via `.git/info/exclude`.
- Source photos: `R_E_V/Saba realty website/From Dad/` (4032 px). WhatsApp 07.25.43 is
  St. Eustatius, not Saba: don't use it.
- `~/lemo-opuscar` (library) and its Claude plugin; synth kit at
  `videos/motion-2026-11/shared/synth.py` (used by the reelkit films' `mix.py`).
- Claude memory: `~/.claude/projects/-Users-nathanaeljohnson-GitHub-sabanrealty/memory/reelkit.md`.
