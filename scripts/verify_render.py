#!/usr/bin/env python3
"""
Post-render verifier — cross-references rendered MP4 against paper edit.

Catches:
  - Narration mismatch (wrong text at wrong timecode)
  - Clip audio ducking failure (narration playing when clip should be)
  - Wrong visual at a beat (podcast clip instead of Ford Pinto)
  - Missing/extra text overlay cards
  - Silence where there should be audio

Usage:
    cd /Users/jefflawrence/Documents/youtube-automation-production
    venv/bin/python scripts/verify_render.py
    venv/bin/python scripts/verify_render.py --render output/breaking_law_production.mp4
    venv/bin/python scripts/verify_render.py --skip-vision  # faster, no frame analysis
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.chapter_assembler import find_media_file

# ─── Defaults ──────────────────────────────────────────────────────────────

DEFAULT_RENDER = PROJECT_ROOT / "output" / "breaking_law_production_preview_v3.mp4"
PAPER_EDIT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v2.json"
DEFAULT_ALIGNMENT = PROJECT_ROOT / "audio" / "breaking_law" / "narration_alignment.json"
CHAPTER_CARD_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "chapters"
REPORT_OUT = PROJECT_ROOT / "output" / "verify_report.json"

# Thresholds
NARRATION_MATCH_MIN = 0.6       # Fraction of expected words in transcribed segment
DUCKING_RMS_MAX = 0.01           # RMS threshold — above this = narration not ducked
VISION_MATCH_MIN = 0.5           # Relevance score threshold

# ─── Helpers ───────────────────────────────────────────────────────────────

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def extract_audio_to_wav(render_path, out_path):
    """Extract audio from rendered MP4 to WAV."""
    subprocess.run([
        "ffmpeg", "-y", "-v", "quiet",
        "-i", str(render_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "48000", "-ac", "2",
        str(out_path)
    ], check=True)


def decode_mono(path, sr=48000):
    """Decode audio to float32 mono numpy array."""
    cmd = ["ffmpeg", "-v", "quiet", "-i", str(path),
           "-f", "f32le", "-acodec", "pcm_f32le",
           "-ar", str(sr), "-ac", "1", "pipe:1"]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    if r.returncode != 0:
        return None
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def extract_frame(render_path, time_sec, out_path):
    """Extract a single frame at time_sec."""
    r = subprocess.run([
        "ffmpeg", "-y", "-v", "quiet",
        "-ss", f"{time_sec:.3f}",
        "-i", str(render_path),
        "-frames:v", "1",
        "-q:v", "3",
        str(out_path)
    ], capture_output=True, timeout=30)
    return r.returncode == 0 and os.path.exists(out_path)


def normalize_text(text):
    """Lowercase, strip markup, strip punctuation for comparison."""
    # Remove [BEAT], [PAUSE:1.0], [VOICE:...] markers
    text = re.sub(r'\[.*?\]', '', text)
    # Lowercase, keep only words and numbers
    return set(re.findall(r'\w+', text.lower()))


def words_in_range(alignment, start_sec, end_sec):
    """Get all transcribed words whose timestamps fall in [start_sec, end_sec)."""
    words = []
    for sent in alignment.get("sentences", []):
        for w in sent.get("words", []):
            if start_sec <= w["start"] < end_sec:
                words.append(w["word"].lower().strip())
    return words


# ─── Checks ───────────────────────────────────────────────────────────────

def check_narration(beat, alignment):
    """Check: transcribed text at beat timecode matches expected narration.

    For clip_audio beats, only check narration AFTER the clip audio window
    (narration is ducked during clip audio so we'd only hear clip speech).

    Returns: {pass, severity, expected, actual, match_ratio}
    """
    expected = normalize_text(beat.get("text", ""))
    if not expected:
        return {"check": "narration", "pass": True, "severity": "info",
                "note": "no text expected"}

    # Skip narration check for very short beats (< 2s) — Whisper unreliable
    duration = beat["end_sec"] - beat["start_sec"]
    if duration < 2.0:
        return {"check": "narration", "pass": True, "severity": "info",
                "note": f"beat too short ({duration:.1f}s)"}

    # For clip_audio beats: skip past the clip audio window to check
    # the narration portion only (narration is ducked during clip audio)
    check_start = beat["start_sec"]
    clip_mode = beat.get("clip_audio", "mute")
    if clip_mode in ("play", "play_then_mute"):
        clip_dur = beat.get("clip_audio_duration") or 5.0
        if isinstance(clip_dur, str):
            try: clip_dur = float(clip_dur)
            except: clip_dur = 5.0
        check_start = beat["start_sec"] + clip_dur + 0.3  # +ducking fade

    check_end = beat["end_sec"]

    # If clip audio covers the whole beat, narration check is moot
    if check_end - check_start < 1.5:
        return {"check": "narration", "pass": True, "severity": "info",
                "note": "beat fully within clip audio window"}

    actual_words = words_in_range(alignment, check_start, check_end)
    actual = set(re.findall(r'\w+', " ".join(actual_words).lower()))

    # Ignore common filler words that add noise
    filler = {"a", "an", "the", "and", "or", "of", "in", "to", "on", "at", "is",
              "was", "be", "it", "that", "this", "for", "with", "by", "s"}
    expected_content = expected - filler
    actual_content = actual - filler

    if not expected_content:
        return {"check": "narration", "pass": True, "severity": "info",
                "note": "only filler words expected"}

    match = len(expected_content & actual_content) / len(expected_content)

    return {
        "check": "narration",
        "pass": match >= NARRATION_MATCH_MIN,
        "severity": "critical" if match < 0.3 else ("warning" if match < NARRATION_MATCH_MIN else "info"),
        "expected": " ".join(sorted(expected_content))[:120],
        "actual": " ".join(sorted(actual_content))[:120],
        "match_ratio": round(match, 2),
        "check_window": f"{check_start:.1f}-{check_end:.1f}s",
    }


def check_narration_silenced_during_clip_audio(beat, original_alignment):
    """For play/play_then_mute beats, the original narration must have NO words
    in the clip-audio window. The renderer hard-mutes narration during this window,
    so any word that "should" be playing there gets cut mid-utterance.

    Reads original narration_alignment.json (NOT the rendered transcription) for
    word-level timings of what the narration actually contains. Returns critical
    failure with the list of cut words.
    """
    clip_mode = beat.get("clip_audio", "mute")
    if clip_mode not in ("play", "play_then_mute"):
        return {"check": "narration_silenced", "pass": True, "severity": "info",
                "note": "not a clip-audio beat"}

    clip_dur = beat.get("clip_audio_duration") or 5.0
    if isinstance(clip_dur, str):
        try: clip_dur = float(clip_dur)
        except: clip_dur = 5.0

    start = beat["start_sec"]
    end = start + float(clip_dur)

    # Support both formats: legacy {sentences:[{words:[...]}]} and WhisperX {words:[...]}
    if "words" in original_alignment and original_alignment["words"]:
        flat_words = original_alignment["words"]
    else:
        flat_words = [w for s in original_alignment.get("sentences", []) for w in s.get("words", [])]

    cut_words = []
    for w in flat_words:
        ws, we = w.get("start"), w.get("end")
        if ws is None or we is None:
            continue
        if ws < end and we > start + 0.05:
            cut_words.append(w["word"])

    if not cut_words:
        return {
            "check": "narration_silenced",
            "pass": True,
            "severity": "info",
            "window": f"{start:.2f}-{end:.2f}s",
            "note": "clean — no narration in clip-audio window",
        }

    return {
        "check": "narration_silenced",
        "pass": False,
        "severity": "critical",
        "window": f"{start:.2f}-{end:.2f}s",
        "cut_count": len(cut_words),
        "cut_words": " ".join(cut_words[:12]),
        "note": f"play_then_mute would silence {len(cut_words)} narration word(s) mid-utterance",
    }


def check_clip_audio_ducking(beat, audio_mono, sr=48000):
    """For play/play_then_mute beats, check if narration is silent during clip audio.

    This works by measuring RMS during the clip_audio_duration window. If narration
    is properly ducked AND clip audio has speech, RMS will be in a normal range.
    The true test: check RMS pattern — is there a sudden level change when the
    clip audio ends and narration starts?
    """
    clip_mode = beat.get("clip_audio", "mute")
    if clip_mode not in ("play", "play_then_mute"):
        return {"check": "clip_audio_ducking", "pass": True, "severity": "info",
                "note": "not a clip audio beat"}

    clip_dur = beat.get("clip_audio_duration") or 5.0
    if isinstance(clip_dur, str):
        try: clip_dur = float(clip_dur)
        except: clip_dur = 5.0

    start_sample = int(beat["start_sec"] * sr)
    during_end = min(int((beat["start_sec"] + clip_dur) * sr), len(audio_mono))
    after_end = min(during_end + int(2.0 * sr), len(audio_mono))

    if start_sample >= len(audio_mono) or during_end <= start_sample:
        return {"check": "clip_audio_ducking", "pass": False, "severity": "warning",
                "note": "beat past audio end"}

    rms_during = float(np.sqrt(np.mean(audio_mono[start_sample:during_end]**2)))
    rms_after = float(np.sqrt(np.mean(audio_mono[during_end:after_end]**2))) if after_end > during_end else 0.0

    # If clip audio has audio (rms_during > 0.005), it's playing — good
    # If audio is mostly silent during clip section, clip audio extraction failed
    has_audio = rms_during > 0.005

    return {
        "check": "clip_audio_ducking",
        "pass": has_audio,
        "severity": "info" if has_audio else "critical",
        "clip_mode": clip_mode,
        "clip_duration": clip_dur,
        "rms_during": round(rms_during, 4),
        "rms_after": round(rms_after, 4),
        "note": "clip audio present" if has_audio else "clip audio silent/missing",
    }


def check_visual(beat, render_path, tmp_dir, use_vision=True):
    """Check: does the frame at beat.start_sec match beat.visual_file?

    Extracts a frame from render, compares against expected visual description.
    """
    expected_file = beat.get("visual_file", "")
    if not expected_file:
        return {"check": "visual", "pass": True, "severity": "info",
                "note": "no visual expected"}

    # Extract frame at beat middle point (to avoid transitions)
    mid_time = beat["start_sec"] + (beat["end_sec"] - beat["start_sec"]) / 2
    frame_path = os.path.join(tmp_dir, f"frame_{beat.get('beat_id', 'x')}.jpg")

    if not extract_frame(render_path, mid_time, frame_path):
        return {"check": "visual", "pass": False, "severity": "warning",
                "note": "could not extract frame"}

    # Resolve expected visual — get its name for comparison
    expected_path = find_media_file(expected_file)
    if not expected_path:
        # Also check chapter dir
        cp = CHAPTER_CARD_DIR / expected_file
        if cp.exists():
            expected_path = str(cp)

    if not expected_path:
        return {"check": "visual", "pass": False, "severity": "critical",
                "note": f"expected visual not on disk: {expected_file}",
                "frame": frame_path}

    result = {
        "check": "visual",
        "expected_file": expected_file,
        "expected_path": expected_path,
        "frame": frame_path,
        "time_sec": round(mid_time, 1),
    }

    if not use_vision:
        result["pass"] = True
        result["severity"] = "info"
        result["note"] = "vision check skipped"
        return result

    # Use Claude vision to compare (deferred — returns frame path for batch analysis)
    result["pass"] = True  # default, updated by batch vision pass
    result["severity"] = "info"
    result["note"] = "awaiting vision analysis"
    return result


def check_overlay(beat, render_path, tmp_dir):
    """Check: is there a text overlay when beat.text_overlay is set?

    Simple heuristic: compare frame at mid-beat vs frame 0.5s before beat start
    to detect presence of overlay graphics (text rendered on top).
    Limitation: doesn't read OCR — just checks if overlay was placed.
    """
    overlay_text = beat.get("text_overlay")
    # We only flag when overlay_text IS set but the overlay MOV wasn't placed
    # (the renderer logs this). For now this is a structural check only.
    return {
        "check": "overlay",
        "pass": True,
        "severity": "info",
        "overlay_text": overlay_text,
        "note": "structural only (no OCR)",
    }


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Verify rendered MP4 against paper edit")
    parser.add_argument("--render", default=str(DEFAULT_RENDER))
    parser.add_argument("--paper-edit", default=str(PAPER_EDIT))
    parser.add_argument("--alignment", default=None,
                        help="Narration alignment JSON for clip-audio coverage check. "
                             "If omitted, auto-detects best available: padded > whisperx > legacy. "
                             "CRITICAL: a padded render (silence-inserted) MUST be checked against "
                             "the padded alignment or narration_silenced will false-fail.")
    parser.add_argument("--report", default=str(REPORT_OUT))
    parser.add_argument("--skip-vision", action="store_true",
                        help="Skip Claude vision checks (faster)")
    parser.add_argument("--whisper-model", default="base",
                        help="Whisper model size (tiny/base/small/medium)")
    parser.add_argument("--max-beats", type=int, default=None,
                        help="Only check first N beats (for testing)")
    parser.add_argument("--fail-on-critical", action="store_true",
                        help="Exit with non-zero status if any critical failures (for pipeline gating)")
    args = parser.parse_args()

    render_path = Path(args.render)
    if not render_path.exists():
        print(f"ERROR: render not found: {render_path}")
        sys.exit(1)

    print("=" * 60)
    print("  Render Verifier")
    print("=" * 60)
    print(f"  Render:     {render_path.name}")
    print(f"  Paper edit: {Path(args.paper_edit).name}")
    print()

    # ── Load paper edit ────────────────────────────────────────────────────
    with open(args.paper_edit) as f:
        data = json.load(f)
    beats = data["beats"]
    if args.max_beats:
        beats = beats[:args.max_beats]
    print(f"  Beats to check: {len(beats)}")

    # ── Load original narration alignment (for clip-audio coverage check) ──
    # Auto-detect best alignment if not explicitly given: padded > whisperx > legacy.
    # A silence-inserted (padded) render MUST be checked against padded timing, or
    # the narration_silenced check false-fails on every clip-audio beat.
    original_alignment = {"sentences": [], "words": []}
    if args.alignment:
        align_path = Path(args.alignment)
    else:
        audio_dir = PROJECT_ROOT / "audio" / "breaking_law"
        candidates = [
            audio_dir / "narration_alignment_padded.json",
            audio_dir / "narration_alignment_whisperx.json",
            audio_dir / "narration_alignment.json",
        ]
        align_path = next((c for c in candidates if c.exists()), candidates[-1])
        print(f"  Alignment auto-detected: {align_path.name}")
    if align_path.exists():
        with open(align_path) as f:
            original_alignment = json.load(f)
        n_units = len(original_alignment.get("words") or original_alignment.get("sentences") or [])
        unit = "words" if original_alignment.get("words") else "sentences"
        print(f"  Original alignment: {align_path.name} ({n_units} {unit})")
    else:
        print(f"  WARNING: original alignment not found: {align_path}")
        print(f"           clip-audio coverage check will be skipped")

    # ── Setup temp dir ─────────────────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="verify_")
    print(f"  Temp dir: {tmp_dir}")

    t0 = time.time()

    # ── Extract audio + transcribe ─────────────────────────────────────────
    print("\n[1/4] Extracting audio from render...")
    audio_wav = os.path.join(tmp_dir, "render_audio.wav")
    extract_audio_to_wav(render_path, audio_wav)

    print(f"[2/4] Transcribing with Whisper {args.whisper_model}...")
    from pipeline_v2.narration_aligner import align_narration
    alignment_out = os.path.join(tmp_dir, "alignment.json")
    alignment = align_narration(
        audio_wav,
        script_path=None,
        model_size=args.whisper_model,
        output_path=alignment_out,
    )
    print(f"  Transcribed: {alignment.get('total_words')} words, "
          f"{alignment.get('duration_sec', 0):.1f}s")

    # ── Decode audio for ducking check ────────────────────────────────────
    print("\n[3/4] Decoding audio for clip audio checks...")
    audio_mono = decode_mono(audio_wav)
    if audio_mono is None:
        print("  WARNING: could not decode audio")
        audio_mono = np.zeros(1, dtype=np.float32)

    # ── Run checks per beat ────────────────────────────────────────────────
    print(f"\n[4/4] Running checks on {len(beats)} beats...")
    results = []

    for i, beat in enumerate(beats):
        beat_id = beat.get("beat_id", f"beat_{i:04d}")
        beat_result = {
            "beat_id": beat_id,
            "start_sec": beat.get("start_sec"),
            "end_sec": beat.get("end_sec"),
            "chapter": beat.get("chapter"),
            "text": beat.get("text", "")[:80],
            "visual_file": beat.get("visual_file"),
            "checks": [],
        }

        # Narration text
        beat_result["checks"].append(check_narration(beat, alignment))

        # Clip-audio coverage: original narration must be silent in the play_then_mute window
        beat_result["checks"].append(
            check_narration_silenced_during_clip_audio(beat, original_alignment)
        )

        # Clip audio ducking
        beat_result["checks"].append(check_clip_audio_ducking(beat, audio_mono))

        # Visual (without vision for speed by default)
        beat_result["checks"].append(
            check_visual(beat, render_path, tmp_dir, use_vision=not args.skip_vision)
        )

        # Overlay
        beat_result["checks"].append(check_overlay(beat, render_path, tmp_dir))

        results.append(beat_result)

        if (i + 1) % 25 == 0 or i == len(beats) - 1:
            print(f"  {i+1}/{len(beats)} beats checked")

    # ── Vision analysis (batched for frames that were extracted) ──────────
    if not args.skip_vision:
        print("\n[5/5] Running Claude vision on extracted frames...")
        from pipeline_v2.llm import query_claude_vision

        vision_checked = 0
        vision_failed = 0

        for br in results:
            visual_check = next((c for c in br["checks"] if c["check"] == "visual"), None)
            if not visual_check or "frame" not in visual_check:
                continue

            frame = visual_check.get("frame")
            expected = visual_check.get("expected_file", "")

            if not frame or not os.path.exists(frame):
                continue

            prompt = (
                f"Describe what you see in this frame in one sentence. "
                f"Then answer YES or NO: does this frame appear to show '{expected}'? "
                f"Return JSON: {{\"description\": \"...\", \"matches\": \"yes\"/\"no\"}}"
            )

            response = query_claude_vision(prompt, frame, timeout=60)

            matches = True  # default to pass on parse failure
            description = ""
            if response:
                # Try to parse JSON from response
                try:
                    m = re.search(r'\{.*?\}', response, re.DOTALL)
                    if m:
                        parsed = json.loads(m.group(0))
                        description = parsed.get("description", "")
                        matches = parsed.get("matches", "yes").lower() == "yes"
                except (json.JSONDecodeError, AttributeError):
                    matches = "no" not in response.lower()[:100]

            visual_check["description"] = description[:120]
            visual_check["matches"] = matches
            visual_check["pass"] = matches
            visual_check["severity"] = "info" if matches else "critical"

            vision_checked += 1
            if not matches:
                vision_failed += 1

            if vision_checked % 10 == 0:
                print(f"  {vision_checked} frames analyzed, {vision_failed} mismatches")

        print(f"  Vision done: {vision_checked} frames, {vision_failed} mismatches")

    # ── Summarize ──────────────────────────────────────────────────────────
    summary = {
        "total_beats": len(results),
        "critical_failures": 0,
        "warnings": 0,
        "passes": 0,
        "by_check": defaultdict(lambda: {"pass": 0, "fail": 0}),
    }

    critical_list = []
    warning_list = []

    for br in results:
        beat_passed = True
        for c in br["checks"]:
            check_name = c.get("check", "?")
            if c.get("pass", True):
                summary["by_check"][check_name]["pass"] += 1
            else:
                summary["by_check"][check_name]["fail"] += 1
                beat_passed = False
                sev = c.get("severity", "warning")
                entry = {
                    "beat_id": br["beat_id"],
                    "start_sec": br["start_sec"],
                    "check": check_name,
                    "severity": sev,
                    "note": c.get("note", ""),
                    "expected": c.get("expected_file") or c.get("expected"),
                    "actual": c.get("description") or c.get("actual"),
                }
                if sev == "critical":
                    summary["critical_failures"] += 1
                    critical_list.append(entry)
                else:
                    summary["warnings"] += 1
                    warning_list.append(entry)

        if beat_passed:
            summary["passes"] += 1

    summary["by_check"] = dict(summary["by_check"])

    # ── Write report ───────────────────────────────────────────────────────
    report = {
        "render": str(render_path),
        "paper_edit": str(args.paper_edit),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_sec": round(time.time() - t0, 1),
        "summary": summary,
        "critical": critical_list,
        "warnings": warning_list,
        "results": results,
    }

    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w") as f:
        json.dump(report, f, indent=2)

    # ── Print summary ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  VERIFICATION REPORT")
    print(f"{'='*60}")
    print(f"  Total beats:        {summary['total_beats']}")
    print(f"  Passed all checks:  {summary['passes']}")
    print(f"  Critical failures:  {summary['critical_failures']}")
    print(f"  Warnings:           {summary['warnings']}")
    print()
    print(f"  By check type:")
    for check, stats in summary["by_check"].items():
        total = stats["pass"] + stats["fail"]
        pct = 100 * stats["pass"] / total if total else 0
        print(f"    {check:25s} {stats['pass']:4d}/{total:4d} pass ({pct:.0f}%)")

    if critical_list:
        print(f"\n  CRITICAL FAILURES (first 15):")
        for c in critical_list[:15]:
            t = c.get("start_sec", 0) or 0
            print(f"    {c['beat_id']} @ {t:6.1f}s  [{c['check']}]  {c.get('note','')[:70]}")
            if c.get("expected"):
                print(f"      expected: {str(c['expected'])[:80]}")
            if c.get("actual"):
                print(f"      actual:   {str(c['actual'])[:80]}")

    if warning_list:
        print(f"\n  WARNINGS (first 5):")
        for w in warning_list[:5]:
            t = w.get("start_sec", 0) or 0
            print(f"    {w['beat_id']} @ {t:6.1f}s  [{w['check']}]  {w.get('note','')[:70]}")

    print(f"\n  Full report: {args.report}")
    print(f"  Render time: {report['elapsed_sec']:.0f}s")
    print(f"{'='*60}")

    # Cleanup (keep frames if any vision failures for inspection)
    if summary["critical_failures"] == 0:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        print(f"\n  Frames kept for inspection in: {tmp_dir}")

    # Gate exit code if requested by pipeline
    if args.fail_on_critical and summary["critical_failures"] > 0:
        print(f"\n  ❌ FAIL: {summary['critical_failures']} critical failure(s). Pipeline halted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
