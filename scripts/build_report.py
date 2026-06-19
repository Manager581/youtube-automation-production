#!/usr/bin/env python3
"""
build_report.py — the per-render diagnostic report (guarantee step 5).

ONE self-contained HTML the owner reviews BEFORE watching: gate verdict up top,
then every beat with its provenance (which workflow made it), gate status, a
contact-sheet thumbnail (when a matching render is given), and a repetition
summary. Re-derives provenance from disk and reuses gate_provenance — no parallel
logic. Answers frame-level-QA (see the frames) + the consistency guarantee (see
which beats are sanctioned) on one page.

  venv/bin/python scripts/build_report.py \
      --paper-edit storyboards/trex_pilot_ch1_only.json \
      --render output/trex_pilot_ch1_body_540p.mp4 \
      --out output/report_ch1.html
"""
import argparse
import base64
import html
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from provenance import ROOT  # noqa
from gate_provenance import ledger, beat_status, enforce

COLOR = {'approved': '#1D9E75', 'pending': '#BA7517', 'non_recipe': '#888780',
         'unknown_recipe': '#E24B4A', 'stale': '#E24B4A', 'unsanctioned': '#A32D2D'}


def ffprobe_dur(p):
    try:
        r = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json',
                            '-show_format', str(p)], capture_output=True, text=True, timeout=15)
        return float(json.loads(r.stdout)['format']['duration'])
    except Exception:
        return None


def thumb(render, t, w=168):
    out = f'/tmp/_rpt_{int(t * 1000)}.jpg'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', str(render),
                    '-frames:v', '1', '-vf', f'scale={w}:-1', out], timeout=20)
    p = Path(out)
    if p.exists() and p.stat().st_size > 0:
        b = base64.b64encode(p.read_bytes()).decode()
        p.unlink()
        return 'data:image/jpeg;base64,' + b
    return None


def mmss(s):
    s = int(s or 0)
    return f'{s // 60}:{s % 60:02d}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper-edit', required=True)
    ap.add_argument('--render', default=None, help='matching mp4 for per-beat thumbnails')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    pe = json.loads(Path(a.paper_edit).read_text())
    beats = pe['beats'] if isinstance(pe, dict) else pe
    approved, candidates = ledger()
    ok, _ = enforce(beats, strict=False)
    ok_strict, _ = enforce(beats, strict=True)

    thumbs, thumb_note = {}, ''
    if a.render and Path(a.render).exists():
        rd = ffprobe_dur(a.render)
        span = max((b.get('end_sec', 0) for b in beats), default=0)
        if rd and span and abs(rd - span) < max(5.0, 0.1 * span):
            for i, b in enumerate(beats):
                thumbs[i] = thumb(a.render, min(b.get('start_sec', 0) + 0.2, rd - 0.1))
        else:
            thumb_note = f'thumbnails skipped — render {rd}s vs paper-edit span {span:.0f}s (mismatch)'
    elif a.render:
        thumb_note = f'thumbnails skipped — render not found: {a.render}'

    reuse = Counter(Path(b.get('visual_file') or '').name for b in beats if b.get('visual_file'))
    rows, counts = [], Counter()
    summary_rows = []
    for i, b in enumerate(beats):
        st, p = beat_status(b, approved, candidates)
        counts[st] += 1
        col = COLOR.get(st, '#888780')
        vf = Path(b.get('visual_file') or '').name
        dup = reuse[vf] if vf else 0
        img = (f'<img src="{thumbs[i]}" alt="">' if thumbs.get(i)
               else '<div class="ph">no frame</div>')
        dupflag = f'<span class="dup">×{dup}</span>' if dup >= 3 else ''
        rows.append(
            f'<div class="b"><div class="th">{img}{dupflag}</div>'
            f'<div class="m"><span class="t">{mmss(b.get("start_sec"))}</span> '
            f'<span class="id">{html.escape(str(b.get("beat_id", i)))}</span>'
            f'<span class="pill" style="background:{col}">{st}</span><br>'
            f'<span class="rec">{html.escape(str(p["recipe"]))}</span> '
            f'<span class="cls">{p["class"]}</span><br>'
            f'<span class="tx">{html.escape((b.get("text") or "")[:70])}</span></div></div>')
        summary_rows.append((i, mmss(b.get('start_sec')), st, p['recipe']))

    verdict = 'PASS' if ok else 'BLOCKED'
    vcol = '#1D9E75' if ok else '#A32D2D'
    top = sorted([(c, n) for n, c in reuse.items() if c >= 3], reverse=True)[:8]
    chips = ' '.join(f'<span class="chip" style="background:{COLOR.get(k, "#888")}">{v} {k}</span>'
                     for k, v in counts.most_common())
    rep = ('<ul>' + ''.join(f'<li>{c}× <code>{html.escape(n)}</code></li>' for c, n in top) + '</ul>'
           if top else '<p>no visual reused ≥3×.</p>')

    css = ('body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:24px;color:#1a1a1a;background:#fafaf7}'
           'h1{font-size:20px;font-weight:500}h2{font-size:15px;font-weight:500;margin:22px 0 8px}'
           '.v{display:inline-block;color:#fff;padding:4px 12px;border-radius:14px;font-weight:500}'
           '.chip,.pill{color:#fff;border-radius:12px;padding:2px 8px;font-size:12px;display:inline-block}'
           '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}'
           '.b{display:flex;gap:8px;border:1px solid #e4e2da;border-radius:10px;padding:7px;background:#fff}'
           '.th{position:relative;flex:0 0 84px}.th img{width:84px;border-radius:5px;display:block}'
           '.ph{width:84px;height:47px;background:#eee;border-radius:5px;font-size:10px;color:#999;'
           'display:flex;align-items:center;justify-content:center}'
           '.dup{position:absolute;top:2px;left:2px;background:#A32D2D;color:#fff;font-size:10px;padding:0 4px;border-radius:8px}'
           '.m{font-size:12px;line-height:1.5}.t{color:#888;font-variant-numeric:tabular-nums}'
           '.id{color:#555;margin:0 5px}.rec{font-weight:500}.cls{color:#999}.tx{color:#666;font-size:11px}'
           'code{background:#f0eee8;padding:1px 4px;border-radius:4px;font-size:12px}')

    doc = (f'<!doctype html><meta charset="utf-8"><title>render report</title><style>{css}</style>'
           f'<h1>render report — {html.escape(Path(a.paper_edit).name)}</h1>'
           f'<p><span class="v" style="background:{vcol}">gate: {verdict}</span> '
           f'&nbsp; strict: {"PASS" if ok_strict else "BLOCKED"} &nbsp; {len(beats)} beats &nbsp; '
           f'{len(thumbs)} thumbnails</p><p>{chips}</p>'
           f'{("<p style=color:#A32D2D>" + thumb_note + "</p>") if thumb_note else ""}'
           f'<h2>repetition (visuals reused ≥3×)</h2>{rep}'
           f'<h2>beats</h2><div class="grid">{"".join(rows)}</div>')
    Path(a.out).write_text(doc)

    print(enforce(beats, strict=False)[1])
    print(f'\nwrote {a.out} ({len(beats)} beats, {len(thumbs)} thumbnails, {Path(a.out).stat().st_size // 1024} KB)')
    if thumb_note:
        print('  ' + thumb_note)
    print('  first beats:', summary_rows[:6])


if __name__ == '__main__':
    main()
