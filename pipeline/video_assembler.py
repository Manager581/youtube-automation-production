#!/usr/bin/env python3
"""
video_assembler.py — Assembles Fern-style YouTube videos from components.

Production spec (measured from actual Fern videos):
  Ken Burns: 5%/sec zoom, alternating in→out→in, ~26% segments static
  Color grade: saturation 0.46× input, black crush (push 0–7% luma to black)
  Text: slide_reveal 511ms, upper/center/lower zone by content type, hold ~9s
  Cuts: content-driven (not beat-synced), avg 4–6s per segment
  SFX: none needed — music carries continuously
  Footage: 62% document_photo, 13% documentary_photo, 6% archival_footage (measured)
  Chapter cards: white serif typewriter text on black (wkVygetgeRY style)
  Lower thirds: name + role with semi-transparent dark bar

Pipeline:
  narration_manifest.json + footage_manifest.json + music.mp3
  → per-segment clips (Ken Burns stills + archival clips)
  → color graded
  → text overlays
  → chapter cards injected at act breaks
  → concatenated
  → audio mixed (narration + music)
  → final.mp4

Chapter cards (narration_manifest.chapters field):
  [{
    "num": 1,
    "title": "A Mind Set Apart",
    "start_sec": 45.0    ← where in narration audio the chapter break occurs
  }, ...]
  NOTE: Include a [PAUSE:5.0] in the script at chapter breaks so the narration
  audio has silence for the chapter card to fill.

Lower thirds (call directly):
  from pipeline.video_assembler import add_lower_third
  add_lower_third(video_path, name="Ted Kaczynski", role="The Unabomber",
                  start_sec=10.0, end_sec=14.0, out_path=out)

Usage:
  python pipeline/video_assembler.py \\
    --brand fern_clone \\
    --narration audio/cia_mkultra/narration_manifest.json \\
    --footage footage/fern_clone/cia_mkultra/manifest.json \\
    --music assets/music/track.mp3 \\
    --out output/cia_mkultra/final.mp4

  # Dry-run (prints timeline, no render)
  python pipeline/video_assembler.py --dry-run ...
"""

import argparse
import json
import math
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Production constants — measured from Fern videos
# ---------------------------------------------------------------------------

# Ken Burns
KB_ZOOM_RATE_PER_SEC  = 0.05    # 5% scale change per second
KB_ZOOM_IN_PCT        = 0.40    # 40% of segments zoom in
KB_ZOOM_OUT_PCT        = 0.25    # 25% zoom out
KB_STATIC_PCT         = 0.26    # 26% hold static (no motion)
KB_START_ZOOM_IN       = 1.00    # zoom-in segments: start at 100%, grow
KB_START_ZOOM_OUT      = 1.30    # zoom-out segments: start at 130%, shrink back
KB_MAX_ZOOM            = 1.35    # never exceed 35% zoom (avoid aliasing)

# Color grade — matches Fern's measured saturation=0.183, black_crush=13%
COLOR_SATURATION       = 0.46    # hue filter saturation multiplier (natural → Fern)
COLOR_BLACK_CRUSH      = 0.07    # push luma below 7% to black
COLOR_CONTRAST_GAMMA   = 0.90    # slight gamma pull-down (darker midtones)

# Output
OUTPUT_RES             = "1920x1080"
OUTPUT_FPS             = 30
OUTPUT_CRF             = 18      # H.264 quality (lower = better)
MUSIC_VOLUME           = 0.18    # music under narration (headroom for voice)
MUSIC_INTRO_VOLUME     = 0.55    # music during first 3s before narration
NARRATION_VOLUME       = 1.0

# Segment timing
MIN_SEGMENT_SEC        = 2.0     # shortest a segment can be
MAX_SEGMENT_SEC        = 8.0     # longest a segment holds on one visual
DEFAULT_SEGMENT_SEC    = 4.5     # fallback when timing isn't driven by narration

# Text overlays — measured: slide_reveal 511ms, upper 48% / center 28% / lower 24%
TEXT_SLIDE_DURATION    = 0.511   # seconds for slide-in animation
TEXT_SLIDE_OFFSET_PX   = 120     # pixels off-center text starts from (slides to center)
TEXT_UPPER_Y_PCT       = 0.07    # 7% from top
TEXT_CENTER_Y_PCT      = 0.42    # ~middle of frame
TEXT_LOWER_Y_PCT       = 0.75    # 75% from top (lower third area)
TEXT_FONTSIZE          = 52
TEXT_COLOR             = "white"
TEXT_SHADOW_COLOR      = "black@0.7"
TEXT_FONT              = "Arial-Bold"  # fallback to available system font

