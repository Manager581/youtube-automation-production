#!/usr/bin/env python3
"""
composite_beat.py — the reusable "loaded composite beat" engine generalized
from the strike prototype. Each creature beat is a CONFIG, not a script:
cut-out creature on its own animated layer (motion preset) composited into a
real moving background (camera preset), + configurable graphic + narration-
synced kinetic text + real SFX mix + shared cinematic grade.

Config surface (all optional unless noted):
  bg_frames=dir | bg_video=clip(+bg_in) | bg_still=image   background source
  duration=sec (else from window)                          clip length
  window=(abs0, abs1) + align=whisperx.json                word-anchor space
  cutout=png  motion=lunge|stumble|loom  impact=sec|'word' creature layer
  camera=push|slam|handheld  sway=0..1                     camera
  graphic=reticle (+reticle_xy, reticle_track, reticle_hold)
  text=[{msg, t|word, hold, y, size, color, sub}]          kinetic text
  vo=wav | vo_span=(wav, abs0, abs1)                       QA audio (renderer
  sfx=[{name, t|word(+dt), vol}]  bed=0.10                  discards on splice)

render_beat(cfg, out_mp4). Configs at the bottom; run:
  venv.nosync/bin/python scripts/composite_beat.py strike stumble
"""
import json
import math
import subprocess
import sys
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FPS, W, H = 30, 960, 540
INK, ORANGE, YELLOW = (16, 13, 10), (245, 130, 32), (255, 209, 40)
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


def norm_word(w):
    return w.lower().strip(" .,!?;:\"'—–-")


def resolve_cues(cfg):
    """Resolve {'word': ...} anchors (impact / text t / sfx t) into seconds-
    into-beat via the WhisperX alignment + the beat's absolute window."""
    needs = (isinstance(cfg.get('impact'), str)
             or any('word' in c for c in cfg.get('text', []))
             or any('word' in c for c in cfg.get('sfx', [])))
    if not needs:
        return cfg
    w0, w1 = cfg['window']
    words = [w for w in json.load(open(cfg['align']))['words']
             if w.get('start') is not None and w0 - .25 <= w['start'] < w1 + .35]

    def at(tok):
        tgt = norm_word(tok)
        for w in words:
            if norm_word(w['word']) == tgt:
                return round(w['start'] - w0, 3)
        raise KeyError(f"word {tok!r} not in window {w0}-{w1}: "
                       f"{[w['word'] for w in words]}")

    if isinstance(cfg.get('impact'), str):
        cfg['impact'] = at(cfg['impact'])
    for c in cfg.get('text', []):
        if 'word' in c:
            c['t'] = max(0.0, at(c['word']) + c.get('dt', 0.0))
    for c in cfg.get('sfx', []):
        if 'word' in c:
            c['t'] = max(0.0, at(c['word']) + c.get('dt', 0.0))
    return cfg


