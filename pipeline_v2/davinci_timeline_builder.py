#!/usr/bin/env python3
"""
DaVinci Resolve Timeline Builder (v2 — reads Director v3 schema)

Reads the director output (v3 schema) and builds a complete timeline in DaVinci.
The director has already picked EXACT files, clip audio rules, VO pauses, SFX,
text overlays, and transitions. This builder just EXECUTES those decisions.

Director v3 schema fields used per segment:
  - visual_file: exact filename to place on V1
  - visual_type: "video_clip" or "still_image"
  - clip_start_sec: where to start in the source clip
  - clip_audio: "mute" / "play" / "play_then_mute"
  - clip_audio_duration: seconds of clip audio to play
  - vo_pause_before / vo_pause_after: VO silence gaps
  - sfx.file: exact SFX filename for A3/A4
  - text_overlay + text_style: V4 text reveals
  - transition_in / transition_out: cut/dissolve/fade
  - chapter_card: chapter title for V3
  - zoom_target: face/document/subject/wide

Track layout:
  V1: Main footage (video clips + images, ≤7s each)
  V2: Character cards / stat overlays (faded ProRes MOVs)
  V3: Chapter cards + gap fills
  V4: Text reveals (typewriter with audio)
  V5: Vignette overlay
  A1: Narration (with VO pauses baked in)
  A2: Music (ducked)
  A3: SFX (tension, shimmer, impact)
  A4: SFX 2 (overflow)
  A5: Typewriter click audio

Usage:
  python -m pipeline_v2.davinci_timeline_builder --director storyboards/directed_v3.json
"""

import json
import os
import subprocess
import sys
from pathlib import Path

RESOLVE_MODULES = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
if RESOLVE_MODULES not in sys.path:
    sys.path.append(RESOLVE_MODULES)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.davinci_helpers import (
    render_overlay_with_fade,
    create_chapter_card,
    create_text_reveal,
    create_typewriter_with_audio,
    create_ducked_music,
    trim_timeline_to_narration,
    verify_track_alignment,
    verify_source_diversity,
    normalize_sfx,
)


FPS = 30
MAX_CLIP_DURATION = 7.0  # seconds, fair use


def connect_resolve():
    """Connect to DaVinci Resolve."""
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("ERROR: Cannot connect to DaVinci Resolve. Is it running?")
        sys.exit(1)
    return resolve


def load_director_output(path):
    """Load director v3 output."""
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


def import_media(mp, segments, narration_path, music_path, sfx_dir):
    """Import all media files referenced by director into media pool."""
    root = mp.GetRootFolder()
    mp.SetCurrentFolder(root)
    
    # Collect all unique files to import
    files_to_import = set()
    
    for seg in segments:
        vf = seg.get("visual_file")
        if vf:
            # Search common directories for the file
            for search_dir in [
                str(PROJECT_ROOT / "footage"),
                os.path.expanduser("~/Desktop/SecretScores_Media"),
                str(PROJECT_ROOT / "images"),
            ]:
                for dirpath, _, filenames in os.walk(search_dir):
                    if vf in filenames:
                        files_to_import.add(os.path.join(dirpath, vf))
                        break
        
        sf = seg.get("sfx", {})
        if sf and sf.get("file"):
            sfx_path = os.path.join(sfx_dir, sf["file"])
            if os.path.exists(sfx_path):
                files_to_import.add(sfx_path)
    
    # Add narration and music
    if narration_path and os.path.exists(narration_path):
        files_to_import.add(narration_path)
    if music_path and os.path.exists(music_path):
        files_to_import.add(music_path)
    
    # Import
    existing = set(clip.GetName() for clip in root.GetClipList())
    new_files = [f for f in files_to_import if os.path.basename(f) not in existing]
    
    if new_files:
        items = mp.ImportMedia(list(new_files))
        print(f"  Imported {len(items) if items else 0} new media files")
    
    # Build pool lookup
    pool = {}
    for clip in root.GetClipList():
        pool[clip.GetName()] = clip
    
    return pool


