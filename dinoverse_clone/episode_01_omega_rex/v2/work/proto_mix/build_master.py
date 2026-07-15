#!/usr/bin/env python3
"""
FULL MASTER build from motivated recipes.
  motivated body (per-clip trim + aimed punch/hold, native dialogue kept)
  + recut intro  + music bed (light->dark)  + SFX on cuts  + end-card VO.
Recipes: proto_mix/motivated_recipes.json  {shot:{technique,trim_end,cut_at,zoom,xp,yp}}
Missing/invalid recipe -> safe fallback (hold, trimmed to speech+0.3 or full).
"""
import subprocess, re, json
from pathlib import Path
import numpy as np
ROOT=Path("/Users/jefflawrence/Documents/youtube-automation-production")
CL=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
RCB=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut"
VO=ROOT/"audio/dinoverse_omega"; SFXD=ROOT/"assets/sfx"; MUSD=ROOT/"audio/breaking_law/music_tracks"
PM=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"; T=PM/"_master"; T.mkdir(parents=True,exist_ok=True)
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
def vseg(clip,ss,t,out,zoom=1.0,xp=0.5,yp=0.5):
    if zoom<=1.001: vf="scale=1264:720,setsar=1"
    else:
        sw,sh=ev(1264*zoom),ev(720*zoom)
        ox=min(max(ev(xp*sw-632),0),sw-1264); oy=min(max(ev(yp*sh-360),0),sh-720)
        vf=f"scale={sw}:{sh},crop=1264:720:{ox}:{oy},setsar=1"
    run(["ffmpeg","-y","-v","error","-ss",f"{ss}","-t",f"{t}","-i",str(clip),"-an","-vf",vf,*ENC,str(out)])

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

# ---- build each motivated body clip; track new timeline ----
clip_files=[]; cut_rel=[]; zone_start={}; tcur=0.0; log=[]
for shot in body:
    clip=CL/f"{shot}.mp4"; cd=dur(clip)
    info=POJ.get(shot,{}); se=info.get("speech_end",0)
    r=REC.get(shot,{})
    # validate/clamp
    te=r.get("trim_end", (se+0.3 if se>0 else cd)); te=min(max(te, se if se>0 else 1.0), cd)
    tech=r.get("technique","hold")
    segs=[]
    if tech=="punch":
        ca=r.get("cut_at",0); zoom=min(max(r.get("zoom",1.25),1.1),1.45)
        xp=min(max(r.get("xp",0.5),0.12),0.88); yp=min(max(r.get("yp",0.5),0.12),0.88)
        if not (0.5 < ca < te-0.5) or not r.get("aim_ok",True):
            tech="hold"                                   # unsafe cut -> fall back
        else:
            a=T/f"{shot}_w.mp4"; vseg(clip,0,ca,a)
            b=T/f"{shot}_p.mp4"; vseg(clip,ca,te-ca,b,zoom=zoom,xp=xp,yp=yp)
            segs=[a,b]
    if tech!="punch":
        s=T/f"{shot}_f.mp4"; vseg(clip,0,te,s); segs=[s]
    lst=T/f"{shot}_l.txt"; lst.write_text("".join(f"file '{s}'\n" for s in segs))
    cv=T/f"{shot}_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(cv)])
    ca_=T/f"{shot}_a.m4a"; run(["ffmpeg","-y","-v","error","-t",f"{te}","-i",str(clip),"-vn","-c:a","aac","-b:a","192k",str(ca_)])
    cr=T/f"{shot}_r.mp4"; run(["ffmpeg","-y","-v","error","-i",str(cv),"-i",str(ca_),"-map","0:v","-map","1:a","-c","copy","-shortest",str(cr)])
    clip_files.append(cr)
    z=zone(znum(shot)); zone_start.setdefault(z,round(tcur,2))
    cut_rel.append(round(tcur,2)); log.append((shot,tech,round(te,2))); tcur+=dur(cr)
BLEN=tcur
DARK_AT=zone_start["TRex"]
print(f"motivated body: {BLEN:.1f}s ({len(body)} shots)  dark@{DARK_AT:.1f}s")
punches=sum(1 for _,t,_ in log if t=="punch"); print(f"  punches {punches}, holds {len(log)-punches}")

# ---- concat body: video copy + audio via filter (avoid AAC gap bug) ----
bl=T/"bl.txt"; bl.write_text("".join(f"file '{f}'\n" for f in clip_files))
bvid=T/"body_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(bl),"-map","0:v","-c:v","copy","-an",str(bvid)])
ain=[];aff=[]
for j,f in enumerate(clip_files): ain+=["-i",str(f)]; aff.append(f"[{j}:a]")
bnat=T/"body_native.m4a"; run(["ffmpeg","-y","-v","error",*ain,"-filter_complex","".join(aff)+f"concat=n={len(clip_files)}:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(bnat)])

# ---- music bed (light->dark) ----
lenA=DARK_AT; lenB=BLEN-DARK_AT+1.5
mA=T/"mA.wav"; run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(MUSD/"track_03_emotional.wav"),"-t",f"{lenA}","-af","loudnorm=I=-25:TP=-2:LRA=11",str(mA)])
mB=T/"mB.wav"; run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(MUSD/"track_04_dark.wav"),"-t",f"{lenB}","-af","loudnorm=I=-24:TP=-2:LRA=11",str(mB)])
music=T/"music.wav"; run(["ffmpeg","-y","-v","error","-i",str(mA),"-i",str(mB),"-filter_complex","[0][1]acrossfade=d=1.5:c1=tri:c2=tri[a]","-map","[a]",str(music)])

