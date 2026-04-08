#!/usr/bin/env python3
"""
Edit Reviewer — automated editorial review of the paper edit.

7 checks that catch the problems the old pipeline missed:
  1. Visual-narration semantic match
  2. Generic B-roll where specific A-roll exists
  3. Visual overuse (same file 3+ times)
  4. Missing clip audio at key narrative moments
  5. Tension mismatch (calm visuals during high-tension narration)
  6. Cut frequency vs narrative function rules
  7. Missing WHY justification

Usage:
  python -m pipeline_v2.edit_reviewer
  python -m pipeline_v2.edit_reviewer --paper-edit storyboards/breaking_law_paper_edit.json
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude

DEFAULT_PAPER_EDIT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit.json"
DEFAULT_SELECTS = PROJECT_ROOT / "storyboards" / "breaking_law_selects.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_reviewed.json"

# LearnByLeo cut duration rules by narrative function
CUT_DURATION_RULES = {
    "exposition": (8, 12),
    "tension_build": (2, 4),
    "evidence": (5, 7),
    "character_intro": (5, 7),
    "hook": (12, 20),
    "revelation": (2, 3),
    "transition": (2, 4),
}


def check_missing_why(beat):
    """Check 7: WHY column must have substantive reasoning."""
    why = beat.get("why", "")
    if not why or len(why) < 10:
        return {
            "check": "missing_why",
            "severity": "error",
            "message": "No editorial reasoning for visual choice",
            "confidence": 1.0,
        }
    # Check for generic non-answers
    generic = ["generic", "stock footage", "related to topic", "relevant", "matches"]
    if any(g in why.lower() for g in generic) and len(why) < 30:
        return {
            "check": "missing_why",
            "severity": "warning",
            "message": f"WHY is generic: '{why}'",
            "confidence": 0.7,
        }
    return None


def check_visual_overuse(beats):
    """Check 3: Flag visuals used 3+ times."""
    counts = Counter(b.get("visual_file", "") for b in beats if b.get("visual_file"))
    flags = []
    for filename, count in counts.items():
        if count >= 3:
            affected = [i for i, b in enumerate(beats) if b.get("visual_file") == filename]
            for idx in affected[2:]:  # flag the 3rd+ usage
                flags.append((idx, {
                    "check": "visual_overuse",
                    "severity": "warning",
                    "message": f"'{filename}' used {count} times (this is usage #{affected.index(idx)+1})",
                    "confidence": 0.9,
                }))
    return flags


def check_generic_over_specific(beat, selects):
    """Check 2: B-roll/stock used when entity index has specific A-roll."""
    if beat.get("visual_type") not in ("b_roll", "stock"):
        return None

    text = beat.get("text", "").lower()
    entity_index = selects.get("entity_index", {})

    for entity_name, entity_data in entity_index.items():
        if entity_name.lower() in text:
            best_a = entity_data.get("best_a_roll")
            if best_a and best_a != beat.get("visual_file"):
                best_quote = None
                for clip in entity_data.get("clips", []):
                    if clip.get("best_quote"):
                        best_quote = clip["best_quote"][:60]
                        break

                return {
                    "check": "generic_over_specific",
                    "severity": "warning",
                    "message": f"Narration mentions '{entity_name}' but using generic {beat.get('visual_type')} "
                               f"instead of A-roll '{best_a}'",
                    "suggested_fix": {
                        "visual_file": best_a,
                        "visual_type": "a_roll",
                        "why": f"Shows {entity_name} directly — specific footage exists",
                        "clip_audio_quote": best_quote,
                    },
                    "confidence": 0.8,
                }
    return None


def check_tension_mismatch(beat):
    """Check 5: Tension level vs visual type mismatch."""
    tension = beat.get("tension_level", 0.5)
    visual_type = beat.get("visual_type", "b_roll")
    nf = beat.get("narrative_function", "exposition")

    # High tension with stock footage
    if tension > 0.7 and visual_type == "stock":
        return {
            "check": "tension_mismatch",
            "severity": "warning",
            "message": f"High tension ({tension:.1f}) with stock footage — "
                       f"should use specific A-roll or evidence",
            "confidence": 0.7,
        }

    # Revelation with B-roll
    if nf == "revelation" and visual_type in ("b_roll", "stock"):
        return {
            "check": "tension_mismatch",
            "severity": "warning",
            "message": "Revelation beat using B-roll/stock — should show the reveal directly",
            "confidence": 0.75,
        }

    return None


def check_cut_frequency(beats):
    """Check 6: Beat duration vs narrative function rules."""
    flags = []
    for i, beat in enumerate(beats):
        if beat.get("is_chapter_marker"):
            continue
        nf = beat.get("narrative_function", "exposition")
        duration = beat.get("duration", 0)
        if duration <= 0:
            continue

        rules = CUT_DURATION_RULES.get(nf)
        if not rules:
            continue

        min_dur, max_dur = rules
        # Allow 50% tolerance
        if duration > max_dur * 1.5:
            flags.append((i, {
                "check": "cut_frequency",
                "severity": "info",
                "message": f"{nf} beat is {duration:.1f}s (guideline: {min_dur}-{max_dur}s) — consider splitting",
                "confidence": 0.6,
            }))
        elif duration < min_dur * 0.5 and duration > 0.5:
            flags.append((i, {
                "check": "cut_frequency",
                "severity": "info",
                "message": f"{nf} beat is {duration:.1f}s (guideline: {min_dur}-{max_dur}s) — may be too short",
                "confidence": 0.5,
            }))

    return flags


def check_missing_clip_audio(beat, selects):
    """Check 4: Narration references a quote but clip audio not used."""
    if beat.get("clip_audio") != "mute":
        return None

    text = beat.get("text", "").lower()
    nf = beat.get("narrative_function", "")

    # Only flag for evidence/revelation/character_intro beats
    if nf not in ("evidence", "revelation", "character_intro"):
        return None

    # Check if narration references speech ("said", "testified", "announced")
    speech_words = ["said", "testified", "announced", "stated", "told",
                    "explained", "revealed", "admitted", "claimed", "argued"]
    if not any(w in text for w in speech_words):
        return None

    # Check if the visual file has quotable moments
    visual_file = beat.get("visual_file", "")
    clip_data = selects.get("clips", {}).get(visual_file, {})
    moments = clip_data.get("quotable_moments", [])

    if moments and moments[0].get("editorial_value", 0) >= 7:
        return {
            "check": "missing_clip_audio",
            "severity": "info",
            "message": f"Narration references speech, and clip has strong quote: "
                       f"\"{moments[0]['text'][:50]}...\" (value {moments[0]['editorial_value']}/10)",
            "suggested_fix": {
                "clip_audio": "play_then_mute",
                "clip_audio_quote": moments[0]["text"],
                "clip_audio_duration": 4,
            },
            "confidence": 0.65,
        }

    return None


def check_visual_narration_match_batch(beats, batch_size=12):
    """Check 1: Semantic visual-narration match using Claude (batched)."""
    flags = []
    content_beats = [(i, b) for i, b in enumerate(beats)
                     if not b.get("is_chapter_marker") and b.get("visual_file")]

    for batch_start in range(0, len(content_beats), batch_size):
        batch = content_beats[batch_start:batch_start + batch_size]

        items = "\n".join(
            f"  Beat {idx}: narration=\"{b['text'][:80]}\" visual=\"{b.get('visual_file', '?')}\" "
            f"why=\"{b.get('why', '?')[:60]}\""
            for idx, b in batch
        )

        prompt = f"""Review these documentary beats. For each, rate 1-10 how well the visual matches the narration.
