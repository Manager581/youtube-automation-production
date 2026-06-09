#!/usr/bin/env python3
"""
gen_dunk_clips.py — Generate the Dunkleosteus creature clips with LTX-Video,
ONE AT A TIME (MPS-safe: never run two torch/MPS processes at once on the M5).

Reads the storyboard, runs tools/ltx-video/inference.py per shot via the
ltx_env interpreter, writes footage/dunkleosteus/dunk_<id>.mp4. Skips shots
whose output already exists (resume-friendly). Prints per-clip wall time.

Usage:
  PYTORCH_ENABLE_MPS_FALLBACK=1 venv/bin/python scripts/gen_dunk_clips.py \
    --storyboard storyboards/dunkleosteus_storyboard.json \
    --out-dir footage/dunkleosteus \
    --width 512 --height 288 --frames 97 --steps 8 \
    [--only sh01_hook_jaw]   # generate a single shot (prototype)
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LTX = ROOT / "tools" / "ltx-video"
PY = LTX / "ltx_env.nosync" / "bin" / "python"   # direct .nosync path (iCloud-excluded; symlink is unreliable)
CONFIG = LTX / "configs" / "ltxv-2b-minimal.yaml"
NEG = ("blurry, low quality, distorted anatomy, extra fins, six eyes, cartoon, "
       "illustration, text, watermark, logo, human, scuba diver, jpeg artifacts, "
       "warping, melting")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--height", type=int, default=288)
    ap.add_argument("--frames", type=int, default=97)      # ~4s @ 24fps; (8k+1)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--python", default=str(PY))
    ap.add_argument("--only", default=None, help="generate only this shot id")
    args = ap.parse_args()

    shots = json.load(open(args.storyboard))["shots"]
    if args.only:
        shots = [s for s in shots if s["id"] == args.only]
        if not shots:
            sys.exit(f"shot {args.only} not found")
    out_dir = (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK="1", TOKENIZERS_PARALLELISM="false")
    done, total_t = 0, time.time()
    for i, shot in enumerate(shots, 1):
        out = out_dir / f"dunk_{shot['id']}.mp4"
        if out.exists() and out.stat().st_size > 10_000:
            print(f"[{i}/{len(shots)}] SKIP {out.name} (exists)")
            done += 1
            continue
        # LTX treats --output_path as a DIRECTORY and writes video_output_*.mp4
        # inside it. Generate into a per-shot temp dir, then move to the final name.
        tmp_out = out_dir / f"_tmp_{shot['id']}"
        cmd = [
            args.python, "inference.py",
            "--prompt", shot["prompt"],
            "--negative_prompt", NEG,
            "--height", str(args.height), "--width", str(args.width),
            "--num_frames", str(args.frames), "--frame_rate", str(args.fps),
            "--seed", str(args.seed),
            "--pipeline_config", str(CONFIG),
            "--output_path", str(tmp_out),
        ]
        print(f"[{i}/{len(shots)}] GEN {out.name} :: {shot['prompt'][:60]}…", flush=True)
        t0 = time.time()
        r = subprocess.run(cmd, cwd=str(LTX), env=env)
        dt = time.time() - t0
        produced = sorted(tmp_out.glob("*.mp4")) if tmp_out.exists() else []
        if produced:
            produced[0].replace(out)
            import shutil; shutil.rmtree(tmp_out, ignore_errors=True)
        ok = out.exists() and out.stat().st_size > 10_000
        print(f"    -> {'OK' if ok else 'FAIL'} in {dt:.0f}s "
              f"(exit {r.returncode})", flush=True)
        if ok:
            done += 1
    print(f"\nDone: {done}/{len(shots)} clips in {time.time()-total_t:.0f}s -> {out_dir}")


if __name__ == "__main__":
    main()