def bg_frames_for(cfg, n):
    """n background frame paths: dir of f*.png | bg_video (extract+cache) |
    bg_still. Short sources pingpong-loop so reuse never pops."""
    if cfg.get('bg_still'):
        return [cfg['bg_still']] * n
    if cfg.get('bg_frames'):
        fr = sorted(Path(cfg['bg_frames']).glob('f*.png'))
    else:
        vid = Path(cfg['bg_video'])
        cache = Path(f"/tmp/bgx_{vid.stem}_{cfg.get('bg_in', 0):g}_{W}")
        if not list(cache.glob('f*.png')):
            cache.mkdir(exist_ok=True)
            subprocess.run(
                ['ffmpeg', '-y', '-loglevel', 'error',
                 '-ss', str(cfg.get('bg_in', 0)), '-i', str(vid),
                 '-vf', f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,'
                        f'crop={W}:{H}',
                 str(cache / 'f%04d.png')], check=True)
        fr = sorted(cache.glob('f*.png'))
    if not fr:
        raise FileNotFoundError(f"no bg frames for {cfg}")
    if len(fr) < n:
        fr = fr + fr[-2:0:-1]  # pingpong: seamless under modulo
    return [fr[i % len(fr)] for i in range(n)]


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
# phase boundaries ride imp so the proven shapes survive any beat length
# (lunge imp=6 → 1.2/3.48 vs the blessed 1.2/3.5; stumble imp=3.3 → 1.98/3.3
# vs the blessed 2.0/3.3)
def motion(preset, t, imp, tune=None):
    tune = tune or {}
    if preset == 'lunge':
        ap, lu = smooth(t, .2 * imp, .58 * imp), smooth(t, .58 * imp, imp)
        s = .42 + .16 * ap + .95 * lu ** 1.8
        if t >= imp: s = 1.45 * (1 - .05 * smooth(t, imp, imp + .5))
        bob = math.sin(t * 7.5) * (3 + 9 * ap)
        return s, W / 2 + int(40 * (ap - lu)), H * .60 + bob, 0, 0, 34 * lu
    if preset == 'stumble':
        run, fall = smooth(t, 0, .6 * imp), smooth(t, .6 * imp, imp)
        s = .55 + .30 * run + .25 * fall
        rot = -28 * fall                                   # pitch forward
        dy = H * (.50 + .22 * fall)
        blur = fall
        if t >= imp:                                       # down + small recoil
            ds = tune.get('down_s', .80); dyf = tune.get('down_y', .74)
            s = ds * (1 + .04 * math.sin((t - imp) * 30) * max(0, 1 - (t - imp) * 3))
            rot = tune.get('down_rot', -34); dy = H * dyf
            blur = max(0.0, 1 - (t - imp) * 4)             # body at rest ≠ blurred
        bob = math.sin(t * 9) * (2 + 7 * run) * (1 - fall)
        return s, W / 2 - int(60 * run), dy + bob, rot, 60 * blur * fall, 30 * blur * fall
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
    cfg = resolve_cues(dict(cfg))
    dur = cfg.get('duration') or (cfg['window'][1] - cfg['window'][0])
    N = max(int(round(dur * FPS)), 2)
    BG = bg_frames_for(cfg, N)
    cut = None
    if cfg.get('cutout'):
        cut = load_cut(cfg['cutout']); CW, CH = cut.size
    imp = cfg.get('impact')
    if imp is None: imp = dur + 1.0                       # never fires
    # camera span: stills push across the WHOLE beat (impact word may land
    # early); footage cams stay impact-driven (the proven strike/stumble feel)
    cam_end = cfg.get('cam_end') or (dur if cfg.get('bg_still') else imp)
    name = Path(out_mp4).stem
    OUT = ROOT / f'output/_beatframes_{name}'; OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob('*.png'): f.unlink()

    for i, bgp in enumerate(BG):
        t = i / FPS
        cam = camera(cfg['camera'], t, cam_end)
        frame = Image.open(bgp).convert('RGBA')
        bw, bh = int(W * cam), int(H * cam)
        sw = cfg.get('sway', 0.0)
        mx, my = (bw - W) // 2, (bh - H) // 2
        ox = int(max(-mx, min(mx, 14 * sw * math.sin(t * 1.15 + .7))))
        oy = int(max(-my, min(my, 9 * sw * math.sin(t * .75 + 2.1))))
        frame = frame.resize((bw, bh), Image.LANCZOS).crop(
            (mx + ox, my + oy, mx + ox + W, my + oy + H))

        cre = None
        if cut is not None:
            s, cx, cy, rot, bdx, bdy = motion(cfg['motion'], t, imp, cfg.get('tune'))
            ch = max(int(s * H), 2); cw = max(int(CW * ch / CH), 2)
            cre = cut.resize((cw, ch), Image.LANCZOS)
            if rot: cre = cre.rotate(rot, expand=True, resample=Image.BICUBIC)
            cre = dir_blur(cre, bdx, bdy)
            if imp <= t < imp + 2 / FPS:
                cre = cre.resize((int(cre.width * 1.07), int(cre.height * 1.07)), Image.LANCZOS)
            frame.alpha_composite(cre, (int(cx - cre.width / 2), int(cy - cre.height / 2)))

        # breath fog (creature beats only — anchored to the cutout)
        if cre is not None and cfg.get('fog', True) and smooth(t, 1.2, imp) > .2:
            puff = math.sin(t * 2.1) * .5 + .5
            fog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            r = int(26 + 30 * puff)
            fx, fy = int(cx + cre.width * .14), int(cy - cre.height * .16)
            ImageDraw.Draw(fog).ellipse((fx - r, fy - r, fx + r, fy + r),
                                        fill=(235, 235, 240, int(70 * puff)))
            frame.alpha_composite(fog.filter(ImageFilter.GaussianBlur(18)))

        d = ImageDraw.Draw(frame, 'RGBA')
        # graphic: reticle — pops in pre-impact, optionally TRACKS a bg point
        # through the camera (reticle_xy as bg-image fraction) and HOLDS to imp
        if cfg.get('graphic') == 'reticle':
            rin = cfg.get('reticle_in', imp - 2.7)
            rout = (imp - .15) if cfg.get('reticle_hold') else (imp - 1.7)
            pv = smooth(t, rin, rin + .5) * (1 - smooth(t, rout, rout + .5))
            if pv > .02:
                rx, ry = cfg.get('reticle_xy', (.42, .72))
                if cfg.get('reticle_track'):
                    gx = int(W / 2 + (rx - .5) * W * cam - ox)
                    gy = int(H / 2 + (ry - .5) * H * cam - oy)
                else:
                    gx, gy = int(W * rx), int(H * ry)
                sz = int(70 - 26 * smooth(t, rin, rin + .5))
                col = ORANGE + (int(220 * pv),)
                for kx, ky in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                    X, Y = gx + kx * sz, gy + ky * sz
                    d.line((X, Y, X - kx * 22, Y), fill=col, width=3)
                    d.line((X, Y, X, Y - ky * 22), fill=col, width=3)
                if smooth(t, rin + .3, rin + .6) > .5:
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
        # kinetic text: BIG branded orange/yellow, NO banner, heavy ink outline
        # so it reads over busy footage (owner brand call). hold past the clip
        # end = rides to the cut.
        for cap in cfg.get('text', []):
            st = smooth(t, cap['t'], cap['t'] + .18) * (1 - smooth(t, cap['t'] + cap.get('hold', 1.6), cap['t'] + cap.get('hold', 1.6) + .3))
            if st <= .01: continue
            sz = int(cap.get('size', 130) * (1.45 - .45 * smooth(t, cap['t'], cap['t'] + .18)))
            col = YELLOW if cap.get('color') == 'yellow' else ORANGE
            a = int(255 * st); msg = cap['msg']
            while sz > 30 and d.textlength(msg, font=font(sz)) > W * .92:   # fit width
                sz -= 4
            f1 = font(sz); swd = max(5, sz // 15)
            tb = d.textbbox((0, 0), msg, font=f1, stroke_width=swd)
            tx, ty = (W - (tb[2] - tb[0])) / 2 - tb[0], H * cap.get('y', .34) - tb[1]
            d.text((tx, ty), msg, font=f1, fill=col + (a,), stroke_width=swd, stroke_fill=INK + (a,))
            if cap.get('sub'):
                f2 = font(26); sw2 = 4
                sb = d.textbbox((0, 0), cap['sub'], font=f2, stroke_width=sw2)
                d.text(((W - (sb[2] - sb[0])) / 2 - sb[0], ty + (tb[3] - tb[1]) + 22),
                       cap['sub'], font=f2, fill=col + (a,), stroke_width=sw2, stroke_fill=INK + (a,))
        frame.convert('RGB').save(OUT / f'{i:04d}.png')

    # audio mix — QA only on spliced beats (the production renderer maps -an
    # and lays SFX from the paper edit's events; this mix is for standalone QA)
    if cfg.get('vo_span'):
        src, a0, a1 = cfg['vo_span']
        vo = load_audio(src)[int(a0 * SR):int(a1 * SR)]
    elif cfg.get('vo'):
        vo = load_audio(cfg['vo'])
    else:
        vo = np.zeros(2, np.float32)
    mix = np.zeros(int(max(len(vo) / SR, N / FPS) * SR) + SR, np.float32)
    mix[:len(vo)] += vo
    bed = load_audio(SFX / 'rumble_01_loud.wav')
    mix += np.tile(bed, len(mix) // len(bed) + 1)[:len(mix)] * cfg.get('bed', .10)
    for cue in cfg.get('sfx', []):
        s = load_audio(SFX / cue['name']); i0 = int(cue['t'] * SR)
        mix[i0:i0 + len(s)] += s[:len(mix) - i0] * cue['vol']
    mix = mix / max(np.max(np.abs(mix)), 1) * .97
    mixwav = f'/tmp/_beatmix_{name}.wav'
    with wave.open(mixwav, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).clip(-32768, 32767).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                    '-i', str(OUT / '%04d.png'), '-i', mixwav,
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                    '-c:a', 'aac', '-shortest', str(out_mp4)], check=True)
    print('wrote', out_mp4)


