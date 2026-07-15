#!/usr/bin/env python3
"""
Re-mix BODY with REAL sourced audio (replaces placeholders):
  - park-crowd AMBIENCE as the continuous bed (the layer we lacked)  [above music, under dialogue]
  - real dino ROARS / ALARM / CRASH mapped to the actual beats
  - real music (light_playful / dark_tension) per zone, subordinate
Reuses the built body video. -> EPISODE_MASTER_v3.mp4
"""
import subprocess, re
from pathlib import Path
import numpy as np
ROOT=Path("/Users/jefflawrence/Documents/youtube-automation-production")
RCB=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut"; CL=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
AMB=ROOT/"assets/dino_ambience"; SFX=ROOT/"assets/dino_sfx"; MUS=ROOT/"assets/dino_music"
PM=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"; T=PM/"_master"; TM=PM/"_real"; TM.mkdir(parents=True,exist_ok=True)
SR=48000
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
def znum(n): return int(re.sub(r'\D','',n) or 0)
def zone(n):
    return ("Entry" if n<=16 else "Carno" if n<=23 else "Quetzal" if n<=30 else "Aquatic" if n<=42
            else "Utahraptor" if n<=50 else "Herbivores" if n<=58 else "Lunch" if n<=60
            else "TRex" if n<=68 else "Hybrid" if n<=78 else "Climax")
DARKZONES={"TRex","Hybrid","Climax","Utahraptor"}

# body order + new durs + zone spans + cut times
lines=[re.search(r"file '?([^']+)'?",l).group(1) for l in (RCB/"concat_list.txt").read_text().splitlines() if l.startswith("file")]
body=[]
for fn in lines:
    nm=Path(fn).stem; num=znum(nm)
    if nm in("S01","S02","S89") or (nm.startswith("S") and num<=12 and 'b' not in nm and 'c' not in nm): continue
    if (CL/f"{nm}.mp4").exists(): body.append(nm)
tcur=0.0; start={}; cutrel=[]; spans=[]; curz=None; zs=0.0
for shot in body:
    d=dur(T/f"{shot}_r.mp4"); z=zone(znum(shot))
    if z!=curz:
        if curz is not None: spans.append((curz,zs,tcur))
        curz=z; zs=tcur
    start[shot]=tcur; cutrel.append(tcur); tcur+=d
spans.append((curz,zs,tcur)); BLEN=tcur
print(f"body {BLEN:.1f}s")

# --- MUSIC: real light/dark per zone, subordinate (-29 LUFS) ---
segfiles=[]
for i,(z,a,b) in enumerate(spans):
    trk = MUS/"dark_tension.mp3" if z in DARKZONES else MUS/"light_playful.mp3"
    seg=TM/f"z{i}.wav"; d=b-a+(1.2 if i<len(spans)-1 else 0)
    run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(trk),"-t",f"{d}","-af","loudnorm=I=-29:TP=-3:LRA=11",str(seg)])
    segfiles.append(seg)
acc=segfiles[0]
for i in range(1,len(segfiles)):
    nxt=TM/f"acc{i}.wav"; run(["ffmpeg","-y","-v","error","-i",str(acc),"-i",str(segfiles[i]),"-filter_complex","[0][1]acrossfade=d=1.2:c1=tri:c2=tri[a]","-map","[a]",str(nxt)]); acc=nxt
music=TM/"music.wav"; run(["ffmpeg","-y","-v","error","-i",str(acc),"-af",f"atrim=0:{BLEN}","-ar",str(SR),str(music)])

# --- AMBIENCE: zoo crowd, continuous, ~-27 LUFS (park sounds, above music/under dialogue) ---
amb=TM/"amb.wav"
run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(AMB/"zoo_crowd_atmo.mp3"),"-t",f"{BLEN}","-af","loudnorm=I=-27:TP=-3:LRA=11,afade=t=in:d=1.5",str(amb)])

