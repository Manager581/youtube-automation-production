#!/usr/bin/env python3
"""AMBER stage A — build the masked-crop input for one beat from a real composite frame.

Runs in the MAIN venv (needs rembg + PIL). No GPU.
Outputs into tools/amber/work/<beat>/:
  frame.png        full source frame (960x540)
  crop.png         square crop around the creature, resized to 512x512
  mask.png         creature mask inside the crop (white = VACE regenerates)
  meta.json        crop window + scale for stage D stitch-back
  event_sheet.json authored events + SFX mapping (detected timing added by stage C)
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter

REPO = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent / "work" / "beat01_strike"
WORK.mkdir(parents=True, exist_ok=True)

SRC_VIDEO = REPO / "output" / "proto_strike_540p.mp4"
FRAME_IDX = 96
NUM_FRAMES = 41          # Wan needs 4k+1
FPS = 16                 # VACE-1.3B native
CROP_MODEL_SIZE = 448

frame_png = WORK / "frame.png"
subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-i", str(SRC_VIDEO),
     "-vf", f"select='eq(n,{FRAME_IDX})'", "-frames:v", "1", str(frame_png)],
    check=True,
)
frame = Image.open(frame_png).convert("RGB")
W, H = frame.size

# The composite was authored from a known cutout — locate it by template matching
# (the cutout's own alpha IS the creature matte; no segmentation guessing).
CUTOUT = REPO / "assets" / "trex_pilot" / "cutouts" / "c_strike_blur_cut.png"
cut = Image.open(CUTOUT).convert("RGBA")
cut_rgb = np.array(cut.convert("RGB"))
cut_a = np.array(cut.split()[3])
frame_bgr = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
cut_bgr_full = cv2.cvtColor(cut_rgb, cv2.COLOR_RGB2BGR)

best = None  # (score, scale, x, y, w, h)
for scale_h_px in range(180, 561, 10):  # head height sweep in a 540px frame
    s = scale_h_px / cut.height
    tw, th = max(int(cut.width * s), 8), max(int(cut.height * s), 8)
    if tw >= W or th >= H:
        continue
    tmpl = cv2.resize(cut_bgr_full, (tw, th), interpolation=cv2.INTER_AREA)
    tmask = cv2.resize(cut_a, (tw, th), interpolation=cv2.INTER_AREA)
    res = cv2.matchTemplate(frame_bgr, tmpl, cv2.TM_CCORR_NORMED, mask=tmask)
    _, mx, _, ml = cv2.minMaxLoc(res)
    if np.isfinite(mx) and (best is None or mx > best[0]):
        best = (mx, s, ml[0], ml[1], tw, th)
if best is None:
    sys.exit("template match failed")
score, s, tx, ty, tw, th = best
print(f"cutout match: score={score:.4f} scale={s:.3f} at ({tx},{ty}) size {tw}x{th}")

# Creature alpha placed at the matched location = exact matte
a = np.zeros((H, W), np.uint8)
tmask = cv2.resize(cut_a, (tw, th), interpolation=cv2.INTER_AREA)
a[ty:ty + th, tx:tx + tw] = np.maximum(a[ty:ty + th, tx:tx + tw], tmask)
ys, xs = np.where(a > 127)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
print(f"creature bbox: x {x0}-{x1}, y {y0}-{y1}  (frame {W}x{H})")

# Square crop window around the bbox with margin, clamped to frame
cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
side = int(max(x1 - x0, y1 - y0) * 1.35)
side = min(side, W, H)
left = int(max(0, min(cx - side // 2, W - side)))
top = int(max(0, min(cy - side // 2, H - side)))
crop_box = (left, top, left + side, top + side)
print(f"crop window: {crop_box} ({side}x{side}) -> {CROP_MODEL_SIZE}x{CROP_MODEL_SIZE}")

crop = frame.crop(crop_box).resize((CROP_MODEL_SIZE, CROP_MODEL_SIZE), Image.LANCZOS)
crop.save(WORK / "crop.png")

# Mask = creature alpha inside the crop, dilated so VACE gets room to move the jaw
mask_full = Image.fromarray(a).crop(crop_box).resize(
    (CROP_MODEL_SIZE, CROP_MODEL_SIZE), Image.LANCZOS
)
mask_np = (np.array(mask_full) > 127).astype(np.uint8) * 255
mask_img = Image.fromarray(mask_np).filter(ImageFilter.MaxFilter(31))  # ~15px dilation
mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
mask_img = Image.fromarray(((np.array(mask_img) > 64) * 255).astype(np.uint8))
mask_img.save(WORK / "mask.png")

meta = {
    "src_video": str(SRC_VIDEO),
    "frame_idx": FRAME_IDX,
    "frame_size": [W, H],
    "crop_box": list(crop_box),
    "model_size": CROP_MODEL_SIZE,
    "num_frames": NUM_FRAMES,
    "fps": FPS,
}
(WORK / "meta.json").write_text(json.dumps(meta, indent=2))

# The event sheet: authored intent. Stage C adds detected_events after generation.
event_sheet = {
    "beat": "beat01_strike",
    "duration_s": NUM_FRAMES / FPS,
    "prompt": (
        "photorealistic tyrannosaurus rex head rears back then snaps its jaws "
        "open in a ferocious roar, muscles tensing, skin wrinkling, "
        "overcast city street, natural light, documentary wildlife footage"
    ),
    "authored_events": [
        {"name": "tension_build", "t": 0.6, "intent": "head rears back"},
        {"name": "jaws_snap", "t": 1.5, "intent": "jaw opens fully - the strike moment"},
        {"name": "settle", "t": 2.6, "intent": "head settles, breathing"},
    ],
    "sfx_map": [
        {"event": "jaws_snap", "file": "assets/sfx/whoosh_03_loud.wav", "offset_s": -0.35, "gain_db": -6},
        {"event": "jaws_snap", "file": "assets/sfx/impact_new_loud.wav", "offset_s": 0.0, "gain_db": 0},
        {"event": "jaws_snap", "file": "assets/sfx/rumble_02_loud.wav", "offset_s": 0.05, "gain_db": -3},
    ],
    "detected_events": None,
}
(WORK / "event_sheet.json").write_text(json.dumps(event_sheet, indent=2))
print(f"stage A done -> {WORK}")
