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
    ap.add_argument("--pip-cap", type=int, default=20); ap.add_argument("--chars-per-sec", type=float, default=None, help="MEASURED value; normally read from --lane speech.chars_per_sec"); ap.add_argument("--lane"); ap.add_argument("--partial", action="store_true", help="the script is an excerpt (e.g. first minute): loops that never PAY and the word band are WARN, everything else still FAILs"); ap.add_argument("--air", type=float, default=0.2); ap.add_argument("--min-words", type=int, default=3800); ap.add_argument("--max-words", type=int, default=4200)
    a = ap.parse_args()
    ladder = DEFAULT_LADDER
    shots = []
    if a.ladder:
        try:
            M = json.load(open(a.ladder)); ladder = M.get("ladder", DEFAULT_LADDER); shots = M.get("shots", [])
        except Exception as e: print(f"  WARN ladder file unreadable ({e}); using default")
    # A reaction has to be READABLE. Presence in a wide is not a reaction: the reference cuts to a face.
    REACTION_FRAMINGS = {"CU", "ECU", "MCU", "MS", "OTS", "INS"}
    react_shots = {}   # beat -> {character: [shot ids framed tightly enough to read]}
    for sh in shots:
        if sh.get("shot_type") in REACTION_FRAMINGS:
            for c in (sh.get("characters") or []): react_shots.setdefault(sh.get("beat"), {}).setdefault(c.upper(), []).append(sh.get("id"))
    fails, warns, info = [], [], {}
    if a.lane and a.chars_per_sec is None:
        L = json.load(open(a.lane)); a.chars_per_sec = (L.get("speech") or {}).get("chars_per_sec")
    if a.chars_per_sec is None:
        print("story_gate REFUSED: chars/s is not measured yet (lane.speech.chars_per_sec is None). Run vo_qc.py --measure-cps on the directed prototype line first; a constant would be a guess that fails after credits are spent."); sys.exit(2)
    beats = []  # (t_in, t_out, name)
    silences = []; react_needed = []; reacts = []; flashfwd = set(); wow_beats = []; wow_text = []
    cur_t = None; cur_day = None; last_day = -1
    events = []  # (t, kind, detail)
    loops = {}   # id -> {"OPEN":t, "FEED":[t], "PAY":t}
    pip_on = 0; words = 0; share = {}; chars_by_beat = {}
    planet_by_beat = {}; count_by_beat = {}; day_by_beat = {}
    for ln in open(a.script, encoding="utf-8"):
        s = ln.strip()
        m = re.match(r"^##\s+(B\d{2})\s+\[(\d+:\d{2})-(\d+:\d{2})\]", s)
        if m:
            cur = m.group(1); cur_t = tc(m.group(2)); beats.append((cur_t, tc(m.group(3)), cur)); events.append((cur_t, "beat", cur)); continue
        if cur_t is None: continue
        cur = beats[-1][2]
        if s.startswith("["):   # EVERY bracket tag on the line is parsed (v3 scripts put several tags on one line; the old parser read only the first)
            for tag in re.findall(r"\[[^\]]*\]", s):
                m = re.match(r"^\[DAY\s+(\d+)\]", tag)
                if m:
                    d = int(m.group(1)); day_by_beat[cur] = d
                    if cur in flashfwd: pass   # a flash-forward beat may show a later day without advancing the ladder clock
                    elif d < last_day: fails.append(f"{cur}: DAY {d} < previous {last_day} (non-monotonic)")
                    else: last_day = max(last_day, d)
                    events.append((cur_t, "tag", tag)); continue
                m = re.match(r"^\[PLANET\s+(\d+)\]", tag)
                if m: planet_by_beat[cur] = int(m.group(1)); events.append((cur_t, "tag", tag)); continue
                m = re.match(r"^\[COUNT\s+(\d+)\]", tag)
                if m: count_by_beat[cur] = int(m.group(1)); events.append((cur_t, "tag", tag)); continue
                m = re.match(r"^\[LOOP\s+(\w+)\s+(OPEN|FEED|PAY)\]", tag)
                if m:
                    lid, k = m.group(1), m.group(2); L = loops.setdefault(lid, {"OPEN": None, "FEED": [], "PAY": None})
                    if k == "OPEN": L["OPEN"] = cur_t
                    elif k == "FEED": L["FEED"].append(cur_t)
                    else: L["PAY"] = cur_t
                    events.append((cur_t, "tag", tag)); continue
                m = re.match(r"^\[SILENT\s+(\d+(?:\.\d+)?)s?\]", tag)
                if m: silences.append((cur, float(m.group(1)))); events.append((cur_t, "tag", tag)); continue
                if re.match(r"^\[(STAKES|REVEAL|LOCK)\b", tag): react_needed.append((cur, tag[:24])); events.append((cur_t, "tag", tag)); continue
                m = re.match(r"^\[REACT\s+(\w+)", tag)
                if m: reacts.append((cur, m.group(1).upper())); events.append((cur_t, "tag", tag)); continue
                if re.match(r"^\[FLASHFWD\b", tag): flashfwd.add(cur); events.append((cur_t, "tag", tag)); continue
                if re.match(r"^\[WOW\b", tag): wow_beats.append(cur); wow_text.append((cur, tag)); events.append((cur_t, "tag", tag)); continue
                if re.match(r"^\[(TEXT|MUSIC|SFX|TIMER|HOST)\b", tag): events.append((cur_t, "tag", tag)); continue
            continue
        m = re.match(r"^\*\*(\w+)\*\*\s*\(([^)]*)\):\s*(.+)$", s)
        if m:
            spk, meta, text = m.group(1), m.group(2), m.group(3)
            n = len(re.findall(r"[A-Za-z0-9']+", text)); words += n; share[spk] = share.get(spk, 0) + n
            chars_by_beat[cur] = chars_by_beat.get(cur, 0) + len(text)
            if spk.upper() == "PIP" and re.search(r"mouth:\s*ON", meta, re.I): pip_on += 1
            if BANNED.search(text): fails.append(f"{cur}: banned brand/likeness token in line: {text[:60]!r}")
    # SPEECH BUDGET per beat (2026-09-08: the first minute carried 91 s of speech in 60 s; ~16 chars/s spoken at announcer pace,
    # a beat may hold at most (1-air) of its length in speech). Fails BEFORE any voice is bought.
    for (t_in, t_out, name) in beats:
        spoken = chars_by_beat.get(name, 0) / a.chars_per_sec; budget = (1 - a.air) * (t_out - t_in)
        if spoken > budget + 0.25: fails.append(f"{name}: {spoken:.1f}s of speech in a {t_out - t_in:.0f}s beat (budget {budget:.1f}s) -> cut ~{spoken - budget:.1f}s (~{int((spoken - budget) * a.chars_per_sec)} chars)")
    info["speech_seconds_by_beat"] = {n: round(chars_by_beat.get(n, 0) / a.chars_per_sec, 1) for _, _, n in beats}
    # designed silences count against the beat's air, and a beat holding [SILENT] must still fit its speech
    for (b, secs) in silences:
        t = next(((ti, to) for ti, to, n in beats if n == b), None)
        if t and chars_by_beat.get(b, 0) / a.chars_per_sec + secs > (t[1] - t[0]) + 0.25: fails.append(f"{b}: [SILENT {secs}s] + {chars_by_beat.get(b, 0) / a.chars_per_sec:.1f}s speech exceed the {t[1] - t[0]:.0f}s beat")
    info["designed_silences"] = silences
    # REACTION LAW (reference: every stakes/reveal/lock line is followed by contestant reaction CUs, often a silent matched pair)
    for (b, tag) in react_needed:
        who = {c for bb, c in reacts if bb == b}
        if len(who) < 2: fails.append(f"{b}: {tag} has {len(who)} [REACT <char>] tags after it (need >= 2, one per contestant): nobody listens")
    # ...and a [REACT X] tag must have somewhere to BE. Counting tags is what let four drafts satisfy this law on paper
    # while the beat held only wides: you cannot read a face in a WS or a HERO, so the tag has to point at a real
    # tight shot on that character in that beat.
    if react_shots:
        for (b, c) in sorted(set(reacts)):
            got = react_shots.get(b, {}).get(c, [])
            if not got:
                have = sorted(react_shots.get(b, {}))
                fails.append(f"{b}: [REACT {c}] has no shot in this beat that can carry it — no {sorted(REACTION_FRAMINGS)} shot holds {c} "
                             f"(readable reactions available here: {have or 'none'}). A reaction nobody can see is not a reaction.")
    info["reaction_shots_available"] = {b: {c: v for c, v in d.items()} for b, d in react_shots.items()}
    info["reaction_tags"] = len(reacts)
    # loops
    for lid, L in loops.items():
        if L["OPEN"] is None: fails.append(f"loop '{lid}' has FEED/PAY but no OPEN")
        if L["PAY"] is None: (warns if a.partial else fails).append(f"loop '{lid}' OPEN at {L['OPEN']}s never PAYs" + (" (excerpt)" if a.partial else ""))
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
    # LAW 1 — the promise is on screen by lane.promise.by_s: the FIRST beat carries [WOW ...] and starts by by_s; a [FLASHFWD] beat
    # must be that first beat, <= 3 s, and its DAY/PLANET must sit on the ladder (checked above) so the cold open cannot contradict the story
    lane_cfg = json.load(open(a.lane)) if a.lane else {}
    prom = lane_cfg.get("promise")
    if prom and beats:
        first = beats[0]
        if first[2] not in wow_beats: fails.append(f"{first[2]}: first beat has no [WOW ...] tag — the promise ('{prom.get('claim','')[:50]}') is not on screen by {prom.get('by_s', 3)} s")
        elif first[0] > float(prom.get("by_s", 3)): fails.append(f"{first[2]}: WOW beat starts at {first[0]}s > by_s {prom.get('by_s')}")
        # The tag used to satisfy Law 1 by merely EXISTING — its text was never compared to the promise it claims to prove.
        # A [WOW ...] must NAME one of lane.promise.proof_shots, the same shot deliver.py makes WATCH_NOTES name for first_3s.
        proof = [p for p in (prom.get("proof_shots") or [])]
        if proof:
            txt = " ".join(t for b, t in wow_text if b == first[2])
            if not any(ps in txt for ps in proof):
                fails.append(f"{first[2]}: [WOW ...] does not name a promise proof shot {proof} — the tag asserts the promise instead of "
                             f"pointing at the shot that shows it (deliver.py demands the same shot in WATCH_NOTES first_3s)")
    for b in flashfwd:
        t = next(((ti, to) for ti, to, n in beats if n == b), None)
        if t and (t[1] - t[0]) > 3.0: fails.append(f"{b}: [FLASHFWD] beat is {t[1]-t[0]:.0f}s (> 3 s): a flash-forward is a glimpse, not a scene")
        if beats and b != beats[0][2]: fails.append(f"{b}: [FLASHFWD] is only legal as the first beat (cold open)")
        if b not in day_by_beat or b not in planet_by_beat: fails.append(f"{b}: [FLASHFWD] must carry [DAY] and [PLANET] on the ladder (a wrong-size rock is a continuity reject later)")
    info_extra = {"flashfwd": sorted(flashfwd), "wow_beats": wow_beats}
    # caps
    if pip_on > a.pip_cap: fails.append(f"PIP mouth:ON lines = {pip_on} > cap {a.pip_cap}")
    if not a.partial and not (a.min_words <= words <= a.max_words): fails.append(f"dialogue words = {words}, outside [{a.min_words},{a.max_words}]")
    info = {"beats": len(beats), "words": words, "pip_mouth_on": pip_on, "loops": {k: v for k, v in loops.items()}, "share": {k: round(v/words, 2) for k, v in share.items()} if words else {}, **info_extra}
    print(f"story_gate: beats={len(beats)} words={words} PIP mouth:ON={pip_on} loops={list(loops)} share={info['share']}")
    for w in warns: print(f"  WARN {w}")
    for f in fails: print(f"  FAIL {f}")
    if a.json: json.dump({"fails": fails, "warns": warns, "info": info}, open(a.json, "w"), indent=1)
    print("story_gate: " + ("PASS" if not fails else f"FAIL ({len(fails)})"))
    sys.exit(1 if fails else 0)

if __name__ == "__main__": main()
