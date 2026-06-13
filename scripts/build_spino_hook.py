#!/usr/bin/env python3
"""build_spino_hook.py — Spinosaurus/Lagos HOOK, the "what you are" section
(0-32.5s of the Mark VO). Each beat is a composite_beat config (cut-out creature
on a motion layer over a Lagos plate + word-anchored device/text/SFX + baked VO
span). Renders each beat then concatenates → output/spino_hook_partA_540p.mp4.

Beats:
  b01 reveal      "the largest predator that ever hunted"  hero loom
  b02 50 FT       "Fifty feet from snout to tail"          horizontal tape
  b03 vs T-Rex    "longer than the Tyrannosaurus"          text pop
  b04 vs bus      "longer than a city bus..."              text pop
  b05 7 TONS      "Seven tons of muscle"                   gauge
  b06 SAIL 6 FT   "a sail of bone as tall as a grown man"  vertical tape
  b07 jaws        "jaws... built to grip"                  jaws macro (breathes)
  b08 60 TEETH    "dozens of... cone-shaped teeth"         count device
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from composite_beat import render_beat, ROOT

ALIGN = str(ROOT / 'audio/spino_lagos/narration_11l_mark_whisperx.json')
VO = str(ROOT / 'audio/spino_lagos/narration_11l_mark_full.wav')
LAGOON = str(ROOT / 'assets/spino_lagos/hook_stills/s_lagos_lagoon_wide.png')
HERO = str(ROOT / 'assets/spino_lagos/cutouts/c_spino_hero_cut.png')
JAWS_PLATE = str(ROOT / 'assets/spino_lagos/hook_stills/c_spino_jaws_macro.png')
JAWS = str(ROOT / 'assets/spino_lagos/cutouts/c_spino_jaws_macro_cut.png')


def beat(t0, t1, **kw):
    return dict(window=(t0, t1), align=ALIGN, vo_span=(VO, t0, t1), fog=False, **kw)


BEATS = [
    ('b01_reveal', beat(0.0, 3.9, bg_still=LAGOON, cutout=HERO, motion='loom',
        camera='push', sway=.25)),
    ('b02_50ft', beat(3.9, 6.6, bg_still=LAGOON, cutout=HERO, motion='loom',
        camera='push', sway=.2, graphic='measuring_tape', tape_axis='horizontal',
        device_label='50 FT', impact='Fifty',
        sfx=[{'name': 'whoosh_03_loud.wav', 'word': 'Fifty', 'dt': -.2, 'vol': .4},
             {'name': 'impact_02_loud.wav', 'word': 'Fifty', 'vol': .5}])),
    ('b03_trex', beat(6.6, 9.7, bg_still=LAGOON, cutout=HERO, motion='loom',
        camera='push', sway=.2, impact='Tyrannosaurus',
        text=[{'msg': 'LONGER THAN A T-REX', 'word': 'Tyrannosaurus', 'hold': 2.2, 'y': .30}],
        sfx=[{'name': 'whoosh_05_loud.wav', 'word': 'Tyrannosaurus', 'dt': -.2, 'vol': .35},
             {'name': 'impact_02_loud.wav', 'word': 'Tyrannosaurus', 'vol': .45}])),
    ('b04_bus', beat(9.7, 12.9, bg_still=LAGOON, cutout=HERO, motion='loom',
        camera='push', sway=.2, impact='bus',
        text=[{'msg': '+ A CITY BUS', 'word': 'bus', 'hold': 2.0, 'y': .30}],
        sfx=[{'name': 'impact_02_loud.wav', 'word': 'bus', 'vol': .45}])),
    ('b05_7tons', beat(12.9, 17.2, bg_still=LAGOON, cutout=HERO, motion='loom',
        camera='push', sway=.2, graphic='gauge', device_label='7 TONS', impact='Seven',
        sfx=[{'name': 'whoosh_03_loud.wav', 'word': 'Seven', 'dt': -.2, 'vol': .4},
             {'name': 'body_impact_01_loud.wav', 'word': 'Seven', 'vol': .5}])),
    ('b06_sail', beat(17.2, 20.0, bg_still=LAGOON, cutout=HERO, motion='loom',
        camera='push', sway=.2, graphic='measuring_tape', tape_axis='vertical',
        device_label='SAIL 6 FT', impact='tall',
        sfx=[{'name': 'whoosh_05_loud.wav', 'word': 'tall', 'dt': -.2, 'vol': .4},
             {'name': 'impact_02_loud.wav', 'word': 'tall', 'vol': .45}])),
    ('b07_jaws', beat(20.0, 26.0, bg_still=JAWS_PLATE, cutout=JAWS, motion='macro_drift',
        camera='push', tune={'s': 1.06, 'cx': .5, 'cy': .5}, impact='crush',
        text=[{'msg': 'BUILT TO GRIP', 'word': 'grip', 'hold': 2.0, 'y': .80}],
        sfx=[{'name': 'impact_new_loud.wav', 'word': 'crush', 'vol': .45}])),
    ('b08_teeth', beat(26.0, 32.5, bg_still=JAWS_PLATE, cutout=JAWS, motion='macro_drift',
        camera='push', tune={'s': 1.10, 'cx': .5, 'cy': .5}, graphic='count',
        device_label='60 TEETH', impact='teeth',
        sfx=[{'name': 'whoosh_03_loud.wav', 'word': 'teeth', 'dt': -.2, 'vol': .35},
             {'name': 'impact_02_loud.wav', 'word': 'teeth', 'vol': .45}])),
]

BEATDIR = Path('/tmp/spino_beats')
BEATDIR.mkdir(exist_ok=True)


def main():
    clips = []
    for name, cfg in BEATS:
        out = BEATDIR / f'{name}.mp4'
        print(f'--- {name} {cfg["window"]} ---')
        render_beat(cfg, str(out))
        clips.append(out)
    listf = BEATDIR / 'concat.txt'
    listf.write_text(''.join(f"file '{c}'\n" for c in clips))
    final = ROOT / 'output/spino_hook_partA_540p.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(listf), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                    '-c:a', 'aac', str(final)], check=True)
    print('\nwrote', final)


if __name__ == '__main__':
    main()
