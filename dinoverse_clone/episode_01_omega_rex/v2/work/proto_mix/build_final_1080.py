#!/usr/bin/env python3
"""
FINAL master: loudness-master the approved episode mix to broadcast level and
upscale to 1080p.
  audio: two-pass loudnorm (measure -> apply, audio_master.py style) to -14 LUFS,
         TP -1.5, + alimiter safety  (fixes the peak clipping in the amix chain)
  video: 1264x720 -> 1920x1080 lanczos (AI-gen source; no ESRGAN needed), CRF 18
Run AFTER the owner approves the v7 balance:
  venv/bin/python build_final_1080.py [in.mp4] [out.mp4]
"""
import json, subprocess, sys
from pathlib import Path

PM = Path(__file__).parent
IN = Path(sys.argv[1]) if len(sys.argv) > 1 else PM/"EPISODE_MASTER_v7.mp4"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else PM/"EPISODE_FINAL_1080.mp4"
LUFS, TP, LRA = -14.0, -1.5, 11.0

def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: print("ERR\n", r.stderr[-1500:]); raise SystemExit(1)
    return r

# pass 1: measure
p = subprocess.run(["ffmpeg","-hide_banner","-i",str(IN),"-af",
     f"loudnorm=I={LUFS}:TP={TP}:LRA={LRA}:print_format=json","-f","null","-"],
     capture_output=True, text=True)
err = p.stderr; m = json.loads(err[err.rfind("{"):err.rfind("}")+1])
print(f"input: {m['input_i']} LUFS, TP {m['input_tp']} dBTP, LRA {m['input_lra']}")

# pass 2: apply loudnorm + limiter, upscale, single encode
af = (f"loudnorm=I={LUFS}:TP={TP}:LRA={LRA}:"
      f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
      f"offset={m['target_offset']},"
      f"alimiter=limit={10**(TP/20):.4f}:level=disabled")
run(["ffmpeg","-y","-v","error","-i",str(IN),
     "-vf","scale=1920:1080:flags=lanczos,setsar=1",
     "-r","24","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
     "-af",af,"-ar","48000","-c:a","aac","-b:a","256k",
     "-movflags","+faststart",str(OUT)])

# report
p2 = subprocess.run(["ffmpeg","-hide_banner","-i",str(OUT),"-af",
     f"loudnorm=I={LUFS}:TP={TP}:LRA={LRA}:print_format=json","-f","null","-"],
     capture_output=True, text=True)
e2 = p2.stderr; m2 = json.loads(e2[e2.rfind("{"):e2.rfind("}")+1])
d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(OUT)],capture_output=True,text=True).stdout.strip()
print(f"FINAL: {float(d):.1f}s  {OUT.stat().st_size//1024//1024}MB  "
      f"{m2['input_i']} LUFS, TP {m2['input_tp']} dBTP  -> {OUT}")
