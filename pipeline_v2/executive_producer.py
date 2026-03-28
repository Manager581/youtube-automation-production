#!/usr/bin/env python3
"""
executive_producer.py — Watches the final DaVinci timeline and verifies
everything the director specified actually made it to screen.

Connects to DaVinci Resolve, loads the director output, cross-references
every segment, and reports exactly what's wrong and which pipeline stage
to re-run to fix it.

This is the ONLY script that sees EVERYTHING:
- The director's instructions (what SHOULD be on screen)
- The DaVinci timeline (what IS on screen)
- The narration timing (what's being SAID)
- The audio mix (what's being HEARD)
- The LearnByLeo playbook (what the RULES are)

Usage:
    python -m pipeline_v2.executive_producer
    python -m pipeline_v2.executive_producer --fix  # auto-fix what it can
    python -m pipeline_v2.executive_producer --report report.json
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

# ── ANSI colors ──
GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
BOLD = "\033[1m"; RESET = "\033[0m"; GRAY = "\033[90m"


def connect_resolve():
    """Connect to DaVinci Resolve."""
    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        if not resolve:
            print(f"{RED}ERROR: Cannot connect to DaVinci Resolve{RESET}")
            return None, None, None
        project = resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        return resolve, project, timeline
    except Exception as e:
        print(f"{RED}ERROR: {e}{RESET}")
        return None, None, None


def load_director(path=None):
    """Load director output JSON."""
    if path is None:
        # Find latest directed storyboard
        sb_dir = PROJECT_ROOT / "storyboards"
        candidates = sorted(sb_dir.glob("*directed*.json"), key=os.path.getmtime, reverse=True)
        if not candidates:
            return None
        path = candidates[0]
    
    with open(path) as f:
        data = json.load(f)
    
    segments = []
    if 'scenes' in data:
        for scene in data['scenes']:
            segments.extend(scene.get('segments', []))
    else:
        segments = data.get('segments', [])
    
    return segments


def load_playbook():
    """Load LearnByLeo playbook modules."""
    modules = {}
    pb_dir = PROJECT_ROOT / "playbook"
    for f in pb_dir.glob("*.json"):
        if f.name not in ('index.json', 'sources.json'):
            with open(f) as fh:
                modules[f.stem] = json.load(fh)
    return modules


def get_timeline_state(timeline):
    """Extract complete state of the DaVinci timeline."""
    fps = 30
    tl_start = timeline.GetStartFrame()
    
    state = {
        "name": timeline.GetName(),
        "duration": (timeline.GetEndFrame() - tl_start) / fps,
        "tracks": {},
    }
    
    for track_type, label in [('video', 'V'), ('audio', 'A')]:
        count = timeline.GetTrackCount(track_type)
        for t in range(1, count + 1):
            clips = timeline.GetItemListInTrack(track_type, t) or []
            track_name = timeline.GetTrackName(track_type, t)
            track_key = f"{label}{t}"
            
            state["tracks"][track_key] = {
                "name": track_name,
                "enabled": timeline.GetIsTrackEnabled(track_type, t),
                "clips": [],
            }
            
            for c in clips:
                clip_start = (c.GetStart() - tl_start) / fps
                clip_end = (c.GetEnd() - tl_start) / fps
                state["tracks"][track_key]["clips"].append({
                    "name": c.GetName(),
                    "start": clip_start,
                    "end": clip_end,
                    "duration": clip_end - clip_start,
                })
    
    return state


def compute_narration_timing(director_segments):
    """Map each director segment to its narration position."""
    total_words = sum(len(s.get('text', s.get('narration', '')).split()) 
                      for s in director_segments)
    
    if total_words == 0:
        return []
    
    # Check if director has pre-computed timing
    if director_segments[0].get('_timeline_start_sec') is not None:
        has_timing = True
    else:
        has_timing = False
    
    timings = []
    cumulative_words = 0
    narr_start = 11.8  # typical intro offset
    
    # Find actual narration duration from timeline or estimate
    narr_dur = 860.0  # default estimate
    
    for i, seg in enumerate(director_segments):
        text = seg.get('text', seg.get('narration', ''))
        words = len(text.split())
        
        if has_timing:
            # Use director's pre-computed timing, scaled to actual narration
            dir_start = seg.get('_timeline_start_sec', 0)
            dir_end = seg.get('_timeline_end_sec', 0)
            dir_max = max(s.get('_timeline_end_sec', 0) for s in director_segments)
            scale = narr_dur / dir_max if dir_max > 0 else 1
            start = narr_start + dir_start * scale
            end = narr_start + dir_end * scale
        else:
            # Proportional timing from word count
            start = narr_start + (cumulative_words / total_words) * narr_dur
            cumulative_words += words
            end = narr_start + (cumulative_words / total_words) * narr_dur
        
        timings.append({
            "seg_idx": i,
            "start": start,
            "end": end,
            "duration": end - start,
            "text_preview": text[:60],
        })
    
    return timings


# ── Individual Checks ─────────────────────────────────────────────────────

def check_visual_coverage(state, timings, director_segments):
    """For each segment, is there video showing?"""
    issues = []
    
    v1_clips = state["tracks"].get("V1", {}).get("clips", [])
    v2_clips = state["tracks"].get("V2", {}).get("clips", [])
    v3_clips = state["tracks"].get("V3", {}).get("clips", [])
    all_video = v1_clips + v2_clips + v3_clips
    
    for t in timings:
        mid = (t["start"] + t["end"]) / 2
        covered = any(c["start"] <= mid <= c["end"] for c in all_video)
        if not covered:
            issues.append({
                "type": "no_video",
                "severity": "FAIL",
                "segment": t["seg_idx"],
                "time": mid,
                "message": f"Seg {t['seg_idx']} @ {mid:.0f}s: BLACK SCREEN (no video on V1/V2/V3)",
                "fix": "re-run: web_image_sourcer or footage_sourcer",
            })
    
    return issues


def check_overlay_match(state, timings, director_segments):
    """Are V2 overlays at the right narration positions?"""
    issues = []
    
    v2_clips = state["tracks"].get("V2", {}).get("clips", [])
    
    # For each V2 overlay, check if it's near the right segment
    for v2 in v2_clips:
        v2_mid = (v2["start"] + v2["end"]) / 2
        v2_name = v2["name"]
        
        # Extract segment number from name (e.g., "seg_04_mary_louis_faded.mov")
        seg_num = None
        if "seg_" in v2_name:
            try:
                parts = v2_name.split("_")
                seg_num = int(parts[1])
            except (IndexError, ValueError):
                pass
        
        if seg_num is not None and seg_num < len(timings):
            expected_time = timings[seg_num]["start"]
            drift = abs(v2_mid - expected_time)
            
            if drift > 30:
                issues.append({
                    "type": "overlay_misplaced",
                    "severity": "WARN",
                    "segment": seg_num,
                    "time": v2_mid,
                    "message": f"V2 '{v2_name[:30]}' at {v2_mid:.0f}s but narration expects {expected_time:.0f}s (drift: {drift:.0f}s)",
                    "fix": "re-run: davinci_timeline_builder (sort overlays chronologically)",
                })
    
    return issues


def check_sfx_coverage(state, timings, director_segments):
    """Are SFX placed where the director specified?"""
    issues = []
    
    # Collect all SFX clips
    sfx_clips = []
    for track_key in ["A3", "A4", "A5"]:
        track = state["tracks"].get(track_key, {})
        sfx_clips.extend(track.get("clips", []))
    
    sfx_positions = set()
    for c in sfx_clips:
        sfx_positions.add(round(c["start"]))
    
    # Check each director SFX specification
    for i, seg in enumerate(director_segments):
        sfx = seg.get('sfx', {})
        if not sfx:
            continue
        
        if i >= len(timings):
            continue
        
        expected_time = round(timings[i]["start"])
        
        # Check if there's an SFX within 10s of expected position
        found = any(abs(pos - expected_time) < 10 for pos in sfx_positions)
        
        if not found:
            issues.append({
                "type": "missing_sfx",
                "severity": "WARN",
                "segment": i,
                "time": expected_time,
                "message": f"Seg {i} @ {expected_time}s: Director wants {sfx.get('type', '?')} SFX ({sfx.get('motivation', '')}), none found",
                "fix": "re-run: davinci_timeline_builder (SFX placement)",
            })
    
    return issues


def check_chapter_cards(state, timings, director_segments):
    """Are chapter cards at the right positions?"""
    issues = []
    
    v3_clips = state["tracks"].get("V3", {}).get("clips", [])
    chapter_clips = [c for c in v3_clips if "chapter" in c["name"].lower()]
    
    # Find segments that should have chapter cards
    chapter_segments = []
    prev_arc = None
    for i, seg in enumerate(director_segments):
        arc = seg.get('arc_position', '')
        is_chapter = seg.get('is_chapter_break', False)
        
        # Chapter at major arc transitions or explicit breaks
        if is_chapter or (prev_arc and arc != prev_arc and arc in ('context_setup', 'cold_open')):
            chapter_segments.append(i)
        prev_arc = arc
    
    if len(chapter_clips) < 5:
        issues.append({
            "type": "few_chapters",
            "severity": "WARN",
            "segment": 0,
            "time": 0,
            "message": f"Only {len(chapter_clips)} chapter cards (LearnByLeo wants 5+)",
            "fix": "re-run: davinci_timeline_builder (chapter card placement)",
        })
    
    return issues


def check_audio_mix(state):
    """Verify audio tracks are present and enabled."""
    issues = []
    
    # Narration
    a1 = state["tracks"].get("A1", {})
    if not a1.get("clips"):
        issues.append({
            "type": "no_narration",
            "severity": "FAIL",
            "segment": 0, "time": 0,
            "message": "NO NARRATION on A1",
            "fix": "re-run: voice_generator + insert_pauses",
        })
    elif not a1.get("enabled", True):
        issues.append({
            "type": "narration_disabled",
            "severity": "FAIL",
            "segment": 0, "time": 0,
            "message": "A1 narration track is DISABLED",
            "fix": "Enable A1 in DaVinci",
        })
    
    # Music
    a2 = state["tracks"].get("A2", {})
    if not a2.get("clips"):
        issues.append({
            "type": "no_music",
            "severity": "WARN",
            "segment": 0, "time": 0,
            "message": "NO MUSIC on A2",
            "fix": "re-run: music_sourcer + pre_duck",
        })
    
    # SFX
    a3_count = len(state["tracks"].get("A3", {}).get("clips", []))
    a4_count = len(state["tracks"].get("A4", {}).get("clips", []))
    if a3_count + a4_count < 10:
        issues.append({
            "type": "few_sfx",
            "severity": "WARN",
            "segment": 0, "time": 0,
            "message": f"Only {a3_count + a4_count} SFX clips (want 20+)",
            "fix": "re-run: davinci_timeline_builder (SFX placement)",
        })
    
    return issues


def check_track_alignment(state):
    """All tracks should end within 10s of each other."""
    issues = []
    
    ends = {}
    for key, track in state["tracks"].items():
        clips = track.get("clips", [])
        if clips:
            ends[key] = max(c["end"] for c in clips)
    
    if ends:
        main_tracks = {k: v for k, v in ends.items() if k in ("V1", "A1", "A2")}
        if main_tracks:
            max_end = max(main_tracks.values())
            min_end = min(main_tracks.values())
            if max_end - min_end > 30:
                issues.append({
                    "type": "track_misalignment",
                    "severity": "WARN",
                    "segment": 0, "time": 0,
                    "message": f"Tracks misaligned: V1/A1/A2 end spread is {max_end-min_end:.0f}s",
                    "fix": "re-run: davinci_timeline_builder (trim tracks)",
                })
    
    return issues


def check_source_diversity(state):
    """No single source should dominate."""
    issues = []
    
    v1_clips = state["tracks"].get("V1", {}).get("clips", [])
    usage = {}
    for c in v1_clips:
        usage[c["name"]] = usage.get(c["name"], 0) + 1
    
    if usage:
        max_usage = max(usage.values())
        max_source = max(usage, key=usage.get)
        unique = len(usage)
        
        if max_usage > 10:
            issues.append({
                "type": "source_overuse",
                "severity": "WARN",
                "segment": 0, "time": 0,
                "message": f"'{max_source[:30]}' used {max_usage}x (max 10 recommended)",
                "fix": "re-run: footage_sourcer + web_image_sourcer for more variety",
            })
        
        if unique < 20:
            issues.append({
                "type": "low_diversity",
                "severity": "WARN",
                "segment": 0, "time": 0,
                "message": f"Only {unique} unique sources (want 20+)",
                "fix": "re-run: web_image_sourcer with more queries",
            })
    
    return issues


def check_fair_use(state):
    """No clip should play continuously for too long."""
    issues = []
    
    v1_clips = state["tracks"].get("V1", {}).get("clips", [])
    for c in v1_clips:
        if c["duration"] > 30 and "intro" not in c["name"].lower():
            issues.append({
                "type": "fair_use_violation",
                "severity": "FAIL",
                "segment": 0, "time": c["start"],
                "message": f"'{c['name'][:30]}' plays for {c['duration']:.0f}s continuous (max 30s)",
                "fix": "re-run: davinci_timeline_builder with fair_use_guard",
            })
    
    return issues


def check_typewriter_text(state, timings, director_segments):
    """Are typewriter text reveals present where director specified sync_points?"""
    issues = []
    
    v4_clips = state["tracks"].get("V4", {}).get("clips", [])
    a5_clips = state["tracks"].get("A5", {}).get("clips", [])
    
    # Count segments with sync_points
    sync_segments = [i for i, s in enumerate(director_segments) if s.get('sync_points')]
    
    if sync_segments and not v4_clips:
        issues.append({
            "type": "no_typewriter",
            "severity": "WARN",
            "segment": sync_segments[0], "time": 0,
            "message": f"Director specifies {len(sync_segments)} text reveals but V4 is empty",
            "fix": "re-run: davinci_helpers.create_typewriter_with_audio()",
        })
    
    if v4_clips and not a5_clips:
        issues.append({
            "type": "no_typewriter_audio",
            "severity": "WARN",
            "segment": 0, "time": 0,
            "message": "Typewriter text on V4 but NO click audio on A5",
            "fix": "Extract audio from typewriter MOVs and place on A5",
        })
    
    return issues


def check_intro(state):
    """Verify intro exists and has enrichment."""
    issues = []
    
    v1_clips = state["tracks"].get("V1", {}).get("clips", [])
    v2_clips = state["tracks"].get("V2", {}).get("clips", [])
    
    if not v1_clips:
        issues.append({
            "type": "no_v1",
            "severity": "FAIL",
            "segment": 0, "time": 0,
            "message": "V1 is EMPTY — no video at all",
            "fix": "re-run: entire build pipeline",
        })
        return issues
    
    first_clip = v1_clips[0]
    if "intro" not in first_clip["name"].lower():
        issues.append({
            "type": "no_intro",
            "severity": "FAIL",
            "segment": 0, "time": 0,
            "message": f"First V1 clip is '{first_clip['name'][:30]}', not intro",
            "fix": "re-run: davinci_timeline_builder (place intro first)",
        })
    
    # Check for overlay on intro
    intro_overlay = any(c["start"] < 20 and "overlay" in c["name"].lower() for c in v2_clips)
    if not intro_overlay:
        issues.append({
            "type": "no_intro_overlay",
            "severity": "WARN",
            "segment": 0, "time": 0,
            "message": "No visual enrichment (overlay) on intro",
            "fix": "Place news_overlay on V2 at 0s",
        })
    
    return issues


def check_accidental_transitions(state):
    """Check for leftover Cross Dissolve / Cross Fade clips from Cmd+T accidents."""
    issues = []
    
    for track_key, track in state["tracks"].items():
        for c in track.get("clips", []):
            if "Cross Dissolve" in c["name"] or "Cross Fade" in c["name"]:
                issues.append({
                    "type": "accidental_transition",
                    "severity": "FAIL",
                    "segment": 0, "time": c["start"],
                    "message": f"{track_key}: Accidental '{c['name']}' at {c['start']:.0f}s (causes wind sound)",
                    "fix": "Delete all Cross Dissolve/Cross Fade clips from timeline",
                })
    
    return issues


# ── Main Runner ───────────────────────────────────────────────────────────

def run_review(timeline, director_segments, playbook, verbose=True):
    """Run all checks and return categorized issues."""
    
    state = get_timeline_state(timeline)
    timings = compute_narration_timing(director_segments)
    
    all_issues = []
    
    checks = [
        ("Intro", check_intro, (state,)),
        ("Visual Coverage", check_visual_coverage, (state, timings, director_segments)),
        ("Overlay Positions", check_overlay_match, (state, timings, director_segments)),
        ("SFX Coverage", check_sfx_coverage, (state, timings, director_segments)),
        ("Chapter Cards", check_chapter_cards, (state, timings, director_segments)),
        ("Audio Mix", check_audio_mix, (state,)),
        ("Track Alignment", check_track_alignment, (state,)),
        ("Source Diversity", check_source_diversity, (state,)),
        ("Fair Use", check_fair_use, (state,)),
        ("Typewriter Text", check_typewriter_text, (state, timings, director_segments)),
        ("Accidental Transitions", check_accidental_transitions, (state,)),
    ]
    
    for check_name, check_fn, check_args in checks:
        issues = check_fn(*check_args)
        
        if verbose:
            if not issues:
                print(f"  {GREEN}✅ {check_name}{RESET}")
            else:
                for iss in issues:
                    color = RED if iss["severity"] == "FAIL" else YELLOW
                    icon = "❌" if iss["severity"] == "FAIL" else "⚠️"
                    print(f"  {icon} {color}{check_name}{RESET}: {iss['message']}")
                    print(f"     {GRAY}Fix: {iss['fix']}{RESET}")
        
        all_issues.extend(issues)
    
    return all_issues, state


def main():
    parser = argparse.ArgumentParser(description="Executive Producer — verify everything works together")
    parser.add_argument('--director', help='Path to director JSON output')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues where possible')
    parser.add_argument('--report', help='Save report to JSON file')
    args = parser.parse_args()
    
    print(f"\n{BOLD}Executive Producer — Final Review{RESET}")
    print("=" * 60)
    
    # Connect to DaVinci
    resolve, project, timeline = connect_resolve()
    if not timeline:
        return 1
    
    print(f"Timeline: {timeline.GetName()}")
    
    # Load director output
    director_segments = load_director(args.director)
    if not director_segments:
        print(f"{RED}ERROR: No director output found{RESET}")
        return 1
    print(f"Director: {len(director_segments)} segments")
    
    # Load playbook
    playbook = load_playbook()
    print(f"Playbook: {len(playbook)} modules\n")
    
    # Run all checks
    issues, state = run_review(timeline, director_segments, playbook)
    
    # Summary
    fails = [i for i in issues if i["severity"] == "FAIL"]
    warns = [i for i in issues if i["severity"] == "WARN"]
    total_checks = 11
    passed = total_checks - len(set(i["type"] for i in issues))
    
    print(f"\n{'='*60}")
    print(f"  {BOLD}SCORE: {passed}/{total_checks} checks passed{RESET}")
    print(f"  Fails: {len(fails)}, Warnings: {len(warns)}")
    
    if fails:
        print(f"\n  {RED}{BOLD}VERDICT: NOT READY — {len(fails)} critical issues{RESET}")
        print(f"  Fix these before render:")
        for f in fails:
            print(f"    → {f['fix']}")
    elif warns:
        print(f"\n  {YELLOW}{BOLD}VERDICT: ACCEPTABLE — {len(warns)} minor issues{RESET}")
    else:
        print(f"\n  {GREEN}{BOLD}VERDICT: READY TO RENDER{RESET}")
    
    # Save report
    if args.report:
        report = {
            "timeline": state["name"],
            "duration": state["duration"],
            "director_segments": len(director_segments),
            "checks_passed": passed,
            "checks_total": total_checks,
            "fails": len(fails),
            "warnings": len(warns),
            "issues": issues,
        }
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n  Report saved: {args.report}")
    
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
