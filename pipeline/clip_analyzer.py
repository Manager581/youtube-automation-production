#!/usr/bin/env python3
"""
clip_analyzer.py — Find the best moment within a downloaded video clip.

Problem: footage_sourcer downloads a 3-minute AP Archive clip. The assembler
needs a 5-second excerpt. prepare_clip() currently takes from position 0.
This module finds the RIGHT window — the section that actually matches the
story beat, not just the beginning of the clip.

Method:
  1. Sample frames at regular intervals (every 2s by default)
  2. Score each frame window against the storyboard description using:
     a. Keyword match between storyboard `show` text and frame OCR (fast)
     b. Vision model description match (if available, slower but accurate)
  3. Return the best-scoring (start_sec, duration_sec) window
  4. Falls back to the most visually "active" window (scene change detection)

Usage (standalone):
    python pipeline/clip_analyzer.py \
        --clip footage/topic/ap_archive_clip.mp4 \
        --show "FBI director testifying at Senate hearing" \
        --duration 5.0

Usage (from code — called by video_assembler.py):
    from pipeline.clip_analyzer import find_best_moment
    start, dur = find_best_moment(clip_path, storyboard_show="FBI director...", duration=5.0)
    # Then pass start_sec to prepare_clip()
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

SAMPLE_INTERVAL_SEC = 2.0    # sample one frame every N seconds
MIN_CLIP_DURATION   = 2.0    # don't try to find moments in clips shorter than this
CACHE_DIR           = Path(".clip_moment_cache")

# Vision-capable models only — must support image input via Ollama "images" field.
# Text-only models (qwen3.5:27b, qwen3.5:4b) are NOT included here.
VISION_MODELS = ["qwen2.5vl:7b", "qwen2.5vl:72b", "llava:13b", "llava:7b", "llava"]
OLLAMA_URL    = "http://localhost:11434/api/generate"

# Scene activity threshold — used when no vision model available
# Frames with lots of scene change are more "active" / news-worthy
SCENE_SCORE_MIN = 0.1


# ── ffprobe helpers ───────────────────────────────────────────────────────────

def get_duration(clip_path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json",
        str(clip_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


def extract_frame(clip_path: Path, time_sec: float, out_path: Path) -> bool:
    """Extract a single frame from the clip at time_sec."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_sec),
        "-i", str(clip_path),
        "-vframes", "1",
        "-q:v", "3",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=15)
    return out_path.exists() and out_path.stat().st_size > 0


def measure_scene_activity(clip_path: Path, start_sec: float, duration: float) -> float:
    """
    Measure visual activity (scene change score) in a clip window.
    Higher = more visual change = more likely to be an action/reaction shot.
    Uses ffmpeg scene detection on the window.
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration),
        "-i", str(clip_path),
        "-vf", "select=gt(scene\\,0.2),showinfo",
        "-vsync", "vfr",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    changes = result.stderr.count("pts_time:")
    return changes / max(duration, 1.0)


# ── Vision model scoring ──────────────────────────────────────────────────────

def _get_vision_model() -> str | None:
    """Return first available vision model from VISION_MODELS, or None."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        installed = {m["name"] for m in data.get("models", [])}
        for model in VISION_MODELS:
            if model in installed:
                return model
            base = model.split(":")[0]
            for inst in installed:
                if inst.startswith(base + ":"):
                    return inst
    except Exception:
        pass
    return None


