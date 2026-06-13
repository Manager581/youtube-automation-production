#!/usr/bin/env python3
"""Cut out the foreground subject (creature) from a still → transparent PNG via rembg.

The composite engine (composite_beat.py) consumes pre-made cutout PNGs; this is the
helper that produces them. Reports alpha coverage %. For hard cases (macros,
reflections, water-merged edges) where rembg returns <~10% coverage, fall back to a
manual soft-mask (PIL ellipse + GaussianBlur) — see the c_glass_refl_cut history.

Usage:
    venv/bin/python scripts/make_cutout.py IN.png OUT.png [--model u2net] [--alpha-matting]
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from rembg import remove, new_session


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--model", default="u2net")
    ap.add_argument("--alpha-matting", action="store_true",
                    help="finer edges (slower); good for hair/water fringe")
    a = ap.parse_args()

    session = new_session(a.model)
    img = Image.open(a.inp).convert("RGBA")
    cut = remove(img, session=session, alpha_matting=a.alpha_matting)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cut.save(a.out)

    alpha = np.array(cut)[:, :, 3]
    cov = (alpha > 16).mean() * 100
    print(f"{a.out}: {cut.size}, alpha coverage {cov:.1f}%")
    if cov < 10:
        print("WARNING: <10% coverage — rembg likely failed; use the soft-mask fallback")


if __name__ == "__main__":
    main()
