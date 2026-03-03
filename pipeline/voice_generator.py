#!/usr/bin/env python3
"""
voice_generator.py — Local voice cloning via F5-TTS with Fern-style emotion control.

Supports script markup for pauses and emotional register switching:
  [PAUSE:1.2]   → insert 1.2 seconds of silence
  [BEAT]        → insert 0.3s pause (mid-thought)
  [BREATH]      → insert 0.15s pause (natural breath)
  [VOICE:tense]     → switch to tense reference clip
  [VOICE:neutral]   → switch to neutral reference clip
  [VOICE:energized] → switch to energized reference clip

Usage:
  # Single reference clip (simplest)
  venv/bin/python pipeline/voice_generator.py \
    --ref-audio assets/voice/voice_neutral.wav \
    --auto-transcribe \
    --script scripts/cia_mkultra.txt \
    --out audio/cia_mkultra/narration.wav

  # Multi-register (closest Fern match)
  venv/bin/python pipeline/voice_generator.py \
    --ref-neutral  assets/voice/voice_neutral.wav \
    --ref-tense    assets/voice/voice_tense.wav \
    --ref-energized assets/voice/voice_energized.wav \
    --auto-transcribe \
    --script scripts/cia_mkultra.txt \
    --out audio/cia_mkultra/narration.wav

Example script with markup:
  [VOICE:energized]
  In 1953, the CIA did something that should have been impossible. [BEAT]

  [VOICE:neutral]
  They erased a man's mind. [PAUSE:1.2]

  [VOICE:tense]
  And then they did it again... and again... until there was nothing left.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants — Fern production spec
# ---------------------------------------------------------------------------
TARGET_WPM       = 138.7   # Fern's measured avg across 3 videos (127 / 151 / 138)
CHUNK_WORD_LIMIT = 150     # target words per F5-TTS chunk
CHUNK_WORD_MIN   = 15      # don't make a chunk this tiny

# Default pause durations (seconds)
PAUSE_BEAT   = 0.30
PAUSE_BREATH = 0.15
PAUSE_CHUNK  = 0.20   # gap between chunks that share the same voice register

# WPM normalization: if generated chunk is >15% off target, time-stretch it
WPM_TOLERANCE = 0.15
WPM_STRETCH_MIN = 0.5   # ffmpeg atempo min
WPM_STRETCH_MAX = 2.0   # ffmpeg atempo max


# ---------------------------------------------------------------------------
# Script segment data structures
# ---------------------------------------------------------------------------

@dataclass
class SpeechSegment:
    text: str
    voice: str = "neutral"   # neutral | tense | energized


@dataclass
class PauseSegment:
    duration: float          # seconds


Segment = SpeechSegment | PauseSegment


# ---------------------------------------------------------------------------
# Script parsing
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Remove leftover stage directions that aren't our markup."""
    # Remove timestamps (00:00)
    text = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_script(raw: str) -> list[Segment]:
    """
    Parse a script into a list of SpeechSegments and PauseSegments.

    Recognises:
      [PAUSE:N]       → PauseSegment(N)
      [BEAT]          → PauseSegment(0.30)
      [BREATH]        → PauseSegment(0.15)
      [VOICE:name]    → sets current voice register (no segment emitted)
    """
    segments: list[Segment] = []
    current_voice = "neutral"
    current_text_parts: list[str] = []

    # Tokenise: split on any tag
    token_re = re.compile(
        r'(\[PAUSE:[\d.]+\]|\[BEAT\]|\[BREATH\]|\[VOICE:\w+\])',
        re.IGNORECASE,
    )

    def flush_text():
        joined = ' '.join(current_text_parts).strip()
        if joined:
            cleaned = _clean_text(joined)
            if cleaned:
                # Chunk long runs at sentence boundaries
                for chunk in _chunk(cleaned, CHUNK_WORD_LIMIT):
                    segments.append(SpeechSegment(text=chunk, voice=current_voice))
                    segments.append(PauseSegment(duration=PAUSE_CHUNK))
                # Remove the trailing inter-chunk pause after each flush
                if segments and isinstance(segments[-1], PauseSegment) and segments[-1].duration == PAUSE_CHUNK:
                    segments.pop()
        current_text_parts.clear()

    tokens = token_re.split(raw)
    for tok in tokens:
        if not tok:
            continue

        upper = tok.upper()

        if upper.startswith('[PAUSE:'):
            flush_text()
            m = re.match(r'\[PAUSE:([\d.]+)\]', tok, re.IGNORECASE)
            if m:
                segments.append(PauseSegment(duration=float(m.group(1))))

        elif upper == '[BEAT]':
            flush_text()
            segments.append(PauseSegment(duration=PAUSE_BEAT))

        elif upper == '[BREATH]':
            flush_text()
            segments.append(PauseSegment(duration=PAUSE_BREATH))

        elif upper.startswith('[VOICE:'):
            flush_text()
            m = re.match(r'\[VOICE:(\w+)\]', tok, re.IGNORECASE)
            if m:
                current_voice = m.group(1).lower()

        else:
            current_text_parts.append(tok)

    flush_text()

    # Collapse consecutive pauses
    merged: list[Segment] = []
    for seg in segments:
        if merged and isinstance(merged[-1], PauseSegment) and isinstance(seg, PauseSegment):
            merged[-1].duration += seg.duration
        else:
            merged.append(seg)

    return merged


