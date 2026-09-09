#!/usr/bin/env python3
"""listen_record.py — writes the LISTEN record deliver.py requires (<render>_listen.json, bound to the render's sha).
Two producers, both explicit about WHO listened:
  --render R.mp4 --by model --model "gemini app" --answers ANSWERS.json     (the 6-line form answered by a listening model)
  --render R.mp4 --by owner --answers ANSWERS.json --words "owner's exact words"
ANSWERS.json = {"vo_flat": bool, "pace_ok": bool, "music_fits": bool, "foley_plausible": bool, "balance_ok": bool, "worst_timestamp": "mm:ss + why"}
Verdict = PASS only if vo_flat is false and the other four booleans are true; the worst timestamp is always recorded (it is the next fix).
A model record is valid ONLY if the model was first shown to separate v3 (known bad) from the reference (known good): --calibration CAL.json
with {"v3_verdict": "FAIL", "reference_verdict": "PASS", "model": ..., "at": ...}; without it a model record is refused."""
import argparse, datetime, hashlib, json, os, sys
def sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--render", required=True); ap.add_argument("--by", required=True, choices=["model", "owner"]); ap.add_argument("--answers", required=True); ap.add_argument("--model", default=""); ap.add_argument("--words", default=""); ap.add_argument("--calibration")
    a = ap.parse_args(); A = json.load(open(a.answers)); need = ["vo_flat", "pace_ok", "music_fits", "foley_plausible", "balance_ok", "worst_timestamp"]
    missing = [k for k in need if k not in A]
    if missing: print("listen_record REFUSED: answers missing", missing); return 1
    if a.by == "model":
        if not a.calibration or not os.path.exists(a.calibration): print("listen_record REFUSED: a model record needs --calibration (the model must have called v3 FAIL and the reference PASS first)"); return 1
        C = json.load(open(a.calibration))
        if C.get("v3_verdict") != "FAIL" or C.get("reference_verdict") != "PASS": print("listen_record REFUSED: calibration shows the model does not separate v3 from the reference:", C); return 1
    ok = (A["vo_flat"] is False) and all(A[k] is True for k in ("pace_ok", "music_fits", "foley_plausible", "balance_ok"))
    rec = {"render": a.render, "render_sha": sha(a.render), "by": a.by, "model": a.model, "words": a.words, "answers": A, "calibration": a.calibration, "verdict": "PASS" if ok else "FAIL", "at": datetime.datetime.now().isoformat(timespec="seconds")}
    out = os.path.splitext(a.render)[0] + "_listen.json"; json.dump(rec, open(out, "w"), indent=1); print(f"listen record {rec['verdict']} by {a.by} -> {out}; worst: {A['worst_timestamp']}"); return 0 if ok else 1
if __name__ == "__main__": sys.exit(main())
