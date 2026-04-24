#!/usr/bin/env python3
"""
FFmpeg Preview Renderer — diagnostic tool for paper edit verification.

Reads breaking_law_paper_edit_v2.json and composites a low-res MP4 preview
with the actual images/clips over narration.wav.

If the preview has black sections → the paper edit data is wrong.
If it looks correct → the problem is DaVinci import, not the data.

Usage:
    cd /Users/jefflawrence/Documents/youtube-automation-production
    venv/bin/python scripts/ffmpeg_preview.py

    # With beat ID labels burned in:
    venv/bin/python scripts/ffmpeg_preview.py --labels

    # Custom output path:
    venv/bin/python scripts/ffmpeg_preview.py --output /path/to/preview.mp4
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.chapter_assembler import find_media_file, FOOTAGE_DIRS

# ─── Defaults ──────────────────────────────────────────────────────────────

PAPER_EDIT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v2.json"
NARRATION = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
CHAPTER_CARD_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "chapters"
OUTPUT = PROJECT_ROOT / "output" / "breaking_law_preview.mp4"

PREVIEW_W = 960
PREVIEW_H = 540
FPS = 24
MAX_WORKERS = 6  # parallel ffmpeg processes


# ─── Helpers ───────────────────────────────────────────────────────────────

def get_duration(path):
    """Get media duration via ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def is_image(filename):
    return Path(filename).suffix.lower() in {
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"
    }


def resolve_visual(visual_file):
    """Resolve a visual_file name to an absolute path.

    Tries EXACT match across all footage dirs FIRST, before falling back to
    prefix matching. Fixes the bug where *_still_Ns.jpg got prefix-matched
    to the source .mp4 clip.
    """
    if not visual_file:
        return None

    # Pass 1: Exact match across all footage + chapter dirs
    search_dirs = list(FOOTAGE_DIRS) + [CHAPTER_CARD_DIR]
    for search_dir in search_dirs:
        direct = Path(search_dir) / visual_file
        if direct.exists():
            return str(direct)
        for dirpath, _, filenames in os.walk(search_dir):
            if visual_file in filenames:
                return os.path.join(dirpath, visual_file)

    # Pass 2: Fall back to legacy prefix matching
    path = find_media_file(visual_file)
    if path and os.path.exists(path):
        return path

    return None


# ─── Segment renderer (runs in worker process) ────────────────────────────

