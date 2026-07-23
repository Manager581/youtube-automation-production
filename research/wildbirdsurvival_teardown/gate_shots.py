#!/usr/bin/env python3
"""
Shot-manifest gate for ep02_shots.json.

Checks the pacing/craft laws the teardown proved, and — unlike the agents' own
audit — computes them from the JSON, the single source of truth. Run it after
any edit to the manifest.

  venv/bin/python research/wildbirdsurvival_teardown/gate_shots.py

HOOK DEFINITION (this is the one the agents' arithmetic got wrong): a "hook cut"
is a shot that STARTS within the first 60 s. Filtering on out_s<=60 wrongly drops
the 14.9 s silence hold at 48.4-63.3 — the single most important hook shot — and
makes the hook look busier and shorter than it is.
"""
import json
import statistics as st
import sys
import os

PATH = os.path.join(os.path.dirname(__file__), "ep02_shots.json")
GROK_CAP = 6.04
GRIT = "real handheld wildlife documentary footage"
BLOOD_RIDER = "does NOT drip"
ANATOMY = "no extra limbs"
HEADON_OK = ("never turns head-on", "never turning head-on", "not turn the booby's head fully head-on",
             "without ever turning head-on", "never head-on", "never faces head-on",
             "do not turn", "never turn")


def gates(shots):
    s = sorted(shots, key=lambda x: x["in_s"])
    durs = [x["dur_s"] for x in s]
    hook = [x for x in s if x["in_s"] < 60]          # STARTS in the first minute
    longs = [x for x in s if x["dur_s"] > GROK_CAP]
    ids = [x["id"] for x in s]

    prev, tiling = 0.0, 0
    for x in s:
        if abs(x["in_s"] - prev) > 0.011:
            tiling += 1
        prev = x["out_s"]

    noblood = [x["id"] for x in s if x.get("has_blood") and BLOOD_RIDER not in x["grok_prompt"]]
    nogrit = [x["id"] for x in s if not x["grok_prompt"].startswith(GRIT)]
    noanat = [x["id"] for x in s if ANATOMY not in x["grok_prompt"]]
    # the two rider closing clauses the audit flagged as self-contradictory — must be gone
    oldrider = [x["id"] for x in s if "only the finch moves" in x["grok_prompt"].lower()
                or "count stays the same" in x["grok_prompt"].lower()]
    headon = [x["id"] for x in s if "head-on" in x["grok_prompt"].lower()
              and not any(n in x["grok_prompt"].lower() for n in HEADON_OK)]
    nocov = [x["id"] for x in longs if not x.get("coverage_note")]

    hmean = sum(x["dur_s"] for x in hook) / len(hook)
    rows = [
        ("Tiling 0->480 s", "0 gaps/overlaps", f"{tiling}", tiling == 0),
        ("Unique shot IDs", f"{len(s)}", f"{len(set(ids))}", len(set(ids)) == len(s)),
        ("Span", "0 -> 480", f"{s[0]['in_s']:.0f} -> {s[-1]['out_s']:.0f}", s[0]["in_s"] == 0 and abs(s[-1]["out_s"] - 480) < 0.5),
        ("Median shot", "3.5-4.7 s", f"{st.median(durs):.2f} s", 3.5 <= st.median(durs) <= 4.7),
        ("Mean shot", ">=5.4 s", f"{st.mean(durs):.2f} s", st.mean(durs) >= 5.4),
        ("Shots under 3 s", "<=50%", f"{sum(1 for d in durs if d < 3)} ({100*sum(1 for d in durs if d<3)/len(durs):.0f}%)", sum(1 for d in durs if d < 3) / len(durs) <= 0.5),
        ("Holds >=10 s", ">=12", f"{sum(1 for d in durs if d >= 10)}", sum(1 for d in durs if d >= 10) >= 12),
        ("Hook cuts (start <60 s)", "9-13", f"{len(hook)}", 9 <= len(hook) <= 13),
        ("Hook mean shot", ">=5 s", f"{hmean:.2f} s", hmean >= 5),
        (">6 s shots w/ coverage note", "all", "all" if not nocov else ",".join(nocov), not nocov),
        ("Grit prefix on every prompt", "all", "all" if not nogrit else ",".join(nogrit), not nogrit),
        ("Anatomy rider on every prompt", "all", "all" if not noanat else ",".join(noanat), not noanat),
        ("DRY-blood rider on blood shots", "all", "all" if not noblood else ",".join(noblood), not noblood),
        ("No prompt asks booby head-on", "0", "none" if not headon else ",".join(headon), not headon),
        ("No self-contradictory rider tails", "0", "none" if not oldrider else ",".join(oldrider), not oldrider),
    ]
    return rows


def main():
    shots = json.load(open(PATH))["shots"]
    rows = gates(shots)
    print(f"\n=== SHOT MANIFEST GATE ({len(shots)} shots) ===")
    ok = True
    for name, target, val, passed in rows:
        ok = ok and passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:<32} target {target:<16} got {val}")
    print(f"  ---> {'ALL GATES PASS' if ok else 'GATES FAILING'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
