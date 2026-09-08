"""Build the first-minute MIX SPEC for lib/assembly/audio_mix.py: VO lines at script times (shifted forward if the previous
line's audio overruns), MMAudio foley per edit-spec window, one music bed with the SCRIPT's [MUSIC] cues as section automation.
Refuses to run unless every VO line file exists (one-pass VO; no placeholders in the mix). Usage: build_first_minute_mix.py [--allow-missing-vo]"""
import json, os, subprocess, sys
S = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(S, "..", "..", ".."))
VO = f"{S}/vo_lines_first_minute"; man = json.load(open(f"{VO}/VO_LINES_MANIFEST.json"))["lines"]
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
music = {"file": f"{REPO}/assets/dino_music/light_playful.mp3", "gain_db": -18, "duck_db": -8,
         "sections": [{"t0": 0.0, "t1": 0.4, "gain_db": 4, "why": "[MUSIC hit] on the cold open"}, {"t0": 30.0, "t1": 39.0, "gain_db": -60, "why": "B05 [MUSIC out]: the rule is delivered dry"}, {"t0": 39.0, "t1": 40.0, "gain_db": 5, "why": "[MUSIC hit] slam on the planet reveal (S021)"}],
         "placeholder": "library bed (Pixabay CC0, from assets/dino_music); swap for a driving MrBeast-style cue when the owner allows a Pixabay download"}
mix = {"duration": 60.0, "vo": vo, "foley": foley, "music": music, "target_lufs": -14, "true_peak": -1.5, "notes": {"vo_overrun_shifts": [v["line"] for v, l in zip(vo, [m for m in man if m["id"] in {x["line"] for x in vo}]) if abs(v["t"] - tc(l["t"])) > 0.2]}}
json.dump(mix, open(f"{S}/first_minute_mix_spec.json", "w"), indent=1)
print(f"mix spec: {len(vo)} VO lines, {len(foley)} foley windows, music {os.path.basename(music['file'])}; missing VO: {missing}")
