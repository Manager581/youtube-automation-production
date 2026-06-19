#!/usr/bin/env python3
"""
FFmpeg Production Renderer — paper_edit_v2.json → finished 1080p MP4.

Replaces DaVinci Resolve as the assembly engine. Reads the same paper edit
JSON and produces a YouTube-ready video with:
  - Ken Burns zoom on stills (zoompan filter)
  - Text overlays (pre-rendered MOVs composited with alpha)
  - Chapter cards
  - Music (looped per chapter, pre-ducked)
  - SFX at beat timecodes
  - Clip audio moments (play_then_mute)
  - Fade from black on first beat

Usage:
    cd /Users/jefflawrence/Documents/youtube-automation-production
    venv/bin/python scripts/ffmpeg_production_render.py
    venv/bin/python scripts/ffmpeg_production_render.py --preview  # 540p fast
"""

import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile
import shutil
import time
import wave
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.chapter_assembler import (
    find_media_file, find_overlay_file, CHAPTERS, FOOTAGE_DIRS, SFX_DIR, OVERLAY_DIR,
)

# ─── Constants ─────────────────────────────────────────────────────────────

# Defaults track the latest verified paper-edit and the working narration WAV.
# Override with --paper-edit / --narration. NEVER point NARRATION at
# narration_smoothed.wav until the voice-smoother bug is fixed
# (it's currently 87.9% silent — measured 2026-04-24).
PAPER_EDIT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v11.json"
NARRATION = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
INTRO_SPEC = PROJECT_ROOT / "storyboards" / "intro_spec_locked.json"
MUSIC_DIR = PROJECT_ROOT / "audio" / "breaking_law" / "music_tracks"
CHAPTER_CARD_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "chapters"
OUTPUT = PROJECT_ROOT / "output" / "breaking_law_production.mp4"

WIDTH, HEIGHT, FPS = 1920, 1080, 24
AUDIO_SR = 48000
MUSIC_CROSSFADE = 2.0
MAX_WORKERS = 6

# SFX type name → list of actual filenames (rotated per occurrence)
# This avoids the same file being used for every "impact" in the video
SFX_TYPE_MAP = {
    "impact": ["impact_01_loud.wav", "impact_02_loud.wav", "impact_new_loud.wav"],
    "impact_hit": ["body_impact_01_loud.wav", "impact_01_loud.wav", "impact_new_loud.wav"],
    "whoosh": ["whoosh_01_loud.wav", "whoosh_02_loud.wav", "whoosh_03_loud.wav",
               "whoosh_04_loud.wav", "whoosh_05_loud.wav"],
    "tension": ["tension_01.mp3", "rumble_01_loud.wav"],
    "tension_riser": ["shimmer_01_loud.wav", "shimmer_02_loud.wav", "shimmer_03_loud.wav"],
    "tension_sting": ["impact_02_loud.wav", "glass_shatter_01_loud.wav"],
    "tension_build": ["rumble_01_loud.wav", "rumble_02_loud.wav", "rumble_03_loud.wav"],
    "tension_rumble": ["rumble_02_loud.wav", "rumble_03_loud.wav", "rumble_01_loud.wav"],
    "riser": ["shimmer_02_loud.wav", "shimmer_03_loud.wav", "shimmer_01_loud.wav"],
    "rumble": ["rumble_03_loud.wav", "rumble_01_loud.wav", "rumble_02_loud.wav"],
    "shimmer": ["shimmer_03_loud.wav", "shimmer_02_loud.wav", "shimmer_01_loud.wav"],
    "highlight": ["shimmer_01_loud.wav", "shimmer_02_loud.wav", "shimmer_03_loud.wav"],
    "glass_shatter": ["glass_shatter_new_loud.wav", "glass_shatter_01_loud.wav"],
}

# Counter used to rotate through variants per SFX type
_SFX_ROTATION = defaultdict(int)


# ─── Helpers ───────────────────────────────────────────────────────────────

def get_duration(path):
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
    return Path(filename).suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def resolve_visual(visual_file):
    """Resolve a visual filename to absolute path.

    CRITICAL: tries EXACT match across all footage dirs FIRST, before falling
    back to prefix matching. This fixes the bug where `X_still_2s.jpg` (a real
    still image on disk) was getting prefix-matched to `X.mp4` (the source
    video), causing the same opening frame to play on every _still_ beat.
    """
    if not visual_file:
        return None

    # Pass 1: Exact match across all footage dirs + chapter card dir
    search_dirs = list(FOOTAGE_DIRS) + [CHAPTER_CARD_DIR]
    for search_dir in search_dirs:
        direct = Path(search_dir) / visual_file
        if direct.exists():
            return str(direct)
        # Walk subdirectories for exact filename match
        for dirpath, _, filenames in os.walk(search_dir):
            if visual_file in filenames:
                return os.path.join(dirpath, visual_file)

    # Pass 2: Fall back to prefix matching (legacy chapter_assembler behavior)
    path = find_media_file(visual_file)
    if path and os.path.exists(path):
        return path

    return None


def resolve_sfx(sfx_type):
    """Map SFX type name to actual file path, rotating through variants."""
    if not sfx_type:
        return None
    # Already a filename?
    direct = SFX_DIR / sfx_type
    if direct.exists():
        return str(direct)
    # Rotate through variants for this type
    variants = SFX_TYPE_MAP.get(sfx_type)
    if variants:
        idx = _SFX_ROTATION[sfx_type] % len(variants)
        _SFX_ROTATION[sfx_type] += 1
        p = SFX_DIR / variants[idx]
        if p.exists():
            return str(p)
        # Fall back to first variant that exists
        for fname in variants:
            p = SFX_DIR / fname
            if p.exists():
                return str(p)
    return None


