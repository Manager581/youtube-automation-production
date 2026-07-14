#!/usr/bin/env python
"""
Definitive speaking rate: per SOURCE SHOT, words / (last_word_end - first_word_start).
This includes natural intra-sentence pauses (part of the delivery) but excludes the
inter-shot silences (an artifact of concatenating three clips into one sample).

Also reported: the cruder energy-gate rate, for comparison.
"""
import json

import librosa
import numpy as np
from faster_whisper import WhisperModel

BASE = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep"
CFG = {
    "LUKE": (f"{BASE}/LUKE_sample.mp3", [("S40", 18), ("S67", 17), ("S21", 16)]),
    "GF": (f"{BASE}/GF_sample.mp3", [("S23", 12), ("S34", 8), ("S66", 8)]),
}

model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}

for name, (path, shots) in CFG.items():
    segs, _ = model.transcribe(path, word_timestamps=True, language="en")
    words = [{"w": w.word.strip(), "s": w.start, "e": w.end}
             for s in segs for w in (s.words or [])
             if any(c.isalnum() for c in w.word)]

    y, sr = librosa.load(path, sr=None, mono=True)
    iv = librosa.effects.split(y, top_db=30, frame_length=2048, hop_length=512)
    gate_s = sum((b - a) for a, b in iv) / sr

    print(f"\n=== {name} ===")
    i, rows, tot_w, tot_span = 0, [], 0, 0.0
    for label, nw in shots:
        wl = words[i:i + nw]
        i += nw
        if not wl:
            continue
        span = wl[-1]["e"] - wl[0]["s"]
        rate = len(wl) / span
        rows.append({"shot": label, "words": len(wl), "span_s": round(span, 2),
                     "wps": round(rate, 2), "wpm": round(60 * rate, 1)})
        tot_w += len(wl)
        tot_span += span
        print(f"  {label}: {len(wl):>2} words / {span:5.2f}s = {rate:.2f} w/s ({60*rate:5.1f} wpm)")

    ov = tot_w / tot_span
    gate_rate = len(words) / gate_s
    print(f"  ---")
    print(f"  PER-SHOT (definitive): {tot_w} words / {tot_span:.2f}s = "
          f"{ov:.2f} w/s ({60*ov:.1f} wpm)")
    print(f"  energy-gate (top_db=30, for comparison): {len(words)} words / {gate_s:.2f}s = "
          f"{gate_rate:.2f} w/s ({60*gate_rate:.1f} wpm)")
    out[name] = {"per_shot": rows,
                 "overall_wps": round(ov, 2), "overall_wpm": round(60 * ov, 1),
                 "energy_gate_wps": round(gate_rate, 2),
                 "energy_gate_wpm": round(60 * gate_rate, 1)}

with open(f"{BASE}/speaking_rate_FINAL.json", "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\nWrote {BASE}/speaking_rate_FINAL.json")
