#!/usr/bin/env python3
"""
check_fern_video.py — Final video QA checker for Fern-style videos.

Validates the assembled video against Fern's measured benchmarks.
Run after video_assembler.py, before upload.

Usage:
    python check_fern_video.py output/topic/final.mp4
    python check_fern_video.py output/topic/final.mp4 --timeline output/topic/timeline.json
    python check_fern_video.py output/topic/final.mp4 --music assets/music/track.mp3

Output: PASS / WARN / FAIL with per-check details.
Exit code: 0 = PASS or WARN, 1 = FAIL (hard spec violations).

Fern benchmarks (measured from 3 reference videos, 1,838 frames):
  Duration:       22–27 min typical (18 min floor, 32 min ceiling)
  Cut rate:       11.3 cuts/min avg (8–15 acceptable)
  Audio:          Mixed -14 to -18 LUFS integrated
  Color grade:    0.46x saturation applied (avg saturation < 0.35)
  Chapter cards:  ~5 per video (3 minimum)
  Footage variety: no single clip used > 3 times
  Beat sync:      ~39% of cuts within ±100ms of a beat
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Fern benchmarks ──────────────────────────────────────────────────────────

DURATION_FLOOR        = 18 * 60    # hard fail below
DURATION_CEILING      = 32 * 60    # hard fail above
DURATION_TARGET_LOW   = 22 * 60    # warn below
DURATION_TARGET_HIGH  = 27 * 60    # warn above

CUT_RATE_MIN    = 8.0    # cuts/min — warn below
CUT_RATE_MAX    = 15.0   # cuts/min — warn above
CUT_RATE_TARGET = 11.3   # Fern avg

SCENE_THRESHOLD = 0.3    # ffmpeg scene change sensitivity (0–1)

LUFS_LOW   = -23.0   # warn below (too quiet)
LUFS_HIGH  = -10.0   # warn above (too loud / clipping risk)

SAT_HIGH = 0.40      # warn above (looks ungraded)
SAT_LOW  = 0.05      # warn below (over-desaturated / B&W)

CHAPTER_MIN = 3      # warn below

MAX_CLIP_REPEATS = 3  # warn if same source clip used more than this

BEAT_SNAP_WINDOW = 0.10   # ±100ms
BEAT_SYNC_FLOOR  = 0.25   # warn below 25%

# ── ANSI colors ──────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ICONS = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗", "SKIP": "—"}
COLORS = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED, "SKIP": GRAY}


# ── ffprobe / ffmpeg helpers ──────────────────────────────────────────────────

def _ffprobe_json(video_path, show_entries, select_streams=None):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_entries", show_entries]
    if select_streams:
        cmd += ["-select_streams", select_streams]
    cmd.append(str(video_path))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _ffmpeg_run(args, timeout=600):
    result = subprocess.run(
        ["ffmpeg"] + args,
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout, result.stderr, result.returncode


# ── Individual checks ─────────────────────────────────────────────────────────

def check_duration(video_path):
    data = _ffprobe_json(video_path, "format=duration")
    if not data:
        return None, "FAIL", "ffprobe failed — is ffmpeg installed?"

    dur = float(data["format"]["duration"])
    m = dur / 60

    if dur < DURATION_FLOOR:
        return dur, "FAIL", f"{m:.1f} min — too short (hard floor: 18 min)"
    if dur > DURATION_CEILING:
        return dur, "FAIL", f"{m:.1f} min — too long (hard ceiling: 32 min)"
    if dur < DURATION_TARGET_LOW:
        return dur, "WARN", f"{m:.1f} min — below typical range (target: 22–27 min)"
    if dur > DURATION_TARGET_HIGH:
        return dur, "WARN", f"{m:.1f} min — above typical range (target: 22–27 min)"
    return dur, "PASS", f"{m:.1f} min ✓"


def check_cut_rate(video_path, total_dur_sec):
    if not total_dur_sec:
        return None, "SKIP", "No duration"

    # ffmpeg scene detection — counts detected transitions
    _, stderr, _ = _ffmpeg_run([
        "-i", str(video_path),
        "-vf", f"select=gt(scene\\,{SCENE_THRESHOLD}),showinfo",
        "-vsync", "vfr", "-f", "null", "-",
    ], timeout=300)

    cuts = stderr.count("pts_time:")
    rate = cuts / (total_dur_sec / 60)

    if rate < CUT_RATE_MIN:
        return rate, "WARN", f"{rate:.1f} cuts/min — below min ({CUT_RATE_MIN}). Footage may be too static."
    if rate > CUT_RATE_MAX:
        return rate, "WARN", f"{rate:.1f} cuts/min — above max ({CUT_RATE_MAX}). Too frenetic."
    return rate, "PASS", f"{rate:.1f} cuts/min ✓  (Fern avg: {CUT_RATE_TARGET})"


def check_audio_levels(video_path):
    _, stderr, _ = _ffmpeg_run([
        "-i", str(video_path),
        "-af", "loudnorm=print_format=json",
        "-f", "null", "-",
    ], timeout=300)

    try:
        start = stderr.rfind("{")
        end   = stderr.rfind("}") + 1
        if start == -1 or end <= 0:
            return None, "WARN", "Could not parse loudnorm output"
        data = json.loads(stderr[start:end])
        lufs = float(data.get("input_i", "-999"))
    except (json.JSONDecodeError, ValueError):
        return None, "WARN", "Could not parse audio levels"

    if lufs < LUFS_LOW:
        return lufs, "WARN", f"{lufs:.1f} LUFS — too quiet (target: -14 to -18 LUFS)"
    if lufs > LUFS_HIGH:
        return lufs, "WARN", f"{lufs:.1f} LUFS — too loud / clipping risk"
    return lufs, "PASS", f"{lufs:.1f} LUFS ✓"


def check_color_grade(video_path):
    try:
        from PIL import Image
        import colorsys
    except ImportError:
        return None, "SKIP", "Pillow not installed  →  pip install pillow"

    try:
        data = _ffprobe_json(video_path, "format=duration")
        if not data:
            return None, "SKIP", "Could not read duration"
        dur = float(data["format"]["duration"])
        seek = dur * 0.4   # sample at 40% through

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            frame_path = f.name

        _ffmpeg_run([
            "-ss", str(seek), "-i", str(video_path),
            "-vframes", "1", "-q:v", "2", frame_path, "-y",
        ], timeout=30)

        img = Image.open(frame_path).convert("RGB").resize((64, 64))
        pixels = list(img.getdata())
        os.unlink(frame_path)

        sats = [colorsys.rgb_to_hsv(r/255, g/255, b/255)[1] for r, g, b in pixels]
        avg = sum(sats) / len(sats)

        if avg > SAT_HIGH:
            return avg, "WARN", f"Saturation {avg:.2f} — looks ungraded (expect <{SAT_HIGH} after Fern grade)"
        if avg < SAT_LOW:
            return avg, "WARN", f"Saturation {avg:.2f} — near B&W, may be over-graded"
        return avg, "PASS", f"Saturation {avg:.2f} ✓  (desaturated cinematic look)"
    except Exception as e:
        return None, "WARN", f"Color grade check error: {e}"


def check_chapter_cards(timeline_path):
    if not timeline_path:
        return None, "SKIP", "No timeline.json  →  pass --timeline or it auto-detects"
    try:
        with open(timeline_path) as f:
            tl = json.load(f)
        n = sum(1 for s in tl if s.get("source_type") == "chapter_card")
    except Exception as e:
        return None, "WARN", f"Could not read timeline: {e}"

    if n == 0:
        return n, "WARN", "No chapter cards (Fern avg: ~5).  Add [PAUSE:5.0] markers in script."
    if n < CHAPTER_MIN:
        return n, "WARN", f"{n} chapter card(s) — low (Fern avg: ~5, minimum: {CHAPTER_MIN})"
    return n, "PASS", f"{n} chapter cards ✓"


def check_footage_variety(timeline_path):
    if not timeline_path:
        return None, "SKIP", "No timeline.json"
    try:
        with open(timeline_path) as f:
            tl = json.load(f)
    except Exception as e:
        return None, "WARN", f"Could not read timeline: {e}"

    counts = {}
    for seg in tl:
        src = seg.get("source_path")
        if src:
            name = Path(src).name
            counts[name] = counts.get(name, 0) + 1

    overused = {k: v for k, v in counts.items() if v > MAX_CLIP_REPEATS}
    if overused:
        top = sorted(overused.items(), key=lambda x: -x[1])[:3]
        details = ", ".join(f"{k} ×{v}" for k, v in top)
        return overused, "WARN", f"{len(overused)} clip(s) used >{MAX_CLIP_REPEATS}×: {details}"

    return counts, "PASS", f"{len(counts)} unique sources, no overuse ✓"


def check_beat_sync(timeline_path, music_path):
    if not timeline_path:
        return None, "SKIP", "No timeline.json"
    if not music_path:
        return None, "SKIP", "No music file  →  pass --music or put at assets/music/track.mp3"

    try:
        import librosa
        import numpy as np
    except ImportError:
        return None, "SKIP", "librosa not installed  →  pip install librosa"

    try:
        with open(timeline_path) as f:
            tl = json.load(f)
    except Exception as e:
        return None, "WARN", f"Could not read timeline: {e}"

    # Build cut timestamps from cumulative durations
    cursor = 0.0
    cut_times = []
    for seg in tl:
        if seg.get("source_type") not in ("chapter_card",):
            cut_times.append(cursor)
        cursor += seg.get("duration_sec", 0)

    if not cut_times:
        return None, "WARN", "No cut timestamps in timeline"

    try:
        y, sr = librosa.load(str(music_path), sr=None)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
    except Exception as e:
        return None, "WARN", f"librosa beat detection failed: {e}"

    import numpy as np
    synced = sum(1 for t in cut_times if np.abs(beat_times - t).min() <= BEAT_SNAP_WINDOW)
    pct = synced / len(cut_times)

    if pct < BEAT_SYNC_FLOOR:
        return pct, "WARN", f"{pct:.0%} cuts on beat — low (target: ~35–40%)"
    return pct, "PASS", f"{pct:.0%} cuts on beat ✓  (Fern target: ~39%)"


def check_narration_sync(video_path):
    """Check audio/video stream duration match (no A/V drift)."""
    data = _ffprobe_json(video_path, "stream=codec_type,duration", select_streams="a:0")
    if not data or not data.get("streams"):
        return None, "WARN", "No audio stream found"

    audio_dur = float(data["streams"][0].get("duration", 0))
    vdata = _ffprobe_json(video_path, "stream=codec_type,duration", select_streams="v:0")
    if not vdata or not vdata.get("streams"):
        return None, "WARN", "No video stream found"

    video_dur = float(vdata["streams"][0].get("duration", 0))
    drift = abs(audio_dur - video_dur)

    if drift > 2.0:
        return drift, "FAIL", f"A/V drift {drift:.1f}s — audio and video durations mismatch"
    if drift > 0.5:
        return drift, "WARN", f"A/V drift {drift:.2f}s — minor (acceptable < 0.5s)"
    return drift, "PASS", f"A/V sync ✓  (drift: {drift:.2f}s)"


# ── Output ────────────────────────────────────────────────────────────────────

def print_check(name, status, message):
    c = COLORS.get(status, RESET)
    icon = ICONS.get(status, "?")
    print(f"  {c}{icon}{RESET}  {name:<22}  {message}")
    return status


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Fern video QA checker")
    ap.add_argument("video",      help="Path to final.mp4")
    ap.add_argument("--timeline", help="Path to timeline.json (auto-detected if omitted)")
    ap.add_argument("--music",    help="Path to music track (auto-detected if omitted)")
    args = ap.parse_args()

    video = Path(args.video)
    if not video.exists():
        print(f"ERROR: {video} not found", file=sys.stderr)
        sys.exit(1)

    # Auto-detect timeline.json in same dir as video
    timeline = args.timeline
    if not timeline:
        candidate = video.parent / "timeline.json"
        if candidate.exists():
            timeline = str(candidate)

    # Auto-detect music
    music = args.music
    if not music:
        for candidate in [
            Path("assets/music/track.mp3"),
            video.parent.parent.parent / "assets/music/track.mp3",
        ]:
            if candidate.exists():
                music = str(candidate)
                break

    print(f"\n{BOLD}Fern Video QA{RESET}  —  {video.name}")
    if timeline:
        print(f"  Timeline: {timeline}")
    if music:
        print(f"  Music:    {music}")
    print()

    results = []

    # Run all checks
    dur_sec, s, m = check_duration(video)
    results.append(print_check("Duration", s, m))

    _, s, m = check_cut_rate(video, dur_sec or 0)
    results.append(print_check("Cut rate", s, m))

    _, s, m = check_audio_levels(video)
    results.append(print_check("Audio levels", s, m))

    _, s, m = check_color_grade(video)
    results.append(print_check("Color grade", s, m))

    _, s, m = check_narration_sync(video)
    results.append(print_check("A/V sync", s, m))

    _, s, m = check_chapter_cards(timeline)
    results.append(print_check("Chapter cards", s, m))

    _, s, m = check_footage_variety(timeline)
    results.append(print_check("Footage variety", s, m))

    _, s, m = check_beat_sync(timeline, music)
    results.append(print_check("Beat sync", s, m))

    # Summary
    fails  = results.count("FAIL")
    warns  = results.count("WARN")
    passes = results.count("PASS")

    print()
    if fails:
        verdict = f"{RED}{BOLD}FAIL{RESET}  —  {fails} critical issue(s), {warns} warning(s). Fix before upload."
        code = 1
    elif warns:
        verdict = f"{YELLOW}{BOLD}WARN{RESET}  —  {passes} passed, {warns} warning(s). Review before upload."
        code = 0
    else:
        verdict = f"{GREEN}{BOLD}PASS{RESET}  —  all {passes} checks passed. Good to upload."
        code = 0

    print(f"Verdict: {verdict}\n")
    sys.exit(code)


if __name__ == "__main__":
    main()
