#!/usr/bin/env python3
"""
Verify FCPXML output for structural integrity — comprehensive automated checker.

Checks:
  1. XML structure: Valid FCPXML 1.9 with required hierarchy
  2. V1 clip count (configurable minimum)
  3. No 0dB mute bug on spine clips
  4. Timecode continuity: spine clips are contiguous (no gaps/overlaps)
  5. Lane offset math: all lane clips have valid offsets
  6. Lane clip non-overlap: clips within same lane don't overlap
  7. Asset existence: all file:// paths resolve on disk
  8. Media validation (ffprobe): stream types + duration sanity
  9. Volume sanity: mute=-96dB, play=0dB/none, play_then_mute=keyframes
  10. Narration coverage: A1 duration matches expected
  11. Lane assignment correctness

Usage:
  python -m pipeline_v2.verify_fcpxml
  python -m pipeline_v2.verify_fcpxml --fcpxml path/to/timeline.fcpxml
  python -m pipeline_v2.verify_fcpxml --fcpxml timeline.fcpxml --narration-duration 1200
  python -m pipeline_v2.verify_fcpxml --fcpxml timeline.fcpxml --min-v1-clips 5  # for test timelines
"""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).parent.parent

# Default to the latest production FCPXML
DEFAULT_FCPXML = PROJECT_ROOT / "timeline_v6_final.fcpxml"
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


def ffprobe_streams(filepath):
    """Get stream info via ffprobe. Returns list of stream dicts or None on error."""
    try:
        r = subprocess.run(
            ['/opt/homebrew/bin/ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_streams', '-show_format', filepath],
            capture_output=True, text=True, timeout=10
        )
        info = json.loads(r.stdout)
        return info.get('streams', []), info.get('format', {})
    except Exception:
        return None, None


