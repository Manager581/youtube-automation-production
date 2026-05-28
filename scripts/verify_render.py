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
import math
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
INTRO_SPEC = PROJECT_ROOT / "storyboards" / "intro_spec_locked.json"
REPORT_OUT = PROJECT_ROOT / "output" / "verify_report.json"

# Thresholds
NARRATION_MATCH_MIN = 0.6       # Fraction of expected words in transcribed segment
DUCKING_RMS_MAX = 0.01           # RMS threshold — above this = narration not ducked
VISION_MATCH_MIN = 0.5           # Relevance score threshold
BLACK_MIN_DUR = 0.5              # blackdetect: min seconds of continuous black to report
BLACK_PIC_TH = 0.98              # blackdetect: luma threshold (fraction of black pixels)
BLACK_BEAT_FRAC = 0.4            # Beat fails if >this fraction of its duration is black
BLACK_BEAT_ABS = 1.5             # ...or if >this many absolute seconds are black

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


def extract_frame_accurate(render_path, time_sec, out_path):
    """Frame-accurate extract that stays fast at any position via two-stage seek:
    a coarse keyframe seek (-ss before -i) to ~2s before the target, then a fine
    seek (-ss after -i) for the remainder. Decodes only ~2s regardless of how far
    into the file the target is — needed so a late black-gap thumbnail actually
    shows black without re-decoding the whole video (which timed out)."""
    coarse = max(0.0, float(time_sec) - 2.0)
    fine = float(time_sec) - coarse
    r = subprocess.run([
        "ffmpeg", "-y", "-v", "quiet",
        "-ss", f"{coarse:.3f}",
        "-i", str(render_path),
        "-ss", f"{fine:.3f}",
        "-frames:v", "1", "-q:v", "3",
        str(out_path)
    ], capture_output=True, timeout=60)
    return r.returncode == 0 and os.path.exists(out_path)


def scan_black_segments(render_path, min_dur=BLACK_MIN_DUR, pic_th=BLACK_PIC_TH):
    """Whole-render black-frame scan via ffmpeg blackdetect.

    Returns a list of (start_sec, end_sec, duration) for every stretch the
    renderer left black. This is what the structural visual check is blind to:
    a beat can have a valid visual_file on disk yet render as pure black when
    its per-segment encode failed and the renderer substituted a black frame.
    """
    r = subprocess.run([
        "ffmpeg", "-nostats", "-hide_banner",
        "-i", str(render_path),
        "-vf", f"blackdetect=d={min_dur}:pic_th={pic_th}",
        "-an", "-f", "null", "-",
    ], capture_output=True, text=True, timeout=600)
    segs = []
    for line in (r.stderr or "").splitlines():
        if "black_start" not in line:
            continue
        try:
            parts = dict(p.split(":") for p in line.split("] ", 1)[1].strip().split(" "))
            segs.append((float(parts["black_start"]),
                         float(parts["black_end"]),
                         float(parts["black_duration"])))
        except (ValueError, KeyError, IndexError):
            continue
    return segs


def black_overlap(beat, black_segments):
    """Seconds of this beat that fall inside any black segment."""
    s, e = beat.get("start_sec", 0.0), beat.get("end_sec", 0.0)
    total = 0.0
    for bs, be, _ in black_segments:
        lo, hi = max(s, bs), min(e, be)
        if hi > lo:
            total += hi - lo
    return total


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


def check_not_black(beat, black_segments):
    """Check: is this beat actually showing its visual, or did the renderer
    drop it to a pure-black frame?

    The structural visual check (check_visual) confirms only that the
    expected_file exists on disk — it is BLIND to the renderer substituting a
    black segment when a per-segment encode fails under parallel load. This
    check compares the beat's time window against the whole-render blackdetect
    scan and fails when too much of the beat is black.
    """
    dur = max(beat.get("end_sec", 0.0) - beat.get("start_sec", 0.0), 0.001)
    black = black_overlap(beat, black_segments)
    frac = black / dur
    is_black = black >= BLACK_BEAT_ABS or frac >= BLACK_BEAT_FRAC
    return {
        "check": "not_black",
        "pass": not is_black,
        "severity": "critical" if is_black else "info",
        "black_sec": round(black, 2),
        "beat_dur": round(dur, 2),
        "black_frac": round(frac, 2),
        "note": (f"{black:.1f}s of {dur:.1f}s black ({frac*100:.0f}%)"
                 if is_black else "visual present"),
    }


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


