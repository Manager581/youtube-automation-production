#!/usr/bin/env python3
"""
build_hook_mock_strip.py — the OWNER MOCK GATE artifact: one strip image of a
proposed open (tiles = stills/frames with orange stat CHIPS composited on,
timestamp + VO + motion note under each) so layer-3 taste calls get a human
veto/bless BEFORE anything is rendered. See NEXT_SESSION.md "HOW ON-SCREEN
CHOICES GET MADE".

Chip style is cloned from rexcaped_stat_cards.render_card_orange() — orange
field, halftone dots, ink double border, ink value w/ warm under-shadow,
white context — at overlay-chip scale (the restructure law: stats ride as
SMALL overlays on world shots, never full-frame).

Usage: venv/bin/python scripts/build_hook_mock_strip.py
Edit TILES below per mock. Output: output/<OUT_NAME>.png (≤2000px wide).
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from rexcaped_stat_cards import render_chip_orange  # canonical chip recipe

STILLS = ROOT / 'assets/trex_pilot/hook_stills/169'

# brand constants — keep identical to rexcaped_stat_cards.py
ORANGE_BG = (235, 92, 4)
INK = (16, 13, 10)
WHITE = (240, 236, 230)
WARM_SHADOW = (255, 200, 150)
DOTS = (120, 40, 0)
F_BLACK = '/System/Library/Fonts/Supplemental/Arial Black.ttf'
F_BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
F_MONO = '/System/Library/Fonts/Menlo.ttc'

OUT_NAME = 'trex_hook_mock_strip_0_15_v1'

# the restructured 0-15s — scene-first open, stats as chips on world shots
TILES = [
    dict(img=STILLS / 'ch_trex_avenue_wide.png', t='0.0–4.3',
         vo='"You are the closest thing the ancient world ever built to"',
         note='NEW still A · slow push · sub-boom at 0.0, bed starts', chips=[]),
    dict(img=STILLS / 'ch_trex_lowangle_taxis.png', t='4.3–6.0',
         vo='"a perfect killing machine."',
         note='NEW still B · punch-in on "machine" · metallic shink', chips=[]),
    dict(img=STILLS / 'ch_trex_walkaway_crowd.png', t='6.0–7.2',
         vo='"Forty feet long."',
         note='NEW still C · chip SLAMS +shake on "Forty"',
         chips=[('40 FT', 'NOSE TO TAIL')]),
    dict(img=STILLS / 'ch_trex_walkaway_crowd.png', t='7.2–7.6',
         vo='"Nine —"',
         note='C holds · 2nd chip slams under the 1st',
         chips=[('40 FT', 'NOSE TO TAIL'), ('9 TONS', None)]),
    dict(img=STILLS / 'ch_skull_bathtub.png', t='7.6–11.8',
         vo='"tons. A skull the size of a bathtub, packed with sixty"',
         note='pop-in on "bathtub" · chip on "sixty"',
         chips=[('60 TEETH', None)]),
    dict(img=Path('/tmp/mock_jaws_frame.jpg'), t='11.8–13.3',
         vo='"teeth, some of them"',
         note='jaws_teeth clip (motion) · whoosh on cut', chips=[]),
    dict(img=STILLS / 'ch_knife_macro.png', t='13.3–15.0+',
         vo='"twelve inches long and serrated like steak knives."',
         note='*shing* on knife reveal', chips=[]),
]

TILE_W, TILE_H = 470, 264          # 16:9 tile
LABEL_H = 118
PAD, GUT = 28, 18
COLS = 4
HEADER_H, FOOTER_H = 96, 54
PAPER = (242, 240, 236)            # review-doc paper, not video black
INK_SOFT = (90, 86, 80)


def font(path, size):
    return ImageFont.truetype(path, size)


def chip_img(value, context):
    """canonical chip, scaled to the renderer's frame fraction (w=0.29 of
    1536) so the mock previews exactly what the render composites"""
    ch = render_chip_orange(value, context)
    cw = int(1536 * 0.29)
    return ch.resize((cw, int(ch.height * cw / ch.width)), Image.LANCZOS)


def tile_frame(spec):
    """full-res still + chips composited, then shrunk to tile size"""
    im = Image.open(spec['img']).convert('RGB').resize((1536, 864), Image.LANCZOS)
    d = ImageDraw.Draw(im, 'RGBA')
    y = 64
    for value, context in spec['chips']:
        ch = chip_img(value, context)
        d.rectangle((64 + 14, y + 16, 64 + ch.width + 14, y + ch.height + 16),
                    fill=(10, 8, 6, 110))            # soft drop shadow
        im.paste(ch, (64, y))
        y += ch.height + 22
    return im.resize((TILE_W, TILE_H), Image.LANCZOS)


def main():
    jaws = Path('/tmp/mock_jaws_frame.jpg')          # tile 6 frame, re-extract if gone
    if not jaws.exists():
        import subprocess
        subprocess.run(['ffmpeg', '-y', '-ss', '1.5', '-i',
                        str(ROOT / 'footage/trex_pilot/dunk_trex_jaws_teeth.mp4'),
                        '-frames:v', '1', '-q:v', '2', str(jaws)],
                       check=True, capture_output=True)
    rows = (len(TILES) + COLS - 1) // COLS
    W = PAD * 2 + COLS * TILE_W + (COLS - 1) * GUT
    H = HEADER_H + rows * (TILE_H + LABEL_H + GUT) + FOOTER_H + PAD
    strip = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(strip, 'RGBA')

    d.text((PAD, 26), 'REXCAPED · T-REX PILOT — restructured 0–15s  (mock v1 · bless / veto)',
           font=font(F_BLACK, 30), fill=INK)
    d.text((PAD, 64), 'scene-first open: premise on screen from frame 1 · stats ride as orange '
           'CHIPS on world shots · full-frame stat cards killed',
           font=font(F_BOLD, 19), fill=INK_SOFT)

    for i, spec in enumerate(TILES):
        r, c = divmod(i, COLS)
        x = PAD + c * (TILE_W + GUT)
        y = HEADER_H + r * (TILE_H + LABEL_H + GUT)
        strip.paste(tile_frame(spec), (x, y))
        d.rectangle((x, y, x + TILE_W, y + TILE_H), outline=INK + (70,), width=1)
        ly = y + TILE_H + 8
        d.text((x, ly), spec['t'] + 's', font=font(F_MONO, 17), fill=ORANGE_BG)
        vo_f = font(F_BOLD, 17)
        words, line, ly2 = spec['vo'].split(), '', ly + 24
        for wd in words:
            t = (line + ' ' + wd).strip()
            if d.textlength(t, font=vo_f) <= TILE_W:
                line = t
            else:
                d.text((x, ly2), line, font=vo_f, fill=INK); line = wd; ly2 += 21
        d.text((x, ly2), line, font=vo_f, fill=INK)
        d.text((x, ly2 + 26), spec['note'], font=font(F_BOLD, 14), fill=INK_SOFT)

    d.text((PAD, H - FOOTER_H - 6),
           'NEW stills A/B/C generated this session (same ChatGPT char/style ref) · chips are a MOCK — '
           'overlay-within-beat compositing builds in the renderer only after bless',
           font=font(F_BOLD, 15), fill=INK_SOFT)

    out = ROOT / 'output' / f'{OUT_NAME}.png'
    strip.save(out)
    print(out, strip.size)


if __name__ == '__main__':
    main()
