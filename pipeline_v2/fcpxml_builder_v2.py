#!/usr/bin/env python3
"""
FCPXML Builder v2 — Custom timeline builder for YouTube documentary pipeline.

Built from scratch for director v4 + Whisper alignment. Places EVERY element
at its exact timecode:
  V1: Director's visual picks (video clips + images)
  V2: Text overlay MOVs (50 overlays at narration-synced positions)
  V3: Chapter card MOVs
  A1: Narration WAV (full 150 WPM, 27.3 min)
  A2: Music (one ducked track per chapter)
  A3/A4: SFX (max 2 per chapter at Whisper word timestamps)

Clip audio: play / play_then_mute / mute per director decisions.
Transitions: fade_from_black, dissolve, cut.
Ken Burns: animated zoom on still images (keyframed scale transform).

Usage:
  cd /Users/jefflawrence/Documents/youtube-automation-production
  venv/bin/python -m pipeline_v2.fcpxml_builder_v2 --output timeline_v2.fcpxml
  venv/bin/python -m pipeline_v2.fcpxml_builder_v2 --output timeline_v2.fcpxml --import-resolve

Requires: ffprobe in PATH for video clip durations.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline_v2.chapter_assembler import (
    load_director, load_alignment, match_segments_to_narration,
    split_into_chapters, find_overlay_file, pick_chapter_sfx,
    find_media_file, CHAPTERS,
)

# ─── Constants ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
FPS = 24
TC_START = 3600  # 01:00:00:00
WIDTH = 1920
HEIGHT = 1080

# Use smoothed narration (crossfaded chunk boundaries, same duration as narration.wav)
NARRATION_PATH = PROJECT_ROOT / "audio" / "breaking_law" / "narration_smoothed.wav"
SFX_DIR = PROJECT_ROOT / "assets" / "sfx"
OVERLAY_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "overlays"
CHAPTER_CARD_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "chapters"
MUSIC_DIR = PROJECT_ROOT / "audio" / "breaking_law" / "music_tracks"

# FCPXML lane assignments
LANE_OVERLAY = 1   # V2
LANE_CHAPTER = 2   # V3
LANE_NARRATION = 3 # A1  (using 3-6 to avoid DaVinci lane conflicts)
LANE_MUSIC = 4     # A2
LANE_SFX1 = 5      # A3
LANE_SFX2 = 6      # A4

# Fix 6: Valid chapter names — reject any invented ones
VALID_CHAPTERS = {"THE FORMULA", "THE DATA", "THE MACHINES", "THE RENT", "THE RECKONING"}

# Fix 8: Normalize non-standard music_state values to valid states
MUSIC_STATE_MAP = {
    "raise": "playing", "rising": "playing", "building": "playing",
    "full": "playing", "transition": "ducking",
}


# ─── Time helpers ───────────────────────────────────────────────────────────

def to_rational(seconds):
    """Convert seconds to FCPXML rational time (e.g., '86401/24s')."""
    if seconds is None or seconds < 0:
        return "0/1s"
    frames = round(seconds * FPS)
    frac = Fraction(frames, FPS)
    return f"{frac.numerator}/{frac.denominator}s"


def to_dur(seconds):
    """Convert duration, minimum 1 frame."""
    if seconds is None or seconds <= 0:
        seconds = 1 / FPS
    return to_rational(seconds)


# ─── Media helpers ──────────────────────────────────────────────────────────

def get_duration(filepath):
    """Get media file duration via ffprobe."""
    try:
        r = subprocess.run(
            ['/opt/homebrew/bin/ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_format', filepath],
            capture_output=True, text=True, timeout=10
        )
        info = json.loads(r.stdout)
        return float(info['format']['duration'])
    except Exception:
        return None


def is_image(path):
    return Path(path).suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')


def is_video(path):
    return Path(path).suffix.lower() in ('.mp4', '.mov', '.avi', '.mkv', '.mxf')


def is_audio(path):
    return Path(path).suffix.lower() in ('.wav', '.mp3', '.aac', '.flac')


def file_url(path):
    """Convert absolute path to file:// URL."""
    return "file://" + os.path.abspath(path).replace(" ", "%20")


def _normalize_music_state(state):
    """Fix 8: Normalize non-standard music_state values."""
    if not state:
        return state
    return MUSIC_STATE_MAP.get(state, state)


# ─── FCPXML Builder ────────────────────────────────────────────────────────

