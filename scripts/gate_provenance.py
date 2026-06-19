#!/usr/bin/env python3
"""
gate_provenance.py — the assembler's approval gate. THE consistency guarantee:
refuse to ship a beat that did not come from a sanctioned, approved recipe.

Per beat (provenance re-derived from disk — never trusts a possibly-stale stamp):
  unsanctioned   came from a quarantined builder (build_ch1_auto)        -> BLOCK
  unknown_recipe a composite whose recipe is in no ledger list           -> BLOCK
  stale          composite clip's render sidecar != current recipe hash  -> BLOCK
  pending        a known recipe the owner has not blessed yet            -> warn (BLOCK under --strict)
  non_recipe     library / card / inherited (no recipe behind it)        -> coverage (BLOCK under --strict)
  approved       recipe in research/approved_recipes.json                -> PASS

Exit 0 = shippable under policy; 1 = blocked. Importable: enforce(beats, strict).
  venv/bin/python scripts/gate_provenance.py --paper-edit storyboards/foo.json [--strict]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from composite_beat import CONFIGS
from provenance import classify_beat, ROOT

LEDGER = ROOT / 'research/approved_recipes.json'
HARD = {'unsanctioned', 'unknown_recipe', 'stale'}   # never ship
SOFT = {'pending', 'non_recipe'}                      # ship unless --strict


def ledger():
    if LEDGER.exists():
        d = json.loads(LEDGER.read_text())
        return set(d.get('approved', [])), set(d.get('candidates_pending_owner_signoff', []))
    return set(), set()


def beat_status(beat, approved, candidates):
    p = classify_beat(beat, CONFIGS, approved)
    cls, recipe, vf = p['class'], p['recipe'], (beat.get('visual_file') or '')
    if cls == 'unsanctioned':
        return 'unsanctioned', p
    if cls in ('composite', 'prebuilt_composite'):
        if cls == 'composite':
            side = Path(vf + '.prov.json')           # drift: was the clip rendered from THIS recipe?
            if side.exists():
                try:
                    rh = json.loads(side.read_text()).get('params_hash')
                    if rh and rh != p['params_hash']:
                        return 'stale', p
                except Exception:
                    pass
        if recipe in approved:
            return 'approved', p
        if recipe in candidates:
            return 'pending', p
        return 'unknown_recipe', p
    return 'non_recipe', p


def check(beats, approved, candidates, strict=False):
    rows = [(beat_status(b, approved, candidates), b) for b in beats]
    counts = Counter(s for (s, _), _ in rows)
    hard = [(i, s, p, b) for i, ((s, p), b) in enumerate(rows) if s in HARD]
    soft = [(i, s, p, b) for i, ((s, p), b) in enumerate(rows) if s in SOFT]
    ok = (not hard) and not (strict and soft)
    return ok, counts, hard, soft


def enforce(beats, strict=False):
    """Returns (ok, printable_summary). Used by the renderer and the CLI."""
    approved, candidates = ledger()
    ok, counts, hard, soft = check(beats, approved, candidates, strict)
    L = [f"provenance gate ({'STRICT' if strict else 'default'}): {len(beats)} beats"]
    for k in ('approved', 'pending', 'non_recipe', 'unknown_recipe', 'stale', 'unsanctioned'):
        if counts.get(k):
            L.append(f"  {counts[k]:3d}  {k}")
    for i, s, p, b in hard:
        L.append(f"  x BLOCK beat[{i}] {b.get('beat_id', '')}: {s} — "
                 f"recipe={p['recipe']} file={Path(b.get('visual_file') or '').name}")
    if strict:
        for i, s, p, b in soft[:8]:
            L.append(f"  ! strict beat[{i}] {b.get('beat_id', '')}: {s} — recipe={p['recipe']}")
        if len(soft) > 8:
            L.append(f"  ! ... +{len(soft) - 8} more soft beats under --strict")
    L.append("  VERDICT: " + ("PASS" if ok else "BLOCKED"))
    return ok, "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper-edit', required=True)
    ap.add_argument('--strict', action='store_true',
                    help='also require every beat to be an APPROVED recipe')
    a = ap.parse_args()
    pe = json.loads(Path(a.paper_edit).read_text())
    beats = pe['beats'] if isinstance(pe, dict) else pe
    ok, text = enforce(beats, a.strict)
    print(text)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
