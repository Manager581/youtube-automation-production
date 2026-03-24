#!/usr/bin/env python3
"""
video_assembler.py — Assembles Fern-style YouTube videos from components.

Production spec (measured from actual Fern videos):
  Ken Burns: 5%/sec zoom, alternating in→out→in, ~26% segments static
  Color grade: saturation 0.46× input, black crush (push 0–7% luma to black)
  Text: slide_reveal 511ms, upper/center/lower zone by content type, hold ~9s
  Cuts: content-driven (not beat-synced), avg 4–6s per segment
  SFX: ~10.9% of cuts trigger impact/whoosh from assets/sfx/ (formula-measured)
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

# Ensure project root is on path for `from pipeline.xxx` imports
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from pipeline.production_rules import (
        classify_all_chunks,
        get_spec,
        load_playbook,
        pacing_range,
        playbook_motion,
        playbook_prefers_clip,
        playbook_segment_duration,
        playbook_sfx,
    )
except ImportError:
    from production_rules import (  # type: ignore[no-redef]
        classify_all_chunks,
        get_spec,
        load_playbook,
        pacing_range,
        playbook_motion,
        playbook_prefers_clip,
        playbook_segment_duration,
        playbook_sfx,
    )

# ---------------------------------------------------------------------------
# Production constants — measured from Fern videos
# ---------------------------------------------------------------------------

# Ken Burns
KB_ZOOM_RATE_PER_SEC  = 0.05    # 5% scale change per second (Fern measured baseline)
KB_ZOOM_IN_PCT        = 0.40    # 40% of segments zoom in
KB_ZOOM_OUT_PCT        = 0.25    # 25% zoom out
KB_STATIC_PCT         = 0.26    # 26% hold static (no motion)
KB_START_ZOOM_IN       = 1.00    # zoom-in segments: start at 100%, grow
KB_START_ZOOM_OUT      = 1.30    # zoom-out segments: start at 130%, shrink back
KB_MAX_ZOOM            = 1.35    # never exceed 35% zoom (avoid aliasing)

# Storyboard intensity → Ken Burns zoom rate (varies from baseline)
# tense = faster push creates anxiety; ominous = ultra-slow creates dread
KB_INTENSITY_ZOOM = {
    "tense":     0.070,   # 7%/sec — anxious energy
    "ominous":   0.025,   # 2.5%/sec — slow creeping dread
    "energized": 0.080,   # 8%/sec — momentum and pace
    "neutral":   0.050,   # 5%/sec — Fern baseline
}

# Color grade — matches Fern's measured saturation=0.183, black_crush=13%
COLOR_SATURATION       = 0.35    # hue filter saturation multiplier (Fern measured: 0.244)
COLOR_BLACK_CRUSH      = 0.07    # push luma below 7% to black
COLOR_CONTRAST_GAMMA   = 0.90    # slight gamma pull-down (darker midtones)

# Output
OUTPUT_RES             = "1920x1080"
OUTPUT_FPS             = 30
OUTPUT_CRF             = 18      # H.264 quality (lower = better)
MUSIC_VOLUME           = 0.18    # music under narration (headroom for voice)
MUSIC_INTRO_VOLUME     = 0.55    # music during first 3s before narration
NARRATION_VOLUME       = 1.8     # boost narration (source ~-30 LUFS → target ~-16)

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
TEXT_FONTSIZE          = 78
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

# SFX — formula-measured: ~10.9% of cuts trigger a sound effect
SFX_CUT_RATE   = 0.109   # probability of SFX on any visual cut
SFX_VOLUME     = 0.45    # SFX level (applied inside sfx_composite before mixing)
SFX_DIR        = Path(__file__).parent.parent / "assets" / "sfx"

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
    """Escape text for FFmpeg drawtext filter.

    Apostrophes are replaced with the visually-identical Unicode right single
    quotation mark (U+2019) so they don't break single-quote delimiters in the
    filter graph.  All other special chars are backslash-escaped.
    """
    return (text
            .replace("\\", "\\\\")
            .replace("'", "\u2019")   # avoid breaking single-quote wrapping
            .replace(":", "\\:")
            .replace("[", "\\[")
            .replace("]", "\\]"))


# ---------------------------------------------------------------------------
# Ken Burns focal point detection
# ---------------------------------------------------------------------------

# Falls back to (0.5, 0.5) if model unavailable or parse fails.
# Cache: {image}.focal.json — dict keyed by narration_hash so same image can have
# different focal points for different story moments.
# Vision-capable models only — must support image input via Ollama "images" field.
# Text-only models (qwen3.5:27b, qwen3.5:4b) are NOT included here.
FOCAL_MODEL_PREFERENCE = ["qwen2.5vl:7b", "qwen2.5vl:72b", "llava:13b", "llava:7b", "llava"]


def _focal_from_description(description: str, image_path: Path) -> tuple[float, float] | None:
    """
    Convert a text description of a focal element (e.g. "the date stamp top-right")
    into approximate (x, y) coordinates. Used when storyboard provides explicit
    focal_element text — avoids needing to call the vision model.

    Returns (fx, fy) in [0,1] or None if description gives no positional hints.
    """
    desc = description.lower()

    # Positional keywords → approximate grid coordinates
    x_hints = {"left": 0.25, "right": 0.75, "center": 0.5, "middle": 0.5}
    y_hints = {"top": 0.25, "bottom": 0.75, "upper": 0.25, "lower": 0.75,
               "center": 0.5, "middle": 0.5}

    fx, fy = None, None
    for word, val in x_hints.items():
        if word in desc:
            fx = val
            break
    for word, val in y_hints.items():
        if word in desc:
            fy = val
            break

    if fx is None and fy is None:
        # No positional hints — fall through to model detection
        return None

    return (fx or 0.5, fy or 0.5)


def detect_focal_point(
    image_path: Path,
    narration_text: str = "",
) -> tuple[float, float]:
    """
    Ask a local vision model WHERE in this image the story is pointing right now.
    The focal point is story-driven — if narration says "the date was March 14th",
    the zoom should lock onto the date on the document, not a face.

    narration_text: the script line being spoken over this image — tells the model
                    what story element to find in the frame.

    Returns (fx, fy) as fractions of frame width/height (0.0–1.0).
    Results cached per (image, narration_hash). Falls back to (0.5, 0.5).
    """
    import hashlib, urllib.request as _req

    cache_path = image_path.with_suffix(image_path.suffix + ".focal.json")
    cache_key  = hashlib.md5(narration_text.encode()).hexdigest()[:8] if narration_text else "default"

    # Check disk cache
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
            if cache_key in cache:
                d = cache[cache_key]
                return (float(d["x"]), float(d["y"]))
        except Exception:
            cache = {}
    else:
        cache = {}

    # Build story-aware prompt — focal point follows the NARRATION, not just the image
    if narration_text:
        prompt = (
            f'The narrator is saying: "{narration_text.strip()}"\n\n'
            "Given what the narrator is talking about, where in this image should "
            "the camera focus to best emphasize that story element? "
            "It could be a date, a name, a face, a signature, a building, a document detail — "
            "whatever the narration is pointing at.\n\n"
            'Return ONLY a JSON object: {"x": 0.45, "y": 0.38} '
            "where x=0.0 is left edge, x=1.0 is right edge, y=0.0 is top, y=1.0 is bottom."
        )
    else:
        prompt = (
            "Where is the most visually important element in this image? "
            'Return ONLY a JSON object: {"x": 0.45, "y": 0.38} '
            "where x=0.0 is left, x=1.0 is right, y=0.0 is top, y=1.0 is bottom."
        )

    import base64, re as _re

    for model in FOCAL_MODEL_PREFERENCE:
        try:
            # Call ollama REST API (correct way to send images)
            img_b64 = base64.b64encode(image_path.read_bytes()).decode()
            payload = json.dumps({
                "model": model,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
            }).encode()
            req = _req.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with _req.urlopen(req, timeout=60) as resp:
                response_text = json.loads(resp.read())["response"]

            match = _re.search(r'"x"\s*:\s*([\d.]+).*?"y"\s*:\s*([\d.]+)', response_text)
            if match:
                fx = max(0.05, min(0.95, float(match.group(1))))
                fy = max(0.05, min(0.95, float(match.group(2))))
                cache[cache_key] = {"x": fx, "y": fy, "model": model,
                                    "narration": narration_text[:80]}
                cache_path.write_text(json.dumps(cache, indent=2))
                return (fx, fy)
        except Exception:
            continue

    # Fallback: frame center
    return (0.5, 0.5)


# ---------------------------------------------------------------------------
# Ken Burns — create video from a still image
# ---------------------------------------------------------------------------

def make_ken_burns(
    image_path: Path,
    duration_sec: float,
    direction: str,      # "zoom_in" | "zoom_out" | "static" | "pan_left" | "pan_right" | "pan_up" | "pan_down"
    out_path: Path,
    fps: int = OUTPUT_FPS,
    focal_point: tuple[float, float] | None = None,
    zoom_rate: float = KB_ZOOM_RATE_PER_SEC,   # modulated by storyboard intensity
    parallax_engine=None,       # ParallaxEngine instance for depth parallax rendering
    visual_config=None,         # SegmentVisualConfig for story-driven overlays
    start_time: float = 0.0,    # absolute timeline position (for time-based effects)
    bg_image_path: str | None = None,  # background image for composite rendering
) -> Path:
    """
    Render a Ken Burns motion clip from a still image.

    If parallax_engine is provided: uses Depth Anything V2 parallax + numpy overlays
    (frame-by-frame, story-driven visual treatment from SegmentVisualConfig).
    Otherwise: uses FFmpeg zoompan filter (backward compatible).

    Three layers of motion (matching Fern's actual camera behavior):
      1. Primary motion — zoom or pan as specified by direction
      2. Compound drift — zooms get subtle pan; pans get subtle zoom
      3. Easing — sinusoidal ease-in-out on all motion (never constant speed)

    direction: zoom_in, zoom_out, static, pan_left, pan_right, pan_up, pan_down
    focal_point: (fx, fy) as fractions [0..1]. Zoom anchors here. Default center.
    zoom_rate: zoom %/sec change. Modulated by storyboard intensity.
    """
    # Parallax path: depth-based 3D Ken Burns with overlays (story-driven)
    if parallax_engine is not None:
        from pipeline.parallax_renderer import (
            render_segment_frames, frames_to_mp4, SegmentVisualConfig
        )
        config = visual_config or SegmentVisualConfig(
            motion_type={"zoom_in": "slow_zoom_in", "zoom_out": "slow_zoom_out",
                         "pan_left": "pan_left", "pan_right": "pan_right",
                         "pan_up": "pan_up", "pan_down": "pan_down",
                         "static": "static"}.get(direction, "slow_zoom_in"),
            motion_speed=zoom_rate * 60,
        )
        try:
            frames = render_segment_frames(
                parallax_engine, str(image_path), duration_sec, config,
                start_time=start_time, focal_point=focal_point,
                bg_image_path=bg_image_path,
            )
            frames_to_mp4(frames, str(out_path), fps)
            return out_path
        except Exception as e:
            logging.warning("Parallax render failed for %s: %s — falling back to FFmpeg",
                            image_path, e)

    # FFmpeg zoompan path (fallback when no parallax engine)
    n_frames = max(int(math.ceil(duration_sec * fps)), 1)

    # Focal point — defaults to center
    fx, fy = focal_point if focal_point else (0.5, 0.5)

    # --- Easing expression: sinusoidal ease-in-out ---
    # ease(t) = (1 - cos(t * PI)) / 2  →  0 at start, 1 at end, smooth accel/decel
    ease = f"(1-cos(on/{n_frames}*PI))/2"

    # --- Compound drift: subtle random offset unique to each segment ---
    # For zooms: camera settles toward focal (zoom_in) or drifts away (zoom_out)
    # For pans: slight perpendicular sway so motion isn't robotically straight
    drift_x = random.uniform(-0.03, 0.03)
    drift_y = random.uniform(-0.02, 0.02)

    # Helper: focal-anchored x/y with optional animated drift
    def _focal_xy(dfx: str = "0", dfy: str = "0") -> tuple[str, str]:
        """Return clamped (x_expr, y_expr) for zoompan, with drift offset."""
        ex = f"max(0,min(iw-iw/zoom,iw*({fx:.4f}+{dfx})-(iw/zoom/2)))"
        ey = f"max(0,min(ih-ih/zoom,ih*({fy:.4f}+{dfy})-(ih/zoom/2)))"
        return ex, ey

    if direction == "zoom_in":
        start_z = KB_START_ZOOM_IN
        end_z = min(start_z + zoom_rate * duration_sec, KB_MAX_ZOOM)
        delta = end_z - start_z
        # Eased zoom: starts slow, accelerates, decelerates into cut
        z_expr = f"{start_z:.4f}+{delta:.4f}*{ease}"
        # Compound: settle drift — start slightly offset, land on focal point
        dfx = f"{drift_x:.4f}*(1-{ease})"
        dfy = f"{drift_y:.4f}*(1-{ease})"
        x_expr, y_expr = _focal_xy(dfx, dfy)

    elif direction == "zoom_out":
        start_z = min(KB_START_ZOOM_OUT, KB_MAX_ZOOM)
        end_z = max(start_z - zoom_rate * duration_sec, 1.0)
        delta = start_z - end_z
        # Eased zoom out
        z_expr = f"{start_z:.4f}-{delta:.4f}*{ease}"
        # Compound: release drift — start on focal, drift away as we pull back
        dfx = f"{drift_x:.4f}*{ease}"
        dfy = f"{drift_y:.4f}*{ease}"
        x_expr, y_expr = _focal_xy(dfx, dfy)

    elif direction in ("pan_left", "pan_right", "pan_up", "pan_down"):
        # Pans get subtle zoom (1.15→1.22) instead of flat 1.15
        z_expr = f"1.15+0.07*{ease}"
        # Eased pan travel (15% of visible frame)
        eased_t = f"0.15*{ease}"
        if direction == "pan_left":
            x_expr = f"iw/2-(iw/zoom/2)+((iw/zoom)*{eased_t})"
            # Perpendicular micro-sway on y
            y_expr = f"ih/2-(ih/zoom/2)+((ih/zoom)*{drift_y:.4f}*{ease})"
        elif direction == "pan_right":
            x_expr = f"iw/2-(iw/zoom/2)-((iw/zoom)*{eased_t})"
            y_expr = f"ih/2-(ih/zoom/2)+((ih/zoom)*{drift_y:.4f}*{ease})"
        elif direction == "pan_up":
            x_expr = f"iw/2-(iw/zoom/2)+((iw/zoom)*{drift_x:.4f}*{ease})"
            y_expr = f"ih/2-(ih/zoom/2)+((ih/zoom)*{eased_t})"
        else:  # pan_down
            x_expr = f"iw/2-(iw/zoom/2)+((iw/zoom)*{drift_x:.4f}*{ease})"
            y_expr = f"ih/2-(ih/zoom/2)-((ih/zoom)*{eased_t})"

    else:  # static — micro-drift + micro-zoom (Fern never truly holds still)
        z_expr = f"1.0+0.03*{ease}"   # barely perceptible 3% zoom
        # Random directional drift so each "static" shot has unique subtle movement
        dfx = f"{drift_x:.4f}*{ease}"
        dfy = f"{drift_y:.4f}*{ease}"
        x_expr, y_expr = _focal_xy(dfx, dfy)

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

def apply_color_grade(
    input_path: Path,
    out_path: Path,
    scene_type: str = "default",
    is_clip: bool = False,
) -> Path:
    """
    Apply Fern color grade with film grain, vignette, and per-scene treatment.

    scene_type controls the look:
      "default"     — standard Fern desaturation + black crush
      "archival_bw" — full desaturation for B&W archival footage
      "document"    — warm sepia tint for documents/memos
      "cold"        — blue-shifted for clinical/institutional scenes

    is_clip: when True, uses lighter grade (no vignette, softer black crush,
             lighter gamma) to avoid crushing already-dark archival footage.
    """
    if is_clip:
        # Clips: gentle grade only — keep original brightness/contrast
        black_in = 0.03  # softer black crush (3% vs 7% for stills)
        gamma = 0.96     # barely touch gamma
        sat = min(COLOR_SATURATION * 1.4, 0.65)  # less desaturation
    else:
        black_in = COLOR_BLACK_CRUSH
        gamma = COLOR_CONTRAST_GAMMA
        sat = COLOR_SATURATION

    curves = f"all='{0}/{0} {black_in:.3f}/{0} 1/1'"

    # Base color grade varies by scene type
    if scene_type == "archival_bw":
        color = "hue=s=0"  # full desaturation
    elif scene_type == "document":
        color = f"hue=s={sat},colorbalance=rs=0.05:gs=0.02:bs=-0.03"
    elif scene_type == "cold":
        color = f"hue=s={sat},colorbalance=rs=-0.03:gs=-0.01:bs=0.05"
    else:
        color = f"hue=s={sat}"

    # Film grain: subtle temporal noise (changes per frame = organic feel)
    grain = "noise=alls=12:allf=t+u"

    if is_clip:
        # No vignette on clips — they're already produced video
        vf = (
            f"{color},"
            f"curves={curves},"
            f"eq=gamma={gamma},"
            f"{grain}"
        )
    else:
        # Vignette: darken edges to draw eye to center (Fern's measured vignetting)
        vignette = "vignette=PI/5"
        vf = (
            f"{color},"
            f"curves={curves},"
            f"eq=gamma={gamma},"
            f"{grain},"
            f"{vignette}"
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


def _scene_type_for(shot_type: str | None) -> str:
    """Map storyboard shot_type → color grade scene_type."""
    if not shot_type:
        return "default"
    st = shot_type.lower()
    if st in ("archival_footage", "archival_photo", "historical_photo"):
        return "archival_bw"
    if st in ("document_photo", "government_document", "classified_document"):
        return "document"
    if st in ("laboratory", "medical", "institutional", "autopsy"):
        return "cold"
    return "default"


# ---------------------------------------------------------------------------
# Text overlay
# ---------------------------------------------------------------------------

TYPEWRITER_CHAR_SEC = 0.04  # 40ms per character for typewriter reveal


def add_text_overlay(
    input_path: Path,
    text_entries: list[dict],  # [{text, start_sec, end_sec, zone, style?}]
    out_path: Path,
) -> Path:
    """
    Add text overlays with animation.

    text_entries: [{"text": "...", "start_sec": 0.0, "end_sec": 9.0,
                    "zone": "upper", "style": "slide"|"typewriter"}]
    zone: "upper" | "center" | "lower"
    style:
      "slide"      — Fern slide-in from left (default)
      "typewriter"  — character-by-character reveal (for dates, names, quotes)
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
        style    = entry.get("style", "slide")
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
            escaped_full = _escape_text(line.upper())
            y_pos = f"h*{base_y_pct:.3f}+{line_idx * (TEXT_FONTSIZE + 10)}"
            font_arg = f":fontfile={font_path}" if font_path else ""

            if style == "typewriter" and len(line) <= 40:
                # Typewriter: each character appears sequentially
                # Use a single drawtext with alpha based on character count reveal
                type_dur = len(line) * TYPEWRITER_CHAR_SEC
                type_end = t_start + type_dur
                # Reveal progress: 0→1 over type_dur, then hold
                # We use a text clip approach — show full text but with
                # a crop mask effect. Simpler: use drawtext with x_expr
                # that pushes a cursor, and alpha that fades in quickly.

                # Approach: render full text, use a box behind it that
                # reveals by expanding width. Simpler: just fade in quickly
                # char-by-char isn't native in ffmpeg, so we use a fast
                # fade (0.3s) combined with a brief left-to-right slide
                # that feels like typewriter.
                slide_expr = (
                    f"(w-text_w)/2-{TEXT_SLIDE_OFFSET_PX // 2}"
                    f"*(1-min(1,max(0,(t-{t_start:.3f})/{type_dur:.3f})))"
                )
                alpha_expr = (
                    f"if(lt(t,{type_end:.3f}),"
                    f"  min(1,max(0,(t-{t_start:.3f})/{type_dur:.3f})),"
                    f"  if(gt(t,{fade_start:.3f}),"
                    f"    max(0,({t_end:.3f}-t)/0.2),"
                    f"    1))"
                ).replace(" ", "")

                drawtext_filters.append(
                    f"drawtext=text='{escaped_full}'"
                    f":fontcolor={TEXT_COLOR}"
                    f":fontsize={TEXT_FONTSIZE}"
                    f"{font_arg}"
                    f":x='{slide_expr}'"
                    f":y={y_pos}"
                    f":shadowcolor={TEXT_SHADOW_COLOR}:shadowx=2:shadowy=2"
                    f":alpha='{alpha_expr}'"
                    f":enable='between(t,{t_start:.3f},{t_end:.3f})'"
                )
            else:
                # Standard slide-in animation
                slide_end = t_start + TEXT_SLIDE_DURATION
                slide_expr = (
                    f"(w-text_w)/2-{TEXT_SLIDE_OFFSET_PX}"
                    f"*(1-min(1,max(0,(t-{t_start:.3f})/{TEXT_SLIDE_DURATION:.3f})))"
                )
                alpha_expr = (
                    f"if(lt(t,{slide_end:.3f}),"
                    f"  max(0,(t-{t_start:.3f})/{TEXT_SLIDE_DURATION:.3f}),"
                    f"  if(gt(t,{fade_start:.3f}),"
                    f"    max(0,({t_end:.3f}-t)/0.2),"
                    f"    1))"
                ).replace(" ", "")

                drawtext_filters.append(
                    f"drawtext=text='{escaped_full}'"
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

    # Escape commas inside each drawtext filter (min/max/between expressions)
    # so ffmpeg doesn't treat them as filter-chain separators.
    vf = ",".join(f.replace(",", "\\,") for f in drawtext_filters)
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
    start_sec: float = 0.0,
) -> Path:
    """Resize an archival video clip to 1080p and apply color grade.

    start_sec: offset into the clip to begin from (from clip_analyzer.find_best_moment).
    """
    pad_res = OUTPUT_RES.replace("x", ":")   # ffmpeg pad needs 1920:1080
    vf = (
        f"scale={OUTPUT_RES}:force_original_aspect_ratio=decrease,"
        f"pad={pad_res}:(ow-iw)/2:(oh-ih)/2:black,"
        f"hue=s={COLOR_SATURATION},"
        f"curves=all='0/0 {COLOR_BLACK_CRUSH:.3f}/0 1/1',"
        f"eq=gamma={COLOR_CONTRAST_GAMMA}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", str(clip_path),
        "-t", str(duration_sec),
        "-vf", vf,
        "-r", str(OUTPUT_FPS),   # force consistent fps for concat
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    _run(cmd, "prepare_clip")
    return out_path


# ---------------------------------------------------------------------------
# Beat sync helpers
# ---------------------------------------------------------------------------

# Fern measured: ~39% of cuts land within 100ms of a beat.
# We snap any cut that naturally falls within BEAT_SNAP_WINDOW of a beat.
# At 116 BPM (beat every 0.517s), a ±0.1s window gives ~39% natural snap rate.
BEAT_SNAP_WINDOW = 0.10   # seconds on either side of a beat


def load_beat_times(music_path: Path) -> list[float]:
    """
    Return sorted list of beat timestamps (seconds) from a music file.
    Uses librosa beat tracker. Cached in memory per path for the process lifetime.
    Returns [] if librosa unavailable or file unreadable.
    """
    try:
        import librosa
        y, sr = librosa.load(str(music_path), sr=None, mono=True)
        _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        return librosa.frames_to_time(beat_frames, sr=sr).tolist()
    except Exception:
        return []


def snap_to_beat(
    t_start: float,
    desired_end: float,
    beat_times: list[float],
    min_dur: float,
    max_dur: float,
) -> float:
    """
    If a beat falls within BEAT_SNAP_WINDOW of desired_end AND the resulting
    duration stays within [min_dur, max_dur], return the beat time.
    Otherwise return desired_end unchanged.
    """
    for beat in beat_times:
        if abs(beat - desired_end) <= BEAT_SNAP_WINDOW:
            new_dur = beat - t_start
            if min_dur <= new_dur <= max_dur:
                return beat
    return desired_end


# ---------------------------------------------------------------------------
# Timeline builder
# ---------------------------------------------------------------------------

def _find_storyboard_match(
    chunk_text: str,
    storyboard: list,
    start_idx: int = 0,
) -> int | None:
    """
    Find the storyboard entry (by index) that best matches a narration chunk.
    Uses word-overlap (Jaccard similarity). Returns None if no confident match.

    start_idx: search forward from this index (sequential matching — narration
    and storyboard are generated from the same script in the same order).
    Allows a small lookback in case of minor segment misalignment.
    """
    chunk_words = set(w.lower() for w in chunk_text.split() if len(w) > 3)
    if not chunk_words:
        return None
    # Windowed search: look from slightly before start_idx up to +20 entries.
    # This prevents matching already-passed storyboard segments while tolerating
    # the different segmentation granularity (narration chunks are larger than
    # storyboard entries — typically 4:1 ratio).
    search_from = max(0, start_idx - 2)
    search_to   = min(len(storyboard), start_idx + 20)
    best_score = 0.0
    best_idx = None
    for i in range(search_from, search_to):
        entry = storyboard[i]
        if entry.get("shot_type") == "chapter_card":
            continue
        entry_words = set(w.lower() for w in entry.get("text", "").split() if len(w) > 3)
        if not entry_words:
            continue
        union = len(chunk_words | entry_words)
        overlap = len(chunk_words & entry_words) / max(union, 1)
        if overlap > best_score:
            best_score = overlap
            best_idx = i
    return best_idx if best_score >= 0.15 else None


def _chapters_from_storyboard(storyboard: list, chunks: list) -> list:
    """
    Extract chapter timing from storyboard is_chapter_break entries.
    Places each chapter at the nearest large pause gap (≥3s) between speech
    chunks — these are the [PAUSE:5.0] / [PAUSE:3.0] markers written into
    the script specifically for chapter breaks.

    Falls back to proportional mapping if there aren't enough pause gaps.
    Called by build_timeline() when the narration manifest has no chapters.
    """
    chapter_entries = [e for e in storyboard if e.get("is_chapter_break")]
    if not chapter_entries or not chunks:
        return []

    # Find large pause gaps between speech chunks.
    pause_gaps = []
    for ci in range(len(chunks) - 1):
        chunk_end_t = chunks[ci].get("start_sec", 0) + chunks[ci].get("duration_sec", 0)
        next_start = chunks[ci + 1].get("start_sec", chunk_end_t)
        gap = next_start - chunk_end_t
        if gap >= 3.0:
            pause_gaps.append((chunk_end_t, gap))

    # Prefer 5.0s gaps (explicit chapter breaks), then 3.0s gaps as fallback.
    pause_5s = sorted([p for p in pause_gaps if p[1] >= 4.5])
    pause_3s = sorted([p for p in pause_gaps if p[1] < 4.5])
    available = list(pause_5s)
    if len(available) < len(chapter_entries):
        available.extend(pause_3s[:len(chapter_entries) - len(available)])
    available.sort()  # chronological order

    chapters = []
    for i, entry in enumerate(chapter_entries):
        if i < len(available):
            start_sec = available[i][0]
        else:
            # Fallback: proportional mapping for excess chapters
            total_sb = max(len(storyboard) - 1, 1)
            total_chunks = max(len(chunks) - 1, 1)
            try:
                sb_idx = storyboard.index(entry)
            except ValueError:
                sb_idx = i
            chunk_idx = min(int(round(sb_idx / total_sb * total_chunks)),
                            len(chunks) - 1)
            start_sec = chunks[chunk_idx].get("start_sec", 0.0)

        chapters.append({
            "num":   entry.get("chapter_num", len(chapters) + 2),
            "title": entry.get("chapter_title", f"Part {len(chapters) + 2}"),
            "start_sec": start_sec,
        })
    return chapters


def build_timeline(
    narration_manifest: dict,
    footage_manifest: dict,
    brand_config: dict,
    beat_times: list[float] | None = None,
    detect_focal_points: bool = False,
    storyboard: list | None = None,
    stills_only: bool = False,
) -> list[dict]:
    """
    Map narration chunks to visual segments.

    storyboard: optional list of storyboard entries (from storyboard_generator.py).
    When provided, clips tagged with matching storyboard_segment_ids are preferred
    over round-robin selection — giving story-specific footage for each moment.

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
    # voice_generator outputs "segments"; legacy manifests may use "chunks".
    # Filter to speech-only — drop pause segments that have no visual content.
    chunks = narration_manifest.get("chunks") or [
        s for s in narration_manifest.get("segments", [])
        if s.get("type", "speech") == "speech"
    ]
    chapters = narration_manifest.get("chapters", [])
    # Merge clips + images from manifest (footage_sourcer uses "clips",
    # Pixabay sourcer uses "images" — both are valid footage sources)
    clips = footage_manifest.get("clips", []) + footage_manifest.get("images", [])

    # If the narration manifest has no chapter data but a storyboard was provided,
    # extract chapter timing from the storyboard's is_chapter_break entries.
    # This covers the common case where voice_generator doesn't write chapters.
    if not chapters and storyboard:
        chapters = _chapters_from_storyboard(storyboard, chunks)
        if chapters:
            print(f"  Chapters extracted from storyboard: {len(chapters)} chapter breaks")

    # Extend each speech chunk's visual coverage to fill the pause gap after it.
    # The narration WAV includes pauses between chunks, so the visual timeline must
    # match — otherwise A/V drift accumulates (visuals end before audio).
    total_narration_dur = narration_manifest.get("total_duration_sec", 0)

    # Build a set of chapter card start positions so we can skip those gaps.
    chapter_starts = {float(ch.get("start_sec", -1)) for ch in chapters}

    for ci in range(len(chunks)):
        speech_end = chunks[ci].get("start_sec", 0) + chunks[ci].get("duration_sec", 0)
        if ci + 1 < len(chunks):
            next_start = chunks[ci + 1].get("start_sec", speech_end)
            # Don't extend into pause gaps that have chapter cards — those cards
            # fill the gap themselves. Extending into them double-counts duration.
            if speech_end in chapter_starts:
                chunks[ci]["_visual_end"] = speech_end
            else:
                chunks[ci]["_visual_end"] = next_start
        else:
            chunks[ci]["_visual_end"] = total_narration_dur or speech_end

    # Pre-compute lower-third events (first occurrence of each named person)
    lower_third_map = _detect_named_persons(chunks)

    # Normalize all clip/image entries to have local_path + downloaded flag.
    # Pixabay images use "filename" (relative to output_dir), clips use "local_path".
    _output_dir = footage_manifest.get("output_dir", "")
    for c in clips:
        if not c.get("local_path") and c.get("filename"):
            c["local_path"] = str(Path(_output_dir) / c["filename"])
        if "downloaded" not in c:
            # Infer: if the file exists, mark as downloaded
            lp = c.get("local_path") or c.get("path") or ""
            c["downloaded"] = Path(lp).exists() if lp else False

    # Separate stills from video clips in footage.
    def _clip_path_str(c):
        return str(c.get("local_path") or c.get("path") or "")

    _STILL_EXTS = (".jpg", ".jpeg", ".png", ".webp")
    stills = [
        c for c in clips
        if c.get("downloaded") and (
            c.get("type") in ("still", "image")
            or _clip_path_str(c).lower().endswith(_STILL_EXTS)
        ) and _clip_path_str(c).lower().endswith(_STILL_EXTS)  # reject unsupported formats
    ]
    if stills_only:
        videos = []
    else:
        videos = [
            c for c in clips
            if c.get("downloaded") and
            _clip_path_str(c).lower().endswith((".mp4", ".mov", ".mkv", ".webm"))
        ]

    # Shuffle stills so they don't appear in the same order as sourced
    random.shuffle(stills)

    # Classify every chunk by content type using the production rules engine.
    # This replaces the old random motion_cycle + flat SFX_CUT_RATE approach.
    total_dur_sec = sum(c.get("duration_sec", DEFAULT_SEGMENT_SEC) for c in chunks)
    chunk_types = classify_all_chunks(chunks, total_duration_sec=total_dur_sec)

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
    sb_cursor = 0   # sequential storyboard pointer — advances as we match chunks
    _prev_still_path = None   # track last image for Ken Burns continuity
    _prev_motion = None       # maintain motion direction across same-image sub-segments
    # Rhythm breathing tracker: alternates long holds ↔ burst cuts
    _rhythm_accum = 0.0       # seconds accumulated in current mode
    _rhythm_burst = False     # True = burst mode (short cuts), False = normal

    for chunk_idx, chunk in enumerate(chunks):
        chunk_start  = chunk.get("start_sec", cursor)
        chunk_dur    = chunk.get("duration_sec", DEFAULT_SEGMENT_SEC)
        chunk_text   = chunk.get("text", "")
        # Use _visual_end to cover trailing pause gap (if set), otherwise
        # fall back to speech-only end for backward compatibility.
        chunk_end    = chunk.get("_visual_end", chunk_start + chunk_dur)
        content_type = chunk_types[chunk_idx]
        spec         = get_spec(content_type)

        # Inject chapter card if one is scheduled at or just before this chunk.
        # _visual_end was NOT extended into chapter-card gaps, so the card fills
        # the gap without double-counting.
        for ch_start in sorted(chapter_by_sec.keys()):
            if cursor <= ch_start <= chunk_start:
                ch = chapter_by_sec.pop(ch_start)
                # Playbook 5-step chapter transition:
                # 1. Concluding punch (in narration — no code change needed)
                # 2. Dramatic silence: 2-5s black (replaces old 0.4s)
                # 3. Music bridge (handled by [PAUSE:5.0+] in script audio)
                # Look for transition_spec from storyboard chapter entry
                _silence_dur = 3.0   # default
                if storyboard:
                    for sb_e in storyboard:
                        if (sb_e.get("is_chapter_break")
                                and sb_e.get("chapter_title") == ch.get("title")):
                            ts = sb_e.get("transition_spec", {})
                            sil_range = ts.get("silence_sec", [2, 5])
                            _silence_dur = random.uniform(sil_range[0], sil_range[1])
                            break
                segments.append({
                    "start_sec": round(cursor, 3),
                    "duration_sec": round(_silence_dur, 3),
                    "source_type": "black",
                    "source_path": None,
                    "motion": "static",
                    "text": None,
                    "text_zone": "upper",
                    "narration_chunk_idx": None,
                })
                cursor += _silence_dur
                # Pre-compute card duration (same formula as make_chapter_card)
                roman_idx = min(ch["num"] - 1, len(_ROMAN) - 1) if ch["num"] >= 1 else 0
                full_text = f"Chapter {_ROMAN[roman_idx]}: {ch['title']}"
                _card_dur = (CHAPTER_CARD_FADE_SEC
                             + len(full_text) / CHAPTER_CARD_CHARS_PER_SEC
                             + CHAPTER_CARD_MIN_HOLD_SEC
                             + CHAPTER_CARD_FADE_SEC)
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
                cursor += _card_dur   # advance cursor past the card

        # ── DP7: Text overlay ─────────────────────────────────────────
        # Prefer storyboard text_overlay_type when available
        overlay_text, overlay_zone = _extract_overlay_text(chunk_text)
        if spec.text_zone != "auto":
            overlay_zone = spec.text_zone

        # Storyboard match — done before pacing and inner loop so the
        # narrative_function override applies to ALL visual segments in this chunk.
        sb_entry_idx = None
        sb_focal_element = None
        sb_intensity = "neutral"
        sb_entry = None
        if storyboard:
            sb_entry_idx = _find_storyboard_match(chunk_text, storyboard,
                                                  start_idx=sb_cursor)
            if sb_entry_idx is not None:
                sb_cursor = sb_entry_idx
                sb_entry = storyboard[sb_entry_idx]
                sb_focal_element = sb_entry.get("focal_element")
                sb_intensity     = sb_entry.get("intensity", "neutral")
                sb_narrative_fn = sb_entry.get("narrative_function")
                if sb_narrative_fn and sb_narrative_fn not in ("chapter_break",):
                    content_type = sb_narrative_fn
                    spec = get_spec(content_type)
                    if spec.text_zone != "auto":
                        overlay_zone = spec.text_zone

                # DP7 enrichment: storyboard text_overlay_type → semantic overlay
                sb_overlay_type = sb_entry.get("text_overlay_type")
                if sb_overlay_type and sb_overlay_type != "null":
                    if sb_overlay_type == "person_identification":
                        # Extract FULL NAME from text
                        names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", chunk_text)
                        if names:
                            overlay_text = names[0].upper()
                            overlay_zone = "center"
                    elif sb_overlay_type == "entity_label":
                        acronyms = re.findall(r"\b[A-Z]{2,}\b", chunk_text)
                        real = [a for a in acronyms if a not in ("THE", "AND", "FOR", "BUT")]
                        if real:
                            overlay_text = real[0]
                            overlay_zone = "center"
                    elif sb_overlay_type == "location_label":
                        overlay_zone = "lower"
                    elif sb_overlay_type == "quote":
                        quotes = re.findall(r'"([^"]{10,})"', chunk_text)
                        if quotes:
                            overlay_text = f'"{quotes[0]}"'
                            overlay_zone = "center"

        # ── DP2: Segment duration ─────────────────────────────────────
        # Prefer storyboard hold_duration_range, fallback to playbook by shot_type,
        # then existing pacing_range.
        if sb_entry and "hold_duration_range" in sb_entry:
            min_seg, max_seg = sb_entry["hold_duration_range"]
        elif sb_entry and sb_entry.get("shot_type"):
            min_seg, max_seg = playbook_segment_duration(
                sb_entry["shot_type"], content_type)
        else:
            min_seg, max_seg = pacing_range(spec.cut_pacing)

        # Burst mode: rapid 2-4s cuts during peak intensity moments
        # Only triggers at "intense" level on reveal/climax (not every tension_build)
        if sb_intensity == "intense" and content_type in (
                "reveal", "climax", "stakes_moment"):
            if not _rhythm_burst:
                _rhythm_burst = True
                _rhythm_accum = 0.0
            min_seg = min(min_seg, 2.0)
            max_seg = min(max_seg, 4.0)
        elif _rhythm_burst and _rhythm_accum > 8.0:
            # After 8s of bursts, return to normal breathing
            _rhythm_burst = False
            _rhythm_accum = 0.0

        # Story-tagged footage: collect ALL stills/clips matching the current
        # storyboard window so sub-segments can rotate through them instead of
        # reusing the same image for every cut within a chunk.
        tagged_stills = []
        tagged_clip   = None
        if sb_entry_idx is not None and storyboard:
            search_ids = set(range(sb_cursor, min(sb_cursor + 6, len(storyboard))))
            for s in stills:
                if search_ids & set(s.get("storyboard_segment_ids", [])):
                    tagged_stills.append(s)
            for c in videos:
                if search_ids & set(c.get("storyboard_segment_ids", [])):
                    tagged_clip = c
                    break
        tagged_still_idx = 0

        # Fill the chunk duration with one or more visual segments
        t = chunk_start
        while t < chunk_end - 0.5:
            remaining = chunk_end - t
            raw_end = t + min(remaining, random.uniform(min_seg, max_seg))
            if beat_times:
                raw_end = snap_to_beat(t, raw_end, beat_times, min_seg, min(remaining, max_seg))
            seg_dur = raw_end - t
            is_chunk_start = (t == chunk_start)

            # ── DP3: Motion type + speed ──────────────────────────────
            # Prefer storyboard motion_direction, fallback to playbook resolver,
            # then existing weighted random.
            if sb_entry and "motion_direction" in sb_entry:
                motion = sb_entry["motion_direction"]
            else:
                motion = spec.weighted_motion()

            # ── DP4: SFX ──────────────────────────────────────────────
            # Prefer Director-provided SFX (content-matched), then playbook,
            # then existing probability.
            _sfx_is_director = False
            director_sfx = sb_entry.get("sfx") if sb_entry else None
            if isinstance(director_sfx, dict) and director_sfx.get("type"):
                seg_sfx = director_sfx["type"]
                _sfx_is_director = True
            else:
                sb_cut_mot = sb_entry.get("cut_motivation") if sb_entry else None
                seg_sfx_type = playbook_sfx(content_type, sb_cut_mot)
                if seg_sfx_type:
                    seg_sfx = seg_sfx_type
                    _sfx_is_director = True
                elif random.random() < spec.sfx_probability:
                    seg_sfx = spec.sfx_type
                    _sfx_is_director = False
                else:
                    seg_sfx = None
                    _sfx_is_director = False

            # Lower third: first segment of chunk, if this chunk introduces a named person
            lt_info = lower_third_map.get(chunk_idx) if is_chunk_start else None
            seg_lower_third = {"name": lt_info[0], "role": lt_info[1]} if lt_info else None

            # ── DP5: Clip vs still ────────────────────────────────────
            # Prefer playbook shot_type classification, fallback to existing probability.
            sb_shot_type = sb_entry.get("shot_type") if sb_entry else None
            if sb_shot_type and playbook_prefers_clip(sb_shot_type):
                use_clip = bool(tagged_clip) or (video_idx < len(videos))
            elif bool(tagged_clip):
                use_clip = True
            else:
                use_clip = (
                    (video_idx < len(videos)) and (
                        random.random() < spec.clip_probability
                        or (random.random() < 0.05)
                    )
                )

            # ── Ken Burns zoom rate ───────────────────────────────────
            # Prefer storyboard zoom_rate_pct_sec (editorial playbook values),
            # fallback to intensity-keyed constant.
            if sb_entry and "zoom_rate_pct_sec" in sb_entry:
                kb_zoom_rate = sb_entry["zoom_rate_pct_sec"] / 100.0
            else:
                kb_zoom_rate = KB_INTENSITY_ZOOM.get(sb_intensity, KB_ZOOM_RATE_PER_SEC)

            seg_base = {
                "start_sec": round(t, 3),
                "duration_sec": round(seg_dur, 3),
                "text": overlay_text if is_chunk_start else None,
                "text_zone": overlay_zone if is_chunk_start else "upper",
                "narration_chunk_idx": chunk_idx,
                "content_type": content_type,   # carry through for compliance report
                "intensity": sb_intensity,      # for parallax visual config
                "sfx": seg_sfx,
                "_sfx_is_director": _sfx_is_director,
                "lower_third": seg_lower_third,
                "kb_zoom_rate": kb_zoom_rate,   # story-aware Ken Burns rate
                "shot_type": sb_shot_type,      # for per-scene color grading
                # v2.0 storyboard / Director fields (passed through to parallax renderer)
                "composition": sb_entry.get("composition") if sb_entry else None,
                "sync_points": sb_entry.get("sync_points", []) if sb_entry else [],
                "_scene_id": sb_entry.get("_scene_id") if sb_entry else None,
                "transition_in": sb_entry.get("transition_in") if sb_entry else None,
                "transition_out": sb_entry.get("transition_out") if sb_entry else None,
                "zoom_target": sb_entry.get("zoom_target") if sb_entry else None,
                "arc_position": sb_entry.get("arc_position") if sb_entry else None,
                # Director text overlay overrides
                "_text_overlay": sb_entry.get("_text_overlay") if sb_entry else None,
                "_text_overlay_size": sb_entry.get("_text_overlay_size") if sb_entry else None,
                "_text_overlay_style": sb_entry.get("_text_overlay_style") if sb_entry else None,
                "_text_overlay_hold_sec": sb_entry.get("_text_overlay_hold_sec") if sb_entry else None,
                "highlight_regions": sb_entry.get("highlight_regions") if sb_entry else None,
                "_document_content": sb_entry.get("_document_content", False) if sb_entry else False,
                "search_query": sb_entry.get("search_query", "") if sb_entry else "",
            }

            if use_clip and (tagged_clip or videos):
                clip = tagged_clip or videos[video_idx % len(videos)]
                if not tagged_clip:
                    video_idx += 1
                segments.append({**seg_base,
                    "source_type": "clip",
                    "source_path": clip.get("path", clip.get("local_path", "")),
                    "clip_start_sec": clip.get("clip_start_sec", 0.0),  # from clip_analyzer
                    "motion": "natural",
                    "storyboard_match": sb_entry_idx is not None,
                })
            elif tagged_stills or stills:
                if tagged_stills:
                    still = tagged_stills[tagged_still_idx % len(tagged_stills)]
                    tagged_still_idx += 1
                else:
                    still = stills[still_idx % len(stills)]
                    still_idx += 1
                still_path = Path(still.get("path", still.get("local_path", "")))
                # Ken Burns continuity: keep same direction for same image
                sp_str = str(still_path)
                if sp_str == _prev_still_path and _prev_motion:
                    motion = _prev_motion
                _prev_still_path = sp_str
                _prev_motion = motion
                focal = None
                if still_path.exists():
                    # Text-based focal from storyboard — always apply, no model needed
                    if sb_focal_element:
                        focal = _focal_from_description(sb_focal_element, still_path)
                    # Vision model fallback: only when --focal-points flag is set
                    if focal is None and detect_focal_points:
                        focal = detect_focal_point(still_path, narration_text=chunk_text)
                # For composite segments, pick a second still as background
                _bg_img = None
                if seg_base.get("composition", {}).get("type") == "composite":
                    # Try next tagged still, else next general still
                    if tagged_stills and len(tagged_stills) > 1:
                        bg_still = tagged_stills[(tagged_still_idx) % len(tagged_stills)]
                        _bg_img = str(Path(bg_still.get("path", bg_still.get("local_path", ""))))
                    elif len(stills) > 1:
                        bg_still = stills[(still_idx) % len(stills)]
                        _bg_img = str(Path(bg_still.get("path", bg_still.get("local_path", ""))))
                        still_idx += 1

                segments.append({**seg_base,
                    "source_type": "still",
                    "source_path": str(still_path),
                    "motion": motion,
                    "focal_point": focal,
                    "storyboard_match": bool(tagged_stills),
                    "_bg_image_path": _bg_img,
                })
            elif sb_entry_idx is not None and storyboard:
                # No real footage found but storyboard entry exists — generate visual
                sb = storyboard[sb_entry_idx]
                segments.append({**seg_base,
                    "source_type": "animation",
                    "source_path": None,
                    "motion": motion,
                    "focal_point": None,
                    "storyboard_match": True,
                    "anim_show": sb.get("show", ""),
                    "anim_shot_type": sb.get("shot_type", "documentary_photo"),
                })
            else:
                # No footage and no storyboard entry — generate a narration text card.
                # Fern NEVER uses black screens for content. Always show something.
                segments.append({**seg_base,
                    "source_type": "animation",
                    "source_path": None,
                    "motion": motion,
                    "focal_point": None,
                    "storyboard_match": False,
                    "anim_show": chunk_text[:100] if chunk_text else "documentary segment",
                    "anim_shot_type": "documentary_photo",
                })

            t += seg_dur
            cursor = t
            _rhythm_accum += seg_dur  # track for burst breathing

    # ── Post-build normalization ─────────────────────────────────────────
    # Small drift can remain because chapter cards don't exactly fill their
    # pause gaps. Scale content segment durations so total video ≈ narration.
    if total_narration_dur > 0:
        total_visual = 0.0
        for s in segments:
            if s["duration_sec"] < 0:  # chapter card sentinel
                ri = min(s.get("chapter_num", 1) - 1, len(_ROMAN) - 1)
                ft = f"Chapter {_ROMAN[ri]}: {s.get('chapter_title', '')}"
                total_visual += (CHAPTER_CARD_FADE_SEC
                                 + len(ft) / CHAPTER_CARD_CHARS_PER_SEC
                                 + CHAPTER_CARD_MIN_HOLD_SEC
                                 + CHAPTER_CARD_FADE_SEC)
            else:
                total_visual += s["duration_sec"]
        drift = total_visual - total_narration_dur
        if abs(drift) > 0.5:
            content_dur = sum(s["duration_sec"] for s in segments
                              if s["source_type"] not in ("chapter_card", "black")
                              and s["duration_sec"] > 0)
            if content_dur > 0:
                scale = (content_dur - drift) / content_dur
                for s in segments:
                    if (s["source_type"] not in ("chapter_card", "black")
                            and s["duration_sec"] > 0):
                        s["duration_sec"] = round(s["duration_sec"] * scale, 3)
                print(f"  A/V sync normalization: {drift:+.1f}s drift → "
                      f"scaled {len([s for s in segments if s['source_type'] not in ('chapter_card','black')])} "
                      f"segments by {scale:.4f}")

    # ── Post-build image diversity pass ─────────────────────────────
    segments = _enforce_image_diversity(segments, stills)

    # ── Post-build compliance report (validates, doesn't drive) ─────
    _print_compliance_report(segments)

    return segments


def _enforce_image_diversity(segments: list, stills: list,
                             max_per_window: int = 1, window_sec: float = 20.0) -> list:
    """Reduce image repetition by swapping duplicate stills within a sliding window."""
    if not segments or not stills:
        return segments
    still_paths = list({
        str(s.get("local_path") or s.get("path") or "")
        for s in stills
        if (s.get("local_path") or s.get("path") or "").lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp"))
    })
    swaps = 0
    for i, seg in enumerate(segments):
        if seg.get("source_type") != "still" or not seg.get("source_path"):
            continue
        if seg.get("highlight_regions"):
            continue
        src = seg["source_path"]
        t_start = sum(s.get("duration_sec", 0) for s in segments[:i])
        count = 0
        t_acc = t_start
        for j in range(i - 1, -1, -1):
            t_acc -= segments[j].get("duration_sec", 0)
            if t_start - t_acc > window_sec:
                break
            if segments[j].get("source_path") == src:
                count += 1
        if count >= max_per_window:
            alts = [p for p in still_paths if p != src and Path(p).exists()]
            if alts:
                seg["source_path"] = random.choice(alts)
                seg["_diversity_swapped"] = True
                seg.pop("highlight_regions", None)
                seg.pop("shots", None)
                seg.pop("_document_content", None)
                swaps += 1
    if swaps:
        print(f"  Image diversity: swapped {swaps} segments to reduce repetition")
    return segments


def _print_compliance_report(segments: list[dict]) -> None:
    """Print editorial compliance stats — validates output vs playbook targets."""
    content_segs = [s for s in segments
                    if s["source_type"] not in ("chapter_card", "black")]
    if not content_segs:
        return

    total_dur = sum(s["duration_sec"] for s in content_segs if s["duration_sec"] > 0)
    total_dur_min = total_dur / 60.0 if total_dur > 0 else 1.0

    # Cut rate
    cut_rate = len(content_segs) / total_dur_min if total_dur_min > 0 else 0

    # Motion distribution
    motion_counts: dict[str, int] = {}
    for s in content_segs:
        m = s.get("motion", "static")
        motion_counts[m] = motion_counts.get(m, 0) + 1
    n = len(content_segs) or 1

    # Average segment duration
    avg_dur = total_dur / len(content_segs) if content_segs else 0

    # SFX rate
    sfx_segs = sum(1 for s in content_segs if s.get("sfx"))
    sfx_pct = sfx_segs / n * 100

    print(f"\n  ── Editorial compliance report ──")
    print(f"  Cut rate:    {cut_rate:.1f}/min  (playbook target: ~13.2)")
    print(f"  Avg segment: {avg_dur:.1f}s")
    print(f"  Motion:  ", end="")
    for m in ("zoom_in", "zoom_out", "static", "pan_up", "pan_down", "pan_right", "pan_left", "natural"):
        c = motion_counts.get(m, 0)
        if c > 0:
            print(f"{m}={c/n*100:.0f}% ", end="")
    print(f"\n  SFX:     {sfx_pct:.1f}% of cuts  (playbook: ~10.9%)")
    print(f"  Storyboard match: {sum(1 for s in content_segs if s.get('storyboard_match'))}/{n}")


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


def _pick_sfx_file(sfx_type: str) -> Path | None:
    """Return a random existing SFX file for the given type, or None if unavailable."""
    candidates = {
        "impact": ["impact_01.mp3", "impact_02.mp3", "impact_cc0_01.mp3", "impact_cc0_02.mp3"],
        "body_impact": ["body_impact_01.mp3", "body_fall_cc0_01.mp3", "impact_cc0_01.mp3"],
        "glass_shatter": ["glass_shatter_01.mp3", "glass_cc0_01.mp3", "glass_cc0_03.mp3", "glass_cc0_04.mp3"],
        "whoosh": ["whoosh_01.mp3", "whoosh_02.mp3", "whoosh_03.mp3", "whoosh_04.mp3", "whoosh_05.mp3"],
        "rumble": ["rumble_01.mp3", "rumble_02.mp3", "rumble_03.mp3"],
        "shimmer": ["shimmer_01.mp3", "shimmer_02.mp3", "shimmer_03.mp3"],
        "tension": ["tension_01.mp3"],
        "highlighter": ["highlighter_01.mp3"],
    }
    files = [SFX_DIR / f for f in candidates.get(sfx_type, []) if (SFX_DIR / f).exists()]
    return random.choice(files) if files else None


def _extract_overlay_text(chunk_text: str) -> tuple[str | None, str]:
    """
    Extract a short text overlay and its display zone from a narration chunk.
    Returns (text, zone) where zone is "upper" | "center" | "lower".

    Only returns overlays for high-value content:
      - Full dates/years  → upper  (e.g. "November 28, 1953")
      - Person names on first mention → center  (e.g. "Frank Olson")
      - Named locations   → lower  (e.g. "Fort Detrick, Maryland")

    Returns (None, "upper") for most chunks — Fern doesn't overlay every segment.
    """
    # Full date expressions → upper zone  (e.g. "November 28, 1953" or "April 1953")
    date_match = re.search(
        r'((?:January|February|March|April|May|June|July|August|September|'
        r'October|November|December)\s+\d{1,2},?\s+\d{4})', chunk_text)
    if date_match:
        return date_match.group(1), "upper"

    # Standalone year with context  (e.g. "1953." at sentence start)
    year_match = re.search(r'(?:^|\.\s+)(\d{4})\.\s', chunk_text)
    if year_match:
        return year_match.group(1), "upper"

    # Named locations with state/country  (e.g. "Fort Detrick, Maryland")
    loc_match = re.search(
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2},\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
        chunk_text)
    if loc_match:
        loc = loc_match.group(1)
        # Filter out sentence-start false positives
        filler = {"The", "A", "An", "In", "On", "At", "Of", "To", "By", "But", "And", "His", "Her"}
        if loc.split()[0] not in filler:
            return loc[:45], "lower"

    # Person names: only 2–3 word Title Case names that look like real names
    # (skip sentence-initial words and common articles)
    filler = {"The", "A", "An", "In", "On", "At", "Of", "To", "By", "But", "And",
              "His", "Her", "He", "She", "It", "This", "That", "They", "Some",
              "What", "When", "Where", "Over", "Under", "Room", "About", "After"}
    person_matches = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', chunk_text)
    for name in person_matches:
        parts = name.split()
        if parts[0] not in filler and len(parts) >= 2:
            return name[:40], "center"

    # No overlay for most chunks — this is intentional
    return None, "upper"


def _detect_named_persons(chunks: list[dict]) -> dict[int, tuple[str, str]]:
    """
    Scan narration chunks and return the FIRST occurrence of each named person.
    Returns {chunk_idx: (name, role)} for segments that should show a lower-third.

    Detects patterns like:
      "Theodore Kaczynski, known as the Unabomber"
      "J. Edgar Hoover — the FBI director"
      "Richard Nixon" (name only, no role)
    """
    seen_names: set[str] = set()
    result: dict[int, tuple[str, str]] = {}

    # Appositive: "Name, [the/a/known as] Role" or "Name — [the] Role"
    appositive_re = re.compile(
        r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?(?:[A-Z][a-z]+\s*){1,3})'
        r'(?:,\s*(?:known as\s*)?(?:the\s+|a\s+)?([A-Za-z][^,.\n]{3,40}?)'
        r'|\s+—\s*(?:the\s+)?([A-Za-z][^,.\n]{3,40}?))'
        r'(?=[,. ])'
    )
    name_only_re = re.compile(r'\b([A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+)\b')
    filler = {"The", "A", "An", "In", "On", "At", "Of", "To", "By",
              "It", "This", "That", "These", "United", "New"}
    skip_words = {"States", "War", "Era", "Act", "Bill", "Case", "Street",
                  "Avenue", "Commission", "Committee", "Congress", "Senate"}

    for idx, chunk in enumerate(chunks):
        text = chunk.get("text", "")

        # Try appositive pattern first (gives name + role)
        for m in appositive_re.finditer(text):
            name = m.group(1).strip()
            role = (m.group(2) or m.group(3) or "").strip().rstrip(".,;")
            parts = name.split()
            if len(parts) < 2 or parts[0] in filler:
                continue
            if name not in seen_names:
                seen_names.add(name)
                result[idx] = (name, role[:42] if role else "")
                break

        if idx in result:
            continue

        # Fall back: plain "First Last" pattern
        for m in name_only_re.finditer(text):
            name = m.group(1).strip()
            parts = name.split()
            if parts[0] in filler:
                continue
            if any(w in name for w in skip_words):
                continue
            if name not in seen_names:
                seen_names.add(name)
                result[idx] = (name, "")
                break

    return result


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
    use_parallax: bool = False,
) -> Path:
    """
    Render all segments, apply grade, add text, concatenate, mix audio.
    When use_parallax=True, stills get depth parallax + motion graphics + story-driven color.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Initialize parallax engine if requested
    parallax_engine = None
    if use_parallax:
        from pipeline.parallax_renderer import ParallaxEngine, SegmentVisualConfig
        cache_dir = tmp_dir / ".depth_cache"
        parallax_engine = ParallaxEngine(cache_dir=str(cache_dir))
        print("  Parallax rendering enabled (depth model loads on first still)")

    if dry_run:
        print("\n=== DRY RUN TIMELINE ===")
        for i, seg in enumerate(segments):
            dur_str = f"{seg['duration_sec']:.1f}s" if seg['duration_sec'] >= 0 else "(auto)"
            label = seg['source_type']
            if label == "chapter_card":
                label = f"CHAPTER {seg.get('chapter_num','?')}: {seg.get('chapter_title','')}"
            ct = seg.get("content_type", "")[:14]
            print(f"  [{i:03d}] {seg['start_sec']:6.1f}s  {dur_str:7s}  "
                  f"{seg['motion']:12s}  {ct:14s}  {label[:40]}"
                  + (f"  SFX:{seg['sfx']}" if seg.get("sfx") else "")
                  + (f"  LT:{seg['lower_third']['name'][:20]}" if seg.get("lower_third") else ""))
        total_dur = sum(s["duration_sec"] for s in segments if s["duration_sec"] >= 0)
        print(f"\nTotal (excl. chapter cards): {total_dur:.1f}s  ({total_dur/60:.1f}min)")
        print(f"Segments: {len(segments)}")
        print(f"Output: {out_path}")
        return out_path

    segment_paths = []
    sfx_events: list[dict]  = []   # {"time_sec": float, "sfx_file": str}
    lt_events:  list[dict]  = []   # {"time_sec", "end_sec", "name", "role"}
    clip_audio_events: list[dict] = []  # footage audio passthrough
    render_cursor = 0.0            # cumulative final-video timestamp

    print(f"\nRendering {len(segments)} segments...")

    for i, seg in enumerate(segments):
        seg_raw    = tmp_dir / f"seg_{i:04d}_raw.mp4"
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
            render_cursor += card_dur
            continue

        dur = seg["duration_sec"]

        # Collect SFX event at the START of this segment (the visual cut point)
        if seg.get("sfx"):
            sfx_file = _pick_sfx_file(seg["sfx"])
            if sfx_file:
                sfx_events.append({"time_sec": render_cursor, "sfx_file": str(sfx_file)})

        # Collect typewriter click SFX for sync point text reveals
        typewriter_sfx = Path("assets/sfx/typewriter_key.wav")
        if typewriter_sfx.exists():
            for sp in seg.get("sync_points", []):
                if sp.get("typewriter_click") and sp.get("word_index") is not None:
                    total_words = sp.get("_total_words", 20)
                    trigger_t = render_cursor + (sp["word_index"] / max(1, total_words)) * dur
                    sfx_events.append({"time_sec": trigger_t, "sfx_file": str(typewriter_sfx)})

        # Collect highlighter SFX for segments with highlight_regions
        if seg.get("highlight_regions"):
            hl_sfx = _pick_sfx_file("highlighter")
            if hl_sfx:
                for hr in seg["highlight_regions"]:
                    hl_time = render_cursor + hr.get("reveal_at", 0.5) * dur
                    sfx_events.append({"time_sec": hl_time, "sfx_file": str(hl_sfx)})

        # Collect lower-third event (will be applied post-concat for accurate timestamps)
        lt = seg.get("lower_third")
        if lt and lt.get("name"):
            lt_events.append({
                "time_sec": render_cursor,
                "end_sec":  render_cursor + min(dur, 4.0),
                "name": lt["name"],
                "role": lt.get("role", ""),
            })

        print(f"  [{i+1}/{len(segments)}] {seg['motion']:12s}  {dur:.1f}s  "
              f"{Path(seg['source_path'] or '').name[:35] if seg['source_path'] else 'BLACK'}",
              end="  ", flush=True)

        # Step 1: Create raw segment
        # Build parallax visual config from storyboard metadata (if parallax enabled)
        _visual_config = None
        _bg_image_path = None  # for composite rendering
        if parallax_engine and seg["source_type"] == "still":
            from pipeline.parallax_renderer import SegmentVisualConfig
            _visual_config = SegmentVisualConfig.from_storyboard(
                narrative_function=seg.get("content_type", "context_background"),
                intensity=seg.get("intensity", "neutral"),
                shot_type=seg.get("shot_type"),
                motion_direction=seg.get("motion", "zoom_in"),
                zoom_rate_pct_sec=seg.get("kb_zoom_rate", KB_ZOOM_RATE_PER_SEC) * 100,
            )
            # Attach text overlay to visual config (rendered in-frame, not separate ffmpeg pass)
            # Director-provided text overlay takes priority
            if seg.get("_text_overlay"):
                _visual_config.text_overlay = seg["_text_overlay"]
                _visual_config.text_position = seg.get("_text_overlay_position", "lower_third")
                _visual_config.text_size = seg.get("_text_overlay_size", 56)
                _visual_config.text_style = seg.get("_text_overlay_style", "typewriter")
            elif seg.get("text"):
                _visual_config.text_overlay = seg["text"]
                _visual_config.text_position = (
                    "lower_third" if seg.get("text_zone") == "lower" else "center"
                )
            # v2.0: Apply composition, sync_points, transitions from storyboard
            comp = seg.get("composition")
            if comp:
                _visual_config.composition_type = comp.get("type", "single")
                _visual_config.layers = comp.get("layers", [])
                _visual_config.atmosphere = comp.get("atmosphere", "none")
                # Override color grade from composition if specified
                cg = comp.get("color_grade")
                if cg:
                    _visual_config.color_style = cg
            sync_pts = seg.get("sync_points", [])
            if sync_pts:
                # Inject total word count for timing estimation
                total_words = len(seg.get("text", "").split()) if seg.get("text") else 20
                for sp in sync_pts:
                    sp["_total_words"] = total_words
                _visual_config.sync_points = sync_pts
            # Director-provided transitions
            if seg.get("transition_in"):
                _visual_config.transition_in = seg["transition_in"]
            if seg.get("transition_out"):
                _visual_config.transition_out = seg["transition_out"]

            # Document mode: letterbox portrait documents
            _src = seg.get("source_path", "")
            if _src and seg.get("source_type") == "still":
                _is_doc_type = seg.get("shot_type", "").lower() in ("document_photo", "document", "declassified", "memo")
                _is_doc_query = any(w in seg.get("search_query", "").lower() for w in ("document", "memo", "declassified", "report"))
                if _is_doc_type or _is_doc_query:
                    try:
                        from PIL import Image as _PILImg
                        with _PILImg.open(_src) as _dim:
                            if _dim.height > _dim.width * 1.2:
                                _visual_config.document_mode = True
                    except Exception:
                        pass

            # Wire highlight_regions to renderer
            if seg.get("highlight_regions"):
                _visual_config.highlight_regions = seg["highlight_regions"]

            # Camera shake only for Director/playbook SFX (not random rolls)
            if seg.get("sfx") and seg.get("_sfx_is_director"):
                _visual_config.camera_shake = True

        if seg["source_type"] == "still":
            src = Path(seg["source_path"])
            if src.exists():
                # For composite segments, try to find a background image
                _bg_path = seg.get("_bg_image_path")
                make_ken_burns(src, dur, seg["motion"], seg_raw,
                               focal_point=seg.get("focal_point"),
                               zoom_rate=seg.get("kb_zoom_rate", KB_ZOOM_RATE_PER_SEC),
                               parallax_engine=parallax_engine,
                               visual_config=_visual_config,
                               start_time=render_cursor,
                               bg_image_path=_bg_path)
            else:
                _make_black(dur, seg_raw)

        elif seg["source_type"] == "clip":
            src = Path(seg["source_path"])
            if src.exists():
                prepare_clip(src, dur, seg_raw,
                             start_sec=seg.get("clip_start_sec", 0.0))
                # Extract clip audio for passthrough (low volume under narration)
                clip_audio_path = seg_raw.parent / f"{seg_raw.stem}_clipaudio.wav"
                try:
                    _run([
                        "ffmpeg", "-y",
                        "-ss", str(seg.get("clip_start_sec", 0.0)),
                        "-i", str(src), "-t", str(dur),
                        "-vn", "-ac", "2", "-ar", "44100",
                        str(clip_audio_path),
                    ], "clip_audio_extract")
                    if clip_audio_path.exists() and clip_audio_path.stat().st_size > 1000:
                        clip_audio_events.append({
                            "time_sec": render_cursor,
                            "audio_file": str(clip_audio_path),
                            "duration_sec": dur,
                        })
                except Exception:
                    pass  # silently skip if clip has no audio track
            else:
                _make_black(dur, seg_raw)

        elif seg["source_type"] == "animation":
            # No real footage — generate a still using animation_generator, then Ken Burns it
            try:
                from pipeline.animation_generator import generate_animation_frame
                anim_png = seg_raw.parent / f"{seg_raw.stem}_anim.png"
                narration_text = ""
                # Recover narration text from chunk if available
                if "_narration_chunks" in globals():
                    chunk_idx = seg.get("narration_chunk_idx", 0)
                    # narration_chunks is local to assemble() — we stored narration in seg
                result = generate_animation_frame(
                    show=seg.get("anim_show", ""),
                    shot_type=seg.get("anim_shot_type", "documentary_photo"),
                    narration_text=seg.get("text") or seg.get("anim_show", ""),
                    out_path=anim_png,
                )
                if result and anim_png.exists():
                    make_ken_burns(anim_png, dur, seg.get("motion", "zoom_in"), seg_raw,
                                   focal_point=seg.get("focal_point"),
                                   zoom_rate=seg.get("kb_zoom_rate", KB_ZOOM_RATE_PER_SEC))
                else:
                    _make_black(dur, seg_raw)
            except Exception as e:
                print(f"  [animation] render error: {e}")
                _make_black(dur, seg_raw)

        else:  # black
            _make_black(dur, seg_raw)

        # Step 2 & 3: Color grade + text overlay
        # When parallax rendered a still, both are already applied in-frame — skip ffmpeg passes
        if parallax_engine and seg["source_type"] == "still" and _visual_config:
            seg_final = seg_raw  # parallax already did color + overlays + text
        else:
            # FFmpeg color grade — per-scene treatment based on shot_type
            scene_type = _scene_type_for(seg.get("shot_type"))
            if seg["source_type"] in ("still", "clip"):
                apply_color_grade(seg_raw, seg_graded, scene_type=scene_type,
                                  is_clip=(seg["source_type"] == "clip"))
            else:
                seg_graded = seg_raw

            # FFmpeg text overlay
            text_entries = []
            if seg.get("text"):
                text_style = "slide"
                txt = seg["text"]
                if re.match(r"^\d{4}$|^\w+ \d{1,2},?\s*\d{4}$", txt.strip()):
                    text_style = "typewriter"
                elif txt.isupper() and len(txt) <= 30:
                    text_style = "typewriter"
                text_entries.append({
                    "text": txt,
                    "start_sec": 0.0,
                    "end_sec": min(dur - 0.1, 9.0),
                    "zone": seg.get("text_zone", "upper"),
                    "style": text_style,
                })
            add_text_overlay(seg_graded, text_entries, seg_final)

        segment_paths.append(seg_final)
        render_cursor += dur
        print("✓")

    total_video_dur = render_cursor

    # Step 4: Concatenate all segments
    print(f"\nConcatenating {len(segment_paths)} segments "
          f"(planned: {total_video_dur:.1f}s / {total_video_dur/60:.1f}min)...")
    raw_video = tmp_dir / "video_no_audio.mp4"
    _concat_videos(segment_paths, raw_video)

    # Verify concat output matches expected duration
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(raw_video)],
            capture_output=True, text=True)
        concat_dur = float(json.loads(probe.stdout)["format"]["duration"])
        drift = abs(concat_dur - total_video_dur)
        print(f"  Concat video: {concat_dur:.1f}s  (expected {total_video_dur:.1f}s, "
              f"drift {drift:.1f}s{'  ⚠️' if drift > 2.0 else '  ✓'})")
    except Exception:
        pass

    # Step 4b: Apply lower thirds in one pass (avoids N re-encodes)
    if lt_events:
        print(f"Applying {len(lt_events)} lower-third overlays...")
        video_with_lt = tmp_dir / "video_with_lt.mp4"
        _apply_lower_thirds_batch(raw_video, lt_events, video_with_lt)
        raw_video = video_with_lt

    # Step 4c: Build SFX composite audio track
    sfx_composite: "Path | None" = None
    if sfx_events:
        print(f"Building SFX composite ({len(sfx_events)} events)...")
        sfx_composite_path = tmp_dir / "sfx_composite.wav"
        sfx_composite = _build_sfx_composite(sfx_events, total_video_dur, sfx_composite_path)

    # Step 4d: Build clip audio passthrough composite
    clip_audio_composite: "Path | None" = None
    if clip_audio_events:
        print(f"Building clip audio composite ({len(clip_audio_events)} clips)...")
        ca_path = tmp_dir / "clip_audio_composite.wav"
        clip_audio_composite = _build_clip_audio_composite(
            clip_audio_events, total_video_dur, ca_path)

    # Merge SFX + clip audio into one composite (simpler mix_audio signature)
    if sfx_composite and clip_audio_composite:
        merged_fx = tmp_dir / "merged_fx_composite.wav"
        _run([
            "ffmpeg", "-y",
            "-i", str(sfx_composite), "-i", str(clip_audio_composite),
            "-filter_complex", "[0][1]amix=inputs=2:duration=first:normalize=0[out]",
            "-map", "[out]", "-ar", "44100", "-ac", "2",
            str(merged_fx),
        ], "merge_fx")
        sfx_composite = merged_fx
    elif clip_audio_composite:
        sfx_composite = clip_audio_composite

    # Step 5: Mix audio
    print("Mixing audio...")
    if music_path and music_path.exists():
        mix_audio(raw_video, narration_path, music_path, out_path, sfx_composite)
    else:
        _mix_narration_only(raw_video, narration_path, out_path, sfx_composite)

    # ── Formula compliance report ────────────────────────────────────────────
    visual_segs = [s for s in segments if s["source_type"] not in ("chapter_card", "black", "animation")]
    if visual_segs and total_video_dur > 0:
        dur_min      = total_video_dur / 60
        cuts_per_min = len(visual_segs) / dur_min
        motions      = [s["motion"] for s in visual_segs]
        n            = len(motions)
        zi_pct   = motions.count("zoom_in")   / n * 100
        zo_pct   = motions.count("zoom_out")  / n * 100
        st_pct   = motions.count("static")    / n * 100
        pan_pct  = (motions.count("pan_right") + motions.count("pan_left") + motions.count("pan_up") + motions.count("pan_down")) / n * 100
        sfx_pct  = len(sfx_events) / n * 100 if n else 0
        lt_count = len(lt_events)

        def _bar(val: float, target: float, tol: float = 20) -> str:
            ok = abs(val - target) / max(target, 1) <= tol / 100
            return "✓" if ok else "✗"

        print(f"\n{'─' * 58}")
        print(f"  FORMULA COMPLIANCE REPORT")
        print(f"{'─' * 58}")
        print(f"  Duration:    {total_video_dur:.0f}s  ({dur_min:.1f} min)")
        print(f"  Segments:    {len(visual_segs)}")
        print(f"  Cuts/min:    {cuts_per_min:.1f}  [target 11.3]  {_bar(cuts_per_min, 11.3)}")
        print(f"  Zoom-in:     {zi_pct:.0f}%  [target 40%]  {_bar(zi_pct, 40)}")
        print(f"  Zoom-out:    {zo_pct:.0f}%  [target 25%]  {_bar(zo_pct, 25)}")
        print(f"  Static:      {st_pct:.0f}%  [target 26%]  {_bar(st_pct, 26)}")
        print(f"  Pan:         {pan_pct:.0f}%  [target 9%]   {_bar(pan_pct, 9)}")
        print(f"  SFX rate:    {sfx_pct:.1f}%  [target 10.9%]  {_bar(sfx_pct, 10.9)}")
        print(f"  Lower thirds:{lt_count}  (named persons shown)")
        still_pct = sum(1 for s in visual_segs if s["source_type"] == "still") / n * 100
        clip_pct  = 100 - still_pct
        print(f"  Footage mix: {still_pct:.0f}% stills / {clip_pct:.0f}% clips  [target 88%/12%]")
        print(f"{'─' * 58}")

    # Save timeline.json alongside output for check_fern_video.py and debugging
    timeline_json = out_path.parent / "timeline.json"
    try:
        timeline_json.write_text(json.dumps(segments, indent=2, default=str))
        print(f"Timeline → {timeline_json}")
    except Exception:
        pass  # non-critical

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


