#!/usr/bin/env python3
"""
FCPXML 1.9 Timeline Builder for YouTube Documentary Pipeline

Generates an FCPXML file from director v3 JSON output that can be imported
into DaVinci Resolve with ALL clips at their correct timeline positions.

WHY THIS EXISTS:
  DaVinci Resolve's external scripting API (dvr.scriptapp("Resolve")) has a
  fundamental bug: AppendToTimeline() ignores the recordFrame parameter and
  places ALL clips sequentially at the END of each track. This makes it
  impossible to position overlays, SFX, chapter cards, or any non-V1 element
  at its correct timeline position via the API.

  FCPXML import is the ONLY reliable way to place clips at exact positions.
  DaVinci parses the offset/duration/start attributes faithfully.

FCPXML STRUCTURE (DaVinci-compatible):
  - <spine> contains V1 clips sequentially (primary storyline)
  - Higher video tracks use lane="N" (positive integers) on clips attached
    to the FIRST spine element (or a gap appended to the spine)
  - Audio tracks use positive lane numbers on clips attached to spine/gap
  - Each clip: offset = timeline position, duration = how long, start = source in-point
  - All times expressed as rational numbers (e.g., "3600/1s" = 3600 seconds)

TRACK LAYOUT:
  V1 (spine):  Main footage (video clips + images, ≤7s each)
  V2 (lane 1): Text overlays at narration-synced positions
  V3 (lane 2): Chapter cards at transition points
  A1 (lane 5): Narration WAV (full duration)
  A2 (lane 6): Music WAV (ducked, full duration)
  A3 (lane 7): SFX track 1 (odd-indexed SFX)
  A4 (lane 8): SFX track 2 (even-indexed SFX)

Usage:
  python -m pipeline_v2.fcpxml_builder \\
      --director storyboards/directed_v3.json \\
      --narration audio/narration.wav \\
      --music audio/music_ducked.wav \\
      --sfx-dir assets/sfx/ \\
      --output timeline_import.fcpxml

  # Then import into DaVinci:
  python -m pipeline_v2.fcpxml_builder \\
      --director storyboards/directed_v3.json \\
      --narration audio/narration.wav \\
      --output timeline_import.fcpxml \\
      --import-resolve
"""

import argparse
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

PROJECT_ROOT = Path(__file__).parent.parent

# Timeline constants
FPS = 24
FRAME_DUR = Fraction(1, FPS)
WIDTH = 1920
HEIGHT = 1080
TC_START_SEC = 3600  # 01:00:00:00 — DaVinci default
MAX_CLIP_SEC = 7.0   # Fair use limit
STILL_DEFAULT_SEC = 5.0  # Default duration for still images

# Lane assignments for multi-track layout
# Positive lanes = above the spine in DaVinci
LANE_V2_OVERLAY = 1
LANE_V3_CHAPTER = 2
LANE_A1_NARRATION = 5
LANE_A2_MUSIC = 6
LANE_A3_SFX = 7
LANE_A4_SFX2 = 8


# ─── Rational time helpers ───────────────────────────────────────────────────

def sec_to_rational(seconds: float) -> str:
    """Convert seconds to FCPXML rational time string (e.g., '3607/1s').

    Uses frame-accurate rounding: snap to nearest frame boundary at 24fps,
    then express as a fraction with denominator = FPS to avoid rounding errors.
    """
    if seconds is None or seconds < 0:
        return "0/1s"
    frames = round(seconds * FPS)
    # Express as frames/FPS to maintain frame accuracy
    frac = Fraction(frames, FPS)
    return f"{frac.numerator}/{frac.denominator}s"


def dur_to_rational(seconds: float) -> str:
    """Convert duration in seconds to rational string. Minimum 1 frame."""
    if seconds is None or seconds <= 0:
        seconds = FRAME_DUR
    return sec_to_rational(seconds)


# ─── Media file discovery ────────────────────────────────────────────────────

def find_media_file(filename: str, search_dirs: list) -> str | None:
    """Search for a media file across multiple directories."""
    if not filename:
        return None

    # Check if it's already an absolute path
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename

    for search_dir in search_dirs:
        # Direct match
        direct = os.path.join(search_dir, filename)
        if os.path.exists(direct):
            return direct

        # Walk subdirectories
        for dirpath, _, filenames in os.walk(search_dir):
            if filename in filenames:
                return os.path.join(dirpath, filename)

    return None


def get_media_duration(filepath: str) -> float | None:
    """Get duration of a media file using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_format', '-show_streams', filepath],
            capture_output=True, text=True, timeout=10
        )
        info = json.loads(result.stdout)
        # Try format duration first
        if 'format' in info and 'duration' in info['format']:
            return float(info['format']['duration'])
        # Fall back to first stream
        for stream in info.get('streams', []):
            if 'duration' in stream:
                return float(stream['duration'])
    except Exception:
        pass
    return None


def is_image_file(filepath: str) -> bool:
    """Check if file is a still image (not video)."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp')


def is_video_file(filepath: str) -> bool:
    """Check if file is a video."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ('.mp4', '.mov', '.avi', '.mkv', '.mxf', '.m4v', '.webm')


def is_audio_file(filepath: str) -> bool:
    """Check if file is audio."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ('.wav', '.mp3', '.aac', '.flac', '.m4a', '.ogg')


# ─── Director JSON loader ────────────────────────────────────────────────────

