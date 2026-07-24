#!/usr/bin/env python3
"""Flag pre-crops on the same seed that would render as the same shot.

73 of the 88 shots share a seed. The pre-crop is what makes them read as different
camera set-ups; if two shots on one seed get near-identical boxes they come back as
near-identical clips, which is the glitchy-loop look that got rough_cut_v1 rejected.

Two boxes are "too alike" when they overlap heavily (IoU) AND sit at a similar scale,
because either alone is fine -- a tight box inside a wide one is a legitimate push-in,
and two same-scale boxes on opposite sides of the frame are legitimately different.

  venv/bin/python research/wildbirdsurvival_teardown/gate_crop_distinct.py
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "ep02_shots.json")

IOU_LIMIT = 0.80       # boxes overlapping more than this...
SCALE_LIMIT = 0.15     # ...at within this relative width difference, are too alike


def box(s):
    x, y, w, h = (int(float(v)) for v in s.split(","))
    return x, y, w, h


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def main():
    shots = json.load(open(SHOTS))["shots"]
    by = collections.defaultdict(list)
    for s in shots:
        if s.get("seed_crop"):
            by[s["seed"]].append((s["id"], box(s["seed_crop"]), s["in_s"]))

    problems = []
    for seed, items in sorted(by.items()):
        items.sort(key=lambda t: t[2])
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                ida, a, ta = items[i]
                idb, b, tb = items[j]
                o = iou(a, b)
                scale = abs(a[2] - b[2]) / max(a[2], b[2])
                if o > IOU_LIMIT and scale < SCALE_LIMIT:
                    problems.append((seed, ida, idb, o, scale, abs(tb - ta)))

    print(f"seeds with crops: {len(by)}   shots with crops: {sum(len(v) for v in by.values())}")
    print(f"pairs too alike (IoU > {IOU_LIMIT} at < {SCALE_LIMIT:.0%} scale difference): {len(problems)}")
    for seed, a, b, o, sc, dt in sorted(problems, key=lambda p: -p[3]):
        near = "  <-- ADJACENT IN TIME" if dt < 30 else ""
        print(f"  {a} vs {b:5s} IoU {o:.2f}  scale diff {sc:.0%}  {dt:.0f}s apart  {seed}{near}")
    if not problems:
        print("  every pair on a shared seed is visibly distinct")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