class FCPXMLBuilderV2:
    def __init__(self):
        self._rid = 0
        self._assets = {}     # path → (resource_id, format_id)
        self._formats = []    # (id, attrs)
        self._main_fmt = None

    def _next_id(self):
        rid = f"r{self._rid}"
        self._rid += 1
        return rid

    def _register_format(self):
        if self._main_fmt:
            return self._main_fmt
        self._main_fmt = self._next_id()
        return self._main_fmt

    def _register_asset(self, filepath):
        """Register a media file. Returns (asset_id, format_id)."""
        abspath = os.path.abspath(filepath)
        if abspath in self._assets:
            return self._assets[abspath]

        asset_id = self._next_id()
        fmt_id = self._next_id()

        self._assets[abspath] = (asset_id, fmt_id)
        return asset_id, fmt_id

    def build(self, segments, chapter_map, narration_path, sfx_by_chapter, music_by_chapter, alignment=None):
        """Build complete FCPXML ElementTree.

        Args:
            segments: flat list of all segments with _narr_start/_narr_end
            chapter_map: {chapter_num: [segments]}
            narration_path: path to narration WAV
            sfx_by_chapter: {chapter_num: [(time_sec, sfx_file)]}
            music_by_chapter: {chapter_num: (music_file, start_sec, end_sec)}
        """
        main_fmt = self._register_format()

        # ── Calculate total duration ──
        total_dur = segments[-1]["_narr_end"] + 5.0

        # ── Resolve all media and get durations ──
        print("  Resolving media files...")
        media_cache = {}  # filename → (abspath, duration)

        for seg in segments:
            # Fix 8: normalize music_state on each segment
            if "music_state" in seg:
                seg["music_state"] = _normalize_music_state(seg.get("music_state"))

            # Resolve visual_file (v4 schema)
            vf = seg.get("visual_file")
            if vf:
                path = find_media_file(vf)
                if path:
                    dur = get_duration(path) if not is_image(path) else None
                    media_cache[vf] = (path, dur)
            # Resolve beats visual files (v5 schema)
            for beat in (seg.get("beats") or []):
                bvf = beat.get("visual_file")
                if bvf and bvf not in media_cache:
                    path = find_media_file(bvf)
                    if path:
                        dur = get_duration(path) if not is_image(path) else None
                        media_cache[bvf] = (path, dur)

        # ── Pre-process: close gaps between segments ──
        # Extend each segment's end to the next segment's start.
        # This prevents orphan narration sentences from creating black holes.
        # Fix 6: Also filter out marker-only segments (chapter_card + [CHAPTER:...] text)
        active_segs = [s for s in segments
                       if s.get("text", "").strip()
                       and not s["text"].startswith("[")
                       and not (s.get("chapter_card") and s.get("text", "").startswith("[CHAPTER:"))]
        for i in range(len(active_segs) - 1):
            gap = active_segs[i + 1]["_narr_start"] - active_segs[i]["_narr_end"]
            if gap > 0.1:
                active_segs[i]["_narr_end"] = active_segs[i + 1]["_narr_start"]

        # Force first segment to start at 0 (no black gap at start)
        if active_segs and active_segs[0]["_narr_start"] > 0:
            active_segs[0]["_narr_start"] = 0

        # Cap last segment at narration duration
        if alignment:
            narr_total = alignment.get("duration_sec", active_segs[-1]["_narr_end"])
        else:
            narr_total = active_segs[-1]["_narr_end"]
        if active_segs[-1]["_narr_end"] > narr_total:
            active_segs[-1]["_narr_end"] = narr_total

        # ── Build V1 spine clips ──
        # Supports BOTH schemas:
        #   v4 (old): one "visual_file" per segment
        #   v5 (new): "beats" array with multiple visuals per segment
        print("  Building V1 spine...")
        v1_clips = []
        for seg in active_segs:
            seg_start = seg["_narr_start"]
            seg_end = seg["_narr_end"]
            seg_dur = max(seg_end - seg_start, 0.5)

            # Check for v5 beats schema
            beats = seg.get("beats")
            if beats and isinstance(beats, list) and len(beats) > 0:
                # v5: multiple visual beats per segment
                num_beats = len(beats)
                beat_dur = seg_dur / num_beats  # distribute evenly

                for b_idx, beat in enumerate(beats):
                    vf = beat.get("visual_file")
                    if not vf or vf not in media_cache:
                        continue
                    path, source_dur = media_cache[vf]
                    b_start = seg_start + (b_idx * beat_dur)
                    b_dur = beat_dur
                    clip_start_sec = beat.get("clip_start_sec") or 0

                    if is_image(path):
                        if b_dur > 7.5:
                            # Split long image beats further
                            seg_text_lower = beat.get("text", seg.get("text", "")).lower()
                            seg_keywords = set(re.findall(r'[a-z]{4,}', seg_text_lower))
                            seg_keywords -= {'that', 'this', 'with', 'from', 'they', 'their',
                                             'were', 'have', 'been', 'what', 'when', 'than',
                                             'more', 'most', 'just', 'only', 'also', 'into'}

                            # First sub-clip: director's chosen image
                            v1_clips.append({
                                "path": path, "offset": b_start,
                                "duration": min(5.0, b_dur), "start": 0,
                                "name": os.path.basename(path),
                                "clip_audio": beat.get("clip_audio", "mute"),
                                "clip_audio_duration": beat.get("clip_audio_duration"),
                                "transition_in": "cut",
                                "zoom_target": beat.get("zoom_target", "wide"),
                                "is_image": True, "seg": seg,
                            })
                            filled = 5.0
                            avail = [(sum(1 for kw in seg_keywords if kw in n.lower()), p)
                                     for n, (p, _) in media_cache.items()
                                     if is_image(p) and p != path]
                            avail.sort(key=lambda x: -x[0])
                            avail = [p for _, p in avail] or [path]
                            rot = 0
                            while filled < b_dur - 1.0:
                                alt = avail[rot % len(avail)]
                                rot += 1
                                chunk = min(6.0, b_dur - filled)
                                v1_clips.append({
                                    "path": alt, "offset": b_start + filled,
                                    "duration": chunk, "start": 0,
                                    "name": os.path.basename(alt),
                                    "clip_audio": "mute", "clip_audio_duration": None,
                                    "transition_in": "cut",
                                    "zoom_target": beat.get("zoom_target", "wide"),
                                    "is_image": True, "seg": seg,
                                })
                                filled += chunk
                        else:
                            v1_clips.append({
                                "path": path, "offset": b_start,
                                "duration": b_dur, "start": 0,
                                "name": os.path.basename(path),
                                "clip_audio": beat.get("clip_audio", "mute"),
                                "clip_audio_duration": beat.get("clip_audio_duration"),
                                "transition_in": "cut",
                                "zoom_target": beat.get("zoom_target", "wide"),
                                "is_image": True, "seg": seg,
                            })
                    else:
                        available = (source_dur or 60) - clip_start_sec
                        use_dur = min(b_dur, available)
                        v1_clips.append({
                            "path": path, "offset": b_start,
                            "duration": use_dur, "start": clip_start_sec,
                            "name": os.path.basename(path),
                            "clip_audio": beat.get("clip_audio", "mute"),
                            "clip_audio_duration": beat.get("clip_audio_duration"),
                            "transition_in": "cut",
                            "zoom_target": beat.get("zoom_target", "wide"),
                            "is_image": False, "seg": seg,
                        })
                        if use_dur < b_dur - 1.0:
                            v1_clips[-1]["duration"] = b_dur  # extend to fill
                continue  # skip the v4 fallback below

            # v4 fallback: single visual_file per segment
            vf = seg.get("visual_file")
            if not vf or vf not in media_cache:
                continue

            path, source_dur = media_cache[vf]

            clip_start = seg.get("clip_start_sec") or 0

            if is_image(path):
                # Image: if segment > 7s, split into multiple 5-7s sub-clips
                # using different images from the media pool for visual variety
                if seg_dur > 7.5:
                    # First sub-clip: director's chosen image (5s)
                    sub_dur = min(5.0, seg_dur)
                    v1_clips.append({
                        "path": path,
                        "offset": seg["_narr_start"],
                        "duration": sub_dur,
                        "start": 0,
                        "name": os.path.basename(path),
                        "clip_audio": "mute",
                        "clip_audio_duration": None,
                        "transition_in": seg.get("transition_in", "cut"),
                        "zoom_target": seg.get("zoom_target", "wide"),
                        "is_image": True,
                        "seg": seg,
                    })
                    # Remaining sub-clips: use TOPICALLY RELEVANT images
                    # Extract keywords from narration text to filter images
                    seg_text_lower = seg.get("text", "").lower()
                    seg_keywords = set(re.findall(r'[a-z]{4,}', seg_text_lower))
                    seg_keywords -= {'that', 'this', 'with', 'from', 'they', 'their',
                                     'were', 'have', 'been', 'what', 'when', 'than',
                                     'more', 'most', 'just', 'only', 'also', 'into',
                                     'over', 'would', 'could', 'should', 'about'}

                    # Score each available image by keyword overlap with filename
                    avail_images = []
                    for n, (p, _) in media_cache.items():
                        if not is_image(p) or p == path:
                            continue
                        fname_words = set(re.findall(r'[a-z]{4,}', n.lower()))
                        score = len(seg_keywords & fname_words)
                        avail_images.append((score, p))

                    # Sort by relevance (highest score first), then shuffle within same score
                    avail_images.sort(key=lambda x: -x[0])
                    avail_images = [p for _, p in avail_images]

                    if not avail_images:
                        avail_images = [p for n, (p, _) in media_cache.items()
                                       if is_image(p) and p != path]
                    img_rot_idx = 0

                    filled = sub_dur
                    while filled < seg_dur - 1.0:
                        if avail_images:
                            alt_img = avail_images[img_rot_idx % len(avail_images)]
                            img_rot_idx += 1
                        else:
                            alt_img = path

                        chunk = min(6.0, seg_dur - filled)
                        v1_clips.append({
                            "path": alt_img,
                            "offset": seg["_narr_start"] + filled,
                            "duration": chunk,
                            "start": 0,
                            "name": os.path.basename(alt_img),
                            "clip_audio": "mute",
                            "clip_audio_duration": None,
                            "transition_in": "cut",
                            "zoom_target": seg.get("zoom_target", "wide"),
                            "is_image": True,
                            "seg": seg,
                        })
                        filled += chunk
                    continue  # skip the normal append below

                clip_dur = seg_dur
                clip_start = 0
            else:
                # Video: use up to segment duration, capped at source length
                available = (source_dur or 60) - clip_start
                clip_dur = min(seg_dur, available)

            v1_clips.append({
                "path": path,
                "offset": seg["_narr_start"],
                "duration": clip_dur,
                "start": clip_start,
                "name": os.path.basename(path),
                "clip_audio": seg.get("clip_audio", "mute"),
                "clip_audio_duration": seg.get("clip_audio_duration"),
                "transition_in": seg.get("transition_in", "cut"),
                "zoom_target": seg.get("zoom_target", "wide"),
                "is_image": is_image(path),
                "seg": seg,
            })

            # If video clip is shorter than segment, fill remaining time
            # by extending the clip (last frame holds) or adding next visual
            if not is_image(path) and clip_dur < seg_dur - 1.0:
                remaining = seg_dur - clip_dur
                v1_clips[-1]["duration"] = seg_dur  # extend to fill

        # Final safety: ensure no gaps between consecutive V1 clips
        for i in range(len(v1_clips) - 1):
            clip_end = v1_clips[i]["offset"] + v1_clips[i]["duration"]
            next_start = v1_clips[i + 1]["offset"]
            if next_start > clip_end + 0.05:
                v1_clips[i]["duration"] = next_start - v1_clips[i]["offset"]

        print(f"  V1: {len(v1_clips)} clips")

        # ── Collect lane clips ──
        lane_clips = []  # (lane, offset, duration, path, start, name, is_audio, extra)

        # V2: Overlays (skip the $5B overlay at intro — it's a black card that covers the news clip)
        overlay_count = 0
        for seg in segments:
            ov_text = seg.get("text_overlay")
            if not ov_text:
                continue
            # Skip the $5B overlay at intro — black card covers the Facebook news clip
            if ov_text.startswith("$5,000,000,000") and seg["_narr_start"] < 5.0:
                continue
            ov_path = find_overlay_file(ov_text)
            if not ov_path:
                continue
            ov_dur = get_duration(ov_path) or 3.0
            lane_clips.append({
                "lane": LANE_OVERLAY,
                "offset": seg["_narr_start"],
                "duration": ov_dur,
                "path": ov_path,
                "start": 0,
                "name": os.path.basename(ov_path),
                "is_audio": False,
            })
            overlay_count += 1
        print(f"  V2: {overlay_count} overlays")

        # V3: Chapter cards — use MOV files from chapters/ directory
        # Fix 6: Only place valid chapter cards, skip duplicates and invented names
        card_count = 0
        seen_chapters = set()
        for seg in segments:
            card = seg.get("chapter_card")
            if not card:
                continue
            # Fix 6: Skip invented chapter names
            card_upper = card.upper().strip()
            if card_upper not in VALID_CHAPTERS:
                print(f"    SKIP invented chapter card: '{card}'")
                continue
            # Fix 6: Skip duplicate chapter cards
            if card_upper in seen_chapters:
                print(f"    SKIP duplicate chapter card: '{card}'")
                continue
            seen_chapters.add(card_upper)

            # Map chapter name to filename
            card_slug = card.lower().replace(' ', '_')
            card_name = f"chapter_{card_slug}.mov"
            card_path = str(CHAPTER_CARD_DIR / card_name)
            if not os.path.exists(card_path):
                # Try without "the_" prefix
                card_name2 = f"chapter_{card_slug.replace('the_', '')}.mov"
                card_path2 = str(CHAPTER_CARD_DIR / card_name2)
                if os.path.exists(card_path2):
                    card_path = card_path2
                    card_name = card_name2
                else:
                    print(f"    WARNING: chapter card not found: {card_name}")
                    continue

            card_dur = get_duration(card_path) or 3.0
            # Place AT the chapter start (not before — the visual fills the gap)
            card_offset = seg["_narr_start"]
            lane_clips.append({
                "lane": LANE_CHAPTER,
                "offset": card_offset,
                "duration": min(card_dur, 4.0),
                "path": card_path,
                "start": 0,
                "name": card_name,
                "is_audio": False,
            })
            card_count += 1
            print(f"    Card: {card_name} at {card_offset:.1f}s")
        print(f"  V3: {card_count} chapter cards")

        # A1: Narration
        narr_dur = get_duration(str(narration_path))
        if narr_dur:
            lane_clips.append({
                "lane": LANE_NARRATION,
                "offset": 0,
                "duration": narr_dur,
                "path": str(narration_path),
                "start": 0,
                "name": "narration.wav",
                "is_audio": True,
            })
            print(f"  A1: narration ({narr_dur:.1f}s)")

        # A2: Music per chapter
        for ch_num, (music_file, ch_start, ch_end) in music_by_chapter.items():
            music_path = str(MUSIC_DIR / music_file)
            if not os.path.exists(music_path):
                continue
            music_dur = min(get_duration(music_path) or 200, ch_end - ch_start)
            lane_clips.append({
                "lane": LANE_MUSIC,
                "offset": ch_start,
                "duration": music_dur,
                "path": music_path,
                "start": 0,
                "name": music_file,
                "is_audio": True,
            })
        print(f"  A2: {len(music_by_chapter)} music tracks")

        # A3/A4: SFX — alternate lanes globally (not per-chapter)
        # Fix 7: Cap SFX at 2 per chapter
        sfx_count = 0
        sfx_global_idx = 0
        sfx_placed_by_chapter = defaultdict(int)
        for ch_num in sorted(sfx_by_chapter.keys()):
            sfx_list = sfx_by_chapter[ch_num]
            for sfx_time, sfx_file in sfx_list:
                # Fix 7: enforce max 2 SFX per chapter
                if sfx_placed_by_chapter[ch_num] >= 2:
                    continue
                sfx_path = str(SFX_DIR / sfx_file)
                if not os.path.exists(sfx_path):
                    continue
                sfx_dur = get_duration(sfx_path) or 2.0
                lane = LANE_SFX1 if sfx_global_idx % 2 == 0 else LANE_SFX2
                lane_clips.append({
                    "lane": lane,
                    "offset": sfx_time,
                    "duration": sfx_dur,
                    "path": sfx_path,
                    "start": 0,
                    "name": sfx_file,
                    "is_audio": True,
                })
                sfx_count += 1
                sfx_global_idx += 1
                sfx_placed_by_chapter[ch_num] += 1
        print(f"  A3/A4: {sfx_count} SFX ({sfx_global_idx} total, alternating lanes)")

        # ── Generate XML ──
        print("  Generating FCPXML...")
        root = Element("fcpxml", version="1.9")

        # Resources
        resources = SubElement(root, "resources")
        SubElement(resources, "format", {
            "id": main_fmt,
            "name": f"FFVideoFormat{HEIGHT}p{FPS}",
            "frameDuration": f"1/{FPS}s",
            "width": str(WIDTH),
            "height": str(HEIGHT),
        })

        # Register all assets
        all_files = set()
        for c in v1_clips:
            all_files.add(c["path"])
        for lc in lane_clips:
            all_files.add(lc["path"])

        for fpath in all_files:
            asset_id, fmt_id = self._register_asset(fpath)

            # Format for this asset
            SubElement(resources, "format", {
                "id": fmt_id,
                "name": "FFVideoFormatRateUndefined",
                "width": str(WIDTH),
                "height": str(HEIGHT),
            })

            # Asset element
            attrs = {
                "id": asset_id,
                "name": os.path.basename(fpath),
                "start": "0/1s",
                "format": fmt_id,
            }

            if is_image(fpath):
                attrs["hasVideo"] = "1"
                attrs["duration"] = "0/1s"
            elif is_video(fpath):
                dur = get_duration(fpath)
                attrs["hasVideo"] = "1"
                attrs["hasAudio"] = "1"
                attrs["audioSources"] = "1"
                attrs["audioChannels"] = "2"
                attrs["duration"] = to_rational(dur) if dur else "0/1s"
            elif is_audio(fpath):
                dur = get_duration(fpath)
                attrs["hasAudio"] = "1"
                attrs["audioSources"] = "1"
                attrs["audioChannels"] = "1"
                attrs["duration"] = to_rational(dur) if dur else "0/1s"

            asset_el = SubElement(resources, "asset", attrs)
            SubElement(asset_el, "media-rep", {
                "kind": "original-media",
                "src": file_url(fpath),
            })

        # Library / Event / Project / Sequence
        library = SubElement(root, "library")
        event = SubElement(library, "event", name="Production")
        project = SubElement(event, "project", name="Breaking Law FINAL")

        sequence = SubElement(project, "sequence", {
            "format": main_fmt,
            "duration": to_rational(total_dur),
            "tcStart": to_rational(TC_START),
            "tcFormat": "NDF",
        })

        spine = SubElement(sequence, "spine")

        # ── Build spine (V1) with transitions (Fix 4) ──
        cursor = 0  # current position in seconds
        prev_clip = None  # track previous clip for transitions
        # Build a lookup: chapter start times for detecting chapter boundaries
        chapter_starts = set()
        for ch_num, segs in chapter_map.items():
            if segs:
                chapter_starts.add(round(segs[0]["_narr_start"], 2))

        for clip_idx, clip in enumerate(v1_clips):
            clip_offset = clip["offset"]
            clip_dur = clip["duration"]

            # Fix 4: Insert transition at chapter boundaries (between clips)
            trans = clip.get("transition_in", "cut")
            insert_transition = False

            if trans == "fade_from_black" and clip_idx == 0:
                # Fade from black at the very start
                insert_transition = True
            elif trans == "dissolve" and prev_clip is not None:
                insert_transition = True
            elif prev_clip is not None and round(clip_offset, 2) in chapter_starts:
                # Chapter boundary — insert cross dissolve
                insert_transition = True

            if insert_transition:
                trans_dur = 1.0  # 1 second = 24/24s at 24fps
                trans_offset = TC_START + clip_offset - (trans_dur / 2)
                if trans == "fade_from_black" and clip_idx == 0:
                    trans_offset = TC_START + clip_offset
                SubElement(spine, "transition", {
                    "name": "Cross Dissolve",
                    "offset": to_rational(max(trans_offset, TC_START)),
                    "duration": to_dur(trans_dur),
                })

            # Insert gap if needed before this clip
            if clip_offset > cursor + 0.02:
                gap_dur = clip_offset - cursor
                SubElement(spine, "gap", {
                    "name": "Gap",
                    "offset": to_rational(TC_START + cursor),
                    "duration": to_dur(gap_dur),
                    "start": to_rational(TC_START),
                })
                cursor = clip_offset
            elif clip_offset < cursor - 0.02:
                # Overlap — skip this clip
                continue

            # Place the clip
            abs_offset = TC_START + cursor
            path = clip["path"]
            asset_id, _ = self._assets[os.path.abspath(path)]

            if clip["is_image"]:
                el = SubElement(spine, "video", {
                    "ref": asset_id,
                    "name": clip["name"],
                    "offset": to_rational(abs_offset),
                    "duration": to_dur(clip_dur),
                    "start": "0/1s",
                })
                # Fix 5: Animated Ken Burns with keyframed scale transform
                zoom_target = clip.get("zoom_target", "wide")
                xform = SubElement(el, "adjust-transform")

                # Anchor point based on zoom target
                if zoom_target == "face":
                    anchor = "0 -200"  # upper third
                elif zoom_target == "document":
                    anchor = "-200 0"  # left side
                else:
                    anchor = "0 0"     # center (wide)

                # Position param (static)
                SubElement(xform, "param", name="position", value="0 0")
                SubElement(xform, "param", name="anchor", value=anchor)

                # Scale param with keyframes for animated zoom
                scale_param = SubElement(xform, "param", name="scale")
                SubElement(scale_param, "keyframe", time="0/1s", value="1.0 1.0")
                if zoom_target in ("face", "document"):
                    SubElement(scale_param, "keyframe", time=to_dur(clip_dur), value="1.05 1.05")
                else:
                    SubElement(scale_param, "keyframe", time=to_dur(clip_dur), value="1.03 1.03")
            else:
                el = SubElement(spine, "clip", {
                    "name": clip["name"],
                    "offset": to_rational(abs_offset),
                    "duration": to_dur(clip_dur),
                    "start": to_rational(clip["start"]),
                    "tcFormat": "NDF",
                })

                # Video reference
                SubElement(el, "video", {
                    "ref": asset_id,
                    "offset": "0/1s",
                    "duration": to_rational(get_duration(path) or clip_dur),
                    "start": "0/1s",
                })

                # Clip audio handling
                ca = clip["clip_audio"]
                if ca == "mute":
                    # Fix 1: -96dB = true silence (0dB was unity gain)
                    SubElement(el, "adjust-volume", amount="-96dB")
                elif ca == "play":
                    pass  # full volume
                elif ca == "play_then_mute":
                    # Fix 2: Volume keyframes — play at 0dB then ramp to silence
                    cad = clip.get("clip_audio_duration") or 3
                    vol = SubElement(el, "adjust-volume")
                    param = SubElement(vol, "param", name="amount")
                    SubElement(param, "keyframe", time="0/1s", value="0dB")
                    SubElement(param, "keyframe", time=to_rational(cad), value="0dB")
                    SubElement(param, "keyframe", time=to_rational(cad + 0.5), value="-96dB")
                    SubElement(param, "keyframe", time=to_dur(clip_dur), value="-96dB")

            prev_clip = clip
            cursor += clip_dur

        # ── Trailing gap (extends timeline to cover full narration) ──
        trailing_dur = max(total_dur - cursor, 5.0)
        gap_offset = TC_START + cursor
        trailing_gap = SubElement(spine, "gap", {
            "name": "Gap",
            "offset": to_rational(gap_offset),
            "duration": to_dur(trailing_dur),
            "start": to_rational(gap_offset),
        })

        # ── Attach lane clips to their PARENT spine clips ──
        # DaVinci requires lane clips to be children of the spine clip that
        # covers their timeline position. Attaching everything to the first
        # element causes DaVinci to ignore audio lanes entirely.
        #
        # For each lane clip, find the spine clip whose offset range contains
        # the lane clip's start time, then attach as a child with relative offset.

        # Build index of spine clips with their timeline ranges
        spine_elements = list(spine)
        spine_ranges = []  # [(element, start_sec, end_sec, content_start_sec)]
        for el in spine_elements:
            offset_str = el.get("offset", "0/1s")
            dur_str = el.get("duration", "0/1s")
            start_str = el.get("start", "0/1s")

            offset_sec = float(Fraction(offset_str.rstrip('s')))
            dur_sec = float(Fraction(dur_str.rstrip('s')))
            content_start = float(Fraction(start_str.rstrip('s')))

            spine_ranges.append((el, offset_sec, offset_sec + dur_sec, content_start))

        def find_parent_spine(timeline_sec, skip_transitions=False):
            """Find the spine element that covers this timeline position."""
            for el, start, end, cs in spine_ranges:
                if skip_transitions and el.tag == "transition":
                    continue
                if start <= timeline_sec < end:
                    return el, start, cs
            # Fallback: first non-transition spine element
            for el, start, _, cs in spine_ranges:
                if el.tag != "transition":
                    return el, start, cs
            if spine_ranges:
                el, start, _, cs = spine_ranges[0]
                return el, start, cs
            return None, 0, 0

        attached = 0
        for lc in lane_clips:
            abspath = os.path.abspath(lc["path"])
            asset_id, _ = self._assets.get(abspath, (None, None))
            if not asset_id:
                continue

            # Find which spine clip covers this lane clip's start
            # Audio lane clips must skip transitions (DaVinci ignores audio on transitions)
            lc_timeline_sec = TC_START + lc["offset"]
            parent_el, parent_offset, parent_content_start = find_parent_spine(
                lc_timeline_sec, skip_transitions=lc["is_audio"]
            )
            if parent_el is None:
                continue

            # Lane clip offset is relative to the parent's content timebase
            # offset_in_parent = parent_content_start + (lane_timeline_pos - parent_offset)
            rel_offset = parent_content_start + (lc_timeline_sec - parent_offset)

            attrs = {
                "ref": asset_id,
                "name": lc["name"],
                "lane": str(lc["lane"]),
                "offset": to_rational(rel_offset),
                "duration": to_dur(lc["duration"]),
                "start": to_rational(lc["start"]),
            }

            if lc["is_audio"]:
                # Assign distinct roles so DaVinci creates separate audio tracks
                if lc["lane"] == LANE_NARRATION:
                    attrs["role"] = "dialogue"
                elif lc["lane"] == LANE_MUSIC:
                    attrs["role"] = "music"
                else:
                    attrs["role"] = "effects"
                SubElement(parent_el, "asset-clip", attrs)
            else:
                vid = SubElement(parent_el, "video", attrs)
                if lc["lane"] == LANE_OVERLAY:
                    SubElement(vid, "adjust-transform", {
                        "position": "0 0",
                        "scale": "1 1",
                        "anchor": "0 0",
                    })
            attached += 1

        print(f"  Attached {attached} lane clips to first spine element")

        # Pretty print
        indent(root, space="  ")

        return ElementTree(root)


