#!/usr/bin/env python3
"""
proto_layered_composite.py — PROTOTYPE of the viral video's engine, FULLY
LOADED: a cut-out creature on its own animated layer composited INTO real
moving footage, plus the polish layers the owner asked for —
  • virtual CAMERA moves (stalk push-in, anticipation pull, SLAM-zoom on bite)
  • MOTION BLUR scaled to lunge speed
  • predator-vision crosshair that SWEEPS + locks then fades (POV = you're the
    rex, so the graphic targets the STRIKE POINT, not the creature)
  • narration-synced kinetic TEXT
  • grade (warm tone + vignette + grain) + chromatic shake on impact
  • real SFX mix: footstep thuds, lunge whoosh, layered bite crunch, rumble bed
One beat: the street strike, "...One bite." Out: output/proto_strike_540p.mp4
"""
import math
import subprocess
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parents[1]
BG = sorted(Path('/tmp/bg_frames').glob('f*.png'))
FPS, W, H = 30, 960, 540
INK, ORANGE = (16, 13, 10), (245, 130, 32)
SFX = ROOT / 'assets/sfx'
font = lambda s: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', s)

cut = Image.open(ROOT / 'assets/trex_pilot/cutouts/c_strike_blur_cut.png').convert('RGBA')
_a = np.array(cut)[:, :, 3]; ys, xs = np.where(_a > 20)
cut = cut.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
CW, CH = cut.size
OUT = ROOT / 'output/proto_frames'; OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob('*.png'): f.unlink()

BITE = 6.0
N = len(BG)
GOLD = np.array([1.06, 1.00, 0.90])      # warm grade multiplier


def smooth(t, a, b):
    if t <= a: return 0.0
    if t >= b: return 1.0
    x = (t - a) / (b - a); return x * x * (3 - 2 * x)


# vignette + grain, prebuilt
_vig = Image.new('L', (W, H), 0)
_vd = ImageDraw.Draw(_vig)
_vd.ellipse((-W * 0.25, -H * 0.25, W * 1.25, H * 1.25), fill=255)
_vig = _vig.filter(ImageFilter.GaussianBlur(120))
VIG = np.asarray(_vig, np.float32)[..., None] / 255.0 * 0.45 + 0.55

