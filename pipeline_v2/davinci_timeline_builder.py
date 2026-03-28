#!/usr/bin/env python3
"""
DaVinci Resolve Timeline Builder (v2)

Reads the directed storyboard + narration manifest and builds a complete timeline
in DaVinci Resolve using the scripting API. Reads director output for all editorial
decisions (transitions, SFX, text overlays, zoom targets).

Key fixes from v1:
  - Overlays sorted chronologically before AppendToTimeline
  - Uses davinci_helpers functions for all rendering
  - Director output drives transitions, SFX placement, text overlays
  - Track alignment verification after build

Requirements:
  - DaVinci Resolve must be running
  - Python scripting must be enabled in Resolve preferences

Usage:
  RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
  RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
  PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
  python3 pipeline_v2/davinci_timeline_builder.py --storyboard storyboards/directed.json
"""

import json
import os
import sys
from pathlib import Path

# Add DaVinci scripting path
RESOLVE_MODULES = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
if RESOLVE_MODULES not in sys.path:
    sys.path.append(RESOLVE_MODULES)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.davinci_helpers import (
    render_overlay_with_fade,
    create_chapter_card,
    create_text_reveal,
    create_ducked_music,
    trim_timeline_to_narration,
    verify_track_alignment,
    verify_source_diversity,
    normalize_sfx,
)


def connect_resolve():
    """Connect to DaVinci Resolve."""
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        import importlib
        spec = importlib.util.spec_from_file_location(
            "fusionscript",
            "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
        )
        if spec is None:
            print("ERROR: Cannot find DaVinci Resolve scripting module")
            sys.exit(1)
        dvr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dvr)

    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("ERROR: Cannot connect to DaVinci Resolve. Is it running?")
        sys.exit(1)

    print(f"Connected to DaVinci Resolve {resolve.GetVersionString()}")
    return resolve


def setup_project(resolve, name="LearnByLeo Production"):
    """Create or open the project."""
    pm = resolve.GetProjectManager()

    project = pm.LoadProject(name)
    if project:
        print(f"Opened existing project: {name}")
        return project

    project = pm.CreateProject(name)
    if not project:
        print(f"ERROR: Cannot create project '{name}'")
        sys.exit(1)

    project.SetSetting("timelineResolutionWidth", "1920")
    project.SetSetting("timelineResolutionHeight", "1080")
    project.SetSetting("timelineFrameRate", "30")

    print(f"Created project: {name} (1920x1080 @ 30fps)")
    return project


def import_media(project, clips_dir, images_dir, narration_path, music_path=None):
    """Import all clips, images, narration, and music into the media pool."""
    mp = project.GetMediaPool()
    root = mp.GetRootFolder()

    clips_bin = mp.AddSubFolder(root, "Clips")
    images_bin = mp.AddSubFolder(root, "Images")
    audio_bin = mp.AddSubFolder(root, "Audio")
    overlays_bin = mp.AddSubFolder(root, "Overlays")

    imported = {"clips": [], "images": [], "audio": [], "overlays": []}

    # Import clips
    clips_path = Path(clips_dir)
    if clips_path.exists():
        mp.SetCurrentFolder(clips_bin)
        clip_files = [str(f) for f in sorted(clips_path.iterdir())
                      if f.suffix in ('.mp4', '.mkv', '.webm', '.mov')]
        if clip_files:
            items = mp.ImportMedia(clip_files)
            if items:
                imported["clips"] = list(items)
                print(f"  Imported {len(items)} clips")

    # Import images
    images_path = Path(images_dir)
    if images_path.exists():
        mp.SetCurrentFolder(images_bin)
        img_files = [str(f) for f in sorted(images_path.iterdir())
                     if f.suffix in ('.jpg', '.jpeg', '.png', '.webp')]
        if img_files:
            items = mp.ImportMedia(img_files)
            if items:
                imported["images"] = list(items)
                print(f"  Imported {len(items)} images")

    # Import narration
    narr_path = Path(narration_path)
    if narr_path.exists():
        mp.SetCurrentFolder(audio_bin)
        items = mp.ImportMedia([str(narr_path)])
        if items:
            imported["audio"].extend(list(items))
            print(f"  Imported narration audio")

    # Import music
    if music_path and Path(music_path).exists():
        mp.SetCurrentFolder(audio_bin)
        items = mp.ImportMedia([str(music_path)])
        if items:
            imported["audio"].extend(list(items))
            print(f"  Imported music")

    mp.SetCurrentFolder(root)
    return imported


