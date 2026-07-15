#!/usr/bin/env python3
"""
Roll the Sik style across the WHOLE episode (audio layer):
  intro_RECUT  +  styled body (native dialogue + music bed + SFX on cuts)  +  end card (VO).
Body cut-RHYTHM variance (cutaways/punch-ins) is a SEPARATE later pass — dialogue-constrained.
Placeholder music (2 beds) + generic SFX; real dino audio swaps in later.
"""
import subprocess, re
from pathlib import Path
import numpy as np

ROOT=Path("/Users/jefflawrence/Documents/youtube-automation-production")
RCB=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut"; SEG=RCB/"segments"
VO=ROOT/"audio/dinoverse_omega"; SFXD=ROOT/"assets/sfx"; MUSD=ROOT/"audio/breaking_law/music_tracks"
PM=ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"; TMP=PM/"_ep_tmp"; TMP.mkdir(parents=True,exist_ok=True)
SR=48000; GREEN="0x2ecc40"
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print("ERR",c[:5],"\n",r.stderr[-1500:]); raise SystemExit(1)
def dur(f):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip() or 0)
def dec(p):
    raw=subprocess.run(["ffmpeg","-v","error","-i",str(p),"-f","f32le","-ar",str(SR),"-ac","2","-"],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32).reshape(-1,2).copy()
def enc(arr,p):
    pr=subprocess.Popen(["ffmpeg","-y","-v","error","-f","f32le","-ar",str(SR),"-ac","2","-i","-",str(p)],stdin=subprocess.PIPE)
    pr.communicate(np.clip(arr,-1,1).astype(np.float32).tobytes())

# ---- body shot list (skip cold open S01-S12 + end card S89) ----
lines=[re.search(r"file '?([^']+)'?",l).group(1) for l in (RCB/"concat_list.txt").read_text().splitlines() if l.startswith("file")]
def znum(n):
    return int(re.sub(r'\D','',n) or 0)
body=[]; t=0.0
for fn in lines:
    nm=Path(fn).stem; d=dur(fn); num=znum(nm)
    if nm in("S01","S02","S89") or (nm.startswith("S") and num<=12 and 'b' not in nm and 'c' not in nm):
        t+=d; continue
    body.append((fn,round(t,3),round(d,3))); t+=d
BODY_START=body[0][1]; BODY_END=body[-1][1]+body[-1][2]; BLEN=BODY_END-BODY_START
cut_rel=[s-BODY_START for _,s,_ in body]                       # cut times in body-relative sec
zone_entries=sorted({round(cut_rel[i],2) for i,(fn,_,_) in enumerate(body)
                     if i==0 or (lambda a,b:(a<=16<b>0))})      # placeholder; real entries below
DARK_AT=344.3-BODY_START                                        # T-Rex onward = dark bed
print(f"body {BODY_START}->{BODY_END} ({BLEN:.1f}s), {len(body)} shots, dark bed from {DARK_AT:.1f}s")

# ---- 1) body video+native audio: concat the body segments ----
bl=TMP/"body_list.txt"; bl.write_text("".join(f"file '{fn}'\n" for fn,_,_ in body))
body_av=TMP/"body_av.mp4"
run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(bl),"-c","copy",str(body_av)])

# ---- 2) music bed: light (first half) + dark (T-Rex on), crossfaded ----
lenA=DARK_AT; lenB=BLEN-DARK_AT+1.5
mA=TMP/"mA.wav"; mB=TMP/"mB.wav"
run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(MUSD/"track_03_emotional.wav"),
     "-t",f"{lenA}","-af","loudnorm=I=-25:TP=-2:LRA=11",str(mA)])
run(["ffmpeg","-y","-v","error","-stream_loop","-1","-i",str(MUSD/"track_04_dark.wav"),
     "-t",f"{lenB}","-af","loudnorm=I=-24:TP=-2:LRA=11",str(mB)])
music=TMP/"music_body.wav"
run(["ffmpeg","-y","-v","error","-i",str(mA),"-i",str(mB),
     "-filter_complex","[0][1]acrossfade=d=1.5:c1=tri:c2=tri[a]","-map","[a]",str(music)])

# ---- 3) SFX bed (numpy): soft whoosh on every body cut + impacts on zone entries + rumble under dark ----
buf=np.zeros((int((BLEN+2)*SR),2),dtype=np.float32)
def overlay(arr,at,g):
    i=int(at*SR); n=min(len(arr),len(buf)-i)
    if i>=0 and n>0: buf[i:i+n]+=arr[:n]*g
WH=[dec(SFXD/f"whoosh_0{n}_loud.wav") for n in (1,2,3,4,5)]
IMP=dec(SFXD/"impact_new_loud.wav"); BIMP=dec(SFXD/"body_impact_01_loud.wav"); RUM=dec(SFXD/"rumble_03_loud.wav")
ZONE_STARTS={"Carno":60.8,"Quetzal":103.0,"Aquatic":145.3,"Utahraptor":221.7,"Herbivores":267.9,
             "Lunch":318.2,"TRex":344.3,"Hybrid":393.5,"Climax":462.8}
