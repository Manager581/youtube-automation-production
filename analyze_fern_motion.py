#!/usr/bin/env python3
"""
analyze_fern_motion.py — Measure actual production dynamics from Fern video files.

Uses OpenCV feature tracking to measure:
  - Ken Burns zoom speed and direction (zoom-in vs zoom-out)
  - Pan direction and speed
  - Motion intensity per segment
  - Cut timing relative to music beats
  - Color grade intensity (not just type)

Usage:
  venv/bin/python analyze_fern_motion.py --video analysis/fern/aVA7aXOH1pk/video.mp4
  venv/bin/python analyze_fern_motion.py --all        # all 3 videos
"""

import argparse
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SAMPLE_FPS      = 5      # frames per second to sample within a segment
MIN_SEG_SECS    = 0.4    # ignore segments shorter than this
MIN_FEATURES    = 20     # need at least this many feature matches to trust the measurement
ZOOM_IN_THRESH  = 1.002  # scale > this = zooming in
ZOOM_OUT_THRESH = 0.998  # scale < this = zooming out

# Log file for monitor.py to watch
MOTION_LOG = Path("/tmp/fern_motion.log")

_log_file = None


def _init_log():
    """Open motion log file for writing (append mode for resume)."""
    global _log_file
    _log_file = open(MOTION_LOG, "a", buffering=1)  # line-buffered


def _log(msg: str):
    """Print to stdout AND flush to motion log file for monitor.py."""
    print(msg)
    if _log_file:
        _log_file.write(msg + "\n")


# ---------------------------------------------------------------------------
# Feature tracker: measures motion between two frames
# ---------------------------------------------------------------------------

def _measure_transform(frame1: np.ndarray, frame2: np.ndarray) -> dict | None:
    """
    Estimate the zoom/pan transform between two frames using ORB + homography.
    Returns dict with: scale, tx_pct, ty_pct, or None if insufficient features.
    """
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=500)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    if des1 is None or des2 is None or len(kp1) < MIN_FEATURES or len(kp2) < MIN_FEATURES:
        return None

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    # Only use top 50% best matches
    good = matches[:max(MIN_FEATURES, len(matches) // 2)]
    if len(good) < MIN_FEATURES:
        return None

    pts1 = np.float32([kp1[m.queryIdx].pt for m in good])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good])

    # Estimate similarity transform (scale + rotation + translation)
    M, inliers = cv2.estimateAffinePartial2D(pts1, pts2, method=cv2.RANSAC,
                                              ransacReprojThreshold=3.0)
    if M is None or inliers is None or inliers.sum() < MIN_FEATURES // 2:
        return None

    # Decompose: M = [[s*cos, -s*sin, tx], [s*sin, s*cos, ty]]
    scale = math.sqrt(M[0, 0] ** 2 + M[1, 0] ** 2)
    tx = M[0, 2]
    ty = M[1, 2]
    h, w = frame1.shape[:2]

    return {
        "scale": scale,                # >1 = zoom in, <1 = zoom out
        "tx_pct": tx / w * 100,       # horizontal pan as % of frame width
        "ty_pct": ty / h * 100,       # vertical pan as % of frame height
        "inliers": int(inliers.sum()),
    }


# ---------------------------------------------------------------------------
# Dense optical flow: measures total motion energy (camera + subject combined)
# ---------------------------------------------------------------------------

