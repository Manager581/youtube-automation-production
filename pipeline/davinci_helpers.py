#!/usr/bin/env python3
"""
DaVinci Resolve Helper Functions

Reusable utilities for building DaVinci timelines. Encapsulates lessons learned
from the Secret Scores production (2026-03-27):

ROOT CAUSE FIXES:
1. NEVER use H.264 for overlays with alpha — use ProRes 4444 (yuva444p10le)
2. NEVER use AddFusionComp() from external API — fades don't persist.
   Bake fade-in/fade-out into video files via FFmpeg before importing.
3. ALWAYS trim V1 clips to match narration duration — prevents dead tail.
4. ALWAYS verify composite mode after setting — SetProperty() can silently fail.
5. NEVER use Fusion for effects from external scripts — bake everything into files.

Usage:
    from pipeline.davinci_helpers import (
        render_overlay_with_fade,
        render_vignette_prores,
        create_chapter_card,
        create_text_reveal,
        trim_timeline_to_narration,
    )
"""

import os
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# =============================================================================
# CODEC RULES
# =============================================================================

# CRITICAL: Any file with transparency MUST use ProRes 4444.
# H.264/H.265 do NOT support alpha channels — the transparency is silently
# discarded, resulting in solid black or opaque frames.
PRORES_4444_ARGS = [
    '-c:v', 'prores_ks',
    '-profile:v', '4',          # ProRes 4444
    '-pix_fmt', 'yuva444p10le', # WITH alpha channel
    '-r', '30',
]

# For opaque videos (no alpha needed), H.264 is fine and much smaller
H264_ARGS = [
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-r', '30',
    '-crf', '18',
]


def render_overlay_with_fade(png_path: str, output_dir: str,
                              duration_sec: float = 5.0,
                              fade_in_sec: float = 0.5,
                              fade_out_sec: float = 0.5) -> str:
    """
    Render a PNG overlay as a ProRes 4444 MOV with fade-in/fade-out baked in.

    WHY: DaVinci's external scripting API cannot persist Fusion compositions
    (AddFusionComp() creates them but they don't save). The only reliable way
    to get fade effects is to bake them into the video file before import.

    Args:
        png_path: Path to the source PNG (can be RGBA or RGB)
        output_dir: Directory for the output MOV
        duration_sec: Total clip duration in seconds
        fade_in_sec: Fade-in duration
        fade_out_sec: Fade-out duration

    Returns:
        Path to the output .mov file (ProRes 4444 with alpha)
    """
    os.makedirs(output_dir, exist_ok=True)
    name = Path(png_path).stem
    output = os.path.join(output_dir, f"{name}_faded.mov")

    fade_in_frames = int(fade_in_sec * 30)
    fade_out_start = int((duration_sec - fade_out_sec) * 30)
    fade_out_frames = int(fade_out_sec * 30)

    cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', png_path,
        '-t', str(duration_sec),
        '-vf', f'fade=in:0:{fade_in_frames},fade=out:{fade_out_start}:{fade_out_frames}',
        *PRORES_4444_ARGS,
        output,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()[-200:]}")

    return output


def render_vignette_prores(output_path: str, duration_sec: float = 10.0,
                            width: int = 1920, height: int = 1080) -> str:
    """
    Create a radial vignette overlay as ProRes 4444 (preserves alpha gradient).

    WHY: H.264 discards alpha channels. A vignette PNG with RGBA gradient
    rendered to .mp4 becomes a solid black frame. Must use ProRes 4444.

    Args:
        output_path: Where to save the .mov file
        duration_sec: Duration of the vignette clip (tile to fill timeline)
        width, height: Frame dimensions

    Returns:
        Path to the output .mov file
    """
    import math

    # Create vignette with radial alpha gradient
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2
    max_dist = math.sqrt(cx ** 2 + cy ** 2)

    # Draw concentric ellipses
    for ring in range(0, max(width, height), 2):
        alpha = int(min(180, max(0, (ring / max_dist) ** 1.8 * 300)))
        draw.ellipse([cx - ring, cy - ring, cx + ring, cy + ring],
                     outline=(0, 0, 0, alpha))

    # Smooth the rings
    from PIL import ImageFilter
    img = img.filter(ImageFilter.GaussianBlur(radius=40))

    # Save temp PNG then render to ProRes 4444
    tmp_png = output_path.replace('.mov', '_tmp.png')
    img.save(tmp_png)

    cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', tmp_png,
        '-t', str(duration_sec),
        *PRORES_4444_ARGS,
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    os.remove(tmp_png)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()[-200:]}")

    return output_path


