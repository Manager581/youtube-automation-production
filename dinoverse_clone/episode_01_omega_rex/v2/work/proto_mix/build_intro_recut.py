#!/usr/bin/env python3
"""
RECUT the intro to Sik's style: ~25 fast varied cuts (accel to a snap),
SFX on nearly every cut, dark music bed throughout, cold-open VO over the top.
Native clip audio muted (trailer montage = VO+music+SFX driven, like Sik's).

Output: intro_RECUT.mp4  +  intro_CURRENT.mp4 (the A/B reference).
Prototype — clip picks/offsets are reasonable, not final; the point is RHYTHM.
"""
import subprocess, os
from pathlib import Path

ROOT = Path("/Users/jefflawrence/Documents/youtube-automation-production")
CL   = ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
VO   = ROOT/"audio/dinoverse_omega"
SFXD = ROOT/"assets/sfx"
MUS  = ROOT/"assets/dino_music/dark_tension.mp3"   # real dark trailer bed
RC   = ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut/rough_cut_v6.mp4"
OUT  = ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"
TMP  = OUT/"_intro_tmp"; TMP.mkdir(parents=True, exist_ok=True)
GREEN="0x2ecc40"

def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print("ERR:\n",r.stderr[-1800:]); raise SystemExit(1)

# real logo card (falls back to drawtext if the PNG isn't there yet)
LOGO = ROOT/"assets/dinoverse/dino_zoo_logo_card.png"
# S02 gate shot slots into the gf_s02 VO beat once its clip exists (same 1.10s -> zero ripple)
HAVE_S02 = (CL/"S02.mp4").exists()

# ---- SHOT LIST: (source|CARD, in_point, dur) — tiles 0..19.0s continuously ----
SHOTS = [
 ("CARD", 0, 0.90),                                                                # DINO ZOO title
 ("S67", 2.0, 0.70), ("S88", 1.5, 0.68), ("S48", 2.0, 0.50), ("S38", 3.0, 0.50),  # last-time flash (dino)
 (("S02" if HAVE_S02 else "S75"), (0.5 if HAVE_S02 else 2.0), 1.10),               # hosts at the gate on GF's line
 ("S71", 1.5, 1.00), ("S77", 2.0, 1.28),                                           # "part they hid" (hybrid/D-Rex)
 ("S61", 2.0, 0.60), ("S67", 6.0, 0.55), ("S48", 3.0, 0.55), ("S49", 2.0, 0.55),  # montage: T-Rex / raptors
 ("S46", 2.0, 0.50), ("S71", 2.5, 0.55), ("S72", 2.5, 0.55), ("S74", 4.0, 0.55),  # raptor / hybrids
 ("S77", 2.5, 0.55), ("S85", 2.0, 0.70), ("S68", 2.0, 0.60), ("S22", 2.0, 0.64),  # dome breach + dinos (kids saved for the hold)
 ("S69", 1.5, 1.57),                                                               # "Remember them." held — the ONLY kid shot
 ("S88", 2.0, 0.55), ("S77", 3.0, 0.50), ("S67", 7.0, 0.45),                       # wordless showdown-tease accel (no "stay till the end")
 ("CARD", 0, 0.88),                                                                # snap -> title button
]

# ---- VO placement: (stem, start_sec) ----
# luke_s12 ("Stay till the end...") CUT — owner: cheesy retention-beg; end on the planted mystery.
VO_PLAN = [("luke_s01",0.0),("gf_s02",3.28),("luke_s03_montage",6.66),
           ("gf_s11",13.85)]

# 1) VIDEO segments (video-only, uniform) -> concat
seg_files=[]; cut_times=[]; t=0.0
for i,(src,inp,dur) in enumerate(SHOTS):
    cut_times.append(t); t+=dur
    out=TMP/f"v{i:02d}.mp4"
    if src=="CARD":
        if LOGO.exists():
            run(["ffmpeg","-y","-v","error","-loop","1","-t",f"{dur}","-i",str(LOGO),
                 "-vf","scale=1264:720,setsar=1","-r","24",
                 "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
                 "-an","-t",f"{dur}",str(out)])
        else:
            vf=(f"drawtext=text='DINO ZOO':fontcolor={GREEN}:fontsize=120:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:font=Helvetica")
            run(["ffmpeg","-y","-v","error","-f","lavfi",
                 "-i",f"color=c=black:s=1264x720:r=24:d={dur}","-vf",vf,
                 "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
                 "-an","-t",f"{dur}",str(out)])
    else:
        vf=("scale=1264:720:force_original_aspect_ratio=increase,crop=1264:720,setsar=1")
        run(["ffmpeg","-y","-v","error","-ss",f"{inp}","-t",f"{dur}","-i",str(CL/f'{src}.mp4'),
             "-vf",vf,"-r","24","-c:v","libx264","-preset","veryfast","-crf","18",
             "-pix_fmt","yuv420p","-an","-t",f"{dur}",str(out)])
    seg_files.append(out)
