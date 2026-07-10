#!/usr/bin/env python3
"""AMBER stage A — beat02_dunk: 6s apex-reveal beat from a current ChatGPT still.

Source is a full AI still (no known cutout), so the matte comes from rembg —
verify the overlay before generating. Also saves ref.png (creature on white)
for VACE reference_images identity locking. Main venv.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

REPO = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent / "work" / "beat02_dunk"
WORK.mkdir(parents=True, exist_ok=True)

SRC_STILL = REPO / "assets" / "dunkleosteus" / "sh04_apex_reveal.png"
NUM_FRAMES = 49          # 4k+1; presented at half speed -> 6.1s
FPS = 16
MODEL_W, MODEL_H = 512, 320

frame = Image.open(SRC_STILL).convert("RGB")
W, H = frame.size
frame.save(WORK / "frame.png")

session = new_session("u2net")
alpha = remove(frame, session=session, only_mask=True)
a = np.array(alpha)
ys, xs = np.where(a > 127)
x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
print(f"creature bbox: x {x0}-{x1}, y {y0}-{y1}  (frame {W}x{H}, "
      f"mask covers {100*(a>127).mean():.0f}% of frame)")

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

mask_full = Image.fromarray(a).crop(crop_box).resize(
    (MODEL_W, MODEL_H), Image.LANCZOS
)
mask_np = (np.array(mask_full) > 127).astype(np.uint8) * 255
mask_img = Image.fromarray(mask_np).filter(ImageFilter.MaxFilter(25))
mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
mask_img = Image.fromarray(((np.array(mask_img) > 64) * 255).astype(np.uint8))
mask_img.save(WORK / "mask.png")

# Reference image: creature on white, for VACE identity locking
cut = remove(frame, session=session)  # RGBA
ref = Image.new("RGB", (W, H), (255, 255, 255))
ref.paste(cut, (0, 0), cut)
ref = ref.crop(crop_box).resize((MODEL_W, MODEL_H), Image.LANCZOS)
ref.save(WORK / "ref.png")

(WORK / "meta.json").write_text(json.dumps({
    "src_still": str(SRC_STILL),
    "frame_size": [W, H],
    "crop_box": list(crop_box),
    "model_w": MODEL_W,
    "model_h": MODEL_H,
    "num_frames": NUM_FRAMES,
    "fps": FPS,
}, indent=2))

(WORK / "event_sheet.json").write_text(json.dumps({
    "beat": "beat02_dunk",
    "duration_s": NUM_FRAMES / FPS,
    "prompt": (
        "massive armored dunkleosteus swims forward through deep dark "
        "ocean water, jaws gaping wider then snapping shut with force, fins "
        "rippling, tail sweeping, drifting sediment particles, volumetric god "
        "rays from above, photorealistic underwater documentary footage"
    ),
    "authored_events": [
        {"name": "glide_in", "t": 0.8, "intent": "forward drift, fins working"},
        {"name": "jaw_snap", "t": 3.2, "intent": "jaws gape then snap - the scare"},
        {"name": "menace_hold", "t": 5.0, "intent": "slow menace, sediment settles"},
    ],
    "sfx_map": [
        {"event": "clip_start", "file": "assets/sfx/rumble_03_loud.wav", "offset_s": 0.0, "gain_db": -8},
        {"event": "jaw_snap", "file": "assets/sfx/whoosh_02_loud.wav", "offset_s": -0.4, "gain_db": -4},
        {"event": "jaw_snap", "file": "assets/sfx/impact_02_loud.wav", "offset_s": 0.0, "gain_db": -1},
        {"event": "jaw_snap", "file": "assets/sfx/rumble_02_loud.wav", "offset_s": 0.1, "gain_db": -5},
    ],
    "detected_events": None,
}, indent=2))
print(f"stage A2 done -> {WORK}")
