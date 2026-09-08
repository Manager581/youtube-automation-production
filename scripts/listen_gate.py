#!/usr/bin/env python3
"""listen_gate.py — S7 DSP listen gate v0 (build step 8). Measures a MIX the way the reference was measured and
fails closed against reference-derived bands: integrated LUFS, loudness range (LRA), momentary-loudness floor
(dead air), fraction of near-silent seconds, longest silent stretch, and the money-line dip depth (max dip of
momentary vs integrated over >=1 s). Semantic listening stays CANNOT-CONFIRM; this is the numbers half.
  --calibrate REF.mp4 --targets T.json [--t0 --t1 --band]      write bands from the reference
  --video OURS.mp4 --targets T.json                            score; exit 1 on any FAIL (unmeasurable = FAIL)
"""
import argparse, json, re, subprocess, sys
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True).stderr
def measure(video, t0, t1):
    dur = t1 - t0
    err = run(["ffmpeg", "-hide_banner", "-ss", str(t0), "-t", str(dur), "-i", video, "-af", "ebur128=peak=none", "-f", "null", "-"])
    M = [float(m) for m in re.findall(r"\bM:\s*(-?[0-9.]+)", err)]
    tail = err.split("Summary")[-1] if "Summary" in err else ""
    I = re.search(r"I:\s*(-?[0-9.]+) LUFS", tail); L = re.search(r"LRA:\s*(-?[0-9.]+) LU", tail)
    I = float(I.group(1)) if I else None; L = float(L.group(1)) if L else None
    if not M: return {"integrated_lufs": I, "lra_lu": L, "silent_frac": None, "longest_silence_s": None, "max_dip_lu": None, "floor_lufs": None}
    per_s = 10; secs = [max(M[i:i+per_s]) for i in range(0, len(M), per_s)]  # per-second loudest momentary
    thr = (I - 20) if I is not None else -40
    silent = [v < thr for v in secs]; frac = sum(silent) / len(secs)
    longest = cur = 0
    for sflag in silent: cur = cur + 1 if sflag else 0; longest = max(longest, cur)
    floor = min(v for v in secs if v > -70) if any(v > -70 for v in secs) else None
    dip = (I - min(secs)) if (I is not None and secs) else None
    return {"integrated_lufs": I, "lra_lu": L, "silent_frac": round(frac, 3), "longest_silence_s": longest, "max_dip_lu": round(dip, 1) if dip is not None else None, "floor_lufs": floor}
SPEC = {"integrated_lufs": ("abs", 2.5), "lra_lu": ("max", 1.5), "silent_frac": ("max", 0.05), "longest_silence_s": ("max", 1.0), "max_dip_lu": ("min", 0.35)}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--calibrate"); ap.add_argument("--video"); ap.add_argument("--targets", required=True); ap.add_argument("--t0", type=float, default=0.0); ap.add_argument("--t1", type=float, default=45.0); ap.add_argument("--band", type=float, default=0.35); ap.add_argument("--json")
    a = ap.parse_args()
    if a.calibrate:
        ref = measure(a.calibrate, a.t0, a.t1); json.dump({"reference": a.calibrate, "t0": a.t0, "t1": a.t1, "band": a.band, "measured": ref}, open(a.targets, "w"), indent=1); print("calibrated:", json.dumps(ref)); return 0
    T = json.load(open(a.targets)); ref = T["measured"]; band = T.get("band", a.band); ours = measure(a.video, a.t0, a.t1); fails = []
    print("listen_gate: ours=" + json.dumps(ours))
    for k, (kind, tol) in SPEC.items():
        r, o = ref.get(k), ours.get(k)
        if r is None: continue
        if o is None: fails.append(f"{k}: unmeasurable (fail-closed)"); continue
        if kind == "abs": ok = abs(o - r) <= tol; rng = f"[{r-tol:.1f},{r+tol:.1f}]"
        elif kind == "max": ok = o <= r + tol; rng = f"<= {r+tol:.2f}"
        else: ok = o >= r * (1 - band); rng = f">= {r*(1-band):.2f}"
        print(f"  {'PASS' if ok else 'FAIL'} {k}: ours={o} ref={r} {rng}")
        if not ok: fails.append(f"{k}: ours={o} vs ref={r}")
    if a.json: json.dump({"ours": ours, "ref": ref, "fails": fails}, open(a.json, "w"), indent=1)
    print("listen_gate: " + ("PASS" if not fails else f"FAIL ({len(fails)})")); return 1 if fails else 0
if __name__ == "__main__": sys.exit(main())
