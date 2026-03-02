#!/usr/bin/env python3
"""
analyze_fern_sfx.py — Detect SFX / impact sounds at cut points in Fern videos.

Method:
  1. Load the mixed audio (.wav from audio_cache)
  2. Compute onset strength envelope (detects audio transients)
  3. At each cut timestamp, measure onset energy in a ±100ms window
  4. Compare against baseline (non-cut windows) to see if Fern uses SFX hits
  5. Classify SFX type by frequency band:
     - Impact/thud:  low-frequency burst (< 300 Hz)
     - Whoosh/sweep: broadband sweep with spectral centroid moving
     - Stinger:      tonal mid-high freq spike (> 1kHz)
     - Air/riser:    sustained high-freq buildup
  6. Output: SFX_FORMULA.json with timing, types, and loudness

Usage:
  venv/bin/python analyze_fern_sfx.py --all
  venv/bin/python analyze_fern_sfx.py --video-id aVA7aXOH1pk
"""

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np

AUDIO_CACHE = Path("analysis/fern/audio_cache")
FERN_DIR    = Path("analysis/fern")

# Window around each cut to inspect (seconds)
CUT_WINDOW_SEC = 0.10   # ±100ms

# SFX detection threshold: ratio of cut-window energy vs baseline
SFX_RATIO_THRESHOLD = 1.8   # cut must be 1.8× louder than baseline to count

# Frequency bands (Hz)
BAND_LOW   = (20, 300)
BAND_MID   = (300, 3000)
BAND_HIGH  = (3000, 20000)


# ---------------------------------------------------------------------------
# Audio loading
# ---------------------------------------------------------------------------

def load_audio(video_id: str, sr: int = 22050):
    path = AUDIO_CACHE / f"{video_id}.wav"
    if not path.exists():
        raise FileNotFoundError(f"Audio not found: {path}")
    audio, sr = librosa.load(str(path), sr=sr, mono=True)
    return audio, sr


# ---------------------------------------------------------------------------
# Onset / transient detection
# ---------------------------------------------------------------------------

def compute_onset_envelope(audio: np.ndarray, sr: int) -> tuple[np.ndarray, float]:
    """
    Compute onset strength envelope.
    Returns (envelope_array, hop_duration_sec)
    """
    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop_length)
    hop_dur = hop_length / sr
    return onset_env, hop_dur


def energy_in_window(audio: np.ndarray, sr: int, center_sec: float,
                     window_sec: float = CUT_WINDOW_SEC) -> float:
    """RMS energy in a time window around center_sec."""
    start = max(0, int((center_sec - window_sec) * sr))
    end   = min(len(audio), int((center_sec + window_sec) * sr))
    if end <= start:
        return 0.0
    chunk = audio[start:end]
    return float(np.sqrt(np.mean(chunk ** 2)))


def onset_strength_at(onset_env: np.ndarray, hop_dur: float, center_sec: float,
                      window_sec: float = CUT_WINDOW_SEC) -> float:
    """Max onset strength within a window around center_sec."""
    start_frame = max(0, int((center_sec - window_sec) / hop_dur))
    end_frame   = min(len(onset_env), int((center_sec + window_sec) / hop_dur))
    if end_frame <= start_frame:
        return 0.0
    return float(np.max(onset_env[start_frame:end_frame]))


# ---------------------------------------------------------------------------
# Frequency band analysis
# ---------------------------------------------------------------------------

def band_energy(audio: np.ndarray, sr: int, center_sec: float,
                band_hz: tuple[float, float], window_sec: float = 0.15) -> float:
    """Energy in a specific frequency band around a timestamp."""
    start = max(0, int((center_sec - window_sec) * sr))
    end   = min(len(audio), int((center_sec + window_sec) * sr))
    chunk = audio[start:end]
    if len(chunk) < 32:
        return 0.0

    n_fft = min(2048, len(chunk))
    spec = np.abs(np.fft.rfft(chunk, n=n_fft))
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)

    mask = (freqs >= band_hz[0]) & (freqs <= band_hz[1])
    return float(np.mean(spec[mask] ** 2)) if mask.any() else 0.0


def classify_sfx(audio: np.ndarray, sr: int, t: float) -> str:
    """
    Classify the SFX type at a given timestamp by frequency content.
    """
    low  = band_energy(audio, sr, t, BAND_LOW)
    mid  = band_energy(audio, sr, t, BAND_MID)
    high = band_energy(audio, sr, t, BAND_HIGH)
    total = low + mid + high + 1e-10

    low_pct  = low / total
    mid_pct  = mid / total
    high_pct = high / total

    if low_pct > 0.55:
        return "impact_thud"       # dominant low-freq → impact/punch
    elif high_pct > 0.45:
        return "stinger_hiss"      # dominant high-freq → stinger/air
    elif mid_pct > 0.60:
        return "tonal_stinger"     # dominant mid → musical stinger
    else:
        return "broadband_whoosh"  # spread across all → whoosh/sweep


