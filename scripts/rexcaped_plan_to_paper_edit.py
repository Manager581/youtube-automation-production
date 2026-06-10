#!/usr/bin/env python3
"""
rexcaped_plan_to_paper_edit.py — the missing glue: turn a rexcaped_edit_engine
plan (shots with asset types) into a renderer-ready paper edit for
scripts/ffmpeg_production_render.py.

Per-shot asset -> visual:
  stat_card -> <cards-dir>/card_s{i:04d}.png            (still, slow push)
  stock     -> <cards-dir>/ph_stock_s{i:04d}.png        (placeholder slate, static)
  meme      -> <cards-dir>/ph_meme_s{i:04d}.png         (placeholder slate, static)
  creature  -> clip from --creature-dir pool (cycled, hero clip opens the video);
               no pool -> <cards-dir>/ph_creature_s{i:04d}.png slate

Also wires the measured sound grammar (R4: sound on ~every cut) via the
renderer's per-beat "sfx" field (assets/sfx types): impact on cards, whoosh on
stock/meme, impact_hit on creature, thinned to every 3rd cut inside rapid-fire
bursts so 0.1s runs don't turn to mush. One chapter name on every beat ->
the renderer loops its fallback music track wall-to-wall.

Creature clips shorter than their beat freeze-extend in the renderer (tpad
clone). For nicer long holds, pre-loop the pool with
scripts/boomerang_loop_clips.py and pass that dir instead.

Usage:
  venv.nosync/bin/python scripts/rexcaped_plan_to_paper_edit.py \
    --plan storyboards/trex_pilot_plan.json \
    --manifest audio/trex_pilot/narration_manifest.json \
    --cards-dir assets/trex_pilot/cards \
    --creature-dir footage/trex_pilot \
    --out storyboards/trex_pilot_paper_edit.json
"""
import argparse, json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SFX_BY_ASSET = {'stat_card': 'impact', 'meme': 'whoosh',
                'creature': 'impact_hit', 'stock': 'whoosh'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True)
    ap.add_argument('--manifest', help='narration manifest (for total duration)')
    ap.add_argument('--cards-dir', required=True)
    ap.add_argument('--creature-dir', help='dir of creature mp4 clips (the hero pool)')
    ap.add_argument('--creature-glob', default='*.mp4',
                    help="restrict the creature pool (e.g. 'dunk_trex_*.mp4') so "
                         "b-roll in the same dir can't land in a creature slot")
    ap.add_argument('--hero', help='filename cycled FIRST (the video must open on it)')
    ap.add_argument('--stock-dir', help='dir of stock/b-roll mp4 clips for stock slots')
    ap.add_argument('--stock-glob', default='*.mp4')
    ap.add_argument('--out', required=True)
    ap.add_argument('--chapter', default='REXCAPED PILOT')
    ap.add_argument('--no-sfx', action='store_true')
    a = ap.parse_args()

    shots = json.load(open(a.plan))['shots']
    cards = (PROJECT_ROOT / a.cards_dir).resolve()

    total = shots[-1]['end']
    if a.manifest:
        total = max(total, float(json.load(open(a.manifest))['total_duration_sec']))

    def build_pool(d, glob_pat, hero=None):
        if not d:
            return []
        dd = (PROJECT_ROOT / d).resolve()
        pool = sorted(p for p in dd.glob(glob_pat) if not p.name.startswith('_'))
        if hero:
            pool.sort(key=lambda p: p.name != hero)      # hero cycles first
        return pool

    pool = build_pool(a.creature_dir, a.creature_glob, a.hero)
    stock_pool = build_pool(a.stock_dir, a.stock_glob)

    beats, missing, n_creature, n_stock = [], [], 0, 0
    burst_run = 0
    for i, s in enumerate(shots):
        asset = s['asset']
        visual_type, zoom = 'still', 0.0
        if asset == 'stat_card':
            path = cards / f'card_s{i:04d}.png'
            zoom = 1.5
        elif asset == 'creature' and pool:
            path = pool[n_creature % len(pool)]
            n_creature += 1
            visual_type = 'video'
        elif asset == 'stock' and stock_pool:
            path = stock_pool[n_stock % len(stock_pool)]
            n_stock += 1
            visual_type = 'video'
        else:
            ph = 'creature' if asset == 'creature' else asset
            path = cards / f'ph_{ph}_s{i:04d}.png'
        if not path.exists():
            missing.append((i, asset, str(path)))

        # R4 sound-on-cut, thinned inside bursts
        burst_run = burst_run + 1 if s['why'] == 'burst' else 0
        if a.no_sfx or i == 0:
            sfx = None
        elif s['why'] == 'burst':
            sfx = 'impact' if burst_run == 1 else (
                'whoosh' if burst_run % 3 == 0 else None)
        else:
            sfx = SFX_BY_ASSET[asset]

        end = s['end'] if i + 1 < len(shots) else max(s['end'], total)
        beat = {
            'beat_id': f'beat_{i:04d}',
            'start_sec': s['t'],
            'end_sec': end,
            'duration': round(end - s['t'], 3),
            'visual_file': str(path),
            'visual_type': visual_type,
            'clip_audio': 'mute',
            'tension_level': 0.6,
            'zoom_speed_pct_per_sec': zoom,
            'chapter': a.chapter,
            'text': s.get('text', ''),
            'asset': asset,
            'why': s['why'],
        }
        if sfx:
            beat['sfx'] = sfx
        beats.append(beat)

    # ── CONTENT GATE: slot/content contracts, checked BEFORE any render ──
    # (added after two silent failures: b-roll landing in the creature-hero
    #  open slot, and a stat card parked on a 5.25s shot)
    import fnmatch, sys
    gate = []
    if a.hero and Path(beats[0]['visual_file']).name != a.hero:
        gate.append(f"GATE FAIL: beat_0000 must OPEN on hero '{a.hero}', "
                    f"got '{Path(beats[0]['visual_file']).name}'")
    for b in beats:
        nm = Path(b['visual_file']).name
        if (b['asset'] == 'creature' and b['visual_type'] == 'video'
                and not fnmatch.fnmatch(nm, a.creature_glob)):
            gate.append(f"GATE FAIL: creature slot {b['beat_id']} holds "
                        f"non-creature file '{nm}'")
        if b['asset'] == 'stat_card' and b['duration'] > 3.5:
            gate.append(f"GATE FAIL: card {b['beat_id']} held "
                        f"{b['duration']:.2f}s (cards must flash; max 3.5s)")
    ph_time = sum(b['duration'] for b in beats if 'ph_' in b['visual_file'])
    pct_ph = 100 * ph_time / beats[-1]['end_sec']
    first30_ph = sum(1 for b in beats if b['start_sec'] < 30
                     and 'ph_' in b['visual_file'])

    from collections import Counter
    mix = dict(Counter(b['asset'] for b in beats))
    out = {
        'beats': beats,
        'stats': {'beat_count': len(beats),
                  'total_duration_sec': round(beats[-1]['end_sec'], 3),
                  'asset_mix': mix,
                  'creature_pool': [p.name for p in pool],
                  'sfx_beats': sum(1 for b in beats if b.get('sfx'))},
        '_version': 'rexcaped_plan_v1',
    }
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}: {len(beats)} beats, {out['stats']['total_duration_sec']}s, "
          f"mix={mix}, sfx on {out['stats']['sfx_beats']} beats, "
          f"creature pool={len(pool)}, stock pool={len(stock_pool)}")
    print(f"  CONTENT: placeholder slates = {pct_ph:.0f}% of runtime"
          + (" ⚠ HIGH (sourcing decisions pending)" if pct_ph > 30 else "")
          + f"; slates in first 30s: {first30_ph}")
    for g in gate:
        print(' ', g)
    if gate:
        sys.exit(1)
    if missing:
        print(f"  MISSING {len(missing)} visuals (run rexcaped_stat_cards.py first):")
        for i, asset, p in missing[:6]:
            print(f"    shot {i:04d} [{asset}] {p}")


if __name__ == '__main__':
    main()
