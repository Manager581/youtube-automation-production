#!/usr/bin/env python3
"""
Fix the mix per owner note: music too loud + same track whole time.
Re-do BODY audio only (reuse built body_v.mp4 / native / sfx):
  - drop music ~6dB (clearly subordinate to dialogue+ambience)
  - ROTATE 4 tracks mapped per zone (was 2 blocks) -> changes ~10x
Then re-mux body + re-concat intro/endcard -> EPISODE_MASTER_v2.mp4.
"""
import subprocess, re
from pathlib import Path
ROOT=Path("/Users/jefflawrence/Documents/youtube-automation-production")
RCB=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut"; CL=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
MUSD=ROOT/"audio/breaking_law/music_tracks"
PM=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"; T=PM/"_master"; TM=PM/"_remix"; TM.mkdir(parents=True,exist_ok=True)
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print("ERR",c[:6],"\n",r.stderr[-1400:]); raise SystemExit(1)
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip() or 0)
ENC=["-r","24","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-video_track_timescale","24000"]
def znum(n): return int(re.sub(r'\D','',n) or 0)
def zone(n):
    return ("Entry" if n<=16 else "Carno" if n<=23 else "Quetzal" if n<=30 else "Aquatic" if n<=42
            else "Utahraptor" if n<=50 else "Herbivores" if n<=58 else "Lunch" if n<=60
            else "TRex" if n<=68 else "Hybrid" if n<=78 else "Climax")
# zone -> placeholder track (mood-mapped). 4 tracks -> per-zone variety.
ZTRACK={"Entry":"track_02_investigative","Carno":"track_02_investigative","Quetzal":"track_03_emotional",
        "Aquatic":"track_03_emotional","Utahraptor":"track_01_tense","Herbivores":"track_03_emotional",
        "Lunch":"track_02_investigative","TRex":"track_04_dark","Hybrid":"track_04_dark","Climax":"track_01_tense"}
MUS_LUFS=-30    # was -24/-25 -> ~6dB quieter, clearly under dialogue+ambience

# rebuild body timeline from the already-built per-clip segments
lines=[re.search(r"file '?([^']+)'?",l).group(1) for l in (RCB/"concat_list.txt").read_text().splitlines() if l.startswith("file")]
body=[]
for fn in lines:
    nm=Path(fn).stem; num=znum(nm)
    if nm in("S01","S02","S89") or (nm.startswith("S") and num<=12 and 'b' not in nm and 'c' not in nm): continue
    if (CL/f"{nm}.mp4").exists(): body.append(nm)
# zone spans in the NEW (motivated) timeline
tcur=0.0; spans=[]  # (zone, start, end)
cur_zone=None; z_start=0.0
for shot in body:
    d=dur(T/f"{shot}_r.mp4")
    z=zone(znum(shot))
    if z!=cur_zone:
        if cur_zone is not None: spans.append((cur_zone,z_start,tcur))
        cur_zone=z; z_start=tcur
    tcur+=d
spans.append((cur_zone,z_start,tcur))
BLEN=tcur
print(f"body {BLEN:.1f}s, {len(spans)} zone music cues:")
for z,a,b in spans: print(f"  {z:11} {a:6.1f}->{b:6.1f}  [{ZTRACK[z]}]")

# build per-zone music segments then crossfade-chain
segfiles=[]
for i,(z,a,b) in enumerate(spans):
    seg=TM/f"z{i}.wav"; d=b-a+ (1.2 if i<len(spans)-1 else 0)  # overlap for xfade
    run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(MUSD/f"{ZTRACK[z]}.wav"),
         "-t",f"{d}","-af",f"loudnorm=I={MUS_LUFS}:TP=-3:LRA=11",str(seg)])
    segfiles.append(seg)
# crossfade chain
acc=segfiles[0]
for i in range(1,len(segfiles)):
    nxt=TM/f"acc{i}.wav"
    run(["ffmpeg","-y","-v","error","-i",str(acc),"-i",str(segfiles[i]),
         "-filter_complex","[0][1]acrossfade=d=1.2:c1=tri:c2=tri[a]","-map","[a]",str(nxt)])
    acc=nxt
music=TM/"music.wav"; run(["ffmpeg","-y","-v","error","-i",str(acc),"-t",f"{BLEN}","-c","copy",str(music)]) if False else run(["ffmpeg","-y","-v","error","-i",str(acc),"-af",f"atrim=0:{BLEN}","-ar","48000",str(music)])

# re-mix: native (fg) + quieter music (light duck) + existing sfx
baud=TM/"body_audio.wav"
run(["ffmpeg","-y","-v","error","-i",str(T/"body_native.m4a"),"-i",str(music),"-i",str(T/"sfx.wav"),
     "-filter_complex",
     "[0:a]asplit=2[nmix][nkey];[1:a][nkey]sidechaincompress=threshold=0.05:ratio=4:attack=25:release=400[musd];"
     "[nmix][musd][2:a]amix=inputs=3:normalize=0:dropout_transition=0[pre];[pre]alimiter=limit=0.95[out]",
     "-map","[out]",str(baud)])
bstyled=TM/"body_styled.mp4"; run(["ffmpeg","-y","-v","error","-i",str(T/"body_v.mp4"),"-i",str(baud),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(bstyled)])

# re-concat: reuse intro_n + ec_n; norm body
def norm(src,out): run(["ffmpeg","-y","-v","error","-i",str(src),*ENC,"-vf","scale=1264:720,setsar=1","-c:a","aac","-b:a","192k",str(out)])
bN=TM/"body_n.mp4"; norm(bstyled,bN)
iN=T/"intro_n.mp4"; eN=T/"ec_n.mp4"
flist=TM/"flist.txt"; flist.write_text("".join(f"file '{p}'\n" for p in (iN,bN,eN)))
fv=TM/"final_v.mp4"; run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(flist),"-map","0:v","-c:v","copy","-an",str(fv)])
fa=TM/"final_a.m4a"; run(["ffmpeg","-y","-v","error","-i",str(iN),"-i",str(bN),"-i",str(eN),"-filter_complex","[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]","-map","[a]","-c:a","aac","-b:a","192k",str(fa)])
MASTER=PM/"EPISODE_MASTER_v2.mp4"; run(["ffmpeg","-y","-v","error","-i",str(fv),"-i",str(fa),"-map","0:v","-map","1:a","-c","copy",str(MASTER)])
print(f"\nEPISODE_MASTER_v2: {dur(MASTER):.1f}s  {MASTER.stat().st_size//1024//1024}MB")
# verify new music-vs-dialogue gap
def lufs(f):
    r=subprocess.run(["ffmpeg","-i",str(f),"-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr
    m=[x for x in r.splitlines() if "I:" in x and "LUFS" in x]; return float(m[-1].split("I:")[1].split("LUFS")[0]) if m else 0
print(f"new music bed: {lufs(music):.1f} LUFS  (dialogue ~-18.8) -> gap {-18.8-lufs(music):.1f} dB (was 4.7)")
