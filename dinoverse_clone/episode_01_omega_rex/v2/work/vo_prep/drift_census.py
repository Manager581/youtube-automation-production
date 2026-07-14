#!/usr/bin/env python
"""
BLAST RADIUS: per-clip F0 census across the whole Omega Rex episode.

Reuses the method already established in this directory:
  - stem_stats.py     : F0 measured on the demucs VOCALS stem, restricted to whisper
                        word windows (kills ambience/creature-call contamination).
  - octave_arbiter.py : wide-range pyin as the ESTIMATE, then the HARMONIC COMB as the
                        ARBITER, plus torchaudio autocorrelation as an independent
                        estimator. octave_arbiter.py explicitly warns that a narrow
                        fmin/fmax cannot settle an octave question because it FORCES
                        the answer -- so we keep pyin wide (60-500) and let the comb +
                        autocorrelation reject octave errors. We run those checks on
                        EVERY clip, not just suspected outliers.

Scope: every STORYBOARD row with Clip type == GEN and Status == clip whose Speaker is
LUKE (alone) or GF (alone). Mixed rows (LUKE / GF, GF / LUKE) are measured but held
OUT of the drift statistics -- two speakers in one clip legitimately show two F0s.
"""
import csv
import json
import os

import librosa
import numpy as np
import torch
import torchaudio
from faster_whisper import WhisperModel

ROOT = "/Users/jefflawrence/Documents/youtube-automation-production"
EP = f"{ROOT}/dinoverse_clone/episode_01_omega_rex"
BASE = f"{EP}/v2/work/vo_prep"
SEP = ("/private/tmp/claude-501/-Users-jefflawrence-Documents-youtube-automation-production"
       "/b21f8831-73ac-48b0-a1c0-457f8f7c71ca/scratchpad/sep/htdemucs")

SOLO = {"LUKE", "GF"}
MIXED = {"LUKE / GF", "GF / LUKE"}
NFFT = 8192          # 5.9 Hz resolution -> 120 vs 241 Hz cleanly resolved
OUTLIER_HZ = 25.0    # >|25| Hz from the character median = outlier (brief says 15-20 normal)

model = WhisperModel("small", device="cpu", compute_type="int8")


# --------------------------------------------------------------------------
def peak_at(mag, freqs, f, hw=15.0):
    sel = (freqs >= f - hw) & (freqs <= f + hw)
    return float(mag[sel].max()) if sel.any() else 0.0


def floor_at(mag, freqs, f, lo=40.0, hi=60.0):
    sel = ((freqs >= f - hi) & (freqs <= f - lo)) | ((freqs >= f + lo) & (freqs <= f + hi))
    return float(np.median(mag[sel])) + 1e-12 if sel.any() else 1e-12


