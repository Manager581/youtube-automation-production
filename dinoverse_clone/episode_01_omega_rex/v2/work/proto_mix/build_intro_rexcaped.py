#!/usr/bin/env python3
"""
REXCAPED variant intro v2 — matched to Sik's MEASURED opening
(reference/sik_opening_16s.mp4, frame-verified 2026-07-21):

  1. DISCLAIMER card 2.0s, FAST zoom (his text grows ~30% over 2s), small logo
     badge baked into the card bottom — NO separate logo card (his has none)
  2. HOST at 2.0s (S02 gate selfie) — VO spills from card onto host, like his
  3. MONTAGE word-aligned to luke_s03_montage (whisper word times, QA run wf_db3873e0):
     T-Rex flash + roar ON "A T-Rex", raptors ON "Raptor Pack", the two hybrid
     shots ON "two hybrids", teens land ON "three kids..." and HOLD through
     "dare" into gf_s11 "Remember them." (no duplicate tease flashes after)
  4. snap -> DINO ZOO logo card button (our end-of-intro handoff to the body)

QA fixes vs v1 (wf_db3873e0): roar lead-silence stripped (fired +0.76s late),
limiter 0.85 for AAC true-peak headroom (-0.2 dBTP fail), apad+explicit -t so
the tpad tail survives -shortest, rumble carried to the snap (15.5s mix hole).
Output: intro_REXCAPED.mp4
"""
import subprocess, os
from pathlib import Path

ROOT = Path("/Users/jefflawrence/Documents/youtube-automation-production")
CL   = ROOT/"dinoverse_clone/episode_01_omega_rex/v2/clips"
VO   = ROOT/"audio/dinoverse_omega"
SFXD = ROOT/"assets/sfx"
MUS  = ROOT/"assets/dino_music/dark_tension.mp3"
OUT  = ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix"
TMP  = OUT/"_intro_rex_tmp"; TMP.mkdir(parents=True, exist_ok=True)
LOGO = ROOT/"assets/dinoverse/dino_zoo_logo_card.png"
DISC = TMP/"disclaimer_card.png"
GREEN=(46,204,64)   # DINO ZOO #2ecc40
PAD  = 1.2          # end tail so the snap SFX rings out

def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print("ERR:\n",r.stderr[-1800:]); raise SystemExit(1)

# ---------- 0) disclaimer card PNG (Sik-style: DISCLAIMER + entertainment-only text
#              + small logo badge bottom-center, exactly his layout) ----------
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB",(1264,720),(0,0,0))
d = ImageDraw.Draw(img)
def font(sz,bold=True):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",sz,index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
def center(txt,f,y,fill):
    w = d.textlength(txt,font=f); d.text(((1264-w)/2,y),txt,font=f,fill=fill)
