#!/usr/bin/env python3
"""gen_foley_lane.py — lane-generic wrapper of the PROVEN cookies method (research/techjoint_cookies/gen_foley_v4.py):
MMAudio watches each BANKED clip's exact window and generates synced foley from the shot's prompt (never library SFX).
  --manifest M.json --ledger L.json --out DIR [--only S001,S002] [--dry-run]
Prompt per shot = manifest shot.foley_prompt if present, else derived from i2v_prompt (motion nouns) with the standing
negative prompt (no music/speech). --dry-run validates inputs and prints the exact MMAudio commands without running them.
Real runs are CPU-bound minutes per clip (M5, serialize with other torch jobs). Verification = scripts/verify_foley (S7).
"""
import argparse, json, os, sys
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MM = os.path.join(REPO, "tools", "MMAudio"); NEG = "music, melody, speech, voice, talking, whispering, narration, singing, crowd"
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", required=True); ap.add_argument("--ledger", required=True); ap.add_argument("--out", required=True); ap.add_argument("--only"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(); m = json.load(open(a.manifest)); L = json.load(open(a.ledger)); only = set(a.only.split(",")) if a.only else None; os.makedirs(a.out, exist_ok=True); jobs = []; fails = []
    for s in m["shots"]:
        sid = s["id"]
        if only and sid not in only: continue
        if s.get("reuse") == "insert": continue
        row = L["clips"].get(sid)
        if not row or row.get("verdict") != "PASS": fails.append(f"{sid}: not PASS-banked (foley only on banked clips)"); continue
        prompt = s.get("foley_prompt") or ("foley for: " + (s.get("i2v_prompt") or s.get("vantage") or "ambient")[:160])
        outp = os.path.join(a.out, sid + ".flac")
        cmd = [os.path.join(REPO, "venv", "bin", "python"), os.path.join(MM, "demo.py"), "--video", row["clip"], "--prompt", prompt, "--negative_prompt", NEG, "--output", a.out, "--variant", "large_44k_v2"]
        jobs.append((sid, cmd, outp))
    print(f"gen_foley_lane: {len(jobs)} jobs, {len(fails)} skipped")
    for f in fails: print("  SKIP", f)
    for sid, cmd, outp in jobs:
        print(f"  {'DRY' if a.dry_run else 'RUN'} {sid}: {' '.join(cmd[2:6])} ...")
        if not a.dry_run:
            import subprocess; r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0: fails.append(f"{sid}: MMAudio failed: {r.stderr[-160:]}")
    sys.exit(1 if fails and not a.dry_run else 0)
if __name__ == "__main__": main()
