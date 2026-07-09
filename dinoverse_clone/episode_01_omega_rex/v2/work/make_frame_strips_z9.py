#!/usr/bin/env python3
"""Zone 9: extract 2fps frames per clip + build a labelled contact sheet for adversarial
physics QA. Full-res frames kept per-clip (qa_z9/<shot>_frames/) for flag adjudication."""
import subprocess, os, glob, math
from PIL import Image, ImageDraw

BASE = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2"
CLIPS = f"{BASE}/clips"
OUT = f"{BASE}/work/qa_z9"
os.makedirs(OUT, exist_ok=True)
SHOTS = ["S69","S70","S71","S72","S73","S74","S75","S76","S77","S78"]

def frames_for(shot):
    fdir = f"{OUT}/{shot}_frames"
    os.makedirs(fdir, exist_ok=True)
    for f in glob.glob(f"{fdir}/*.png"): os.remove(f)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"{CLIPS}/{shot}.mp4",
                    "-vf","fps=2","-q:v","2",f"{fdir}/f_%02d.png"], check=True)
    return sorted(glob.glob(f"{fdir}/*.png"))

def contact_sheet(shot, frames):
    cols = 4
    tw = 480
    thumbs = []
    for i,fp in enumerate(frames):
        im = Image.open(fp).convert("RGB")
        th = int(im.height * tw / im.width)
        im = im.resize((tw, th))
        d = ImageDraw.Draw(im)
        label = f"{shot} f{i:02d}  t={i*0.5:.1f}s"
        d.rectangle([0,0,190,22], fill=(0,0,0))
        d.text((4,4), label, fill=(255,255,0))
        thumbs.append(im)
    rows = math.ceil(len(thumbs)/cols)
    thh = thumbs[0].height; tw2 = thumbs[0].width
    sheet = Image.new("RGB",(cols*tw2, rows*thh),(20,20,20))
    for i,im in enumerate(thumbs):
        r,c = divmod(i,cols)
        sheet.paste(im,(c*tw2, r*thh))
    out = f"{OUT}/{shot}_sheet.png"
    sheet.save(out)
    return out, len(frames)

for s in SHOTS:
    fr = frames_for(s)
    out,n = contact_sheet(s, fr)
    print(f"{s}: {n} frames -> {out}")
print("Done.")
