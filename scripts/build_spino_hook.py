#!/usr/bin/env python3
"""build_spino_hook.py — Spinosaurus/Lagos HOOK "what you are" section (0-32.5s).

FIX (owner feedback 2026-06-14): no more "same creature zooming + same SFX".
Each creature beat now plays a REAL LTX i2v motion clip (footage/spino_lagos/
dunk_*.mp4) as the background — the creature actually MOVES — with NO cutout and
camera='none' (no zoom). Beats rotate across distinct clips (hero / side / jaws),
each with a DIFFERENT SFX, devices/text overlaid + baked VO span. Renders each
beat via composite_beat then concatenates → output/spino_hook_partA_motion_540p.mp4.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from composite_beat import render_beat, ROOT

ALIGN = str(ROOT / 'audio/spino_lagos/narration_11l_mark_whisperx.json')
VO = str(ROOT / 'audio/spino_lagos/narration_11l_mark_full.wav')
CLIPS = {
    'hero': str(ROOT / 'footage/spino_lagos/dunk_c_spino_hero.mp4'),
    'side': str(ROOT / 'footage/spino_lagos/dunk_c_spino_side.mp4'),
    'jaws': str(ROOT / 'footage/spino_lagos/dunk_c_spino_jaws_macro.mp4'),
    'lunge': str(ROOT / 'footage/spino_lagos/dunk_c_spino_lunge.mp4'),
}


def beat(t0, t1, clip, bg_in=0.0, **kw):
    # bg_video = the moving creature clip; camera='none' => no zoom (motion is in the clip)
    return dict(window=(t0, t1), align=ALIGN, vo_span=(VO, t0, t1), fog=False,
                bg_video=CLIPS[clip], bg_in=bg_in, camera='none', **kw)


BEATS = [
    ('b01_reveal', beat(0.0, 3.9, 'hero')),
    ('b02_50ft', beat(3.9, 6.6, 'side', graphic='measuring_tape', tape_axis='horizontal',
        device_label='50 FT', impact='Fifty',
        sfx=[{'name': 'whoosh_01_loud.wav', 'word': 'Fifty', 'dt': -.2, 'vol': .4},
             {'name': 'impact_01_loud.wav', 'word': 'Fifty', 'vol': .5}])),
    ('b03_trex', beat(6.6, 9.7, 'hero', bg_in=1.0, impact='Tyrannosaurus',
        text=[{'msg': 'LONGER THAN A T-REX', 'word': 'Tyrannosaurus', 'hold': 2.2, 'y': .30}],
        sfx=[{'name': 'whoosh_02_loud.wav', 'word': 'Tyrannosaurus', 'dt': -.2, 'vol': .35},
             {'name': 'impact_02_loud.wav', 'word': 'Tyrannosaurus', 'vol': .45}])),
    ('b04_bus', beat(9.7, 12.9, 'side', bg_in=1.0, impact='bus',
        text=[{'msg': '+ A CITY BUS', 'word': 'bus', 'hold': 2.0, 'y': .30}],
        sfx=[{'name': 'whoosh_04_loud.wav', 'word': 'bus', 'dt': -.15, 'vol': .35},
             {'name': 'impact_new_loud.wav', 'word': 'bus', 'vol': .45}])),
    ('b05_7tons', beat(12.9, 17.2, 'hero', bg_in=0.4, graphic='gauge', device_label='7 TONS',
        impact='Seven',
        sfx=[{'name': 'whoosh_03_loud.wav', 'word': 'Seven', 'dt': -.2, 'vol': .4},
             {'name': 'body_impact_01_loud.wav', 'word': 'Seven', 'vol': .5}])),
    ('b06_sail', beat(17.2, 20.0, 'side', bg_in=0.5, graphic='measuring_tape', tape_axis='vertical',
        device_label='SAIL 6 FT', impact='tall',
        sfx=[{'name': 'whoosh_05_loud.wav', 'word': 'tall', 'dt': -.2, 'vol': .4},
             {'name': 'impact_01_loud.wav', 'word': 'tall', 'vol': .45}])),
    ('b07_jaws', beat(20.0, 26.0, 'jaws', impact='crush',
        text=[{'msg': 'BUILT TO GRIP', 'word': 'grip', 'hold': 2.0, 'y': .80}],
        sfx=[{'name': 'impact_new_loud.wav', 'word': 'crush', 'vol': .45},
             {'name': 'whoosh_02_loud.wav', 'word': 'grip', 'dt': -.1, 'vol': .3}])),
    ('b08_teeth', beat(26.0, 32.5, 'jaws', bg_in=1.4, graphic='count', device_label='60 TEETH',
        impact='teeth',
        sfx=[{'name': 'whoosh_03_loud.wav', 'word': 'teeth', 'dt': -.2, 'vol': .35},
             {'name': 'impact_02_loud.wav', 'word': 'teeth', 'vol': .45}])),
]

BEATDIR = Path('/tmp/spino_beats')
BEATDIR.mkdir(exist_ok=True)


def main():
    clips = []
    for name, cfg in BEATS:
        out = BEATDIR / f'{name}.mp4'
        print(f'--- {name} {cfg["window"]} clip={Path(cfg["bg_video"]).stem} ---')
        render_beat(cfg, str(out))
        clips.append(out)
    listf = BEATDIR / 'concat.txt'
    listf.write_text(''.join(f"file '{c}'\n" for c in clips))
    final = ROOT / 'output/spino_hook_partA_motion_540p.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(listf), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                    '-c:a', 'aac', str(final)], check=True)
    print('\nwrote', final)


if __name__ == '__main__':
    main()
