#!/usr/bin/env python3
"""
Fern Audio Analysis — Demucs Source Separation + Full Timeline

For each downloaded Fern video:
  1. Extract raw audio (ffmpeg)
  2. Separate into: vocals, music (drums+bass+other) using Demucs htdemucs
  3. Analyze each track:
     - Vocals: energy per second, pause detection, emphasis peaks
     - Music:  energy per second, BPM, build/drop detection
     - SFX:    transient detection on residual (total - vocals - music)
  4. Fuse with VTT word timeline → master per-second timeline
  5. Save to analysis/fern/<video_id>_audio_full.json

Usage:
    python analyze_fern_audio_demucs.py
    python analyze_fern_audio_demucs.py --video wkVygetgeRY
"""

import subprocess
import json
import re
import sys
import os
import time
import argparse
import numpy as np
from pathlib import Path


FERN_DIR = Path("analysis/fern")
AUDIO_CACHE = FERN_DIR / "audio_cache"
DEMUCS_OUT = FERN_DIR / "demucs_out"


# ============================================================================
# AUDIO EXTRACTION
# ============================================================================

def extract_audio(video_path: Path, out_path: Path):
    """Extract full audio from video as WAV (mono, 44100hz)"""
    if out_path.exists():
        print(f"    Audio already extracted: {out_path.name}")
        return True

    print(f"    Extracting audio...")
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-ac', '1',           # mono
        '-ar', '44100',       # 44.1kHz
        '-vn',                # no video
        '-y', str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    if result.returncode != 0:
        print(f"    ❌ ffmpeg failed: {result.stderr.decode()[:200]}")
        return False
    print(f"    ✓ Audio extracted ({out_path.stat().st_size // 1024 // 1024}MB)")
    return True


# ============================================================================
# DEMUCS SEPARATION
# ============================================================================

def separate_audio(video_id: str, audio_path: Path) -> dict:
    """
    Run Demucs htdemucs to separate vocals + drums + bass + other.
    Returns paths to each stem.
    """
    out_dir = DEMUCS_OUT / video_id
    vocals_path = out_dir / "htdemucs" / audio_path.stem / "vocals.wav"
    drums_path  = out_dir / "htdemucs" / audio_path.stem / "drums.wav"
    bass_path   = out_dir / "htdemucs" / audio_path.stem / "bass.wav"
    other_path  = out_dir / "htdemucs" / audio_path.stem / "other.wav"

    if vocals_path.exists():
        print(f"    Demucs already done, loading stems...")
    else:
        print(f"    Running Demucs separation (this takes a few minutes)...")
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, '-m', 'demucs',
            '--two-stems', 'vocals',   # fast mode: vocals vs everything else
            '-o', str(out_dir),
            str(audio_path)
        ]
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, timeout=1800)
        elapsed = time.time() - start

        if result.returncode != 0:
            print(f"    ❌ Demucs failed: {result.stderr.decode()[-500:]}")
            # Try without --two-stems if it failed
            return {}

        print(f"    ✓ Demucs done in {elapsed:.0f}s")

    # With --two-stems vocals, we get: vocals.wav + no_vocals.wav
    no_vocals_path = out_dir / "htdemucs" / audio_path.stem / "no_vocals.wav"

    stems = {}
    for name, path in [('vocals', vocals_path), ('music', no_vocals_path)]:
        if path.exists():
            stems[name] = path
        else:
            print(f"    ⚠ Missing stem: {name} at {path}")

    return stems


# ============================================================================
# AUDIO ANALYSIS
# ============================================================================