center("DISCLAIMER",font(58),210,(255,255,255))
center("This video contains AI-generated visuals and is",font(24,False),330,(220,220,220))
center("intended for entertainment only.",font(24,False),368,(220,220,220))
center("It does not represent real footage or real-life events.",font(24,False),406,(220,220,220))
badge = Image.open(LOGO).convert("RGB").resize((126,72))     # small logo bug, like his
img.paste(badge,((1264-126)//2,588))
img.save(DISC)

# ---------- montage word times (whisper, rel to stem start) ----------
# "A T-Rex" 0.36-0.92 | "a Raptor Pack" 1.26-1.86 | "two hybrids...exist" 2.26-4.02
# | "and three kids...dare" 4.54-6.50
M0 = 3.85   # montage VO + first flash start

# ---------- SHOT LIST: (kind, src, in_point, dur) ----------
# Owner spec 2026-07-21 (rev 2): Sik's host beat is the MAIN CHARACTER TALKING
# to camera giving the update — so the host shot is S13 with its NATIVE
# lip-synced audio (Luke: "Okay - we're back at Dino Zoo." GF: "You said that
# like it's a good thing."), not the silent S02 couple shot. S02 follows as the
# mission beat under gf_s02 VO. luke_s01 ("So last time...") DROPPED — the
# on-camera update replaces it.
SHOTS = [
 ("ZCARD", DISC, 0, 1.50),                 # disclaimer: text, music starts, zoom
 ("NCLIP", "S13", 0.0, 2.35),              # 1.50 HOST TALKS — Luke's line ONLY
                                           #      (owner cut GF's "good thing" snark;
                                           #      Luke ends 2.00 in-clip, GF starts 2.56)
 # GF walk-and-talk beat REMOVED entirely (owner 2026-07-21: too long) —
 # card -> Luke -> straight to montage, closest yet to Sik's ~7.5s-to-body pace.
 # S02b clip/still stay on disk for reuse.
 ("CLIP","S67",5.5,0.70),                  # 3.85  T-REX ("A T-Rex" 4.21) + HERO roar
 ("CLIP","S61",2.0,0.60),                  # 4.55  T-Rex 2nd angle (word tail)
 ("CLIP","S48",4.0,0.60),                  # 5.15  raptors ("Raptor Pack" 5.11-5.71)
 ("CLIP","S49",2.0,0.45),                  # 5.75  raptor close (bridge)
 ("CLIP","S82",3.5,0.65),                  # 6.20  Indominus wall-burst ("two hybrids" 6.11)
 ("CLIP","S83",3.0,0.60),                  # 6.85  D-Rex in smoke (hybrid #2)
 ("CLIP","S77",3.5,0.55),                  # 7.45  D-Rex at glass ("exist" ends 7.87)
 ("CLIP","S88",3.0,0.45),                  # 8.00  showdown tease (chaos beat)
 ("CLIP","S69",2.0,3.65),                  # 8.45  TEENS ("three kids" 8.47) HELD
                                           #       through gf_s11 "Remember them."
 ("CARD", LOGO, 0, 0.90),                  # 12.10 snap -> logo button
]
HERO_ROAR_CUT = 3    # S67 flash
WALL_CRASH_CUT = 7   # S82 wall-burst
TEENS_CUT = 11
SNAP_CUT = len(SHOTS)-1

# ---------- VO placement ----------
VO_PLAN = [("luke_s03_montage",M0),    # 3.85 -> 10.74, flashes word-aligned
           ("gf_s11",10.60)]           # over the held S69 (ends 11.87)
# NCLIP native audio (clip, delay_s, trim_end_s, fade_start_s): same
# dialogue-forward treatment as the stems, pre-attenuated to stem level
NATIVES=[("S13",1.50,2.35,2.05)]

# ---------- 1) VIDEO segments ----------
# Quantize every cut to the 24fps frame grid against PLANNED ABSOLUTE times —
# naive per-segment rounding accumulated +0.22s by S69 and pushed "three kids"
# onto the S88 flash (measured via scene detection on the v4 render).
for f in TMP.glob("v*.mp4"): f.unlink()          # stale segments from prior layouts
_end=0.0; _planned=[]
for kind,src,inp,dur in SHOTS:
    _end+=dur; _planned.append(_end)
seg_files=[]; cut_times=[]; t=0.0
for i,(kind,src,inp,dur) in enumerate(SHOTS):
    cut_times.append(t)
    nfr=max(1,round((_planned[i]-t)*24)); dur=nfr/24.0   # snap to frame grid
    t+=dur
    out=TMP/f"v{i:02d}.mp4"
    if kind=="ZCARD":
        # owner spec: text holds a beat, THEN the zoom kicks in (with the music)
        # hold ~0.33s (8 frames), then push 1.00 -> 1.28 over the rest — super fast
        n=int(round(dur*24)); hold=8
        vf=(f"scale=5056:2880,zoompan=z='1+0.28*max(on-{hold},0)/{n-hold}':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1264x720:fps=24,setsar=1")
        run(["ffmpeg","-y","-v","error","-loop","1","-t",f"{dur}","-i",str(src),
             "-vf",vf,"-r","24","-c:v","libx264","-preset","veryfast","-crf","18",
             "-pix_fmt","yuv420p","-an","-t",f"{dur}",str(out)])
    elif kind=="CARD":
        run(["ffmpeg","-y","-v","error","-loop","1","-t",f"{dur}","-i",str(src),
             "-vf","scale=1264:720,setsar=1","-r","24",
             "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
             "-an","-t",f"{dur}",str(out)])
    else:
        vf=("scale=1264:720:force_original_aspect_ratio=increase,crop=1264:720,setsar=1")
        run(["ffmpeg","-y","-v","error","-ss",f"{inp}","-t",f"{dur}","-i",str(CL/f"{src}.mp4"),
             "-map","0:v:0","-vf",vf,"-r","24","-c:v","libx264","-preset","veryfast","-crf","18",
             "-pix_fmt","yuv420p","-an","-t",f"{dur}",str(out)])
    seg_files.append(out)
TOTAL=t
lst=TMP/"list.txt"; lst.write_text("".join(f"file '{f}'\n" for f in seg_files))
vid=TMP/"video.mp4"
run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(vid)])