def _apply_lower_thirds_batch(
    input_path: Path,
    lt_events: list[dict],  # [{"time_sec", "end_sec", "name", "role"}]
    out_path: Path,
) -> Path:
    """
    Apply multiple lower-third overlays in a single ffmpeg pass over the full video.
    More efficient than calling add_lower_third() N times (avoids N re-encodes).
    """
    font_opts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFPro.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_path = next((f for f in font_opts if Path(f).exists()), "")
    font_arg  = f":fontfile={font_path}" if font_path else ""

    bar_y  = int(1080 * LOWER_THIRD_BAR_Y_PCT)
    name_y = bar_y + 10
    role_y = name_y + LOWER_THIRD_NAME_SIZE + 8

    filters = []
    for ev in lt_events:
        t_in  = ev["time_sec"]
        t_out = ev["end_sec"]
        enable = f"between(t,{t_in:.3f},{t_out:.3f})"

        slide_end  = t_in + TEXT_SLIDE_DURATION
        fade_start = t_out - 0.2
        alpha = (
            f"if(lt(t,{slide_end:.3f}),"
            f"max(0,(t-{t_in:.3f})/{TEXT_SLIDE_DURATION:.3f}),"
            f"if(gt(t,{fade_start:.3f}),"
            f"max(0,({t_out:.3f}-t)/0.2),1))"
        ).replace(" ", "")

        escaped_name = _escape_text(ev["name"].upper())
        filters.append(
            f"drawbox=x=0:y={bar_y}:w=iw:h={LOWER_THIRD_BAR_H}"
            f":color=black@0.78:t=fill:enable='{enable}'"
        )
        filters.append(
            f"drawtext=text='{escaped_name}'"
            f":fontcolor=white:fontsize={LOWER_THIRD_NAME_SIZE}{font_arg}"
            f":x=60:y={name_y}"
            f":shadowcolor=black@0.5:shadowx=2:shadowy=2"
            f":alpha='{alpha}':enable='{enable}'"
        )
        role = ev.get("role", "")
        if role:
            escaped_role = _escape_text(role)
            filters.append(
                f"drawtext=text='{escaped_role}'"
                f":fontcolor={LOWER_THIRD_ROLE_COLOR}:fontsize={LOWER_THIRD_ROLE_SIZE}{font_arg}"
                f":x=60:y={role_y}"
                f":alpha='{alpha}':enable='{enable}'"
            )

    vf = ",".join(filters)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", str(OUTPUT_CRF),
        "-pix_fmt", "yuv420p", "-an",
        str(out_path),
    ]
    _run(cmd, "lower_thirds_batch")
    return out_path