def decode_audio(path, sr=AUDIO_SR):
    """Decode any audio file to float32 stereo numpy array at target sample rate."""
    cmd = [
        "ffmpeg", "-v", "quiet", "-i", str(path),
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ar", str(sr), "-ac", "2",
        "pipe:1"
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    if r.returncode != 0 or len(r.stdout) == 0:
        return None
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2).copy()


def extract_clip_audio(video_path, duration, sr=AUDIO_SR):
    """Extract first N seconds of audio from a video file."""
    cmd = [
        "ffmpeg", "-v", "quiet",
        "-i", str(video_path),
        "-t", f"{duration:.2f}",
        "-vn",
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ar", str(sr), "-ac", "2",
        "pipe:1"
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    if r.returncode != 0 or len(r.stdout) == 0:
        return None
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2).copy()


def place_audio(mix, audio, start_sec, sr=AUDIO_SR, volume=1.0):
    """Place audio array into mix buffer at a specific time offset."""
    start_sample = int(start_sec * sr)
    end_sample = min(start_sample + len(audio), len(mix))
    chunk_len = end_sample - start_sample
    if chunk_len > 0 and start_sample >= 0:
        mix[start_sample:end_sample] += audio[:chunk_len] * volume


def apply_fade(audio, fade_in=0, fade_out=0, sr=AUDIO_SR):
    """Apply linear fade in/out to audio array (in-place)."""
    if fade_in > 0:
        n = min(int(fade_in * sr), len(audio))
        ramp = np.linspace(0, 1, n, dtype=np.float32).reshape(-1, 1)
        audio[:n] *= ramp
    if fade_out > 0:
        n = min(int(fade_out * sr), len(audio))
        ramp = np.linspace(1, 0, n, dtype=np.float32).reshape(-1, 1)
        audio[-n:] *= ramp
    return audio


# ─── Ken Burns ─────────────────────────────────────────────────────────────

def build_zoompan_filter(beat, w, h, fps):
    """Build zoompan filter string for a still image beat."""
    duration = beat["end_sec"] - beat["start_sec"]
    # Frame count from rounded cumulative positions (matches render_production_segment's
    # out_frames) so the zoom spans exactly the segment and contiguous beats telescope
    # to the narration length — int() truncation here would reintroduce per-segment drift.
    total_frames = max(round(beat["end_sec"] * fps) - round(beat["start_sec"] * fps), 1)

    zoom_speed = beat.get("zoom_speed_pct_per_sec", 3.0)
    end_scale = 1.0 + (zoom_speed / 100.0) * duration
    # Clamp to avoid excessive zoom
    end_scale = min(end_scale, 3.0)

    zoom_rate = (end_scale - 1.0) / total_frames if total_frames > 0 else 0

    zoom_target = beat.get("zoom_target", "wide")
    if zoom_target == "face":
        x_base, y_base = "iw/2-(iw/zoom/2)", "ih/3-(ih/zoom/2)"
    elif zoom_target == "document":
        x_base, y_base = "iw/3-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    else:  # wide / center
        x_base, y_base = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"

    # Event-layer enter effect (viral_recreation_spec law 4: cuts are FELT).
    # 'slam': ~0.13s scale punch (z descends 1.3x -> base) + 1-frame x jitter,
    # then the normal Ken Burns ramp continues from the landing frame.
    if beat.get("enter") == "slam" and total_frames > 4:
        n_slam = max(2, int(round(fps * 0.13)))
        z0 = min(3.0, max(end_scale, 1.0) + 0.28)
        dz = (z0 - 1.0) / n_slam
        z_expr = (f"if(lt(on,{n_slam}),{z0:.4f}-{dz:.6f}*on,"
                  f"min(1.0+{zoom_rate:.8f}*(on-{n_slam}),{end_scale:.4f}))")
        x_expr = f"'{x_base}+if(lt(on,{n_slam}),(mod(on,2)*2-1)*14,0)'"
        y_expr = f"'{y_base}'"
    else:
        z_expr = f"min(1.0+{zoom_rate:.8f}*on,{end_scale:.4f})"
        x_expr = f"'{x_base}'"
        y_expr = f"'{y_base}'"

    return (
        f"zoompan=z='{z_expr}':"
        f"x={x_expr}:y={y_expr}:"
        f"d={total_frames}:s={w}x{h}:fps={fps},"
        f"format=yuv420p"
    )


# ─── Video segment renderer ───────────────────────────────────────────────

# Black detection is tuned to MATCH the watcher's ffmpeg blackdetect
# (d=0.5:pic_th=0.98 with ffmpeg's default pix_th=0.10 → a pixel is "dark"
# below luma ~25, a frame is "black" when ≥98% of its pixels are dark). The
# h264_videotoolbox silent-black failure under sustained parallel load emits a
# UNIFORM DIM frame at luma ~14 — above a naive mean<6 cutoff yet 100% dark by
# blackdetect's pixel test. Mirroring blackdetect makes the libx264 retry fire
# on exactly what the watcher will later flag, no more and no less.
_DARK_PIX_MAX = 25       # luma at/below this counts as a "dark" pixel
_BLACK_FRAC = 0.98       # frame is black when this fraction of pixels are dark


