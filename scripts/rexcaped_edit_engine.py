#!/usr/bin/env python3
"""
rexcaped_edit_engine.py — turn a word-timed narration into an EDIT PLAN using the
measured edit grammar (research/edit_grammar_ruleset.md).

Two layers:
  1. CUT-LATTICE  — candidate cut points on script features (stat / turn / pause).
  2. TEMPO        — selects which candidates actually FIRE, by section:
                     slow hook -> faster body -> rapid-fire bursts on dense
                     enumeration ("the math is simple, you're always hunting...").

Then it assigns each shot an ASSET TYPE (creature / stock / meme / card) per the
measured mix + rules (stat->card, comedic-release->meme, hero beat->creature,
default->stock), a meme on a ~75s cadence, sound-on-every-cut, logo stamps.

Self-validates generated cuts against a reference video's real cuts when --grammar
is given (recall / precision / count vs ground truth).

Usage (validate against the real T.Rex):
  venv.nosync/bin/python scripts/rexcaped_edit_engine.py \
    --vtt /tmp/edit_deep/trex.en.vtt --grammar /tmp/edit_deep/trex_grammar.json \
    --hook-dur 4.8 --body-dur 3.0 --out /tmp/edit_deep/trex_engine_plan.json
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


def parse_words(path):
    txt = Path(path).read_text(errors='ignore')
    if path.endswith('.json'):                      # narration manifest -> approx word times
        m = json.load(open(path))
        words = []
        for seg in m.get('segments', []):
            if seg.get('type') != 'speech':
                continue
            toks = seg['text'].split()
            t0, dur = seg['start_sec'], seg['duration_sec']
            for k, w in enumerate(toks):
                words.append((round(t0 + dur * k / max(1, len(toks)), 2), w))
        return words
    words, seen = [], set()
    for m in re.finditer(r'<(\d\d):(\d\d):(\d\d\.\d\d\d)><c>\s*([^<]+?)</c>', txt):
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        w = m.group(4).strip()
        k = (round(t, 2), w.lower())
        if w and k not in seen:
            seen.add(k); words.append((t, w))
    return sorted(words)


def tag_candidates(words):
    cands = []
    for i, (t, w) in enumerate(words):
        types = []
        if NUM.search(w) or UNIT.search(w):
            types.append('stat')
        if w.lower().strip('.,!?') in TURN:
            types.append('turn')
        if i and (t - words[i - 1][0]) > 0.6:
            types.append('pause')
        if types:
            cands.append({'t': round(t, 2), 'types': types})
    return cands


def select_cuts(cands, hook_end, hook_dur, body_dur, burst_win, burst_min):
    """greedy: fire on the next candidate once target shot-length elapsed; on a
    dense candidate cluster (a list), fire a rapid-fire burst."""
    cuts, last, i, n = [], -99.0, 0, len(cands)
    while i < n:
        t = cands[i]['t']
        j = i
        while j < n and cands[j]['t'] < t + burst_win:
            j += 1
        packed = j - i
        if packed >= burst_min and (t - last) >= 1.0:          # list -> rapid-fire
            for k in range(i, j):
                cuts.append({'t': cands[k]['t'], 'why': 'burst'})
            last = cands[j - 1]['t']; i = j; continue
        tgt = hook_dur if t < hook_end else body_dur
        if t - last >= tgt:
            cuts.append({'t': t, 'why': '+'.join(cands[i]['types'])})
            last = t
        i += 1
    return cuts


def assign_assets(cuts, dur, meme_cadence=75.0):
    """asset type per shot, per the measured mix + rules."""
    out, last_meme = [], -999
    for c in cuts:
        t, why = c['t'], c['why']
        if 'stat' in why:
            a = 'stat_card'
        elif (t - last_meme) >= meme_cadence and 'turn' in why:
            a = 'meme'; last_meme = t
        elif why == 'burst':
            a = 'stock'                      # rapid-fire list montage = stock/creature flashes
        else:
            a = 'creature' if (hash(round(t)) % 5 == 0) else 'stock'
        out.append({'t': t, 'why': why, 'asset': a, 'sfx_on_cut': True})
    return out


def validate(gen_cuts, grammar_path, tol=1.0):
    real = [c['t'] for c in json.load(open(grammar_path))['cuts']]
    gt = [c['t'] for c in gen_cuts]
    if not real or not gt:
        return {}

    def nearest(x, arr):
        return min((abs(x - y) for y in arr), default=9e9)
    recall = round(100 * sum(nearest(r, gt) <= tol for r in real) / len(real), 1)
    prec = round(100 * sum(nearest(g, real) <= tol for g in gt) / len(gt), 1)
    return {'real_cuts': len(real), 'gen_cuts': len(gt), 'recall_pct': recall,
            'precision_pct': prec, 'count_ratio': round(len(gt) / len(real), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vtt', help='word-timed .vtt OR narration manifest .json')
    ap.add_argument('--grammar', help='reference *_grammar.json to validate against')
    ap.add_argument('--out')
    ap.add_argument('--hook-end', type=float, default=50)
    ap.add_argument('--hook-dur', type=float, default=4.8)
    ap.add_argument('--body-dur', type=float, default=3.0)
    ap.add_argument('--burst-win', type=float, default=2.2)
    ap.add_argument('--burst-min', type=int, default=4)
    a = ap.parse_args()

    words = parse_words(a.vtt)
    dur = words[-1][0] if words else 0
    cands = tag_candidates(words)
    cuts = select_cuts(cands, a.hook_end, a.hook_dur, a.body_dur, a.burst_win, a.burst_min)
    plan = assign_assets(cuts, dur)

    print(f"words={len(words)}  candidates={len(cands)}  -> generated cuts={len(cuts)}")
    from collections import Counter
    print("  asset mix:", dict(Counter(p['asset'] for p in plan)))
    if a.grammar:
        print("  VALIDATION vs real:", json.dumps(validate(cuts, a.grammar)))
    if a.out:
        Path(a.out).write_text(json.dumps({'plan': plan, 'params': vars(a)}, indent=1))
        print("  wrote", a.out)


if __name__ == '__main__':
    main()
