#!/usr/bin/env python3
"""
rexcaped_stat_cards.py — render the Rexcaped branded 1920x1080 PNGs an engine
plan needs: STAT CARDS (orange/black, big spoken number) for asset=stat_card
shots, and labeled PLACEHOLDER SLATES for asset=stock/meme shots (and creature
shots when no clip exists yet). The slates double as the sourcing shot-list:
each shows the spoken line + timecode the asset must be found for.

Brand: orange (247,98,5) on near-black, assets/brand/emblem_trex_orange.png,
hand-drawn-ink energy (halftone dots + grain), Arial Black.

Usage:
  venv.nosync/bin/python scripts/rexcaped_stat_cards.py \
    --plan /tmp/edit_deep/trex_engine_plan_v2.json \
    --out-dir assets/trex_pilot/cards [--cards-only|--placeholders-only]
  venv.nosync/bin/python scripts/rexcaped_stat_cards.py --demo --out-dir /tmp/cards_demo

Files: card_s{idx:04d}.png / ph_{stock|meme|creature}_s{idx:04d}.png, where idx
is the shot index in the plan (the paper-edit converter joins on that).
"""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EMBLEM = ROOT / 'assets/brand/emblem_trex_orange.png'
W, H = 1920, 1080
ORANGE = (247, 98, 5)
BLACK = (13, 12, 10)
SLATE_BG = (22, 21, 19)
WHITE = (240, 236, 230)
F_BLACK = '/System/Library/Fonts/Supplemental/Arial Black.ttf'
F_BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
F_MONO = '/System/Library/Fonts/Menlo.ttc'


def font(path, size):
    return ImageFont.truetype(path, size)


def fit_font(draw, text, path, max_w, max_h, start=320, floor=60):
    """largest font size that fits text inside max_w x max_h"""
    lo, hi = floor, start
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = font(path, mid)
        x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=f)
        if x1 - x0 <= max_w and y1 - y0 <= max_h:
            lo = mid
        else:
            hi = mid - 1
    return font(path, lo)


def tracked(draw, xy, text, f, fill, tracking=8, anchor_mid_w=None):
    """draw text with letter tracking; optionally center on anchor_mid_w"""
    widths = [draw.textlength(ch, font=f) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (anchor_mid_w - total / 2) if anchor_mid_w else xy[0]
    y = xy[1]
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=f, fill=fill)
        x += w + tracking


def wrap(draw, text, f, max_w, max_lines=4):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=f) <= max_w:
            cur = t
        else:
            lines.append(cur); cur = w
            if len(lines) == max_lines - 1:
                break
    lines.append(cur)
    rest = text[len(' '.join(lines)):].strip()
    if rest:
        lines[-1] = lines[-1].rstrip('.,') + '…'
    return lines


