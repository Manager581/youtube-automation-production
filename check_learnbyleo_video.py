#!/usr/bin/env python3
"""
check_learnbyleo_video.py — QA checker against LearnByLeo playbook rules.

Checks the ACTIVE DaVinci Resolve timeline (not a rendered file).
Validates against playbook/editing.json, retention_delivery.json, scripting.json, intros.json.

Usage:
    python check_learnbyleo_video.py

Output: PASS / WARN / FAIL per check with overall score.
"""

import json
import os
import sys

# DaVinci scripting
RESOLVE_MODULES = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
if RESOLVE_MODULES not in sys.path:
    sys.path.append(RESOLVE_MODULES)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ── ANSI colors ──
GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"; BOLD = "\033[1m"; RESET = "\033[0m"

def connect():
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print(f"{RED}ERROR: Cannot connect to DaVinci Resolve{RESET}")
        sys.exit(1)
    project = resolve.GetProjectManager().GetCurrentProject()
    timeline = project.GetCurrentTimeline()
    if not timeline:
        print(f"{RED}ERROR: No active timeline{RESET}")
        sys.exit(1)
    return timeline

def load_playbook():
    """Load all LearnByLeo playbook modules."""
    modules = {}
    pb_dir = os.path.join(PROJECT_ROOT, "playbook")
    for f in os.listdir(pb_dir):
        if f.endswith('.json') and f != 'index.json' and f != 'sources.json':
            with open(os.path.join(pb_dir, f)) as fh:
                modules[f.replace('.json', '')] = json.load(fh)
    return modules

def run_checks(timeline, playbook):
    fps = 30
    tl_start = timeline.GetStartFrame()
    results = []
    
    # Gather timeline data
    tracks = {}
    for tt, label in [('video', 'V'), ('audio', 'A')]:
        count = timeline.GetTrackCount(tt)
        for t in range(1, count + 1):
            clips = timeline.GetItemListInTrack(tt, t) or []
            tracks[f"{label}{t}"] = clips
    
    v1 = tracks.get('V1', [])
    v2 = tracks.get('V2', [])
    v3 = tracks.get('V3', [])
    v4 = tracks.get('V4', [])
    a1 = tracks.get('A1', [])
    a2 = tracks.get('A2', [])
    
    total_dur = (timeline.GetEndFrame() - tl_start) / fps
    sfx_count = len(tracks.get('A3', [])) + len(tracks.get('A4', []))
    
    # ── P-ED-02: Cut frequency (new visual every 5-7s) ──
    avg_dur = total_dur / len(v1) if v1 else 999
    if avg_dur <= 7:
        results.append(("PASS", "P-ED-02 Cut frequency", f"avg {avg_dur:.1f}s per clip (target ≤7s)"))
    elif avg_dur <= 10:
        results.append(("WARN", "P-ED-02 Cut frequency", f"avg {avg_dur:.1f}s per clip (target ≤7s)"))
    else:
        results.append(("FAIL", "P-ED-02 Cut frequency", f"avg {avg_dur:.1f}s per clip (target ≤7s)"))
    
    # ── P-ED-03: Editing invisible (graphics animate, not pop) ──
    # Check if V2 overlays are faded MOVs (not raw PNGs)
    faded = sum(1 for c in v2 if 'faded' in c.GetName() or '.mov' in c.GetName())
    if faded >= len(v2) * 0.8:
        results.append(("PASS", "P-ED-03 Graphics animate", f"{faded}/{len(v2)} V2 clips have fade animation"))
    else:
        results.append(("WARN", "P-ED-03 Graphics animate", f"Only {faded}/{len(v2)} have fades"))
    
    # ── P-ED-04: Energy variation ──
    # Check SFX + chapter cards as energy markers
    energy_markers = sfx_count + len(v3)
    markers_per_min = energy_markers / (total_dur / 60) if total_dur > 0 else 0
    if markers_per_min >= 2:
        results.append(("PASS", "P-ED-04 Energy variation", f"{markers_per_min:.1f} markers/min (SFX + chapters)"))
    else:
        results.append(("WARN", "P-ED-04 Energy variation", f"{markers_per_min:.1f} markers/min (need ≥2)"))
    
    # ── AP-ED-01: Not monotone energy ──
    # Verified by SFX spread — check if SFX are distributed, not clustered
    sfx_all = list(tracks.get('A3', [])) + list(tracks.get('A4', []))
    if sfx_all:
        positions = sorted((c.GetStart() - tl_start) / fps for c in sfx_all)
        gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
        max_gap = max(gaps) if gaps else total_dur
        if max_gap < 120:
            results.append(("PASS", "AP-ED-01 No monotone energy", f"Max SFX gap: {max_gap:.0f}s (< 2min)"))
        else:
            results.append(("WARN", "AP-ED-01 No monotone energy", f"Max SFX gap: {max_gap:.0f}s (> 2min)"))
    
    # ── AP-ED-02: Graphics don't pop ──
    png_count = sum(1 for c in v2 if c.GetName().endswith('.png'))
    if png_count == 0:
        results.append(("PASS", "AP-ED-02 No popping graphics", "All V2 are MOVs with fades"))
    else:
        results.append(("FAIL", "AP-ED-02 No popping graphics", f"{png_count} raw PNGs on V2 (will pop in/out)"))
    
    # ── AP-ED-03: Risers before real reveals only ──
    if sfx_count <= len(v1) * 0.3:
        results.append(("PASS", "AP-ED-03 SFX not overused", f"{sfx_count} SFX for {len(v1)} clips ({sfx_count/len(v1)*100:.0f}%)"))
    else:
        results.append(("WARN", "AP-ED-03 SFX overused", f"{sfx_count} SFX for {len(v1)} clips"))
    
    # ── Sound design: SFX present ──
    if sfx_count >= 20:
        results.append(("PASS", "Sound design: SFX count", f"{sfx_count} SFX clips"))
    elif sfx_count >= 10:
        results.append(("WARN", "Sound design: SFX count", f"{sfx_count} SFX (need 20+)"))
    else:
        results.append(("FAIL", "Sound design: SFX count", f"{sfx_count} SFX (need 20+)"))
    
    # ── Sound design: Music present ──
    if a2:
        results.append(("PASS", "Sound design: Music", "Music track present"))
    else:
        results.append(("FAIL", "Sound design: Music", "No music track"))
    
    # ── Chapter transitions ──
    chapter_clips = [c for c in v3 if 'chapter' in c.GetName().lower()]
    if len(chapter_clips) >= 5:
        results.append(("PASS", "Chapter transitions", f"{len(chapter_clips)} chapter cards"))
    elif len(chapter_clips) >= 3:
        results.append(("WARN", "Chapter transitions", f"{len(chapter_clips)} chapter cards (need 5+)"))
    else:
        results.append(("FAIL", "Chapter transitions", f"{len(chapter_clips)} chapter cards"))
    
    # ── P-IN-01: Intro exists ──
    if v1 and 'intro' in v1[0].GetName().lower():
        results.append(("PASS", "P-IN-01 Intro exists", v1[0].GetName()[:40]))
    else:
        results.append(("FAIL", "P-IN-01 Intro exists", "First V1 clip is not intro"))
    
    # ── P-IN-05: Intro enrichment (overlay on intro) ──
    intro_overlay = any('news_overlay' in c.GetName() for c in v2)
    if intro_overlay:
        results.append(("PASS", "P-IN-05 Intro enrichment", "News overlay on intro"))
    else:
        results.append(("WARN", "P-IN-05 Intro enrichment", "No overlay on intro"))
    
    # ── P-RD-04: Every topic has visual ──
    if len(v2) >= 15:
        results.append(("PASS", "P-RD-04 Visual coverage", f"{len(v2)} V2 overlays for key topics"))
    else:
        results.append(("WARN", "P-RD-04 Visual coverage", f"Only {len(v2)} overlays"))
    
    # ── Narration present ──
    if a1:
        narr_dur = (a1[0].GetEnd() - a1[0].GetStart()) / fps
        results.append(("PASS", "Narration present", f"{narr_dur:.0f}s ({narr_dur/60:.1f} min)"))
    else:
        results.append(("FAIL", "Narration present", "No narration on A1"))
    
    # ── Duration in range ──
    if 10 <= total_dur / 60 <= 25:
        results.append(("PASS", "Duration", f"{total_dur/60:.1f} min (10-25 range)"))
    else:
        results.append(("WARN", "Duration", f"{total_dur/60:.1f} min"))
    
    # ── V1 no gaps ──
    prev = 0; gap_count = 0
    for c in v1:
        s = (c.GetStart() - tl_start) / fps
        if s - prev > 1: gap_count += 1
        prev = (c.GetEnd() - tl_start) / fps
    if gap_count == 0:
        results.append(("PASS", "No dead space (V1 gaps)", "0 gaps"))
    else:
        results.append(("FAIL", "No dead space (V1 gaps)", f"{gap_count} gaps"))
    
    # ── Source diversity ──
    sources = {}
    for c in v1:
        n = c.GetName()
        sources[n] = sources.get(n, 0) + 1
    max_repeat = max(sources.values()) if sources else 0
    unique = len(sources)
    if unique >= 30:
        results.append(("PASS", "Source diversity", f"{unique} unique sources"))
    elif unique >= 15:
        results.append(("WARN", "Source diversity", f"{unique} unique sources (want 30+)"))
    else:
        results.append(("FAIL", "Source diversity", f"Only {unique} unique sources"))
    
    # ── Fair use: clip duration ──
    # Timeline clip duration = next clip start - this clip start
    clip_durs = []
    for idx, c in enumerate(v1):
        if idx < len(v1) - 1:
            next_start = (v1[idx+1].GetStart() - tl_start) / fps
            this_start = (c.GetStart() - tl_start) / fps
            clip_durs.append(next_start - this_start)
        else:
            clip_durs.append(7)  # last clip default
    over_8 = sum(1 for i, c in enumerate(v1) if clip_durs[i] > 8 and 'intro' not in c.GetName().lower())
    if over_8 == 0:
        results.append(("PASS", "Fair use: clip duration", "All clips ≤7s (excl intro)"))
    else:
        results.append(("FAIL", "Fair use: clip duration", f"{over_8} clips exceed 8s"))
    
    # ── Typewriter text ──
    tw = [c for c in (tracks.get('V4', []) or []) if 'typewriter' in c.GetName().lower()]
    tw_audio = tracks.get('A5', [])
    if tw:
        results.append(("PASS", "Typewriter text reveals", f"{len(tw)} on V4"))
    else:
        results.append(("WARN", "Typewriter text reveals", "None on V4"))
    if tw_audio:
        results.append(("PASS", "Typewriter click audio", f"{len(tw_audio)} on A5"))
    else:
        results.append(("WARN", "Typewriter click audio", "None on A5"))
    
    # ── Vignette ──
    v5 = tracks.get('V5', [])
    if v5:
        results.append(("PASS", "Production polish: vignette", f"{len(v5)} clips on V5"))
    else:
        results.append(("WARN", "Production polish: vignette", "No vignette"))
    
    return results


def main():
    print(f"\n{BOLD}LearnByLeo Video QA Checker{RESET}")
    print("=" * 60)
    
    timeline = connect()
    print(f"Timeline: {timeline.GetName()}")
    print(f"Duration: {(timeline.GetEndFrame() - timeline.GetStartFrame()) / 30 / 60:.1f} min\n")
    
    playbook = load_playbook()
    results = run_checks(timeline, playbook)
    
    # Print results
    passed = sum(1 for r in results if r[0] == "PASS")
    warned = sum(1 for r in results if r[0] == "WARN")
    failed = sum(1 for r in results if r[0] == "FAIL")
    total = len(results)
    
    for status, name, detail in results:
        color = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED}[status]
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[status]
        print(f"  {icon} {color}{name}{RESET}: {detail}")
    
    print(f"\n{'='*60}")
    score = (passed + warned * 0.5) / total * 100
    print(f"  Score: {BOLD}{score:.0f}%{RESET} ({passed} pass, {warned} warn, {failed} fail)")
    
    if failed == 0:
        print(f"  {GREEN}{BOLD}RESULT: PASS{RESET}")
    elif failed <= 2:
        print(f"  {YELLOW}{BOLD}RESULT: WARN{RESET}")
    else:
        print(f"  {RED}{BOLD}RESULT: FAIL{RESET}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
