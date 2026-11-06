#!/usr/bin/env python3
"""V1: 120 BPM marimba and steel pan, bright morning feel, an accent on every cut."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from synth import Mix, finish, hz, marimba, ocean, pad, piano, steelpan, timeline

tl, b, shots, dur = timeline(HERE)
m, rng = Mix(dur, tail=3), np.random.default_rng(120)
m.add(ocean(dur + 3, level=.012), 0, wet=0)
MELODY = {"exterior": [("C#6", 0), ("E6", 1.5), ("F#6", 3)], "interior": [("F#6", 0), ("E6", 1.5), ("D6", 3)],
          "detail": [("B5", 0), ("E6", 1.5), ("G#5", 3)]}

for sh in shots:
    t0, n, name = sh["t"], sh["beats"], sh["name"]
    notes = [hz(x) for x in sh["chord"]]
    # Every cut: bass and chord on the downbeat.
    m.add(marimba(notes[0], .95, 2.4), t0, wet=.2)
    for i, f in enumerate(notes[1:]):
        m.add(steelpan(f, .6), t0 + .006 * i, pan=-.3 + .25 * i, wet=.35, gain=.8)
    if name == "view":
        m.add(pad(notes[1:], n * b + .8, vel=.2, swell=.5), 0, wet=.5)
        for k, off in enumerate((4, 4.5, 5, 5.5)):   # lifts into the first cut as the hook clears
            m.add(marimba(notes[1 + k % 3] * 2, .5), t0 + off * b, pan=.3 - .2 * k, wet=.3)
    elif name in ("exterior", "interior", "detail"):
        up = notes[1:] + notes[-2:0:-1]
        for k in range(1, n * 2):
            m.add(marimba(up[k % len(up)] * 2, (.45 if k % 2 == 0 else .3) * (.85 + .3 * rng.random())), t0 + k * b / 2, pan=.5 * np.sin(k), wet=.25, gain=.8)
        for note, off in MELODY[name]:
            m.add(steelpan(hz(note), .7), t0 + off * b, pan=.2, wet=.4)
    elif name == "name":
        m.add(steelpan(hz("E6"), .7), t0, pan=.2, wet=.4)                 # name lands
        m.add(steelpan(hz("A5"), .8), t0 + b, pan=-.2, wet=.4)            # price lands
        m.add(steelpan(hz("C#6"), .7), t0 + 3 * b, pan=.2, wet=.4)        # link in bio
        for k in range(1, 12, 2):
            m.add(marimba(notes[1 + k % 3] * 2, .28), t0 + k * b / 2, pan=.4 * np.sin(k), wet=.3)
    elif name == "end":
        m.add(piano(hz("A4"), .55, 4), t0, wet=.4)
        m.add(pad(notes[1:], n * b + .8, vel=.14, swell=.4), t0, wet=.5)
        m.add(steelpan(hz("A6"), .5), t0 + 2 * b, wet=.6)

finish(m.render(fade=.7), HERE)
