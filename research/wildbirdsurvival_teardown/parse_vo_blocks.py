#!/usr/bin/env python3
"""Parse EP02_SCRIPT_LOCKED.md into the VO blocks ElevenLabs will actually speak.

Emits ep02_vo_blocks.json: one entry per timecoded segment with clean spoken text.
Strips markdown quoting, timecode stamps, stage directions and [SILENCE] beats,
because none of those are spoken -- feeding them to the voice would both cost
credits and put stray words in the render.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "EP02_SCRIPT_LOCKED.md"
OUT = ROOT / "ep02_vo_blocks.json"

TIMECODE = re.compile(r"\*\*\[(\d+):(\d\d)\]\*\*")
STAGE = re.compile(r"\*\([^)]*\)\*")           # *(over the 12-second hold)*
SILENCE = re.compile(r"\[?\s*(NEAR-)?SILENCE[^\]]*\]?", re.I)
BOLD_BRACKET = re.compile(r"\*\*\[[^\]]*\]\*\*")  # any leftover **[...]**


def clean(text: str) -> str:
    text = STAGE.sub(" ", text)
    text = BOLD_BRACKET.sub(" ", text)
    text = SILENCE.sub(" ", text)
    text = text.replace("**", "").replace("_", "")
    text = re.sub(r"\s+", " ", text).strip()
    # Drop only the dangling em-dashes left at a split point -- NEVER terminal
    # punctuation. Periods, question marks and the deliberate trailing ellipses
    # ("closest to the skin...") set the voice's falling intonation and pause;
    # stripping them would change prosody and invalidate the wpm measurement,
    # which was taken on fully punctuated text.
    text = re.sub(r"^[\s\-—·]+", "", text)
    text = re.sub(r"[\s\-—·]+$", "", text)
    if not re.search(r"[A-Za-z]", text):
        return ""
    # A block split off mid-sentence starts lowercase; it is now its own
    # utterance, so give it a capital.
    for i, ch in enumerate(text):
        if ch.isalpha():
            text = text[:i] + ch.upper() + text[i + 1:]
            break
    # Guarantee terminal punctuation so the voice lands the sentence.
    if not text.endswith((".", "!", "?", "…")):
        text += "."
    return text


def parse():
    lines = SCRIPT.read_text(encoding="utf-8").splitlines()
    blocks, act = [], None
    for raw in lines:
        if raw.startswith("### "):
            act = raw[4:].split("·")[0].strip()
            continue
        if not raw.startswith(">"):
            continue
        line = raw.lstrip("> ").rstrip()
        if not line or not TIMECODE.search(line):
            continue
        # split the line at each embedded timecode -> separate drop points
        parts = TIMECODE.split(line)
        # parts = [pre, mm, ss, text, mm, ss, text, ...]
        for i in range(1, len(parts), 3):
            mm, ss, body = int(parts[i]), int(parts[i + 1]), parts[i + 2]
            spoken = clean(body)
            if not spoken or not re.search(r"[A-Za-z]", spoken):
                continue  # pure pause / silence marker -> nothing to speak
            blocks.append({
                "act": act,
                "t": mm * 60 + ss,
                "timecode": f"{mm}:{ss:02d}",
                "text": spoken,
                "words": len([w for w in spoken.split() if re.search(r"[A-Za-z0-9]", w)]),
                "chars": len(spoken),
            })
    return blocks


def main():
    blocks = parse()
    total_words = sum(b["words"] for b in blocks)
    total_chars = sum(b["chars"] for b in blocks)
    # one blank line between blocks in the single pass
    joined = "\n\n".join(b["text"] for b in blocks)
    payload = {
        "source": "EP02_SCRIPT_LOCKED.md",
        "blocks": len(blocks),
        "total_words": total_words,
        "total_chars_blocks": total_chars,
        "single_pass_chars": len(joined),
        "speed": 0.95,
        "measured_wpm": 153.7,
        "predicted_speech_s": round(total_words / 153.7 * 60, 1),
        "runtime_s": 480,
        "predicted_coverage_pct": round(total_words / 153.7 * 60 / 480 * 100, 1),
        "blocks_detail": blocks,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "ep02_vo_single_pass.txt").write_text(joined, encoding="utf-8")

    print(f"blocks: {len(blocks)}")
    print(f"words:  {total_words}  (script ledger says 487)")
    print(f"chars:  {len(joined)} for the single pass -> {len(joined)} credits")
    print(f"speech @153.7 wpm: {payload['predicted_speech_s']} s "
          f"= {payload['predicted_coverage_pct']}% of 480 s")
    if len(joined) > 5000:
        print(f"!! EXCEEDS the 5,000-char box by {len(joined)-5000} - must split")
    else:
        print(f"fits the 5,000-char box with {5000-len(joined)} to spare")
    return 0


if __name__ == "__main__":
    sys.exit(main())
