#!/usr/bin/env python3
"""
beat_director.py — runs research/edit_decision_rulebook.md. Given a VO line it
classifies the fact and returns the shot recipe the owner would choose: device,
angle, comparison object, motion, graphic, SFX, kinetic text, attribution.

  from beat_director import direct
  direct("you weigh as much as a full city bus")
  -> {device:'scale', compare:'city bus', text:'9 TONS', cut:True, ...}

CLI: venv/bin/python scripts/beat_director.py            # demo on the CH1 script
"""
import re

# ordered: most specific first. each rule: (concept, test(line)->bool|match, recipe)
NUM = r'(\d[\d,]*)'


def _compare(l):
    m = re.search(r'(?:as much as|the size of|big as|like) an?\s+([a-z][a-z ]+?)(?:[,.]| that| packed|$)', l)
    return m.group(1).strip() if m else None


def _val(l, unit_words):
    m = re.search(NUM + r'\s*(?:thousand\s*)?(?:' + '|'.join(unit_words) + r')', l)
    return m.group(0).upper() if m else None


RULES = [
    ('height',  lambda l: re.search(r'\b(feet|foot|ft)\b.*\b(tall|hip)\b|\btall\b', l),
     lambda l: dict(device='measuring_tape', axis='vertical', angle='front',
                    text=_val(l, ['feet', 'foot', 'ft']) or 'TALL', motion='stomp')),
    ('length',  lambda l: re.search(r'\b(long|nose to tail)\b', l),
     lambda l: dict(device='measuring_tape', axis='horizontal', angle='side',
                    text=_val(l, ['feet', 'foot', 'ft']) or 'LONG', motion='pivot')),
    ('weight',  lambda l: re.search(r'\b(tons?|weigh)\b', l),
     lambda l: dict(device='scale', compare=_compare(l) or 'object', cut=True,
                    text=_val(l, ['tons', 'ton']) or 'WEIGHT', motion='cut')),
    ('force',   lambda l: re.search(r'\bforce\b|pounds of force|\bcrush\b|\bbite down\b|psi', l),
     lambda l: dict(device='gauge_max', demo=_compare(l) or 'car door',
                    text=_val(l, ['pounds', 'lbs', 'psi']) or 'BITE FORCE', motion='slam')),
    ('speed',   lambda l: re.search(r'miles an hour|\bmph\b|\bsprint\b|how fast', l),
     lambda l: dict(device='speedometer', text=_val(l, ['miles']) or 'SPEED', motion='loom')),
    ('count',   lambda l: re.search(NUM + r'\s+(teeth|inches|inch)', l),
     lambda l: dict(device='count_macro', text=_val(l, ['teeth', 'inches', 'inch']),
                    angle='macro', motion='ratchet')),
    ('smell',   lambda l: re.search(r'\bsmell\b|\bscent\b|\bnose\b', l),
     lambda l: dict(device='range_map', text='SCENT: >1 MILE', angle='nostril_macro',
                    motion='push', attribution=True)),
    ('sight',   lambda l: re.search(r'\beyes\b|resolve detail|pick (one|out)|six blocks', l),
     lambda l: dict(device='reticle', text='13× HUMAN ACUITY', angle='pov',
                    motion='push', attribution=True)),
    ('bodypart', lambda l: re.search(r'\b(arms?|legs?|skull|muscle|jaws?|claws?|tail)\b', l),
     lambda l: dict(device='macro', part=re.search(r'\b(arms?|legs?|skull|muscle|jaws?|claws?|tail)\b', l).group(1),
                    angle='on_part', motion='composite')),
    ('action',  lambda l: re.search(r'\b(stomp|bite|catch|caught|hunt|herd|swim|step|lunge|kill|tear|grab)\b', l),
     lambda l: dict(device='action_composite', verb=re.search(r'\b(stomp|bite|catch|caught|hunt|herd|swim|step|lunge|kill|tear|grab)\b', l).group(1),
                    motion='lunge', sfx='impact')),
    ('threat',  lambda l: re.search(r'\b(police|helicopter|rifle|armored|swat|river|hudson|gun|siren)\b', l),
     lambda l: dict(device='threat_footage', motion='composite', sfx='riser')),
    ('time',    lambda l: re.search(r'\bday one\b|\bhour\b|\bminutes?\b|\bseconds?\b', l),
     lambda l: dict(device='clock', motion='flip')),
    ('comparison', lambda l: re.search(r'the size of|like an?', l),
     lambda l: dict(device='compare_object', compare=_compare(l) or 'object', motion='cut')),
    ('danger',  lambda l: re.search(r'cannot fall|fatal|dying|death|shatter|kill you', l),
     lambda l: dict(device='consequence', text='A FALL AT SPEED = FATAL', color='yellow',
                    attribution=True, motion='stumble', sfx='impact')),
]
DEFAULT = lambda l: dict(device='loom', motion='loom', note='presence shot — abstract/transition')

UNIVERSAL = "creature alive · word-anchored pop · SFX on every event · orange/yellow ink-outline text no banner"


def direct(vo):
    l = vo.lower()
    for concept, test, recipe in RULES:
        if test(l):
            r = recipe(l); r['concept'] = concept
            r.setdefault('attribution', concept in ('danger', 'smell', 'sight'))
            r['confidence'] = 'high'
            return r
    r = DEFAULT(l); r['concept'] = 'abstract'; r['confidence'] = 'LOW — owner check'
    return r


if __name__ == '__main__':
    import json, sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[1]
    pe = json.load(open(ROOT / 'storyboards/trex_pilot_paper_edit_v3_mark.json'))
    # merge consecutive beats into sentence-ish lines for cleaner classification
    lines, cur = [], ''
    for b in pe['beats']:
        if not (24 <= pe['beats'].index(b) <= 66):
            pass
    print(f"{'VO line':52s} -> DEVICE (angle) · text · compare")
    print('-' * 110)
    seen = set()
    for i, b in enumerate(pe['beats']):
        if not (24 <= i <= 67):
            continue
        vo = b.get('text', '').strip()
        if not vo or vo in seen:
            continue
        seen.add(vo)
        r = direct(vo)
        extra = []
        if r.get('text'): extra.append(r['text'])
        if r.get('compare'): extra.append('= ' + r['compare'])
        if r.get('part'): extra.append(r['part'])
        if r.get('demo'): extra.append('crush ' + r['demo'])
        flag = '  ⚠' if 'LOW' in r['confidence'] else ''
        print(f"{vo[:50]:52s} -> {r['device']:16s} ({r.get('angle', r['motion'])}) {' · '.join(extra)}{flag}")
