#!/usr/bin/env python3
"""continuity_check.py — S4/S6 deterministic continuity + coverage gate on a shot manifest.

FAILS CLOSED on: count_display != planet_m; planet_m != ladder[day]; adjacent shots sharing a vantage;
an insert adjacent to itself; a shot whose characters lack seed_master refs; beats with zero shots
(given --beats N); unique-shot count outside [--min-unique,--max-unique]; masters != --masters (default 23);
a mouth_visible PIP shot in a beat with no PIP mouth:ON line (given --lines script_lines.json).
Usage: continuity_check.py shot_manifest.json [--beats 30] [--lines script_lines.json] [--json out.json]
"""
import argparse, json, sys, re

def ladder_for(day, ladder):
    keys = sorted(int(k) for k in ladder); best = None
    for k in keys:
        if k <= day: best = k
    return ladder[str(best)] if best is not None else None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("manifest"); ap.add_argument("--beats", type=int, default=30)
    ap.add_argument("--lines"); ap.add_argument("--json"); ap.add_argument("--min-unique", type=int, default=150); ap.add_argument("--max-unique", type=int, default=200); ap.add_argument("--masters", type=int, default=23)
    a = ap.parse_args(); m = json.load(open(a.manifest)); fails, warns = [], []
    ladder = m.get("ladder", {}); shots = m.get("shots", []); masters = m.get("seed_masters", [])
    mids = {x.get("id") for x in masters}
    kinds = {}
    for x in masters: kinds[x.get("kind")] = kinds.get(x.get("kind"), 0) + 1
    if len(masters) != a.masters: fails.append(f"seed_masters = {len(masters)}, expected {a.masters} ({kinds})")
    prev = None; uniq = 0; ins = 0; beats_seen = {}
    for s in shots:
        sid = s.get("id"); b = s.get("beat"); beats_seen[b] = beats_seen.get(b, 0) + 1
        if s.get("reuse") == "insert": ins += 1
        else: uniq += 1
        if s.get("count_display") != s.get("planet_m"): fails.append(f"{sid}: count_display {s.get('count_display')} != planet_m {s.get('planet_m')}")
        exp = ladder_for(int(s.get("day", 0)), ladder) if ladder else None
        if exp is not None and s.get("planet_m") != exp: fails.append(f"{sid}: planet_m {s.get('planet_m')} != ladder {exp} on day {s.get('day')}")
        for c in s.get("characters", []):
            if not any(str(r).upper().find(c.upper()[:4]) >= 0 for r in s.get("seed_masters", [])): fails.append(f"{sid}: character {c} has no seed_master ref")
        for r in s.get("seed_masters", []):
            if r not in mids: fails.append(f"{sid}: seed_master {r!r} not in seed_masters")
        if prev is not None:
            if s.get("vantage") and s.get("vantage") == prev.get("vantage"): fails.append(f"{sid}: same vantage as adjacent {prev.get('id')} ({s.get('vantage')!r})")
            if s.get("reuse") == "insert" and prev.get("reuse") == "insert" and s.get("composite_seed_id") == prev.get("composite_seed_id"): fails.append(f"{sid}: insert adjacent to itself")
        prev = s
    for i in range(1, a.beats + 1):
        if f"B{i:02d}" not in beats_seen: fails.append(f"beat B{i:02d} has zero shots")
    if not (a.min_unique <= uniq <= a.max_unique): fails.append(f"unique shots = {uniq}, outside [{a.min_unique},{a.max_unique}]")
    if a.lines:
        lines = json.load(open(a.lines)); on_beats = {l.get("beat") for l in lines if l.get("speaker", "").upper() == "PIP" and str(l.get("mouth", "")).upper() == "ON"}
        for s in shots:
            if "PIP" in [c.upper() for c in s.get("mouth_visible", [])] and s.get("beat") not in on_beats: fails.append(f"{s.get('id')}: PIP mouth_visible but no PIP mouth:ON line in {s.get('beat')}")
    print(f"continuity: shots={len(shots)} unique={uniq} inserts={ins} masters={len(masters)} beats_covered={len(beats_seen)}")
    for w in warns: print(f"  WARN {w}")
    for f in fails[:80]: print(f"  FAIL {f}")
    if len(fails) > 80: print(f"  ... {len(fails)-80} more")
    if a.json: json.dump({"fails": fails, "warns": warns, "unique": uniq, "inserts": ins}, open(a.json, "w"), indent=1)
    print("continuity: " + ("PASS" if not fails else f"FAIL ({len(fails)})")); sys.exit(1 if fails else 0)

if __name__ == "__main__": main()
