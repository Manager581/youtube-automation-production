#!/usr/bin/env python3
"""Overlay pass for the Genesis v2 assembly (ledger step 5).

Burns in:
  - verse-reference lower-thirds during the 8 NKJV quote windows (whisperx-timed,
    +1.2s read-out tail, 0.4s alpha fades)
  - end attribution: NKJV copyright line + AI disclosure during the G051 settle

Usage:
  venv/bin/python scripts/genesis_overlay_pass.py \
      -i output/christ_cares_genesis_v2.mp4 -o output/christ_cares_genesis_v2_overlaid.mp4
"""
import argparse, os, subprocess

FONT = "/System/Library/Fonts/Helvetica.ttc"
# (label, start, end) — starts from whisperx quote windows, ends +1.2s read tail
REFS = [
    ("GENESIS 1:1 · NKJV",   0.3,   3.8),
    ("GENESIS 1:31 · NKJV",  51.8,  55.4),
    ("GENESIS 3:1 · NKJV",   67.7,  70.5),
    ("GENESIS 3:15 · NKJV",  87.3,  91.8),
    ("GENESIS 6:8 · NKJV",   124.1, 127.5),
    ("GENESIS 12:3 · NKJV",  161.6, 166.1),
    ("GENESIS 15:6 · NKJV",  178.1, 184.1),
    ("GENESIS 50:20 · NKJV", 225.0, 229.6),
]
ATTRIB = ("Scripture taken from the New King James Version (NKJV). Copyright 1982 "
          "by Thomas Nelson. Used by permission. All rights reserved.")
DISCLOSE = "Imagery is AI-generated."
CARD_START, CARD_END = 268.5, 274.3


def fade_alpha(st, et, d=0.4):
    return (f"if(lt(t\\,{st + d})\\,(t-{st})/{d}\\,"
            f"if(lt(t\\,{et - d})\\,1\\,({et}-t)/{d}))")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True)
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()

    filters = []
    for label, st, et in REFS:
        label = label.replace(":", "\\:")  # ffmpeg 8.0: colons break even quoted text
        filters.append(
            f"drawtext=fontfile={FONT}:text='{label}':fontsize=34:fontcolor=white:"
            f"alpha='{fade_alpha(st, et)}':x=84:y=h-150:"
            f"box=1:boxcolor=black@0.35:boxborderw=14:"
            f"enable='between(t\\,{st}\\,{et})'")
    filters.append(
        f"drawtext=fontfile={FONT}:text='{ATTRIB}':fontsize=22:fontcolor=white@0.85:"
        f"alpha='{fade_alpha(CARD_START, CARD_END, 0.6)}':x=(w-text_w)/2:y=h-118:"
        f"enable='between(t\\,{CARD_START}\\,{CARD_END})'")
    filters.append(
        f"drawtext=fontfile={FONT}:text='{DISCLOSE}':fontsize=22:fontcolor=white@0.85:"
        f"alpha='{fade_alpha(CARD_START, CARD_END, 0.6)}':x=(w-text_w)/2:y=h-84:"
        f"enable='between(t\\,{CARD_START}\\,{CARD_END})'")

    cmd = ["ffmpeg", "-y", "-v", "error", "-i", args.input,
           "-vf", ",".join(filters),
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "copy", args.output]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1500:])
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
