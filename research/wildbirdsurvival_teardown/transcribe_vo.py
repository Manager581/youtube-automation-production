#!/usr/bin/env python3
"""Transcribe the full EP02 VO with word-level timestamps and cache the result.

Split step is separate (split_vo_blocks.py) so a slow transcribe is never redone.
"""
import json
import sys
from pathlib import Path

import whisper

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
AUDIO = REPO / "audio/vampire_finch/ep02_vo_full_sp95_s74_sb75_m2.mp3"
OUT = ROOT / "ep02_vo_transcript_words.json"

MODEL = sys.argv[1] if len(sys.argv) > 1 else "small.en"


def main():
    print(f"loading whisper {MODEL} ...", flush=True)
    model = whisper.load_model(MODEL)
    print(f"transcribing {AUDIO.name} ...", flush=True)
    r = model.transcribe(str(AUDIO), fp16=False, word_timestamps=True,
                         language="en", verbose=False)
    words = []
    for seg in r["segments"]:
        for w in seg.get("words", []):
            words.append({
                "w": w["word"].strip(),
                "s": round(float(w["start"]), 3),
                "e": round(float(w["end"]), 3),
            })
    OUT.write_text(json.dumps({
        "model": MODEL,
        "audio": str(AUDIO.relative_to(REPO)),
        "text": r["text"].strip(),
        "words": words,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.name}: {len(words)} words, "
          f"last word ends {words[-1]['e'] if words else 0} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