# ---------------------------------------------------------------------------
# Main analysis per video
# ---------------------------------------------------------------------------

def analyze_video_sfx(video_id: str) -> dict:
    print(f"\n  Analyzing SFX: {video_id}")

    # Load audio
    audio, sr = load_audio(video_id)
    duration = len(audio) / sr
    print(f"    Audio: {duration/60:.1f}min @ {sr}Hz")

    # Load cut timestamps from timeline
    # Prefer complete timelines; among those prefer qwen-vl over gemini
    all_timelines = sorted((FERN_DIR / video_id).glob("timeline_hybrid_*.json"))
    timeline_path = next(
        (p for p in all_timelines
         if json.load(open(p)).get("complete") and
            len(json.load(open(p)).get("timeline", [])) > 0),
        None
    )
    if not timeline_path:
        print(f"    No complete timeline found for {video_id}")
        return {}

    timeline = json.load(open(timeline_path))

    cut_timestamps = [e["timestamp"] for e in timeline.get("timeline", [])]
    # Filter to valid range
    cut_timestamps = [t for t in cut_timestamps if CUT_WINDOW_SEC < t < duration - CUT_WINDOW_SEC]
    print(f"    Cut timestamps: {len(cut_timestamps)}")

    # Compute onset envelope
    onset_env, hop_dur = compute_onset_envelope(audio, sr)

    # Compute baseline: onset strength at 200 random non-cut times
    rng = np.random.default_rng(42)
    non_cut_times = rng.uniform(CUT_WINDOW_SEC, duration - CUT_WINDOW_SEC, 200).tolist()
    # Remove times near actual cuts
    non_cut_times = [
        t for t in non_cut_times
        if all(abs(t - c) > 0.5 for c in cut_timestamps)
    ]

    baseline_onset = np.mean([onset_strength_at(onset_env, hop_dur, t) for t in non_cut_times])
    baseline_energy = np.mean([energy_in_window(audio, sr, t) for t in non_cut_times])
    print(f"    Baseline onset strength: {baseline_onset:.3f}")
    print(f"    Baseline RMS energy:     {baseline_energy:.5f}")

    # Measure each cut
    cut_results = []
    sfx_at_cuts = 0
    sfx_types = []

    for t in cut_timestamps:
        onset_val  = onset_strength_at(onset_env, hop_dur, t)
        energy_val = energy_in_window(audio, sr, t)
        ratio      = onset_val / (baseline_onset + 1e-10)

        is_sfx = ratio >= SFX_RATIO_THRESHOLD
        sfx_type = None
        if is_sfx:
            sfx_type = classify_sfx(audio, sr, t)
            sfx_types.append(sfx_type)
            sfx_at_cuts += 1

        cut_results.append({
            "timestamp": round(t, 3),
            "onset_strength": round(float(onset_val), 3),
            "onset_ratio": round(float(ratio), 3),
            "rms_energy": round(float(energy_val), 6),
            "has_sfx": bool(is_sfx),
            "sfx_type": sfx_type,
        })

    sfx_pct = sfx_at_cuts / len(cut_timestamps) * 100 if cut_timestamps else 0
    from collections import Counter
    sfx_type_dist = dict(Counter(sfx_types).most_common())

    # Average SFX loudness above baseline
    sfx_ratios = [r["onset_ratio"] for r in cut_results if r["has_sfx"]]
    avg_sfx_ratio = float(np.mean(sfx_ratios)) if sfx_ratios else 0

    # Timing pattern: does SFX fire exactly ON the cut or just before/after?
    # Look at where in the ±100ms window the peak onset falls
    sfx_offsets = []
    for t in [r["timestamp"] for r in cut_results if r["has_sfx"]]:
        # Find peak onset frame within window
        start_f = max(0, int((t - CUT_WINDOW_SEC) / hop_dur))
        end_f   = min(len(onset_env), int((t + CUT_WINDOW_SEC) / hop_dur))
        window  = onset_env[start_f:end_f]
        if len(window) > 0:
            peak_frame = np.argmax(window)
            offset_sec = (peak_frame / len(window) - 0.5) * 2 * CUT_WINDOW_SEC
            sfx_offsets.append(float(offset_sec * 1000))  # ms

    avg_sfx_offset_ms = float(np.mean(sfx_offsets)) if sfx_offsets else 0

    result = {
        "video_id": video_id,
        "duration_sec": round(duration, 1),
        "total_cut_timestamps": len(cut_timestamps),
        "sfx_findings": {
            "cuts_with_sfx_pct": round(sfx_pct, 1),
            "sfx_type_distribution": sfx_type_dist,
            "avg_sfx_loudness_ratio_vs_baseline": round(avg_sfx_ratio, 2),
            "avg_sfx_peak_offset_ms": round(avg_sfx_offset_ms, 1),
            "sfx_ratio_threshold_used": SFX_RATIO_THRESHOLD,
            "verdict": _sfx_verdict(sfx_pct, sfx_type_dist),
        },
        "baseline": {
            "avg_onset_strength": round(float(baseline_onset), 3),
            "avg_rms_energy": round(float(baseline_energy), 6),
        },
        # First 20 cuts for inspection
        "sample_cuts": cut_results[:20],
    }

    print(f"    SFX at cuts: {sfx_pct:.1f}%")
    print(f"    SFX types:   {sfx_type_dist}")
    return result