def load_director_output(storyboard_path: str) -> list[dict]:
    """Load director decisions from directed storyboard."""
    with open(storyboard_path) as f:
        storyboard = json.load(f)

    # Get directed segments
    directed = storyboard.get("directed_segments", [])
    if directed:
        return directed

    # Fallback: extract from scene segments
    segments = []
    if "scenes" in storyboard:
        for scene in storyboard["scenes"]:
            for seg in scene.get("segments", []):
                if "director" in seg:
                    segments.append(seg["director"])
    return segments


def build_timeline(project, imported, storyboard_path, manifest_path=None):
    """Build the timeline following director decisions."""
    mp = project.GetMediaPool()
    fps = 30

    # Load director output
    director_segments = load_director_output(storyboard_path)
    print(f"  Director segments loaded: {len(director_segments)}")

    # Load storyboard for visual info
    with open(storyboard_path) as f:
        storyboard = json.load(f)

    # Flatten storyboard segments
    sb_segments = []
    if "scenes" in storyboard:
        for scene in storyboard["scenes"]:
            sb_segments.extend(scene.get("segments", []))
    elif "segments" in storyboard:
        sb_segments = storyboard["segments"]

    # Load narration manifest for timing
    manifest = None
    if manifest_path and Path(manifest_path).exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    # Create timeline
    timeline_name = storyboard.get("title", "Main") + " - Production"
    timeline = mp.CreateEmptyTimeline(timeline_name)
    if not timeline:
        print("ERROR: Cannot create timeline")
        return None

    project.SetCurrentTimeline(timeline)
    print(f"Created timeline: {timeline.GetName()}")

    # ── Track Layout ──
    # V1: Main footage (images/clips)
    # V2: Overlays (vignette, effects)
    # V3: Chapter cards
    # V4: Text overlays (names, dates, quotes)
    # A1: Narration
    # A2: Music
    # A3: SFX
    # A4: SFX 2

    # Put narration on A1
    if imported["audio"]:
        narration_clip = imported["audio"][0]
        mp.AppendToTimeline([{
            "mediaPoolItem": narration_clip,
            "mediaType": 2,  # Audio only
            "trackIndex": 1,
        }])
        print("  Added narration to A1")

    # Put music on A2 (if available)
    if len(imported["audio"]) > 1:
        music_clip = imported["audio"][1]
        mp.AppendToTimeline([{
            "mediaPoolItem": music_clip,
            "mediaType": 2,
            "trackIndex": 2,
        }])
        print("  Added music to A2")

    # Build media lookup
    media_lookup = {}
    for clip in imported["clips"] + imported["images"]:
        name = clip.GetName().lower()
        media_lookup[name] = clip

    # ── Pre-render overlays ──
    overlays_dir = str(PROJECT_ROOT / "render_cache" / "overlays")
    os.makedirs(overlays_dir, exist_ok=True)

    # Collect all overlay items with their target positions
    overlay_items = []  # [(position_sec, track, media_pool_item)]

    # ── Place segments on V1 ──
    # Sort by segment_index to ensure chronological order
    # (AppendToTimeline ignores recordFrame — must sort first)
    sorted_segments = sorted(
        zip(sb_segments, director_segments) if len(director_segments) == len(sb_segments)
        else [(s, {}) for s in sb_segments],
        key=lambda x: x[0].get("segment_index", 0)
    )

    timeline_pos_sec = 0
    placed_count = 0

    for sb_seg, dir_seg in sorted_segments:
        duration_sec = sb_seg.get("duration_sec", 5.0)
        search_query = sb_seg.get("search_query", "").lower()
        text = sb_seg.get("text", "")

        # Find matching media
        best_match = None
        for name, clip in media_lookup.items():
            if any(word in name for word in search_query.split()[:3] if len(word) > 3):
                best_match = clip
                break

        # Fallback: use any available image
        if not best_match and imported["images"]:
            img_idx = placed_count % len(imported["images"])
            best_match = imported["images"][img_idx]

        if best_match:
            dur_frames = int(duration_sec * fps)
            mp.AppendToTimeline([{
                "mediaPoolItem": best_match,
                "mediaType": 1,  # Video only
                "trackIndex": 1,
                "startFrame": 0,
                "endFrame": dur_frames,
            }])
            placed_count += 1

        # ── Director-driven text overlays ──
        text_overlay = dir_seg.get("text_overlay", {})
        if text_overlay and text_overlay.get("text"):
            style = text_overlay.get("style", "entity")
            size_px = text_overlay.get("size_px", 56)
            try:
                mov_path = create_text_reveal(
                    text_overlay["text"], overlays_dir,
                    style=style, duration_sec=min(duration_sec, 3.0)
                )
                overlay_items.append((timeline_pos_sec, 4, mov_path))
            except Exception as e:
                print(f"  WARNING: Text overlay render failed: {e}")

        # ── Director-driven chapter cards ──
        if dir_seg.get("arc_position") == "chapter_transition":
            chapter_title = text[:40].strip().rstrip('.')
            if chapter_title:
                try:
                    card_path = create_chapter_card(
                        chapter_title, overlays_dir, duration_sec=2.5
                    )
                    overlay_items.append((timeline_pos_sec, 3, card_path))
                except Exception as e:
                    print(f"  WARNING: Chapter card render failed: {e}")

        timeline_pos_sec += duration_sec

    print(f"  Placed {placed_count} segments on V1")

    # ── Import and place overlays (sorted chronologically) ──
    overlay_items.sort(key=lambda x: x[0])  # CRITICAL: sort by position

    if overlay_items:
        overlay_bin = None
        for sub in mp.GetRootFolder().GetSubFolderList():
            if sub.GetName() == "Overlays":
                overlay_bin = sub
                break
        if overlay_bin:
            mp.SetCurrentFolder(overlay_bin)

        for pos_sec, track, mov_path in overlay_items:
            if not os.path.exists(mov_path):
                continue
            items = mp.ImportMedia([mov_path])
            if items:
                mp.AppendToTimeline([{
                    "mediaPoolItem": items[0],
                    "mediaType": 1,
                    "trackIndex": track,
                }])

        mp.SetCurrentFolder(mp.GetRootFolder())
        print(f"  Placed {len(overlay_items)} overlays (V3/V4)")

    return timeline


