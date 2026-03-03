#!/usr/bin/env python3
"""
check_fern_voice.py — Automated voice narration QA checker.

Validates generated narration audio against Fern's measured spec BEFORE
committing to hours of footage sourcing and assembly. Catches F5-TTS issues
automatically so you don't have to listen unless something is wrong.

Fern voice benchmarks (measured from 3 reference videos):
  WPM:          138.7 (range: 120–160 acceptable)
  Duration:     ~1,800s (25 min) for ~4,200 word script
  Loudness:     -20 to -16 LUFS (voice-only track before mixing)
  Silence:      < 25% of total duration
  Clipping:     0 samples above -1 dBFS

Usage:
    python check_fern_voice.py audio/topic/narration.wav
    python check_fern_voice.py audio/topic/narration.wav \\
        --script scripts/enhanced_topic.txt \\
        --manifest audio/topic/narration_manifest.json

Exit code: 0 = PASS or WARN, 1 = FAIL (regeneration recommended).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ── Fern voice benchmarks ─────────────────────────────────────────────────────

WPM_TARGET      = 138.7
WPM_MIN         = 110.0   # warn below
WPM_MAX         = 170.0   # warn above
WPM_FAIL_MIN    = 90.0    # fail below (F5-TTS badly slowed)
WPM_FAIL_MAX    = 200.0   # fail above (F5-TTS badly sped up)

LUFS_LOW        = -28.0   # warn below (too quiet)
LUFS_HIGH       = -12.0   # warn above (too loud)
LUFS_FAIL_LOW   = -35.0   # fail — barely audible
LUFS_FAIL_HIGH  = -8.0    # fail — clipping risk after mixing

SILENCE_WARN    = 0.25    # warn if > 25% silence
SILENCE_FAIL    = 0.45    # fail if > 45% silence (F5-TTS stuttered)
SILENCE_DB      = -35     # threshold below which audio is considered silence

DUR_TOLERANCE   = 0.30    # ±30% from expected duration → WARN
DUR_FAIL        = 0.50    # ±50% → FAIL

# ── ANSI colors ───────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ICONS  = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗", "SKIP": "—"}
COLORS = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED, "SKIP": GRAY}


# ── ffprobe / ffmpeg helpers ──────────────────────────────────────────────────

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


# ── Individual checks ─────────────────────────────────────────────────────────

def check_duration(audio_path: Path, script_path: Path | None):
    """
    Check narration duration against expected from script word count.
    Expected = word_count / WPM_TARGET * 60 seconds (+ ~10% for pauses/breaths).
    """
    dur = _get_duration(audio_path)
    if dur is None:
        return None, "FAIL", "Could not read audio duration — is ffprobe installed?"

    m = dur / 60

    if script_path and script_path.exists():
        # Count words in script (strip control markers)
        text = script_path.read_text(encoding="utf-8", errors="ignore")
        clean = re.sub(r"\[PAUSE:[^\]]+\]|\[BEAT\]|\[BREATH\]|\[VOICE:[^\]]+\]", "", text)
        words = len(clean.split())
        expected_sec = (words / WPM_TARGET) * 60 * 1.12   # +12% for pauses/breaths
        expected_min = expected_sec / 60
        ratio = (dur - expected_sec) / expected_sec   # positive = longer than expected

        if abs(ratio) > DUR_FAIL:
            return dur, "FAIL", (
                f"{m:.1f} min (expected ~{expected_min:.1f} min for {words} words) — "
                f"{'too long' if ratio > 0 else 'too short'} by {abs(ratio):.0%}. "
                f"F5-TTS speed issue. Regenerate."
            )
        if abs(ratio) > DUR_TOLERANCE:
            return dur, "WARN", (
                f"{m:.1f} min (expected ~{expected_min:.1f} min for {words} words) — "
                f"{'slightly long' if ratio > 0 else 'slightly short'} ({abs(ratio):.0%} off)"
            )
        return dur, "PASS", f"{m:.1f} min ✓  (expected ~{expected_min:.1f} min, {words} words)"

    # No script — just check reasonable range for 20–35 min video
    if dur < 10 * 60:
        return dur, "FAIL", f"{m:.1f} min — suspiciously short. Narration likely incomplete."
    if dur > 45 * 60:
        return dur, "WARN", f"{m:.1f} min — very long. Verify script length."
    return dur, "PASS", f"{m:.1f} min (no script provided for comparison)"


def check_loudness(audio_path: Path):
    """
    Measure integrated LUFS loudness of the narration.
    Voice-only track should be around -20 to -16 LUFS before mixing.
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
        return None, "WARN", "Could not parse loudnorm output — check ffmpeg install"

    if lufs < LUFS_FAIL_LOW:
        return lufs, "FAIL", f"{lufs:.1f} LUFS — barely audible. Check audio_preprocessor output."
    if lufs > LUFS_FAIL_HIGH:
        return lufs, "FAIL", f"{lufs:.1f} LUFS — will clip after mixing. Re-normalize."
    if lufs < LUFS_LOW:
        return lufs, "WARN", f"{lufs:.1f} LUFS — quiet (target: -20 to -16 LUFS for voice)"
    if lufs > LUFS_HIGH:
        return lufs, "WARN", f"{lufs:.1f} LUFS — loud for voice-only track (target: -20 to -16)"
    return lufs, "PASS", f"{lufs:.1f} LUFS ✓  (good level for voice before mixing)"


