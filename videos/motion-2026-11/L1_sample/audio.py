#!/usr/bin/env python3
"""L1 sample: 72 BPM piano and marimba, with a cue under every on screen event. Chords and event beats
come from timeline.json, so moving an event moves its sound."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from synth import Mix, finish, hz, marimba, ocean, pad, piano, timeline, whoosh

tl, b, shots, dur = timeline(HERE)
at = {k: v * b for k, v in tl["at"].items()}
m, rng = Mix(dur, tail=3), np.random.default_rng(72)
m.add(ocean(dur + 3, level=.01), 0, wet=0)

for sh in shots:
    t0, n = sh["t"], sh["beats"]
    notes = [hz(x) for x in sh["chord"]]
    for i, f in enumerate(notes):
        m.add(piano(f, .62 - .03 * i, 5), t0 + .008 * i, pan=-.25 + .1 * i, wet=.35)
    if sh["name"] == "end":
        m.add(pad(notes[:5], n * b + 1, vel=.13, swell=.5), t0, wet=.5)
        continue
    # Marimba runs on the eighths and keeps the picture moving.
    up = notes[1:] + notes[-2:0:-1]
    for k in range(1, int(n * 2)):
        v = (.46 if k % 2 == 0 else .32) * (.85 + .3 * rng.random())
        m.add(marimba(up[k % len(up)] * 2, v), t0 + k * b / 2, pan=.5 * np.sin(k * .9), wet=.3, gain=.75)

def click(t):
    m.add(marimba(hz("A6"), .5, .5), t, pan=.1, wet=.25, gain=.7)

# Title lines, each on a high piano note.
m.add(piano(hz("A5"), .55, 4), at["title1"], pan=-.15, wet=.5, gain=.8)
m.add(piano(hz("D6"), .55, 4), at["title2"], pan=.15, wet=.5, gain=.8)
# The card row slides in, then the photo grows into the gallery.
m.add(whoosh(1.0, vel=.07), at["row"] - .45, pan=.5, wet=.5)
m.add(whoosh(.8, vel=.06), at["click"] - .1, pan=-.3, wet=.5)
click(at["click"])
# Each check climbs a step, so the three read as one rising line.
for t, n in ((at["check1"], "F#5"), (at["thumb2"], "A5"), (at["thumb3"], "D6")):
    m.add(piano(hz(n), .6, 3), t + .2, pan=.2, wet=.5, gain=.85)
for k in ("thumb2", "thumb3"):
    click(at[k])
# The address lands on a final bright note.
m.add(whoosh(.7, vel=.05), at["out"] - .3, wet=.5)
m.add(piano(hz("D6"), .55, 4), at["site"], pan=.2, wet=.6, gain=.75)

finish(m.render(fade=.7), HERE)
