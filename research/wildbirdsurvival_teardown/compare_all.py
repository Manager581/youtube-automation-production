#!/usr/bin/env python3
import json, os
import numpy as np

VIDS=[("BEST",1984363,"win"),("WIN2",939961,"win"),("WIN3",855377,"win"),
      ("WIN4",674534,"win"),("WIN5",653959,"win"),
      ("LOSE2",3041,"lose"),("WORST",1879,"lose")]

def words_of(name):
    wj=f"wordts/{name}.json"; ws=[]
    if os.path.exists(wj):
        for seg in json.load(open(wj)).get("segments",[]):
            for w in seg.get("words",[]):
                if w.get("start") is not None: ws.append((w["start"],w["end"]))
    return ws

def dedup_artifact(words):
    """Whisper loops on music-only regions produce evenly-spaced phantom words; keep as-is
       but compute coverage robustly using actual word spans."""
    return words

rows=[]
for name,views,cls in VIDS:
    d=json.load(open(f"forensics_{name}.json"))
    dur=d["dur"]; durs=[s["dur"] for s in d["shots"]]
    ws=words_of(name)
    # narration coverage: union of word spans / dur
    cov=0.0; last=0.0
    spans=sorted([(a,b) for a,b in ws])
    merged=[]
    for a,b in spans:
        if merged and a<=merged[-1][1]: merged[-1]=(merged[-1][0],max(merged[-1][1],b))
        else: merged.append((a,b))
    cov=sum(b-a for a,b in merged)
    covpct=100*cov/dur
    # pauses
    pauses=[]
    for i in range(len(ws)-1):
        g=ws[i+1][0]-ws[i][1]
        if g>0.7: pauses.append(g)
    long_pauses=[g for g in pauses if g>=5]
    max_pause=max(pauses) if pauses else 0
    # time to first word
    t1=ws[0][0] if ws else dur
    # words/sec during speech
    nwords=len(ws)
    wps=nwords/cov if cov>0 else 0
    # cut alignment
    al=d.get("aligns",[])
    dws=[abs(a["d_word"]) for a in al if "d_word" in a]
    onword=100*sum(1 for x in dws if x<=0.4)/len(dws) if dws else 0
    med_dword=np.median(dws) if dws else 0
    # shot dist
    fast=100*sum(1 for x in durs if x<=3)/len(durs)
    longhold=100*sum(1 for x in durs if x>10)/len(durs)
    # music arc: peak location of harmonic energy (fraction into video)
    rh=np.array(d["env"]["rms_h"]); g=np.array(d["env"]["grid"])
    peak_frac=g[int(np.argmax(rh))]/dur if len(rh) else 0
    rows.append(dict(name=name,views=views,cls=cls,dur=round(dur),cuts=d["num_cuts"],
        mean_shot=d["mean_shot"],med_shot=round(float(np.median(durs)),1),
        fast=round(fast),longhold=round(longhold),cov=round(covpct),
        t1=round(t1,1),wps=round(wps,2),maxpause=round(max_pause,1),
        nlongpause=len(long_pauses),onword=round(onword),med_dword=round(float(med_dword),2),
        onsets=len(d["onsets"]),peakfrac=round(float(peak_frac),2)))

hdr=["name","views","cls","dur","cuts","mean_shot","med_shot","fast%","long%","cov%","t1st","wps","maxpz","npz5","onwd%","medΔw","sfx","pkfr"]
print("  ".join(f"{h:>7}" for h in hdr))
for r in rows:
    print(f"{r['name']:>7} {r['views']:>7} {r['cls']:>7} {r['dur']:>7} {r['cuts']:>7} {r['mean_shot']:>7} "
          f"{r['med_shot']:>7} {r['fast']:>6} {r['longhold']:>6} {r['cov']:>6} {r['t1']:>6} {r['wps']:>6} "
          f"{r['maxpause']:>6} {r['nlongpause']:>6} {r['onword']:>6} {r['med_dword']:>6} {r['onsets']:>6} {r['peakfrac']:>6}")

print("\n--- WIN avg vs LOSE avg ---")
for k in ["med_shot","fast","longhold","cov","t1","wps","maxpause","nlongpause","onword","med_dword","onsets"]:
    wv=np.mean([r[k] for r in rows if r['cls']=='win'])
    lv=np.mean([r[k] for r in rows if r['cls']=='lose'])
    print(f"  {k:>12}: win={wv:>7.1f}   lose={lv:>7.1f}")
json.dump(rows,open("compare_metrics.json","w"),indent=1)
