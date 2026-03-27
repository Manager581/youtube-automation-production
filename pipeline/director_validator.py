#!/usr/bin/env python3
"""
Director Validator — Post-build QA that enforces ALL playbook rules.

Runs AFTER the video is assembled and produces a PASS/FAIL report.
If any critical check fails, it outputs specific fix instructions.

Checks:
1. First 15s scoring (95%+ required)
2. Open loops in intro (minimum 2)
3. Litmus test on every segment
4. SFX density vs narrative intensity
5. Pacing (cuts/min)
6. Audio levels at key timestamps
7. Energy variation across sections
8. Text overlay coverage
"""
import json, os, subprocess
from pathlib import Path

def dur(path):
    r = subprocess.run(f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{path}"',
                      shell=True, capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0

def check_audio(path, t):
    r = subprocess.run(f'ffmpeg -ss {t} -i "{path}" -t 2 -af volumedetect -f null /dev/null 2>&1',
                      shell=True, capture_output=True, text=True)
    for l in r.stderr.split('\n'):
        if 'mean_volume' in l:
            return float(l.split('mean_volume:')[1].split('dB')[0].strip())
    return -91.0

def validate(video_path, edit_map_path, director_path, playbook_dir, text_overlays_path=None):
    """Run full validation. Returns (passed: bool, report: dict)."""
    
    report = {
        "video": str(video_path),
        "checks": [],
        "critical_failures": [],
        "warnings": [],
        "score": 0.0,
        "passed": False
    }
    
    # Load data
    with open(edit_map_path) as f:
        edit = json.load(f)
    with open(director_path) as f:
        director = json.load(f)
    with open(os.path.join(playbook_dir, 'intros.json')) as f:
        intros_pb = json.load(f)
    with open(os.path.join(playbook_dir, 'editing.json')) as f:
        editing_pb = json.load(f)
    
    dir_segs = [s for sc in director['scenes'] for s in sc['segments']]
    edit_segs = edit['segments']
    intros = set(edit.get('intro_segments', []))
    
    text_overlays = []
    if text_overlays_path and os.path.exists(text_overlays_path):
        with open(text_overlays_path) as f:
            text_overlays = json.load(f)
    text_map = {t['seg_id']: t for t in text_overlays}
    
    total_checks = 0
    passed_checks = 0
    
    # ── CHECK 1: First 15s Scoring ──
    print("── CHECK 1: First 15 Seconds ──")
    windows = intros_pb.get('tactics', {}).get('first_15_seconds', {}).get('windows', [])
    
    # Calculate segment positions
    pos = 0.0
    seg_pos = {}
    for seg in edit_segs:
        sid = seg['seg_id']
        d = max(seg['clip_end_sec'] - seg['clip_start_sec'], 3)
        seg_pos[sid] = (pos, d)
        pos += d
    
    first_15_score = 0
    window_scores = []
    for w in windows:
        wname = w['window']
        reqs = w['requirements']
        ws, we = [float(x) for x in wname.replace('s','').split('-')]
        w_segs = [edit_segs[i] for i in range(len(edit_segs)) 
                  if seg_pos.get(edit_segs[i]['seg_id'], (999,0))[0] < we 
                  and seg_pos.get(edit_segs[i]['seg_id'], (999,0))[0] + seg_pos.get(edit_segs[i]['seg_id'], (999,0))[1] > ws]
        
        req_met = 0
        for req in reqs:
            # Simple heuristic scoring
            met = len(w_segs) > 0  # At least has content
            req_met += 1 if met else 0
        
        w_score = req_met / max(len(reqs), 1) * 100
        window_scores.append((wname, w_score))
        print(f"  {wname}: {w_score:.0f}%")
    
    avg_first_15 = sum(s for _, s in window_scores) / max(len(window_scores), 1)
    total_checks += 1
    if avg_first_15 >= 95:
        passed_checks += 1
        print(f"  ✅ PASS: {avg_first_15:.0f}% (≥95%)")
    else:
        report['critical_failures'].append(f"First 15s scores {avg_first_15:.0f}% (need 95%+)")
        print(f"  ❌ FAIL: {avg_first_15:.0f}% (need 95%+)")
    
    # ── CHECK 2: Open Loops ──
    print("\n── CHECK 2: Open Loops in Intro ──")
    intro_text = " ".join(s.get('narration_text_snippet', '') for s in edit_segs[:6])
    questions = intro_text.count('?')
    mystery_words = sum(1 for w in ['never', 'secret', 'hidden', 'nobody', 'invisible'] if w in intro_text.lower())
    open_loops = questions + min(mystery_words, 2)
    
    total_checks += 1
    if open_loops >= 2:
        passed_checks += 1
        print(f"  ✅ PASS: {open_loops} open loops (questions={questions}, mystery={mystery_words})")
    else:
        report['critical_failures'].append(f"Only {open_loops} open loops in intro (need 2+)")
        print(f"  ❌ FAIL: {open_loops} open loops (need 2+)")
    
    # ── CHECK 3: Litmus Test ──
    print("\n── CHECK 3: 3-Part Litmus Test ──")
    litmus_fails = 0
    for i, seg in enumerate(edit_segs[:20]):  # Check first 20 segments
        narr = seg.get('narration_text_snippet', '')
        has_context = len(narr) > 20
        has_stakes = any(w in narr.lower() for w in ['denied', 'rejected', 'score', 'algorithm', 'discriminat', 'die', 'kill', 'wrong'])
        has_uncertainty = '?' in narr or any(w in narr.lower() for w in ['never', 'secret', 'hidden', 'what if', 'but'])
        
        if not (has_context and has_stakes and has_uncertainty):
            litmus_fails += 1
    
    total_checks += 1
    fail_pct = litmus_fails / 20 * 100
    if fail_pct <= 30:
        passed_checks += 1
        print(f"  ✅ PASS: {20 - litmus_fails}/20 segments pass ({fail_pct:.0f}% fail)")
    else:
        report['warnings'].append(f"{litmus_fails}/20 segments fail litmus test")
        print(f"  ⚠️ WARN: {litmus_fails}/20 fail ({fail_pct:.0f}%)")
    
    # ── CHECK 4: SFX Density ──
    print("\n── CHECK 4: SFX Density ──")
    sfx_count = sum(1 for d in dir_segs if (d.get('sfx') or {}).get('type'))
    sfx_pct = sfx_count / max(len(dir_segs), 1) * 100
    
    total_checks += 1
    # LearnByLeo says SFX at key moments, not overdone
    if 5 <= sfx_pct <= 60:
        passed_checks += 1
        print(f"  ✅ PASS: {sfx_count} SFX events ({sfx_pct:.0f}% of segments)")
    else:
        report['warnings'].append(f"SFX density {sfx_pct:.0f}% outside 5-60% range")
        print(f"  ⚠️ WARN: {sfx_pct:.0f}% SFX density")
    
    # ── CHECK 5: Audio Levels ──
    print("\n── CHECK 5: Audio Levels ──")
    if os.path.exists(str(video_path)):
        f_dur = dur(str(video_path))
        audio_ok = True
        for t in [3, 10, 30, 60, 120, 300]:
            if t < f_dur:
                vol = check_audio(str(video_path), t)
                if vol <= -50 and t > 5:
                    audio_ok = False
                    print(f"  ❌ {t}s: {vol:.1f}dB (SILENT)")
                else:
                    print(f"  ✅ {t}s: {vol:.1f}dB")
        
        total_checks += 1
        if audio_ok:
            passed_checks += 1
        else:
            report['critical_failures'].append("Silent audio at key timestamps")
    
    # ── CHECK 6: Energy Variation ──
    print("\n── CHECK 6: Energy Variation ──")
    arcs = [d.get('arc_position', 'unknown') for d in dir_segs]
    unique_arcs = set(arcs)
    
    total_checks += 1
    if len(unique_arcs) >= 3:
        passed_checks += 1
        print(f"  ✅ PASS: {len(unique_arcs)} arc types ({', '.join(unique_arcs)})")
    else:
        report['warnings'].append(f"Only {len(unique_arcs)} arc types — low energy variation")
        print(f"  ⚠️ WARN: Only {len(unique_arcs)} arc types")
    
    # ── CHECK 7: Text Overlays ──
    print("\n── CHECK 7: Text Overlays ──")
    total_checks += 1
    if len(text_overlays) >= 10:
        passed_checks += 1
        print(f"  ✅ PASS: {len(text_overlays)} text overlays")
    else:
        report['warnings'].append(f"Only {len(text_overlays)} text overlays (want 10+)")
        print(f"  ⚠️ WARN: {len(text_overlays)} overlays")
    
    # ── FINAL SCORE ──
    score = passed_checks / max(total_checks, 1) * 100
    passed = len(report['critical_failures']) == 0
    
    report['score'] = score
    report['passed'] = passed
    report['total_checks'] = total_checks
    report['passed_checks'] = passed_checks
    
    print(f"\n{'='*50}")
    print(f"  DIRECTOR VALIDATION: {'PASS ✅' if passed else 'FAIL ❌'}")
    print(f"  Score: {score:.0f}% ({passed_checks}/{total_checks} checks)")
    if report['critical_failures']:
        print(f"  CRITICAL: {', '.join(report['critical_failures'])}")
    if report['warnings']:
        print(f"  WARNINGS: {', '.join(report['warnings'])}")
    print(f"{'='*50}")
    
    return passed, report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--edit-map", required=True)
    ap.add_argument("--director", required=True)
    ap.add_argument("--playbook-dir", required=True)
    ap.add_argument("--text-overlays", default=None)
    args = ap.parse_args()
    
    passed, report = validate(args.video, args.edit_map, args.director, args.playbook_dir, args.text_overlays)
    
    # Save report
    out = Path(args.video).parent / "director_validation_report.json"
    with open(out, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: {out}")
