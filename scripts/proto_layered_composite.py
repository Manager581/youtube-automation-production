#!/usr/bin/env python3
"""
proto_layered_composite.py — PROTOTYPE of the viral video's actual engine:
a CUT-OUT creature on its own animated layer, composited INTO real moving
footage, with a narration-synced motion graphic + impact/shake. NOT Ken Burns
on a flat still — separate background + clipped subject + overlay layers, each
moving independently. One beat: the street strike, "...One bite."

Out: output/proto_strike_540p.mp4
"""
import math
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BG = sorted((Path('/tmp/bg_frames')).glob('f*.png'))
FPS = 30
W, H = 960, 540
INK = (16, 13, 10)
ORANGE = (245, 130, 32)
F_BLACK = '/System/Library/Fonts/Supplemental/Arial Black.ttf'
font = lambda s: ImageFont.truetype(F_BLACK, s)

# cut-out creature (strike), cropped to its matte bbox
cut = Image.open(ROOT / 'assets/trex_pilot/cutouts/c_strike_blur_cut.png').convert('RGBA')
a = np.array(cut)[:, :, 3]
ys, xs = np.where(a > 20)
cut = cut.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
CW, CH = cut.size

OUT = ROOT / 'output/proto_frames'
OUT.mkdir(parents=True, exist_ok=True)

# ── beat timeline (s), mapped to the VO span 218.4–225.7 ──
#  0.0  "whole block moves at once"     -> creature stalks, reticle hunts
#  1.2  "You catch the first one"       -> approach begins
#  3.5  "before it clears the curb"     -> LUNGE (fast scale-in)
#  6.0  "One bite."                     -> BITE: flash + shake + stamp
BITE = 6.0
N = len(BG)


def smooth(t, a, b):           # 0..1 ease across [a,b]
    if t <= a: return 0.0
    if t >= b: return 1.0
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)


for i, bgp in enumerate(BG):
    t = i / FPS
    frame = Image.open(bgp).convert('RGBA')

    # parallax: background slow push-in (its own motion, opposite the creature)
    pz = 1.0 + 0.10 * smooth(t, 0, 7.3)
    bw, bh = int(W * pz), int(H * pz)
    frame = frame.resize((bw, bh), Image.LANCZOS).crop(
        ((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H))
    d = ImageDraw.Draw(frame, 'RGBA')

    # ── creature layer: approach (0.45h) -> lunge (1.55h past frame) ──
    appr = smooth(t, 1.2, 3.5)            # walk in
    lunge = smooth(t, 3.5, BITE)          # accelerate toward camera
    scale_h = (0.42 + 0.16 * appr + 0.95 * (lunge ** 1.8)) * H
    bob = math.sin(t * 7.5) * (3 + 9 * appr)        # step bob, grows on approach
    if t >= BITE:                                    # recoil settle after bite
        scale_h = 1.45 * H * (1 - 0.06 * smooth(t, BITE, BITE + 0.5))
    cw = int(CW * scale_h / CH)
    ch = int(scale_h)
    cre = cut.resize((max(cw, 2), max(ch, 2)), Image.LANCZOS)

    # bite scale-punch (2 frames)
    if BITE <= t < BITE + 2 / FPS:
        cre = cre.resize((int(cre.width * 1.07), int(cre.height * 1.07)), Image.LANCZOS)

    cx = W // 2 + int(40 * (appr - lunge))           # drift L as it nears
    cy = int(H * 0.60 + bob)                          # anchored low (looming)
    frame.alpha_composite(cre, (cx - cre.width // 2, cy - cre.height // 2))

    # breath fog puff near where the snout is (upper-center of the cutout)
    if appr > 0.2:
        puff = (math.sin(t * 2.1) * 0.5 + 0.5)
        fog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fog)
        r = int(26 + 30 * puff + 40 * lunge)
        fx, fy = cx + int(cre.width * 0.16), cy - int(cre.height * 0.18)
        fd.ellipse((fx - r, fy - r, fx + r, fy + r), fill=(235, 235, 240, int(70 * puff)))
        frame.alpha_composite(fog.filter(ImageFilter.GaussianBlur(18)))

    # ── motion-graphic layer: reticle that hunts then LOCKS on the lunge ──
    if t < BITE:
        lock = smooth(t, 3.3, 4.2)
        bx, by = cx, cy - int(cre.height * 0.12)
        s = int(150 - 70 * lock + (1 - lock) * 30 * math.sin(t * 3))
        col = ORANGE + (int(120 + 135 * lock),)
        for ox, oy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:        # corner brackets
            X, Y = bx + ox * s, by + oy * s
            d.line((X, Y, X - ox * 34, Y), fill=col, width=4)
            d.line((X, Y, X, Y - oy * 34), fill=col, width=4)
        if lock > 0.4:
            d.text((bx - s, by - s - 30), 'LOCK', font=font(26), fill=ORANGE)
            rng = max(0, int(6 * (1 - smooth(t, 1.2, BITE))))
            d.text((bx + s - 70, by + s + 6), f'{rng} BLOCKS', font=font(22), fill=ORANGE)

    # ── BITE: white flash + screen shake + kinetic stamp ──
    if t >= BITE:
        ft = t - BITE
        if ft < 0.10:                                 # flash
            fl = Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - ft / 0.10))))
            frame.alpha_composite(fl)
        # deterministic shake (no RNG), decaying
        dec = max(0, 1 - ft / 0.45)
        sx = int(16 * dec * math.sin(ft * 90))
        sy = int(12 * dec * math.cos(ft * 70))
        frame = frame.transform((W, H), Image.AFFINE, (1, 0, sx, 0, 1, sy))
        d = ImageDraw.Draw(frame, 'RGBA')
        # "ONE BITE" stamp slams in
        st = smooth(t, BITE, BITE + 0.18)
        ssz = int(150 * (1.6 - 0.6 * st))
        stamp = font(ssz)
        msg = 'ONE BITE'
        tb = d.textbbox((0, 0), msg, font=stamp)
        tx, ty = (W - (tb[2] - tb[0])) / 2, H * 0.36
        d.rectangle((tx - 24, ty - 12, tx + (tb[2] - tb[0]) + 24, ty + (tb[3] - tb[1]) + 26),
                    fill=ORANGE + (int(235 * st),))
        d.text((tx, ty - tb[1]), msg, font=stamp, fill=INK)

    frame.convert('RGB').save(OUT / f'{i:04d}.png')

# encode + VO
subprocess.run([
    'ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
    '-i', str(OUT / '%04d.png'), '-i', '/tmp/proto_vo.wav',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
    '-c:a', 'aac', '-shortest',
    str(ROOT / 'output/proto_strike_540p.mp4')], check=True)
print('wrote output/proto_strike_540p.mp4')
