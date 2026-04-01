#!/usr/bin/env python3
"""
director_review.py — Post-build timeline verification.

After the builder places everything in DaVinci, the director reads the timeline
BACK and verifies its decisions were executed correctly. Reports mismatches and
can auto-fix via DaVinci API or generate gap lists for the research agent.

Usage:
    python -m pipeline_v2.director_review --director storyboards/directed_v3.json
    python -m pipeline_v2.director_review --director storyboards/directed_v3.json --fix
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# DaVinci scripting
RESOLVE_MODULES = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
if RESOLVE_MODULES not in sys.path:
    sys.path.append(RESOLVE_MODULES)

from pipeline_v2.llm import query_claude

# ── ANSI colors ──
GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
BOLD = "\033[1m"; RESET = "\033[0m"; GRAY = "\033[90m"

FPS = 30


# ── DaVinci Connection ─────────────────────────────────────────────────────

def connect_resolve():
    """Connect to DaVinci Resolve and return (resolve, project, timeline)."""
    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        if not resolve:
            print(f"{RED}ERROR: Cannot connect to DaVinci Resolve. Is it running?{RESET}")
            return None, None, None
        project = resolve.GetProjectManager().GetCurrentProject()
        if not project:
            print(f"{RED}ERROR: No project open in DaVinci Resolve{RESET}")
            return None, None, None
        timeline = project.GetCurrentTimeline()
        if not timeline:
            print(f"{RED}ERROR: No timeline selected in DaVinci Resolve{RESET}")
            return None, None, None
        return resolve, project, timeline
    except Exception as e:
        print(f"{RED}ERROR: {e}{RESET}")
        return None, None, None


# ── Read Timeline ──────────────────────────────────────────────────────────

def _safe_str(val):
    """Safely convert DaVinci API return values to Python str."""
    if val is None:
        return ""
    if isinstance(val, bytes):
        return val.decode('utf-8', errors='replace')
    return str(val)


def read_davinci_timeline(timeline):
    """Connect to DaVinci, extract full timeline state (all tracks, clip names,
    positions, durations).

    Returns:
        dict with keys: name, duration, fps, tracks (keyed by V1..Vn, A1..An),
        each track containing: name, enabled, clips list.
    """
    tl_start = timeline.GetStartFrame()

    state = {
        "name": _safe_str(timeline.GetName()),
        "duration": (timeline.GetEndFrame() - tl_start) / FPS,
        "fps": FPS,
        "tl_start_frame": tl_start,
        "tracks": {},
    }

    for track_type, label in [("video", "V"), ("audio", "A")]:
        count = timeline.GetTrackCount(track_type)
        for t in range(1, count + 1):
            clips_raw = timeline.GetItemListInTrack(track_type, t) or []
            track_name = _safe_str(timeline.GetTrackName(track_type, t))
            track_key = f"{label}{t}"

            clip_list = []
            for c in clips_raw:
                clip_start = (c.GetStart() - tl_start) / FPS
                clip_end = (c.GetEnd() - tl_start) / FPS
                clip_list.append({
                    "name": _safe_str(c.GetName()),
                    "start": round(clip_start, 3),
                    "end": round(clip_end, 3),
                    "duration": round(clip_end - clip_start, 3),
                    "muted": c.GetProperty("Volume") == 0 if track_type == "video" else False,
                    "_item": c,  # keep reference for fixes
                })

            state["tracks"][track_key] = {
                "name": track_name,
                "enabled": timeline.GetIsTrackEnabled(track_type, t),
                "clips": clip_list,
            }

    return state


# ── Load Director Decisions ────────────────────────────────────────────────

def _sanitize_strings(obj):
    """Replace non-ASCII chars in all strings to avoid DaVinci IPC encoding errors."""
    if isinstance(obj, str):
        return obj.encode('ascii', errors='replace').decode('ascii')
    elif isinstance(obj, dict):
        return {k: _sanitize_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_strings(v) for v in obj]
    return obj


def load_director_decisions(path):
    """Load the v3 director output JSON. Returns (raw_data, flat_segments)."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    data = _sanitize_strings(data)

    segments = []
    if "scenes" in data:
        for scene in data["scenes"]:
            segments.extend(scene.get("segments", []))
    else:
        segments = data.get("segments", [])

    return data, segments


# ── Compute Segment Timing ────────────────────────────────────────────────

