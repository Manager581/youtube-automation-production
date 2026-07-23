#!/usr/bin/env python3
"""Pre-render half of the WBS style gate — the 9 of 11 gates knowable before assembly.

`gate_style_wbs.py` grades a finished render against the measured winner bands, so it
cannot run until the video exists. But 9 of its 11 gates are already determined by the
locked shot manifest and the finished VO, so they can be checked NOW — before spending
hours on the clip grind — instead of discovering a failure at the end.

The two it cannot judge are cuts-on-audio-hit (needs the assembled render) and
music-peak-position (needs the chosen track).

  venv/bin/python research/wildbirdsurvival_teardown/gate_style_preflight.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "ep02_shots.json")
VO = os.path.join(HERE, "ep02_vo_block_manifest.json")
RUNTIME = 480.0


def vo_metrics():
    m = json.load(open(VO))
    segs = sorted(m["segments"], key=lambda s: s["drop_at_s"])
    speech = sum(s["duration"] for s in segs)
    words = sum(len([w for w in s["text"].split() if any(c.isalnum() for c in w)])
                for s in segs)
    gaps, prev = [], 0.0
    for s in segs:
        if s["drop_at_s"] > prev:
            gaps.append(s["drop_at_s"] - prev)
        prev = max(prev, s["drop_at_s"] + s["duration"])
    if RUNTIME > prev:
        gaps.append(RUNTIME - prev)
    cov = speech / RUNTIME * 100
    wps = words / speech
    return {"cov": cov, "wps": wps, "density": cov / 100 * wps,
            "maxgap": max(gaps) if gaps else 0.0}


def shot_metrics():
    shots = json.load(open(SHOTS))["shots"]
    durs = sorted(s["dur_s"] for s in shots)
    n = len(durs)
    med = durs[n // 2] if n % 2 else (durs[n // 2 - 1] + durs[n // 2]) / 2
    return {
        "med": med,
        "mean": sum(durs) / n,
        "fast": 100 * sum(1 for d in durs if d < 3) / n,
        "holds": sum(1 for d in durs if d > 10),
        "hookcuts": sum(1 for s in shots if s["in_s"] < 60),
    }


def main():
    if not os.path.exists(VO):
        print("no VO block manifest yet — run split_vo_blocks.py first")
        return 1
    v, s = vo_metrics(), shot_metrics()
    GATES = [
        ("median shot >= 3.5s",         s["med"],      "min", 3.5,  "winners 3.6-4.7; losers <=3.0"),
        ("mean shot >= 5.4s",           s["mean"],     "min", 5.4,  "winners 5.56-7.11"),
        ("fast cuts (<3s) <= 50%",      s["fast"],     "max", 50,   "losers 50/54"),
        ("10s+ holds >= 12",            s["holds"],    "min", 12,   "winners 13-21"),
        ("hook cuts 9-13 (first 60s)",  s["hookcuts"], "rng", (9, 13), "LOSE2 doubled to 22"),
        ("narration coverage <= 60%",   v["cov"],      "max", 60,   "only WORST(67) breached"),
        ("speech pace <= 2.75 wps",     v["wps"],      "max", 2.75, "~150wpm; WORST 3.17 died"),
        ("word density <= 1.5",         v["density"],  "max", 1.5,  "WORST 2.12 died"),
        ("longest wordless gap >= 25s", v["maxgap"],   "min", 25,   "winners >=28s; WORST 17.3"),
    ]
    print("=== WBS STYLE GATE — PRE-RENDER HALF (9 of 11) ===")
    npass = 0
    for label, val, kind, thr, note in GATES:
        ok = val >= thr if kind == "min" else (val <= thr if kind == "max"
                                               else thr[0] <= val <= thr[1])
        npass += ok
        tstr = f">={thr}" if kind == "min" else (f"<={thr}" if kind == "max"
                                                 else f"{thr[0]}-{thr[1]}")
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:<30} got {val:<8.2f} ({tstr})  {note}")
    print(f"  ---> {npass}/{len(GATES)} pre-render style gates pass")
    print("\n  deferred to the render: cuts-on-audio-hit <= 3%, music peak before 50%")
    return 0 if npass == len(GATES) else 1


if __name__ == "__main__":
    sys.exit(main())
