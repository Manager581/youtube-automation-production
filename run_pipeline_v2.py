#!/usr/bin/env python3
"""
run_pipeline_v2.py -- LearnByLeo production pipeline orchestrator.

Runs every automated step with live terminal output. Stops at decision points
and asks you in plain English before proceeding. You always have final say.

State is saved to .pipeline_v2_run.json after each stage -- Ctrl+C and resume
anytime by running again with no arguments.

Usage:
    python run_pipeline_v2.py                          # Start fresh or resume
    python run_pipeline_v2.py --topic "Secret Scores"  # Pre-set topic
    python run_pipeline_v2.py --stage voice            # Resume from stage
    python run_pipeline_v2.py --stage all               # Run everything
    python run_pipeline_v2.py --list                    # List all stages
    python run_pipeline_v2.py --status                  # Show current state

Stages in order:
     1. topic           -> Run topic_radar (find story candidates)
     2. comments        -> Mine audience signals
     3. brief           -> Research brief (structured)
     4. validate        -> Story validator (GO/SKIP)
     5. script          -> YOU write the script (Claude Code interactive)
     6. enhance         -> Script enhancer (add markers)
     7. qa_script       -> LearnByLeo script QA gate (must pass)
     8. voice           -> Voice narration (F5-TTS)
     9. qa_voice        -> LearnByLeo voice QA gate
    10. storyboard      -> Visual brief generation
    11. director        -> Editorial decisions pass
    12. insert_pauses   -> Split narration WAV per delivery rules
    13. music           -> CC0 music sourcing
    14. pre_duck        -> Create ducked music track
    15. normalize_sfx   -> Normalize SFX levels
    16. footage         -> Source footage
    17. verify_footage  -> Verify footage with Claude vision
    18. web_images      -> Source web images (Pexels/Pixabay)
    19. davinci         -> Build DaVinci Resolve timeline
    20. qa_video        -> Final video QA (must pass)
    21. done            -> Render + upload (manual)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────────────────

R    = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
GR   = "\033[92m"
YL   = "\033[93m"
RD   = "\033[91m"
CY   = "\033[96m"
BL   = "\033[94m"
MG   = "\033[95m"
WH   = "\033[97m"

# ── Constants ────────────────────────────────────────────────────────────────

STATE_FILE = Path(".pipeline_v2_run.json")
PYTHON     = str(Path("venv/bin/python"))

STAGE_ORDER = [
    "topic", "comments", "brief", "validate", "script", "enhance",
    "qa_script", "voice", "qa_voice", "storyboard", "director",
    "insert_pauses", "music", "pre_duck", "normalize_sfx",
    "footage", "verify_footage", "web_images", "davinci",
    "qa_video", "done",
]

STAGE_LABELS = {
    "topic":          "Topic Research",
    "comments":       "Audience Mining",
    "brief":          "Research Brief",
    "validate":       "Story Validation",
    "script":         "Script Writing  <- YOUR TURN",
    "enhance":        "Script Enhancement",
    "qa_script":      "Script QA (LearnByLeo)",
    "voice":          "Voice Narration (F5-TTS)",
    "qa_voice":       "Voice QA (LearnByLeo)",
    "storyboard":     "Storyboard Generation",
    "director":       "Director's Pass",
    "insert_pauses":  "Insert Pauses",
    "music":          "Music Selection (CC0)",
    "pre_duck":       "Pre-Duck Music",
    "normalize_sfx":  "Normalize SFX",
    "footage":        "Footage Sourcing",
    "verify_footage": "Footage Verification",
    "web_images":     "Web Image Sourcing",
    "davinci":        "DaVinci Timeline Build",
    "qa_video":       "Final Video QA",
    "done":           "Render + Upload  <- YOUR TURN",
}

MANUAL_STAGES = {"script", "done"}

# Stages that use pipeline_v2/ instead of pipeline/
PIPELINE_V2_STAGES = {
    "enhance", "storyboard", "director", "verify_footage", "web_images",
}


# ── State management ────────────────────────────────────────────────────────

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
    s = topic.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:50]


# ── Terminal helpers ─────────────────────────────────────────────────────────

def _cols():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 100


def _line(char="-"):
    return char * min(_cols() - 4, 90)


def print_header(state: dict, stage: str):
    stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0
    total     = len(STAGE_ORDER) - 1
    completed = state.get("completed", [])
    topic     = state.get("topic", "")

    print()
    print(f"{CY}{BOLD}{'=' * min(_cols()-2, 92)}{R}")
    print(f"{CY}{BOLD}  LEARNBYLEO PIPELINE v2{R}  {DIM}--  stage {stage_idx+1} of {total}{R}")
    if topic:
        print(f"  {DIM}Topic: {R}{WH}{BOLD}{topic}{R}")
    print(f"{CY}{BOLD}{'=' * min(_cols()-2, 92)}{R}")
    print()

    for i, s in enumerate(STAGE_ORDER):
        if s == "done":
            continue
        label = STAGE_LABELS[s]
        if s in completed:
            icon = f"{GR}+{R}"
            col  = DIM
        elif s == stage:
            icon = f"{CY}>{R}"
            col  = f"{CY}{BOLD}"
        else:
            icon = f"{DIM}o{R}"
            col  = DIM
        print(f"  {icon}  {col}{label:<35}{R}")
    print()
    print(f"  {CY}{BOLD}{_line()}{R}")
    print()


def ask(question: str, options: list = None, default: str = None) -> str:
    print()
    print(f"  {YL}{BOLD}+{'=' * 62}+{R}")
    print(f"  {YL}{BOLD}|  YOUR DECISION{R}{' ' * 48}{YL}{BOLD}|{R}")
    print(f"  {YL}{BOLD}|{R}  {question:<60}{YL}{BOLD}|{R}")
    if options:
        opts = "  /  ".join(options)
        print(f"  {YL}{BOLD}|{R}  {DIM}Options: {opts}{R}{' ' * max(0, 51-len(opts))}{YL}{BOLD}|{R}")
    if default:
        print(f"  {YL}{BOLD}|{R}  {DIM}[Enter] = {default}{R}{' ' * max(0, 50-len(default))}{YL}{BOLD}|{R}")
    print(f"  {YL}{BOLD}+{'=' * 62}+{R}")
    print()

    prompt = f"  {YL}>{R} "
    try:
        answer = input(prompt).strip()
    except KeyboardInterrupt:
        print(f"\n\n  {YL}Paused. Run again to resume from this stage.{R}\n")
        sys.exit(0)

    if not answer and default:
        return default.lower() if options else default
    return answer.lower() if options else answer


def inform(message: str, style: str = "info"):
    colors = {"info": CY, "success": GR, "warn": YL, "error": RD, "manual": MG}
    c = colors.get(style, CY)
    print(f"\n  {c}{BOLD}  {message}{R}\n")


def step_done(label: str):
    print(f"\n  {GR}{BOLD}+  {label}{R}\n")


def step_fail(label: str):
    print(f"\n  {RD}{BOLD}X  {label}{R}\n")


# ── Subprocess helpers ───────────────────────────────────────────────────────

def run_live(cmd: list, label: str = "") -> tuple[int, str]:
    """
    Run a command with live stdout/stderr streaming.
    Returns (returncode, combined_output_text).
    """
    print(f"  {DIM}Running: {' '.join(cmd[:6])}{R}")
    print(f"  {DIM}{_line('.')}{R}")

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
            disp = line
            if any(w in line for w in ["ERROR", "FAIL", "Error", "Traceback"]):
                disp = f"{RD}{line}{R}"
            elif any(w in line for w in ["Done", "PASS", "complete"]):
                disp = f"{GR}{line}{R}"
            elif any(w in line for w in ["WARNING", "WARN", "skipping"]):
                disp = f"{YL}{line}{R}"
            elif any(w in line for w in ["[", "->", ">"]):
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

    print(f"  {DIM}{_line('.')}{R}")
    return rc, "\n".join(output_lines)


# ── Stage implementations ───────────────────────────────────────────────────

def stage_topic(state: dict) -> bool:
    """Run topic_radar, display results, ask user to pick."""
    print_header(state, "topic")
    inform("Running topic radar -- scanning for story candidates...", "info")

    rc, output = run_live([PYTHON, "pipeline/topic_radar.py"])

    candidates = []
    for candidate_path in sorted(Path("research").glob("*/topic_candidates.json"),
                                  key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(candidate_path.read_text())
            raw = data if isinstance(data, list) else data.get("candidates", [])
            candidates = raw[:10]
            break
        except Exception:
            pass

    if candidates:
        print(f"\n  {BOLD}{'-' * 60}{R}")
        print(f"  {BOLD}Top Candidates Found:{R}")
        print()
        for i, c in enumerate(candidates[:8]):
            topic_name = c.get("topic") or c.get("title") or c.get("query") or str(c)[:60]
            score = c.get("score") or c.get("viral_score") or c.get("total_score") or "?"
            score_color = GR if isinstance(score, (int, float)) and score >= 85 else YL
            print(f"  {WH}{i+1:>2}.{R}  {topic_name:<52}  {score_color}score:{score}{R}")
        print()

    print(f"  {BOLD}{'-' * 60}{R}")
    print()
    topic_input = ask(
        "Which topic do you want to produce?",
        options=["enter number (1-8)", "type your own topic"],
    )

    if topic_input.isdigit():
        idx = int(topic_input) - 1
        if 0 <= idx < len(candidates):
            c = candidates[idx]
            chosen = c.get("topic") or c.get("title") or c.get("query") or topic_input
        else:
            inform("Number out of range -- enter the topic name directly.", "warn")
            chosen = ask("Topic name:")
    else:
        chosen = topic_input.strip()

    if not chosen:
        inform("No topic entered. Try again.", "error")
        return False

    state["topic"] = chosen
    state["slug"]  = slug_from_topic(chosen)
    step_done(f'Topic selected: "{chosen}"  ->  slug: {state["slug"]}')
    return True


def stage_comments(state: dict) -> bool:
    """Run comments_miner.py."""
    print_header(state, "comments")
    inform(f"Mining audience signals for: {state['topic']}", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/comments_miner.py",
        "--query", state["topic"],
    ])

    if rc == 0:
        step_done("Audience signals mined")
        return True
    step_fail(f"comments_miner returned code {rc}")
    # Non-critical -- proceed anyway
    inform("Comments mining failed but is non-critical. Proceeding.", "warn")
    return True


def stage_brief(state: dict) -> bool:
    """Run research_brief.py."""
    print_header(state, "brief")
    inform(f"Building research brief for: {state['topic']}", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/research_brief.py",
        "--query", state["topic"],
    ])

    brief_candidates = list(Path("research").glob(f"*/briefs/*{state['slug']}*.json"))
    if brief_candidates:
        brief_path = str(sorted(brief_candidates, key=lambda p: p.stat().st_mtime)[-1])
        state["paths"]["brief"] = brief_path
        step_done(f"Brief saved -> {brief_path}")
    elif rc == 0:
        step_done("Brief generated")
    else:
        step_fail(f"research_brief returned code {rc}")
        return False
    return True


def stage_validate(state: dict) -> bool:
    """Run story_validator.py."""
    print_header(state, "validate")
    inform(f"Validating story viability for: {state['topic']}", "info")

    rc, output = run_live([
        PYTHON, "pipeline/story_validator.py",
        "--query", state["topic"],
    ])

    verdict = "UNKNOWN"
    score = "?"
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
        inform("Validator says SKIP. Low story viability.", "warn")
        answer = ask(
            "The validator recommends skipping. Proceed anyway?",
            options=["yes", "no -- go back to topic"],
            default="no",
        )
        if not answer.startswith("y"):
            state["stage"] = "topic"
            return False

    elif verdict == "NEEDS WORK":
        answer = ask(
            f"Validator: NEEDS WORK (score {score}). Proceed to scripting?",
            options=["yes", "no -- pick a different topic"],
            default="yes",
        )
        if not answer.startswith("y"):
            state["stage"] = "topic"
            return False
    else:
        step_done("Story validated -- GO")

    return True


def stage_script(state: dict) -> bool:
    """Manual stage -- user writes the script in Claude Code."""
    print_header(state, "script")

    slug     = state["slug"]
    raw_path = Path(f"scripts/raw_{slug}.txt")

    print(f"  {MG}{BOLD}===  YOUR TURN  ==={R}")
    print()
    print(f"  Write the script in THIS Claude Code session.")
    print()
    print(f"  {BOLD}Instructions:{R}")
    print(f"  {DIM}1. Tell Claude: \"Write a full script on: {state['topic']}\"{R}")
    print(f"  {DIM}2. Reference: playbook/scripting.json for structure rules{R}")
    print(f"  {DIM}3. Target: 1,800-4,500 words, 10-25 min @ 120-180 WPM{R}")
    print(f"  {DIM}4. Green/Purple alternation throughout (P-SC-01){R}")
    print(f"  {DIM}5. But/Therefore flow, not And/Then (P-SC-03){R}")
    print(f"  {DIM}6. Conversational tone (P-SC-05){R}")
    print(f"  {DIM}7. Save to: {raw_path}{R}")
    print()

    while True:
        answer = ask(
            f"Have you saved your script to {raw_path}?",
            options=["yes -- continue", "no -- still writing"],
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
            inform("Take your time -- run this script again when ready.", "info")
            print(f"  {DIM}Your saved state will resume here next run.{R}\n")
            sys.exit(0)


def stage_enhance(state: dict) -> bool:
    """Run script_enhancer.py from pipeline_v2/."""
    print_header(state, "enhance")

    slug     = state["slug"]
    raw_path = state["paths"].get("script_raw", f"scripts/raw_{slug}.txt")
    out_path = f"scripts/enhanced_{slug}.txt"

    inform("Adding BEAT / PAUSE / VOICE markers to script...", "info")

    rc, _ = run_live([
        PYTHON, "pipeline_v2/script_enhancer.py",
        "--input", raw_path,
        "--output", out_path,
    ])

    if Path(out_path).exists():
        state["paths"]["script_enhanced"] = out_path
        step_done(f"Enhanced script -> {out_path}")
        return True

    # Fallback to pipeline/ if pipeline_v2/ version doesn't exist
    inform("pipeline_v2/script_enhancer.py not found, trying pipeline/...", "warn")
    rc, _ = run_live([
        PYTHON, "pipeline/script_enhancer.py",
        "--input", raw_path,
        "--output", out_path,
    ])

    if Path(out_path).exists():
        state["paths"]["script_enhanced"] = out_path
        step_done(f"Enhanced script -> {out_path}")
        return True

    step_fail(f"script_enhancer failed (code {rc})")
    return False


def stage_qa_script(state: dict) -> bool:
    """Run check_learnbyleo_script.py -- must pass to proceed."""
    print_header(state, "qa_script")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")

    inform("Running LearnByLeo script QA...", "info")
    rc, output = run_live([
        PYTHON, "check_learnbyleo_script.py",
        enhanced, state.get("topic", ""),
    ])

    # Extract score
    score = None
    for line in output.splitlines():
        m = re.search(r"OVERALL.*?(\d+)/100", line)
        if m:
            score = int(m.group(1))
        m2 = re.search(r"VERDICT:\s*(\w+)", line)
        if m2:
            verdict = m2.group(1)

    if score is None:
        inform("Could not parse script score.", "warn")
        answer = ask(
            "Script QA output above. Continue to voice?",
            options=["yes", "no -- rewrite first"],
            default="yes",
        )
        return answer.startswith("y")

    score_color = GR if score >= 70 else (YL if score >= 55 else RD)
    print(f"\n  {BOLD}LearnByLeo Script Score:  {score_color}{BOLD}{score}/100{R}")
    print()

    if score >= 70:
        step_done(f"Script passes ({score}/100) -- proceeding to voice")
        return True
    elif score >= 55:
        answer = ask(
            f"Script scored {score}/100 (target: 70+). Weak but workable. Proceed?",
            options=["yes", "no -- rewrite"],
            default="no",
        )
        return answer.startswith("y")
    else:
        inform(f"Script scored {score}/100 -- below minimum. Rewrite recommended.", "warn")
        answer = ask(
            "Override and proceed anyway? (Not recommended below 55)",
            options=["yes -- override", "no -- go back to script"],
            default="no",
        )
        if answer.startswith("y"):
            return True
        state["stage"] = "script"
        return False


def stage_voice(state: dict) -> bool:
    """Run voice_generator.py (F5-TTS)."""
    print_header(state, "voice")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")
    out_dir  = f"audio/{slug}"

    inform("Generating voice narration with F5-TTS...", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/voice_generator.py",
        "--script", enhanced,
        "--output-dir", out_dir,
    ])

    narration = Path(out_dir) / "narration.wav"
    if narration.exists():
        state["paths"]["narration"] = str(narration)
        state["paths"]["audio_dir"] = out_dir
        step_done(f"Narration -> {narration}")
        return True

    step_fail(f"voice_generator failed (code {rc})")
    return False


def stage_qa_voice(state: dict) -> bool:
    """Run check_learnbyleo_voice.py -- QA gate."""
    print_header(state, "qa_voice")

    slug      = state["slug"]
    narration = state["paths"].get("narration", f"audio/{slug}/narration.wav")
    enhanced  = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")

    inform("Running LearnByLeo voice QA...", "info")

    cmd = [PYTHON, "check_learnbyleo_voice.py", narration]
    if Path(enhanced).exists():
        cmd.extend(["--script", enhanced])

    rc, output = run_live(cmd)

    if rc == 0:
        step_done("Voice QA passed")
        return True
    else:
        # FAIL -- offer to regenerate or override
        inform("Voice QA FAILED. Issues detected in the narration.", "error")
        answer = ask(
            "Voice QA failed. What do you want to do?",
            options=["retry -- regenerate voice", "override -- proceed anyway"],
            default="retry",
        )
        if answer.startswith("o"):
            return True
        state["stage"] = "voice"
        return False


def stage_storyboard(state: dict) -> bool:
    """Run storyboard_generator.py from pipeline_v2/."""
    print_header(state, "storyboard")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")
    out_path = f"storyboards/{slug}.json"

    inform("Generating per-segment visual brief...", "info")

    # Try pipeline_v2/ first, fall back to pipeline/
    script_path = "pipeline_v2/storyboard_generator.py"
    if not Path(script_path).exists():
        script_path = "pipeline/storyboard_generator.py"

    rc, _ = run_live([
        PYTHON, script_path,
        "--script", enhanced,
        "--out", out_path,
    ])

    if Path(out_path).exists():
        state["paths"]["storyboard"] = out_path
        try:
            sb = json.loads(Path(out_path).read_text())
            n = len(sb) if isinstance(sb, list) else len(sb.get("segments", sb.get("scenes", [])))
        except Exception:
            n = "?"
        step_done(f"Storyboard -> {out_path}  ({n} segments)")
        return True
    step_fail(f"storyboard_generator failed (code {rc})")
    return False


def stage_director(state: dict) -> bool:
    """Run director.py -- full-context editorial pass."""
    print_header(state, "director")

    slug       = state["slug"]
    enhanced   = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")
    storyboard = state["paths"].get("storyboard", f"storyboards/{slug}.json")

    inform("Running editorial director pass...", "info")

    script_path = "pipeline_v2/director.py"
    if not Path(script_path).exists():
        script_path = "pipeline/director.py"

    rc, _ = run_live([
        PYTHON, script_path,
        "--script", enhanced,
        "--storyboard", storyboard,
    ])

    if rc == 0:
        step_done("Director pass complete")
        return True
    step_fail(f"director failed (code {rc})")
    return False


def stage_insert_pauses(state: dict) -> bool:
    """Split narration WAV per LearnByLeo delivery rules (pauses for pacing)."""
    print_header(state, "insert_pauses")

    slug      = state["slug"]
    narration = state["paths"].get("narration", f"audio/{slug}/narration.wav")

    inform("Inserting delivery pauses per LearnByLeo retention rules...", "info")

    # Check if a dedicated pause insertion script exists
    pause_script = "pipeline_v2/insert_pauses.py"
    if not Path(pause_script).exists():
        inform("No dedicated pause insertion script found. Skipping (non-critical).", "warn")
        step_done("Pause insertion skipped (no pipeline_v2/insert_pauses.py)")
        return True

    rc, _ = run_live([
        PYTHON, pause_script,
        "--audio", narration,
    ])

    if rc == 0:
        step_done("Pauses inserted")
        return True
    step_fail(f"insert_pauses failed (code {rc})")
    # Non-critical
    inform("Pause insertion failed but is non-critical. Proceeding.", "warn")
    return True


def stage_music(state: dict) -> bool:
    """Run music_sourcer.py -- CC0 music."""
    print_header(state, "music")

    slug     = state["slug"]
    enhanced = state["paths"].get("script_enhanced", f"scripts/enhanced_{slug}.txt")

    inform("Sourcing CC0 background music...", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/music_sourcer.py",
        "--script", enhanced,
    ])

    music_path = Path(f"assets/music/track.mp3")
    if music_path.exists():
        state["paths"]["music"] = str(music_path)
        step_done(f"Music -> {music_path}")
        return True

    if rc == 0:
        step_done("Music sourced")
        return True

    step_fail(f"music_sourcer failed (code {rc})")
    # Non-critical
    inform("Music sourcing failed. You can add music manually later.", "warn")
    return True


def stage_pre_duck(state: dict) -> bool:
    """Create ducked music track (lower music volume under narration)."""
    print_header(state, "pre_duck")

    slug      = state["slug"]
    narration = state["paths"].get("narration", f"audio/{slug}/narration.wav")
    music     = state["paths"].get("music", "assets/music/track.mp3")

    inform("Creating ducked music track...", "info")

    duck_script = "pipeline_v2/create_ducked_music.py"
    if not Path(duck_script).exists():
        # Try inline ffmpeg ducking
        out_path = f"audio/{slug}/music_ducked.wav"
        if Path(music).exists() and Path(narration).exists():
            inform("No dedicated ducking script. Using ffmpeg sidechain compression...", "info")
            rc, _ = run_live([
                "ffmpeg", "-y",
                "-i", music,
                "-i", narration,
                "-filter_complex",
                "[0:a][1:a]sidechaincompress=threshold=0.02:ratio=6:attack=200:release=1000[out]",
                "-map", "[out]",
                out_path,
            ])
            if Path(out_path).exists():
                state["paths"]["music_ducked"] = out_path
                step_done(f"Ducked music -> {out_path}")
                return True
        inform("Ducking skipped (missing music or narration).", "warn")
        return True

    rc, _ = run_live([
        PYTHON, duck_script,
        "--music", music,
        "--narration", narration,
    ])

    if rc == 0:
        step_done("Music ducked")
        return True
    inform("Music ducking failed (non-critical). Proceeding.", "warn")
    return True


def stage_normalize_sfx(state: dict) -> bool:
    """Normalize SFX levels to match narration."""
    print_header(state, "normalize_sfx")

    inform("Normalizing SFX levels...", "info")

    sfx_dir = Path("assets/sfx")
    if not sfx_dir.exists() or not list(sfx_dir.glob("*.wav")):
        inform("No SFX files found in assets/sfx/. Skipping.", "warn")
        step_done("SFX normalization skipped (no files)")
        return True

    normalize_script = "pipeline_v2/normalize_sfx.py"
    if not Path(normalize_script).exists():
        # Inline normalization with ffmpeg
        inform("No dedicated normalize script. Using ffmpeg loudnorm on each SFX...", "info")
        sfx_files = list(sfx_dir.glob("*.wav"))
        normalized = 0
        for sfx in sfx_files:
            out = sfx.parent / f"{sfx.stem}_norm.wav"
            if out.exists():
                normalized += 1
                continue
            rc, _ = run_live([
                "ffmpeg", "-y", "-i", str(sfx),
                "-af", "loudnorm=I=-18:TP=-2:LRA=7",
                str(out),
            ])
            if rc == 0:
                normalized += 1
        step_done(f"Normalized {normalized}/{len(sfx_files)} SFX files")
        return True

    rc, _ = run_live([PYTHON, normalize_script])
    if rc == 0:
        step_done("SFX normalized")
        return True
    inform("SFX normalization failed (non-critical).", "warn")
    return True


def stage_footage(state: dict) -> bool:
    """Run footage_sourcer.py."""
    print_header(state, "footage")

    slug       = state["slug"]
    storyboard = state["paths"].get("storyboard", f"storyboards/{slug}.json")

    inform("Sourcing footage from archives...", "info")

    rc, _ = run_live([
        PYTHON, "pipeline/footage_sourcer.py",
        "--storyboard", storyboard,
    ])

    if rc == 0:
        step_done("Footage sourced")
        return True
    step_fail(f"footage_sourcer failed (code {rc})")
    return False


def stage_verify_footage(state: dict) -> bool:
    """Run footage_verifier.py with Claude vision."""
    print_header(state, "verify_footage")

    slug       = state["slug"]
    storyboard = state["paths"].get("storyboard", f"storyboards/{slug}.json")

    inform("Verifying footage with Claude vision...", "info")

    script_path = "pipeline_v2/footage_verifier.py"
    if not Path(script_path).exists():
        script_path = "pipeline/footage_verifier.py"

    rc, _ = run_live([
        PYTHON, script_path,
        "--storyboard", storyboard,
    ])

    if rc == 0:
        step_done("Footage verified")
        return True
    inform("Footage verification had issues. Check output above.", "warn")
    return True  # Non-critical


def stage_web_images(state: dict) -> bool:
    """Run web_image_sourcer.py (Pexels/Pixabay)."""
    print_header(state, "web_images")

    slug       = state["slug"]
    storyboard = state["paths"].get("storyboard", f"storyboards/{slug}.json")

    inform("Sourcing web images (Pexels/Pixabay)...", "info")

    script_path = "pipeline_v2/web_image_sourcer.py"
    if not Path(script_path).exists():
        script_path = "pipeline/web_image_sourcer.py"

    if not Path(script_path).exists():
        inform("No web_image_sourcer found. Skipping.", "warn")
        return True

    rc, _ = run_live([
        PYTHON, script_path,
        "--storyboard", storyboard,
    ])

    if rc == 0:
        step_done("Web images sourced")
        return True
    inform("Web image sourcing had issues. Check output above.", "warn")
    return True


def stage_davinci(state: dict) -> bool:
    """Run davinci_timeline_builder.py."""
    print_header(state, "davinci")

    slug       = state["slug"]
    storyboard = state["paths"].get("storyboard", f"storyboards/{slug}.json")
    narration  = state["paths"].get("narration", f"audio/{slug}/narration.wav")

    inform("Building DaVinci Resolve timeline...", "info")

    # Try pipeline_v2/ first
    script_path = "pipeline_v2/davinci_timeline_builder.py"
    if not Path(script_path).exists():
        script_path = "pipeline/davinci_timeline_builder.py"

    cmd = [
        PYTHON, script_path,
        "--storyboard", storyboard,
        "--narration", narration,
    ]

    # Add music if available
    music = state["paths"].get("music_ducked") or state["paths"].get("music")
    if music and Path(music).exists():
        cmd.extend(["--music", music])

    rc, _ = run_live(cmd)

    if rc == 0:
        step_done("DaVinci timeline built")
        return True
    step_fail(f"davinci_timeline_builder failed (code {rc})")
    return False


def stage_qa_video(state: dict) -> bool:
    """Run check_learnbyleo_video.py -- final QA gate."""
    print_header(state, "qa_video")

    slug = state["slug"]

    inform("Running final video QA...", "info")

    # Look for the rendered video
    video_candidates = (
        list(Path(f"output/{slug}").glob("*.mp4")) +
        list(Path("output").glob(f"*{slug}*.mp4")) +
        list(Path(".").glob(f"*{slug}*.mp4"))
    )

    if not video_candidates:
        inform("No rendered video found. Render in DaVinci Resolve first, then re-run this stage.", "warn")
        answer = ask(
            "No video file found. Skip QA and mark as done?",
            options=["yes -- skip QA", "no -- wait for render"],
            default="no",
        )
        if answer.startswith("y"):
            return True
        sys.exit(0)

    video_path = str(sorted(video_candidates, key=lambda p: p.stat().st_mtime)[-1])
    print(f"  {BOLD}Video: {video_path}{R}")

    qa_script = "check_learnbyleo_video.py"
    if not Path(qa_script).exists():
        inform("check_learnbyleo_video.py not found. Skipping final QA.", "warn")
        return True

    rc, output = run_live([PYTHON, qa_script, video_path])

    if rc == 0:
        step_done("Final video QA passed")
        return True
    else:
        inform("Video QA FAILED. Review issues above.", "error")
        answer = ask(
            "Video QA failed. Override and proceed to upload?",
            options=["yes -- override", "no -- fix issues first"],
            default="no",
        )
        return answer.startswith("y")


def stage_done(state: dict) -> bool:
    """Manual stage -- render in DaVinci and upload."""
    print_header(state, "done")

    print(f"  {GR}{BOLD}===  PIPELINE COMPLETE  ==={R}")
    print()
    print(f"  {BOLD}Next steps:{R}")
    print(f"  {DIM}1. Open DaVinci Resolve and review the timeline{R}")
    print(f"  {DIM}2. Make final color/audio adjustments{R}")
    print(f"  {DIM}3. Render to MP4 (H.264, 1080p or 4K){R}")
    print(f"  {DIM}4. Upload to YouTube{R}")
    print(f"  {DIM}5. Set title, description, thumbnail, tags{R}")
    print()
    print(f"  {BOLD}Topic:{R} {state.get('topic', '?')}")
    print(f"  {BOLD}Files:{R}")
    for k, v in state.get("paths", {}).items():
        print(f"    {k}: {v}")
    print()
    return True


# ── Stage dispatcher ─────────────────────────────────────────────────────────

STAGE_FUNCTIONS = {
    "topic":          stage_topic,
    "comments":       stage_comments,
    "brief":          stage_brief,
    "validate":       stage_validate,
    "script":         stage_script,
    "enhance":        stage_enhance,
    "qa_script":      stage_qa_script,
    "voice":          stage_voice,
    "qa_voice":       stage_qa_voice,
    "storyboard":     stage_storyboard,
    "director":       stage_director,
    "insert_pauses":  stage_insert_pauses,
    "music":          stage_music,
    "pre_duck":       stage_pre_duck,
    "normalize_sfx":  stage_normalize_sfx,
    "footage":        stage_footage,
    "verify_footage": stage_verify_footage,
    "web_images":     stage_web_images,
    "davinci":        stage_davinci,
    "qa_video":       stage_qa_video,
    "done":           stage_done,
}


# ── Main loop ────────────────────────────────────────────────────────────────

def run_pipeline(state: dict, start_stage: str = None):
    """Run the pipeline from start_stage to completion."""
    if start_stage:
        if start_stage not in STAGE_ORDER:
            print(f"{RD}Unknown stage: {start_stage}{R}")
            print(f"Valid stages: {', '.join(STAGE_ORDER)}")
            sys.exit(1)
        state["stage"] = start_stage

    current = state.get("stage", "topic")
    if current not in STAGE_ORDER:
        current = "topic"

    start_idx = STAGE_ORDER.index(current)

    for stage in STAGE_ORDER[start_idx:]:
        state["stage"] = stage
        save_state(state)

        if stage == "done":
            STAGE_FUNCTIONS[stage](state)
            state["completed"].append(stage)
            save_state(state)
            break

        func = STAGE_FUNCTIONS[stage]
        success = func(state)

        if success:
            if stage not in state["completed"]:
                state["completed"].append(stage)
            save_state(state)
        else:
            # Stage failed -- state["stage"] may have been rewound
            save_state(state)
            if state["stage"] != stage:
                # Rewound to earlier stage -- restart
                run_pipeline(state)
            return

    print(f"\n  {GR}{BOLD}Pipeline complete.{R}\n")


def main():
    ap = argparse.ArgumentParser(description="LearnByLeo production pipeline v2")
    ap.add_argument("--topic",  help="Pre-set topic (skip topic selection)")
    ap.add_argument("--stage",  help="Start from specific stage (or 'all' for beginning)")
    ap.add_argument("--list",   action="store_true", help="List all stages and exit")
    ap.add_argument("--status", action="store_true", help="Show current state and exit")
    args = ap.parse_args()

    if args.list:
        print(f"\n  {BOLD}Pipeline v2 Stages:{R}\n")
        for i, stage in enumerate(STAGE_ORDER):
            label = STAGE_LABELS[stage]
            manual = "  (manual)" if stage in MANUAL_STAGES else ""
            print(f"  {i+1:>3}. {stage:<20} {label}{manual}")
        print()
        sys.exit(0)

    state = load_state()

    if args.status:
        print(f"\n  {BOLD}Pipeline v2 State:{R}\n")
        print(f"  Stage:     {state.get('stage', '?')}")
        print(f"  Topic:     {state.get('topic', '(none)')}")
        print(f"  Slug:      {state.get('slug', '(none)')}")
        print(f"  Completed: {', '.join(state.get('completed', []))}")
        print(f"\n  {BOLD}Paths:{R}")
        for k, v in state.get("paths", {}).items():
            exists = Path(v).exists() if v else False
            status = f"{GR}exists{R}" if exists else f"{RD}missing{R}"
            print(f"    {k}: {v}  [{status}]")
        print()
        sys.exit(0)

    # Pre-set topic
    if args.topic:
        state["topic"] = args.topic
        state["slug"]  = slug_from_topic(args.topic)
        if "topic" not in state.get("completed", []):
            state.setdefault("completed", []).append("topic")

    # Determine start stage
    start_stage = None
    if args.stage:
        if args.stage.lower() == "all":
            state = {"stage": "topic", "topic": state.get("topic", ""),
                     "slug": state.get("slug", ""), "completed": [], "paths": {}}
            if args.topic:
                state["topic"] = args.topic
                state["slug"] = slug_from_topic(args.topic)
                state["completed"] = ["topic"]
        else:
            start_stage = args.stage

    run_pipeline(state, start_stage)


if __name__ == "__main__":
    main()
