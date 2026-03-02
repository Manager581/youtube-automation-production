#!/usr/bin/env python3
"""
analyze_fern_style_ground_truth.py

Answers the visual unknowns programmatically from actual Fern video frames.
No human eyes needed.

Questions answered:
  Q1. Does Fern EVER show text on a solid/dark background (no photo)?
      → Check non-text area of every text_on_screen=True frame

  Q2. What color(s) is the in-video text?
      → Sample bright pixel hues in text zones

  Q3. What happens at section transitions?
      → Brightness curve in 10 frames around each cut (fade vs hard cut)

  Q4. When no good image exists, what does Fern put on screen?
      → Find the lowest-visual-complexity frames, extract them, describe them

  Q5. Are there any full-screen motion graphics / animated elements?
      → Frames with zero feature points (can't be a photo) but non-black content

  Q6. Font weight estimate
      → Measure stroke width of bright text pixels

Usage:
  venv/bin/python analyze_fern_style_ground_truth.py --all
  venv/bin/python analyze_fern_style_ground_truth.py --video-id aVA7aXOH1pk

Output:
  analysis/fern/FERN_STYLE_GROUND_TRUTH.json  — verified answers
  analysis/fern/ground_truth_frames/          — sample frames for each finding
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

FERN_DIR  = Path("analysis/fern")
OUT_DIR   = FERN_DIR / "ground_truth_frames"
OUT_JSON  = FERN_DIR / "FERN_STYLE_GROUND_TRUTH.json"

# How many sample frames to save per question
MAX_SAMPLES = 8


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_complete_timeline(video_id: str) -> list:
    """Load the best complete timeline for a video."""
    vid_dir = FERN_DIR / video_id
    timelines = sorted(vid_dir.glob("timeline_hybrid_*.json"))
    for p in timelines:
        data = json.loads(p.read_text())
        if data.get("complete") and len(data.get("timeline", [])) > 0:
            return data.get("timeline", [])
    # Fallback: largest timeline even if not flagged complete
    best = max(timelines, key=lambda p: len(json.loads(p.read_text()).get("timeline", [])),
               default=None)
    if best:
        return json.loads(best.read_text()).get("timeline", [])
    return []


def get_frame(cap: cv2.VideoCapture, timestamp: float) -> np.ndarray | None:
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(timestamp * fps))
    ret, frame = cap.read()
    return frame if ret else None


def save_sample(frame: np.ndarray, label: str, index: int) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe = label.replace(" ", "_").replace("/", "-")[:40]
    path = OUT_DIR / f"{safe}_{index:03d}.jpg"
    cv2.imwrite(str(path), frame)
    return path


def image_complexity(frame: np.ndarray) -> float:
    """
    Laplacian variance — high = lots of detail (photo), low = flat/solid (text card).
    Photos: typically > 500. Solid color: < 50. Text on solid: 50–300.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def background_is_solid(frame: np.ndarray, text_zone_pct: float = 0.3) -> tuple[bool, float]:
    """
    Check if the non-text area of a frame is a near-solid dark color.
    Returns (is_solid, background_mean_brightness).

    Masks the bottom 30% (lower third, likely text zone) and checks the rest.
    """
    h, w = frame.shape[:2]
    # Use the upper 70% as "background" (excludes lower third text area)
    bg_region = frame[:int(h * (1 - text_zone_pct)), :]
    gray = cv2.cvtColor(bg_region, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(gray.mean())
    std_brightness = float(gray.std())
    # Solid dark: low mean AND low std (uniform dark)
    is_solid = mean_brightness < 40 and std_brightness < 20
    return is_solid, mean_brightness


def text_pixel_colors(frame: np.ndarray) -> dict:
    """
    Find the hue distribution of very bright pixels (the text itself).
    Returns counts per hue bucket.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    text_mask = gray > 200   # very bright = text
    if text_mask.sum() < 50:
        return {}

    hues = hsv[:, :, 0][text_mask]
    # Bucket into: white (S<30), red (H<10 or H>170), yellow (H 20-35), other
    sat = hsv[:, :, 1][text_mask]
    is_white  = (sat < 40).sum()
    is_red    = ((hues < 10) | (hues > 170)).sum() - is_white
    is_yellow = ((hues >= 20) & (hues <= 35)).sum()
    total = len(hues)
    return {
        "white_pct":  round(is_white  / total * 100, 1),
        "red_pct":    round(max(0, is_red)    / total * 100, 1),
        "yellow_pct": round(is_yellow / total * 100, 1),
        "total_text_pixels": int(total),
    }


def measure_text_stroke_width(frame: np.ndarray) -> float:
    """
    Estimate font stroke width by measuring the mean width of bright-pixel
    horizontal runs in text zones. Thin font: 2–4px. Bold: 6–12px.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    # Focus on lower third + upper strip (most text lives here)
    zones = [gray[:h//8, :], gray[h*2//3:, :]]
    widths = []
    for zone in zones:
        bright = (zone > 200).astype(np.uint8)
        for row in bright:
            in_run = False
            run_len = 0
            for px in row:
                if px:
                    in_run = True
                    run_len += 1
                elif in_run:
                    if 2 < run_len < 80:  # plausible text stroke width
                        widths.append(run_len)
                    in_run = False
                    run_len = 0
    return float(np.median(widths)) if widths else 0.0


def detect_transition_type(cap: cv2.VideoCapture, cut_ts: float) -> str:
    """
    Examine 5 frames before and after a cut timestamp.
    Returns: 'hard_cut' | 'fade_to_black' | 'fade_to_white' | 'unknown'
    """
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = 1.0 / fps

    brightnesses = []
    for offset in np.linspace(-0.4, 0.4, 10):
        t = cut_ts + offset
        if t < 0:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightnesses.append((t, float(gray.mean())))

    if len(brightnesses) < 4:
        return "unknown"

    vals = [b for _, b in brightnesses]
    min_b = min(vals)
    max_b = max(vals)

    # If any frame dips near black between two bright frames → fade to black
    if min_b < 15 and max_b > 40:
        return "fade_to_black"
    # If any frame goes near white
    if max_b > 220 and min_b < 180:
        return "fade_to_white"
    # If brightness difference across window is small → hard cut
    if max_b - min_b < 30:
        return "hard_cut"

    return "hard_cut"  # default


# ---------------------------------------------------------------------------
# Per-video analysis
# ---------------------------------------------------------------------------

def analyze_video(video_id: str) -> dict:
    print(f"\n  Analyzing: {video_id}")

    video_path = FERN_DIR / video_id / "video.mp4"
    if not video_path.exists():
        print(f"    Video not found: {video_path}")
        return {}

    timeline = load_complete_timeline(video_id)
    if not timeline:
        print(f"    No timeline found")
        return {}

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"    Cannot open video")
        return {}

    print(f"    Timeline: {len(timeline)} frames")

    # -----------------------------------------------------------------------
    # Q1: Does Fern use text-only frames (solid dark background, no photo)?
    # -----------------------------------------------------------------------
    print("    Q1: Checking for text-only frames (solid background)...")
    text_frames = [e for e in timeline if e.get("visual", {}).get("text_on_screen") is True]

    solid_bg_count = 0
    non_solid_count = 0
    solid_bg_samples = []
    non_solid_samples = []

    for entry in text_frames[:60]:  # sample up to 60 text frames
        frame = get_frame(cap, entry["timestamp"])
        if frame is None:
            continue
        is_solid, bg_brightness = background_is_solid(frame)
        complexity = image_complexity(frame)

        if is_solid:
            solid_bg_count += 1
            if len(solid_bg_samples) < MAX_SAMPLES:
                p = save_sample(frame, f"Q1_solid_bg_{video_id}", solid_bg_count)
                solid_bg_samples.append(str(p))
        else:
            non_solid_count += 1
            if len(non_solid_samples) < MAX_SAMPLES:
                p = save_sample(frame, f"Q1_photo_bg_{video_id}", non_solid_count)
                non_solid_samples.append(str(p))

    total_text = solid_bg_count + non_solid_count
    solid_pct = solid_bg_count / total_text * 100 if total_text > 0 else 0
    print(f"      Text frames: {total_text} | Solid dark bg: {solid_bg_count} ({solid_pct:.1f}%) | Photo bg: {non_solid_count}")

    # -----------------------------------------------------------------------
    # Q2: Text color distribution
    # -----------------------------------------------------------------------
    print("    Q2: Text color analysis...")
    color_totals = defaultdict(list)
    for entry in text_frames[:40]:
        frame = get_frame(cap, entry["timestamp"])
        if frame is None:
            continue
        colors = text_pixel_colors(frame)
        for k, v in colors.items():
            if k.endswith("_pct"):
                color_totals[k].append(v)

    text_colors = {
        k: round(float(np.mean(v)), 1)
        for k, v in color_totals.items()
        if v
    }
    print(f"      Text colors: {text_colors}")

    # -----------------------------------------------------------------------
    # Q3: Section transition types
    # -----------------------------------------------------------------------
    print("    Q3: Transition type detection...")
    cut_timestamps = [e["timestamp"] for e in timeline]

    transition_types = []
    for ts in cut_timestamps[:40]:
        t_type = detect_transition_type(cap, ts)
        transition_types.append(t_type)

    transition_dist = dict(Counter(transition_types).most_common())
    dominant_transition = transition_types[0] if transition_types else "unknown"
    if transition_dist:
        dominant_transition = max(transition_dist, key=transition_dist.get)
    print(f"      Transitions: {transition_dist}")

    # -----------------------------------------------------------------------
    # Q4: What's on screen during low-complexity sections?
    # -----------------------------------------------------------------------
    print("    Q4: Low-complexity frame analysis...")
    low_complexity_frames = []
    for entry in timeline:
        frame = get_frame(cap, entry["timestamp"])
        if frame is None:
            continue
        c = image_complexity(frame)
        low_complexity_frames.append((c, entry["timestamp"], frame))

    low_complexity_frames.sort(key=lambda x: x[0])

    low_comp_categories = []
    low_comp_samples = []
    for complexity, ts, frame in low_complexity_frames[:20]:
        is_solid, bg_b = background_is_solid(frame, text_zone_pct=0)  # whole frame
        has_text = any(e["timestamp"] == ts and
                       e.get("visual", {}).get("text_on_screen")
                       for e in timeline)

        if complexity < 50 and bg_b < 30:
            cat = "black_frame"
        elif complexity < 200 and is_solid:
            cat = "text_on_dark_bg"
        elif complexity < 300:
            cat = "near_solid_with_slight_texture"
        else:
            cat = "photo_with_text"

        low_comp_categories.append(cat)
        if len(low_comp_samples) < MAX_SAMPLES:
            p = save_sample(frame, f"Q4_low_complexity_{video_id}", len(low_comp_samples))
            low_comp_samples.append({"path": str(p), "complexity": round(complexity, 1),
                                     "category": cat, "timestamp": ts})

    low_comp_dist = dict(Counter(low_comp_categories).most_common())
    print(f"      Low-complexity categories: {low_comp_dist}")

    # -----------------------------------------------------------------------
    # Q5: Motion graphics / non-photographic frames
    # -----------------------------------------------------------------------
    print("    Q5: Detecting motion graphic / non-photo frames...")
    non_photo_count = 0
    non_photo_samples = []

    for entry in timeline:
        frame = get_frame(cap, entry["timestamp"])
        if frame is None:
            continue

        complexity = image_complexity(frame)
        is_solid, bg_b = background_is_solid(frame, text_zone_pct=0)

        # A motion graphic frame: not a black frame, not a photo,
        # but has structured content (complexity 100-600, non-solid)
        if 80 < complexity < 600 and bg_b > 20:
            # Check if it could be a photo by looking for natural color variation
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            sat_std = float(hsv[:, :, 1].std())
            if sat_std < 25 and not is_solid:
                # Low saturation std + not solid = probably animated/graphic
                non_photo_count += 1
                if len(non_photo_samples) < MAX_SAMPLES:
                    p = save_sample(frame, f"Q5_motion_graphic_{video_id}", non_photo_count)
                    non_photo_samples.append(str(p))

    total_analyzed = len([e for e in timeline])
    non_photo_pct = non_photo_count / total_analyzed * 100 if total_analyzed > 0 else 0
    print(f"      Potential motion graphic frames: {non_photo_count} ({non_photo_pct:.1f}%)")

    # -----------------------------------------------------------------------
    # Q6: Font weight (stroke width)
    # -----------------------------------------------------------------------
    print("    Q6: Estimating font stroke width...")
    stroke_widths = []
    for entry in text_frames[:20]:
        frame = get_frame(cap, entry["timestamp"])
        if frame is None:
            continue
        sw = measure_text_stroke_width(frame)
        if sw > 0:
            stroke_widths.append(sw)

    avg_stroke = float(np.median(stroke_widths)) if stroke_widths else 0
    # Interpret: <3px = thin, 3-5px = regular, 6-10px = bold, >10px = extra bold
    if avg_stroke < 3:
        font_weight = "thin"
    elif avg_stroke < 5:
        font_weight = "regular"
    elif avg_stroke < 9:
        font_weight = "bold"
    else:
        font_weight = "extra_bold"
    print(f"      Avg stroke width: {avg_stroke:.1f}px → {font_weight}")

    cap.release()

    return {
        "video_id": video_id,
        "Q1_text_on_solid_background": {
            "solid_dark_bg_pct": round(solid_pct, 1),
            "solid_dark_count": solid_bg_count,
            "photo_bg_count": non_solid_count,
            "verdict": "YES — Fern uses text-on-dark-bg frames" if solid_pct > 5
                       else "NO — text is always overlaid on photos",
            "sample_frames": solid_bg_samples,
        },
        "Q2_text_colors": {
            "distribution": text_colors,
            "dominant": max(text_colors, key=text_colors.get) if text_colors else "unknown",
        },
        "Q3_transition_types": {
            "distribution": transition_dist,
            "dominant": dominant_transition,
            "verdict": f"Fern primarily uses {dominant_transition}",
        },
        "Q4_low_complexity_frames": {
            "distribution": low_comp_dist,
            "sample_frames": low_comp_samples,
            "verdict": "black_frame" in low_comp_dist and
                       "text_on_dark_bg" in low_comp_dist and
                       "Fern does use text-on-dark for some content" or
                       "Content sections always have photo underneath",
        },
        "Q5_motion_graphics": {
            "detected_pct": round(non_photo_pct, 1),
            "sample_frames": non_photo_samples,
            "verdict": f"{non_photo_pct:.1f}% of frames appear to be non-photographic (potential motion graphics)",
        },
        "Q6_font_weight": {
            "avg_stroke_width_px": round(avg_stroke, 1),
            "classification": font_weight,
            "verdict": f"Text appears to be {font_weight} weight",
        },
    }


# ---------------------------------------------------------------------------
# Aggregation + production spec update
# ---------------------------------------------------------------------------

def aggregate(results: list[dict]) -> dict:
    """Merge per-video findings into a single ground truth spec."""

    # Q1: solid bg prevalence
    solid_pcts = [r["Q1_text_on_solid_background"]["solid_dark_bg_pct"] for r in results]
    avg_solid = float(np.mean(solid_pcts)) if solid_pcts else 0

    # Q2: text color
    color_votes = Counter()
    for r in results:
        dom = r["Q2_text_colors"].get("dominant", "")
        if dom:
            color_votes[dom] += 1

    # Q3: transitions
    trans_votes = Counter()
    for r in results:
        dom = r["Q3_transition_types"].get("dominant", "")
        if dom:
            trans_votes[dom] += 1

    # Q5: motion graphics
    mg_pcts = [r["Q5_motion_graphics"]["detected_pct"] for r in results]
    avg_mg = float(np.mean(mg_pcts)) if mg_pcts else 0

    # Q6: font weight
    fw_votes = Counter(r["Q6_font_weight"]["classification"] for r in results)

    return {
        "videos_analyzed": len(results),
        "VERIFIED_SPEC": {
            "text_on_solid_dark_background": {
                "avg_pct_of_text_frames": round(avg_solid, 1),
                "verdict": "YES — use text-on-dark frames" if avg_solid > 5 else
                           "NO — text is always on top of photos. Do NOT use bare text cards.",
                "implication": "When no image exists: find ANY related image rather than showing text alone"
                               if avg_solid < 5 else
                               "Text-on-dark-bg is valid in Fern's style for short moments",
            },
            "text_color": {
                "dominant": color_votes.most_common(1)[0][0] if color_votes else "unknown",
                "distribution": dict(color_votes),
            },
            "transition_style": {
                "dominant": trans_votes.most_common(1)[0][0] if trans_votes else "unknown",
                "distribution": dict(trans_votes),
                "implication": f"Use {trans_votes.most_common(1)[0][0] if trans_votes else 'hard_cut'} between segments",
            },
            "motion_graphics_usage": {
                "avg_pct": round(avg_mg, 1),
                "verdict": f"{'Significant' if avg_mg > 10 else 'Minimal'} motion graphics detected (~{avg_mg:.0f}% of frames)",
            },
            "font_weight": {
                "classification": fw_votes.most_common(1)[0][0] if fw_votes else "unknown",
                "distribution": dict(fw_votes),
            },
        },
        "per_video": results,
        "sample_frames_dir": str(OUT_DIR),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Verify Fern visual style from actual video frames")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--video-id")
    args = p.parse_args()

    if args.all:
        video_ids = [d.name for d in FERN_DIR.iterdir()
                     if d.is_dir() and (d / "video.mp4").exists()]
    else:
        video_ids = [args.video_id]

    print(f"Style Ground Truth Analyzer — {len(video_ids)} video(s)")
    print(f"Sample frames → {OUT_DIR}\n")

    results = []
    for vid in sorted(video_ids):
        try:
            r = analyze_video(vid)
            if r:
                results.append(r)
        except Exception as e:
            print(f"  ERROR {vid}: {e}")
            import traceback; traceback.print_exc()

    if not results:
        print("No results.")
        return

    aggregate_result = aggregate(results)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(aggregate_result, indent=2))

    spec = aggregate_result["VERIFIED_SPEC"]
    print(f"\n{'='*60}")
    print("VERIFIED STYLE GROUND TRUTH")
    print(f"{'='*60}")
    print(f"\nQ1 Text on solid dark background:")
    print(f"   {spec['text_on_solid_dark_background']['verdict']}")
    print(f"   Implication: {spec['text_on_solid_dark_background']['implication']}")
    print(f"\nQ2 Text color: {spec['text_color']['dominant']} "
          f"({spec['text_color']['distribution']})")
    print(f"\nQ3 Transitions: {spec['transition_style']['dominant']} "
          f"→ {spec['transition_style']['implication']}")
    print(f"\nQ5 Motion graphics: {spec['motion_graphics_usage']['verdict']}")
    print(f"\nQ6 Font weight: {spec['font_weight']['classification']}")
    print(f"\nSaved: {OUT_JSON}")
    print(f"Sample frames: {OUT_DIR}")
    print(f"\nOpen the sample frames folder to visually verify the findings.")


if __name__ == "__main__":
    main()
