#!/usr/bin/env python3
"""
Edit Approve — interactive approval of the reviewed paper edit.

Shows each flagged beat and lets the user approve, override, or skip.
Also supports non-interactive auto-approve mode for CI/batch runs.

Usage:
  python -m pipeline_v2.edit_approve --reviewed storyboards/breaking_law_paper_edit_reviewed.json
  python -m pipeline_v2.edit_approve --auto-approve 0.85  # approve fixes with confidence >= 0.85
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_REVIEWED = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_reviewed.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_approved.json"


def display_flag(beat, flag, flag_num, total_flags):
    """Display a single flag for user review."""
    print(f"\n{'='*70}")
    print(f"[Flag {flag_num}/{total_flags}] Beat {beat.get('beat_id', '?')} "
          f"({beat.get('start_sec', 0):.1f}-{beat.get('end_sec', 0):.1f}s) "
          f"Chapter: {beat.get('chapter', '?')}")
    print(f"  Script: \"{beat.get('text', '')[:80]}\"")
    print(f"  Current visual: {beat.get('visual_file', '?')} ({beat.get('visual_type', '?')})")
    print(f"  WHY: {beat.get('why', '(none)')[:60]}")
    print(f"  Tension: {beat.get('tension_level', 0):.1f} | Function: {beat.get('narrative_function', '?')}")
    print()
    print(f"  [{flag['severity'].upper()}] {flag['check']}: {flag['message']}")

    if flag.get("suggested_fix"):
        fix = flag["suggested_fix"]
        print(f"\n  Suggested fix:")
        for k, v in fix.items():
            if v is not None:
                print(f"    {k}: {v}")

    print(f"  Confidence: {flag.get('confidence', 0):.0%}")


def apply_fix(beat, flag):
    """Apply a suggested fix to a beat."""
    fix = flag.get("suggested_fix", {})
    for key, value in fix.items():
        if value is not None:
            beat[key] = value
    beat.setdefault("applied_fixes", []).append(flag["check"])
    return beat


def approve_interactive(reviewed_path, output_path):
    """Interactive approval — show each flag, user decides."""
    with open(reviewed_path) as f:
        paper_edit = json.load(f)

    beats = paper_edit.get("beats", [])
    flagged = [(i, b) for i, b in enumerate(beats) if b.get("review_flags")]
    total_flags = sum(len(b.get("review_flags", [])) for b in beats)

    if not flagged:
        print("  No flags to review — all beats approved.")
        with open(output_path, 'w') as f:
            json.dump(paper_edit, f, indent=2)
        return paper_edit

    print(f"\n  {total_flags} flags across {len(flagged)} beats to review.\n")

    flag_num = 0
    for beat_idx, beat in flagged:
        for flag in beat.get("review_flags", []):
            flag_num += 1
            display_flag(beat, flag, flag_num, total_flags)

            if flag.get("suggested_fix"):
                prompt = "  [a]pprove fix  [s]kip  [A]pprove all remaining > "
            else:
                prompt = "  [s]kip  [A]pprove all remaining > "

            try:
                choice = input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                choice = "s"

            if choice == "a" and flag.get("suggested_fix"):
                apply_fix(beat, flag)
                print("  -> Applied fix")
            elif choice.upper() == "A":
                # Auto-approve all remaining
                apply_fix(beat, flag) if flag.get("suggested_fix") else None
                for remaining_beat_idx, remaining_beat in flagged[flagged.index((beat_idx, beat)):]:
                    for rf in remaining_beat.get("review_flags", []):
                        if rf.get("suggested_fix"):
                            apply_fix(remaining_beat, rf)
                print(f"  -> Approved all remaining flags")
                break
            else:
                print("  -> Skipped")

        else:
            continue
        break  # break outer loop if "Approve all" was selected

    # Clear review_flags from output (they've been processed)
    for beat in beats:
        beat.pop("review_flags", None)

    with open(output_path, 'w') as f:
        json.dump(paper_edit, f, indent=2)

    print(f"\n  Approved paper edit saved: {output_path}")
    return paper_edit


def approve_auto(reviewed_path, output_path, threshold=0.85):
    """Non-interactive — auto-approve fixes above confidence threshold."""
    with open(reviewed_path) as f:
        paper_edit = json.load(f)

    beats = paper_edit.get("beats", [])
    applied = 0
    skipped = 0

    for beat in beats:
        for flag in beat.get("review_flags", []):
            if flag.get("suggested_fix") and flag.get("confidence", 0) >= threshold:
                apply_fix(beat, flag)
                applied += 1
            else:
                skipped += 1

        beat.pop("review_flags", None)

    with open(output_path, 'w') as f:
        json.dump(paper_edit, f, indent=2)

    print(f"  Auto-approved {applied} fixes (threshold {threshold:.0%}), skipped {skipped}")
    print(f"  Saved: {output_path}")
    return paper_edit


def main():
    parser = argparse.ArgumentParser(description="Edit Approve — review and approve paper edit flags")
    parser.add_argument("--reviewed", type=str, default=str(DEFAULT_REVIEWED))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--auto-approve", type=float, default=None,
                        help="Auto-approve fixes with confidence >= threshold (e.g., 0.85)")
    args = parser.parse_args()

    print("Edit Approve")

    if args.auto_approve is not None:
        approve_auto(args.reviewed, args.output, args.auto_approve)
    else:
        approve_interactive(args.reviewed, args.output)


if __name__ == "__main__":
    main()
