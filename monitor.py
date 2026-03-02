#!/usr/bin/env python3
"""
Live dashboard — monitors the full Fern production pipeline.

Usage:
  # Terminal 1: run analysis, stream to log
  venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen-vl 2>&1 | tee /tmp/fern_analysis.log

  # Terminal 2: live dashboard
  python monitor.py
"""

import os
import time
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Log file written by analyze_fern_hybrid_checkpoint.py
ANALYSIS_LOG = "/tmp/fern_analysis.log"
CHECKPOINT   = Path("analysis/fern/.checkpoint.json")
FERN_DIR     = Path("analysis/fern")
VIDEO_IDS    = ["aVA7aXOH1pk", "wLFY_Zu_O08", "wkVygetgeRY"]
VIDEO_NAMES  = {
    "aVA7aXOH1pk": "Trump Assassination Attempt",
    "wLFY_Zu_O08": "FBI Undercover / KKK",
    "wkVygetgeRY": "Unabomber",
}

# Pipeline phases — what's built and runnable
PIPELINE_PHASES = [
    ("Analysis (visual)",  "analyze_fern_hybrid_checkpoint.py", "complete",    "free-local"),
    ("Motion Analysis",    "analyze_fern_motion.py",            "complete",    "free-local"),
    ("Master Formula",     "create_master_formula.py",          "complete",    "free-local"),
    ("Topic Radar",        "pipeline/topic_radar.py",           "ready",       "free-local"),
    ("Comments Miner",     "pipeline/comments_miner.py",        "ready",       "free-yt-dlp"),
    ("Research Brief",     "pipeline/research_brief.py",        "ready",       "free-local"),
    ("Story Validator",    "pipeline/story_validator.py",       "ready",       "free-local"),
    ("Script Gen",         "(use Claude Code interactively)",   "ready",       "free-claude-max"),
    ("Script Enhancer",    "pipeline/script_enhancer.py",       "ready",       "free-local-ollama"),
    ("Voice Preprocessor", "pipeline/audio_preprocessor.py",   "needs-clips", "free-local"),
    ("Voice Generator",    "pipeline/voice_generator.py",       "needs-clips", "free-f5-tts"),
    ("Footage Sourcer",    "pipeline/footage_sourcer.py",       "ready",       "free-local"),
    ("Video Assembler",    "pipeline/video_assembler.py",       "ready",       "free-local"),
    ("Publish",            "(manual upload for now)",           "manual",      "free"),
]

R   = "\033[0m"
B   = "\033[1m"
DIM = "\033[2m"
CY  = "\033[1;36m"
YL  = "\033[1;33m"
GR  = "\033[1;32m"
RD  = "\033[1;31m"
WH  = "\033[1;37m"
MG  = "\033[1;35m"


def cols():
    try:
        return os.get_terminal_size().columns
    except:
        return 120

def clear():
    print("\033[H\033[2J", end="", flush=True)

def read_log(path, n=500):
    try:
        raw = Path(path).read_text()
        lines = re.split(r"[\r\n]+", raw)
        return [l.rstrip() for l in lines if l.strip()][-n:]
    except:
        return []

def log_age(path):
    try:
        return time.time() - Path(path).stat().st_mtime
    except:
        return 9999

def get_analysis_pid():
    try:
        out = subprocess.run(
            ["pgrep", "-f", "analyze_fern_hybrid_checkpoint"],
            capture_output=True, text=True
        ).stdout.strip()
        return out.split()[0] if out else None
    except:
        return None