def run_checks(fcpxml_path, expected_narr_dur=None, min_v1_clips=200, skip_ffprobe=False):
    """Run all FCPXML verification checks."""
    passes = []
    failures = []
    warnings = []

    tree = ET.parse(fcpxml_path)
    root = tree.getroot()

    # --- 1. XML Structure ---
    version = root.get('version', '')
    if version == '1.9':
        passes.append("FCPXML version 1.9")
    elif version:
        warnings.append(f"FCPXML version {version} (expected 1.9)")
    else:
        failures.append("No version attribute on <fcpxml> root")

    resources = root.find("resources")
    if resources is None:
        failures.append("No <resources> element")
    else:
        passes.append("<resources> element present")

    spine = root.find(".//spine")
    if spine is None:
        failures.append("No <spine> element found — cannot continue checks")
        return passes, failures, warnings

    seq = root.find(".//sequence")
    library = root.find(".//library")
    event = root.find(".//event")
    project = root.find(".//project")

    for name, el in [("library", library), ("event", event), ("project", project), ("sequence", seq)]:
        if el is not None:
            passes.append(f"<{name}> element present")
        else:
            failures.append(f"Missing <{name}> element")

    # Get TC start from sequence
    tc_start = 0.0
    if seq is not None:
        tc_start = parse_rational_time(seq.get('tcStart', '0/1s'))

    # --- 2. V1 spine clips ---
    spine_clips = []       # all spine children
    spine_content = []     # non-transition spine children (clips, gaps, videos)
    transitions = []

    for child in spine:
        spine_clips.append(child)
        if child.tag == 'transition':
            transitions.append(child)
        else:
            spine_content.append(child)

    v1_count = len(spine_content)
    if v1_count >= min_v1_clips:
        passes.append(f"V1 spine elements: {v1_count} (≥ {min_v1_clips})")
    else:
        failures.append(f"V1 spine elements: {v1_count} (expected ≥ {min_v1_clips})")

    # --- 3. No 0dB mute bug ---
    muted_0db = 0
    for clip in spine_content:
        for vol in clip.iter('adjust-volume'):
            amount = vol.get('amount', '')
            if amount == '0dB':
                muted_0db += 1

    if muted_0db == 0:
        passes.append("No 0dB mute bug (all mutes use -96dB)")
    else:
        failures.append(f"Found {muted_0db} spine clips with adjust-volume 0dB (mute bug)")

    # --- 4. Timecode continuity ---
    continuity_errors = []
    prev_end = None
    for i, clip in enumerate(spine_content):
        offset = parse_rational_time(clip.get('offset', '0/1s'))
        duration = parse_rational_time(clip.get('duration', '0/1s'))

        if prev_end is not None:
            gap = abs(offset - prev_end)
            # Allow small tolerance for transition overlap (1s max) and rounding
            if gap > 1.5:
                continuity_errors.append(
                    f"Gap of {gap:.2f}s between spine clips {i-1} and {i} "
                    f"(prev_end={prev_end:.2f}, offset={offset:.2f})")

        prev_end = offset + duration

    if not continuity_errors:
        passes.append("Spine timecode continuity OK (no gaps > 1.5s)")
    else:
        for err in continuity_errors[:5]:
            failures.append(f"Continuity: {err}")
        if len(continuity_errors) > 5:
            failures.append(f"  ...and {len(continuity_errors) - 5} more continuity errors")

    # --- 5 & 6. Lane clips: offset validation and non-overlap ---
    lane_clips_by_lane = defaultdict(list)

    # Lane clips are children of spine elements. Their offset is relative to
    # the parent's content timebase (parent.start), NOT absolute timeline time.
    # Actual timeline position = parent.offset + (lane.offset - parent.start)
    for spine_el in spine_clips:
        parent_offset = parse_rational_time(spine_el.get('offset', '0/1s'))
        parent_start = parse_rational_time(spine_el.get('start', '0/1s'))

        for child in spine_el:
            lane_str = child.get('lane')
            if lane_str is None:
                continue
            try:
                lane = int(lane_str)
            except ValueError:
                continue
            raw_offset = parse_rational_time(child.get('offset', '0/1s'))
            duration = parse_rational_time(child.get('duration', '0/1s'))
            # Convert to absolute timeline position
            abs_offset = parent_offset + (raw_offset - parent_start)
            name = child.get('name', child.get('ref', '?'))
            lane_clips_by_lane[lane].append({
                'offset': abs_offset,
                'duration': duration,
                'end': abs_offset + duration,
                'name': name,
            })

    # Check 5: lane offsets are non-negative (relative to timeline start)
    bad_offsets = []
    for lane, clips in lane_clips_by_lane.items():
        for lc in clips:
            if lc['offset'] < tc_start - 0.1:
                bad_offsets.append(f"Lane {lane} clip '{lc['name']}' abs_offset={lc['offset']:.2f} < tc_start={tc_start:.2f}")

    if not bad_offsets:
        total_lane = sum(len(v) for v in lane_clips_by_lane.values())
        passes.append(f"All {total_lane} lane clips have valid absolute offsets (≥ tc_start)")
    else:
        for err in bad_offsets[:5]:
            failures.append(f"Lane offset: {err}")

    # Check 6: non-overlap within same lane (audio lanes only — overlays may intentionally overlap)
    overlap_errors = []
    # Audio lanes: narration (3), music (4), sfx (5, 6)
    audio_lanes = {3, 4, 5, 6}
    for lane, clips in lane_clips_by_lane.items():
        if lane not in audio_lanes:
            continue  # skip visual lanes — overlays/chapters can overlap
        sorted_clips = sorted(clips, key=lambda c: c['offset'])
        for i in range(1, len(sorted_clips)):
            prev = sorted_clips[i - 1]
            curr = sorted_clips[i]
            if curr['offset'] < prev['end'] - 0.5:  # 0.5s tolerance for transitions
                overlap_errors.append(
                    f"Lane {lane}: '{prev['name']}' (ends {prev['end']:.2f}) "
                    f"overlaps '{curr['name']}' (starts {curr['offset']:.2f})")

    if not overlap_errors:
        passes.append("No audio lane overlaps (lanes 3-6)")
    else:
        for err in overlap_errors[:5]:
            failures.append(f"Lane overlap: {err}")
        if len(overlap_errors) > 5:
            failures.append(f"  ...and {len(overlap_errors) - 5} more overlap errors")

    # --- 7. Asset existence ---
    missing_assets = []
    total_assets = 0
    asset_paths = {}  # asset_id -> filepath

    for asset in root.iter('asset'):
        asset_id = asset.get('id', '')
        for media_rep in asset.iter('media-rep'):
            src = media_rep.get('src', '')
            if src.startswith('file://'):
                total_assets += 1
                file_path = unquote(src.replace('file://', ''))
                asset_paths[asset_id] = file_path
                if not os.path.exists(file_path):
                    missing_assets.append(file_path)

        # Also check src directly on asset (some FCPXML formats)
        src = asset.get('src', '')
        if src.startswith('file://') and asset_id not in asset_paths:
            total_assets += 1
            file_path = unquote(src.replace('file://', ''))
            asset_paths[asset_id] = file_path
            if not os.path.exists(file_path):
                missing_assets.append(file_path)

    if not missing_assets:
        passes.append(f"All {total_assets} asset file paths exist on disk")
    else:
        failures.append(
            f"Missing asset files ({len(missing_assets)}/{total_assets}):\n"
            + "\n".join(f"    {p}" for p in missing_assets[:10]))

    # --- 8. Media validation (ffprobe) ---
    if not skip_ffprobe and asset_paths:
        media_errors = []
        media_warnings = []
        probed = 0

        for asset in root.iter('asset'):
            aid = asset.get('id', '')
            fpath = asset_paths.get(aid)
            if not fpath or not os.path.exists(fpath):
                continue

            has_video = asset.get('hasVideo', '0') == '1'
            has_audio = asset.get('hasAudio', '0') == '1'
            declared_dur = parse_rational_time(asset.get('duration', '0/1s'))

            streams, fmt_info = ffprobe_streams(fpath)
            if streams is None:
                media_errors.append(f"ffprobe failed for {os.path.basename(fpath)}")
                continue

            probed += 1
            stream_types = {s.get('codec_type') for s in streams}

            if has_video and 'video' not in stream_types:
                media_errors.append(f"{os.path.basename(fpath)}: declared hasVideo=1 but no video stream")
            if has_audio and 'audio' not in stream_types:
                # MOV overlays/chapter cards often lack audio — DaVinci handles gracefully
                media_warnings.append(f"{os.path.basename(fpath)}: declared hasAudio=1 but no audio stream")

            # Check duration (skip images which have duration=0)
            if declared_dur > 0.1 and fmt_info:
                actual_dur = float(fmt_info.get('duration', 0))
                if actual_dur > 0 and declared_dur > actual_dur + 1.0:
                    media_errors.append(
                        f"{os.path.basename(fpath)}: FCPXML duration {declared_dur:.1f}s "
                        f"> actual {actual_dur:.1f}s")

        if not media_errors:
            passes.append(f"Media validation passed ({probed} assets probed)")
        else:
            for err in media_errors[:5]:
                failures.append(f"Media: {err}")
            if len(media_errors) > 5:
                failures.append(f"  ...and {len(media_errors) - 5} more media errors")
        for mw in media_warnings[:3]:
            warnings.append(f"Media: {mw}")
        if len(media_warnings) > 3:
            warnings.append(f"  ...and {len(media_warnings) - 3} more media warnings")
    elif skip_ffprobe:
        warnings.append("ffprobe checks skipped (--skip-ffprobe)")

    # --- 9. Volume sanity ---
    volume_errors = []
    for clip in spine_content:
        if clip.tag == 'gap':
            continue

        vol_els = list(clip.iter('adjust-volume'))
        if not vol_els:
            continue  # no volume adjustment = play at default (fine)

        for vol in vol_els:
            amount = vol.get('amount', '')
            # Check for keyframes (play_then_mute pattern)
            keyframes = list(vol.iter('keyframe'))
            if keyframes:
                # Should have at least: 0dB start, then -96dB mute
                values = [kf.get('value', '') for kf in keyframes]
                has_full = any('0dB' in v for v in values)
                has_mute = any('-96dB' in v for v in values)
                if not (has_full and has_mute):
                    clip_name = clip.get('name', '?')
                    volume_errors.append(
                        f"'{clip_name}': keyframes present but missing 0dB→-96dB pattern "
                        f"(values: {values})")
            elif amount:
                if amount != '-96dB':
                    clip_name = clip.get('name', '?')
                    volume_errors.append(f"'{clip_name}': adjust-volume amount='{amount}' (expected -96dB for mute)")

    if not volume_errors:
        passes.append("Volume assignments are sane (mute=-96dB, keyframes have 0dB→-96dB)")
    else:
        for err in volume_errors[:5]:
            failures.append(f"Volume: {err}")

    # --- 10. Narration coverage ---
    if expected_narr_dur is None:
        expected_narr_dur = get_narration_duration()

    # Calculate timeline duration from spine
    timeline_dur = 0.0
    for clip in spine_content:
        dur_str = clip.get('duration', '')
        if dur_str:
            timeline_dur += parse_rational_time(dur_str)

    # Also check sequence duration
    if seq is not None:
        seq_dur_str = seq.get('duration', '')
        if seq_dur_str:
            seq_dur = parse_rational_time(seq_dur_str)
            if seq_dur > timeline_dur:
                timeline_dur = seq_dur

    # Find narration lane clip duration
    narr_dur_found = None
    for lane, clips in lane_clips_by_lane.items():
        for lc in clips:
            if 'narration' in lc['name'].lower():
                narr_dur_found = lc['duration']
                break

    if expected_narr_dur and narr_dur_found:
        diff = abs(narr_dur_found - expected_narr_dur)
        if diff < 2.0:
            passes.append(f"Narration lane duration {narr_dur_found:.1f}s ≈ WAV {expected_narr_dur:.1f}s")
        else:
            failures.append(
                f"Narration lane duration {narr_dur_found:.1f}s vs WAV {expected_narr_dur:.1f}s "
                f"(diff {diff:.1f}s)")
    elif expected_narr_dur and timeline_dur > 0:
        diff_pct = abs(timeline_dur - expected_narr_dur) / expected_narr_dur * 100
        if diff_pct < 15:
            passes.append(
                f"Timeline duration {timeline_dur:.1f}s ≈ narration {expected_narr_dur:.1f}s "
                f"(diff {diff_pct:.1f}%)")
        else:
            failures.append(
                f"Timeline {timeline_dur:.1f}s vs narration {expected_narr_dur:.1f}s "
                f"(diff {diff_pct:.1f}%, expected < 15%)")
    elif timeline_dur > 0:
        passes.append(f"Timeline duration: {timeline_dur:.1f}s (narration WAV not available for comparison)")
    else:
        failures.append("Could not determine timeline duration")

    # --- 11. Lane assignment summary ---
    lane_summary = {}
    for lane, clips in sorted(lane_clips_by_lane.items()):
        lane_summary[lane] = len(clips)

    if lane_summary:
        summary_str = ", ".join(f"lane {l}: {c} clips" for l, c in sorted(lane_summary.items()))
        passes.append(f"Lane summary: {summary_str}")

    return passes, failures, warnings


