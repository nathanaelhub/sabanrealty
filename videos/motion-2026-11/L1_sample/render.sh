#!/bin/bash
# render.sh [--stills 1.5,6.2]   Writes the music once per run, then renders. Stills skip the music.
set -e
cd "$(dirname "$0")/.."
[[ "$1" == "--stills" ]] || .venv/bin/python L1_sample/audio.py
node shared/render.mjs L1_sample "$@"
