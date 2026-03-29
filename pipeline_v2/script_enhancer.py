#!/usr/bin/env python3
"""
script_enhancer.py — Adds [BEAT], [PAUSE:X], and [VOICE:register] markers to raw scripts.

Uses Claude + LearnByLeo scripting.json playbook rules:
  - Green/Purple formula (alternate curiosity and payoff)
  - Pause BEFORE reveals (anticipation), not after
  - Energy variation between sections
  - [BEAT] = 0.5s micro-pause, [PAUSE:X] = X seconds

Usage:
    from pipeline_v2.script_enhancer import enhance_script
    enhanced = enhance_script("path/to/raw_script.txt")
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude


def load_scripting_playbook() -> dict:
    """Load the LearnByLeo scripting playbook."""
    path = os.path.join(PROJECT_ROOT, "playbook/scripting.json")
    with open(path) as f:
        return json.load(f)


def enhance_script(script_text: str, target_duration_min: float = 25.0) -> str:
    """
    Add [BEAT], [PAUSE:X], and [VOICE:register] markers to a raw script.

    Markers:
      [BEAT]       — 0.5s micro-pause for emphasis or breath
      [PAUSE:X]    — X-second pause (0.5-3.0) for dramatic effect
      [VOICE:reg]  — Switch voice register (neutral, tense, energized)

    Args:
        script_text: Raw script without markers
        target_duration_min: Target video duration in minutes

    Returns:
        Enhanced script text with markers inserted
    """
    playbook = load_scripting_playbook()

    principles = json.dumps(playbook.get("principles", []), indent=2)
    tactics = json.dumps(playbook.get("tactics", {}), indent=2)
    anti_patterns = json.dumps(playbook.get("anti_patterns", []), indent=2)

    prompt = f"""You are a script enhancer for a YouTube documentary channel.
Your job is to add performance markers to a raw script following the LearnByLeo playbook.

MARKER TYPES:
- [BEAT] = 0.5s micro-pause. Use for:
  - After a punchy statement before moving on
  - Between two contrasting ideas
  - After a name or date for emphasis
- [PAUSE:X] = X-second pause (0.5 to 3.0). Use for:
  - BEFORE reveals (builds anticipation) — NEVER after
  - Before chapter transitions (1.5-3.0s)
  - After rhetorical questions (1.0-1.5s)
  - Before counterintuitive facts (1.0-2.0s)
- [VOICE:neutral] = measured, informational tone (default)
- [VOICE:tense] = lower, slower, suspenseful delivery
- [VOICE:energized] = louder, faster, excited delivery

PLAYBOOK PRINCIPLES:
{principles}

PLAYBOOK TACTICS:
{tactics}

ANTI-PATTERNS TO AVOID:
{anti_patterns}

KEY RULES:
1. GREEN/PURPLE FORMULA: Identify green (curiosity) and purple (payoff) sections.
   Place [PAUSE:1.0-2.0] BEFORE each purple section (anticipation before reveal).
2. ENERGY VARIATION: Alternate [VOICE:] registers. Never stay in one register for
   more than 3-4 paragraphs. Pattern: neutral -> tense -> energized -> neutral.
3. WATER TANK: Place [BEAT] markers at value delivery points (every 20-40 seconds
   of spoken content) so the viewer gets regular micro-payoffs.
4. BUT/THEREFORE: At causal pivot points ("but", "however", "therefore"),
   place [BEAT] before the pivot word.
5. NO PAUSE AFTER REVEALS: Pauses go BEFORE the reveal, not after.
   Wrong: "He was the killer. [PAUSE:2]"
   Right: "[PAUSE:2] He was the killer."
6. Target duration: ~{target_duration_min} minutes at 140 WPM.

Return the COMPLETE script with markers inserted. Do not change any words.
Only add markers between existing sentences or at natural breath points.