def _compute_timing(segments):
    """Map each director segment to expected timeline position.

    Uses _timeline_start_sec / _timeline_end_sec from the director JSON
    directly — these come from Whisper alignment (exact word timestamps).
    Falls back to word-count estimation only if alignment data is missing.
    """
    total_words = sum(
        len(s.get("text", s.get("narration", "")).split()) for s in segments
    )
    if total_words == 0:
        return []

    # Check for pre-computed timing from Whisper alignment
    has_timing = segments[0].get("_timeline_start_sec") is not None

    timings = []
    cumulative_words = 0

    if not has_timing:
        # Estimate total duration at ~150 WPM
        narr_dur = total_words / 2.5

    for i, seg in enumerate(segments):
        text = seg.get("text", seg.get("narration", ""))
        words = len(text.split())

        if has_timing:
            # Use Whisper-aligned timestamps directly — no scaling, no offset
            start = seg.get("_timeline_start_sec", 0)
            end = seg.get("_timeline_end_sec", start + words / 2.5)
        else:
            start = (cumulative_words / total_words) * narr_dur
            cumulative_words += words
            end = (cumulative_words / total_words) * narr_dur

        timings.append({
            "seg_idx": i,
            "start": round(start, 2),
            "end": round(end, 2),
        })

    return timings


# ── Compare ────────────────────────────────────────────────────────────────

def compare(timeline_state, decisions):
    """For each segment, check whether the builder executed the director's
    decisions correctly. Returns a list of mismatch dicts.

    Checks per segment:
      - Is the right visual_file on V1 at the expected position?
      - Is clip audio muted/playing per the decision?
      - Is the SFX placed at the right time?
      - Is the text overlay present?
      - Is the chapter card at the right position?
    """
    timings = _compute_timing(decisions)
    mismatches = []

    v1_clips = timeline_state["tracks"].get("V1", {}).get("clips", [])
    v2_clips = timeline_state["tracks"].get("V2", {}).get("clips", [])
    v3_clips = timeline_state["tracks"].get("V3", {}).get("clips", [])
    v4_clips = timeline_state["tracks"].get("V4", {}).get("clips", [])

    # SFX on A3/A4/A5
    sfx_clips = []
    for tk in ("A3", "A4", "A5"):
        sfx_clips.extend(timeline_state["tracks"].get(tk, {}).get("clips", []))
    sfx_positions = {round(c["start"]): c for c in sfx_clips}

    for i, seg in enumerate(decisions):
        if i >= len(timings):
            break

        t = timings[i]
        seg_mid = (t["start"] + t["end"]) / 2
        seg_issues = []

        # ── Visual file on V1 ──
        expected_visual = seg.get("visual_file")
        if expected_visual:
            # Find V1 clip covering this segment's midpoint
            covering = [
                c for c in v1_clips if c["start"] <= seg_mid <= c["end"]
            ]
            if not covering:
                seg_issues.append({
                    "check": "visual_file",
                    "expected": expected_visual,
                    "actual": "NO_CLIP",
                    "time": seg_mid,
                    "severity": "FAIL",
                    "message": f"No V1 clip at {seg_mid:.1f}s — expected '{expected_visual}'",
                })
            else:
                actual_name = covering[0]["name"]
                # Compare base name (strip extension for fuzzy match)
                exp_base = os.path.splitext(expected_visual)[0].lower()
                act_base = os.path.splitext(actual_name)[0].lower()
                if exp_base not in act_base and act_base not in exp_base:
                    seg_issues.append({
                        "check": "visual_file",
                        "expected": expected_visual,
                        "actual": actual_name,
                        "time": seg_mid,
                        "severity": "WARN",
                        "message": (
                            f"V1 @ {seg_mid:.1f}s shows '{actual_name}' "
                            f"but director wants '{expected_visual}'"
                        ),
                    })

        # ── Clip audio mute check ──
        clip_audio_rule = seg.get("clip_audio", "mute")
        if expected_visual and clip_audio_rule == "mute":
            covering = [
                c for c in v1_clips if c["start"] <= seg_mid <= c["end"]
            ]
            if covering and not covering[0].get("muted", False):
                seg_issues.append({
                    "check": "clip_audio",
                    "expected": "muted",
                    "actual": "playing",
                    "time": seg_mid,
                    "severity": "WARN",
                    "message": f"V1 clip audio playing at {seg_mid:.1f}s but should be muted",
                })
        elif expected_visual and clip_audio_rule in ("play", "play_then_mute"):
            covering = [
                c for c in v1_clips if c["start"] <= seg_mid <= c["end"]
            ]
            if covering and covering[0].get("muted", False):
                seg_issues.append({
                    "check": "clip_audio",
                    "expected": "playing",
                    "actual": "muted",
                    "time": seg_mid,
                    "severity": "WARN",
                    "message": f"V1 clip audio muted at {seg_mid:.1f}s but should play",
                })

        # ── SFX placement ──
        sfx_spec = seg.get("sfx") or {}
        sfx_file = sfx_spec.get("file") if isinstance(sfx_spec, dict) else None
        if sfx_file:
            expected_time = round(t["start"])
            found = any(abs(pos - expected_time) < 10 for pos in sfx_positions)
            if not found:
                seg_issues.append({
                    "check": "sfx",
                    "expected": sfx_file,
                    "actual": "MISSING",
                    "time": t["start"],
                    "severity": "WARN",
                    "message": (
                        f"SFX '{sfx_file}' expected near {t['start']:.1f}s "
                        f"({sfx_spec.get('motivation', '')}), not found on A3/A4/A5"
                    ),
                })

        # ── Text overlay ──
        text_overlay = seg.get("text_overlay")
        if text_overlay:
            text_style = seg.get("text_style", "static")
            target_track = v4_clips if text_style == "typewriter" else v2_clips
            track_label = "V4" if text_style == "typewriter" else "V2"

            near_overlay = any(
                abs(c["start"] - t["start"]) < 30 for c in target_track
            )
            if not near_overlay:
                seg_issues.append({
                    "check": "text_overlay",
                    "expected": text_overlay,
                    "actual": "MISSING",
                    "time": t["start"],
                    "severity": "WARN",
                    "message": (
                        f"Text overlay '{text_overlay[:40]}' expected on {track_label} "
                        f"near {t['start']:.1f}s, not found"
                    ),
                })

        # ── Chapter card ──
        chapter_title = seg.get("chapter_card")
        if chapter_title:
            expected_pos = t["start"] - 2  # cards placed 2s before segment
            near_chapter = any(
                abs(c["start"] - expected_pos) < 10
                for c in v3_clips
                if "chapter" in c["name"].lower()
            )
            if not near_chapter:
                seg_issues.append({
                    "check": "chapter_card",
                    "expected": chapter_title,
                    "actual": "MISSING",
                    "time": expected_pos,
                    "severity": "WARN",
                    "message": (
                        f"Chapter card '{chapter_title}' expected on V3 near "
                        f"{expected_pos:.1f}s, not found"
                    ),
                })

        if seg_issues:
            mismatches.append({
                "segment": i,
                "text_preview": seg.get("text", "")[:60],
                "issues": seg_issues,
            })

    return mismatches


