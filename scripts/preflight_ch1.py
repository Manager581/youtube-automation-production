#!/usr/bin/env python3
"""
preflight_ch1.py — RUN THIS FIRST in the next session. Verifies the entire
foundation built 2026-06-11 is intact and FUNCTIONAL before any new building, so
the next session builds ON it instead of rebuilding or breaking it. Exits non-
zero if anything is red. Triple-checks: files exist, AND key tools actually run
and produce the right output.

  venv/bin/python scripts/preflight_ch1.py
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ok, bad = [], []


def chk(label, cond, detail=''):
    (ok if cond else bad).append((label, detail))
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail and not cond else ''))


def exists(p, minbytes=1):
    f = ROOT / p
    return f.exists() and f.stat().st_size >= minbytes


print("── 1. FILES (the system) ──")
for p in ['scripts/beat_director.py', 'scripts/composite_beat.py',
          'scripts/build_body_reveal.py', 'scripts/build_ch1_composites.py',
          'research/edit_decision_rulebook.md', 'storyboards/spec_ch1.json',
          'storyboards/trex_pilot_paper_edit_v3_mark.json']:
    chk(p, exists(p), 'MISSING')

print("── 2. ASSETS (cutouts / audio / alignment) ──")
for p in ['assets/trex_pilot/cutouts/trex_side_cut.png',
          'assets/trex_pilot/cutouts/city_bus_cut.png',
          'assets/trex_pilot/cutouts/ch_trex_avenue_wide_cut.png',
          'assets/trex_pilot/cutouts/c_statue_still_cut.png',
          'audio/trex_pilot/narration_11l_mark_full.wav',
          'audio/trex_pilot/narration_11l_mark_whisperx.json']:
    chk(p, exists(p, 1000), 'MISSING')

print("── 3. PROVEN OUTPUTS (watchable, owner-seen) ──")
for p in ['output/body_reveal_540p.mp4', 'output/proto_strike_540p.mp4']:
    chk(p, exists(p, 100000), 'MISSING/empty')

print("── 4. beat_director ACTUALLY RUNS + reproduces owner calls ──")
try:
    spec = importlib.util.spec_from_file_location('bd', ROOT / 'scripts/beat_director.py')
    bd = importlib.util.module_from_spec(spec); spec.loader.exec_module(bd)
    cases = [('thirteen feet tall at the hip', 'measuring_tape', 'vertical'),
             ('forty feet from nose to tail', 'measuring_tape', 'horizontal'),
             ('you weigh as much as a full city bus', 'scale', None),
             ('your eyes resolve detail, pick one running figure', 'reticle', None),
             ('your nose can smell blood', 'range_map', None),
             ('you cannot fall, falling is the same as dying', 'consequence', None),
             ('twelve miles an hour', 'speedometer', None)]
    for vo, dev, axis in cases:
        r = bd.direct(vo)
        good = r['device'] == dev and (axis is None or r.get('axis') == axis)
        chk(f"direct({vo[:34]!r}) -> {dev}", good, f"got {r['device']}/{r.get('axis')}")
except Exception as e:
    chk('beat_director import/run', False, repr(e)[:80])

print("── 5. composite_beat imports + CH1 configs present ──")
try:
    spec = importlib.util.spec_from_file_location('cb', ROOT / 'scripts/composite_beat.py')
    cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
    need = {'ch1_body', 'ch1_legs', 'ch1_furnace', 'ch1_stumble', 'ch1_nostril',
            'ch1_povpick', 'ch1_loom', 'strike'}
    have = set(cb.CONFIGS)
    chk('composite_beat.CONFIGS has all CH1 configs', need <= have, f"missing {need - have}")
except Exception as e:
    chk('composite_beat import', False, repr(e)[:80])

print("── 6. DEVICE LIBRARY status (what's built vs TO BUILD next) ──")
brv = (ROOT / 'scripts/build_body_reveal.py').read_text()
chk('measuring_tape (vtape/htape) BUILT', 'def vtape' in brv and 'def htape' in brv)
chk('scale comparison BUILT', 'PHASE C' in brv or '9 TONS' in brv)
for dev in ['gauge_max', 'speedometer', 'count_macro']:
    built = dev in brv or dev in (ROOT / 'scripts/composite_beat.py').read_text()
    print(f"  {'✅ built' if built else '🔨 TO BUILD'} device: {dev}")

print("── 7. BUILD SCRIPTS ACTUALLY RUN (not just stale outputs) ──")
import py_compile
for s in ['scripts/build_body_reveal.py', 'scripts/build_ch1_composites.py',
          'scripts/composite_beat.py', 'scripts/beat_director.py']:
    try:
        py_compile.compile(str(ROOT / s), doraise=True); chk(f"{s} compiles", True)
    except Exception as e:
        chk(f"{s} compiles", False, repr(e)[:70])
# build_ch1_composites assembles the paper edit (skips render if clips exist) —
# this is what caught the ch1_body window/anchor crash; run it for real.
r = subprocess.run(['venv/bin/python', 'scripts/build_ch1_composites.py'],
                   cwd=str(ROOT), capture_output=True, text=True, timeout=600)
chk('build_ch1_composites.py runs clean', r.returncode == 0,
    (r.stderr.strip().splitlines() or [''])[-1][:80])

print("── 8. git pushed / clean ──")
st = subprocess.run(['git', '-C', str(ROOT), 'status', '--porcelain'], capture_output=True, text=True).stdout
unpushed = subprocess.run(['git', '-C', str(ROOT), 'log', '@{u}..', '--oneline'], capture_output=True, text=True).stdout
IGNORE = ('tools/ltx-video',)   # pre-existing dirty submodule, unrelated to the pipeline
dirty = [l for l in st.splitlines() if l.strip() and '??' not in l and not any(g in l for g in IGNORE)]
chk('working tree clean (tracked)', not dirty, f"uncommitted: {[l[3:] for l in dirty]}")
chk('all commits pushed', not unpushed.strip(), 'unpushed commits')

print(f"\n{'='*60}\nPREFLIGHT: {len(ok)} green, {len(bad)} red")
if bad:
    print("RED — fix before building:")
    for l, d in bad: print(f"   ❌ {l}  {d}")
    sys.exit(1)
print("✅ FOUNDATION INTACT — safe to wire director→builder→gate.")