def parse_progress(lines):
    vid_num = "?"
    vid_id  = "?"
    done    = 0
    total   = 0
    eta_str = "calculating..."
    spf     = None
    errors  = 0
    model   = "qwen-vl"

    last_bar = None
    for line in lines:
        m = re.search(r"\[(\d+)/(\d+)\] Analyzing (\S+)", line)
        if m:
            vid_num = f"{m.group(1)}/{m.group(2)}"
            vid_id  = m.group(3).rstrip(".")
        if "Model:" in line:
            m2 = re.search(r"Model:\s+(\S+)", line)
            if m2:
                model = m2.group(1)
        bars = re.findall(
            r"(\d+\.\d+)%\s*\|\s*(\d+)/(\d+) frames.*?ETA:\s*(\S+)", line
        )
        if bars:
            last_bar = bars[-1]
        if "⚠" in line or "ERROR" in line:
            errors += 1

    if last_bar:
        _, done_s, total_s, eta_str = last_bar
        done  = int(done_s)
        total = int(total_s)
        m_eta = re.match(r"(?:(\d+)h)?(?:(\d+)m)?(\d+)s", eta_str)
        if m_eta:
            h  = int(m_eta.group(1) or 0)
            mn = int(m_eta.group(2) or 0)
            s  = int(m_eta.group(3) or 0)
            remaining_sec    = h * 3600 + mn * 60 + s
            remaining_frames = total - done
            if remaining_frames > 0:
                spf = remaining_sec / remaining_frames

    return vid_num, vid_id, done, total, eta_str, spf, errors, model

def load_checkpoint():
    try:
        return json.loads(CHECKPOINT.read_text())
    except:
        return {}

def timeline_status(vid):
    """Return (frames_count, is_complete, model_used) for best available timeline."""
    for model in ["qwen3.5-27b", "qwen3.5-4b", "qwen-vl", "gemini-flash"]:
        p = FERN_DIR / vid / f"timeline_hybrid_{model}.json"
        if p.exists() and p.stat().st_size > 5000:
            try:
                data     = json.loads(p.read_text())
                timeline = data.get("timeline", [])   # key is "timeline", not "frames"
                return len(timeline), data.get("complete", False), model
            except:
                pass
    return 0, False, None

def audio_status(vid):
    p = FERN_DIR / f"{vid}_audio_full.json"
    if not p.exists():
        return False, {}
    try:
        d = json.loads(p.read_text())
        return True, d.get("metadata", {})
    except:
        return True, {}

def bar(pct, width=40, color=GR):
    filled = int(width * pct / 100)
    return f"{color}{'█' * filled}{'░' * (width - filled)}{R}"

