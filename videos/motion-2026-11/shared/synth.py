"""Small additive instrument kit. Same seed, same audio: every mix is reproducible."""
import json, re, subprocess, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

def hz(n):
    m = re.fullmatch(r"([A-G])([#b]?)(-?\d)", n)
    semis = NOTE[m[1]] + {"#": 1, "b": -1, "": 0}[m[2]] + 12 * (int(m[3]) + 1)
    return 440 * 2 ** ((semis - 69) / 12)

def _t(dur): return np.arange(int(dur * SR)) / SR

def piano(f, vel=.7, dur=4.):
    t, out = _t(dur), 0
    tau0 = 3.2 * (261.6 / f) ** .45
    for n in range(1, 11):
        fn = n * f * np.sqrt(1 + .00035 * n * n)
        if fn > 16000: break
        a = vel ** (1 + .3 * n) / n ** 1.5
        tau = tau0 / (1 + .45 * (n - 1))
        env = .75 * np.exp(-t / tau) + .25 * np.exp(-t / (tau * .18))
        out = out + a * env * (np.sin(2 * np.pi * fn * t) + .6 * np.sin(2 * np.pi * fn * 1.0007 * t + .7))
    out = out * np.minimum(t / .004, 1) * np.minimum((dur - t) / .1, 1)
    return out * .35

def marimba(f, vel=.7, dur=1.8):
    t = _t(dur)
    tau = .75 * (261.6 / f) ** .55
    out = np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
    out += .28 * vel * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / (tau * .28))
    out += .05 * vel * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / (tau * .1))
    return vel * .5 * out * np.minimum(t / .005, 1) * np.minimum((dur - t) / .05, 1)

def steelpan(f, vel=.7, dur=2.2):
    t = _t(dur)
    trem = 1 + .05 * np.sin(2 * np.pi * 5.3 * t)
    out = np.sin(2 * np.pi * f * t) * np.exp(-t / .95)
    out += .55 * np.sin(2 * np.pi * f * 2.003 * t) * np.exp(-t / .6)
    out += .2 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / .3)
    return vel * .42 * trem * out * np.minimum(t / .009, 1) * np.minimum((dur - t) / .05, 1)

def pad(freqs, dur, vel=.3, swell=1.):
    t, out = _t(dur), 0
    for f in freqs:
        for d, ph in ((.998, 0), (1.002, 1.3)):
            out = out + np.sin(2 * np.pi * f * d * t + ph) + .18 * np.sin(4 * np.pi * f * d * t + ph)
    return vel * out / len(freqs) * np.minimum(t / swell, 1) * np.minimum((dur - t) / swell, 1) * .5

def ocean(dur, seed=7, level=.05):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros((n, 2))
    for c in range(2):
        low = sosfilt(butter(2, [90, 900], "band", fs=SR, output="sos"), r.standard_normal(n))
        hi = sosfilt(butter(2, [1500, 6000], "band", fs=SR, output="sos"), r.standard_normal(n))
        t = np.arange(n) / SR
        swell = .6 + .4 * np.sin(2 * np.pi * t / 9. + c * .8) * np.sin(2 * np.pi * t / 23. + 1.1)
        out[:, c] = level * swell * (low + .12 * np.maximum(swell - .6, 0) * hi)
    return out

def whoosh(dur=.9, seed=3, vel=.2):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    noise, x = r.standard_normal(n), np.linspace(0, 1, n)
    a = sosfilt(butter(2, [250, 1200], "band", fs=SR, output="sos"), noise)
    b = sosfilt(butter(2, [1200, 5000], "band", fs=SR, output="sos"), noise)
    env = np.sin(np.pi * x) ** 2 * x ** .6
    return vel * env * ((1 - x) * a + x * b)

class Mix:
    def __init__(self, dur, tail=0.):
        self.dur = dur
        self.dry = np.zeros((int((dur + tail) * SR), 2))
        self.send = np.zeros_like(self.dry)
    def add(self, sig, at, pan=0., wet=.3, gain=1.):
        i = int(round(at * SR))
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l, sig * r], 1) * 1.414
        sig = sig[: max(0, len(self.dry) - i)] * gain
        self.dry[i: i + len(sig)] += sig
        self.send[i: i + len(sig)] += sig * wet
    def render(self, fade=.5, room=2.1):
        r = np.random.default_rng(11)
        n = int(room * SR)
        env = np.exp(-np.arange(n) / SR / (room / 5))
        ir = sosfilt(butter(2, [180, 6500], "band", fs=SR, output="sos"), r.standard_normal((n, 2)), axis=0) * env[:, None]
        ir /= np.sqrt((ir ** 2).sum(0))
        wet = np.stack([fftconvolve(self.send[:, c], ir[:, c])[: len(self.send)] for c in range(2)], 1)
        out = (self.dry + wet)[: int(self.dur * SR)]
        k = int(fade * SR)
        out[-k:] *= np.cos(np.linspace(0, np.pi / 2, k))[:, None]
        return out

def _measure(path):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    tail = e[e.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail)[1]), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)[1])

def _write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def finish(x, vid, target=-15.):
    """Soft limit, gain to target LUFS, verify with ffmpeg's EBU R128 meter, write build/<video>/audio.wav."""
    vid = Path(vid).resolve()
    out = vid.parent / "build" / vid.name / "audio.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    x = x / np.abs(x).max()
    for _ in range(6):
        _write(out, x)
        lufs, peak = _measure(out)
        if abs(lufs - target) < .1 and peak <= -1.: break
        x = x * 10 ** ((target - lufs) / 20)
        knee = 10 ** (-3.5 / 20)
        over = np.abs(x) > knee
        x[over] = np.sign(x[over]) * (knee + (10 ** (-1.3 / 20) - knee) * np.tanh((np.abs(x[over]) - knee) / (10 ** (-1.3 / 20) - knee)))
    print(f"{vid.name}: {lufs:.1f} LUFS, true peak {peak:.1f} dBFS, {len(x) / SR:.2f}s")

def timeline(vid):
    tl = json.loads((Path(vid) / "timeline.json").read_text())
    b, s, acc = 60 / tl["bpm"], [], 0
    for sh in tl["shots"]:
        s.append({**sh, "t": acc * b}); acc += sh["beats"]
    return tl, b, s, acc * b