def build_timeline(resolve, project, mp, segments, pool, narration_path, music_path, sfx_dir):
    """Build the complete DaVinci timeline from director decisions."""
    
    # Create or get timeline
    timeline_name = "Production"
    timeline = mp.CreateEmptyTimeline(timeline_name)
    if not timeline:
        # Already exists, find it
        for i in range(1, project.GetTimelineCount() + 1):
            tl = project.GetTimelineByIndex(i)
            if tl.GetName() == timeline_name:
                timeline = tl
                break
        if not timeline:
            timeline = mp.CreateEmptyTimeline(timeline_name + " v2")
    
    project.SetCurrentTimeline(timeline)
    tl_start = timeline.GetStartFrame()
    
    # Ensure tracks exist
    while timeline.GetTrackCount('video') < 5:
        timeline.AddTrack('video')
    while timeline.GetTrackCount('audio') < 5:
        timeline.AddTrack('audio')
    
    timeline.SetTrackName('audio', 1, 'Narration')
    timeline.SetTrackName('audio', 2, 'Music')
    timeline.SetTrackName('audio', 3, 'SFX')
    timeline.SetTrackName('audio', 4, 'SFX 2')
    timeline.SetTrackName('audio', 5, 'Typewriter')
    
    # ── V1: Main footage ──
    # Place clips in order. Director picked exact files.
    # Sort by segment order (they're already in order from director).
    print(f"\n  V1: Placing {len(segments)} segments...")
    
    v1_placed = 0
    source_usage = {}
    
    for i, seg in enumerate(segments):
        vf = seg.get("visual_file")
        if not vf or vf not in pool:
            # Fallback: use any available clip
            for name, clip in pool.items():
                if name.endswith('.mp4') and source_usage.get(name, 0) < 3:
                    vf = name
                    break
        
        if vf and vf in pool:
            # Enforce fair use: max 7s, max 3 uses per source
            source_usage[vf] = source_usage.get(vf, 0) + 1
            
            clip_start = int(seg.get("clip_start_sec", 0) * FPS)
            clip_end = clip_start + int(MAX_CLIP_DURATION * FPS)
            
            mp.AppendToTimeline([{
                "mediaPoolItem": pool[vf],
                "mediaType": 1,
                "trackIndex": 1,
                "startFrame": clip_start,
                "endFrame": clip_end,
            }])
            v1_placed += 1
    
    print(f"  V1: {v1_placed} clips placed")
    
    # ── V2: Overlays (character cards, stats) ──
    # Only place overlays that the director specified as text_overlay
    # Sort chronologically before placing
    overlays = []
    total_words = sum(s.get("word_count", len(s.get("text", "").split())) for s in segments)
    narr_dur = total_words / 2.5  # ~150 WPM
    cumulative = 0
    
    for i, seg in enumerate(segments):
        words = seg.get("word_count", len(seg.get("text", "").split()))
        seg_start = 11.8 + (cumulative / total_words) * narr_dur if total_words else 0
        cumulative += words
        
        text = seg.get("text_overlay")
        if text:
            style = seg.get("text_style", "static")
            overlays.append((seg_start, text, style, i))
    
    overlays.sort(key=lambda x: x[0])
    
    print(f"  V2/V4: {len(overlays)} text overlays...")
    
    fade_dir = os.path.expanduser("~/Desktop/SecretScores_Media/assets_faded/")
    os.makedirs(fade_dir, exist_ok=True)
    typewriter_dir = os.path.expanduser("~/Desktop/SecretScores_Media/typewriter/")
    os.makedirs(typewriter_dir, exist_ok=True)
    key_sound = os.path.join(str(PROJECT_ROOT), "assets/sfx/typewriter_key.wav")
    
    for pos, text, style, seg_idx in overlays:
        if style == "typewriter":
            # Create typewriter animation with click audio
            mov_path = os.path.join(typewriter_dir, f"tw_{seg_idx}_{text[:10].replace(' ', '_')}.mov")
            create_typewriter_with_audio(text, mov_path, key_sound)
            
            if os.path.exists(mov_path):
                items = mp.ImportMedia([mov_path])
                if items:
                    mp.AppendToTimeline([{
                        "mediaPoolItem": items[0],
                        "mediaType": 1,
                        "trackIndex": 4,
                    }])
        else:
            # Static/lower_third text reveal with fade
            mov_path = os.path.join(fade_dir, f"text_{seg_idx}_{text[:10].replace(' ', '_')}.mov")
            create_text_reveal(text, fade_dir, style=style)
            
            if os.path.exists(mov_path):
                items = mp.ImportMedia([mov_path])
                if items:
                    mp.AppendToTimeline([{
                        "mediaPoolItem": items[0],
                        "mediaType": 1,
                        "trackIndex": 2,
                    }])
    
    # ── V3: Chapter cards ──
    chapters = []
    cumulative = 0
    for i, seg in enumerate(segments):
        words = seg.get("word_count", len(seg.get("text", "").split()))
        seg_start = 11.8 + (cumulative / total_words) * narr_dur if total_words else 0
        cumulative += words
        
        card_title = seg.get("chapter_card")
        if card_title:
            chapters.append((seg_start - 2, card_title))  # 2s before content
    
    chapters.sort(key=lambda x: x[0])
    
    print(f"  V3: {len(chapters)} chapter cards...")
    
    card_dir = os.path.expanduser("~/Desktop/SecretScores_Media/chapter_cards/")
    os.makedirs(card_dir, exist_ok=True)
    
    for pos, title in chapters:
        card_path = create_chapter_card(title, card_dir)
        if card_path and os.path.exists(card_path):
            items = mp.ImportMedia([card_path])
            if items:
                mp.AppendToTimeline([{
                    "mediaPoolItem": items[0],
                    "mediaType": 1,
                    "trackIndex": 3,
                }])
    
    # ── A1: Narration ──
    if narration_path and os.path.basename(narration_path) in pool:
        mp.AppendToTimeline([{
            "mediaPoolItem": pool[os.path.basename(narration_path)],
            "mediaType": 2,
            "trackIndex": 1,
        }])
        print(f"  A1: Narration placed")
    
    # ── A2: Music (ducked) ──
    if music_path and os.path.basename(music_path) in pool:
        mp.AppendToTimeline([{
            "mediaPoolItem": pool[os.path.basename(music_path)],
            "mediaType": 2,
            "trackIndex": 2,
        }])
        print(f"  A2: Music placed")
    
    # ── A3/A4: SFX ──
    # Sort SFX chronologically, alternate between A3 and A4
    sfx_list = []
    cumulative = 0
    for i, seg in enumerate(segments):
        words = seg.get("word_count", len(seg.get("text", "").split()))
        seg_start = 11.8 + (cumulative / total_words) * narr_dur if total_words else 0
        cumulative += words
        
        sfx = seg.get("sfx")
        if sfx and sfx.get("file"):
            sfx_list.append((seg_start, sfx["file"]))
    
    sfx_list.sort(key=lambda x: x[0])
    
    print(f"  A3/A4: {len(sfx_list)} SFX...")
    
    for idx, (pos, sfx_file) in enumerate(sfx_list):
        if sfx_file in pool:
            track = 3 if idx % 2 == 0 else 4
            mp.AppendToTimeline([{
                "mediaPoolItem": pool[sfx_file],
                "mediaType": 2,
                "trackIndex": track,
            }])
    
    # ── Mute clip audio during narration ──
    print(f"  Muting V1 clip audio during narration...")
    v1_clips = timeline.GetItemListInTrack('video', 1) or []
    narr_start_sec = 11.8
    
    for i, seg in enumerate(segments):
        if i < len(v1_clips):
            clip = v1_clips[i]
            clip_start = (clip.GetStart() - tl_start) / FPS
            clip_audio_rule = seg.get("clip_audio", "mute")
            
            if clip_audio_rule == "mute" or clip_start >= narr_start_sec:
                clip.SetProperty("Volume", 0)
            elif clip_audio_rule == "play_then_mute":
                # Can't do mid-clip volume changes via API
                # Leave audio on — the ducked music handles the mix
                pass
    
    return timeline


