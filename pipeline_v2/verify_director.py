#!/usr/bin/env python3
"""
Verify Director v5 JSON for structural integrity.

Checks:
  - Timestamps monotonically increasing (excluding chapter markers)
  - No gaps > 15s between consecutive segments
  - No visual_file used > 2 times
  - Max 2 SFX per chapter
  - Only valid chapter cards
  - At least 3 clip_audio "play" or "play_then_mute" moments
  - Every visual_file exists on disk

Usage:
  python -m pipeline_v2.verify_director
  python -m pipeline_v2.verify_director --director path/to/file.json
"""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_DIRECTOR = PROJECT_ROOT / "storyboards" / "breaking_law_directed_v5.json"

VALID_CHAPTERS = {
    "COLD OPEN",
    "THE FORMULA",
    "THE DATA",
    "THE MACHINES",
    "THE RENT",
    "THE RECKONING",
}

FOOTAGE_DIRS = [
    PROJECT_ROOT / "footage" / "breaking_law" / "clips",
    PROJECT_ROOT / "footage" / "breaking_law" / "images",
    PROJECT_ROOT / "footage" / "breaking_law" / "gap_fills" / "images",
]


def find_media_file(filename):
    """Search for a media file across all footage directories."""
    if not filename:
        return None
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename
    name_stem = os.path.splitext(filename)[0]
    for search_dir in FOOTAGE_DIRS:
        direct = search_dir / filename
        if direct.exists():
            return str(direct)
        if search_dir.exists():
            for dirpath, _, filenames in os.walk(search_dir):
                if filename in filenames:
                    return os.path.join(dirpath, filename)
                for f in filenames:
                    f_stem = os.path.splitext(f)[0]
                    if f_stem.startswith(name_stem) or name_stem.startswith(f_stem):
                        return os.path.join(dirpath, f)
    return None


def flatten_segments(data):
    """Flatten scenes -> segments, expanding beats."""
    raw = []
    for scene in data.get("scenes", []):
        raw.extend(scene.get("segments", []))

    segments = []
    for seg in raw:
        beats = seg.get("beats")
        if beats and len(beats) > 0:
            seg_start = seg.get("_timeline_start_sec", 0.0)
            seg_end = seg.get("_timeline_end_sec", seg_start + 1.0)
            seg_duration = seg_end - seg_start
            beat_duration = seg_duration / len(beats) if len(beats) > 0 else seg_duration
            for i, beat in enumerate(beats):
                expanded = dict(seg)
                expanded["visual_file"] = beat.get("visual_file", seg.get("visual_file"))
                expanded["visual_type"] = beat.get("visual_type", seg.get("visual_type"))
                expanded["clip_audio"] = beat.get("clip_audio", seg.get("clip_audio"))
                expanded["_timeline_start_sec"] = seg_start + i * beat_duration
                expanded["_timeline_end_sec"] = seg_start + (i + 1) * beat_duration
                expanded["beats"] = None
                expanded["sfx"] = beat.get("sfx", seg.get("sfx"))
                expanded["chapter_card"] = None  # only parent has card
                segments.append(expanded)
        else:
            segments.append(seg)
    return segments