def base_canvas(bg):
    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im, 'RGBA')
    # halftone dot field, fading from the bottom-left corner
    for gy in range(0, H, 26):
        for gx in range(0, W, 26):
            dist = ((gx / W) ** 2 + ((H - gy) / H) ** 2) ** 0.5
            a = max(0, int(26 - 34 * dist))
            if a:
                d.ellipse((gx, gy, gx + 5, gy + 5), fill=ORANGE + (a,))
    # film grain
    noise = Image.effect_noise((W, H), 22).convert('L')
    im = Image.composite(im, Image.new('RGB', (W, H), (0, 0, 0)),
                         noise.point(lambda v: 255 - max(0, (v - 128) // 6)))
    return im


def stamp_emblem(im, size=170, alpha=235):
    if not EMBLEM.exists():
        return
    em = Image.open(EMBLEM).convert('RGBA').resize((size, size))
    mask = Image.new('L', (size, size), 0)               # round off the square plate
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=alpha)
    em.putalpha(mask)
    im.paste(em, (W - size - 56, H - size - 52), em)


def render_card(value, context, out_path):
    im = base_canvas(BLACK)
    d = ImageDraw.Draw(im, 'RGBA')
    # double frame
    d.rectangle((36, 36, W - 36, H - 36), outline=ORANGE, width=4)
    d.rectangle((50, 50, W - 50, H - 50), outline=ORANGE + (90,), width=1)
    # channel wordmark
    tracked(d, (0, 76), 'REXCAPED', font(F_BLACK, 34), ORANGE + (200,),
            tracking=16, anchor_mid_w=W / 2)
    # VALUE — huge, orange, soft ink shadow
    fv = fit_font(d, value, F_BLACK, 1640, 430, start=330)
    x0, y0, x1, y1 = d.textbbox((0, 0), value, font=fv)
    vx, vy = (W - (x1 - x0)) / 2 - x0, (H - (y1 - y0)) * 0.40 - y0
    d.text((vx + 9, vy + 11), value, font=fv, fill=(0, 0, 0))
    d.text((vx, vy), value, font=fv, fill=ORANGE)
    # rule + CONTEXT — white, tracked
    cy = vy + y1 + 46
    if context:
        d.line((W / 2 - 130, cy, W / 2 + 130, cy), fill=ORANGE + (160,), width=3)
        fc = fit_font(d, context, F_BLACK, 1500, 120, start=84, floor=40)
        tracked(d, (0, cy + 28), context, fc, WHITE, tracking=6, anchor_mid_w=W / 2)
    stamp_emblem(im)
    im.save(out_path)


def _frames_to_mp4(frames, out_path, fps=30):
    """Pipe PIL frames to ffmpeg -> H.264 mp4 (the renderer treats animated
    cards as ordinary video beats — zero renderer changes needed)."""
    import subprocess
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
         '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps),
         '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', str(out_path)],
        stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()


def render_typewriter_mov(value, context, out_path, dur, fps=30, cps=27):
    """Animated stat card (measured grammar: value slams in ~3 frames, context
    TYPEWRITES at ~27 chars/s — the reference card anatomy at 7:53)."""
    bg = base_canvas(BLACK)
    d0 = ImageDraw.Draw(bg, 'RGBA')
    d0.rectangle((36, 36, W - 36, H - 36), outline=ORANGE, width=4)
    d0.rectangle((50, 50, W - 50, H - 50), outline=ORANGE + (90,), width=1)
    tracked(d0, (0, 76), 'REXCAPED', font(F_BLACK, 34), ORANGE + (200,),
            tracking=16, anchor_mid_w=W / 2)
    stamp_emblem(bg)
    fv = fit_font(d0, value, F_BLACK, 1640, 430, start=330)
    x0, y0, x1, y1 = d0.textbbox((0, 0), value, font=fv)
    vx, vy = (W - (x1 - x0)) / 2 - x0, (H - (y1 - y0)) * 0.40 - y0
    cy = vy + y1 + 46
    fc = fit_font(d0, context or ' ', F_BLACK, 1500, 120, start=84, floor=40)

    n = max(int(dur * fps), 6)
    frames = []
    for i in range(n):
        im = bg.copy()
        d = ImageDraw.Draw(im, 'RGBA')
        punch = {0: 1.16, 1: 1.08}.get(i, 1.0)          # 3-frame value slam
        if punch > 1.0:
            fv_p = font(F_BLACK, int(fv.size * punch))
            px0, py0, px1, py1 = d.textbbox((0, 0), value, font=fv_p)
            pvx, pvy = (W - (px1 - px0)) / 2 - px0, (H - (py1 - py0)) * 0.40 - py0
            d.text((pvx + 9, pvy + 11), value, font=fv_p, fill=(0, 0, 0))
            d.text((pvx, pvy), value, font=fv_p, fill=ORANGE)
        else:
            d.text((vx + 9, vy + 11), value, font=fv, fill=(0, 0, 0))
            d.text((vx, vy), value, font=fv, fill=ORANGE)
        if context:
            shown = context[:max(0, int((i / fps) * cps))]
            if shown:
                d.line((W / 2 - 130, cy, W / 2 + 130, cy), fill=ORANGE + (160,), width=3)
                tracked(d, (0, cy + 28), shown + ('▌' if len(shown) < len(context) and i % 8 < 4 else ''),
                        fc, WHITE, tracking=6, anchor_mid_w=W / 2)
        frames.append(im)
    _frames_to_mp4(frames, out_path, fps)
    print(f'typewriter mov {out_path} ({dur}s, {n}f)')


def render_boil_mov(out_path, dur=1.0, fps=30, size=560):
    """Boiling Rexcaped emblem stamp (reference logo anatomy: 2-3 alternating
    drawings, sketchbook 'boil', used as scene-transition punctuation)."""
    if not EMBLEM.exists():
        raise SystemExit(f'missing {EMBLEM}')
    em = Image.open(EMBLEM).convert('RGBA').resize((size, size))
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    em.putalpha(mask)
    bg = base_canvas(BLACK)
    states = []
    for rot, sc, dx, dy in ((-1.6, 0.985, -5, 3), (0.0, 1.0, 0, -4), (1.7, 1.02, 5, 2)):
        e = em.rotate(rot, resample=Image.BICUBIC, expand=False)
        s = int(size * sc)
        e = e.resize((s, s))
        f = bg.copy()
        f.paste(e, ((W - s) // 2 + dx, (H - s) // 2 + dy), e)
        states.append(f)
    n = max(int(dur * fps), 6)
    frames = [states[(i // 3) % 3] for i in range(n)]    # ~10fps boil at 30fps out
    _frames_to_mp4(frames, out_path, fps)
    print(f'boil mov {out_path} ({dur}s, {n}f)')


PH_STYLE = {
    'stock': ('STOCK B-ROLL', ORANGE),
    'meme': ('MEME CUTAWAY', WHITE),
    'creature': ('CREATURE SHOT', (208, 58, 36)),
}


def render_placeholder(asset, shot, idx, out_path):
    label, bar = PH_STYLE[asset]
    im = base_canvas(SLATE_BG)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle((0, 0, 26, H), fill=bar)
    d.rectangle((36, 36, W - 36, H - 36), outline=(90, 86, 80), width=2)
    d.text((110, 96), label, font=font(F_BLACK, 112), fill=WHITE)
    if shot.get('meme_reset'):
        bx = 110 + d.textlength(label, font=font(F_BLACK, 112)) + 46
        d.rectangle((bx, 130, bx + 360, 206), outline=ORANGE, width=4)
        d.text((bx + 28, 144), 'TONAL RESET', font=font(F_BLACK, 38), fill=ORANGE)
    tc = f"shot {idx:04d}   {shot['t']:8.2f} → {shot['end']:8.2f}   {shot['dur']:5.2f}s   [{shot['why']}]"
    d.text((114, 252), tc, font=font(F_MONO, 40), fill=(150, 145, 138))
    fq = font(F_BLACK, 56)
    qy = 400
    for line in wrap(d, f'“{shot.get("text", "").strip()}”', fq, 1620):
        d.text((114, qy), line, font=fq, fill=ORANGE)
        qy += 78
    d.text((114, H - 120), 'PLACEHOLDER — source this slot against the line above',
           font=font(F_BOLD, 34), fill=(150, 145, 138))
    stamp_emblem(im, size=130, alpha=110)
    im.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--cards-only', action='store_true')
    ap.add_argument('--placeholders-only', action='store_true')
    ap.add_argument('--creature-placeholders', action='store_true',
                    help='also render slates for creature shots (no clip pool yet)')
    ap.add_argument('--demo', action='store_true')
    ap.add_argument('--typewriter-mov', nargs=4, metavar=('VALUE', 'CONTEXT', 'DUR', 'OUT'),
                    help='render an animated typewriter card mp4')
    ap.add_argument('--boil-mov', nargs=2, metavar=('DUR', 'OUT'),
                    help='render the boiling emblem stamp mp4')
    a = ap.parse_args()

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    if a.typewriter_mov:
        v, c, dur, dest = a.typewriter_mov
        render_typewriter_mov(v, c, out / dest, float(dur))
        return
    if a.boil_mov:
        dur, dest = a.boil_mov
        render_boil_mov(out / dest, float(dur))
        return

    if a.demo:
        render_card('12,800 PSI', 'BITE FORCE', out / 'demo_card_psi.png')
        render_card('40 LBS', 'OF MEAT. EVERY DAY.', out / 'demo_card_meat.png')
        shot = {'t': 104.8, 'end': 107.9, 'dur': 3.1, 'why': 'turn',
                'text': 'then the flies find the carcass before you do', 'meme_reset': True}
        render_placeholder('meme', shot, 31, out / 'demo_ph_meme.png')
        render_placeholder('stock', {'t': 47.7, 'end': 50.1, 'dur': 2.4, 'why': 'stat',
                                     'text': 'four hundred meters away across the open intersection'},
                           14, out / 'demo_ph_stock.png')
        print(f'demo -> {out}')
        return

    shots = json.load(open(a.plan))['shots']
    n_card = n_ph = 0
    for i, s in enumerate(shots):
        if s['asset'] == 'stat_card' and not a.placeholders_only:
            card = s.get('card') or {}
            if card.get('value'):
                render_card(card['value'], card.get('context', ''),
                            out / f'card_s{i:04d}.png')
                n_card += 1
        elif s['asset'] in ('stock', 'meme') and not a.cards_only:
            render_placeholder(s['asset'], s, i, out / f"ph_{s['asset']}_s{i:04d}.png")
            n_ph += 1
        elif s['asset'] == 'creature' and a.creature_placeholders and not a.cards_only:
            render_placeholder('creature', s, i, out / f'ph_creature_s{i:04d}.png')
            n_ph += 1
    print(f'wrote {n_card} stat cards + {n_ph} placeholder slates -> {out}')


if __name__ == '__main__':
    main()
