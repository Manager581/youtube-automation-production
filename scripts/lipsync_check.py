#!/usr/bin/env python3
"""lipsync_check.py — Law 2(b): does the mouth move WITH the words? Mouth-box motion energy (frame diff, 25 fps) vs the speech
RMS envelope of the line; max normalized cross-correlation within ±0.3 s lag. Calibrate on a reference talking clip.
  --clip X.mp4 --audio line.wav|mp3 [--t0 s] --box x,y,w,h (fractions of frame; the mouth region) [--profile P.json] [--calibrate --out P.json]
FAIL if corr < profile floor (default 0.35) or if the mouth box shows no motion while speech has energy (static mouth)."""
import argparse, json, subprocess, sys
import numpy as np, librosa
def frames(clip, t0, dur, box, fps=25, w=320, h=180):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", clip, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h); fr = np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w).astype(np.float32)
    x, y, bw, bh = box; X0, Y0, X1, Y1 = int(x * w), int(y * h), int((x + bw) * w), int((y + bh) * h)
    roi = fr[:, Y0:Y1, X0:X1]; return np.abs(np.diff(roi, axis=0)).mean(axis=(1, 2)), fps
def envelope(audio, n, fps):
    y, sr = librosa.load(audio, sr=16000, mono=True); hop = int(sr / fps); rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
    e = np.diff(np.pad(rms, (1, 0)))  # speech onsets, not level
    return np.resize(np.abs(e), n)
def xcorr(a, b, maxlag):
    a = (a - a.mean()) / (a.std() + 1e-9); b = (b - b.mean()) / (b.std() + 1e-9); best = -1
    for lag in range(-maxlag, maxlag + 1):
        if lag >= 0: c = np.mean(a[lag:] * b[: len(b) - lag]) if len(b) - lag > 5 else -1
        else: c = np.mean(a[: lag] * b[-lag:]) if len(a) + lag > 5 else -1
        best = max(best, float(c))
    return best
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--clip", required=True); ap.add_argument("--audio", required=True); ap.add_argument("--t0", type=float, default=0.0); ap.add_argument("--box", required=True); ap.add_argument("--profile"); ap.add_argument("--calibrate", action="store_true"); ap.add_argument("--out")
    a = ap.parse_args(); box = [float(v) for v in a.box.split(",")]; dur = librosa.get_duration(path=a.audio)
    m, fps = frames(a.clip, a.t0, dur, box); e = envelope(a.audio, len(m), fps); c = xcorr(m, e, int(0.3 * fps)); mouth_motion = float(m.mean())
    if a.calibrate: json.dump({"source": a.clip, "corr": round(c, 3), "mouth_motion": round(mouth_motion, 3), "floor": round(0.6 * c, 3)}, open(a.out, "w"), indent=1); print("profile:", {"corr": round(c, 3), "mouth_motion": round(mouth_motion, 3), "floor": round(0.6 * c, 3)}); return
    floor = json.load(open(a.profile))["floor"] if a.profile else 0.35
    ok = c >= floor and mouth_motion > 0.5
    print(f"lipsync: corr={c:.3f} (floor {floor}) mouth_motion={mouth_motion:.2f} -> {'PASS' if ok else 'FAIL'}"); sys.exit(0 if ok else 1)
if __name__ == "__main__": main()
