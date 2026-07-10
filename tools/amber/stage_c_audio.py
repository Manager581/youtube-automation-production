#!/usr/bin/env python3
"""AMBER stage C — detect motion events in the generated crop, place SFX on them.

The event sheet authored the intent (jaws_snap); the generated clip decides the
actual frame. We detect the motion peak inside the creature mask and anchor the
SFX stack there — sync is computed, not guessed. Runs in main venv. No GPU.
"""
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

WORK = Path(__file__).resolve().parent / "work" / "beat01_strike"
REPO = Path(__file__).resolve().parents[2]
SR = 44100

meta = json.loads((WORK / "meta.json").read_text())
sheet = json.loads((WORK / "event_sheet.json").read_text())
fps = meta["fps"]

frames = sorted((WORK / "gen").glob("*.png"))
mask = np.array(Image.open(WORK / "mask.png").convert("L")) > 127

imgs = [np.asarray(Image.open(f).convert("L"), np.float32) for f in frames]
motion = np.array([np.abs(imgs[i + 1] - imgs[i])[mask].mean() for i in range(len(imgs) - 1)])
k = np.ones(3) / 3
motion_s = np.convolve(motion, k, mode="same")
peak_idx = int(np.argmax(motion_s))
t_peak = (peak_idx + 1) / fps
print(f"motion peak at frame {peak_idx + 1} -> t={t_peak:.2f}s "
      f"(curve max {motion_s[peak_idx]:.2f}, mean {motion_s.mean():.2f})")

sheet["detected_events"] = [
    {"name": "jaws_snap", "t": round(t_peak, 3), "method": "frame-diff-in-mask",
     "motion_curve_max": round(float(motion_s[peak_idx]), 2)}
]
(WORK / "event_sheet.json").write_text(json.dumps(sheet, indent=2))

# Mix the SFX stack anchored on the detected event
dur = meta["num_frames"] / fps
mix = np.zeros(int(dur * SR) + SR, np.float32)  # +1s tail room
for sfx in sheet["sfx_map"]:
    t0 = t_peak + sfx["offset_s"]
    if t0 < 0:
        continue
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(REPO / sfx["file"]),
         "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True,
    ).stdout
    s = np.frombuffer(raw, np.float32) * (10 ** (sfx["gain_db"] / 20))
    i0 = int(t0 * SR)
    n = min(len(s), len(mix) - i0)
    mix[i0:i0 + n] += s[:n]
    print(f"  placed {Path(sfx['file']).name} at {t0:.2f}s ({sfx['gain_db']}dB)")

mix = np.clip(mix[: int(dur * SR)], -1, 1)
pcm = (mix * 32767).astype(np.int16).tobytes()
subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ac", "1", "-ar", str(SR),
     "-i", "-", str(WORK / "beat_audio.wav")],
    input=pcm, check=True,
)
print(f"stage C done -> beat_audio.wav ({dur:.2f}s), jaws_snap detected at {t_peak:.2f}s")