def _sfx_verdict(sfx_pct: float, sfx_type_dist: dict) -> str:
    dominant = max(sfx_type_dist, key=sfx_type_dist.get) if sfx_type_dist else None
    if sfx_pct < 15:
        return "minimal_sfx: cuts are mostly audio-free"
    elif sfx_pct < 40:
        return f"selective_sfx: {sfx_pct:.0f}% of cuts have audio event — likely only on major narrative beats"
    elif sfx_pct < 70:
        return f"regular_sfx: {sfx_pct:.0f}% of cuts have audio event ({dominant})"
    else:
        return f"heavy_sfx: {sfx_pct:.0f}% of cuts have audio event ({dominant}) — every cut is accented"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Detect SFX at cut points in Fern videos")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--video-id", help="e.g. aVA7aXOH1pk")
    p.add_argument("--out", default="analysis/fern/FERN_SFX_FORMULA.json")
    args = p.parse_args()

    if args.all:
        video_ids = [p.stem.replace(".wav", "") for p in AUDIO_CACHE.glob("*.wav")]
        video_ids = [v for v in video_ids if (FERN_DIR / v).exists()]
    else:
        video_ids = [args.video_id]

    print(f"Analyzing SFX for {len(video_ids)} video(s)...")
    results = []
    for vid in sorted(video_ids):
        try:
            r = analyze_video_sfx(vid)
            if r:
                results.append(r)
        except Exception as e:
            print(f"  ERROR {vid}: {e}")

    if not results:
        print("No results.")
        sys.exit(1)

    # Aggregate across videos
    all_sfx_pcts = [r["sfx_findings"]["cuts_with_sfx_pct"] for r in results]
    from collections import Counter
    all_types = Counter()
    for r in results:
        all_types.update(r["sfx_findings"]["sfx_type_distribution"])

    aggregate = {
        "videos_analyzed": len(results),
        "per_video": results,
        "PRODUCTION_SPEC": {
            "cuts_with_sfx_pct":         round(float(np.mean(all_sfx_pcts)), 1),
            "dominant_sfx_type":         all_types.most_common(1)[0][0] if all_types else "none",
            "sfx_type_breakdown":        dict(all_types.most_common()),
            "avg_loudness_ratio":        round(float(np.mean([
                r["sfx_findings"]["avg_sfx_loudness_ratio_vs_baseline"] for r in results
            ])), 2),
            "verdict": results[0]["sfx_findings"]["verdict"] if results else "unknown",
            "assembler_guidance": _assembler_guidance(
                float(np.mean(all_sfx_pcts)),
                all_types.most_common(1)[0][0] if all_types else "none"
            ),
        }
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(aggregate, f, indent=2)

    print(f"\n{'='*60}")
    print(f"SFX FORMULA RESULTS")
    print(f"{'='*60}")
    spec = aggregate["PRODUCTION_SPEC"]
    print(f"  Cuts with SFX: {spec['cuts_with_sfx_pct']}%")
    print(f"  Dominant type: {spec['dominant_sfx_type']}")
    print(f"  Type breakdown: {spec['sfx_type_breakdown']}")
    print(f"  Verdict: {spec['verdict']}")
    print(f"  Guidance: {spec['assembler_guidance']}")
    print(f"\nSaved: {out}")


def _assembler_guidance(sfx_pct: float, dominant_type: str) -> str:
    if sfx_pct < 15:
        return "No SFX layer needed — cuts are clean audio transitions"
    elif sfx_pct < 40:
        return f"Add {dominant_type} SFX on ~{sfx_pct:.0f}% of cuts — major narrative beats only"
    else:
        return f"Add {dominant_type} SFX on every cut or most cuts ({sfx_pct:.0f}%)"


if __name__ == "__main__":
    main()
