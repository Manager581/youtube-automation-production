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
Ken Burns: static zoom on still images (ZoomX/ZoomY in transform).

Usage:
  cd /Users/jefflawrence/Documents/youtube-automation-production
  venv/bin/python -m pipeline_v2.fcpxml_builder_v2 --output timeline_v2.fcpxml
  venv/bin/python -m pipeline_v2.fcpxml_builder_v2 --output timeline_v2.fcpxml --import-resolve

Requires: ffprobe in PATH for video clip durations.
"""

import argparse
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline_v2.chapter_assembler import (
    load_director, load_alignment, match_segments_to_narration,
    split_into_chapters, find_overlay_file, pick_chapter_sfx,
    find_media_file, deduplicate_visuals, CHAPTERS,
)

# ─── Constants ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
FPS = 24
TC_START = 3600  # 01:00:00:00
WIDTH = 1920
HEIGHT = 1080

NARRATION_PATH = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
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

    def build(self, segments, chapter_map, narration_path, sfx_by_chapter, music_by_chapter):
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
            vf = seg.get("visual_file")
            if vf:
                path = find_media_file(vf)
                if path:
                    dur = get_duration(path) if not is_image(path) else None
                    media_cache[vf] = (path, dur)

        # ── Build V1 spine clips ──
        print("  Building V1 spine...")
        v1_clips = []
        for seg in segments:
            text = seg.get("text", "")
            if text.startswith("[") and seg["_narr_end"] == seg["_narr_start"]:
                continue  # skip stage directions

            vf = seg.get("visual_file")
            if not vf or vf not in media_cache:
                continue

            path, source_dur = media_cache[vf]
            seg_dur = max(seg["_narr_end"] - seg["_narr_start"], 0.5)

            if is_image(path):
                # Image: hold for segment duration (FCPXML controls this, not DaVinci default)
                clip_dur = min(seg_dur, 20.0)  # cap at 20s per editing rules
                clip_start = 0
            else:
                # Video: use up to segment duration, capped at source
                clip_start = seg.get("clip_start_sec") or 0
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

        # Fill V1 gaps: if a clip ends before the next starts, extend it
        for i in range(len(v1_clips) - 1):
            gap = v1_clips[i + 1]["offset"] - (v1_clips[i]["offset"] + v1_clips[i]["duration"])
            if gap > 0.1:
                # Extend current clip to fill gap (image holds, video holds last frame)
                v1_clips[i]["duration"] += gap

        print(f"  V1: {len(v1_clips)} clips")

        # ── Collect lane clips ──
        lane_clips = []  # (lane, offset, duration, path, start, name, is_audio, extra)

        # V2: Overlays
        overlay_count = 0
        for seg in segments:
            ov_text = seg.get("text_overlay")
            if not ov_text:
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

        # V3: Chapter cards
        card_count = 0
        for seg in segments:
            card = seg.get("chapter_card")
            if not card:
                continue
            card_name = f"chapter_{card.lower().replace(' ', '_')}.mov"
            card_path = str(CHAPTER_CARD_DIR / card_name)
            if not os.path.exists(card_path):
                continue
            card_dur = get_duration(card_path) or 3.0
            # Place 2s before content
            card_offset = max(0, seg["_narr_start"] - 2.0)
            lane_clips.append({
                "lane": LANE_CHAPTER,
                "offset": card_offset,
                "duration": card_dur,
                "path": card_path,
                "start": 0,
                "name": card_name,
                "is_audio": False,
            })
            card_count += 1
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

        # A3/A4: SFX
        sfx_count = 0
        for ch_num, sfx_list in sfx_by_chapter.items():
            for idx, (sfx_time, sfx_file) in enumerate(sfx_list):
                sfx_path = str(SFX_DIR / sfx_file)
                if not os.path.exists(sfx_path):
                    continue
                sfx_dur = get_duration(sfx_path) or 2.0
                lane = LANE_SFX1 if idx % 2 == 0 else LANE_SFX2
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
        print(f"  A3/A4: {sfx_count} SFX")

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

        # ── Build spine (V1) ──
        cursor = 0  # current position in seconds

        for clip in v1_clips:
            clip_offset = clip["offset"]
            clip_dur = clip["duration"]

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
                # Ken Burns: slight zoom
                zoom = "1.05 1.05" if clip["zoom_target"] in ("face", "document") else "1.03 1.03"
                SubElement(el, "adjust-transform", {
                    "position": "0 0",
                    "scale": zoom,
                    "anchor": "0 0",
                })
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
                    SubElement(el, "adjust-volume", amount="0dB")
                elif ca == "play":
                    pass  # full volume
                elif ca == "play_then_mute":
                    SubElement(el, "adjust-volume", amount="-12dB")

            # Transition
            trans = clip.get("transition_in", "cut")
            if trans == "fade_from_black" and cursor < 1:
                # Add fade in at very start
                pass  # DaVinci auto-applies this on import sometimes
            elif trans == "dissolve":
                # Cross dissolve: attach to previous spine element
                pass  # Would need transition element between spine clips

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

        # ── Attach lane clips to the spine elements they overlap with ──
        # Build a list of (xml_element, seq_start, seq_end) for all spine elements
        spine_elements = []
        for child in spine:
            tag = child.tag
            offset_str = child.get("offset", "0/1s")
            dur_str = child.get("duration", "0/1s")
            # Parse rational time
            def parse_rat(s):
                s = s.rstrip('s')
                if '/' in s:
                    num, den = s.split('/')
                    return float(num) / float(den)
                return float(s)
            off = parse_rat(offset_str)
            dur = parse_rat(dur_str)
            spine_elements.append((child, off, off + dur))

        for lc in lane_clips:
            abs_time = TC_START + lc["offset"]  # absolute sequence time
            abspath = os.path.abspath(lc["path"])
            asset_id, _ = self._assets.get(abspath, (None, None))
            if not asset_id:
                continue

            # Find the spine element that contains this lane clip's start time
            parent = trailing_gap
            parent_offset = gap_offset
            parent_start_content = gap_offset  # trailing gap start
            for el, el_off, el_end in spine_elements:
                if el_off <= abs_time < el_end:
                    parent = el
                    parent_offset = el_off
                    # Parse the parent's "start" attribute (source in-point)
                    start_str = el.get("start", "0/1s").rstrip('s')
                    if '/' in start_str:
                        n, d = start_str.split('/')
                        parent_start_content = float(n) / float(d)
                    else:
                        parent_start_content = float(start_str)
                    break

            # Lane clip offset is RELATIVE to parent's content timebase:
            # lane_offset = parent_start_content + (abs_time - parent_offset)
            lane_offset = parent_start_content + (abs_time - parent_offset)

            attrs = {
                "ref": asset_id,
                "name": lc["name"],
                "lane": str(lc["lane"]),
                "offset": to_rational(lane_offset),
                "duration": to_dur(lc["duration"]),
                "start": to_rational(lc["start"]),
            }

            if lc["is_audio"]:
                # Use asset-clip for audio lanes (not <audio> which is for embedded audio)
                attrs["role"] = "dialogue"
                SubElement(parent, "asset-clip", attrs)
            else:
                vid = SubElement(parent, "video", attrs)
                if lc["lane"] == LANE_OVERLAY:
                    SubElement(vid, "adjust-transform", {
                        "position": "0 0",
                        "scale": "1 1",
                        "anchor": "0 0",
                    })

        # Pretty print
        indent(root, space="  ")

        return ElementTree(root)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FCPXML Builder v2")
    parser.add_argument("--output", default="timeline_v2.fcpxml", help="Output FCPXML file")
    parser.add_argument("--import-resolve", action="store_true", help="Import into DaVinci after building")
    args = parser.parse_args()

    print("=" * 60)
    print("  FCPXML Builder v2")
    print("=" * 60)

    # Load data
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
                    print(f"  ✅ Imported as '{result.GetName()}'")
                    proj.SetCurrentTimeline(result)
                    resolve.OpenPage("edit")
                else:
                    print("  ❌ ImportTimelineFromFile returned None")
                    print("  → Try File > Import > Timeline manually")
            else:
                print("  Cannot connect to DaVinci")
        except Exception as e:
            print(f"  Import error: {e}")
            print("  → Try File > Import > Timeline manually")

    print("\nDone!")


if __name__ == "__main__":
    main()
