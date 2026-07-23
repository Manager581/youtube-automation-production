#!/usr/bin/env python3
"""WBS style-gate: grade any render's forensics against the MEASURED winner bands.
Reuses extract_forensics.py output. Usage: python gate_style_wbs.py <NAME> [<NAME> ...]
Prints per-metric PASS/FAIL. This checks STYLE conformance only — NOT virality (see note)."""
import json, sys, os
import numpy as np

# Verified winner bands from the adversarial teardown (research/wildbirdsurvival_teardown).
# Each gate: (label, getter, kind, threshold, note)   kind: 'min'|'max'|'range'
def hook_cuts(f):   return sum(1 for c in f["cuts"] if c < 60)
def longest_gap(name, cm): return cm["maxpause"]

GATES = [
 ("median shot >= 3.5s",        lambda m,f: m["med_shot"],   "min", 3.5,  "winners 3.6-4.7; losers <=3.0"),
 ("mean shot >= 5.4s",          lambda m,f: m["mean_shot"],  "min", 5.4,  "winners 5.56-7.11; losers <=5.02"),
 ("fast cuts (<3s) <= 50%",     lambda m,f: m["fast"],       "max", 50,   "winners <=48% (WIN5 13); losers 50/54"),
 ("narration coverage <= 60%",  lambda m,f: m["cov"],        "max", 60,   "ceiling; only WORST(67) breached"),
 ("word density <= 1.5",        lambda m,f: round(m["cov"]/100*m["wps"],2),"max",1.5,"cov*wps; WORST 2.12 died"),
 ("speech pace <= 2.75 wps",    lambda m,f: m["wps"],        "max", 2.75, "~150wpm; WORST 3.17 died"),
 ("longest wordless gap >= 25s",lambda m,f: m["maxpause"],   "min", 25,   "winners >=28s; WORST 17.3"),
 ("10s+ holds >= 12",           lambda m,f: sum(1 for s in f['shots'] if s['dur']>10),"min",12,"winners 13-21"),
 ("hook cuts 9-13 (first 60s)", lambda m,f: hook_cuts(f),    "range",(9,13),"winners 9-11; LOSE2 doubled to 22"),
 ("cuts-on-audio-hit <= 3%",    lambda m,f: round(100*sum(1 for a in f['aligns'] if a.get('d_onset') is not None and abs(a['d_onset'])<=0.4)/max(len(f['aligns']),1),1),"max",3,"no SFX-stinger editing"),
 ("music peak before 50%",      lambda m,f: m["peakfrac"],   "max", 0.50, "mid-peak co-occurs with flop"),
]

def load(name):
    cm={r["name"]:r for r in json.load(open("compare_metrics.json"))}[name]
    fo=json.load(open(f"forensics_{name}.json"))
    return cm,fo

def grade(name):
    m,f=load(name)
    print(f"\n=== {name}  ({m['views']:,} views, {m['cls'].upper()}) ===")
    npass=0
    for label,get,kind,thr,note in GATES:
        v=get(m,f)
        if kind=="min":   ok=v>=thr
        elif kind=="max": ok=v<=thr
        else:             ok=thr[0]<=v<=thr[1]
        npass+=ok
        tstr=f">={thr}" if kind=="min" else (f"<={thr}" if kind=="max" else f"{thr[0]}-{thr[1]}")
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:<30} got {v:<7} ({tstr})  {note}")
    print(f"  --> {npass}/{len(GATES)} style gates passed")
    return npass

if __name__=="__main__":
    names=sys.argv[1:] or ["BEST","WIN2","WIN3","WIN4","WIN5","LOSE2","WORST"]
    for n in names: grade(n)
    print("\nNOTE: this gate verifies STYLE conformance only. LOSE2 (a 3K flop) will PASS most gates —")
    print("that is correct and by design: the gate cannot see topic/title/thumbnail, which is where")
    print("virality actually lives. Post-publish CTR/retention is the only check for that layer.")