def _build_sfx_composite(
    sfx_events: list[dict],  # [{"time_sec": float, "sfx_file": str}]
    total_dur: float,
    out_path: Path,
) -> "Path | None":
    """
    Build a composite audio track: each SFX placed at its timestamp.
    Uses adelay to position each SFX at the correct cut point.
    Returns out_path if successful, None if no valid SFX files found.
    """
    valid = [ev for ev in sfx_events if Path(ev["sfx_file"]).exists()]
    if not valid:
        return None

    # Start with a silent base, then layer in each delayed SFX
    inputs = ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={total_dur}"]
    filter_parts = []
    for i, ev in enumerate(valid):
        delay_ms = int(ev["time_sec"] * 1000)
        inputs += ["-i", ev["sfx_file"]]
        filter_parts.append(
            f"[{i + 1}]volume={SFX_VOLUME},adelay={delay_ms}|{delay_ms}[sfx{i}]"
        )

    n_inputs = 1 + len(valid)
    labels = "[0]" + "".join(f"[sfx{i}]" for i in range(len(valid)))
    filter_parts.append(
        f"{labels}amix=inputs={n_inputs}:duration=first:dropout_transition=0[sfxout]"
    )

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", ";".join(filter_parts),
            "-map", "[sfxout]",
            "-t", str(total_dur),
            "-ar", "44100", "-ac", "2",
            str(out_path),
        ]
    )
    _run(cmd, "sfx_composite")
    return out_path


