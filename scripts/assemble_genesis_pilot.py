#!/usr/bin/env python3
"""Assemble the Christ Cares Genesis-overview pilot: 14 stills + Brian VO.

Per-video assembler in the assemble_spino_short.py tradition. Shot timing comes
from the whisperx alignment: each script paragraph's span drives its still's
hold. Ken Burns alternates zoom-in/zoom-out per shot so no two adjacent moves
match. No music bed in the pilot (owner: hymns optional / can ship without).

Usage:
  venv/bin/python scripts/assemble_genesis_pilot.py -o output/christ_cares_genesis_overview_v1.mp4
"""
import argparse, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
STILLS = os.path.join(REPO, "assets", "christ_cares", "genesis_overview")
NARRATION = os.path.join(REPO, "audio", "christ_cares", "genesis_overview.wav")
ALIGNMENT = os.path.join(REPO, "audio", "christ_cares", "genesis_overview_whisperx.json")
SCRIPT_TXT = os.path.join(REPO, "scripts", "christ_cares_genesis_overview_clean.txt")

W, H, FPS = 1920, 1080, 30
TAIL_HOLD = 1.0  # extra hold on the last shot after the final word

# paragraph index -> still (S01a beats S01b on drama; both passed the gate)
SHOT_FILES = ["genesis_S01a.png", "genesis_S02.png", "genesis_S03.png",
              "genesis_S04.png", "genesis_S05.png", "genesis_S06.png",
              "genesis_S07.png", "genesis_S08.png", "genesis_S09.png",
              "genesis_S10.png", "genesis_S11.png", "genesis_S12.png",
              "genesis_S13.png", "genesis_S14.png"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"failed: {' '.join(cmd[:8])}...\n{r.stderr[-1500:]}")
    return r


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def paragraph_spans():
    paras = [p for p in open(SCRIPT_TXT).read().split("\n\n") if p.strip()]
    counts = [len(p.split()) for p in paras]
    data = json.load(open(ALIGNMENT))
    words = data["words"] if isinstance(data, dict) else data
    if sum(counts) != len(words):
        sys.exit(f"word-count mismatch: script {sum(counts)} vs alignment {len(words)}")
    audio_dur = probe_duration(NARRATION)
    spans, idx = [], 0
    for i, c in enumerate(counts):
        start = 0.0 if i == 0 else words[idx]["start"]
        idx += c
        end = words[idx]["start"] if idx < len(words) else audio_dur + TAIL_HOLD
        spans.append((start, end))
    # each shot runs from its paragraph's first word to the next paragraph's first word
    return spans, audio_dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=os.path.join(REPO, "output", "christ_cares_genesis_overview_v1.mp4"))
    args = ap.parse_args()

    if len(SHOT_FILES) != 14:
        sys.exit("expected 14 shots")
    spans, audio_dur = paragraph_spans()
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        seg_paths = []
        for i, (fname, (start, end)) in enumerate(zip(SHOT_FILES, spans)):
            dur = end - start
            frames = max(2, round(dur * FPS))
            still = os.path.join(STILLS, fname)
            if not os.path.exists(still):
                sys.exit(f"missing still: {still}")
            # alternate slow zoom-in / zoom-out; ±10% over the hold
            if i % 2 == 0:
                zexpr = f"1+0.10*on/{frames}"
            else:
                zexpr = f"1.10-0.10*on/{frames}"
            seg = os.path.join(td, f"seg_{i:02d}.mp4")
            vf = (f"scale=2112:1188,zoompan=z='{zexpr}':"
                  f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d={frames}:s={W}x{H}:fps={FPS}")
            run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", still,
                 "-vf", vf, "-frames:v", str(frames),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                 "-pix_fmt", "yuv420p", seg])
            seg_paths.append(seg)
            print(f"  seg {i+1:02d}/14 {fname} {dur:.2f}s ({frames}f)")

        concat_list = os.path.join(td, "list.txt")
        with open(concat_list, "w") as f:
            for p in seg_paths:
                f.write(f"file '{p}'\n")
        video_only = os.path.join(td, "video.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", video_only])

        total = sum(e - s for s, e in spans)
        fade_start = max(0.0, total - 1.0)
        run(["ffmpeg", "-y", "-v", "error", "-i", video_only, "-i", NARRATION,
             "-af", f"apad=pad_dur={TAIL_HOLD + 0.5},atrim=0:{total},afade=t=out:st={fade_start}:d=1.0",
             "-vf", f"fade=t=out:st={fade_start}:d=1.0",
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", args.output])

    out_dur = probe_duration(args.output)
    print(f"wrote {args.output}: {out_dur:.2f}s (narration {audio_dur:.2f}s + {TAIL_HOLD}s tail)")


if __name__ == "__main__":
    main()
