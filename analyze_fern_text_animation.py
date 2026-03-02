#!/usr/bin/env python3
"""
analyze_fern_text_animation.py — Measure text animation parameters from Fern videos.

No OCR needed. Method:
  1. From the timeline, find timestamps where text_on_screen transitions
     False → True (text appears) or True → False (text disappears)
  2. Extract video frames at 15fps in a ±1.5s window around each transition
  3. Measure pixel brightness in the "text zones" (lower third + upper safe area)
     across consecutive frames
  4. Fit the brightness curve to detect:
     - Fade-in: smooth brightness increase over N frames → duration in ms
     - Cut-in: sudden full brightness in 1 frame → instant
     - Slide-in: spatial shift of bright pixels (text moves into frame)
  5. Also measure: text position (upper/lower/center), text color, hold duration

Usage:
  venv/bin/python analyze_fern_text_animation.py --all
  venv/bin/python analyze_fern_text_animation.py --video-id aVA7aXOH1pk
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

FERN_DIR = Path("analysis/fern")
EXTRACT_FPS = 15          # frames per second to extract around text transitions
WINDOW_SEC  = 1.5         # seconds before/after transition to extract
BRIGHTNESS_THRESHOLD = 220  # pixel value considered "bright" (text is usually white)


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def extract_frames_around(cap: cv2.VideoCapture, center_sec: float,
                          video_fps: float, window_sec: float = WINDOW_SEC,
                          target_fps: float = EXTRACT_FPS) -> list[tuple[float, np.ndarray]]:
    """Extract frames at target_fps in a window around center_sec."""
    interval = 1.0 / target_fps
    times = [center_sec + (i * interval)
             for i in range(-int(window_sec / interval), int(window_sec / interval) + 1)]

    frames = []
    for t in times:
        if t < 0:
            continue
        frame_idx = int(t * video_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frames.append((round(t, 3), frame))
    return frames


# ---------------------------------------------------------------------------
# Text zone analysis
# ---------------------------------------------------------------------------

def get_text_zones(frame: np.ndarray) -> dict[str, np.ndarray]:
    """Split frame into text-likely zones: upper strip, lower third, center."""
    h, w = frame.shape[:2]
    return {
        "upper":  frame[:h // 8, :],          # top 12.5% (title/chapter cards)
        "lower":  frame[h * 2 // 3:, :],       # bottom 33% (lower thirds, captions)
        "center": frame[h // 3: h * 2 // 3, :], # middle third (name cards, quotes)
    }


def brightness_score(region: np.ndarray) -> float:
    """Mean brightness of very bright pixels (text detection heuristic)."""
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY).astype(np.float32)
    bright_mask = gray > BRIGHTNESS_THRESHOLD
    if bright_mask.sum() < 10:
        return 0.0
    return float(gray[bright_mask].mean() * bright_mask.mean())


def horizontal_spread(region: np.ndarray) -> float:
    """
    Compute the horizontal spread of bright pixels.
    Rising spread across frames = slide-in animation.
    """
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    bright = gray > BRIGHTNESS_THRESHOLD
    cols_with_text = np.where(bright.any(axis=0))[0]
    if len(cols_with_text) < 2:
        return 0.0
    return float(cols_with_text[-1] - cols_with_text[0]) / region.shape[1]


# ---------------------------------------------------------------------------
# Animation type classifier
# ---------------------------------------------------------------------------

def classify_animation(brightness_curve: list[float], frame_times: list[float]) -> dict:
    """
    Given brightness scores over time, classify the animation type and duration.
    brightness_curve: list of float (brightness score per frame)
    frame_times: list of float (timestamp in seconds per frame)
    """
    if len(brightness_curve) < 3:
        return {"type": "unknown", "duration_ms": 0}

    # Normalize
    peak = max(brightness_curve) or 1.0
    norm = [b / peak for b in brightness_curve]

    # Find the transition region: where brightness goes from <20% to >80%
    low_idx = next((i for i, v in enumerate(norm) if v < 0.2), None)
    high_idx = next((i for i, v in enumerate(norm) if v > 0.8), None)

    if low_idx is None or high_idx is None or high_idx <= low_idx:
        # No clear transition found — text might already be visible
        return {"type": "already_visible", "duration_ms": 0}

    # Duration of the transition
    duration_ms = (frame_times[high_idx] - frame_times[low_idx]) * 1000

    # If transition happens in 1 frame → cut-in (instant)
    if high_idx - low_idx <= 1:
        return {"type": "cut_in", "duration_ms": round(duration_ms, 0)}

    # Check if transition is smooth (fade) or stepped (slide)
    transition_values = norm[low_idx:high_idx + 1]
    diffs = [abs(transition_values[i + 1] - transition_values[i])
             for i in range(len(transition_values) - 1)]

    if diffs:
        max_step = max(diffs)
        avg_step = sum(diffs) / len(diffs)
        # If one step is much larger than others → probably a slide with reveal
        if max_step > 3 * avg_step:
            return {"type": "slide_reveal", "duration_ms": round(duration_ms, 0)}
        else:
            return {"type": "fade_in", "duration_ms": round(duration_ms, 0)}

    return {"type": "fade_in", "duration_ms": round(duration_ms, 0)}


def classify_disappear(brightness_curve: list[float], frame_times: list[float]) -> dict:
    """Same but for text disappearing."""
    if len(brightness_curve) < 3:
        return {"type": "unknown", "duration_ms": 0}
    peak = max(brightness_curve) or 1.0
    norm = [b / peak for b in brightness_curve]

    # Find where brightness drops from >80% to <20%
    high_idx = next((i for i, v in enumerate(norm) if v > 0.8), None)
    low_idx  = next((i for i, v in enumerate(norm[high_idx or 0:], start=high_idx or 0)
                     if v < 0.2), None) if high_idx is not None else None

    if high_idx is None or low_idx is None or low_idx <= high_idx:
        return {"type": "unknown", "duration_ms": 0}

    duration_ms = (frame_times[low_idx] - frame_times[high_idx]) * 1000
    if low_idx - high_idx <= 1:
        return {"type": "cut_out", "duration_ms": round(duration_ms, 0)}
    return {"type": "fade_out", "duration_ms": round(duration_ms, 0)}


# ---------------------------------------------------------------------------
# Find text transitions in timeline
# ---------------------------------------------------------------------------

def find_text_transitions(timeline_entries: list[dict]) -> list[dict]:
    """
    Find moments where text_on_screen changes value.
    Returns list of {timestamp, direction: 'appear'|'disappear', zone_hint, prev_ts}.
    """
    transitions = []
    prev_has_text = None
    prev_ts = 0

    for entry in timeline_entries:
        v = entry.get("visual", {})
        has_text = v.get("text_on_screen") is True
        ts = entry["timestamp"]

        if prev_has_text is not None and has_text != prev_has_text:
            direction = "appear" if has_text else "disappear"
            transitions.append({
                "timestamp": ts,
                "direction": direction,
                "prev_timestamp": prev_ts,
                "gap_sec": round(ts - prev_ts, 3),
                "text_content": v.get("text_content", "") if has_text else "",
                "text_style": v.get("text_style", ""),
            })

        prev_has_text = has_text
        prev_ts = ts

    return transitions


def measure_text_hold_durations(timeline_entries: list[dict]) -> list[float]:
    """Measure how long text stays on screen between appear/disappear."""
    durations = []
    text_start = None

    for entry in timeline_entries:
        v = entry.get("visual", {})
        has_text = v.get("text_on_screen") is True
        ts = entry["timestamp"]

        if has_text and text_start is None:
            text_start = ts
        elif not has_text and text_start is not None:
            durations.append(round(ts - text_start, 2))
            text_start = None

    return durations


# ---------------------------------------------------------------------------
# Main analysis per video
# ---------------------------------------------------------------------------

def analyze_video_text(video_id: str) -> dict:
    print(f"\n  Analyzing text animation: {video_id}")

    video_path = FERN_DIR / video_id / "video.mp4"
    if not video_path.exists():
        print(f"    Video not found: {video_path}")
        return {}

    # Prefer complete timelines
    all_timelines = sorted((FERN_DIR / video_id).glob("timeline_hybrid_*.json"))
    timeline_path = next(
        (p for p in all_timelines
         if json.load(open(p)).get("complete") and
            len(json.load(open(p)).get("timeline", [])) > 0),
        None
    )
    if not timeline_path:
        print(f"    No complete timeline found")
        return {}

    timeline_data = json.load(open(timeline_path))

    timeline_entries = timeline_data.get("timeline", [])

    # Find text transitions
    transitions = find_text_transitions(timeline_entries)
    appear_transitions = [t for t in transitions if t["direction"] == "appear"]
    disappear_transitions = [t for t in transitions if t["direction"] == "disappear"]
    hold_durations = measure_text_hold_durations(timeline_entries)

    print(f"    Text appears: {len(appear_transitions)}×  disappears: {len(disappear_transitions)}×")
    print(f"    Avg hold duration: {np.mean(hold_durations):.2f}s" if hold_durations else "    No hold data")

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"    Cannot open video")
        return {}
    video_fps = cap.get(cv2.CAP_PROP_FPS)

    # Analyze up to 30 appear transitions
    appear_results = []
    for trans in appear_transitions[:30]:
        t = trans["timestamp"]
        frames = extract_frames_around(cap, t, video_fps, window_sec=1.0)
        if len(frames) < 3:
            continue

        # Measure brightness in each zone across frames
        zone_results = {}
        for zone_name in ["upper", "lower", "center"]:
            brightness_curve = []
            frame_times_local = []
            for ts, frame in frames:
                zones = get_text_zones(frame)
                brightness_curve.append(brightness_score(zones[zone_name]))
                frame_times_local.append(ts)

            if max(brightness_curve) > 1.0:  # some text brightness detected
                anim = classify_animation(brightness_curve, frame_times_local)
                zone_results[zone_name] = anim

        # Best zone = the one with the longest detected animation
        best_zone = None
        best_dur = -1
        for zone, anim in zone_results.items():
            if anim.get("duration_ms", 0) > best_dur:
                best_dur = anim.get("duration_ms", 0)
                best_zone = zone

        if best_zone:
            appear_results.append({
                "timestamp": t,
                "zone": best_zone,
                "animation": zone_results[best_zone],
                "text_content": trans.get("text_content", "")[:80],
            })

    cap.release()

    # Aggregate animation types
    appear_types = [r["animation"]["type"] for r in appear_results if r.get("animation")]
    appear_type_dist = dict(Counter(appear_types).most_common())

    fade_durations = [r["animation"]["duration_ms"] for r in appear_results
                      if r.get("animation", {}).get("type") == "fade_in"]
    avg_fade_ms = float(np.mean(fade_durations)) if fade_durations else 0

    zone_dist = dict(Counter(r["zone"] for r in appear_results).most_common())

    result = {
        "video_id": video_id,
        "text_stats": {
            "appear_events": len(appear_transitions),
            "disappear_events": len(disappear_transitions),
            "avg_hold_duration_sec": round(float(np.mean(hold_durations)), 2) if hold_durations else 0,
            "min_hold_duration_sec": round(float(min(hold_durations)), 2) if hold_durations else 0,
            "max_hold_duration_sec": round(float(max(hold_durations)), 2) if hold_durations else 0,
        },
        "animation": {
            "appear_type_distribution": appear_type_dist,
            "dominant_appear_type": appear_types[0] if appear_types else "unknown",
            "avg_fade_in_duration_ms": round(avg_fade_ms, 0),
            "zone_distribution": zone_dist,
            "dominant_zone": max(zone_dist, key=zone_dist.get) if zone_dist else "unknown",
        },
        "sample_events": appear_results[:10],
    }

    print(f"    Appear types: {appear_type_dist}")
    print(f"    Avg fade-in: {avg_fade_ms:.0f}ms")
    print(f"    Zone distribution: {zone_dist}")
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Measure text animation from Fern videos")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--video-id")
    p.add_argument("--out", default="analysis/fern/FERN_TEXT_ANIMATION_FORMULA.json")
    args = p.parse_args()

    if args.all:
        video_ids = [d.name for d in FERN_DIR.iterdir()
                     if d.is_dir() and (d / "video.mp4").exists()]
    else:
        video_ids = [args.video_id]

    print(f"Analyzing text animation for {len(video_ids)} video(s)...")
    results = []
    for vid in sorted(video_ids):
        try:
            r = analyze_video_text(vid)
            if r:
                results.append(r)
        except Exception as e:
            print(f"  ERROR {vid}: {e}")
            import traceback; traceback.print_exc()

    if not results:
        print("No results.")
        sys.exit(1)

    # Aggregate
    all_appear_types = Counter()
    all_zone_dists   = Counter()
    for r in results:
        all_appear_types.update(r["animation"]["appear_type_distribution"])
        all_zone_dists.update(r["animation"]["zone_distribution"])

    fade_durations_all = [r["animation"]["avg_fade_in_duration_ms"]
                          for r in results if r["animation"]["avg_fade_in_duration_ms"] > 0]
    hold_durations_all = [r["text_stats"]["avg_hold_duration_sec"] for r in results]

    aggregate = {
        "videos_analyzed": len(results),
        "per_video": results,
        "PRODUCTION_SPEC": {
            "dominant_appear_animation": all_appear_types.most_common(1)[0][0] if all_appear_types else "unknown",
            "appear_type_breakdown": dict(all_appear_types.most_common()),
            "avg_fade_in_ms": round(float(np.mean(fade_durations_all)), 0) if fade_durations_all else 0,
            "dominant_text_zone": all_zone_dists.most_common(1)[0][0] if all_zone_dists else "unknown",
            "zone_breakdown": dict(all_zone_dists.most_common()),
            "avg_text_hold_sec": round(float(np.mean(hold_durations_all)), 2) if hold_durations_all else 0,
            "assembler_guidance": "",  # filled below
        }
    }

    spec = aggregate["PRODUCTION_SPEC"]
    anim_type = spec["dominant_appear_animation"]
    fade_ms = spec["avg_fade_in_ms"]
    zone = spec["dominant_text_zone"]
    hold = spec["avg_text_hold_sec"]
    spec["assembler_guidance"] = (
        f"Use {anim_type} for text appearance ({fade_ms:.0f}ms duration). "
        f"Place text primarily in {zone} zone. "
        f"Hold text for avg {hold:.1f}s before removing."
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(aggregate, f, indent=2)

    print(f"\n{'='*60}")
    print(f"TEXT ANIMATION FORMULA")
    print(f"{'='*60}")
    print(f"  Dominant animation: {spec['dominant_appear_animation']}")
    print(f"  Appear types:       {spec['appear_type_breakdown']}")
    print(f"  Avg fade-in:        {spec['avg_fade_in_ms']}ms")
    print(f"  Dominant zone:      {spec['dominant_text_zone']}")
    print(f"  Avg text hold:      {spec['avg_text_hold_sec']}s")
    print(f"  Guidance: {spec['assembler_guidance']}")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