def _segment_is_black(ts_path, duration):
    """Return True if a rendered segment measures (near-)black.

    Catches the h264_videotoolbox silent-black failure: under sustained
    parallel load the encoder can return success (returncode 0) yet emit a dim
    all-black segment, so returncode checks miss it. Samples a few frames across
    the segment (not just the midpoint) so partial-black beats — e.g. a dim
    still that is only bright where a centered text overlay covers it — are
    still caught. Returns False on any measurement error so it never blocks a
    good render.
    """
    try:
        from PIL import Image
    except Exception:
        return False
    if duration <= 0:
        return False
    # Sample interior points, skipping any 0.5s fade-in and the final frame.
    lo = min(0.55, max(duration - 0.05, 0.0))
    hi = max(duration - 0.05, lo)
    times = [lo] if hi <= lo else [lo + (hi - lo) * f for f in (0.0, 0.4, 0.8)]
    png = ts_path + ".chk.png"
    for t in times:
        try:
            # Output-seek (-ss AFTER -i): input-seek silently fails to extract a
            # frame from short MPEG-TS segments (no nearby keyframe).
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error",
                 "-i", ts_path, "-ss", f"{t:.3f}", "-frames:v", "1", png],
                capture_output=True, timeout=30,
            )
            if not os.path.exists(png):
                continue
            hist = Image.open(png).convert("L").histogram()
            total = sum(hist) or 1
            if sum(hist[:_DARK_PIX_MAX + 1]) / total >= _BLACK_FRAC:
                return True
        except Exception:
            continue
        finally:
            try:
                if os.path.exists(png):
                    os.remove(png)
            except OSError:
                pass
    return False