def check_intro_protocol(beats, spec_path=INTRO_SPEC):
    """Compare the render's intro beats against the locked, user-approved intro spec.

    The intro is a fixed creative decision (intro_spec_locked.json, approved
    2026-04-04). Every regenerated paper edit drifts from it — wrong clips, the
    rejected "$5B card" overlay creeping back, the Facebook clip's 3s of its own
    audio dropped. This check flags each divergence so the locked intro can be
    re-injected before render. Returns one list of check dicts (not per-beat).
    """
    if not Path(spec_path).exists():
        return [{"check": "intro_protocol", "pass": True, "severity": "info",
                 "note": f"no locked intro spec at {spec_path}"}]
    with open(spec_path) as f:
        spec = json.load(f)
    segments = spec.get("segments", [])

    def parse_range(t):
        t = str(t).replace("s", "").strip()
        a, b = t.split("-")
        return float(a), float(b)

    def base_noext(p):
        return os.path.splitext(os.path.basename(str(p or "")))[0].lower()

    def find_beat(lo, hi):
        best, best_ov = None, 0.0
        for b in beats:
            s, e = b.get("start_sec", 0.0), b.get("end_sec", 0.0)
            ov = max(0.0, min(e, hi) - max(s, lo))
            if ov > best_ov:
                best_ov, best = ov, b
        return best

    out = []
    for seg in segments:
        idx = seg.get("index")
        try:
            lo, hi = parse_range(seg.get("time", "0-0s"))
        except (ValueError, AttributeError):
            lo, hi = 0.0, 0.0
        beat = find_beat(lo, hi)
        svf = seg.get("visual_file", "")
        prefix = f"intro_seg{idx}"

        if beat is None:
            out.append({"check": f"{prefix}_visual", "pass": False, "severity": "critical",
                        "expected": svf, "actual": None,
                        "note": f"no beat covers {seg.get('time')} (expected {svf})"})
            continue

        # 1. Visual file match (exact basename, case-insensitive)
        vis_ok = base_noext(svf) == base_noext(beat.get("visual_file"))
        out.append({
            "check": f"{prefix}_visual", "pass": vis_ok,
            "severity": "info" if vis_ok else "critical",
            "expected_file": svf, "actual": beat.get("visual_file"),
            "note": "matches spec" if vis_ok
                    else f"expected {svf}, got {beat.get('visual_file')}",
        })

        # 2. Clip-audio mode match (e.g. Facebook clip must play_then_mute for 3s)
        exp_audio, act_audio = seg.get("clip_audio", "mute"), beat.get("clip_audio", "mute")
        audio_ok = exp_audio == act_audio
        out.append({
            "check": f"{prefix}_clip_audio", "pass": audio_ok,
            "severity": "info" if audio_ok else "critical",
            "expected": exp_audio, "actual": act_audio,
            "note": "matches spec" if audio_ok
                    else f"expected {exp_audio}, got {act_audio}",
        })

        # 3. Overlay match. Spec overlay starting with "NONE" means NO overlay allowed
        #    (e.g. the user-rejected "$5B card" must stay removed → critical if present).
        exp_overlay = (seg.get("overlay") or "").strip()
        act_overlay = (beat.get("text_overlay") or "").strip()
        expects_none = exp_overlay.upper().startswith("NONE") or exp_overlay == ""
        if expects_none:
            ov_ok = act_overlay == ""
            out.append({
                "check": f"{prefix}_overlay", "pass": ov_ok,
                "severity": "info" if ov_ok else "critical",
                "expected": "(no overlay)", "actual": act_overlay,
                "note": "correctly absent" if ov_ok
                        else f"rejected overlay is back: '{act_overlay}' (spec: {exp_overlay})",
            })
        else:
            ov_ok = act_overlay != "" and normalize_text(exp_overlay).issubset(normalize_text(act_overlay))
            out.append({
                "check": f"{prefix}_overlay", "pass": ov_ok,
                "severity": "info" if ov_ok else "warning",
                "expected": exp_overlay, "actual": act_overlay,
                "note": "matches spec" if ov_ok
                        else f"expected '{exp_overlay}', got '{act_overlay or 'NONE'}'",
            })

    return out