def _chunk(text: str, word_limit: int) -> list[str]:
    """Split text into ≤word_limit chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?…])\s+', text)
    chunks, current, current_words = [], [], 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        wc = len(sent.split())

        if wc > word_limit:
            # Long sentence: split at commas
            for part in re.split(r',\s+', sent):
                pw = len(part.split())
                if current_words + pw > word_limit and current_words >= CHUNK_WORD_MIN:
                    chunks.append(' '.join(current))
                    current, current_words = [part], pw
                else:
                    current.append(part)
                    current_words += pw
            continue

        if current_words + wc > word_limit and current_words >= CHUNK_WORD_MIN:
            chunks.append(' '.join(current))
            current, current_words = [sent], wc
        else:
            current.append(sent)
            current_words += wc

    if current:
        chunks.append(' '.join(current))

    # Merge tiny trailing chunk
    if len(chunks) >= 2 and len(chunks[-1].split()) < CHUNK_WORD_MIN:
        chunks[-2] += ' ' + chunks[-1]
        chunks.pop()

    return [c for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# Audio utilities
# ---------------------------------------------------------------------------

def _get_wav_duration(path: Path) -> float:
    with wave.open(str(path), 'r') as w:
        return w.getnframes() / w.getframerate()


def _make_silence(duration_sec: float, sample_rate: int = 24000) -> Path:
    tmp = Path(tempfile.mktemp(suffix='.wav'))
    n = int(sample_rate * duration_sec)
    with wave.open(str(tmp), 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b'\x00\x00' * n)
    return tmp


def _concat_wavs(wav_paths: list[Path], out_path: Path) -> None:
    list_file = out_path.parent / '_concat_list.txt'
    with open(list_file, 'w') as f:
        for p in wav_paths:
            f.write(f"file '{p.resolve()}'\n")
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
           '-i', str(list_file), '-ar', '24000', '-ac', '1', str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    list_file.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed:\n{r.stderr}")


def _time_stretch(wav_path: Path, ratio: float) -> Path:
    """
    Apply time-stretch (speed up/slow down) via ffmpeg atempo without pitch shift.
    ratio > 1 = faster, < 1 = slower.
    atempo is limited to 0.5–2.0; chain filters for extreme ratios.
    """
    ratio = max(0.25, min(4.0, ratio))
    out = wav_path.with_suffix('.stretched.wav')

    # Build filter chain: atempo only accepts 0.5–2.0
    filters = []
    r = ratio
    while r > 2.0:
        filters.append('atempo=2.0')
        r /= 2.0
    while r < 0.5:
        filters.append('atempo=0.5')
        r *= 2.0
    filters.append(f'atempo={r:.4f}')

    cmd = ['ffmpeg', '-y', '-i', str(wav_path),
           '-filter:a', ','.join(filters), str(out)]
    r2 = subprocess.run(cmd, capture_output=True, text=True)
    if r2.returncode != 0:
        print(f"  WARNING: time-stretch failed, keeping original: {r2.stderr[:200]}")
        return wav_path
    return out


def wav_to_mp3(wav_path: Path, mp3_path: Path, bitrate: str = '192k') -> None:
    cmd = ['ffmpeg', '-y', '-i', str(wav_path), '-b:a', bitrate, str(mp3_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg mp3 failed:\n{r.stderr}")


# ---------------------------------------------------------------------------
# Auto-transcription
# ---------------------------------------------------------------------------

def auto_transcribe(audio_path: Path) -> str:
    try:
        import whisper  # type: ignore
    except ImportError:
        raise ImportError(
            "openai-whisper not installed. Run:\n"
            "  venv/bin/pip install openai-whisper"
        )
    print("  Transcribing reference audio with Whisper (base model)...")
    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path))
    text = result["text"].strip()
    print(f"  Transcription: {text!r}")
    return text


# ---------------------------------------------------------------------------
# F5-TTS
# ---------------------------------------------------------------------------

def _load_tts():
    from f5_tts.api import F5TTS  # type: ignore
    return F5TTS()


def _generate_chunk(tts, ref_audio: Path, ref_text: str,
                    gen_text: str, out_path: Path) -> Path:
    tts.infer(
        ref_file=str(ref_audio),
        ref_text=ref_text,
        gen_text=gen_text,
        file_wave=str(out_path),
    )
    return out_path


# ---------------------------------------------------------------------------
# WPM normalization
# ---------------------------------------------------------------------------

def _normalize_wpm(chunk_wav: Path, word_count: int,
                   target_wpm: float = TARGET_WPM) -> Path:
    """
    If the generated audio is too fast or too slow vs target WPM, time-stretch it.
    Returns path to (possibly new) normalized file.
    """
    actual_duration = _get_wav_duration(chunk_wav)
    if actual_duration < 0.1 or word_count < 3:
        return chunk_wav

    actual_wpm = (word_count / actual_duration) * 60
    target_duration = (word_count / target_wpm) * 60
    # ratio = actual/target: >1 means audio is too long (too slow), <1 means too short (too fast)
    # atempo: >1 = faster (shorter), <1 = slower (longer) — so pass ratio directly
    ratio = actual_duration / target_duration

    if abs(ratio - 1.0) > WPM_TOLERANCE:
        print(f"    WPM {actual_wpm:.0f} → stretching ×{ratio:.2f} → ~{target_wpm:.0f} WPM")
        return _time_stretch(chunk_wav, ratio)

    return chunk_wav


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def generate_narration(
    ref_clips: dict[str, tuple[Path, str]],  # {register: (wav_path, transcription)}
    script_text: str,
    out_path: Path,
    normalize_wpm: bool = True,
    to_mp3: bool = False,
) -> dict:
    """
    Full pipeline: parse script → generate each speech segment → concatenate.

    ref_clips: dict mapping register name → (wav_path, transcription_text)
               Must contain at least "neutral".

    Returns manifest dict with per-segment timestamps.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = out_path.parent / '_voice_tmp'
    tmp_dir.mkdir(exist_ok=True)

    segments = parse_script(script_text)
    speech_count = sum(1 for s in segments if isinstance(s, SpeechSegment))
    print(f"  Parsed script: {speech_count} speech segments, "
          f"{len(segments) - speech_count} pause segments")

    # Validate all referenced registers exist
    used_registers = {s.voice for s in segments if isinstance(s, SpeechSegment)}
    for reg in used_registers:
        if reg not in ref_clips:
            print(f"  WARNING: register '{reg}' not provided — falling back to 'neutral'")

    print("  Loading F5-TTS model (first run downloads ~700MB)...")
    tts = _load_tts()

    wav_parts: list[Path] = []
    manifest = {"segments": [], "total_duration_sec": 0.0, "out": str(out_path)}
    cursor = 0.0
    speech_idx = 0

    for seg in segments:
        if isinstance(seg, PauseSegment):
            sil = _make_silence(seg.duration)
            wav_parts.append(sil)
            manifest["segments"].append({
                "type": "pause",
                "start_sec": round(cursor, 3),
                "duration_sec": round(seg.duration, 3),
            })
            cursor += seg.duration

        else:  # SpeechSegment
            speech_idx += 1
            reg = seg.voice if seg.voice in ref_clips else "neutral"
            ref_wav, ref_text = ref_clips[reg]
            word_count = len(seg.text.split())

            chunk_wav = tmp_dir / f'seg_{speech_idx:04d}.wav'
            print(f"  [{speech_idx}/{speech_count}] [{reg}] {word_count}w: {seg.text[:55]}…")

            try:
                _generate_chunk(tts, ref_wav, ref_text, seg.text, chunk_wav)
            except Exception as e:
                print(f"  ERROR on segment {speech_idx}: {e}")
                raise

            if normalize_wpm:
                chunk_wav = _normalize_wpm(chunk_wav, word_count)

            dur = _get_wav_duration(chunk_wav)
            manifest["segments"].append({
                "type": "speech",
                "index": speech_idx,
                "start_sec": round(cursor, 3),
                "duration_sec": round(dur, 3),
                "end_sec": round(cursor + dur, 3),
                "word_count": word_count,
                "voice_register": reg,
                "text": seg.text,
            })
            wav_parts.append(chunk_wav)
            cursor += dur

    print("  Concatenating segments...")
    wav_out = out_path if out_path.suffix == '.wav' else out_path.with_suffix('.wav')
    _concat_wavs(wav_parts, wav_out)

    manifest["total_duration_sec"] = round(cursor, 3)
    manifest["word_count_total"] = sum(
        s["word_count"] for s in manifest["segments"] if s["type"] == "speech"
    )
    manifest["avg_wpm"] = round(
        manifest["word_count_total"] / (cursor / 60), 1
    ) if cursor > 0 else 0

    if to_mp3 or out_path.suffix == '.mp3':
        mp3_out = out_path.with_suffix('.mp3')
        print(f"  Converting to MP3: {mp3_out}")
        wav_to_mp3(wav_out, mp3_out)
        if out_path.suffix == '.mp3':
            wav_out.unlink(missing_ok=True)
        manifest["out"] = str(mp3_out)

    manifest_path = out_path.parent / (out_path.stem + '_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Cleanup
    for p in tmp_dir.iterdir():
        try:
            p.unlink()
        except Exception:
            pass
    try:
        tmp_dir.rmdir()
    except Exception:
        pass

    print(f"\nDone. {manifest['total_duration_sec']:.1f}s | {manifest['avg_wpm']} WPM → {manifest['out']}")
    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(
        description="Fern-style voice cloning narration via F5-TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Reference clip options — simple (single) or multi-register
    ref_g = p.add_argument_group("Reference clips")
    ref_g.add_argument('--ref-audio', metavar='WAV',
                       help='Single reference WAV (used as "neutral" register)')
    ref_g.add_argument('--ref-neutral', metavar='WAV',
                       help='Neutral register reference WAV')
    ref_g.add_argument('--ref-tense', metavar='WAV',
                       help='Tense register reference WAV')
    ref_g.add_argument('--ref-energized', metavar='WAV',
                       help='Energized register reference WAV')

    ref_g.add_argument('--ref-text', default=None,
                       help='Transcription of --ref-audio / --ref-neutral')
    ref_g.add_argument('--auto-transcribe', action='store_true',
                       help='Auto-transcribe reference clips with Whisper')

    # Script input
    inp = p.add_mutually_exclusive_group(required=True)
    inp.add_argument('--script', metavar='FILE', help='Script text file')
    inp.add_argument('--text', metavar='TEXT', help='Inline script text')

    # Output
    p.add_argument('--out', required=True, help='Output path (.wav or .mp3)')
    p.add_argument('--mp3', action='store_true', help='Also produce MP3')
    p.add_argument('--no-wpm-normalize', action='store_true',
                   help='Skip WPM normalization (time-stretch)')

    return p.parse_args()


def _resolve_ref_clip(wav_arg: Optional[str], text_arg: Optional[str],
                      auto: bool, label: str) -> Optional[tuple[Path, str]]:
    """Load a reference clip path and resolve its transcription."""
    if not wav_arg:
        return None
    path = Path(wav_arg)
    if not path.exists():
        print(f"ERROR: {label} reference not found: {path}")
        sys.exit(1)
    if text_arg:
        return path, text_arg
    if auto:
        return path, auto_transcribe(path)
    print(f"ERROR: Provide --ref-text or --auto-transcribe for {label}")
    sys.exit(1)


def main():
    args = _parse_args()

    # Build ref_clips dict
    ref_clips: dict[str, tuple[Path, str]] = {}

    # Simple single-clip mode
    if args.ref_audio:
        clip = _resolve_ref_clip(args.ref_audio, args.ref_text, args.auto_transcribe, "neutral")
        if clip:
            ref_clips["neutral"] = clip
            # Also make it available as tense/energized fallback
            ref_clips.setdefault("tense", clip)
            ref_clips.setdefault("energized", clip)

    # Multi-register mode
    if args.ref_neutral:
        clip = _resolve_ref_clip(args.ref_neutral, args.ref_text, args.auto_transcribe, "neutral")
        if clip:
            ref_clips["neutral"] = clip
    if args.ref_tense:
        clip = _resolve_ref_clip(args.ref_tense, None, args.auto_transcribe, "tense")
        if clip:
            ref_clips["tense"] = clip
    if args.ref_energized:
        clip = _resolve_ref_clip(args.ref_energized, None, args.auto_transcribe, "energized")
        if clip:
            ref_clips["energized"] = clip

    if "neutral" not in ref_clips:
        print("ERROR: Provide --ref-audio or --ref-neutral")
        sys.exit(1)

    # Fill missing registers with neutral
    ref_clips.setdefault("tense", ref_clips["neutral"])
    ref_clips.setdefault("energized", ref_clips["neutral"])

    # Script
    if args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            print(f"ERROR: Script not found: {script_path}")
            sys.exit(1)
        script_text = script_path.read_text()
    else:
        script_text = args.text

    out_path = Path(args.out)

    print(f"\nVoice Generator")
    print(f"  Registers : {list(ref_clips.keys())}")
    print(f"  Script    : {len(script_text.split())} words")
    print(f"  Target WPM: {TARGET_WPM}")
    print(f"  Output    : {out_path}\n")

    generate_narration(
        ref_clips=ref_clips,
        script_text=script_text,
        out_path=out_path,
        normalize_wpm=not args.no_wpm_normalize,
        to_mp3=args.mp3,
    )


if __name__ == '__main__':
    main()
