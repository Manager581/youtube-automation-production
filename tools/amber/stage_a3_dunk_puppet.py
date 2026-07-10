#!/usr/bin/env python3
"""AMBER stage A3 — beat03: puppet-conditioned dunk beat.

The beat02 failure: 49 identical conditioning frames = "static scene" prior =
no motion. Fix: author crude motion (scale-in approach + sway + a gape pulse)
on the creature cutout with the compositing transforms we already use, and let
VACE refine crude into organic (the Time-to-Move principle). Main venv.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

REPO = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent / "work" / "beat03_dunk_puppet"
WORK.mkdir(parents=True, exist_ok=True)

SRC_STILL = REPO / "assets" / "dunkleosteus" / "sh04_apex_reveal.png"
NUM_FRAMES = 97          # 4k+1 -> 6.06s @ 16fps, native speed
FPS = 16
MODEL_W, MODEL_H = 416, 256

frame = Image.open(SRC_STILL).convert("RGB")
W, H = frame.size
frame.save(WORK / "frame.png")

session = new_session("u2net")
cut_full = remove(frame, session=session)           # RGBA full frame
a_full = np.array(cut_full.split()[3])
ys, xs = np.where(a_full > 127)
x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())

# Same rectangular whole-creature window as beat02, AR matched to model
cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
cw = min(int((x1 - x0) * 1.15), W)
ch = min(int(cw * MODEL_H / MODEL_W), H)
cw = int(ch * MODEL_W / MODEL_H)
left = int(max(0, min(cx - cw // 2, W - cw)))
top = int(max(0, min(cy - ch // 2, H - ch)))
crop_box = (left, top, left + cw, top + ch)
print(f"crop window: {crop_box} ({cw}x{ch}) -> {MODEL_W}x{MODEL_H}")

crop = frame.crop(crop_box).resize((MODEL_W, MODEL_H), Image.LANCZOS)
crop.save(WORK / "crop.png")
cut = cut_full.crop(crop_box).resize((MODEL_W, MODEL_H), Image.LANCZOS)

# Reference for identity lock
ref = Image.new("RGB", (MODEL_W, MODEL_H), (255, 255, 255))
ref.paste(cut, (0, 0), cut)
ref.save(WORK / "ref.png")


def smoothstep(u):
    return u * u * (3 - 2 * u)


# Puppet pass: crude approach + sway + midpoint gape pulse on the cutout
cond_dir = WORK / "cond"
cond_dir.mkdir(exist_ok=True)
union = np.zeros((MODEL_H, MODEL_W), np.uint8)
ccx, ccy = MODEL_W // 2, MODEL_H // 2
for i in range(NUM_FRAMES):
    u = i / (NUM_FRAMES - 1)
    s = 1.0 + 0.10 * smoothstep(u)                       # approach: +10% scale
    gape = 0.035 * math.exp(-((u - 0.5) ** 2) / 0.008)   # midpoint lunge pulse
    sx = s
    sy = s * (1.0 + gape)
    dx = 0.012 * MODEL_W * math.sin(2 * math.pi * 1.5 * u)
    dy = 0.008 * MODEL_H * math.sin(2 * math.pi * 2.2 * u + 1.1) - 0.02 * MODEL_H * smoothstep(u)
    tw, th = int(MODEL_W * sx), int(MODEL_H * sy)
    t = cut.resize((tw, th), Image.LANCZOS)
    px = int(ccx - tw / 2 + dx)
    py = int(ccy - th / 2 + dy)
    f = crop.copy()
    f.paste(t, (px, py), t)
    f.save(cond_dir / f"{i:04d}.png")
    ta = np.zeros((MODEL_H, MODEL_W), np.uint8)
    tm = np.array(t.split()[3])
    yy0, xx0 = max(0, py), max(0, px)
    yy1, xx1 = min(MODEL_H, py + th), min(MODEL_W, px + tw)
    if yy1 > yy0 and xx1 > xx0:
        ta[yy0:yy1, xx0:xx1] = tm[yy0 - py:yy1 - py, xx0 - px:xx1 - px]
    union = np.maximum(union, ta)

mask_img = Image.fromarray(((union > 127) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21))
mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
mask_img = Image.fromarray(((np.array(mask_img) > 64) * 255).astype(np.uint8))
mask_img.save(WORK / "mask.png")
print(f"puppet conditioning: {NUM_FRAMES} frames, mask union covers "
      f"{100*(union>127).mean():.0f}% of crop")

(WORK / "meta.json").write_text(json.dumps({
    "beat": "beat03_dunk_puppet",
    "src_still": str(SRC_STILL),
    "frame_size": [W, H],
    "crop_box": list(crop_box),
    "model_w": MODEL_W,
    "model_h": MODEL_H,
    "num_frames": NUM_FRAMES,
    "fps": FPS,
}, indent=2))

(WORK / "event_sheet.json").write_text(json.dumps({
    "beat": "beat03_dunk_puppet",
    "duration_s": NUM_FRAMES / FPS,
    "prompt": (
        "massive armored dunkleosteus swims forward through deep dark ocean, "
        "powerful tail strokes, fins rippling, then lunges and snaps its bony "
        "jaws shut hard at the midpoint, sediment swirling in its wake, "
        "volumetric god rays, photorealistic underwater documentary footage"
    ),
    "authored_events": [
        {"name": "approach", "t": 1.0, "intent": "tail strokes, closing distance"},
        {"name": "jaw_snap", "t": 3.0, "intent": "lunge + hard jaw snap (matches gape pulse)"},
        {"name": "menace_hold", "t": 5.0, "intent": "slow glide out, sediment"},
    ],
    "sfx_map": [
        {"event": "clip_start", "file": "assets/sfx/rumble_03_loud.wav", "offset_s": 0.0, "gain_db": -8},
        {"event": "jaw_snap", "file": "assets/sfx/whoosh_02_loud.wav", "offset_s": -0.4, "gain_db": -4},
        {"event": "jaw_snap", "file": "assets/sfx/impact_02_loud.wav", "offset_s": 0.0, "gain_db": -1},
        {"event": "jaw_snap", "file": "assets/sfx/rumble_02_loud.wav", "offset_s": 0.1, "gain_db": -5},
    ],
    "detected_events": None,
}, indent=2))
print(f"stage A3 done -> {WORK}")