RAW SCRIPT:
{script_text}"""

    enhanced = query_claude(prompt, timeout=600)

    if not enhanced:
        print("WARNING: Claude returned empty response, returning original script",
              file=sys.stderr)
        return script_text

    # Validate markers are present
    marker_count = (enhanced.count("[BEAT]") +
                    enhanced.count("[PAUSE:") +
                    enhanced.count("[VOICE:"))
    if marker_count < 5:
        print(f"WARNING: Only {marker_count} markers found — may need manual review",
              file=sys.stderr)

    return enhanced


def analyze_green_purple(script_text: str) -> list[dict]:
    """
    Analyze script for green/purple (curiosity/payoff) section balance.

    Returns list of sections with their classification and any issues.
    """
    playbook = load_scripting_playbook()
    green_types = playbook["principles"][0]["green_types"]
    purple_types = playbook["principles"][0]["purple_types"]

    prompt = f"""Analyze this script for the Green/Purple formula balance.

Green sections BUILD CURIOSITY: {green_types}
Purple sections DELIVER PAYOFF: {purple_types}

For each paragraph or logical section, classify it as "green" or "purple"
and note if any purple section lacks a preceding green section.

Return JSON array:
[
  {{"section": 1, "type": "green", "subtype": "mystery", "text_preview": "first 30 chars...", "issue": null}},
  {{"section": 2, "type": "purple", "subtype": "reveal", "text_preview": "first 30 chars...", "issue": null}},
  ...
]

Flag issues like:
- "purple_without_green": payoff delivered without setup
- "green_cluster": multiple curiosity sections without payoff
- "long_gap": more than 3 minutes of content without a payoff

SCRIPT:
{script_text[:20000]}"""

    result = query_claude(prompt, timeout=120)
    try:
        import re
        match = re.search(r'\[.*\]', result, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return []


def score_script(script_text: str) -> dict:
    """
    Score a script against the LearnByLeo scripting checklist.

    Returns dict with per-criterion scores and overall score (0-100).
    """
    playbook = load_scripting_playbook()
    checklist = playbook["checklists"]["script_quality"]
    criteria = json.dumps(checklist["criteria"], indent=2)

    prompt = f"""Score this script against the LearnByLeo scripting quality checklist.

CRITERIA:
{criteria}

Score each criterion 0-100 and provide a brief justification.

Return JSON:
{{
  "scores": {{
    "green_purple_ratio": {{"score": 0-100, "justification": "..."}},
    "water_tank_pacing": {{"score": 0-100, "justification": "..."}},
    "but_therefore_flow": {{"score": 0-100, "justification": "..."}},
    "conversational_tone": {{"score": 0-100, "justification": "..."}},
    "trim_test": {{"score": 0-100, "justification": "..."}},
    "energy_variation": {{"score": 0-100, "justification": "..."}},
    "clarity": {{"score": 0-100, "justification": "..."}}
  }},
  "overall_score": 0-100,
  "top_issues": ["issue1", "issue2"]
}}

SCRIPT:
{script_text[:20000]}"""

    result = query_claude(prompt, timeout=120)
    try:
        import re
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return {"overall_score": 0, "scores": {}, "top_issues": ["scoring failed"]}


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Add performance markers to script")
    parser.add_argument("script", help="Path to raw script text file")
    parser.add_argument("--output", "-o", help="Output path (default: stdout)")
    parser.add_argument("--duration", "-d", type=float, default=25.0,
                        help="Target duration in minutes")
    parser.add_argument("--score", action="store_true",
                        help="Score script against playbook checklist")
    parser.add_argument("--analyze", action="store_true",
                        help="Analyze green/purple balance")
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    script_text = script_path.read_text()

    if args.score:
        result = score_script(script_text)
        print(json.dumps(result, indent=2))
        return

    if args.analyze:
        result = analyze_green_purple(script_text)
        print(json.dumps(result, indent=2))
        return

    enhanced = enhance_script(script_text, target_duration_min=args.duration)

    if args.output:
        Path(args.output).write_text(enhanced)
        print(f"Enhanced script saved to: {args.output}")

        marker_count = (enhanced.count("[BEAT]") +
                        enhanced.count("[PAUSE:") +
                        enhanced.count("[VOICE:"))
        print(f"  Markers added: {marker_count}")
        print(f"  [BEAT]: {enhanced.count('[BEAT]')}")
        print(f"  [PAUSE]: {enhanced.count('[PAUSE:')}")
        print(f"  [VOICE]: {enhanced.count('[VOICE:')}")
    else:
        print(enhanced)


if __name__ == "__main__":
    main()
