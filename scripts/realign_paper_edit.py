#!/usr/bin/env python3
"""realign_paper_edit.py — fix beat timestamps using WhisperX forced alignment.

The original paper-edit-generator uses a sentence-count walker that drifts when
Whisper splits the narration into more sentences than the script has. WhisperX
forced alignment (wav2vec2 phoneme matching) gives ground-truth word-level
timings for the original script text. This script walks the paper-edit beats
through the aligned word stream and rewrites start_sec/end_sec.

Usage:
    venv/bin/python scripts/realign_paper_edit.py \\
        --paper-edit storyboards/breaking_law_paper_edit_v13c.json \\
        --alignment audio/breaking_law/narration_alignment_whisperx.json \\
        --output storyboards/breaking_law_paper_edit_v13d.json

Or generate the alignment on the fly:
    venv/bin/python scripts/realign_paper_edit.py \\
        --paper-edit storyboards/breaking_law_paper_edit_v13c.json \\
        --narration audio/breaking_law/narration.wav \\
        --script scripts/raw_breaking_law_v45.txt \\
        --output storyboards/breaking_law_paper_edit_v13d.json
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path


def normalize_word(w):
    """Lowercase, strip surrounding punctuation."""
    return w.lower().strip(" .,!?;:\"'—–-")


def beat_words(text):
    """Tokenize beat text after stripping markers."""
    text = re.sub(r"\[.*?\]", " ", text)
    return [normalize_word(w) for w in re.findall(r"[\w']+(?:-[\w']+)*", text) if w.strip()]


def run_forced_alignment(narration_path, script_path, device="cpu"):
    """Run WhisperX forced alignment, returning {words: [{word, start, end, score}, ...], duration_sec}."""
    import whisperx

    print(f"  loading wav2vec2 align model...")
    align_model, metadata = whisperx.load_align_model(language_code="en", device=device)

    audio = whisperx.load_audio(narration_path)
    duration_sec = len(audio) / 16000
    print(f"  audio: {duration_sec:.1f}s")

    with open(script_path) as f:
        raw = f.read()
    script = re.sub(r"\[.*?\]", " ", raw)
    script = re.sub(r"\s+", " ", script).strip()

    segments = [{"text": script, "start": 0.0, "end": duration_sec}]
    print(f"  forced-aligning {len(script.split())} words against {duration_sec:.0f}s audio...")
    t0 = time.time()
    result = whisperx.align(segments, align_model, metadata, audio, device,
                            return_char_alignments=False)
    print(f"  done in {time.time()-t0:.1f}s")

    words = [
        {"word": w["word"], "start": w.get("start"), "end": w.get("end"),
         "score": w.get("score")}
        for w in result.get("word_segments", [])
        if w.get("start") is not None
    ]
    return {
        "narration_path": narration_path,
        "model": "whisperx-wav2vec2",
        "duration_sec": duration_sec,
        "total_words": len(words),
        "avg_wpm": round(len(words) / duration_sec * 60, 1) if duration_sec else 0,
        "words": words,
    }


def realign_beats(beats, alignment, default_marker_dur=3.0):
    """Walk beats through the aligned word stream; rewrite start_sec/end_sec.

    Strategy per beat:
      1. Tokenize beat text (strip [BEAT]/[CHAPTER:]/[VOICE:] markers).
      2. Find first beat word in alignment starting at the cursor.
      3. Find last beat word similarly.
      4. start_sec = first match's start; end_sec = last match's end.
      5. Advance cursor to last match's index + 1.
      6. Beats with no spoken text (pure chapter markers) hold position
         and are time-stamped from the previous beat's end.

    Returns (realigned_beats, stats).
    """
    flat = [(normalize_word(w["word"]), w["start"], w["end"]) for w in alignment["words"]]
    n = len(flat)
    duration = float(alignment.get("duration_sec") or (flat[-1][2] if flat else 0))

    cursor = 0
    last_end = 0.0
    stats = {"realigned": 0, "marker": 0, "unmatched": 0}

    out = []
    for beat in beats:
        nb = dict(beat)  # shallow copy
        words = beat_words(beat.get("text", ""))

        if not words:
            # Chapter marker / pure structural beat — sit at last_end with default duration
            nb["start_sec"] = round(last_end, 3)
            nb["end_sec"] = round(min(last_end + default_marker_dur, duration), 3)
            nb["duration"] = round(nb["end_sec"] - nb["start_sec"], 3)
            stats["marker"] += 1
            out.append(nb)
            continue

        # Find first beat word in flat[cursor:]
        first_idx = None
        first_target = words[0]
        # Allow up to ~600 words (~3 min) ahead to absorb short script-only [BEAT]s
        search_end = min(cursor + 600, n)
        for i in range(cursor, search_end):
            if flat[i][0] == first_target:
                first_idx = i
                break
        # If first word didn't match (e.g. hyphenation differs), try second word
        if first_idx is None and len(words) > 1:
            for i in range(cursor, search_end):
                if flat[i][0] == words[1]:
                    first_idx = i
                    break

        if first_idx is None:
            # Cannot match — interpolate from last_end at avg WPM
            est = max(1.0, len(words) * 60 / float(alignment.get("avg_wpm") or 175))
            nb["start_sec"] = round(last_end, 3)
            nb["end_sec"] = round(min(last_end + est, duration), 3)
            nb["duration"] = round(nb["end_sec"] - nb["start_sec"], 3)
            stats["unmatched"] += 1
            out.append(nb)
            continue

        # Find last beat word starting from first_idx
        last_idx = first_idx
        last_target = words[-1]
        # Search a window proportional to beat length (1.5x word count)
        last_search_end = min(first_idx + max(15, int(len(words) * 1.5)), n)
        for i in range(min(first_idx + len(words) - 1, n - 1), last_search_end):
            if flat[i][0] == last_target:
                last_idx = i
                break
        if last_idx == first_idx and len(words) > 1:
            # Fallback: use first_idx + word count
            last_idx = min(first_idx + len(words) - 1, n - 1)

        nb["start_sec"] = round(flat[first_idx][1], 3)
        nb["end_sec"] = round(flat[last_idx][2], 3)
        nb["duration"] = round(nb["end_sec"] - nb["start_sec"], 3)

        # Word-anchored within-beat offsets (animatic chip overlays / event
        # SFX): when an entry carries "word", re-time its at/t from that
        # word's aligned start so pops stay on their words as the beat moves.
        span = flat[first_idx:last_idx + 1]

        def _word_start(anchor):
            tgt = normalize_word(anchor)
            for wd, ws, _ in span:
                if wd == tgt:
                    return ws
            return None

        for ov in nb.get("overlays") or []:
            wt = _word_start(ov["word"]) if ov.get("word") else None
            if wt is not None:
                win = (float(ov["until"]) - float(ov["at"])
                       if ov.get("until") is not None else None)
                ov["at"] = round(max(0.0, wt - nb["start_sec"]), 3)
                if win is not None:
                    ov["until"] = round(ov["at"] + win, 3)
        for ev in nb.get("events") or []:
            wt = _word_start(ev["word"]) if ev.get("word") else None
            if wt is not None:
                ev["t"] = round(max(0.0, wt - nb["start_sec"]), 3)

        last_end = nb["end_sec"]
        cursor = last_idx + 1
        stats["realigned"] += 1
        out.append(nb)

    # Stitch markers to next beat's start (so chapter card flows into next narration)
    for i, b in enumerate(out):
        words = beat_words(b.get("text", ""))
        if words:
            continue
        nxt = next((bb for bb in out[i+1:] if beat_words(bb.get("text", ""))), None)
        if nxt:
            b["end_sec"] = nxt["start_sec"]
            b["duration"] = round(b["end_sec"] - b["start_sec"], 3)

    return out, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-edit", required=True, help="Input paper edit JSON")
    ap.add_argument("--output", required=True, help="Output (realigned) paper edit JSON")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--alignment", help="Pre-computed WhisperX alignment JSON")
    g.add_argument("--narration", help="Path to narration WAV (will run alignment)")
    ap.add_argument("--script", help="Path to script text (required with --narration)")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "mps"])
    ap.add_argument("--stitch", action="store_true",
                    help="extend each beat through pauses to the next beat's "
                         "start (contiguous timeline, renderer assumption); "
                         "last beat extends to narration end")
    args = ap.parse_args()

    # Load or compute alignment
    if args.alignment:
        with open(args.alignment) as f:
            alignment = json.load(f)
        print(f"Loaded alignment: {alignment.get('total_words')} words, "
              f"{alignment.get('duration_sec'):.1f}s")
    else:
        if not args.script:
            print("ERROR: --script required with --narration", file=sys.stderr)
            sys.exit(2)
        print(f"Running WhisperX forced alignment...")
        alignment = run_forced_alignment(args.narration, args.script, args.device)

    # Load paper edit
    with open(args.paper_edit) as f:
        pe = json.load(f)
    beats = pe["beats"]
    print(f"Paper edit: {len(beats)} beats")

    # Realign
    new_beats, stats = realign_beats(beats, alignment)

    if args.stitch:
        if new_beats and new_beats[0]["start_sec"] > 0:
            new_beats[0]["start_sec"] = 0.0     # hold visual over lead-in silence
        for i in range(len(new_beats) - 1):
            new_beats[i]["end_sec"] = new_beats[i + 1]["start_sec"]
            new_beats[i]["duration"] = round(
                new_beats[i]["end_sec"] - new_beats[i]["start_sec"], 3)
        if new_beats:
            dur = float(alignment.get("duration_sec")
                        or new_beats[-1]["end_sec"])
            new_beats[-1]["end_sec"] = round(dur, 3)
            new_beats[-1]["duration"] = round(
                new_beats[-1]["end_sec"] - new_beats[-1]["start_sec"], 3)

    # Drift report
    drifts = []
    for old, new in zip(beats, new_beats):
        if old.get("start_sec") is not None and new.get("start_sec") is not None:
            drifts.append(abs(old["start_sec"] - new["start_sec"]))
    if drifts:
        big = sum(1 for d in drifts if d > 1.0)
        print(f"\nDrift summary:")
        print(f"  realigned:   {stats['realigned']}")
        print(f"  markers:     {stats['marker']}")
        print(f"  unmatched:   {stats['unmatched']}")
        print(f"  drift > 1s:  {big}/{len(drifts)} beats")
        print(f"  max drift:   {max(drifts):.1f}s")
        print(f"  mean drift:  {sum(drifts)/len(drifts):.1f}s")

    # Write
    pe["beats"] = new_beats
    pe.setdefault("stats", {})["realigned_with"] = "whisperx-wav2vec2"
    pe["stats"]["realign_stats"] = stats
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(pe, f, indent=2)
    print(f"\nWrote: {args.output}")


if __name__ == "__main__":
    main()
