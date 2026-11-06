#!/bin/bash
# Called by each video's render.sh with its own folder name.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; V="$1"; shift; cd "$ROOT"
.venv/bin/python shared/prep_photos.py "$V"
if [ "$1" = "--stills" ]; then exec node shared/render.mjs "$V" "$@"; fi
.venv/bin/python "$V/audio.py"
exec node shared/render.mjs "$V"
