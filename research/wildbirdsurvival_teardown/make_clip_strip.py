#!/usr/bin/env python3
"""Build the mandatory 3x3 frame strip for EP02 clips (physics / anatomy QA).

Frame-stripping every clip is a hard rule -- an i2v clip that looks fine playing
can still morph a beak, split a bird, or run a blood thread on one frame. The
strip is what makes that visible without scrubbing.

  venv/bin/python research/wildbirdsurvival_teardown/make_clip_strip.py S002 [S003 ...]
  venv/bin/python research/wildbirdsurvival_teardown/make_clip_strip.py --all

Matches the existing grok_test strips: 9 frames evenly spaced across the clip,
laid out 3x3, each stamped with its timestamp.
"""
import glob
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
CLIPS = os.path.join(REPO, "assets", "vampire_finch", "clips")
COLS, ROWS = 3, 3
THUMB_W = 440


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def strip(shot):
    src = os.path.join(CLIPS, f"{shot}.mp4")
    if not os.path.exists(src):
        print(f"  {shot}: no clip on disk — skipped")
        return False
    dur = duration(src)
    n = COLS * ROWS
    # sample inside the clip, avoiding the very first/last frame
    times = [dur * (i + 0.5) / n for i in range(n)]

    with tempfile.TemporaryDirectory() as td:
        thumbs = []
        for i, t in enumerate(times):
            fp = os.path.join(td, f"f{i:02d}.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}",
                            "-i", src, "-frames:v", "1", fp], check=True)
            im = Image.open(fp).convert("RGB")
            h = int(im.height * THUMB_W / im.width)
            im = im.resize((THUMB_W, h), Image.LANCZOS)
            d = ImageDraw.Draw(im)
            label = f"{t:.2f}s"
            d.rectangle([0, 0, 70, 20], fill=(0, 0, 0))
            d.text((5, 5), label, fill=(255, 255, 255))
            thumbs.append(im)

        tw, th = thumbs[0].size
        sheet = Image.new("RGB", (tw * COLS, th * ROWS), (18, 18, 18))
        for i, im in enumerate(thumbs):
            sheet.paste(im, ((i % COLS) * tw, (i // COLS) * th))
        out = os.path.join(CLIPS, f"{shot}_strip.jpg")
        sheet.save(out, "JPEG", quality=88)
        print(f"  {shot}: strip -> {os.path.relpath(out, REPO)} ({sheet.size[0]}x{sheet.size[1]})")
    return True


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args == ["--all"]:
        shots = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(CLIPS, "S*.mp4")))
    else:
        shots = args
    made = sum(strip(s) for s in shots)
    print(f"{made} strip(s) written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