def fmt_duration(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"


def render():
    w     = cols()
    lines = read_log(ANALYSIS_LOG)
    pid   = get_analysis_pid()
    age   = log_age(ANALYSIS_LOG)
    cp    = load_checkpoint()
    now   = datetime.now().strftime("%H:%M:%S")

    vid_num, vid_id, done, total, eta_str, spf, errors, model = parse_progress(lines)

    clear()

    # ── HEADER ──────────────────────────────────────────────────────────────
    hdr = "  FERN PRODUCTION PIPELINE MONITOR  "
    pad = (w - len(hdr) - 2) // 2
    print(f"{CY}{'═'*pad}⟨{hdr}⟩{'═'*(max(0,w-pad-len(hdr)-2))}{R}")
    print(f"  {DIM}Time: {now}  ·  Refreshes every 5s  ·  Ctrl+C to exit{R}")
    print()

    sep = f"  {DIM}{'─'*(w-4)}{R}"

    # ── ANALYSIS PROCESS STATUS ─────────────────────────────────────────────
    print(f"  {B}▸ ANALYSIS PROCESS{R}")
    if pid:
        if age < 120:
            status = f"{GR}● RUNNING{R}  PID {pid}  —  log updated {int(age)}s ago"
        else:
            status = f"{YL}● STALLED{R}  PID {pid}  —  last update {int(age//60)}m ago (Ollama thinking)"
    elif lines:
        status = f"{DIM}● NOT RUNNING{R}  (log exists from previous run)"
    else:
        status = f"{DIM}● NOT RUNNING{R}"

    print(f"    {status}")
    if not pid:
        print(f"    {DIM}To run: venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen-vl 2>&1 | tee {ANALYSIS_LOG}{R}")
        print(f"    {DIM}Better:  ... --model qwen3.5-4b  (need: ollama pull qwen3.5:4b){R}")
    print()

    # ── CURRENT VIDEO PROGRESS ─────────────────────────────────────────────
    if pid and total > 0:
        print(sep)
        vid_label = VIDEO_NAMES.get(vid_id, vid_id)
        print(f"  {B}▸ NOW PROCESSING:{R}  Video {vid_num}  ·  {WH}{vid_id}{R}  ·  {vid_label}")
        print()
        pct   = (done / total * 100) if total > 0 else 0
        bar_w = min(w - 25, 50)
        print(f"    {bar(pct, bar_w)}  {WH}{pct:.1f}%{R}  ({done}/{total} frames)")
        spf_str = f"{spf:.0f}s/frame" if spf else "measuring..."
        print(f"    Speed: {WH}{spf_str}{R}   ETA this video: {YL}{eta_str}{R}   Errors: {RD if errors else DIM}{errors}{R}")
        if spf and total > 0:
            remaining_this = (total - done) * spf
            cur_idx    = cp.get("current_video_index", 0)
            vids_left  = len(VIDEO_IDS) - cur_idx - 1
            est_other  = vids_left * 150 * spf
            finish_at  = datetime.now() + timedelta(seconds=remaining_this + est_other)
            print(f"    Est. all videos: {YL}{fmt_duration(remaining_this + est_other)}{R}  (~{finish_at.strftime('%I:%M %p')})")
        print()

    # ── VIDEO ANALYSIS TABLE ─────────────────────────────────────────────────
    print(sep)
    print(f"  {B}▸ VIDEO ANALYSIS STATUS{R}")
    print()
    print(f"  {'#':<3} {'VIDEO ID':<14} {'TITLE':<32} {'TIMELINE':<32} {'AUDIO':<14}")
    print(f"  {'─'*3} {'─'*14} {'─'*32} {'─'*32} {'─'*14}")

    for i, vid in enumerate(VIDEO_IDS):
        label = VIDEO_NAMES.get(vid, "?")[:31]
        frames, is_complete, tl_model = timeline_status(vid)
        aud_ok, aud_meta = audio_status(vid)
        is_cur = (vid == vid_id and bool(pid))

        if frames > 0 and is_complete:
            model_tag = f"[{tl_model}]" if tl_model else ""
            vis = f"{GR}✓ {frames} frames {model_tag}{R}"
        elif frames > 0:
            vis = f"{YL}⏸ {frames} frames (paused){R}"
        elif is_cur and done > 0:
            pct2 = int(done / total * 100) if total > 0 else 0
            vis = f"{YL}⟳ {done}/{total} ({pct2}%){R}"
        elif is_cur:
            vis = f"{YL}⟳ starting...{R}"
        else:
            vis = f"{DIM}◌ queued{R}"

        if aud_ok:
            bpm = aud_meta.get("music_bpm", "?")
            wpm = aud_meta.get("narration_wpm", "?")
            aud = f"{GR}✓{R} {DIM}bpm:{bpm} wpm:{wpm}{R}"
        else:
            aud = f"{DIM}◌ pending{R}"

        print(f"  {i+1:<3} {vid:<14} {label:<32} {vis:<42} {aud}")
    print()

    # ── FORMULA FILES ────────────────────────────────────────────────────────
    print(sep)
    print(f"  {B}▸ FORMULA FILES{R}")
    print()
    formula_files = [
        ("FERN_MASTER_FORMULA.json",    "Master aggregate (all formulas)"),
        ("FERN_MOTION_FORMULA.json",    "Camera + optical flow + transitions"),
        ("SCRIPT_FORMULA.json",         "Script structure + pacing"),
        ("MUSIC_IDENTITY.json",         "BPM + genre + energy"),
        ("SOUND_DESIGN_FORMULA.json",   "SFX + ambient"),
        ("THUMBNAIL_FORMULA.json",      "Thumbnail composition"),
        ("TITLE_ANGLE_FORMULA.json",    "Title patterns by performance"),
        ("FERN_STYLE_GROUND_TRUTH.json","Ground truth style reference"),
    ]
    for fname, desc in formula_files:
        p = FERN_DIR / fname
        if p.exists():
            sz  = p.stat().st_size
            age2 = datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)
            age_str = f"{age2.days}d ago" if age2.days > 0 else "today"
            print(f"    {GR}✓{R}  {fname:<40} {DIM}{desc} · {sz//1024}KB · {age_str}{R}")
        else:
            print(f"    {RD}✗{R}  {fname:<40} {DIM}MISSING{R}")
    print()

    # ── FULL PIPELINE STATUS ─────────────────────────────────────────────────
    print(sep)
    print(f"  {B}▸ PIPELINE PHASE STATUS{R}")
    print()
    status_colors  = {"complete": GR, "ready": CY, "needs-clips": YL, "manual": MG, "not-started": DIM}
    status_labels  = {"complete": "✓ DONE", "ready": "▶ READY", "needs-clips": "⚠ NEEDS CLIPS",
                      "manual": "○ MANUAL", "not-started": "◌ NOT STARTED"}
    cost_labels    = {
        "free-local":        f"{GR}free/local{R}",
        "free-yt-dlp":       f"{GR}free/yt-dlp{R}",
        "free-local-ollama": f"{GR}free/ollama{R}",
        "free-claude-max":   f"{GR}free/claude-max{R}",
        "free-f5-tts":       f"{GR}free/f5-tts{R}",
        "free":              f"{GR}free{R}",
    }
    for phase, script, status, cost in PIPELINE_PHASES:
        col      = status_colors.get(status, DIM)
        label    = status_labels.get(status, status.upper())
        cost_str = cost_labels.get(cost, f"{DIM}{cost}{R}")
        print(f"    {col}{label:<18}{R}  {phase:<22}  {DIM}{script:<44}{R}  {cost_str}")

    print()
    print(f"  {YL}⚠ Voice clips needed:{R} record neutral/tense/energized (15–30s each)")
    print(f"  {DIM}  Save to: assets/voice/voice_neutral.wav, voice_tense.wav, voice_energized.wav{R}")
    print()

    # ── SAMPLE CLASSIFICATIONS ───────────────────────────────────────────────
    print(sep)
    print(f"  {B}▸ SAMPLE CLASSIFICATIONS (latest per video){R}")
    print()
    any_shown = False
    for vid in VIDEO_IDS:
        frames_count, _, tl_model = timeline_status(vid)
        if frames_count == 0 or tl_model is None:
            continue
        p = FERN_DIR / vid / f"timeline_hybrid_{tl_model}.json"
        try:
            data     = json.loads(p.read_text())
            timeline = data.get("timeline", [])
            if not timeline:
                continue
            any_shown = True
            last = next((e for e in reversed(timeline) if e.get("visual") and e["visual"] != {}), None)
            if not last:
                continue
            vis    = last.get("visual", {})
            ts     = last.get("timestamp", 0)
            cat    = vis.get("visual_category", "?")
            scene  = vis.get("scene_description", "?")[:75]
            emo    = vis.get("emotional_tone", "?")
            cam    = vis.get("camera_movement", "?")
            # new motion fields (present after re-run with updated prompt)
            motion_src = vis.get("motion_source", "")
            kinetic    = vis.get("kinetic_quality", "")
            anim_ease  = vis.get("animation_easing", "")
            extras = ""
            if motion_src: extras += f"  src:{motion_src}"
            if kinetic:    extras += f"  kinetic:{kinetic}"
            if anim_ease:  extras += f"  ease:{anim_ease}"
            print(f"    {GR}{vid}{R} ({VIDEO_NAMES[vid][:25]})  {DIM}model:{tl_model}  {frames_count} frames{R}")
            print(f"    {DIM}t={ts:.1f}s  [{cat}]  cam:{cam}  emo:{emo}{extras}{R}")
            print(f"    {DIM}\"{scene}\"{R}")
            print()
        except Exception:
            pass

    if not any_shown:
        print(f"    {DIM}No complete timelines yet — run analysis first.{R}")
        print()

    print(f"  {DIM}Ctrl+C to exit{R}", end="", flush=True)


if __name__ == "__main__":
    print("Starting Fern Pipeline Monitor...")
    time.sleep(0.3)
    try:
        while True:
            render()
            time.sleep(5)
    except KeyboardInterrupt:
        clear()
        print("Monitor stopped.")
