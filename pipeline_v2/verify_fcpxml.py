#!/usr/bin/env python3
"""
Verify FCPXML output for structural integrity.

Checks:
  - V1 clip count > 200
  - No adjust-volume amount="0dB" on spine clips (old mute bug)
  - Narration starts at approximately 0s
  - All <asset> src file:// paths exist on disk
  - Timeline duration approximately matches narration duration

Usage:
  python -m pipeline_v2.verify_fcpxml
  python -m pipeline_v2.verify_fcpxml --fcpxml path/to/timeline.fcpxml
  python -m pipeline_v2.verify_fcpxml --fcpxml timeline.fcpxml --narration-duration 1200
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).parent.parent

# Default to the latest production FCPXML
DEFAULT_FCPXML = PROJECT_ROOT / "timeline_breaking_law_v5.fcpxml"
NARRATION_PATH = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"


def parse_rational_time(time_str):
    """Parse FCPXML rational time like '1234/24s' to seconds."""
    if not time_str:
        return 0.0
    time_str = time_str.rstrip('s')
    if '/' in time_str:
        num, den = time_str.split('/')
        return float(num) / float(den)
    return float(time_str)


def get_narration_duration():
    """Get narration WAV duration in seconds using wave module."""
    import wave
    if not NARRATION_PATH.exists():
        return None
    try:
        with wave.open(str(NARRATION_PATH), 'r') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / rate
    except Exception:
        return None


def run_checks(fcpxml_path, expected_narr_dur=None):
    """Run all FCPXML verification checks."""
    passes = []
    failures = []

    tree = ET.parse(fcpxml_path)
    root = tree.getroot()

    # Collect all elements for analysis
    # In FCPXML, the spine is inside <sequence> -> <spine>
    spine = root.find(".//spine")
    if spine is None:
        failures.append("No <spine> element found in FCPXML")
        return passes, failures

    # --- 1. Count V1 clips (direct children of spine) ---
    # V1 clips are <video>, <clip>, <asset-clip> elements directly in the spine
    v1_clips = []
    for child in spine:
        tag = child.tag
        if tag in ('video', 'clip', 'asset-clip', 'ref-clip', 'gap'):
            v1_clips.append(child)

    v1_count = len(v1_clips)
    if v1_count > 200:
        passes.append(f"V1 clip count: {v1_count} (> 200)")
    else:
        failures.append(f"V1 clip count: {v1_count} (expected > 200)")

    # --- 2. No adjust-volume amount="0dB" on spine clips (old mute bug) ---
    muted_spine_clips = 0
    for clip in v1_clips:
        for vol in clip.iter('adjust-volume'):
            amount = vol.get('amount', '')
            if amount == '0dB':
                muted_spine_clips += 1

    if muted_spine_clips == 0:
        passes.append("No spine clips with adjust-volume 0dB (mute bug absent)")
    else:
        failures.append(f"Found {muted_spine_clips} spine clips with adjust-volume 0dB (mute bug)")

    # --- 3. Narration starts at approximately 0s ---
    # Look for the narration audio clip (typically named narration*.wav)
    narr_offset = None
    for elem in root.iter():
        name = elem.get('name', '')
        if 'narration' in name.lower() and elem.tag in ('asset-clip', 'clip', 'audio'):
            offset_str = elem.get('offset', '0/1s')
            narr_offset = parse_rational_time(offset_str)
            break

    # Also check spine children for narration
    if narr_offset is None:
        for clip in spine:
            ref = clip.get('ref', '')
            # Look up in assets
            for asset in root.iter('asset'):
                if asset.get('id') == ref:
                    aname = asset.get('name', '')
                    if 'narration' in aname.lower():
                        narr_offset = parse_rational_time(clip.get('offset', '0/1s'))
                        break

    if narr_offset is not None:
        if abs(narr_offset) < 2.0:
            passes.append(f"Narration starts at {narr_offset:.2f}s (approx 0s)")
        else:
            failures.append(f"Narration starts at {narr_offset:.2f}s (expected ~0s)")
    else:
        # Narration may be on a separate audio lane; check the first spine clip offset
        if v1_clips:
            first_offset = parse_rational_time(v1_clips[0].get('offset', '0/1s'))
            if abs(first_offset) < 2.0:
                passes.append(f"First spine clip starts at {first_offset:.2f}s (narration element not found by name)")
            else:
                failures.append(f"First spine clip starts at {first_offset:.2f}s, narration element not found")
        else:
            failures.append("Could not locate narration element in FCPXML")

    # --- 4. All <asset> src file:// paths exist on disk ---
    missing_assets = []
    total_assets = 0
    for asset in root.iter('asset'):
        for media_rep in asset.iter('media-rep'):
            src = media_rep.get('src', '')
            if src.startswith('file://'):
                total_assets += 1
                file_path = unquote(src.replace('file://', ''))
                if not os.path.exists(file_path):
                    missing_assets.append(file_path)

    if not missing_assets:
        passes.append(f"All {total_assets} asset file paths exist on disk")
    else:
        failures.append(
            f"Missing asset files ({len(missing_assets)}/{total_assets}):\n"
            + "\n".join(f"  {p}" for p in missing_assets[:10]))

    # --- 5. Timeline duration approximately matches narration duration ---
    # Calculate timeline duration from spine clips
    timeline_dur = 0.0
    for clip in v1_clips:
        dur_str = clip.get('duration', '')
        if dur_str:
            timeline_dur += parse_rational_time(dur_str)
        else:
            # If no duration, check offset of next clip
            offset = parse_rational_time(clip.get('offset', '0/1s'))
            if offset > timeline_dur:
                timeline_dur = offset

    # Also check the <sequence> duration attribute
    seq = root.find(".//sequence")
    if seq is not None:
        seq_dur_str = seq.get('duration', '')
        if seq_dur_str:
            seq_dur = parse_rational_time(seq_dur_str)
            if seq_dur > timeline_dur:
                timeline_dur = seq_dur

    if expected_narr_dur is None:
        expected_narr_dur = get_narration_duration()

    if expected_narr_dur and timeline_dur > 0:
        diff_pct = abs(timeline_dur - expected_narr_dur) / expected_narr_dur * 100
        if diff_pct < 15:
            passes.append(
                f"Timeline duration {timeline_dur:.1f}s ~ narration {expected_narr_dur:.1f}s "
                f"(diff {diff_pct:.1f}%)")
        else:
            failures.append(
                f"Timeline duration {timeline_dur:.1f}s vs narration {expected_narr_dur:.1f}s "
                f"(diff {diff_pct:.1f}%, expected < 15%)")
    elif timeline_dur > 0:
        passes.append(f"Timeline duration: {timeline_dur:.1f}s (narration duration unavailable for comparison)")
    else:
        failures.append("Could not determine timeline duration")

    return passes, failures


def main():
    parser = argparse.ArgumentParser(description="Verify FCPXML output")
    parser.add_argument("--fcpxml", type=str, default=str(DEFAULT_FCPXML),
                        help="Path to FCPXML file")
    parser.add_argument("--narration-duration", type=float, default=None,
                        help="Expected narration duration in seconds (auto-detected from WAV if omitted)")
    args = parser.parse_args()

    fcpxml_path = Path(args.fcpxml)
    if not fcpxml_path.exists():
        print(f"FAIL: FCPXML file not found: {fcpxml_path}")
        sys.exit(1)

    print(f"Verifying: {fcpxml_path.name}")
    print()

    passes, failures = run_checks(fcpxml_path, args.narration_duration)

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
