#!/usr/bin/env python
"""
DECISIVE: per-shot F0 on the demucs-isolated VOCALS stem vs the BACKGROUND stem.

Competing hypotheses for the 135 Hz per-shot F0 spread in LUKE:
  (A) Grok generated a different voice per clip -> vocals stem will STILL show the
      spread (S40 ~145, S67 ~187, S21 ~269).
  (B) Native background audio (dino calls / music) is contaminating F0 -> vocals stem
      will COLLAPSE to a consistent value, and the background stem will show the
      high tonal F0 that was polluting the mix.

Also reports background loudness under each shot (RMS ratio), which tells the owner
how much creature noise sits under the dialogue.
"""
import json

import librosa
import numpy as np
from faster_whisper import WhisperModel

BASE = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep"
SEP = f"{BASE}/sep/htdemucs"

# shot boundaries are derived from the ORIGINAL mix transcript, then applied to stems
CFG = {
    "LUKE": {"mix": f"{BASE}/LUKE_sample.mp3", "stem": "LUKE_sample",
             "fmin": 60.0, "fmax": 400.0,
             "shots": [("S40", 18), ("S67", 17), ("S21", 16)]},
    "GF": {"mix": f"{BASE}/GF_sample.mp3", "stem": "GF_sample",
           "fmin": 70.0, "fmax": 500.0,
           "shots": [("S23", 12), ("S34", 8), ("S66", 8)]},
    "RANGER_ref": {"mix": f"{BASE}/S46_ranger_audio.mp3", "stem": "S46_ranger_audio",
                   "fmin": 60.0, "fmax": 400.0,
                   "shots": [("S46", 32)]},
}

model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}


def f0_stats(y, sr, wl, fmin, fmax):
    chunks = []
    for w in wl:
        i0, i1 = max(0, int(w["s"] * sr)), min(len(y), int(w["e"] * sr))
        if i1 - i0 > int(0.02 * sr):
            chunks.append(y[i0:i1])
    if not chunks:
        return None
    ys = np.concatenate(chunks)
    if np.sqrt(np.mean(ys**2)) < 1e-5:
        return None
    f0, _, _ = librosa.pyin(ys, fmin=fmin, fmax=fmax, sr=sr,
                            frame_length=2048, hop_length=256)
    v = f0[~np.isnan(f0)]
    if v.size < 10:
        return None
    cent = librosa.feature.spectral_centroid(y=ys, sr=sr, n_fft=2048, hop_length=256)[0]
    n = min(len(cent), len(f0))
    cv = cent[:n][~np.isnan(f0[:n])]
    return {
        "median": float(np.median(v)),
        "p10": float(np.percentile(v, 10)),
        "p90": float(np.percentile(v, 90)),
        "p25": float(np.percentile(v, 25)),
        "p75": float(np.percentile(v, 75)),
        "centroid": float(np.mean(cv)),
        "voiced_pct": float(100 * v.size / f0.size),
        "rms": float(np.sqrt(np.mean(ys**2))),
        "n_voiced": int(v.size),
    }


for name, cfg in CFG.items():
    print(f"\n================ {name} ================")
    segs, _ = model.transcribe(cfg["mix"], word_timestamps=True, language="en")
    words = [{"w": w.word.strip(), "s": w.start, "e": w.end}
             for s in segs for w in (s.words or [])
             if any(c.isalnum() for c in w.word)]

    voc, sr = librosa.load(f"{SEP}/{cfg['stem']}/vocals.wav", sr=None, mono=True)
    bg, _ = librosa.load(f"{SEP}/{cfg['stem']}/no_vocals.wav", sr=sr, mono=True)

    # split words into the known source shots by cumulative word count
    shots, i = [], 0
    for label, nw in cfg["shots"]:
        shots.append((label, words[i:i + nw]))
        i += nw
    if i != len(words):
        print(f"  NOTE: whisper found {len(words)} words, expected {i} -> "
              f"shot split may be off by {len(words)-i}")

    rows = []
    print(f"  {'shot':>6} {'words':>5} | {'VOCALS F0':>10} {'IQR':>13} {'cent':>6} | "
          f"{'BG F0':>7} {'BG/voc RMS':>10}")
    for label, wl in shots:
        if not wl:
            continue
        vs = f0_stats(voc, sr, wl, cfg["fmin"], cfg["fmax"])
        bs = f0_stats(bg, sr, wl, 60.0, 600.0)
        if vs is None:
            print(f"  {label:>6} {len(wl):>5} | vocals stem: too few voiced frames")
            continue
        ratio = (bs["rms"] / vs["rms"]) if bs else 0.0
        bgf0 = f"{bs['median']:.0f}" if bs else "-"
        print(f"  {label:>6} {len(wl):>5} | {vs['median']:>9.1f}  "
              f"{vs['p25']:>5.0f}-{vs['p75']:<5.0f} {vs['centroid']:>6.0f} | "
              f"{bgf0:>7} {ratio:>9.2f}")
        rows.append({"shot": label, "n_words": len(wl),
                     "vocals_f0_median": round(vs["median"], 1),
                     "vocals_f0_p25": round(vs["p25"], 1),
                     "vocals_f0_p75": round(vs["p75"], 1),
                     "vocals_centroid": round(vs["centroid"]),
                     "bg_f0_median": round(bs["median"], 1) if bs else None,
                     "bg_to_vocal_rms": round(ratio, 2)})

    # overall on vocals stem
    ov = f0_stats(voc, sr, words, cfg["fmin"], cfg["fmax"])
    meds = [r["vocals_f0_median"] for r in rows]
    spread = max(meds) - min(meds) if len(meds) > 1 else 0.0

    speech_s = sum(w["e"] - w["s"] for w in words)
    for prev, w in zip(words, words[1:]):
        g = w["s"] - prev["e"]
        if 0 < g <= 0.4:
            speech_s += g
    wps = len(words) / speech_s

    print(f"\n  VOCALS-STEM OVERALL: F0 median {ov['median']:.1f} Hz "
          f"(p10-p90 {ov['p10']:.1f}-{ov['p90']:.1f}, IQR {ov['p25']:.1f}-{ov['p75']:.1f})")
    print(f"  spectral centroid (voiced): {ov['centroid']:.0f} Hz")
    print(f"  speaking rate: {wps:.2f} w/s ({60*wps:.1f} wpm), "
          f"{len(words)} words / {speech_s:.2f}s speech")
    print(f"  per-shot spread on VOCALS: {spread:.1f} Hz -> "
          f"{'CONSISTENT (one voice)' if spread < 30 else 'STILL DRIFTING (different voices per clip)'}")

    out[name] = {
        "shots": rows,
        "vocals_overall": {k: (round(v, 1) if isinstance(v, float) else v)
                           for k, v in ov.items()},
        "per_shot_spread_hz": round(spread, 1),
        "n_words": len(words),
        "speech_only_s": round(speech_s, 2),
        "words_per_sec": round(wps, 2),
        "words_per_min": round(60 * wps, 1),
    }

with open(f"{BASE}/voice_acoustics_STEMS.json", "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\nWrote {BASE}/voice_acoustics_STEMS.json")