def _measure_optical_flow(frame1: np.ndarray, frame2: np.ndarray) -> dict:
    """
    Measure total motion energy using dense optical flow (Farneback).
    Unlike ORB feature matching which only captures camera transforms,
    optical flow captures ALL pixel movement — including subject motion
    like fire flickering, insect wings, flowing water, and crowd movement.

    Returns mean_flow_pct: mean flow magnitude as % of frame diagonal.
    """
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Half-resolution for speed — optical flow is O(pixels)
    h, w = gray1.shape
    g1 = cv2.resize(gray1, (w // 2, h // 2))
    g2 = cv2.resize(gray2, (w // 2, h // 2))

    flow = cv2.calcOpticalFlowFarneback(g1, g2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

    # Normalize by frame diagonal so the metric is resolution-independent
    diag = math.sqrt(g1.shape[0] ** 2 + g1.shape[1] ** 2)
    mean_flow_pct = float(magnitude.mean()) / diag * 100
    p95_flow_pct = float(np.percentile(magnitude, 95)) / diag * 100

    # Dominant motion direction: distinguishes slide_left, slide_right, scale_up, etc.
    # Critical for identifying animation direction (text sliding in, elements scaling up)
    mean_vx = float(flow[..., 0].mean())
    mean_vy = float(flow[..., 1].mean())
    net_magnitude = math.sqrt(mean_vx ** 2 + mean_vy ** 2)

    # Radial component: positive = expanding outward (zoom in / scale up),
    # negative = converging inward (zoom out / scale down)
    cy, cx = g1.shape[0] // 2, g1.shape[1] // 2
    y_coords = (np.arange(g1.shape[0], dtype=np.float32) - cy).reshape(-1, 1)
    x_coords = (np.arange(g1.shape[1], dtype=np.float32) - cx).reshape(1, -1)
    radial_dist = np.sqrt(x_coords ** 2 + y_coords ** 2) + 1e-6
    rnx = x_coords / radial_dist
    rny = y_coords / radial_dist
    radial_component = float((flow[..., 0] * rnx + flow[..., 1] * rny).mean())

    # Classify: radial wins if it accounts for >50% of net motion
    if abs(radial_component) > net_magnitude * 0.5 and abs(radial_component) > 0.1:
        dominant_direction = "radial_out" if radial_component > 0 else "radial_in"
    elif net_magnitude > 0.2:
        # In image coords: +x = right, +y = down
        angle = math.degrees(math.atan2(mean_vy, mean_vx))
        if -45 <= angle <= 45:
            dominant_direction = "rightward"
        elif 45 < angle <= 135:
            dominant_direction = "downward"
        elif angle < -135 or angle > 135:
            dominant_direction = "leftward"
        else:
            dominant_direction = "upward"
    else:
        dominant_direction = "none"

    return {
        "mean_flow_pct": round(mean_flow_pct, 4),
        "p95_flow_pct": round(p95_flow_pct, 4),
        "dominant_direction": dominant_direction,
    }


# ---------------------------------------------------------------------------
# Transition type classifier — what happens AT each cut point
# ---------------------------------------------------------------------------

def classify_transition(cap: cv2.VideoCapture, cut_time: float, video_fps: float) -> str:
    """
    Classify the type of transition at a detected cut point.
    Analyzes 4 frames around the cut (before, just-before, just-after, after).

    Returns: hard_cut | dissolve | fade_to_black | fade_from_black | whip_pan
    """
    samples = {}
    for offset, label in [(-0.4, "pre"), (-0.05, "at_cut"), (0.05, "post"), (0.4, "after")]:
        t = max(0.0, cut_time + offset)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * video_fps))
        ret, frame = cap.read()
        if ret:
            samples[label] = frame

    if "at_cut" not in samples or "post" not in samples:
        return "hard_cut"

    gray_at = cv2.cvtColor(samples["at_cut"], cv2.COLOR_BGR2GRAY)
    gray_post = cv2.cvtColor(samples["post"], cv2.COLOR_BGR2GRAY)

    # Fade to black: the frame just before cut is nearly black
    if gray_at.mean() < 12:
        return "fade_to_black"

    # Fade from black: the frame just after cut is nearly black (coming out of darkness)
    if gray_post.mean() < 12:
        return "fade_from_black"

    # Dissolve: frame at cut point looks like a 50/50 blend of pre and post scenes
    if "pre" in samples and "after" in samples:
        pre_f  = samples["pre"].astype(np.float32)
        post_f = samples["after"].astype(np.float32)
        blend  = (pre_f + post_f) / 2.0
        at_f   = samples["at_cut"].astype(np.float32)
        diff_blend = np.abs(at_f - blend).mean()
        diff_pre   = np.abs(at_f - pre_f).mean()
        diff_post  = np.abs(at_f - post_f).mean()
        # If the frame looks more like a blend than either pure source → dissolve
        if diff_blend < min(diff_pre, diff_post) * 0.75:
            return "dissolve"

    # Whip pan: very high directional horizontal optical flow spanning the cut
    flow_info = _measure_optical_flow(samples["at_cut"], samples["post"])
    if flow_info["mean_flow_pct"] > 2.0 and flow_info["dominant_direction"] in ("leftward", "rightward"):
        return "whip_pan"

    return "hard_cut"


# ---------------------------------------------------------------------------
# Color grade intensity measurement
# ---------------------------------------------------------------------------

def _measure_color_grade(frame: np.ndarray) -> dict:
    """Measure color grade intensity: contrast, saturation, black crush."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)

    saturation = float(hsv[:, :, 1].mean()) / 255.0        # 0=grey, 1=vivid
    brightness = float(gray.mean()) / 255.0                 # 0=black, 1=white
    contrast = float(gray.std()) / 255.0                    # higher = more contrast
    # Black crush: % of pixels below 20/255
    black_pct = float((gray < 20).mean())
    # Highlight clip: % of pixels above 235/255
    highlight_pct = float((gray > 235).mean())

    return {
        "saturation": round(saturation, 3),
        "brightness": round(brightness, 3),
        "contrast": round(contrast, 3),
        "black_crush_pct": round(black_pct * 100, 1),
        "highlight_clip_pct": round(highlight_pct * 100, 1),
    }


# ---------------------------------------------------------------------------
# Segment analyzer
# ---------------------------------------------------------------------------

def analyze_segment(cap: cv2.VideoCapture, start_sec: float, end_sec: float,
                    video_fps: float) -> dict:
    """
    Analyze one segment (between two cuts) for zoom/pan motion and color grade.
    Returns per-segment stats.
    """
    duration = end_sec - start_sec
    if duration < MIN_SEG_SECS:
        return None

    # Compute frame indices to sample
    sample_interval = 1.0 / SAMPLE_FPS
    sample_times = [start_sec + i * sample_interval
                    for i in range(int(duration / sample_interval))]
    if len(sample_times) < 2:
        # Add start + end at minimum
        sample_times = [start_sec, end_sec - 0.05]

    frames = []
    for t in sample_times:
        frame_idx = int(t * video_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frames.append((t, frame))

    if len(frames) < 2:
        return None

    # Measure transforms between consecutive frames (camera motion via ORB)
    # AND dense optical flow (total motion energy including subject motion)
    transforms = []
    flow_magnitudes = []
    for i in range(len(frames) - 1):
        t1, f1 = frames[i]
        t2, f2 = frames[i + 1]
        dt = t2 - t1
        if dt <= 0:
            continue
        xform = _measure_transform(f1, f2)
        if xform:
            # Convert per-frame to per-second rates
            transforms.append({
                "scale_per_sec": (xform["scale"] - 1.0) / dt,  # % change per second
                "pan_x_per_sec": xform["tx_pct"] / dt,
                "pan_y_per_sec": xform["ty_pct"] / dt,
                "scale": xform["scale"],
                "inliers": xform["inliers"],
            })
        # Optical flow: captures fire, insects, water, etc. that ORB misses
        flow = _measure_optical_flow(f1, f2)
        flow_magnitudes.append(flow["mean_flow_pct"])

    avg_flow_pct = float(np.mean(flow_magnitudes)) if flow_magnitudes else 0.0

    # Color grade from middle frame
    mid_frame = frames[len(frames) // 2][1]
    grade = _measure_color_grade(mid_frame)

    if not transforms:
        motion_type = "indeterminate"
        avg_scale_per_sec = 0.0
    else:
        avg_scale_per_sec = np.mean([t["scale_per_sec"] for t in transforms])
        avg_pan_x = np.mean([t["pan_x_per_sec"] for t in transforms])
        avg_pan_y = np.mean([t["pan_y_per_sec"] for t in transforms])

        zoom_magnitude = abs(avg_scale_per_sec)
        pan_magnitude = math.sqrt(avg_pan_x ** 2 + avg_pan_y ** 2)

        if zoom_magnitude > 0.005:          # >0.5% zoom per second
            motion_type = "zoom_in" if avg_scale_per_sec > 0 else "zoom_out"
        elif pan_magnitude > 0.3:           # >0.3% pan per second
            pan_dir = ""
            if abs(avg_pan_x) > abs(avg_pan_y):
                pan_dir = "pan_right" if avg_pan_x > 0 else "pan_left"
            else:
                pan_dir = "pan_down" if avg_pan_y > 0 else "pan_up"
            motion_type = pan_dir
        else:
            motion_type = "static"

    # Determine what's driving the motion:
    # - "static" camera + high flow → subjects are moving (fire, bugs, water)
    # - camera moving + high flow → both camera and subjects moving
    # - camera moving + low flow → camera-only (e.g. slow zoom on still photo)
    subject_motion_threshold = 0.3  # % of frame diagonal per frame
    if motion_type in ("static", "indeterminate"):
        motion_source = "subject_only" if avg_flow_pct > subject_motion_threshold else "neither"
    else:
        motion_source = "both" if avg_flow_pct > subject_motion_threshold else "camera_only"

    return {
        "start_sec": round(start_sec, 2),
        "end_sec": round(end_sec, 2),
        "duration_sec": round(duration, 2),
        "motion_type": motion_type,
        "zoom_rate_pct_per_sec": round(avg_scale_per_sec * 100, 3),
        "n_transforms": len(transforms),
        "total_motion_energy_pct": round(avg_flow_pct, 3),
        "motion_source": motion_source,
        **grade,
    }


# ---------------------------------------------------------------------------
# Cut timing vs beat analysis
# ---------------------------------------------------------------------------

def analyze_beat_sync(cut_times: list[float], bpm: float) -> dict:
    """
    For each cut, compute how close it falls to a musical beat.
    Returns: % of cuts within 100ms of a beat, avg offset.
    """
    if not cut_times or bpm <= 0:
        return {"beat_sync_pct": 0, "avg_offset_ms": 0}

    beat_interval = 60.0 / bpm
    offsets = []
    for t in cut_times:
        # Position within beat cycle
        phase = (t % beat_interval)
        # Distance to nearest beat (could be ahead or behind)
        offset = min(phase, beat_interval - phase)
        offsets.append(offset)

    threshold_ms = 100  # 100ms = tight sync
    tight_pct = sum(1 for o in offsets if o * 1000 <= threshold_ms) / len(offsets) * 100

    return {
        "beat_sync_pct": round(tight_pct, 1),
        "avg_offset_ms": round(np.mean(offsets) * 1000, 1),
        "beat_interval_sec": round(beat_interval, 3),
        "total_cuts": len(cut_times),
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_video(video_path: Path, timeline_path: Path, audio_path: Path = None) -> dict:
    _log(f"\nAnalyzing motion: {video_path.name}")

    # Load timeline (cut points + timestamps)
    timeline = json.load(open(timeline_path))
    all_timestamps = sorted(set(e["timestamp"] for e in timeline.get("timeline", [])))
    cut_count = timeline.get("cut_count", 0)
    video_duration = timeline.get("duration", 0)
    # Prefer stored cut_timestamps (available after the hybrid analyzer update).
    # Fall back to all_timestamps as segment boundaries if not yet stored.
    actual_cut_timestamps = timeline.get("cut_timestamps", [])
    cut_timestamps = all_timestamps  # used for segment boundaries
    reported_cuts_per_min = cut_count / (video_duration / 60) if video_duration else 0

    # Build segment list from cut timestamps
    times = sorted(set([0.0] + cut_timestamps + [video_duration]))
    segments_to_analyze = [(times[i], times[i + 1]) for i in range(len(times) - 1)]
    # Sample max 200 segments (for speed)
    step = max(1, len(segments_to_analyze) // 200)
    segments_to_analyze = segments_to_analyze[::step]

    # Load video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  ERROR: Cannot open {video_path}")
        return {}

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    vid_id = video_path.parent.name
    _log(f"  Video: {video_fps:.1f}fps, {video_duration/60:.1f}min")
    _log(f"  Analyzing {len(segments_to_analyze)} segments (sampled from {len(times)-1} total)...")
    _log(f"MOTION_START {vid_id} {len(segments_to_analyze)}")

    segment_results = []
    t_start = time.time()
    n_total = len(segments_to_analyze)
    for i, (start, end) in enumerate(segments_to_analyze):
        if i % 10 == 0 and i > 0:
            elapsed = time.time() - t_start
            rate = i / elapsed
            eta_sec = int((n_total - i) / rate) if rate > 0 else 0
            eta_str = f"{eta_sec//60}m{eta_sec%60:02d}s"
            pct = i / n_total * 100
            _log(f"MOTION_PROGRESS {vid_id} {i}/{n_total} {pct:.1f}% ETA:{eta_str}")
        result = analyze_segment(cap, start, end, video_fps)
        if result:
            segment_results.append(result)

    # Transition type analysis — must run before cap.release()
    # Requires cut_timestamps stored in the timeline JSON (available after hybrid analyzer update)
    transition_dist = {}
    if actual_cut_timestamps:
        # Sample up to 300 cuts for speed
        step_t = max(1, len(actual_cut_timestamps) // 300)
        sampled_cuts = actual_cut_timestamps[::step_t]
        _log(f"  Classifying {len(sampled_cuts)} transitions...")
        transition_types = []
        for ct in sampled_cuts:
            t_type = classify_transition(cap, ct, video_fps)
            transition_types.append(t_type)
        t_counts = Counter(transition_types)
        transition_dist = {k: round(v / len(transition_types) * 100, 1)
                           for k, v in t_counts.most_common()}
        _log(f"  Transitions: {transition_dist}")
    else:
        transition_dist = {"_note": "Re-run hybrid analyzer to store cut_timestamps, then re-run this script"}

    cap.release()

    if not segment_results:
        _log("  No segments analyzed.")
        return {}

    # Aggregate motion types
    motion_counts = Counter(s["motion_type"] for s in segment_results)
    total_segs = len(segment_results)
    motion_distribution = {k: round(v / total_segs * 100, 1)
                           for k, v in motion_counts.most_common()}

    # Zoom stats (only zoom_in / zoom_out segments)
    zoom_segs = [s for s in segment_results if s["motion_type"] in ("zoom_in", "zoom_out")]
    zoom_in_segs = [s for s in segment_results if s["motion_type"] == "zoom_in"]
    zoom_out_segs = [s for s in segment_results if s["motion_type"] == "zoom_out"]

    avg_zoom_rate = np.mean([abs(s["zoom_rate_pct_per_sec"]) for s in zoom_segs]) if zoom_segs else 0
    avg_zoom_in_rate = abs(np.mean([s["zoom_rate_pct_per_sec"] for s in zoom_in_segs])) if zoom_in_segs else 0
    avg_zoom_out_rate = abs(np.mean([s["zoom_rate_pct_per_sec"] for s in zoom_out_segs])) if zoom_out_segs else 0

    # Cut rate
    cut_rate_per_min = len(cut_timestamps) / (video_duration / 60) if video_duration else 0
    avg_seg_duration = video_duration / len(cut_timestamps) if cut_timestamps else 0

    # Color grade stats (avg across all segments)
    grade_keys = ["saturation", "brightness", "contrast", "black_crush_pct", "highlight_clip_pct"]
    color_grade = {k: round(float(np.mean([s[k] for s in segment_results])), 3)
                   for k in grade_keys}

    # Content/subject motion stats (from optical flow)
    motion_source_counts = Counter(s.get("motion_source", "unknown") for s in segment_results)
    motion_source_dist = {k: round(v / total_segs * 100, 1)
                          for k, v in motion_source_counts.most_common()}
    avg_total_motion = float(np.mean([s.get("total_motion_energy_pct", 0.0)
                                      for s in segment_results]))
    # Key metric: static camera shots where subjects are still moving
    static_segs = [s for s in segment_results if s["motion_type"] == "static"]
    static_with_subject = [s for s in static_segs
                           if s.get("motion_source") == "subject_only"]
    subject_in_static_pct = (len(static_with_subject) / len(static_segs) * 100
                              if static_segs else 0.0)

    # Beat sync
    bpm = 116.1  # from audio formula
    beat_sync = analyze_beat_sync(cut_timestamps, bpm)

    # Segment duration distribution
    durations = [s["duration_sec"] for s in segment_results]
    dur_distribution = {
        "under_1s": round(sum(1 for d in durations if d < 1.0) / len(durations) * 100, 1),
        "1_to_3s": round(sum(1 for d in durations if 1.0 <= d < 3.0) / len(durations) * 100, 1),
        "3_to_6s": round(sum(1 for d in durations if 3.0 <= d < 6.0) / len(durations) * 100, 1),
        "over_6s": round(sum(1 for d in durations if d >= 6.0) / len(durations) * 100, 1),
    }

    results = {
        "video": str(video_path),
        "video_id": video_path.parent.name,
        "duration_sec": round(video_duration, 1),
        # Private: only present when --save-segments; consumed and removed by main()
        "_segment_results": segment_results,

        "cut_dynamics": {
            "total_cuts": cut_count,
            "cuts_per_minute": round(reported_cuts_per_min, 1),
            "avg_segment_duration_sec": round(video_duration / cut_count if cut_count else 0, 2),
            "segment_duration_distribution": dur_distribution,
        },

        "motion": {
            "distribution_pct": motion_distribution,
            "zoom_in_pct": round(motion_counts.get("zoom_in", 0) / total_segs * 100, 1),
            "zoom_out_pct": round(motion_counts.get("zoom_out", 0) / total_segs * 100, 1),
            "pan_pct": round(sum(v for k, v in motion_counts.items()
                                 if k.startswith("pan_")) / total_segs * 100, 1),
            "static_pct": round(motion_counts.get("static", 0) / total_segs * 100, 1),

            # KEY: zoom speed
            "avg_zoom_rate_pct_per_sec": round(avg_zoom_rate, 3),
            "zoom_in_rate_pct_per_sec": round(avg_zoom_in_rate, 3),
            "zoom_out_rate_pct_per_sec": round(avg_zoom_out_rate, 3),

            "interpretation": _interpret_zoom_rate(avg_zoom_rate),
        },

        "color_grade_intensity": color_grade,

        "content_motion": {
            "avg_total_motion_energy_pct": round(avg_total_motion, 3),
            "motion_source_distribution": motion_source_dist,
            "subject_motion_in_static_shots_pct": round(subject_in_static_pct, 1),
            "interpretation": _interpret_content_motion(avg_total_motion),
        },

        "transition_types": transition_dist,

        "beat_sync": beat_sync,
    }

    return results


def _interpret_zoom_rate(rate: float) -> str:
    """Classify zoom speed into human-readable category."""
    if rate < 0.5:
        return "nearly_static (< 0.5%/s — imperceptible)"
    elif rate < 2.0:
        return "gentle_ken_burns (0.5–2%/s — traditional documentary)"
    elif rate < 5.0:
        return "moderate_motion (2–5%/s — modern YouTube doc)"
    elif rate < 10.0:
        return "aggressive_motion (5–10%/s — high energy)"
    else:
        return "very_aggressive (>10%/s — action/hype content)"


def _interpret_content_motion(mean_flow_pct: float) -> str:
    """Classify total motion energy (camera + subject) into human-readable category."""
    if mean_flow_pct < 0.1:
        return "completely_static (freeze frames, still graphics)"
    elif mean_flow_pct < 0.5:
        return "subtle_life (distant fire, slow breathing, barely-moving subjects)"
    elif mean_flow_pct < 1.5:
        return "moderate_motion (insect wings, close fire, gentle water flow)"
    elif mean_flow_pct < 5.0:
        return "high_energy (active crowd, fast action, rushing water)"
    else:
        return "chaotic (handheld shake, action sequences, rapid cuts)"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Measure Fern production dynamics from video files")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--video", help="Path to a specific video.mp4")
    g.add_argument("--all", action="store_true", help="Analyze all 3 Fern videos")
    p.add_argument("--out", default="analysis/fern/FERN_MOTION_FORMULA.json",
                   help="Output JSON path")
    p.add_argument("--save-segments", action="store_true",
                   help="Save per-segment motion data to {video_id}_segment_motion.json "
                        "for cross-correlation with narrative_function via "
                        "analyze_fern_crosscorrelate.py. Enables per-content-type motion "
                        "weights in production_rules.py (currently using global averages).")
    args = p.parse_args()

    _init_log()
    _log(f"Motion analysis started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.all:
        video_paths = sorted(Path("analysis/fern").glob("*/video.mp4"))
    else:
        video_paths = [Path(args.video)]

    all_results = []
    for video_path in video_paths:
        vid_id = video_path.parent.name

        # Checkpoint: if segment_motion.json already exists, skip this video
        seg_path = video_path.parent / "segment_motion.json"
        if args.save_segments and seg_path.exists():
            _log(f"\n  SKIP {vid_id} — segment_motion.json already exists (checkpoint)")
            # Still need its results for the aggregate formula
            # Re-load from existing segment file to reconstruct aggregate
            # (We don't have the full result dict, so just skip aggregate for now)
            _log(f"  NOTE: {vid_id} will be excluded from aggregate formula re-run.")
            _log(f"        To re-analyze: delete {seg_path} first.")
            continue

        # Find matching qwen-vl timeline (complete)
        timeline_path = video_path.parent / "timeline_hybrid_qwen-vl.json"
        if not timeline_path.exists():
            timeline_path = next(video_path.parent.glob("timeline_hybrid_*.json"), None)
        if not timeline_path:
            _log(f"  Skipping {vid_id} — no timeline found")
            continue

        result = analyze_video(video_path, timeline_path)
        if result:
            all_results.append(result)

            # Save per-segment motion data immediately after each video completes.
            # Doing this per-video (not at the end) means if the run is interrupted
            # mid-way, completed videos are already saved and won't need re-processing.
            if args.save_segments:
                segs = result.pop("_segment_results", [])
                seg_data = {
                    "video_id": vid_id,
                    "timeline_source": str(timeline_path),
                    "_note": (
                        "Per-segment motion data for cross-correlation with narrative_function. "
                        "Join on timestamp range [start_sec, end_sec] against "
                        "timeline_hybrid_qwen-vl.json frame timestamps."
                    ),
                    "segments": segs,
                }
                with open(seg_path, "w") as f:
                    json.dump(seg_data, f, indent=2)
                _log(f"  ✓ Saved segment data: {seg_path} ({len(segs)} segments)")
                _log(f"MOTION_DONE {vid_id} {len(segs)}")
            else:
                result.pop("_segment_results", None)  # discard if not saving

    if not all_results:
        print("No results.")
        sys.exit(1)

    # Aggregate across videos
    def _avg(key_path):
        vals = []
        for r in all_results:
            v = r
            for k in key_path:
                v = v.get(k, {}) if isinstance(v, dict) else None
                if v is None:
                    break
            if isinstance(v, (int, float)):
                vals.append(v)
        return round(float(np.mean(vals)), 3) if vals else 0

    aggregate = {
        "videos_analyzed": len(all_results),
        "per_video": all_results,

        "PRODUCTION_SPEC": {
            "_comment": "Use these values when building video_assembler.py",

            "ken_burns": {
                "zoom_in_rate_pct_per_sec":  _avg(["motion", "zoom_in_rate_pct_per_sec"]),
                "zoom_out_rate_pct_per_sec": _avg(["motion", "zoom_out_rate_pct_per_sec"]),
                "avg_zoom_rate_pct_per_sec": _avg(["motion", "avg_zoom_rate_pct_per_sec"]),
                "zoom_in_pct":  _avg(["motion", "zoom_in_pct"]),
                "zoom_out_pct": _avg(["motion", "zoom_out_pct"]),
                "static_pct":   _avg(["motion", "static_pct"]),
                "interpretation": _interpret_zoom_rate(_avg(["motion", "avg_zoom_rate_pct_per_sec"])),
            },

            "cut_timing": {
                "cuts_per_minute":          _avg(["cut_dynamics", "cuts_per_minute"]),
                "avg_segment_duration_sec": _avg(["cut_dynamics", "avg_segment_duration_sec"]),
            },

            "beat_sync": {
                "tight_sync_pct":   _avg(["beat_sync", "beat_sync_pct"]),
                "avg_offset_ms":    _avg(["beat_sync", "avg_offset_ms"]),
            },

            "color_grade": {
                "saturation":         _avg(["color_grade_intensity", "saturation"]),
                "brightness":         _avg(["color_grade_intensity", "brightness"]),
                "contrast":           _avg(["color_grade_intensity", "contrast"]),
                "black_crush_pct":    _avg(["color_grade_intensity", "black_crush_pct"]),
                "highlight_clip_pct": _avg(["color_grade_intensity", "highlight_clip_pct"]),
            },

            "content_motion": {
                "_comment": "Optical flow captures subject motion (fire, insects, water) missed by camera tracking",
                "avg_total_motion_energy_pct": _avg(["content_motion", "avg_total_motion_energy_pct"]),
                "subject_motion_in_static_shots_pct": _avg(["content_motion", "subject_motion_in_static_shots_pct"]),
                "interpretation": _interpret_content_motion(_avg(["content_motion", "avg_total_motion_energy_pct"])),
            },

            "transition_types": {
                "_comment": "How shots connect — hard_cut dominant in fast-paced docs, dissolve/fade for emotional moments",
                "_note": "Requires cut_timestamps in timeline JSON. Re-run hybrid analyzer, then this script.",
                "distribution": {
                    k: _avg(["transition_types", k])
                    for k in ("hard_cut", "dissolve", "fade_to_black", "fade_from_black", "whip_pan")
                },
            },
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(aggregate, f, indent=2)

    print(f"\n{'='*60}")
    print(f"MOTION FORMULA RESULTS")
    print(f"{'='*60}")
    spec = aggregate["PRODUCTION_SPEC"]

    kb = spec["ken_burns"]
    print(f"\nKen Burns Motion:")
    print(f"  Zoom-in:   {kb['zoom_in_pct']:.1f}% of segments @ {kb['zoom_in_rate_pct_per_sec']:.2f}%/sec")
    print(f"  Zoom-out:  {kb['zoom_out_pct']:.1f}% of segments @ {kb['zoom_out_rate_pct_per_sec']:.2f}%/sec")
    print(f"  Static:    {kb['static_pct']:.1f}% of segments")
    print(f"  Speed:     {kb['interpretation']}")

    ct = spec["cut_timing"]
    print(f"\nCut Timing:")
    print(f"  {ct['cuts_per_minute']:.1f} cuts/min → avg {ct['avg_segment_duration_sec']:.2f}s per segment")

    bs = spec["beat_sync"]
    print(f"\nBeat Sync:")
    print(f"  {bs['tight_sync_pct']:.1f}% of cuts land within 100ms of a beat")
    print(f"  Avg offset: {bs['avg_offset_ms']:.0f}ms")

    cg = spec["color_grade"]
    print(f"\nColor Grade Intensity:")
    print(f"  Saturation:    {cg['saturation']:.3f}  (0=grey, 1=vivid)")
    print(f"  Brightness:    {cg['brightness']:.3f}  (0=black, 1=white)")
    print(f"  Contrast:      {cg['contrast']:.3f}  (higher=more contrast)")
    print(f"  Black crush:   {cg['black_crush_pct']:.1f}% of pixels near-black")

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
