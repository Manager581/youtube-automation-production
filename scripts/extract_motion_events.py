#!/usr/bin/env python3
"""
extract_motion_events.py — Tier-1 mechanical pass of the frame-event study:
measure the WITHIN-SHOT motion that hard-cut analysis misses (egg sways,
crack-pops, sun slams, overlay slide-ins — the texture layer of the reference
style that scene-detect calls a "10s hold").

Method (validated by the 2026-06-10 prototype on DzUKhb2ZSko 0-14s):
  - decode EVERY frame at --fps via an ffmpeg gray rawvideo pipe (no temp jpgs)
  - inter-frame mean-abs-diff curve over the whole video
  - segment by the hard cuts in *_grammar.json (extract_edit_grammar.py output)
  - per shot: motion floor (median diff), profile class
      static <1.0 / drift 1-6 / alive 6-15 / kinetic >15   (gray levels, 320px)
    and WITHIN-SHOT EVENTS = frames where diff > max(med + 4*MAD, med+5, 6),
    local-maximum filtered, excluding ±0.25s around the hard cuts themselves
  - fuse each event with the nearest spoken word (--vtt) and the nearest
    percussive onset; compute a music beat grid (librosa.beat_track)
  - headline stat: VISUAL EVENT RATE = (hard cuts + within-shot events)/min —
    the number the cut rate alone understates ~2x in the reference hook.

Usage (smoke test on the egg open, then the full video):
  venv/bin/python scripts/extract_motion_events.py \
    --video /tmp/edit_deep/trex.webm --vtt /tmp/edit_deep/trex.en.vtt \
    --grammar research/edit_analysis/trex_grammar.json \
    --out /tmp/edit_deep/trex_motion_events.json [--t0 0 --t1 60]
"""
import argparse, json, subprocess, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_edit_grammar import parse_vtt_words  # noqa: E402

W, H = 320, 180
CLASSES = [(1.0, 'static'), (6.0, 'drift'), (15.0, 'alive'), (1e9, 'kinetic')]


