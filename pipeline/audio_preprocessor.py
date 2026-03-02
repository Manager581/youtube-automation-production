#!/usr/bin/env python3
"""
audio_preprocessor.py — Clean up a voice reference clip before F5-TTS.

Fixes:
  - Background hiss/hum/room noise (spectral subtraction)
  - Low-frequency rumble (80Hz high-pass filter)
  - Volume too low or too loud (normalize to -23 LUFS)
  - Stereo → mono conversion
  - Resampling to 24kHz (F5-TTS native rate)

Usage:
  # Clean a noisy recording
  venv/bin/python pipeline/audio_preprocessor.py \
    --input my_rough_recording.wav \
    --output my_voice_clean.wav

  # Preview what the noise profile looks like
  venv/bin/python pipeline/audio_preprocessor.py \
    --input my_rough_recording.wav \
    --output my_voice_clean.wav \
    --report

  # If your recording has 0.5s of silence at the start, use that as noise profile
  venv/bin/python pipeline/audio_preprocessor.py \
    --input my_rough_recording.wav \
    --output my_voice_clean.wav \
    --noise-sample-sec 0.5
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf


# Target loudness (broadcast standard / YouTube standard)
TARGET_LUFS = -23.0

# F5-TTS native sample rate
TARGET_SR = 24000

# High-pass cutoff — removes room rumble, AC hum
HP_CUTOFF_HZ = 80

# How many seconds from the START of the clip to use as noise sample
# (assumes first N seconds are room noise / silence before speaking)
DEFAULT_NOISE_SAMPLE_SEC = 0.3


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Load audio as mono float32, return (samples, sample_rate)."""
    data, sr = sf.read(str(path), always_2d=True, dtype='float32')
    # Mix to mono
    if data.shape[1] > 1:
        data = data.mean(axis=1)
    else:
        data = data[:, 0]
    return data, sr


def save_audio(path: Path, data: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), data, sr, subtype='PCM_16')


def resample(data: np.ndarray, from_sr: int, to_sr: int) -> np.ndarray:
    """Resample audio using scipy (installed with librosa)."""
    if from_sr == to_sr:
        return data
    import scipy.signal as signal
    num_samples = int(len(data) * to_sr / from_sr)
    return signal.resample(data, num_samples).astype(np.float32)


# ---------------------------------------------------------------------------
# Processing steps
# ---------------------------------------------------------------------------

def high_pass_filter(data: np.ndarray, sr: int, cutoff_hz: float = HP_CUTOFF_HZ) -> np.ndarray:
    """Remove low-frequency rumble below cutoff_hz."""
    import scipy.signal as signal
    nyq = sr / 2.0
    norm_cutoff = cutoff_hz / nyq
    b, a = signal.butter(4, norm_cutoff, btype='high', analog=False)
    return signal.lfilter(b, a, data).astype(np.float32)


def reduce_noise(data: np.ndarray, sr: int, noise_sample_sec: float) -> np.ndarray:
    """
    Spectral noise reduction using noisereduce.
    Uses the first noise_sample_sec seconds as the noise profile.
    """
    import noisereduce as nr  # type: ignore
    noise_samples = int(noise_sample_sec * sr)
    noise_clip = data[:noise_samples] if noise_samples > 0 else None

    if noise_clip is not None and len(noise_clip) < 64:
        print("  WARNING: noise sample too short — skipping noise reduction")
        return data

    reduced = nr.reduce_noise(
        y=data,
        sr=sr,
        y_noise=noise_clip,
        prop_decrease=0.85,       # how aggressively to reduce (0–1)
        stationary=False,         # works on varying background noise too
        n_fft=2048,
    )
    return reduced.astype(np.float32)


def normalize_loudness(data: np.ndarray, sr: int, target_lufs: float = TARGET_LUFS) -> np.ndarray:
    """
    Normalize to target integrated loudness (LUFS).
    Falls back to peak normalization if pyloudnorm fails.
    """
    try:
        import pyloudnorm as pyln  # type: ignore
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(data.astype(np.float64))

        if not np.isfinite(loudness) or loudness < -70:
            print(f"  Loudness measurement failed ({loudness:.1f} LUFS) — using peak normalization")
            return _peak_normalize(data)

        gain = target_lufs - loudness
        print(f"  Loudness: {loudness:.1f} LUFS → applying {gain:+.1f} dB gain")
        normalized = pyln.normalize.loudness(data.astype(np.float64), loudness, target_lufs)
        return normalized.astype(np.float32)

    except Exception as e:
        print(f"  pyloudnorm error: {e} — using peak normalization")
        return _peak_normalize(data)