# ── Generate Fix Instructions ──────────────────────────────────────────────

def generate_fix_instructions(mismatches):
    """Output specific fix commands as human-readable strings and structured
    dicts suitable for apply_fixes().

    Example output:
      "DELETE V1 clip at 340s and REPLACE with data_brokers_clip.mp4"
      "ADD tension_boosted.wav to A3 at 278s"
      "MOVE seg_04_mary_louis overlay from 125s to 62s"
    """
    fixes = []

    for mm in mismatches:
        seg_idx = mm["segment"]
        for issue in mm["issues"]:
            check = issue["check"]
            time = issue.get("time", 0)

            if check == "visual_file":
                if issue["actual"] == "NO_CLIP":
                    fixes.append({
                        "action": "INSERT",
                        "track": "V1",
                        "time": time,
                        "file": issue["expected"],
                        "segment": seg_idx,
                        "instruction": (
                            f"INSERT {issue['expected']} on V1 at {time:.0f}s "
                            f"(seg {seg_idx} has no coverage)"
                        ),
                    })
                else:
                    fixes.append({
                        "action": "REPLACE",
                        "track": "V1",
                        "time": time,
                        "file": issue["expected"],
                        "old_file": issue["actual"],
                        "segment": seg_idx,
                        "instruction": (
                            f"DELETE V1 clip at {time:.0f}s and REPLACE "
                            f"with {issue['expected']}"
                        ),
                    })

            elif check == "clip_audio":
                action = "MUTE" if issue["expected"] == "muted" else "UNMUTE"
                fixes.append({
                    "action": action,
                    "track": "V1",
                    "time": time,
                    "segment": seg_idx,
                    "instruction": f"{action} V1 clip audio at {time:.0f}s",
                })

            elif check == "sfx":
                fixes.append({
                    "action": "ADD",
                    "track": "A3",
                    "time": time,
                    "file": issue["expected"],
                    "segment": seg_idx,
                    "instruction": (
                        f"ADD {issue['expected']} to A3 at {time:.0f}s"
                    ),
                })

            elif check == "text_overlay":
                fixes.append({
                    "action": "ADD",
                    "track": "V2",
                    "time": time,
                    "text": issue["expected"],
                    "segment": seg_idx,
                    "instruction": (
                        f"ADD text overlay '{issue['expected'][:30]}' "
                        f"to V2/V4 at {time:.0f}s"
                    ),
                })

            elif check == "chapter_card":
                fixes.append({
                    "action": "ADD",
                    "track": "V3",
                    "time": time,
                    "text": issue["expected"],
                    "segment": seg_idx,
                    "instruction": (
                        f"ADD chapter card '{issue['expected']}' "
                        f"to V3 at {time:.0f}s"
                    ),
                })

    return fixes


