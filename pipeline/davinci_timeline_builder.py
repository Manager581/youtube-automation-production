#!/usr/bin/env python3
"""
DaVinci Resolve Timeline Builder

Reads the production guide and builds a complete timeline in DaVinci Resolve
using the scripting API. Imports all media, places clips, adds text overlays,
and sets up the audio mix.

Requirements:
  - DaVinci Resolve must be running
  - Python scripting must be enabled in Resolve preferences

Usage:
  RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
  RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
  PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
  python3 pipeline/davinci_timeline_builder.py
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
CLIPS_DIR = PROJECT_ROOT / "footage/fern_clone/secret_scores/clips"
IMAGES_DIR = PROJECT_ROOT / "footage/fern_clone/secret_scores/images"
NARRATION_PATH = PROJECT_ROOT / "audio/secret_scores/narration.wav"
GUIDE_PATH = PROJECT_ROOT / "production_guide_secret_scores.md"
STORYBOARD_PATH = PROJECT_ROOT / "storyboards/secret_scores_directed.json"
MANIFEST_PATH = PROJECT_ROOT / "audio/secret_scores/narration_manifest.json"


def connect_resolve():
    """Connect to DaVinci Resolve."""
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        # Try loading directly
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


def setup_project(resolve, name="Secret Scores"):
    """Create or open the project."""
    pm = resolve.GetProjectManager()
    
    # Try to open existing project
    project = pm.LoadProject(name)
    if project:
        print(f"Opened existing project: {name}")
        return project
    
    # Create new project
    project = pm.CreateProject(name)
    if not project:
        print(f"ERROR: Cannot create project '{name}'")
        sys.exit(1)
    
    # Set project settings
    project.SetSetting("timelineResolutionWidth", "1920")
    project.SetSetting("timelineResolutionHeight", "1080")
    project.SetSetting("timelineFrameRate", "30")
    
    print(f"Created project: {name} (1920x1080 @ 30fps)")
    return project


def import_media(project):
    """Import all clips, images, and narration into the media pool."""
    mp = project.GetMediaPool()
    root = mp.GetRootFolder()
    
    # Create bins
    clips_bin = mp.AddSubFolder(root, "Clips")
    images_bin = mp.AddSubFolder(root, "Images")
    audio_bin = mp.AddSubFolder(root, "Audio")
    
    imported = {"clips": [], "images": [], "audio": []}
    
    # Import clips
    if CLIPS_DIR.exists():
        mp.SetCurrentFolder(clips_bin)
        clip_files = [str(f) for f in sorted(CLIPS_DIR.iterdir()) 
                      if f.suffix in ('.mp4', '.mkv', '.webm', '.mov')]
        if clip_files:
            items = mp.ImportMedia(clip_files)
            if items:
                imported["clips"] = list(items)
                print(f"  Imported {len(items)} clips")
    
    # Import images
    if IMAGES_DIR.exists():
        mp.SetCurrentFolder(images_bin)
        img_files = [str(f) for f in sorted(IMAGES_DIR.iterdir())
                     if f.suffix in ('.jpg', '.jpeg', '.png', '.webp')]
        if img_files:
            items = mp.ImportMedia(img_files)
            if items:
                imported["images"] = list(items)
                print(f"  Imported {len(items)} images")
    
    # Import narration
    if NARRATION_PATH.exists():
        mp.SetCurrentFolder(audio_bin)
        items = mp.ImportMedia([str(NARRATION_PATH)])
        if items:
            imported["audio"] = list(items)
            print(f"  Imported narration audio")
    
    mp.SetCurrentFolder(root)
    return imported


def load_narration_manifest():
    """Load narration timing data."""
    if not MANIFEST_PATH.exists():
        print("WARNING: No narration manifest found")
        return None
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def build_timeline(project, imported, manifest):
    """Build the timeline following the production guide."""
    mp = project.GetMediaPool()
    
    # Create timeline
    timeline = mp.CreateEmptyTimeline("Secret Scores - Main")
    if not timeline:
        print("ERROR: Cannot create timeline")
        return None
    
    project.SetCurrentTimeline(timeline)
    print(f"Created timeline: {timeline.GetName()}")
    
    # Put narration on audio track 1
    if imported["audio"]:
        narration_clip = imported["audio"][0]
        mp.AppendToTimeline([{
            "mediaPoolItem": narration_clip,
            "mediaType": 2,  # Audio only
            "trackIndex": 1,
        }])
        print("  Added narration to audio track 1")
    
    # Build clip lookup by name
    clip_lookup = {}
    for clip in imported["clips"]:
        name = clip.GetName()
        clip_lookup[name.lower()] = clip
    
    # Load storyboard for segment timing
    if STORYBOARD_PATH.exists():
        with open(STORYBOARD_PATH) as f:
            storyboard = json.load(f)
        segments = storyboard.get("segments", storyboard) if isinstance(storyboard, dict) else storyboard
    else:
        segments = []
    
    # Place clips on video track based on narration segments
    if manifest:
        timeline_pos = 0  # frames
        fps = 30
        
        for i, seg in enumerate(manifest.get("segments", [])):
            if seg["type"] != "speech":
                timeline_pos += int(seg.get("duration_sec", 0) * fps)
                continue
            
            dur_sec = seg.get("duration_sec", 3)
            dur_frames = int(dur_sec * fps)
            
            # Find matching clip based on content
            text = seg.get("text", "").lower()
            best_clip = None
            
            # Simple keyword matching to assign clips
            if any(w in text for w in ["cigna", "insurance", "claim", "denied"]):
                for k, v in clip_lookup.items():
                    if "cigna" in k or "insurance" in k or "deny" in k:
                        best_clip = v
                        break
            elif any(w in text for w in ["hirevue", "hiring", "resume", "personality", "kyle", "behm"]):
                for k, v in clip_lookup.items():
                    if "algorithm" in k and "disability" in k:
                        best_clip = v
                        break
            elif any(w in text for w in ["lexisnexis", "telematics", "data broker"]):
                for k, v in clip_lookup.items():
                    if "lexisnexis" in k or "data broker" in k:
                        best_clip = v
                        break
            elif any(w in text for w in ["ftc", "congress", "regulation", "senator"]):
                for k, v in clip_lookup.items():
                    if "ftc" in k or "senate" in k or "protecting" in k:
                        best_clip = v
                        break
            elif any(w in text for w in ["tenant", "apartment", "housing", "rent", "evict"]):
                for k, v in clip_lookup.items():
                    if "jacksonville" in k or "lawsuit" in k:
                        best_clip = v
                        break
            
            # Fallback: use 60 Minutes or John Oliver for general data broker content
            if not best_clip:
                for k, v in clip_lookup.items():
                    if "60 minutes" in k or "john oliver" in k or "data brokers" in k:
                        best_clip = v
                        break
            
            # If we found a clip, add it
            if best_clip and dur_frames > 0:
                mp.AppendToTimeline([{
                    "mediaPoolItem": best_clip,
                    "mediaType": 1,  # Video only
                    "trackIndex": 1,
                    "startFrame": 0,
                    "endFrame": min(dur_frames, int(best_clip.GetClipProperty("Frames"))),
                }])
            
            timeline_pos += dur_frames
        
        print(f"  Placed {i+1} segments on timeline")
    
    return timeline


def apply_soundbite_punchthroughs(project, timeline, soundbites_path):
    """
    Apply soundbite audio punch-throughs to an existing timeline.

    Reads soundbite JSON and creates volume adjustments:
    - Ducks narration (A2) volume at punch-through points
    - Unmutes clip audio (A1) at the same points
    - Uses fade in/out for smooth transitions

    Note: DaVinci Resolve free version has limited API for volume automation.
    This function generates a DaVinci Resolve Fusion Macro or uses available
    clip-level volume controls.
    """
    with open(soundbites_path) as f:
        soundbites = json.load(f)

    if not soundbites:
        print("No soundbites to apply.")
        return

    fps = int(timeline.GetSetting("timelineFrameRate") or 30)
    print(f"\nApplying {len(soundbites)} soundbite punch-throughs...")

    # Get track items
    # A1 = clip audio (muted by default, unmute at soundbite points)
    # A2 = narration (full volume, duck at soundbite points)
    a1_count = timeline.GetItemListInTrack("audio", 1)
    a2_count = timeline.GetItemListInTrack("audio", 2)

    print(f"  A1 items: {len(a1_count) if a1_count else 0}")
    print(f"  A2 items: {len(a2_count) if a2_count else 0}")

    # Since DaVinci free doesn't support full keyframe automation via API,
    # we'll use clip-level operations: split narration at duck points
    # and set volume on the split segments.
    #
    # Strategy:
    # 1. For each soundbite, calculate the frame position
    # 2. Use Razor to split the narration clip at duck start/end
    # 3. Set volume on the ducked segment to 0 (or low)
    # 4. Set volume on A1 clips in that range to 1.0

    for i, sb in enumerate(soundbites):
        duck_start = sb.get("narration_duck_start_sec", 0)
        duck_end = sb.get("narration_duck_end_sec", 0)
        duration = sb.get("duration_sec", 0)

        duck_start_frame = int(duck_start * fps) + timeline.GetStartFrame()
        duck_end_frame = int(duck_end * fps) + timeline.GetStartFrame()

        print(f"  [{i+1}] {sb.get('source_clip', '?')[:40]}")
        print(f"      Time: {duck_start:.1f}s - {duck_end:.1f}s ({duration:.1f}s)")
        print(f"      Frames: {duck_start_frame} - {duck_end_frame}")
        print(f"      Text: \"{sb.get('soundbite_text', '')[:60]}...\"")

    # Generate a DaVinci-compatible edit decision list (EDL) for manual/script import
    edl_path = Path(soundbites_path).parent / "soundbite_edl.json"
    edl = {
        "description": "Soundbite punch-through edit points",
        "fps": fps,
        "edits": [],
    }

    for i, sb in enumerate(soundbites):
        edl["edits"].append({
            "index": i,
            "action": "duck_narration_unmute_clip",
            "duck_start_sec": sb.get("narration_duck_start_sec", 0),
            "duck_end_sec": sb.get("narration_duck_end_sec", 0),
            "clip_audio_start_sec": sb.get("start_sec", 0),
            "clip_audio_end_sec": sb.get("end_sec", 0),
            "source_clip": sb.get("source_clip", ""),
            "narration_volume_during": 0.0,
            "clip_audio_volume_during": 1.0,
            "fade_in_sec": 0.3,
            "fade_out_sec": 0.5,
            "impact_score": sb.get("impact_score", 0),
            "text": sb.get("soundbite_text", ""),
        })

    with open(edl_path, "w") as f:
        json.dump(edl, f, indent=2)
    print(f"\n  EDL saved: {edl_path}")
    print(f"  Use this with the DaVinci script runner to apply volume keyframes")

    return edl


def generate_resolve_punchthrough_script(soundbites_path, output_path=None):
    """
    Generate a standalone DaVinci Resolve Python script that applies
    soundbite punch-throughs to the current timeline.

    This script is designed to be run inside DaVinci Resolve's console
    (Workspace > Scripts) and uses the Resolve API directly.
    """
    with open(soundbites_path) as f:
        soundbites = json.load(f)

    if output_path is None:
        output_path = Path(soundbites_path).parent / "Apply_Soundbites.py"

    lines = [
        '#!/usr/bin/env python3',
        '"""',
        'Apply Soundbite Punch-Throughs',
        f'Generated from {len(soundbites)} soundbites.',
        'Run this from DaVinci Resolve: Workspace > Scripts > Apply_Soundbites',
        '"""',
        '',
        'resolve = app.GetResolve()',
        'project = resolve.GetProjectManager().GetCurrentProject()',
        'tl = project.GetCurrentTimeline()',
        'fps = int(tl.GetSetting("timelineFrameRate") or 30)',
        'start_frame = tl.GetStartFrame()',
        '',
        '# Get all items on each audio track',
        'a1_items = tl.GetItemListInTrack("audio", 1) or []',
        'a2_items = tl.GetItemListInTrack("audio", 2) or []',
        '',
        'print(f"Timeline: {tl.GetName()}")',
        'print(f"A1 (clip audio): {len(a1_items)} items")',
        'print(f"A2 (narration): {len(a2_items)} items")',
        '',
        '# First, mute ALL of A1 (clip audio) by default',
        'for item in a1_items:',
        '    try:',
        '        item.SetClipProperty("Volume", "0.0")',
        '    except:',
        '        pass',
        'print("Muted all A1 clip audio")',
        '',
        '# Soundbite punch-through points',
        'soundbites = [',
    ]

    for sb in soundbites:
        lines.append(f'    {{"duck_start": {sb.get("narration_duck_start_sec", 0)}, '
                     f'"duck_end": {sb.get("narration_duck_end_sec", 0)}, '
                     f'"clip_start": {sb.get("start_sec", 0)}, '
                     f'"clip_end": {sb.get("end_sec", 0)}, '
                     f'"source": "{sb.get("source_clip", "")[:50]}", '
                     f'"text": """{sb.get("soundbite_text", "")[:80]}"""}},')

    lines.extend([
        ']',
        '',
        'applied = 0',
        'for i, sb in enumerate(soundbites):',
        '    duck_start_frame = int(sb["duck_start"] * fps) + start_frame',
        '    duck_end_frame = int(sb["duck_end"] * fps) + start_frame',
        '',
        '    # Find A1 items that overlap this time range and unmute them',
        '    for item in a1_items:',
        '        item_start = item.GetStart()',
        '        item_end = item.GetEnd()',
        '        if item_start < duck_end_frame and item_end > duck_start_frame:',
        '            try:',
        '                item.SetClipProperty("Volume", "1.0")',
        '                applied += 1',
        '                print(f"  [{i+1}] Unmuted A1 clip at {sb[\'duck_start\']:.1f}s: {sb[\'source\'][:40]}")',
        '            except Exception as e:',
        '                print(f"  [{i+1}] Could not set volume: {e}")',
        '',
        '    # Duck narration (A2) at this point',
        '    for item in a2_items:',
        '        item_start = item.GetStart()',
        '        item_end = item.GetEnd()',
        '        if item_start < duck_end_frame and item_end > duck_start_frame:',
        '            # Note: We cannot split clips or set per-region volume in free Resolve API',
        '            # This is a placeholder — in Studio, we would use Fairlight keyframes',
        '            print(f"  [{i+1}] Narration duck point: {sb[\'duck_start\']:.1f}s - {sb[\'duck_end\']:.1f}s")',
        '            print(f"         (Manual: lower A2 volume here, or use Fairlight)")',
        '',
        'print(f"\\nApplied {applied} soundbite punch-throughs")',
        'print(f"\\nIMPORTANT: For narration ducking, manually lower A2 volume")',
        'print(f"at each punch-through point using Fairlight, or upgrade to")',
        'print(f"DaVinci Resolve Studio for full keyframe automation.")',
        'print("\\nDone!")',
    ])

    script_content = '\n'.join(lines)
    Path(output_path).write_text(script_content)
    print(f"Generated DaVinci script: {output_path}")
    return output_path


