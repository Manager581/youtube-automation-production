#!/usr/bin/env python3
"""
build_body_reveal.py — the body-reveal SCENE the owner directed: an illustrated
size breakdown, not text labels.
  A "you are thirteen feet tall"  -> front creature STOMPING the avenue, a
                                     vertical MEASURING TAPE pops "13 FT" beside it
  B "and forty feet from nose..." -> PIVOT to the side profile, a horizontal
                                     measuring tape pops "40 FT"
  C "as much as a full city bus"  -> hard CUT to a balance SCALE: creature = bus,
                                     "9 TONS"
Rendered with the Mark VO span so stats land on the words. Out: output/body_reveal_540p.mp4
"""
import math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FPS, W, H = 30, 960, 540
INK, ORANGE = (16, 13, 10), (245, 130, 32)
ORANGE_BG = (235, 92, 4)
SFX = ROOT / 'assets/sfx'
SR = 48000
font = lambda s: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', s)
GOLD = np.array([1.06, 1.0, 0.9])

W0, W1 = 73.38, 85.28                      # body-reveal window in the Mark VO
T_13, T_40, T_BUS = 76.86 - W0, 79.48 - W0, 84.04 - W0   # word times -> scene time
A_END, B_END = T_40 - 0.2, T_BUS - 0.4     # phase cuts
DUR = W1 - W0
N = int(DUR * FPS)

vig = Image.new('L', (W, H), 0)
ImageDraw.Draw(vig).ellipse((-W*.25, -H*.25, W*1.25, H*1.25), fill=255)
VIG = np.asarray(vig.filter(ImageFilter.GaussianBlur(120)), np.float32)[..., None]/255*.45+.55


def smooth(t, a, b):
    if t <= a: return 0.0
    if t >= b: return 1.0
    x = (t-a)/(b-a); return x*x*(3-2*x)


def load_cut(p):
    im = Image.open(p).convert('RGBA'); a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > 20); return im.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1))


def bg_frames(clip, n, ss=0):
    cache = Path(f'/tmp/brv_{Path(clip).stem}')
    if not list(cache.glob('f*.png')):
        cache.mkdir(exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(ss), '-i', clip,
                        '-vf', f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
                        str(cache/'f%04d.png')], check=True)
    fr = sorted(cache.glob('f*.png'))
    if len(fr) < n: fr = fr + fr[-2:0:-1]
    return [fr[i % len(fr)] for i in range(n)]


