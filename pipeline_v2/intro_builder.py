#!/usr/bin/env python3
"""
Intro Builder — first-class pipeline stage for the video intro.

Reads intro_spec_locked.json (user-approved intro decisions) and returns
structured intro data for the FCPXML builder. Replaces scattered intro logic
in apply_locked_intro.py, fcpxml_builder overlay skip, chapter_assembler
CHAPTERS[0] special handling, and chapter card filtering.

The intro is treated as a SEPARATE section from the director's output:
  - Intro clips play BEFORE the VO narration starts
  - VO narration.wav is offset by the intro duration
  - No chapter cards appear during the intro
  - Overlays and SFX from the intro spec are placed independently

Usage:
  python -m pipeline_v2.intro_builder
  python -m pipeline_v2.intro_builder --spec path/to/intro_spec.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline_v2.fcpxml_builder_v2 import find_media_file, get_duration, is_image

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_SPEC = PROJECT_ROOT / "storyboards" / "intro_spec_locked.json"


def parse_time_range(time_str):
    """Parse time range like '0.0-32.8s' into (start, end)."""
    time_str = time_str.rstrip('s')
    parts = time_str.split('-')
    return float(parts[0]), float(parts[1])


def load_intro(spec_path=None):
    """Load intro spec and return structured intro data.

    Returns:
        dict with:
            - segments: list of intro segment dicts with resolved paths
            - total_duration: total intro duration in seconds
            - vo_start_offset: where VO narration should begin (= total_duration)
            - chapter_card_blackout_end: no chapter cards before this time
    """
    spec_path = Path(spec_path or DEFAULT_SPEC)
    if not spec_path.exists():
        print(f"WARNING: Intro spec not found at {spec_path}")
        return None

    with open(spec_path) as f:
        spec = json.load(f)

    intro_segments = []
    max_end = 0.0

    for seg in spec.get("segments", []):
        time_range = seg.get("time", "0-0s")
        start, end = parse_time_range(time_range)
        max_end = max(max_end, end)

        vf = seg.get("visual_file", "")
        resolved_path = find_media_file(vf) if vf else None

        # Get actual media duration for video clips
        source_dur = None
        if resolved_path and not is_image(resolved_path):
            source_dur = get_duration(resolved_path)

        intro_segments.append({
            "index": seg.get("index", len(intro_segments)),
            "start_sec": start,
            "end_sec": end,
            "duration": end - start,
            "visual_file": vf,
            "visual_path": resolved_path,
            "visual_type": seg.get("visual_type", "video_clip"),
            "clip_audio": seg.get("clip_audio", "mute"),
            "clip_audio_duration": seg.get("clip_audio_duration"),
            "transition_in": seg.get("transition_in", "cut"),
            "overlay_text": seg.get("overlay"),
            "sfx_file": seg.get("sfx"),
            "music_state": seg.get("music_state", "playing"),
            "text": seg.get("text", ""),
            "source_duration": source_dur,
        })

    total_duration = max_end

    result = {
        "segments": intro_segments,
        "total_duration": total_duration,
        "vo_start_offset": total_duration,
        "chapter_card_blackout_end": total_duration + 5.0,  # no cards until 5s after intro
        "spec_version": spec.get("_version", "unknown"),
    }

    return result


def validate_intro(intro_data):
    """Validate intro data. Returns (passes, failures)."""
    passes = []
    failures = []

    if not intro_data:
        failures.append("No intro data loaded")
        return passes, failures

    segs = intro_data["segments"]
    if len(segs) < 2:
        failures.append(f"Only {len(segs)} intro segments (need at least 2)")
    else:
        passes.append(f"{len(segs)} intro segments")

    # Check all visual files resolve
    missing = []
    for seg in segs:
        if seg["visual_file"] and not seg["visual_path"]:
            missing.append(seg["visual_file"])

    if not missing:
        passes.append("All intro visual files found on disk")
    else:
        failures.append(f"Missing intro visual files: {missing}")

    # Check at least one clip audio moment in intro
    play_count = sum(1 for s in segs if s["clip_audio"] in ("play", "play_then_mute"))
    if play_count >= 1:
        passes.append(f"Intro has {play_count} clip audio moment(s)")
    else:
        failures.append("No clip audio in intro (need at least 1)")

    # Check total duration is reasonable (5-30s)
    dur = intro_data["total_duration"]
    if 5.0 <= dur <= 60.0:
        passes.append(f"Intro duration: {dur:.1f}s")
    else:
        failures.append(f"Intro duration {dur:.1f}s is outside 5-60s range")

    return passes, failures


def main():
    parser = argparse.ArgumentParser(description="Intro Builder")
    parser.add_argument("--spec", type=str, default=str(DEFAULT_SPEC),
                        help="Path to intro spec JSON")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only validate, don't output")
    args = parser.parse_args()

    intro = load_intro(args.spec)

    if intro is None:
        print("ERROR: Could not load intro spec")
        sys.exit(1)

    passes, failures = validate_intro(intro)

    print(f"Intro Builder — {intro['spec_version']}")
    print(f"  Segments: {len(intro['segments'])}")
    print(f"  Total duration: {intro['total_duration']:.1f}s")
    print(f"  VO starts at: {intro['vo_start_offset']:.1f}s")
    print()

    for seg in intro["segments"]:
        status = "OK" if seg["visual_path"] else "MISSING"
        print(f"  [{seg['index']}] {seg['start_sec']:.1f}-{seg['end_sec']:.1f}s  "
              f"{seg['clip_audio']:16s}  {seg['visual_file'][:40]}  [{status}]")

    print()
    for p in passes:
        print(f"  PASS  {p}")
    for f in failures:
        print(f"  FAIL  {f}")

    if failures:
        sys.exit(1)
    else:
        if not args.validate_only:
            # Write resolved intro to temp file for other stages
            output_path = PROJECT_ROOT / "storyboards" / "intro_resolved.json"
            with open(output_path, 'w') as f:
                json.dump(intro, f, indent=2)
            print(f"\n  Written: {output_path}")
        sys.exit(0)


if __name__ == "__main__":
    main()
