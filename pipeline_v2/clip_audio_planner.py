#!/usr/bin/env python3
"""
Clip Audio Planner — punch silence holes into narration where clip audio should play.

Two modes:
  --mode gap (default): Post-production. Takes existing narration.wav and inserts
    silence gaps at clip_audio "play"/"play_then_mute" points using ffmpeg.

  --mode inject-markers: Pre-production. Inserts [CLIP_AUDIO:Ns] markers into the
    enhanced script so the voice generator creates gaps during TTS generation.

Usage (gap mode):
  python -m pipeline_v2.clip_audio_planner \\
    --director storyboards/breaking_law_directed_v5.json \\
    --narration audio/breaking_law/narration.wav \\
    --output audio/breaking_law/narration_gapped.wav

  python -m pipeline_v2.clip_audio_planner \\
    --mode inject-markers \\
    --director storyboards/breaking_law_directed_v5.json \\
    --script scripts/breaking_law_enhanced_v45.txt \\
    --output scripts/breaking_law_enhanced_v45_gapped.txt
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_DIRECTOR = PROJECT_ROOT / "storyboards" / "breaking_law_directed_v5.json"
DEFAULT_NARRATION = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
DEFAULT_OUTPUT = PROJECT_ROOT / "audio" / "breaking_law" / "narration_gapped.wav"
DEFAULT_GAP_PLAN = PROJECT_ROOT / "audio" / "breaking_law" / "gap_plan.json"

DEFAULT_CLIP_AUDIO_DURATION = 3.0  # seconds


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
                expanded["clip_audio"] = beat.get("clip_audio", seg.get("clip_audio"))
                expanded["clip_audio_duration"] = beat.get("clip_audio_duration",
                                                           seg.get("clip_audio_duration"))
                expanded["_timeline_start_sec"] = seg_start + i * beat_duration
                expanded["_timeline_end_sec"] = seg_start + (i + 1) * beat_duration
                expanded["beats"] = None
                segments.append(expanded)
        else:
            segments.append(seg)
    return segments


def find_gap_points(segments):
    """Find all points where clip audio should play.

    Returns list of dicts: {timeline_sec, duration, visual_file, clip_audio}
    sorted by timeline position.
    """
    gaps = []
    for seg in segments:
        clip_audio = seg.get("clip_audio", "")
        if clip_audio in ("play", "play_then_mute"):
            start = seg.get("_timeline_start_sec", 0.0)
            duration = seg.get("clip_audio_duration") or DEFAULT_CLIP_AUDIO_DURATION
            gaps.append({
                "timeline_sec": round(start, 3),
                "duration": round(float(duration), 3),
                "visual_file": seg.get("visual_file", ""),
                "clip_audio": clip_audio,
            })

    # Sort by timeline position and deduplicate overlaps
    gaps.sort(key=lambda g: g["timeline_sec"])

    # Merge overlapping gaps
    merged = []
    for gap in gaps:
        if merged and gap["timeline_sec"] < merged[-1]["timeline_sec"] + merged[-1]["duration"]:
            # Extend previous gap if overlapping
            prev = merged[-1]
            new_end = max(prev["timeline_sec"] + prev["duration"],
                          gap["timeline_sec"] + gap["duration"])
            prev["duration"] = round(new_end - prev["timeline_sec"], 3)
        else:
            merged.append(gap)

    return merged


def get_wav_duration(wav_path):
    """Get WAV duration in seconds."""
    import wave
    with wave.open(str(wav_path), 'r') as wf:
        return wf.getnframes() / wf.getframerate()


def gap_mode(director_path, narration_path, output_path, gap_plan_path):
    """Insert silence gaps into narration.wav at clip audio points using ffmpeg."""
    # Load director
    with open(director_path) as f:
        data = json.load(f)

    segments = flatten_segments(data)
    gaps = find_gap_points(segments)

    if not gaps:
        print("No clip_audio play/play_then_mute moments found. Copying narration as-is.")
        import shutil
        shutil.copy2(str(narration_path), str(output_path))
        return

    original_dur = get_wav_duration(narration_path)
    print(f"Original narration: {original_dur:.1f}s")
    print(f"Found {len(gaps)} gap points")

    # Get narration sample rate
    import wave
    with wave.open(str(narration_path), 'r') as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()

    # Build ffmpeg filter to split and insert silence
    # Strategy: use ffmpeg's -filter_complex with asplit, atrim, apad, and concat
    # For each gap, we trim the narration into segments and insert silence between them

    with tempfile.TemporaryDirectory() as tmpdir:
        # Split narration at each gap point
        pieces = []
        prev_end = 0.0
        cumulative_offset = 0.0

        gap_plan = []

        for i, gap in enumerate(gaps):
            gap_start = gap["timeline_sec"]
            gap_dur = gap["duration"]

            # Narration piece before this gap
            if gap_start > prev_end:
                piece_path = os.path.join(tmpdir, f"piece_{len(pieces):03d}.wav")
                cmd = [
                    "ffmpeg", "-y", "-i", str(narration_path),
                    "-ss", f"{prev_end:.6f}",
                    "-t", f"{gap_start - prev_end:.6f}",
                    "-acodec", "pcm_s16le",
                    piece_path,
                ]
                subprocess.run(cmd, capture_output=True, check=True)
                pieces.append(piece_path)
                cumulative_offset += (gap_start - prev_end)

            # Silence piece for the gap
            silence_path = os.path.join(tmpdir, f"silence_{i:03d}.wav")
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i",
                f"anullsrc=channel_layout={'stereo' if n_channels == 2 else 'mono'}:sample_rate={sample_rate}",
                "-t", f"{gap_dur:.6f}",
                "-acodec", "pcm_s16le",
                silence_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            pieces.append(silence_path)

            gap_plan.append({
                "index": i,
                "original_position_sec": round(gap_start, 3),
                "gapped_position_sec": round(cumulative_offset, 3),
                "duration_sec": round(gap_dur, 3),
                "visual_file": gap["visual_file"],
                "clip_audio": gap["clip_audio"],
            })

            cumulative_offset += gap_dur
            prev_end = gap_start

        # Final piece after last gap
        if prev_end < original_dur:
            piece_path = os.path.join(tmpdir, f"piece_{len(pieces):03d}.wav")
            cmd = [
                "ffmpeg", "-y", "-i", str(narration_path),
                "-ss", f"{prev_end:.6f}",
                "-acodec", "pcm_s16le",
                piece_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            pieces.append(piece_path)

        # Concatenate all pieces
        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, 'w') as f:
            for piece in pieces:
                f.write(f"file '{piece}'\n")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-acodec", "pcm_s16le",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    # Write gap plan
    gapped_dur = get_wav_duration(output_path)
    gap_plan_data = {
        "original_duration_sec": round(original_dur, 3),
        "gapped_duration_sec": round(gapped_dur, 3),
        "gap_count": len(gaps),
        "total_silence_added_sec": round(sum(g["duration"] for g in gaps), 3),
        "gaps": gap_plan,
    }

    gap_plan_path.parent.mkdir(parents=True, exist_ok=True)
    with open(gap_plan_path, 'w') as f:
        json.dump(gap_plan_data, f, indent=2)

    print(f"\nSummary:")
    print(f"  Original duration:  {original_dur:.1f}s")
    print(f"  Gapped duration:    {gapped_dur:.1f}s")
    print(f"  Silence added:      {gapped_dur - original_dur:.1f}s")
    print(f"  Number of gaps:     {len(gaps)}")
    print(f"  Output:             {output_path}")
    print(f"  Gap plan:           {gap_plan_path}")


def inject_markers_mode(director_path, script_path, output_path):
    """Insert [CLIP_AUDIO:Ns] markers into the enhanced script.

    For FUTURE videos -- the voice generator treats these like [PAUSE:N]
    and inserts silence during TTS generation.
    """
    with open(director_path) as f:
        data = json.load(f)

    segments = flatten_segments(data)
    gaps = find_gap_points(segments)

    with open(script_path) as f:
        script_text = f.read()

    if not gaps:
        print("No clip_audio play/play_then_mute moments found. Script unchanged.")
        with open(output_path, 'w') as f:
            f.write(script_text)
        return

    # For each gap, find the corresponding text position in the script
    # Match by finding the segment text near each gap point
    gap_segments = []
    for gap in gaps:
        target_time = gap["timeline_sec"]
        # Find the segment closest to this gap time
        best_seg = None
        best_dist = float('inf')
        for seg in segments:
            start = seg.get("_timeline_start_sec", 0)
            dist = abs(start - target_time)
            if dist < best_dist:
                best_dist = dist
                best_seg = seg
        if best_seg:
            gap_segments.append((gap, best_seg))

    # Insert markers by finding segment text in the script
    # Work backwards to preserve positions
    insertions = []  # (position_in_script, marker_text)

    for gap, seg in gap_segments:
        seg_text = seg.get("text", "").strip()
        if not seg_text or seg_text.startswith("["):
            continue

        # Find this text (first 30 chars) in the script
        search_text = seg_text[:40].strip()
        pos = script_text.find(search_text)
        if pos == -1:
            # Try shorter match
            search_text = seg_text[:20].strip()
            pos = script_text.find(search_text)

        if pos >= 0:
            marker = f"\n[CLIP_AUDIO:{gap['duration']:.0f}s]\n"
            insertions.append((pos, marker))

    # Sort by position descending (insert from end to preserve earlier positions)
    insertions.sort(key=lambda x: x[0], reverse=True)

    modified = script_text
    for pos, marker in insertions:
        modified = modified[:pos] + marker + modified[pos:]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(modified)

    print(f"Inserted {len(insertions)} [CLIP_AUDIO] markers into script")
    print(f"Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Clip Audio Planner - insert silence gaps for clip audio playback")
    parser.add_argument("--mode", choices=["gap", "inject-markers"], default="gap",
                        help="Mode: 'gap' inserts silence into WAV, "
                             "'inject-markers' adds markers to script (default: gap)")
    parser.add_argument("--director", type=str, default=str(DEFAULT_DIRECTOR),
                        help="Path to director JSON")
    parser.add_argument("--narration", type=str, default=str(DEFAULT_NARRATION),
                        help="Path to narration WAV (gap mode)")
    parser.add_argument("--script", type=str, default=None,
                        help="Path to enhanced script (inject-markers mode)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path")
    parser.add_argument("--gap-plan", type=str, default=str(DEFAULT_GAP_PLAN),
                        help="Path for gap_plan.json output (gap mode)")
    args = parser.parse_args()

    director_path = Path(args.director)
    if not director_path.exists():
        print(f"ERROR: Director file not found: {director_path}")
        sys.exit(1)

    if args.mode == "gap":
        narration_path = Path(args.narration)
        if not narration_path.exists():
            print(f"ERROR: Narration file not found: {narration_path}")
            sys.exit(1)

        output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
        gap_plan_path = Path(args.gap_plan)
        gap_mode(director_path, narration_path, output_path, gap_plan_path)

    elif args.mode == "inject-markers":
        if not args.script:
            print("ERROR: --script is required for inject-markers mode")
            sys.exit(1)

        script_path = Path(args.script)
        if not script_path.exists():
            print(f"ERROR: Script file not found: {script_path}")
            sys.exit(1)

        output_path = Path(args.output) if args.output else script_path.with_suffix('.gapped.txt')
        inject_markers_mode(director_path, script_path, output_path)


if __name__ == "__main__":
    main()
