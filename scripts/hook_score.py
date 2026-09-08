#!/usr/bin/env python3
"""hook_score.py — GATE 2 scorer: measure a hook render with the SAME code that measured the
reference, and pass/fail against bands derived from the reference (never hand-typed).

  --calibrate REF.mp4 --targets T.json   measure the reference, write bands (±--band, default 0.35)
  --video OURS.mp4 --targets T.json      measure ours, compare, exit 1 on any FAIL (fail-closed;
                                         a metric that cannot be measured is a FAIL, not a skip)
Metrics (window --t0..--t1, default 0-45 s): hard cuts (scene th 0.30), transitions (scene th 0.10,
proxy for punch-ins/flashes/text pops), transitions in first 12 s, longest gap with no transition,
cut-on-onset rate (cuts within ±0.12 s of a librosa onset), onsets/min, integrated LUFS, LRA,
max loudness dip (integrated − quietest momentary M over ≥1 s). Requires ffmpeg + venv librosa.
"""
import argparse, json, re, subprocess, sys

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True).stderr

def scene_times(video, t0, dur, th):
    err = run(["ffmpeg", "-hide_banner", "-ss", str(t0), "-t", str(dur), "-i", video, "-vf", f"select='gt(scene,{th})',showinfo", "-f", "null", "-"])
    return sorted(float(x) for x in re.findall(r"pts_time:\s*([0-9.]+)", err))

def loudness(video, t0, dur):
    err = run(["ffmpeg", "-hide_banner", "-ss", str(t0), "-t", str(dur), "-i", video, "-af", "ebur128=peak=none", "-f", "null", "-"])
    M = [(float(t), float(m)) for t, m in re.findall(r"t:\s*([0-9.]+)\s+.*?M:\s*(-?[0-9.]+)", err)]
    I = re.search(r"I:\s*(-?[0-9.]+) LUFS", err.split("Summary")[-1]) if "Summary" in err else None
    L = re.search(r"LRA:\s*(-?[0-9.]+) LU", err.split("Summary")[-1]) if "Summary" in err else None
    return M, (float(I.group(1)) if I else None), (float(L.group(1)) if L else None)

def onsets(video, t0, dur):
    try:
        import librosa, numpy as np
        y, sr = librosa.load(video, sr=22050, offset=t0, duration=dur, mono=True)
        return [float(x) for x in librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=False)]
    except Exception as e:
        print(f"  WARN onsets unavailable ({e})"); return None

def measure(video, t0, t1):
    dur = t1 - t0
    cuts = scene_times(video, t0, dur, 0.30); trans = scene_times(video, t0, dur, 0.10)
    M, I, LRA = loudness(video, t0, dur); ons = onsets(video, t0, dur)
    m = {}
    m["hard_cuts"] = len(cuts); m["transitions"] = len(trans); m["transitions_first12s"] = sum(1 for t in trans if t < 12.0)
    pts = [0.0] + trans + [dur]; m["longest_gap_s"] = round(max(b - a for a, b in zip(pts, pts[1:])), 2)
    if ons is not None:
        m["onsets_per_min"] = round(len(ons) / dur * 60, 1)
        m["cut_on_onset_rate"] = round(sum(1 for c in cuts if any(abs(c - o) <= 0.12 for o in ons)) / len(cuts), 2) if cuts else 0.0
    else: m["onsets_per_min"] = None; m["cut_on_onset_rate"] = None
    m["integrated_lufs"] = I; m["lra_lu"] = LRA
    if M and I is not None:
        vals = [v for _, v in M if v > -70]; win = 10  # ebur128 prints ~10 M values/s
        mins = [max(vals[i:i+win]) for i in range(0, max(1, len(vals) - win))]  # quietest 1-s window = min over windows of max
        m["max_dip_lu"] = round(I - min(mins), 1) if mins else None
    else: m["max_dip_lu"] = None
    return m

# band spec: metric -> (kind) ; "range" = within ±band of ref; "min" = at least ref*(1-band); "max" = at most ref*(1+band)+slack
SPEC = {"hard_cuts": "range", "transitions": "range", "transitions_first12s": "min", "longest_gap_s": "max", "cut_on_onset_rate": "min", "onsets_per_min": "min", "lra_lu": "max", "max_dip_lu": "min"}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--calibrate"); ap.add_argument("--video"); ap.add_argument("--targets", required=True)
    ap.add_argument("--t0", type=float, default=0.0); ap.add_argument("--t1", type=float, default=45.0); ap.add_argument("--band", type=float, default=0.35); ap.add_argument("--json")
    a = ap.parse_args()
    if a.calibrate:
        ref = measure(a.calibrate, a.t0, a.t1); json.dump({"reference": a.calibrate, "t0": a.t0, "t1": a.t1, "band": a.band, "measured": ref}, open(a.targets, "w"), indent=1)
        print("calibrated from reference:", json.dumps(ref)); return 0
    T = json.load(open(a.targets)); ref = T["measured"]; band = T.get("band", a.band)
    ours = measure(a.video, a.t0, a.t1); fails = []
    print(f"hook_score: ours={json.dumps(ours)}")
    for k, kind in SPEC.items():
        r, o = ref.get(k), ours.get(k)
        if r is None: continue
        if o is None: fails.append(f"{k}: could not be measured (fail-closed)"); continue
        lo, hi = r * (1 - band), r * (1 + band)
        ok = (lo <= o <= hi) if kind == "range" else (o >= lo) if kind == "min" else (o <= hi + 0.5)
        print(f"  {'PASS' if ok else 'FAIL'} {k}: ours={o} ref={r} band=[{lo:.2f},{hi:.2f}] ({kind})")
        if not ok: fails.append(f"{k}: ours={o} vs ref={r} ({kind})")
    if a.json: json.dump({"ours": ours, "ref": ref, "fails": fails}, open(a.json, "w"), indent=1)
    print("hook_score: " + ("PASS" if not fails else f"FAIL ({len(fails)})")); return 1 if fails else 0

if __name__ == "__main__": sys.exit(main())