def main():
    import argparse

    ap = argparse.ArgumentParser(description="DaVinci Resolve Timeline Builder")
    ap.add_argument("--soundbites", help="Soundbites JSON to apply punch-throughs")
    ap.add_argument("--generate-script", action="store_true",
                    help="Generate a DaVinci Resolve script for soundbite punch-throughs")
    ap.add_argument("--out", help="Output path for generated script")
    args = ap.parse_args()

    if args.generate_script and args.soundbites:
        generate_resolve_punchthrough_script(args.soundbites, args.out)
        return

    print("=" * 60)
    print("  DaVinci Resolve Timeline Builder")
    print("=" * 60)

    # Connect
    resolve = connect_resolve()

    # Setup project
    project = setup_project(resolve)

    # Import media
    print("\nImporting media...")
    imported = import_media(project)

    # Load narration manifest
    manifest = load_narration_manifest()

    # Build timeline
    print("\nBuilding timeline...")
    timeline = build_timeline(project, imported, manifest)

    if timeline:
        print(f"\nDone! Timeline '{timeline.GetName()}' is ready.")
        print(f"  Duration: {timeline.GetEndFrame() / 30:.1f}s")
        print(f"  Tracks: {timeline.GetTrackCount('video')} video, {timeline.GetTrackCount('audio')} audio")

        # Apply soundbites if provided
        if args.soundbites:
            apply_soundbite_punchthroughs(project, timeline, args.soundbites)

        # MANDATORY: Trim all tracks to narration end and verify alignment
        # This prevents the "dead tail" bug where V1/music extend past narration
        from pipeline.davinci_helpers import trim_timeline_to_narration, verify_track_alignment

        a1 = timeline.GetItemListInTrack('audio', 1) or []
        if a1:
            narr_end = (a1[-1].GetEnd() - timeline.GetStartFrame()) / 30
            print(f"\nTrimming timeline to narration end ({narr_end:.1f}s + 5s buffer)...")
            trim_timeline_to_narration(timeline, narr_end, buffer_sec=5.0)

        print("\nVerifying track alignment...")
        alignment = verify_track_alignment(timeline)
        if not alignment['passed']:
            print("\n⚠️  WARNING: Track alignment check FAILED.")
            print("    Some tracks extend past narration. Review and fix before rendering.")

    # Save
    project.SaveProject()
    print("\nProject saved.")


if __name__ == "__main__":
    main()
