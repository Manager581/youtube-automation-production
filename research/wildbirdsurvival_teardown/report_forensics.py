#!/usr/bin/env python3
import sys, os, json
import numpy as np

def load(name):
    return json.load(open(f"forensics_{name}.json"))

def report(name):
    d=load(name)
    print("="*90)
    print(f"{name}  dur={d['dur']}s  cuts={d['num_cuts']}  mean_shot={d['mean_shot']}s  thr={d['cut_threshold']}")
    # words
    wj=f"wordts/{name}.json"
    words=[]
    if os.path.exists(wj):
        wd=json.load(open(wj))
        for seg in wd.get("segments",[]):
            for w in seg.get("words",[]):
                if w.get("start") is not None:
                    words.append((w["start"],w["end"],w["word"].strip()))
    # PACING: words per 10s bucket
    dur=d['dur']
    if words:
        nb=int(dur//10)+1
        wc=[0]*nb
        for s,e,w in words: wc[int(s//10)]+=1
        wps=[round(c/10,1) for c in wc]
        print("\nNARRATION PACING (words/sec per 10s bucket):")
        print("  "+" ".join(f"{v:.1f}" for v in wps))
        # pauses (gap between consecutive words > 0.7s)
        pauses=[]
        for i in range(len(words)-1):
            gap=words[i+1][0]-words[i][1]
            if gap>0.7:
                pauses.append((round(words[i][1],1),round(gap,1),words[i][2],words[i+1][2]))
        print(f"\nDELIBERATE PAUSES (>0.7s gap) [{len(pauses)}]: time(gap) after..before")
        for t,g,a,b in pauses[:25]:
            print(f"  {t:>6}s (+{g}s)  ...{a} | {b}...")
    # CUT ALIGNMENT
    al=d.get("aligns",[])
    if al and "d_word" in al[0]:
        dws=[abs(a["d_word"]) for a in al if "d_word" in a]
        on_beat=sum(1 for x in dws if x<=0.4)
        print(f"\nCUT vs NARRATION: {on_beat}/{len(dws)} cuts within 0.4s of a word-start "
              f"({100*on_beat/len(dws):.0f}%). median|d_word|={np.median(dws):.2f}s")
    if al and "d_onset" in al[0]:
        dos=[abs(a["d_onset"]) for a in al if "d_onset" in a]
        near=sum(1 for x in dos if x<=0.4)
        print(f"CUT vs AUDIO-ONSET: {near}/{len(dos)} cuts within 0.4s of an audio transient.")
    # MUSIC ENVELOPE
    env=d["env"]; g=np.array(env["grid"]); rms=np.array(env["rms"]); rh=np.array(env["rms_h"])
    # music entrance: first time harmonic energy sustained above 20% of its max for >2s in first 60s
    hmax=rh.max() if rh.max()>0 else 1
    print(f"\nAUDIO ENERGY (RMS x1000), sampled every ~20s:")
    idx=range(0,len(g),40)
    print("  t   : "+" ".join(f"{int(g[i]):>4}" for i in idx))
    print("  all : "+" ".join(f"{int(rms[i]*1000):>4}" for i in idx))
    print("  harm: "+" ".join(f"{int(rh[i]*1000):>4}" for i in idx))
    print(f"  onsets(transients): {d['onsets']}")
    # HOOK shot-by-shot (first 40s)
    print("\nHOOK — SHOT x NARRATION (first 45s):")
    for s in d["shots"]:
        if s["s"]>45: break
        print(f"  [{s['s']:>5}–{s['e']:>5}] {s['dur']:>4}s | {s['text'][:95]}")
    # SHOT DURATION distribution
    durs=[s['dur'] for s in d['shots']]
    print(f"\nSHOT DURATIONS: min={min(durs)} max={max(durs)} median={np.median(durs):.1f} "
          f"mean={np.mean(durs):.1f}  | <=3s:{sum(1 for x in durs if x<=3)} "
          f"3-6s:{sum(1 for x in durs if 3<x<=6)} 6-10s:{sum(1 for x in durs if 6<x<=10)} >10s:{sum(1 for x in durs if x>10)}")

if __name__=="__main__":
    for n in sys.argv[1:]:
        report(n)
