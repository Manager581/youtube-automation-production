#!/usr/bin/env python3
"""Genesis trailer thumbnail — dino x flood hero (+ ark-door alt).

Competitor field (YouTube 'book of genesis explained' / 'genesis full story
animated', surveyed 2026-08-06): bright cartoon/AI-fantasy, gold-serif GENESIS
text, God faces, busy collages. Standout wedge = the channel's own register:
dark documentary photoreal, ONE subject, dinosaurs+ark (nobody has it, and it
is the recon's #1 most-asked question). Composed from the 1672px SEED plates
(not video frames) per playbook P-TT-03; text delivers the claim the title
doesn't repeat (P-TT-02).
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SEEDS = os.path.join(REPO, "assets", "christ_cares", "doc_seeds")
OUT = os.path.join(REPO, "assets", "christ_cares")
FONT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
W, H = 1280, 720
AMBER = (245, 183, 66)
WHITE = (245, 245, 245)


def draw_block(draw, xy, text, size, fill, stroke=8):
    f = ImageFont.truetype(FONT, size)
    # soft drop shadow then hard stroke for small-size read
    x, y = xy
    draw.text((x + 6, y + 8), text, font=f, fill=(0, 0, 0, 160))
    draw.text((x, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(10, 10, 10))
    return draw.textbbox((x, y), text, font=f, stroke_width=stroke)


def grade(im, contrast=1.14, color=0.9, dark_top=0.45):
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    # darken the upper sky band so text carries at 168x94
    ov = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(ov)
    for row in range(int(im.height * 0.55)):
        a = int(255 * dark_top * (1 - row / (im.height * 0.55)) ** 1.5)
        d.line([(0, row), (im.width, row)], fill=a)
    black = Image.new("RGB", im.size, (4, 6, 10))
    return Image.composite(black, im, ov.point(lambda v: v)).convert("RGB")


def feather_paste(base, patch, center, feather=40):
    mask = Image.new("L", patch.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([feather // 2, feather // 2,
                         patch.width - feather // 2, patch.height - feather // 2],
                        radius=feather, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather // 2))
    base.paste(patch, (center[0] - patch.width // 2, center[1] - patch.height // 2), mask)


def hero():
    src = Image.open(os.path.join(SEEDS, "doc_flood_creatures.png")).convert("RGB")
    # zoom crop so the hero neck+head dominates the right half, head clear of sky band
    im = src.crop((418, 60, 1672, 765)).resize((W, H), Image.LANCZOS)
    # ark patch from the ORIGINAL plate (same light), enlarged, lower-left midground
    ark = src.crop((300, 220, 620, 400))
    ark = ark.resize((int(ark.width * 1.45), int(ark.height * 1.45)), Image.LANCZOS)
    feather_paste(im, ark, (280, 380), feather=80)
    im = grade(im, contrast=1.13, dark_top=0.36)
    d = ImageDraw.Draw(im, "RGBA")
    bb = draw_block(d, (44, 36), "DINOSAURS", 116, AMBER, stroke=9)
    draw_block(d, (44, bb[3] + 4), "WERE THERE", 86, WHITE, stroke=8)
    im.save(os.path.join(OUT, "thumb_genesis_dino_flood.png"))
    im.resize((168, 94), Image.LANCZOS).save(os.path.join(OUT, "thumb_genesis_dino_flood_168.png"))


def alt():
    im = Image.open(os.path.join(SEEDS, "doc_ark_door_family.png")).convert("RGB")
    im = im.resize((W, H), Image.LANCZOS)
    im = grade(im, contrast=1.10, dark_top=0.5)
    d = ImageDraw.Draw(im, "RGBA")
    bb = draw_block(d, (46, 40), "ONE DOOR", 150, AMBER, stroke=10)
    draw_block(d, (46, bb[3] + 6), "SAVED THEM ALL", 88, WHITE, stroke=8)
    im.save(os.path.join(OUT, "thumb_genesis_ark_door.png"))
    im.resize((168, 94), Image.LANCZOS).save(os.path.join(OUT, "thumb_genesis_ark_door_168.png"))


def speed():
    """Utility/speed angle for Test & Compare: the whole book, fast."""
    plate = os.path.join(REPO, "assets", "christ_cares", "genesis_overview", "genesis_S14.png")
    im = Image.open(plate).convert("RGB").resize((W, H), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.08)  # flanks are already near-black; no sky band
    d = ImageDraw.Draw(im, "RGBA")
    bb = draw_block(d, (44, 40), "ALL 50 CHAPTERS", 108, AMBER, stroke=9)
    draw_block(d, (44, bb[3] + 6), "IN 5 MINUTES", 86, WHITE, stroke=8)
    im.save(os.path.join(OUT, "thumb_genesis_50chapters.png"))
    im.resize((168, 94), Image.LANCZOS).save(os.path.join(OUT, "thumb_genesis_50chapters_168.png"))


def results_row():
    """All three at 168x94 side by side — a mock search-results row for judging."""
    names = ["thumb_genesis_dino_flood_168.png", "thumb_genesis_ark_door_168.png",
             "thumb_genesis_50chapters_168.png"]
    row = Image.new("RGB", (168 * 3 + 40, 94 + 20), (24, 24, 24))
    for i, n in enumerate(names):
        row.paste(Image.open(os.path.join(OUT, n)), (10 + i * 178, 10))
    row.resize((row.width * 2, row.height * 2), Image.NEAREST).save(
        os.path.join(OUT, "thumb_genesis_test_row.png"))


if __name__ == "__main__":
    hero()
    alt()
    speed()
    results_row()
    print("wrote 3 thumbnails + test row to", OUT)
