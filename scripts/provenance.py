#!/usr/bin/env python3
"""
provenance.py — ONE schema for "which workflow made this beat".

The guarantee (consistency across all scenes) rests on a single comparable
signature per beat: same (recipe, params_hash, inputs) == made the identical
way. This module is the only place that schema is defined, so render_beat (at
render time) and stamp_provenance.py (back-filling an existing paper edit) agree
by construction.

Pure over a composite CONFIG dict — imports NOTHING from composite_beat, so
composite_beat can import cfg_signature without a cycle.

  cfg_signature(cfg)   -> {engine, recipe, params_hash, inputs}  (a composite recipe)
  classify_beat(beat, configs) -> full provenance dict for a paper-edit beat
"""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# per-beat injected timing — NOT part of recipe identity. Dropping these makes
# the same CONFIG used in two windows hash identically (that is the whole point:
# it lets the assembler prove two scenes were built the same way).
VOLATILE = {'window', 'vo_span', 'vo', 'duration', 'align', 'cam_end', '_recipe'}

ENGINE = 'composite_beat.render_beat'


def _rel(p):
    """Stable, ROOT-relative string for a path-ish value."""
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except Exception:
        return str(p)


def _canon(cfg):
    """Recipe-identity view of a cfg: volatile timing dropped, paths stabilized,
    deterministically serialized for hashing."""
    out = {}
    for k, v in cfg.items():
        if k in VOLATILE:
            continue
        if k in ('cutout', 'bg_video', 'bg_still', 'bg_frames'):
            out[k] = _rel(v) if v is not None else None
        else:
            out[k] = v
    return json.dumps(out, sort_keys=True, default=str)


def params_hash(cfg):
    return hashlib.sha256(_canon(cfg).encode()).hexdigest()[:12]


def recipe_inputs(cfg):
    """The asset files a composite recipe consumes (cutout + background)."""
    inputs = []
    if cfg.get('cutout'):
        inputs.append(_rel(cfg['cutout']))
    for k in ('bg_video', 'bg_still', 'bg_frames'):
        if cfg.get(k):
            inputs.append(_rel(cfg[k]))
    return inputs


def cfg_signature(cfg, recipe=None):
    """Provenance signature for a composite beat, from its CONFIG dict.
    `recipe` is the friendly CONFIG name when known (cfg['_recipe'] otherwise)."""
    return {
        'engine': ENGINE,
        'recipe': recipe or cfg.get('_recipe'),
        'params_hash': params_hash(cfg),
        'inputs': recipe_inputs(cfg),
    }


def _basename(beat):
    return os.path.basename(beat.get('visual_file') or '')


def classify_beat(beat, configs, approved=frozenset()):
    """Full provenance record for an EXISTING paper-edit beat, recovered from
    its visual_file. Honest: traced=False where the generative recipe is not
    recoverable (raw library asset / inherited animatic) — we never invent one."""
    vf = beat.get('visual_file') or ''
    bn = _basename(beat)
    stem = bn[:-4] if bn.endswith('.mp4') else bn
    parent = os.path.basename(os.path.dirname(vf))

    prov = {'traced': False, 'class': 'inherited', 'recipe': None,
            'engine': None, 'builder': None, 'params_hash': None,
            'inputs': [], 'rendered_file': bn or None, 'approved': False}

    if beat.get('asset') == 'auto' or parent == 'auto_beats':
        prov.update(traced=True, **{'class': 'unsanctioned'}, recipe='build_ch1_auto',
                    builder='build_ch1_auto.py (QUARANTINED)', inputs=[_rel(vf)] if vf else [])
    elif parent == 'composite_beats' and stem in configs:
        sig = cfg_signature(configs[stem], recipe=stem)
        prov.update(traced=True, **{'class': 'composite'}, builder='build_ch1_composites.py',
                    engine=sig['engine'], recipe=sig['recipe'],
                    params_hash=sig['params_hash'], inputs=sig['inputs'])
    elif bn == 'body_reveal_540p.mp4':
        prov.update(traced=True, **{'class': 'prebuilt_composite'},
                    recipe='body_reveal', builder='build_body_reveal.py',
                    engine='composite_beat (prebuilt clip)', inputs=[_rel(vf)])
    elif '/body_stills/' in vf or '/footage/' in vf or '/stock/' in vf:
        prov.update(**{'class': 'library_asset'}, recipe='library_asset',
                    builder='sourced/retarget', inputs=[_rel(vf)])
    elif bn.startswith(('card_', 'g_')):
        prov.update(**{'class': 'card'}, recipe='stat_card',
                    builder='rexcaped_stat_cards.py', inputs=[_rel(vf)] if vf else [])
    elif bn.startswith('i_'):
        prov.update(**{'class': 'ink_gag'}, recipe='ink_gag',
                    builder='rexcaped_stat_cards.py', inputs=[_rel(vf)] if vf else [])
    elif beat.get('asset') == 'animatic':
        prov.update(**{'class': 'inherited'}, recipe='inherited_v3_mark')
    elif vf:
        prov.update(**{'class': 'library_asset'}, recipe='library_asset',
                    builder='sourced', inputs=[_rel(vf)])

    prov['approved'] = bool(prov['recipe']) and prov['recipe'] in approved
    return prov


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from composite_beat import CONFIGS
    print('=== cfg_signature on real CONFIGS (stable recipe identity) ===')
    for nm in ('ch1_body', 'ch1_stumble', 'ch1_povpick'):
        print(f'  {nm:14s}', json.dumps(cfg_signature(CONFIGS[nm], recipe=nm)))
    print('\n  same CONFIG in a different window hashes identically:')
    a = cfg_signature(dict(CONFIGS['ch1_stumble'], window=(10, 18), vo_span=('x', 10, 18)))
    b = cfg_signature(dict(CONFIGS['ch1_stumble'], window=(99, 110), vo_span=('y', 99, 110)))
    print(f'    {a["params_hash"]} == {b["params_hash"]}  -> {a["params_hash"] == b["params_hash"]}')
