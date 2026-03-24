#!/usr/bin/env python3
"""
Live dashboard — monitors the QA-gated render pipeline.

Usage:
  # Terminal 1: run render, stream to log
  venv/bin/python scripts/render_with_qa.py \
      --topic frank_olson_cia_scientist_lsd_murder_cover_up \
      --stills-only --parallax 2>&1 | tee /tmp/render_qa.log

  # Terminal 2: live dashboard
  python monitor.py
"""

import os
import re
import json
import subprocess
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

RENDER_LOG = "/tmp/render_qa.log"
PROJECT    = Path(__file__).resolve().parent

# ── ANSI ─────────────────────────────────────────────────────────────────────
R   = "\033[0m"
B   = "\033[1m"
DIM = "\033[2m"
CY  = "\033[1;36m"
YL  = "\033[1;33m"
GR  = "\033[1;32m"
RD  = "\033[1;31m"
WH  = "\033[1;37m"
MG  = "\033[1;35m"
BG_DK = "\033[48;5;234m"


def cols():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 120


def clear():
    print("\033[H\033[2J", end="", flush=True)


def read_log(path, n=5000):
    try:
        raw = Path(path).read_text()
        return raw.splitlines()
    except Exception:
        return []


def log_age(path):
    try:
        return time.time() - Path(path).stat().st_mtime
    except Exception:
        return 9999


def get_render_pid():
    try:
        out = subprocess.run(
            ["pgrep", "-f", "render_with_qa"],
            capture_output=True, text=True
        ).stdout.strip()
        return out.split()[0] if out else None
    except Exception:
        return None


def get_assembler_pid():
    try:
        out = subprocess.run(
            ["pgrep", "-f", "video_assembler"],
            capture_output=True, text=True
        ).stdout.strip()
        return out.split()[0] if out else None
    except Exception:
        return None


def strip_ansi(s):
    return re.sub(r'\033\[[^m]*m', '', s)


# ── Log parsing ──────────────────────────────────────────────────────────────

def parse_gates(lines):
    """Parse gate results from log lines."""
    gates = []
    current_gate = None
    checks = []

    for line in lines:
        clean = strip_ansi(line).strip()

        # Gate header
        m = re.match(r'GATE (\d+): (.+)', clean)
        if m:
            if current_gate is not None:
                gates.append({"num": current_gate[0], "name": current_gate[1],
                              "checks": checks, "verdict": None})
            current_gate = (int(m.group(1)), m.group(2))
            checks = []
            continue

        # Check result
        if current_gate and clean.startswith(('✓', '⚠', '✗', '–')):
            icon = clean[0]
            status = {"✓": "PASS", "⚠": "WARN", "✗": "FAIL", "–": "SKIP"}.get(icon, "?")
            detail = clean[1:].strip()
            checks.append({"status": status, "detail": detail})
            continue

        # Verdict
        vm = re.match(r'VERDICT:\s*(PASS|WARN|FAIL)', clean)
        if vm and current_gate:
            gates.append({"num": current_gate[0], "name": current_gate[1],
                          "checks": checks, "verdict": vm.group(1)})
            current_gate = None
            checks = []

    # Capture any unfinished gate
    if current_gate:
        gates.append({"num": current_gate[0], "name": current_gate[1],
                      "checks": checks, "verdict": None})
    return gates


