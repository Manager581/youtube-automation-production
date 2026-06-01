#!/usr/bin/env python3
"""Regenerate text-overlay MOVs as ProRes 4444 with a TRANSPARENT background.

Matches the existing "tw_" house style: white uppercase serif (Georgia),
horizontally centered, subtle drop shadow, alpha fade in/out. Long strings
wrap to fit and shrink only if a single word overflows.

WHY this exists: the original generator that produced
assets/breaking_law/overlays/tw_*.mov is no longer in the repo, and 13 of
those files were evicted to iCloud (dataless) and cannot be read locally.
The other 37 were repaired in place by deriving alpha from luma. This script
rebuilds the missing ones from their authoritative paper-edit text.
"""
import os
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

OVERLAY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "breaking_law", "overlays",
)
FONT = "/System/Library/Fonts/Supplemental/Georgia.ttf"
W, H, FPS, DUR = 1920, 1080, 24, 3.0
FADE = 0.3
MAX_W = 1600          # text must fit within this width
Y_CENTER = int(H * 0.46)
LINE_GAP = 1.25       # multiple of line height

# filename stem -> exact on-screen text (recovered from _OVERLAY_MANUAL +
# paper edit + storyboard search; the two sentence overlays were confirmed
# verbatim in the storyboards, not guessed).
OVERLAYS = {
    "tw_004_richard_grimshaw___age_13":      "RICHARD GRIMSHAW, AGE 13",
    "tw_013_then_the_formula_met_the_inter": "THEN THE FORMULA MET THE INTERNET.",
    "tw_015_cambridge_analytica":            "CAMBRIDGE ANALYTICA",
    "tw_017_march_2018":                     "MARCH 2018",
    "tw_020_yesenia_guitron":                "YESENIA GUITRON",
    "tw_027_3_000":                          "$3,000",
    "tw_028_irreversible":                   "IRREVERSIBLE.",
    "tw_029_what_happens_when_the_fine_is":  "WHAT HAPPENS WHEN THE FINE IS ZERO?",
    "tw_032_the_most_painful_and_revoltin":  "“THE MOST PAINFUL AND REVOLTING”",
    "tw_033_doj_v__realpage___nov__2025":    "DOJ v. REALPAGE — NOV. 2025",
    "tw_036_richard_grimshaw":               "RICHARD GRIMSHAW",
    "tw_043_elliana_esquivel":               "ELLIANA ESQUIVEL",
    "tw_044_74__of_facebook_users_don_t_kn": "74% OF FACEBOOK USERS DON'T KNOW THEY'RE PROFILED",
}


def wrap_lines(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(text):
    """Return (font, lines) that fit within MAX_W, shrinking font if needed."""
    for size in range(76, 33, -4):
        font = ImageFont.truetype(FONT, size)
        img = Image.new("RGBA", (10, 10))
        d = ImageDraw.Draw(img)
        lines = wrap_lines(d, text, font, MAX_W)
        if all(d.textlength(ln, font=font) <= MAX_W for ln in lines):
            return font, lines
    return ImageFont.truetype(FONT, 36), wrap_lines(ImageDraw.Draw(Image.new("RGBA", (10, 10))), text, ImageFont.truetype(FONT, 36), MAX_W)


def render_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font, lines = fit(text)
    asc, desc = font.getmetrics()
    line_h = int((asc + desc) * LINE_GAP)
    total_h = line_h * len(lines)
    y = Y_CENTER - total_h // 2
    for ln in lines:
        tw = draw.textlength(ln, font=font)
        x = (W - tw) / 2
        draw.text((x + 3, y + 3), ln, fill=(0, 0, 0, 150), font=font)   # shadow
        draw.text((x, y), ln, fill=(255, 255, 255, 255), font=font)     # text
        y += line_h
    img.save(path)


def make_mov(png, out):
    fade_out_st = round(DUR - FADE, 3)
    vf = (f"fade=t=in:st=0:d={FADE}:alpha=1,"
          f"fade=t=out:st={fade_out_st}:d={FADE}:alpha=1,"
          f"format=yuva444p10le")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png,
           "-t", str(DUR), "-r", str(FPS), "-vf", vf,
           "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
           out]
    subprocess.run(cmd, check=True)


def main():
    with tempfile.TemporaryDirectory() as td:
        for stem, text in OVERLAYS.items():
            out = os.path.join(OVERLAY_DIR, stem + ".mov")
            png = os.path.join(td, stem + ".png")
            render_png(text, png)
            make_mov(png, out)
            print(f"  {stem}.mov  <-  {text!r}")
    print(f"Regenerated {len(OVERLAYS)} overlays in {OVERLAY_DIR}")


if __name__ == "__main__":
    main()
