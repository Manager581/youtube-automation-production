#!/usr/bin/env python3
"""
rexcaped_edit_engine.py — turn a word-timed narration into an EDIT PLAN using the
measured edit grammar (research/edit_grammar_ruleset.md).

Three layers:
  1. CUT-LATTICE  — candidate cut points on script features (stat / turn / pause).
  2. TEMPO        — selects which candidates actually FIRE, by section:
                     slow hook -> faster body -> rapid-fire bursts on dense
                     enumeration ("the math is simple, you're always hunting...").
  3. ASSETS       — each SHOT gets an asset type, quota-balanced to the MEASURED
                     mix (stock ~42% / meme ~26% / creature ~21% / card ~10.5%):
                     stat->card when the shot can hold one, meme reset every ~75s,
                     hero-creature open, deterministic largest-deficit fill.
                     Stat shots carry extracted card text for the card generator.

Self-validates generated cuts against a reference video's real cuts when --grammar
is given (recall / precision / count vs ground truth).

Usage (validate against the real T.Rex):
  venv.nosync/bin/python scripts/rexcaped_edit_engine.py \
    --vtt /tmp/edit_deep/trex.en.vtt --grammar /tmp/edit_deep/trex_grammar.json \
    --hook-dur 4.8 --body-dur 3.0 --out /tmp/edit_deep/trex_engine_plan.json

Output JSON: {shots: [{t, end, dur, why, text, asset, card?, sfx_on_cut}],
              cuts: [...], mix: {...}, params: {...}}
"""
import argparse, json, re
from pathlib import Path

NUM = re.compile(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
                 r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
                 r'thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|'
                 r'billion|trillion)\b', re.I)
UNIT = re.compile(r'\b(tons?|pounds?|lbs?|kg|m|cm|km|mm|ft|met(?:er|re)s?|feet|foot|miles?|'
                  r'mph|degrees?|years?|months?|weeks?|days?|hours?|minutes?|seconds?|'
                  r'percent|psi|calories)\b', re.I)
STOP = set("and or of the a an if which so to that this is are was were being you your "
           "it its but as on at by for with from into we're i'm you're".split())
TURN = {'but', 'until', 'then', 'however', 'suddenly', 'because', 'except', 'instead',
        'yet', 'although', 'unless', 'before', 'after', 'once', 'so', 'now', 'meanwhile'}

# Measured asset mix (edit_grammar_ruleset.md §5), normalized to sum to 1.0:
# stock B-roll 40 / memes 25 / creature 20 / stat-cards 10  (of 95) -> shares below.
RATIOS = {'stock': 0.42, 'meme': 0.26, 'creature': 0.21, 'stat_card': 0.105}
MIN_CARD_SHOT = 1.2      # a stat card needs hold time; never on a sub-1.2s flash
MEME_RESET = 75.0        # comedic-reset cadence (measured: every 60-90s)


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


def _words_in(words, t0, t1):
    return [w for (t, w) in words if t0 <= t < t1]


def _card_text(words, t):
    """Extract the spoken stat near a cut as card copy: the number..unit span as
    the VALUE line, the meatier neighbor phrase as the CONTEXT line."""
    win = [(wt, w) for (wt, w) in words if t - 0.8 <= wt <= t + 1.8]
    idx = [i for i, (_, w) in enumerate(win) if NUM.search(w) or UNIT.search(w)]
    if not idx:
        return None
    i0, i1 = idx[0], idx[-1]
    if i1 - i0 > 5:                                  # cap runaway spans
        i1 = i0 + 5
    def clean(toks):
        toks = [re.sub(r"[^\w%$.'\-]", '', w) for w in toks]
        toks = [w for w in toks if w]
        while toks and toks[0].lower() in STOP:      # trim non-label edge words
            toks.pop(0)
        while toks and toks[-1].lower() in STOP:
            toks.pop()
        return ' '.join(toks).upper()

    value = clean([w for _, w in win[i0:i1 + 1]]) or \
        ' '.join(w for _, w in win[i0:i1 + 1]).upper()
    after = clean([w for _, w in win[i1 + 1:i1 + 6]])
    before = clean([w for _, w in win[max(0, i0 - 5):i0]])

    def content(s):
        return sum(1 for w in s.split() if len(w) > 2)
    context = after if content(after) >= content(before) else before
    if content(context) < 1:
        context = ''
    return {'value': value, 'context': context} if value else None


