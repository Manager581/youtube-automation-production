"""VO-driven retime (the reference law: the picture follows the voice). Anchors = script line starts -> real line starts
(sequential, never overlapping, never tighter than the scripted spacing). Every segment boundary / op time / foley window /
music section is warped through the piecewise-linear map. Writes *_edit_spec_v1r.json + *_mix_spec_r.json."""
import json, os, subprocess
S = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(S, "..", "..", ".."))
TEMPO = {"ORB": 1.15, "PIP": 1.05, "GRUFF": 1.0}; GAP = 0.12
VO = f"{S}/vo_lines_first_minute"; man = json.load(open(f"{VO}/VO_LINES_MANIFEST.json"))["lines"]
spec = json.load(open(f"{S}/first_minute_edit_spec_v1.json")); mix = json.load(open(f"{S}/first_minute_mix_spec.json"))
def tc(s): a, b = s.split(":"); return int(a) * 60 + float(b)
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())
lines = []
for l in man:
    f = f"{VO}/{l['id']}.mp3"; tp = TEMPO[l["speaker"]]; d = dur(f) / tp; lines.append({"id": l["id"], "speaker": l["speaker"], "file": f, "s": tc(l["t"]), "d": round(d, 3), "tempo": tp})
r_prev = None
for i, l in enumerate(lines):
    if i == 0: l["r"] = l["s"]
    else:
        p = lines[i - 1]; l["r"] = round(max(p["r"] + p["d"] + GAP, p["r"] + (l["s"] - p["s"])), 3)
anchors = [(0.0, 0.0)] + [(l["s"], l["r"]) for l in lines]
last = lines[-1]; tail_s = spec["segments"][-1]["t_out"]; tail_r = round(last["r"] + last["d"] + 1.0, 3)
anchors.append((tail_s, max(tail_r, tail_s + (last["r"] - last["s"]))))
def warp(t):
    for (s0, r0), (s1, r1) in zip(anchors, anchors[1:]):
        if t <= s1: return r0 + (r1 - r0) * ((t - s0) / (s1 - s0) if s1 > s0 else 0)
    s0, r0 = anchors[-1]; return r0 + (t - s0)
EXTRA_WHITEOUT = {"S011", "S012", "S016", "S017"}
MAX_K = 1.25   # the reference tolerates ~25% timing slack; beyond that the hook grammar dilutes -> the SCRIPT must lose seconds
over = {}
for sg in spec["segments"]:
    a, b = warp(sg["t_in"]), warp(sg["t_out"]); k = (b - a) / max(sg["t_out"] - sg["t_in"], 1e-6)
    if k > MAX_K: over.setdefault(sg["beat"], []).append((sg["shot"], round(k, 2)))
if over:
    print("retime REFUSED: the voice runs longer than the cut allows. Cut dialogue, do not stretch picture:")
    for beat, shots in over.items():
        bl = [l for l in lines if any(m["id"] == l["id"] and m["beat"] == beat for m in man)]
        spoken = sum(l["d"] for l in bl); alloc = sum(sg["t_out"] - sg["t_in"] for sg in spec["segments"] if sg["beat"] == beat)
        print(f"  {beat}: {spoken:.1f}s of speech in a {alloc:.1f}s beat -> cut ~{max(0, spoken - 0.8 * alloc):.1f}s of dialogue (~{int(max(0, spoken - 0.8 * alloc) * 16)} chars)  worst stretch {max(k for _, k in shots)}x")
    raise SystemExit(1)