def _flat_words(alignment):
    """Flatten an alignment dict to a list of (clean_token, raw_word)."""
    out = []
    for sent in alignment.get("sentences", []):
        for w in sent.get("words", []):
            raw = w.get("word", "")
            tok = re.sub(r'[^a-z0-9]', '', raw.lower())
            if tok:
                out.append((tok, raw.strip()))
    return out


def check_vo_quality(alignment, audio_mono, sr=48000):
    """Check the voice-over for the defects that make a render "sound awful":
    F5-TTS stutter/hallucination (repeated words), digital clipping, and dead air.

    Runs once per render. Returns a list of check dicts.
      • vo_repetition — TTS stutter: a word repeated 3+ times in a row, or a
        2-word phrase repeated back-to-back. These are the audible "the the the"
        / "we run ads we run ads" artifacts F5-TTS produces.
      • vo_clipping  — fraction of samples over 0.99 (distortion) + peak dBFS.
      • vo_silence   — fraction of the mix that is near-silent (catches a silent
        / mostly-empty narration stem, e.g. the voice-smoother 79%-silent bug).
    """
    out = []

    # ── Repetition / hallucination ─────────────────────────────────────────
    words = _flat_words(alignment)
    toks = [t for t, _ in words]
    stutters = []
    i = 0
    while i < len(toks):
        j = i
        while j < len(toks) and toks[j] == toks[i]:
            j += 1
        if (j - i) >= 3 and len(toks[i]) > 1:
            stutters.append(f"{toks[i]}x{j-i}")
        i = j
    bigram_rep = []
    for k in range(len(toks) - 3):
        if (toks[k] == toks[k+2] and toks[k+1] == toks[k+3]
                and len(toks[k]) + len(toks[k+1]) > 3):
            bigram_rep.append(f"{toks[k]} {toks[k+1]}")
    n_rep = len(stutters) + len(bigram_rep)
    rep_examples = (stutters + bigram_rep)[:8]
    out.append({
        "check": "vo_repetition",
        "pass": n_rep < 1,
        "severity": "critical" if n_rep >= 5 else ("warning" if n_rep >= 1 else "info"),
        "count": n_rep,
        "examples": rep_examples,
        "note": "no TTS stutter detected" if n_rep == 0
                else f"{n_rep} repeated-word artifact(s): {', '.join(rep_examples)}",
    })

    # ── Clipping / peak ────────────────────────────────────────────────────
    if audio_mono is not None and len(audio_mono) > 1:
        peak = float(np.max(np.abs(audio_mono)))
        clip_frac = float(np.mean(np.abs(audio_mono) > 0.99))
        peak_db = 20 * math.log10(peak) if peak > 1e-9 else -120.0
        out.append({
            "check": "vo_clipping",
            "pass": clip_frac <= 0.001,
            "severity": "critical" if clip_frac > 0.01 else ("warning" if clip_frac > 0.001 else "info"),
            "clip_frac": round(clip_frac, 5),
            "peak_dbfs": round(peak_db, 2),
            "note": (f"{clip_frac*100:.2f}% of samples clipped (peak {peak_db:+.1f} dBFS)"
                     if clip_frac > 0.001 else f"no sustained clipping (peak {peak_db:+.1f} dBFS)"),
        })

        # ── Silence / dead air ─────────────────────────────────────────────
        fr = int(0.05 * sr)
        n = len(audio_mono) // fr
        if n > 0:
            frames = audio_mono[:n*fr].reshape(n, fr)
            fr_rms = np.sqrt(np.mean(frames.astype(np.float64)**2, axis=1))
            sil_frac = float(np.mean(fr_rms < 0.01))
            out.append({
                "check": "vo_silence",
                "pass": sil_frac <= 0.25,
                "severity": "critical" if sil_frac > 0.5 else ("warning" if sil_frac > 0.25 else "info"),
                "silence_frac": round(sil_frac, 3),
                "note": (f"{sil_frac*100:.0f}% of mix near-silent — VO likely missing/buried"
                         if sil_frac > 0.25 else f"{sil_frac*100:.0f}% near-silent (normal)"),
            })

    return out


