#!/usr/bin/env python3
"""check.py <video dir>: ffprobe the output, then measure the picture and the sound against the timeline:
cuts land on planned frames, the frame is still while text is read, moves have no spikes, sound hits the cuts."""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.signal import stft
ROOT = Path(__file__).resolve().parent.parent
vid = Path(sys.argv[1]).resolve(); name = vid.name
tl = json.loads((vid / "timeline.json").read_text()); mp4 = ROOT / "output" / f"{name}.mp4"
p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp4)], capture_output=True, text=True).stdout)
v = next(s for s in p["streams"] if s["codec_type"] == "video"); a = next(s for s in p["streams"] if s["codec_type"] == "audio")
print(f"{name}: {v['codec_name']} {v['profile']} {v['width']}x{v['height']} {v['pix_fmt']} {v['r_frame_rate']} {v['nb_frames']} frames | {a['codec_name']} {a['sample_rate']} {int(a['bit_rate'])//1000}k {a['channels']}ch | format {float(p['format']['duration']):.3f}s video {float(v['duration']):.3f}s audio {float(a['duration']):.3f}s | {mp4.stat().st_size/1e6:.1f} MB")
atoms = mp4.read_bytes()[:4096]; print("faststart:", atoms.find(b"moov") < atoms.find(b"mdat") if b"mdat" in atoms else True)
e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
tail = e[e.rfind("Summary:"):]; print("loudness:", re.search(r"I:\s+(-?[\d.]+) LUFS", tail)[1], "LUFS, true peak", re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)[1], "dBFS")
w, h = 192, round(192 * tl["height"] / tl["width"])
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
d = np.abs(np.diff(f, axis=0)).mean((1, 2))
b = 60 / tl["bpm"]; acc = 0; cuts = []
for s in tl["shots"]:
    cuts.append((s["name"], acc * b)); acc += s["beats"]
print("frames:", len(f), "expected", round(acc * b * tl["fps"]))
found = [i + 1 for i in np.where(d > 8)[0]]
print("cut frames found:", found, "| planned:", [round(t * tl["fps"]) for _, t in cuts[1:]])
for (n, t0), nxt in zip(cuts, [c[1] for c in cuts[1:]] + [acc * b]):
    i0, i1 = round(t0 * tl["fps"]), round(nxt * tl["fps"]) - 1
    seg = d[i0:i1]
    still = np.where(seg < .06)[0]
    last_move = (np.where(seg >= .06)[0].max() + 1) / tl["fps"] if (seg >= .06).any() else 0
    jumps = np.abs(np.diff(seg)); print(f"  {n:9} {nxt - t0:5.2f}s  settled at +{last_move:4.2f}s, still for {nxt - t0 - last_move:4.2f}s, largest step between frames {jumps.max() if len(jumps) else 0:.3f}")
wav = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-ac", "1", "-ar", "24000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(wav, np.float32)
_, ts, Z = stft(x, 24000, nperseg=1024, noverlap=768)
flux = np.maximum(np.diff(np.abs(Z), axis=1), 0).sum(0)
thr = np.median(flux) * 4
for n, t in cuts:
    idx = np.where((ts[1:] >= t - .06) & (ts[1:] <= t + .08))[0]
    pk = flux[idx].max() / np.median(flux) if len(idx) else 0
    print(f"  onset at {n:9} t={t:6.2f}: {pk:5.1f}x median")
