#!/usr/bin/env python
"""
Turn the per-clip F0 census into the BLAST RADIUS report.

Outlier rule (from the brief): a real human's F0 median across takes moves maybe
+/-15-20 Hz; treat >|25| Hz from that character's median-of-medians as an outlier.

Two honest guards against overclaiming:
  1. SHOUTED / high-arousal lines genuinely raise F0 by a lot. They are measured and
     reported, but also broken out so the drift claim can be re-checked on the calm,
     conversational lines alone.
  2. Where pyin(60-500) and torchaudio autocorrelation disagree by >40 Hz, the estimate
     is marked low-confidence. The headline numbers are re-checked without them.
"""
import json
import os
import subprocess

import numpy as np

BASE = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep"
CUT = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut"

OUTLIER_HZ = 25.0
DISAGREE_HZ = 40.0

# lines the SCRIPT itself marks as shouted / panicked -> F0 legitimately jumps
SHOUTED = {"S76", "S78", "S81", "S84"}

rows = json.load(open(f"{BASE}/_census_raw.json"))

# ---- runtime of every clip as it actually sits in the cut -------------------
seg_dur = {}
for line in open(f"{CUT}/concat_list.txt"):
    p = line.strip().split("'")[1] if "'" in line else None
    if not p or not os.path.exists(p):
        continue
    shot = os.path.basename(p)[:-4]
    d = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
    seg_dur[shot] = float(d)
episode_s = float(subprocess.run(
    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0",
     f"{CUT}/rough_cut_v6.mp4"], capture_output=True, text=True).stdout.strip())

for r in rows:
    r["dur_in_cut_s"] = round(seg_dur.get(r["shot"], 0.0), 2)
    r["shouted"] = r["shot"] in SHOUTED
    ta = r.get("torchaudio_autocorr")
    r["pyin_vs_autocorr_hz"] = round(abs(r["f0_median"] - ta), 1) if ta else None
    r["low_confidence"] = bool(ta and abs(r["f0_median"] - ta) > DISAGREE_HZ)

solo = [r for r in rows if not r["is_mixed"] and "error" not in r]
mixed = [r for r in rows if r["is_mixed"]]


def block(name, rs):
    med = float(np.median([r["f0_median"] for r in rs]))
    for r in rs:
        r["dev_from_char_median"] = round(r["f0_median"] - med, 1)
        r["outlier"] = abs(r["f0_median"] - med) > OUTLIER_HZ
    v = [r["f0_median"] for r in rs]
    out = [r for r in rs if r["outlier"]]
    calm = [r for r in rs if not r["shouted"]]
    calm_out = [r for r in calm if r["outlier"]]
    hi = [r for r in rs if not r["low_confidence"]]
    hi_out = [r for r in hi if r["outlier"]]
    band = [r for r in rs if not r["outlier"]]
    return {
        "character": name,
        "n_clips": len(rs),
        "median_of_medians_hz": round(med, 1),
        "min_hz": round(min(v), 1),
        "max_hz": round(max(v), 1),
        "spread_hz": round(max(v) - min(v), 1),
        "stdev_hz": round(float(np.std(v)), 1),
        "n_outliers": len(out),
        "pct_outliers": round(100 * len(out) / len(rs), 1),
        "n_within_band": len(band),
        "outlier_shots": sorted([r["shot"] for r in out]),
        "calm_only": {"n": len(calm), "n_outliers": len(calm_out),
                      "pct": round(100 * len(calm_out) / len(calm), 1),
                      "min_hz": round(min(r["f0_median"] for r in calm), 1),
                      "max_hz": round(max(r["f0_median"] for r in calm), 1),
                      "spread_hz": round(max(r["f0_median"] for r in calm)
                                         - min(r["f0_median"] for r in calm), 1)},
        "high_confidence_only": {"n": len(hi), "n_outliers": len(hi_out),
                                 "pct": round(100 * len(hi_out) / len(hi), 1)},
        "runtime_s_total": round(sum(r["dur_in_cut_s"] for r in rs), 1),
        "runtime_s_outliers": round(sum(r["dur_in_cut_s"] for r in out), 1),
    }


luke = block("LUKE", [r for r in solo if r["speaker"] == "LUKE"])
gf = block("GF", [r for r in solo if r["speaker"] == "GF"])

# mixed clips: measured, but explicitly NOT counted as drift
for r in mixed:
    r["outlier"] = False
    r["dev_from_char_median"] = None
mv = [r["f0_median"] for r in mixed]

all_out = [r for r in solo if r["outlier"]]
solo_rt = sum(r["dur_in_cut_s"] for r in solo)
out_rt = sum(r["dur_in_cut_s"] for r in all_out)
dialogue_rt = solo_rt + sum(r["dur_in_cut_s"] for r in mixed)

worst = sorted(all_out, key=lambda r: -abs(r["dev_from_char_median"]))[:10]