def assign_assets(cuts, words, dur, meme_cadence=MEME_RESET):
    """Per-shot asset type, quota-balanced to the MEASURED mix (RATIOS).
    Hard rules first, then a deterministic largest-deficit fill:
      - shot 0 (before the first cut) = hero creature: the video opens ON the creature
      - stat cut + shot long enough to hold -> stat_card (best stats first, capped at quota)
      - a meme reset every ~75s, preferring a 'turn' cut (tonal turn = comedic reset)
      - remaining shots: pick the asset type furthest under its quota (bursts thereby
        interleave stock/meme/creature flashes instead of being all-stock)
    """
    times = [0.0] + [c['t'] for c in cuts]
    whys = ['open'] + [c['why'] for c in cuts]
    shots = []
    for i, (t, why) in enumerate(zip(times, whys)):
        end = times[i + 1] if i + 1 < len(times) else max(dur, t)
        shots.append({'t': round(t, 2), 'end': round(end, 2),
                      'dur': round(end - t, 2), 'why': why,
                      'text': ' '.join(_words_in(words, t, end))[:160],
                      'asset': None, 'sfx_on_cut': i > 0})

    n = len(shots)
    quota = {a: r * n for a, r in RATIOS.items()}
    count = {a: 0 for a in RATIOS}

    def take(i, a):
        shots[i]['asset'] = a; count[a] += 1

    take(0, 'creature')

    # stat cards: qualifying stat shots, best-first (a unit beats a bare number)
    stat_idx = [i for i, s in enumerate(shots)
                if s['asset'] is None and 'stat' in s['why'] and s['dur'] >= MIN_CARD_SHOT]

    def card_score(i):
        s = shots[i]
        return ((1 if UNIT.search(s['text'] or '') else 0) +
                (1 if re.search(r'\d', s['text'] or '') else 0), s['dur'])

    for i in sorted(stat_idx, key=card_score, reverse=True)[:int(round(quota['stat_card']))]:
        card = _card_text(words, shots[i]['t'])
        if card:
            take(i, 'stat_card'); shots[i]['card'] = card

    # meme resets on cadence
    next_reset = meme_cadence
    for i, s in enumerate(shots):
        if s['t'] >= next_reset:
            free = [j for j in range(i, min(i + 6, n)) if shots[j]['asset'] is None]
            if free:
                j = next((j for j in free if 'turn' in shots[j]['why']), free[0])
                take(j, 'meme'); shots[j]['meme_reset'] = True
            next_reset = s['t'] + meme_cadence

    # proportional fill: pick the type with the most RELATIVE capacity left, so
    # stock/meme/creature interleave (incl. inside bursts) instead of long runs
    for i, s in enumerate(shots):
        if s['asset'] is not None:
            continue
        for a in sorted(RATIOS, key=lambda a: (quota[a] - count[a]) / quota[a],
                        reverse=True):
            if a == 'stat_card':
                continue
            if (a == 'creature' and i and shots[i - 1]['asset'] == 'creature'
                    and quota['creature'] - count['creature'] < 2):
                continue                              # space hero shots out a touch
            take(i, a); break

    mix = {a: round(100 * c / n, 1) for a, c in count.items()}
    return shots, mix


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
    ap.add_argument('--meme-cadence', type=float, default=MEME_RESET)
    a = ap.parse_args()

    words = parse_words(a.vtt)
    dur = words[-1][0] if words else 0
    cands = tag_candidates(words)
    cuts = select_cuts(cands, a.hook_end, a.hook_dur, a.body_dur, a.burst_win, a.burst_min)
    shots, mix = assign_assets(cuts, words, dur, a.meme_cadence)

    print(f"words={len(words)}  candidates={len(cands)}  -> cuts={len(cuts)}  shots={len(shots)}")
    target = {a: round(100 * r, 1) for a, r in RATIOS.items()}
    print(f"  asset mix %: {mix}")
    print(f"  target    %: {target}")
    cards = [s for s in shots if s['asset'] == 'stat_card']
    print(f"  stat cards: {len(cards)}  e.g. " +
          ' | '.join(f"[{c['card']['value']}]" for c in cards[:5]))
    if a.grammar:
        print('  VALIDATION vs real:', json.dumps(validate(cuts, a.grammar)))
    if a.out:
        Path(a.out).write_text(json.dumps(
            {'shots': shots, 'cuts': cuts, 'mix': mix, 'params': vars(a)}, indent=1))
        print('  wrote', a.out)


if __name__ == '__main__':
    main()
