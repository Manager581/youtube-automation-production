#!/usr/bin/env python3
"""
extract_edit_grammar.py — reverse-engineer the EDIT GRAMMAR of a reference video.

It fuses the precise CUT list with the word-timed TRANSCRIPT so every cut is
annotated with WHAT was being said and (inferred) WHY it landed there — turning
"they cut every 1.4s" into transferable rules like "cut on a spoken stat -> card".

Signals (all measured, not guessed):
  - cuts        : ffmpeg scene-detection -> exact timestamp of every hard cut
  - transcript  : word-level timings parsed from YouTube auto-sub .vtt
  - moment-type : per cut, from the spoken context -> stat / turn / question /
                  pause-boundary / mid_phrase
  - SFX         : librosa onset (transient) times + how many land ON a cut
  - music bed   : fraction of audio frames above a silence floor

Reference-video analysis only (to derive editing rules). Writes <out>.json and
prints a summary.

Usage:
  venv.nosync/bin/python scripts/extract_edit_grammar.py \
    --video /tmp/edit_deep/megalodon.webm --vtt /tmp/edit_deep/megalodon.en.vtt \
    --out /tmp/edit_deep/megalodon_grammar.json --name megalodon
"""
import argparse, json, re, statistics, subprocess
from collections import Counter
from pathlib import Path

NUM = re.compile(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
                 r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
                 r'thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|'
                 r'billion|trillion)\b', re.I)
UNIT = re.compile(r'\b(tons?|pounds?|lbs?|kg|kilograms?|grams?|met(?:er|re)s?|feet|foot|'
                  r'miles?|mph|km|degrees?|years?|months?|weeks?|days?|hours?|minutes?|'
                  r'seconds?|percent|psi|inches?)\b', re.I)
TURN = {'but', 'until', 'then', 'however', 'suddenly', 'because', 'except', 'instead',
        'yet', 'although', 'unless', 'before', 'after', 'once', 'so', 'now', 'meanwhile'}
QWORD = {'what', 'how', 'why', 'could', 'would', 'can', 'will', 'does', 'which', 'who'}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def detect_cuts(video, thresh):
    r = sh(['ffmpeg', '-hide_banner', '-i', video, '-vf',
            f"select='gt(scene,{thresh})',showinfo", '-an', '-f', 'null', '-'])
    return sorted(set(round(float(m), 3) for m in re.findall(r'pts_time:([0-9.]+)', r.stderr)))


def parse_vtt_words(vtt_path):
    txt = Path(vtt_path).read_text(errors='ignore')
    words = []
    for m in re.finditer(r'<(\d\d):(\d\d):(\d\d\.\d\d\d)><c>\s*([^<]+?)</c>', txt):
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        w = m.group(4).strip()
        if w:
            words.append((t, w))
    if not words:  # fallback: cue-level timing
        for blk in re.finditer(r'(\d\d):(\d\d):(\d\d\.\d\d\d) -->.*?\n(.+?)(?:\n\n|\Z)', txt, re.S):
            t = int(blk.group(1)) * 3600 + int(blk.group(2)) * 60 + float(blk.group(3))
            for w in re.sub(r'<[^>]+>', '', blk.group(4)).split():
                words.append((t, w))
    seen, out = set(), []
    for t, w in sorted(words):
        k = (round(t, 2), w.lower())
        if k not in seen:
            seen.add(k)
            out.append((t, w))
    return out


def context(words, t, win):
    return ' '.join(w for (wt, w) in words if t - win <= wt <= t + win)


def word_at(words, t):
    prev = ''
    for wt, w in words:
        if wt <= t:
            prev = w
        else:
            break
    return prev


def is_pause_boundary(words, t):
    before = [wt for wt, _ in words if wt <= t]
    after = [wt for wt, _ in words if wt > t]
    if not before or not after:
        return True
    return (after[0] - before[-1]) > 0.6 and before[-1] < t < after[0]


def classify(ctx, pause):
    types = []
    if NUM.search(ctx) or UNIT.search(ctx):
        types.append('stat')
    toks = ctx.lower().split()
    if any(w in TURN for w in toks):
        types.append('turn')
    if toks and toks[0] in QWORD:
        types.append('question')
    if pause:
        types.append('pause_boundary')
    if not types:
        types.append('mid_phrase')
    return types


def detect_onsets(video):
    import librosa
    wav = '/tmp/_eg_audio.wav'
    sh(['ffmpeg', '-y', '-hide_banner', '-i', video, '-ac', '1', '-ar', '22050', wav])
    y, sr = librosa.load(wav, sr=22050)
    onsets = librosa.onset.onset_detect(y=librosa.effects.percussive(y), sr=sr,
                                         units='time', backtrack=False)
    rms = librosa.feature.rms(y=y)[0]
    return [round(float(t), 3) for t in onsets], round(float((rms > 0.01).mean()), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True)
    ap.add_argument('--vtt', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--thresh', type=float, default=0.3)
    ap.add_argument('--name', default='')
    a = ap.parse_args()

    dur = float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'default=nk=1:nw=1', a.video]).stdout.strip() or 0)
    cuts = detect_cuts(a.video, a.thresh)
    words = parse_vtt_words(a.vtt)
    try:
        onsets, music_active = detect_onsets(a.video)
    except Exception as e:
        onsets, music_active = [], -1
        print(f"[warn] onset detection failed: {e}")

    recs, prev = [], 0.0
    for t in cuts:
        pause = is_pause_boundary(words, t)
        ctx = context(words, t, 0.7)
        recs.append({
            't': round(t, 2), 'shot_dur': round(t - prev, 2),
            'word_at': word_at(words, t), 'spoken': ctx,
            'spoken_wide': context(words, t, 2.2),
            'moment': classify(ctx, pause),
            'sfx_on_cut': any(abs(o - t) <= 0.2 for o in onsets),
        })
        prev = t

    durs = [c['shot_dur'] for c in recs if c['shot_dur'] > 0]
    mt = Counter(m for c in recs for m in c['moment'])
    summary = {
        'name': a.name or Path(a.video).stem,
        'duration_sec': round(dur, 1), 'n_cuts': len(cuts),
        'cuts_per_min': round(len(cuts) / (dur / 60), 1) if dur else 0,
        'shot_dur_median': round(statistics.median(durs), 2) if durs else 0,
        'shot_dur_mean': round(statistics.mean(durs), 2) if durs else 0,
        'pct_shots_under_2s': round(100 * sum(d < 2 for d in durs) / max(1, len(durs)), 1),
        'pct_shots_under_1s': round(100 * sum(d < 1 for d in durs) / max(1, len(durs)), 1),
        'pct_shots_over_5s': round(100 * sum(d > 5 for d in durs) / max(1, len(durs)), 1),
        'n_sfx_onsets': len(onsets),
        'sfx_per_min': round(len(onsets) / (dur / 60), 1) if dur else 0,
        'sfx_on_cut_rate': round(sum(c['sfx_on_cut'] for c in recs) / max(1, len(recs)), 3),
        'music_active_frac': music_active,
        'moment_at_cut_pct': {k: round(100 * v / max(1, len(recs)), 1) for k, v in mt.most_common()},
        'n_words': len(words),
    }
    Path(a.out).write_text(json.dumps({'summary': summary, 'cuts': recs}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
