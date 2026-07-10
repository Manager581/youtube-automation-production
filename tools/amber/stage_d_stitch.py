#!/usr/bin/env python3
"""AMBER stage D — stitch the generated crop back into the full frame + mux audio.

Fixes for VACE's known composite-boundary issues (per research):
  - paste back ONLY the masked area (feathered), never the whole crop
  - color-ring correction: the background ring inside the crop should be
    pixel-identical to the original, so any mean/std drift measured there is
    VAE roundtrip shift — correct the generated frames by that delta.

Runs in main venv. No GPU.
"""
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

WORK = Path(__file__).resolve().parent / "work" / os.environ.get("AMBER_BEAT", "beat01_strike")
meta = json.loads((WORK / "meta.json").read_text())

W, H = meta["frame_size"]
x0, y0, x1, y1 = meta["crop_box"]
cw, ch = x1 - x0, y1 - y0
fps = meta["fps"]
RETIME = float(os.environ.get("AMBER_RETIME", "1"))

full = np.asarray(Image.open(WORK / "frame.png").convert("RGB"), np.float32)
orig_crop = full[y0:y1, x0:x1]

mask448 = Image.open(WORK / "mask.png").convert("L").resize((cw, ch), Image.LANCZOS)
mask = np.asarray(mask448, np.float32) / 255.0
ring = mask < 0.05  # background ring: should be untouched by generation

blend = np.asarray(mask448.filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255.0

frames = sorted((WORK / "gen").glob("*.png"))
out_dir = WORK / "stitched"
out_dir.mkdir(exist_ok=True)

# Color-ring correction from the middle frame (per-channel gain + offset)
mid = np.asarray(Image.open(frames[len(frames) // 2]).convert("RGB")
                 .resize((cw, ch), Image.LANCZOS), np.float32)
gain = orig_crop[ring].std(0) / (mid[ring].std(0) + 1e-6)
gain = np.clip(gain, 0.8, 1.25)
offset = orig_crop[ring].mean(0) - mid[ring].mean(0) * gain
print(f"color-ring correction: gain={gain.round(3)} offset={offset.round(1)}")

for i, fp in enumerate(frames):
    g = np.asarray(Image.open(fp).convert("RGB").resize((cw, ch), Image.LANCZOS), np.float32)
    g = np.clip(g * gain + offset, 0, 255)
    stitched = full.copy()
    stitched[y0:y1, x0:x1] = blend * g + (1 - blend) * orig_crop
    Image.fromarray(stitched.astype(np.uint8)).save(out_dir / f"{i:04d}.png")

out_name = f"{meta.get('beat', WORK.name)}_AMBER.mp4" if meta.get('beat') else f"{WORK.name}_AMBER.mp4"
in_rate = fps / RETIME
vf = ("minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc," if RETIME > 1 else "") + "scale=trunc(iw/2)*2:trunc(ih/2)*2"
subprocess.run(
    ["ffmpeg", "-y", "-v", "error",
     "-framerate", str(in_rate), "-i", str(out_dir / "%04d.png"),
     "-i", str(WORK / "beat_audio.wav"),
     "-vf", vf,
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
     "-c:a", "aac", "-b:a", "192k", "-shortest",
     str(WORK / out_name)],
    check=True,
)
print(f"stage D done -> {WORK / out_name}")