# ── Apply Fixes ────────────────────────────────────────────────────────────

def apply_fixes(timeline, timeline_state, fixes):
    """Attempt to auto-fix via DaVinci API where possible.

    Supports:
      - MUTE/UNMUTE: set clip volume to 0 or 1
      - DELETE: remove misplaced clips (V1 only)

    Returns (applied, skipped) counts.
    """
    applied = 0
    skipped = 0
    tl_start = timeline.GetStartFrame()

    for fix in fixes:
        action = fix["action"]
        track = fix.get("track", "V1")
        time_sec = fix.get("time", 0)

        if action in ("MUTE", "UNMUTE"):
            # Find the V1 clip at this time
            v1_items = timeline.GetItemListInTrack("video", 1) or []
            target = None
            for c in v1_items:
                c_start = (c.GetStart() - tl_start) / FPS
                c_end = (c.GetEnd() - tl_start) / FPS
                if c_start <= time_sec <= c_end:
                    target = c
                    break

            if target:
                vol = 0 if action == "MUTE" else 1
                target.SetProperty("Volume", vol)
                print(f"  {GREEN}APPLIED{RESET}: {fix['instruction']}")
                applied += 1
            else:
                print(f"  {YELLOW}SKIPPED{RESET}: No clip found at {time_sec:.0f}s for {action}")
                skipped += 1

        elif action == "REPLACE" and track == "V1":
            # Delete the old clip. Replacement requires re-import which is
            # beyond simple API fix — flag for manual or re-run builder.
            v1_items = timeline.GetItemListInTrack("video", 1) or []
            target = None
            for c in v1_items:
                c_start = (c.GetStart() - tl_start) / FPS
                c_end = (c.GetEnd() - tl_start) / FPS
                if c_start <= time_sec <= c_end:
                    target = c
                    break

            if target:
                try:
                    timeline.DeleteClips([target])
                    print(f"  {GREEN}DELETED{RESET}: old clip at {time_sec:.0f}s — "
                          f"re-run builder to insert {fix.get('file', '?')}")
                    applied += 1
                except Exception as e:
                    print(f"  {RED}FAILED{RESET}: Could not delete clip at {time_sec:.0f}s: {e}")
                    skipped += 1
            else:
                skipped += 1

        else:
            # INSERT, ADD — these require importing media, which needs the
            # media pool and source files. Flag for re-run.
            print(f"  {YELLOW}MANUAL{RESET}: {fix['instruction']}")
            skipped += 1

    return applied, skipped


# ── Request New Footage ────────────────────────────────────────────────────