for i, bgp in enumerate(BG):
    t = i / FPS
    lunge = smooth(t, 3.5, BITE)
    appr = smooth(t, 1.2, 3.5)

    # ── virtual CAMERA: push-in during stalk, tiny pull at anticipation,
    #    SLAM-zoom on the bite, settle ──
    cam = 1.0 + 0.12 * smooth(t, 0, 5.4) - 0.05 * smooth(t, 5.4, 5.9)
    if t >= BITE:
        cam += 0.22 * (1 - smooth(t, BITE, BITE + 0.5))     # SLAM then ease
    frame = Image.open(bgp).convert('RGBA')
    bw, bh = int(W * cam), int(H * cam)
    frame = frame.resize((bw, bh), Image.LANCZOS).crop(
        ((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H))

    # ── creature layer: approach -> lunge, with motion blur on speed ──
    scale_h = (0.42 + 0.16 * appr + 0.95 * lunge ** 1.8) * H
    if t >= BITE:
        scale_h = 1.45 * H * (1 - 0.05 * smooth(t, BITE, BITE + 0.5))
    bob = math.sin(t * 7.5) * (3 + 9 * appr)
    cw, ch = max(int(CW * scale_h / CH), 2), max(int(scale_h), 2)
    cre = cut.resize((cw, ch), Image.LANCZOS)
    speed = (lunge - smooth(t - 1 / FPS, 3.5, BITE)) * FPS      # d(lunge)/dt proxy
    if speed > 0.04 and t < BITE:                              # directional-ish blur
        k = int(min(speed * 60, 14))
        cre = cre.filter(ImageFilter.GaussianBlur(k))
    if BITE <= t < BITE + 2 / FPS:
        cre = cre.resize((int(cw * 1.07), int(ch * 1.07)), Image.LANCZOS)
    cx = W // 2 + int(40 * (appr - lunge))
    cy = int(H * 0.60 + bob)
    frame.alpha_composite(cre, (cx - cre.width // 2, cy - cre.height // 2))

    # breath fog at the snout
    if appr > 0.2:
        puff = math.sin(t * 2.1) * 0.5 + 0.5
        fog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        r = int(26 + 30 * puff + 40 * lunge)
        fx, fy = cx + int(cre.width * 0.16), cy - int(cre.height * 0.18)
        ImageDraw.Draw(fog).ellipse((fx - r, fy - r, fx + r, fy + r),
                                    fill=(235, 235, 240, int(70 * puff)))
        frame.alpha_composite(fog.filter(ImageFilter.GaussianBlur(18)))

    d = ImageDraw.Draw(frame, 'RGBA')
    # ── predator-vision crosshair: sweeps onto the STRIKE POINT (prey), locks
    #    over 0.5s, then fades — POV is the rex, so it targets the kill spot ──
    pv = smooth(t, 3.3, 3.8) * (1 - smooth(t, 4.3, 4.8))
    if pv > 0.02:
        tx_, ty_ = cx - int(cre.width * 0.20), int(H * 0.72)    # ahead/below = prey
        s = int(70 - 26 * smooth(t, 3.3, 3.8))
        col = ORANGE + (int(220 * pv),)
        for ox, oy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            X, Y = tx_ + ox * s, ty_ + oy * s
            d.line((X, Y, X - ox * 22, Y), fill=col, width=3)
            d.line((X, Y, X, Y - oy * 22), fill=col, width=3)
        if smooth(t, 3.6, 3.9) > 0.5:
            d.text((tx_ - s, ty_ - s - 24), 'TARGET', font=font(20), fill=ORANGE + (int(220 * pv),))

    # ── grade: warm tone + vignette + grain ──
    arr = np.asarray(frame.convert('RGB'), np.float32)
    arr = np.clip(arr * GOLD * VIG, 0, 255)
    if t >= BITE and (t - BITE) < 0.18:                        # chromatic split on impact
        sh = int(6 * (1 - (t - BITE) / 0.18))
        arr[:, sh:, 0] = arr[:, :W - sh, 0]
        arr[:, :W - sh, 2] = arr[:, sh:, 2]
    arr = np.clip(arr + np.sin(np.arange(W) * 12.9 + i)[None, :, None] * 2.0, 0, 255)  # light grain
    frame = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(frame, 'RGBA')

    # ── BITE: flash + screen shake + kinetic stamp; then follow-text ──
    if t >= BITE:
        ft = t - BITE
        if ft < 0.10:
            frame.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - ft / 0.10)))))
        dec = max(0, 1 - ft / 0.45)
        sx, sy = int(16 * dec * math.sin(ft * 90)), int(12 * dec * math.cos(ft * 70))
        frame = frame.transform((W, H), Image.AFFINE, (1, 0, sx, 0, 1, sy))
        d = ImageDraw.Draw(frame, 'RGBA')
        st = smooth(t, BITE, BITE + 0.18)
        sz = int(150 * (1.6 - 0.6 * st))
        msg = 'ONE BITE'
        tb = d.textbbox((0, 0), msg, font=font(sz))
        tx, ty = (W - (tb[2] - tb[0])) / 2, H * 0.34
        d.rectangle((tx - 24, ty - 12, tx + (tb[2] - tb[0]) + 24, ty + (tb[3] - tb[1]) + 26),
                    fill=ORANGE + (int(235 * st),))
        d.text((tx, ty - tb[1]), msg, font=font(sz), fill=INK)

    frame.convert('RGB').save(OUT / f'{i:04d}.png')


# ── audio: VO + SFX mix (numpy, like the main renderer) ──
SR = 48000


def load(p, sr=SR):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'f32le',
                        '-ac', '1', '-ar', str(sr), '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).copy()


vo = load('/tmp/proto_vo.wav')
dur = max(len(vo) / SR, N / FPS)
mix = np.zeros(int(dur * SR) + SR, np.float32)
mix[:len(vo)] += vo * 1.0


def place(name, t, vol):
    s = load(SFX / name)
    i0 = int(t * SR)
    mix[i0:i0 + len(s)] += s[:len(mix) - i0] * vol


# rumble bed (looped low), footsteps on the bob beats, whoosh into bite, crunch
bed = load(SFX / 'rumble_01_loud.wav')
bed = np.tile(bed, int(len(mix) / len(bed)) + 1)[:len(mix)]
mix += bed * 0.10
for ft in [1.0, 1.8, 2.6, 3.3]:                 # footstep thuds during stalk
    place('impact_01_loud.wav', ft, 0.22)
place('whoosh_03_loud.wav', BITE - 0.5, 0.5)    # lunge whoosh swells into the bite
place('body_impact_01_loud.wav', BITE, 0.85)    # layered bite crunch
place('impact_new_loud.wav', BITE, 0.7)
mix = mix / max(np.max(np.abs(mix)), 1) * 0.97
wav = '/tmp/proto_mix.wav'
with wave.open(wav, 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).clip(-32768, 32767).astype(np.int16).tobytes())

subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                '-i', str(OUT / '%04d.png'), '-i', wav,
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                '-c:a', 'aac', '-shortest',
                str(ROOT / 'output/proto_strike_540p.mp4')], check=True)
print('wrote output/proto_strike_540p.mp4')
