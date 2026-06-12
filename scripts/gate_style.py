#!/usr/bin/env python3
"""
gate_style.py — THE canonical "does this render match the APPROVED STYLE" gate.

Why this exists: every handoff session kept writing its own gate (preflight,
gate_ch1 sync/motion/subject) that tested what that session built — never the
style the owner approved. Green gates, wrong-feeling output, every time.
This gate encodes the approved style itself (research/style_bands.json, sourced
from research/viral_recreation_spec.md) so "green" finally means "in the band".

Measures (motion method = the validated curve from extract_motion_events.py):
  EVENTS  visual event rate/min = hard cuts + within-shot events   >= band
  GAP     max runtime gap without any visual event                 <= band
  SHOT    median shot length (between hard cuts)                   in band
  STATIC  share of runtime in 'static' motion class (<1.0 gray)    <= band
  MUSIC   audio coverage above bed floor (catches missing bed)     >= band
  CARDS   (with --paper-edit) full-frame card/graphic beat holds   <= band

Usage:
  venv/bin/python scripts/gate_style.py --render output/foo.mp4 \
      [--paper-edit storyboards/foo.json] [--bands research/style_bands.json]
Exit 0 = in band on every measured axis; 1 = any FAIL.
"""
import argparse, json, subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
W, H = 320, 180
FPS = 12.0
HARD_CUT = 22.0          # gray-level mean-abs-diff that only a cut produces
MIN_CUT_SEP = 0.34       # s


def motion_curve(video):
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(video),
           '-vf', f'fps={FPS},scale={W}:{H},format=gray', '-f', 'rawvideo', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n, prev, diffs = W * H, None, []
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        fr = np.frombuffer(buf, np.uint8).astype(np.float32)
        diffs.append(0.0 if prev is None else float(np.abs(fr - prev).mean()))
        prev = fr
    p.wait()
    return np.array(diffs)