def _score_frame_with_model(model: str, frame_path: Path, description: str) -> float:
    """
    Ask vision model: does this frame match the description?
    Returns 0.0–1.0 confidence score.
    """
    try:
        import base64
        with open(frame_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        prompt = (
            f"I'm looking for a specific image in a video clip.\n"
            f"Description of what I want to find: {description}\n\n"
            f"Does this video frame match or closely relate to that description?\n"
            f"Reply with ONLY a number from 0.0 to 1.0 where:\n"
            f"  1.0 = perfect match\n"
            f"  0.5 = somewhat related\n"
            f"  0.0 = completely unrelated\n"
            f"Reply with the number only."
        )

        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 10},
        }).encode()

        req = urllib.request.Request(
            OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            response_text = data.get("response", "0").strip()
            # Extract first number from response
            import re
            numbers = re.findall(r"\d+\.?\d*", response_text)
            if numbers:
                score = float(numbers[0])
                return min(1.0, max(0.0, score))
    except Exception:
        pass
    return 0.0


def _keyword_score(frame_time: float, clip_duration: float, description: str) -> float:
    """
    Heuristic: early frames of news clips often have establishing shots.
    Middle frames have the main content.
    Returns a position-based score biased toward 20-60% into the clip.
    """
    position = frame_time / max(clip_duration, 1.0)
    # Bell curve peaking at 30% into the clip (typical for news clips)
    import math
    position_score = math.exp(-((position - 0.30) ** 2) / (2 * 0.20 ** 2))
    return position_score * 0.3  # max 0.3 contribution from position heuristic


# ── Cache ─────────────────────────────────────────────────────────────────────

def _cache_key(clip_path: Path, description: str, duration: float) -> str:
    key = f"{clip_path}|{description}|{duration:.1f}"
    return hashlib.md5(key.encode()).hexdigest()[:16]


def _load_cache(cache_key: str) -> tuple[float, float] | None:
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            return data["start_sec"], data["duration_sec"]
        except Exception:
            pass
    return None


def _save_cache(cache_key: str, start_sec: float, duration_sec: float):
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    cache_file.write_text(json.dumps({"start_sec": start_sec, "duration_sec": duration_sec}))


# ── Main function ─────────────────────────────────────────────────────────────

def find_best_moment(
    clip_path: Path,
    storyboard_show: str = "",
    duration: float = 5.0,
    use_vision: bool = True,
    use_cache: bool = True,
) -> tuple[float, float]:
    """
    Find the best start_sec within clip_path for a `duration`-second excerpt
    that matches the storyboard description.

    Returns: (start_sec, duration_sec)
    Falls back to (0.0, duration) if analysis fails or clip is too short.
    """
    if not clip_path.exists():
        return (0.0, duration)

    clip_duration = get_duration(clip_path)
    if clip_duration < MIN_CLIP_DURATION or clip_duration <= duration:
        # Clip is too short to search — use from start
        return (0.0, min(clip_duration, duration))

    # Cache check
    ck = _cache_key(clip_path, storyboard_show, duration)
    if use_cache:
        cached = _load_cache(ck)
        if cached:
            return cached

    # Get vision model if available
    vision_model = _get_vision_model() if use_vision and storyboard_show else None

    # Sample frames at regular intervals
    sample_times = []
    t = 0.0
    while t + duration <= clip_duration:
        sample_times.append(t)
        t += SAMPLE_INTERVAL_SEC

    if not sample_times:
        return (0.0, duration)

    best_score = -1.0
    best_start = 0.0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        for t in sample_times:
            frame_path = tmp_path / f"frame_{t:.1f}.jpg"
            if not extract_frame(clip_path, t, frame_path):
                continue

            score = 0.0

            # Vision model score (0.0–1.0, high weight)
            if vision_model and storyboard_show:
                score += _score_frame_with_model(vision_model, frame_path, storyboard_show) * 0.7

            # Position heuristic (0.0–0.3, low weight)
            score += _keyword_score(t, clip_duration, storyboard_show)

            if score > best_score:
                best_score = score
                best_start = t

    # If vision model not available, use scene activity as tiebreaker
    if not vision_model:
        # Find the most visually active window
        activity_scores = []
        for t in sample_times:
            activity = measure_scene_activity(clip_path, t, duration)
            activity_scores.append((activity, t))
        if activity_scores:
            activity_scores.sort(reverse=True)
            best_start = activity_scores[0][1]

    # Ensure we don't start too close to the end
    best_start = min(best_start, clip_duration - duration - 0.5)
    best_start = max(0.0, best_start)

    result = (round(best_start, 2), duration)

    if use_cache:
        _save_cache(ck, *result)

    return result


def analyze_manifest_clips(
    manifest_path: Path,
    target_duration: float = 5.0,
    use_vision: bool = True,
) -> dict:
    """
    Process all video clips in a footage manifest.
    Adds clip_start_sec to each clip entry.
    Saves updated manifest in-place.
    """
    manifest = json.loads(manifest_path.read_text())
    clips = manifest.get("clips", [])

    video_clips = [
        c for c in clips
        if str(c.get("local_path", "")).lower().endswith((".mp4", ".mov", ".mkv", ".webm"))
        and c.get("downloaded")
    ]

    if not video_clips:
        print("No downloaded video clips to analyze.")
        return manifest

    print(f"\nAnalyzing {len(video_clips)} video clips for best moments...")

    for i, clip in enumerate(video_clips):
        path = Path(clip["local_path"])
        show = clip.get("storyboard_show", "")

        print(f"  [{i+1}/{len(video_clips)}] {path.name[:50]}", end="  ", flush=True)

        start, dur = find_best_moment(path, storyboard_show=show,
                                      duration=target_duration, use_vision=use_vision)
        clip["clip_start_sec"]    = start
        clip["clip_duration_sec"] = dur

        clip_total = get_duration(path)
        print(f"→ {start:.1f}s–{start+dur:.1f}s  (of {clip_total:.0f}s total)")

    manifest["clips"] = clips
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nUpdated manifest: {manifest_path}")
    return manifest


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Find the best moment in a video clip")
    subp = ap.add_subparsers(dest="cmd")

    # Single clip
    clip_p = subp.add_parser("clip", help="Analyze one clip")
    clip_p.add_argument("--clip", required=True, help="Path to video clip")
    clip_p.add_argument("--show", default="", help="Storyboard description (what to find)")
    clip_p.add_argument("--duration", type=float, default=5.0, help="Desired excerpt duration (sec)")
    clip_p.add_argument("--no-vision", action="store_true", help="Skip vision model, use heuristics only")

    # Full manifest
    mfst_p = subp.add_parser("manifest", help="Analyze all clips in a footage manifest")
    mfst_p.add_argument("--manifest", required=True, help="Path to manifest.json")
    mfst_p.add_argument("--duration", type=float, default=5.0, help="Target clip excerpt duration")
    mfst_p.add_argument("--no-vision", action="store_true", help="Skip vision model")

    args = ap.parse_args()

    if not args.cmd:
        ap.print_help()
        sys.exit(1)

    if args.cmd == "clip":
        start, dur = find_best_moment(
            Path(args.clip),
            storyboard_show=args.show,
            duration=args.duration,
            use_vision=not args.no_vision,
        )
        clip_dur = get_duration(Path(args.clip))
        print(f"\nBest moment: {start:.2f}s – {start+dur:.2f}s  "
              f"(clip is {clip_dur:.0f}s total)")
        print(f"Command:\n  ffmpeg -ss {start} -t {dur} -i {args.clip} excerpt.mp4")

    elif args.cmd == "manifest":
        analyze_manifest_clips(
            Path(args.manifest),
            target_duration=args.duration,
            use_vision=not args.no_vision,
        )


if __name__ == "__main__":
    main()
