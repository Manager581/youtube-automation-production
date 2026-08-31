#!/usr/bin/env python3
"""Per-video forensic extraction: cuts, audio envelopes, cut/narration/audio alignment."""
import sys, os, json, subprocess, math
import numpy as np
import librosa

SCRATCH = os.path.dirname(os.path.abspath(__file__))

def ffprobe_dur(path):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","default=noprint_wrappers=1:nokey=1",path],
                         capture_output=True,text=True).stdout.strip()
    return float(out)

def scene_scores(path):
    """Return list of (pts_time, scene_score) for frames with scene>0.05."""
    cmd = ["ffmpeg","-i",path,"-vf","select='gt(scene,0.05)',metadata=mode=print:file=-",
           "-an","-f","null","-"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    txt = p.stderr + p.stdout
    times=[]; scores=[]
    cur_t=None
    for line in txt.splitlines():
        line=line.strip()
        if line.startswith("frame:") and "pts_time:" in line:
            try: cur_t=float(line.split("pts_time:")[1].split()[0])
            except: cur_t=None
        elif "lavfi.scene_score" in line and cur_t is not None:
            try:
                sc=float(line.split("=")[1])
                times.append(cur_t); scores.append(sc)
            except: pass
    return list(zip(times,scores))

def detect_cuts(scenes, thr=0.4, min_gap=1.0):
    """Hard cuts: scene score above thr, merged within min_gap."""
    cuts=[]
    for t,s in scenes:
        if s>=thr:
            if not cuts or (t-cuts[-1])>=min_gap:
                cuts.append(round(t,3))
    return cuts

def audio_features(path, sr=22050):
    y,_ = librosa.load(path, sr=sr, mono=True)
    dur=len(y)/sr
    hop=512
    # RMS loudness
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    t_rms = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    # HPSS: harmonic ~ music/voice tone; percussive ~ transients/SFX/drums
    yh, yp = librosa.effects.hpss(y)
    rms_h = librosa.feature.rms(y=yh, hop_length=hop)[0]
    rms_p = librosa.feature.rms(y=yp, hop_length=hop)[0]
    # Onset envelope + onsets (transients: SFX, musical hits)
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onsets = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr, hop_length=hop,
                                         units='time', backtrack=False, delta=0.6, wait=10)
    return dict(dur=dur, sr=sr, hop=hop,
                t=t_rms.tolist(), rms=rms.tolist(), rms_h=rms_h.tolist(), rms_p=rms_p.tolist(),
                oenv=oenv.tolist(), onsets=[round(float(x),3) for x in onsets])

def load_words(wordts_json):
    if not os.path.exists(wordts_json): return None
    d=json.load(open(wordts_json))
    words=[]
    for seg in d.get("segments",[]):
        for w in seg.get("words",[]):
            words.append(dict(w=w.get("word","").strip(), s=w.get("start"), e=w.get("end")))
    return [w for w in words if w["s"] is not None]

def analyze(name, video, wordts_json=None):
    dur=ffprobe_dur(video)
    # audio
    wav=os.path.join(SCRATCH,f"_af_{name}.wav")
    subprocess.run(["ffmpeg","-y","-i",video,"-ac","1","-ar","22050",wav,"-loglevel","error"])
    af=audio_features(wav)
    # cuts
    scenes=scene_scores(video)
    # adaptive threshold: pick so median shot len is 3-8s if possible
    # (2026-08-31: code now matches this comment. The old tie-break minimized |avg-5.0| only,
    #  which sat on a knife edge — a re-encode of BEST flipped it 0.40->0.35 by a 0.03 margin,
    #  128 cuts vs the recorded 80, silently failing 2 style gates. Median-in-band first,
    #  then closest avg, reproduces the recorded reference measurements.)
    best=None
    for thr in [0.30,0.35,0.40,0.45,0.50,0.55,0.60]:
        cuts=detect_cuts(scenes,thr=thr,min_gap=0.8)
        n=len(cuts)
        if n>=1:
            avg=dur/(n+1)
            durs=[b-a for a,b in zip([0.0]+cuts,cuts+[dur])]
            durs_s=sorted(durs); med=durs_s[len(durs_s)//2]
            med_ok=3.0<=med<=8.0
            key=(not med_ok, abs(avg-5.0))   # in-band medians beat out-of-band; then closest avg
            if best is None or key<best[4]:
                best=(thr,cuts,avg,n,key)
    if best is not None:
        best=best[:4]
    if best is None:  # no cut at any threshold (single continuous take) -> treat as one shot
        best=(0.30,[],dur,0)
    thr,cuts,avg,n = best
    shots=[]
    bounds=[0.0]+cuts+[dur]
    words=load_words(wordts_json) if wordts_json else None
    for i in range(len(bounds)-1):
        s,e=bounds[i],bounds[i+1]
        txt=""
        if words:
            txt=" ".join(w["w"] for w in words if w["s"]>=s-0.2 and w["s"]<e-0.2)
        shots.append(dict(i=i,s=round(s,2),e=round(e,2),dur=round(e-s,2),text=txt.strip()))
    # cut alignment: for each cut, nearest word-start and nearest audio onset
    aligns=[]
    if words:
        wstarts=np.array([w["s"] for w in words])
    onarr=np.array(af["onsets"]) if af["onsets"] else np.array([])
    for c in cuts:
        rec={"cut":c}
        if words is not None and len(wstarts):
            j=int(np.argmin(np.abs(wstarts-c)))
            rec["d_word"]=round(float(wstarts[j]-c),2)  # + means word starts after cut
            rec["word"]=words[j]["w"]
        if len(onarr):
            k=int(np.argmin(np.abs(onarr-c)))
            rec["d_onset"]=round(float(onarr[k]-c),2)
        aligns.append(rec)
    # downsample envelopes to 0.5s grid for compactness
    grid=np.arange(0,dur,0.5)
    def rs(arr):
        ta=np.array(af["t"]); a=np.array(arr)
        return [round(float(np.interp(g,ta,a)),4) for g in grid]
    env=dict(grid=[round(float(g),2) for g in grid],
             rms=rs(af["rms"]), rms_h=rs(af["rms_h"]), rms_p=rs(af["rms_p"]))
    result=dict(name=name, dur=round(dur,2), cut_threshold=thr, num_cuts=len(cuts),
                mean_shot=round(avg,2), cuts=cuts, shots=shots, aligns=aligns,
                onsets=af["onsets"], env=env)
    os.remove(wav)
    return result

if __name__=="__main__":
    jobs=[]
    for a in sys.argv[1:]:
        # format name:videopath:wordtsjson(optional)
        parts=a.split(":")
        name=parts[0]; video=parts[1]; wj=parts[2] if len(parts)>2 else None
        r=analyze(name,video,wj)
        outp=os.path.join(SCRATCH,f"forensics_{name}.json")
        json.dump(r,open(outp,"w"),indent=1)
        print(f"{name}: dur={r['dur']}s cuts={r['num_cuts']} mean_shot={r['mean_shot']}s thr={r['cut_threshold']} onsets={len(r['onsets'])}")