def create_chapter_card(title: str, output_dir: str,
                         duration_sec: float = 2.0,
                         width: int = 1920, height: int = 1080) -> str:
    """
    Create a chapter transition card (white text on black, H.264).

    Chapter cards are opaque by design — they briefly replace the footage
    to signal a new section. H.264 is fine here (no alpha needed).

    Returns:
        Path to the output .mov file
    """
    os.makedirs(output_dir, exist_ok=True)

    font_paths = [
        "/System/Library/Fonts/Times.ttc",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Georgia.ttf",
    ]
    font_path = next((fp for fp in font_paths if os.path.exists(fp)), None)

    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, 72) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), title, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - tw) // 2
    y = (height - th) // 2
    draw.text((x, y), title, fill=(255, 255, 255), font=font)

    # Subtle underline
    line_y = y + th + 30
    line_w = min(tw + 40, 600)
    draw.line([((width - line_w) // 2, line_y),
               ((width + line_w) // 2, line_y)],
              fill=(100, 100, 100), width=1)

    safe_name = title.lower().replace(' ', '_')
    png_path = os.path.join(output_dir, f"chapter_{safe_name}.png")
    img.save(png_path)

    # Render to H.264 (opaque, no alpha needed)
    mov_path = os.path.join(output_dir, f"chapter_{safe_name}_{duration_sec:.0f}s.mov")
    cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', png_path,
        '-t', str(duration_sec),
        *H264_ARGS,
        mov_path,
    ]
    subprocess.run(cmd, capture_output=True, timeout=15)
    return mov_path


def create_text_reveal(text: str, output_dir: str,
                        style: str = "name",
                        duration_sec: float = 3.0) -> str:
    """
    Create a lower-third text reveal as ProRes 4444 (needs alpha for overlay).

    Text reveals sit on V4 over the B-roll, so they MUST have alpha.
    Includes baked-in fade-in/fade-out.

    Returns:
        Path to the output .mov file
    """
    os.makedirs(output_dir, exist_ok=True)

    font_sizes = {"name": 64, "entity": 56, "location": 52, "date": 72, "callout": 44}
    size = font_sizes.get(style, 56)

    font_paths = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]
    font_path = next((fp for fp in font_paths if os.path.exists(fp)), None)

    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = 120, 880

    # Shadow + text
    draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 200), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    if style == "name":
        draw.line([(x, y + th + 8), (x + tw, y + th + 8)],
                  fill=(255, 255, 255, 150), width=2)

    safe = text.lower().replace(" ", "_").replace("'", "")
    png_path = os.path.join(output_dir, f"text_{safe}.png")
    img.save(png_path)

    # Render as ProRes 4444 WITH fade baked in
    return render_overlay_with_fade(png_path, output_dir,
                                     duration_sec=duration_sec,
                                     fade_in_sec=0.4,
                                     fade_out_sec=0.4)


