#!/usr/bin/env python3
"""
animation_generator.py — Generate static visuals when real footage is unavailable.

When footage_sourcer.py cannot find real images/clips for a storyboard segment,
it flags those segments in `needs_animation`. This module generates a still image
for each flagged segment. The image then feeds directly into the existing Ken Burns
pipeline in video_assembler.py — no downstream changes required.

Visual types generated (based on storyboard `shot_type`):

  document_photo   → A realistic document/memo graphic with typed text content,
                     aged paper texture, CONFIDENTIAL stamp variant
  map              → Dark political map card with location text highlighted
  text_card        → Dark background with key fact as large display text
  person_photo     → Portrait placeholder card with name, role, date
  chapter_card     → Black screen with white serif text (handled by assembler)
  default          → Dark cinematic still with centered narration excerpt

All output is 1920×1080 PNG, dark palette matching Fern's color grade.
Pillow is the only dependency (already available in project venv).

Usage (standalone):
    python pipeline/animation_generator.py \\
        --manifest footage/topic/manifest.json \\
        --out footage/topic/generated/

Usage (from code — called by video_assembler.py):
    from pipeline.animation_generator import generate_animation_frame
    img_path = generate_animation_frame(
        show="FBI internal memo, 1971, COINTELPRO letterhead",
        shot_type="document_photo",
        narration_text="The FBI was watching.",
        out_path=Path("footage/topic/generated/seg_003.png"),
    )
"""

import hashlib
import json
import re
import textwrap
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_W = 1920
OUTPUT_H = 1080

# Fern color palette (dark cinematic)
BG_DARK          = (12, 12, 14)          # near-black background
BG_PAPER         = (220, 208, 185)       # aged document paper
BG_PAPER_DARK    = (180, 165, 140)       # slightly darker paper
TEXT_ON_DARK     = (230, 225, 218)       # warm off-white text
TEXT_ON_PAPER    = (22, 20, 18)          # near-black ink on paper
TEXT_ACCENT      = (170, 130, 60)        # amber/gold accent
TEXT_MUTED       = (100, 95, 88)         # muted secondary text
STAMP_RED        = (165, 28, 28)         # CONFIDENTIAL stamp color
RULE_COLOR       = (50, 45, 40)          # dark divider lines

# Font fallback order for Pillow (system-agnostic)
FONT_PATHS_MONO = [
    "/System/Library/Fonts/Courier.dfont",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]
FONT_PATHS_SERIF = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Times New Roman.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
]
FONT_PATHS_SANS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

CACHE_DIR = Path(".animation_cache")


# ── Pillow helpers ────────────────────────────────────────────────────────────

