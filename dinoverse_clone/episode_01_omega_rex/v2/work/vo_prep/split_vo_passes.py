import json, subprocess, re, sys, os
from pathlib import Path

ROOT = Path("/Users/jefflawrence/Documents/youtube-automation-production")
AUD  = ROOT/"audio/dinoverse_omega"
SRC  = AUD/"source_chunks"
MAN  = json.load(open(ROOT/"dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep/vo_manifest_v2.json"))

def gaps(mp3, thresh=40, dur=float(os.environ.get("GAP_MIN","1.2"))):
    out = subprocess.run(["ffmpeg","-i",str(mp3),"-af",
        f"silencedetect=noise=-{thresh}dB:d={dur}","-f","null","-"],
        capture_output=True, text=True).stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", out)]
    ends   = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends))

def total_dur(f):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries",
        "format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout.strip())

pass_id = sys.argv[1]
p = next(p for p in MAN["generation_passes"] if p["pass_id"]==pass_id)
mp3 = SRC/Path(p["source_mp3"]).name
segs = p["segment_order"]
n_expect = len(segs)

g = gaps(mp3)
print(f"{pass_id}: {mp3.name}  dur={total_dur(mp3):.2f}s  gaps={len(g)}  expect={n_expect-1}")
if len(g) != n_expect-1:
    print(f"  !! GAP MISMATCH — expected {n_expect-1}, got {len(g)}. NOT splitting.")
    sys.exit(1)

# cut points = midpoint of each silence; keep 0.30s handles
bounds, prev = [], 0.0
for (s,e) in g:
    bounds.append((prev, s + 0.30))   # segment runs to just after speech ends
    prev = e - 0.30                   # next starts just before speech resumes
bounds.append((prev, total_dur(mp3)))

for (name,(a,b)) in zip(segs, bounds):
    a = max(0.0, a)
    out = AUD/name
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(mp3),
        "-ss",f"{a:.3f}","-to",f"{b:.3f}",
        "-af","afade=t=in:st=%.3f:d=0.04,afade=t=out:st=%.3f:d=0.06" % (a, max(a, b-0.06)),
        "-ar","44100","-ac","1",str(out)], check=True)
    d = total_dur(out)
    print(f"  {name:<28} {d:6.2f}s")
