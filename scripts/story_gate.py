#!/usr/bin/env python3
"""story_gate.py — S3 deterministic story-structure gate (PIPELINE_OVERHAUL_PLAN S3).

Parses a tagged script (SCRIPT_v*.md format) and FAILS CLOSED on:
  - any [LOOP id OPEN] without a later [LOOP id PAY]
  - FEED/PAY gaps for any loop > --max-loop-gap seconds (default 300)
  - any stretch of runtime with no tag line and no beat header > --max-device-gap s (default 60)
  - PIP mouth:ON lines > --pip-cap (default 20)
  - total dialogue words outside [--min-words, --max-words] (default 3800-4200)
  - [DAY] non-monotonic; [PLANET]/[COUNT] mismatch with the ladder for that day
  - banned brand/likeness tokens
Usage: story_gate.py SCRIPT.md [--ladder shot_manifest.json] [--json out.json]
"""
import argparse, json, re, sys

BANNED = re.compile(r"\b(mrbeast|mr\.? beast|beast games|feastables|lunchly|jimmy|chandler|karl|nolan)\b|in a \w+ video", re.I)
DEFAULT_LADDER = {"1":1000,"2":1000,"5":500,"6":500,"10":300,"15":300,"20":25,"25":20,"26":12,"27":7,"28":4,"29":2,"30":2}

def tc(s):
    m = re.match(r"(\d+):(\d{2})", s); return int(m.group(1))*60+int(m.group(2))

def ladder_for(day, ladder):
    keys = sorted(int(k) for k in ladder)
    best = None
    for k in keys:
        if k <= day: best = k
    return ladder[str(best)] if best is not None else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("--ladder"); ap.add_argument("--json")
    ap.add_argument("--max-loop-gap", type=int, default=300); ap.add_argument("--max-device-gap", type=int, default=60)
    ap.add_argument("--pip-cap", type=int, default=20); ap.add_argument("--min-words", type=int, default=3800); ap.add_argument("--max-words", type=int, default=4200)
    a = ap.parse_args()
    ladder = DEFAULT_LADDER
    if a.ladder:
        try: ladder = json.load(open(a.ladder)).get("ladder", DEFAULT_LADDER)
        except Exception as e: print(f"  WARN ladder file unreadable ({e}); using default")
    fails, warns, info = [], [], {}
    beats = []  # (t_in, t_out, name)
    cur_t = None; cur_day = None; last_day = -1
    events = []  # (t, kind, detail)
    loops = {}   # id -> {"OPEN":t, "FEED":[t], "PAY":t}
    pip_on = 0; words = 0; share = {}
    planet_by_beat = {}; count_by_beat = {}; day_by_beat = {}
    for ln in open(a.script, encoding="utf-8"):
        s = ln.strip()
        m = re.match(r"^##\s+(B\d{2})\s+\[(\d+:\d{2})-(\d+:\d{2})\]", s)
        if m:
            cur = m.group(1); cur_t = tc(m.group(2)); beats.append((cur_t, tc(m.group(3)), cur)); events.append((cur_t, "beat", cur)); continue
        if cur_t is None: continue
        cur = beats[-1][2]
        m = re.match(r"^\[DAY\s+(\d+)\]", s)
        if m:
            d = int(m.group(1)); day_by_beat[cur] = d
            if d < last_day: fails.append(f"{cur}: DAY {d} < previous {last_day} (non-monotonic)")
            last_day = max(last_day, d); events.append((cur_t, "tag", s)); continue
        m = re.match(r"^\[PLANET\s+(\d+)\]", s)
        if m: planet_by_beat[cur] = int(m.group(1)); events.append((cur_t, "tag", s)); continue
        m = re.match(r"^\[COUNT\s+(\d+)\]", s)
        if m: count_by_beat[cur] = int(m.group(1)); events.append((cur_t, "tag", s)); continue
        m = re.match(r"^\[LOOP\s+(\w+)\s+(OPEN|FEED|PAY)\]", s)
        if m:
            lid, k = m.group(1), m.group(2); L = loops.setdefault(lid, {"OPEN": None, "FEED": [], "PAY": None})
            if k == "OPEN": L["OPEN"] = cur_t
            elif k == "FEED": L["FEED"].append(cur_t)
            else: L["PAY"] = cur_t
            events.append((cur_t, "tag", s)); continue
        if re.match(r"^\[(TEXT|MUSIC|SFX|FLASHFWD|TIMER)\b", s): events.append((cur_t, "tag", s)); continue
        m = re.match(r"^\*\*(\w+)\*\*\s*\(([^)]*)\):\s*(.+)$", s)
        if m:
            spk, meta, text = m.group(1), m.group(2), m.group(3)
            n = len(re.findall(r"[A-Za-z0-9']+", text)); words += n; share[spk] = share.get(spk, 0) + n
            if spk.upper() == "PIP" and re.search(r"mouth:\s*ON", meta, re.I): pip_on += 1
            if BANNED.search(text): fails.append(f"{cur}: banned brand/likeness token in line: {text[:60]!r}")
    # loops
    for lid, L in loops.items():
        if L["OPEN"] is None: fails.append(f"loop '{lid}' has FEED/PAY but no OPEN")
        if L["PAY"] is None: fails.append(f"loop '{lid}' OPEN at {L['OPEN']}s never PAYs")
        pts = sorted([t for t in [L["OPEN"]] + L["FEED"] + [L["PAY"]] if t is not None])
        for x, y in zip(pts, pts[1:]):
            if y - x > a.max_loop_gap: fails.append(f"loop '{lid}': gap {y-x}s between touches at {x}s→{y}s exceeds {a.max_loop_gap}s")
    # device cadence
    ts = sorted(set(t for t, _, _ in events))
    for x, y in zip(ts, ts[1:]):
        if y - x > a.max_device_gap: fails.append(f"no retention device/beat for {y-x}s ({x}s→{y}s) > {a.max_device_gap}s")
    # ladder
    for b, p in planet_by_beat.items():
        d = day_by_beat.get(b)
        if d is None: warns.append(f"{b}: PLANET tag without DAY"); continue
        exp = ladder_for(d, ladder)
        if exp is not None and p != exp: fails.append(f"{b}: PLANET {p} but ladder says {exp} on day {d}")
        c = count_by_beat.get(b)
        if c is not None and c != p: fails.append(f"{b}: COUNT {c} != PLANET {p}")
    # caps
    if pip_on > a.pip_cap: fails.append(f"PIP mouth:ON lines = {pip_on} > cap {a.pip_cap}")
    if not (a.min_words <= words <= a.max_words): fails.append(f"dialogue words = {words}, outside [{a.min_words},{a.max_words}]")
    info = {"beats": len(beats), "words": words, "pip_mouth_on": pip_on, "loops": {k: v for k, v in loops.items()}, "share": {k: round(v/words, 2) for k, v in share.items()} if words else {}}
    print(f"story_gate: beats={len(beats)} words={words} PIP mouth:ON={pip_on} loops={list(loops)} share={info['share']}")
    for w in warns: print(f"  WARN {w}")
    for f in fails: print(f"  FAIL {f}")
    if a.json: json.dump({"fails": fails, "warns": warns, "info": info}, open(a.json, "w"), indent=1)
    print("story_gate: " + ("PASS" if not fails else f"FAIL ({len(fails)})"))
    sys.exit(1 if fails else 0)

if __name__ == "__main__": main()