def parse_render_progress(lines):
    """Parse segment render progress."""
    segments = []
    total_segs = 0
    start_time = None
    editorial = {}

    for line in lines:
        clean = strip_ansi(line).strip()

        # Total segment count
        m = re.match(r'Rendering (\d+) segments', clean)
        if m:
            total_segs = int(m.group(1))
            continue

        # Individual segment render
        m = re.match(r'\[(\d+)/(\d+)\]\s+(\S+)\s+(\S+)s\s+(.+?)(?:\s+✓|\s+Using|\s+Loading|$)', clean)
        if m:
            idx = int(m.group(1))
            total_segs = int(m.group(2))
            motion = m.group(3)
            dur = m.group(4)
            source = m.group(5).strip()
            segments.append({
                "idx": idx, "total": total_segs,
                "motion": motion, "dur": float(dur),
                "source": source,
            })
            continue

        # Chapter card
        m = re.match(r'\[(\d+)/(\d+)\]\s+CHAPTER CARD\s+(\S+)s\s+(.+?)(?:\s+✓|$)', clean)
        if m:
            idx = int(m.group(1))
            total_segs = int(m.group(2))
            dur = m.group(3)
            title = m.group(4).strip()
            segments.append({
                "idx": idx, "total": total_segs,
                "motion": "CHAPTER", "dur": float(dur),
                "source": title,
            })
            continue

        # Editorial compliance
        m = re.search(r'Cut rate:\s+([\d.]+)/min', clean)
        if m:
            editorial["cut_rate"] = float(m.group(1))
        m = re.search(r'Avg segment:\s+([\d.]+)s', clean)
        if m:
            editorial["avg_seg"] = float(m.group(1))
        m = re.search(r'SFX:\s+([\d.]+)%', clean)
        if m:
            editorial["sfx_pct"] = float(m.group(1))
        m = re.search(r'Storyboard match:\s+(\d+)/(\d+)', clean)
        if m:
            editorial["sb_match"] = f"{m.group(1)}/{m.group(2)}"

        # Motion distribution
        m = re.search(r'Motion:\s+(.+)', clean)
        if m:
            editorial["motion_dist"] = m.group(1).strip()

        # Render complete
        m = re.search(r'Render complete in ([\d.]+) min', clean)
        if m:
            editorial["render_time"] = float(m.group(1))

        # Render failed
        if 'Render FAILED' in clean:
            editorial["render_failed"] = True

        # Timeline info
        m = re.search(r'(\d+) segments → (\d+)s \(([\d.]+)min\)', clean)
        if m:
            editorial["timeline_segs"] = int(m.group(1))
            editorial["timeline_dur"] = float(m.group(3))

        # Beat detection
        m = re.search(r'(\d+) beats detected\s+\(~(\d+) BPM', clean)
        if m:
            editorial["beats"] = int(m.group(1))
            editorial["bpm"] = int(m.group(2))

    return segments, total_segs, editorial


def parse_summary(lines):
    """Parse final summary if present."""
    summary = []
    in_summary = False
    overall = None
    for line in lines:
        clean = strip_ansi(line).strip()
        if clean == "SUMMARY":
            in_summary = True
            continue
        if in_summary:
            m = re.match(r'Gate (\d+)\s+(\S.+?)\s+(\d+)/(\d+)\s+(PASS|WARN|FAIL)', clean)
            if m:
                summary.append({
                    "num": int(m.group(1)), "name": m.group(2).strip(),
                    "passed": int(m.group(3)), "total": int(m.group(4)),
                    "verdict": m.group(5),
                })
            m = re.match(r'OVERALL:\s+(.+)', clean)
            if m:
                overall = m.group(1).strip()
    return summary, overall


# ── Rendering ────────────────────────────────────────────────────────────────

def bar(pct, width=40, color=GR):
    filled = int(width * pct / 100)
    return f"{color}{'█' * filled}{DIM}{'░' * (width - filled)}{R}"


def fmt_duration(sec):
    if sec < 60:
        return f"{sec:.0f}s"
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"


