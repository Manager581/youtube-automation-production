#!/usr/bin/env python3
"""silence_inserter.py — insert narration silence at every play_then_mute clip-audio beat.

The renderer hard-mutes narration during play_then_mute windows. If narration has
spoken words in those windows, they get cut mid-utterance. This stage inserts
silence into narration.wav at each clip-audio beat's start so the renderer's
mute is a no-op on already-silent audio.

Effects:
  - narration.wav gets `clip_audio_duration + 0.3s` of silence inserted at each
    clip-audio beat's start position (orig timeline)
  - alignment word timestamps shift forward at each insert position
  - paper edit beats: clip-audio beats keep their start_sec (visual anchored to
    the new silence), end_sec extends by the inserted silence; non-clip beats
    shift by accumulated silence

Usage:
    venv/bin/python -m pipeline_v2.silence_inserter \\
        --paper-edit storyboards/breaking_law_paper_edit_v13d.json \\
        --alignment audio/breaking_law/narration_alignment_whisperx.json \\
        --narration audio/breaking_law/narration.wav \\
        --out-paper-edit storyboards/breaking_law_paper_edit_v13e.json \\
        --out-alignment audio/breaking_law/narration_alignment_padded.json \\
        --out-narration audio/breaking_law/narration_padded.wav
"""

import argparse
import json
import wave
from pathlib import Path

import numpy as np


SR = 24000  # narration.wav sample rate
FADE_BUFFER = 0.3  # seconds added to clip_audio_duration so narration doesn't bleed into the fade


def read_wav_mono(path):
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == SR, f"expected {SR} Hz, got {w.getframerate()}"
        assert w.getnchannels() == 1, "expected mono"
        n = w.getnframes()
        return np.frombuffer(w.readframes(n), dtype=np.int16)


def write_wav_mono(path, samples):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(samples.tobytes())


def collect_inserts(beats):
    """Return sorted [(orig_position_sec, silence_dur_sec)] for every play/play_then_mute beat."""
    inserts = []
    for b in beats:
        mode = b.get("clip_audio", "mute")
        if mode not in ("play", "play_then_mute"):
            continue
        dur = b.get("clip_audio_duration") or 0
        try:
            dur = float(dur)
        except (TypeError, ValueError):
            dur = 0
        if dur <= 0:
            continue
        pos = b.get("start_sec")
        if pos is None:
            continue
        inserts.append((float(pos), dur + FADE_BUFFER))
    inserts.sort()
    return inserts


def shift_at_or_before(orig_pos, inserts):
    """Sum of silence_dur for inserts whose orig_position <= orig_pos.
    Words/beats AT or AFTER an insert position move by the inserted silence.
    """
    return sum(d for p, d in inserts if p <= orig_pos)


def shift_strictly_before(orig_pos, inserts):
    """Sum of silence_dur for inserts STRICTLY before orig_pos.
    The clip-audio beat at the insert position itself stays anchored to that
    position — we don't add the silence-for-its-own-window to its start."""
    return sum(d for p, d in inserts if p < orig_pos)


def insert_silences_in_audio(audio, inserts):
    """Build new audio with silence inserted at each (orig_position, silence_dur).
    Inserts must be sorted by orig_position ascending. Inserts are applied to the
    ORIGINAL timeline so we walk back to front to keep slice indices valid.
    """
    new_audio = audio
    for pos_sec, dur_sec in reversed(inserts):
        pos_samples = int(round(pos_sec * SR))
        pos_samples = max(0, min(pos_samples, len(new_audio)))
        silence = np.zeros(int(round(dur_sec * SR)), dtype=new_audio.dtype)
        new_audio = np.concatenate([new_audio[:pos_samples], silence, new_audio[pos_samples:]])
    return new_audio


def shift_alignment(alignment, inserts):
    """Return alignment with word timestamps shifted by accumulated silence."""
    new_words = []
    for w in alignment.get("words", []):
        if w.get("start") is None or w.get("end") is None:
            new_words.append(w)
            continue
        shift = shift_at_or_before(w["start"], inserts)
        new_words.append({**w, "start": round(w["start"] + shift, 3),
                          "end": round(w["end"] + shift, 3)})
    new_align = dict(alignment)
    new_align["words"] = new_words
    if new_words:
        new_align["duration_sec"] = round(new_words[-1]["end"] + 0.5, 3)
    return new_align