def _pil_available() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def _load_font(font_paths: list, size: int):
    """Load first available font at given size, falling back to Pillow default."""
    from PIL import ImageFont
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _draw_text_wrapped(draw, text: str, x: int, y: int, max_width: int,
                       font, color: tuple, line_spacing: int = 8) -> int:
    """Draw word-wrapped text, return final y position."""
    from PIL import ImageFont
    # Estimate chars per line based on avg char width
    try:
        bbox = font.getbbox("W")
        char_w = bbox[2] - bbox[0]
    except AttributeError:
        char_w = 10
    chars_per_line = max(20, max_width // max(char_w, 1))
    lines = textwrap.wrap(text, width=chars_per_line)
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        try:
            bbox = font.getbbox(line)
            line_h = bbox[3] - bbox[1]
        except AttributeError:
            line_h = 20
        y += line_h + line_spacing
    return y


def _noise_texture(img, intensity: int = 6):
    """Add subtle film grain to image."""
    import random
    from PIL import Image
    pixels = img.load()
    w, h = img.size
    for _ in range(w * h // 20):  # sample 5% of pixels for performance
        px = random.randint(0, w - 1)
        py = random.randint(0, h - 1)
        r, g, b = pixels[px, py]
        d = random.randint(-intensity, intensity)
        pixels[px, py] = (
            max(0, min(255, r + d)),
            max(0, min(255, g + d)),
            max(0, min(255, b + d)),
        )
    return img


# ── Visual generators ─────────────────────────────────────────────────────────

def _make_document_card(show: str, narration_text: str, out_path: Path):
    """
    Generate a realistic document/memo graphic.
    Styled as a typed government memo with aged paper texture.
    """
    from PIL import Image, ImageDraw, ImageFilter

    img = Image.new("RGB", (OUTPUT_W, OUTPUT_H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Dark vignette border
    for i in range(60):
        alpha = int(80 * (1 - i / 60))
        c = (0, 0, 0)
        draw.rectangle([i, i, OUTPUT_W - i, OUTPUT_H - i], outline=c)

    # Paper area (centered, slightly off-center upward)
    paper_w, paper_h = 780, 820
    paper_x = (OUTPUT_W - paper_w) // 2
    paper_y = (OUTPUT_H - paper_h) // 2 - 20

    # Paper shadow
    shadow_offset = 8
    draw.rectangle(
        [paper_x + shadow_offset, paper_y + shadow_offset,
         paper_x + paper_w + shadow_offset, paper_y + paper_h + shadow_offset],
        fill=(5, 5, 6),
    )

    # Paper background with aged tone
    draw.rectangle([paper_x, paper_y, paper_x + paper_w, paper_y + paper_h],
                   fill=BG_PAPER)

    # Subtle horizontal lines (ruled paper effect)
    for line_y in range(paper_y + 80, paper_y + paper_h - 40, 28):
        draw.line([(paper_x + 30, line_y), (paper_x + paper_w - 30, line_y)],
                  fill=BG_PAPER_DARK, width=1)

    # Header area
    header_font = _load_font(FONT_PATHS_MONO, 18)
    label_font  = _load_font(FONT_PATHS_MONO, 13)
    body_font   = _load_font(FONT_PATHS_MONO, 14)

    # Extract agency name / subject from show text
    # E.g. "FBI internal memo 1971 COINTELPRO letterhead" → FEDERAL BUREAU OF INVESTIGATION
    show_upper = show.upper()
    if "FBI" in show_upper or "FEDERAL BUREAU" in show_upper:
        agency = "FEDERAL BUREAU OF INVESTIGATION"
    elif "CIA" in show_upper:
        agency = "CENTRAL INTELLIGENCE AGENCY"
    elif "NSA" in show_upper:
        agency = "NATIONAL SECURITY AGENCY"
    elif "DOJ" in show_upper or "JUSTICE" in show_upper:
        agency = "U.S. DEPARTMENT OF JUSTICE"
    elif "STATE DEPARTMENT" in show_upper or "DEPT OF STATE" in show_upper:
        agency = "UNITED STATES DEPARTMENT OF STATE"
    else:
        agency = "UNITED STATES GOVERNMENT"

    cx = paper_x + paper_w // 2
    ty = paper_y + 28

    # Agency name (centered, small caps style)
    try:
        bbox = header_font.getbbox(agency)
        text_w = bbox[2] - bbox[0]
    except AttributeError:
        text_w = len(agency) * 10
    draw.text((cx - text_w // 2, ty), agency, font=header_font, fill=TEXT_ON_PAPER)
    ty += 28

    # Thin horizontal rule under agency name
    draw.line([(paper_x + 40, ty), (paper_x + paper_w - 40, ty)],
              fill=TEXT_ON_PAPER, width=1)
    ty += 14

    # TO / FROM / DATE / SUBJECT block
    meta_items = [
        ("MEMORANDUM", ""),
        ("TO:", "Director"),
        ("FROM:", "Special Agent in Charge"),
        ("RE:", _summarize_show(show, 50)),
        ("CLASSIFICATION:", "CONFIDENTIAL"),
    ]
    for label, value in meta_items:
        if value:
            draw.text((paper_x + 45, ty), label, font=label_font, fill=TEXT_MUTED)
            draw.text((paper_x + 200, ty), value, font=label_font, fill=TEXT_ON_PAPER)
        else:
            draw.text((paper_x + 45, ty), label, font=label_font, fill=TEXT_ON_PAPER)
        ty += 22

    ty += 10
    draw.line([(paper_x + 40, ty), (paper_x + paper_w - 40, ty)],
              fill=TEXT_ON_PAPER, width=1)
    ty += 20

    # Body text — narration excerpt typed out
    body_text = narration_text[:500] if narration_text else show
    _draw_text_wrapped(draw, body_text, paper_x + 45, ty,
                       paper_w - 90, body_font, TEXT_ON_PAPER, line_spacing=6)

    # CONFIDENTIAL stamp (rotated, red) — bottom right of paper
    stamp_font = _load_font(FONT_PATHS_MONO, 30)
    stamp_text = "CONFIDENTIAL"
    try:
        bbox = stamp_font.getbbox(stamp_text)
        stamp_w = bbox[2] - bbox[0]
    except AttributeError:
        stamp_w = len(stamp_text) * 18

    # Draw stamp as a bordered box
    sx = paper_x + paper_w - stamp_w - 50
    sy = paper_y + paper_h - 80
    draw.rectangle([sx - 8, sy - 8, sx + stamp_w + 8, sy + 42], outline=STAMP_RED, width=3)
    draw.text((sx, sy), stamp_text, font=stamp_font, fill=STAMP_RED)

    # Subtle noise
    _noise_texture(img, intensity=4)

    img.save(str(out_path), "PNG")
    return out_path


def _make_text_card(show: str, narration_text: str, shot_type: str, out_path: Path):
    """
    Generate a dark cinematic text card.
    Used for documentary_photo, news_footage, and default fallback.
    Large display text on dark background, matching Fern's aesthetic.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (OUTPUT_W, OUTPUT_H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Subtle gradient background — slightly lighter in center
    for y in range(OUTPUT_H):
        factor = 1.0 - abs(y - OUTPUT_H // 2) / (OUTPUT_H * 0.8)
        shade = int(12 + 8 * factor)
        draw.line([(0, y), (OUTPUT_W, y)], fill=(shade, shade, shade + 2))

    # Thin amber rule at top and bottom
    draw.line([(80, 60), (OUTPUT_W - 80, 60)], fill=TEXT_ACCENT, width=1)
    draw.line([(80, OUTPUT_H - 60), (OUTPUT_W - 80, OUTPUT_H - 60)],
              fill=TEXT_ACCENT, width=1)

    # Main display text (2–4 words from show description)
    headline = _make_headline(show, max_words=6)
    headline_font = _load_font(FONT_PATHS_SERIF, 72)
    sub_font      = _load_font(FONT_PATHS_SERIF, 28)
    label_font    = _load_font(FONT_PATHS_SANS, 18)

    # Draw headline centered
    lines = textwrap.wrap(headline, width=25)
    total_h = len(lines) * 90
    start_y = (OUTPUT_H - total_h) // 2 - 40
    for line in lines:
        try:
            bbox = headline_font.getbbox(line)
            w = bbox[2] - bbox[0]
        except AttributeError:
            w = len(line) * 42
        draw.text(((OUTPUT_W - w) // 2, start_y), line,
                  font=headline_font, fill=TEXT_ON_DARK)
        start_y += 90

    # Narration excerpt below headline
    excerpt = narration_text[:120] + "…" if len(narration_text) > 120 else narration_text
    if excerpt:
        sub_lines = textwrap.wrap(excerpt, width=60)
        ey = start_y + 30
        for sub_line in sub_lines[:3]:
            try:
                bbox = sub_font.getbbox(sub_line)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w = len(sub_line) * 16
            draw.text(((OUTPUT_W - w) // 2, ey), sub_line,
                      font=sub_font, fill=TEXT_MUTED)
            ey += 44

    # Shot type label in corner
    type_label = shot_type.replace("_", " ").upper()
    draw.text((90, OUTPUT_H - 50), type_label, font=label_font, fill=TEXT_MUTED)

    _noise_texture(img, intensity=5)
    img.save(str(out_path), "PNG")
    return out_path


def _make_map_card(show: str, narration_text: str, out_path: Path):
    """
    Generate a dark map-style card.
    Shows location name large with grid lines suggesting a map view.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (OUTPUT_W, OUTPUT_H), (8, 10, 14))  # very dark blue-black
    draw = ImageDraw.Draw(img)

    # Grid lines (cartographic look)
    grid_color = (20, 25, 32)
    for gx in range(0, OUTPUT_W, 80):
        draw.line([(gx, 0), (gx, OUTPUT_H)], fill=grid_color, width=1)
    for gy in range(0, OUTPUT_H, 80):
        draw.line([(0, gy), (OUTPUT_W, gy)], fill=grid_color, width=1)

    # Crosshair in center
    cx, cy = OUTPUT_W // 2, OUTPUT_H // 2
    cross_color = (40, 60, 80)
    draw.line([(cx, 0), (cx, OUTPUT_H)], fill=cross_color, width=1)
    draw.line([(0, cy), (OUTPUT_W, cy)], fill=cross_color, width=1)
    draw.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], outline=TEXT_ACCENT, width=1)
    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=TEXT_ACCENT)

    # Location name
    location = _make_headline(show, max_words=4)
    headline_font = _load_font(FONT_PATHS_SANS, 60)
    sub_font      = _load_font(FONT_PATHS_SANS, 24)
    label_font    = _load_font(FONT_PATHS_SANS, 16)

    try:
        bbox = headline_font.getbbox(location)
        w = bbox[2] - bbox[0]
    except AttributeError:
        w = len(location) * 35

    # Location above crosshair
    draw.text(((OUTPUT_W - w) // 2, cy - 160), location,
              font=headline_font, fill=TEXT_ON_DARK)

    # Coordinates-style subtitle (fabricated for aesthetic)
    coord_text = f"REF: {_extract_year(show) or 'CLASSIFIED'}"
    try:
        bbox = sub_font.getbbox(coord_text)
        cw = bbox[2] - bbox[0]
    except AttributeError:
        cw = len(coord_text) * 14
    draw.text(((OUTPUT_W - cw) // 2, cy + 100), coord_text,
              font=sub_font, fill=TEXT_ACCENT)

    # Narration context small at bottom
    excerpt = narration_text[:90] if narration_text else ""
    if excerpt:
        draw.text((90, OUTPUT_H - 70), excerpt[:90], font=label_font, fill=TEXT_MUTED)

    draw.text((OUTPUT_W - 200, OUTPUT_H - 50), "LOCATION REFERENCE",
              font=label_font, fill=TEXT_MUTED)

    _noise_texture(img, intensity=4)
    img.save(str(out_path), "PNG")
    return out_path


def _make_person_card(show: str, narration_text: str, out_path: Path):
    """
    Generate a portrait-style placeholder card for a person.
    Dark background with name, role, dates — styled like Fern's lower-third cards.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (OUTPUT_W, OUTPUT_H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Left dark panel
    draw.rectangle([0, 0, OUTPUT_W // 2 - 20, OUTPUT_H], fill=(10, 10, 12))

    # Right info panel (slightly lighter)
    draw.rectangle([OUTPUT_W // 2 + 20, 0, OUTPUT_W, OUTPUT_H], fill=(14, 14, 16))

    # Portrait placeholder (left side, centered)
    portrait_size = 380
    px = (OUTPUT_W // 2 - portrait_size) // 2
    py = (OUTPUT_H - portrait_size) // 2
    # Outer ring
    draw.ellipse([px - 4, py - 4, px + portrait_size + 4, py + portrait_size + 4],
                 outline=TEXT_ACCENT, width=2)
    # Silhouette fill
    draw.ellipse([px, py, px + portrait_size, py + portrait_size],
                 fill=(22, 22, 26))
    # Head
    head_cx = px + portrait_size // 2
    head_size = 100
    draw.ellipse([head_cx - head_size, py + 70,
                  head_cx + head_size, py + 70 + head_size * 2],
                 fill=(35, 35, 40))
    # Body
    draw.ellipse([head_cx - 150, py + portrait_size - 100,
                  head_cx + 150, py + portrait_size + 100],
                 fill=(35, 35, 40))

    # Name and info on right side
    name = _extract_person_name(show) or _make_headline(show, max_words=3)
    name_font  = _load_font(FONT_PATHS_SERIF, 52)
    role_font  = _load_font(FONT_PATHS_SANS, 26)
    label_font = _load_font(FONT_PATHS_SANS, 18)

    rx = OUTPUT_W // 2 + 60
    ry = OUTPUT_H // 2 - 120

    # Amber accent line
    draw.rectangle([rx, ry - 6, rx + 4, ry + 60], fill=TEXT_ACCENT)

    # Name
    draw.text((rx + 18, ry), name, font=name_font, fill=TEXT_ON_DARK)
    ry += 70

    # Year if found
    year = _extract_year(show)
    if year:
        draw.text((rx + 18, ry), year, font=role_font, fill=TEXT_ACCENT)
        ry += 44

    # Narration excerpt
    excerpt_lines = textwrap.wrap(narration_text[:200] if narration_text else show, width=32)
    for line in excerpt_lines[:4]:
        draw.text((rx + 18, ry), line, font=label_font, fill=TEXT_MUTED)
        ry += 28

    # "ARCHIVAL PHOTO" watermark bottom left
    draw.text((90, OUTPUT_H - 50), "ARCHIVAL REFERENCE", font=label_font, fill=TEXT_MUTED)

    _noise_texture(img, intensity=5)
    img.save(str(out_path), "PNG")
    return out_path


# ── Text extraction helpers ───────────────────────────────────────────────────

def _summarize_show(show: str, max_chars: int) -> str:
    """Truncate show description to max_chars words for document subject line."""
    if len(show) <= max_chars:
        return show
    return show[:max_chars - 1].rsplit(" ", 1)[0] + "…"


def _make_headline(show: str, max_words: int = 5) -> str:
    """Extract the key noun phrase from show description for large display text."""
    # Remove common filler words
    stop = {"a", "an", "the", "of", "in", "at", "by", "for", "with", "and",
            "from", "on", "to", "as", "its", "this", "that", "their", "is",
            "are", "was", "were", "be", "been", "being", "photo", "image",
            "picture", "footage", "video", "showing", "shows", "taken"}
    words = [w for w in re.findall(r"\b\w+\b", show) if w.lower() not in stop]
    headline = " ".join(words[:max_words])
    return headline.upper() if headline else show[:40].upper()


def _extract_year(text: str) -> str | None:
    """Extract a 4-digit year from text."""
    m = re.search(r"\b(1[89]\d\d|20[012]\d)\b", text)
    return m.group(1) if m else None


def _extract_person_name(text: str) -> str | None:
    """Extract a likely person name (title-cased 2+ word sequence)."""
    m = re.search(r"\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b", text)
    return m.group(1) if m else None


# ── Cache ─────────────────────────────────────────────────────────────────────

def _cache_key(show: str, shot_type: str, narration_text: str) -> str:
    key = f"{shot_type}|{show}|{narration_text[:100]}"
    return hashlib.md5(key.encode()).hexdigest()[:16]


# ── Main function ─────────────────────────────────────────────────────────────

def generate_animation_frame(
    show: str,
    shot_type: str,
    narration_text: str,
    out_path: Path,
    use_cache: bool = True,
) -> Path | None:
    """
    Generate a single still image frame for a segment that has no real footage.

    Args:
        show:           Storyboard `show` field — specific visual description
        shot_type:      Storyboard `shot_type` field (document_photo, map, etc.)
        narration_text: The narration spoken over this segment
        out_path:       Where to save the output PNG
        use_cache:      Whether to use cache (avoids regenerating identical frames)

    Returns:
        out_path if successful, None if Pillow not available or error occurred.
    """
    if not _pil_available():
        print("  [animation] WARNING: Pillow not installed — run: pip install Pillow")
        return None

    # Cache check
    if use_cache:
        CACHE_DIR.mkdir(exist_ok=True)
        ck = _cache_key(show, shot_type, narration_text)
        cache_file = CACHE_DIR / f"{ck}.png"
        if cache_file.exists():
            import shutil
            shutil.copy2(cache_file, out_path)
            return out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if shot_type == "document_photo":
            _make_document_card(show, narration_text, out_path)
        elif shot_type == "map":
            _make_map_card(show, narration_text, out_path)
        elif shot_type in ("person_photo",):
            _make_person_card(show, narration_text, out_path)
        else:
            # documentary_photo, news_footage, archival_footage, default
            _make_text_card(show, narration_text, shot_type, out_path)
    except Exception as e:
        print(f"  [animation] ERROR generating frame for '{show[:40]}': {e}")
        return None

    # Save to cache
    if use_cache and out_path.exists():
        import shutil
        CACHE_DIR.mkdir(exist_ok=True)
        ck = _cache_key(show, shot_type, narration_text)
        shutil.copy2(out_path, CACHE_DIR / f"{ck}.png")

    return out_path


def generate_for_manifest(
    manifest_path: Path,
    out_dir: Path,
    use_cache: bool = True,
) -> list[dict]:
    """
    Process all `needs_animation` segments from a footage manifest.
    Generates one PNG per segment and returns list of {segment_id, path} records.

    The manifest must have a `needs_animation` list (added by footage_sourcer.py)
    and a `storyboard` list with `show`, `shot_type`, `text` fields.
    """
    manifest = json.loads(manifest_path.read_text())
    needs_animation = manifest.get("needs_animation", [])
    storyboard = manifest.get("storyboard", [])

    if not needs_animation:
        print("No segments flagged for animation in manifest.")
        return []

    # Build lookup: segment_id → storyboard entry
    sb_by_id: dict[int, dict] = {}
    for entry in storyboard:
        sid = entry.get("segment_id")
        if sid is not None:
            sb_by_id[sid] = entry

    out_dir.mkdir(parents=True, exist_ok=True)
    results = []

    print(f"\nGenerating {len(needs_animation)} animation frames...")
    for i, seg_id in enumerate(needs_animation):
        sb = sb_by_id.get(seg_id, {})
        show           = sb.get("show", f"segment {seg_id}")
        shot_type      = sb.get("shot_type", "documentary_photo")
        narration_text = sb.get("text", "")

        out_path = out_dir / f"anim_seg_{seg_id:04d}.png"
        print(f"  [{i+1}/{len(needs_animation)}] {shot_type:20s}  {show[:55]}", end="  ")

        result = generate_animation_frame(
            show=show,
            shot_type=shot_type,
            narration_text=narration_text,
            out_path=out_path,
            use_cache=use_cache,
        )
        if result:
            print("✓")
            results.append({"segment_id": seg_id, "path": str(out_path), "shot_type": shot_type})
        else:
            print("FAILED")

    # Inject generated frames into manifest clips list
    clips = manifest.get("clips", [])
    for r in results:
        clips.append({
            "path": r["path"],
            "local_path": r["path"],
            "source": "animation_generator",
            "shot_type": r["shot_type"],
            "storyboard_segment_ids": [r["segment_id"]],
            "downloaded": True,
            "generated": True,
        })
    manifest["clips"] = clips

    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest updated with {len(results)} generated frames: {manifest_path}")
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    import sys

    ap = argparse.ArgumentParser(
        description="Generate still image frames for storyboard segments lacking real footage"
    )
    sub = ap.add_subparsers(dest="cmd")

    # Single frame
    fp = sub.add_parser("frame", help="Generate one frame")
    fp.add_argument("--show",      required=True, help="Storyboard show description")
    fp.add_argument("--type",      default="documentary_photo",
                    help="Shot type: document_photo|map|person_photo|documentary_photo|...")
    fp.add_argument("--narration", default="", help="Narration text for this segment")
    fp.add_argument("--out",       required=True, help="Output PNG path")
    fp.add_argument("--no-cache",  action="store_true")

    # Full manifest
    mp = sub.add_parser("manifest", help="Process all needs_animation from manifest")
    mp.add_argument("--manifest", required=True, help="Path to footage manifest.json")
    mp.add_argument("--out",      required=True, help="Output directory for generated PNGs")
    mp.add_argument("--no-cache", action="store_true")

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        sys.exit(1)

    if not _pil_available():
        print("ERROR: Pillow not installed. Run: pip install Pillow")
        sys.exit(1)

    if args.cmd == "frame":
        result = generate_animation_frame(
            show=args.show,
            shot_type=args.type,
            narration_text=args.narration,
            out_path=Path(args.out),
            use_cache=not args.no_cache,
        )
        if result:
            print(f"Generated: {result}")
        else:
            print("Generation failed.")
            sys.exit(1)

    elif args.cmd == "manifest":
        results = generate_for_manifest(
            manifest_path=Path(args.manifest),
            out_dir=Path(args.out),
            use_cache=not args.no_cache,
        )
        print(f"\nDone: {len(results)} frames generated.")


if __name__ == "__main__":
    main()
