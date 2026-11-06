# Motion videos, November 2026

Six marketing videos drawn on a canvas, frame by frame, from real listing photos.

## Change something, then re-render

| To change | Edit | Then run |
|---|---|---|
| Length or order of a shot (the music follows) | `<video>/timeline.json`, `beats` | `<video>/render.sh` |
| Chord on a shot | `<video>/timeline.json`, `chord` | `<video>/render.sh` |
| Camera move, copy, layout | `<video>/video.html` | `<video>/render.sh` |
| Which photo a shot uses | `<video>/timeline.json`, `photos` | `<video>/render.sh` |
| Instruments, melody | `<video>/audio.py` | `<video>/render.sh` |

`<video>/render.sh --stills 1.5,6.2` writes stills only, into `build/<video>/stills/`. Set `STILLS=name` to use a different folder.

`.venv/bin/python shared/check.py <video>` confirms codecs, duration and loudness, and that cuts land on the planned frames.

## Layout

- `<video>/` holds `timeline.json`, `video.html`, `audio.py`, `render.sh`.
- `shared/` holds the brand helpers, instrument kit, renderer and checks.
- `assets/`, `build/`, `output/` and `.venv/` are gitignored. `build/<video>/index.html` is the self contained page with fonts inlined.

## Setup on a new machine

```
npm install && npx playwright install chromium
python3 -m venv .venv && .venv/bin/pip install numpy scipy pillow
.venv/bin/python shared/fetch_assets.py the-mill cats-eye-cottage
```

`fetch_assets.py` prefers `~/Documents/sabanrealty-photo-originals-2026-10-03/`, falls back to R2 with a delay, and never refetches a file it already has.

## Rules the code enforces

- A camera path that leaves the photo stops the render, because clamping it would squash the ease into an abrupt move.
- A missing font or photo stops the render.
- Upscaling is plain Lanczos only. No generated or AI imagery.

## Before committing

This repo deploys to GitHub Pages. Add `videos/` to `exclude` in `_config.yml` if these sources get committed, or the pages will be published.