TOTAL=t
lst=TMP/"list.txt"; lst.write_text("".join(f"file '{f}'\n" for f in seg_files))
vid=TMP/"video.mp4"
run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(vid)])

# 2) AUDIO: build inputs = VO stems + music + SFX, one big filter_complex
ins=[]; fc=[]; idx=0
# VO stems
vo_labels=[]
for stem,st in VO_PLAN:
    ins+=["-i",str(VO/f"{stem}.wav")]
    fc.append(f"[{idx}:a]adelay={int(st*1000)}|{int(st*1000)},volume=1.0[vo{idx}]")
    vo_labels.append(f"[vo{idx}]"); idx+=1
fc.append("".join(vo_labels)+f"amix=inputs={len(vo_labels)}:normalize=0[vodry]")
# music
ins+=["-i",str(MUS)]; mi=idx; idx+=1
fc.append(f"[{mi}:a]atrim=0:{TOTAL:.2f},afade=t=in:d=1.0,afade=t=out:st={TOTAL-1.5:.2f}:d=1.5,"
          f"loudnorm=I=-33:TP=-6:LRA=11[mus]")   # -27 -> -33, DECISIVE cut (owner: still too loud)
# SFX on cuts: whoosh rotating; impacts on the big beats; rumble bed under montage
WHOOSH=[f"whoosh_0{n}_loud.wav" for n in (1,2,3,4,5)]
IMPACT_AT={1:"impact_new_loud.wav",8:"impact_01_loud.wav",21:"body_impact_01_loud.wav",24:"impact_new_loud.wav"}
sfx_labels=[]; wi=0
for ci,ct in enumerate(cut_times):
    if ci==0: continue
    f = IMPACT_AT.get(ci) or WHOOSH[wi % len(WHOOSH)]
    if ci not in IMPACT_AT: wi+=1
    vol = 0.5 if ci in IMPACT_AT else 0.32
    ins+=["-i",str(SFXD/f)]
    d=int(max(0.0,ct-0.06)*1000)
    fc.append(f"[{idx}:a]adelay={d}|{d},volume={vol}[s{idx}]"); sfx_labels.append(f"[s{idx}]"); idx+=1
# rumble bed under the montage (cut 8 -> ~13.5s)
ins+=["-i",str(SFXD/"rumble_03_loud.wav")]
rd=int(cut_times[8]*1000)
fc.append(f"[{idx}:a]adelay={rd}|{rd},volume=0.22[rumble]"); sfx_labels.append("[rumble]"); idx+=1
# HERO: classic-style T-Rex roar right when he hits the screen (cut 1 = the S67 T-Rex flash)
ins+=["-i",str(ROOT/"assets/dino_sfx/roar_trex_victory.mp3")]
rr=int(max(0.0,cut_times[1]-0.03)*1000)
fc.append(f"[{idx}:a]adelay={rr}|{rr},volume=0.9[roar]"); sfx_labels.append("[roar]"); idx+=1
# DIALOGUE-FORWARD (v7): stems sit at ~-23.8 LUFS; compress + raise to ~-12 so the
# cold-open VO matches the body dialogue level (duck keys off the RAISED voice)
fc.append("[vodry]acompressor=threshold=-26dB:ratio=3:attack=8:release=200:knee=4:makeup=2dB,"
          "volume=9.8dB,alimiter=limit=0.98:level=disabled[vofwd]")
# duck music under VO, then mix everything
fc.append("[vofwd]asplit=2[vomix][vokey]")
fc.append("[mus][vokey]sidechaincompress=threshold=0.06:ratio=6:attack=15:release=280[musd]")
allmix="[vomix][musd]"+"".join(sfx_labels)
fc.append(f"{allmix}amix=inputs={2+len(sfx_labels)}:normalize=0:dropout_transition=0[premix]")
fc.append("[premix]alimiter=limit=0.95[aout]")
aud=TMP/"audio.wav"
run(["ffmpeg","-y","-v","error",*ins,"-filter_complex",";".join(fc),"-map","[aout]",str(aud)])

# 3) mux — clone the last frame (tpad) so no SFX tail gets truncated by -shortest
recut=OUT/"intro_RECUT.mp4"
run(["ffmpeg","-y","-v","error","-i",str(vid),"-i",str(aud),
     "-filter_complex","[0:v]tpad=stop_mode=clone:stop_duration=1.5[v]",
     "-map","[v]","-map","1:a","-c:v","libx264","-preset","veryfast","-crf","18",
     "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",str(recut)])

# 4) A/B reference: current cold open (0..20.5) from the real cut
cur=OUT/"intro_CURRENT.mp4"
run(["ffmpeg","-y","-v","error","-t","20.5","-i",str(RC),
     "-c:v","libx264","-crf","24","-preset","veryfast","-c:a","aac","-b:a","160k",str(cur)])

print(f"cuts: {len(SHOTS)}   total video: {TOTAL:.2f}s")
for tag,f in [("RECUT",recut),("CURRENT",cur)]:
    d=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip()
    print(f"  {tag:8} {d}s  {os.path.getsize(f)//1024}KB")