def render_production_segment(args):
    """Render one beat to a 1080p MPEG-TS segment.

    Returns (index, success, beat_id, error_msg).
    """
    (i, beat, path, is_img, overlay_path,
     tmp_dir, w, h, fps, use_hw) = args

    beat_id = beat.get("beat_id", f"beat_{i:04d}")
    start = beat["start_sec"]
    end = beat["end_sec"]
    duration = end - start
    out_file = os.path.join(tmp_dir, f"seg_{i:04d}.ts")

    if duration <= 0:
        return (i, False, beat_id, "zero duration")

    # Exact frame count from ROUNDED cumulative positions. The timeline is
    # contiguous (each beat's end == the next beat's start), so computing
    # round(end*fps) - round(start*fps) per segment makes the segments telescope
    # to round(narration*fps) total. The old int(duration*fps) floored every
    # segment, dropping ~one fractional frame each of ~250 times → the video ran
    # ~6s short and the visuals drifted ahead of the audio. out_frames is the
    # single source of truth for every encode path below.
    out_frames = max(round(end * fps) - round(start * fps), 1)

    encoder = "h264_videotoolbox" if use_hw else "libx264"
    enc_args = ["-b:v", "8M"] if use_hw else ["-preset", "ultrafast"]

    try:
        if path is None:
            # Black frame — pin to out_frames so gaps/tail telescope too
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi",
                "-i", f"color=c=black:s={w}x{h}:d={(out_frames + 1) / fps:.4f}:r={fps}",
                "-c:v", encoder, *enc_args,
                "-pix_fmt", "yuv420p", "-an",
                "-frames:v", str(out_frames),
                "-f", "mpegts", out_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                return (i, False, beat_id, result.stderr[-200:])
            return (i, True, beat_id, "")

        # Build video filter chain
        is_chapter_card = beat.get("visual_type") == "chapter_card"

        if is_img and not is_chapter_card:
            visual_name = os.path.basename(path) if path else ""
            is_data_chart = (visual_name.startswith("data_") or
                             "_annotated" in visual_name)

            # Skip zoompan entirely when:
            #   - it's a data chart (viewer needs to read the full chart)
            #   - the beat is long (>8s) — extended zoom is nauseating
            if is_data_chart or duration > 8.0:
                vf = (
                    f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                    f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
                )
            else:
                # Normal stills: subtle Ken Burns zoom capped at 3%/s max
                # (avoids the director's insane 20-25%/s "revelation" speeds)
                capped_beat = dict(beat)
                raw_speed = capped_beat.get("zoom_speed_pct_per_sec", 3.0)
                try:
                    raw_speed = float(raw_speed)
                except (TypeError, ValueError):
                    raw_speed = 3.0
                capped_beat["zoom_speed_pct_per_sec"] = min(raw_speed, 3.0)
                # Force all stills to center zoom — face/document targets
                # only make sense for photos with a clear subject location
                capped_beat["zoom_target"] = "wide"
                vf = build_zoompan_filter(capped_beat, w, h, fps)
        else:
            # Video clip or chapter card → scale + pad, then freeze-extend the
            # last frame (tpad) so a source SHORTER than its allotted beat still
            # fills out_frames instead of coming up short and reintroducing
            # timeline drift. No-op for clips longer than the beat — -frames:v
            # clips the output before the cloned padding is ever reached.
            vf = (
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
                f"tpad=stop_mode=clone:stop_duration=10"
            )

        # Fade from black on first beat
        if beat.get("transition_in") == "fade_from_black" or i == 0:
            vf += ",fade=in:st=0:d=0.5"

        # Reused clips start at a varied in-point (beat['src_offset'], set by
        # the dispatcher per reuse) — replaying the same opening frames is what
        # makes reuse read as "the same shot over and over".
        src_off = float(beat.get("src_offset") or 0.0)
        src_seek = ["-ss", f"{src_off:.3f}"] if src_off > 0 else []

        # Build ffmpeg command (encoder is a parameter so we can retry the
        # exact same render with libx264 if the hardware encoder misbehaves)
        def _build(enc, enc_a):
            chip_specs = beat.get("overlays") or []
            if chip_specs:
                # Within-beat positioned overlays (stat chips — restructure law:
                # stats ride as small overlays on world shots, never full-frame).
                # Each appears at its word-timed offset and rides to the cut.
                # x/y/w are FRACTIONS of the frame so previews scale correctly.
                if is_img and not is_chapter_card:
                    inputs = ["-loop", "1", "-framerate", str(fps), "-i", path]
                else:
                    inputs = [*src_seek, "-t", f"{(out_frames + 1) / fps:.4f}", "-i", path]
                fc = [f"[0:v]{vf}[bg]"]
                prev = "bg"
                for k, ov in enumerate(chip_specs):
                    inputs += ["-loop", "1", "-framerate", str(fps),
                               "-i", ov["file"]]
                    cw = int(round(w * float(ov.get("w", 0.29))))
                    px = int(round(w * float(ov.get("x", 0.04))))
                    py = int(round(h * float(ov.get("y", 0.07))))
                    at = float(ov.get("at", 0.0))
                    until = ov.get("until")          # absent = rides to the cut
                    en = (f"between(t,{at:.3f},{float(until):.3f})" if until
                          else f"gte(t,{at:.3f})")
                    fc.append(f"[{k + 1}:v]scale={cw}:-1[c{k}]")
                    fc.append(f"[{prev}][c{k}]overlay={px}:{py}:shortest=0:"
                              f"enable='{en}'[b{k}]")
                    prev = f"b{k}"
                if overlay_path and os.path.exists(overlay_path):
                    ov_dur = min(get_duration(overlay_path) or 3.0, duration)
                    idx = len(chip_specs) + 1
                    inputs += ["-t", f"{ov_dur:.4f}", "-i", overlay_path]
                    fc.append(f"[{idx}:v]format=yuva420p,scale={w}:{h}:"
                              f"force_original_aspect_ratio=decrease[ovr]")
                    fc.append(f"[{prev}][ovr]overlay=(W-w)/2:(H-h)/2:shortest=0:"
                              f"enable='between(t,0,{ov_dur:.2f})'[bo]")
                    prev = "bo"
                return [
                    "ffmpeg", "-y", "-loglevel", "error", *inputs,
                    "-filter_complex", ";".join(fc),
                    "-map", f"[{prev}]",
                    "-c:v", enc, *enc_a,
                    "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
                    "-frames:v", str(out_frames),
                    "-f", "mpegts", out_file
                ]
            if overlay_path and os.path.exists(overlay_path):
                overlay_dur = get_duration(overlay_path) or 3.0
                overlay_dur = min(overlay_dur, duration)
                if is_img and not is_chapter_card:
                    # Image + overlay: single input frame, zoompan outputs d frames
                    return [
                        "ffmpeg", "-y", "-loglevel", "error",
                        "-loop", "1", "-framerate", str(fps), "-i", path,
                        "-t", f"{overlay_dur:.4f}", "-i", overlay_path,
                        "-filter_complex",
                        f"[0:v]{vf}[bg];"
                        f"[1:v]format=yuva420p,scale={w}:{h}:force_original_aspect_ratio=decrease[ovr];"
                        f"[bg][ovr]overlay=(W-w)/2:(H-h)/2:shortest=0:enable='between(t,0,{overlay_dur:.2f})'[out]",
                        "-map", "[out]",
                        "-c:v", enc, *enc_a,
                        "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
                        "-frames:v", str(out_frames),
                        "-f", "mpegts", out_file
                    ]
                # Video + overlay
                return [
                    "ffmpeg", "-y", "-loglevel", "error",
                    *src_seek, "-t", f"{(out_frames + 1) / fps:.4f}", "-i", path,
                    "-t", f"{overlay_dur:.4f}", "-i", overlay_path,
                    "-filter_complex",
                    f"[0:v]{vf}[bg];"
                    f"[1:v]format=yuva420p,scale={w}:{h}:force_original_aspect_ratio=decrease[ovr];"
                    f"[bg][ovr]overlay=(W-w)/2:(H-h)/2:shortest=0:enable='between(t,0,{overlay_dur:.2f})'[out]",
                    "-map", "[out]",
                    "-c:v", enc, *enc_a,
                    "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
                    "-frames:v", str(out_frames),
                    "-f", "mpegts", out_file
                ]
            # No overlay
            if is_img and not is_chapter_card:
                return [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-loop", "1", "-framerate", str(fps), "-i", path,
                    "-vf", vf,
                    "-c:v", enc, *enc_a,
                    "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
                    "-frames:v", str(out_frames),
                    "-f", "mpegts", out_file
                ]
            return [
                "ffmpeg", "-y", "-loglevel", "error",
                *src_seek, "-t", f"{(out_frames + 1) / fps:.4f}", "-i", path,
                "-vf", vf,
                "-c:v", enc, *enc_a,
                "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
                "-frames:v", str(out_frames),
                "-f", "mpegts", out_file
            ]

        result = subprocess.run(_build(encoder, enc_args),
                                capture_output=True, text=True, timeout=600)

        hw_failed = result.returncode != 0
        # h264_videotoolbox can return success but emit an all-black segment
        # under sustained parallel load — measure the output to catch it.
        hw_black = (use_hw and not hw_failed and not is_chapter_card
                    and duration >= 1.0 and _segment_is_black(out_file, duration))

        if use_hw and (hw_failed or hw_black):
            # Retry this one segment with libx264 BEFORE falling back to black.
            # Software encoding is deterministic and never silent-blacks.
            retry = subprocess.run(_build("libx264", ["-preset", "medium", "-crf", "18"]),
                                   capture_output=True, text=True, timeout=600)
            if retry.returncode == 0:
                still_black = (not is_chapter_card and duration >= 1.0
                               and _segment_is_black(out_file, duration))
                if not still_black:
                    return (i, True, beat_id,
                            "recovered-hw-black" if hw_black else "recovered-hw-fail")
                return (i, False, beat_id, "black-after-libx264-retry")
            result = retry  # libx264 hard-failed too → black fallback below

        if result.returncode != 0:
            # Last resort: intentional black frame so the timeline stays aligned
            cmd_black = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi",
                "-i", f"color=c=black:s={w}x{h}:d={(out_frames + 1) / fps:.4f}:r={fps}",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", "-an",
                "-frames:v", str(out_frames),
                "-f", "mpegts", out_file
            ]
            subprocess.run(cmd_black, capture_output=True, timeout=30)
            return (i, False, beat_id, result.stderr[-300:] if result.stderr else "unknown")

        return (i, True, beat_id, "")

    except subprocess.TimeoutExpired:
        cmd_black = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=black:s={w}x{h}:d={(out_frames + 1) / fps:.4f}:r={fps}",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-an",
            "-frames:v", str(out_frames),
            "-f", "mpegts", out_file
        ]
        subprocess.run(cmd_black, capture_output=True, timeout=30)
        return (i, False, beat_id, "timeout")

    except Exception as e:
        return (i, False, beat_id, str(e))