segs = []
for sg in spec["segments"]:
    a, b = warp(sg["t_in"]), warp(sg["t_out"]); old = sg["t_out"] - sg["t_in"]; new = b - a; k = new / old if old > 0 else 1
    ops = []
    for o in sg.get("ops", []):
        o = dict(o)
        for key in ("t0", "t1", "t", "t_on", "t_off", "t_start"):
            if key in o and isinstance(o[key], (int, float)): o[key] = round(o[key] * k, 3)
        if "each" in o: o["each"] = round(o["each"] * k, 3)
        ops.append(o)
    if sg["shot"] in EXTRA_WHITEOUT: ops.append({"op": "whiteout", "t": 0.0, "dur": 0.08, "alpha": 0.85, "note": "added: soft transition on the re-use cut (hook transitions floor)"})
    s2 = dict(sg); s2.update({"t_in": round(a, 3), "t_out": round(b, 3), "ops": ops, "retime_k": round(k, 3)}); segs.append(s2)
for x, y in zip(segs, segs[1:]): y["t_in"] = x["t_out"]
# split slots longer than their source clip into alternating punch-ins (no looped clip, +cuts); clip lengths from the ledger
L = json.load(open(f"{REPO}/assets/shrinking_planet/CLIP_LEDGER.json"))["clips"]
def clen(src): row = L.get(src); return dur(row["clip"]) if row else 999
split = []
for sg in segs:
    src = sg["src"].split(":", 1)[1]; avail = clen(src) - float(sg.get("t0", 0.0)) - 0.15; slot = sg["t_out"] - sg["t_in"]
    if slot <= avail or any(o.get("op") == "cards" for o in sg.get("ops", [])): split.append(sg); continue
    n = int(slot // avail) + 1; part = slot / n; t = sg["t_in"]
    for j in range(n):
        s2 = dict(sg); s2["t_in"] = round(t, 3); s2["t_out"] = round(t + part, 3); t += part
        s2["ops"] = [o for o in sg["ops"] if o.get("op") == "text"] if j == 0 else []
        if j % 2 == 1: s2["ops"].append({"op": "punch", "z0": 1.3, "z1": 1.3, "t0": 0.0, "note": "split: alternating punch-in so a long slot never loops its clip"})
        s2["shot"] = f"{sg['shot']}{'abcdef'[j]}"; s2["split_of"] = sg["shot"]; split.append(s2)
    print(f"  split {sg['shot']}: slot {slot:.1f}s > clip {avail:.1f}s -> {n} parts")
segs = split
spec2 = dict(spec); spec2.update({"version": "first_minute_edit_spec_v1r", "window": [0.0, segs[-1]["t_out"]], "segments": segs, "retime": {"anchors": anchors, "tempo": TEMPO, "gap": GAP}})
json.dump(spec2, open(f"{S}/first_minute_edit_spec_v1r.json", "w"), indent=1)
total = segs[-1]["t_out"]
vo = [{"file": l["file"], "t": l["r"], "gain_db": 0, "tempo": l["tempo"], "line": l["id"], "dur": l["d"]} for l in lines]
foley = []
for sg in segs:
    f = f"{REPO}/output/shrinking_planet/foley/{sg['shot']}.flac"
    if os.path.exists(f): foley.append({"file": f, "t": sg["t_in"], "gain_db": -10, "dur": round(sg["t_out"] - sg["t_in"], 3), "shot": sg["shot"]})
music = dict(mix["music"]); music["sections"] = [dict(s, t0=round(warp(s["t0"]), 3), t1=round(warp(s["t1"]), 3)) for s in mix["music"]["sections"]]
mix2 = {"duration": round(total, 3), "vo": vo, "foley": foley, "music": music, "target_lufs": -7, "true_peak": -1.0, "retimed_from": "first_minute_mix_spec.json"}
json.dump(mix2, open(f"{S}/first_minute_mix_spec_r.json", "w"), indent=1)
over = [(sg["shot"], round(sg["t_out"] - sg["t_in"], 2)) for sg in segs if sg["t_out"] - sg["t_in"] > 6.0]
print(f"retimed: {len(segs)} segments, total {total:.1f}s (was 60.0); lines placed {lines[0]['r']:.1f}..{last['r']:.1f}; slots >6s: {over}")
for l in lines: print(f"  {l['id']:10s} script {l['s']:5.1f} -> {l['r']:5.1f}  dur {l['d']:4.1f} (tempo {l['tempo']})")
