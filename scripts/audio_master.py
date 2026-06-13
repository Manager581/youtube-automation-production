#!/usr/bin/env python3
"""
audio_master.py — broadcast "studio polish" master for TTS voiceover.

TTS engines (Chatterbox/Qwen3/VoxCPM/F5) output a clean but flat, often 24kHz
signal. This is the post chain every professional VO gets anyway: it does NOT
fix robotic prosody (that's a model/fine-tune problem) — it adds the studio
SHEEN: tight level (low LRA like ElevenLabs' Mark = 5.0), presence, "air", and
broadcast loudness.

Chain (standard VO mastering order):
  resample 48k → highpass 80 → [denoise] → de-ess → compressor → tone EQ
  (mud cut + presence + air shelf) → exciter (fake HF air on 24k sources) →
  two-pass loudnorm (the right way: measure, then apply) → true-peak limiter.

Usage:
  venv/bin/python scripts/audio_master.py in.wav out.wav            # VO stem, -16 LUFS
  venv/bin/python scripts/audio_master.py in.wav out.wav --lufs -14 # standalone YouTube
  venv/bin/python scripts/audio_master.py raw_ref.wav clean_ref.wav --denoise --lufs -23
      # clean a RAW recording before using it as a clone reference

Pure ffmpeg — no extra deps. Two-pass loudnorm keeps level + true-peak honest.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def pre_chain(denoise: bool, air: bool, sr: int) -> str:
    """Everything before the final loudnorm, as one ffmpeg -af string."""
    parts = [
        f"aresample={sr}",
        "highpass=f=80",                       # kill rumble / DC / plosive thump
    ]
    if denoise:
        parts.append("afftdn=nr=12:nf=-30:tn=1")   # gentle broadband denoise (raw refs)
    parts += [
        "deesser=i=0.35:m=0.5:f=0.18",         # tame sibilance
        # gentle leveling toward a tight, consistent LRA (Mark = 5.0 LU)
        "acompressor=threshold=-20dB:ratio=3:attack=8:release=140:makeup=2:knee=4",
        "equalizer=f=250:t=q:w=1.2:g=-2.5",    # cut boxy low-mid mud
        "equalizer=f=3200:t=q:w=1.4:g=2.5",    # presence / intelligibility
        "equalizer=f=11000:t=h:w=0.7:g=2.0",   # air shelf (top of the existing band)
    ]
    if air:
        # synthesize subtle high harmonics — the only way to add "studio air"
        # to a 24kHz source whose real spectrum stops at 12kHz.
        parts.append("aexciter=amount=2.0:blend=2:freq=7500:ceil=16000")
    return ",".join(parts)


def measure(in_path: str, pre: str, lufs: float, tp: float, lra: float) -> dict:
    """Pass 1: run the pre-chain + a measuring loudnorm, parse its JSON."""
    af = f"{pre},loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json"
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", in_path, "-af", af, "-f", "null", "-"],
        capture_output=True, text=True,
    )
    # the JSON block is the last {...} on stderr
    err = p.stderr
    start = err.rfind("{")
    end = err.rfind("}")
    if start == -1 or end == -1:
        sys.exit(f"loudnorm measure failed:\n{err[-1500:]}")
    return json.loads(err[start:end + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--lufs", type=float, default=-16.0,
                    help="integrated target (-16 VO stem, -14 standalone YT, -23 ref clip)")
    ap.add_argument("--tp", type=float, default=-1.5, help="true-peak ceiling dBTP")
    ap.add_argument("--lra", type=float, default=8.0, help="target loudness range")
    ap.add_argument("--denoise", action="store_true", help="add broadband denoise (raw recordings)")
    ap.add_argument("--no-air", dest="air", action="store_false", help="skip the exciter")
    ap.add_argument("--sr", type=int, default=48000)
    args = ap.parse_args()

    pre = pre_chain(args.denoise, args.air, args.sr)
    m = measure(args.infile, pre, args.lufs, args.tp, args.lra)
    print(f"  input: {m['input_i']} LUFS, TP {m['input_tp']} dBTP, LRA {m['input_lra']}")

    # dynamic (NOT linear) two-pass: respects the true-peak ceiling via loudnorm's
    # own TP limiter; final alimiter is a belt-and-suspenders safety catch.
    af = (f"{pre},loudnorm=I={args.lufs}:TP={args.tp}:LRA={args.lra}:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']},"
          f"alimiter=limit={10**(args.tp/20):.4f}:level=disabled")
    Path(args.outfile).parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-i", args.infile, "-af", af,
         "-ar", str(args.sr), "-c:a", "pcm_s16le", args.outfile],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        sys.exit(f"master render failed:\n{p.stderr[-1500:]}")

    # report the result
    out_m = measure(args.outfile, f"aresample={args.sr}", args.lufs, args.tp, args.lra)
    print(f"  output: {out_m['input_i']} LUFS, TP {out_m['input_tp']} dBTP, "
          f"LRA {out_m['input_lra']}  →  {args.outfile}")


if __name__ == "__main__":
    main()
