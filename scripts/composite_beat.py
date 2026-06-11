#!/usr/bin/env python3
"""
composite_beat.py — the reusable "loaded composite beat" engine generalized
from the strike prototype. Each creature beat is a CONFIG, not a script:
cut-out creature on its own animated layer (motion preset) composited into a
real moving background (camera preset), + configurable graphic + narration-
synced kinetic text + real SFX mix + shared cinematic grade.

render_beat(cfg, out_mp4). Configs at the bottom; run:
  venv/bin/python scripts/composite_beat.py strike stumble
"""
import math
import subprocess
import sys
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FPS, W, H = 30, 960, 540
INK, ORANGE, RED = (16, 13, 10), (245, 130, 32), (200, 40, 24)
SFX = ROOT / 'assets/sfx'
SR = 48000
font = lambda s: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', s)
GOLD = np.array([1.06, 1.00, 0.90])

_vig = Image.new('L', (W, H), 0)
ImageDraw.Draw(_vig).ellipse((-W * .25, -H * .25, W * 1.25, H * 1.25), fill=255)
VIG = np.asarray(_vig.filter(ImageFilter.GaussianBlur(120)), np.float32)[..., None] / 255 * .45 + .55


def smooth(t, a, b):
    if t <= a: return 0.0
    if t >= b: return 1.0
    x = (t - a) / (b - a); return x * x * (3 - 2 * x)


def load_cut(path):
    cut = Image.open(path).convert('RGBA')
    a = np.array(cut)[:, :, 3]; ys, xs = np.where(a > 20)
    return cut.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def dir_blur(img, dx, dy, n=6):
    """cheap directional motion blur: average n shifted copies along (dx,dy)"""
    if abs(dx) < 1 and abs(dy) < 1:
        return img
    acc = Image.new('RGBA', img.size, (0, 0, 0, 0))
    for j in range(n):
        f = (j / (n - 1) - 0.5)
        off = img.transform(img.size, Image.AFFINE, (1, 0, dx * f, 0, 1, dy * f))
        acc = Image.blend(acc, off, 1 / (j + 1))
    return acc


# ── motion presets: t -> (scale_frac_of_H, cx, cy, rot_deg, blur_dx, blur_dy) ──
def motion(preset, t, imp):
    if preset == 'lunge':
        ap, lu = smooth(t, 1.2, 3.5), smooth(t, 3.5, imp)
        s = .42 + .16 * ap + .95 * lu ** 1.8
        if t >= imp: s = 1.45 * (1 - .05 * smooth(t, imp, imp + .5))
        bob = math.sin(t * 7.5) * (3 + 9 * ap)
        return s, W / 2 + int(40 * (ap - lu)), H * .60 + bob, 0, 0, 34 * lu
    if preset == 'stumble':
        run, fall = smooth(t, 0, 2.0), smooth(t, 2.0, imp)
        s = .55 + .30 * run + .25 * fall
        rot = -28 * fall                                   # pitch forward
        dy = H * (.50 + .22 * fall)
        if t >= imp:                                       # down + small recoil
            s = .80 * (1 + .04 * math.sin((t - imp) * 30) * max(0, 1 - (t - imp) * 3))
            rot = -34; dy = H * .74
        bob = math.sin(t * 9) * (2 + 7 * run) * (1 - fall)
        return s, W / 2 - int(60 * run), dy + bob, rot, 60 * fall, 30 * fall
    if preset == 'loom':                                   # slow patient push
        ap = smooth(t, .5, imp)
        s = .55 + .55 * ap ** 1.4
        bob = math.sin(t * 2.6) * 5
        return s, W / 2 + int(30 * math.sin(t * .6)), H * .60 + bob, 0, 0, 0
    raise ValueError(preset)


def camera(preset, t, imp):
    if preset == 'push':  return 1.0 + .12 * smooth(t, 0, imp)
    if preset == 'slam':
        c = 1.0 + .12 * smooth(t, 0, imp - .6) - .05 * smooth(t, imp - .6, imp - .1)
        if t >= imp: c += .22 * (1 - smooth(t, imp, imp + .5))
        return c
    if preset == 'handheld':
        c = 1.05 + .10 * smooth(t, 0, imp)
        if t >= imp: c += .18 * (1 - smooth(t, imp, imp + .4))
        return c
    return 1.0


