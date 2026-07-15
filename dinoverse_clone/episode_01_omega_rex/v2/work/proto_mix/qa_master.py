import json, re
from faster_whisper import WhisperModel
PM="dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"
POJ=json.load(open(f"{PM}/body_pauses.json"))
def norm(s): return re.sub(r"[^a-z0-9 ]"," ",s.lower()).split()
m=WhisperModel("small",device="cpu",compute_type="int8")
segs,_=m.transcribe(f"{PM}/EPISODE_MASTER.mp4",language="en")
master=set(norm(" ".join(s.text for s in segs)))
rows=[]
for shot,info in POJ.items():
    words=[w for w in norm(info["text"]) if len(w)>2]
    if not words: continue
    present=sum(1 for w in words if w in master)
    frac=present/len(words)
    rows.append((shot,round(frac,2),info["text"][:45]))
bad=[r for r in rows if r[1]<0.7]
print(f"dialogue clips checked: {len(rows)}")
print(f"clips >=70% words present: {sum(1 for r in rows if r[1]>=0.7)}/{len(rows)}")
if bad:
    print("\nLOW-COVERAGE (investigate):")
    for s,f,t in sorted(bad,key=lambda x:x[1]): print(f"  {s} {f:.0%}  \"{t}\"")
else:
    print("VERDICT: all dialogue preserved (every clip >=70% words survive)")
