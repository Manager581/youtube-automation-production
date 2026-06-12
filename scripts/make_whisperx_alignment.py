#!/usr/bin/env python3
"""Produce a WhisperX word-level alignment JSON for a narration WAV.

Thin wrapper around the canonical run_forced_alignment() in
realign_paper_edit.py (wav2vec2 forced alignment of the known script text to the
audio). Output matches the format the composite engine's ALIGN step + the
realign step both consume: {narration_path, model, duration_sec, total_words,
avg_wpm, words:[{word,start,end,score}]}.

Usage:
    venv/bin/python scripts/make_whisperx_alignment.py \
        --narration audio/spino_lagos/narration_11l_mark_full.wav \
        --script scripts/spino_lagos.txt \
        --out audio/spino_lagos/narration_11l_mark_whisperx.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from realign_paper_edit import run_forced_alignment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narration", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()

    result = run_forced_alignment(a.narration, a.script, device=a.device)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(result, f, indent=1)
    print(f"wrote {a.out}: {result['total_words']} words, "
          f"{result['avg_wpm']} wpm, {result['duration_sec']:.1f}s")


if __name__ == "__main__":
    main()
