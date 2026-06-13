#!/usr/bin/env python3
"""
tts_mlx_worker.py — persistent mlx-audio TTS worker for pipeline/voice_generator.py.

Runs inside the mlx lab venv (~/tts-lab/mlx/venv). Loads the model ONCE, then
serves chunk requests as JSON lines on stdin -> JSON lines on stdout, so the
production generator can synthesize hundreds of chunks without per-chunk model
reloads and without mixing mlx into the project venv.

Protocol (one JSON object per line):
  request:  {"text": "...", "ref_audio": "path.wav", "ref_text": "..."|null,
             "out": "path/to/seg.wav"}
  response: {"ok": true, "out": "path/to/seg.wav", "duration_sec": 3.21}
            {"ok": false, "error": "..."}
EOF on stdin exits cleanly.

Smoke test:
  echo '{"text":"Testing the worker.","ref_audio":"assets/voice/voice_neutral_ref.wav","ref_text":null,"out":"/tmp/worker_test.wav"}' | \
    ~/tts-lab/mlx/venv/bin/python scripts/tts_mlx_worker.py \
    --model mlx-community/Chatterbox-TTS-fp16
"""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=2400)
    args = ap.parse_args()

    from mlx_audio.tts.generate import generate_audio
    from mlx_audio.tts.utils import load_model

    model = load_model(model_path=args.model)
    print(json.dumps({"ok": True, "loaded": args.model}), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            out = Path(req["out"])
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory() as td:
                generate_audio(
                    text=req["text"],
                    model=model,
                    ref_audio=req["ref_audio"],
                    ref_text=req.get("ref_text"),
                    output_path=td,
                    file_prefix="seg",
                    join_audio=True,
                    verbose=False,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                )
                segs = sorted(Path(td).glob("seg*.wav"))
                if not segs:
                    raise RuntimeError("model produced no audio")
                shutil.move(str(segs[0]), out)
            import soundfile as sf
            info = sf.info(str(out))
            print(json.dumps({"ok": True, "out": str(out),
                              "duration_sec": round(info.frames / info.samplerate, 3)}),
                  flush=True)
        except Exception as e:  # keep serving; caller decides what to do
            print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}),
                  flush=True)


if __name__ == "__main__":
    main()