def motion_curve(video, fps, t0, t1):
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error']
    if t0:
        cmd += ['-ss', str(t0)]
    if t1:
        cmd += ['-t', str(t1 - t0)]
    cmd += ['-i', video, '-vf', f'fps={fps},scale={W}:{H},format=gray',
            '-f', 'rawvideo', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = W * H
    prev, diffs = None, []
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        fr = np.frombuffer(buf, np.uint8).astype(np.float32)
        diffs.append(0.0 if prev is None else float(np.abs(fr - prev).mean()))
        prev = fr
    p.wait()
    return np.array(diffs)


def classify(med):
    for lim, name in CLASSES:
        if med < lim:
            return name
    return 'kinetic'


def shot_events(d, fps, t0, cut_times, end_t):
    """Per-shot baseline + within-shot event spikes (local maxima, cut-masked)."""
    bounds = [t0] + [c for c in cut_times if t0 < c < end_t] + [end_t]
    near_cut = np.zeros(len(d), bool)
    for c in cut_times:
        i = int(round((c - t0) * fps))
        near_cut[max(0, i - int(0.25 * fps)):i + int(0.25 * fps) + 1] = True
    shots, events = [], []
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        i0, i1 = int((a - t0) * fps), int((b - t0) * fps)
        seg = d[i0:i1]
        if len(seg) < 3:
            continue
        inner = seg[~near_cut[i0:i1]]
        med = float(np.median(inner)) if len(inner) else float(np.median(seg))
        mad = float(np.median(np.abs(inner - med))) if len(inner) else 0.0
        thr = max(med + 4 * mad, med + 5, 6.0)
        ev = []
        for j in range(1, len(seg) - 1):
            gi = i0 + j
            if near_cut[gi] or seg[j] <= thr:
                continue
            if seg[j] >= seg[j - 1] and seg[j] >= seg[j + 1]:      # local max
                ev.append({'t': round(t0 + gi / fps, 2), 'mag': round(float(seg[j]), 1)})
        # merge spikes <0.3s apart (one physical event, e.g. a 2-frame slam)
        merged = []
        for e in ev:
            if merged and e['t'] - merged[-1]['t'] < 0.3:
                if e['mag'] > merged[-1]['mag']:
                    merged[-1] = e
            else:
                merged.append(e)
        shots.append({'idx': k, 't0': round(a, 2), 't1': round(b, 2),
                      'motion_med': round(med, 1),
                      'motion_p90': round(float(np.percentile(inner, 90)) if len(inner) else med, 1),
                      'class': classify(med), 'n_events': len(merged)})
        events.extend({**e, 'shot_idx': k} for e in merged)
    return shots, events


def audio_layers(video, t0, t1):
    import librosa
    wav = '/tmp/_motion_events_audio.wav'
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error']
    if t0:
        cmd += ['-ss', str(t0)]
    if t1:
        cmd += ['-t', str(t1 - t0)]
    cmd += ['-i', video, '-ac', '1', '-ar', '22050', wav]
    subprocess.run(cmd, check=True)
    y, sr = librosa.load(wav, sr=22050)
    perc = librosa.effects.percussive(y)
    onsets = [round(float(t) + t0, 2) for t in
              librosa.onset.onset_detect(y=perc, sr=sr, units='time')]
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    return onsets, float(np.atleast_1d(tempo)[0]), [round(float(b) + t0, 2) for b in beats]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True)
    ap.add_argument('--vtt', required=True)
    ap.add_argument('--grammar', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--fps', type=int, default=15)
    ap.add_argument('--t0', type=float, default=0.0)
    ap.add_argument('--t1', type=float, default=None)
    a = ap.parse_args()

    g = json.load(open(a.grammar))
    dur = g['summary']['duration_sec']
    t1 = a.t1 or dur
    cuts = [c['t'] for c in g['cuts'] if a.t0 < c['t'] < t1]

    print(f"decoding {a.video} @ {a.fps}fps gray {W}x{H} [{a.t0}-{t1:.1f}s] ...", flush=True)
    d = motion_curve(a.video, a.fps, a.t0, t1)
    print(f"  {len(d)} frames; global diff median {np.median(d):.1f}", flush=True)

    shots, events = shot_events(d, a.fps, a.t0, cuts, t1)
    words = [(t, w) for t, w in parse_vtt_words(a.vtt) if a.t0 <= t <= t1]

    print("audio layers (onsets + beat grid) ...", flush=True)
    onsets, tempo, beats = audio_layers(a.video, a.t0, t1)

    on = np.array(onsets) if onsets else np.array([0.0])
    for e in events:
        e['onset_dt'] = round(float(np.min(np.abs(on - e['t']))), 2)
        near = [(abs(t - e['t']), t, w) for t, w in words if abs(t - e['t']) <= 1.0]
        e['word'] = min(near)[2] if near else None
        e['word_t'] = min(near)[1] if near else None

    span_min = (t1 - a.t0) / 60
    n_classes = {c: sum(1 for s in shots if s['class'] == c) for c in
                 ('static', 'drift', 'alive', 'kinetic')}
    summary = {
        'video': a.video, 'span': [a.t0, round(t1, 1)], 'fps': a.fps,
        'n_shots': len(shots), 'n_hard_cuts': len(cuts),
        'n_within_shot_events': len(events),
        'cuts_per_min': round(len(cuts) / span_min, 1),
        'visual_event_rate_per_min': round((len(cuts) + len(events)) / span_min, 1),
        'motion_floor_median': round(float(np.median([s['motion_med'] for s in shots])), 1),
        'pct_shots_truly_static': round(100 * n_classes['static'] / max(1, len(shots)), 1),
        'shot_class_counts': n_classes,
        'events_on_onset_pct': round(100 * sum(1 for e in events if e['onset_dt'] <= 0.15)
                                     / max(1, len(events)), 1),
        'music_tempo_bpm': round(tempo, 1), 'n_beats': len(beats),
    }
    Path(a.out).write_text(json.dumps(
        {'summary': summary, 'shots': shots, 'events': events,
         'beat_grid': beats, 'onsets': onsets}, indent=1))
    print(json.dumps(summary, indent=1))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