def load_audio(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'f32le',
                        '-ac', '1', '-ar', str(SR), '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).copy()


def render_beat(cfg, out_mp4):
    BG = sorted(Path(cfg['bg_frames']).glob('f*.png'))
    N = len(BG)
    cut = load_cut(cfg['cutout']); CW, CH = cut.size
    imp = cfg['impact']
    accent = RED if cfg.get('accent') == 'red' else ORANGE
    OUT = ROOT / 'output/_beatframes'; OUT.mkdir(exist_ok=True)
    for f in OUT.glob('*.png'): f.unlink()

    for i, bgp in enumerate(BG):
        t = i / FPS
        cam = camera(cfg['camera'], t, imp)
        frame = Image.open(bgp).convert('RGBA')
        bw, bh = int(W * cam), int(H * cam)
        frame = frame.resize((bw, bh), Image.LANCZOS).crop(
            ((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H))

        s, cx, cy, rot, bdx, bdy = motion(cfg['motion'], t, imp)
        ch = max(int(s * H), 2); cw = max(int(CW * ch / CH), 2)
        cre = cut.resize((cw, ch), Image.LANCZOS)
        if rot: cre = cre.rotate(rot, expand=True, resample=Image.BICUBIC)
        cre = dir_blur(cre, bdx, bdy)
        if imp <= t < imp + 2 / FPS:
            cre = cre.resize((int(cre.width * 1.07), int(cre.height * 1.07)), Image.LANCZOS)
        frame.alpha_composite(cre, (int(cx - cre.width / 2), int(cy - cre.height / 2)))

        # breath fog
        if cfg.get('fog', True) and smooth(t, 1.2, imp) > .2:
            puff = math.sin(t * 2.1) * .5 + .5
            fog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            r = int(26 + 30 * puff)
            fx, fy = int(cx + cre.width * .14), int(cy - cre.height * .16)
            ImageDraw.Draw(fog).ellipse((fx - r, fy - r, fx + r, fy + r),
                                        fill=(235, 235, 240, int(70 * puff)))
            frame.alpha_composite(fog.filter(ImageFilter.GaussianBlur(18)))

        d = ImageDraw.Draw(frame, 'RGBA')
        # graphic: reticle (targets a config- point) or none
        if cfg.get('graphic') == 'reticle':
            pv = smooth(t, imp - 2.7, imp - 2.2) * (1 - smooth(t, imp - 1.7, imp - 1.2))
            if pv > .02:
                gx, gy = int(W * cfg.get('reticle_xy', (.42, .72))[0]), int(H * cfg.get('reticle_xy', (.42, .72))[1])
                sz = int(70 - 26 * smooth(t, imp - 2.7, imp - 2.2))
                col = ORANGE + (int(220 * pv),)
                for ox, oy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                    X, Y = gx + ox * sz, gy + oy * sz
                    d.line((X, Y, X - ox * 22, Y), fill=col, width=3)
                    d.line((X, Y, X, Y - oy * 22), fill=col, width=3)
                if smooth(t, imp - 2.4, imp - 2.1) > .5:
                    d.text((gx - sz, gy - sz - 24), 'TARGET', font=font(20), fill=col)

        # grade + grain + chromatic split on impact
        arr = np.clip(np.asarray(frame.convert('RGB'), np.float32) * GOLD * VIG, 0, 255)
        if t >= imp and (t - imp) < .18:
            sh = int(6 * (1 - (t - imp) / .18))
            arr[:, sh:, 0] = arr[:, :W - sh, 0]; arr[:, :W - sh, 2] = arr[:, sh:, 2]
        arr = np.clip(arr + np.sin(np.arange(W) * 12.9 + i)[None, :, None] * 2, 0, 255)
        frame = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')

        # impact: flash + shake; kinetic text on cue
        if t >= imp:
            ft = t - imp
            if ft < .10:
                frame.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - ft / .10)))))
            dec = max(0, 1 - ft / .45)
            frame = frame.transform((W, H), Image.AFFINE,
                                    (1, 0, int(16 * dec * math.sin(ft * 90)), 0, 1, int(12 * dec * math.cos(ft * 70))))
        d = ImageDraw.Draw(frame, 'RGBA')
        for cap in cfg.get('text', []):
            st = smooth(t, cap['t'], cap['t'] + .18) * (1 - smooth(t, cap['t'] + cap.get('hold', 1.6), cap['t'] + cap.get('hold', 1.6) + .3))
            if st <= .01: continue
            sz = int(cap.get('size', 120) * (1.5 - .5 * smooth(t, cap['t'], cap['t'] + .18)))
            msg = cap['msg']; tb = d.textbbox((0, 0), msg, font=font(sz))
            tx, ty = (W - (tb[2] - tb[0])) / 2, H * cap.get('y', .34)
            d.rectangle((tx - 22, ty - 10, tx + (tb[2] - tb[0]) + 22, ty + (tb[3] - tb[1]) + 24),
                        fill=accent + (int(235 * st),))
            d.text((tx, ty - tb[1]), msg, font=font(sz), fill=INK)
            if cap.get('sub'):
                d.text((tx, ty + (tb[3] - tb[1]) + 30), cap['sub'], font=font(22), fill=accent + (int(235 * st),))
        frame.convert('RGB').save(OUT / f'{i:04d}.png')

    # audio mix
    vo = load_audio(cfg['vo'])
    mix = np.zeros(int(max(len(vo) / SR, N / FPS) * SR) + SR, np.float32)
    mix[:len(vo)] += vo
    bed = load_audio(SFX / 'rumble_01_loud.wav')
    mix += np.tile(bed, len(mix) // len(bed) + 1)[:len(mix)] * cfg.get('bed', .10)
    for cue in cfg.get('sfx', []):
        s = load_audio(SFX / cue['name']); i0 = int(cue['t'] * SR)
        mix[i0:i0 + len(s)] += s[:len(mix) - i0] * cue['vol']
    mix = mix / max(np.max(np.abs(mix)), 1) * .97
    with wave.open('/tmp/_beatmix.wav', 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).clip(-32768, 32767).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                    '-i', str(OUT / '%04d.png'), '-i', '/tmp/_beatmix.wav',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                    '-c:a', 'aac', '-shortest', str(out_mp4)], check=True)
    print('wrote', out_mp4)


