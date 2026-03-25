#!/usr/bin/env python3
"""
run_pipeline.py — Interactive conductor for the Fern-style video pipeline.

Runs every automated step with live terminal output. Stops at decision points
and asks you in plain English before proceeding. You always have final say.

State is saved to .pipeline_run.json after each stage — Ctrl+C and resume
anytime by running again with no arguments.

Usage:
    python run_pipeline.py                     # Start fresh or resume saved state
    python run_pipeline.py --topic "CIA MKULTRA"  # Pre-set topic, skip selection
    python run_pipeline.py --from voice        # Resume from a specific stage
    python run_pipeline.py --list              # List all stages and exit
    python run_pipeline.py --status            # Show current saved state and exit

Stages in order:
    topic       → Run topic_radar. YOU pick which topic.
    brief       → Research brief (automated)
    validate    → Story validator. YOU confirm GO/SKIP.
    script      → YOU write the script in Claude Code.
    enhance     → Script enhancer (automated)
    qa_script   → Script QA check. YOU confirm score before voice.
    storyboard  → Storyboard generator (automated)
    voice       → Voice narration + automated QA (LUFS, WPM, silence). Only stops if FAIL.
    music       → Music sourcer (automated)
    footage     → Footage sourcing + vision verification (auto-removes bad items).
    assemble    → Video assembler (automated, slow)
    qa_video    → Final video QA. YOU approve before upload.
    done        → Ready to upload!
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# ── ANSI colors ───────────────────────────────────────────────────────────────

R    = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
GR   = "\033[92m"   # green
YL   = "\033[93m"   # yellow
RD   = "\033[91m"   # red
CY   = "\033[96m"   # cyan
BL   = "\033[94m"   # blue
MG   = "\033[95m"   # magenta
WH   = "\033[97m"   # white

# ── Constants ─────────────────────────────────────────────────────────────────

STATE_FILE = Path(".pipeline_run.json")
PYTHON     = str(Path("venv/bin/python"))

# All stage names in order
STAGE_ORDER = [
    "topic", "brief", "validate", "script", "enhance",
    "qa_script", "storyboard", "director", "voice", "music",
    "footage", "assemble", "qa_video", "done",
]

STAGE_LABELS = {
    "topic":      "Topic Research",
    "brief":      "Research Brief",
    "validate":   "Story Validation",
    "script":     "Script Writing  ← YOUR TURN",
    "enhance":    "Script Enhancement",
    "qa_script":  "Script QA Check",
    "storyboard": "Storyboard Generation",
    "director":   "Director's Pass",
    "voice":      "Voice Narration",
    "music":      "Music Selection",
    "footage":    "Footage Sourcing",
    "assemble":   "Video Assembly",
    "qa_video":   "Final Video QA",
    "done":       "Ready to Upload  ← YOUR TURN",
}

MANUAL_STAGES = {"script", "done"}   # stages where you do the work, runner just guides

# ── State management ──────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"stage": "topic", "topic": "", "slug": "", "completed": [], "paths": {}}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def slug_from_topic(topic: str) -> str:
    """Convert topic string to a safe filesystem slug."""
    s = topic.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:50]


# ── Terminal helpers ──────────────────────────────────────────────────────────

def _cols():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 100


def _line(char="─"):
    return char * min(_cols() - 4, 90)


def clear_line():
    print("\r\033[K", end="", flush=True)


def print_header(state: dict, stage: str):
    """Print the pipeline progress header."""
    stage_idx  = STAGE_ORDER.index(stage)
    total      = len(STAGE_ORDER) - 1   # exclude "done"
    completed  = state.get("completed", [])
    topic      = state.get("topic", "")

    print()
    print(f"{CY}{BOLD}{'═' * min(_cols()-2, 92)}{R}")
    print(f"{CY}{BOLD}  FERN PIPELINE RUNNER{R}  {DIM}—  stage {stage_idx+1} of {total}{R}")
    if topic:
        print(f"  {DIM}Topic: {R}{WH}{BOLD}{topic}{R}")
    print(f"{CY}{BOLD}{'═' * min(_cols()-2, 92)}{R}")
    print()

    # Stage progress bar
    for i, s in enumerate(STAGE_ORDER):
        if s == "done":
            continue
        label = STAGE_LABELS[s]
        if s in completed:
            icon = f"{GR}✓{R}"
            col  = DIM
        elif s == stage:
            icon = f"{CY}▶{R}"
            col  = f"{CY}{BOLD}"
        else:
            icon = f"{DIM}◌{R}"
            col  = DIM
        print(f"  {icon}  {col}{label:<35}{R}")
    print()
    print(f"  {CY}{BOLD}{_line()}{R}")
    print()


def ask(question: str, options: list = None, default: str = None) -> str:
    """
    Ask user a plain-English question in a clearly marked decision box.
    Returns user input (lowercased if options provided).
    """
    print()
    print(f"  {YL}{BOLD}{'┌' + '─' * 62 + '┐'}{R}")
    print(f"  {YL}{BOLD}│  YOUR DECISION{R}{' ' * 48}{YL}{BOLD}│{R}")
    print(f"  {YL}{BOLD}│{R}  {question:<60}{YL}{BOLD}│{R}")
    if options:
        opts = "  /  ".join(options)
        print(f"  {YL}{BOLD}│{R}  {DIM}Options: {opts}{R}{' ' * max(0, 51-len(opts))}{YL}{BOLD}│{R}")
    if default:
        print(f"  {YL}{BOLD}│{R}  {DIM}[Enter] = {default}{R}{' ' * max(0, 50-len(default))}{YL}{BOLD}│{R}")
    print(f"  {YL}{BOLD}{'└' + '─' * 62 + '┘'}{R}")
    print()

    prompt = f"  {YL}▶{R} "
    try:
        answer = input(prompt).strip()
    except KeyboardInterrupt:
        print(f"\n\n  {YL}Paused. Run again to resume from this stage.{R}\n")
        sys.exit(0)

    if not answer and default:
        return default.lower() if options else default
    return answer.lower() if options else answer


def inform(message: str, style: str = "info"):
    """Show a prominent informational message."""
    colors = {"info": CY, "success": GR, "warn": YL, "error": RD, "manual": MG}
    c = colors.get(style, CY)
    print(f"\n  {c}{BOLD}ℹ  {message}{R}\n")


def step_done(label: str):
    print(f"\n  {GR}{BOLD}✓  {label}{R}\n")


def step_fail(label: str):
    print(f"\n  {RD}{BOLD}✗  {label}{R}\n")


# ── Subprocess helpers ────────────────────────────────────────────────────────

def run_live(cmd: list, label: str = "", capture_output: bool = False) -> tuple[int, str]:
    """
    Run a command with live stdout/stderr streaming to terminal.
    Returns (returncode, combined_output_text).
    Prefixes each line with a dim indent so it's visually separate from UI.
    """
    print(f"  {DIM}Running: {' '.join(cmd[:6])}{R}")
    print(f"  {DIM}{_line('·')}{R}")

    output_lines = []
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        for line in proc.stdout:
            line = line.rstrip()
            output_lines.append(line)
            # Colorize key words inline
            disp = line
            if any(w in line for w in ["ERROR", "FAIL", "Error", "Traceback"]):
                disp = f"{RD}{line}{R}"
            elif any(w in line for w in ["✓", "Done", "PASS", "complete"]):
                disp = f"{GR}{line}{R}"
            elif any(w in line for w in ["WARNING", "WARN", "⚠", "skipping"]):
                disp = f"{YL}{line}{R}"
            elif any(w in line for w in ["[", "→", "▶"]):
                disp = f"{DIM}{line}{R}"
            print(f"    {disp}")

        proc.wait()
        rc = proc.returncode
    except FileNotFoundError:
        print(f"    {RD}Command not found: {cmd[0]}{R}")
        rc = 127
    except KeyboardInterrupt:
        if 'proc' in locals():
            proc.terminate()
        print(f"\n\n  {YL}Interrupted. Run again to resume.{R}\n")
        sys.exit(0)

    print(f"  {DIM}{_line('·')}{R}")
    return rc, "\n".join(output_lines)


# ── Stage implementations ─────────────────────────────────────────────────────

def stage_topic(state: dict) -> bool:
    """Run topic_radar, display results, ask user to pick."""
    print_header(state, "topic")
    inform("Running topic radar — scanning Reddit, News, YouTube for story candidates…", "info")

    rc, output = run_live([
        PYTHON, "pipeline/topic_radar.py", "--brand", "fern_clone"
    ], "topic_radar")

    # Try to load the candidates JSON
    candidates = []
    for candidate_path in sorted(Path("research").glob("*/topic_candidates.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(candidate_path.read_text())
            raw = data if isinstance(data, list) else data.get("candidates", [])
            candidates = raw[:10]
            break
        except Exception:
            pass

    if candidates:
        print(f"\n  {BOLD}{'─' * 60}{R}")
        print(f"  {BOLD}Top Candidates Found:{R}")
        print()
        for i, c in enumerate(candidates[:8]):
            topic_name = c.get("topic") or c.get("title") or c.get("query") or str(c)[:60]
            score      = c.get("score") or c.get("viral_score") or c.get("total_score") or "?"
            overlap    = c.get("fern_overlap") or c.get("overlap") or ""
            overlap_str = f"  {RD}overlap:{overlap}{R}" if overlap else ""
            score_color = GR if isinstance(score, (int, float)) and score >= 85 else YL
            print(f"  {WH}{i+1:>2}.{R}  {topic_name:<52}  {score_color}score:{score}{R}{overlap_str}")
        print()

    print(f"  {BOLD}{'─' * 60}{R}")
    print()
    topic_input = ask(
        "Which topic do you want to produce?",
        options=["enter number (1-8)", "type your own topic"],
    )

    # Resolve number to topic name
    if topic_input.isdigit():
        idx = int(topic_input) - 1
        if 0 <= idx < len(candidates):
            c = candidates[idx]
            chosen = c.get("topic") or c.get("title") or c.get("query") or topic_input
        else:
            inform("Number out of range — enter the topic name directly.", "warn")
            chosen = ask("Topic name:")
    else:
        chosen = topic_input.strip()

    if not chosen:
        inform("No topic entered. Try again.", "error")
        return False

    state["topic"] = chosen
    state["slug"]  = slug_from_topic(chosen)
    step_done(f'Topic selected: "{chosen}"  →  slug: {state["slug"]}')
    return True


def stage_brief(state: dict) -> bool:
    """Run research_brief.py."""
    print_header(state, "brief")
    inform(f"Building research brief for: {state['topic']}", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/research_brief.py",
        "--brand", "fern_clone",
        "--query", state["topic"],
    ])

    # Find the brief
    brief_candidates = list(Path("research").glob(f"*/briefs/*{state['slug']}*.json"))
    if brief_candidates:
        brief_path = str(sorted(brief_candidates, key=lambda p: p.stat().st_mtime)[-1])
        state["paths"]["brief"] = brief_path
        step_done(f"Brief saved → {brief_path}")
    elif rc == 0:
        step_done("Brief generated (auto-detect path)")
    else:
        step_fail(f"research_brief.py returned code {rc}")
        return False
    return True


def stage_validate(state: dict) -> bool:
    """Run story_validator.py and show GO/SKIP/NEEDS WORK verdict."""
    print_header(state, "validate")
    inform(f"Validating story viability for: {state['topic']}", "info")

    rc, output = run_live([
        PYTHON, "pipeline/story_validator.py",
        "--query", state["topic"],
        "--brand", "fern_clone",
    ])

    # Extract verdict from output
    verdict = "UNKNOWN"
    score   = "?"
    for line in output.splitlines():
        if "GO" in line and "VERDICT" in line.upper():
            verdict = "GO"
        elif "SKIP" in line and "VERDICT" in line.upper():
            verdict = "SKIP"
        elif "NEEDS WORK" in line:
            verdict = "NEEDS WORK"
        m = re.search(r"score[:\s]+(\d+)", line, re.IGNORECASE)
        if m:
            score = m.group(1)

    verdict_color = GR if verdict == "GO" else (RD if verdict == "SKIP" else YL)
    print(f"\n  {BOLD}Validator verdict:  {verdict_color}{BOLD}{verdict}{R}   Score: {score}/100\n")

    if verdict == "SKIP":
        inform("Validator says SKIP. Strong Fern overlap or low story viability.", "warn")
        answer = ask(
            "The validator recommends skipping this topic. Proceed anyway?",
            options=["yes — override and proceed", "no — go back to topic selection"],
            default="no",
        )
        if not answer.startswith("y"):
            state["stage"] = "topic"
            return False

    elif verdict == "NEEDS WORK":
        answer = ask(
            f"Validator: NEEDS WORK (score {score}). Proceed to scripting?",
            options=["yes — proceed", "no — pick a different topic"],
            default="yes",
        )
        if not answer.startswith("y"):
            state["stage"] = "topic"
            return False
    else:
        step_done("Story validated — GO")

    return True


def stage_script(state: dict) -> bool:
    """Manual stage — user writes the script in Claude Code."""
    print_header(state, "script")

    slug        = state["slug"]
    raw_path    = Path(f"scripts/raw_{slug}.txt")
    enhanced_path = Path(f"scripts/enhanced_{slug}.txt")

    print(f"  {MG}{BOLD}━━━  YOUR TURN  ━━━{R}")
    print()
    print(f"  Write the script in THIS Claude Code session.")
    print()
    print(f"  {BOLD}Instructions:{R}")
    print(f"  {DIM}1. Tell Claude: \"Write a full Fern-style script on: {state['topic']}\"{R}")
    print(f"  {DIM}2. Reference: analysis/fern/SCRIPT_FORMULA.json + FERN_MASTER_FORMULA.json{R}")
    print(f"  {DIM}3. Target: ~4,200 words, 25 min @ 138.7 WPM{R}")
    print(f"  {DIM}4. Structure: hook → context → escalation → revelation → climax → outro{R}")
    print(f"  {DIM}5. Include [PAUSE:5.0] at chapter breaks (aim for 5 chapters){R}")
    print(f"  {DIM}6. Save to: {raw_path}{R}")
    print()

    while True:
        answer = ask(
            f"Have you saved your script to {raw_path}?",
            options=["yes — continue", "no — still writing"],
            default="no",
        )
        if answer.startswith("y"):
            if raw_path.exists() and raw_path.stat().st_size > 100:
                state["paths"]["script_raw"] = str(raw_path)
                step_done(f"Script found at {raw_path}  ({raw_path.stat().st_size // 1024}KB)")
                return True
            else:
                inform(f"File not found or empty: {raw_path}. Please save it there.", "warn")
        else:
            inform("Take your time — run this script again when ready.", "info")
            print(f"  {DIM}Your saved state will resume here next run.{R}\n")
            sys.exit(0)


def stage_enhance(state: dict) -> bool:
    """Run script_enhancer.py."""
    print_header(state, "enhance")

    slug      = state["slug"]
    raw_path  = state["paths"].get("script_raw", f"scripts/raw_{slug}.txt")
    out_path  = f"scripts/enhanced_{slug}.txt"

    inform("Adding BEAT / PAUSE / VOICE markers to script…", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/script_enhancer.py",
        "--input", raw_path,
        "--output", out_path,
    ])

    if Path(out_path).exists():
        state["paths"]["script_enhanced"] = out_path
        step_done(f"Enhanced script → {out_path}")
        return True
    step_fail(f"script_enhancer failed (code {rc})")
    return False


def stage_qa_script(state: dict) -> bool:
    """Run check_fern_script.py AND playbook structure analyzer."""
    print_header(state, "qa_script")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")

    # ── Playbook Structure Analysis (LearnByLeo-derived) ──
    inform("Running playbook structure analysis (green/purple, pacing, flow)…", "info")
    pb_rc, pb_output = run_live([
        PYTHON, "-m", "pipeline.script_structure_analyzer",
        enhanced, "--title", state.get("topic", ""),
    ], "playbook_analyzer")

    # Extract playbook composite score
    pb_score = None
    for line in pb_output.splitlines():
        m = re.search(r"COMPOSITE:\s+([\d.]+)/100", line)
        if m:
            pb_score = float(m.group(1))

    if pb_score is not None:
        pb_color = GR if pb_score >= 80 else (YL if pb_score >= 65 else RD)
        print(f"\n  {BOLD}Playbook score:  {pb_color}{BOLD}{pb_score:.1f}/100{R}")
        if pb_score < 65:
            inform("Script structure needs work — green/purple pattern or energy variation may be weak.", "warn")
        print()

    # ── Fern Benchmark Analysis ──

    inform("Scoring script against Fern benchmarks…", "info")
    rc, output = run_live([PYTHON, "check_fern_script.py", enhanced])

    # Extract score from output
    score = None
    grade = "?"
    for line in output.splitlines():
        m = re.search(r"(\d+)/100", line)
        if m:
            score = int(m.group(1))
        if "Grade:" in line or "grade:" in line.lower():
            m2 = re.search(r"Grade:\s*([A-F][+\-]?)", line, re.IGNORECASE)
            if m2:
                grade = m2.group(1)

    if score is None:
        inform("Could not parse script score from output.", "warn")
        answer = ask(
            "Script QA output above. Continue to storyboard and voice?",
            options=["yes", "no — rewrite script first"],
            default="yes",
        )
        return answer.startswith("y")

    score_color = GR if score >= 85 else (YL if score >= 75 else RD)
    print(f"\n  {BOLD}Script score:  {score_color}{BOLD}{score}/100{R}   Grade: {grade}")
    print()

    if score >= 85:
        step_done(f"Script passes ({score}/100) — proceeding to storyboard and voice")
        return True
    elif score >= 75:
        answer = ask(
            f"Script scored {score}/100 (target: 85+). Weak but workable. Proceed anyway?",
            options=["yes — proceed", "no — rewrite and re-run"],
            default="no",
        )
        return answer.startswith("y")
    else:
        inform(f"Script scored {score}/100 — below minimum (75). Rewrite recommended.", "warn")
        answer = ask(
            "Override and proceed to voice anyway? (Not recommended below 75)",
            options=["yes — override", "no — go back to script stage"],
            default="no",
        )
        if answer.startswith("y"):
            return True
        state["stage"] = "script"
        return False


def stage_storyboard(state: dict) -> bool:
    """Run storyboard_generator.py."""
    print_header(state, "storyboard")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")
    out_path = f"storyboards/{slug}.json"

    inform("Generating per-segment visual brief — making every choice story-aware…", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/storyboard_generator.py",
        "--script", enhanced,
        "--out", out_path,
    ])

    if Path(out_path).exists():
        state["paths"]["storyboard"] = out_path
        # Count segments
        try:
            sb = json.loads(Path(out_path).read_text())
            n = len(sb)
        except Exception:
            n = "?"
        step_done(f"Storyboard → {out_path}  ({n} segments)")
        return True
    step_fail(f"storyboard_generator failed (code {rc})")
    return False


def stage_director(state: dict) -> bool:
    """Run director.py — full-context editorial pass over storyboard."""
    print_header(state, "director")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")
    sb_in    = state["paths"].get("storyboard", f"storyboards/{slug}.json")
    sb_out   = f"storyboards/{slug}_directed.json"

    inform("Director's pass — full-context editorial decisions for the whole video…", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/director.py",
        "--script", enhanced,
        "--storyboard", sb_in,
        "--out", sb_out,
    ])

    if Path(sb_out).exists():
        # Replace storyboard path with directed version for downstream stages
        state["paths"]["storyboard"] = sb_out
        try:
            d = json.loads(Path(sb_out).read_text())
            n_seg = d.get("segment_count", "?")
            n_sc  = d.get("scene_count", "?")
            n_sfx = d.get("sfx_count", 0)

            # Show playbook audit if present
            audit = d.get("playbook_audit")
            if audit and "scores" in audit:
                print(f"\n  {BOLD}Playbook Editing Audit — {audit.get('overall_percent', '?')}{R}")
                for k, v in audit["scores"].items():
                    bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
                    color = GR if v >= 0.8 else (YL if v >= 0.6 else RD)
                    print(f"  {k:25s} {color}{bar}{R} {v*100:.0f}%")
                if audit.get("warnings"):
                    for w in audit["warnings"]:
                        print(f"  {YL}⚠ [{w['rule']}] {w['issue']}{R}")
                print()
        except Exception:
            n_seg, n_sc, n_sfx = "?", "?", "?"
        step_done(f"Director → {sb_out}  ({n_seg} segments, {n_sc} scenes, {n_sfx} SFX)")
        return True
    step_fail(f"director failed (code {rc})")
    return False


def stage_voice(state: dict) -> bool:
    """
    Run voice_generator.py then auto-verify with check_fern_voice.py.
    Only pauses for manual intervention if voice QA returns FAIL.
    PASS and WARN proceed automatically — no need to listen every time.
    """
    print_header(state, "voice")

    slug      = state["slug"]
    enhanced  = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")
    out_dir   = f"audio/{slug}"
    out_wav   = f"{out_dir}/narration.wav"

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    inform("Generating voice narration — this takes several minutes…", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/voice_generator.py",
        "--ref-neutral",   "assets/voice/voice_neutral_ref.wav",
        "--ref-tense",     "assets/voice/voice_tense_ref.wav",
        "--ref-energized", "assets/voice/voice_energized_ref.wav",
        "--auto-transcribe",
        "--script", enhanced,
        "--out", out_wav,
    ])

    # Find narration manifest
    manifest_path = str(Path(out_dir) / "narration_manifest.json")
    if Path(manifest_path).exists():
        state["paths"]["narration_manifest"] = manifest_path
        state["paths"]["narration_wav"]      = out_wav
    elif rc == 0:
        state["paths"]["narration_wav"] = out_wav
    else:
        step_fail(f"voice_generator failed (code {rc})")
        return False

    if not Path(out_wav).exists():
        step_fail(f"Narration file missing after generation: {out_wav}")
        return False

    # ── Automated voice QA ────────────────────────────────────────────────────
    inform("Running automated voice QA — checking LUFS, WPM, silence, clipping…", "info")

    qa_cmd = [PYTHON, "check_fern_voice.py", out_wav, "--script", enhanced]
    if Path(manifest_path).exists():
        qa_cmd += ["--manifest", manifest_path]

    qa_rc, qa_output = run_live(qa_cmd, "voice_qa")

    # Parse verdict
    voice_verdict = "UNKNOWN"
    for line in qa_output.splitlines():
        if "FAIL" in line and "Verdict" in line:
            voice_verdict = "FAIL"
        elif "WARN" in line and "Verdict" in line:
            voice_verdict = "WARN"
        elif "PASS" in line and "Verdict" in line:
            voice_verdict = "PASS"

    if voice_verdict == "PASS":
        step_done("Voice narration: PASS — all checks green. Proceeding automatically.")
        return True

    if voice_verdict == "WARN":
        inform("Voice QA: WARN — minor issues, within acceptable range. Auto-proceeding.", "warn")
        step_done("Narration accepted (warnings noted)")
        return True

    # FAIL or UNKNOWN — stop and ask
    inform("Voice QA: FAIL — critical issues detected. Regeneration recommended.", "error")
    print()
    print(f"  {DIM}Common causes: F5-TTS speed, LUFS too low/high, excessive silence{R}")
    print(f"  {DIM}Check script for very long runs of text without [PAUSE] markers{R}")
    print()

    answer = ask(
        "Voice QA failed. Regenerate narration? (recommended)",
        options=["yes — regenerate", "no — override and proceed anyway"],
        default="yes",
    )
    if answer.startswith("y"):
        inform("Rerunning voice generator…", "info")
        state["stage"] = "voice"
        return False

    inform("Overriding voice QA failure — proceeding with flagged narration.", "warn")
    step_done("Narration accepted (QA override)")
    return True


def stage_music(state: dict) -> bool:
    """Run music_sourcer.py."""
    print_header(state, "music")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")

    inform("Finding mood-matched music track (Pixabay CC0 / FMA / YouTube Audio)…", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/music_sourcer.py",
        "--script", enhanced,
    ])

    music_path = Path("assets/music/track.mp3")
    if music_path.exists():
        state["paths"]["music"] = str(music_path)
        sz = music_path.stat().st_size // 1024
        step_done(f"Music track → {music_path}  ({sz}KB)")
        return True
    elif rc == 0:
        step_done("Music downloaded (track at assets/music/track.mp3)")
        state["paths"]["music"] = "assets/music/track.mp3"
        return True
    step_fail(f"music_sourcer failed (code {rc}) — proceeding without music (assembler will still work)")
    return True   # don't block on music — assembler handles missing track


def stage_footage(state: dict) -> bool:
    """
    Run footage_sourcer.py then auto-verify with footage_verifier.py.
    Vision model scores each item against its storyboard description.
    Auto-removes irrelevant items. Only asks user if coverage is critically low.
    """
    print_header(state, "footage")

    slug       = state["slug"]
    brief      = state["paths"].get("brief", f"research/fern_clone/briefs/{slug}.json")
    storyboard = state["paths"].get("storyboard", f"storyboards/{slug}.json")
    out_dir    = f"footage/fern_clone/{slug}"

    inform("Sourcing footage — targeted searches per storyboard entry…", "info")
    inform("This may take several minutes depending on download speed.", "info")

    cmd = [
        PYTHON, "pipeline/footage_sourcer.py",
        "--brand", "fern_clone",
        "--out", out_dir,
        "--download",
    ]
    if Path(brief).exists():
        cmd += ["--brief", brief]
    if Path(storyboard).exists():
        cmd += ["--storyboard", storyboard]

    rc, _ = run_live(cmd)

    # Find manifest
    manifest_path = Path(out_dir) / "manifest.json"
    if not manifest_path.exists():
        step_fail(f"footage_sourcer failed (code {rc}) or no manifest created")
        return False

    state["paths"]["footage_manifest"] = str(manifest_path)

    # Quick download summary
    try:
        manifest = json.loads(manifest_path.read_text())
        clips  = manifest.get("clips", [])
        images = [c for c in clips if str(c.get("local_path","")).lower().endswith((".jpg",".png",".jpeg",".webp"))]
        videos = [c for c in clips if str(c.get("local_path","")).lower().endswith((".mp4",".mov",".mkv",".webm"))]
        needs_anim = manifest.get("needs_animation", [])

        print(f"\n  {BOLD}{'─' * 60}{R}")
        print(f"  {BOLD}Download Summary:{R}")
        print()
        print(f"  {GR}✓{R}  Images:           {WH}{len(images)}{R}  stills")
        print(f"  {GR}✓{R}  Video clips:      {WH}{len(videos)}{R}  clips")
        if needs_anim:
            print(f"  {YL}▲{R}  Needs animation:  {WH}{len(needs_anim)}{R}  segments (will be auto-generated)")
        print(f"  {BOLD}{'─' * 60}{R}\n")
    except Exception:
        pass

    # ── Web image sourcing (Chrome-powered, Claude Vision verified) ──────────
    try:
        from pipeline.web_image_sourcer import WebImageSourcer
        inform("Running web image sourcer — searching government archives + web…", "info")
        web_sourcer = WebImageSourcer(output_dir=f"{out_dir}/web_sourced")

        # Load storyboard segments for targeted search
        if Path(storyboard).exists():
            sb_data = json.loads(Path(storyboard).read_text())
            if isinstance(sb_data, dict) and sb_data.get("scenes"):
                sb_flat = []
                for scene in sb_data["scenes"]:
                    sb_flat.extend(scene.get("segments", []))
            else:
                sb_flat = sb_data if isinstance(sb_data, list) else []

            web_manifest = web_sourcer.source_for_storyboard(sb_flat[:10])  # First 10 segments
            web_count = web_manifest.get("total_clips", 0)
            if web_count > 0:
                inform(f"Web sourcer found {web_count} verified images", "success")
                # Merge web results into main manifest
                try:
                    main_manifest = json.loads(manifest_path.read_text())
                    main_manifest["clips"].extend(web_manifest.get("clips", []))
                    manifest_path.write_text(json.dumps(main_manifest, indent=2))
                except Exception:
                    pass
    except ImportError:
        inform("Web image sourcer not available — using standard sources only", "warn")
    except Exception as e:
        inform(f"Web sourcer error (non-fatal): {e}", "warn")

    # ── Clip verification (frame extraction + Claude Vision) ──────────────
    try:
        from pipeline.clip_verifier import ClipVerifier
        verifier = ClipVerifier()
        if Path(storyboard).exists():
            inform("Verifying video clips against storyboard…", "info")
            verifier.verify_manifest(str(manifest_path), sb_flat if 'sb_flat' in dir() else [])
    except ImportError:
        pass
    except Exception as e:
        inform(f"Clip verification error (non-fatal): {e}", "warn")

    # ── Automated footage verification ────────────────────────────────────────
    inform("Running footage verification — scoring items against storyboard…", "info")
    inform("This removes irrelevant downloads automatically. No manual review needed.", "info")

    verify_rc, verify_output = run_live([
        PYTHON, "pipeline/footage_verifier.py",
        "--manifest", str(manifest_path),
    ], "footage_verifier")

    # Parse coverage from output
    coverage_pct = 100.0
    for line in verify_output.splitlines():
        m = re.search(r"Coverage:\s*([\d.]+)%", line)
        if m:
            coverage_pct = float(m.group(1))
            break

    # Parse removed count
    removed_count = 0
    for line in verify_output.splitlines():
        m = re.search(r"(\d+) irrelevant item", line)
        if m:
            removed_count = int(m.group(1))

    if removed_count > 0:
        inform(f"Removed {removed_count} irrelevant item(s) from manifest.", "info")

    # Coverage-based decision
    if coverage_pct >= 60:
        # Good enough — auto-proceed, animation handles the rest
        step_done(
            f"Footage verified — {coverage_pct:.0f}% storyboard coverage. "
            f"Gaps will use auto-generated animations."
        )
        return True

    if coverage_pct >= 40:
        # Low but workable — inform and auto-proceed
        inform(
            f"Coverage is low ({coverage_pct:.0f}%) — many segments will use animation. "
            f"This is normal for niche/archival topics.",
            "warn",
        )
        step_done("Footage stage complete — proceeding (animation will fill gaps)")
        return True

    # Critically low — ask user
    inform(
        f"CRITICAL: only {coverage_pct:.0f}% of story segments have verified footage. "
        f"Most of the video will be animated.",
        "error",
    )
    print()
    print(f"  {DIM}This can happen for highly specific archival topics — still a valid video.{R}")
    print(f"  {DIM}Animation frames are cinematic and match Fern's visual style.{R}")
    print()

    answer = ask(
        f"Only {coverage_pct:.0f}% footage coverage. Proceed anyway (animation fills gaps)?",
        options=["yes — proceed with animation", "no — re-source footage first"],
        default="yes",
    )
    if answer.startswith("n"):
        inform("Re-run footage_sourcer manually with different search terms, then run again.", "info")
        sys.exit(0)

    step_done("Footage stage complete (low coverage override — animation will fill gaps)")
    return True


def stage_assemble(state: dict) -> bool:
    """Run video_assembler.py."""
    print_header(state, "assemble")

    slug      = state["slug"]
    narration = state["paths"].get("narration_manifest",
                                   f"audio/{slug}/narration_manifest.json")
    footage   = state["paths"].get("footage_manifest",
                                   f"footage/fern_clone/{slug}/manifest.json")
    music     = state["paths"].get("music", "assets/music/track.mp3")
    storyboard = state["paths"].get("storyboard", f"storyboards/{slug}.json")
    out_path  = f"output/{slug}/final.mp4"

    Path(f"output/{slug}").mkdir(parents=True, exist_ok=True)

    # ── Fair Use Compliance Check ──
    try:
        from pipeline.fair_use_guard import FairUseGuard
        guard = FairUseGuard()
        if Path(footage).exists():
            footage_data = json.loads(Path(footage).read_text())
            clips = footage_data.get("clips", [])
            # Add default transformative elements for our pipeline
            for clip in clips:
                clip.setdefault("has_narration", True)
                clip.setdefault("has_source_audio", False)
                clip.setdefault("transformative_elements", ["narration_overlay", "ken_burns", "color_grade"])
                clip.setdefault("duration_sec", 5.0)

            report = guard.check_timeline(clips)
            compliance = report["compliance_rate"]
            blocked = report["blocked"]

            if blocked > 0:
                inform(f"Fair use check: {compliance} compliant, {blocked} segment(s) blocked", "warn")
                for v in report["violations_log"][:3]:
                    print(f"  {RD}  Segment {v['segment']}: {', '.join(v['violations'][:2])}{R}")
            else:
                inform(f"Fair use check: {compliance} — all segments compliant ✓", "success")
    except ImportError:
        pass
    except Exception as e:
        inform(f"Fair use check error (non-fatal): {e}", "warn")

    inform("Assembling video — Ken Burns, color grade, audio mix, chapter cards…", "info")
    inform("This takes a while. Do not close the terminal.", "info")

    cmd = [
        PYTHON, "pipeline/video_assembler.py",
        "--brand", "fern_clone",
        "--narration", narration,
        "--footage",   footage,
        "--music",     music,
        "--out",       out_path,
    ]
    if Path(storyboard).exists():
        cmd += ["--storyboard", storyboard]

    rc, _ = run_live(cmd)

    if Path(out_path).exists():
        sz = Path(out_path).stat().st_size // (1024 * 1024)
        state["paths"]["video"] = out_path
        state["paths"]["timeline"] = str(Path(out_path).parent / "timeline.json")
        step_done(f"Video assembled → {out_path}  ({sz}MB)")
        return True
    step_fail(f"video_assembler failed (code {rc})")
    return False


def stage_qa_video(state: dict) -> bool:
    """Run check_fern_video.py and show QA results. User approves upload."""
    print_header(state, "qa_video")

    video    = state["paths"].get("video", f"output/{state['slug']}/final.mp4")
    timeline = state["paths"].get("timeline", "")
    music    = state["paths"].get("music", "assets/music/track.mp3")

    inform("Running final video QA — 8 checks against Fern benchmarks…", "info")

    cmd = [PYTHON, "check_fern_video.py", video]
    if timeline and Path(timeline).exists():
        cmd += ["--timeline", timeline]
    if music and Path(music).exists():
        cmd += ["--music", music]

    rc, output = run_live(cmd)

    # Parse outcome
    passed = rc == 0
    verdict_line = next((l for l in output.splitlines() if "Verdict:" in l), "")
    is_fail = "FAIL" in verdict_line and rc != 0
    is_warn = "WARN" in verdict_line
    is_pass = "PASS" in verdict_line

    print()
    if is_fail:
        inform("Video QA: FAIL — fix issues before uploading.", "error")
        answer = ask(
            "Video has FAIL checks above. Upload anyway? (Not recommended)",
            options=["no — fix issues first", "yes — override and upload anyway"],
            default="no",
        )
        if answer.startswith("n"):
            inform("Re-run after fixing the issues. State saved — run again to resume.", "info")
            sys.exit(0)
    elif is_warn:
        inform("Video QA: WARN — warnings present but not hard failures.", "warn")
        answer = ask(
            "Video has warnings above. Ready to watch and upload?",
            options=["yes — looks good", "no — re-assemble first"],
            default="yes",
        )
        if not answer.startswith("y"):
            state["stage"] = "assemble"
            return False
    else:
        step_done("Video QA: PASS — all checks green")

    # Final manual review
    print()
    print(f"  {MG}{BOLD}━━━  YOUR TURN  ━━━{R}")
    print()
    print(f"  {BOLD}Watch the full video before uploading:{R}")
    print(f"  {DIM}  open {video}{R}")
    print()
    print(f"  {DIM}Look for: wrong footage at key moments, audio sync issues,{R}")
    print(f"  {DIM}chapter card text correct, pacing feels right, nothing offensive{R}")
    print()

    answer = ask(
        "Have you watched the video? Is it ready to upload to YouTube?",
        options=["yes — upload it", "no — needs changes"],
        default="yes",
    )
    if not answer.startswith("y"):
        inform("OK — re-assemble or fix footage, then run again to re-QA.", "info")
        state["stage"] = "assemble"
        return False

    state["paths"]["ready_to_upload"] = video
    return True


def stage_done(state: dict):
    """Final stage — tell user how to upload."""
    print_header(state, "done")
    video = state["paths"].get("video", f"output/{state['slug']}/final.mp4")

    print(f"  {GR}{BOLD}🎬  VIDEO IS READY TO UPLOAD!{R}")
    print()
    print(f"  {BOLD}File:{R}  {WH}{video}{R}")
    print()
    print(f"  {BOLD}Upload steps:{R}")
    print(f"  {DIM}1. Go to studio.youtube.com → Upload video{R}")
    print(f"  {DIM}2. Select: {video}{R}")
    print(f"  {DIM}3. Title: use Claude Code → paste TITLE_ANGLE_FORMULA.json → ask for 3 options{R}")
    print(f"  {DIM}4. Thumbnail: follow THUMBNAIL_FORMULA.json{R}")
    print(f"  {DIM}5. Description: include chapter timestamps from timeline.json{R}")
    print(f"  {DIM}6. Tags: topic keywords + your brand name{R}")
    print(f"  {DIM}7. Schedule or publish{R}")
    print()
    print(f"  {GR}{BOLD}Done. Great work.{R}")
    print()


# ── Stage router ──────────────────────────────────────────────────────────────

STAGE_FUNCS = {
    "topic":      stage_topic,
    "brief":      stage_brief,
    "validate":   stage_validate,
    "script":     stage_script,
    "enhance":    stage_enhance,
    "qa_script":  stage_qa_script,
    "storyboard": stage_storyboard,
    "director":   stage_director,
    "voice":      stage_voice,
    "music":      stage_music,
    "footage":    stage_footage,
    "assemble":   stage_assemble,
    "qa_video":   stage_qa_video,
}


def run_from(state: dict, from_stage: str):
    """Walk through stages from from_stage onward."""
    start_idx = STAGE_ORDER.index(from_stage)

    for stage in STAGE_ORDER[start_idx:]:
        if stage == "done":
            stage_done(state)
            # Mark production complete
            state["stage"] = "done"
            save_state(state)
            break

        state["stage"] = stage
        save_state(state)

        fn = STAGE_FUNCS.get(stage)
        if fn is None:
            continue

        success = fn(state)
        save_state(state)

        if success:
            if stage not in state["completed"]:
                state["completed"].append(stage)
            save_state(state)
        else:
            # Stage returned False — either go back or stop
            # state["stage"] may have been changed by the stage fn
            inform(f"Stage '{stage}' needs attention. Resuming from: {state.get('stage', stage)}", "warn")
            run_from(state, state.get("stage", stage))
            return


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Interactive Fern pipeline runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--topic",   help="Pre-set topic name (skip selection prompt)")
    ap.add_argument("--from",    dest="from_stage",
                    choices=STAGE_ORDER,
                    help="Start from a specific stage (skips earlier stages)")
    ap.add_argument("--list",    action="store_true", help="List all stages and exit")
    ap.add_argument("--status",  action="store_true", help="Show saved state and exit")
    ap.add_argument("--reset",   action="store_true", help="Clear saved state and start fresh")
    args = ap.parse_args()

    if args.list:
        print(f"\n{BOLD}Pipeline Stages:{R}")
        for i, s in enumerate(STAGE_ORDER):
            manual = f"  {MG}(manual){R}" if s in MANUAL_STAGES else ""
            print(f"  {i+1:2d}.  {WH}{s:<12}{R}  {STAGE_LABELS[s]}{manual}")
        print()
        return

    if args.reset:
        STATE_FILE.unlink(missing_ok=True)
        print(f"{GR}State cleared.{R}")
        return

    state = load_state()

    if args.status:
        print(f"\n{BOLD}Current Pipeline State:{R}")
        print(f"  Topic:     {state.get('topic') or '(none)'}")
        print(f"  Stage:     {state.get('stage')}")
        print(f"  Completed: {', '.join(state.get('completed', [])) or '(none)'}")
        print(f"  State file: {STATE_FILE}")
        print()
        return

    # Apply CLI overrides
    if args.topic:
        state["topic"] = args.topic
        state["slug"]  = slug_from_topic(args.topic)

    if args.reset or not STATE_FILE.exists():
        state = {"stage": "topic", "topic": state.get("topic",""),
                 "slug": state.get("slug",""), "completed": [], "paths": {}}
        save_state(state)

    # Determine start stage
    from_stage = args.from_stage or state.get("stage", "topic")
    if from_stage not in STAGE_ORDER:
        from_stage = "topic"

    # Greeting
    print()
    print(f"{CY}{BOLD}{'═' * min(_cols()-2, 92)}{R}")
    print(f"{CY}{BOLD}  FERN PIPELINE RUNNER  {R}{DIM}— Interactive video production conductor{R}")
    print(f"{CY}{BOLD}{'═' * min(_cols()-2, 92)}{R}")
    print()

    if state.get("topic") and from_stage != "topic":
        print(f"  {DIM}Resuming from stage: {R}{WH}{BOLD}{from_stage}{R}{DIM}  ·  Topic: {R}{WH}{state['topic']}{R}")
        print(f"  {DIM}Completed: {', '.join(state.get('completed', [])) or 'none'}{R}")
        print()
        answer = ask(
            f"Resume from '{from_stage}' for topic: {state['topic']}?",
            options=["yes — resume", "no — start fresh from topic selection"],
            default="yes",
        )
        if not answer.startswith("y"):
            state = {"stage": "topic", "topic": "", "slug": "",
                     "completed": [], "paths": {}}
            save_state(state)
            from_stage = "topic"
    else:
        print(f"  {DIM}Ctrl+C at any time to pause. Run again to resume from where you stopped.{R}")
        print()

    run_from(state, from_stage)


if __name__ == "__main__":
    main()