def measure(shot, path_mix, path_voc):
    """Return F0 stats on the vocals stem inside whisper word windows."""
    segs, _ = model.transcribe(path_mix, word_timestamps=True, language="en")
    words = [{"w": w.word.strip(), "s": w.start, "e": w.end}
             for s in segs for w in (s.words or [])
             if any(c.isalnum() for c in w.word)]
    if not words:
        return {"shot": shot, "error": "no words transcribed"}

    voc, sr = librosa.load(path_voc, sr=None, mono=True)
    chunks = []
    for w in words:
        i0, i1 = max(0, int(w["s"] * sr)), min(len(voc), int(w["e"] * sr))
        if i1 - i0 > int(0.02 * sr):
            chunks.append(voc[i0:i1])
    if not chunks:
        return {"shot": shot, "error": "no usable word windows"}
    y = np.concatenate(chunks)
    if np.sqrt(np.mean(y ** 2)) < 1e-5:
        return {"shot": shot, "error": "vocals stem silent"}

    def pyin_med(fmin, fmax, fl=2048, hop=256):
        f0, _, _ = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=sr,
                                frame_length=fl, hop_length=hop)
        v = f0[~np.isnan(f0)]
        if v.size < 10:
            return float("nan"), 0, None
        return float(np.median(v)), int(v.size), v

    wide, nv, v = pyin_med(60, 500)
    if np.isnan(wide):
        return {"shot": shot, "error": f"too few voiced frames ({nv})"}
    nmale, _, _ = pyin_med(70, 250)     # narrow male band
    nfem, _, _ = pyin_med(140, 400)     # narrow female band

    # independent estimator: torchaudio autocorrelation (different failure mode)
    try:
        t = torch.tensor(y, dtype=torch.float32).unsqueeze(0)
        ta = torchaudio.functional.detect_pitch_frequency(
            t, sample_rate=sr, frame_time=0.02, freq_low=60, freq_high=500)
        tam = float(np.median(ta.numpy()))
    except Exception:
        tam = float("nan")

    # ARBITER: harmonic comb (does not share pyin's failure mode)
    S = np.abs(librosa.stft(y, n_fft=NFFT, hop_length=512, win_length=NFFT))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=NFFT)
    f0c, _, _ = librosa.pyin(y, fmin=60, fmax=500, sr=sr, frame_length=NFFT, hop_length=512)
    n = min(S.shape[1], len(f0c))
    Rs, atf0 = [], []
    for k in range(n):
        if np.isnan(f0c[k]):
            continue
        f, mag = float(f0c[k]), S[:, k]
        odd = np.mean([peak_at(mag, freqs, m * f) for m in (0.5, 1.5, 2.5)])
        inte = np.mean([peak_at(mag, freqs, m * f) for m in (1.0, 2.0, 3.0)])
        if inte > 0:
            Rs.append(odd / inte)
        atf0.append(peak_at(mag, freqs, f) / floor_at(mag, freqs, f))
    R = float(np.median(Rs)) if Rs else float("nan")
    snr = float(np.median(atf0)) if atf0 else float("nan")

    if not np.isnan(R) and R > 0.30:
        octv = f"OCTAVE-DOUBLED (true ~{wide/2:.0f} Hz)"
    elif not np.isnan(snr) and snr < 2.0:
        octv = f"possible HALVING (check {wide*2:.0f} Hz)"
    else:
        octv = "REAL (no octave error)"

    cent = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=2048, hop_length=256)[0]

    return {
        "shot": shot,
        "n_words": len(words),
        "f0_median": round(wide, 1),
        "f0_p25": round(float(np.percentile(v, 25)), 1),
        "f0_p75": round(float(np.percentile(v, 75)), 1),
        "pyin_narrow_male_70_250": round(nmale, 1) if not np.isnan(nmale) else None,
        "pyin_narrow_female_140_400": round(nfem, 1) if not np.isnan(nfem) else None,
        "torchaudio_autocorr": round(tam, 1) if not np.isnan(tam) else None,
        "R_half": round(R, 3) if not np.isnan(R) else None,
        "peak_over_floor": round(snr, 1) if not np.isnan(snr) else None,
        "octave_verdict": octv,
        "centroid": round(float(np.mean(cent))),
        "n_voiced_frames": nv,
        "transcript": " ".join(w["w"] for w in words),
    }


# --------------------------------------------------------------------------
rows = list(csv.DictReader(open(f"{EP}/STORYBOARD.tsv"), delimiter="\t"))
sel = []
for x in rows:
    if x["Clip type"] != "GEN" or x["Status"] != "clip":
        continue
    sp = x["Speaker"].strip()
    if sp not in SOLO and sp not in MIXED:
        continue
    shot = x["Shot"].strip()
    p = f"{EP}/v2/clips/{shot}.mp4"
    if os.path.exists(p):
        sel.append({"shot": shot, "speaker": sp, "scene": x["Scene"].strip(),
                    "dur": x["Dur"].strip(), "mix": p,
                    "voc": f"{SEP}/{shot}/vocals.wav",
                    "line": (x["Dialogue / VO"] or "").strip()})

print(f"selected {len(sel)} clips "
      f"({sum(1 for s in sel if s['speaker'] in SOLO)} solo, "
      f"{sum(1 for s in sel if s['speaker'] in MIXED)} mixed)")

results = []
for i, s in enumerate(sel, 1):
    r = measure(s["shot"], s["mix"], s["voc"])
    r.update({"speaker": s["speaker"], "scene": s["scene"],
              "dur_board": s["dur"], "line": s["line"],
              "is_mixed": s["speaker"] in MIXED})
    results.append(r)
    f0 = r.get("f0_median")
    print(f"  [{i:2d}/{len(sel)}] {s['shot']:6} {s['speaker']:10} "
          f"F0={f0 if f0 else 'ERR':>6} ta={r.get('torchaudio_autocorr')} "
          f"{r.get('octave_verdict','')}")

with open(f"{BASE}/_census_raw.json", "w") as fh:
    json.dump(results, fh, indent=2)
print(f"\nwrote {BASE}/_census_raw.json")