def shift_beats(beats, inserts):
    """Return beats with start_sec/end_sec shifted.

    For clip-audio beats (the inserts): start_sec keeps its original timeline
    position plus shifts from PREVIOUS inserts (silence inserted strictly before
    this beat). end_sec gets the same baseline shift PLUS this beat's own silence
    PLUS any inserts that fall strictly inside this beat's [start, end] window.

    For non-clip-audio beats: start_sec and end_sec each shift by the cumulative
    silence inserted at or before that timestamp.
    """
    new_beats = []
    for b in beats:
        nb = dict(b)
        orig_start = b.get("start_sec")
        orig_end = b.get("end_sec")
        if orig_start is None:
            new_beats.append(nb)
            continue

        mode = b.get("clip_audio", "mute")

        if mode in ("play", "play_then_mute"):
            shift_before = shift_strictly_before(orig_start, inserts)
            # This beat's own silence
            own_silence = next((d for p, d in inserts if abs(p - orig_start) < 1e-6), 0.0)
            # Inserts that fall strictly between orig_start and orig_end (other beats inside)
            inner = sum(d for p, d in inserts if orig_start < p <= (orig_end or orig_start))
            nb["start_sec"] = round(orig_start + shift_before, 3)
            nb["end_sec"] = round((orig_end or orig_start) + shift_before + own_silence + inner, 3)
        else:
            shift_s = shift_at_or_before(orig_start, inserts)
            shift_e = shift_at_or_before(orig_end if orig_end is not None else orig_start, inserts)
            nb["start_sec"] = round(orig_start + shift_s, 3)
            if orig_end is not None:
                nb["end_sec"] = round(orig_end + shift_e, 3)

        if nb.get("end_sec") is not None and nb.get("start_sec") is not None:
            nb["duration"] = round(nb["end_sec"] - nb["start_sec"], 3)
        new_beats.append(nb)
    return new_beats


def main():
    ap = argparse.ArgumentParser(description="Insert narration silence at clip-audio beats")
    ap.add_argument("--paper-edit", required=True)
    ap.add_argument("--alignment", required=True)
    ap.add_argument("--narration", required=True)
    ap.add_argument("--out-paper-edit", required=True)
    ap.add_argument("--out-alignment", required=True)
    ap.add_argument("--out-narration", required=True)
    args = ap.parse_args()

    with open(args.paper_edit) as f:
        pe = json.load(f)
    with open(args.alignment) as f:
        alignment = json.load(f)

    print(f"Loaded paper edit: {len(pe['beats'])} beats")
    print(f"Loaded alignment:  {len(alignment.get('words', []))} words")

    audio = read_wav_mono(args.narration)
    print(f"Loaded narration:  {len(audio)/SR:.2f}s ({len(audio)} samples)")

    inserts = collect_inserts(pe["beats"])
    if not inserts:
        print("No clip-audio beats — nothing to insert.")
        return 0

    total_silence = sum(d for _, d in inserts)
    print(f"\n{len(inserts)} inserts (total silence: {total_silence:.2f}s)")
    for pos, dur in inserts[:5]:
        print(f"  at {pos:7.2f}s → +{dur:.2f}s silence")
    if len(inserts) > 5:
        print(f"  ... and {len(inserts) - 5} more")

    print("\nBuilding padded audio...")
    new_audio = insert_silences_in_audio(audio, inserts)
    print(f"  new duration: {len(new_audio)/SR:.2f}s "
          f"(+{(len(new_audio) - len(audio))/SR:.2f}s)")

    print("Shifting alignment...")
    new_alignment = shift_alignment(alignment, inserts)

    print("Shifting paper edit beats...")
    new_beats = shift_beats(pe["beats"], inserts)
    new_pe = dict(pe)
    new_pe["beats"] = new_beats
    new_pe.setdefault("stats", {})["silence_inserter"] = {
        "inserts": [{"orig_position": p, "silence_dur": d} for p, d in inserts],
        "total_silence_sec": round(total_silence, 3),
    }

    # Write outputs
    Path(args.out_paper_edit).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_alignment).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_narration).parent.mkdir(parents=True, exist_ok=True)

    write_wav_mono(args.out_narration, new_audio)
    with open(args.out_alignment, "w") as f:
        json.dump(new_alignment, f, indent=2)
    with open(args.out_paper_edit, "w") as f:
        json.dump(new_pe, f, indent=2)

    print(f"\nWrote:")
    print(f"  {args.out_narration}")
    print(f"  {args.out_alignment}")
    print(f"  {args.out_paper_edit}")

    # Quick sanity check: count words still inside any clip-audio window
    leaks = 0
    for b in new_beats:
        if b.get("clip_audio") not in ("play", "play_then_mute"):
            continue
        dur = b.get("clip_audio_duration") or 0
        try:
            dur = float(dur)
        except (TypeError, ValueError):
            dur = 0
        if dur <= 0:
            continue
        s, e = b["start_sec"], b["start_sec"] + dur
        for w in new_alignment["words"]:
            if w.get("start") is None:
                continue
            if w["start"] < e and w["end"] > s + 0.05:
                leaks += 1
                break
    print(f"\nSanity: {leaks}/{len(inserts)} clip-audio beats still have narration words in window")
    print(f"  (target: 0 — silence inserter eliminates clip-audio coverage failures)")


if __name__ == "__main__":
    main()
