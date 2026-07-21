#!/usr/bin/env python3
"""
REXCAPED variant master — light re-edit of the published v7 for the second
channel (owner-approved scope 2026-07-21):
  - intro_REXCAPED.mp4 (Sik-matched cold open) instead of intro_RECUT
  - variant punch/hold pattern: 8 of 23 punches demoted to holds, the kept 15
    re-timed to a DIFFERENT pause (body_pauses.json) + zoom varied — dialogue
    and shot order untouched, so total body duration is unchanged
  - light zones get candidates/hidden-treasure.mp3 (v7: light_cinematic);
    dark zones keep dark_tension (only dark option)
  - ambience bed rotation flipped; whoosh rotation offset +2
  - end card rebuilt on the DINO ZOO logo card (v7: text on black)

NON-DESTRUCTIVE: reads _master/ segments READ-ONLY, rebuilds only changed
shots into _master_rex/, all intermediates in _rex/, writes
EPISODE_MASTER_REXCAPED.mp4. v7 and its dirs are never written.

Cut logic (vseg/punch/hold/audio), dialogue-forward chain, bed levels and
HERO SFX map are copied VERBATIM from build_master.py / build_remix_real.py —
this is a parameter variant, not a new pipeline.
"""
import subprocess, re, json
from pathlib import Path
import numpy as np
ROOT=Path("/Users/jefflawrence/Documents/youtube-automation-production")
CL=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
RCB=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut"
VO=ROOT/"audio/dinoverse_omega"; SFXD=ROOT/"assets/sfx"
AMB=ROOT/"assets/dino_ambience"; SFX=ROOT/"assets/dino_sfx"; MUS=ROOT/"assets/dino_music"
MUSD=ROOT/"audio/breaking_law/music_tracks"
PM=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"
T=PM/"_master"                              # v7 segments — READ-ONLY
TR=PM/"_master_rex"; TR.mkdir(parents=True,exist_ok=True)   # variant segments
TM=PM/"_rex"; TM.mkdir(parents=True,exist_ok=True)          # variant intermediates
LOGO=ROOT/"assets/dinoverse/dino_zoo_logo_card.png"
SR=48000; GREEN="0x2ecc40"
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print("ERR",c[:6],"\n",r.stderr[-1400:]); raise SystemExit(1)
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip() or 0)
def dec(p):
    raw=subprocess.run(["ffmpeg","-v","error","-i",str(p),"-f","f32le","-ar",str(SR),"-ac","2","-"],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32).reshape(-1,2).copy()
def enc(a,p):
    pr=subprocess.Popen(["ffmpeg","-y","-v","error","-f","f32le","-ar",str(SR),"-ac","2","-i","-",str(p)],stdin=subprocess.PIPE)
    pr.communicate(np.clip(a,-1,1).astype(np.float32).tobytes())
ENC=["-r","24","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-video_track_timescale","24000"]
def ev(x): return int(round(x/2)*2)
def vseg(clip,ss,t,out,zoom=1.0,xp=0.5,yp=0.5):     # verbatim from build_master.py
    if zoom<=1.001: vf="scale=1264:720,setsar=1"
    else:
        sw,sh=ev(1264*zoom),ev(720*zoom)
        ox=min(max(ev(xp*sw-632),0),sw-1264); oy=min(max(ev(yp*sh-360),0),sh-720)
        vf=f"scale={sw}:{sh},crop=1264:720:{ox}:{oy},setsar=1"
    run(["ffmpeg","-y","-v","error","-ss",f"{ss}","-t",f"{t}","-i",str(clip),"-an","-vf",vf,*ENC,str(out)])
