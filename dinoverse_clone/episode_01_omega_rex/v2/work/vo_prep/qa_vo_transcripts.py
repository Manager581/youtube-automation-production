import json, re, sys
from pathlib import Path
from faster_whisper import WhisperModel

ROOT = Path("/Users/jefflawrence/Documents/youtube-automation-production")
AUD  = ROOT/"audio/dinoverse_omega"
MAN  = json.load(open(ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep/vo_manifest_v2.json"))

def norm(s):
    s = s.lower().replace("—"," ").replace("…"," ").replace("’","'")
    return re.sub(r"[^a-z0-9' ]"," ", s).split()

model = WhisperModel("small", device="cpu", compute_type="int8")
bad, ok = [], 0
print(f"{'shot':<7}{'wav':<24} verdict")
print("-"*78)
for l in MAN["lines"]:
    w = AUD/l["wav"]
    if not w.exists(): continue
    segs,_ = model.transcribe(str(w), language="en")
    heard = " ".join(s.text for s in segs).strip()
    exp_w, got_w = norm(l["exact_text"]), norm(heard)
    # word-level recall of the scripted words
    missing = [x for x in exp_w if x not in got_w]
    status = "OK" if not missing else f"MISSING {missing}"
    if missing:
        bad.append((l["shot"], l["exact_text"], heard, missing))
    else:
        ok += 1
    print(f"{l['shot']:<7}{l['wav']:<24} {status}")

print("\n" + "="*78)
print(f"CLEAN: {ok}/{ok+len(bad)}")
if bad:
    print("\n--- lines with missing/mangled words ---")
    for shot, exp, heard, miss in bad:
        print(f"\n{shot}")
        print(f"  script: {exp}")
        print(f"  heard : {heard}")
        print(f"  miss  : {miss}")