def check_silence_ratio(audio_path: Path):
    """
    Detect excessive silence — F5-TTS sometimes adds long gaps between segments.
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

    # Parse silence_duration entries from ffmpeg output
    silence_durations = re.findall(r"silence_duration:\s*([\d.]+)", stderr)
    total_silence = sum(float(d) for d in silence_durations)
    ratio = total_silence / max(dur, 1)

    if ratio > SILENCE_FAIL:
        return ratio, "FAIL", (
            f"{ratio:.0%} silence ({total_silence:.0f}s of {dur/60:.1f} min) — "
            f"F5-TTS added excessive gaps. Regenerate or clean up silences."
        )
    if ratio > SILENCE_WARN:
        return ratio, "WARN", (
            f"{ratio:.0%} silence ({total_silence:.0f}s) — slightly high. "
            f"Pauses/breaths in script are normal; check for long gaps."
        )
    return ratio, "PASS", f"{ratio:.0%} silence ✓  ({total_silence:.0f}s total pauses)"


def check_wpm(audio_path: Path, manifest_path: Path | None):
    """
    Check speech rate (WPM) from narration manifest timestamps.
    Fern target: 138.7 WPM. Acceptable: 110–170 WPM.
    """
    if not manifest_path or not manifest_path.exists():
        return None, "SKIP", "No narration_manifest.json — WPM check skipped"

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as e:
        return None, "WARN", f"Could not read manifest: {e}"

    # Manifest may have word-level or chunk-level timestamps.
    # voice_generator writes "segments"; support both field names.
    chunks = manifest.get("chunks") or [
        s for s in manifest.get("segments", [])
        if s.get("type", "speech") == "speech"
    ]
    if not chunks:
        return None, "SKIP", "No chunk data in manifest — WPM check skipped"

    total_words = sum(len(c.get("text", "").split()) for c in chunks)
    if total_words == 0:
        return None, "SKIP", "No text in manifest chunks"

    # Duration from first to last chunk.
    # voice_generator writes "start_sec"/"end_sec"; support both timestamp formats.
    start_time = chunks[0].get("start_sec", chunks[0].get("start", 0))
    end_time   = chunks[-1].get("end_sec", chunks[-1].get("end",
                    chunks[-1].get("start_sec", chunks[-1].get("start", 0))))
    speech_dur_min = (end_time - start_time) / 60

    if speech_dur_min <= 0:
        return None, "SKIP", "Could not calculate speech duration from timestamps"

    wpm = total_words / speech_dur_min

    if wpm < WPM_FAIL_MIN:
        return wpm, "FAIL", (
            f"{wpm:.0f} WPM — much too slow (target: {WPM_TARGET} WPM). "
            f"F5-TTS is dragging. Regenerate."
        )
    if wpm > WPM_FAIL_MAX:
        return wpm, "FAIL", (
            f"{wpm:.0f} WPM — much too fast (target: {WPM_TARGET} WPM). "
            f"F5-TTS is rushing. Regenerate."
        )
    if wpm < WPM_MIN:
        return wpm, "WARN", f"{wpm:.0f} WPM — slower than Fern (target: {WPM_TARGET:.0f})"
    if wpm > WPM_MAX:
        return wpm, "WARN", f"{wpm:.0f} WPM — faster than Fern (target: {WPM_TARGET:.0f})"
    return wpm, "PASS", f"{wpm:.0f} WPM ✓  (Fern target: {WPM_TARGET:.0f} WPM)"


def check_clipping(audio_path: Path):
    """
    Detect audio clipping (samples at or above 0 dBFS).
    A clipped narration track sounds harsh after mixing.
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
            f"Peak level {max_vol:.1f} dBFS — near clipping. "
            f"Re-normalize before mixing."
        )
    return max_vol, "PASS", f"Peak {max_vol:.1f} dBFS ✓  (no clipping)"


# ── Output helpers ────────────────────────────────────────────────────────────

def print_check(name: str, status: str, message: str):
    c    = COLORS.get(status, RESET)
    icon = ICONS.get(status, "?")
    print(f"  {c}{icon}{RESET}  {name:<24}  {message}")
    return status


# ── Main ──────────────────────────────────────────────────────────────────────

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

    return results


def main():
    ap = argparse.ArgumentParser(description="Fern voice narration QA checker")
    ap.add_argument("audio",       help="Path to narration.wav")
    ap.add_argument("--script",    help="Path to enhanced script .txt (for duration/WPM comparison)")
    ap.add_argument("--manifest",  help="Path to narration_manifest.json (for WPM check)")
    args = ap.parse_args()

    audio = Path(args.audio)
    if not audio.exists():
        print(f"ERROR: {audio} not found", file=sys.stderr)
        sys.exit(1)

    # Auto-detect script and manifest in same directory
    script   = Path(args.script)   if args.script   else None
    manifest = Path(args.manifest) if args.manifest else None

    if manifest is None:
        candidate = audio.parent / "narration_manifest.json"
        if candidate.exists():
            manifest = candidate

    print(f"\n{BOLD}Fern Voice QA{RESET}  —  {audio.name}")
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
        verdict = (f"{RED}{BOLD}FAIL{RESET}  —  {fails} critical issue(s). "
                   f"Regenerate narration before proceeding.")
        code = 1
    elif warns:
        verdict = (f"{YELLOW}{BOLD}WARN{RESET}  —  {passes} passed, {warns} warning(s). "
                   f"Acceptable — proceed or regenerate.")
        code = 0
    else:
        verdict = f"{GREEN}{BOLD}PASS{RESET}  —  all {passes} checks passed. Good to proceed."
        code = 0

    print(f"Verdict: {verdict}\n")
    sys.exit(code)


if __name__ == "__main__":
    main()
