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
TARGET_WPM       = 175.0   # ColdFusion/HMW pace (was 138.7 Fern — too slow for business documentary)
CHUNK_WORD_LIMIT = 40      # paragraph-level chunks (was 22 — caused robotic splits at every sentence)
CHUNK_WORD_MIN   = 8       # don't make a chunk this tiny

# Default pause durations (seconds)
PAUSE_BEAT   = 0.30
PAUSE_BREATH = 0.15
PAUSE_CHUNK  = 0.0    # no artificial gap between chunks (crossfade handles transitions)

# Crossfade between speech chunks (seconds)
CROSSFADE_DURATION = 0.08  # 80ms crossfade at chunk boundaries

# WPM normalization: if generated chunk is >15% off target, time-stretch it
WPM_TOLERANCE = 0.15
WPM_STRETCH_MIN = 0.5   # ffmpeg atempo min
WPM_STRETCH_MAX = 2.0   # ffmpeg atempo max

# Per-register F5-TTS speed calibration (measured with _ref.wav clips)
# Each register's reference clip has a different natural speaking rate.
# These multipliers normalize all registers to ~139 WPM.
REGISTER_SPEED = {
    "neutral":   0.75,
    "tense":     0.78,
    "energized": 0.80,
}


# ---------------------------------------------------------------------------
# TTS text preprocessor — convert numbers/symbols to spoken words
# ---------------------------------------------------------------------------

_ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
         "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