def run_checks(data, segments):
    """Run all verification checks. Returns (passes, failures) lists."""
    passes = []
    failures = []

    # --- 1. Timestamps monotonically increasing (excluding chapter markers) ---
    non_chapter = [s for s in segments
                   if not (s.get("text", "").strip().startswith("[CHAPTER:"))]
    mono_ok = True
    mono_violations = []
    for i in range(1, len(non_chapter)):
        prev_start = non_chapter[i - 1].get("_timeline_start_sec", 0)
        curr_start = non_chapter[i].get("_timeline_start_sec", 0)
        if curr_start < prev_start:
            mono_ok = False
            mono_violations.append(
                f"  seg {i}: {curr_start:.2f}s < prev {prev_start:.2f}s "
                f"({non_chapter[i].get('text', '')[:40]})")
    if mono_ok:
        passes.append("Timestamps monotonically increasing")
    else:
        failures.append(f"Timestamps NOT monotonic ({len(mono_violations)} violations):\n"
                        + "\n".join(mono_violations[:5]))

    # --- 2. No gaps > 15s between consecutive segments ---
    gap_ok = True
    gap_violations = []
    for i in range(1, len(non_chapter)):
        prev_end = non_chapter[i - 1].get("_timeline_end_sec", 0)
        curr_start = non_chapter[i].get("_timeline_start_sec", 0)
        gap = curr_start - prev_end
        if gap > 15.0:
            gap_ok = False
            gap_violations.append(
                f"  gap={gap:.1f}s between seg {i-1} ({prev_end:.1f}s) and seg {i} ({curr_start:.1f}s)")
    if gap_ok:
        passes.append("No gaps > 15s between segments")
    else:
        failures.append(f"Gaps > 15s found ({len(gap_violations)}):\n"
                        + "\n".join(gap_violations[:5]))

    # --- 3. No visual_file used > 2 times ---
    visual_counts = Counter()
    for seg in segments:
        vf = seg.get("visual_file")
        if vf:
            visual_counts[vf] += 1
    overused = {k: v for k, v in visual_counts.items() if v > 2}
    if not overused:
        passes.append("No visual_file used > 2 times")
    else:
        failures.append(f"Visual files used > 2 times ({len(overused)}):\n"
                        + "\n".join(f"  {k}: {v}x" for k, v in
                                    sorted(overused.items(), key=lambda x: -x[1])[:10]))

    # --- 4. Max 2 SFX per chapter ---
    current_chapter = "COLD OPEN"
    chapter_sfx = Counter()
    for seg in segments:
        card = seg.get("chapter_card")
        if card and card.upper().strip() in VALID_CHAPTERS:
            current_chapter = card.upper().strip()
        sfx = seg.get("sfx")
        if sfx and (sfx.get("file") or sfx.get("name")):
            chapter_sfx[current_chapter] += 1
    sfx_over = {k: v for k, v in chapter_sfx.items() if v > 2}
    if not sfx_over:
        passes.append("Max 2 SFX per chapter")
    else:
        failures.append(f"Chapters with > 2 SFX:\n"
                        + "\n".join(f"  {k}: {v} SFX" for k, v in sfx_over.items()))

    # --- 5. Only valid chapter cards ---
    invalid_cards = set()
    for seg in segments:
        card = seg.get("chapter_card")
        if card and card.upper().strip() not in VALID_CHAPTERS:
            invalid_cards.add(card)
    if not invalid_cards:
        passes.append("All chapter cards are valid")
    else:
        failures.append(f"Invalid chapter cards: {sorted(invalid_cards)}")

    # --- 6. At least 3 clip_audio play moments ---
    play_count = sum(1 for seg in segments
                     if seg.get("clip_audio") in ("play", "play_then_mute"))
    if play_count >= 3:
        passes.append(f"clip_audio play moments: {play_count} (>= 3)")
    else:
        failures.append(f"Only {play_count} clip_audio play moments (need >= 3)")

    # --- 7b. Clip audio advisory — warn if density seems high ---
    # Guideline: ~1 moment per 3 minutes of video
    total_dur = segments[-1].get("_timeline_end_sec", 0) if segments else 0
    video_min = total_dur / 60 if total_dur > 0 else 20
    recommended = max(3, int(video_min / 3))
    if play_count > recommended * 2:
        # Not a FAIL — just a warning. Director makes editorial choices.
        passes.append(f"clip_audio: {play_count} moments (high for {video_min:.0f}-min video, "
                      f"guideline ~{recommended} — review director prompt)")
    else:
        passes.append(f"clip_audio density: {play_count} moments / {video_min:.0f} min "
                      f"(guideline ~{recommended})")

    # --- 8. Every visual_file exists on disk ---
    missing_files = []
    checked = set()
    for seg in segments:
        vf = seg.get("visual_file")
        if vf and vf not in checked:
            checked.add(vf)
            if not find_media_file(vf):
                missing_files.append(vf)
    if not missing_files:
        passes.append(f"All {len(checked)} visual files exist on disk")
    else:
        failures.append(f"Missing visual files ({len(missing_files)}/{len(checked)}):\n"
                        + "\n".join(f"  {f}" for f in missing_files[:10]))

    return passes, failures


def main():
    parser = argparse.ArgumentParser(description="Verify director v5 JSON")
    parser.add_argument("--director", type=str, default=str(DEFAULT_DIRECTOR),
                        help="Path to director JSON file")
    args = parser.parse_args()

    director_path = Path(args.director)
    if not director_path.exists():
        print(f"FAIL: Director file not found: {director_path}")
        sys.exit(1)

    with open(director_path) as f:
        data = json.load(f)

    segments = flatten_segments(data)
    print(f"Loaded {len(segments)} segments (after beat expansion) from {director_path.name}")
    print()

    passes, failures = run_checks(data, segments)

    for p in passes:
        print(f"  PASS  {p}")
    for f in failures:
        print(f"  FAIL  {f}")

    print()
    total = len(passes) + len(failures)
    print(f"Results: {len(passes)}/{total} passed, {len(failures)}/{total} failed")

    if failures:
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