# ─── Stage 2: Audio Mix ───────────────────────────────────────────────────

def build_audio_mix(beats, narration_path, narr_dur, chapter_map, music_by_chapter, tmp_dir,
                    duck_db=10.0):
    """Build complete stereo audio mix as a WAV file.

    Layers: narration + music + SFX + clip audio. The non-VO layers form a
    bed bus that is sidechain-DUCKED under the narration (measured 2026-06-10:
    the reference rides its voice ~22dB clearer over the bed — mid/side +26.6
    vs our +4.2; our median VO SNR was +2.1dB with 60% of windows <6dB).
    """
    total_samples = int(narr_dur * AUDIO_SR)
    mix = np.zeros((total_samples, 2), dtype=np.float32)
    vo_buf = np.zeros((total_samples, 2), dtype=np.float32)

    # ── Layer 1: Narration (with ducking during clip audio) ──────────────
    print("  Audio: decoding narration...")
    narr = decode_audio(narration_path)
    if narr is not None:
        n = min(len(narr), total_samples)
        narr_layer = narr[:n].copy()

        # Duck (silence) narration during clip audio play sections
        # so source clip audio is heard clearly
        for beat in beats:
            clip_mode = beat.get("clip_audio", "mute")
            if clip_mode not in ("play", "play_then_mute"):
                continue
            visual = beat.get("visual_file", "")
            if is_image(visual):
                continue

            clip_dur = beat.get("clip_audio_duration") or 5.0
            if isinstance(clip_dur, str):
                try:
                    clip_dur = float(clip_dur)
                except (ValueError, TypeError):
                    clip_dur = 5.0

            duck_start = int(beat["start_sec"] * AUDIO_SR)
            duck_end = min(int((beat["start_sec"] + clip_dur) * AUDIO_SR), n)
            fade_samples = int(0.3 * AUDIO_SR)  # 0.3s crossfade

            if duck_start < n and duck_end > duck_start:
                # Silence narration during clip audio
                narr_layer[duck_start:duck_end] *= 0.0
                # Smooth fade back in after clip audio ends
                fade_end = min(duck_end + fade_samples, n)
                if fade_end > duck_end:
                    ramp = np.linspace(0, 1, fade_end - duck_end, dtype=np.float32).reshape(-1, 1)
                    narr_layer[duck_end:fade_end] *= ramp

        # VO rider: even out the TTS stem's uneven sentence levels (quiet word
        # tails stayed <6dB vs the bed even at -14dB duck; reference VO is
        # broadcast-compressed). Gentle AGC toward -20dBFS, ride 0.6-2.2x.
        hop = int(0.02 * AUDIO_SR)
        env = narr_layer[:, 0].astype(np.float64)
        w = int(0.4 * AUDIO_SR)
        c = np.cumsum(np.concatenate(([0.0], env ** 2)))
        rms = np.sqrt(np.maximum((c[w:] - c[:-w]) / w, 1e-18))
        nh = max(len(env) // hop, 1)
        idx = np.minimum(np.arange(nh) * hop, len(rms) - 1) if len(rms) else None
        if idx is not None and len(rms):
            r_h = rms[idx]
            g_h = np.clip(10 ** (-20 / 20) / np.maximum(r_h, 1e-9), 0.6, 2.2)
            g_h = np.where(r_h > 10 ** (-45 / 20), g_h, 1.0)
            for _ in range(2):                       # ~smooth the ride
                g_h = np.convolve(g_h, np.ones(5) / 5, mode='same')
            ride = np.interp(np.arange(len(narr_layer), dtype=np.float64),
                             np.arange(nh) * hop, g_h).astype(np.float32)
            narr_layer *= ride.reshape(-1, 1)
        vo_buf[:n] += narr_layer            # VO bus — added after the bed ducks
    else:
        print("  WARNING: could not decode narration!")

    # ── Layer 2: Music (per chapter, looped with crossfade) ────────────────
    print("  Audio: mixing music...")
    music_cache = {}  # filename → numpy array

    for ch_num in sorted(music_by_chapter.keys()):
        music_file, ch_start, ch_end = music_by_chapter[ch_num]
        music_path = MUSIC_DIR / music_file

        if not music_path.exists():
            continue

        # Cache decoded music tracks
        if music_file not in music_cache:
            music_cache[music_file] = decode_audio(str(music_path))

        track = music_cache[music_file]
        if track is None:
            continue

        track_dur = len(track) / AUDIO_SR
        ch_duration = ch_end - ch_start

        # Loop music across chapter with crossfade overlap
        cursor = ch_start
        loop_num = 0
        while cursor < ch_end:
            remaining = ch_end - cursor
            clip_dur = min(track_dur, remaining)
            clip_samples = int(clip_dur * AUDIO_SR)

            chunk = track[:clip_samples].copy()

            # Crossfade: fade in at loop points (not first loop)
            if loop_num > 0:
                apply_fade(chunk, fade_in=MUSIC_CROSSFADE)

            # Fade out at chapter end or loop overlap
            if cursor + track_dur >= ch_end:
                apply_fade(chunk, fade_out=2.0)

            # Chapter start fade in
            if loop_num == 0:
                apply_fade(chunk, fade_in=1.0)

            # Music volume: pre-ducked tracks are already at -24dB
            place_audio(mix, chunk, cursor, volume=0.7)

            cursor += track_dur - MUSIC_CROSSFADE
            loop_num += 1
            if clip_dur < 5:
                break

    # ── Layer 3: SFX — place EVERY SFX defined in paper edit ──────────────
    print("  Audio: mixing SFX...")
    sfx_count = 0
    sfx_by_chapter = defaultdict(int)
    sfx_cache = {}

    for beat in beats:
        sfx_type = beat.get("sfx")
        if not sfx_type:
            continue

        sfx_path = resolve_sfx(sfx_type)
        if not sfx_path:
            continue

        if sfx_path in sfx_cache:
            sfx_audio = sfx_cache[sfx_path]
        else:
            sfx_audio = decode_audio(sfx_path)
            sfx_cache[sfx_path] = sfx_audio
        if sfx_audio is None:
            continue

        # Trim SFX to beat duration
        beat_dur = beat["end_sec"] - beat["start_sec"]
        max_samples = int(beat_dur * AUDIO_SR)

        # Whoosh-hit grammar (measured iteratively: whoosh-only cuts read as
        # SILENT — onset detectors and ears both want a transient ON the cut;
        # peak-aligning the swell just lands it early). So: the swell rides
        # INTO the cut, and a quiet sharp impact lands exactly ON it.
        if sfx_type == "whoosh":
            place_audio(mix, sfx_audio[:int(1.2 * AUDIO_SR)],
                        max(0.0, beat["start_sec"] - 0.45), volume=0.5)
            hit_path = resolve_sfx("impact")
            hit = sfx_cache.get(hit_path)
            if hit is None and hit_path:
                hit = decode_audio(hit_path)
                sfx_cache[hit_path] = hit
            if hit is not None:
                place_audio(mix, hit[:max_samples + AUDIO_SR],
                            beat["start_sec"], volume=0.4)
        else:
            place_audio(mix, sfx_audio[:max_samples + AUDIO_SR],
                        beat["start_sec"], volume=0.65)
        sfx_count += 1
        sfx_by_chapter[beat.get("chapter", "?")] += 1

    print(f"    {sfx_count} SFX placed: {dict(sfx_by_chapter)}")

    # ── Layer 3b: per-EVENT SFX (event layer: a sound on every within-shot
    # event — pop-ins, overlay entries — not just on cuts; spec law 4) ──────
    ev_count = 0
    for beat in beats:
        for ev in beat.get("events", []):
            sfx_path = resolve_sfx(ev.get("sfx"))
            if not sfx_path:
                continue
            if sfx_path in sfx_cache:
                sfx_audio = sfx_cache[sfx_path]
            else:
                sfx_audio = decode_audio(sfx_path)
                sfx_cache[sfx_path] = sfx_audio
            if sfx_audio is None:
                continue
            t_abs = beat["start_sec"] + float(ev.get("t", 0.0))
            place_audio(mix, sfx_audio[:int(2.5 * AUDIO_SR)], t_abs, volume=0.65)
            ev_count += 1
    if ev_count:
        print(f"    {ev_count} per-event SFX placed")

    # ── Layer 4: Clip audio (play / play_then_mute) ────────────────────────
    print("  Audio: mixing clip audio moments...")
    clip_audio_count = 0

    for beat in beats:
        clip_mode = beat.get("clip_audio", "mute")
        if clip_mode == "mute":
            continue

        visual = beat.get("visual_file", "")
        # Only video files have audio
        if is_image(visual):
            continue

        video_path = resolve_visual(visual)
        if not video_path or is_image(video_path):
            continue

        clip_dur = beat.get("clip_audio_duration") or 5.0
        if isinstance(clip_dur, str):
            try:
                clip_dur = float(clip_dur)
            except (ValueError, TypeError):
                clip_dur = 5.0

        audio = extract_clip_audio(video_path, clip_dur)
        if audio is None:
            continue

        if clip_mode == "play_then_mute":
            apply_fade(audio, fade_out=0.5)

        place_audio(mix, audio, beat["start_sec"], volume=0.8)
        clip_audio_count += 1

    print(f"    {clip_audio_count} clip audio moments placed")

    # ── Sidechain duck: bed bus under the VO ───────────────────────────────
    if duck_db > 0:
        hop = int(0.02 * AUDIO_SR)                       # 20ms hops
        env = vo_buf[:, 0].astype(np.float64)
        w50 = int(0.05 * AUDIO_SR)                       # 50ms moving RMS
        c = np.cumsum(np.concatenate(([0.0], env ** 2)))
        rms = np.sqrt(np.maximum((c[w50:] - c[:-w50]) / w50, 1e-18))
        active = np.zeros(len(env), bool)
        active[:len(rms)] = rms > 10 ** (-38 / 20)
        nh = len(env) // hop + 1
        act_h = np.array([active[i * hop:(i + 1) * hop].any() for i in range(nh)])
        g_t = np.where(act_h, 10 ** (-duck_db / 20), 1.0)
        g = np.empty_like(g_t)
        cur = 1.0
        for i, t in enumerate(g_t):                      # ~60ms attack, ~300ms release
            coef = 0.45 if t < cur else 0.93
            cur = coef * cur + (1 - coef) * t
            g[i] = cur
        gain = np.interp(np.arange(len(mix), dtype=np.float64),
                         np.arange(nh) * hop, g).astype(np.float32)
        mix *= gain.reshape(-1, 1)
        ducked_pct = 100.0 * act_h.mean()
        print(f"  Audio: bed ducked -{duck_db:.0f}dB under VO "
              f"({ducked_pct:.0f}% of timeline VO-active)")
    mix += vo_buf

    # ── Normalize ──────────────────────────────────────────────────────────
    peak = np.max(np.abs(mix))
    if peak > 0:
        target = 10 ** (-1.0 / 20)  # -1dB
        mix = mix * (target / peak)

    # ── Write WAV ──────────────────────────────────────────────────────────
    out_path = os.path.join(tmp_dir, "mixed_audio.wav")
    # Convert to int16 for WAV
    audio_int16 = (mix * 32767).clip(-32768, 32767).astype(np.int16)

    with wave.open(out_path, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(AUDIO_SR)
        wf.writeframes(audio_int16.tobytes())

    return out_path


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FFmpeg Production Renderer")
    parser.add_argument("--paper-edit", default=str(PAPER_EDIT))
    parser.add_argument("--narration", default=str(NARRATION))
    parser.add_argument("--output", "-o", default=str(OUTPUT))
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--enforce-provenance", action="store_true",
                        help="refuse to assemble any beat not from a sanctioned recipe (consistency guarantee)")
    parser.add_argument("--strict-provenance", action="store_true",
                        help="with --enforce-provenance: also require every beat to be an APPROVED recipe")
    parser.add_argument("--preview", action="store_true",
                        help="540p fast render (for checking)")
    parser.add_argument("--no-hw", action="store_true",
                        help="Disable hardware encoding (use libx264)")
    parser.add_argument("--crf", type=int, default=18,
                        help="CRF quality for final encode (default 18)")
    parser.add_argument("--duck-db", type=float, default=10.0,
                        help="sidechain-duck the bed (music+SFX+clip) this many "
                             "dB under active VO (0 = off; default 10)")
    args = parser.parse_args()

    if args.preview:
        w, h = 960, 540
    else:
        w, h = WIDTH, HEIGHT

    use_hw = not args.no_hw

    print("=" * 60)
    print("  FFmpeg Production Renderer")
    print("=" * 60)

    # ── Load paper edit ────────────────────────────────────────────────────
    with open(args.paper_edit) as f:
        data = json.load(f)
    beats = data["beats"]

    if args.enforce_provenance:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from gate_provenance import enforce
        ok, gate_summary = enforce(beats, strict=args.strict_provenance)
        print(gate_summary)
        if not ok:
            print("ABORT: provenance gate failed — not assembling.")
            sys.exit(2)

    narr_dur = get_duration(args.narration)
    if narr_dur is None:
        print("ERROR: cannot read narration")
        sys.exit(1)

    print(f"\nNarration:  {narr_dur:.1f}s ({narr_dur/60:.1f} min)")
    print(f"Beats:      {len(beats)}")
    print(f"Resolution: {w}x{h}")

    # ── Intro spec DISABLED — paper edit cold open has the right structure ──
    # The intro_spec_locked.json replaces 10 quick-cut beats with 1 long clip.
    # Paper edit beats already have correct visuals and clip_audio decisions.
    print("Intro:      using paper edit cold open (intro spec disabled)")

    # ── Close gaps between beats ───────────────────────────────────────────
    beats_sorted = sorted(beats, key=lambda b: b.get("start_sec", 0))
    gaps_closed = 0
    for i in range(len(beats_sorted) - 1):
        curr_end = beats_sorted[i].get("end_sec", 0)
        next_start = beats_sorted[i + 1].get("start_sec", 0)
        if 0 < next_start - curr_end < 2.0:
            beats_sorted[i]["end_sec"] = next_start
            gaps_closed += 1
    if gaps_closed:
        print(f"Gaps closed: {gaps_closed}")
    beats = beats_sorted

    # ── Drop beats past narration end ──────────────────────────────────────
    beats = [b for b in beats if b.get("start_sec", 0) < narr_dur]
    for b in beats:
        b["end_sec"] = min(b["end_sec"], narr_dur)

    # ── Auto intro montage: DISABLED ──────────────────────────────────────
    # Previously this auto-upgraded the first 3 cold-open video clips to
    # clip_audio="play_then_mute" with clip_audio_duration=2.5s, regardless
    # of what the director set. Result: narration was muted three times in
    # the first 15 seconds, cutting "In 2019, Facebook was fined $5 billion..."
    # mid-sentence with random source-clip audio. The director's per-beat
    # clip_audio decision is the source of truth — don't override it.
    print("Intro montage: auto-upgrade disabled (director's clip_audio honored)")

    # ── Resolve visuals + overlays ─────────────────────────────────────────
    print("\nResolving assets...")
    resolved_visuals = {}
    resolved_overlays = {}
    missing_visuals = []

    for beat in beats:
        bid = beat.get("beat_id", "?")
        vf = beat.get("visual_file", "")
        path = resolve_visual(vf)

        if path is None:
            missing_visuals.append((bid, vf))
        resolved_visuals[bid] = path

        # Resolve text overlay
        # Skip overlays in: first 15s (intro), clip_audio beats (let source clip speak),
        # chapter_card beats, and data chart beats (chart IS the visual)
        overlay_text = beat.get("text_overlay")
        skip_overlay = (
            beat.get("start_sec", 0) < 15.0 or                         # intro window
            beat.get("clip_audio", "mute") in ("play", "play_then_mute") or  # clip audio
            beat.get("visual_type") == "chapter_card"                   # chapter card
        )
        if overlay_text and not skip_overlay:
            ov_path = find_overlay_file(overlay_text)
            if ov_path and os.path.exists(ov_path):
                resolved_overlays[bid] = ov_path

    if missing_visuals:
        print(f"  WARNING: {len(missing_visuals)} missing visuals")
        for bid, vf in missing_visuals[:5]:
            print(f"    {bid}: {vf}")

    print(f"  Visuals:  {len(resolved_visuals) - len(missing_visuals)} resolved")
    print(f"  Overlays: {len(resolved_overlays)} matched")

    # ── Build chapter map for music ────────────────────────────────────────
    chapter_names_ordered = []
    chapter_map = defaultdict(list)
    for beat in beats:
        ch = beat.get("chapter", "COLD OPEN")
        if ch not in chapter_names_ordered:
            chapter_names_ordered.append(ch)
        chapter_map[ch].append(beat)

    # Music assignment
    chapter_music_map = {
        "COLD OPEN": "track_01_tense_ducked.wav",
        "THE FORMULA": "track_01_tense_ducked.wav",
        "THE DATA": "track_02_investigative_ducked.wav",
        "THE MACHINES": "track_04_dark_ducked.wav",
        "THE RENT": "track_03_emotional_ducked.wav",
        "THE RECKONING": "track_01_tense_ducked.wav",
    }

    music_by_chapter = {}
    for ch_idx, ch_name in enumerate(chapter_names_ordered):
        ch_beats = chapter_map[ch_name]
        ch_start = ch_beats[0]["start_sec"]
        ch_end = ch_beats[-1]["end_sec"]
        music_file = chapter_music_map.get(ch_name, "track_01_tense_ducked.wav")
        music_by_chapter[ch_idx] = (music_file, ch_start, ch_end)

    # ── Build timeline (same logic as preview) ─────────────────────────────
    segments = []
    for beat in beats:
        bid = beat.get("beat_id", "?")
        s = beat["start_sec"]
        e = beat["end_sec"]
        if e <= s:
            continue
        path = resolved_visuals.get(bid)
        check_name = path if path else beat.get("visual_file", "")
        img = is_image(check_name) if check_name else True
        segments.append((s, e, path, img, bid, beat))

    # Resolve overlaps
    segments.sort(key=lambda x: x[0])
    for i in range(len(segments) - 1):
        s_i, e_i, p_i, img_i, bid_i, beat_i = segments[i]
        s_next = segments[i + 1][0]
        if s_next < e_i:
            segments[i] = (s_i, s_next, p_i, img_i, bid_i, beat_i)
            beat_i["end_sec"] = s_next

    segments = [s for s in segments if s[1] - s[0] > 0.04]

    # Fill gaps with black
    timeline = []
    prev_end = 0.0
    for s, e, path, img, bid, beat in segments:
        if s > prev_end + 0.04:
            gap_beat = {"start_sec": prev_end, "end_sec": s, "beat_id": "BLACK_GAP",
                        "visual_type": "gap", "zoom_target": "wide", "zoom_speed_pct_per_sec": 0}
            timeline.append((prev_end, s, None, True, "BLACK_GAP", gap_beat))
        timeline.append((s, e, path, img, bid, beat))
        prev_end = e

    if prev_end < narr_dur - 0.04:
        tail_beat = {"start_sec": prev_end, "end_sec": narr_dur, "beat_id": "BLACK_TAIL",
                     "visual_type": "gap", "zoom_target": "wide", "zoom_speed_pct_per_sec": 0}
        timeline.append((prev_end, narr_dur, None, True, "BLACK_TAIL", tail_beat))

    total_black = sum(e - s for s, e, _, _, bid, _ in timeline if bid.startswith("BLACK"))
    print(f"\nTimeline:   {len(timeline)} segments")
    print(f"Gap/black:  {total_black:.1f}s ({total_black/narr_dur*100:.1f}%)")

    # ── Stage 1: Render video segments ─────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="production_")
    print(f"\nTemp dir: {tmp_dir}")
    t0 = time.time()

    print(f"\n{'='*40}")
    print(f"STAGE 1: Video segments ({len(timeline)} @ {w}x{h})")
    print(f"{'='*40}")

    render_args = []
    seen_uses = defaultdict(int)        # reused clips get a varied in-point —
    dur_cache = {}                      # same opening frames read as repeats
    for i, (s, e, path, img, bid, beat) in enumerate(timeline):
        if path and not img:
            n_prev = seen_uses[path]
            seen_uses[path] += 1
            if n_prev:
                if path not in dur_cache:
                    dur_cache[path] = get_duration(path) or 0.0
                head = max(dur_cache[path] - (e - s) - 0.25, 0.0)
                if head > 0.5:
                    beat["src_offset"] = round((n_prev * 1.9) % head, 3)
        overlay_path = resolved_overlays.get(bid)
        render_args.append((
            i, beat, path, img, overlay_path,
            tmp_dir, w, h, FPS, use_hw
        ))

    errors = []
    done = 0

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(render_production_segment, ra): ra[0] for ra in render_args}
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
            print(f"  {bid}: {err[:120]}")

    # ── Stage 2: Audio mix ─────────────────────────────────────────────────
    print(f"\n{'='*40}")
    print("STAGE 2: Audio mix")
    print(f"{'='*40}")

    audio_path = build_audio_mix(
        beats, args.narration, narr_dur,
        chapter_map, music_by_chapter, tmp_dir,
        duck_db=args.duck_db
    )
    print(f"  Audio mix: {os.path.getsize(audio_path) / (1024*1024):.0f} MB")

    # ── Stage 3: Final encode ──────────────────────────────────────────────
    print(f"\n{'='*40}")
    print("STAGE 3: Final encode")
    print(f"{'='*40}")

    # Concatenate TS segments
    print("  Concatenating video segments...")
    concat_path = os.path.join(tmp_dir, "concat.txt")
    ts_files = sorted(Path(tmp_dir).glob("seg_*.ts"))

    with open(concat_path, "w") as f:
        for ts in ts_files:
            f.write(f"file '{ts}'\n")

    # Final encode: concat + audio → MP4
    print(f"  Encoding final MP4 (CRF {args.crf})...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    encode_cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path)
    ]
    subprocess.run(encode_cmd, check=True)

    elapsed = time.time() - t0
    size_mb = output_path.stat().st_size / (1024 * 1024)

    print(f"\n{'='*60}")
    print(f"PRODUCTION RENDER COMPLETE")
    print(f"  Output:     {output_path}")
    print(f"  Duration:   ~{narr_dur/60:.1f} min")
    print(f"  Resolution: {w}x{h}")
    print(f"  Size:       {size_mb:.0f} MB")
    print(f"  Render time: {elapsed/60:.1f} min")
    print(f"  Errors:     {len(errors)} segments fell back to black")
    print(f"{'='*60}")

    # Cleanup
    print("\nCleaning up temp dir...")
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
