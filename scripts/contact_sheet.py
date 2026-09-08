#!/usr/bin/env python3
"""contact_sheet.py — labeled grid of images (gate review artifact: seed masters, act frames).
Usage: contact_sheet.py OUT.jpg IMG1 IMG2 ... [--cols 6] [--tile 320] [--labels a,b,c]"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("images", nargs="+"); ap.add_argument("--cols", type=int, default=6); ap.add_argument("--tile", type=int, default=320); ap.add_argument("--labels")
    a = ap.parse_args(); labels = a.labels.split(",") if a.labels else [os.path.splitext(os.path.basename(p))[0] for p in a.images]
    try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    except Exception: font = ImageFont.load_default()
    T, LH = a.tile, 26; rows = (len(a.images) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * T, rows * (T * 9 // 16 + LH)), (18, 18, 22)); d = ImageDraw.Draw(sheet)
    for i, p in enumerate(a.images):
        try: im = Image.open(p).convert("RGB")
        except Exception: im = Image.new("RGB", (T, T * 9 // 16), (90, 20, 20))
        im.thumbnail((T, T * 9 // 16)); x, y = (i % a.cols) * T, (i // a.cols) * (T * 9 // 16 + LH)
        sheet.paste(im, (x + (T - im.width) // 2, y)); d.text((x + 6, y + T * 9 // 16 + 4), labels[i][:38], fill=(235, 235, 235), font=font)
    sheet.save(a.out, quality=88); print(f"{a.out}: {len(a.images)} tiles, {sheet.size}")
if __name__ == "__main__": main()