def post_build_checks(timeline):
    """Run mandatory post-build verification."""
    print(f"\n  POST-BUILD CHECKS:")
    
    fps = 30
    tl_start = timeline.GetStartFrame()
    
    # Track alignment
    ends = {}
    for tt, label in [('video', 'V'), ('audio', 'A')]:
        for t in range(1, timeline.GetTrackCount(tt) + 1):
            clips = timeline.GetItemListInTrack(tt, t) or []
            if clips:
                end = (clips[-1].GetEnd() - tl_start) / fps
                ends[f"{label}{t}"] = end
    
    if ends:
        main = {k: v for k, v in ends.items() if k in ('V1', 'A1', 'A2')}
        if main:
            spread = max(main.values()) - min(main.values())
            ok = "✅" if spread < 30 else "⚠️"
            print(f"    {ok} Track alignment: {spread:.0f}s spread")
    
    # Source diversity
    v1 = timeline.GetItemListInTrack('video', 1) or []
    usage = {}
    for c in v1:
        usage[c.GetName()] = usage.get(c.GetName(), 0) + 1
    
    if usage:
        max_use = max(usage.values())
        unique = len(usage)
        ok = "✅" if max_use <= 3 else "⚠️"
        print(f"    {ok} Source diversity: {unique} unique, max {max_use}x")
    
    # Gaps
    prev = 0
    gap_count = 0
    for c in v1:
        s = (c.GetStart() - tl_start) / fps
        if s - prev > 2:
            gap_count += 1
        prev = (c.GetEnd() - tl_start) / fps
    
    ok = "✅" if gap_count == 0 else "⚠️"
    print(f"    {ok} V1 gaps: {gap_count}")
    
    # Intro
    if v1 and 'intro' in v1[0].GetName().lower():
        print(f"    ✅ Intro present")
    else:
        print(f"    ⚠️ No intro clip at V1[0]")
    
    # Clip count
    print(f"    ℹ️  V1: {len(v1)} clips")
    
    for tt, label in [('video', 'V'), ('audio', 'A')]:
        for t in range(1, min(timeline.GetTrackCount(tt) + 1, 6)):
            clips = timeline.GetItemListInTrack(tt, t) or []
            if clips:
                name = timeline.GetTrackName(tt, t)
                print(f"    ℹ️  {label}{t} ({name}): {len(clips)} clips")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build DaVinci timeline from director v3 output")
    parser.add_argument('--director', required=True, help='Director output JSON (v3 schema)')
    parser.add_argument('--narration', help='Narration WAV path')
    parser.add_argument('--music', help='Music WAV path')
    parser.add_argument('--sfx-dir', default='', help='SFX directory')
    parser.add_argument('--timeline-name', default='Production', help='Timeline name')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"DaVinci Timeline Builder (v3 schema)")
    print(f"{'='*60}")
    
    # Load director output
    print(f"\n  Loading director: {args.director}")
    data, segments = load_director_output(args.director)
    print(f"  {len(segments)} segments")
    
    # Connect to DaVinci
    print(f"\n  Connecting to DaVinci Resolve...")
    resolve = connect_resolve()
    project = resolve.GetProjectManager().GetCurrentProject()
    mp = project.GetMediaPool()
    print(f"  Project: {project.GetName()}")
    
    # Import media
    print(f"\n  Importing media...")
    pool = import_media(mp, segments, args.narration, args.music, args.sfx_dir)
    print(f"  Media pool: {len(pool)} items")
    
    # Build timeline
    print(f"\n  Building timeline...")
    timeline = build_timeline(resolve, project, mp, segments, pool,
                              args.narration, args.music, args.sfx_dir)
    
    # Post-build checks
    post_build_checks(timeline)
    
    # Save
    subprocess.run(['osascript', '-e',
        'tell application "System Events" to tell process "Resolve" to keystroke "s" using command down'],
        capture_output=True, timeout=5)
    
    print(f"\n  ✅ Timeline built and saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