CLIP_AUDIO_VOLUME = 0.15   # footage audio ducked well under narration


def _build_clip_audio_composite(
    events: list[dict],
    total_dur: float,
    out_path: Path,
) -> "Path | None":
    """Build composite audio from archival clip audio for passthrough mixing."""
    valid = [ev for ev in events if Path(ev["audio_file"]).exists()]
    if not valid:
        return None
    inputs = ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={total_dur}"]
    filter_parts = []
    for i, ev in enumerate(valid):
        delay_ms = int(ev["time_sec"] * 1000)
        inputs += ["-i", ev["audio_file"]]
        filter_parts.append(
            f"[{i + 1}]volume={CLIP_AUDIO_VOLUME},"
            f"afade=t=in:d=0.3,afade=t=out:st={ev['duration_sec'] - 0.3}:d=0.3,"
            f"adelay={delay_ms}|{delay_ms}[ca{i}]"
        )
    n_inputs = 1 + len(valid)
    labels = "[0]" + "".join(f"[ca{i}]" for i in range(len(valid)))
    filter_parts.append(
        f"{labels}amix=inputs={n_inputs}:duration=first:dropout_transition=0[caout]"
    )
    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", ";".join(filter_parts),
            "-map", "[caout]",
            "-t", str(total_dur),
            "-ar", "44100", "-ac", "2",
            str(out_path),
        ]
    )
    _run(cmd, "clip_audio_composite")
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
    sfx_path: "Path | None" = None,
) -> Path:
    """
    Mix narration + music (+ optional SFX composite) under video.
    Music ducks under narration (MUSIC_VOLUME).
    Music plays louder during first 3s intro (MUSIC_INTRO_VOLUME).
    SFX composite is mixed at full scale (already volume-adjusted by _build_sfx_composite).
    """
    if sfx_path and sfx_path.exists():
        filter_complex = (
            f"[1:a]volume={NARRATION_VOLUME}[narr];"
            f"[2:a]volume='{MUSIC_INTRO_VOLUME}*between(t,0,3)"
            f"+{MUSIC_VOLUME}*(1-between(t,0,3))'[music];"
            f"[3:a]volume=1.0[sfx];"
            f"[narr][music][sfx]amix=inputs=3:duration=first:dropout_transition=3:normalize=0[aout]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(narration_path),
            "-stream_loop", "-1", "-i", str(music_path),
            "-i", str(sfx_path),
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ]
    else:
        filter_complex = (
            f"[1:a]volume={NARRATION_VOLUME}[narr];"
            f"[2:a]volume='{MUSIC_INTRO_VOLUME}*between(t,0,3)"
            f"+{MUSIC_VOLUME}*(1-between(t,0,3))'[music];"
            f"[narr][music]amix=inputs=2:duration=first:dropout_transition=3:normalize=0[aout]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(narration_path),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ]
    _run(cmd, "mix_audio")
    return out_path


def _mix_narration_only(
    video_path: Path,
    narration_path: Path,
    out_path: Path,
    sfx_path: "Path | None" = None,
) -> Path:
    """Attach narration (+ optional SFX) to video without background music.

    Uses -map flags to select exactly one video and one audio stream.
    Does NOT use -shortest — if there's a small duration mismatch the video
    simply freezes on the last frame while audio finishes (better than truncating).
    """
    if sfx_path and sfx_path.exists():
        filter_complex = (
            f"[1:a]volume={NARRATION_VOLUME}[narr];"
            f"[2:a]volume=1.0[sfx];"
            f"[narr][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(narration_path),
            "-i", str(sfx_path),
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(narration_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ]
    _run(cmd, "attach_audio")
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
    p.add_argument("--focal-points", action="store_true",
                   help="Detect Ken Burns focal points via local vision model (qwen3.5:27b). "
                        "Results cached per image. Falls back to center if model unavailable.")
    p.add_argument("--storyboard", default=None,
                   help="Path to storyboard.json (from storyboard_generator.py). "
                        "Enables story-specific footage selection: clips tagged with "
                        "matching storyboard_segment_ids are preferred over round-robin.")
    p.add_argument("--parallax", action="store_true",
                   help="Use depth parallax + motion graphics rendering for stills. "
                        "Requires Depth Anything V2 (~95MB). Renders ~2-3 hours for 25min video. "
                        "Every segment's visual treatment is story-driven (narrative_function, "
                        "intensity, shot_type).")
    p.add_argument("--stills-only", action="store_true",
                   help="Use only still images, skip all video clips. "
                        "Eliminates watermark/wrong-content issues from stock clips.")
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

    # Load beat timestamps from music track for beat-sync cut snapping
    beat_times: list[float] = []
    if music_path and music_path.exists():
        print("\nDetecting beats from music track...")
        beat_times = load_beat_times(music_path)
        if beat_times:
            print(f"  {len(beat_times)} beats detected  (~{60/(beat_times[1]-beat_times[0]):.0f} BPM estimated)")
        else:
            print("  Beat detection unavailable — cuts will not be beat-synced")

    # Load storyboard if provided
    storyboard = None
    if args.storyboard:
        sb_path = Path(args.storyboard)
        if sb_path.exists():
            raw_sb = json.load(open(sb_path))
            # v2.0 schema: flatten scenes[].segments[] into a flat list
            if isinstance(raw_sb, dict) and raw_sb.get("schema_version") == "2.0":
                storyboard = []
                for scene in raw_sb.get("scenes", []):
                    for seg in scene.get("segments", []):
                        seg["_scene_id"] = scene.get("scene_id")
                        storyboard.append(seg)
                print(f"  Storyboard v2.0: {sb_path.name} ({len(storyboard)} segments in "
                      f"{raw_sb.get('scene_count', '?')} scenes, "
                      f"{raw_sb.get('composite_count', 0)} composites, "
                      f"{raw_sb.get('sync_point_count', 0)} sync points)")
            else:
                # v1 flat list
                storyboard = raw_sb if isinstance(raw_sb, list) else []
                tagged = sum(1 for e in storyboard if e.get("search_query"))
                print(f"  Storyboard: {sb_path.name} ({len(storyboard)} entries, {tagged} with search queries)")
        else:
            print(f"  WARNING: Storyboard not found: {sb_path} — proceeding without")

    # Build timeline
    print("\nBuilding timeline...")
    if args.focal_points:
        print("  Focal point detection enabled (qwen3.5:27b — will cache results per image)")
    if storyboard:
        print("  Story-aware footage selection enabled (storyboard match → tagged clips first)")
    if args.stills_only:
        print("  Stills-only mode: all video clips will be skipped")
    segments = build_timeline(
        narration_manifest, footage_manifest, brand_config,
        beat_times=beat_times,
        detect_focal_points=args.focal_points,
        storyboard=storyboard,
        stills_only=args.stills_only,
    )
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
            use_parallax=args.parallax,
        )
    finally:
        if not args.keep_tmp and not args.dry_run and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