def big_text(d, msg, cx, cy, size, col=ORANGE):
    f = font(size); sw = max(5, size//15)
    b = d.textbbox((0, 0), msg, font=f, stroke_width=sw)
    d.text((cx-(b[2]-b[0])/2-b[0], cy-(b[3]-b[1])/2-b[1]), msg, font=f, fill=col,
           stroke_width=sw, stroke_fill=INK)


def vtape(d, x, y0, y1, label, p):                 # vertical measuring tape, p=0..1 draws in
    yy = y0 + (y1-y0)*(1-p)
    d.line((x, yy, x, y1), fill=ORANGE, width=6)
    for ya, dx in ((yy, 22), (y1, 22)):            # arrow caps
        d.line((x-dx, ya+(14 if ya == yy else -14), x, ya), fill=ORANGE, width=6)
        d.line((x+dx, ya+(14 if ya == yy else -14), x, ya), fill=ORANGE, width=6)
    for ty in range(int(yy), int(y1), 26):         # ticks
        d.line((x-10, ty, x+10, ty), fill=ORANGE+(180,), width=3)
    if p > .5: big_text(d, label, x+78, (y0+y1)/2, 70)


def htape(d, x0, x1, y, label, p):                 # horizontal tape
    xx = x0 + (x1-x0)*p
    d.line((x0, y, xx, y), fill=ORANGE, width=6)
    for xa, s in ((x0, 1), (x1, -1)):
        d.line((xa+s*14, y-22, xa, y), fill=ORANGE, width=6)
        d.line((xa+s*14, y+22, xa, y), fill=ORANGE, width=6)
    for tx in range(int(x0), int(xx), 30):
        d.line((tx, y-10, tx, y+10), fill=ORANGE+(180,), width=3)
    if p > .5: big_text(d, label, (x0+x1)/2, y-58, 70)


# assets
front = load_cut(ROOT/'assets/trex_pilot/cutouts/ch_trex_avenue_wide_cut.png')
side = load_cut(ROOT/'assets/trex_pilot/cutouts/trex_side_cut.png')
bus = load_cut(ROOT/'assets/trex_pilot/cutouts/city_bus_cut.png')
BGA = bg_frames(str(ROOT/'footage/trex_pilot/dunk_nyc_avenue_taxis.mp4'), int(A_END*FPS)+2)
BGB = bg_frames(str(ROOT/'footage/trex_pilot/stock/s_taxi_wall.mp4'), int((B_END-A_END)*FPS)+2)

OUT = ROOT/'output/_brvframes'; OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.png'): f.unlink()
stomps = []                                        # times of foot-impacts for SFX

for i in range(N):
    t = i/FPS
    if t < A_END:                                  # ── PHASE A: 13 FT tall, stomping ──
        frame = Image.open(BGA[i]).convert('RGBA')
        z = 1.0+.10*smooth(t, 0, A_END)            # camera push
        bw, bh = int(W*z), int(H*z)
        frame = frame.resize((bw, bh)).crop(((bw-W)//2, (bh-H)//2, (bw-W)//2+W, (bh-H)//2+H))
        grow = .55+.30*smooth(t, 0, A_END)
        bob = math.sin(t*4.2)
        step = bob*16                              # heavy stomp bob
        if i > 0 and math.sin((t-1/FPS)*4.2) > 0 >= bob:   # bottom of stomp
            stomps.append(t)
        ch = int(grow*H); cw = int(front.width*ch/front.height)
        cre = front.resize((max(cw, 2), max(ch, 2)))
        cx = int(W*0.40 + 30*math.sin(t*0.7)); cy = int(H*0.60+step)
        shake = max(0, (t-stomps[-1])) if stomps else 9
        sh = int(6*max(0, 1-shake*8)) if stomps else 0
        frame.alpha_composite(cre, (cx-cre.width//2+sh, cy-cre.height//2))
        # foot dust
        if abs(step) > 12:
            dust = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(dust).ellipse((cx-70, cy+ch//2-30, cx+70, cy+ch//2+20), fill=(220, 215, 205, 70))
            frame.alpha_composite(dust.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(frame, 'RGBA')
        p = smooth(t, T_13, T_13+.4)               # tape draws in on "thirteen"
        if p > 0:
            vtape(d, cx+cre.width//2+30, cy-cre.height//2, cy+cre.height//2, '13 FT', p)
    elif t < B_END:                                # ── PHASE B: 40 FT long, side pivot ──
        j = int((t-A_END)*FPS)
        frame = Image.open(BGB[min(j, len(BGB)-1)]).convert('RGBA')
        sw_ = smooth(t-A_END, 0, .3)               # quick whip-in
        ch = int(.52*H); cw = int(side.width*ch/side.height)
        cre = side.resize((max(cw, 2), max(ch, 2)))
        cx = int(W*0.5); cy = int(H*0.56)
        frame.alpha_composite(cre, (cx-cre.width//2, cy-cre.height//2))
        d = ImageDraw.Draw(frame, 'RGBA')
        p = smooth(t-A_END, (T_40-A_END), (T_40-A_END)+.4)
        if p > 0:
            htape(d, cx-cre.width//2, cx+cre.width//2, cy+cre.height//2+34, '40 FT', p)
    else:                                          # ── PHASE C: 9 TONS = bus, scale ──
        frame = Image.new('RGBA', (W, H), ORANGE_BG+(255,))
        d = ImageDraw.Draw(frame, 'RGBA')
        for gy in range(0, H, 22):                 # brand halftone
            for gx in range(0, W, 22):
                a = max(0, int(40-30*(((gx/W)**2+((H-gy)/H)**2)**.5)))
                if a: d.ellipse((gx, gy, gx+4, gy+4), fill=(120, 40, 0, a))
        pin = smooth(t, B_END, B_END+.3)
        beam_y = 300
        d.line((W/2, beam_y, W/2, 470), fill=INK, width=12)        # fulcrum post
        d.polygon([(W/2-40, 470), (W/2+40, 470), (W/2, 420)], fill=INK)
        d.line((180, beam_y, 780, beam_y), fill=INK, width=12)     # beam
        for px, cut, lab in ((300, front, ''), (660, bus, '')):
            sc = int(150*pin); c = cut.resize((int(cut.width*sc/cut.height), max(sc, 2))) if pin > .05 else None
            if c:
                d.line((px, beam_y, px, beam_y+70), fill=INK, width=6)
                frame.alpha_composite(c, (px-c.width//2, beam_y+70))
        if pin > .5:
            big_text(d, '=', W/2, beam_y+120, 90, col=INK)
            big_text(d, '9 TONS', W/2, 150, 110)
            big_text(d, '= 1 CITY BUS', W/2, 235, 40, col=(245, 240, 235))
    # grade
    arr = np.clip(np.asarray(frame.convert('RGB'), np.float32)*(GOLD if t < B_END else 1)*(VIG if t < B_END else 1), 0, 255)
    Image.fromarray(arr.astype(np.uint8)).save(OUT/f'{i:04d}.png')

# ── audio: VO + stomp SFX + stat impacts + rumble bed ──
def la(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).copy()
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(ROOT/'audio/trex_pilot/narration_11l_mark_full.wav'),
                '-ss', str(W0), '-to', str(W1), '/tmp/brv_vo.wav'], check=True)
vo = la('/tmp/brv_vo.wav'); mix = np.zeros(int(DUR*SR)+SR, np.float32); mix[:len(vo)] += vo
bed = la(SFX/'rumble_01_loud.wav'); mix += np.tile(bed, len(mix)//len(bed)+1)[:len(mix)]*.10
def place(name, t, v):
    s = la(SFX/name); i0 = int(t*SR); mix[i0:i0+len(s)] += s[:len(mix)-i0]*v
for st in stomps: place('impact_01_loud.wav', st, .3)            # footstomps
place('whoosh_03_loud.wav', T_13-.2, .4); place('impact_02_loud.wav', T_13, .55)
place('whoosh_05_loud.wav', A_END-.1, .4); place('impact_02_loud.wav', T_40, .55)
place('body_impact_01_loud.wav', B_END, .7); place('impact_new_loud.wav', T_BUS, .6)
mix = mix/max(np.max(np.abs(mix)), 1)*.97
with wave.open('/tmp/brv_mix.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix*32767).clip(-32768, 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(OUT/'%04d.png'),
                '-i', '/tmp/brv_mix.wav', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                '-c:a', 'aac', '-shortest', str(ROOT/'output/body_reveal_540p.mp4')], check=True)
print('wrote output/body_reveal_540p.mp4   stomps:', len(stomps))
