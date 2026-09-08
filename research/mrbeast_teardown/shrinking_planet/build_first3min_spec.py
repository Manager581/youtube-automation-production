"""Build the 0:00-3:02 edit spec for shrinking_planet: hook_edit_spec_v1 segments verbatim (0:00-0:45) + B06-B09 from shot_manifest_v2.
Inserts (punch-ins / re-uses) are FREE edit-layer ops on their source shot. TEXT chips / ladder ticks / flash-forward whiteouts from SCRIPT_v2 tags.
Also writes a DRY-RUN ledger pointing every unique shot at a still->video stand-in made from its seed (timing/coverage checks ONLY; never shipped)."""
import json, os, subprocess, sys
S = os.path.dirname(os.path.abspath(__file__))
hook = json.load(open(f"{S}/hook_edit_spec_v1.json")); m = json.load(open(f"{S}/shot_manifest_v2.json"))
def tc(s): a, b = s.split(":"); return int(a) * 60 + float(b)
shots = {s["id"]: s for s in m["shots"]}
INSERT_SRC = {"S004": "S002", "S011": "S009", "S012": "S010", "S016": "S007", "S017": "S006", "S031": "S027", "S034": "S033", "S036": "S035", "S040": "S039", "S044": "S043"}
PUNCH = {"S034": 1.6, "S036": 1.5, "S040": 1.6, "S044": 1.6}
segs = list(hook["segments"]); last_out = segs[-1]["t_out"]
TEXT = {  # shot -> list of text ops (within-segment seconds)
 "S022": [{"op": "text", "text": "DAY 1", "t_on": 0.3, "t_off": 2.8, "lead": 0.3, "size": 84, "y": "h*0.10", "color": "white"},
          {"op": "text", "text": "1,000 M", "t_on": 0.6, "t_off": 2.8, "lead": 0.3, "size": 84, "y": "h*0.19", "color": "0xFFD24A"}],
 "S038": [{"op": "text", "text": "DAY 2", "t_on": 0.3, "t_off": 2.8, "lead": 0.3, "size": 84, "y": "h*0.10", "color": "white"}],
 "S046": [{"op": "text", "text": "DAY 4", "t_on": 0.3, "t_off": 2.8, "lead": 0.3, "size": 84, "y": "h*0.10", "color": "white"},
          {"op": "text", "text": "OFFER #1", "t_on": 1.2, "t_off": 4.0, "lead": 0.3, "size": 84, "y": "h*0.19", "color": "0xFFD24A"}],
}
# B08 ladder ticks on the orbital plate S042 (2:21-2:30): each rung draws as a text pop, 1,000 M -> 2 M
rungs = ["1,000 M", "500 M", "300 M", "25 M", "12 M", "4 M", "2 M"]
TEXT["S042"] = [{"op": "text", "text": r, "t_on": 0.8 + i * 1.05, "t_off": 8.8, "lead": 0.2, "size": 64, "y": f"h*{0.14 + i * 0.10:.2f}", "color": ("white" if i < 6 else "0xFF4040")} for i, r in enumerate(rungs)]
# B07 flash-forward: five whiteout whooshes over the dust plate (the five flash-forward frames are later-video shots not yet generated -> KNOWN GAP)
FLASH = {"S037": [{"op": "whiteout", "t": 0.6 + i * 0.85, "dur": 0.10, "alpha": 0.9} for i in range(5)]}
for s in sorted(m["shots"], key=lambda x: tc(x["t_in"])):
    if tc(s["t_in"]) < last_out or tc(s["t_in"]) >= 182: continue
    sid = s["id"]; src = INSERT_SRC.get(sid, sid); ops = []
    if sid in PUNCH: ops.append({"op": "punch", "z0": 1.0, "z1": PUNCH[sid], "t0": 0.0, "t1": tc(s["t_out"]) - tc(s["t_in"]), "note": "insert = free punch-in on source shot"})
    elif sid in INSERT_SRC: ops.append({"op": "punch", "z0": 1.3, "z1": 1.3, "t0": 0.0, "note": "re-use insert, static re-crop so it never matches its source frame"})
    ops += TEXT.get(sid, []) + FLASH.get(sid, [])
    segs.append({"shot": sid, "beat": s["beat"], "t_in": tc(s["t_in"]), "t_out": tc(s["t_out"]), "src": f"ledger:{src}", "reuse": s.get("reuse", "unique"), "ops": ops})
spec = {"lane": "shrinking_planet", "version": "first3min_edit_spec_v1", "fps": 24, "size": "1920x1080", "window": [0.0, segs[-1]["t_out"]], "base": "hook_edit_spec_v1 (segments verbatim)",
        "known_gaps": ["B07 FLASHFWD: the five flash-forward frames are later-video shots (not in the 0-3min seed set); placeholder = dust plate + five whiteouts", "audio: VO/music/foley attached at assembly after ElevenLabs + MMAudio (credits pending)"],
        "segments": segs}
json.dump(spec, open(f"{S}/first3min_edit_spec_v1.json", "w"), indent=1)
# continuity
bad = [(a["shot"], b["shot"]) for a, b in zip(segs, segs[1:]) if abs(a["t_out"] - b["t_in"]) > 1e-6]
print(f"segments {len(segs)} span {segs[0]['t_in']}-{segs[-1]['t_out']}s gaps/overlaps {bad}")
uniq = sorted({sg["src"].split(":")[1] for sg in segs if sg["src"].startswith("ledger:")}); print("unique ledger refs", len(uniq))
# dry-run stand-ins from seeds
if "--standins" in sys.argv:
    D = "output/shrinking_planet/dryrun_standins"; os.makedirs(D, exist_ok=True); led = {"_schema": "DRY-RUN ONLY — still->video stand-ins from seeds; NOT banked clips; never ship", "clips": {}}
    for sid in uniq:
        png = f"assets/shrinking_planet/seeds/{sid}.png"; mp4 = f"{D}/{sid}_standin.mp4"
        if not os.path.exists(png): print("NO SEED", sid); continue
        if not os.path.exists(mp4): subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-i", png, "-t", "12", "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", mp4], check=True)
        led["clips"][sid] = {"clip": mp4, "verdict": "PASS", "note": "DRY-RUN stand-in"}
    json.dump(led, open(f"{D}/DRYRUN_LEDGER.json", "w"), indent=1); print("stand-ins", len(led["clips"]))