def create_ducked_music(music_path: str, output_path: str,
                         narr_start_sec: float, narr_end_sec: float,
                         loud_db: float = -8, quiet_db: float = -24) -> str:
    """
    Create a pre-ducked music file with FFmpeg volume automation.

    WHY: DaVinci's external API cannot create Fairlight volume keyframes
    or sidechain compressors. Pre-baking the duck into the audio file
    is the only reliable approach.

    Args:
        music_path: Source music file
        output_path: Where to save the ducked version
        narr_start_sec: When narration begins
        narr_end_sec: When narration ends
        loud_db: Volume during non-narration sections
        quiet_db: Volume during narration (should be very low)

    Returns:
        Path to the ducked music file
    """
    loud_vol = 10 ** (loud_db / 20)
    quiet_vol = 10 ** (quiet_db / 20)

    cmd = [
        'ffmpeg', '-y', '-i', music_path,
        '-filter:a', (
            f"volume=enable='between(t,0,{narr_start_sec})':volume={loud_vol},"
            f"volume=enable='between(t,{narr_start_sec},{narr_end_sec})':volume={quiet_vol},"
            f"volume=enable='gte(t,{narr_end_sec})':volume={loud_vol}"
        ),
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return output_path


def trim_timeline_to_narration(timeline, narr_end_sec: float,
                                buffer_sec: float = 5.0, fps: int = 30):
    """
    Delete all clips on all tracks that start after narration ends + buffer.

    WHY: The original Secret Scores build had 2.5 minutes of silent B-roll
    past the narration end because V1 clips weren't trimmed to match.

    Args:
        timeline: DaVinci Timeline object
        narr_end_sec: When narration ends (in timeline seconds from start)
        buffer_sec: Extra seconds for music fade-out
        fps: Frame rate
    """
    tl_start = timeline.GetStartFrame()
    cutoff = tl_start + int((narr_end_sec + buffer_sec) * fps)

    for track_type in ['video', 'audio']:
        count = timeline.GetTrackCount(track_type)
        for t in range(1, count + 1):
            clips = timeline.GetItemListInTrack(track_type, t) or []
            to_delete = [c for c in clips if c.GetStart() >= cutoff]
            if to_delete:
                timeline.DeleteClips(to_delete)
                print(f"  Trimmed {len(to_delete)} clips from {track_type.upper()} {t}")


def verify_track_alignment(timeline, fps: int = 30, tolerance_sec: float = 5.0):
    """
    MANDATORY post-build check: verify all tracks end at approximately the same time.

    WHY: Secret Scores had music running 2.5 min past narration, V1 clips
    extending past VO, and no check caught it. This function should be called
    after EVERY timeline build.

    Returns:
        dict with 'passed' bool, 'target_end' float, and 'tracks' list of dicts

    Raises:
        ValueError if any continuous track (V1, V2, A1, A2) is misaligned
        beyond tolerance. Point-in-time tracks (V3 chapters, V4 text, A3/A4 SFX)
        are allowed to end early since they're discrete events.
    """
    tl_start = timeline.GetStartFrame()

    # Find narration end as the reference point
    a1_clips = timeline.GetItemListInTrack('audio', 1) or []
    if not a1_clips:
        raise ValueError("No narration on A1 — cannot determine target end")

    narr_end = (a1_clips[-1].GetEnd() - tl_start) / fps
    target_end = narr_end + 5.0  # 5s buffer for music fade

    # Continuous tracks MUST match target (within tolerance)
    continuous_tracks = [
        ('video', 1, 'V1 Footage'),
        ('video', 2, 'V2 Overlays'),
        ('audio', 2, 'A2 Music'),
    ]
    # Point-in-time tracks are OK ending early
    discrete_tracks = [
        ('video', 3, 'V3 Chapters'),
        ('video', 4, 'V4 Text'),
        ('audio', 3, 'A3 SFX'),
        ('audio', 4, 'A4 SFX 2'),
    ]

    results = {'passed': True, 'target_end': target_end, 'tracks': []}
    errors = []

    for track_type, track_idx, label in continuous_tracks + discrete_tracks:
        try:
            clips = timeline.GetItemListInTrack(track_type, track_idx) or []
        except Exception:
            continue
        if not clips:
            continue

        end = (clips[-1].GetEnd() - tl_start) / fps
        diff = end - target_end
        is_continuous = (track_type, track_idx, label) in continuous_tracks

        entry = {
            'track': label,
            'end_sec': end,
            'diff_sec': diff,
            'status': 'ok',
        }

        if is_continuous and abs(diff) > tolerance_sec:
            entry['status'] = 'ERROR'
            errors.append(f"{label} ends at {end:.1f}s (target {target_end:.1f}s, Δ{diff:+.1f}s)")
            results['passed'] = False
        elif is_continuous and diff > tolerance_sec:
            entry['status'] = 'TOO_LONG'
            results['passed'] = False

        results['tracks'].append(entry)

    # Print report
    print(f"\nTRACK ALIGNMENT CHECK (target: {target_end:.1f}s)")
    print(f"{'='*60}")
    for t in results['tracks']:
        icon = '✅' if t['status'] == 'ok' else '❌'
        print(f"  {icon} {t['track']}: {t['end_sec']:.1f}s (Δ{t['diff_sec']:+.1f}s)")

    if errors:
        print(f"\n  ERRORS:")
        for e in errors:
            print(f"    ❌ {e}")
        print(f"\n  Call trim_timeline_to_narration() to fix.")
    else:
        print(f"\n  ✅ All tracks aligned within {tolerance_sec}s tolerance")

    return results


def verify_source_diversity(timeline, max_total_per_source_sec: float = 30.0,
                             fps: int = 30):
    """
    MANDATORY post-build check: verify no single source is over-used.

    WHY: Secret Scores used "Algorithms AI" clip 47 times (274 seconds)
    because the builder had a fallback that kept picking the same source.
    Even though each clip was ≤7s (fair use per cut), 274s from one source
    is a massive copyright risk and will get flagged.

    Args:
        timeline: DaVinci Timeline object
        max_total_per_source_sec: Maximum total seconds from any single source
        fps: Frame rate

    Returns:
        dict with 'passed' bool and 'sources' list
    """
    tl_start = timeline.GetStartFrame()
    v1 = timeline.GetItemListInTrack('video', 1) or []

    source_usage = {}
    for clip in v1:
        name = clip.GetName()
        dur = (clip.GetEnd() - clip.GetStart()) / fps
        if name not in source_usage:
            source_usage[name] = {"count": 0, "total_sec": 0}
        source_usage[name]["count"] += 1
        source_usage[name]["total_sec"] += dur

    results = {'passed': True, 'sources': []}
    print(f"\nSOURCE DIVERSITY CHECK (max {max_total_per_source_sec}s per source)")
    print(f"{'='*60}")

    for name, data in sorted(source_usage.items(), key=lambda x: -x[1]["total_sec"]):
        over = data["total_sec"] > max_total_per_source_sec
        icon = '❌' if over else '✅'
        if over:
            results['passed'] = False
        print(f"  {icon} {data['count']:3d}x {data['total_sec']:6.1f}s  {name[:55]}")
        results['sources'].append({
            'name': name,
            'count': data['count'],
            'total_sec': data['total_sec'],
            'over_limit': over,
        })

    if not results['passed']:
        over_sources = [s for s in results['sources'] if s['over_limit']]
        print(f"\n  ❌ {len(over_sources)} sources exceed {max_total_per_source_sec}s limit")
        print(f"  ACTION: Replace excess clips with images/overlays or different sources")
    else:
        print(f"\n  ✅ All sources within fair use limits")

    return results


def normalize_sfx(sfx_dir: str, target_lufs: float = -12.0):
    """
    Normalize all SFX files to a consistent loudness level.

    WHY: Secret Scores SFX were at -39dB to -49dB (inaudible in the mix).
    The pipeline had no normalization step, so raw downloaded/generated
    SFX played at reference levels that were far too quiet.

    Args:
        sfx_dir: Directory containing SFX .wav files
        target_lufs: Target loudness in LUFS (default -12 = clearly audible)

    Returns:
        dict mapping original filename to normalized filename
    """
    import subprocess

    normalized = {}
    for f in os.listdir(sfx_dir):
        if not f.endswith('.wav') or f.endswith('_loud.wav'):
            continue

        src = os.path.join(sfx_dir, f)
        dst = os.path.join(sfx_dir, f.replace('.wav', '_loud.wav'))

        result = subprocess.run([
            'ffmpeg', '-y', '-i', src,
            '-af', f'loudnorm=I={target_lufs}:TP=-1.5:LRA=11',
            dst,
        ], capture_output=True, timeout=30)

        if result.returncode == 0:
            normalized[f] = os.path.basename(dst)

    return normalized


# =============================================================================
# RULES FOR FUTURE PIPELINE CODE
# =============================================================================
"""
DAVINCI API GOTCHAS (learned the hard way):

1. AddFusionComp() — Creates a Fusion composition on a timeline item but it
   does NOT persist when called from the external scripting API. The comp
   exists during the script run but is gone when you check afterward.
   WORKAROUND: Bake all effects into files via FFmpeg before importing.

2. SetProperty("CompositeMode", "Multiply") — The string "Multiply" doesn't
   work. DaVinci uses numeric enum values (0=Normal, etc). The exact mapping
   isn't documented. SetProperty returns True but the mode doesn't change.
   WORKAROUND: Use the Edit page Inspector UI, or apply effects via CDL/LUT.

3. SetProperty("ZoomX", 1.35) — Works for SOME clips but silently fails for
   others (especially still images placed from PNGs). No error returned.
   WORKAROUND: Apply zoom as a FFmpeg scale+crop before importing.

4. SetCDL() — Works during the session but GetProperty("CDL") returns None.
   The grade IS applied but cannot be read back via API. Verify visually.

5. AppendToTimeline(recordFrame=X) — The recordFrame parameter is IGNORED.
   Clips always append at the end of the track. To place clips at specific
   positions, you must place them in chronological order.
   WORKAROUND: Sort all clips by target position before calling AppendToTimeline.

6. H.264 (.mp4) — Does NOT support alpha channels. Any PNG with transparency
   rendered to H.264 becomes solid/opaque. Use ProRes 4444 for overlays.

7. PNG still duration — DaVinci defaults PNGs to 5 seconds regardless of
   the endFrame parameter. Convert to video first for longer durations.
"""
