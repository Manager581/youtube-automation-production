#!/usr/bin/env python3
"""
Place overlays, SFX, and fix music position on chapter timelines.

Uses DaVinci Python API + AppleScript UI automation.
Requires: Accessibility permissions for claude/Terminal in System Settings.

Usage:
  python -m pipeline_v2.place_assets --chapter 0
  python -m pipeline_v2.place_assets --all
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

RESOLVE_MODULES = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
if RESOLVE_MODULES not in sys.path:
    sys.path.append(RESOLVE_MODULES)

PROJECT_ROOT = Path(__file__).parent.parent


# ─── AppleScript helpers ────────────────────────────────────────────────────

def run_applescript(script, timeout=20):
    """Run AppleScript, return (success, stderr)."""
    try:
        r = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"


def activate_davinci():
    """Bring DaVinci to front."""
    run_applescript('tell application "DaVinci Resolve" to activate')
    time.sleep(0.3)


def goto_timecode(tc_digits):
    """Move DaVinci playhead to timecode. tc_digits = '01000000' for 01:00:00:00."""
    ok, err = run_applescript(f'''
        tell application "DaVinci Resolve" to activate
        delay 0.2
        tell application "System Events"
            tell process "DaVinci Resolve"
                keystroke "="
                delay 0.2
                keystroke "{tc_digits}"
                delay 0.15
                keystroke return
                delay 0.3
            end tell
        end tell
    ''')
    if not ok:
        print(f"      goto_timecode failed: {err}")
    return ok


def tc_to_digits(tc_string):
    """Convert '01:00:28:06' to '01002806'."""
    return tc_string.replace(":", "")


def search_and_overwrite(clip_name):
    """Search media pool for clip and overwrite at playhead.

    Steps:
    1. Click in media pool area (Cmd+F to search)
    2. Type clip name
    3. Return to select
    4. Escape to close search
    5. F10 to overwrite
    """
    # Escape any quotes in clip name
    safe_name = clip_name.replace('"', '\\"').replace("'", "")

    ok, err = run_applescript(f'''
        tell application "System Events"
            tell process "DaVinci Resolve"
                -- Search media pool
                keystroke "f" using command down
                delay 0.4
                -- Clear search and type clip name
                keystroke "a" using command down
                delay 0.1
                keystroke "{safe_name}"
                delay 0.8
                -- Select first result
                keystroke return
                delay 0.4
                -- Close search
                key code 53
                delay 0.3
                -- F10 = Overwrite at playhead on destination track
                key code 109
                delay 0.5
            end tell
        end tell
    ''')
    if not ok:
        print(f"      search_and_overwrite failed: {err}")
    return ok


def select_destination_track(track_type, track_num):
    """Select a destination track in DaVinci.

    In DaVinci, destination patches are toggled by Alt+clicking the track header,
    or we can use the keyboard shortcut to cycle destinations.
    For simplicity, we'll click the destination patch area.

    This is approximate — we toggle all other destinations OFF then the target ON.
    """
    # DaVinci doesn't have simple keyboard shortcuts for destination tracks.
    # We'll use the "auto track" approach — just overwrite and DaVinci will
    # place on the lowest available track. For overlays (V2), we need V1
    # destination OFF and V2 ON.
    #
    # For now, we'll rely on DaVinci's default behavior:
    # - Video overwrites go to the selected video destination
    # - Audio overwrites go to the selected audio destination
    #
    # TODO: Click destination patches if auto-targeting is wrong
    pass


# ─── Data loading ───────────────────────────────────────────────────────────

def load_placement_data():
    """Load director v4 and narration alignment, compute chapter data.

    Returns the same chapter structure as chapter_assembler.py --plan.
    """
    # Import from chapter_assembler
    sys.path.insert(0, str(PROJECT_ROOT))
    from pipeline_v2.chapter_assembler import (
        load_director, load_alignment, match_segments_to_narration,
        split_into_chapters, pick_chapter_sfx, find_overlay_file,
        deduplicate_visuals, CHAPTERS, _sec_to_timecode,
    )

    _, raw_segments = load_director()
    alignment = load_alignment()
    matched = match_segments_to_narration(raw_segments, alignment)
    chapter_map = split_into_chapters(matched)

    result = {}
    for ch_num, ch_segs in chapter_map.items():
        ch_def = CHAPTERS[ch_num]
        ch_segs = deduplicate_visuals(ch_segs)
        sfx_picks = pick_chapter_sfx(ch_segs)
        ch_start = ch_segs[0]["_narr_start"]

        # Build overlay list
        overlays = []
        for seg in ch_segs:
            overlay_text = seg.get("text_overlay")
            if not overlay_text:
                continue
            from pipeline_v2.chapter_assembler import find_overlay_file
            overlay_path = find_overlay_file(overlay_text)
            if overlay_path:
                rel_time = max(0, seg["_narr_start"] - ch_start)
                fps = 24
                tl_start = 3600  # 01:00:00:00
                tc = _sec_to_timecode(rel_time, fps, tl_start * fps)
                overlays.append({
                    "file": os.path.basename(overlay_path),
                    "timecode": tc,
                    "tc_digits": tc_to_digits(tc),
                    "text": overlay_text[:40],
                })

        # Build SFX list
        sfx_list = []
        for sfx_time, sfx_file in sfx_picks:
            rel_time = sfx_time - ch_start
            fps = 24
            tl_start = 3600
            tc = _sec_to_timecode(rel_time, fps, tl_start * fps)
            sfx_list.append({
                "file": sfx_file,
                "timecode": tc,
                "tc_digits": tc_to_digits(tc),
                "track": 3 if len(sfx_list) % 2 == 0 else 4,
            })

        result[ch_num] = {
            "def": ch_def,
            "overlays": overlays,
            "sfx": sfx_list,
            "music": ch_def["music"],
        }

    return result


# ─── DaVinci API helpers ────────────────────────────────────────────────────

def connect():
    """Connect to DaVinci Resolve."""
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("ERROR: Cannot connect to DaVinci. Is it running?")
        sys.exit(1)
    return resolve


def switch_to_timeline(project, timeline_name):
    """Switch to a specific timeline by name."""
    for i in range(1, project.GetTimelineCount() + 1):
        tl = project.GetTimelineByIndex(i)
        if tl.GetName() == timeline_name:
            project.SetCurrentTimeline(tl)
            return tl
    return None


def fix_music_position(project, mp, timeline, music_file):
    """Fix A2 music by deleting and re-placing at start.

    Strategy: Delete the A2 clip, delete A1 clip, place music first (goes to 0),
    then re-place narration (goes after music). But that breaks A1.

    Better strategy: Delete A2, use AppleScript to move playhead to 0,
    then overwrite music from media pool onto A2.
    """
    # Delete existing A2 clip
    a2_clips = timeline.GetItemListInTrack('audio', 2) or []
    if a2_clips:
        timeline.DeleteClips(a2_clips)
        print(f"    Deleted {len(a2_clips)} A2 clip(s)")
        time.sleep(0.5)

    # Move playhead to start
    goto_timecode("01000000")
    time.sleep(0.3)

    # Search for music in media pool and overwrite to A2
    # First we need A2 to be the audio destination
    # For now, just overwrite — we'll handle destination targeting if needed
    activate_davinci()
    ok = search_and_overwrite(music_file)
    if ok:
        print(f"    Music placed at 01:00:00:00")
    else:
        print(f"    Music placement failed — manual fix needed")

    time.sleep(0.5)


def place_overlay_at_timecode(tc_digits, overlay_file):
    """Place a single overlay on V2 at the given timecode."""
    goto_timecode(tc_digits)
    time.sleep(0.2)
    ok = search_and_overwrite(overlay_file)
    return ok


def place_sfx_at_timecode(tc_digits, sfx_file):
    """Place a single SFX on A3/A4 at the given timecode."""
    goto_timecode(tc_digits)
    time.sleep(0.2)
    ok = search_and_overwrite(sfx_file)
    return ok


# ─── Main ───────────────────────────────────────────────────────────────────

def process_chapter(project, mp, ch_num, ch_data):
    """Place all overlays and SFX for one chapter."""
    ch_def = ch_data["def"]
    tl_name = ch_def["timeline_name"]

    print(f"\n{'='*60}")
    print(f"  PLACING ASSETS: {ch_def['name']}")
    print(f"  Timeline: {tl_name}")
    print(f"  Overlays: {len(ch_data['overlays'])}")
    print(f"  SFX: {len(ch_data['sfx'])}")
    print(f"{'='*60}")

    # Switch to this chapter's timeline
    timeline = switch_to_timeline(project, tl_name)
    if not timeline:
        # Try v2 suffix
        timeline = switch_to_timeline(project, tl_name + " v2")
    if not timeline:
        print(f"  ERROR: Timeline '{tl_name}' not found!")
        return False

    time.sleep(0.5)
    activate_davinci()
    time.sleep(0.5)

    # ── Fix A2 music position ──
    print(f"\n  Fixing A2 music...")
    fix_music_position(project, mp, timeline, ch_data["music"])

    # ── Place SFX ──
    if ch_data["sfx"]:
        print(f"\n  Placing SFX...")
        for sfx in ch_data["sfx"]:
            print(f"    A{sfx['track']}: {sfx['file']} at {sfx['timecode']}")
            ok = place_sfx_at_timecode(sfx["tc_digits"], sfx["file"])
            if not ok:
                print(f"      FAILED — manual placement needed")
            time.sleep(0.3)

    # ── Place overlays ──
    if ch_data["overlays"]:
        print(f"\n  Placing overlays on V2...")
        for ov in ch_data["overlays"]:
            print(f"    V2: {ov['file'][:40]} at {ov['timecode']} \"{ov['text']}\"")
            ok = place_overlay_at_timecode(ov["tc_digits"], ov["file"])
            if not ok:
                print(f"      FAILED — manual placement needed")
            time.sleep(0.3)

    # ── Verify ──
    print(f"\n  Verifying {ch_def['name']}...")
    fps = 24
    sf = timeline.GetStartFrame()
    for tt, label in [('video', 'V'), ('audio', 'A')]:
        for t in range(1, timeline.GetTrackCount(tt) + 1):
            clips = timeline.GetItemListInTrack(tt, t) or []
            if clips:
                dur = (clips[-1].GetEnd() - sf) / fps
                print(f"    {label}{t}: {len(clips)} clips ({dur:.1f}s)")

    # Save
    run_applescript('''
        tell application "System Events"
            tell process "DaVinci Resolve"
                keystroke "s" using command down
            end tell
        end tell
    ''')

    return True


def main():
    parser = argparse.ArgumentParser(description="Place overlays/SFX on chapter timelines")
    parser.add_argument("--chapter", type=int, help="Process specific chapter (0-5)")
    parser.add_argument("--all", action="store_true", help="Process all chapters")
    args = parser.parse_args()

    if args.chapter is None and not args.all:
        parser.print_help()
        return

    print("Loading placement data...")
    chapters = load_placement_data()

    print("Connecting to DaVinci...")
    resolve = connect()
    project = resolve.GetProjectManager().GetCurrentProject()
    mp = project.GetMediaPool()
    resolve.OpenPage('edit')

    targets = sorted(chapters.keys()) if args.all else [args.chapter]

    for ch_num in targets:
        if ch_num not in chapters:
            print(f"  Chapter {ch_num} not found")
            continue
        process_chapter(project, mp, ch_num, chapters[ch_num])

    print(f"\n  Done! Review each chapter in DaVinci.")


if __name__ == "__main__":
    main()
