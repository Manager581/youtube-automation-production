#!/usr/bin/env python3
"""
build_ch1_composites.py — CH1 · THE BODY composite rollout
(research/trex_pilot_chapter_plan.md, beats 24-66).

Renders the chapter's composite beats via composite_beat.render_beat (beat
windows + Mark-VO spans injected from the canonical paper edit), splices the
clips in (beats 35+36 merge into one stumble shot), and writes:
  output/composite_beats/ch1_*.mp4                 the beat clips
  storyboards/trex_pilot_paper_edit_v4_ch1.json    full-timeline v4
  storyboards/trex_pilot_ch1_only.json             re-zeroed CH1 slice
  audio/trex_pilot/narration_11l_mark_ch1.wav      matching narration span

Then render the chapter:
  venv.nosync/bin/python scripts/ffmpeg_production_render.py \
    --paper-edit storyboards/trex_pilot_ch1_only.json \
    --narration audio/trex_pilot/narration_11l_mark_ch1.wav \
    --output output/trex_pilot_ch1_body_540p.mp4 --preview
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from composite_beat import ALIGN, CONFIGS, VO_MARK, norm_word, render_beat, ROOT

PE_V3 = ROOT / 'storyboards/trex_pilot_paper_edit_v3_mark.json'
PE_V4 = ROOT / 'storyboards/trex_pilot_paper_edit_v4_ch1.json'
PE_CH1 = ROOT / 'storyboards/trex_pilot_ch1_only.json'
WAV_CH1 = ROOT / 'audio/trex_pilot/narration_11l_mark_ch1.wav'
CLIPS = ROOT / 'output/composite_beats'
CH1_FIRST, CH1_LAST = 24, 66          # chapter plan: CH1 · THE BODY

# Composite splices: which v3 beats each clip replaces + the SFX events the
# production renderer lays (word-anchored offsets resolved below; events
# survive future realigns because the word rides along).
SPLICES = [
    # the owner-directed ILLUSTRATED body scene (tapes + side pivot + bus scale),
    # built once by scripts/build_body_reveal.py — spliced as-is, never re-rendered.
    # stomp SFX at the preset's falling zero-crossings (sin(t*4.2)); stats word-anchored.
    dict(clip='output/body_reveal_540p.mp4', beats=[26, 27, 28, 29, 30],
         events=[dict(t=.75, sfx='impact_01_loud.wav'), dict(t=2.24, sfx='impact_01_loud.wav'),
                 dict(t=3.74, sfx='impact_01_loud.wav'), dict(t=5.24, sfx='impact_01_loud.wav'),
                 dict(word='thirteen', dt=-.2, sfx='whoosh_03_loud.wav'),
                 dict(word='thirteen', sfx='impact_02_loud.wav'),
                 dict(word='forty', dt=-.5, sfx='whoosh_05_loud.wav'),
                 dict(word='forty', sfx='impact_02_loud.wav'),
                 dict(word='bus', dt=-.4, sfx='body_impact_01_loud.wav'),
                 dict(word='bus', sfx='impact_new_loud.wav')]),
    dict(cfg='ch1_legs', beats=[32],
         events=[dict(t=.1, sfx='rumble_03_loud.wav')]),
    dict(cfg='ch1_stumble', beats=[35, 36],
         events=[dict(word='slams', dt=-.7, sfx='whoosh_05_loud.wav'),
                 dict(word='slams', sfx='body_impact_01_loud.wav'),
                 dict(word='slams', sfx='impact_02_loud.wav'),
                 dict(word='slams', sfx='rumble_03_loud.wav')]),
    dict(cfg='ch1_furnace', beats=[43],
         events=[dict(t=.1, sfx='rumble_01_loud.wav')]),
    dict(cfg='ch1_nostril', beats=[54, 55],
         events=[dict(t=.15, sfx='rumble_02_loud.wav'),
                 dict(word='existed', sfx='impact_01_loud.wav')]),
    dict(cfg='ch1_povpick', beats=[61],
         events=[dict(t=.5, sfx='shimmer_01_loud.wav'),
                 dict(word='six', sfx='impact_01_loud.wav')]),
    dict(cfg='ch1_speed', beats=[62, 63],
         events=[dict(t=.1, sfx='rumble_02_loud.wav'),
                 dict(word='twelve', sfx='impact_01_loud.wav')]),
    dict(cfg='ch1_loom', beats=[65],
         events=[dict(t=.1, sfx='rumble_02_loud.wav')]),
]

# noun-fix retargets within the existing library (no renders): visual_file swaps
# that put the spoken noun on screen and cut the card count to the spec budget.
RETARGETS = [
    (31, 'footage/trex_pilot/dunk_trex_stride_avenue.mp4', 'video'),  # "a single stride" (was arc graphic)
    (37, 'assets/trex_pilot/body_stills/c_tiny_arms_macro.png', 'image'),  # "famously tiny arms" macro (i_arms art = duplicate of i_uhoh)
    (39, 'assets/trex_pilot/body_stills/i_uhoh.png', 'image'),        # "falling = dying" -> UH OH ink gag
    (49, 'footage/trex_pilot/dunk_trex_taxi_hunt.mp4', 'video'),      # "you have to hunt here"
    (52, 'assets/trex_pilot/body_stills/c_pov_crowd_up.png', 'image'),  # "four million strangers" staring up (world-consistent)
    (60, 'footage/trex_pilot/stock/s_phones_up.mp4', 'video'),        # "ten thousand people" sea of lights (crowd_mass = CNBC interview, unusable)
]

# creature PHOTO stills must never sit frozen (zoom 0 = the static-lazy read the
# owner rejected). Cards / ink gags (g_*, i_*, card_*) stay zoom-0 flash-holds by
# design — that's the winner's card grammar.
ZOOM_FIXES = [33, 37, 38, 47, 50, 52, 53]  # statue, arms-macro, trip_stumble, food_cart, glass_refl, crowd_up, hide


def main():
    pe = json.load(open(PE_V3))
    beats = pe['beats']
    words = [w for w in json.load(open(ALIGN))['words'] if w.get('start') is not None]
    CLIPS.mkdir(parents=True, exist_ok=True)

    def word_t(w0, w1, tok):
        tgt = norm_word(tok)
        for w in words:
            if w0 - .25 <= w['start'] < w1 + .35 and norm_word(w['word']) == tgt:
                return w['start'] - w0
        raise KeyError(f"{tok!r} not aligned in {w0}-{w1}")

    only = set(sys.argv[1:])                  # re-render just the named cfgs
    dropped = set()
    for sp in SPLICES:
        bs = [beats[i] for i in sp['beats']]
        w0, w1 = bs[0]['start_sec'], bs[-1]['end_sec']
        name = sp.get('cfg') or Path(sp['clip']).stem
        if sp.get('clip'):                    # pre-built scene (body reveal): splice as-is
            clip = ROOT / sp['clip']
            print(f"\n── {name} (pre-built)  beats {sp['beats']}  {w0:.2f}-{w1:.2f} ({w1 - w0:.2f}s)")
        else:
            cfg = dict(CONFIGS[sp['cfg']])
            cfg.update(window=(w0, w1), vo_span=(VO_MARK, w0, w1))
            clip = CLIPS / f"{sp['cfg']}.mp4"
            print(f"\n── {sp['cfg']}  beats {sp['beats']}  {w0:.2f}-{w1:.2f} ({w1 - w0:.2f}s)")
            if not only or sp['cfg'] in only or not clip.exists():
                render_beat(cfg, clip)

        b = bs[0]
        b['end_sec'] = w1
        b['duration'] = round(w1 - w0, 3)
        b['visual_file'] = str(clip.resolve())
        b['visual_type'] = 'video'
        b['asset'] = 'creature'
        b['text'] = ' '.join(x.get('text', '') for x in bs).strip()
        b['src_offset'] = 0
        b['clip_audio'] = 'mute'
        b['events'] = [
            {('word' if 'word' in ev else 't'): ev.get('word', ev.get('t')),
             't': round((word_t(w0, w1, ev['word']) + ev.get('dt', 0.0))
                        if 'word' in ev else ev['t'], 3),
             'sfx': ev['sfx']}
            for ev in sp['events']]
        dropped.update(sp['beats'][1:])

    for i, path, vt in RETARGETS:
        b = beats[i]
        b['visual_file'] = str((ROOT / path).resolve())
        b['visual_type'] = vt
        if vt == 'video':
            b['clip_audio'] = 'mute'
            b['src_offset'] = 0
        print(f"retarget beat {i:3d} -> {Path(path).name}")
    for i in ZOOM_FIXES:
        beats[i]['zoom_speed_pct_per_sec'] = 3.0

    pe['beats'] = [b for i, b in enumerate(beats) if i not in dropped]
    pe.setdefault('stats', {})['ch1_composites'] = [sp.get('cfg') or Path(sp['clip']).stem for sp in SPLICES]
    json.dump(pe, open(PE_V4, 'w'), indent=2)
    print(f"\nwrote {PE_V4} ({len(pe['beats'])} beats, {len(dropped)} merged away)")

    # CH1-only slice, re-zeroed to the chapter head (events are beat-relative
    # already; narration span extracted to match exactly)
    t0 = beats[CH1_FIRST]['start_sec']
    t1 = beats[CH1_LAST]['end_sec']
    sl = [dict(b) for b in pe['beats'] if b['start_sec'] >= t0 - 1e-6 and b['end_sec'] <= t1 + 1e-6]
    for b in sl:
        b['start_sec'] = round(b['start_sec'] - t0, 3)
        b['end_sec'] = round(b['end_sec'] - t0, 3)
    ch1 = {'_version': pe.get('_version', 1),
           'beats': sl,
           'stats': {'sliced_from': str(PE_V4), 'span': [t0, t1]}}
    json.dump(ch1, open(PE_CH1, 'w'), indent=2)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(VO_MARK),
                    '-ss', f'{t0:.3f}', '-to', f'{t1:.3f}', str(WAV_CH1)], check=True)
    print(f"wrote {PE_CH1} ({len(sl)} beats, {t1 - t0:.2f}s) + {WAV_CH1}")


if __name__ == '__main__':
    main()