def _l(f):
    r=subprocess.run(["ffmpeg","-i",str(f),"-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr
    m=[x for x in r.splitlines() if "I:" in x and "LUFS" in x]; return float(m[-1].split("I:")[1].split("LUFS")[0]) if m else 0

REC=json.loads((PM/"motivated_recipes.json").read_text())
POJ=json.loads((PM/"body_pauses.json").read_text())
def znum(n): return int(re.sub(r'\D','',n) or 0)
def zone(n):
    return ("Entry" if n<=16 else "Carno" if n<=23 else "Quetzal" if n<=30 else "Aquatic" if n<=42
            else "Utahraptor" if n<=50 else "Herbivores" if n<=58 else "Lunch" if n<=60
            else "TRex" if n<=68 else "Hybrid" if n<=78 else "Climax")
lines=[re.search(r"file '?([^']+)'?",l).group(1) for l in (RCB/"concat_list.txt").read_text().splitlines() if l.startswith("file")]
body=[]
for fn in lines:
    nm=Path(fn).stem; num=znum(nm)
    if nm in("S01","S02","S89") or (nm.startswith("S") and num<=12 and 'b' not in nm and 'c' not in nm): continue
    if (CL/f"{nm}.mp4").exists(): body.append(nm)

# ---------- 1) derive the VARIANT recipes (deterministic, no randomness) ----------
punch_ids=sorted([k for k,v in REC.items() if v.get("technique")=="punch"])
DEMOTE={punch_ids[i] for i in range(0,len(punch_ids),3)}     # every 3rd -> hold (8 of 23)
# QA wf_c48f688d: S62's 1.33x reframe at xp .43 bisected the 2nd ranger's face
# at the right edge — pull the aim left to keep her whole (target still centered)
OVERRIDE={"S62":{"xp":0.35}}
VREC={}; changed={}
for shot,r in REC.items():
    v=dict(r)
    if r.get("technique")=="punch":
        info=POJ.get(shot,{}); cd=info.get("clip_dur",6.0)
        se=info.get("speech_end",0)
        te=min(max(r.get("trim_end",(se+0.3 if se>0 else cd)), se if se>0 else 1.0), cd)
        if shot in DEMOTE:
            v["technique"]="hold"; v["cut_at"]=0; v["zoom"]=1; v["xp"]=0.5; v["yp"]=0.5
            v["rationale"]="[REXCAPED] demoted to hold for variant cut pattern"
            changed[shot]="demoted"
        else:
            # re-time to a DIFFERENT pause; vary zoom; keep the authored aim
            ca=r.get("cut_at",0)
            cands=[p for p in info.get("pauses",[]) if 0.6<p<te-0.6 and abs(p-ca)>=0.25]
            if cands:
                v["cut_at"]=min(cands,key=lambda p:abs(p-ca))
            z=r.get("zoom",1.25)
            v["zoom"]=min(max(z+0.08 if z<=1.30 else z-0.08,1.15),1.42)
            v.update(OVERRIDE.get(shot,{}))
            if v["cut_at"]!=ca or abs(v["zoom"]-z)>0.001:
                v["rationale"]=f"[REXCAPED] re-timed {ca}->{v['cut_at']} zoom {z}->{v['zoom']:.2f}"
                changed[shot]="retimed"
    VREC[shot]=v
(PM/"rexcaped_recipes.json").write_text(json.dumps(VREC,indent=1))
print(f"variant recipes: {len(changed)} changed ({sum(1 for x in changed.values() if x=='demoted')} demoted, "
      f"{sum(1 for x in changed.values() if x=='retimed')} re-timed)")

# ---------- 2) rebuild ONLY changed shots into _master_rex/ ----------
for shot,why in sorted(changed.items()):
    clip=CL/f"{shot}.mp4"; cd=dur(clip)
    info=POJ.get(shot,{}); se=info.get("speech_end",0)
    r=VREC[shot]
    te=min(max(r.get("trim_end",(se+0.3 if se>0 else cd)), se if se>0 else 1.0), cd)
    tech=r["technique"]; segs=[]
    if tech=="punch":
        ca=r["cut_at"]; zoom=min(max(r["zoom"],1.1),1.45)
        xp=min(max(r["xp"],0.12),0.88); yp=min(max(r["yp"],0.12),0.88)
        if not (0.5<ca<te-0.5): tech="hold"
        else:
            a=TR/f"{shot}_w.mp4"; vseg(clip,0,ca,a)
            b=TR/f"{shot}_p.mp4"; vseg(clip,ca,te-ca,b,zoom=zoom,xp=xp,yp=yp)
            segs=[a,b]
    if tech!="punch":
        s=TR/f"{shot}_f.mp4"; vseg(clip,0,te,s); segs=[s]
    lst=TR/f"{shot}_l.txt"; lst.write_text("".join(f"file '{s}'\n" for s in segs))
    cv=TR/f"{shot}_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(cv)])
    ca_=TR/f"{shot}_a.m4a"; run(["ffmpeg","-y","-v","error","-t",f"{te}","-i",str(clip),"-vn","-c:a","aac","-b:a","192k",str(ca_)])
    cr=TR/f"{shot}_r.mp4"; run(["ffmpeg","-y","-v","error","-i",str(cv),"-i",str(ca_),"-map","0:v","-map","1:a","-c","copy","-shortest",str(cr)])
    print(f"  rebuilt {shot} ({why})")

# ---------- 3) concat variant body (mixed sources) + timeline ----------
clip_files=[(TR if s in changed else T)/f"{s}_r.mp4" for s in body]
missing=[f for f in clip_files if not f.exists()]
if missing: print("MISSING SEGMENTS:",missing[:5]); raise SystemExit(1)
tcur=0.0; start={}; cutrel=[]; spans=[]; curz=None; zs=0.0
for shot,f in zip(body,clip_files):
    d=dur(f); z=zone(znum(shot))
    if z!=curz:
        if curz is not None: spans.append((curz,zs,tcur))
        curz=z; zs=tcur
    start[shot]=tcur; cutrel.append(tcur); tcur+=d
spans.append((curz,zs,tcur)); BLEN=tcur
print(f"variant body {BLEN:.1f}s ({len(body)} shots)")
bl=TM/"bl.txt"; bl.write_text("".join(f"file '{f}'\n" for f in clip_files))
bvid=TM/"body_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(bl),"-map","0:v","-c:v","copy","-an",str(bvid)])
ain=[];aff=[]
for j,f in enumerate(clip_files): ain+=["-i",str(f)]; aff.append(f"[{j}:a]")
bnat=TM/"body_native.m4a"; run(["ffmpeg","-y","-v","error",*ain,"-filter_complex","".join(aff)+f"concat=n={len(clip_files)}:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(bnat)])

# ---------- 4) MUSIC: variant light bed (hidden-treasure), same levels ----------
DARKZONES={"TRex","Hybrid","Climax","Utahraptor"}
LIGHT=MUS/"candidates/hidden-treasure.mp3"          # v7 used light_cinematic
segfiles=[]
for i,(z,a,b) in enumerate(spans):
    trk = MUS/"dark_tension.mp3" if z in DARKZONES else LIGHT
    seg=TM/f"z{i}.wav"; d=b-a+(1.2 if i<len(spans)-1 else 0)
    run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(trk),"-t",f"{d}","-af","loudnorm=I=-37:TP=-6:LRA=11",str(seg)])
    segfiles.append(seg)
acc=segfiles[0]
for i in range(1,len(segfiles)):
    nxt=TM/f"acc{i}.wav"; run(["ffmpeg","-y","-v","error","-i",str(acc),"-i",str(segfiles[i]),"-filter_complex","[0][1]acrossfade=d=1.2:c1=tri:c2=tri[a]","-map","[a]",str(nxt)]); acc=nxt
music=TM/"music.wav"; run(["ffmpeg","-y","-v","error","-i",str(acc),"-af",f"atrim=0:{BLEN}","-ar",str(SR),str(music)])

# ---------- 5) AMBIENCE: same beds, rotation FLIPPED ----------
BEDS=["crowd_b.mp3","crowd_a.mp3"]                  # v7 started with crowd_a
abits=[]; tacc=0.0; k=0
while tacc < BLEN+2:
    src=AMB/BEDS[k%2]; d=dur(src)
    seg=TM/f"amb{k}.wav"
    run(["ffmpeg","-y","-v","error","-i",str(src),"-af","loudnorm=I=-33:TP=-6:LRA=11",str(seg)])
    abits.append(seg); tacc+=d-1.2; k+=1
accA=abits[0]
for i in range(1,len(abits)):
    nx=TM/f"ambacc{i}.wav"; run(["ffmpeg","-y","-v","error","-i",str(accA),"-i",str(abits[i]),"-filter_complex","[0][1]acrossfade=d=1.2:c1=tri:c2=tri[a]","-map","[a]",str(nx)]); accA=nx
amb=TM/"amb.wav"
run(["ffmpeg","-y","-v","error","-i",str(accA),"-af",f"atrim=0:{BLEN},afade=t=in:d=1.5","-ar",str(SR),str(amb)])

# ---------- 6) SFX: whoosh rotation +2; HERO map verbatim (diegetic beats) ----------
buf=np.zeros((int((BLEN+3)*SR),2),dtype=np.float32)
def ov(a,at,g):
    i=int(at*SR); n=min(len(a),len(buf)-i)
    if i>=0 and n>0: buf[i:i+n]+=a[:n]*g
WHOOSH=[dec(ROOT/"assets/sfx"/f"whoosh_0{n}_loud.wav") for n in (1,2,3,4,5)]
R_TREX=dec(SFX/"roar_trex_victory.mp3"); R_GEN=dec(SFX/"roar_generic.mp3"); R_MON=dec(SFX/"roar_monster.mp3")
ALARM=dec(SFX/"alarm_emergency.mp3"); CRASH=dec(SFX/"crash_debris.mp3"); BOOM=dec(SFX/"impact_boom.mp3")
for i,ct in enumerate(cutrel):
    if i==0: continue
    ov(WHOOSH[(i+2)%5],max(0,ct-0.05),0.13)
HERO=[("S65",R_GEN,0.55,0.4),("S67",R_TREX,0.7,0.5),("S71",R_MON,0.5,0.6),("S75",R_MON,0.6,1.0),
      ("S38",BOOM,0.55,1.4),("S78",CRASH,0.65,0.3),("S82",CRASH,0.6,0.3),("S85",R_TREX,0.55,0.3),
      ("S88",BOOM,0.6,0.3),("S48",R_GEN,0.4,0.2)]
for shot,a,g,off in HERO:
    if shot in start: ov(a, start[shot]+off, g)
if "S79" in start: ov(ALARM, start["S79"], 0.28)
sfx=TM/"sfx.wav"; enc(buf,sfx)

# ---------- 7) dialogue-forward chain (verbatim, on the VARIANT native) ----------
DLG_I=-12.0
nat0=TM/"native_comp.wav"
run(["ffmpeg","-y","-v","error","-i",str(bnat),"-af",
     "highpass=f=70,acompressor=threshold=-26dB:ratio=3:attack=8:release=200:knee=4:makeup=2dB",
     "-ar",str(SR),str(nat0)])
gN=DLG_I-_l(nat0)
natF=TM/"native_fwd.wav"
run(["ffmpeg","-y","-v","error","-i",str(nat0),"-af",f"volume={gN:.1f}dB,alimiter=limit=0.98:level=disabled","-ar",str(SR),str(natF)])
print(f"dialogue: {_l(natF):.1f} LUFS (target {DLG_I}, gain {gN:+.1f}dB)")
baud=TM/"body_audio.wav"
run(["ffmpeg","-y","-v","error","-i",str(natF),"-i",str(amb),"-i",str(music),"-i",str(sfx),
     "-filter_complex",
     "[0:a]asplit=2[nmix][nkey];"
     "[2:a][nkey]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=450[musd];"
     "[nmix][1:a][musd][3:a]amix=inputs=4:normalize=0:dropout_transition=0[pre];[pre]alimiter=limit=0.95[out]",
     "-map","[out]",str(baud)])
bstyled=TM/"body_styled.mp4"; run(["ffmpeg","-y","-v","error","-i",str(bvid),"-i",str(baud),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(bstyled)])

# ---------- 8) END CARD variant: VO on the DINO ZOO logo card (v7: black) ----------
gf=dec(VO/"gf_s89_closer.wav"); lk=dec(VO/"luke_s89_cta.wav")
ECLEN=1.0+len(gf)/SR+0.6+len(lk)/SR+1.4
ea=np.zeros((int(ECLEN*SR),2),dtype=np.float32)
def put(a,at,g=1.0):
    i=int(at*SR); n=min(len(a),len(ea)-i); ea[i:i+n]+=a[:n]*g
put(gf,1.0); put(lk,1.0+len(gf)/SR+0.6)
stg=dec(MUSD/"track_04_dark.wav")[:int(ECLEN*SR)]; put(stg*(np.linspace(1,0,len(stg)).reshape(-1,1)**1.5),0,0.18)
ecw=TM/"ec.wav"; enc(ea,ecw)
vf=(f"scale=1264:720,setsar=1,"
    f"drawtext=text='Comment which dino you’d survive.':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=h*0.80:font=Helvetica,"
    f"drawtext=text='Subscribe — part two if this hits.':fontcolor={GREEN}:fontsize=34:x=(w-text_w)/2:y=h*0.89:font=Helvetica")
ec=TM/"endcard.mp4"; run(["ffmpeg","-y","-v","error","-loop","1","-t",f"{ECLEN}","-i",str(LOGO),"-i",str(ecw),
     "-vf",vf,"-map","0:v","-map","1:a",*ENC,"-c:a","aac","-b:a","192k","-shortest",str(ec)])
# end-card dialogue-forward leveling (verbatim treatment)
eS=TM/"ec_fwd_a.wav"
run(["ffmpeg","-y","-v","error","-i",str(ec),"-af",
     "acompressor=threshold=-26dB:ratio=3:attack=8:release=200:knee=4:makeup=2dB","-ar",str(SR),str(eS)])
gE=(DLG_I-1.0)-_l(eS)
eS2=TM/"ec_fwd.wav"; run(["ffmpeg","-y","-v","error","-i",str(eS),"-af",f"volume={gE:.1f}dB,alimiter=limit=0.95","-ar",str(SR),str(eS2)])
print(f"end card: {_l(eS2):.1f} LUFS (gain {gE:+.1f}dB)")

# ---------- 9) final concat: REXCAPED intro + variant body + variant card ----------
def norm(src,out): run(["ffmpeg","-y","-v","error","-i",str(src),*ENC,"-vf","scale=1264:720,setsar=1","-c:a","aac","-b:a","192k",str(out)])
iN=TM/"intro_n.mp4"; norm(PM/"intro_REXCAPED.mp4",iN)
bN=TM/"body_n.mp4"; norm(bstyled,bN)
eN=TM/"ec_fwd.mp4"; run(["ffmpeg","-y","-v","error","-i",str(ec),"-i",str(eS2),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(TM/"ec_lv.mp4")])
norm(TM/"ec_lv.mp4",eN)
flist=TM/"flist.txt"; flist.write_text("".join(f"file '{p}'\n" for p in (iN,bN,eN)))
fv=TM/"final_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(flist),"-map","0:v","-c:v","copy","-an",str(fv)])
fa=TM/"final_a.m4a"; run(["ffmpeg","-y","-v","error","-i",str(iN),"-i",str(bN),"-i",str(eN),"-filter_complex","[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(fa)])
MASTER=PM/"EPISODE_MASTER_REXCAPED.mp4"; run(["ffmpeg","-y","-v","error","-i",str(fv),"-i",str(fa),"-map","0:v","-map","1:a","-c","copy",str(MASTER)])
print(f"\nEPISODE_MASTER_REXCAPED: {dur(MASTER):.1f}s ({int(dur(MASTER))//60}:{dur(MASTER)%60:04.1f})  {MASTER.stat().st_size//1024//1024}MB")
print(f"beds: ambience {_l(amb):.1f} LUFS, music {_l(music):.1f} LUFS")
