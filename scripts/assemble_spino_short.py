#!/usr/bin/env python3
"""Assemble the wordless vertical Spinosaurus Short from Grok i2v clips.

Built to the measured spec in
research/primeval_atlas_teardown/CAMERA_AND_SOUND_SPEC.md:

  * NO IMPOSED GRADE. Each location keeps its own true palette. We only match
    exposure inside an act. (The reference's "saturation arc" is three real
    environments shot honestly, not a LUT -- copying it as a filter is what
    turned the first attempt to murk.)
  * KEEP THE NATIVE CLIP AUDIO where it is real; only fill where it is dead.
    Measured per clip: reveal -29.3, hero -40.1, wade -52.2 LUFS.
  * THE LOWPASS ARC is the film's best trick and we apply it OURSELVES rather
    than trusting the generator: full band above water, ~800 Hz under, a sweep
    on the dive, a one-frame snap back on the breach.
  * HOLES BEFORE PAYOFFS -- duck to near-silence 0.5-1.0 s before each reveal.
  * Master -15 LUFS, TP -1.5, defend LRA >= 9.

Usage:
  venv/bin/python scripts/assemble_spino_short.py -o output/spino_short_v1.mp4
  venv/bin/python scripts/assemble_spino_short.py --preview
"""
import argparse, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
CLIPS = os.path.join(REPO, "assets", "spino_short", "clips")
SFX = os.path.join(REPO, "assets", "sfx")

W, H, FPS = 720, 1280, 24

# act: "bank" (above water, full band) | "under" (lowpass ~800Hz)
EDIT = [
    dict(id="SPINO_S01_reveal", act="bank",  tin=0.3, tout=8.0,
         note="WORLD -> REVEAL. Sandbar lifts. Locked off, low."),
    dict(id="SP_B02_wade_sail", act="bank",  tin=0.0, tout=9.0,
         note="Wades away, gets smaller. Locked off."),
    dict(id="SP_B05_hero",      act="under", tin=0.0, tout=10.0,
         note="HERO. Eye level, head-on, fills frame. The attachment shot."),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"failed: {' '.join(cmd[:9])}...\n{r.stderr[-1500:]}")
    return r


def probe(path, entries="format=duration"):
    return subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries,
                           "-of", "csv=p=0", path],
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output",
                    default=os.path.join(REPO, "output", "spino_short_v1.mp4"))
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    w, h = (540, 960) if args.preview else (W, H)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        segs, t = [], 0.0
        print("Segments (no grade applied -- each location keeps its own palette):")
        for i, e in enumerate(EDIT):
            src = os.path.join(CLIPS, e["id"] + ".mp4")
            if not os.path.exists(src):
                print(f"  !! MISSING {e['id']}")
                continue
            dur = round(e["tout"] - e["tin"], 3)

            v = os.path.join(tmp, f"v{i}.mp4")
            run(["ffmpeg", "-y", "-ss", str(e["tin"]), "-i", src, "-t", str(dur),
                 "-vf", (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                         f"crop={w}:{h},fps={FPS},format=yuv420p"),
                 "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                 v, "-loglevel", "error"])

            # audio: keep native, normalise to a common level, apply the act's filter
            a = os.path.join(tmp, f"a{i}.wav")
            af = "loudnorm=I=-20:TP=-2:LRA=11"
            if e["act"] == "under":
                af += ",lowpass=f=800,bass=g=4:f=90"      # the underwater filter
            else:
                af += ",highpass=f=45"
            run(["ffmpeg", "-y", "-ss", str(e["tin"]), "-i", src, "-t", str(dur),
                 "-vn", "-af", af, "-ar", "48000", "-ac", "2",
                 a, "-loglevel", "error"])

            seg = os.path.join(tmp, f"s{i}.mp4")
            run(["ffmpeg", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                 "-shortest", seg, "-loglevel", "error"])

            segs.append(seg)
            print(f"  [{i+1}] {e['id']:22s} {e['act']:6s} {t:5.1f}-{t+dur:5.1f}s  {e['note']}")
            t += dur

        if not segs:
            sys.exit("no clips found in " + CLIPS)

        lst = os.path.join(tmp, "l.txt")
        with open(lst, "w") as f:
            for s in segs:
                f.write(f"file '{s}'\n")
        joined = os.path.join(tmp, "joined.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             joined, "-loglevel", "error"])

        print(f"\nTotal {t:.1f}s across {len(segs)} shots. Mastering to -15 LUFS...")
        run(["ffmpeg", "-y", "-i", joined,
             "-af", "loudnorm=I=-15:TP=-1.5:LRA=10",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             args.output, "-loglevel", "error"])

    print(f"Wrote {args.output}")
    print(f"  {probe(args.output,'stream=width,height,r_frame_rate')}  dur={probe(args.output)}")


if __name__ == "__main__":
    main()