# Chapter cards — measured from wkVygetgeRY (Unabomber): typewriter on black, serif
CHAPTER_CARD_FONT_SIZE    = 72     # Large serif title
CHAPTER_CARD_CHARS_PER_SEC = 15   # Typewriter reveal speed
CHAPTER_CARD_MIN_HOLD_SEC  = 2.0  # Hold after full text appears
CHAPTER_CARD_FADE_SEC      = 0.5  # Fade in / fade out duration
CHAPTER_CARD_SERIF_FONTS   = [    # Font preference order (macOS + Linux)
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]

# Lower third — name/role overlay with background bar
LOWER_THIRD_NAME_SIZE   = 48     # Primary name text size
LOWER_THIRD_ROLE_SIZE   = 32     # Secondary role/title size
LOWER_THIRD_BAR_H       = 110    # Background bar height (px at 1080p)
LOWER_THIRD_BAR_Y_PCT   = 0.84   # Bar top = 84% from top of frame
LOWER_THIRD_ROLE_COLOR  = "white"  # Role text color (yellow accent in some Fern videos)

# Roman numeral mapping (Fern uses I, II, III, IV, V…)
_ROMAN = ["I","II","III","IV","V","VI","VII","VIII","IX","X",
          "XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX"]

# ---------------------------------------------------------------------------
# FFmpeg helpers
# ---------------------------------------------------------------------------

def _run(cmd: list, desc: str = "", check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"FFmpeg error ({desc}):\n{result.stderr[-2000:]}")
    return result


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _escape_text(text: str) -> str:
    """Escape text for FFmpeg drawtext filter."""
    return (text
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace(":", "\\:")
            .replace("[", "\\[")
            .replace("]", "\\]"))


# ---------------------------------------------------------------------------
# Ken Burns — create video from a still image
# ---------------------------------------------------------------------------

def make_ken_burns(
    image_path: Path,
    duration_sec: float,
    direction: str,      # "zoom_in" | "zoom_out" | "static" | "pan_left" | "pan_right"
    out_path: Path,
    fps: int = OUTPUT_FPS,
) -> Path:
    """
    Render a Ken Burns motion clip from a still image using FFmpeg zoompan.
    direction is one of: zoom_in, zoom_out, static, pan_left, pan_right
    """
    n_frames = int(math.ceil(duration_sec * fps))
    zoom_per_frame = KB_ZOOM_RATE_PER_SEC / fps

    if direction == "zoom_in":
        start_z = KB_START_ZOOM_IN
        end_z   = min(start_z + KB_ZOOM_RATE_PER_SEC * duration_sec, KB_MAX_ZOOM)
        z_expr  = f"min(zoom+{zoom_per_frame:.6f},{end_z:.4f})"
        x_expr  = "iw/2-(iw/zoom/2)"
        y_expr  = "ih/2-(ih/zoom/2)"

    elif direction == "zoom_out":
        start_z = min(KB_START_ZOOM_OUT, KB_MAX_ZOOM)
        end_z   = max(start_z - KB_ZOOM_RATE_PER_SEC * duration_sec, 1.0)
        z_expr  = f"if(eq(on,1),{start_z:.4f},max(zoom-{zoom_per_frame:.6f},{end_z:.4f}))"
        x_expr  = "iw/2-(iw/zoom/2)"
        y_expr  = "ih/2-(ih/zoom/2)"

    elif direction == "pan_left":
        z_expr  = "1.15"   # slight zoom to allow panning without black bars
        x_expr  = f"iw/2-(iw/zoom/2)+((iw/zoom)*0.15*on/{n_frames})"
        y_expr  = "ih/2-(ih/zoom/2)"

    elif direction == "pan_right":
        z_expr  = "1.15"
        x_expr  = f"iw/2-(iw/zoom/2)-((iw/zoom)*0.15*on/{n_frames})"
        y_expr  = "ih/2-(ih/zoom/2)"

    else:  # static — very subtle 1% drift zoom-in (not fully static, maintains energy)
        z_expr  = f"min(zoom+{zoom_per_frame*0.2:.6f},1.05)"
        x_expr  = "iw/2-(iw/zoom/2)"
        y_expr  = "ih/2-(ih/zoom/2)"

    zoompan = (
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}'"
        f":d={n_frames}:s={OUTPUT_RES}:fps={fps}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-vf", zoompan,
        "-t", str(duration_sec),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    _run(cmd, f"ken_burns:{direction}")
    return out_path


# ---------------------------------------------------------------------------
# Color grade
# ---------------------------------------------------------------------------

