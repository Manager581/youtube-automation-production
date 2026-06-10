#!/usr/bin/env python3
"""
analyze_shot_assets.py — second pass of the edit-grammar study: classify WHAT
each cut goes to. For each shot (from the cut list in *_grammar.json) it samples
the shot's midpoint frame, OCRs it (on-screen text/numbers), and tiles a sampled
subset into labeled contact sheets so the asset TYPE
(creature / real-stock / meme / stat-card / facecam / graphic) can be read off.

Reference-video analysis only. Writes <out>.json + <sheet_prefix>_NN.jpg.
"""
import argparse, json, math, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NUM = re.compile(r'\d')


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors='replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--grammar', required=True)
    ap.add_argument('--video', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--frames-dir', required=True)
    ap.add_argument('--sheet-prefix', required=True)
    ap.add_argument('--every', type=int, default=6)
    ap.add_argument('--cols', type=int, default=6)
    ap.add_argument('--per-sheet', type=int, default=24)
    a = ap.parse_args()

    cuts = json.load(open(a.grammar))['cuts']
    shots = [{'idx': i, 't_mid': round(max(0.1, c['t'] - c['shot_dur'] / 2), 2),
              'dur': c['shot_dur']} for i, c in enumerate(cuts)]
    fd = Path(a.frames_dir); fd.mkdir(parents=True, exist_ok=True)
    sampled = shots[::a.every]

    recs = []
    for s in sampled:
        fp = fd / f"s{s['idx']:04d}.jpg"
        sh(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-ss', str(s['t_mid']),
            '-i', a.video, '-frames:v', '1', '-vf', 'scale=-1:200', '-q:v', '3', str(fp)])
        text = ''
        if fp.exists():
            try:
                text = ' '.join(sh(['tesseract', str(fp), 'stdout', '--psm', '11',
                                    '-l', 'eng']).stdout.split())[:120]
            except Exception:
                text = ''
        s['text'] = text
        s['has_number'] = bool(NUM.search(text))
        s['frame'] = str(fp)
        recs.append(s)
    Path(a.out).write_text(json.dumps(recs, indent=1))

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
    except Exception:
        font = ImageFont.load_default()
    tw, th, pad, cols = 320, 180, 24, a.cols
    for sN in range(0, len(recs), a.per_sheet):
        chunk = recs[sN:sN + a.per_sheet]
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new('RGB', (cols * tw, rows * (th + pad)), (18, 18, 18))
        d = ImageDraw.Draw(sheet)
        for j, r in enumerate(chunk):
            cx, cy = (j % cols) * tw, (j // cols) * (th + pad)
            try:
                sheet.paste(Image.open(r['frame']).convert('RGB').resize((tw, th)), (cx, cy + pad))
            except Exception:
                pass
            lbl = f"#{r['idx']} {int(r['t_mid'] // 60):02d}:{r['t_mid'] % 60:04.1f}"
            if r['text']:
                lbl += ' TXT'
            d.text((cx + 3, cy + 4), lbl, fill=(255, 190, 0), font=font)
        out = f"{a.sheet_prefix}_{sN // a.per_sheet:02d}.jpg"
        sheet.save(out, quality=80)
        print("sheet", out, len(chunk))
    print(f"sampled {len(recs)}/{len(shots)} shots; text in {sum(bool(r['text']) for r in recs)}")


if __name__ == '__main__':
    main()
