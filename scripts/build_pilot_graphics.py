#!/usr/bin/env python3
"""
build_pilot_graphics.py — render every `graphic`-lane slot from
storyboards/trex_pilot_asset_plan.json into assets/trex_pilot/graphics/ and
point the paper edit's beats at them (plus the capped `existing` 2nd-use
swaps). The winner's graphics system: text cards + maps + gauges + clocks +
diagrams, all on the orange brand canvas.

Usage: venv/bin/python scripts/build_pilot_graphics.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from rexcaped_stat_cards import (render_card_orange, render_map_card,
                                 render_gauge_card, render_clock_card,
                                 render_senses_x_card, render_stride_card,
                                 render_scale_chart_card)

OUT = ROOT / 'assets/trex_pilot/graphics'
OUT.mkdir(parents=True, exist_ok=True)

# slug -> (renderer, args)  — text cards use render_card_orange(value, context)
GRAPHICS = {
    'g_ground_warn':  ('card', 'THE GROUND', 'REMEMBER IT.'),
    'g_scale_bus':    ('scale',),
    'g_stride_arc':   ('stride',),
    'g_meat_meter':   ('card', '500 LBS', 'OF MEAT. EVERY FEW DAYS.'),
    'g_smell_map':    ('map', 'ring', 'YOU SMELL BLOOD FROM 1 MILE'),
    'g_speedo':       ('gauge', '12', 'MPH', 'TOP SPEED', 12 / 70),
    'g_day_one':      ('clock', 'DAY ONE.', 'THE FIRST MORNING', 'calendar'),
    'g_hunt_4s':      ('card', '4 SECONDS', 'THE ENTIRE HUNT'),
    'g_clock_10s':    ('clock', '00:10', 'THE OLD RULES HOLD', 'countdown'),
    'g_track_map':    ('map', 'track', 'THE WHOLE ISLAND KNOWS'),
    'g_senses_x':     ('senses',),
    'g_herd_map':     ('map', 'herd', 'THEY HERD YOU'),
    'g_hudson_map':   ('map', 'span', 'THE HUDSON'),
    'g_temp_gauge':   ('gauge', '4', '°C', 'WATER TEMP', 4 / 30, True),
    'g_rule_fall':    ('card', 'YOU CANNOT FALL.', None),
    'g_zero_falls':   ('card', 'FALLS ALLOWED: 0', None),
    'g_yes':          ('card', 'YES.', None),
    'g_catch':        ('card', 'THE CATCH —', 'IT IS A BRUTAL ONE'),
    'g_vote':         ('card', 'NEXT PREDATOR?', 'YOU PICK. TOP COMMENT WINS.'),
    'g_top_comment':  ('card', 'TOP COMMENT', 'WINS.'),
    'g_subscribe':    ('card', 'LIKE + SUBSCRIBE', "LET'S FIND OUT HOW LONG THE KING LASTS"),
}


def render(slug):
    spec = GRAPHICS[slug]
    out = OUT / f'{slug}.png'
    kind = spec[0]
    if kind == 'card':
        render_card_orange(spec[1], spec[2], out)
    elif kind == 'map':
        render_map_card(spec[1], spec[2], out)
    elif kind == 'gauge':
        render_gauge_card(spec[1], spec[2], spec[3], spec[4], out,
                          falling=(len(spec) > 5 and spec[5]))
    elif kind == 'clock':
        render_clock_card(spec[1], spec[2], out, kind=spec[3])
    elif kind == 'senses':
        render_senses_x_card(out)
    elif kind == 'stride':
        render_stride_card(out)
    elif kind == 'scale':
        render_scale_chart_card(out)
    return out


def main():
    plan = json.load(open(ROOT / 'storyboards/trex_pilot_asset_plan.json'))
    pe_path = ROOT / 'storyboards/trex_pilot_paper_edit_v3_mark.json'
    pe = json.load(open(pe_path))
    beats = pe['beats']

    n_g = n_e = 0
    for k, slot in plan.items():
        i = int(k)
        if slot['lane'] == 'graphic':
            out = render(slot['slug'])
            beats[i]['visual_file'] = str(out)
            beats[i]['visual_type'] = 'image'
            beats[i].setdefault('zoom_speed_pct_per_sec', 1.2)
            beats[i]['enter'] = 'slam'
            beats[i].setdefault('sfx', 'impact')
            n_g += 1
        elif slot['lane'] == 'existing':
            # capped 2nd-use swap: point at the named asset (renderer varies
            # the in-point per reuse automatically)
            name = slot['slug']
            for d in ('assets/trex_pilot/hook_stills/169', 'footage/trex_pilot',
                      'assets/trex_pilot/anim'):
                p = ROOT / d / name
                if p.exists():
                    beats[i]['visual_file'] = str(p)
                    beats[i]['visual_type'] = ('video' if p.suffix == '.mp4'
                                               else 'image')
                    n_e += 1
                    break

    json.dump(pe, open(pe_path, 'w'), indent=1)
    print(f'rendered {n_g} graphics, swapped {n_e} existing-use slots; PE updated')


if __name__ == '__main__':
    main()
