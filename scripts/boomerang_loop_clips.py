#!/usr/bin/env python3
"""
boomerang_loop_clips.py — Turn short LTX i2v clips into seamless, beat-filling
loops so the FFmpeg renderer never has to freeze-extend (tpad) the last frame.

For each dunk_<shot_id>.mp4 in --in-dir (shot ids from the storyboard), build a
boomerang (forward + reverse, which loops seamlessly because the last reversed
frame == the first forward frame) and repeat it to >= --target seconds. Writes
loops_v2/dunk_<shot_id>.mp4. Resume-friendly (skips finished outputs).

Usage:
  venv.nosync/bin/python scripts/boomerang_loop_clips.py \
    --storyboard storyboards/dunkleosteus_storyboard_v2.json \
    --in-dir footage/dunkleosteus --out-dir footage/dunkleosteus/loops_v2 \
    --target 24 [--only sh01_guillotine_jaws]
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries",
                        "format=duration", "-of", "default=nw=1:nk=1", str(p)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def boomerang(src, dst, target):
    """fwd+reverse, then stream-loop the boomerang to >= target seconds."""
    with tempfile.TemporaryDirectory() as td:
        bm = Path(td) / "bm.mp4"
        # forward + reversed, concatenated -> seamless boomerang (no audio)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src),
             "-filter_complex", "[0:v]split[f][t];[t]reverse[r];[f][r]concat=n=2:v=1[v]",
             "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-crf", "18", str(bm)], check=True)
        one = dur(bm) or 1.0
        loops = max(1, int(target / one) + 1)        # enough repeats to exceed target
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-stream_loop", str(loops - 1),
             "-i", str(bm), "-t", f"{target:.2f}", "-an",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(dst)],
            check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--target", type=float, default=24.0)
    ap.add_argument("--ext", default="mp4")
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    shots = json.load(open(args.storyboard))["shots"]
    if args.only:
        shots = [s for s in shots if s["id"] == args.only]
    in_dir = (ROOT / args.in_dir).resolve()
    out_dir = (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    done = skipped = missing = 0
    for shot in shots:
        sid = shot["id"]
        src = in_dir / f"dunk_{sid}.{args.ext}"
        dst = out_dir / f"dunk_{sid}.{args.ext}"
        if not src.exists():
            print(f"  MISSING src dunk_{sid} (i2v not done yet) — skip")
            missing += 1
            continue
        if dst.exists() and dur(dst) >= args.target - 1:
            print(f"  SKIP dunk_{sid} (loop exists)")
            skipped += 1
            continue
        print(f"  BOOMERANG dunk_{sid} ({dur(src):.1f}s -> {args.target:.0f}s)", flush=True)
        try:
            boomerang(src, dst, args.target)
            done += 1
        except subprocess.CalledProcessError as e:
            print(f"    FAIL dunk_{sid}: {e}")
    print(f"\nLoops: {done} built, {skipped} skipped, {missing} missing -> {out_dir}")


if __name__ == "__main__":
    main()