Flag any beat where the visual is WRONG for what's being said (score < 5).

{items}

Return JSON array:
[{{"beat_idx": 0, "match_score": 8, "issue": null}}, ...]
Only include beats with score < 5. If all are fine, return empty array [].
ONLY JSON, no other text."""

        try:
            response = query_claude(prompt, timeout=60)
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                results = json.loads(match.group())
                for result in results:
                    if result.get("match_score", 10) < 5:
                        beat_idx = result.get("beat_idx", 0)
                        # Map batch-relative index to absolute
                        if beat_idx < len(batch):
                            abs_idx = batch[beat_idx][0]
                            flags.append((abs_idx, {
                                "check": "visual_narration_match",
                                "severity": "error",
                                "message": result.get("issue", "Visual doesn't match narration"),
                                "confidence": 0.8,
                            }))
        except Exception as e:
            print(f"    WARNING: semantic check failed: {e}")

    return flags


def review_paper_edit(paper_edit_path, selects_path, output_path):
    """Run all 7 editorial checks on the paper edit."""
    with open(paper_edit_path) as f:
        paper_edit = json.load(f)

    with open(selects_path) as f:
        selects = json.load(f)

    beats = paper_edit.get("beats", [])
    print(f"  Reviewing {len(beats)} beats...")

    # Initialize flags per beat
    for beat in beats:
        beat["review_flags"] = []

    # Check 7: Missing WHY
    for i, beat in enumerate(beats):
        if beat.get("is_chapter_marker"):
            continue
        flag = check_missing_why(beat)
        if flag:
            beat["review_flags"].append(flag)

    why_flags = sum(1 for b in beats if any(f["check"] == "missing_why" for f in b["review_flags"]))
    print(f"  Check 7 (missing WHY): {why_flags} flags")

    # Check 3: Visual overuse
    overuse_flags = check_visual_overuse(beats)
    for idx, flag in overuse_flags:
        beats[idx]["review_flags"].append(flag)
    print(f"  Check 3 (visual overuse): {len(overuse_flags)} flags")

    # Check 2: Generic over specific
    generic_count = 0
    for beat in beats:
        if beat.get("is_chapter_marker"):
            continue
        flag = check_generic_over_specific(beat, selects)
        if flag:
            beat["review_flags"].append(flag)
            generic_count += 1
    print(f"  Check 2 (generic over specific): {generic_count} flags")

    # Check 5: Tension mismatch
    tension_count = 0
    for beat in beats:
        if beat.get("is_chapter_marker"):
            continue
        flag = check_tension_mismatch(beat)
        if flag:
            beat["review_flags"].append(flag)
            tension_count += 1
    print(f"  Check 5 (tension mismatch): {tension_count} flags")

    # Check 6: Cut frequency
    freq_flags = check_cut_frequency(beats)
    for idx, flag in freq_flags:
        beats[idx]["review_flags"].append(flag)
    print(f"  Check 6 (cut frequency): {len(freq_flags)} flags")

    # Check 4: Missing clip audio
    audio_count = 0
    for beat in beats:
        if beat.get("is_chapter_marker"):
            continue
        flag = check_missing_clip_audio(beat, selects)
        if flag:
            beat["review_flags"].append(flag)
            audio_count += 1
    print(f"  Check 4 (missing clip audio): {audio_count} flags")

    # Check 1: Semantic visual-narration match (Claude — slowest, run last)
    print(f"  Check 1 (semantic match via Claude)...")
    semantic_flags = check_visual_narration_match_batch(beats)
    for idx, flag in semantic_flags:
        beats[idx]["review_flags"].append(flag)
    print(f"  Check 1 (semantic match): {len(semantic_flags)} flags")

    # Summary
    total_flags = sum(len(b.get("review_flags", [])) for b in beats)
    error_flags = sum(1 for b in beats for f in b.get("review_flags", []) if f["severity"] == "error")
    warning_flags = sum(1 for b in beats for f in b.get("review_flags", []) if f["severity"] == "warning")
    info_flags = sum(1 for b in beats for f in b.get("review_flags", []) if f["severity"] == "info")

    paper_edit["review_summary"] = {
        "total_flags": total_flags,
        "errors": error_flags,
        "warnings": warning_flags,
        "info": info_flags,
        "flagged_beats": sum(1 for b in beats if b.get("review_flags")),
        "clean_beats": sum(1 for b in beats if not b.get("review_flags")),
    }

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(paper_edit, f, indent=2)

    rs = paper_edit["review_summary"]
    print(f"\n  Review complete: {rs['total_flags']} flags "
          f"({rs['errors']} errors, {rs['warnings']} warnings, {rs['info']} info)")
    print(f"  {rs['flagged_beats']} beats flagged, {rs['clean_beats']} clean")
    print(f"  Saved: {output_path}")

    return paper_edit


def main():
    parser = argparse.ArgumentParser(description="Edit Reviewer")
    parser.add_argument("--paper-edit", type=str, default=str(DEFAULT_PAPER_EDIT))
    parser.add_argument("--selects", type=str, default=str(DEFAULT_SELECTS))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    print("Edit Reviewer")
    review_paper_edit(args.paper_edit, args.selects, args.output)


if __name__ == "__main__":
    main()
