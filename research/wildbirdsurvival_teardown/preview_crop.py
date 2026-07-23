#!/usr/bin/env python3
"""Render a candidate pre-crop of a seed so it can be LOOKED AT before use.

Grok i2v begins on the seed's frame 1, so the only way a shot gets a framing
tighter than its seed is to crop the seed FIRST and feed the crop. That is also
how 73 of the 88 shots get DISTINCT vantages out of only 25 stills -- without it,
the 21 shots sharing hero_still_A_booby_finch.png all render as the same wide shot.

  venv/bin/python research/wildbirdsurvival_teardown/preview_crop.py SEED.png x,y,w,h [OUT.png]

Prints the crop's upscale factor (how far it is being blown up to 1264x720) --
past ~2.5x the source goes visibly soft, which matters for a documentary look.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(REPO, "assets", "vampire_finch")
OUT_W, OUT_H = 1264, 720


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    seed = sys.argv[1]
    path = seed if os.path.isabs(seed) else os.path.join(ASSETS, seed)
    x, y, w, h = (int(float(v)) for v in sys.argv[2].split(","))
    out = sys.argv[3] if len(sys.argv) > 3 else "/tmp/_crop_preview.png"

    im = Image.open(path)
    if x < 0 or y < 0 or x + w > im.width or y + h > im.height:
        print(f"CROP OUTSIDE IMAGE: seed is {im.width}x{im.height}, "
              f"crop asks for x{x}-{x+w}, y{y}-{y+h}")
        return 1

    crop = im.crop((x, y, x + w, y + h))
    aspect = crop.width / crop.height
    upscale = OUT_W / crop.width
    crop.resize((OUT_W, OUT_H), Image.LANCZOS).save(out)

    print(f"seed      : {seed}  {im.width}x{im.height}")
    print(f"crop      : {x},{y},{w},{h}  ->  {crop.width}x{crop.height}")
    print(f"aspect    : {aspect:.3f}  (16:9 = 1.778){'  <-- OFF 16:9' if abs(aspect-1.778) > 0.05 else ''}")
    print(f"upscale   : {upscale:.2f}x to {OUT_W}x{OUT_H}"
          f"{'  <-- SOFT, past 2.5x' if upscale > 2.5 else ''}")
    print(f"wrote     : {out}   <- open this with Read and LOOK at it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