for i,ct in enumerate(cut_rel):
    if i==0: continue
    overlay(WH[i%5], max(0,ct-0.05), 0.22)                      # soft whoosh on the cut
for z,abst in ZONE_STARTS.items():
    overlay(IMP, abst-BODY_START, 0.4)                          # impact on zone entry
overlay(BIMP, 462.8-BODY_START, 0.5)                            # climax breach
# rumble bed pulses under the dark block
tt=DARK_AT
while tt < BLEN-3:
    overlay(RUM, tt, 0.15); tt+=len(RUM)/SR*0.9
sfx=TMP/"sfx_body.wav"; enc(buf,sfx)

# ---- 4) final body mix: native (fg) + music (ducked) + sfx, limited ----
body_audio=TMP/"body_audio.wav"
run(["ffmpeg","-y","-v","error","-i",str(body_av),"-i",str(music),"-i",str(sfx),
     "-filter_complex",
     "[0:a]asplit=2[nmix][nkey];"
     "[1:a][nkey]sidechaincompress=threshold=0.06:ratio=5:attack=20:release=350[musd];"
     "[nmix][musd][2:a]amix=inputs=3:normalize=0:dropout_transition=0[pre];"
     "[pre]alimiter=limit=0.95[out]",
     "-map","[out]",str(body_audio)])
body_styled=TMP/"body_styled.mp4"
run(["ffmpeg","-y","-v","error","-i",str(body_av),"-i",str(body_audio),
     "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(body_styled)])
print(f"body_styled: {dur(body_styled):.1f}s")

# ---- 5) end card: black + GF closer then Luke CTA + music sting -> silence ----
gf=dec(VO/"gf_s89_closer.wav"); lk=dec(VO/"luke_s89_cta.wav")
ECLEN=1.0+len(gf)/SR+0.6+len(lk)/SR+1.4
eaud=np.zeros((int(ECLEN*SR),2),dtype=np.float32)
def put(a,at,g=1.0):
    i=int(at*SR); n=min(len(a),len(eaud)-i); eaud[i:i+n]+=a[:n]*g
put(gf,1.0); put(lk,1.0+len(gf)/SR+0.6)
stg=dec(MUSD/"track_04_dark.wav")[:int(ECLEN*SR)]
fade=np.linspace(1,0,len(stg)).reshape(-1,1)**1.5
put(stg*fade,0,0.18)
ec_wav=TMP/"ec.wav"; enc(eaud,ec_wav)
vf=(f"drawtext=text='Comment which dino you\\'d survive.':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2-40:font=Helvetica,"
    f"drawtext=text='Subscribe — part two if this hits.':fontcolor={GREEN}:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2+40:font=Helvetica")
endcard=TMP/"endcard.mp4"
run(["ffmpeg","-y","-v","error","-f","lavfi","-i",f"color=c=black:s=1264x720:r=24:d={ECLEN}",
     "-i",str(ec_wav),"-vf",vf,"-map","0:v","-map","1:a",
     "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","192k","-shortest",str(endcard)])

# ---- 6) concat intro + body + endcard ----
intro=PM/"intro_RECUT.mp4"
# normalize intro to same params for safe concat
intro_n=TMP/"intro_n.mp4"
run(["ffmpeg","-y","-v","error","-i",str(intro),"-c:v","libx264","-preset","veryfast","-crf","18",
     "-pix_fmt","yuv420p","-r","24","-vf","scale=1264:720,setsar=1","-c:a","aac","-b:a","192k",
     "-video_track_timescale","24000",str(intro_n)])
body_n=TMP/"body_n.mp4"
run(["ffmpeg","-y","-v","error","-i",str(body_styled),"-c:v","libx264","-preset","veryfast","-crf","18",
     "-pix_fmt","yuv420p","-r","24","-vf","scale=1264:720,setsar=1","-c:a","aac","-b:a","192k",
     "-video_track_timescale","24000",str(body_n)])
ec_n=TMP/"ec_n.mp4"
run(["ffmpeg","-y","-v","error","-i",str(endcard),"-c:v","libx264","-preset","veryfast","-crf","18",
     "-pix_fmt","yuv420p","-r","24","-vf","scale=1264:720,setsar=1","-c:a","aac","-b:a","192k",
     "-video_track_timescale","24000",str(ec_n)])
fl=TMP/"final_list.txt"; fl.write_text("".join(f"file '{p}'\n" for p in (intro_n,body_n,ec_n)))
final=PM/"EPISODE_STYLED.mp4"
run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(fl),"-c","copy",str(final)])
print(f"\nEPISODE_STYLED: {dur(final):.1f}s ({int(dur(final))//60}:{dur(final)%60:04.1f})  {final.stat().st_size//1024//1024}MB")
