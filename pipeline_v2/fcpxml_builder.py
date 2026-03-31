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

        file_url = "file://" + filepath.replace(" ", "%20")

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
        spine_elements = []  # list of (element, tl_start_sec, tl_end_sec)
        cursor = 0.0  # current position in timeline-relative seconds

        for clip in self._v1_clips:
            clip_start = clip["offset_sec"]
            clip_dur = clip["duration_sec"]
            clip_end = clip_start + clip_dur

            # Insert gap if there's dead space before this clip
            if clip_start > cursor + 0.001:
                gap_dur = clip_start - cursor
                spine_elements.append(("gap", cursor, clip_start, gap_dur, None))
                cursor = clip_start

            spine_elements.append(("clip", clip_start, clip_end, clip_dur, clip))
            cursor = clip_end

        # Append a trailing gap to anchor any lane clips that extend beyond V1
        if total_dur > cursor:
            trailing_dur = total_dur - cursor
            spine_elements.append(("gap", cursor, total_dur, trailing_dur, None))

        # ── Render spine elements into XML ──
        spine_xml_elements = []  # parallel list of XML elements

        for elem_type, tl_start, tl_end, dur, clip_data in spine_elements:
            abs_offset = self.tc_start + tl_start  # absolute timeline position

            if elem_type == "gap":
                el = SubElement(spine, "gap", {
                    "name": "Gap",
                    "offset": sec_to_rational(abs_offset),
                    "duration": dur_to_rational(dur),
                    "start": sec_to_rational(self.tc_start),
                })
            elif elem_type == "clip":
                filepath = clip_data["filepath"]

                if is_image_file(filepath):
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
                    # Fallback: treat as generic asset-clip
                    el = SubElement(spine, "asset-clip", {
                        "ref": clip_data["ref"],
                        "name": clip_data["name"],
                        "offset": sec_to_rational(abs_offset),
                        "duration": dur_to_rational(dur),
                        "start": "0/1s",
                        "enabled": "1",
                    })

            spine_xml_elements.append((el, tl_start, tl_end))

        # ── Attach lane clips to spine elements ──
        # For each lane clip, find the spine element that contains its offset
        # time and attach it as a child element with the lane attribute.
        # If no spine element covers the time, attach to the trailing gap.

        for lc in self._lane_clips:
            lc_offset = lc["offset_sec"]
            lc_dur = lc["duration_sec"]
            lc_abs_offset = self.tc_start + lc_offset

            # Audio clips placement strategy:
            # - Narration (lane 5): attach to FIRST spine element so it starts
            #   at the same time as V1 clips
            # - SFX (lanes 7,8): attach to trailing gap (DaVinci groups them)
            # Video lane clips: attach to the overlapping spine element.
            parent_el = None
            if lc["is_audio"]:
                if lc.get("lane") == LANE_A1_NARRATION and spine_xml_elements:
                    parent_el = spine_xml_elements[0][0]  # first clip
                elif spine_xml_elements:
                    parent_el = spine_xml_elements[-1][0]  # trailing gap
            else:
                for xml_el, tl_start, tl_end in spine_xml_elements:
                    if tl_start <= lc_offset < tl_end:
                        parent_el = xml_el
                        break

            # Fallback: attach to last spine element (trailing gap)
            if parent_el is None and spine_xml_elements:
                parent_el = spine_xml_elements[-1][0]

            if parent_el is None:
                print(f"  WARNING: No spine element for lane clip at {lc_offset:.1f}s: {lc['name']}")
                continue

            # Build the lane clip element
            # Narration (lane 5) attached to first clip: use offset=0 so it
            # starts at the same time as V1. Other lane clips use absolute offsets.
            if lc.get("lane") == LANE_A1_NARRATION:
                clip_offset = "0/1s"
            else:
                clip_offset = sec_to_rational(lc_abs_offset)

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


def import_into_resolve(fcpxml_path: str):
    """Import the FCPXML into DaVinci Resolve via scripting API."""
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
        result = mp.ImportTimelineFromFile(abs_path)

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
            return False

    except ImportError:
        print("  ERROR: DaVinci Resolve scripting module not found.")
        print("  Install DaVinci Resolve or check RESOLVE_MODULES path.")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
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
        success = import_into_resolve(output)
        if not success:
            return 1

    print(f"\n  Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