report = {
    "scope": "CENSUS - every GEN/clip storyboard row whose Speaker is LUKE or GF "
             "(solo), plus all LUKE/GF mixed rows measured separately. Nothing sampled.",
    "method": {
        "source_files": "v2/clips/Sxx.mp4 - verified by waveform correlation (r=1.0) to be "
                        "the exact files in rough_cut_v6 segments; the _roll_* alternates "
                        "are NOT in the cut.",
        "isolation": "demucs --two-stems=vocals -n htdemucs -d cpu (all 63 clips)",
        "windows": "faster-whisper 'small' word timestamps; F0 measured only inside words",
        "estimator": "librosa.pyin 60-500 Hz on the vocals stem (median of voiced frames)",
        "arbiters_run_on_every_clip": "harmonic-comb R_half + torchaudio "
                                      "detect_pitch_frequency autocorrelation",
        "outlier_rule": f">|{OUTLIER_HZ}| Hz from that character's median-of-medians",
        "note_on_narrow_ranges": "octave_arbiter.py explicitly warns a narrow fmin/fmax "
                                 "cannot settle an octave question because it FORCES the "
                                 "answer. So pyin stays wide (60-500) and the harmonic comb "
                                 "+ autocorrelation reject octave errors instead.",
    },
    "episode_runtime_s": round(episode_s, 1),
    "dialogue_runtime_s": round(dialogue_rt, 1),
    "LUKE": luke,
    "GF": gf,
    "MIXED_two_speaker_clips_EXCLUDED_from_drift": {
        "n_clips": len(mixed),
        "shots": [r["shot"] for r in mixed],
        "f0_median_range_hz": [round(min(mv), 1), round(max(mv), 1)],
        "why_excluded": "two speakers in one clip legitimately produce two F0s; a spread "
                        "here is not evidence of drift",
        "octave_flags": [r["shot"] for r in mixed
                         if "DOUBLED" in r.get("octave_verdict", "")],
    },
    "blast_radius": {
        "solo_dialogue_clips": len(solo),
        "solo_outlier_clips": len(all_out),
        "pct_solo_clips_outlier": round(100 * len(all_out) / len(solo), 1),
        "solo_dialogue_runtime_s": round(solo_rt, 1),
        "outlier_runtime_s": round(out_rt, 1),
        "pct_solo_dialogue_runtime_outlier": round(100 * out_rt / solo_rt, 1),
        "pct_episode_runtime_outlier": round(100 * out_rt / episode_s, 1),
    },
    "worst_offenders": [
        {"shot": r["shot"], "speaker": r["speaker"], "scene": r["scene"],
         "f0_median": r["f0_median"], "dev_hz": r["dev_from_char_median"],
         "shouted": r["shouted"], "low_confidence": r["low_confidence"],
         "line": r["line"][:70]} for r in worst],
    "per_clip": sorted(rows, key=lambda r: (r["is_mixed"], r["speaker"], r["shot"])),
}

with open(f"{BASE}/voice_drift_census.json", "w") as fh:
    json.dump(report, fh, indent=2)

# ---- console ---------------------------------------------------------------
for b in (luke, gf):
    print(f"\n===== {b['character']} =====")
    print(f"  n={b['n_clips']}  median-of-medians={b['median_of_medians_hz']} Hz  "
          f"min={b['min_hz']}  max={b['max_hz']}  SPREAD={b['spread_hz']} Hz  "
          f"sd={b['stdev_hz']}")
    print(f"  outliers (>|25| Hz): {b['n_outliers']}/{b['n_clips']} "
          f"({b['pct_outliers']}%)  -> {b['outlier_shots']}")
    c = b["calm_only"]
    print(f"  calm/non-shouted only: {c['n_outliers']}/{c['n']} ({c['pct']}%), "
          f"range {c['min_hz']}-{c['max_hz']} (spread {c['spread_hz']} Hz)")
    h = b["high_confidence_only"]
    print(f"  high-confidence only : {h['n_outliers']}/{h['n']} ({h['pct']}%)")

br = report["blast_radius"]
print(f"\n===== BLAST RADIUS =====")
print(f"  solo clips outlier   : {br['solo_outlier_clips']}/{br['solo_dialogue_clips']} "
      f"({br['pct_solo_clips_outlier']}%)")
print(f"  outlier runtime      : {br['outlier_runtime_s']}s of "
      f"{br['solo_dialogue_runtime_s']}s solo dialogue "
      f"({br['pct_solo_dialogue_runtime_outlier']}%)")
print(f"  = {br['pct_episode_runtime_outlier']}% of the {report['episode_runtime_s']}s episode")
print(f"\n===== WORST OFFENDERS =====")
for w in report["worst_offenders"]:
    tag = " [SHOUTED]" if w["shouted"] else ""
    tag += " [low-conf]" if w["low_confidence"] else ""
    print(f"  {w['shot']:5} {w['speaker']:5} {w['f0_median']:6.1f} Hz  "
          f"({w['dev_hz']:+7.1f}){tag}  {w['line'][:48]}")
print(f"\nwrote {BASE}/voice_drift_census.json")
