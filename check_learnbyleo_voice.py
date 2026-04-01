#!/usr/bin/env python3
"""
check_learnbyleo_voice.py -- Voice narration QA checker for LearnByLeo pipeline.

Validates generated narration audio against LearnByLeo delivery benchmarks
derived from retention_delivery.json before committing to production.

LearnByLeo voice benchmarks:
  WPM:          120-180 (general YouTube educational range)
  Loudness:     -24 to -12 LUFS (voice-only track before mixing)
  Silence:      < 25% of total duration
  Clipping:     0 samples above -1 dBFS
  Vocal var:    Delivery must vary (volume, pace, pitch) -- AP-RD-02

Usage:
    python check_learnbyleo_voice.py audio/narration.wav
    python check_learnbyleo_voice.py audio/narration.wav \\
        --script scripts/enhanced_topic.txt \\
        --manifest audio/narration_manifest.json

Exit code: 0 = PASS or WARN, 1 = FAIL (regeneration recommended).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ── LearnByLeo voice benchmarks ──────────────────────────────────────────────

WPM_MIN         = 120.0
WPM_MAX         = 180.0
WPM_MIDPOINT    = 150.0
WPM_FAIL_MIN    = 90.0    # fail below
WPM_FAIL_MAX    = 210.0   # fail above

LUFS_LOW        = -24.0   # warn below
LUFS_HIGH       = -12.0   # warn above
LUFS_FAIL_LOW   = -35.0   # fail -- barely audible
LUFS_FAIL_HIGH  = -8.0    # fail -- clipping risk after mixing

SILENCE_WARN    = 0.25    # warn if > 25%
SILENCE_FAIL    = 0.45    # fail if > 45%
SILENCE_DB      = -35     # threshold for silence detection

DUR_TOLERANCE   = 0.30    # +/-30% from expected duration -> WARN
DUR_FAIL        = 0.50    # +/-50% -> FAIL

# Duration range for LearnByLeo (10-25 min)
DUR_MIN_SEC     = 10 * 60
DUR_MAX_SEC     = 30 * 60  # generous upper bound for audio

# Vocal variation thresholds (AP-RD-02)
VARIATION_RMS_MIN   = 3.0   # dB range in RMS across chunks (minimum)
VARIATION_WARN      = 2.0   # below this = monotone warning

# ── Load playbook for reference ──────────────────────────────────────────────

PLAYBOOK_PATH = Path(__file__).parent / "playbook" / "retention_delivery.json"


def load_playbook():
    """Load LearnByLeo retention/delivery playbook."""
    try:
        with open(PLAYBOOK_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ── ANSI colors ──────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ICONS  = {"PASS": "v", "WARN": "!", "FAIL": "X", "SKIP": "-"}
COLORS = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED, "SKIP": GRAY}


# ── ffprobe / ffmpeg helpers ─────────────────────────────────────────────────

def _ffprobe_json(path, show_entries):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_entries", show_entries, str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def _ffmpeg_run(args, timeout=300):
    r = subprocess.run(["ffmpeg"] + args, capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr, r.returncode


def _get_duration(audio_path: Path) -> float | None:
    data = _ffprobe_json(audio_path, "format=duration")
    if data:
        try:
            return float(data["format"]["duration"])
        except Exception:
            pass
    return None


# ── Individual checks ────────────────────────────────────────────────────────

def check_duration(audio_path: Path, script_path: Path | None):
    """
    Check narration duration against expected from script word count.
    Expected = word_count / WPM_MIDPOINT * 60 seconds (+ ~10% for pauses).
    """
    dur = _get_duration(audio_path)
    if dur is None:
        return None, "FAIL", "Could not read audio duration -- is ffprobe installed?"

    m = dur / 60

    if script_path and script_path.exists():
        text = script_path.read_text(encoding="utf-8", errors="ignore")
        # Strip control markers
        clean = re.sub(r"\[PAUSE:[^\]]+\]|\[BEAT\]|\[BREATH\]|\[VOICE:[^\]]+\]", "", text)
        words = len(clean.split())
        expected_sec = (words / WPM_MIDPOINT) * 60 * 1.12   # +12% for pauses/breaths
        expected_min = expected_sec / 60
        ratio = (dur - expected_sec) / expected_sec

        if abs(ratio) > DUR_FAIL:
            return dur, "FAIL", (
                f"{m:.1f} min (expected ~{expected_min:.1f} min for {words} words) -- "
                f"{'too long' if ratio > 0 else 'too short'} by {abs(ratio):.0%}. "
                f"TTS speed issue. Regenerate."
            )
        if abs(ratio) > DUR_TOLERANCE:
            return dur, "WARN", (
                f"{m:.1f} min (expected ~{expected_min:.1f} min for {words} words) -- "
                f"{'slightly long' if ratio > 0 else 'slightly short'} ({abs(ratio):.0%} off)"
            )
        return dur, "PASS", f"{m:.1f} min (expected ~{expected_min:.1f} min, {words} words)"

    # No script -- just check reasonable range
    if dur < DUR_MIN_SEC:
        return dur, "FAIL", f"{m:.1f} min -- suspiciously short. Narration likely incomplete."
    if dur > DUR_MAX_SEC:
        return dur, "WARN", f"{m:.1f} min -- very long. Verify script length."
    return dur, "PASS", f"{m:.1f} min (no script provided for comparison)"


def check_loudness(audio_path: Path):
    """
    Measure integrated LUFS loudness.
    Voice-only track should be -24 to -12 LUFS before mixing.
    """
    _, stderr, _ = _ffmpeg_run([
        "-i", str(audio_path),
        "-af", "loudnorm=print_format=json",
        "-f", "null", "-",
    ])

    try:
        start = stderr.rfind("{")
        end   = stderr.rfind("}") + 1
        data  = json.loads(stderr[start:end])
        lufs  = float(data.get("input_i", "-999"))
    except Exception:
        return None, "WARN", "Could not parse loudnorm output -- check ffmpeg install"

    if lufs < LUFS_FAIL_LOW:
        return lufs, "FAIL", f"{lufs:.1f} LUFS -- barely audible. Check audio preprocessing."
    if lufs > LUFS_FAIL_HIGH:
        return lufs, "FAIL", f"{lufs:.1f} LUFS -- will clip after mixing. Re-normalize."
    if lufs < LUFS_LOW:
        return lufs, "WARN", f"{lufs:.1f} LUFS -- quiet (target: {LUFS_LOW:.0f} to {LUFS_HIGH:.0f} LUFS)"
    if lufs > LUFS_HIGH:
        return lufs, "WARN", f"{lufs:.1f} LUFS -- loud for voice-only (target: {LUFS_LOW:.0f} to {LUFS_HIGH:.0f})"
    return lufs, "PASS", f"{lufs:.1f} LUFS (good level for voice before mixing)"


def check_silence_ratio(audio_path: Path):
    """
    Detect excessive silence -- TTS sometimes adds long gaps.
    Total silence should be < 25% of narration duration.
    """
    dur = _get_duration(audio_path)
    if not dur:
        return None, "SKIP", "Could not determine duration"

    _, stderr, _ = _ffmpeg_run([
        "-i", str(audio_path),
        "-af", f"silencedetect=n={SILENCE_DB}dB:d=0.3",
        "-f", "null", "-",
    ])

    silence_durations = re.findall(r"silence_duration:\s*([\d.]+)", stderr)
    total_silence = sum(float(d) for d in silence_durations)
    ratio = total_silence / max(dur, 1)

    if ratio > SILENCE_FAIL:
        return ratio, "FAIL", (
            f"{ratio:.0%} silence ({total_silence:.0f}s of {dur/60:.1f} min) -- "
            f"TTS added excessive gaps. Regenerate or clean up silences."
        )
    if ratio > SILENCE_WARN:
        return ratio, "WARN", (
            f"{ratio:.0%} silence ({total_silence:.0f}s) -- slightly high. "
            f"Check for long gaps between segments."
        )
    return ratio, "PASS", f"{ratio:.0%} silence ({total_silence:.0f}s total pauses)"


def check_wpm(audio_path: Path, manifest_path: Path | None):
    """
    Check speech rate (WPM) from narration manifest timestamps.
    LearnByLeo target: 120-180 WPM.
    """
    if not manifest_path or not manifest_path.exists():
        # Try to estimate from audio duration and script if available
        return None, "SKIP", "No narration manifest -- WPM check skipped"

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as e:
        return None, "WARN", f"Could not read manifest: {e}"

    chunks = manifest.get("chunks") or [
        s for s in manifest.get("segments", [])
        if s.get("type", "speech") == "speech"
    ]
    if not chunks:
        return None, "SKIP", "No chunk data in manifest -- WPM check skipped"

    total_words = sum(len(c.get("text", "").split()) for c in chunks)
    if total_words == 0:
        return None, "SKIP", "No text in manifest chunks"

    start_time = chunks[0].get("start_sec", chunks[0].get("start", 0))
    end_time   = chunks[-1].get("end_sec", chunks[-1].get("end",
                    chunks[-1].get("start_sec", chunks[-1].get("start", 0))))
    speech_dur_min = (end_time - start_time) / 60

    if speech_dur_min <= 0:
        return None, "SKIP", "Could not calculate speech duration from timestamps"

    wpm = total_words / speech_dur_min

    if wpm < WPM_FAIL_MIN:
        return wpm, "FAIL", (
            f"{wpm:.0f} WPM -- much too slow (range: {WPM_MIN:.0f}-{WPM_MAX:.0f}). "
            f"TTS is dragging. Regenerate."
        )
    if wpm > WPM_FAIL_MAX:
        return wpm, "FAIL", (
            f"{wpm:.0f} WPM -- much too fast (range: {WPM_MIN:.0f}-{WPM_MAX:.0f}). "
            f"TTS is rushing. Regenerate."
        )
    if wpm < WPM_MIN:
        return wpm, "WARN", f"{wpm:.0f} WPM -- slower than target (range: {WPM_MIN:.0f}-{WPM_MAX:.0f})"
    if wpm > WPM_MAX:
        return wpm, "WARN", f"{wpm:.0f} WPM -- faster than target (range: {WPM_MIN:.0f}-{WPM_MAX:.0f})"
    return wpm, "PASS", f"{wpm:.0f} WPM (range: {WPM_MIN:.0f}-{WPM_MAX:.0f})"


def check_clipping(audio_path: Path):
    """
    Detect audio clipping (samples at or above 0 dBFS).
    """
    _, stderr, _ = _ffmpeg_run([
        "-i", str(audio_path),
        "-af", "volumedetect",
        "-f", "null", "-",
    ])

    max_vol = None
    m = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", stderr)
    if m:
        max_vol = float(m.group(1))

    if max_vol is None:
        return None, "SKIP", "Could not detect peak level"

    if max_vol >= -1.0:
        return max_vol, "WARN", (
            f"Peak level {max_vol:.1f} dBFS -- near clipping. "
            f"Re-normalize before mixing."
        )
    return max_vol, "PASS", f"Peak {max_vol:.1f} dBFS (no clipping)"


def check_vocal_variation(audio_path: Path):
    """
    Check that vocal delivery varies across the narration (AP-RD-02).
    Measures RMS energy across chunks to detect monotone delivery.
    A varied performance has a wide RMS range; monotone is flat.
    """
    dur = _get_duration(audio_path)
    if not dur or dur < 60:
        return None, "SKIP", "Audio too short for variation analysis"

    # Split audio into 30-second chunks and measure RMS of each
    chunk_sec = 30
    num_chunks = int(dur / chunk_sec)
    if num_chunks < 3:
        chunk_sec = max(10, int(dur / 4))
        num_chunks = int(dur / chunk_sec)

    rms_values = []
    for i in range(min(num_chunks, 20)):
        start = i * chunk_sec
        _, stderr, rc = _ffmpeg_run([
            "-i", str(audio_path),
            "-ss", str(start),
            "-t", str(chunk_sec),
            "-af", "volumedetect",
            "-f", "null", "-",
        ])
        m = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", stderr)
        if m:
            rms_values.append(float(m.group(1)))

    if len(rms_values) < 3:
        return None, "SKIP", "Not enough chunks for variation analysis"

    rms_range = max(rms_values) - min(rms_values)
    rms_std = (sum((v - sum(rms_values) / len(rms_values)) ** 2 for v in rms_values) / len(rms_values)) ** 0.5

    if rms_range < VARIATION_WARN:
        return rms_range, "WARN", (
            f"RMS range {rms_range:.1f} dB across {len(rms_values)} chunks -- monotone delivery detected. "
            f"Vocal delivery must vary: louder for excitement, lower for suspense. (AP-RD-02)"
        )
    if rms_range < VARIATION_RMS_MIN:
        return rms_range, "WARN", (
            f"RMS range {rms_range:.1f} dB -- somewhat flat. "
            f"Consider more vocal variation between sections. (AP-RD-02)"
        )
    return rms_range, "PASS", f"RMS range {rms_range:.1f} dB across {len(rms_values)} chunks (good variation)"


def check_hallucination(audio_path: Path, alignment_path: Path = None):
    """
    Detect TTS hallucination: repeated phrases that F5-TTS injects.
    Uses Whisper alignment JSON if available, otherwise runs quick transcription.
    A hallucinating TTS will repeat the same phrase 5+ times across the narration.
    """
    sentences = []

    if alignment_path and alignment_path.exists():
        try:
            data = json.loads(alignment_path.read_text())
            sentences = [s["text"].strip().lower() for s in data.get("sentences", [])]
        except Exception:
            pass

    if not sentences:
        # No alignment — skip (Whisper would need to run which is slow)
        return None, "SKIP", "No alignment JSON — run narration_aligner first for hallucination check"

    # Check for repeated phrases (first 30 chars as key)
    phrase_counts = {}
    for text in sentences:
        key = text[:30]
        phrase_counts[key] = phrase_counts.get(key, 0) + 1

    # Find the most repeated phrase
    worst_phrase = max(phrase_counts.items(), key=lambda x: x[1])
    worst_count = worst_phrase[1]
    worst_text = worst_phrase[0]

    if worst_count >= 10:
        return worst_count, "FAIL", (
            f"HALLUCINATION: \"{worst_text}...\" repeated {worst_count} times. "
            f"F5-TTS injected a phantom phrase. MUST regenerate narration."
        )
    elif worst_count >= 5:
        return worst_count, "WARN", (
            f"Possible hallucination: \"{worst_text}...\" repeated {worst_count} times. "
            f"Check narration for unwanted repeated phrases."
        )
    return worst_count, "PASS", f"No hallucination detected (max repeat: {worst_count}x)"


# ── Output helpers ───────────────────────────────────────────────────────────

def print_check(name: str, status: str, message: str):
    c    = COLORS.get(status, RESET)
    icon = ICONS.get(status, "?")
    print(f"  {c}{icon}{RESET}  {name:<24}  {message}")
    return status


# ── Main ─────────────────────────────────────────────────────────────────────

def run_checks(audio_path: Path, script_path: Path | None, manifest_path: Path | None) -> list[str]:
    """Run all checks and return list of result strings."""
    results = []

    dur_sec, s, m = check_duration(audio_path, script_path)
    results.append(print_check("Duration / pace", s, m))

    _, s, m = check_loudness(audio_path)
    results.append(print_check("Loudness (LUFS)", s, m))

    _, s, m = check_silence_ratio(audio_path)
    results.append(print_check("Silence ratio", s, m))

    _, s, m = check_wpm(audio_path, manifest_path)
    results.append(print_check("Speech rate (WPM)", s, m))

    _, s, m = check_clipping(audio_path)
    results.append(print_check("Peak level", s, m))

    _, s, m = check_vocal_variation(audio_path)
    results.append(print_check("Vocal variation", s, m))

    # Hallucination check (requires alignment JSON from narration_aligner)
    alignment_path = audio_path.parent / "narration_alignment.json"
    _, s, m = check_hallucination(audio_path, alignment_path)
    results.append(print_check("Hallucination check", s, m))

    return results


def main():
    ap = argparse.ArgumentParser(description="LearnByLeo voice narration QA checker")
    ap.add_argument("audio",       help="Path to narration.wav")
    ap.add_argument("--script",    help="Path to enhanced script .txt (for duration/WPM comparison)")
    ap.add_argument("--manifest",  help="Path to narration_manifest.json (for WPM check)")
    args = ap.parse_args()

    audio = Path(args.audio)
    if not audio.exists():
        print(f"ERROR: {audio} not found", file=sys.stderr)
        sys.exit(1)

    script   = Path(args.script)   if args.script   else None
    manifest = Path(args.manifest) if args.manifest else None

    # Auto-detect manifest in same directory
    if manifest is None:
        candidate = audio.parent / "narration_manifest.json"
        if candidate.exists():
            manifest = candidate

    playbook = load_playbook()

    print(f"\n{BOLD}LearnByLeo Voice QA{RESET}  --  {audio.name}")
    if script:
        print(f"  Script:   {script}")
    if manifest:
        print(f"  Manifest: {manifest}")
    print()

    results = run_checks(audio, script, manifest)

    fails  = results.count("FAIL")
    warns  = results.count("WARN")
    passes = results.count("PASS")

    print()
    if fails:
        verdict = (f"{RED}{BOLD}FAIL{RESET}  --  {fails} critical issue(s). "
                   f"Regenerate narration before proceeding.")
        code = 1
    elif warns:
        verdict = (f"{YELLOW}{BOLD}WARN{RESET}  --  {passes} passed, {warns} warning(s). "
                   f"Acceptable -- proceed or regenerate.")
        code = 0
    else:
        verdict = f"{GREEN}{BOLD}PASS{RESET}  --  all {passes} checks passed. Good to proceed."
        code = 0

    print(f"Verdict: {verdict}\n")
    sys.exit(code)


if __name__ == "__main__":
    main()
