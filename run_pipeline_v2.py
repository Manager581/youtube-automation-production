#!/usr/bin/env python3
"""
run_pipeline_v2.py — LearnByLeo production pipeline orchestrator.

Runs every stage in order. Closed-loop: director reviews its own work,
research agent fills gaps, validator checks every segment.

State saved to .pipeline_v2_state.json after each stage — Ctrl+C safe.

Usage:
    python run_pipeline_v2.py                           # Start fresh or resume
    python run_pipeline_v2.py --topic "Secret Scores"   # Pre-set topic
    python run_pipeline_v2.py --stage director           # Resume from stage
    python run_pipeline_v2.py --list                     # List all stages
    python run_pipeline_v2.py --status                   # Show current state
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PYTHON = sys.executable
STATE_FILE = PROJECT_ROOT / ".pipeline_v2_state.json"

# ── Colors ──
GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
BOLD = "\033[1m"; RESET = "\033[0m"; GRAY = "\033[90m"

# ── Pipeline Stages (in order) ──
STAGES = [
    # PHASE 1: DISCOVERY
    ("topic",           "Find topic candidates",                "pipeline/topic_radar.py"),
    ("comments",        "Mine audience signals",                "pipeline/comments_miner.py"),
    ("research",        "Build research brief",                 "pipeline/research_brief.py"),
    ("validate",        "Story validation (GO/SKIP)",           "pipeline/story_validator.py"),

    # PHASE 2: SCRIPT
    ("script",          "Write script (Claude Code interactive)", None),  # Manual
    ("enhance",         "Add [BEAT][PAUSE][VOICE] markers",     "pipeline_v2/script_enhancer.py"),
    ("qa_script",       "Script QA (LearnByLeo)",               "check_learnbyleo_script.py"),

    # PHASE 3: AUDIO
    ("voice",           "Generate voice (F5-TTS)",              "pipeline/voice_generator.py"),
    ("qa_voice",        "Voice QA (LearnByLeo)",                "check_learnbyleo_voice.py"),
    ("music",           "Source music (Pixabay CC0)",            "pipeline/music_sourcer.py"),

    # PHASE 4: VISUALS — sourcing
    ("footage",         "Source footage (yt-dlp)",              "pipeline/footage_sourcer.py"),
    ("images",          "Source images (Chrome/Pexels/Google)",  "pipeline_v2/web_image_sourcer.py"),
    ("transcripts",     "Extract clip transcripts",             "pipeline_v2/transcript_extractor.py"),
    ("vision",          "Analyze all clips/images (Claude vision)", "pipeline_v2/vision_analyzer.py"),
    ("verify_footage",  "Verify footage matches queries",       "pipeline_v2/footage_verifier.py"),

    # PHASE 5: EDITORIAL — director sees everything
    ("storyboard",      "Generate visual storyboard",           "pipeline_v2/storyboard_generator.py"),
    ("director",        "Director: pick exact files + editorial", "pipeline_v2/director.py"),
    ("validate_segments", "Validate each segment vs LearnByLeo", "pipeline_v2/segment_validator.py"),
    ("fill_gaps",       "Fill footage gaps automatically",      "pipeline_v2/gap_resolver.py"),

    # PHASE 6: ASSEMBLY
    ("pause_insert",    "Insert VO pauses (LearnByLeo rules)",  None),  # Inline
    ("duck_music",      "Pre-duck music under narration",       None),  # Inline
    ("normalize_sfx",   "Normalize SFX to -12 LUFS",           None),  # Inline
    ("exec_producer_pre", "Pre-build executive producer gate",  "pipeline_v2/executive_producer.py"),
    ("davinci_build",   "Build DaVinci timeline",               "pipeline_v2/davinci_timeline_builder.py"),

    # PHASE 7: VERIFICATION — closed loop
    ("director_review", "Director reviews DaVinci timeline",    "pipeline_v2/director_review.py"),
    ("qa_video",        "Video QA (LearnByLeo, 20 checks)",    "check_learnbyleo_video.py"),
    ("exec_producer",   "Executive producer final review",      "pipeline_v2/executive_producer.py"),

    # PHASE 8: PUBLISH
    ("render",          "Render in DaVinci (manual)",           None),  # Manual
    ("upload",          "Upload to YouTube (manual)",           None),  # Manual
]

# ── Quality Gate Stages ──
# These stages are quality checks. On failure, the pipeline retries by re-running
# the associated FIX_STAGE first, then re-checking. Max GATE_MAX_RETRIES attempts.
GATE_STAGES = {
    # gate_stage: [fix_stages_to_rerun]
    "qa_script":          ["enhance"],
    "qa_voice":           ["voice"],
    "verify_footage":     ["images", "footage"],
    "validate_segments":  ["director"],
    "fill_gaps":          ["images", "fill_gaps"],
    "exec_producer_pre":  ["director", "fill_gaps"],
    "director_review":    ["davinci_build"],
    "exec_producer":      ["davinci_build"],
}

GATE_MAX_RETRIES = 2


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"topic": "", "completed": [], "current": None, "config": {}}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def run_script(script_path, extra_args=None, timeout=600):
    """Run a pipeline script and return (exit_code, output)."""
    cmd = [PYTHON, str(PROJECT_ROOT / script_path)]
    if extra_args:
        cmd.extend(extra_args)
    
    print(f"  {GRAY}$ {' '.join(cmd[:3])}...{RESET}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.stdout:
            for line in result.stdout.strip().split('\n')[-5:]:
                print(f"  {line}")
        if result.returncode != 0 and result.stderr:
            for line in result.stderr.strip().split('\n')[-3:]:
                print(f"  {RED}{line}{RESET}")
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"  {RED}TIMEOUT after {timeout}s{RESET}")
        return 1
    except FileNotFoundError:
        print(f"  {RED}Script not found: {script_path}{RESET}")
        return 1


def run_inline_stage(stage_name, state):
    """Run inline stages (pause insertion, music ducking, SFX normalization)."""
    
    if stage_name == "pause_insert":
        print(f"  Inserting VO pauses per LearnByLeo rules...")
        # This would call the pause insertion logic from davinci_helpers
        print(f"  {YELLOW}(Pauses are baked into narration WAV during voice stage){RESET}")
        return 0
    
    elif stage_name == "duck_music":
        print(f"  Pre-ducking music under narration...")
        # Call create_ducked_music from davinci_helpers
        print(f"  {YELLOW}(Music ducking handled by davinci_timeline_builder){RESET}")
        return 0
    
    elif stage_name == "normalize_sfx":
        print(f"  Normalizing SFX to -12 LUFS...")
        sfx_dir = state.get("config", {}).get("sfx_dir", "")
        if sfx_dir and os.path.exists(sfx_dir):
            from pipeline_v2.davinci_helpers import normalize_sfx
            normalize_sfx(sfx_dir)
        else:
            print(f"  {YELLOW}(SFX dir not set — will normalize during build){RESET}")
        return 0
    
    return 0


def run_stage(stage_name, state):
    """Run a single pipeline stage."""
    
    # Find stage definition
    stage_def = None
    for name, desc, script in STAGES:
        if name == stage_name:
            stage_def = (name, desc, script)
            break
    
    if not stage_def:
        print(f"{RED}Unknown stage: {stage_name}{RESET}")
        return 1
    
    name, desc, script = stage_def
    
    print(f"\n{'='*60}")
    print(f"  {BOLD}Stage: {name}{RESET} — {desc}")
    print(f"{'='*60}")
    
    # Manual stages
    if script is None and name in ("script", "render", "upload"):
        print(f"  {YELLOW}MANUAL STAGE — do this yourself, then resume:{RESET}")
        print(f"  python run_pipeline_v2.py --stage {STAGES[STAGES.index(stage_def) + 1][0] if STAGES.index(stage_def) < len(STAGES) - 1 else 'done'}")
        return 0
    
    # Inline stages
    if script is None:
        return run_inline_stage(name, state)
    
    # Build args based on stage
    args = build_stage_args(name, state)
    
    # Run
    rc = run_script(script, args)
    
    if rc == 0:
        print(f"  {GREEN}✅ {name} PASSED{RESET}")
    else:
        print(f"  {RED}❌ {name} FAILED (exit code {rc}){RESET}")
    
    return rc


def build_stage_args(stage_name, state):
    """Build command-line args for each stage based on state."""
    config = state.get("config", {})
    topic = state.get("topic", "")
    
    args_map = {
        "topic": ["--brand", "learnbyleo"],
        "comments": [],
        "research": [],
        "validate": [],
        "enhance": ["--script", config.get("script_path", "scripts/raw_script.txt")],
        "qa_script": [config.get("script_path", "scripts/raw_script.txt")],
        "voice": [],
        "qa_voice": [config.get("narration_path", "audio/narration.wav")],
        "music": [],
        "footage": [],
        "images": ["--storyboard", config.get("storyboard_path", "storyboards/storyboard.json"),
                    "--output", config.get("image_dir", "images/")],
        "transcripts": ["--clips", config.get("footage_dir", "footage/"),
                        "--output", config.get("transcript_path", "transcripts.json")],
        "vision": ["--clips", config.get("footage_dir", "footage/"),
                    "--images", config.get("image_dir", "images/"),
                    "--output", config.get("vision_manifest", "vision_manifest.json")],
        "verify_footage": [],
        "storyboard": ["--script", config.get("script_path", "scripts/enhanced_script.txt")],
        "director": ["--script", config.get("script_path", "scripts/enhanced_script.txt"),
                      "--footage", config.get("footage_dir", "footage/"),
                      "--images", config.get("image_dir", "images/"),
                      "--sfx", config.get("sfx_dir", "assets/sfx/"),
                      "--output", config.get("director_path", "storyboards/directed_v3.json")],
        "validate_segments": ["--director", config.get("director_path", "storyboards/directed_v3.json")],
        "fill_gaps": ["--director", config.get("director_path", "storyboards/directed_v3.json"),
                       "--output-dir", config.get("gap_fill_dir", "footage/gap_fills/")],
        "davinci_build": ["--director", config.get("director_path", "storyboards/directed_v3.json"),
                           "--narration", config.get("narration_path", "audio/narration.wav"),
                           "--music", config.get("music_path", "assets/music/track.wav"),
                           "--sfx-dir", config.get("sfx_dir", "assets/sfx/")],
        "director_review": ["--director", config.get("director_path", "storyboards/directed_v3.json")],
        "qa_video": [],
        "exec_producer_pre": [],
        "exec_producer": [],
    }
    
    return args_map.get(stage_name, [])


def run_all(state, start_from=None):
    """Run all stages in order, starting from a specific stage.

    Quality gate stages (defined in GATE_STAGES) get automatic retry:
    on failure, the associated fix stages are re-run, then the gate is
    re-checked. Up to GATE_MAX_RETRIES attempts before the pipeline stops.
    """

    started = start_from is None

    for name, desc, script in STAGES:
        if not started:
            if name == start_from:
                started = True
            else:
                continue

        if name in state.get("completed", []):
            print(f"  {GRAY}skip  {name} — already completed{RESET}")
            continue

        state["current"] = name
        save_state(state)

        rc = run_stage(name, state)

        if rc == 0:
            state["completed"].append(name)
            state["current"] = None
            save_state(state)
            continue

        # ── Gate retry logic ──
        if name in GATE_STAGES:
            fix_stages = GATE_STAGES[name]
            retries = 0

            while rc != 0 and retries < GATE_MAX_RETRIES:
                retries += 1
                print(f"\n{YELLOW}{BOLD}Gate '{name}' failed — "
                      f"retry {retries}/{GATE_MAX_RETRIES}{RESET}")
                print(f"  Re-running fix stages: {', '.join(fix_stages)}")

                # Re-run each fix stage
                fix_ok = True
                for fix_name in fix_stages:
                    # Remove from completed so it re-runs
                    if fix_name in state.get("completed", []):
                        state["completed"].remove(fix_name)
                        save_state(state)

                    fix_rc = run_stage(fix_name, state)
                    if fix_rc == 0:
                        state["completed"].append(fix_name)
                        save_state(state)
                    else:
                        print(f"  {RED}Fix stage '{fix_name}' failed — "
                              f"cannot retry gate{RESET}")
                        fix_ok = False
                        break

                if not fix_ok:
                    break

                # Re-check the gate
                print(f"\n  Re-checking gate: {name}...")
                rc = run_stage(name, state)

            if rc == 0:
                state["completed"].append(name)
                state["current"] = None
                save_state(state)
                continue

        # Gate exhausted retries or non-gate stage failed
        print(f"\n{RED}{BOLD}Pipeline stopped at: {name}{RESET}")
        if name in GATE_STAGES:
            print(f"Gate failed after {GATE_MAX_RETRIES} retries.")
        print(f"Fix the issue, then resume: python run_pipeline_v2.py --stage {name}")
        save_state(state)
        return 1

    print(f"\n{GREEN}{BOLD}Pipeline complete!{RESET}")
    return 0


def list_stages():
    """List all pipeline stages."""
    print(f"\n{BOLD}Pipeline V2 Stages:{RESET}")
    print(f"{'='*60}")

    # Build phase boundaries from stage names
    phase_map = {
        "topic": "PHASE 1: DISCOVERY",
        "script": "PHASE 2: SCRIPT",
        "voice": "PHASE 3: AUDIO",
        "footage": "PHASE 4: VISUALS",
        "storyboard": "PHASE 5: EDITORIAL",
        "pause_insert": "PHASE 6: ASSEMBLY",
        "director_review": "PHASE 7: VERIFICATION",
        "render": "PHASE 8: PUBLISH",
    }

    for i, (name, desc, script) in enumerate(STAGES):
        if name in phase_map:
            print(f"\n  {BOLD}{phase_map[name]}{RESET}")

        manual = " (manual)" if script is None and name in ("script", "render", "upload") else ""
        inline = " (inline)" if script is None and name not in ("script", "render", "upload") else ""
        gate = " [GATE]" if name in GATE_STAGES else ""

        print(f"  {i+1:2d}. {name:22s} {desc}{manual}{inline}{gate}")


def show_status(state):
    """Show current pipeline state."""
    print(f"\n{BOLD}Pipeline V2 Status:{RESET}")
    print(f"  Topic: {state.get('topic', '(not set)')}")
    print(f"  Completed: {len(state.get('completed', []))} stages")
    print(f"  Current: {state.get('current', '(none)')}")
    
    if state.get("completed"):
        print(f"\n  Completed stages:")
        for s in state["completed"]:
            print(f"    ✅ {s}")
    
    # Find next stage
    completed = set(state.get("completed", []))
    for name, desc, _ in STAGES:
        if name not in completed:
            print(f"\n  Next: {BOLD}{name}{RESET} — {desc}")
            print(f"  Run: python run_pipeline_v2.py --stage {name}")
            break


def main():
    parser = argparse.ArgumentParser(description="Pipeline V2 — LearnByLeo + Claude + DaVinci")
    parser.add_argument('--topic', help='Set the video topic')
    parser.add_argument('--stage', help='Run from this stage (or "all")')
    parser.add_argument('--list', action='store_true', help='List all stages')
    parser.add_argument('--status', action='store_true', help='Show current state')
    parser.add_argument('--reset', action='store_true', help='Reset pipeline state')
    parser.add_argument('--config', help='Path to config JSON with file paths')
    args = parser.parse_args()
    
    if args.list:
        list_stages()
        return 0
    
    state = load_state()
    
    if args.reset:
        state = {"topic": "", "completed": [], "current": None, "config": {}}
        save_state(state)
        print("Pipeline state reset.")
        return 0
    
    if args.topic:
        state["topic"] = args.topic
    
    if args.config:
        with open(args.config) as f:
            state["config"] = json.load(f)
    
    if args.status:
        show_status(state)
        return 0
    
    save_state(state)
    
    print(f"\n{BOLD}🎬 Pipeline V2 — LearnByLeo + Claude + DaVinci{RESET}")
    print(f"Topic: {state.get('topic', '(not set)')}")
    
    if args.stage:
        if args.stage == "all":
            return run_all(state)
        else:
            return run_all(state, start_from=args.stage)
    else:
        # Resume from where we left off, or start fresh
        current = state.get("current")
        if current:
            print(f"Resuming from: {current}")
            return run_all(state, start_from=current)
        else:
            return run_all(state)


if __name__ == "__main__":
    sys.exit(main())
