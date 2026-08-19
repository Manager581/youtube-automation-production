#!/usr/bin/env python3
"""Copy downloaded Grok clips (grok-video-<conversation>.mp4 in ~/Downloads) into assets/techjoint_cookies/clips_v2/<id>.mp4
using grok_ledger_v2.tsv; make a 2fps frame strip for each newly banked clip."""
import os, shutil, subprocess, csv, sys
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.normpath(os.path.join(HERE,"..",".."))
led=[r for r in csv.DictReader(open(os.path.join(HERE,"grok_ledger_v2.tsv")), delimiter="\t")]
dl=os.path.expanduser("~/Downloads"); D=os.path.join(REPO,"assets","techjoint_cookies","clips_v2"); os.makedirs(D,exist_ok=True)
S=os.path.join(D,"strips"); os.makedirs(S,exist_ok=True)
new=[]
for r in led:
    conv=r["post_url"].split("conversation=")[-1]
    src=f"{dl}/grok-video-{conv}.mp4"; dst=f"{D}/{r['id']}.mp4"
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src,dst); new.append(r["id"])
        dur=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",dst],capture_output=True,text=True).stdout.strip()
        cols=5 if float(dur)>8 else 4; rows=4 if float(dur)>8 else 3
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",dst,"-vf",f"fps=2,scale=480:-2,drawtext=text='%{{pts\\:hms}}':x=w-tw-4:y=h-th-4:fontsize=14:fontcolor=white:box=1:boxcolor=black@0.5,tile={cols}x{rows}","-frames:v","1","-q:v","3",f"{S}/{r['id']}_strip.jpg"])
        print("banked",r["id"],dur)
have=sorted(f[:-4] for f in os.listdir(D) if f.endswith(".mp4"))
missing=[r["id"] for r in led if r["id"] not in have]
print("have",len(have),have); print("missing",missing)