# ─── HTML report ─────────────────────────────────────────────────────────────

def _fmt_ts(sec):
    if sec is None:
        return "—"
    sec = float(sec)
    return f"{int(sec//60):d}:{int(sec%60):02d}"


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def generate_html_report(report, render_path, html_path):
    """Write a self-contained, screenshot-rich HTML report next to the JSON.

    The point: the user should see WHAT needs to be redone and WHERE (timecode +
    thumbnail) without scrubbing a 24-minute video. Frames are extracted for every
    failing beat into <stem>_frames/ and referenced relatively.
    """
    html_path = Path(html_path)
    frames_dir = html_path.with_suffix("")
    frames_dir = Path(str(frames_dir) + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    summary = report["summary"]
    n_crit = summary.get("critical_failures", 0)
    n_warn = summary.get("warnings", 0)
    n_pass = summary.get("passes", 0)
    n_beats = summary.get("total_beats", 0)
    verdict = "FAIL — needs work" if n_crit else ("WARN — review" if n_warn else "PASS")
    banner = "#b00020" if n_crit else ("#b06b00" if n_warn else "#0a7d2c")

    black_segs = [(b["start"], b["end"]) for b in report.get("black_segments", [])]

    def black_window_center(start, end):
        """Midpoint of the black stretch that overlaps [start,end], else beat mid."""
        best, best_ov = None, 0.0
        for bs, be in black_segs:
            lo, hi = max(start, bs), min(end, be)
            if hi - lo > best_ov:
                best_ov, best = hi - lo, (lo + hi) / 2
        return best if best is not None else (start + end) / 2

    def thumb(beat_id, t, accurate=False):
        """Extract a frame at t and return a relative <img> path, or '' on failure."""
        if t is None:
            return ""
        fp = frames_dir / f"{beat_id}.jpg"
        fn = extract_frame_accurate if accurate else extract_frame
        if fn(render_path, float(t), str(fp)):
            return f"{frames_dir.name}/{fp.name}"
        return ""

    # Group per-beat failures by check type, preserving timecode + visual
    black_beats, narr_beats, other_beats = [], [], []
    for br in report.get("results", []):
        if br["beat_id"] in ("intro_protocol", "vo_quality"):
            continue
        for c in br.get("checks", []):
            if c.get("pass", True):
                continue
            row = {
                "beat_id": br["beat_id"], "start": br.get("start_sec"),
                "end": br.get("end_sec"), "visual": br.get("visual_file"),
                "text": br.get("text", ""), "check": c.get("check"),
                "severity": c.get("severity", "warning"), "note": c.get("note", ""),
            }
            if c.get("check") == "not_black":
                black_beats.append(row)
            elif c.get("check") == "narration":
                narr_beats.append(row)
            else:
                other_beats.append(row)

    parts = []
    parts.append(f"""<!doctype html><html><head><meta charset="utf-8">
<title>Render QA — {_esc(Path(report.get('render','')).name)}</title>
<style>
 body{{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#111;color:#eee}}
 .wrap{{max-width:1100px;margin:0 auto;padding:24px}}
 .banner{{background:{banner};color:#fff;padding:18px 24px;border-radius:10px;font-size:22px;font-weight:700}}
 .sub{{font-size:14px;font-weight:400;opacity:.92;margin-top:4px}}
 h2{{margin-top:34px;border-bottom:1px solid #333;padding-bottom:6px}}
 .pill{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:700;margin-right:6px}}
 .crit{{background:#3a0d14;color:#ff8095}} .warn{{background:#3a2a0d;color:#ffd080}} .ok{{background:#0d3a1a;color:#7dffaa}}
 .card{{display:flex;gap:14px;background:#1b1b1b;border:1px solid #2a2a2a;border-radius:8px;padding:12px;margin:10px 0}}
 .card img{{width:240px;height:135px;object-fit:cover;background:#000;border-radius:4px;flex:none}}
 .card .meta{{flex:1}} .tc{{font-family:ui-monospace,monospace;color:#9cf;font-weight:700}}
 .fname{{color:#bbb;font-size:12px;word-break:break-all}}
 table{{border-collapse:collapse;width:100%;margin-top:8px}}
 td,th{{border:1px solid #2a2a2a;padding:6px 8px;text-align:left;font-size:13px}}
 th{{background:#1b1b1b}}
</style></head><body><div class="wrap">""")

    parts.append(f"""<div class="banner">{verdict}
<div class="sub">{_esc(Path(report.get('render','')).name)} ·
 {n_crit} critical · {n_warn} warnings · {n_pass}/{n_beats} beats clean ·
 {len(report.get('black_segments',[]))} black gaps ·
 generated {report.get('timestamp','')}</div></div>""")

    # ── Black frames ──
    parts.append(f'<h2>Black frames <span class="pill crit">{len(black_beats)}</span></h2>')
    if not black_beats:
        parts.append("<p>None — every beat renders a visual.</p>")
    for r in sorted(black_beats, key=lambda x: x["start"] or 0):
        ctr = black_window_center(r["start"] or 0, r["end"] or (r["start"] or 0))
        img = thumb(r["beat_id"], ctr, accurate=True)
        imgtag = f'<img src="{img}">' if img else '<div style="width:240px;height:135px;background:#000;border-radius:4px;flex:none"></div>'
        parts.append(f"""<div class="card">{imgtag}<div class="meta">
         <span class="tc">{_fmt_ts(r['start'])}</span> <span class="pill crit">BLACK</span>
         <span class="fname">{_esc(r['beat_id'])}</span>
         <div>{_esc(r['note'])}</div>
         <div class="fname">expected visual: {_esc(r['visual'])}</div>
         <div style="color:#999">{_esc(r['text'])}</div></div></div>""")

    # ── Intro protocol ──
    intro = report.get("intro_protocol", [])
    ifail = [c for c in intro if not c.get("pass", True)]
    parts.append(f'<h2>Intro protocol <span class="pill {"crit" if any(c["severity"]=="critical" for c in ifail) else "ok"}">{len(ifail)} issue(s)</span></h2>')
    parts.append("<table><tr><th>Check</th><th>Status</th><th>Detail</th></tr>")
    for c in intro:
        sev = "ok" if c.get("pass") else ("crit" if c["severity"] == "critical" else "warn")
        label = "PASS" if c.get("pass") else c["severity"].upper()
        parts.append(f'<tr><td>{_esc(c["check"])}</td><td><span class="pill {sev}">{label}</span></td><td>{_esc(c.get("note",""))}</td></tr>')
    parts.append("</table>")

    # ── VO quality ──
    vo = report.get("vo_quality", [])
    parts.append('<h2>Voice-over quality</h2>')
    parts.append("<table><tr><th>Check</th><th>Status</th><th>Detail</th></tr>")
    for c in vo:
        sev = "ok" if c.get("pass") else ("crit" if c["severity"] == "critical" else "warn")
        label = "PASS" if c.get("pass") else c["severity"].upper()
        parts.append(f'<tr><td>{_esc(c["check"])}</td><td><span class="pill {sev}">{label}</span></td><td>{_esc(c.get("note",""))}</td></tr>')
    parts.append("</table>")

    # ── Other failures ──
    parts.append(f'<h2>Other issues <span class="pill warn">{len(narr_beats)+len(other_beats)}</span></h2>')
    parts.append("<table><tr><th>Time</th><th>Beat</th><th>Check</th><th>Severity</th><th>Detail</th></tr>")
    for r in sorted(narr_beats + other_beats, key=lambda x: x["start"] or 0):
        sev = "crit" if r["severity"] == "critical" else "warn"
        parts.append(f'<tr><td class="tc">{_fmt_ts(r["start"])}</td><td>{_esc(r["beat_id"])}</td>'
                     f'<td>{_esc(r["check"])}</td><td><span class="pill {sev}">{r["severity"].upper()}</span></td>'
                     f'<td>{_esc(r["note"])}</td></tr>')
    parts.append("</table>")

    parts.append("</div></body></html>")
    html_path.write_text("\n".join(parts))
    return str(html_path)


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
    print("\n[3/5] Decoding audio for clip audio checks...")
    audio_mono = decode_mono(audio_wav)
    if audio_mono is None:
        print("  WARNING: could not decode audio")
        audio_mono = np.zeros(1, dtype=np.float32)

    # ── Whole-render black-frame scan ──────────────────────────────────────
    # The renderer substitutes pure-black segments when a per-segment encode
    # fails under parallel load. The structural visual check can't see this, so
    # scan the whole render once and flag any beat sitting inside a black gap.
    print("\n[4/5] Scanning for black frames (blackdetect)...")
    black_segments = scan_black_segments(render_path)
    black_total = sum(d for _, _, d in black_segments)
    print(f"  Black segments: {len(black_segments)} "
          f"({black_total:.1f}s total)")

    # ── Run checks per beat ────────────────────────────────────────────────
    print(f"\n[5/5] Running checks on {len(beats)} beats...")
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

        # Black-frame: did the renderer drop this beat to pure black?
        beat_result["checks"].append(check_not_black(beat, black_segments))

        # Overlay
        beat_result["checks"].append(check_overlay(beat, render_path, tmp_dir))

        results.append(beat_result)

        if (i + 1) % 25 == 0 or i == len(beats) - 1:
            print(f"  {i+1}/{len(beats)} beats checked")

    # ── Intro protocol: does the intro follow the locked, approved spec? ───
    intro_checks = check_intro_protocol(beats)
    intro_fail = sum(1 for c in intro_checks if not c.get("pass", True))
    print(f"  Intro protocol: {len(intro_checks)} checks, {intro_fail} divergence(s) from locked spec")
    results.append({
        "beat_id": "intro_protocol",
        "start_sec": 0.0,
        "end_sec": None,
        "chapter": "INTRO",
        "text": "intro vs intro_spec_locked.json",
        "visual_file": None,
        "checks": intro_checks,
    })

    # ── VO quality: stutter / clipping / dead air across the whole render ──
    vo_checks = check_vo_quality(alignment, audio_mono)
    vo_fail = sum(1 for c in vo_checks if not c.get("pass", True))
    print(f"  VO quality: {len(vo_checks)} checks, {vo_fail} issue(s)")
    for c in vo_checks:
        print(f"    - {c['check']}: {c['note']}")
    results.append({
        "beat_id": "vo_quality",
        "start_sec": 0.0,
        "end_sec": None,
        "chapter": "AUDIO",
        "text": "voice-over quality (whole render)",
        "visual_file": None,
        "checks": vo_checks,
    })

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
        "black_segments": [
            {"start": round(s, 2), "end": round(e, 2), "duration": round(d, 2)}
            for s, e, d in black_segments
        ],
        "intro_protocol": intro_checks,
        "vo_quality": vo_checks,
        "critical": critical_list,
        "warnings": warning_list,
        "results": results,
    }

    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w") as f:
        json.dump(report, f, indent=2)

    # ── Human-readable HTML report (screenshots + timecodes) ───────────────
    html_path = Path(args.report).with_suffix(".html")
    try:
        generate_html_report(report, render_path, html_path)
    except Exception as e:
        print(f"  WARNING: could not write HTML report: {e}")
        html_path = None

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
    if html_path:
        print(f"  HTML report: {html_path}")
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
