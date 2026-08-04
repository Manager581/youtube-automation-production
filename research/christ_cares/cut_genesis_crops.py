#!/usr/bin/env python3
"""Cut the 9 ledger crops for the Genesis overview (GENESIS_SHOT_LEDGER.md v2 step 4).

Every crop box is 16:9 on the 1672x941 seeds and is Lanczos-upscaled to full
1672x941 output so Grok gets a uniform full-res seed (ledger mandates upscale for
G025/G046; uniform upscale is strictly better for 720p i2v and costs nothing).

Also runs the WBS same-seed distinctness gate (research/wildbirdsurvival_teardown/
gate_crop_distinct.py thresholds: IoU > 0.80 at < 15% scale diff = too alike)
between each crop and its full-frame sibling shot on the same seed.

  venv/bin/python research/christ_cares/cut_genesis_crops.py
"""
import os

from PIL import Image

ROOT = "/Users/jefflawrence/Documents/youtube-automation-production"
CC = os.path.join(ROOT, "assets/christ_cares")
OUT = os.path.join(CC, "crops")

# shot_id -> (source image, (x, y, w, h) box, full-frame sibling shot on the same seed)
CROPS = {
    "G003_light_core": (f"{CC}/genesis_overview/genesis_S01b.png", (328, 0, 1004, 565), "G001-ish (S01a full is a different seed; S01b has no full-frame shot)"),
    "G016_root_base": (f"{CC}/doc_seeds/doc_tree_serpent.png", (452, 470, 838, 471), "G012 full"),
    "G018_shadow_ground": (f"{CC}/genesis_overview/genesis_S05.png", (660, 500, 784, 441), "G017 full"),
    "G025_ark_window": (f"{CC}/style_test/TEST2_ark_doc.png", (280, 70, 560, 315), "G024 full"),
    "G029_babel_base": (f"{CC}/doc_seeds/doc_babel.png", (480, 541, 711, 400), "G028 full"),
    "G033_gate_glow": (f"{CC}/style_test/TEST3_desert_doc.png", (480, 290, 720, 405), "G031 full"),
    # G044 y starts at 0 so the robed man's head top (source y~430+) stays out of frame
    "G044_hall_windows": (f"{CC}/doc_seeds/doc_throne_hall.png", (560, 0, 720, 405), "G043 full"),
    # G046 window sits between the lit son's head (ends ~y280) and the patriarch's head (starts ~y652)
    "G046_shaft_torso": (f"{CC}/doc_seeds/doc_tent_blessing.png", (690, 285, 649, 365), "G045 full"),
    "G051_scroll_pages": (f"{CC}/genesis_overview/genesis_S14.png", (286, 322, 1100, 619), "G049 full"),
}

IOU_LIMIT = 0.80
SCALE_LIMIT = 0.15
FULL = (0, 0, 1672, 941)


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"{'shot':22s} {'box':>22s}  {'IoU-vs-full':>11s} {'scale-diff':>10s}  gate")
    for shot, (src, box, sibling) in sorted(CROPS.items()):
        im = Image.open(src)
        x, y, w, h = box
        assert abs(w / h - 16 / 9) < 0.02, f"{shot}: box not 16:9 ({w}x{h})"
        assert x + w <= im.width and y + h <= im.height, f"{shot}: box out of bounds"
        crop = im.crop((x, y, x + w, y + h)).resize((1672, 941), Image.LANCZOS)
        crop.save(os.path.join(OUT, f"{shot}.png"))
        o = iou(box, FULL)
        scale = abs(w - FULL[2]) / FULL[2]
        alike = o > IOU_LIMIT and scale < SCALE_LIMIT
        print(f"{shot:22s} {str(box):>22s}  {o:>11.2f} {scale:>9.0%}  {'TOO ALIKE vs ' + sibling if alike else 'distinct'}")
    print(f"\nwrote {len(CROPS)} crops to {OUT}")


if __name__ == "__main__":
    main()