# ---------- 2) AUDIO ----------
def _stemdur(stem):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",str(VO/f"{stem}.wav")],capture_output=True,text=True).stdout.strip())
ins=[]; fc=[]; idx=0
vo_labels=[]
for stem,st in VO_PLAN:
    ins+=["-i",str(VO/f"{stem}.wav")]
    # 0.12s tail fade kills room-tone bleed into the next line (owner note, v5)
    fc.append(f"[{idx}:a]afade=t=out:st={max(0.0,_stemdur(stem)-0.12):.2f}:d=0.12,"
              f"adelay={int(st*1000)}|{int(st*1000)},volume=1.0[vo{idx}]")
    vo_labels.append(f"[vo{idx}]"); idx+=1
# NCLIP native lip-synced dialogue — pre-attenuated 0.55 so the shared
# dialogue-forward chain (+9.8dB) lands it at stem level (native -18.8 vs -23.8 LUFS).
# Edge fades kill baked-ambience hard cuts (the v5 'bleed')
for clipname,delay,trim,fst in NATIVES:
    ins+=["-i",str(CL/f"{clipname}.mp4")]
    d=int(delay*1000)
    fc.append(f"[{idx}:a]atrim=0:{trim},afade=t=in:d=0.05,afade=t=out:st={fst}:d=0.30,"
              f"adelay={d}|{d},volume=0.55[vo{idx}]")
    vo_labels.append(f"[vo{idx}]"); idx+=1
fc.append("".join(vo_labels)+f"amix=inputs={len(vo_labels)}:normalize=0[vodry]")
# music: fade in over the card, fade out only in the very tail (v1 had a mix
# hole after the last VO — keep the bed audible until the snap)
ins+=["-i",str(MUS)]; mi=idx; idx+=1
# loudnorm FIRST, fades after — loudnorm is dynamic, and running it after the
# fade made the music's perceived entrance drift between builds (owner caught it)
fc.append(f"[{mi}:a]atrim=0:{TOTAL+PAD:.2f},loudnorm=I=-33:TP=-6:LRA=11,"
          f"afade=t=in:st=0.15:d=0.8,"
          f"afade=t=out:st={TOTAL-0.2:.2f}:d={PAD+0.2:.2f}[mus]")
# SFX: whoosh on montage cuts, impacts on the big beats; cards + host stay clean
WHOOSH=[f"whoosh_0{n}_loud.wav" for n in (1,2,3,4,5)]
IMPACT_AT={HERO_ROAR_CUT:"impact_new_loud.wav",
           WALL_CRASH_CUT:"body_impact_01_loud.wav",
           TEENS_CUT:"impact_01_loud.wav",
           SNAP_CUT:"impact_new_loud.wav"}