def _peak_normalize(data: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    """Normalize so peak is at target_db dBFS."""
    peak = np.max(np.abs(data))
    if peak < 1e-6:
        return data
    target_linear = 10 ** (target_db / 20)
    return (data / peak * target_linear).astype(np.float32)


def trim_silence(data: np.ndarray, sr: int,
                 threshold_db: float = -40, pad_sec: float = 0.05) -> np.ndarray:
    """Trim leading/trailing silence. Keep a small pad so F5-TTS doesn't clip."""
    import librosa  # type: ignore
    trimmed, _ = librosa.effects.trim(data, top_db=abs(threshold_db), frame_length=512, hop_length=128)
    pad_samples = int(pad_sec * sr)
    padding = np.zeros(pad_samples, dtype=np.float32)
    return np.concatenate([padding, trimmed, padding])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def preprocess(
    input_path: Path,
    output_path: Path,
    noise_sample_sec: float = DEFAULT_NOISE_SAMPLE_SEC,
    report: bool = False,
) -> dict:
    print(f"\nPreprocessing: {input_path.name}")

    data, sr = load_audio(input_path)
    duration = len(data) / sr
    print(f"  Loaded: {duration:.1f}s @ {sr}Hz")

    if duration < 3:
        print("  WARNING: clip is very short (<3s). F5-TTS works best with 10–30s of speech.")
    if duration > 60:
        print("  WARNING: clip is long (>60s). Trim to your best 15–30s for faster cloning.")

    steps = {}

    # 1. High-pass filter
    print(f"  [1/5] High-pass filter @ {HP_CUTOFF_HZ}Hz")
    data = high_pass_filter(data, sr)
    steps['high_pass'] = 'done'

    # 2. Noise reduction
    if noise_sample_sec > 0 and noise_sample_sec < duration * 0.5:
        print(f"  [2/5] Noise reduction (noise sample: first {noise_sample_sec:.2f}s)")
        data = reduce_noise(data, sr, noise_sample_sec)
        steps['noise_reduction'] = f'noise_sample={noise_sample_sec}s'
    else:
        print(f"  [2/5] Noise reduction skipped (sample_sec={noise_sample_sec})")
        steps['noise_reduction'] = 'skipped'

    # 3. Trim silence
    print(f"  [3/5] Trim leading/trailing silence")
    data = trim_silence(data, sr)
    steps['trim'] = 'done'

    # 4. Normalize loudness
    print(f"  [4/5] Loudness normalization → {TARGET_LUFS} LUFS")
    data = normalize_loudness(data, sr)
    steps['normalize'] = f'target={TARGET_LUFS}LUFS'

    # 5. Resample to F5-TTS native rate
    print(f"  [5/5] Resample {sr}Hz → {TARGET_SR}Hz")
    data = resample(data, sr, TARGET_SR)
    steps['resample'] = f'{sr}→{TARGET_SR}Hz'

    # Save
    save_audio(output_path, data, TARGET_SR)
    final_duration = len(data) / TARGET_SR
    print(f"\n  Saved: {output_path}")
    print(f"  Duration: {final_duration:.1f}s @ {TARGET_SR}Hz (mono PCM-16)")

    result = {
        'input': str(input_path),
        'output': str(output_path),
        'input_duration_sec': round(duration, 2),
        'output_duration_sec': round(final_duration, 2),
        'output_sr': TARGET_SR,
        'steps': steps,
    }

    if report:
        _print_report(result)

    return result


def _print_report(result: dict) -> None:
    print("\n" + "="*50)
    print("PREPROCESSING REPORT")
    print("="*50)
    for k, v in result.items():
        if k == 'steps':
            print("  Steps:")
            for step, val in v.items():
                print(f"    {step}: {val}")
        else:
            print(f"  {k}: {v}")
    print("\nNext step:")
    print(f"  venv/bin/python pipeline/voice_generator.py \\")
    print(f"    --ref-audio {result['output']} \\")
    print(f"    --auto-transcribe \\")
    print(f"    --script your_script.txt \\")
    print(f"    --out audio/narration.wav")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Clean a voice reference clip for F5-TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--input', required=True, help='Raw recording (.wav, .m4a, .mp3)')
    p.add_argument('--output', required=True, help='Output clean WAV')
    p.add_argument('--noise-sample-sec', type=float, default=DEFAULT_NOISE_SAMPLE_SEC,
                   help=f'Seconds of silence at start to use as noise profile (default: {DEFAULT_NOISE_SAMPLE_SEC})')
    p.add_argument('--no-noise-reduction', action='store_true',
                   help='Skip noise reduction (if clip has no background noise)')
    p.add_argument('--report', action='store_true',
                   help='Print processing report and next-step command')
    args = p.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    # Handle non-WAV input: convert with ffmpeg first
    output_path = Path(args.output)
    if input_path.suffix.lower() in ('.m4a', '.mp3', '.aac', '.ogg', '.flac'):
        import subprocess, tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tmp.close()
        tmp_wav = Path(tmp.name)
        print(f"  Converting {input_path.suffix} → WAV...")
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', str(input_path), '-ar', str(TARGET_SR),
             '-ac', '1', str(tmp_wav)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"ERROR converting input: {result.stderr}")
            sys.exit(1)
        input_path = tmp_wav

    noise_sec = 0.0 if args.no_noise_reduction else args.noise_sample_sec

    preprocess(
        input_path=input_path,
        output_path=output_path,
        noise_sample_sec=noise_sec,
        report=args.report,
    )


if __name__ == '__main__':
    main()