# ---- SFX bed ----
buf=np.zeros((int((BLEN+2)*SR),2),dtype=np.float32)
def ov(a,at,g):
    i=int(at*SR); n=min(len(a),len(buf)-i)
    if i>=0 and n>0: buf[i:i+n]+=a[:n]*g
WH=[dec(SFXD/f"whoosh_0{n}_loud.wav") for n in (1,2,3,4,5)]
IMP=dec(SFXD/"impact_new_loud.wav"); BIMP=dec(SFXD/"body_impact_01_loud.wav"); RUM=dec(SFXD/"rumble_03_loud.wav")
for i,ct in enumerate(cut_rel):
    if i==0: continue
    ov(WH[i%5],max(0,ct-0.05),0.20)
for z,st in zone_start.items():
    if z!="Entry": ov(IMP,st,0.4)
ov(BIMP,zone_start["Climax"],0.5)
tt=DARK_AT
while tt<BLEN-3: ov(RUM,tt,0.15); tt+=len(RUM)/SR*0.9
sfx=T/"sfx.wav"; enc(buf,sfx)

# ---- body mix ----
baud=T/"body_audio.wav"
run(["ffmpeg","-y","-v","error","-i",str(bnat),"-i",str(music),"-i",str(sfx),"-filter_complex",
     "[0:a]asplit=2[nmix][nkey];[1:a][nkey]sidechaincompress=threshold=0.06:ratio=5:attack=20:release=350[musd];"
     "[nmix][musd][2:a]amix=inputs=3:normalize=0:dropout_transition=0[pre];[pre]alimiter=limit=0.95[out]",
     "-map","[out]",str(baud)])
body_styled=T/"body_styled.mp4"; run(["ffmpeg","-y","-v","error","-i",str(bvid),"-i",str(baud),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(body_styled)])

# ---- end card ----
gf=dec(VO/"gf_s89_closer.wav"); lk=dec(VO/"luke_s89_cta.wav")
ECLEN=1.0+len(gf)/SR+0.6+len(lk)/SR+1.4
ea=np.zeros((int(ECLEN*SR),2),dtype=np.float32)
def put(a,at,g=1.0):
    i=int(at*SR); n=min(len(a),len(ea)-i); ea[i:i+n]+=a[:n]*g
put(gf,1.0); put(lk,1.0+len(gf)/SR+0.6)
stg=dec(MUSD/"track_04_dark.wav")[:int(ECLEN*SR)]; put(stg*(np.linspace(1,0,len(stg)).reshape(-1,1)**1.5),0,0.18)
ecw=T/"ec.wav"; enc(ea,ecw)
vf=(f"drawtext=text='Comment which dino you\\'d survive.':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2-40:font=Helvetica,"
    f"drawtext=text='Subscribe — part two if this hits.':fontcolor={GREEN}:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2+40:font=Helvetica")
ec=T/"endcard.mp4"; run(["ffmpeg","-y","-v","error","-f","lavfi","-i",f"color=c=black:s=1264x720:r=24:d={ECLEN}","-i",str(ecw),"-vf",vf,"-map","0:v","-map","1:a",*ENC,"-c:a","aac","-b:a","192k","-shortest",str(ec)])

# ---- normalize + concat intro + body + endcard (audio via filter) ----
def norm(src,out): run(["ffmpeg","-y","-v","error","-i",str(src),*ENC,"-vf","scale=1264:720,setsar=1","-c:a","aac","-b:a","192k",str(out)])
iN=T/"intro_n.mp4"; norm(PM/"intro_RECUT.mp4",iN)
bN=T/"body_n.mp4"; norm(body_styled,bN)
eN=T/"ec_n.mp4"; norm(ec,eN)
flist=T/"flist.txt"; flist.write_text("".join(f"file '{p}'\n" for p in (iN,bN,eN)))
fv=T/"final_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(flist),"-map","0:v","-c:v","copy","-an",str(fv)])
fa=T/"final_a.m4a"; run(["ffmpeg","-y","-v","error","-i",str(iN),"-i",str(bN),"-i",str(eN),"-filter_complex","[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(fa)])
MASTER=PM/"EPISODE_MASTER.mp4"; run(["ffmpeg","-y","-v","error","-i",str(fv),"-i",str(fa),"-map","0:v","-map","1:a","-c","copy",str(MASTER)])
print(f"\nEPISODE_MASTER: {dur(MASTER):.1f}s ({int(dur(MASTER))//60}:{dur(MASTER)%60:04.1f})  {MASTER.stat().st_size//1024//1024}MB")
