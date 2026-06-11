#!/usr/bin/env python3
"""
build_ch1_auto.py — THE CLOSED LOOP. The owner's creative decisions are no longer
a manual wiring step: this runs beat_director over CH1, turns each recipe into a
renderable config deterministically (recipe_to_config), builds every beat, and
assembles the chapter. Change the script -> the director re-decides -> the chapter
rebuilds itself. No human in the creative loop.

  venv/bin/python scripts/build_ch1_auto.py            # full director-driven CH1
  venv/bin/python scripts/build_ch1_auto.py --plan     # just print the decision plan
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from beat_director import direct
from composite_beat import render_beat, ROOT, ALIGN, VO_MARK, norm_word

PE_V3 = ROOT / 'storyboards/trex_pilot_paper_edit_v3_mark.json'
CLIPS = ROOT / 'output/auto_beats'; CLIPS.mkdir(parents=True, exist_ok=True)
WORDS = [w for w in json.load(open(ALIGN))['words'] if w.get('start') is not None]
AV = str(ROOT / 'footage/trex_pilot/dunk_nyc_avenue_taxis.mp4')
SNOW = str(ROOT / 'footage/trex_pilot/dunk_nyc_snow_street.mp4')
CUT = ROOT / 'assets/trex_pilot/cutouts'

WET = str(ROOT / 'footage/trex_pilot/dunk_nyc_wet_asphalt.mp4')
TAXIW = str(ROOT / 'footage/trex_pilot/stock/s_taxi_wall.mp4')
# angle -> (cutout, background). default/loom ROTATE through pools for variety so
# consecutive creature beats never read as the same shot (the recurring problem).
ANGLE_ASSET = {
    'front': (CUT / 'ch_trex_avenue_wide_cut.png', AV),
    'side':  (CUT / 'trex_side_cut.png', TAXIW),
    'pov':   (CUT / 'c_statue_still_cut.png', str(ROOT / 'footage/trex_pilot/stock/s_crowd_run.mp4')),
}
POOL_CUT = [CUT / 'c_statue_still_cut.png', CUT / 'ch_trex_avenue_wide_cut.png',
            CUT / 'ch_trex_walkaway_crowd_cut.png', CUT / 'trex_side_cut.png']
POOL_BG = [AV, SNOW if False else str(ROOT / 'footage/trex_pilot/dunk_nyc_snow_street.mp4'), TAXIW, WET]
# device -> renderer graphic
DEV_GRAPHIC = {'measuring_tape': 'measuring_tape', 'gauge_max': 'gauge',
               'speedometer': 'speedometer', 'count_macro': 'count', 'reticle': 'reticle'}


def anchor_word(vo, w0, w1):
    """pick a word in the window to anchor the device pop on: the number, else
    the device keyword, else the window midpoint."""
    import re
    m = re.search(r'\b(thirteen|forty|nine|twelve|sixty|fifteen|five|hundred|thousand|'
                  r'tons?|feet|force|miles|teeth|bus|fall\w*|smell|eyes|nose)\b', vo.lower())
    if m:
        tok = norm_word(m.group(1))
        for w in WORDS:                       # stem match: 'fall' ~ 'falling'
            ww = norm_word(w['word'])
            if w0 - .3 <= w['start'] <= w1 + .3 and (ww.startswith(tok[:4]) or tok.startswith(ww[:4])):
                return w['word']
    return None


def recipe_to_config(recipe, vo, w0, w1, idx=0):
    """DETERMINISTIC: a director recipe -> a composite_beat config. This is the
    'forced wiring' — no creative choice left to a human."""
    if recipe.get('angle') in ANGLE_ASSET:
        cut, bg = ANGLE_ASSET[recipe['angle']]
    else:                                    # rotate the pool so beats vary
        cut, bg = POOL_CUT[idx % len(POOL_CUT)], POOL_BG[idx % len(POOL_BG)]
    aw = anchor_word(vo, w0, w1)
    cfg = dict(window=(w0, w1), vo_span=(VO_MARK, w0, w1), align=ALIGN,
               cutout=cut, bg_video=bg, motion='loom', camera='push', sway=.6,
               impact=aw if aw else round((w1 - w0) * .5, 2),
               sfx=[dict(t=.1, name='rumble_02_loud.wav', vol=.45)])
    dev = recipe['device']
    if dev in DEV_GRAPHIC:
        cfg['graphic'] = DEV_GRAPHIC[dev]
        if dev == 'measuring_tape':
            cfg['tape_axis'] = recipe.get('axis', 'vertical')
        if recipe.get('text'):
            cfg['device_label'] = recipe['text']
        if dev == 'reticle':
            cfg.update(reticle_xy=(.5, .55), reticle_track=True, reticle_hold=True, reticle_in=.5,
                       text=[dict(word=aw or 'six', msg=recipe.get('text', ''), y=.26, size=88,
                                  sub='— paleontologists' if recipe.get('attribution') else None, hold=9)])
        else:
            cfg['sfx'].append(dict(t=cfg['impact'] if isinstance(cfg['impact'], (int, float)) else .8,
                                   name='body_impact_01_loud.wav', vol=.6) if False else
                              dict(word=aw, name='impact_01_loud.wav', vol=.6) if aw else
                              dict(t=1.0, name='impact_01_loud.wav', vol=.6))
    elif dev == 'consequence':                        # the fall = FATAL
        at = dict(word=aw) if aw else dict(t=round((w1 - w0) * .4, 2))
        cfg.update(cutout=CUT / 'c_trip_stumble_cut.png', bg_video=SNOW, motion='stumble',
                   camera='handheld', graphic='none', impact=aw or round((w1 - w0) * .4, 2),
                   text=[dict(**at, msg=recipe.get('text', 'A FALL AT SPEED = FATAL'),
                              y=.26, size=70, sub='— paleontologists', hold=9, color='yellow')],
                   sfx=[dict(**at, name='body_impact_01_loud.wav', vol=.9)])
    elif dev == 'range_map':                          # smell — nostril push + range card
        cfg.update(cutout=None, bg_still=str(ROOT / 'assets/trex_pilot/body_stills/c_nostril_smoke.png'),
                   motion=None, graphic='none',
                   text=[dict(word=aw or 'smell', msg='SCENT: >1 MILE', y=.30, size=92,
                              sub='— paleontologists', hold=9)])
    # else loom/macro/action/threat -> plain creature composite (defaults above)
    cfg = {k: v for k, v in cfg.items() if v is not None}
    return cfg


def segments():
    """merge CH1 beats into sentence-ish segments for clean classification."""
    bs = json.load(open(PE_V3))['beats']
    segs, cur, s0 = [], '', None
    for i, b in enumerate(bs):
        if not (24 <= i <= 66):
            continue
        if s0 is None:
            s0 = b['start_sec']
        cur += ' ' + b.get('text', '')
        if b.get('text', '').rstrip().endswith(('.', '?', '!')):
            segs.append((cur.strip(), s0, b['end_sec'])); cur, s0 = '', None
    if cur.strip() and s0 is not None:
        segs.append((cur.strip(), s0, bs[66]['end_sec']))
    return segs


def main():
    plan_only = '--plan' in sys.argv
    print(f"{'VO':46s} {'DEVICE':15s} ANGLE  TEXT")
    print('-' * 92)
    beats, built, failed = [], 0, []
    for idx, (vo, w0, w1) in enumerate(segments()):
        r = direct(vo)
        print(f"{vo[:44]:46s} {r['device']:15s} {str(r.get('angle','-')):6s} {r.get('text','')}")
        if plan_only:
            continue
        clip = CLIPS / f"{w0:07.2f}_{r['device']}.mp4"
        try:
            render_beat(recipe_to_config(r, vo, w0, w1, idx), clip)
            beats.append(dict(start_sec=w0, end_sec=w1, duration=round(w1 - w0, 3),
                              visual_file=str(clip), visual_type='video', clip_audio='mute',
                              text=vo, asset='auto', device=r['device']))
            built += 1
        except Exception as e:
            failed.append((r['device'], repr(e)[:70]))
    if plan_only:
        return
    print(f"\nbuilt {built} director-driven beats; failed {len(failed)}: {failed}")
    out = ROOT / 'storyboards/trex_pilot_ch1_auto.json'
    json.dump({'beats': beats, 'stats': {'director_driven': True, 'built': built, 'failed': len(failed)}},
              open(out, 'w'), indent=1)
    print('wrote', out)


if __name__ == '__main__':
    main()