ALIGN = str(ROOT / 'audio/trex_pilot/narration_11l_mark_whisperx.json')
VO_MARK = str(ROOT / 'audio/trex_pilot/narration_11l_mark_full.wav')

CONFIGS = {
    # ── proven prototypes (blessed pair, /tmp inputs — kept as reference) ──
    'strike': dict(
        bg_frames='/tmp/bg_frames', cutout=ROOT / 'assets/trex_pilot/cutouts/c_strike_blur_cut.png',
        motion='lunge', camera='slam', impact=6.0, graphic='reticle', reticle_xy=(.40, .72),
        duration=7.3, vo='/tmp/proto_vo.wav',
        text=[dict(t=6.0, msg='ONE BITE', y=.34, size=150)],
        sfx=[dict(name='impact_01_loud.wav', t=1.0, vol=.22), dict(name='impact_01_loud.wav', t=1.8, vol=.22),
             dict(name='impact_01_loud.wav', t=2.6, vol=.22), dict(name='impact_01_loud.wav', t=3.3, vol=.22),
             dict(name='whoosh_03_loud.wav', t=5.5, vol=.5), dict(name='body_impact_01_loud.wav', t=6.0, vol=.85),
             dict(name='impact_new_loud.wav', t=6.0, vol=.7)]),
    'stumble': dict(
        bg_frames='/tmp/bg_stumble', cutout=ROOT / 'assets/trex_pilot/cutouts/c_trip_stumble_cut.png',
        motion='stumble', camera='handheld', impact=3.3, graphic='none', duration=8.9,
        vo='/tmp/proto_vo_stumble.wav',
        text=[dict(t=3.3, msg='A FALL AT SPEED = FATAL', y=.30, size=70, sub='— paleontologists', hold=2.4, color='yellow')],
        sfx=[dict(name='whoosh_05_loud.wav', t=2.6, vol=.5), dict(name='body_impact_01_loud.wav', t=3.3, vol=.95),
             dict(name='impact_02_loud.wav', t=3.3, vol=.8), dict(name='rumble_03_loud.wav', t=3.3, vol=.5)]),

    # ── CH1 · THE BODY (windows injected from the paper edit by the builder;
    # word anchors resolved against the Mark WhisperX alignment) ──
    'ch1_stumble': dict(                       # beats 35+36 "a trip at speed SLAMS..."
        bg_video=str(ROOT / 'footage/trex_pilot/dunk_nyc_wet_asphalt.mp4'),
        cutout=ROOT / 'assets/trex_pilot/cutouts/c_trip_stumble_cut.png',
        motion='stumble', camera='handheld', impact='slams', graphic='none',
        align=ALIGN, tune=dict(down_s=.76, down_y=.60, down_rot=-38),
        text=[dict(word='slams', msg='A FALL AT SPEED = FATAL', y=.26, size=70,
                   sub='— paleontologists', hold=9, color='yellow')],
        sfx=[dict(word='slams', dt=-.7, name='whoosh_05_loud.wav', vol=.5),
             dict(word='slams', name='body_impact_01_loud.wav', vol=.95),
             dict(word='slams', name='impact_02_loud.wav', vol=.8),
             dict(word='slams', name='rumble_03_loud.wav', vol=.5)]),
    'ch1_nostril': dict(                       # beat 55 "one of the best that ever existed"
        bg_still=str(ROOT / 'assets/trex_pilot/body_stills/c_nostril_smoke.png'),
        camera='push', sway=1.0, impact='existed', align=ALIGN,
        text=[dict(word='existed', msg='SCENT: >1 MILE', y=.30, size=96,
                   sub='— paleontologists', hold=9)],
        sfx=[dict(t=.15, name='rumble_02_loud.wav', vol=.45),
             dict(word='existed', name='impact_01_loud.wav', vol=.6)]),
    'ch1_povpick': dict(                       # beat 61 "one running figure ... six blocks away"
        bg_still=str(ROOT / 'assets/trex_pilot/body_stills/c_pov_pick.png'),
        camera='push', sway=.7, impact='six', align=ALIGN,
        graphic='reticle', reticle_xy=(.565, .50), reticle_track=True,
        reticle_hold=True, reticle_in=.5,
        text=[dict(word='six', msg='13× HUMAN ACUITY', y=.28, size=96,
                   sub='— paleontologists', hold=9)],
        sfx=[dict(t=.5, name='shimmer_01_loud.wav', vol=.5),
             dict(word='six', name='impact_01_loud.wav', vol=.65)]),
    'ch1_loom': dict(                          # beat 65 "you do not need to be fast"
        bg_video=str(ROOT / 'footage/trex_pilot/dunk_nyc_avenue_taxis.mp4'),
        cutout=ROOT / 'assets/trex_pilot/cutouts/c_statue_still_cut.png',
        motion='loom', camera='push', sway=.5,
        sfx=[dict(t=.1, name='rumble_02_loud.wav', vol=.55)]),
}

if __name__ == '__main__':
    which = sys.argv[1:] or ['strike', 'stumble']
    for nm in which:
        render_beat(CONFIGS[nm], ROOT / f'output/beat_{nm}_540p.mp4')