def apply_color_grade(input_path: Path, out_path: Path) -> Path:
    """
    Apply Fern color grade:
      - Desaturate to 46% of input saturation (matches measured 0.183)
      - Black crush: push low luma to black
      - Slight contrast pull-down
    """
    # curves: black point at 7% (push 0→7% luma to 0)
    black_in = COLOR_BLACK_CRUSH
    # curves filter: "x1/y1 x2/y2 ..."
    # Push (0, 0) and (black_in, 0) and (1, 1) → crushes shadows
    curves = f"all='{0}/{0} {black_in:.3f}/{0} 1/1'"

    vf = (
        f"hue=s={COLOR_SATURATION},"
        f"curves={curves},"
        f"eq=gamma={COLOR_CONTRAST_GAMMA}"
    )

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    _run(cmd, "color_grade")
    return out_path


# ---------------------------------------------------------------------------
# Text overlay
# ---------------------------------------------------------------------------

def add_text_overlay(
    input_path: Path,
    text_entries: list[dict],  # [{text, start_sec, end_sec, zone}]
    out_path: Path,
) -> Path:
    """
    Add text overlays with Fern-measured slide_reveal animation (511ms).
    text_entries: [{"text": "...", "start_sec": 0.0, "end_sec": 9.0, "zone": "upper"}]
    zone: "upper" | "center" | "lower"
    Animation: text slides in from left over TEXT_SLIDE_DURATION seconds,
               then fades out in last 200ms.
    """
    if not text_entries:
        shutil.copy(input_path, out_path)
        return out_path

    font_opts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_path = next((f for f in font_opts if Path(f).exists()), "")

    drawtext_filters = []
    for entry in text_entries:
        raw_text = entry.get("text", "").strip()
        if not raw_text:
            continue
        t_start  = entry.get("start_sec", 0.0)
        t_end    = entry.get("end_sec", t_start + 9.0)
        zone     = entry.get("zone", "upper")
        slide_end = t_start + TEXT_SLIDE_DURATION
        fade_start = t_end - 0.2   # fade out last 200ms

        # Y position by zone
        if zone == "center":
            base_y_pct = TEXT_CENTER_Y_PCT
        elif zone == "lower":
            base_y_pct = TEXT_LOWER_Y_PCT
        else:  # upper
            base_y_pct = TEXT_UPPER_Y_PCT

        lines = raw_text.split("\n")[:3]
        for line_idx, line in enumerate(lines):
            escaped = _escape_text(line.upper())
            y_pos = f"h*{base_y_pct:.3f}+{line_idx * (TEXT_FONTSIZE + 10)}"

            # Slide-in x: starts TEXT_SLIDE_OFFSET_PX to the left, slides to center
            # progress = clamp((t - t_start) / TEXT_SLIDE_DURATION, 0, 1)
            # x = center_x - offset * (1 - progress)
            slide_expr = (
                f"(w-text_w)/2-{TEXT_SLIDE_OFFSET_PX}"
                f"*(1-min(1,max(0,(t-{t_start:.3f})/{TEXT_SLIDE_DURATION:.3f})))"
            )

            # Alpha: fade in over slide, hold, fade out last 200ms
            alpha_expr = (
                f"if(lt(t,{slide_end:.3f}),"
                f"  max(0,(t-{t_start:.3f})/{TEXT_SLIDE_DURATION:.3f}),"
                f"  if(gt(t,{fade_start:.3f}),"
                f"    max(0,({t_end:.3f}-t)/0.2),"
                f"    1))"
            ).replace(" ", "")

            font_arg = f":fontfile={font_path}" if font_path else ""
            drawtext_filters.append(
                f"drawtext=text='{escaped}'"
                f":fontcolor={TEXT_COLOR}"
                f":fontsize={TEXT_FONTSIZE}"
                f"{font_arg}"
                f":x='{slide_expr}'"
                f":y={y_pos}"
                f":shadowcolor={TEXT_SHADOW_COLOR}:shadowx=2:shadowy=2"
                f":alpha='{alpha_expr}'"
                f":enable='between(t,{t_start:.3f},{t_end:.3f})'"
            )

    if not drawtext_filters:
        shutil.copy(input_path, out_path)
        return out_path

    vf = ",".join(drawtext_filters)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    _run(cmd, "text_overlay")
    return out_path


# ---------------------------------------------------------------------------
# Archival clip preparation (resize + grade)
# ---------------------------------------------------------------------------

