#!/usr/bin/env python3
"""
build_dunk_paper_edit.py — Turn the F5-TTS narration manifest + the Dunkleosteus
storyboard into a renderer-ready paper edit (Spinosnack-style proof).

Maps each narration speech segment to a storyboard shot (in order, proportional),
merges consecutive segments sharing a shot into one beat, and emits contiguous
beats covering [0, total_duration] so the FFmpeg renderer has no timeline gaps.

visual_file is written as an ABSOLUTE path so resolve_visual() finds the clip
regardless of the hardcoded breaking_law FOOTAGE_DIRS.

Usage:
  venv/bin/python scripts/build_dunk_paper_edit.py \
    --manifest audio/dunkleosteus/narration_manifest.json \
    --storyboard storyboards/dunkleosteus_storyboard.json \
    --clips-dir footage/dunkleosteus \
    --out storyboards/dunkleosteus_paper_edit.json \
    [--max-duration 45]   # optional: truncate to a vertical-slice proof
"""
import argparse, json, math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--clips-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-duration", type=float, default=None)
    ap.add_argument("--ext", default="mp4")
    ap.add_argument("--stills-dir", default=None,
                    help="proof mode: assign image files from this dir (Ken Burns) "
                         "to beats round-robin instead of LTX clips")
    args = ap.parse_args()

    stills = []
    if args.stills_dir:
        sd = (PROJECT_ROOT / args.stills_dir).resolve()
        stills = sorted(str(p) for p in sd.glob("*")
                        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
                        and "errors" not in p.name.lower())

    manifest = json.load(open(args.manifest))
    storyboard = json.load(open(args.storyboard))
    shots = storyboard["shots"]
    clips_dir = (PROJECT_ROOT / args.clips_dir).resolve()

    speech = [s for s in manifest["segments"] if s["type"] == "speech"]
    total = float(manifest["total_duration_sec"])
    if not speech:
        raise SystemExit("no speech segments in manifest")

    n_seg, n_shot = len(speech), len(shots)

    # Assign each speech segment a shot index, preserving order (proportional).
    for i, seg in enumerate(speech):
        seg["_shot"] = min(n_shot - 1, int(i * n_shot / n_seg))

    # Group consecutive segments sharing a shot into one beat.
    beats = []
    i = 0
    while i < n_seg:
        j = i
        while j + 1 < n_seg and speech[j + 1]["_shot"] == speech[i]["_shot"]:
            j += 1
        shot = shots[speech[i]["_shot"]]
        text = " ".join(s["text"] for s in speech[i:j + 1])
        if stills:                               # PROOF mode: real stills + Ken Burns
            visual_file = stills[len(beats) % len(stills)]
            visual_type, zoom = "still", 2.0
        else:                                    # LTX clip mode
            visual_file = str(clips_dir / f"dunk_{shot['id']}.{args.ext}")
            visual_type, zoom = "video", 0.0
        beats.append({
            "beat_id": f"beat_{len(beats):04d}",
            "shot_id": shot["id"],
            "text": text,
            "start_sec": float(speech[i]["start_sec"]),
            "end_sec": float(speech[j]["end_sec"]),
            "visual_file": visual_file,          # absolute -> resolve_visual finds it
            "visual_type": visual_type,
            "clip_audio": "mute",
            "tension_level": 0.6,
            "zoom_speed_pct_per_sec": zoom,
            "prompt": shot["prompt"],            # the AI-clip prompt for the LTX upgrade
        })
        i = j + 1

    # Make beats contiguous + cover [0, total]: each beat ends where the next begins.
    beats[0]["start_sec"] = 0.0
    for k in range(len(beats) - 1):
        beats[k]["end_sec"] = beats[k + 1]["start_sec"]
    beats[-1]["end_sec"] = total

    # Optional vertical-slice truncation for a fast proof render.
    if args.max_duration:
        kept = [b for b in beats if b["start_sec"] < args.max_duration]
        if kept:
            kept[-1]["end_sec"] = min(kept[-1]["end_sec"], args.max_duration)
        beats = kept

    for b in beats:
        b["duration"] = round(b["end_sec"] - b["start_sec"], 3)

    out = {
        "beats": beats,
        "stats": {
            "beat_count": len(beats),
            "total_duration_sec": round(beats[-1]["end_sec"], 3) if beats else 0,
            "unique_clips": sorted({b["shot_id"] for b in beats}),
        },
        "_version": "dunkleosteus_proof_v1",
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"Wrote {args.out}: {len(beats)} beats, "
          f"{out['stats']['total_duration_sec']}s, "
          f"{len(out['stats']['unique_clips'])} unique clips")
    for b in beats:
        print(f"  {b['beat_id']} {b['start_sec']:6.2f}-{b['end_sec']:6.2f}s "
              f"[{b['shot_id']}] {b['text'][:50]}…")


if __name__ == "__main__":
    main()
