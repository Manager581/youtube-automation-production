#!/usr/bin/env python3
"""
gate_ch1.py — per-beat CONTENT gate for a rendered chapter (the workflow fix from
memory feedback_self_verifying_pipeline). The owner only sees a cut after every
beat is green here AND the contact sheet has been eyeballed.

  1. SYNC    — whisper-transcribes the RENDER (not the plan), then per beat
               compares the words heard inside the beat window vs the paper-edit
               text (token overlap). Catches drift / wrong-line-at-wrong-time.
  2. MOTION  — mean abs frame-diff per beat sampled from the RENDER. Beats whose
               visual is a video (composite/clip) must clear a motion floor;
               catches static-where-should-move.
  3. SUBJECT — noun->asset mapping: a beat whose VO names a thing must show an
               asset mapped to that thing (catches body->street, nose->taxi).

Usage:
  venv/bin/python scripts/gate_ch1.py \
    --render output/trex_pilot_ch1_body_540p.mp4 \
    --paper-edit storyboards/trex_pilot_ch1_only.json \
    [--report output/gate_ch1.json]
"""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

STOP = set('a an the and or of to in on you your is are was be it that this with for — - just'.split())
MOTION_FLOOR_VIDEO = 0.5          # video beats below this = suspiciously static
                                  # (calibrated: dark slow cinematic shots ~0.7; true freezes ~0.0x)
MOTION_FLOOR_IMAGE = 0.10         # stills get Ken Burns; ~0 means a frozen frame
SYNC_FLOOR = 0.45                 # token-overlap ratio per beat

# VO noun -> required asset (basename regex). First matching text rule applies.
SUBJECT_MAP = [
    (r'body you just woke',                    r'body_reveal'),
    (r'thirteen feet|forty feet|full city bus', r'body_reveal'),
    (r'single stride',                         r'stride'),
    (r'legs are the most powerful',            r'ch1_legs'),
    (r'trip at speed|slams',                   r'ch1_stumble'),
    (r'famously',                              r'tiny_arms_macro'),
    (r'push you back up',                      r'trip_stumble'),
    (r'falling down is the same as dying',     r'i_uhoh'),
    (r'wet, flat concrete',                    r'wet_asphalt'),
    (r'furnace',                               r'ch1_furnace'),
    (r'food than this entire street',          r'food_cart'),
    (r'survive here',                          r'taxi_hunt'),
    (r'to hunt here',                          r'glass_reflection|taxi_hunt'),
    (r'glass, steel',                          r'glass_tower'),
    (r'four million strangers',                r'pov_crowd_up'),
    (r'your nose|best that ever existed',      r'ch1_nostril'),
    (r'smell blood',                           r'smell_map'),
    (r'eyes face forward',                     r'eye_detail'),
    (r'hawk',                                  r'hawk_eye'),
    (r'running figure out of a crowd',         r'ch1_povpick'),
    (r'twelve miles an hour|top out around',   r'ch1_speed'),
    (r'sprint would break',                    r'leg_xray'),
    (r'not need to be fast',                   r'ch1_loom'),
]


def toks(s):
    return [w for w in re.findall(r"[a-z']+", s.lower()) if w not in STOP]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--render', required=True)
    ap.add_argument('--paper-edit', required=True)
    ap.add_argument('--report', default=None)
    ap.add_argument('--whisper-model', default='base')
    a = ap.parse_args()

    beats = json.load(open(a.paper_edit))['beats']

    # ── transcribe the render once (word timestamps) ──
    print(f'[1/3] whisper({a.whisper_model}) on {a.render} ...')
    import whisper
    model = whisper.load_model(a.whisper_model)
    res = model.transcribe(a.render, word_timestamps=True, fp16=False, language='en')
    words = [(w['start'], w['word']) for seg in res['segments'] for w in seg.get('words', [])]

    # ── sample frames once (4 fps, small, grayscale) ──
    print('[2/3] sampling frames for motion ...')
    td = Path(tempfile.mkdtemp(prefix='gate_'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.render,
                    '-vf', 'fps=4,scale=240:-1,format=gray', str(td / 'f%05d.png')], check=True)
    frames = sorted(td.glob('f*.png'))
    arrs = [np.asarray(Image.open(f), np.float32) for f in frames]

    def motion(t0, t1):
        # median, trimmed inside the window: a hard CUT at a boundary must not
        # mask a frozen beat (mean was fooled by exactly that)
        i0, i1 = max(0, int(t0 * 4) + 1), min(len(arrs) - 1, int(t1 * 4) - 1)
        if i1 <= i0 + 1:
            return 0.0
        ds = [np.abs(arrs[i + 1] - arrs[i]).mean() for i in range(i0, i1 - 1)]
        return float(np.median(ds))

    # ── per-beat checks ──
    print('[3/3] gating beats ...\n')
    print(f"{'#':>3} {'t':>7} {'SYNC':>5} {'MOT':>6} {'SUBJ':>4}  visual / flags")
    rows, n_fail = [], 0
    for i, b in enumerate(beats):
        t0, t1 = b['start_sec'], b['end_sec']
        vt = b.get('visual_type', 'image')
        vis = Path(b.get('visual_file', '-')).name
        exp = toks(b.get('text', ''))
        heard = [w for t, w in words if t0 - .15 <= t < t1 + .15]
        got = toks(' '.join(heard))
        sync = (len(set(exp) & set(got)) / len(set(exp))) if exp else 1.0
        mot = motion(t0, t1)
        floor = MOTION_FLOOR_VIDEO if vt == 'video' else MOTION_FLOOR_IMAGE
        if re.match(r'^(g_|i_|card_)', vis):
            floor = 0.0                       # cards / ink gags are flash-holds by design
        sub_ok, sub_want = True, None
        text_l = b.get('text', '').lower()
        for pat, want in SUBJECT_MAP:
            if re.search(pat, text_l):
                sub_want = want
                sub_ok = re.search(want, vis) is not None
                break
        flags = []
        if sync < SYNC_FLOOR:
            flags.append(f'SYNC<{SYNC_FLOOR}')
        if mot < floor:
            flags.append(f'STATIC(<{floor})')
        if not sub_ok:
            flags.append(f'SUBJECT wants /{sub_want}/')
        ok = not flags
        n_fail += (not ok)
        rows.append(dict(beat=i, t0=t0, t1=t1, sync=round(sync, 2), motion=round(mot, 2),
                         subject_ok=sub_ok, visual=vis, flags=flags, text=b.get('text', '')[:60]))
        mark = '✅' if ok else '❌'
        print(f"{i:3d} {t0:7.2f} {sync:5.2f} {mot:6.2f} {'ok' if sub_ok else 'NO':>4}  {mark} {vis}"
              + ('   ' + ';'.join(flags) if flags else ''))

    print(f"\nGATE: {len(beats) - n_fail}/{len(beats)} beats green"
          + (f' — {n_fail} FAILING' if n_fail else ' — ALL GREEN'))
    if a.report:
        json.dump(dict(render=a.render, beats=rows, failing=n_fail), open(a.report, 'w'), indent=1)
        print('wrote', a.report)
    raise SystemExit(1 if n_fail else 0)


if __name__ == '__main__':
    main()
