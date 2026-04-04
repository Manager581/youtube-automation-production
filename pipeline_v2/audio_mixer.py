#!/usr/bin/env python3
"""
Mix narration + music into a single stereo WAV per chapter.
Pure Python — no FFmpeg.

Left channel  = narration (upsampled from 24kHz to 48kHz)
Right channel = music (downmixed from stereo to mono, trimmed to chapter length)

DaVinci imports stereo and plays both channels. User can split to separate
tracks in Fairlight if needed.
"""

import os
import struct
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
NARRATION_PATH = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
MUSIC_DIR = PROJECT_ROOT / "audio" / "breaking_law" / "music_tracks"
OUTPUT_DIR = PROJECT_ROOT / "audio" / "breaking_law" / "chapters"


def mix_chapter_audio(chapter_num, narr_start_sec, narr_end_sec, music_filename):
    """Create a stereo WAV: left=narration, right=music.

    Handles sample rate mismatch:
    - Narration: 24kHz mono → upsample to 48kHz
    - Music: 48kHz stereo → downmix to mono

    Returns path to output file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"mixed_ch{chapter_num}.wav"

    if out_path.exists():
        print(f"  Mixed audio already exists: {out_path.name}")
        return str(out_path)

    music_path = MUSIC_DIR / music_filename
    target_rate = 48000

    # ── Read narration segment ──
    with wave.open(str(NARRATION_PATH), 'r') as wf:
        narr_rate = wf.getframerate()  # 24000
        narr_channels = wf.getnchannels()  # 1
        narr_width = wf.getsampwidth()  # 2

        start_sample = int(narr_start_sec * narr_rate)
        end_sample = int(narr_end_sec * narr_rate)
        num_samples = end_sample - start_sample

        wf.setpos(start_sample)
        narr_raw = wf.readframes(num_samples)

    # Convert narration bytes to samples (16-bit signed)
    narr_samples = list(struct.unpack(f'<{num_samples}h', narr_raw))

    # Upsample narration 24kHz → 48kHz (duplicate each sample)
    ratio = target_rate // narr_rate  # 2
    narr_48k = []
    for s in narr_samples:
        for _ in range(ratio):
            narr_48k.append(s)

    chapter_samples = len(narr_48k)
    chapter_duration = chapter_samples / target_rate
    print(f"  Narration: {len(narr_samples)} samples → {chapter_samples} at 48kHz ({chapter_duration:.1f}s)")

    # ── Read music ──
    with wave.open(str(music_path), 'r') as wf:
        music_rate = wf.getframerate()  # 48000
        music_channels = wf.getnchannels()  # 2
        music_width = wf.getsampwidth()  # 2

        # Read enough samples for the chapter duration
        music_frames = min(int(chapter_duration * music_rate), wf.getnframes())
        music_raw = wf.readframes(music_frames)

    # Downmix stereo to mono (average L+R)
    total_stereo_samples = len(music_raw) // (music_width * music_channels)
    stereo = struct.unpack(f'<{total_stereo_samples * music_channels}h', music_raw)
    music_mono = []
    for i in range(0, len(stereo), 2):
        left = stereo[i]
        right = stereo[i + 1] if i + 1 < len(stereo) else stereo[i]
        music_mono.append((left + right) // 2)

    print(f"  Music: {total_stereo_samples} stereo frames → {len(music_mono)} mono samples")

    # ── Pad music to match narration length (or trim) ──
    if len(music_mono) < chapter_samples:
        # Loop music to fill
        loops = (chapter_samples // len(music_mono)) + 1
        music_mono = (music_mono * loops)[:chapter_samples]
    else:
        music_mono = music_mono[:chapter_samples]

    # ── Write stereo output: left=narration, right=music ──
    with wave.open(str(out_path), 'w') as wf:
        wf.setnchannels(2)  # stereo
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(target_rate)

        # Interleave L/R samples
        chunk_size = 10000  # process in chunks to save memory
        for i in range(0, chapter_samples, chunk_size):
            end = min(i + chunk_size, chapter_samples)
            chunk_data = b''
            for j in range(i, end):
                left = narr_48k[j]
                right = music_mono[j] if j < len(music_mono) else 0
                # Clamp to 16-bit range
                left = max(-32768, min(32767, left))
                right = max(-32768, min(32767, right))
                chunk_data += struct.pack('<hh', left, right)
            wf.writeframes(chunk_data)

    size_mb = os.path.getsize(out_path) / 1e6
    print(f"  Output: {out_path.name} ({size_mb:.1f} MB, {chapter_duration:.1f}s stereo 48kHz)")
    return str(out_path)


if __name__ == "__main__":
    # Test with chapter 0
    mix_chapter_audio(0, 0.0, 36.9, "track_01_tense_ducked.wav")
