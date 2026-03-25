#!/usr/bin/env python3
"""
Script Structure Analyzer — Analyzes scripts for the playbook's structural patterns.

Complements check_fern_script.py (which scores against Fern's measured metrics).
This tool scores against the CREATIVE STRUCTURE principles from the playbook:
  - Green/Purple pattern (curiosity → payoff alternation)
  - Water Tank pacing (value spread evenly, no dry stretches)
  - But/Therefore flow (causal connections vs sequential listing)
  - Energy variation (mood shifts throughout)
  - Conversational tone (not textbook)
  - Intro quality (expectation alignment)

Usage:
    python -m pipeline.script_structure_analyzer scripts/enhanced_frank_olson.txt
    python -m pipeline.script_structure_analyzer scripts/raw_mkultra.txt --title "The CIA's Secret Mind Control Program"
    python -m pipeline.script_structure_analyzer --compare scripts/v1.txt scripts/v2.txt

Outputs a structural report with scores and specific line-level recommendations.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playbook.loader import Playbook

# LLM integration: Claude Max (via CLI) is primary, heuristic fallback always available
# The pattern detectors below work without any LLM — LLM is used for deeper analysis only
LLM_MODEL = "claude"  # Uses claude CLI (Max subscription)

# --- PATTERN DETECTORS ---

# Green signals: curiosity builders
GREEN_PATTERNS = [
    r"\bbut\b.*\?",                          # "but how...?"
    r"\bwhat\b.*\bif\b",                      # "what if..."
    r"\bwhy\b.*\?",                            # "why did...?"
    r"\bhow\b.*\?",                            # "how could...?"
    r"\bnobody\b.*\bknew\b",                  # "nobody knew..."
    r"\bsecret\b",                             # "secret"
    r"\bhidden\b",                             # "hidden"
    r"\bmystery\b",                            # "mystery"
    r"\bstrange\b",                            # "strange"
    r"\bimpossible\b",                         # "impossible"
    r"\bsomething\b.*\bwrong\b",              # "something was wrong"
    r"\bdidn'?t\b.*\badd up\b",              # "didn't add up"
    r"\bno one\b.*\bknew\b",                  # "no one knew"
    r"\buntil\b",                              # "until..."
    r"\bwhat\b.*\bhappened\b.*\bnext\b",      # "what happened next"
    r"\bthere\b.*\bone\b.*\bdetail\b",        # "there was one detail"
    r"\boverlooked\b",                         # "overlooked"
    r"\bmissing\b.*\bpiece\b",                # "missing piece"
]

# Purple signals: payoff / resolution
PURPLE_PATTERNS = [
    r"\bthe answer\b",                         # "the answer"
    r"\bthe truth\b",                          # "the truth"
    r"\bit turns out\b",                       # "it turns out"
    r"\bfinally\b",                            # "finally"
    r"\bdiscovered\b",                         # "discovered"
    r"\brevealed\b",                           # "revealed"
    r"\bthe reason\b",                         # "the reason"
    r"\bthis is\b.*\bhow\b",                  # "this is how"
    r"\bhere'?s\b.*\bwhat\b",                 # "here's what"
    r"\bproved\b",                             # "proved"
    r"\bconfirmed\b",                          # "confirmed"
    r"\bevidence\b.*\bshowed\b",              # "evidence showed"
]

# But/Therefore connectors (good flow)
BUT_THEREFORE_PATTERNS = [
    r"\bbut\b",
    r"\bhowever\b",
    r"\btherefore\b",
    r"\bso\b",
    r"\bbecause\b",
    r"\bas a result\b",
    r"\bconsequently\b",
    r"\bnevertheless\b",
    r"\bdespite\b",
    r"\binstead\b",
    r"\byet\b",
    r"\bwhich meant\b",
    r"\bthis meant\b",
]

# And/Then connectors (bad flow — sequential listing)
AND_THEN_PATTERNS = [
    r"\band then\b",
    r"\bafter that\b",
    r"\bnext\b,",
    r"\bfollowing this\b",
    r"\bsubsequently\b",
    r"\bafterward\b",
    r"\blater\b,",
    r"\bthen\b,",
    r"\balso\b,",
    r"\badditionally\b",
    r"\bfurthermore\b",
    r"\bmoreover\b",
]

# Conversational markers
CONVERSATIONAL_PATTERNS = [
    r"\byou\b",                    # Direct address
    r"\byour\b",
    r"\bimagine\b",                # Engagement
    r"\bthink about\b",
    r"\blet'?s\b",
    r"\bhere'?s the thing\b",
    r"\blike\b.*\bfor example\b",  # Analogies
    r"\bit'?s\b.*\blike\b",
    r"\bpicture this\b",
    r"\?\s",                       # Questions
]

# Energy shift markers
ENERGY_MARKERS = {
    "high": [r"\bsuddenly\b", r"\bexplosion\b", r"\bshocking\b", r"\bincredible\b",
             r"\bunbelievable\b", r"\b!\b", r"\bimmediately\b", r"\bcrashed\b"],
    "low": [r"\bquietly\b", r"\bslowly\b", r"\bpeaceful\b", r"\bcalm\b",
            r"\bsilence\b", r"\bgentle\b", r"\bsoftly\b"],
    "tense": [r"\bdangerous\b", r"\bfeared\b", r"\bterrif", r"\banxious\b",
              r"\bnervous\b", r"\bdread\b", r"\bominous\b", r"\bthreat\b"],
}


def parse_script(text: str) -> list[dict]:
    """Parse a script into paragraphs with metadata."""
    # Remove enhancement markers for analysis
    clean = re.sub(r'\[(?:BEAT|PAUSE:\d+\.?\d*|BREATH|VOICE:\w+|CHAPTER:.*?)\]', '', text)

    paragraphs = []
    for i, para in enumerate(clean.split("\n\n")):
        para = para.strip()
        if not para:
            continue

        sentences = re.split(r'(?<=[.!?])\s+', para)
        word_count = len(para.split())

        paragraphs.append({
            "index": i,
            "text": para,
            "sentences": sentences,
            "word_count": word_count,
        })

    return paragraphs


def count_pattern_matches(text: str, patterns: list[str]) -> int:
    """Count how many distinct pattern matches occur in text."""
    count = 0
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            count += 1
    return count


def analyze_green_purple(paragraphs: list[dict]) -> dict:
    """Analyze the green/purple (curiosity/payoff) pattern."""
    sequence = []
    for p in paragraphs:
        text = p["text"]
        green_score = count_pattern_matches(text, GREEN_PATTERNS)
        purple_score = count_pattern_matches(text, PURPLE_PATTERNS)

        if green_score > purple_score:
            sequence.append("G")
        elif purple_score > green_score:
            sequence.append("P")
        else:
            sequence.append("N")  # Neutral

    # Score: how often does purple follow green?
    good_transitions = 0
    bad_transitions = 0  # Purple without preceding green
    total_purple = sequence.count("P")

    for i, s in enumerate(sequence):
        if s == "P":
            # Look back for a green
            found_green = False
            for j in range(max(0, i-3), i):
                if sequence[j] == "G":
                    found_green = True
                    break
            if found_green:
                good_transitions += 1
            else:
                bad_transitions += 1

    if total_purple == 0:
        ratio = 0
    else:
        ratio = good_transitions / total_purple

    # Detect long stretches without green
    max_gap = 0
    current_gap = 0
    for s in sequence:
        if s != "G":
            current_gap += 1
        else:
            max_gap = max(max_gap, current_gap)
            current_gap = 0
    max_gap = max(max_gap, current_gap)

    score = int(ratio * 70 + (30 if max_gap < 5 else 15 if max_gap < 8 else 0))

    return {
        "score": min(100, max(0, score)),
        "sequence": "".join(sequence),
        "green_count": sequence.count("G"),
        "purple_count": total_purple,
        "neutral_count": sequence.count("N"),
        "good_transitions": good_transitions,
        "bad_transitions": bad_transitions,
        "max_gap_without_green": max_gap,
    }


def analyze_water_tank(paragraphs: list[dict]) -> dict:
    """Analyze water tank pacing — are value moments spread evenly?"""
    # Value moments = green or purple paragraphs (non-neutral)
    total_words = sum(p["word_count"] for p in paragraphs)
    value_positions = []
    cumulative_words = 0

    for p in paragraphs:
        green = count_pattern_matches(p["text"], GREEN_PATTERNS)
        purple = count_pattern_matches(p["text"], PURPLE_PATTERNS)
        if green > 0 or purple > 0:
            value_positions.append(cumulative_words / max(total_words, 1))
        cumulative_words += p["word_count"]

    if len(value_positions) < 3:
        return {"score": 30, "reason": "Too few value moments detected", "gaps": []}

    # Calculate gaps between value moments
    gaps = []
    for i in range(1, len(value_positions)):
        gap = value_positions[i] - value_positions[i-1]
        gaps.append(round(gap, 3))

    # Score: penalize large gaps and uneven distribution
    max_gap = max(gaps) if gaps else 1.0
    avg_gap = sum(gaps) / len(gaps) if gaps else 1.0
    std_gap = (sum((g - avg_gap)**2 for g in gaps) / len(gaps))**0.5 if gaps else 0

    score = 100
    if max_gap > 0.15:  # More than 15% of script without a value moment
        score -= int((max_gap - 0.15) * 300)
    if std_gap > 0.05:  # Uneven distribution
        score -= int(std_gap * 200)

    # Bonus for first and last quartile having value
    first_quarter = [p for p in value_positions if p < 0.25]
    last_quarter = [p for p in value_positions if p > 0.75]
    if not first_quarter:
        score -= 15
    if not last_quarter:
        score -= 15

    dry_stretches = [g for g in gaps if g > 0.12]

    return {
        "score": max(0, min(100, score)),
        "value_moment_count": len(value_positions),
        "max_gap": round(max_gap, 3),
        "avg_gap": round(avg_gap, 3),
        "distribution_std": round(std_gap, 4),
        "dry_stretches": len(dry_stretches),
        "has_early_value": len(first_quarter) > 0,
        "has_late_value": len(last_quarter) > 0,
    }


def analyze_but_therefore(paragraphs: list[dict]) -> dict:
    """Analyze but/therefore vs and/then flow."""
    full_text = " ".join(p["text"] for p in paragraphs)

    bt_count = count_pattern_matches(full_text, BUT_THEREFORE_PATTERNS)
    at_count = count_pattern_matches(full_text, AND_THEN_PATTERNS)

    total = bt_count + at_count
    if total == 0:
        return {"score": 50, "but_therefore": 0, "and_then": 0, "ratio": 0}

    ratio = bt_count / total
    score = int(ratio * 100)

    return {
        "score": max(0, min(100, score)),
        "but_therefore_count": bt_count,
        "and_then_count": at_count,
        "ratio": round(ratio, 2),
    }


def analyze_energy_variation(paragraphs: list[dict]) -> dict:
    """Analyze energy level variation throughout the script."""
    energy_sequence = []

    for p in paragraphs:
        text = p["text"]
        high = count_pattern_matches(text, ENERGY_MARKERS["high"])
        low = count_pattern_matches(text, ENERGY_MARKERS["low"])
        tense = count_pattern_matches(text, ENERGY_MARKERS["tense"])

        if high > low and high > tense:
            energy_sequence.append("H")
        elif tense > low:
            energy_sequence.append("T")
        elif low > 0:
            energy_sequence.append("L")
        else:
            energy_sequence.append("M")  # Medium/neutral

    # Count energy shifts
    shifts = 0
    for i in range(1, len(energy_sequence)):
        if energy_sequence[i] != energy_sequence[i-1]:
            shifts += 1

    # Ideal: ~1 shift every 4-5 paragraphs
    expected_shifts = len(paragraphs) / 4.5
    shift_ratio = shifts / max(expected_shifts, 1)

    score = int(min(1.0, shift_ratio) * 100)

    # Detect monotone stretches
    max_monotone = 1
    current = 1
    for i in range(1, len(energy_sequence)):
        if energy_sequence[i] == energy_sequence[i-1]:
            current += 1
            max_monotone = max(max_monotone, current)
        else:
            current = 1

    if max_monotone > 6:
        score -= 20

    return {
        "score": max(0, min(100, score)),
        "energy_sequence": "".join(energy_sequence),
        "shift_count": shifts,
        "max_monotone_stretch": max_monotone,
        "unique_energies": len(set(energy_sequence)),
    }


def analyze_conversational(paragraphs: list[dict]) -> dict:
    """Analyze conversational tone vs textbook."""
    full_text = " ".join(p["text"] for p in paragraphs)
    total_words = len(full_text.split())

    conv_count = count_pattern_matches(full_text, CONVERSATIONAL_PATTERNS)
    questions = len(re.findall(r'\?', full_text))

    # "You/your" density
    you_count = len(re.findall(r'\byou(?:r)?\b', full_text.lower()))
    you_density = you_count / max(total_words, 1) * 100

    # Score
    score = 30  # Baseline
    score += min(conv_count * 5, 30)
    score += min(questions * 3, 15)
    if you_density >= 0.5:
        score += 15
    elif you_density >= 0.2:
        score += 8
    if you_density >= 0.8:
        score += 10

    return {
        "score": max(0, min(100, score)),
        "conversational_markers": conv_count,
        "question_count": questions,
        "you_density_pct": round(you_density, 2),
    }


def analyze_intro(paragraphs: list[dict], title: Optional[str] = None) -> dict:
    """Analyze the intro (first ~10% of paragraphs)."""
    if not paragraphs:
        return {"score": 0}

    intro_count = max(2, len(paragraphs) // 10)
    intro_paras = paragraphs[:intro_count]
    intro_text = " ".join(p["text"] for p in intro_paras)
    intro_words = len(intro_text.split())

    score = 50  # Baseline

    # Check for filler openings
    filler_openers = ["hey guys", "welcome back", "in this video", "today we",
                      "so today", "alright so", "what's up"]
    intro_lower = intro_text.lower()
    has_filler = any(f in intro_lower for f in filler_openers)
    if has_filler:
        score -= 20

    # Check for immediate curiosity/hook
    green_in_intro = count_pattern_matches(intro_text, GREEN_PATTERNS)
    if green_in_intro >= 2:
        score += 25
    elif green_in_intro >= 1:
        score += 15

    # Check for immediate story/narrative
    story_signals = count_pattern_matches(intro_text, [
        r"\bin \d{4}\b",           # Year anchor
        r"\bon\b.*\bnight\b",     # "on the night of..."
        r"\bwhen\b.*\bfirst\b",   # "when they first..."
        r"\bstory\b.*\bbegins\b", # "the story begins..."
    ])
    if story_signals > 0:
        score += 15

    # Conciseness: intro should be ~10% of total
    total_words = sum(p["word_count"] for p in paragraphs)
    intro_ratio = intro_words / max(total_words, 1)
    if intro_ratio > 0.15:
        score -= 10  # Intro too long

    return {
        "score": max(0, min(100, score)),
        "has_filler_opener": has_filler,
        "green_signals_in_intro": green_in_intro,
        "story_signals_in_intro": story_signals,
        "intro_word_ratio": round(intro_ratio, 3),
    }


def analyze_script(script_path: str, title: Optional[str] = None,
                   use_ollama: bool = True) -> dict:
    """Full structural analysis of a script."""
    text = Path(script_path).read_text()
    paragraphs = parse_script(text)
    total_words = sum(p["word_count"] for p in paragraphs)

    pb = Playbook()

    # Run all analyzers
    green_purple = analyze_green_purple(paragraphs)
    water_tank = analyze_water_tank(paragraphs)
    but_therefore = analyze_but_therefore(paragraphs)
    energy = analyze_energy_variation(paragraphs)
    conversational = analyze_conversational(paragraphs)
    intro = analyze_intro(paragraphs, title)

    # Compile scores
    dimensions = {
        "green_purple_pattern": green_purple["score"],
        "water_tank_pacing": water_tank["score"],
        "but_therefore_flow": but_therefore["score"],
        "energy_variation": energy["score"],
        "conversational_tone": conversational["score"],
        "intro_quality": intro["score"],
    }

    weights = {
        "green_purple_pattern": 0.25,
        "water_tank_pacing": 0.20,
        "but_therefore_flow": 0.15,
        "energy_variation": 0.15,
        "conversational_tone": 0.10,
        "intro_quality": 0.15,
    }

    composite = sum(dimensions[k] * weights[k] for k in weights)

    # Generate recommendations
    recommendations = []

    if green_purple["score"] < 60:
        recommendations.append(
            f"Weak curiosity/payoff pattern. Found {green_purple['green_count']} green (curiosity) "
            f"and {green_purple['purple_count']} purple (payoff) sections. "
            f"Add more mystery/question setups BEFORE delivering information.")
    if green_purple["max_gap_without_green"] > 6:
        recommendations.append(
            f"Long dry stretch: {green_purple['max_gap_without_green']} paragraphs "
            f"without a curiosity hook. Viewer interest will drain.")

    if water_tank["score"] < 60:
        recommendations.append(
            f"Uneven value distribution. {water_tank['dry_stretches']} dry stretches found. "
            f"Spread key insights more evenly throughout.")
    if not water_tank.get("has_late_value"):
        recommendations.append(
            "No value moments in the last 25% of the script. The second half needs to be "
            "just as engaging — never wind down.")

    if but_therefore["score"] < 50:
        recommendations.append(
            f"Too many 'and then' connections ({but_therefore['and_then_count']}) vs "
            f"'but/therefore' ({but_therefore['but_therefore_count']}). "
            f"Rewrite sequences to use causal flow: 'but', 'so', 'therefore', 'despite'.")

    if energy["score"] < 50:
        recommendations.append(
            f"Monotone energy. Longest same-energy stretch: {energy['max_monotone_stretch']} paragraphs. "
            f"Alternate between high-energy reveals and reflective moments.")

    if conversational["score"] < 50:
        recommendations.append(
            f"Reads like a textbook. You/your density: {conversational['you_density_pct']:.1f}%, "
            f"questions: {conversational['question_count']}. Add direct address, rhetorical questions, "
            f"and analogies.")

    if intro["has_filler_opener"]:
        recommendations.append(
            "Intro has filler ('hey guys', 'welcome back', etc.). "
            "Cut it. Start with the hook immediately.")
    if intro["green_signals_in_intro"] == 0:
        recommendations.append(
            "Intro lacks a curiosity hook. The first sentence must create a reason to keep watching.")

    # Verdict
    if composite >= 80:
        verdict = "EXCELLENT structure"
        detail = "Script follows strong creative patterns. Minor polish only."
    elif composite >= 65:
        verdict = "GOOD structure"
        detail = "Solid foundation. Address recommendations for maximum retention."
    elif composite >= 50:
        verdict = "NEEDS WORK"
        detail = "Structural issues will hurt retention. Rework before recording."
    else:
        verdict = "WEAK structure"
        detail = "Major structural problems. Consider rewriting with playbook principles."

    # Also score against the playbook checklist
    playbook_scores = {
        "green_purple_ratio": green_purple["score"] / 100,
        "water_tank_pacing": water_tank["score"] / 100,
        "but_therefore_flow": but_therefore["score"] / 100,
        "conversational_tone": conversational["score"] / 100,
        "trim_test": 0.7,  # Can't auto-detect, default moderate
        "energy_variation": energy["score"] / 100,
        "clarity": 0.7,  # Can't auto-detect, default moderate
    }
    playbook_result = pb.score_checklist("scripting", "script_quality", playbook_scores)

    return {
        "script_path": script_path,
        "title": title,
        "total_words": total_words,
        "total_paragraphs": len(paragraphs),
        "dimensions": dimensions,
        "weights": weights,
        "composite_score": round(composite, 1),
        "verdict": verdict,
        "verdict_detail": detail,
        "recommendations": recommendations,
        "details": {
            "green_purple": green_purple,
            "water_tank": water_tank,
            "but_therefore": but_therefore,
            "energy": energy,
            "conversational": conversational,
            "intro": intro,
        },
        "playbook_checklist_score": playbook_result["total_percent"],
    }


def print_report(result: dict):
    """Pretty-print the analysis report."""
    print(f"\n{'='*60}")
    print(f"  SCRIPT STRUCTURE ANALYSIS")
    print(f"{'='*60}")
    print(f"  File: {result['script_path']}")
    if result.get("title"):
        print(f"  Title: {result['title']}")
    print(f"  Words: {result['total_words']:,}  |  Paragraphs: {result['total_paragraphs']}")
    print()

    for dim, score in result["dimensions"].items():
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        label = dim.replace("_", " ").title()
        weight = result["weights"].get(dim, 0)
        print(f"  {label:22s} {bar} {score:3d}/100  ({weight:.0%})")

    print(f"\n  {'─'*56}")
    print(f"  COMPOSITE:   {result['composite_score']:.1f}/100")
    print(f"  VERDICT:     {result['verdict']}")
    print(f"  {result['verdict_detail']}")
    print(f"  Playbook checklist:  {result['playbook_checklist_score']}")

    # Key details
    d = result["details"]
    gp = d["green_purple"]
    print(f"\n  GREEN/PURPLE: {gp['green_count']}G / {gp['purple_count']}P / {gp['neutral_count']}N")
    print(f"  Pattern: {gp['sequence'][:60]}{'...' if len(gp['sequence']) > 60 else ''}")

    bt = d["but_therefore"]
    print(f"  FLOW: {bt['but_therefore_count']} causal vs {bt['and_then_count']} sequential connectors (ratio: {bt['ratio']:.0%})")

    e = d["energy"]
    print(f"  ENERGY: {e['shift_count']} shifts, max monotone: {e['max_monotone_stretch']} paragraphs")
    print(f"  Pattern: {e['energy_sequence'][:60]}{'...' if len(e['energy_sequence']) > 60 else ''}")

    if result["recommendations"]:
        print(f"\n  RECOMMENDATIONS:")
        for r in result["recommendations"]:
            print(f"    ⚠  {r}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Analyze script structure against playbook")
    parser.add_argument("script", nargs="?", help="Path to script file")
    parser.add_argument("--title", "-t", help="Video title (for intro analysis)")
    parser.add_argument("--compare", nargs=2, metavar="SCRIPT", help="Compare two scripts")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM analysis, use heuristics only")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.compare:
        results = []
        for path in args.compare:
            r = analyze_script(path, args.title, not args.no_llm)
            results.append(r)
            if not args.json:
                print_report(r)

        if not args.json:
            print(f"\n{'='*60}")
            print("  COMPARISON")
            print(f"{'='*60}")
            for dim in results[0]["dimensions"]:
                s1 = results[0]["dimensions"][dim]
                s2 = results[1]["dimensions"][dim]
                diff = s2 - s1
                arrow = "↑" if diff > 0 else "↓" if diff < 0 else "="
                label = dim.replace("_", " ").title()
                print(f"  {label:22s}  {s1:3d} → {s2:3d}  ({arrow}{abs(diff)})")
            c1 = results[0]["composite_score"]
            c2 = results[1]["composite_score"]
            diff = c2 - c1
            print(f"\n  COMPOSITE:  {c1:.1f} → {c2:.1f}  ({'↑' if diff > 0 else '↓'}{abs(diff):.1f})")
            print()
        else:
            print(json.dumps(results, indent=2))

    elif args.script:
        result = analyze_script(args.script, args.title, not args.no_llm)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_report(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