def prepare_clip(
    clip_path: Path,
    duration_sec: float,
    out_path: Path,
) -> Path:
    """Resize an archival video clip to 1080p and apply color grade."""
    vf = (
        f"scale={OUTPUT_RES}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_RES}:(ow-iw)/2:(oh-ih)/2:black,"
        f"hue=s={COLOR_SATURATION},"
        f"curves=all='0/0 {COLOR_BLACK_CRUSH:.3f}/0 1/1',"
        f"eq=gamma={COLOR_CONTRAST_GAMMA}"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(clip_path),
        "-t", str(duration_sec),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    _run(cmd, "prepare_clip")
    return out_path


# ---------------------------------------------------------------------------
# Timeline builder
# ---------------------------------------------------------------------------

def build_timeline(
    narration_manifest: dict,
    footage_manifest: dict,
    brand_config: dict,
) -> list[dict]:
    """
    Map narration chunks to visual segments.

    Returns list of segment dicts:
    {
        "start_sec": float,    # in final video
        "duration_sec": float,
        "source_type": "still" | "clip",
        "source_path": str,
        "motion": "zoom_in" | "zoom_out" | "static" | "pan_left" | "pan_right",
        "text": str | None,
        "narration_chunk_idx": int | None,
    }
    """
    chunks   = narration_manifest.get("chunks", [])
    chapters = narration_manifest.get("chapters", [])  # [{title, start_sec, num?}, ...]
    clips    = footage_manifest.get("clips", [])

    # Separate stills from video clips in footage
    stills = [c for c in clips if c.get("type") in ("still", "image", None)
              or str(c.get("path", "")).lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    videos = [c for c in clips if str(c.get("path", "")).lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]

    # Shuffle stills so they don't appear in the same order as sourced
    random.shuffle(stills)

    # Motion direction cycling: alternate zoom_in → zoom_out → static → pan → ...
    motion_cycle = _build_motion_cycle()

    # Build chapter card placeholders keyed by their target start time
    # Chapter cards are inserted BEFORE their start_sec with a time offset
    chapter_by_sec: dict[float, dict] = {}
    for ci, ch in enumerate(chapters):
        num   = ch.get("num", ci + 1)
        title = ch.get("title", f"Part {num}")
        start = float(ch.get("start_sec", 0.0))
        chapter_by_sec[start] = {"num": num, "title": title}

    segments = []
    cursor = 0.0
    still_idx = 0
    video_idx = 0
    motion_idx = 0

    for chunk_idx, chunk in enumerate(chunks):
        chunk_start = chunk.get("start_sec", cursor)
        chunk_dur   = chunk.get("duration_sec", DEFAULT_SEGMENT_SEC)
        chunk_text  = chunk.get("text", "")
        chunk_end   = chunk_start + chunk_dur

        # Inject chapter card if one is scheduled at or just before this chunk
        for ch_start in sorted(chapter_by_sec.keys()):
            if cursor <= ch_start <= chunk_start:
                ch = chapter_by_sec.pop(ch_start)
                # 0.4s black separator before card
                segments.append({
                    "start_sec": round(cursor, 3),
                    "duration_sec": 0.4,
                    "source_type": "black",
                    "source_path": None,
                    "motion": "static",
                    "text": None,
                    "text_zone": "upper",
                    "narration_chunk_idx": None,
                })
                cursor += 0.4
                # Chapter card placeholder (duration filled at render time)
                segments.append({
                    "start_sec": round(cursor, 3),
                    "duration_sec": -1,   # sentinel: filled by make_chapter_card
                    "source_type": "chapter_card",
                    "source_path": None,
                    "motion": "static",
                    "text": None,
                    "text_zone": "upper",
                    "narration_chunk_idx": None,
                    "chapter_num":   ch["num"],
                    "chapter_title": ch["title"],
                })
                cursor += 0.0   # duration updated during render

        # Extract key phrases from this chunk for text overlay
        overlay_text, overlay_zone = _extract_overlay_text(chunk_text)

        # Fill the chunk duration with one or more visual segments
        t = chunk_start
        while t < chunk_end - 0.5:
            remaining = chunk_end - t
            seg_dur = min(remaining, random.uniform(MIN_SEGMENT_SEC, MAX_SEGMENT_SEC))

            # Decide: use archival clip or still?
            # Archival clips appear roughly every 8-10 stills (~10-12% of segments)
            use_clip = (video_idx < len(videos)) and (
                (still_idx > 0 and still_idx % 9 == 0)  # every 9th segment
                or (random.random() < 0.05)              # 5% random chance
            )

            if use_clip and videos:
                clip = videos[video_idx % len(videos)]
                video_idx += 1
                segments.append({
                    "start_sec": round(t, 3),
                    "duration_sec": round(seg_dur, 3),
                    "source_type": "clip",
                    "source_path": clip.get("path", ""),
                    "motion": "natural",
                    "text": overlay_text if t == chunk_start else None,
                    "text_zone": overlay_zone if t == chunk_start else "upper",
                    "narration_chunk_idx": chunk_idx,
                })
            elif stills:
                still = stills[still_idx % len(stills)]
                still_idx += 1
                motion = motion_cycle[motion_idx % len(motion_cycle)]
                motion_idx += 1
                segments.append({
                    "start_sec": round(t, 3),
                    "duration_sec": round(seg_dur, 3),
                    "source_type": "still",
                    "source_path": still.get("path", ""),
                    "motion": motion,
                    "text": overlay_text if t == chunk_start else None,
                    "text_zone": overlay_zone if t == chunk_start else "upper",
                    "narration_chunk_idx": chunk_idx,
                })
            else:
                segments.append({
                    "start_sec": round(t, 3),
                    "duration_sec": round(seg_dur, 3),
                    "source_type": "black",
                    "source_path": None,
                    "motion": "static",
                    "text": overlay_text if t == chunk_start else None,
                    "text_zone": overlay_zone if t == chunk_start else "upper",
                    "narration_chunk_idx": chunk_idx,
                })

            t += seg_dur
            cursor = t

    return segments


def _build_motion_cycle() -> list[str]:
    """
    Build a pseudo-random motion cycle that matches Fern's measured distribution:
    40% zoom_in, 25% zoom_out, 26% static, ~9% pan
    Over 20 segments:
    """
    cycle = (
        ["zoom_in"] * 8 +
        ["zoom_out"] * 5 +
        ["static"] * 5 +
        ["pan_right", "pan_left"]
    )
    random.shuffle(cycle)
    return cycle


def _extract_overlay_text(chunk_text: str) -> tuple[str | None, str]:
    """
    Extract a short text overlay and its display zone from a narration chunk.
    Returns (text, zone) where zone is "upper" | "center" | "lower".

    Zone logic (matches Fern's measured 48%/28%/24% distribution):
      - Dates/years/facts  → upper  (fact card, top of frame)
      - Person names        → center (name reveal, mid frame)
      - Location/context    → lower  (caption style)
    """
    # Dates/years → upper zone
    year_match = re.search(r'\b(19[0-9]{2}|20[0-9]{2})\b', chunk_text)
    if year_match:
        ctx_start = max(0, year_match.start() - 20)
        ctx_end   = min(len(chunk_text), year_match.end() + 30)
        ctx = chunk_text[ctx_start:ctx_end].strip()
        words = ctx.split()[:5]
        return " ".join(words), "upper"

    # Person names (2–4 title-case words) → center zone
    person_match = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b', chunk_text)
    if person_match:
        name = person_match[0]
        # If it looks like a person name (2 title-case words, no "The/A/An")
        parts = name.split()
        filler = {"The", "A", "An", "In", "On", "At", "Of", "To", "By"}
        if len(parts) >= 2 and parts[0] not in filler:
            return name[:40], "center"
        return name[:40], "upper"

    # Location/context keywords → lower
    location_words = {"america", "united states", "russia", "china", "north korea",
                      "washington", "new york", "london", "moscow", "pentagon"}
    chunk_lower = chunk_text.lower()
    if any(w in chunk_lower for w in location_words):
        words = chunk_text.strip().split()[:4]
        return " ".join(words), "lower"

    # Generic fallback → upper
    words = chunk_text.strip().split()[:4]
    candidate = " ".join(words)
    if len(candidate) > 6:
        return candidate, "upper"

    return None, "upper"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render(
    segments: list[dict],
    narration_path: Path,
    music_path: Path | None,
    out_path: Path,
    tmp_dir: Path,
    dry_run: bool = False,
) -> Path:
    """
    Render all segments, apply grade, add text, concatenate, mix audio.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print("\n=== DRY RUN TIMELINE ===")
        for i, seg in enumerate(segments):
            dur_str = f"{seg['duration_sec']:.1f}s" if seg['duration_sec'] >= 0 else "(auto)"
            label = seg['source_type']
            if label == "chapter_card":
                label = f"CHAPTER {seg.get('chapter_num','?')}: {seg.get('chapter_title','')}"
            print(f"  [{i:03d}] {seg['start_sec']:6.1f}s  {dur_str:7s}  "
                  f"{seg['motion']:12s}  {label[:50]}"
                  + (f"  TEXT: {seg['text'][:30]}" if seg.get("text") else ""))
        total_dur = sum(s["duration_sec"] for s in segments if s["duration_sec"] >= 0)
        print(f"\nTotal (excl. chapter cards): {total_dur:.1f}s  ({total_dur/60:.1f}min)")
        print(f"Segments: {len(segments)}")
        print(f"Output: {out_path}")
        return out_path

    segment_paths = []
    print(f"\nRendering {len(segments)} segments...")

    for i, seg in enumerate(segments):
        seg_raw   = tmp_dir / f"seg_{i:04d}_raw.mp4"
        seg_graded = tmp_dir / f"seg_{i:04d}_graded.mp4"
        seg_final  = tmp_dir / f"seg_{i:04d}_final.mp4"
        dur = seg["duration_sec"]

        # Chapter cards: render with Pillow typewriter effect, skip grade
        if seg["source_type"] == "chapter_card":
            _, card_dur = make_chapter_card(
                chapter_num   = seg["chapter_num"],
                chapter_title = seg["chapter_title"],
                out_path      = seg_final,
            )
            seg["duration_sec"] = card_dur   # back-fill actual duration
            print(f"  [{i+1}/{len(segments)}] CHAPTER CARD  {card_dur:.1f}s  "
                  f"Chapter {seg['chapter_num']}: {seg['chapter_title']}  ✓")
            segment_paths.append(seg_final)
            continue

        dur = seg["duration_sec"]
        print(f"  [{i+1}/{len(segments)}] {seg['motion']:12s}  {dur:.1f}s  "
              f"{Path(seg['source_path'] or '').name[:35] if seg['source_path'] else 'BLACK'}",
              end="  ", flush=True)

        # Step 1: Create raw segment
        if seg["source_type"] == "still":
            src = Path(seg["source_path"])
            if src.exists():
                make_ken_burns(src, dur, seg["motion"], seg_raw)
            else:
                _make_black(dur, seg_raw)

        elif seg["source_type"] == "clip":
            src = Path(seg["source_path"])
            if src.exists():
                prepare_clip(src, dur, seg_raw)
            else:
                _make_black(dur, seg_raw)

        else:  # black
            _make_black(dur, seg_raw)

        # Step 2: Color grade (skip for archival clips already graded in prepare_clip)
        if seg["source_type"] == "still":
            apply_color_grade(seg_raw, seg_graded)
        else:
            seg_graded = seg_raw

        # Step 3: Text overlay
        text_entries = []
        if seg.get("text"):
            text_entries.append({
                "text": seg["text"],
                "start_sec": 0.0,
                "end_sec": min(dur - 0.1, 9.0),
                "zone": seg.get("text_zone", "upper"),
            })
        add_text_overlay(seg_graded, text_entries, seg_final)

        segment_paths.append(seg_final)
        print("✓")

    # Step 4: Concatenate all segments
    print("\nConcatenating segments...")
    raw_video = tmp_dir / "video_no_audio.mp4"
    _concat_videos(segment_paths, raw_video)

    # Step 5: Mix audio
    print("Mixing audio...")
    if music_path and music_path.exists():
        mix_audio(raw_video, narration_path, music_path, out_path)
    else:
        # Just attach narration
        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-i", str(narration_path),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ]
        _run(cmd, "attach_audio")

    print(f"\nDone → {out_path}")
    return out_path


def _make_black(duration_sec: float, out_path: Path) -> Path:
    """Create a black video segment."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:s={OUTPUT_RES}:r={OUTPUT_FPS}",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    _run(cmd, "black_frame")
    return out_path


def make_chapter_card(
    chapter_num: int,
    chapter_title: str,
    out_path: Path,
) -> tuple[Path, float]:
    """
    Render a chapter card with typewriter effect: white serif text on black.
    Matches wkVygetgeRY (Unabomber) style: "Chapter I: A Mind Set Apart"

    Returns (out_path, duration_sec).
    Uses Pillow to render a PNG sequence → FFmpeg to encode.
    """
    from PIL import Image, ImageDraw, ImageFont

    roman = _ROMAN[chapter_num - 1] if 1 <= chapter_num <= len(_ROMAN) else str(chapter_num)
    full_text = f"Chapter {roman}: {chapter_title}"

    W, H = 1920, 1080
    fps  = OUTPUT_FPS

    # Font
    font_path = next((f for f in CHAPTER_CARD_SERIF_FONTS if Path(f).exists()), None)

    def _load_font(size: int):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    font = _load_font(CHAPTER_CARD_FONT_SIZE)

    # Measure full text so we can center properly
    probe_img  = Image.new("RGB", (W, H))
    probe_draw = ImageDraw.Draw(probe_img)
    bbox = probe_draw.textbbox((0, 0), full_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x0 = (W - tw) // 2
    y0 = (H - th) // 2

    # Timing
    n_chars   = len(full_text)
    type_dur  = n_chars / CHAPTER_CARD_CHARS_PER_SEC
    total_dur = CHAPTER_CARD_FADE_SEC + type_dur + CHAPTER_CARD_MIN_HOLD_SEC + CHAPTER_CARD_FADE_SEC
    n_frames  = int(math.ceil(total_dur * fps))

    frames_dir = out_path.parent / (out_path.stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    fade_in_frames  = int(CHAPTER_CARD_FADE_SEC * fps)
    type_end_frame  = fade_in_frames + int(type_dur * fps)
    fade_out_start  = n_frames - int(CHAPTER_CARD_FADE_SEC * fps)

    for fi in range(n_frames):
        # Alpha envelope
        if fi < fade_in_frames:
            alpha = fi / max(fade_in_frames, 1)
        elif fi > fade_out_start:
            alpha = (n_frames - fi) / max(n_frames - fade_out_start, 1)
        else:
            alpha = 1.0
        alpha = max(0.0, min(1.0, alpha))

        # How many characters visible (typewriter)
        if fi <= fade_in_frames:
            chars_visible = 0
        elif fi <= type_end_frame:
            progress = (fi - fade_in_frames) / max(type_end_frame - fade_in_frames, 1)
            chars_visible = int(progress * n_chars)
        else:
            chars_visible = n_chars

        img  = Image.new("RGB", (W, H), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        if chars_visible > 0:
            visible = full_text[:chars_visible]
            gray = int(255 * alpha)
            # Subtle glow: draw slightly offset in dark gray first
            draw.text((x0 + 1, y0 + 1), visible, fill=(gray // 4, gray // 4, gray // 4), font=font)
            draw.text((x0, y0), visible, fill=(gray, gray, gray), font=font)

        frame_path = frames_dir / f"frame_{fi:06d}.png"
        img.save(str(frame_path), "PNG")

    # Encode PNG sequence → mp4
    cmd = [
        "ffmpeg", "-y",
        "-r", str(fps),
        "-i", str(frames_dir / "frame_%06d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    _run(cmd, "chapter_card")
    shutil.rmtree(frames_dir, ignore_errors=True)

    return out_path, round(total_dur, 3)


def add_lower_third(
    input_path: Path,
    name: str,
    role: str,
    start_sec: float,
    end_sec: float,
    out_path: Path,
) -> Path:
    """
    Add a lower-third name/role overlay with a dark background bar.
    Matches Fern measured style: white name + white/yellow role, semi-transparent bar.

    name: "Theodore Kaczynski"
    role: "The Unabomber" (optional, pass "" to skip)
    """
    escaped_name = _escape_text(name.upper())
    # Use fixed pixel values (output is always 1920x1080)
    bar_y_px  = int(1080 * LOWER_THIRD_BAR_Y_PCT)
    bar_h_px  = LOWER_THIRD_BAR_H
    name_y_px = bar_y_px + 10
    role_y_px = bar_y_px + 10 + LOWER_THIRD_NAME_SIZE + 8
    t_in      = start_sec
    t_out     = end_sec
    enable    = f"between(t,{t_in:.3f},{t_out:.3f})"

    # Slide-in alpha (matches standard text animation)
    slide_end   = t_in + TEXT_SLIDE_DURATION
    fade_start  = t_out - 0.2
    alpha_expr  = (
        f"if(lt(t,{slide_end:.3f}),"
        f"max(0,(t-{t_in:.3f})/{TEXT_SLIDE_DURATION:.3f}),"
        f"if(gt(t,{fade_start:.3f}),"
        f"max(0,({t_out:.3f}-t)/0.2),1))"
    ).replace(" ", "")

    font_opts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFPro.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_path = next((f for f in font_opts if Path(f).exists()), "")
    font_arg  = f":fontfile={font_path}" if font_path else ""

    filters = [
        # Semi-transparent black bar (drawbox uses w/h for input dimensions)
        f"drawbox=x=0:y={bar_y_px}:w=iw:h={bar_h_px}"
        f":color=black@0.78:t=fill:enable='{enable}'",
        # Name text (large, white) — drawtext uses w/h, not iw/ih
        f"drawtext=text='{escaped_name}'"
        f":fontcolor=white:fontsize={LOWER_THIRD_NAME_SIZE}{font_arg}"
        f":x=60:y={name_y_px}"
        f":shadowcolor=black@0.5:shadowx=2:shadowy=2"
        f":alpha='{alpha_expr}':enable='{enable}'",
    ]

    if role:
        escaped_role = _escape_text(role)
        filters.append(
            f"drawtext=text='{escaped_role}'"
            f":fontcolor={LOWER_THIRD_ROLE_COLOR}:fontsize={LOWER_THIRD_ROLE_SIZE}{font_arg}"
            f":x=60:y={role_y_px}"
            f":alpha='{alpha_expr}':enable='{enable}'"
        )

    vf = ",".join(filters)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-an",
        str(out_path),
    ]
    _run(cmd, "lower_third")
    return out_path


def _concat_videos(video_paths: list[Path], out_path: Path) -> Path:
    """Concatenate video files using ffmpeg concat demuxer."""
    list_file = out_path.parent / "_concat_list.txt"
    with open(list_file, "w") as f:
        for p in video_paths:
            f.write(f"file '{p.resolve()}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", str(OUTPUT_CRF),
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    _run(cmd, "concat")
    list_file.unlink(missing_ok=True)
    return out_path


def mix_audio(
    video_path: Path,
    narration_path: Path,
    music_path: Path,
    out_path: Path,
) -> Path:
    """
    Mix narration + music under video.
    Music ducks under narration (MUSIC_VOLUME).
    Music plays louder during first 3s intro (MUSIC_INTRO_VOLUME).
    """
    # Build filter: music volume envelope
    filter_complex = (
        f"[1:a]volume={NARRATION_VOLUME}[narr];"
        f"[2:a]volume='{MUSIC_INTRO_VOLUME}*between(t,0,3)"
        f"+{MUSIC_VOLUME}*(1-between(t,0,3))'[music];"
        f"[narr][music]amix=inputs=2:duration=first:dropout_transition=3[aout]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(narration_path),
        "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_path),
    ]
    _run(cmd, "mix_audio")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(
        description="Assemble Fern-style YouTube video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--brand", default="fern_clone")
    p.add_argument("--narration", required=True,
                   help="Path to narration_manifest.json from voice_generator.py")
    p.add_argument("--footage", required=True,
                   help="Path to footage manifest.json from footage_sourcer.py")
    p.add_argument("--music", default=None,
                   help="Path to background music .mp3/.wav")
    p.add_argument("--out", required=True,
                   help="Output .mp4 path")
    p.add_argument("--dry-run", action="store_true",
                   help="Print timeline without rendering")
    p.add_argument("--keep-tmp", action="store_true",
                   help="Keep temporary segment files")
    return p.parse_args()


def main():
    if not _ffmpeg_available():
        print("ERROR: ffmpeg not found in PATH")
        sys.exit(1)

    args = _parse_args()

    # Load manifests
    narration_path = Path(args.narration)
    footage_path   = Path(args.footage)

    if not narration_path.exists():
        print(f"ERROR: Narration manifest not found: {narration_path}")
        sys.exit(1)
    if not footage_path.exists():
        print(f"ERROR: Footage manifest not found: {footage_path}")
        sys.exit(1)

    narration_manifest = json.load(open(narration_path))
    footage_manifest   = json.load(open(footage_path))

    # Load brand config
    brand_path = Path(f"brand_configs/{args.brand}.json")
    brand_config = json.load(open(brand_path)) if brand_path.exists() else {}

    # Derive paths
    narration_audio = Path(narration_manifest.get("out", ""))
    if not narration_audio.exists():
        # Try same directory as manifest
        narration_audio = narration_path.parent / (narration_path.stem.replace("_manifest", "") + ".wav")
    if not narration_audio.exists():
        narration_audio = narration_path.parent / (narration_path.stem.replace("_manifest", "") + ".mp3")

    music_path = Path(args.music) if args.music else None
    out_path   = Path(args.out)

    print(f"Video Assembler — Fern production spec")
    print(f"  Narration: {narration_audio} ({narration_manifest.get('total_duration_sec', 0):.0f}s)")
    print(f"  Footage:   {len(footage_manifest.get('clips', []))} clips")
    print(f"  Music:     {music_path or 'none'}")
    print(f"  Output:    {out_path}")

    # Build timeline
    print("\nBuilding timeline...")
    segments = build_timeline(narration_manifest, footage_manifest, brand_config)
    total_dur = sum(s["duration_sec"] for s in segments)
    print(f"  {len(segments)} segments → {total_dur:.0f}s ({total_dur/60:.1f}min)")

    # Render
    tmp_dir = out_path.parent / "_assembler_tmp"
    try:
        render(
            segments=segments,
            narration_path=narration_audio,
            music_path=music_path,
            out_path=out_path,
            tmp_dir=tmp_dir,
            dry_run=args.dry_run,
        )
    finally:
        if not args.keep_tmp and not args.dry_run and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
