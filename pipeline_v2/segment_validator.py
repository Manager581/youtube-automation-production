#!/usr/bin/env python3
"""
segment_validator.py — Score each segment against playbook criteria.

Runs BEFORE the builder to catch bad director decisions, and AFTER the build
to verify. Uses Claude to judge visual-narration match and editorial quality.

Checks per segment:
  P-RD-04: Does the visual match what's being said?
  P-ED-04: Is there energy variation from the previous segment?
  AP-ED-03: Is the SFX justified (not every segment needs one)?
  P-ED-02: Is the cut frequency within 5-7s?
  AP-ED-02: Do graphics animate (not pop)?
  P-SC-01: Green/purple balance across segments
  Litmus test (P-RD-01): Does the viewer know why they should care?

Usage:
    python -m pipeline_v2.segment_validator --director storyboards/directed_v3.json
    python -m pipeline_v2.segment_validator --director storyboards/directed_v3.json --fix-decisions
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude

# ── ANSI colors ──
GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
BOLD = "\033[1m"; RESET = "\033[0m"; GRAY = "\033[90m"


# ── Load Data ──────────────────────────────────────────────────────────────

def load_director(path):
    """Load director v3 output, return (raw_data, flat_segments)."""
    with open(path) as f:
        data = json.load(f)

    segments = []
    if "scenes" in data:
        for scene in data["scenes"]:
            segments.extend(scene.get("segments", []))
    else:
        segments = data.get("segments", [])

    return data, segments


def load_playbook():
    """Load playbook modules: editing.json, retention_delivery.json, scripting.json."""
    modules = {}
    pb_dir = PROJECT_ROOT / "playbook"
    if not pb_dir.exists():
        print(f"{YELLOW}WARNING: playbook/ directory not found{RESET}")
        return modules

    for name in ("editing", "retention_delivery", "scripting"):
        fp = pb_dir / f"{name}.json"
        if fp.exists():
            with open(fp) as f:
                modules[name] = json.load(f)

    return modules


# ── Individual Checks ──────────────────────────────────────────────────────

def check_visual_narration_match(seg, seg_idx):
    """P-RD-04: Does the visual match what's being said?

    Uses Claude to judge: 'narration says X, visual shows Y -- match?'
    """
    text = seg.get("text", seg.get("narration", ""))
    visual = seg.get("visual_file", "")
    visual_type = seg.get("visual_type", "")
    notes = seg.get("notes", "")

    if not text or not visual:
        return {
            "rule": "P-RD-04",
            "description": "No visual assigned to narration segment",
            "score": 0,
            "verdict": "fail",
            "fix": "Assign a visual file that matches the narration content",
        }

    # Derive visual description from filename + notes
    visual_desc = visual.replace("_", " ").replace("-", " ")
    if notes:
        visual_desc += f" ({notes})"

    prompt = (
        f"A documentary video segment has:\n"
        f"  NARRATION: \"{text[:200]}\"\n"
        f"  VISUAL: {visual_desc} (type: {visual_type})\n\n"
        f"Does the visual match what's being narrated?\n"
        f"Reply with ONLY one of: MATCH, PARTIAL, MISMATCH\n"
        f"Then a brief reason (one sentence)."
    )

    response = query_claude(prompt, timeout=30)
    if not response:
        return {"rule": "P-RD-04", "description": "Claude unavailable", "score": 5, "verdict": "warn"}

    response_upper = response.upper()
    if "MATCH" in response_upper and "MISMATCH" not in response_upper:
        return {
            "rule": "P-RD-04",
            "description": response.strip(),
            "score": 10,
            "verdict": "pass",
        }
    elif "PARTIAL" in response_upper:
        return {
            "rule": "P-RD-04",
            "description": response.strip(),
            "score": 5,
            "verdict": "warn",
            "fix": f"Find a closer visual match for: {text[:60]}",
        }
    else:
        return {
            "rule": "P-RD-04",
            "description": response.strip(),
            "score": 0,
            "verdict": "fail",
            "fix": f"Replace visual for seg {seg_idx}: narration and image don't match",
        }


def check_energy_variation(seg, prev_seg, seg_idx):
    """P-ED-04: Is there energy variation from the previous segment?

    Compare tension_level and arc_position to detect monotone energy.
    """
    if prev_seg is None:
        return {
            "rule": "P-ED-04",
            "description": "First segment — no comparison needed",
            "score": 10,
            "verdict": "pass",
        }

    tension = seg.get("tension_level", 0.5)
    prev_tension = prev_seg.get("tension_level", 0.5)
    arc = seg.get("arc_position", "")
    prev_arc = prev_seg.get("arc_position", "")

    tension_diff = abs(tension - prev_tension)
    arc_changed = arc != prev_arc

    if arc_changed or tension_diff >= 0.15:
        return {
            "rule": "P-ED-04",
            "description": (
                f"Energy shift: {prev_arc}({prev_tension:.1f}) -> "
                f"{arc}({tension:.1f})"
            ),
            "score": 10,
            "verdict": "pass",
        }
    elif tension_diff >= 0.05:
        return {
            "rule": "P-ED-04",
            "description": (
                f"Slight energy shift: {prev_tension:.1f} -> {tension:.1f} "
                f"(both {arc})"
            ),
            "score": 7,
            "verdict": "warn",
            "fix": (
                f"Seg {seg_idx}: Consider shifting arc or tension to "
                f"create more contrast with previous segment"
            ),
        }
    else:
        return {
            "rule": "P-ED-04",
            "description": (
                f"Flat energy: {prev_tension:.1f} -> {tension:.1f} "
                f"(both {arc})"
            ),
            "score": 3,
            "verdict": "fail",
            "fix": (
                f"Seg {seg_idx}: Monotone energy — vary tension_level or "
                f"arc_position to break viewer fatigue"
            ),
        }


def check_sfx_justified(seg, seg_idx):
    """AP-ED-03: Is the SFX justified? Not every segment needs one.

    SFX should only appear before genuine reveals or dramatic moments.
    """
    sfx = seg.get("sfx") or {}
    sfx_file = sfx.get("file") if isinstance(sfx, dict) else None

    if not sfx_file:
        return {
            "rule": "AP-ED-03",
            "description": "No SFX — appropriate for non-dramatic segment",
            "score": 10,
            "verdict": "pass",
        }

    arc = seg.get("arc_position", "")
    tension = seg.get("tension_level", 0.5)
    motivation = sfx.get("motivation", "") if isinstance(sfx, dict) else ""

    # SFX justified for high-tension or dramatic arc positions
    dramatic_arcs = {"revelation", "emotional_peak", "climax", "cold_open", "chapter_transition"}
    if arc in dramatic_arcs or tension >= 0.7:
        return {
            "rule": "AP-ED-03",
            "description": f"SFX justified: {arc} at tension {tension:.1f} — {motivation}",
            "score": 10,
            "verdict": "pass",
        }
    elif tension >= 0.5 and motivation:
        return {
            "rule": "AP-ED-03",
            "description": f"SFX borderline: {arc} at tension {tension:.1f} — {motivation}",
            "score": 6,
            "verdict": "warn",
            "fix": (
                f"Seg {seg_idx}: SFX at medium tension ({tension:.1f}) may "
                f"dilute impact. Consider removing."
            ),
        }
    else:
        return {
            "rule": "AP-ED-03",
            "description": (
                f"SFX unjustified: {arc} at tension {tension:.1f} — "
                f"trains viewer to ignore tension signals"
            ),
            "score": 2,
            "verdict": "fail",
            "fix": (
                f"Seg {seg_idx}: Remove SFX '{sfx_file}' — "
                f"risers before unimportant moments diminish real reveals"
            ),
        }


def check_cut_frequency(seg, seg_idx, all_segments):
    """P-ED-02: Is the cut frequency within 5-7s?

    Estimates segment duration from word count and checks against the
    documentary benchmark of 5-7 seconds per cut.
    """
    word_count = seg.get("word_count", len(seg.get("text", "").split()))
    # ~2.5 words/sec at 150 WPM
    est_duration = word_count / 2.5

    if 3.0 <= est_duration <= 9.0:
        return {
            "rule": "P-ED-02",
            "description": f"Cut duration ~{est_duration:.1f}s (target 5-7s)",
            "score": 10,
            "verdict": "pass",
        }
    elif est_duration < 3.0:
        return {
            "rule": "P-ED-02",
            "description": f"Cut too fast: ~{est_duration:.1f}s ({word_count} words)",
            "score": 5,
            "verdict": "warn",
            "fix": f"Seg {seg_idx}: Segment too short ({est_duration:.1f}s). Merge with adjacent.",
        }
    elif est_duration <= 12.0:
        return {
            "rule": "P-ED-02",
            "description": f"Cut slightly slow: ~{est_duration:.1f}s ({word_count} words)",
            "score": 6,
            "verdict": "warn",
            "fix": f"Seg {seg_idx}: Segment long ({est_duration:.1f}s). Consider splitting.",
        }
    else:
        return {
            "rule": "P-ED-02",
            "description": f"Cut too slow: ~{est_duration:.1f}s ({word_count} words)",
            "score": 2,
            "verdict": "fail",
            "fix": (
                f"Seg {seg_idx}: Segment WAY too long ({est_duration:.1f}s). "
                f"Must split to maintain viewer attention."
            ),
        }


def check_graphics_animate(seg, seg_idx):
    """AP-ED-02: Do graphics animate (not pop)?

    Text overlays and chapter cards should use fade or typewriter, never
    instant appear.
    """
    text_overlay = seg.get("text_overlay")
    chapter_card = seg.get("chapter_card")

    if not text_overlay and not chapter_card:
        return {
            "rule": "AP-ED-02",
            "description": "No graphics in this segment",
            "score": 10,
            "verdict": "pass",
        }

    text_style = seg.get("text_style", "static")
    transition_in = seg.get("transition_in", "cut")

    issues = []

    if text_overlay and text_style == "static" and transition_in == "cut":
        issues.append(
            f"Text overlay '{text_overlay[:20]}' uses static+cut (will pop)"
        )

    if chapter_card and transition_in == "cut":
        issues.append(
            f"Chapter card '{chapter_card}' uses hard cut (should fade)"
        )

    if issues:
        return {
            "rule": "AP-ED-02",
            "description": "; ".join(issues),
            "score": 4,
            "verdict": "warn",
            "fix": (
                f"Seg {seg_idx}: Use typewriter/lower_third style or "
                f"fade_from_black transition for graphics"
            ),
        }

    return {
        "rule": "AP-ED-02",
        "description": (
            f"Graphics animated: style={text_style}, "
            f"transition={transition_in}"
        ),
        "score": 10,
        "verdict": "pass",
    }


def check_green_purple_balance(segments):
    """P-SC-01: Green/purple balance across all segments.

    Green = curiosity-building (tension_build, cold_open, context_setup)
    Purple = payoff (revelation, emotional_peak, aftermath)

    Should alternate: green -> purple -> green -> purple.
    """
    green_arcs = {"cold_open", "context_setup", "tension_build"}
    purple_arcs = {"revelation", "emotional_peak", "aftermath", "climax"}

    colors = []
    for seg in segments:
        arc = seg.get("arc_position", "context_setup")
        if arc in green_arcs:
            colors.append("green")
        elif arc in purple_arcs:
            colors.append("purple")
        else:
            colors.append("neutral")

    # Count transitions
    transitions = 0
    long_runs = 0
    run_length = 1

    for i in range(1, len(colors)):
        if colors[i] != colors[i - 1] and colors[i] != "neutral":
            transitions += 1
            run_length = 1
        else:
            run_length += 1
            if run_length > 8:
                long_runs += 1

    green_count = colors.count("green")
    purple_count = colors.count("purple")
    total = len(colors)

    if total == 0:
        return {"rule": "P-SC-01", "score": 5, "verdict": "warn",
                "description": "No segments to analyze"}

    green_pct = green_count / total * 100
    purple_pct = purple_count / total * 100
    balance_ratio = min(green_count, purple_count) / max(green_count, purple_count, 1)

    issues = []
    score = 10

    if balance_ratio < 0.3:
        issues.append(
            f"Imbalanced: {green_pct:.0f}% green vs {purple_pct:.0f}% purple "
            f"(want ~50/50)"
        )
        score -= 4

    if long_runs > 2:
        issues.append(
            f"{long_runs} runs of 8+ same-color segments (monotonous)"
        )
        score -= 3

    if transitions < total * 0.1:
        issues.append("Too few green/purple transitions — viewer fatigue")
        score -= 3

    return {
        "rule": "P-SC-01",
        "description": (
            f"Green: {green_count} ({green_pct:.0f}%), "
            f"Purple: {purple_count} ({purple_pct:.0f}%), "
            f"Transitions: {transitions}"
            + (f" | Issues: {'; '.join(issues)}" if issues else "")
        ),
        "score": max(0, score),
        "verdict": "pass" if score >= 8 else ("warn" if score >= 5 else "fail"),
        "fix": "; ".join(issues) if issues else None,
    }


def check_litmus_test(seg, seg_idx):
    """P-RD-01 / Litmus Test: Does the viewer know why they should care?
    Is something uncertain? Is this scene essential?

    Uses Claude to evaluate the three-part litmus test from the playbook.
    """
    text = seg.get("text", seg.get("narration", ""))
    if not text:
        return {
            "rule": "P-RD-01",
            "description": "No narration text",
            "score": 0,
            "verdict": "fail",
            "fix": f"Seg {seg_idx}: Empty narration — cut or add content",
        }

    arc = seg.get("arc_position", "")
    tension = seg.get("tension_level", 0.5)

    prompt = (
        f"Evaluate this documentary narration segment using the 3-part litmus test:\n"
        f"1. Does the viewer know what is happening?\n"
        f"2. Do they know why it is important?\n"
        f"3. Is there uncertainty (what could go wrong)?\n\n"
        f"Segment (arc: {arc}, tension: {tension}):\n"
        f"\"{text[:300]}\"\n\n"
        f"Reply with ONLY one of: PASS, PARTIAL, FAIL\n"
        f"Then one sentence explaining which question(s) failed."
    )

    response = query_claude(prompt, timeout=30)
    if not response:
        return {"rule": "P-RD-01", "description": "Claude unavailable", "score": 5, "verdict": "warn"}

    response_upper = response.upper()
    if response_upper.startswith("PASS"):
        return {
            "rule": "P-RD-01",
            "description": response.strip(),
            "score": 10,
            "verdict": "pass",
        }
    elif "PARTIAL" in response_upper:
        return {
            "rule": "P-RD-01",
            "description": response.strip(),
            "score": 5,
            "verdict": "warn",
            "fix": f"Seg {seg_idx}: Strengthen stakes or add uncertainty",
        }
    else:
        return {
            "rule": "P-RD-01",
            "description": response.strip(),
            "score": 2,
            "verdict": "fail",
            "fix": f"Seg {seg_idx}: Viewer won't know why to care — add context or cut",
        }


# ── Validate All Segments ─────────────────────────────────────────────────

def validate_segments(segments, use_claude=True, sample_rate=1):
    """Run all checks against every segment (or a sample).

    Args:
        segments: flat list of director segment dicts
        use_claude: if True, run Claude-powered checks (slower)
        sample_rate: 1 = every segment, 3 = every 3rd, etc.

    Returns:
        (segment_results, overall_result)
    """
    segment_results = []
    total_score = 0
    passed = 0
    warned = 0
    failed = 0

    for i, seg in enumerate(segments):
        if i % sample_rate != 0:
            continue

        prev_seg = segments[i - 1] if i > 0 else None
        checks = []

        # Fast checks (no Claude)
        checks.append(check_energy_variation(seg, prev_seg, i))
        checks.append(check_sfx_justified(seg, i))
        checks.append(check_cut_frequency(seg, i, segments))
        checks.append(check_graphics_animate(seg, i))

        # Claude-powered checks (slower)
        if use_claude:
            checks.append(check_visual_narration_match(seg, i))
            # Only run litmus on every 3rd segment to save time
            if i % 3 == 0:
                checks.append(check_litmus_test(seg, i))

        # Score this segment
        seg_score = sum(c["score"] for c in checks) / len(checks) if checks else 0
        issues = [c for c in checks if c["verdict"] != "pass"]
        verdict = "pass" if seg_score >= 7 else ("warn" if seg_score >= 4 else "fail")

        if verdict == "pass":
            passed += 1
        elif verdict == "warn":
            warned += 1
        else:
            failed += 1

        total_score += seg_score

        segment_results.append({
            "segment_idx": i,
            "score": round(seg_score, 1),
            "verdict": verdict,
            "text_preview": seg.get("text", "")[:60],
            "issues": [
                {"rule": c["rule"], "description": c["description"],
                 "fix": c.get("fix")}
                for c in issues
            ],
        })

    # Global check: green/purple balance
    gp_result = check_green_purple_balance(segments)

    evaluated = len(segment_results)
    avg_score = total_score / evaluated if evaluated else 0

    overall = {
        "total_score": round(avg_score, 1),
        "segments_evaluated": evaluated,
        "segments_passed": passed,
        "segments_warned": warned,
        "segments_failed": failed,
        "green_purple_balance": gp_result,
        "worst_segments": sorted(
            segment_results, key=lambda s: s["score"]
        )[:5],
    }

    return segment_results, overall


# ── Fix Decisions ──────────────────────────────────────────────────────────

def fix_decisions(segments, segment_results, director_path):
    """Attempt to fix director decisions based on validation results.

    Fixes applied:
      - Remove unjustified SFX (AP-ED-03 fail)
      - Set transition_in to fade for chapter cards (AP-ED-02)
      - Adjust text_style from static to lower_third (AP-ED-02)
    """
    fixes_applied = 0

    for result in segment_results:
        if result["verdict"] == "pass":
            continue

        seg_idx = result["segment_idx"]
        if seg_idx >= len(segments):
            continue

        seg = segments[seg_idx]

        for issue in result["issues"]:
            rule = issue["rule"]

            # Remove unjustified SFX
            if rule == "AP-ED-03" and "fail" in str(result["verdict"]):
                if seg.get("sfx"):
                    seg["sfx"] = None
                    fixes_applied += 1

            # Fix graphics animation
            if rule == "AP-ED-02":
                if seg.get("text_overlay") and seg.get("text_style") == "static":
                    seg["text_style"] = "lower_third"
                    fixes_applied += 1
                if seg.get("chapter_card") and seg.get("transition_in") == "cut":
                    seg["transition_in"] = "fade_from_black"
                    fixes_applied += 1

    if fixes_applied > 0:
        # Reload original to write back
        with open(director_path) as f:
            data = json.load(f)

        # Write segments back into scenes structure
        if "scenes" in data:
            seg_iter = iter(segments)
            for scene in data["scenes"]:
                for j in range(len(scene.get("segments", []))):
                    scene["segments"][j] = next(seg_iter)
        else:
            data["segments"] = segments

        fixed_path = director_path.replace(".json", "_validated.json")
        with open(fixed_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n  {GREEN}Applied {fixes_applied} fixes{RESET}")
        print(f"  Saved: {fixed_path}")

    return fixes_applied


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Segment Validator — score each segment against playbook criteria"
    )
    parser.add_argument(
        "--director", required=True,
        help="Path to director v3 output JSON",
    )
    parser.add_argument(
        "--fix-decisions", action="store_true",
        help="Auto-fix director decisions that fail validation",
    )
    parser.add_argument(
        "--no-claude", action="store_true",
        help="Skip Claude-powered checks (faster, less thorough)",
    )
    parser.add_argument(
        "--sample-rate", type=int, default=1,
        help="Check every Nth segment (default: 1 = all)",
    )
    parser.add_argument(
        "--report", help="Save validation report to JSON file",
    )
    args = parser.parse_args()

    print(f"\n{BOLD}Segment Validator — Playbook Compliance Check{RESET}")
    print("=" * 60)

    # Load director
    print(f"\n  Loading: {args.director}")
    raw_data, segments = load_director(args.director)
    print(f"  {len(segments)} segments")

    # Load playbook
    playbook = load_playbook()
    print(f"  Playbook: {len(playbook)} modules loaded")

    # Validate
    use_claude = not args.no_claude
    mode = "full (with Claude)" if use_claude else "fast (no Claude)"
    print(f"\n  Running {mode} validation (sample rate: {args.sample_rate})...")

    segment_results, overall = validate_segments(
        segments,
        use_claude=use_claude,
        sample_rate=args.sample_rate,
    )

    # Print results
    print(f"\n{'='*60}")
    print(f"  {BOLD}OVERALL SCORE: {overall['total_score']:.1f}/10{RESET}")
    print(f"  Evaluated: {overall['segments_evaluated']} segments")
    print(f"  Passed: {GREEN}{overall['segments_passed']}{RESET}, "
          f"Warned: {YELLOW}{overall['segments_warned']}{RESET}, "
          f"Failed: {RED}{overall['segments_failed']}{RESET}")

    # Green/purple balance
    gp = overall["green_purple_balance"]
    gp_color = GREEN if gp["verdict"] == "pass" else (YELLOW if gp["verdict"] == "warn" else RED)
    print(f"\n  {gp_color}[P-SC-01] Green/Purple: {gp['description']}{RESET}")

    # Worst segments
    if overall["worst_segments"]:
        print(f"\n  {BOLD}Worst Segments:{RESET}")
        for ws in overall["worst_segments"]:
            color = RED if ws["verdict"] == "fail" else YELLOW
            print(f"    {color}Seg {ws['segment_idx']} ({ws['score']:.1f}/10){RESET}: "
                  f"{ws['text_preview']}")
            for iss in ws["issues"][:3]:
                fix_text = f" -> {iss['fix']}" if iss.get("fix") else ""
                print(f"      [{iss['rule']}] {iss['description'][:80]}{fix_text}")

    # Failed segments detail
    failed = [r for r in segment_results if r["verdict"] == "fail"]
    if failed:
        print(f"\n  {RED}{BOLD}FAILED SEGMENTS ({len(failed)}):{RESET}")
        for f_seg in failed:
            print(f"    Seg {f_seg['segment_idx']}: {f_seg['text_preview']}")
            for iss in f_seg["issues"]:
                fix_text = f"\n      FIX: {iss['fix']}" if iss.get("fix") else ""
                print(f"      [{iss['rule']}] {iss['description'][:100]}{fix_text}")

    # Fix decisions if requested
    if args.fix_decisions:
        print(f"\n  {BOLD}Fixing decisions...{RESET}")
        fix_decisions(segments, segment_results, args.director)

    # Save report
    if args.report:
        report = {
            "director_path": args.director,
            "overall": overall,
            "segments": segment_results,
        }
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Report saved: {args.report}")

    # Verdict
    if overall["segments_failed"] > 0:
        pct_failed = overall["segments_failed"] / overall["segments_evaluated"] * 100
        print(f"\n  {RED}{BOLD}VERDICT: {pct_failed:.0f}% segments failed — "
              f"fix before building timeline{RESET}")
        return 1
    elif overall["segments_warned"] > overall["segments_evaluated"] * 0.3:
        print(f"\n  {YELLOW}{BOLD}VERDICT: Too many warnings — "
              f"not ready to build{RESET}")
        return 1
    else:
        print(f"\n  {GREEN}{BOLD}VERDICT: Ready to build{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
