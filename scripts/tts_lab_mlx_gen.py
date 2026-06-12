#!/usr/bin/env python3
"""
tts_lab_mlx_gen.py — chunked mlx-audio generation for the local-TTS shootout.

Loads an MLX TTS model ONCE, generates each blank-line paragraph separately
(the way production chunks anyway), joins with short gaps. This avoids the
~40s single-call cap (Chatterbox) and long-passage pacing rush (Qwen3).

Run with the mlx lab venv (outside iCloud):
  ~/tts-lab/mlx/venv/bin/python scripts/tts_lab_mlx_gen.py \
    --model mlx-community/Chatterbox-TTS-fp16 \
    --text output/tts_shootout/test_passage.txt \
    --ref assets/voice/voice_energized_ref.wav \
    --out output/tts_shootout/C_chatterbox_owner.wav
"""

import argparse
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--ref-text", default=None, help="path to transcript of ref")
    ap.add_argument("--out", required=True)
    ap.add_argument("--gap-sec", type=float, default=0.35)
    ap.add_argument("--max-tokens", type=int, default=2400)
    ap.add_argument("--exaggeration", type=float, default=None)
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    from mlx_audio.tts.generate import generate_audio
    from mlx_audio.tts.utils import load_model

    t0 = time.time()
    model = load_model(model_path=args.model)
    print(f"loaded {args.model} in {time.time()-t0:.1f}s")

    ref_text = Path(args.ref_text).read_text().strip() if args.ref_text else None
    paras = [p.strip() for p in Path(args.text).read_text().split("\n\n") if p.strip()]

    extra = {}
    if args.exaggeration is not None:
        extra["exaggeration"] = args.exaggeration

    parts, sr = [], None
    gen_t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        for i, p in enumerate(paras):
            t = time.time()
            generate_audio(
                text=p,
                model=model,
                ref_audio=args.ref,
                ref_text=ref_text,
                output_path=td,
                file_prefix=f"seg_{i:03d}",
                join_audio=True,
                verbose=False,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                **extra,
            )
            seg_files = sorted(Path(td).glob(f"seg_{i:03d}*.wav"))
            if not seg_files:
                raise RuntimeError(f"no output for paragraph {i}: {p[:50]}")
            audio, sr = sf.read(seg_files[0])
            dur = len(audio) / sr
            wpm = len(p.split()) / dur * 60
            print(f"  [{i+1}/{len(paras)}] {dur:.1f}s ({wpm:.0f} wpm) "
                  f"in {time.time()-t:.1f}s: {p[:55]}…")
            parts.append(audio)
            parts.append(np.zeros(int(sr * args.gap_sec)))

    full = np.concatenate(parts[:-1])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), full, sr)
    total, wall = len(full) / sr, time.time() - gen_t0
    print(f"wrote {out} ({total:.1f}s audio in {wall:.1f}s wall, "
          f"RTF={wall/total:.2f})")


if __name__ == "__main__":
    main()
