#!/usr/bin/env python3
"""
tts_shootout_score.py — objective gate for TTS engine candidates.

Scores every candidate WAV in a directory against the reference passage text:
  - WER (ordered, number-canonicalized — catches F5-style hallucinated/repeated
    words and skipped sentences)
  - missing / extra content tokens (set diff, same normalization as the render
    watcher)
  - duration + words-per-minute
  - speaker similarity vs the owner's real-voice reference (only if resemblyzer
    is importable in the running venv; skipped otherwise)

Usage:
  venv/bin/python scripts/tts_shootout_score.py \
    --dir output/tts_shootout \
    --text output/tts_shootout/test_passage.txt \
    --owner-ref output/tts_shootout/owner_real_voice_energized.wav

Writes <dir>/scores.json and prints a table. Reference files whose names start
with "owner_real" are used only as similarity anchors, never scored.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_render import _canonicalize_numbers  # reuse watcher normalization


def norm_tokens(text):
    """Ordered token list, lowercased, punctuation stripped, numbers canonical."""
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace(",", "")
    return _canonicalize_numbers(re.findall(r"\w+", text.lower()))


def wer(ref, hyp):
    """Classic word error rate via edit distance on token lists."""
    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1):
        d[i][0] = i
    for j in range(len(hyp) + 1):
        d[0][j] = j
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d[-1][-1] / max(1, len(ref))


def transcribe(path, model):
    segs, _ = model.transcribe(str(path), language="en", beam_size=5)
    return " ".join(s.text for s in segs).strip()


def duration_sec(path):
    import soundfile as sf
    info = sf.info(str(path))
    return info.frames / info.samplerate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--owner-ref", default=None)
    ap.add_argument("--whisper-model", default="base")
    args = ap.parse_args()

    d = Path(args.dir)
    ref_text = Path(args.text).read_text()
    ref_tok = norm_tokens(ref_text)

    from faster_whisper import WhisperModel
    wm = WhisperModel(args.whisper_model, device="cpu", compute_type="int8")

    encoder = owner_emb = None
    if args.owner_ref:
        try:
            from resemblyzer import VoiceEncoder, preprocess_wav
            encoder = VoiceEncoder()
            owner_emb = encoder.embed_utterance(preprocess_wav(Path(args.owner_ref)))
        except ImportError:
            print("(resemblyzer not installed — skipping speaker similarity)")

    rows = []
    for wav in sorted(d.glob("*.wav")):
        if wav.name.startswith("owner_real"):
            continue
        hyp_text = transcribe(wav, wm)
        hyp_tok = norm_tokens(hyp_text)
        missing = set(ref_tok) - set(hyp_tok)
        extra = set(hyp_tok) - set(ref_tok)
        dur = duration_sec(wav)
        row = {
            "file": wav.name,
            "wer": round(wer(ref_tok, hyp_tok), 4),
            "missing_tokens": sorted(missing),
            "extra_tokens": sorted(extra),
            "duration_sec": round(dur, 2),
            "wpm": round(len(hyp_tok) / dur * 60, 1) if dur else 0,
        }
        if encoder is not None:
            from resemblyzer import preprocess_wav
            emb = encoder.embed_utterance(preprocess_wav(wav))
            row["speaker_sim_vs_owner"] = round(float(owner_emb @ emb), 4)
        rows.append(row)
        print(f"{wav.name}: WER={row['wer']:.3f} dur={row['duration_sec']}s "
              f"wpm={row['wpm']}"
              + (f" sim={row.get('speaker_sim_vs_owner')}" if encoder else "")
              + (f" missing={sorted(missing)[:6]}" if missing else "")
              + (f" extra={sorted(extra)[:6]}" if extra else ""))

    out = d / "scores.json"
    out.write_text(json.dumps({"reference_text": ref_text, "results": rows}, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