# ─── Paper Edit Support ──────────────────────────────────────────────────────

# LearnByLeo pacing rules by narrative function
PACING_RULES = {
    "exposition":     {"cut_dur": 10.0, "zoom_rate": 2.0},
    "tension_build":  {"cut_dur": 3.0,  "zoom_rate": 4.0},
    "evidence":       {"cut_dur": 6.0,  "zoom_rate": 3.0},
    "character_intro": {"cut_dur": 6.0, "zoom_rate": 3.5},
    "hook":           {"cut_dur": 15.0, "zoom_rate": 4.0},
    "revelation":     {"cut_dur": 2.5,  "zoom_rate": 20.0},
    "transition":     {"cut_dur": 3.0,  "zoom_rate": 0.5},
}


def compute_ken_burns_from_tension(tension, narrative_function):
    """Compute Ken Burns zoom scale from tension + narrative function.

    Returns (start_scale, end_scale) for keyframes.
    """
    rules = PACING_RULES.get(narrative_function, PACING_RULES["exposition"])
    base_rate = rules["zoom_rate"]
    # Tension modulates: 0.0 = base rate, 1.0 = 2x base rate
    rate = base_rate * (1.0 + tension * 0.5)
    # Convert %/s rate to scale over a typical 6s beat
    duration = 6.0
    end_scale = 1.0 + (rate / 100) * duration
    return 1.0, round(end_scale, 4)