def request_new_footage(mismatches, decisions):
    """For segments where the visual doesn't match or is missing, generate a
    gap list for the research agent (web_image_sourcer / gap_resolver).

    Returns a list of dicts with segment info and search queries.
    """
    gaps = []

    for mm in mismatches:
        seg_idx = mm["segment"]
        visual_issues = [
            iss for iss in mm["issues"]
            if iss["check"] == "visual_file"
        ]
        if not visual_issues:
            continue

        seg = decisions[seg_idx] if seg_idx < len(decisions) else {}
        text = seg.get("text", seg.get("narration", ""))
        search_query = seg.get("search_query", "")

        # If no search_query in director output, generate one from narration
        if not search_query and text:
            search_query = query_claude(
                f"Generate a concise image search query (5-8 words) for "
                f"finding a documentary-style visual to accompany this "
                f"narration:\n\n\"{text[:300]}\"\n\n"
                f"Return ONLY the search query, nothing else.",
                timeout=30,
            )

        gaps.append({
            "segment": seg_idx,
            "text_preview": text[:80],
            "expected_file": visual_issues[0].get("expected", ""),
            "search_query": search_query.strip(),
            "time_sec": visual_issues[0].get("time", 0),
            "arc_position": seg.get("arc_position", ""),
        })

    return gaps


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description="Director Review — verify timeline matches director decisions"
    )
    parser.add_argument(
        "--director", required=True,
        help="Path to director v3 output JSON"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Auto-fix issues where possible via DaVinci API"
    )
    parser.add_argument(
        "--report", help="Save review report to JSON file"
    )
    parser.add_argument(
        "--gaps-out", help="Save footage gap list to JSON file"
    )
    args = parser.parse_args()

    print(f"\n{BOLD}Director Review — Post-Build Verification{RESET}")
    print("=" * 60)

    # Load director decisions
    print(f"\n  Loading director: {args.director}")
    raw_data, decisions = load_director_decisions(args.director)
    print(f"  {len(decisions)} segments")

    # Connect to DaVinci
    print(f"\n  Connecting to DaVinci Resolve...")
    resolve, project, timeline = connect_resolve()
    if not timeline:
        return 1

    print(f"  Timeline: {_safe_str(timeline.GetName())}")

    # Read timeline state
    print(f"\n  Reading timeline state...")
    state = read_davinci_timeline(timeline)
    total_clips = sum(
        len(t["clips"]) for t in state["tracks"].values()
    )
    print(f"  {total_clips} clips across {len(state['tracks'])} tracks")

    # Compare
    print(f"\n  Comparing director decisions vs timeline...")
    mismatches = compare(state, decisions)

    if not mismatches:
        print(f"\n  {GREEN}{BOLD}ALL CLEAR{RESET} — every director decision "
              f"executed correctly")
    else:
        total_issues = sum(len(mm["issues"]) for mm in mismatches)
        fail_count = sum(
            1 for mm in mismatches
            for iss in mm["issues"]
            if iss["severity"] == "FAIL"
        )
        warn_count = total_issues - fail_count

        print(f"\n  {RED if fail_count else YELLOW}"
              f"Found {total_issues} issues across {len(mismatches)} segments{RESET}")
        print(f"  FAIL: {fail_count}  WARN: {warn_count}")

        # Print details
        for mm in mismatches:
            print(f"\n  Seg {mm['segment']}: {mm['text_preview']}")
            for iss in mm["issues"]:
                color = RED if iss["severity"] == "FAIL" else YELLOW
                icon = "X" if iss["severity"] == "FAIL" else "!"
                print(f"    {color}[{icon}]{RESET} {iss['message']}")

        # Generate fix instructions
        fixes = generate_fix_instructions(mismatches)
        print(f"\n  {BOLD}Fix Instructions ({len(fixes)}):{RESET}")
        for fix in fixes:
            print(f"    -> {fix['instruction']}")

        # Apply fixes if requested
        if args.fix:
            print(f"\n  {BOLD}Applying fixes...{RESET}")
            applied, skipped = apply_fixes(timeline, state, fixes)
            print(f"\n  Applied: {applied}, Skipped/Manual: {skipped}")

        # Generate gap list for new footage
        gaps = request_new_footage(mismatches, decisions)
        if gaps:
            print(f"\n  {BOLD}Footage Gaps ({len(gaps)}):{RESET}")
            for g in gaps:
                print(f"    Seg {g['segment']}: \"{g['search_query']}\"")

            if args.gaps_out:
                with open(args.gaps_out, "w") as f:
                    json.dump(gaps, f, indent=2)
                print(f"\n  Gap list saved: {args.gaps_out}")

    # Save report
    if args.report:
        # Strip _item references (not serializable)
        clean_state = json.loads(json.dumps(state, default=str))
        report = {
            "timeline": state["name"],
            "duration": state["duration"],
            "director_segments": len(decisions),
            "mismatches": len(mismatches),
            "total_issues": sum(len(mm["issues"]) for mm in mismatches),
            "details": mismatches,
            "fixes": generate_fix_instructions(mismatches) if mismatches else [],
        }
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Report saved: {args.report}")

    # Verdict
    fail_count = sum(
        1 for mm in mismatches
        for iss in mm["issues"]
        if iss["severity"] == "FAIL"
    )
    if fail_count:
        print(f"\n  {RED}{BOLD}VERDICT: {fail_count} critical mismatches — "
              f"re-run builder or fix manually{RESET}")
    elif mismatches:
        print(f"\n  {YELLOW}{BOLD}VERDICT: Acceptable with warnings{RESET}")
    else:
        print(f"\n  {GREEN}{BOLD}VERDICT: Timeline matches director perfectly{RESET}")

    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