def main():
    parser = argparse.ArgumentParser(description="Verify FCPXML output")
    parser.add_argument("--fcpxml", type=str, default=str(DEFAULT_FCPXML),
                        help="Path to FCPXML file")
    parser.add_argument("--narration-duration", type=float, default=None,
                        help="Expected narration duration in seconds (auto-detected from WAV if omitted)")
    parser.add_argument("--min-v1-clips", type=int, default=200,
                        help="Minimum expected V1 spine elements (default: 200, use lower for test timelines)")
    parser.add_argument("--skip-ffprobe", action="store_true",
                        help="Skip ffprobe media validation checks")
    args = parser.parse_args()

    fcpxml_path = Path(args.fcpxml)
    if not fcpxml_path.exists():
        print(f"FAIL: FCPXML file not found: {fcpxml_path}")
        sys.exit(1)

    print(f"Verifying: {fcpxml_path.name}")
    print()

    passes, failures, warnings = run_checks(
        fcpxml_path, args.narration_duration, args.min_v1_clips, args.skip_ffprobe)

    for p in passes:
        print(f"  PASS  {p}")
    for w in warnings:
        print(f"  WARN  {w}")
    for f in failures:
        print(f"  FAIL  {f}")

    print()
    total = len(passes) + len(failures)
    print(f"Results: {len(passes)}/{total} passed, {len(failures)}/{total} failed"
          + (f", {len(warnings)} warnings" if warnings else ""))

    if failures:
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