# --- SFX bed: real hero SFX at mapped beats + subtle whoosh on cuts ---
buf=np.zeros((int((BLEN+3)*SR),2),dtype=np.float32)
def ov(a,at,g):
    i=int(at*SR); n=min(len(a),len(buf)-i)
    if i>=0 and n>0: buf[i:i+n]+=a[:n]*g
WH=[dec(SFX.parent/"sfx"/f) if (SFX/f).exists() else None for f in []]  # placeholder
WHOOSH=[dec(ROOT/"assets/sfx"/f"whoosh_0{n}_loud.wav") for n in (1,2,3,4,5)]
R_TREX=dec(SFX/"roar_trex.mp3"); R_GEN=dec(SFX/"roar_generic.mp3"); R_MON=dec(SFX/"roar_monster.mp3")
ALARM=dec(SFX/"alarm_emergency.mp3"); CRASH=dec(SFX/"crash_debris.mp3"); BOOM=dec(SFX/"impact_boom.mp3")
# subtle whoosh on each cut
for i,ct in enumerate(cutrel):
    if i==0: continue
    ov(WHOOSH[i%5],max(0,ct-0.05),0.13)
# hero SFX mapped to shots (offset into the clip where the beat lands)
HERO=[("S65",R_GEN,0.55,0.4),("S67",R_TREX,0.7,0.5),("S71",R_MON,0.5,0.6),("S75",R_MON,0.6,1.0),
      ("S38",BOOM,0.55,1.4),("S78",CRASH,0.65,0.3),("S82",CRASH,0.6,0.3),("S85",R_TREX,0.55,0.3),
      ("S88",BOOM,0.6,0.3),("S48",R_GEN,0.4,0.2)]
for shot,a,g,off in HERO:
    if shot in start: ov(a, start[shot]+off, g)
# emergency alarm under the climax (from S79), low + steady
if "S79" in start: ov(ALARM, start["S79"], 0.28)
sfx=TM/"sfx.wav"; enc(buf,sfx)

# --- MIX: native(fg) + ambience + music(ducked) + sfx, limited ---
baud=TM/"body_audio.wav"
run(["ffmpeg","-y","-v","error","-i",str(T/"body_native.m4a"),"-i",str(amb),"-i",str(music),"-i",str(sfx),
     "-filter_complex",
     "[0:a]asplit=2[nmix][nkey];"
     "[2:a][nkey]sidechaincompress=threshold=0.05:ratio=4:attack=25:release=400[musd];"
     "[nmix][1:a][musd][3:a]amix=inputs=4:normalize=0:dropout_transition=0[pre];[pre]alimiter=limit=0.95[out]",
     "-map","[out]",str(baud)])
bstyled=TM/"body_styled.mp4"; run(["ffmpeg","-y","-v","error","-i",str(T/"body_v.mp4"),"-i",str(baud),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(bstyled)])

def norm(src,out): run(["ffmpeg","-y","-v","error","-i",str(src),*ENC,"-vf","scale=1264:720,setsar=1","-c:a","aac","-b:a","192k",str(out)])
bN=TM/"body_n.mp4"; norm(bstyled,bN)
iN=T/"intro_n.mp4"; eN=T/"ec_n.mp4"
flist=TM/"flist.txt"; flist.write_text("".join(f"file '{p}'\n" for p in (iN,bN,eN)))
fv=TM/"final_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(flist),"-map","0:v","-c:v","copy","-an",str(fv)])
fa=TM/"final_a.m4a"; run(["ffmpeg","-y","-v","error","-i",str(iN),"-i",str(bN),"-i",str(eN),"-filter_complex","[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(fa)])
MASTER=PM/"EPISODE_MASTER_v3.mp4"; run(["ffmpeg","-y","-v","error","-i",str(fv),"-i",str(fa),"-map","0:v","-map","1:a","-c","copy",str(MASTER)])
print(f"EPISODE_MASTER_v3: {dur(MASTER):.1f}s  {MASTER.stat().st_size//1024//1024}MB")
