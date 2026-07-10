#!/usr/bin/env python3
"""AMBER stage C — detect motion events in the generated crop, place SFX on them.

The event sheet authored the intent (jaws_snap); the generated clip decides the
actual frame. We detect the motion peak inside the creature mask and anchor the
SFX stack there — sync is computed, not guessed. Runs in main venv. No GPU.
"""
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

WORK = Path(__file__).resolve().parent / "work" / os.environ.get("AMBER_BEAT", "beat01_strike")
REPO = Path(__file__).resolve().parents[2]
SR = 44100

meta = json.loads((WORK / "meta.json").read_text())
sheet = json.loads((WORK / "event_sheet.json").read_text())
fps = meta["fps"]
RETIME = float(os.environ.get("AMBER_RETIME", "1"))  # 2 = half-speed presentation

frames = sorted((WORK / "gen").glob("*.png"))
mask = np.array(Image.open(WORK / "mask.png").convert("L")) > 127

imgs = [np.asarray(Image.open(f).convert("L"), np.float32) for f in frames]
motion = np.array([np.abs(imgs[i + 1] - imgs[i])[mask].mean() for i in range(len(imgs) - 1)])
k = np.ones(3) / 3
motion_s = np.convolve(motion, k, mode="same")
peak_idx = int(np.argmax(motion_s))
t_peak = (peak_idx + 1) / fps * RETIME
print(f"motion peak at frame {peak_idx + 1} -> t={t_peak:.2f}s "
      f"(curve max {motion_s[peak_idx]:.2f}, mean {motion_s.mean():.2f})")

# SFX gate: only a REAL event gets the impact stack (strong, not at clip start)
# Real event = sharp relative spike (quiet clips) OR strong absolute peak (high-energy clips)
event_real = (motion_s[peak_idx] >= 1.8 * motion_s.mean() or motion_s[peak_idx] >= 5.0) \
    and t_peak > 0.5 * RETIME
sheet["detected_events"] = [
    {"name": "jaws_snap", "t": round(t_peak, 3), "method": "frame-diff-in-mask",
     "motion_curve_max": round(float(motion_s[peak_idx]), 2), "real": bool(event_real)}
]
active_sfx = sheet["sfx_map"]
if not event_real:
    print(f"NO REAL EVENT (peak {motion_s[peak_idx]:.2f} vs mean {motion_s.mean():.2f}, "
          f"t={t_peak:.2f}s) -> ambience only, impact stack skipped")
    active_sfx = [x for x in sheet["sfx_map"] if x.get("event") == "clip_start"]
(WORK / "event_sheet.json").write_text(json.dumps(sheet, indent=2))

# Mix the SFX stack anchored on the detected event
dur = meta["num_frames"] / fps * RETIME
mix = np.zeros(int(dur * SR) + SR, np.float32)  # +1s tail room
for sfx in active_sfx:
    anchor = 0.0 if sfx.get("event") == "clip_start" else t_peak
    t0 = anchor + sfx["offset_s"]
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