def load_audio_numpy(path: Path, sr: int = 22050):
    """Load audio file as numpy array using ffmpeg (no librosa needed)"""
    cmd = [
        'ffmpeg', '-i', str(path),
        '-f', 'f32le',     # raw 32-bit float
        '-ac', '1',        # mono
        '-ar', str(sr),    # sample rate
        '-'
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    audio = np.frombuffer(result.stdout, dtype=np.float32)
    return audio, sr


def energy_timeline(audio: np.ndarray, sr: int, window_sec: float = 1.0) -> list:
    """Compute RMS energy per second"""
    window = int(window_sec * sr)
    timeline = []
    for i in range(0, len(audio), window):
        chunk = audio[i:i + window]
        if len(chunk) == 0:
            break
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        timestamp = i / sr
        timeline.append({'timestamp': round(timestamp, 2), 'energy': round(rms, 4)})
    return timeline


def detect_pauses(vocals: np.ndarray, sr: int, threshold: float = 0.01, min_pause_sec: float = 0.3) -> list:
    """Detect silence/pause gaps in vocal track"""
    window = int(0.05 * sr)  # 50ms windows
    pauses = []
    in_pause = False
    pause_start = 0

    for i in range(0, len(vocals) - window, window):
        chunk = vocals[i:i + window]
        rms = np.sqrt(np.mean(chunk ** 2))
        t = i / sr

        if rms < threshold and not in_pause:
            in_pause = True
            pause_start = t
        elif rms >= threshold and in_pause:
            in_pause = False
            duration = t - pause_start
            if duration >= min_pause_sec:
                pauses.append({
                    'start': round(pause_start, 2),
                    'end': round(t, 2),
                    'duration': round(duration, 2)
                })

    return pauses


def detect_emphasis_peaks(vocals: np.ndarray, sr: int, top_n: int = 50) -> list:
    """Find moments of vocal emphasis (loud peaks = narrator emphasis)"""
    window = int(0.5 * sr)  # 500ms windows
    energies = []

    for i in range(0, len(vocals) - window, window):
        chunk = vocals[i:i + window]
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        energies.append((i / sr, rms))

    if not energies:
        return []

    # Normalize and find peaks above 75th percentile
    values = [e[1] for e in energies]
    threshold = np.percentile(values, 75)
    peaks = [
        {'timestamp': round(t, 2), 'energy': round(e, 4)}
        for t, e in energies if e > threshold
    ]
    return peaks[:top_n]


def detect_music_builds_drops(music: np.ndarray, sr: int) -> list:
    """Detect where music builds up or drops (key for emotional pacing)"""
    window = int(1.0 * sr)
    energies = []

    for i in range(0, len(music) - window, window):
        chunk = music[i:i + window]
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        energies.append(rms)

    events = []
    for i in range(2, len(energies)):
        prev = energies[i - 2]
        curr = energies[i]
        if prev > 0:
            change = (curr - prev) / prev
            if abs(change) > 0.4:  # 40% change = significant event
                events.append({
                    'timestamp': round(i, 2),
                    'type': 'build' if change > 0 else 'drop',
                    'magnitude': round(change, 2)
                })

    return events


def estimate_bpm(music: np.ndarray, sr: int) -> float:
    """Estimate BPM from music track using autocorrelation"""
    # Sample first 60 seconds for speed
    sample = music[:sr * 60]

    # Compute onset envelope (frame-by-frame energy differences)
    hop = int(sr * 0.01)  # 10ms hops
    frames = []
    for i in range(0, len(sample) - hop, hop):
        rms = float(np.sqrt(np.mean(sample[i:i+hop] ** 2)))
        frames.append(rms)

    frames = np.array(frames)
    # Onset = positive differences only
    onset = np.maximum(np.diff(frames), 0)

    # Autocorrelation to find beat period
    if len(onset) < 100:
        return 0.0

    corr = np.correlate(onset, onset, mode='full')
    corr = corr[len(corr) // 2:]

    # Search for peak in 60-200 BPM range
    fps = sr / hop
    min_lag = int(fps * 60 / 200)  # 200 BPM
    max_lag = int(fps * 60 / 60)   # 60 BPM

    if max_lag >= len(corr) or min_lag < 1:
        return 0.0

    peak_lag = np.argmax(corr[min_lag:max_lag]) + min_lag
    bpm = fps * 60 / peak_lag if peak_lag > 0 else 0.0
    return round(float(bpm), 1)


# ============================================================================
# VTT PARSING
# ============================================================================

def parse_vtt(vtt_path: Path) -> list:
    """Parse VTT into word-level timeline [{time, word}]"""
    if not vtt_path.exists():
        return []

    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'<(\d{2}):(\d{2}):([\d.]+)><c>\s*([^<]+)</c>'
    matches = re.findall(pattern, content)

    words = []
    for h, m, s, word in matches:
        t = int(h) * 3600 + int(m) * 60 + float(s)
        words.append({'time': round(t, 2), 'word': word.strip()})

    return words


def words_at_second(word_timeline: list, t: float, window: float = 0.5) -> str:
    """Get words spoken around timestamp t"""
    w = [e['word'] for e in word_timeline if abs(e['time'] - t) <= window]
    return ' '.join(w) if w else ''


# ============================================================================
# MASTER TIMELINE FUSION
# ============================================================================

def build_master_timeline(
    duration: float,
    word_timeline: list,
    vocal_energy: list,
    music_energy: list,
    pauses: list,
    builds_drops: list,
    emphasis_peaks: list,
) -> list:
    """
    Fuse all layers into one master timeline (1 entry per second).
    This is the core output — every second: what words, what music energy,
    what vocal energy, is narrator pausing, is music building/dropping.
    """
    pause_set = set()
    for p in pauses:
        for sec in range(int(p['start']), int(p['end']) + 1):
            pause_set.add(sec)

    build_drop_map = {}
    for bd in builds_drops:
        build_drop_map[int(bd['timestamp'])] = bd['type']

    emphasis_set = {int(e['timestamp']) for e in emphasis_peaks}

    vocal_map  = {int(e['timestamp']): e['energy'] for e in vocal_energy}
    music_map  = {int(e['timestamp']): e['energy'] for e in music_energy}

    timeline = []
    for sec in range(int(duration)):
        words = words_at_second(word_timeline, sec, window=0.5)
        entry = {
            'timestamp': sec,
            'words': words,
            'vocal_energy': vocal_map.get(sec, 0.0),
            'music_energy': music_map.get(sec, 0.0),
            'is_pause': sec in pause_set,
            'is_emphasis': sec in emphasis_set,
            'music_event': build_drop_map.get(sec),  # 'build' | 'drop' | None
        }
        timeline.append(entry)

    return timeline


# ============================================================================
# MAIN PER-VIDEO ANALYSIS
# ============================================================================

def analyze_video(video_id: str):
    video_dir = FERN_DIR / video_id
    video_file = video_dir / "video.mp4"
    vtt_file   = video_dir / "video.en.vtt"
    out_file   = FERN_DIR / f"{video_id}_audio_full.json"

    if out_file.exists():
        print(f"  ✓ Already done: {out_file.name}")
        return

    if not video_file.exists():
        print(f"  ⚠ No video file for {video_id}, skipping")
        return

    print(f"\n{'='*60}")
    print(f"Video: {video_id}")
    print(f"{'='*60}")

    AUDIO_CACHE.mkdir(parents=True, exist_ok=True)
    SR = 22050

    # Step 1: Extract audio
    print(f"\n[1/5] Extracting audio...")
    raw_audio = AUDIO_CACHE / f"{video_id}.wav"
    if not extract_audio(video_file, raw_audio):
        return

    # Step 2: Demucs separation
    print(f"\n[2/5] Separating vocals + music (Demucs)...")
    stems = separate_audio(video_id, raw_audio)

    if not stems:
        print("  ❌ Demucs failed, falling back to raw audio only")
        vocals_audio, _ = load_audio_numpy(raw_audio, SR)
        music_audio = np.zeros_like(vocals_audio)
    else:
        print(f"  Loading vocals...")
        vocals_audio, _ = load_audio_numpy(stems['vocals'], SR)
        print(f"  Loading music...")
        music_audio, _  = load_audio_numpy(stems['music'], SR)

    duration = len(vocals_audio) / SR

    # Step 3: Analyze each track
    print(f"\n[3/5] Analyzing tracks ({duration/60:.1f} min)...")

    print(f"  Computing vocal energy timeline...")
    vocal_energy = energy_timeline(vocals_audio, SR)

    print(f"  Computing music energy timeline...")
    music_energy = energy_timeline(music_audio, SR)

    print(f"  Detecting vocal pauses...")
    pauses = detect_pauses(vocals_audio, SR)
    print(f"    Found {len(pauses)} pauses")

    print(f"  Detecting vocal emphasis peaks...")
    emphasis = detect_emphasis_peaks(vocals_audio, SR)
    print(f"    Found {len(emphasis)} emphasis moments")

    print(f"  Detecting music builds/drops...")
    builds_drops = detect_music_builds_drops(music_audio, SR)
    print(f"    Found {len(builds_drops)} music events")

    print(f"  Estimating BPM...")
    bpm = estimate_bpm(music_audio, SR)
    print(f"    BPM: {bpm}")

    # Step 4: Parse VTT
    print(f"\n[4/5] Loading script (VTT)...")
    word_timeline = parse_vtt(vtt_file)
    print(f"  {len(word_timeline)} words loaded")

    # Step 5: Build master timeline
    print(f"\n[5/5] Building master timeline...")
    master = build_master_timeline(
        duration, word_timeline,
        vocal_energy, music_energy,
        pauses, builds_drops, emphasis
    )
    print(f"  {len(master)} seconds of fused timeline")

    # Save
    result = {
        'video_id': video_id,
        'duration': round(duration, 2),
        'bpm': bpm,
        'pause_count': len(pauses),
        'emphasis_count': len(emphasis),
        'music_events': len(builds_drops),
        'word_count': len(word_timeline),
        'pauses': pauses,
        'emphasis_peaks': emphasis,
        'builds_drops': builds_drops,
        'master_timeline': master,
    }

    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ Saved: {out_file}")
    print(f"   Duration: {duration/60:.1f} min | BPM: {bpm} | Pauses: {len(pauses)} | Events: {len(builds_drops)}")


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fern Audio Analysis — Demucs separation + master timeline')
    parser.add_argument('--video', help='Analyze a single video ID (default: all 3 downloaded)')
    args = parser.parse_args()

    if args.video:
        analyze_video(args.video)
    else:
        # Find all downloaded videos
        videos = [d.name for d in FERN_DIR.iterdir()
                  if d.is_dir() and (d / 'video.mp4').exists()]
        print(f"Found {len(videos)} downloaded videos: {videos}")
        for vid in videos:
            analyze_video(vid)

    print("\n🎵 Audio analysis complete.")
