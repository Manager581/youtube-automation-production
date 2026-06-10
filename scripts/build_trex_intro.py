#!/usr/bin/env python3
"""
build_trex_intro.py — hand-authored 60s Rexcaped INTRO paper edit.

Not the auto-engine: this is a tight, fully-finished cut where EVERY beat is real
footage (good T-Rex hero clips + clean NYC b-roll) or a brief branded stat-card
flash. No placeholder slates, no memes, no long black holds. Every video beat is
< the 4.04s clip length, so nothing freeze-tails. Cuts land on the narration.

Pool:
  good creature clips (the long-necked t2v rejects are NOT used) + NYC b-roll
  (originally generated via LTX — zero stock libraries) + intro_cards/*.png.

Usage:
  venv.nosync/bin/python scripts/build_trex_intro.py \
    --out storyboards/trex_intro_paper_edit.json
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'footage' / 'trex_pilot'
C = ROOT / 'assets' / 'trex_pilot' / 'intro_cards'

# Intro stat cards (value, context) — kept here so the whole intro is reproducible
# from this one script. Brief on-screen (see SHEET); punchy, never long black holds.
CARDS = {
    'card_40ft':    ('40 FEET', 'NOSE TO TAIL'),
    'card_9tons':   ('9 TONS', 'WEIGHS AS MUCH AS A CITY BUS'),
    'card_60teeth': ('60 TEETH', 'UP TO 12 INCHES LONG'),
    'card_bite':    ('12,800 LBS', 'BITE FORCE'),
    'card_500':     ('500 LBS', 'TORN OFF IN ONE BITE'),
    'card_cold':    ('4°C', 'MANHATTAN, FEBRUARY'),
}


def render_cards():
    sys.path.insert(0, str(ROOT / 'scripts'))
    from rexcaped_stat_cards import render_card
    C.mkdir(parents=True, exist_ok=True)
    for name, (v, ctx) in CARDS.items():
        render_card(v, ctx, C / f'{name}.png')
    print(f"rendered {len(CARDS)} intro cards -> {C}")

CLIP = {
    # GOOD T-Rex (correct anatomy)
    'jaws':  F / 'dunk_trex_jaws_teeth.mp4',
    'eye':   F / 'dunk_trex_eye_detail.mp4',
    'taxi':  F / 'dunk_trex_taxi_hunt.mp4',
    'heli':  F / 'dunk_trex_helicopters_night.mp4',
    'pier':  F / 'dunk_trex_pier_river.mp4',
    # clean NYC b-roll (no creature -> no anatomy risk)
    'sky':    F / 'dunk_nyc_skyline_dawn.mp4',
    'street': F / 'dunk_nyc_snow_street.mp4',
    'ave':    F / 'dunk_nyc_avenue_taxis.mp4',
    'snow':   F / 'dunk_nyc_snow_macro.mp4',
    'asph':   F / 'dunk_nyc_wet_asphalt.mp4',
    # cards
    'c_40ft':   C / 'card_40ft.png',
    'c_9tons':  C / 'card_9tons.png',
    'c_60teeth':C / 'card_60teeth.png',
    'c_bite':   C / 'card_bite.png',
    'c_500':    C / 'card_500.png',
    'c_cold':   C / 'card_cold.png',
}

# (end_sec, clip_key, sfx, note) — start = previous end. Cards are c_*.
SHEET = [
    (3.10,  'jaws',   'impact',  'open on the jaws'),
    (5.89,  'eye',    'whoosh',  'a perfect killing machine'),
    (6.80,  'c_40ft', 'impact',  'Forty feet long'),
    (7.70,  'c_9tons','impact',  'Nine tons'),
    (10.60, 'jaws',   'whoosh',  'skull the size of a bathtub'),
    (11.90, 'c_60teeth','impact','sixty teeth'),
    (13.60, 'eye',    'whoosh',  'twelve inches long'),
    (16.34, 'jaws',   'impact',  'serrated like steak knives'),
    (18.50, 'heli',   'whoosh',  'you can bite down'),
    (20.00, 'c_bite', 'impact',  '12,800 lbs of force'),
    (22.10, 'taxi',   'impact',  'crush a car door'),
    (23.60, 'jaws',   'impact',  'splinter solid bone'),
    (25.20, 'heli',   'whoosh',  'and tear off'),
    (26.70, 'c_500',  'impact',  '500 lbs of meat'),
    (29.31, 'jaws',   'impact',  'in a single pull'),
    (31.50, 'eye',    'whoosh',  'a tooth snaps off'),
    (33.93, 'jaws',   'impact',  'grow another'),
    (37.63, 'heli',   'impact',  'nothing walked away from you'),
    (39.77, 'pier',   'whoosh',  'but your world is gone'),
    (42.24, 'sky',    'whoosh',  'today you wake up here'),
    (45.50, 'street', 'whoosh',  'middle of Manhattan'),
    (48.00, 'ave',    'whoosh',  'in February'),
    (50.26, 'c_cold', 'impact',  '4 degrees above freezing'),
    (53.44, 'snow',   'whoosh',  'the first thing you feel is the cold'),
    (56.40, 'asph',   'impact',  'the ground'),
    (58.50, 'street', 'whoosh',  'flat, gray'),
    (60.78, 'pier',   'impact',  'harder than any stone'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--chapter', default='REXCAPED')
    ap.add_argument('--render-cards', action='store_true',
                    help='render the 6 intro stat cards before building')
    a = ap.parse_args()

    if a.render_cards:
        render_cards()

    beats, missing, start = [], [], 0.0
    for i, (end, key, sfx, note) in enumerate(SHEET):
        path = CLIP[key]
        is_card = key.startswith('c_')
        if not path.exists():
            missing.append((key, str(path)))
        beat = {
            'beat_id': f'beat_{i:04d}',
            'start_sec': round(start, 3),
            'end_sec': round(end, 3),
            'duration': round(end - start, 3),
            'visual_file': str(path),
            'visual_type': 'still' if is_card else 'video',
            'clip_audio': 'mute',
            'tension_level': 0.7,
            'zoom_speed_pct_per_sec': 0.0,           # cards static (crisp text); clips already move
            'chapter': a.chapter,
            'sfx': sfx,
            'text': note,
            'asset': 'stat_card' if is_card else 'creature',
        }
        beats.append(beat)
        start = end

    out = {
        'beats': beats,
        'stats': {
            'beat_count': len(beats),
            'total_duration_sec': beats[-1]['end_sec'],
            'cards': sum(1 for b in beats if b['asset'] == 'stat_card'),
            'clips': sum(1 for b in beats if b['asset'] == 'creature'),
            'max_video_beat': round(max((b['duration'] for b in beats
                                         if b['visual_type'] == 'video')), 2),
        },
        '_version': 'trex_intro_handcut_v1',
    }
    Path(a.out).write_text(json.dumps(out, indent=1))
    s = out['stats']
    print(f"wrote {a.out}: {s['beat_count']} beats, {s['total_duration_sec']}s, "
          f"{s['clips']} clip-cuts + {s['cards']} card-flashes, "
          f"max video beat {s['max_video_beat']}s (clip len 4.04s -> no freeze)")
    if missing:
        print(f"  ⚠ MISSING {len(missing)} (b-roll still generating?):")
        for k, p in missing:
            print(f"    {k}: {p}")


if __name__ == '__main__':
    main()