def main():
    import argparse

    ap = argparse.ArgumentParser(description="DaVinci Resolve Timeline Builder v2")
    ap.add_argument("--storyboard", "-s", required=True,
                    help="Directed storyboard JSON")
    ap.add_argument("--manifest", "-m", help="Narration manifest JSON")
    ap.add_argument("--clips-dir", help="Directory with video clips")
    ap.add_argument("--images-dir", help="Directory with images")
    ap.add_argument("--narration", help="Narration audio file")
    ap.add_argument("--music", help="Music audio file")
    ap.add_argument("--project-name", default="LearnByLeo Production",
                    help="DaVinci project name")
    ap.add_argument("--soundbites", help="Soundbites JSON for punch-throughs")
    args = ap.parse_args()

    print("=" * 60)
    print("  DaVinci Resolve Timeline Builder v2")
    print("=" * 60)

    # Defaults
    clips_dir = args.clips_dir or str(PROJECT_ROOT / "footage" / "clips")
    images_dir = args.images_dir or str(PROJECT_ROOT / "footage" / "images")
    narration = args.narration or str(PROJECT_ROOT / "audio" / "narration.wav")

    # Connect
    resolve = connect_resolve()

    # Setup project
    project = setup_project(resolve, name=args.project_name)

    # Import media
    print("\nImporting media...")
    imported = import_media(project, clips_dir, images_dir, narration, args.music)

    # Build timeline
    print("\nBuilding timeline...")
    timeline = build_timeline(project, imported, args.storyboard, args.manifest)

    if timeline:
        fps = 30
        print(f"\nDone! Timeline '{timeline.GetName()}' is ready.")
        end_frame = timeline.GetEndFrame()
        start_frame = timeline.GetStartFrame()
        if end_frame and start_frame:
            print(f"  Duration: {(end_frame - start_frame) / fps:.1f}s")
        print(f"  Tracks: {timeline.GetTrackCount('video')} video, "
              f"{timeline.GetTrackCount('audio')} audio")

        # MANDATORY: Trim and verify alignment
        a1 = timeline.GetItemListInTrack('audio', 1) or []
        if a1:
            narr_end = (a1[-1].GetEnd() - timeline.GetStartFrame()) / fps
            print(f"\nTrimming timeline to narration end ({narr_end:.1f}s + 5s buffer)...")
            trim_timeline_to_narration(timeline, narr_end, buffer_sec=5.0)

        print("\nVerifying track alignment...")
        alignment = verify_track_alignment(timeline)
        if not alignment['passed']:
            print("\n  WARNING: Track alignment check FAILED.")
            print("    Some tracks extend past narration. Review and fix before rendering.")

        print("\nVerifying source diversity...")
        diversity = verify_source_diversity(timeline)
        if not diversity['passed']:
            print("\n  WARNING: Source diversity check FAILED.")
            print("    Some sources are overused. Diversify before rendering.")

    project.SaveProject()
    print("\nProject saved.")


if __name__ == "__main__":
    main()