def local_maxima(idx, curve, min_sep_frames):
    keep, last = [], -10**9
    for i in sorted(idx, key=lambda i: -curve[i]):
        if all(abs(i - k) >= min_sep_frames for k in keep):
            keep.append(i)
    return sorted(keep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--render', required=True)
    ap.add_argument('--paper-edit')
    ap.add_argument('--bands', default=str(ROOT / 'research/style_bands.json'))
    ap.add_argument('--report')
    a = ap.parse_args()
    B = json.load(open(a.bands))

    print(f'[1/3] motion curve {a.render} ...')
    d = motion_curve(a.render)
    dur = len(d) / FPS

    # hard cuts
    cut_idx = local_maxima(np.where(d > HARD_CUT)[0], d, int(MIN_CUT_SEP * FPS))
    cuts = [i / FPS for i in cut_idx]

    # within-shot events (formula from extract_motion_events.py docstring)
    bounds = [0] + cut_idx + [len(d)]
    ev_idx = []
    for s, e in zip(bounds[:-1], bounds[1:]):
        seg = d[s:e]
        if len(seg) < 4:
            continue
        med = float(np.median(seg))
        mad = float(np.median(np.abs(seg - med)))
        thr = max(med + 4 * mad, med + 5, 6)
        cand = [s + i for i in np.where(seg > thr)[0]
                if all(abs((s + i) - c) > 0.25 * FPS for c in cut_idx)]
        ev_idx += local_maxima(cand, d, int(0.3 * FPS))
    events = sorted(cuts + [i / FPS for i in ev_idx])

    event_rate = len(events) / dur * 60
    gaps = np.diff([0] + events + [dur]) if events else [dur]
    max_gap = float(np.max(gaps))
    shots = np.diff([0] + cuts + [dur])
    med_shot = float(np.median(shots))

    # static share: 1s windows whose median diff < 1.0 (class 'static')
    win = int(FPS)
    meds = [np.median(d[i:i + win]) for i in range(0, max(1, len(d) - win), win)]
    static_share = float(np.mean([m < 1.0 for m in meds])) if meds else 1.0

    # music/bed floor: mono 8k RMS in 50ms windows
    print('[2/3] audio bed coverage ...')
    pa = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error',
                         '-i', a.render, '-ac', '1', '-ar', '8000',
                         '-f', 's16le', '-'], capture_output=True)
    au = np.frombuffer(pa.stdout, np.int16).astype(np.float32) / 32768.0
    wn = 400  # 50ms
    nw = len(au) // wn
    rms = np.sqrt((au[:nw * wn].reshape(nw, wn) ** 2).mean(axis=1))
    db = 20 * np.log10(np.maximum(rms, 1e-6))
    coverage = float(np.mean(db > B['music_floor_dbfs']))

    # cards + creature-on-still (paper edit optional)
    # Creature rule (owner, locked 2026-06-11): every creature beat MOVES as a
    # layered composite or real footage — "zero Ken-Burns-on-a-still passing as
    # a shot". A c_*/ch_* still rendered as a flat image beat is the REJECTED
    # pattern even with drift. Ink gags (i_*) are deliberate comedy stills.
    card_rows, worst_hold, still_rows = [], 0.0, []
    if a.paper_edit:
        pe = json.load(open(a.paper_edit))
        for i, b in enumerate(pe['beats']):
            vis = Path(b.get('visual_file', '') or '').name
            if vis.startswith(('card_', 'g_')):
                hold = b['end_sec'] - b['start_sec']
                worst_hold = max(worst_hold, hold)
                card_rows.append((i, vis, hold))
            elif vis.startswith(('c_', 'ch_')) and b.get('visual_type') == 'image':
                still_rows.append((i, vis, b['end_sec'] - b['start_sec']))

    print('[3/3] verdict\n')
    checks = [
        ('EVENTS', f"{event_rate:.1f}/min", event_rate >= B['event_rate_per_min_min'],
         f">={B['event_rate_per_min_min']}"),
        ('GAP', f"{max_gap:.1f}s max", max_gap <= B['max_event_gap_sec'],
         f"<={B['max_event_gap_sec']}s"),
        ('SHOT', f"median {med_shot:.2f}s",
         B['median_shot_sec_min'] <= med_shot <= B['median_shot_sec_max'],
         f"{B['median_shot_sec_min']}-{B['median_shot_sec_max']}s"),
        ('STATIC', f"{static_share:.0%} of runtime", static_share <= B['static_share_max'],
         f"<={B['static_share_max']:.0%}"),
        ('MUSIC', f"{coverage:.0%} > {B['music_floor_dbfs']:.0f}dBFS",
         coverage >= B['music_coverage_min'], f">={B['music_coverage_min']:.0%}"),
    ]
    if a.paper_edit:
        checks.append(('CARDS', f"{len(card_rows)} cards, worst hold {worst_hold:.2f}s",
                       worst_hold <= B['card_hold_sec_max'] and len(card_rows) <= B['card_count_max'],
                       f"<={B['card_hold_sec_max']}s hold, <={B['card_count_max']} cards"))
        checks.append(('CREATURE', f"{len(still_rows)} creature beats on flat stills",
                       len(still_rows) == 0, 'must be composite/footage, never a still'))
    n_fail = 0
    for name, val, ok, band in checks:
        n_fail += (not ok)
        print(f"  {'✅' if ok else '❌'} {name:8s} {val:34s} band {band}")
    if card_rows:
        for i, vis, hold in card_rows:
            flag = '  ⚠ OVER' if hold > B['card_hold_sec_max'] else ''
            print(f"     beat {i:3d} {vis:26s} {hold:.2f}s{flag}")
    if still_rows:
        for i, vis, hold in still_rows:
            print(f"     beat {i:3d} {vis:26s} {hold:.2f}s  ⚠ STILL → composite it")
    print(f"\nSTYLE GATE: {'ALL IN BAND ✅' if n_fail == 0 else f'{n_fail} AXES OUT OF BAND ❌'}"
          f"  ({a.render})")
    if a.report:
        json.dump(dict(render=a.render, duration=dur, event_rate=event_rate,
                       max_gap=max_gap, median_shot=med_shot,
                       static_share=static_share, music_coverage=coverage,
                       cards=[dict(beat=i, visual=v, hold=h) for i, v, h in card_rows],
                       creature_stills=[dict(beat=i, visual=v, hold=h) for i, v, h in still_rows],
                       fails=n_fail), open(a.report, 'w'), indent=1)
        print('wrote', a.report)
    raise SystemExit(1 if n_fail else 0)


if __name__ == '__main__':
    main()