def load_director_output(path: str) -> tuple[dict, list[dict]]:
    """Load director v3 JSON and flatten scenes into segments."""
    with open(path) as f:
        data = json.load(f)

    version = data.get("schema_version", "1.0")
    print(f"  Director schema: v{version}")

    segments = []
    if "scenes" in data:
        for scene in data["scenes"]:
            segments.extend(scene.get("segments", []))
    else:
        segments = data.get("segments", [])

    return data, segments


# ─── FCPXML builder ──────────────────────────────────────────────────────────

class FCPXMLBuilder:
    """Builds an FCPXML 1.9 document from director v3 output.

    The key insight: in FCPXML, the <spine> is the primary storyline (V1).
    All other tracks are expressed as "attached clips" using the lane attribute
    on clips nested inside spine elements or inside a trailing <gap>.

    DaVinci maps positive lanes to higher video tracks (lane 1 = V2, lane 2 = V3)
    and to audio tracks (lane 5+ = A1, A2, ...).

    For clips that don't overlap any spine clip (e.g., SFX that plays during
    a spine gap), we attach them to a gap element appended at the end of the spine.
    """

    def __init__(self, fps=FPS, width=WIDTH, height=HEIGHT, tc_start=TC_START_SEC):
        self.fps = fps
        self.width = width
        self.height = height
        self.tc_start = tc_start  # seconds
        self.frame_dur = Fraction(1, fps)

        # Resource tracking
        self._next_resource_id = 0
        self._assets = {}          # filepath -> resource_id
        self._asset_elements = []  # list of (resource_id, Element)
        self._format_id = None     # main timeline format

        # Track items: list of (lane, offset_sec, duration_sec, asset_ref, start_sec, name, is_audio, clip_audio_rule)
        self._v1_clips = []
        self._lane_clips = []  # non-V1 clips with lane assignments

    def _next_id(self) -> str:
        rid = f"r{self._next_resource_id}"
        self._next_resource_id += 1
        return rid

    def _register_format(self) -> str:
        """Register the main timeline format and return its resource ID."""
        if self._format_id:
            return self._format_id
        self._format_id = self._next_id()
        return self._format_id

    def _register_asset(self, filepath: str, name: str = None) -> str:
        """Register a media file as an FCPXML asset. Returns resource ID.

        Each unique filepath gets a UNIQUE resource ID. FCPXML requires
        separate <asset> entries even for the same file used multiple times
        in the same timeline — each usage needs its own ID.
        """
        # For simplicity, we deduplicate by filepath. DaVinci handles
        # multiple references to the same asset ID fine.
        if filepath in self._assets:
            return self._assets[filepath]

        rid = self._next_id()
        self._assets[filepath] = rid

        if name is None:
            name = os.path.basename(filepath)

        # Build the asset element
        asset_attrs = {
            "id": rid,
            "name": name,
            "start": "0/1s",
        }

        abs_filepath = os.path.abspath(filepath)
        file_url = "file://" + abs_filepath.replace(" ", "%20")

        if is_image_file(filepath):
            # Still image — no duration, no audio
            asset_attrs["duration"] = "0/1s"
            asset_attrs["hasVideo"] = "1"
            # Need a format for this image — use a generic one
            fmt_id = self._next_id()
            asset_attrs["format"] = fmt_id
            # We'll store this format
            self._asset_elements.append(("format", {
                "id": fmt_id,
                "name": "FFVideoFormatRateUndefined",
                "width": str(self.width),
                "height": str(self.height),
            }))
        elif is_video_file(filepath):
            dur = get_media_duration(filepath)
            asset_attrs["hasVideo"] = "1"
            asset_attrs["hasAudio"] = "1"
            asset_attrs["audioSources"] = "1"
            asset_attrs["audioChannels"] = "2"
            if dur:
                asset_attrs["duration"] = sec_to_rational(dur)
            else:
                asset_attrs["duration"] = "0/1s"
            # Use a format matching the source — for simplicity use a generic video format
            fmt_id = self._next_id()
            asset_attrs["format"] = fmt_id
            self._asset_elements.append(("format", {
                "id": fmt_id,
                "name": "FFVideoFormatRateUndefined",
                "width": str(self.width),
                "height": str(self.height),
            }))
        elif is_audio_file(filepath):
            dur = get_media_duration(filepath)
            asset_attrs["hasAudio"] = "1"
            asset_attrs["audioSources"] = "1"
            asset_attrs["audioChannels"] = "1"  # mono default
            if dur:
                asset_attrs["duration"] = sec_to_rational(dur)
            else:
                asset_attrs["duration"] = "0/1s"
        else:
            # Unknown type — treat as video
            asset_attrs["hasVideo"] = "1"
            asset_attrs["duration"] = "0/1s"
            fmt_id = self._next_id()
            asset_attrs["format"] = fmt_id
            self._asset_elements.append(("format", {
                "id": fmt_id,
                "name": "FFVideoFormatRateUndefined",
                "width": str(self.width),
                "height": str(self.height),
            }))

        self._asset_elements.append(("asset", asset_attrs, file_url))
        return rid

    def add_v1_clip(self, filepath: str, offset_sec: float, duration_sec: float,
                    start_sec: float = 0, name: str = None,
                    clip_audio: str = "mute"):
        """Add a clip to V1 (primary spine).

        Args:
            filepath: Path to media file.
            offset_sec: Timeline position in seconds (relative to timeline start, NOT tc_start).
            duration_sec: How long this clip appears on the timeline.
            start_sec: Source in-point (where to start playing the source file).
            name: Display name (defaults to filename).
            clip_audio: "mute", "play", or "play_then_mute".
        """
        ref = self._register_asset(filepath)
        if name is None:
            name = os.path.basename(filepath)
        self._v1_clips.append({
            "ref": ref,
            "filepath": filepath,
            "offset_sec": offset_sec,
            "duration_sec": duration_sec,
            "start_sec": start_sec,
            "name": name,
            "clip_audio": clip_audio,
        })

    def add_overlay(self, filepath: str, offset_sec: float, duration_sec: float,
                    lane: int = LANE_V2_OVERLAY, start_sec: float = 0,
                    name: str = None):
        """Add a video overlay to a higher track (V2, V3, etc.)."""
        ref = self._register_asset(filepath)
        if name is None:
            name = os.path.basename(filepath)
        self._lane_clips.append({
            "ref": ref,
            "filepath": filepath,
            "offset_sec": offset_sec,
            "duration_sec": duration_sec,
            "start_sec": start_sec,
            "name": name,
            "lane": lane,
            "is_audio": False,
        })

    def add_audio(self, filepath: str, offset_sec: float, duration_sec: float = None,
                  lane: int = LANE_A1_NARRATION, start_sec: float = 0,
                  name: str = None):
        """Add an audio clip to an audio track."""
        ref = self._register_asset(filepath)
        if name is None:
            name = os.path.basename(filepath)
        if duration_sec is None:
            duration_sec = get_media_duration(filepath) or 0
        self._lane_clips.append({
            "ref": ref,
            "filepath": filepath,
            "offset_sec": offset_sec,
            "duration_sec": duration_sec,
            "start_sec": start_sec,
            "name": name,
            "lane": lane,
            "is_audio": True,
        })

    def build(self) -> ElementTree:
        """Build the complete FCPXML ElementTree."""
        fmt_id = self._register_format()

        # Root
        root = Element("fcpxml", version="1.9")

        # ── Resources ──
        resources = SubElement(root, "resources")

        # Main timeline format
        SubElement(resources, "format", {
            "id": fmt_id,
            "name": f"FFVideoFormat{self.height}p{self.fps}",
            "frameDuration": f"1/{self.fps}s",
            "width": str(self.width),
            "height": str(self.height),
        })

        # All registered formats and assets
        for item in self._asset_elements:
            if item[0] == "format":
                SubElement(resources, "format", item[1])
            elif item[0] == "asset":
                attrs = item[1]
                file_url = item[2]
                asset_el = SubElement(resources, "asset", attrs)
                SubElement(asset_el, "media-rep", {
                    "kind": "original-media",
                    "src": file_url,
                })

        # ── Library / Event / Project / Sequence ──
        library = SubElement(root, "library")
        event = SubElement(library, "event", name="Production")
        project = SubElement(event, "project", name="Production")

        # Sort V1 clips by offset
        self._v1_clips.sort(key=lambda c: c["offset_sec"])

        # Calculate total timeline duration
        total_dur = 0
        if self._v1_clips:
            last = self._v1_clips[-1]
            total_dur = last["offset_sec"] + last["duration_sec"]

        # Include narration in duration calculation (narration is the source of truth)
        narr_dur = 0
        for lc in self._lane_clips:
            if lc.get("lane") == LANE_A1_NARRATION:
                narr_dur = lc["offset_sec"] + lc["duration_sec"]
                break

        # Cap total duration to narration length (prevents runaway from bad offsets)
        if narr_dur > 0:
            total_dur = max(total_dur, narr_dur)
            # Clamp lane clips that extend past narration
            for lc in self._lane_clips:
                if lc["offset_sec"] > narr_dur:
                    lc["offset_sec"] = min(lc["offset_sec"], narr_dur - lc["duration_sec"])
        else:
            for lc in self._lane_clips:
                end = lc["offset_sec"] + lc["duration_sec"]
                if end > total_dur:
                    total_dur = end

        # Add a small buffer
        total_dur += 5.0

        sequence = SubElement(project, "sequence", {
            "format": fmt_id,
            "duration": sec_to_rational(total_dur),
            "tcStart": sec_to_rational(self.tc_start),
            "tcFormat": "NDF",
        })

        spine = SubElement(sequence, "spine")

        # ── Build V1 spine ──
        # The spine is a flat sequence of clips. Between clips, we insert
        # <gap> elements for any dead time. All non-V1 elements are attached
        # to spine clips or gaps via the lane attribute.

        # Build spine elements (clips + gaps)
        # Use frame-accurate Fraction math throughout to avoid float rounding
        # that causes 1-frame overlaps (DaVinci "Trimming item" warnings).
        spine_elements = []  # list of (element, tl_start_sec, tl_end_sec, src_start_sec)
        cursor_frames = 0  # current position in frames (integer, no rounding errors)

        for clip in self._v1_clips:
            clip_start_frames = round(clip["offset_sec"] * FPS)
            clip_dur_frames = max(round(clip["duration_sec"] * FPS), 1)

            # Insert gap if there's dead space before this clip
            if clip_start_frames > cursor_frames:
                gap_dur_frames = clip_start_frames - cursor_frames
                gap_start_sec = cursor_frames / FPS
                gap_end_sec = clip_start_frames / FPS
                spine_elements.append(("gap", gap_start_sec, gap_end_sec,
                                       gap_dur_frames / FPS, None))
                cursor_frames = clip_start_frames
            elif clip_start_frames < cursor_frames:
                # Clip overlaps previous — advance start to cursor to prevent overlap
                clip_dur_frames -= (cursor_frames - clip_start_frames)
                clip_start_frames = cursor_frames
                if clip_dur_frames <= 0:
                    continue

            clip_start_sec = cursor_frames / FPS
            clip_end_frames = cursor_frames + clip_dur_frames
            clip_end_sec = clip_end_frames / FPS

            spine_elements.append(("clip", clip_start_sec, clip_end_sec,
                                   clip_dur_frames / FPS, clip))
            cursor_frames = clip_end_frames

        cursor = cursor_frames / FPS  # convert back for trailing gap

        # Always append a trailing gap — ALL non-narration lane clips attach here
        # (matches DaVinci's own export format). Duration must be non-zero.
        trailing_dur = max(total_dur - cursor, 1.0)
        spine_elements.append(("gap", cursor, cursor + trailing_dur, trailing_dur, None))

        # ── Render spine elements into XML ──
        spine_xml_elements = []  # parallel list of (xml_element, tl_start, tl_end, src_start_sec)

        for elem_type, tl_start, tl_end, dur, clip_data in spine_elements:
            abs_offset = self.tc_start + tl_start  # absolute timeline position
            src_start = 0.0  # source start for this spine element

            if elem_type == "gap":
                src_start = self.tc_start  # gaps use tc_start as their start
                el = SubElement(spine, "gap", {
                    "name": "Gap",
                    "offset": sec_to_rational(abs_offset),
                    "duration": dur_to_rational(dur),
                    "start": sec_to_rational(self.tc_start),
                })
            elif elem_type == "clip":
                filepath = clip_data["filepath"]

                if is_image_file(filepath):
                    src_start = 0.0
                    # Still image: use <video> element directly
                    el = SubElement(spine, "video", {
                        "ref": clip_data["ref"],
                        "name": clip_data["name"],
                        "offset": sec_to_rational(abs_offset),
                        "duration": dur_to_rational(dur),
                        "start": "0/1s",
                        "enabled": "1",
                    })
                    SubElement(el, "adjust-transform", {
                        "scale": "1 1",
                        "position": "0 0",
                        "anchor": "0 0",
                    })
                elif is_video_file(filepath):
                    # Video clip with optional source in-point
                    src_start = clip_data.get("start_sec", 0) or 0

                    el = SubElement(spine, "clip", {
                        "name": clip_data["name"],
                        "offset": sec_to_rational(abs_offset),
                        "duration": dur_to_rational(dur),
                        "start": sec_to_rational(src_start),
                        "tcFormat": "NDF",
                        "enabled": "1",
                        "format": self._get_asset_format(clip_data["ref"]),
                    })
                    SubElement(el, "adjust-transform", {
                        "scale": "1 1",
                        "position": "0 0",
                        "anchor": "0 0",
                    })

                    # Embed video reference for the source media
                    source_dur = get_media_duration(filepath)
                    SubElement(el, "video", {
                        "ref": clip_data["ref"],
                        "offset": "0/1s",
                        "duration": sec_to_rational(source_dur) if source_dur else dur_to_rational(dur),
                        "start": "0/1s",
                    })

                    # Mute clip audio if requested
                    if clip_data.get("clip_audio") == "mute":
                        # Muting is done by not including audio-role or by
                        # setting volume to 0 — FCPXML uses adjust-volume
                        SubElement(el, "adjust-volume", amount="0dB")
                else:
                    src_start = 0.0
                    # Fallback: treat as generic asset-clip
                    el = SubElement(spine, "asset-clip", {
                        "ref": clip_data["ref"],
                        "name": clip_data["name"],
                        "offset": sec_to_rational(abs_offset),
                        "duration": dur_to_rational(dur),
                        "start": "0/1s",
                        "enabled": "1",
                    })

            spine_xml_elements.append((el, tl_start, tl_end, src_start))

        # ── Attach lane clips to spine elements ──
        # DaVinci export format: narration on FIRST spine clip, everything
        # else on the TRAILING GAP.
        #
        # FCPXML lane clip positioning:
        #   timeline_pos = parent.offset + (lane.offset - parent.start)
        #
        # For trailing gap:  gap.offset = tc_start + cursor
        #                     gap.start  = tc_start
        # Solving for lane.offset to place clip at tc_start + lc_offset:
        #   lane.offset = tc_start + lc_offset - cursor

        trailing_gap_el = spine_xml_elements[-1][0] if spine_xml_elements else None
        # cursor = content-relative position where trailing gap starts
        # (= total V1 clip duration, captured from spine building above)
        trailing_gap_cursor = spine_xml_elements[-1][1] if spine_xml_elements else 0.0

        for lc in self._lane_clips:
            lc_offset = lc["offset_sec"]
            lc_dur = lc["duration_sec"]

            if lc.get("lane") == LANE_A1_NARRATION and spine_xml_elements:
                # Narration: attach to FIRST spine clip (matches DaVinci export)
                parent_el = spine_xml_elements[0][0]
                clip_offset = sec_to_rational(spine_xml_elements[0][3])  # parent's src_start
            else:
                # Everything else: trailing gap
                parent_el = trailing_gap_el
                if parent_el is None:
                    print(f"  WARNING: No spine element for lane clip at {lc_offset:.1f}s: {lc['name']}")
                    continue
                # Offset in gap's local time so clip appears at correct
                # timeline position: tc_start + lc_offset - cursor
                clip_offset = sec_to_rational(self.tc_start + lc_offset - trailing_gap_cursor)

            lane_attrs = {
                "ref": lc["ref"],
                "name": lc["name"],
                "lane": str(lc["lane"]),
                "offset": clip_offset,
                "duration": dur_to_rational(lc_dur),
                "start": sec_to_rational(lc.get("start_sec", 0) or 0),
                "enabled": "1",
            }

            if lc["is_audio"]:
                # Audio lane clip
                SubElement(parent_el, "asset-clip", lane_attrs)
            else:
                filepath = lc["filepath"]
                if is_image_file(filepath):
                    SubElement(parent_el, "video", lane_attrs)
                elif is_video_file(filepath):
                    fmt = self._get_asset_format(lc["ref"])
                    lane_attrs["format"] = fmt
                    lane_attrs["tcFormat"] = "NDF"
                    clip_el = SubElement(parent_el, "clip", lane_attrs)
                    SubElement(clip_el, "adjust-transform", {
                        "scale": "1 1",
                        "position": "0 0",
                        "anchor": "0 0",
                    })
                    source_dur = get_media_duration(filepath)
                    SubElement(clip_el, "video", {
                        "ref": lc["ref"],
                        "offset": "0/1s",
                        "duration": sec_to_rational(source_dur) if source_dur else dur_to_rational(lc_dur),
                        "start": "0/1s",
                    })
                else:
                    SubElement(parent_el, "asset-clip", lane_attrs)

        # Pretty print
        indent(root, space="    ")

        tree = ElementTree(root)
        return tree

    def _get_asset_format(self, ref_id: str) -> str:
        """Look up the format ID for a given asset reference."""
        for item in self._asset_elements:
            if item[0] == "asset" and item[1].get("id") == ref_id:
                return item[1].get("format", self._format_id)
        return self._format_id

    def write(self, output_path: str):
        """Build and write the FCPXML to disk."""
        tree = self.build()

        # Write with XML declaration and DOCTYPE
        with open(output_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE fcpxml>\n')
            tree.write(f, encoding="unicode", xml_declaration=False)

        print(f"  FCPXML written: {output_path}")
        file_size = os.path.getsize(output_path)
        print(f"  File size: {file_size:,} bytes")


# ─── Director → FCPXML pipeline ──────────────────────────────────────────────

def build_from_director(director_path: str, narration_path: str = None,
                        music_path: str = None, sfx_dir: str = None,
                        output_path: str = "timeline_import.fcpxml",
                        search_dirs: list = None,
                        fps: int = FPS, width: int = WIDTH, height: int = HEIGHT):
    """Build a complete FCPXML from director v3 JSON.

    Reads the director output, resolves all media file paths, and builds
    the FCPXML with every clip at its correct timeline position.

    Args:
        director_path: Path to director v3 JSON.
        narration_path: Path to narration WAV (placed on A1).
        music_path: Path to music WAV (placed on A2).
        sfx_dir: Directory containing SFX files.
        output_path: Where to write the FCPXML.
        search_dirs: Additional directories to search for media files.
        fps: Timeline frames per second (default: 24).
        width: Timeline width in pixels (default: 1920).
        height: Timeline height in pixels (default: 1080).
    """
    print(f"\n{'='*60}")
    print(f"FCPXML Timeline Builder")
    print(f"{'='*60}")

    # Load director output
    print(f"\n  Loading director: {director_path}")
    data, segments = load_director_output(director_path)
    print(f"  {len(segments)} segments, {data.get('scene_count', '?')} scenes")

    # Set up media search directories
    if search_dirs is None:
        search_dirs = []

    default_search = [
        str(PROJECT_ROOT / "footage"),
        str(PROJECT_ROOT / "images"),
        os.path.expanduser("~/Desktop/SecretScores_Media"),
        os.path.expanduser("~/Desktop/SecretScores_Media/assets"),
        os.path.expanduser("~/Desktop/SecretScores_Media/typewriter"),
        os.path.expanduser("~/Desktop/SecretScores_Media/chapter_cards"),
    ]

    # Add the director file's parent directory too
    director_dir = os.path.dirname(os.path.abspath(director_path))
    all_search_dirs = search_dirs + default_search + [director_dir]
    # Filter to existing directories
    all_search_dirs = [d for d in all_search_dirs if os.path.isdir(d)]

    if sfx_dir:
        all_search_dirs.insert(0, sfx_dir)

    builder = FCPXMLBuilder(fps=fps, width=width, height=height)

    # ── V1: Main footage from director segments ──
    print(f"\n  V1: Processing {len(segments)} segments...")
    v1_count = 0
    v1_skipped = 0
    source_usage = {}  # track fair use compliance

    for seg in segments:
        vf = seg.get("visual_file")
        if not vf:
            v1_skipped += 1
            continue

        filepath = find_media_file(vf, all_search_dirs)
        if not filepath:
            print(f"    WARN: File not found: {vf}")
            v1_skipped += 1
            continue

        tl_start = seg.get("_timeline_start_sec", 0) or 0
        tl_end = seg.get("_timeline_end_sec")

        if tl_end is not None and tl_end > tl_start:
            seg_dur = tl_end - tl_start
        else:
            # Estimate from word count at ~150 WPM = 2.5 words/sec
            wc = seg.get("word_count", len(seg.get("text", "").split()))
            seg_dur = max(wc / 2.5, 2.0)

        # Fair use: cap at MAX_CLIP_SEC per individual clip
        clip_dur = min(seg_dur, MAX_CLIP_SEC)

        # If segment is longer than one clip, split into multiple clips
        # to maintain fair use compliance
        clip_start = seg.get("clip_start_sec") or 0
        clip_audio = seg.get("clip_audio", "mute")
        remaining = seg_dur
        pos = tl_start

        while remaining > 0:
            dur = min(remaining, MAX_CLIP_SEC)

            # Track source usage for diversity check
            source_usage[vf] = source_usage.get(vf, 0) + dur

            builder.add_v1_clip(
                filepath=filepath,
                offset_sec=pos,
                duration_sec=dur,
                start_sec=clip_start,
                name=vf,
                clip_audio=clip_audio,
            )
            v1_count += 1
            pos += dur
            clip_start += dur
            remaining -= dur
            # After first sub-clip, always mute audio
            clip_audio = "mute"

    print(f"  V1: {v1_count} clips placed, {v1_skipped} skipped")

    # Source diversity check
    over_limit = {k: v for k, v in source_usage.items() if v > 30}
    if over_limit:
        print(f"  WARNING: {len(over_limit)} sources exceed 30s total usage:")
        for name, dur in sorted(over_limit.items(), key=lambda x: -x[1]):
            print(f"    {name}: {dur:.1f}s")

    # ── V2: Text overlays ──
    overlay_count = 0
    for seg in segments:
        text_overlay = seg.get("text_overlay")
        text_style = seg.get("text_style")

        if not text_overlay:
            continue

        tl_start = seg.get("_timeline_start_sec", 0) or 0

        # Look for pre-rendered overlay files (case-insensitive fuzzy match)
        overlay_filename = None
        import re as _re
        safe_key = _re.sub(r'[^a-zA-Z0-9]', '_', text_overlay[:30]).strip('_').lower()
        # Search all overlay dirs for any file containing our safe key
        for search_dir in all_search_dirs:
            if not os.path.isdir(search_dir):
                continue
            for fname in os.listdir(search_dir):
                if safe_key[:15] in fname.lower() and fname.endswith('.mov'):
                    overlay_filename = os.path.join(search_dir, fname)
                    break
            if overlay_filename:
                break

        if overlay_filename:
            # Determine overlay duration
            if is_video_file(overlay_filename):
                ov_dur = get_media_duration(overlay_filename) or 3.0
            else:
                ov_dur = 3.0  # default for images

            lane = LANE_V3_CHAPTER if text_style == "typewriter" else LANE_V2_OVERLAY
            builder.add_overlay(
                filepath=overlay_filename,
                offset_sec=tl_start,
                duration_sec=ov_dur,
                lane=LANE_V2_OVERLAY,
                name=f"overlay_{text_overlay[:20]}",
            )
            overlay_count += 1

    print(f"  V2: {overlay_count} text overlays")

    # ── V3: Chapter cards ──
    chapter_count = 0
    for seg in segments:
        card_title = seg.get("chapter_card")
        if not card_title:
            continue

        tl_start = seg.get("_timeline_start_sec", 0) or 0

        # Look for pre-rendered chapter card
        safe_title = card_title.lower().replace(" ", "_").replace(":", "")
        candidates = [
            f"chapter_{safe_title}_2s.mov",
            f"chapter_{safe_title}.mov",
            f"chapter_{safe_title}_2s.mp4",
            f"chapter_{safe_title}.mp4",
        ]

        card_path = None
        for candidate in candidates:
            fp = find_media_file(candidate, all_search_dirs)
            if fp:
                card_path = fp
                break

        if card_path:
            card_dur = get_media_duration(card_path) or 2.0
            builder.add_overlay(
                filepath=card_path,
                offset_sec=max(0, tl_start - 0.5),  # slight lead-in
                duration_sec=card_dur,
                lane=LANE_V3_CHAPTER,
                name=f"chapter_{card_title}",
            )
            chapter_count += 1
        else:
            print(f"    WARN: Chapter card not found for '{card_title}'")

    print(f"  V3: {chapter_count} chapter cards")

    # ── A1: Narration ──
    if narration_path and os.path.exists(narration_path):
        narr_dur = get_media_duration(narration_path)
        builder.add_audio(
            filepath=narration_path,
            offset_sec=0,
            duration_sec=narr_dur,
            lane=LANE_A1_NARRATION,
            name="narration",
        )
        print(f"  A1: Narration ({narr_dur:.1f}s)")
    else:
        print(f"  A1: No narration file")
        narr_dur = None

    # ── A2: Music ──
    if music_path and os.path.exists(music_path):
        music_dur = get_media_duration(music_path)
        builder.add_audio(
            filepath=music_path,
            offset_sec=0,
            duration_sec=music_dur,
            lane=LANE_A2_MUSIC,
            name="music_ducked",
        )
        print(f"  A2: Music ({music_dur:.1f}s)")
    else:
        print(f"  A2: No music file")

    # ── A3/A4: SFX ──
    sfx_count = 0
    sfx_missing = 0
    sfx_list = []

    for seg in segments:
        sfx = seg.get("sfx")
        if not sfx or not sfx.get("file"):
            continue

        sfx_file = sfx["file"]
        tl_start = seg.get("_timeline_start_sec", 0) or 0

        # Find SFX file
        sfx_path = None
        if sfx_dir:
            direct = os.path.join(sfx_dir, sfx_file)
            if os.path.exists(direct):
                sfx_path = direct

        if not sfx_path:
            sfx_path = find_media_file(sfx_file, all_search_dirs)

        if not sfx_path:
            # Try with _loud suffix (normalized versions)
            base, ext = os.path.splitext(sfx_file)
            loud_name = f"{base}_loud{ext}"
            sfx_path = find_media_file(loud_name, all_search_dirs)

        if sfx_path:
            sfx_list.append((tl_start, sfx_path, sfx_file))
        else:
            sfx_missing += 1
            print(f"    WARN: SFX not found: {sfx_file}")

    # Sort by position and alternate between A3/A4
    sfx_list.sort(key=lambda x: x[0])

    for idx, (pos, sfx_path, sfx_name) in enumerate(sfx_list):
        sfx_dur = get_media_duration(sfx_path) or 1.0
        lane = LANE_A3_SFX if idx % 2 == 0 else LANE_A4_SFX2

        builder.add_audio(
            filepath=sfx_path,
            offset_sec=pos,
            duration_sec=sfx_dur,
            lane=lane,
            name=sfx_name,
        )
        sfx_count += 1

    print(f"  A3/A4: {sfx_count} SFX placed, {sfx_missing} missing")

    # ── Write FCPXML ──
    print(f"\n  Building FCPXML...")
    builder.write(output_path)

    # ── Summary ──
    print(f"\n  SUMMARY:")
    print(f"    V1 clips: {v1_count}")
    print(f"    V2 overlays: {overlay_count}")
    print(f"    V3 chapters: {chapter_count}")
    if narr_dur:
        print(f"    A1 narration: {narr_dur:.1f}s")
    print(f"    A3/A4 SFX: {sfx_count}")
    print(f"    Unique sources: {len(source_usage)}")
    print(f"    Output: {output_path}")

    return output_path


def import_into_resolve(fcpxml_path: str, timeline_name: str = None):
    """Import the FCPXML into DaVinci Resolve via scripting API.

    IMPORTANT: Must pass timelineName in the options dict — without it,
    ImportTimelineFromFile returns None for FCPXML files.
    """
    print(f"\n  Importing FCPXML into DaVinci Resolve...")

    resolve_modules = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
    if resolve_modules not in sys.path:
        sys.path.append(resolve_modules)

    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        if not resolve:
            print("  ERROR: Cannot connect to DaVinci Resolve. Is it running?")
            return False

        project = resolve.GetProjectManager().GetCurrentProject()
        mp = project.GetMediaPool()

        abs_path = os.path.abspath(fcpxml_path)
        name = timeline_name or os.path.splitext(os.path.basename(fcpxml_path))[0]

        # Delete existing timeline with same name (re-import scenario)
        for i in range(project.GetTimelineCount(), 0, -1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == name:
                print(f"  Deleting existing timeline: {name}")
                mp.DeleteTimelines([tl])

        # MUST pass timelineName — without it, API returns None for FCPXML
        result = mp.ImportTimelineFromFile(abs_path, {"timelineName": name})

        if result:
            print(f"  Imported timeline: {result.GetName()}")
            project.SetCurrentTimeline(result)

            # Verify
            clip_count = 0
            for track_type in ('video', 'audio'):
                for t in range(1, result.GetTrackCount(track_type) + 1):
                    clips = result.GetItemListInTrack(track_type, t) or []
                    tname = result.GetTrackName(track_type, t)
                    if clips:
                        print(f"    {'V' if track_type == 'video' else 'A'}{t} ({tname}): {len(clips)} clips")
                        clip_count += len(clips)

            print(f"  Total clips: {clip_count}")
            return True
        else:
            print("  ERROR: ImportTimelineFromFile returned None")
            print("  (Even with timelineName option — check if DaVinci is on Edit page)")
            return False

    except ImportError:
        print("  ERROR: DaVinci Resolve scripting module not found.")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def import_via_applescript(fcpxml_path: str, timeline_name: str = None) -> bool:
    """Import FCPXML into DaVinci Resolve via AppleScript through Terminal.

    The DaVinci API's ImportTimelineFromFile returns None for FCPXML files.
    This function uses AppleScript to drive the UI: File > Import > Timeline,
    navigate to the file via Cmd+Shift+G, and confirm the import dialog.
    Must run through Terminal.app (which has accessibility permissions).
    """
    import time

    abs_path = os.path.abspath(fcpxml_path)
    if not os.path.exists(abs_path):
        print(f"  ERROR: FCPXML not found: {abs_path}")
        return False

    # Get pre-import timeline count
    resolve_modules = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
    if resolve_modules not in sys.path:
        sys.path.append(resolve_modules)
    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        project = resolve.GetProjectManager().GetCurrentProject()
        pre_count = project.GetTimelineCount()
    except Exception:
        pre_count = 0

    # Build AppleScript
    script = f'''
    -- Put file path on clipboard for Cmd+Shift+G paste
    do shell script "echo -n '{abs_path}' | pbcopy"

    tell application "DaVinci Resolve" to activate
    delay 1

    -- Dismiss any stale dialogs
    tell application "System Events"
        key code 53
        delay 0.3
    end tell

    -- File > Import > Timeline...
    tell application "System Events"
        tell process "DaVinci Resolve"
            click menu item "Timeline\\u2026" of menu 1 of menu item "Import" of menu "File" of menu bar 1
        end tell
    end tell
    delay 4

    -- Navigate to file via Cmd+Shift+G
    tell application "System Events"
        keystroke "g" using {{shift down, command down}}
        delay 2
        keystroke "a" using {{command down}}
        delay 0.3
        keystroke "v" using {{command down}}
        delay 1
        keystroke return
        delay 3
        keystroke return
    end tell
    delay 5

    -- Handle the Import settings dialog (set timeline name, click Ok)
    tell application "System Events"
        tell process "DaVinci Resolve"
            try
                set importWin to window "Import a Timeline From File"
                set value of text field 2 of importWin to "{timeline_name or 'Breaking Law FINAL'}"
                delay 0.5
                click button "Ok" of importWin
            end try
        end tell
    end tell
    delay 8

    -- Handle missing clips dialog (click No)
    tell application "System Events"
        tell process "DaVinci Resolve"
            repeat 3 times
                try
                    click button "No" of window "Message"
                    delay 2
                end try
            end repeat
            -- Close Log if open
            try
                click button "Close" of window "Log"
            end try
        end tell
    end tell
    '''

    # Write and run through Terminal
    script_path = "/tmp/davinci_fcpxml_import.scpt"
    with open(script_path, "w") as f:
        f.write(script)

    print(f"  Running AppleScript import via Terminal...")
    result = subprocess.run(
        ["osascript", "-e",
         f'tell application "Terminal" to do script "osascript {script_path} 2>&1"'],
        capture_output=True, text=True, timeout=10
    )

    # Wait for import to complete
    print(f"  Waiting for DaVinci import (up to 60s)...")
    for i in range(12):
        time.sleep(5)
        try:
            resolve = dvr.scriptapp("Resolve")
            project = resolve.GetProjectManager().GetCurrentProject()
            post_count = project.GetTimelineCount()
            if post_count > pre_count:
                # Find and switch to the new timeline
                for idx in range(1, post_count + 1):
                    tl = project.GetTimelineByIndex(idx)
                    if tl.GetName() not in [project.GetTimelineByIndex(j).GetName()
                                            for j in range(1, pre_count + 1)]:
                        project.SetCurrentTimeline(tl)
                        print(f"  Imported timeline: {tl.GetName()}")
                        clip_count = 0
                        for tt in ('video', 'audio'):
                            for t in range(1, tl.GetTrackCount(tt) + 1):
                                clips = tl.GetItemListInTrack(tt, t) or []
                                if clips:
                                    prefix = 'V' if tt == 'video' else 'A'
                                    print(f"    {prefix}{t}: {len(clips)} clips")
                                    clip_count += len(clips)
                        print(f"  Total clips: {clip_count}")
                        return True
        except Exception:
            pass

    print(f"  WARNING: Timeline count unchanged after 60s")
    return False


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build FCPXML 1.9 timeline from director v3 output for DaVinci Resolve import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate FCPXML only:
  python -m pipeline_v2.fcpxml_builder \\
      --director storyboards/directed_v3.json \\
      --narration audio/narration.wav \\
      --output timeline_import.fcpxml

  # Generate and import into DaVinci:
  python -m pipeline_v2.fcpxml_builder \\
      --director storyboards/directed_v3.json \\
      --narration audio/narration.wav \\
      --music audio/music_ducked.wav \\
      --sfx-dir assets/sfx/ \\
      --output timeline_import.fcpxml \\
      --import-resolve

  # With extra search directories:
  python -m pipeline_v2.fcpxml_builder \\
      --director storyboards/directed_v3.json \\
      --narration audio/narration.wav \\
      --search-dir footage/my_video/clips/ \\
      --search-dir footage/my_video/images/ \\
      --output timeline_import.fcpxml
""")
    parser.add_argument('--director', required=True,
                        help='Director output JSON (v3 schema with scenes/segments)')
    parser.add_argument('--narration',
                        help='Narration WAV path (placed on A1)')
    parser.add_argument('--music',
                        help='Music WAV path (placed on A2, should be pre-ducked)')
    parser.add_argument('--sfx-dir', default='',
                        help='Directory containing SFX WAV files')
    parser.add_argument('--output', default='timeline_import.fcpxml',
                        help='Output FCPXML path (default: timeline_import.fcpxml)')
    parser.add_argument('--search-dir', action='append', default=[],
                        help='Additional directories to search for media files (can repeat)')
    parser.add_argument('--import-resolve', action='store_true',
                        help='Import the FCPXML into DaVinci Resolve after writing')
    parser.add_argument('--fps', type=int, default=FPS,
                        help=f'Timeline FPS (default: {FPS})')
    parser.add_argument('--width', type=int, default=WIDTH,
                        help=f'Timeline width (default: {WIDTH})')
    parser.add_argument('--height', type=int, default=HEIGHT,
                        help=f'Timeline height (default: {HEIGHT})')

    args = parser.parse_args()

    # Pass custom dimensions to build_from_director via a patched builder
    # (The module-level constants are defaults; the builder takes them as init args)
    output = build_from_director(
        director_path=args.director,
        narration_path=args.narration,
        music_path=args.music,
        sfx_dir=args.sfx_dir,
        output_path=args.output,
        search_dirs=args.search_dir,
        fps=args.fps,
        width=args.width,
        height=args.height,
    )

    if args.import_resolve:
        tl_name = os.path.splitext(os.path.basename(output))[0].replace("_", " ").title()
        success = import_into_resolve(output, timeline_name=tl_name)
        if not success:
            print("  API import failed — trying AppleScript UI import...")
            success = import_via_applescript(output, timeline_name=tl_name)
            if not success:
                print("  ERROR: Both API and AppleScript import failed.")
                return 1

    print(f"\n  Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
