"""Build the first-minute MIX SPEC for lib/assembly/audio_mix.py: VO lines at script times (shifted forward if the previous
line's audio overruns), MMAudio foley per edit-spec window, one music bed with the SCRIPT's [MUSIC] cues as section automation.
Refuses to run unless every VO line file exists (one-pass VO; no placeholders in the mix). Usage: build_first_minute_mix.py [--allow-missing-vo]"""
import json, os, subprocess, sys
S = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(S, "..", "..", ".."))
VO = f"{S}/vo_lines_first_minute_v3"; man = json.load(open(f"{VO}/VO_LINES_MANIFEST.json"))["lines"]
spec = json.load(open(f"{S}/first_minute_edit_spec_v1.json")); foley_dir = f"{REPO}/output/shrinking_planet/foley"
def tc(s): a, b = s.split(":"); return int(a) * 60 + float(b)
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)
vo = []; cursor = 0.0; missing = []
for l in man:
    f = f"{VO}/{l['id']}.mp3"
    if not os.path.exists(f): missing.append(l["id"]); continue
    t = max(tc(l["t"]), cursor + 0.15); d = dur(f); vo.append({"file": f, "t": round(t, 3), "gain_db": 0, "line": l["id"], "dur": round(d, 3)}); cursor = t + d
if missing and "--allow-missing-vo" not in sys.argv: print("REFUSING: missing VO lines", missing); sys.exit(1)
foley = []
for sg in spec["segments"]:
    f = f"{foley_dir}/{sg['shot']}.flac"
    if os.path.exists(f): foley.append({"file": f, "t": sg["t_in"], "gain_db": -10, "dur": round(sg["t_out"] - sg["t_in"], 3), "shot": sg["shot"]})
# DESIGN-LAYER SFX (library, Pixabay licence) at the hook's exact moments — hits on every text pop, whoosh per archive card,
# riser into "30 DAYS", cash register on the crate bloom, sub on the tether insert, drone under the rule, impact on the planet slam.
SFX = {k: f"{REPO}/{v['file']}" for k, v in json.load(open(f"{REPO}/assets/shrinking_planet/sfx/manifest.json"))["items"].items()}
sfx = []
for sg in spec["segments"]:
    for o in sg.get("ops", []):
        if o.get("op") == "text": sfx.append({"file": SFX["impact_hit"], "t": round(sg["t_in"] + o.get("t_on", 0) - 0.05, 3), "gain_db": -9, "dur": 0.9, "why": f"hit under text pop '{o['text']}'"})
        if o.get("op") == "cards":
            for i in range(len(o["stills"])): sfx.append({"file": SFX["whoosh_simple"], "t": round(sg["t_in"] + o.get("t_start", 0) + i * o.get("each", 0.4), 3), "gain_db": -8, "why": "whoosh per archive card"})
    if sg["shot"] == "S005": sfx += [{"file": SFX["riser"], "t": round(sg["t_in"] - 3.0, 3), "gain_db": -12, "dur": 3.4, "why": "riser into 30 DAYS"}, {"file": SFX["cash_register"], "t": round(sg["t_in"] + 0.6, 3), "gain_db": -10, "dur": 1.2, "why": "cash-register hit on the crate bloom"}]
    if sg["shot"] == "S008": sfx.append({"file": SFX["sub_drop"], "t": sg["t_in"], "gain_db": -8, "dur": 2.0, "why": "single sub hit on the tether insert (B02 mix note)"})
    if sg["shot"] == "S018": sfx.append({"file": SFX["dark_drone"], "t": sg["t_in"], "gain_db": -14, "dur": 9.0, "why": "low drone under the rule while music is out (B05 mix note)"})
    if sg["shot"] == "S021": sfx.append({"file": SFX["impact_hit"], "t": sg["t_in"], "gain_db": -4, "dur": 2.5, "why": "music slam on the planet reveal"})
music = {"file": f"{REPO}/assets/shrinking_planet/music/cue_upbeat_epic_134_raw.mp3", "gain_db": -18, "duck_db": -8,
         "sections": [{"t0": 0.0, "t1": 0.4, "gain_db": 4, "why": "[MUSIC hit] on the cold open"}, {"t0": 30.0, "t1": 39.0, "gain_db": -60, "why": "B05 [MUSIC out]: the rule is delivered dry"}, {"t0": 39.0, "t1": 40.0, "gain_db": 5, "why": "[MUSIC hit] slam on the planet reveal (S021)"}],
         "source": "Pixabay music (Content License): epic upbeat trailer cue, 1:34"}
mix = {"duration": 60.0, "vo": vo, "foley": foley, "sfx": sfx, "music": music, "target_lufs": -14, "true_peak": -1.5, "notes": {"vo_overrun_shifts": [v["line"] for v, l in zip(vo, [m for m in man if m["id"] in {x["line"] for x in vo}]) if abs(v["t"] - tc(l["t"])) > 0.2]}}
json.dump(mix, open(f"{S}/first_minute_mix_spec.json", "w"), indent=1)
print(f"mix spec: {len(vo)} VO lines, {len(foley)} foley windows, music {os.path.basename(music['file'])}; missing VO: {missing}")
