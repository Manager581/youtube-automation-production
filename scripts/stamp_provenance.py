#!/usr/bin/env python3
"""
stamp_provenance.py — back-fill a `provenance` record onto every beat of a
paper edit, so the timeline finally records WHICH WORKFLOW MADE EACH SCENE.

Uses the shared schema (provenance.classify_beat) and the on-record approval
ledger (research/approved_recipes.json). Honest by construction: a beat whose
generative recipe is not recoverable is stamped traced=false — never a guessed
recipe. This is the data the assembler guarantee (step 3) reads.

  # dry-run summary (no writes):
  venv.nosync/bin/python scripts/stamp_provenance.py \
      --paper-edit storyboards/trex_pilot_paper_edit_v4_ch1.json

  # stamp in place (writes a one-time .prebak):
  ... --paper-edit storyboards/trex_pilot_paper_edit_v4_ch1.json --write
"""
import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from composite_beat import CONFIGS
from provenance import classify_beat, ROOT


def load_approved():
    p = ROOT / 'research/approved_recipes.json'
    if p.exists():
        return set(json.loads(p.read_text()).get('approved', []))
    return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper-edit', required=True)
    ap.add_argument('--write', action='store_true',
                    help='stamp in place (else dry-run summary only)')
    a = ap.parse_args()

    pe_path = Path(a.paper_edit)
    pe = json.loads(pe_path.read_text())
    beats = pe['beats'] if isinstance(pe, dict) else pe
    approved = load_approved()

    cls = Counter()
    traced = appr = 0
    for b in beats:
        prov = classify_beat(b, CONFIGS, approved)
        b['provenance'] = prov
        cls[prov['class']] += 1
        traced += prov['traced']
        appr += prov['approved']

    print(f"\n{pe_path.name}: {len(beats)} beats")
    for k, v in cls.most_common():
        print(f"  {v:3d}  {k}")
    print(f"  traced (recipe recoverable): {traced}/{len(beats)}")
    print(f"  approved recipe (ship-eligible): {appr}/{len(beats)}")

    if a.write:
        bak = pe_path.with_suffix(pe_path.suffix + '.prebak')
        if not bak.exists():
            shutil.copy(pe_path, bak)
        pe_path.write_text(json.dumps(pe, indent=2))
        print(f"  stamped in place (backup: {bak.name})")
    else:
        print("  dry-run — pass --write to stamp in place")


if __name__ == '__main__':
    main()