CONFIGS = {
    'strike': dict(
        bg_frames='/tmp/bg_frames', cutout=ROOT / 'assets/trex_pilot/cutouts/c_strike_blur_cut.png',
        motion='lunge', camera='slam', impact=6.0, graphic='reticle', reticle_xy=(.40, .72),
        vo='/tmp/proto_vo.wav',
        text=[dict(t=6.0, msg='ONE BITE', y=.34, size=150)],
        sfx=[dict(name='impact_01_loud.wav', t=1.0, vol=.22), dict(name='impact_01_loud.wav', t=1.8, vol=.22),
             dict(name='impact_01_loud.wav', t=2.6, vol=.22), dict(name='impact_01_loud.wav', t=3.3, vol=.22),
             dict(name='whoosh_03_loud.wav', t=5.5, vol=.5), dict(name='body_impact_01_loud.wav', t=6.0, vol=.85),
             dict(name='impact_new_loud.wav', t=6.0, vol=.7)]),
    'stumble': dict(
        bg_frames='/tmp/bg_stumble', cutout=ROOT / 'assets/trex_pilot/cutouts/c_trip_stumble_cut.png',
        motion='stumble', camera='handheld', impact=3.3, graphic='none', accent='red',
        vo='/tmp/proto_vo_stumble.wav',
        text=[dict(t=3.3, msg='A FALL AT SPEED = FATAL', y=.30, size=70, sub='— paleontologists', hold=2.4)],
        sfx=[dict(name='whoosh_05_loud.wav', t=2.6, vol=.5), dict(name='body_impact_01_loud.wav', t=3.3, vol=.95),
             dict(name='impact_02_loud.wav', t=3.3, vol=.8), dict(name='rumble_03_loud.wav', t=3.3, vol=.5)]),
}

if __name__ == '__main__':
    which = sys.argv[1:] or ['strike', 'stumble']
    for name in which:
        render_beat(CONFIGS[name], ROOT / f'output/beat_{name}_540p.mp4')