sfx_labels=[]; wi=0
for ci,ct in enumerate(cut_times):
    if ci in (0,1,2): continue           # card + host + mission stay SFX-clean
    f = IMPACT_AT.get(ci) or WHOOSH[wi % len(WHOOSH)]
    if ci not in IMPACT_AT: wi+=1
    vol = 0.5 if ci in IMPACT_AT else 0.32
    ins+=["-i",str(SFXD/f)]
    dl=int(max(0.0,ct-0.06)*1000)
    fc.append(f"[{idx}:a]adelay={dl}|{dl},volume={vol}[s{idx}]"); sfx_labels.append(f"[s{idx}]"); idx+=1
# rumble bed: montage start ALL THE WAY to the snap (v1's hole was 15.5-15.9s)
ins+=["-i",str(SFXD/"rumble_03_loud.wav")]
rd=int(cut_times[HERO_ROAR_CUT]*1000)
fc.append(f"[{idx}:a]adelay={rd}|{rd},atrim=0:{cut_times[SNAP_CUT]+0.3:.2f},"
          f"afade=t=out:st={cut_times[SNAP_CUT]-0.4:.2f}:d=0.7,volume=0.22[rumble]")
sfx_labels.append("[rumble]"); idx+=1
# HERO roar exactly on the T-Rex flash — strip the file's lead-in silence first
# (v1 fired +0.76s late: the mp3 has leading silence)
ins+=["-i",str(ROOT/"assets/dino_sfx/roar_trex_victory.mp3")]
rr=int(max(0.0,cut_times[HERO_ROAR_CUT]-0.03)*1000)
fc.append(f"[{idx}:a]silenceremove=start_periods=1:start_threshold=-45dB,"
          f"adelay={rr}|{rr},volume=0.9[roar]")
sfx_labels.append("[roar]"); idx+=1
# dialogue-forward (v7 treatment)
fc.append("[vodry]acompressor=threshold=-26dB:ratio=3:attack=8:release=200:knee=4:makeup=2dB,"
          "volume=9.8dB,alimiter=limit=0.98:level=disabled[vofwd]")
fc.append("[vofwd]asplit=2[vomix][vokey]")
fc.append("[mus][vokey]sidechaincompress=threshold=0.06:ratio=6:attack=15:release=280[musd]")
allmix="[vomix][musd]"+"".join(sfx_labels)
fc.append(f"{allmix}amix=inputs={2+len(sfx_labels)}:normalize=0:dropout_transition=0[premix]")
# limit at 0.85 (~-1.4 dBFS): v1's 0.95 came out -0.2 dBTP after AAC.
# level=disabled is REQUIRED — alimiter's default auto-level re-normalizes back up
fc.append(f"[premix]alimiter=limit=0.85:level=disabled,apad=whole_dur={TOTAL+PAD:.2f}[aout]")
aud=TMP/"audio.wav"
run(["ffmpeg","-y","-v","error",*ins,"-filter_complex",";".join(fc),"-map","[aout]",str(aud)])

# ---------- 3) mux — explicit -t keeps the padded tail (v1's -shortest ate it) ----------
rex=OUT/"intro_REXCAPED.mp4"
run(["ffmpeg","-y","-v","error","-i",str(vid),"-i",str(aud),
     "-filter_complex",f"[0:v]tpad=stop_mode=clone:stop_duration={PAD}[v]",
     "-map","[v]","-map","1:a","-t",f"{TOTAL+PAD:.2f}",
     "-c:v","libx264","-preset","veryfast","-crf","18",
     "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",str(rex)])

print(f"cuts: {len(SHOTS)}   total video: {TOTAL:.2f}s (+{PAD}s pad)")
for i,ct in enumerate(cut_times):
    k,s,_,dur=SHOTS[i]
    print(f"  {ct:6.2f}s  {k:5} {s if isinstance(s,str) else Path(s).name:<24} {dur:.2f}s")
d=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(rex)],capture_output=True,text=True).stdout.strip()
print(f"OUT: {rex.name}  {d}s  {os.path.getsize(rex)//1024}KB")
