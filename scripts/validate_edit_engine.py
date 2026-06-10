#!/usr/bin/env python3
"""
validate_edit_engine.py — measure how PREDICTABLE a reference video's cuts are
from its script. Generates cut predictions from simple rules and compares them to
the real extracted cuts (from *_grammar.json). High semantic recall => the editing
is script-driven => a program can reproduce it.

  semantic recall : % of REAL cuts that a stat/turn/pause rule predicts (±1.0s)
  full recall     : same, after adding a body-cadence fill (~every 2.8s)
  precision       : % of PREDICTED cuts that hit a real cut (over-prediction check)

Usage:
  venv.nosync/bin/python scripts/validate_edit_engine.py \
    --grammar /tmp/edit_deep/trex_grammar.json --vtt /tmp/edit_deep/trex.en.vtt --name trex
"""
import argparse, json, re
from pathlib import Path

NUM = re.compile(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
                 r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
                 r'thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|'
                 r'billion|trillion)\b', re.I)
UNIT = re.compile(r'\b(tons?|pounds?|lbs?|kg|met(?:er|re)s?|feet|foot|miles?|mph|degrees?|'
                  r'years?|months?|weeks?|days?|hours?|minutes?|seconds?|percent|psi)\b', re.I)
TURN = {'but', 'until', 'then', 'however', 'suddenly', 'because', 'except', 'instead',
        'yet', 'although', 'unless', 'before', 'after', 'once', 'so', 'now', 'meanwhile'}


def parse_vtt_words(p):
    txt = Path(p).read_text(errors='ignore')
    words, seen = [], set()
    for m in re.finditer(r'<(\d\d):(\d\d):(\d\d\.\d\d\d)><c>\s*([^<]+?)</c>', txt):
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        w = m.group(4).strip()
        k = (round(t, 2), w.lower())
        if w and k not in seen:
            seen.add(k)
            words.append((t, w))
    return sorted(words)


def nearest(t, arr):
    return min((abs(t - x) for x in arr), default=9e9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--grammar', required=True)
    ap.add_argument('--vtt', required=True)
    ap.add_argument('--name', default='')
    ap.add_argument('--tol', type=float, default=1.0)
    ap.add_argument('--cadence', type=float, default=2.8)
    a = ap.parse_args()

    real = [c['t'] for c in json.load(open(a.grammar))['cuts']]
    words = parse_vtt_words(a.vtt)

    # --- semantic predictions: stat / turn / pause-boundary ---
    sem = set()
    for i, (t, w) in enumerate(words):
        if NUM.search(w) or UNIT.search(w):
            sem.add(round(t, 1))
        if w.lower().strip('.,') in TURN:
            sem.add(round(t, 1))
        if i and (t - words[i - 1][0]) > 0.6:          # resumed after a pause
            sem.add(round(t, 1))
    sem = sorted(sem)

    # --- full predictions: semantic + body-cadence fill ---
    full = sorted(sem)
    filled, last = list(sem), 0.0
    span = max(real + [w[0] for w in words]) if real else 0
    grid = [round(x, 1) for x in frange(0, span, a.cadence)]
    allp = sorted(set(sem) | set(grid))

    def recall(preds):
        if not real:
            return 0.0
        return round(100 * sum(nearest(t, preds) <= a.tol for t in real) / len(real), 1)

    def precision(preds):
        if not preds:
            return 0.0
        return round(100 * sum(nearest(p, real) <= a.tol for p in preds) / len(preds), 1)

    print(f"[{a.name}] real_cuts={len(real)}  words={len(words)}")
    print(f"  semantic preds (stat/turn/pause): {len(sem)}")
    print(f"    semantic RECALL  (real cuts the script alone predicts): {recall(sem)}%")
    print(f"    semantic precision: {precision(sem)}%")
    print(f"  + body-cadence fill (~every {a.cadence}s): total preds {len(allp)}")
    print(f"    full RECALL: {recall(allp)}%   full precision: {precision(allp)}%")


def frange(a, b, step):
    x = a
    while x < b:
        yield x
        x += step


if __name__ == '__main__':
    main()
