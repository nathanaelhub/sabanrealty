#!/usr/bin/env python3
"""L1: 72 BPM piano and marimba, warm and reverent. Chords and cut points come from timeline.json,
so a change to the cuts moves the music with the picture."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from synth import Mix, finish, hz, marimba, ocean, pad, piano, timeline, whoosh

tl, b, shots, dur = timeline(HERE)
m, rng = Mix(dur, tail=3), np.random.default_rng(72)
m.add(ocean(dur + 3, level=.012), 0, wet=0)

for sh in shots:
    t0, n = sh["t"], sh["beats"]
    notes = [hz(x) for x in sh["chord"]]
    if sh["name"] == "title":
        m.add(pad(notes[:4], 2 * b + 1, vel=.2, swell=1.2), 0, wet=.5)
    else:
        # Every cut lands on a low piano chord.
        for i, f in enumerate(notes):
            m.add(piano(f, .62 - .03 * i, 5), t0 + .008 * i, pan=-.25 + .1 * i, wet=.35)
    tb = t0 + sh["text_beat"] * b
    if sh["name"] != "end":
        # Text arrives on a single high piano note, marimba underneath.
        m.add(piano(notes[-1] * 2, .55, 4), tb, pan=.2, wet=.5, gain=.8)
        m.add(marimba(notes[-1], .7), tb, pan=-.1, wet=.3)
    if sh["name"] not in ("title", "end"):
        # Gentle marimba arpeggio on the eighths, resting as the text is read.
        up = notes[1:] + notes[-2:0:-1]
        for k in range(int(n * 2)):
            at = t0 + k * b / 2
            if k == 0: continue
            v = (.42 if k % 2 == 0 else .3) * (.85 + .3 * rng.random())
            if at >= tb: v *= .65
            m.add(marimba(up[k % len(up)] * 2, v), at, pan=.5 * np.sin(k * .9), wet=.3, gain=.75)
    if sh["name"] == "hero":
        m.add(whoosh(1.0, vel=.05), t0 + 3 * b - .55, pan=.5, wet=.5)
    if sh["name"] == "end":
        m.add(pad([hz("D3"), hz("A3"), hz("F#4")], n * b + 1, vel=.14, swell=.5), t0, wet=.5)
        m.add(piano(hz("D6"), .5, 4), t0 + b, pan=.2, wet=.6, gain=.6)

finish(m.render(fade=.7), HERE)