def render():
    w = cols()
    lines = read_log(RENDER_LOG)
    pid = get_render_pid()
    asm_pid = get_assembler_pid()
    age = log_age(RENDER_LOG)
    now = datetime.now().strftime("%H:%M:%S")

    gates = parse_gates(lines)
    segments, total_segs, editorial = parse_render_progress(lines)
    summary, overall = parse_summary(lines)

    clear()

    # ── HEADER ───────────────────────────────────────────────────────────
    hdr = "  QA-GATED RENDER PIPELINE  "
    pad = (w - len(hdr) - 2) // 2
    print(f"{CY}{'═' * pad}⟨{hdr}⟩{'═' * max(0, w - pad - len(hdr) - 2)}{R}")

    status_str = ""
    if pid or asm_pid:
        if asm_pid:
            status_str = f"{GR}● RENDERING{R}  (PID {asm_pid})"
        else:
            status_str = f"{GR}● RUNNING{R}  (PID {pid})"
    elif lines and overall:
        if "FAIL" in overall:
            status_str = f"{RD}● FINISHED — FAIL{R}"
        else:
            status_str = f"{GR}● FINISHED — {overall}{R}"
    elif lines:
        status_str = f"{YL}● LOG EXISTS{R}  (process not running)"
    else:
        status_str = f"{DIM}● WAITING FOR LOG{R}"

    print(f"  {status_str}  {DIM}·  {now}  ·  log updated {int(age)}s ago  ·  Ctrl+C to exit{R}")

    # Extract topic from log
    for line in lines[:5]:
        clean = strip_ansi(line).strip()
        m = re.search(r'RENDER QA\s*—\s*(\S+)', clean)
        if m:
            print(f"  {DIM}Topic:{R} {WH}{m.group(1)}{R}")
            break
    print()

    sep = f"  {DIM}{'─' * (w - 4)}{R}"

    # ── GATE STATUS ──────────────────────────────────────────────────────
    print(f"  {B}▸ QUALITY GATES{R}")
    print()

    if summary:
        # Use final summary table
        for s in summary:
            vc = {
                "PASS": GR, "WARN": YL, "FAIL": RD,
            }.get(s["verdict"], DIM)
            icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}.get(s["verdict"], "?")
            print(f"    {vc}{icon}{R}  Gate {s['num']}  {s['name']:<24} {s['passed']:>2}/{s['total']:<2}  {vc}{s['verdict']}{R}")
        if overall:
            oc = GR if "PASS" in overall else (YL if "WARN" in overall else RD)
            print(f"\n    {oc}{B}OVERALL: {overall}{R}")
    elif gates:
        for g in gates:
            v = g["verdict"] or "..."
            vc = {"PASS": GR, "WARN": YL, "FAIL": RD}.get(v, DIM)
            icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}.get(v, "⟳")
            n_checks = len(g["checks"])
            n_pass = sum(1 for c in g["checks"] if c["status"] in ("PASS", "WARN"))
            print(f"    {vc}{icon}{R}  Gate {g['num']}  {g['name']:<24} {n_pass:>2}/{n_checks:<2}  {vc}{v}{R}")

        # Show checks for current/last gate
        active = gates[-1] if gates else None
        if active and active["verdict"] is None and active["checks"]:
            print(f"\n    {CY}Currently checking: Gate {active['num']} — {active['name']}{R}")
            for c in active["checks"][-5:]:
                ci = {"PASS": f"{GR}✓", "WARN": f"{YL}⚠", "FAIL": f"{RD}✗", "SKIP": f"{DIM}–"}.get(c["status"], "?")
                print(f"      {ci}{R} {c['detail'][:80]}")
    else:
        print(f"    {DIM}No gate data yet — waiting for render_with_qa.py output{R}")
    print()

    # ── EDITORIAL DECISIONS ──────────────────────────────────────────────
    if editorial:
        print(sep)
        print(f"  {B}▸ EDITORIAL DECISIONS{R}")
        print()

        if editorial.get("bpm"):
            print(f"    Music:       {WH}{editorial['bpm']} BPM{R}  ({editorial.get('beats', '?')} beats detected)")
        if editorial.get("timeline_dur"):
            print(f"    Duration:    {WH}{editorial['timeline_dur']:.1f} min{R}  ({editorial.get('timeline_segs', '?')} segments)")
        if editorial.get("cut_rate"):
            print(f"    Cut rate:    {WH}{editorial['cut_rate']:.1f}/min{R}  (Fern target: ~13.2)")
        if editorial.get("avg_seg"):
            print(f"    Avg segment: {WH}{editorial['avg_seg']:.1f}s{R}  (Fern target: ~5.3s)")
        if editorial.get("sfx_pct"):
            print(f"    SFX density: {WH}{editorial['sfx_pct']:.1f}%{R} of cuts have SFX")
        if editorial.get("sb_match"):
            print(f"    Storyboard:  {WH}{editorial['sb_match']}{R} segments matched to footage")
        if editorial.get("motion_dist"):
            print(f"    Motion:      {editorial['motion_dist']}")
        print()

    # ── RENDER PROGRESS ──────────────────────────────────────────────────
    if segments:
        print(sep)
        print(f"  {B}▸ RENDER PROGRESS{R}")
        print()

        last = segments[-1]
        done = last["idx"]
        total = last["total"]
        pct = (done / total * 100) if total > 0 else 0

        bar_w = min(w - 30, 50)
        print(f"    {bar(pct, bar_w)}  {WH}{pct:.1f}%{R}  ({done}/{total})")

        # ETA estimate from render speed
        # Count segments rendered, estimate time per segment
        if len(segments) >= 3:
            # Estimate speed from segment durations (video duration, not render time)
            # Use position in list as proxy for time elapsed
            # We know the log age — rough estimate
            elapsed_rough = age  # time since last log update is near 0 if running
            # Better: count how many segments per unit time
            # Use a simple heuristic: ~4s per segment with parallax
            secs_per_seg = 4.0  # approximate from observations
            remaining = (total - done) * secs_per_seg
            eta = datetime.now() + timedelta(seconds=remaining)
            print(f"    ETA: {YL}~{fmt_duration(remaining)}{R}  (~{eta.strftime('%I:%M %p')})")

        if editorial.get("render_time"):
            print(f"    {GR}Render completed in {editorial['render_time']:.1f} min{R}")
        if editorial.get("render_failed"):
            print(f"    {RD}RENDER FAILED{R}")
        print()

        # ── MOTION BREAKDOWN ─────────────────────────────────────────────
        print(sep)
        print(f"  {B}▸ MOTION BREAKDOWN (rendered so far){R}")
        print()

        motion_counts = Counter(s["motion"] for s in segments)
        total_rendered = len(segments)
        # Sort by count descending
        for motion, count in motion_counts.most_common():
            pct_m = count / total_rendered * 100
            bar_w2 = min(int(pct_m / 2), 25)
            color = {
                "zoom_in": CY, "zoom_out": MG, "static": DIM,
                "pan_up": YL, "pan_down": YL,
                "pan_left": YL, "pan_right": YL,
                "CHAPTER": GR,
            }.get(motion, WH)
            print(f"    {color}{motion:<14}{R} {'█' * bar_w2:<25}  {count:>3} ({pct_m:.0f}%)")
        print()

        # ── FOOTAGE USAGE ────────────────────────────────────────────────
        print(sep)
        print(f"  {B}▸ FOOTAGE USAGE (top 10){R}")
        print()

        source_counts = Counter(s["source"] for s in segments
                                if s["source"] not in ("BLACK", "") and s["motion"] != "CHAPTER")
        for source, count in source_counts.most_common(10):
            name = source[:45]
            pct_s = count / total_rendered * 100
            print(f"    {WH}{count:>3}x{R}  {name:<47} {DIM}({pct_s:.0f}%){R}")
        unique = len(source_counts)
        print(f"\n    {DIM}{unique} unique sources across {total_rendered} segments{R}")
        print()

        # ── RECENT SEGMENTS ──────────────────────────────────────────────
        print(sep)
        print(f"  {B}▸ RECENT SEGMENTS (last 8){R}")
        print()

        recent = segments[-8:]
        for s in recent:
            motion = s["motion"]
            mc = {
                "zoom_in": CY, "zoom_out": MG, "static": DIM,
                "pan_up": YL, "pan_down": YL, "CHAPTER": GR,
            }.get(motion, WH)
            src = s["source"][:50]
            print(f"    {DIM}[{s['idx']:>3}/{s['total']}]{R}  {mc}{motion:<14}{R}  {s['dur']:.1f}s  {src}")
        print()

    elif not lines:
        print(sep)
        print(f"  {DIM}No render log found at {RENDER_LOG}{R}")
        print(f"  {DIM}Run: venv/bin/python scripts/render_with_qa.py --topic SLUG --stills-only --parallax 2>&1 | tee {RENDER_LOG}{R}")
        print()

    print(f"  {DIM}Ctrl+C to exit{R}", end="", flush=True)


if __name__ == "__main__":
    print("Starting QA Render Monitor...")
    time.sleep(0.3)
    try:
        while True:
            render()
            time.sleep(3)
    except KeyboardInterrupt:
        clear()
        print("Monitor stopped.")
