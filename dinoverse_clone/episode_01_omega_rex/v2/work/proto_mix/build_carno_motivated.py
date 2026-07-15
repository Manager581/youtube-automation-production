#!/usr/bin/env python3
"""
Carnotaurus zone — MOTIVATED recut (vs the mechanical one).
Every cut is justified by what's on screen + what the line says:
  S17 establishing -> HOLD clean (no punch; let it reveal)
  S18 keeper+baby, GF left -> reaction PUNCH to GF-left on "adorable"
  S19 grown Carno -> PUNCH to head/horns on "look at those horns"
  S20 head at glass -> HOLD (already a tight impact shot)
  S21 mom+baby -> CUTAWAY to horns (S19) on "used those horns to fight"
  S22 two adults facing off -> HOLD standoff, PUNCH clash on the CTA
  S23 GF + "?" sign -> HOLD question, PUNCH GF-left deadpan on the pause
Audio never touched (punch = same clip; cutaway = line plays under it).
"""
import subprocess
from pathlib import Path
ROOT=Path("/Users/jefflawrence/Documents/youtube-automation-production")
CL=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
PM=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"; T=PM/"_carnom"; T.mkdir(parents=True,exist_ok=True)
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print("ERR",c[:6],"\n",r.stderr[-1400:]); raise SystemExit(1)
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip() or 0)
ENC=["-r","24","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-video_track_timescale","24000"]

def ev(x): return int(round(x/2)*2)
def vseg(clip,ss,t,out,zoom=1.0,xp=0.5,yp=0.5):
    if zoom==1.0:
        vf="scale=1264:720,setsar=1"
    else:
        sw,sh=ev(1264*zoom),ev(720*zoom)
        ox=min(max(ev(xp*sw-632),0),sw-1264); oy=min(max(ev(yp*sh-360),0),sh-720)
        vf=f"scale={sw}:{sh},crop=1264:720:{ox}:{oy},setsar=1"
    run(["ffmpeg","-y","-v","error","-ss",f"{ss}","-t",f"{t}","-i",str(clip),"-an","-vf",vf,*ENC,str(out)])

# motivated recipe
# (shot, trim_end, kind, params)
PLAN=[
 ("S17",3.9,"hold",{}),
 ("S18",6.0,"punch",{"at":3.49,"zoom":1.30,"xp":0.22,"yp":0.45}),   # reaction -> GF left
 ("S19",3.3,"punch",{"at":1.81,"zoom":1.35,"xp":0.52,"yp":0.38}),   # -> head/horns
 ("S20",3.2,"hold",{}),                                             # impact hold
 ("S21",5.6,"cutaway",{"at":3.0,"dur":1.2,"src":"S19","soff":0.5}), # -> horns on "fight"
 ("S22",5.5,"punch",{"at":3.05,"zoom":1.22,"xp":0.50,"yp":0.50}),   # clash on CTA
 ("S23",5.0,"hold",{}),   # the joke IS the composition (her deadpan + the "?" sign) -> hold wide
]

clips=[]; log=[]
for i,(shot,te,kind,p) in enumerate(PLAN):
    clip=CL/f"{shot}.mp4"; segs=[]
    if kind=="hold":
        s=T/f"{i}_f.mp4"; vseg(clip,0,te,s); segs=[s]; log.append((shot+" (hold)",te))
    elif kind=="punch":
        a=T/f"{i}_w.mp4"; vseg(clip,0,p["at"],a)
        b=T/f"{i}_p.mp4"; vseg(clip,p["at"],te-p["at"],b,zoom=p["zoom"],xp=p["xp"],yp=p["yp"])
        segs=[a,b]; log+=[(shot,p["at"]),(shot+" punch",te-p["at"])]
    else: # cutaway
        a=T/f"{i}_a.mp4"; vseg(clip,0,p["at"],a)
        m=T/f"{i}_c.mp4"; vseg(CL/f"{p['src']}.mp4",p["soff"],p["dur"],m)
        b=T/f"{i}_b.mp4"; vseg(clip,p["at"]+p["dur"],te-(p["at"]+p["dur"]),b)
        segs=[a,m,b]; log+=[(shot,p["at"]),("cut→"+p["src"],p["dur"]),(shot+"'",te-(p["at"]+p["dur"]))]
    lst=T/f"{i}_l.txt"; lst.write_text("".join(f"file '{s}'\n" for s in segs))
    cv=T/f"{i}_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(cv)])
    ca=T/f"{i}_a.m4a"; run(["ffmpeg","-y","-v","error","-t",f"{te}","-i",str(clip),"-vn","-c:a","aac","-b:a","192k",str(ca)])
    cr=T/f"{i}_r.mp4"; run(["ffmpeg","-y","-v","error","-i",str(cv),"-i",str(ca),"-map","0:v","-map","1:a","-c","copy","-shortest",str(cr)]); clips.append(cr)

fl=T/"zl.txt"; fl.write_text("".join(f"file '{f}'\n" for f in clips))
zv=T/"zv.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(fl),"-map","0:v","-c:v","copy","-an",str(zv)])
ain=[];aff=[]
for j,f in enumerate(clips): ain+=["-i",str(f)]; aff.append(f"[{j}:a]")
za=T/"za.m4a"; run(["ffmpeg","-y","-v","error",*ain,"-filter_complex","".join(aff)+f"concat=n={len(clips)}:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(za)])
out=PM/"carno_MOTIVATED.mp4"; run(["ffmpeg","-y","-v","error","-i",str(zv),"-i",str(za),"-map","0:v","-map","1:a","-c","copy",str(out)])
print(f"MOTIVATED: {dur(out):.1f}s ({len(log)} shots)")
for n,d in log: print(f"  {n:14} {d:4.2f}s")
