#!/usr/bin/env python3
"""
Body cut-rhythm PROTOTYPE — Carnotaurus zone (S17-S23), audio-safe.
3 techniques, none touch the dialogue:
  - TRIM dead tails (host stopped talking; the 6s hold is the metronome)
  - PUNCH-IN at a speech pause (zoom the SAME clip -> audio is continuous)
  - CUTAWAY (show the creature for ~1.2s while the line keeps playing under it)
Output: carno_RECUT.mp4 vs carno_CURRENT.mp4  (A/B).
"""
import subprocess
from pathlib import Path
ROOT=Path("/Users/jefflawrence/Documents/youtube-automation-production")
CL=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
RC=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut/rough_cut_v6.mp4"
PM=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"; T=PM/"_carno"; T.mkdir(parents=True,exist_ok=True)
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print("ERR",c[:6],"\n",r.stderr[-1400:]); raise SystemExit(1)
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip() or 0)
ENC=["-r","24","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-video_track_timescale","24000"]

def vseg(clip,ss,t,out,zoom=1.0):
    vf=(f"scale={round(1264*zoom/2)*2}:{round(720*zoom/2)*2},crop=1264:720,setsar=1"
        if zoom!=1.0 else "scale=1264:720,setsar=1")
    run(["ffmpeg","-y","-v","error","-ss",f"{ss}","-t",f"{t}","-i",str(clip),"-an","-vf",vf,*ENC,str(out)])

# recipe: (shot, trim_end, opts)   opts: punch_at/zoom  OR  cutaway=(ins_at,ins_dur,srcShot,srcOff)
CARNO=[
 ("S17",4.0,{"punch_at":2.64,"zoom":1.30}),
 ("S18",6.0,{"punch_at":3.49,"zoom":1.25}),
 ("S19",3.3,{"punch_at":1.81,"zoom":1.35}),
 ("S20",3.2,{}),
 ("S21",5.6,{"cutaway":(3.0,1.2,"S19",1.0)}),
 ("S22",5.5,{"punch_at":3.05,"zoom":1.25}),
 ("S23",5.0,{"punch_at":2.98,"zoom":1.30}),
]

clip_files=[]; shotlog=[]
for i,(shot,te,o) in enumerate(CARNO):
    clip=CL/f"{shot}.mp4"; segs=[]
    if "cutaway" in o:
        ia,idur,src,soff=o["cutaway"]
        s0=T/f"{i}_a.mp4"; vseg(clip,0,ia,s0); segs.append(s0)
        s1=T/f"{i}_ins.mp4"; vseg(CL/f"{src}.mp4",soff,idur,s1); segs.append(s1)
        s2=T/f"{i}_b.mp4"; vseg(clip,ia+idur,te-(ia+idur),s2); segs.append(s2)
        shotlog += [(shot,ia),("cut→"+src,idur),(shot+"'",te-(ia+idur))]
    elif "punch_at" in o:
        pa=o["punch_at"]
        s0=T/f"{i}_w.mp4"; vseg(clip,0,pa,s0); segs.append(s0)
        s1=T/f"{i}_p.mp4"; vseg(clip,pa,te-pa,s1,zoom=o["zoom"]); segs.append(s1)
        shotlog += [(shot,pa),(shot+"�push",te-pa)]
    else:
        s0=T/f"{i}_f.mp4"; vseg(clip,0,te,s0); segs.append(s0)
        shotlog += [(shot,te)]
    # concat video segs
    lst=T/f"{i}_list.txt"; lst.write_text("".join(f"file '{s}'\n" for s in segs))
    cv=T/f"{i}_vid.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(cv)])
    # native audio, trimmed to te (dialogue preserved, dead tail dropped)
    ca=T/f"{i}_aud.m4a"; run(["ffmpeg","-y","-v","error","-t",f"{te}","-i",str(clip),"-vn","-c:a","aac","-b:a","192k",str(ca)])
    cr=T/f"{i}_recut.mp4"; run(["ffmpeg","-y","-v","error","-i",str(cv),"-i",str(ca),"-map","0:v","-map","1:a","-c:v","copy","-c:a","copy","-shortest",str(cr)])
    clip_files.append(cr)

# concat zone (video copy, audio via filter to avoid the AAC-gap bug)
fl=T/"zone_list.txt"; fl.write_text("".join(f"file '{f}'\n" for f in clip_files))
zv=T/"zone_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(fl),"-map","0:v","-c:v","copy","-an",str(zv)])
n=len(clip_files)
ain=[]; aff=[]
for j,f in enumerate(clip_files): ain+=["-i",str(f)]; aff.append(f"[{j}:a]")
za=T/"zone_a.m4a"
run(["ffmpeg","-y","-v","error",*ain,"-filter_complex","".join(aff)+f"concat=n={n}:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(za)])
recut=PM/"carno_RECUT.mp4"
run(["ffmpeg","-y","-v","error","-i",str(zv),"-i",str(za),"-map","0:v","-map","1:a","-c","copy",str(recut)])

# A/B: current zone (60.8 -> 103.0)
cur=PM/"carno_CURRENT.mp4"
run(["ffmpeg","-y","-v","error","-ss","60.8","-to","103.0","-i",str(RC),*ENC,"-c:a","aac","-b:a","192k",str(cur)])

print(f"CURRENT: {dur(cur):.1f}s (7 shots x ~6s = flat)")
print(f"RECUT:   {dur(recut):.1f}s ({len(shotlog)} shots)")
print("recut shot lengths:")
for name,d in shotlog: print(f"  {name:12} {d:4.2f}s")