def render_segment(args):
    """Render one timeline segment to an MPEG-TS file.

    Returns (index, success, beat_id, error_msg).
    """
    i, start, end, path, img, beat_id, label, tmp_dir, w, h, fps = args
    duration = end - start
    out_file = os.path.join(tmp_dir, f"seg_{i:04d}.ts")

    scale = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    )

    if label:
        # Burn beat_id + timecode into frame
        # Escape colons for ffmpeg filter syntax
        tc = f"{int(start//60):02d}\\:{start%60:05.2f}"
        drawtext = (
            f",drawtext=text='{beat_id}  {tc}':"
            f"fontsize=18:fontcolor=white:borderw=2:bordercolor=black:"
            f"x=10:y={h-30}"
        )
    else:
        drawtext = ""

    try:
        if path is None:
            # Black frame
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi",
                "-i", f"color=c=black:s={w}x{h}:d={duration:.4f}:r={fps}",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", "-an",
                "-f", "mpegts", out_file
            ]
        elif img:
            # Still image → video segment
            vf = scale + drawtext
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-loop", "1", "-t", f"{duration:.4f}",
                "-i", path,
                "-vf", vf,
                "-c:v", "libx264", "-preset", "ultrafast",
                "-tune", "stillimage",
                "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
                "-f", "mpegts", out_file
            ]
        else:
            # Video clip → trim + scale
            vf = scale + drawtext
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", path,
                "-t", f"{duration:.4f}",
                "-vf", vf,
                "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
                "-f", "mpegts", out_file
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            # Fallback: black frame
            cmd_black = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi",
                "-i", f"color=c=black:s={w}x{h}:d={duration:.4f}:r={fps}",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", "-an",
                "-f", "mpegts", out_file
            ]
            subprocess.run(cmd_black, capture_output=True, timeout=30)
            return (i, False, beat_id, result.stderr[-300:] if result.stderr else "unknown error")

        return (i, True, beat_id, "")

    except subprocess.TimeoutExpired:
        # Timeout — generate black
        cmd_black = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=black:s={w}x{h}:d={duration:.4f}:r={fps}",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-an",
            "-f", "mpegts", out_file
        ]
        subprocess.run(cmd_black, capture_output=True, timeout=30)
        return (i, False, beat_id, "timeout")

    except Exception as e:
        return (i, False, beat_id, str(e))


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FFmpeg preview renderer")
    parser.add_argument("--paper-edit", default=str(PAPER_EDIT))
    parser.add_argument("--narration", default=str(NARRATION))
    parser.add_argument("--output", "-o", default=str(OUTPUT))
    parser.add_argument("--labels", action="store_true",
                        help="Burn beat_id + timecode into each frame")
    parser.add_argument("--width", type=int, default=PREVIEW_W)
    parser.add_argument("--height", type=int, default=PREVIEW_H)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()

    w, h = args.width, args.height

    # ── Load paper edit ────────────────────────────────────────────────────
    with open(args.paper_edit) as f:
        data = json.load(f)
    beats = data["beats"]

    # ── Narration duration ─────────────────────────────────────────────────
    narr_dur = get_duration(args.narration)
    if narr_dur is None:
        print(f"ERROR: cannot read narration at {args.narration}")
        sys.exit(1)

    print(f"Narration:  {narr_dur:.1f}s ({narr_dur/60:.1f} min)")
    print(f"Beats:      {len(beats)}")
    print(f"Last beat:  ends at {beats[-1]['end_sec']:.1f}s")
    print(f"Resolution: {w}x{h}")
    print()

    # ── Resolve visuals ────────────────────────────────────────────────────
    resolved = []  # (beat, path)
    missing = []

    for beat in beats:
        vf = beat.get("visual_file", "")
        path = resolve_visual(vf)
        if path is None:
            missing.append((beat.get("beat_id", "?"), vf))
        resolved.append((beat, path))

    if missing:
        print(f"WARNING: {len(missing)} missing visual files:")
        for bid, vf in missing:
            print(f"  {bid}: {vf}")
        print()

    # ── Build timeline ─────────────────────────────────────────────────────
    # Sort by start_sec, resolve overlaps (later beat wins), fill gaps
    sorted_beats = sorted(resolved, key=lambda x: x[0]["start_sec"])

    segments = []  # (start, end, path, is_img, beat_id)
    for beat, path in sorted_beats:
        s = beat["start_sec"]
        e = beat["end_sec"]

        # Cap at narration duration
        if s >= narr_dur:
            continue
        e = min(e, narr_dur)
        if e <= s:
            continue

        # Use RESOLVED path for type detection (find_media_file may resolve
        # a .jpg still name to the .mp4 clip via prefix matching)
        check_name = path if path else beat.get("visual_file", "")
        segments.append((s, e, path, is_image(check_name) if check_name else True, beat.get("beat_id", "?")))

    # Resolve overlaps: if segment i+1 starts before segment i ends, trim i
    for i in range(len(segments) - 1):
        s_i, e_i, p_i, img_i, bid_i = segments[i]
        s_next = segments[i + 1][0]
        if s_next < e_i:
            segments[i] = (s_i, s_next, p_i, img_i, bid_i)

    # Remove zero/negative-duration segments
    segments = [(s, e, p, img, bid) for s, e, p, img, bid in segments if e - s > 0.04]

    # Fill gaps with black
    timeline = []
    prev_end = 0.0

    for s, e, path, img, bid in segments:
        if s > prev_end + 0.04:
            # Gap → black
            timeline.append((prev_end, s, None, True, "BLACK_GAP"))
        timeline.append((s, e, path, img, bid))
        prev_end = e

    # Tail to end of narration
    if prev_end < narr_dur - 0.04:
        timeline.append((prev_end, narr_dur, None, True, "BLACK_TAIL"))

    # Stats
    total_black = sum(e - s for s, e, _, _, bid in timeline if bid.startswith("BLACK"))
    total_missing = sum(e - s for s, e, p, _, _ in timeline if p is None and not _.startswith("BLACK") if False)
    # Count segments where path is None but beat_id is not BLACK
    fallback_black = sum(1 for s, e, p, _, bid in timeline if p is None and not bid.startswith("BLACK"))

    print(f"Timeline:     {len(timeline)} segments")
    print(f"Gap/black:    {total_black:.1f}s ({total_black/narr_dur*100:.1f}%)")
    if fallback_black:
        print(f"Missing file: {fallback_black} segments will render as black")
    print()

    # ── Render segments in parallel ────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="preview_")
    print(f"Temp dir: {tmp_dir}")
    print(f"Rendering {len(timeline)} segments with {args.workers} workers...")
    t0 = time.time()

    render_args = [
        (i, s, e, p, img, bid, args.labels, tmp_dir, w, h, FPS)
        for i, (s, e, p, img, bid) in enumerate(timeline)
    ]

    errors = []
    done = 0

    try:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(render_segment, ra): ra[0] for ra in render_args}

            for future in as_completed(futures):
                idx, success, beat_id, err = future.result()
                done += 1
                if not success:
                    errors.append((beat_id, err))
                if done % 50 == 0 or done == len(timeline):
                    elapsed = time.time() - t0
                    print(f"  {done}/{len(timeline)} segments ({elapsed:.0f}s)")

        if errors:
            print(f"\n{len(errors)} segment errors (rendered as black):")
            for bid, err in errors[:10]:
                print(f"  {bid}: {err[:100]}")
            print()

        # ── Concatenate segments ───────────────────────────────────────────
        print("Concatenating...")

        # Build concat file for the demuxer
        concat_path = os.path.join(tmp_dir, "concat.txt")
        ts_files = sorted(Path(tmp_dir).glob("seg_*.ts"))

        with open(concat_path, "w") as f:
            for ts in ts_files:
                f.write(f"file '{ts}'\n")

        # Concat video segments
        tmp_video = os.path.join(tmp_dir, "video_only.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "warning",
            "-f", "concat", "-safe", "0",
            "-i", concat_path,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-an",
            tmp_video
        ], check=True)

        # ── Mux with narration ─────────────────────────────────────────────
        print("Muxing narration audio...")
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "warning",
            "-i", tmp_video,
            "-i", str(args.narration),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ], check=True)

        elapsed = time.time() - t0
        size_mb = output_path.stat().st_size / (1024 * 1024)

        print(f"\n{'='*60}")
        print(f"PREVIEW READY: {output_path}")
        print(f"  Duration:   ~{narr_dur/60:.1f} min")
        print(f"  Resolution: {w}x{h}")
        print(f"  Size:       {size_mb:.0f} MB")
        print(f"  Render time: {elapsed:.0f}s")
        print(f"  Errors:     {len(errors)} segments fell back to black")
        print(f"{'='*60}")

        if total_black > 5:
            print(f"\n⚠  {total_black:.1f}s of black in timeline (gaps between beats)")
            print("   Watch the preview — if black matches script pauses, it's fine.")
            print("   If black appears mid-narration, the paper edit has coverage gaps.")

    finally:
        print(f"\nCleaning up temp dir...")
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