def load_paper_edit(path):
    """Load an approved paper edit and convert to builder-compatible segments.

    Returns (segments, chapter_map, sfx_by_chapter, music_by_chapter) in the
    same format as load_director() output, so the existing build() method works.
    """
    with open(path) as f:
        paper_edit = json.load(f)

    beats = paper_edit.get("beats", [])

    # Drop phantom beats past narration end
    narr_dur = get_duration(str(NARRATION_PATH))
    if narr_dur:
        before = len(beats)
        beats = [b for b in beats if b.get("start_sec", 0) < narr_dur or b.get("is_chapter_marker")]
        dropped = before - len(beats)
        if dropped:
            print(f"  Dropped {dropped} phantom beats past narration end ({narr_dur:.1f}s)")

    segments = []
    current_chapter_num = 0
    chapter_names = {}

    for beat in beats:
        chapter = beat.get("chapter", "COLD OPEN")
        if chapter not in chapter_names:
            chapter_names[chapter] = len(chapter_names)

        ch_num = chapter_names[chapter]

        # Convert paper edit beat to builder segment format
        visual = beat.get("visual_file", "")
        clip_audio = beat.get("clip_audio", "mute")

        # Force mute on still images — they have no audio track
        if clip_audio != "mute" and is_image(visual):
            clip_audio = "mute"

        seg = {
            "text": beat.get("text", ""),
            "_narr_start": beat.get("start_sec", 0),
            "_narr_end": beat.get("end_sec", 0),
            "visual_file": visual,
            "visual_type": beat.get("visual_type", "still_image"),
            "clip_audio": clip_audio,
            "clip_audio_duration": beat.get("clip_audio_duration"),
            "clip_start_sec": beat.get("clip_in_point", 0),
            "transition_in": beat.get("transition_in", "cut"),
            "text_overlay": beat.get("text_overlay"),
            "tension_level": beat.get("tension_level", 0.5),
            "arc_position": beat.get("narrative_function", "exposition"),
            "music_state": beat.get("music_state", "ducking"),
            "chapter_card": chapter if beat.get("is_chapter_marker") else None,
            "beats": None,  # paper edit beats are already flat
            "_chapter_num": ch_num,
        }

        # Compute zoom from tension + narrative function
        nf = beat.get("narrative_function", "exposition")
        tension = beat.get("tension_level", 0.5)
        zoom_speed = beat.get("zoom_speed_pct_per_sec")
        if zoom_speed:
            duration = seg["_narr_end"] - seg["_narr_start"]
            seg["zoom_target"] = beat.get("zoom_target", "wide")
            seg["_zoom_end_scale"] = 1.0 + (zoom_speed / 100) * max(duration, 1)
        else:
            _, end_scale = compute_ken_burns_from_tension(tension, nf)
            seg["zoom_target"] = beat.get("zoom_target", "wide")
            seg["_zoom_end_scale"] = end_scale

        # SFX
        sfx_file = beat.get("sfx")
        if sfx_file:
            seg["sfx"] = {"file": sfx_file, "motivation": beat.get("sfx_motivation", "")}
            seg["sfx_file"] = sfx_file

        segments.append(seg)

    # Build chapter_map
    chapter_map = defaultdict(list)
    for seg in segments:
        chapter_map[seg["_chapter_num"]].append(seg)

    # SFX per chapter
    sfx_by_chapter = {}
    for ch_num, ch_segs in chapter_map.items():
        sfx_list = []
        for seg in ch_segs:
            if seg.get("sfx_file"):
                sfx_list.append((seg["_narr_start"], seg["sfx_file"]))
        sfx_by_chapter[ch_num] = sfx_list

    # Music per chapter (use defaults)
    music_by_chapter = {}
    for ch_num, ch_segs in chapter_map.items():
        ch_start = ch_segs[0]["_narr_start"]
        ch_end = ch_segs[-1]["_narr_end"]
        if ch_num < len(CHAPTERS):
            music_file = CHAPTERS[ch_num].get("music", "track_01_tense_ducked.wav")
        else:
            music_file = "track_01_tense_ducked.wav"
        music_by_chapter[ch_num] = (music_file, ch_start, ch_end)

    return segments, dict(chapter_map), sfx_by_chapter, music_by_chapter


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FCPXML Builder v2")
    parser.add_argument("--output", default="timeline_v2.fcpxml", help="Output FCPXML file")
    parser.add_argument("--import-resolve", action="store_true", help="Import into DaVinci after building")
    parser.add_argument("--paper-edit", default=None, help="Path to approved paper edit JSON (new workflow)")
    args = parser.parse_args()

    print("=" * 60)
    print("  FCPXML Builder v2")
    print("=" * 60)

    if args.paper_edit:
        # NEW WORKFLOW: Load from approved paper edit
        print(f"\nLoading paper edit: {args.paper_edit}")
        all_segments, chapter_map, sfx_by_chapter, music_by_chapter = load_paper_edit(args.paper_edit)
        print(f"  {len(all_segments)} beats across {len(chapter_map)} chapters")
        for ch_num, segs in sorted(chapter_map.items()):
            print(f"  Ch{ch_num}: {len(segs)} beats, "
                  f"{segs[0]['_narr_start']:.1f}-{segs[-1]['_narr_end']:.1f}s")
        align = None
    else:
        # LEGACY WORKFLOW: Load from director JSON
        print("\nLoading director v4...")
        _, raw_segs = load_director()

        print("Loading narration alignment (150 WPM)...")
        align = load_alignment()
        print(f"  {len(align['sentences'])} sentences, {align['duration_sec']:.1f}s")

        print("Matching segments to narration...")
        matched = match_segments_to_narration(raw_segs, align)

        print("Splitting into chapters...")
        chapter_map = split_into_chapters(matched)
        for ch_num, segs in sorted(chapter_map.items()):
            print(f"  Ch{ch_num} {CHAPTERS[ch_num]['name']}: {len(segs)} segs, "
                  f"{segs[0]['_narr_start']:.1f}-{segs[-1]['_narr_end']:.1f}s")

        # Flatten all segments (in order)
        all_segments = []
        for ch_num in sorted(chapter_map.keys()):
            all_segments.extend(chapter_map[ch_num])

        # SFX per chapter
        sfx_by_chapter = {}
        for ch_num, segs in chapter_map.items():
            sfx_by_chapter[ch_num] = pick_chapter_sfx(segs)

        # Music per chapter
        music_by_chapter = {}
        for ch_num, segs in chapter_map.items():
            ch_start = segs[0]["_narr_start"]
            ch_end = segs[-1]["_narr_end"]
            music_file = CHAPTERS[ch_num]["music"]
            music_by_chapter[ch_num] = (music_file, ch_start, ch_end)

    # Build
    print(f"\nBuilding FCPXML...")
    builder = FCPXMLBuilderV2()
    tree = builder.build(
        segments=all_segments,
        chapter_map=chapter_map,
        narration_path=NARRATION_PATH,
        sfx_by_chapter=sfx_by_chapter,
        music_by_chapter=music_by_chapter,
        alignment=align,
    )

    # Write
    output_path = str(PROJECT_ROOT / args.output)
    tree.write(output_path, encoding="unicode", xml_declaration=True)
    size = os.path.getsize(output_path)
    print(f"\n  Written: {output_path} ({size / 1024:.0f} KB)")

    # Import into DaVinci
    if args.import_resolve:
        print("\nImporting into DaVinci Resolve...")
        resolve_modules = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
        sys.path.append(resolve_modules)
        try:
            import DaVinciResolveScript as dvr
            resolve = dvr.scriptapp("Resolve")
            if resolve:
                proj = resolve.GetProjectManager().GetCurrentProject()
                mp = proj.GetMediaPool()
                result = mp.ImportTimelineFromFile(output_path, {"timelineName": "Breaking Law FINAL"})
                if result:
                    print(f"  Imported as '{result.GetName()}'")
                    proj.SetCurrentTimeline(result)
                    resolve.OpenPage("edit")
                else:
                    print("  ImportTimelineFromFile returned None")
                    print("  -> Try File > Import > Timeline manually")
            else:
                print("  Cannot connect to DaVinci")
        except Exception as e:
            print(f"  Import error: {e}")
            print("  -> Try File > Import > Timeline manually")

    print("\nDone!")


if __name__ == "__main__":
    main()
