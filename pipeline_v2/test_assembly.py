#!/usr/bin/env python3
"""
Integration test — validates the full assembly pipeline produces a cohesive video.

Runs load_paper_edit() → build() → verify_fcpxml checks, plus additional
checks for music coverage, chapter card placement, intro handling, and sync.

Usage:
  python -m pipeline_v2.test_assembly
  python -m pipeline_v2.test_assembly --paper-edit storyboards/breaking_law_paper_edit_v2.json
"""

import argparse
import json
import os
import sys
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.fcpxml_builder_v2 import (
    FCPXMLBuilderV2, load_paper_edit, NARRATION_PATH, MUSIC_DIR,
    find_media_file, get_duration, is_image
)
from pipeline_v2.verify_fcpxml import run_checks

DEFAULT_PAPER_EDIT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v2.json"
FCPXML_OUTPUT = PROJECT_ROOT / "test_assembly_output.fcpxml"


def get_wav_duration(path):
    """Get WAV duration in seconds."""
    try:
        with wave.open(str(path), 'r') as wf:
            return wf.getnframes() / wf.getframerate()
    except Exception:
        return None


def test_load_paper_edit(paper_edit_path):
    """Test 1: load_paper_edit produces valid segments."""
    passes = []
    failures = []

    print("\n=== Test 1: Load Paper Edit ===")
    segments, chapter_map, sfx_by_chapter, music_by_chapter = load_paper_edit(paper_edit_path)

    # Check segments exist
    if len(segments) > 100:
        passes.append(f"Loaded {len(segments)} segments")
    else:
        failures.append(f"Only {len(segments)} segments (expected 100+)")

    # Check all visual files found
    missing = []
    for seg in segments:
        vf = seg.get("visual_file", "")
        if vf and not seg.get("chapter_card"):
            path = find_media_file(vf)
            if not path:
                missing.append(vf)
    if not missing:
        passes.append("All visual files resolved to disk")
    else:
        failures.append(f"{len(missing)} visual files not found: {missing[:5]}")

    # Check no beats past narration end
    narr_dur = get_wav_duration(NARRATION_PATH)
    if narr_dur:
        past_end = [s for s in segments if s.get("_narr_start", 0) >= narr_dur and not s.get("chapter_card")]
        if not past_end:
            passes.append(f"No segments past narration end ({narr_dur:.1f}s)")
        else:
            failures.append(f"{len(past_end)} segments past narration end")

    # Check chapters
    if len(chapter_map) >= 5:
        passes.append(f"{len(chapter_map)} chapters")
    else:
        failures.append(f"Only {len(chapter_map)} chapters (expected 5+)")

    # Check intro was applied
    first_seg = segments[0] if segments else {}
    intro_spec = PROJECT_ROOT / "storyboards" / "intro_spec_locked.json"
    if intro_spec.exists():
        with open(intro_spec) as f:
            spec = json.load(f)
        intro_clip = spec["segments"][0]["visual_file"]
        if first_seg.get("visual_file") == intro_clip:
            passes.append(f"Intro applied: first clip is {intro_clip}")
        else:
            failures.append(f"Intro NOT applied: first clip is {first_seg.get('visual_file')}, expected {intro_clip}")
    else:
        passes.append("No intro spec (skipped)")

    # Check music per chapter
    for ch_num in chapter_map:
        if ch_num in music_by_chapter:
            mf, ms, me = music_by_chapter[ch_num]
            mpath = str(MUSIC_DIR / mf)
            if os.path.exists(mpath):
                passes.append(f"Ch{ch_num} music: {mf}")
            else:
                failures.append(f"Ch{ch_num} music not found: {mpath}")
        else:
            failures.append(f"Ch{ch_num} has no music assignment")

    return passes, failures, segments, chapter_map, sfx_by_chapter, music_by_chapter


def test_build_fcpxml(segments, chapter_map, sfx_by_chapter, music_by_chapter):
    """Test 2: Build FCPXML and run all verification checks."""
    passes = []
    failures = []

    print("\n=== Test 2: Build FCPXML ===")
    builder = FCPXMLBuilderV2()
    tree = builder.build(
        segments=segments,
        chapter_map=chapter_map,
        narration_path=NARRATION_PATH,
        sfx_by_chapter=sfx_by_chapter,
        music_by_chapter=music_by_chapter,
    )

    # Write to temp file
    tree.write(str(FCPXML_OUTPUT), encoding="unicode", xml_declaration=True)
    size = os.path.getsize(str(FCPXML_OUTPUT))
    passes.append(f"FCPXML written: {size / 1024:.0f} KB")

    # Run all verify_fcpxml checks
    print("\n=== Test 3: Verify FCPXML ===")
    v_passes, v_failures, v_warnings = run_checks(
        str(FCPXML_OUTPUT),
        min_v1_clips=100,
        skip_ffprobe=True,
    )
    passes.extend(v_passes)
    failures.extend(v_failures)

    return passes, failures


def test_music_coverage(segments, chapter_map, music_by_chapter):
    """Test 4: Music covers >80% of timeline via chapter assignments."""
    passes = []
    failures = []

    print("\n=== Test 4: Music Coverage ===")
    narr_dur = get_wav_duration(NARRATION_PATH) or 1404.7

    # Calculate music coverage from chapter assignments
    total_music = 0
    for ch_num, (music_file, ch_start, ch_end) in music_by_chapter.items():
        music_path = str(MUSIC_DIR / music_file)
        if os.path.exists(music_path):
            chapter_dur = ch_end - ch_start
            total_music += chapter_dur  # music loops to fill full chapter

    coverage_pct = (total_music / narr_dur) * 100 if narr_dur else 0

    if coverage_pct > 80:
        passes.append(f"Music coverage: {coverage_pct:.0f}% ({total_music:.0f}s / {narr_dur:.0f}s)")
    else:
        failures.append(f"Music coverage only {coverage_pct:.0f}% (need >80%): {total_music:.0f}s / {narr_dur:.0f}s")

    return passes, failures


def main():
    parser = argparse.ArgumentParser(description="Assembly Integration Test")
    parser.add_argument("--paper-edit", type=str, default=str(DEFAULT_PAPER_EDIT))
    args = parser.parse_args()

    print("=" * 60)
    print("  Assembly Integration Test")
    print("=" * 60)

    all_passes = []
    all_failures = []

    # Test 1: Load paper edit
    p, f, segments, chapter_map, sfx, music = test_load_paper_edit(args.paper_edit)
    all_passes.extend(p)
    all_failures.extend(f)

    # Test 2+3: Build and verify FCPXML
    p, f = test_build_fcpxml(segments, chapter_map, sfx, music)
    all_passes.extend(p)
    all_failures.extend(f)

    # Test 4: Music coverage
    p, f = test_music_coverage(segments, chapter_map, music)
    all_passes.extend(p)
    all_failures.extend(f)

    # Summary
    print("\n" + "=" * 60)
    print(f"  RESULTS: {len(all_passes)} passed, {len(all_failures)} failed")
    print("=" * 60)

    if all_failures:
        print("\n  FAILURES:")
        for f in all_failures:
            print(f"    FAIL  {f}")

    print()
    for p in all_passes:
        print(f"  PASS  {p}")

    # Cleanup
    if FCPXML_OUTPUT.exists():
        FCPXML_OUTPUT.unlink()

    sys.exit(1 if all_failures else 0)


if __name__ == "__main__":
    main()
