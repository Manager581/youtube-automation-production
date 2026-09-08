"""Assign downloaded ElevenLabs mp3s (~/Downloads/ElevenLabs_2026-09-08*.mp3) to first-minute lines by whisper transcript.
Copies to L##_SPEAKER.mp3 when best fuzzy ratio >= 0.55 and the line is unassigned (or --force). Prints the ledger."""
import glob, json, os, re, shutil, subprocess, sys, difflib
D = os.path.dirname(os.path.abspath(__file__)); man = json.load(open(f"{D}/VO_LINES_MANIFEST.json")); lines = man["lines"]
def norm(s): return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()
import whisper
model = whisper.load_model("base")
assigned = {l["id"]: os.path.exists(f"{D}/{l['id']}.mp3") for l in lines}
rep = json.load(open(f"{D}/VO_ASSIGN.json")) if os.path.exists(f"{D}/VO_ASSIGN.json") else {}
for f in sorted(glob.glob(os.path.expanduser("~/Downloads/ElevenLabs_2026-09-08*.mp3"))+glob.glob(os.path.expanduser("~/Downloads/EL_line_*.mp3"))+glob.glob(os.path.expanduser("~/Downloads/EL_row*.mp3")), key=os.path.getmtime):
    if f in rep: continue
    txt = model.transcribe(f, fp16=False)["text"].strip()
    best = max(lines, key=lambda l: difflib.SequenceMatcher(None, " ".join(norm(l["text"])), " ".join(norm(txt))).ratio())
    r = difflib.SequenceMatcher(None, " ".join(norm(best["text"])), " ".join(norm(txt))).ratio()
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip() or 0)
    ok = r >= 0.55 and (not assigned[best["id"]] or "--force" in sys.argv)
    if ok: shutil.copy(f, f"{D}/{best['id']}.mp3"); assigned[best["id"]] = True
    rep[f] = {"line": best["id"] if ok else None, "ratio": round(r, 3), "dur": round(dur, 2), "heard": txt[:90]}
    print(f"{os.path.basename(f)[:45]} -> {best['id'] if ok else 'UNASSIGNED'} r={r:.2f} {dur:.1f}s | {txt[:70]}")
json.dump(rep, open(f"{D}/VO_ASSIGN.json", "w"), indent=1)
print("assigned", sum(assigned.values()), "/", len(lines), "missing:", [k for k, v in assigned.items() if not v])