def _num_to_words(n: int) -> str:
    if n < 0:
        return "minus " + _num_to_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        rest = _num_to_words(n % 100)
        return _ONES[n // 100] + " hundred" + ("" if not rest else " " + rest)
    if n < 1_000_000:
        rest = _num_to_words(n % 1000)
        return _num_to_words(n // 1000) + " thousand" + ("" if not rest else " " + rest)
    if n < 1_000_000_000:
        rest = _num_to_words(n % 1_000_000)
        return _num_to_words(n // 1_000_000) + " million" + ("" if not rest else " " + rest)
    return str(n)

def _year_to_words(y: int) -> str:
    if 1000 <= y <= 1999:
        hi, lo = divmod(y, 100)
        if lo == 0:
            return _num_to_words(hi) + " hundred"
        return _num_to_words(hi) + " " + _num_to_words(lo)
    if 2000 <= y <= 2099:
        if y == 2000:
            return "two thousand"
        return "two thousand " + _num_to_words(y - 2000)
    return _num_to_words(y)

def _tts_preprocess(text: str) -> str:
    """Convert numbers, dates, and symbols to spoken words for TTS clarity."""
    import re as _re
    # Time: 3:09 → three oh nine
    def _time_repl(m):
        h, mi = int(m.group(1)), m.group(2)
        mi_words = "oh " + _num_to_words(int(mi)) if mi.startswith("0") and len(mi) == 2 else _num_to_words(int(mi))
        return _num_to_words(h) + " " + mi_words
    text = _re.sub(r'\b(\d{1,2}):(\d{2})\b', _time_repl, text)
    # Ordinals: 10th → tenth, 13th → thirteenth
    _ordinal_map = {"1": "first", "2": "second", "3": "third", "5": "fifth",
                    "8": "eighth", "9": "ninth", "12": "twelfth"}
    def _ord_repl(m):
        n = int(m.group(1))
        s = str(n)
        if s in _ordinal_map:
            return _ordinal_map[s]
        w = _num_to_words(n)
        if w.endswith("y"):
            return w[:-1] + "ieth"
        if w.endswith("e"):
            return w + "th" if not w.endswith("ve") else w[:-2] + "fth"
        return w + "th"
    text = _re.sub(r'\b(\d+)(?:st|nd|rd|th)\b', _ord_repl, text)
    # Dollar amounts: $750,000 → seven hundred fifty thousand dollars
    def _dollar_repl(m):
        n = int(m.group(1).replace(",", ""))
        return _num_to_words(n) + " dollars"
    text = _re.sub(r'\$([0-9,]+)', _dollar_repl, text)
    # Years (4-digit standalone): 1953 → nineteen fifty three
    def _year_repl(m):
        return _year_to_words(int(m.group(0)))
    text = _re.sub(r'\b(1[0-9]{3}|20[0-9]{2})\b', _year_repl, text)
    # Room numbers like 1018A
    def _room_repl(m):
        num_part = m.group(1)
        letter = m.group(2) or ""
        hi, lo = int(num_part[:2]), int(num_part[2:])
        result = _num_to_words(hi) + " " + _num_to_words(lo)
        if letter:
            result += " " + letter.upper()
        return result
    text = _re.sub(r'\b(\d{4})([A-Za-z])\b', _room_repl, text)
    # Remaining plain numbers: 22 → twenty two
    def _plain_num(m):
        return _num_to_words(int(m.group(0).replace(",", "")))
    text = _re.sub(r'\b\d[\d,]*\b', _plain_num, text)
    # U.S. → U S (avoid period confusion)
    text = text.replace("U.S.", "U S")
    return text


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

    # Tokenise: split on any tag (including [CHAPTER:...] and bare [PAUSE])
    token_re = re.compile(
        r'(\[PAUSE:[\d.]+\]|\[PAUSE\]|\[BEAT\]|\[BREATH\]|\[VOICE:\w+\]|\[CHAPTER:[^\]]*\])',
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

        elif upper.startswith('[CHAPTER:'):
            # Chapter markers produce a 3s dramatic silence (LearnByLeo 5-step transition)
            flush_text()
            segments.append(PauseSegment(duration=3.0))

        elif upper == '[PAUSE]':
            # Bare [PAUSE] without duration — treat as 1.5s pause
            flush_text()
            segments.append(PauseSegment(duration=1.5))

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


def _concat_wavs(wav_paths: list[Path], out_path: Path, crossfade: float = 0.0) -> None:
    """Concatenate WAV files. If crossfade > 0, apply crossfade between consecutive files."""
    if crossfade > 0 and len(wav_paths) >= 2:
        _concat_with_crossfade(wav_paths, out_path, crossfade)
    else:
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


def _concat_with_crossfade(wav_paths: list[Path], out_path: Path, fade_dur: float) -> None:
    """Concatenate with crossfade between consecutive WAV files.

    Uses ffmpeg acrossfade filter. For >2 files, chains them pairwise
    through intermediate files.
    """
    if len(wav_paths) < 2:
        import shutil
        shutil.copy2(str(wav_paths[0]), str(out_path))
        return

    # For many files, chain pairwise through temp files
    tmp_dir = out_path.parent / '_xfade_tmp'
    tmp_dir.mkdir(exist_ok=True)

    current = str(wav_paths[0])
    for i, next_wav in enumerate(wav_paths[1:]):
        is_last = (i == len(wav_paths) - 2)
        out_file = str(out_path) if is_last else str(tmp_dir / f'xfade_{i:04d}.wav')

        # Check if files are long enough for crossfade
        try:
            dur_current = _get_wav_duration(Path(current))
            dur_next = _get_wav_duration(next_wav)
        except Exception:
            dur_current = dur_next = 1.0

        effective_fade = min(fade_dur, dur_current * 0.3, dur_next * 0.3)
        if effective_fade < 0.01:
            # Too short to crossfade — just concat
            list_file = tmp_dir / f'_concat_{i}.txt'
            with open(list_file, 'w') as f:
                f.write(f"file '{Path(current).resolve()}'\n")
                f.write(f"file '{next_wav.resolve()}'\n")
            cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                   '-i', str(list_file), '-ar', '24000', '-ac', '1', out_file]
        else:
            cmd = [
                'ffmpeg', '-y',
                '-i', current,
                '-i', str(next_wav),
                '-filter_complex',
                f'acrossfade=d={effective_fade:.3f}:c1=tri:c2=tri',
                '-ar', '24000', '-ac', '1',
                out_file,
            ]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            # Fallback to hard concat if crossfade fails
            list_file = tmp_dir / f'_concat_{i}.txt'
            with open(list_file, 'w') as f:
                f.write(f"file '{Path(current).resolve()}'\n")
                f.write(f"file '{next_wav.resolve()}'\n")
            cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                   '-i', str(list_file), '-ar', '24000', '-ac', '1', out_file]
            subprocess.run(cmd, capture_output=True, text=True)

        current = out_file

    # Cleanup
    for p in tmp_dir.iterdir():
        if p.name != out_path.name:
            p.unlink(missing_ok=True)
    tmp_dir.rmdir()


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
    import os
    # F5_DEVICE env override: MPS model-load can hang on some torch builds;
    # "cpu" is slower but reliable (and frees MPS for a concurrent LTX job).
    dev = os.environ.get("F5_DEVICE")
    return F5TTS(device=dev) if dev else F5TTS()


def _generate_chunk(tts, ref_audio: Path, ref_text: str,
                    gen_text: str, out_path: Path,
                    speed: float = 0.85) -> Path:
    gen_text = _tts_preprocess(gen_text)
    tts.infer(
        ref_file=str(ref_audio),
        ref_text=ref_text,
        gen_text=gen_text,
        file_wave=str(out_path),
        speed=speed,
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
    pending_pause_dur = 0.0  # accumulated pause duration before next speech chunk

    for seg in segments:
        if isinstance(seg, PauseSegment):
            sil = _make_silence(seg.duration)
            wav_parts.append(sil)
            manifest["segments"].append({
                "type": "pause",
                "start_sec": round(cursor, 3),
                "duration_sec": round(seg.duration, 3),
            })
            pending_pause_dur += seg.duration  # will be written to next speech chunk
            cursor += seg.duration

        else:  # SpeechSegment
            speech_idx += 1

            # Reload TTS every 10 segments to prevent OOM on M5 24GB
            if speech_idx > 1 and speech_idx % 10 == 0:
                print(f"  [Reloading F5-TTS to free memory (chunk {speech_idx})...]")
                import gc, torch
                del tts
                gc.collect()
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                tts = _load_tts()
            # Also clear MPS cache every 5 chunks (lightweight, no reload)
            elif speech_idx > 1 and speech_idx % 5 == 0:
                import gc, torch
                gc.collect()
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()

            reg = seg.voice if seg.voice in ref_clips else "neutral"
            ref_wav, ref_text = ref_clips[reg]
            word_count = len(seg.text.split())

            chunk_wav = tmp_dir / f'seg_{speech_idx:04d}.wav'
            print(f"  [{speech_idx}/{speech_count}] [{reg}] {word_count}w: {seg.text[:55]}…")

            # Resume support: skip if chunk already exists
            if chunk_wav.exists() and chunk_wav.stat().st_size > 1000:
                print(f"  [SKIP] {chunk_wav.name} already exists ({chunk_wav.stat().st_size} bytes)")
                dur = _get_wav_duration(chunk_wav)
                manifest["segments"].append({
                    "type": "speech",
                    "index": speech_idx,
                    "start_sec": round(cursor, 3),
                    "duration_sec": round(dur, 3),
                    "end_sec": round(cursor + dur, 3),
                    "word_count": word_count,
                    "voice_register": reg,
                    "pause_before_sec": round(pending_pause_dur, 3),
                    "text": seg.text,
                })
                pending_pause_dur = 0.0
                wav_parts.append(chunk_wav)
                cursor += dur
                continue

            try:
                reg_speed = REGISTER_SPEED.get(reg, 1.15)
                _generate_chunk(tts, ref_wav, ref_text, seg.text, chunk_wav, speed=reg_speed)
            except Exception as e:
                print(f"  ERROR on segment {speech_idx}: {e}")
                print(f"  Retrying with shorter split...")
                # Retry: split text in half and generate separately
                words = seg.text.split()
                mid = len(words) // 2
                half1 = ' '.join(words[:mid])
                half2 = ' '.join(words[mid:])
                try:
                    chunk_wav_a = tmp_dir / f'seg_{speech_idx:04d}_a.wav'
                    chunk_wav_b = tmp_dir / f'seg_{speech_idx:04d}_b.wav'
                    _generate_chunk(tts, ref_wav, ref_text, half1, chunk_wav_a, speed=reg_speed)
                    _generate_chunk(tts, ref_wav, ref_text, half2, chunk_wav_b, speed=reg_speed)
                    _concat_wavs([chunk_wav_a, chunk_wav_b], chunk_wav)
                except Exception as e2:
                    print(f"  RETRY FAILED on segment {speech_idx}: {e2}")
                    print(f"  Inserting silence placeholder for: {seg.text[:60]}...")
                    est_dur = (word_count / TARGET_WPM) * 60
                    chunk_wav = _make_silence(est_dur)
                    wav_parts.append(chunk_wav)
                    cursor += est_dur
                    continue

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
                "pause_before_sec": round(pending_pause_dur, 3),  # for reveal detection
                "text": seg.text,
            })
            pending_pause_dur = 0.0  # reset — consumed by this chunk
            wav_parts.append(chunk_wav)
            cursor += dur

    print("  Concatenating segments with crossfade...")
    wav_out = out_path if out_path.suffix == '.wav' else out_path.with_suffix('.wav')
    _concat_wavs(wav_parts, wav_out, crossfade=CROSSFADE_DURATION)

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
