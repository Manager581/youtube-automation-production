#!/usr/bin/env python3
"""Print every shot assigned to one seed, for the seed-vs-prompt reachability audit.

Grok/LTX i2v begins on the seed's frame 1, so a shot is only makeable if its
prompt's framing, creature count and action are reachable from that still. This
prints the shots for a seed so they can be judged against the actual PNG.

  venv/bin/python research/wildbirdsurvival_teardown/seed_group.py SEED_raw_wound.png
  venv/bin/python research/wildbirdsurvival_teardown/seed_group.py --list
"""
import collections
import json
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
SHOTS = os.path.join(HERE, "ep02_shots.json")
ASSETS = os.path.join(REPO, "assets", "vampire_finch")


def load():
    return sorted(json.load(open(SHOTS))["shots"], key=lambda s: s["in_s"])


def main():
    args = sys.argv[1:]
    shots = load()
    by = collections.defaultdict(list)
    for s in shots:
        by[s["seed"]].append(s)

    if not args or args[0] == "--list":
        print(f"{len(by)} distinct seeds over {len(shots)} shots\n")
        for seed in sorted(by, key=lambda z: -len(by[z])):
            exists = os.path.exists(os.path.join(ASSETS, seed))
            ids = ",".join(s["id"] for s in by[seed])
            print(f"{len(by[seed]):3d}  {seed:42s} {'' if exists else 'MISSING '}{ids}")
        return 0

    seed = args[0]
    if seed not in by:
        print(f"no shots use seed {seed!r}")
        return 1
    path = os.path.join(ASSETS, seed)
    print(f"SEED FILE (open this image and look at it): {path}")
    print(f"exists: {os.path.exists(path)}")
    print(f"shots using it: {len(by[seed])}\n")
    for s in by[seed]:
        print("=" * 78)
        print(f"{s['id']}  [{s['in_s']}-{s['out_s']}s, {s['dur_s']}s]  size={s['size']}  "
              f"act={s['act']}  has_blood={s.get('has_blood')}  physics={s.get('physics_risk')}")
        for field in ("vantage", "action", "grok_prompt"):
            print(f"-- {field.upper()} --")
            print(textwrap.fill(s[field], 96))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
