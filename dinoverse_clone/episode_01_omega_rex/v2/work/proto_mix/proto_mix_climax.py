#!/usr/bin/env python3
"""
PROTOTYPE: prove the control's claim — a ducked music bed + SFX on cuts
transforms the *naked* rough_cut. Tests on the climax slice (S79-S89, ~62s).

Native clip audio (Grok roars/dialogue/ambience) stays FOREGROUND.
A dark trailer bed ducks under it via sidechaincompress. A few rumble/impact
SFX land on the breach + showdown cuts. Pure ffmpeg — no rewrite of the
assembler; this only proves the layer is what's missing.
"""
import subprocess
from pathlib import Path

ROOT = Path("/Users/jefflawrence/Documents/youtube-automation-production")
RC   = ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/rough_cut/rough_cut_v6.mp4"
MUS  = ROOT/"audio/breaking_law/music_tracks/track_04_dark.wav"
SFXD = ROOT/"assets/sfx"
OUT  = Path("/private/tmp/claude-501/-Users-jefflawrence-Documents-youtube-automation-production/b21f8831-73ac-48b0-a1c0-457f8f7c71ca/scratchpad")

SLICE_START = 462.79      # S79 containment breach
SLICE_END   = 525.21      # end (through the S89 card)
DUR = SLICE_END - SLICE_START

# SFX at cut points RELATIVE to slice start. (native roars already carry the
# scene; these just add low-end weight + transients on the big beats)
SFX = [
    (0.00,  "rumble_02_loud.wav", 0.42),   # S79 containment breach
    (18.13, "impact_new_loud.wav", 0.38),  # S82 action beat
    (36.25, "rumble_03_loud.wav", 0.40),   # S85 roar bed
    (54.38, "body_impact_01_loud.wav", 0.5),  # S88 three-way showdown
]

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FFMPEG ERROR:\n", r.stderr[-2500:]); raise SystemExit(1)

# 1) NAKED slice (the A side — exactly what's in the cut today)
naked = OUT/"climax_NAKED.mp4"
run(["ffmpeg","-y","-loglevel","error","-ss",f"{SLICE_START}","-to",f"{SLICE_END}",
     "-i",str(RC),"-c:v","libx264","-crf","20","-preset","veryfast",
     "-c:a","aac","-b:a","192k",str(naked)])

# 2) BEDDED slice (the B side — same pixels, + ducked bed + SFX)
inputs = ["-i",str(naked),"-i",str(MUS)]
for _,f,_ in SFX:
    inputs += ["-i",str(SFXD/f)]

fc = []
# music: trim, fades, NORMALIZE to a consistent bed level (~-24 LUFS) so it
# sits clearly under the -19 LUFS native audio but never disappears.
fc.append(f"[1:a]atrim=0:{DUR:.2f},afade=t=in:st=0:d=1.5,"
          f"afade=t=out:st={DUR-2.0:.2f}:d=2.0,"
          f"loudnorm=I=-24:TP=-2:LRA=11[mus]")
# split native audio: one copy is the mix foreground, one is the duck key
fc.append("[0:a]asplit=2[a_mix][a_key]")
# GENTLE duck: only loud roars pull the bed down, and only ~3:1, so the bed
# stays audible in every gap (Sik keeps music on 99.5% of runtime).
fc.append("[mus][a_key]sidechaincompress=threshold=0.125:ratio=3:attack=20:release=300[mus_d]")
# SFX -> delayed + leveled
sfx_labels = []
for i,(t,f,v) in enumerate(SFX):
    idx = 2+i
    ms = int(t*1000)
    lbl = f"s{i}"
    fc.append(f"[{idx}:a]adelay={ms}|{ms},volume={v}[{lbl}]")
    sfx_labels.append(f"[{lbl}]")
# final mix: foreground native + ducked bed + sfx, then limit
amix_in = "[a_mix][mus_d]" + "".join(sfx_labels)
n_amix = 2 + len(SFX)
fc.append(f"{amix_in}amix=inputs={n_amix}:normalize=0:dropout_transition=0[premix]")
fc.append("[premix]alimiter=limit=0.95:level=disabled[mixout]")

bedded = OUT/"climax_BEDDED.mp4"
run(["ffmpeg","-y","-loglevel","error", *inputs,
     "-filter_complex",";".join(fc),
     "-map","0:v","-map","[mixout]",
     "-c:v","copy","-c:a","aac","-b:a","192k",str(bedded)])

# lightweight deliverables: pure-audio A/B (identical pixels, so audio IS the diff)
# + a compressed 720p bedded video for context.
run(["ffmpeg","-y","-loglevel","error","-i",str(naked),
     "-vn","-c:a","libmp3lame","-b:a","192k",str(OUT/"climax_A_naked.mp3")])
run(["ffmpeg","-y","-loglevel","error","-i",str(bedded),
     "-vn","-c:a","libmp3lame","-b:a","192k",str(OUT/"climax_B_bedded.mp3")])
run(["ffmpeg","-y","-loglevel","error","-i",str(bedded),
     "-c:v","libx264","-crf","26","-preset","veryfast","-vf","scale=-2:720",
     "-c:a","aac","-b:a","160k",str(OUT/"climax_BEDDED_small.mp4")])

for tag,f in [("NAKED",naked),("BEDDED",bedded)]:
    r = subprocess.run(["ffmpeg","-i",str(f),"-af","volumedetect","-f","null","-"],
                       capture_output=True,text=True).stderr
    mv = [l for l in r.splitlines() if "mean_volume" in l or "max_volume" in l]
    print(f"{tag:<7}", " ".join(x.split(']')[-1].strip() for x in mv))
print("OK -> climax_A_naked.mp3, climax_B_bedded.mp3, climax_BEDDED_small.mp4")
