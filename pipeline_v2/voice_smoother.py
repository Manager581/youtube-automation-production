#!/usr/bin/env python3
"""
Voice Smoother — post-process existing narration WAV to fix robotic splits.

Reads the voice manifest (chunk boundaries) and applies short crossfades
at each speech-to-speech transition. Does NOT require regeneration.

Strategy:
  1. Read manifest to find chunk boundaries
  2. At each boundary, extract a small window around the boundary
  3. Apply a short crossfade (fade-out + fade-in overlap) using ffmpeg
  4. Reconstruct the smoothed WAV

Usage:
  python -m pipeline_v2.voice_smoother
  python -m pipeline_v2.voice_smoother --narration audio/breaking_law/narration.wav
  python -m pipeline_v2.voice_smoother --manifest audio/breaking_law/narration_manifest.json
  python -m pipeline_v2.voice_smoother --fade-duration 0.08
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_NARRATION = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
DEFAULT_MANIFEST = PROJECT_ROOT / "audio" / "breaking_law" / "narration_manifest.json"
DEFAULT_FADE = 0.08  # 80ms


def get_wav_info(wav_path):
    """Get WAV sample rate, channels, sample width."""
    with wave.open(str(wav_path), 'r') as wf:
        return {
            'sample_rate': wf.getframerate(),
            'channels': wf.getnchannels(),
            'sample_width': wf.getsampwidth(),
            'duration': wf.getnframes() / wf.getframerate(),
            'frames': wf.getnframes(),
        }


def find_boundaries(manifest):
    """Find chunk boundaries from manifest — transitions between consecutive speech segments."""
    boundaries = []
    segments = manifest.get("segments", [])
    prev_speech = None

    for seg in segments:
        if seg["type"] == "speech":
            if prev_speech is not None:
                # Boundary at end of previous speech / start of current
                boundary_sec = seg["start_sec"]
                boundaries.append(boundary_sec)
            prev_speech = seg

    return boundaries


def smooth_boundaries(narration_path, boundaries, fade_duration, output_path):
    """Apply fade-out/fade-in at each boundary point."""
    info = get_wav_info(narration_path)
    total_dur = info['duration']

    if not boundaries:
        print("  No boundaries found — copying as-is")
        import shutil
        shutil.copy2(str(narration_path), str(output_path))
        return

    print(f"  Found {len(boundaries)} chunk boundaries")
    print(f"  Applying {fade_duration*1000:.0f}ms fade at each boundary")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Strategy: split at each boundary, apply fade-out to end of each piece
        # and fade-in to start of next piece, then hard-concat (no overlap).
        # This softens the abrupt transitions without changing duration.
        half_fade = fade_duration / 2
        pieces = []
        prev_end = 0.0

        for i, boundary in enumerate(boundaries):
            piece_start = prev_end
            piece_end = boundary
            piece_dur = piece_end - piece_start

            if piece_dur < 0.02:
                continue

            piece_path = os.path.join(tmpdir, f"piece_{i:04d}.wav")
            # Apply fade-in at start (if not first piece) and fade-out at end
            af_parts = []
            if i > 0:
                af_parts.append(f'afade=t=in:d={half_fade:.6f}')
            af_parts.append(f'afade=t=out:st={max(0, piece_dur - half_fade):.6f}:d={half_fade:.6f}')
            af_filter = ','.join(af_parts)

            cmd = [
                'ffmpeg', '-y', '-i', str(narration_path),
                '-ss', f'{piece_start:.6f}',
                '-t', f'{piece_dur:.6f}',
                '-af', af_filter,
                '-acodec', 'pcm_s16le',
                piece_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            pieces.append(piece_path)
            prev_end = boundary

        # Final piece
        if prev_end < total_dur:
            piece_path = os.path.join(tmpdir, f"piece_{len(pieces):04d}.wav")
            piece_dur = total_dur - prev_end
            cmd = [
                'ffmpeg', '-y', '-i', str(narration_path),
                '-ss', f'{prev_end:.6f}',
                '-af', f'afade=t=in:d={half_fade:.6f}',
                '-acodec', 'pcm_s16le',
                piece_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            pieces.append(piece_path)

        if len(pieces) < 2:
            import shutil
            shutil.copy2(str(narration_path), str(output_path))
            return

        # Hard concat (no overlap — duration preserved)
        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, 'w') as f:
            for piece in pieces:
                f.write(f"file '{piece}'\n")

        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list,
            '-acodec', 'pcm_s16le',
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    smoothed_info = get_wav_info(output_path)
    dur_diff = abs(smoothed_info['duration'] - info['duration'])
    print(f"  Original: {info['duration']:.1f}s")
    print(f"  Smoothed: {smoothed_info['duration']:.1f}s (diff: {dur_diff:.2f}s)")


def main():
    parser = argparse.ArgumentParser(description="Post-process narration WAV to smooth robotic splits")
    parser.add_argument("--narration", type=str, default=str(DEFAULT_NARRATION))
    parser.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", type=str, default=None,
                        help="Output path (default: narration_smoothed.wav)")
    parser.add_argument("--fade-duration", type=float, default=DEFAULT_FADE,
                        help=f"Fade duration in seconds at each boundary (default: {DEFAULT_FADE})")
    args = parser.parse_args()

    narration_path = Path(args.narration)
    manifest_path = Path(args.manifest)

    if not narration_path.exists():
        print(f"ERROR: Narration not found: {narration_path}")
        sys.exit(1)
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else narration_path.with_name(
        narration_path.stem + "_smoothed.wav")

    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"Voice Smoother")
    print(f"  Input: {narration_path.name}")
    print(f"  Manifest: {manifest_path.name}")
    print(f"  Fade: {args.fade_duration * 1000:.0f}ms")

    boundaries = find_boundaries(manifest)
    smooth_boundaries(narration_path, boundaries, args.fade_duration, output_path)
    print(f"\n  Output: {output_path}")


if __name__ == "__main__":
    main()
