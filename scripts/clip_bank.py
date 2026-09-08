#!/usr/bin/env python3
"""clip_bank.py — bank-time clip ledger (GATE 5 mechanics; generalizes the WBS mp4+strip rule to any lane).
A clip is BANKED only when: file exists (sha recorded) + 8 fps strip exists + verdict == PASS (the verdict itself is
in-session vision labor per the subscriptions rule; this tool makes it a recorded, disk-verified row).
  add     --ledger L.json --shot S001 --clip path.mp4 --composite C001 [--fps 8]     extract strip, add row (verdict PENDING)
  verdict --ledger L.json --shot S001 --pass|--fail --note "..." --by "session"       record the verdict
  status  --ledger L.json [--manifest shot_manifest.json] [--require-complete]       disk-verify; exit 1 on ledger/disk mismatch
"""
import argparse, hashlib, json, os, subprocess, sys, datetime
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def load(p): return json.load(open(p)) if os.path.exists(p) else {"lane": os.path.dirname(os.path.abspath(p)), "clips": {}}
def save(p, L): json.dump(L, open(p, "w"), indent=1)
def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("add"); a1.add_argument("--ledger", required=True); a1.add_argument("--shot", required=True); a1.add_argument("--clip", required=True); a1.add_argument("--composite", required=True); a1.add_argument("--fps", type=int, default=8)
    a2 = sub.add_parser("verdict"); a2.add_argument("--ledger", required=True); a2.add_argument("--shot", required=True); g = a2.add_mutually_exclusive_group(required=True); g.add_argument("--pass", dest="ok", action="store_true"); g.add_argument("--fail", dest="ok", action="store_false"); a2.add_argument("--note", default=""); a2.add_argument("--by", default="session")
    a3 = sub.add_parser("status"); a3.add_argument("--ledger", required=True); a3.add_argument("--manifest"); a3.add_argument("--require-complete", action="store_true")
    a = ap.parse_args(); L = load(a.ledger)
    if a.cmd == "add":
        if not os.path.exists(a.clip): print(f"FAIL clip missing: {a.clip}"); sys.exit(1)
        strip = os.path.splitext(a.clip)[0] + "_strip.jpg"
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.clip, "-vf", f"fps={a.fps},scale=240:-1,tile=8x6", strip], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(strip): print(f"FAIL strip extraction: {r.stderr[-200:]}"); sys.exit(1)
        L["clips"][a.shot] = {"clip": os.path.abspath(a.clip), "sha": sha(a.clip), "strip": os.path.abspath(strip), "composite": a.composite, "added": datetime.datetime.now().isoformat(timespec="seconds"), "verdict": "PENDING", "rolls": L["clips"].get(a.shot, {}).get("rolls", 0) + 1}
        save(a.ledger, L); print(f"added {a.shot} (roll {L['clips'][a.shot]['rolls']}) strip={strip} verdict=PENDING"); sys.exit(0)
    if a.cmd == "verdict":
        if a.shot not in L["clips"]: print(f"FAIL {a.shot} not in ledger"); sys.exit(1)
        L["clips"][a.shot].update({"verdict": "PASS" if a.ok else "FAIL", "note": a.note, "by": a.by, "judged": datetime.datetime.now().isoformat(timespec="seconds")}); save(a.ledger, L); print(f"{a.shot}: {'PASS' if a.ok else 'FAIL'} ({a.note})"); sys.exit(0)
    fails = []; banked = 0
    for shot, row in L["clips"].items():
        if not os.path.exists(row["clip"]): fails.append(f"{shot}: clip missing on disk"); continue
        if sha(row["clip"]) != row["sha"]: fails.append(f"{shot}: clip changed since banking (sha mismatch)")
        if not os.path.exists(row.get("strip", "")): fails.append(f"{shot}: strip missing")
        if row.get("verdict") == "PASS": banked += 1
        if row.get("rolls", 0) > 3 and row.get("verdict") != "PASS": fails.append(f"{shot}: {row['rolls']} rolls without PASS — re-plan the shot (3-roll cap)")
    total = None
    if a.manifest:
        m = json.load(open(a.manifest)); ids = [s["id"] for s in m.get("shots", []) if s.get("reuse", "unique") != "insert"]; total = len(ids)
        missing = [i for i in ids if L["clips"].get(i, {}).get("verdict") != "PASS"]
        if a.require_complete and missing: fails.append(f"{len(missing)} manifest shots not banked (assembly precondition): {missing[:8]}{'...' if len(missing) > 8 else ''}")
    print(f"clip_bank: {banked} banked" + (f" / {total} unique in manifest" if total is not None else "") + f"; {len(L['clips'])} rows")
    for f in fails: print("  FAIL", f)
    print("clip_bank: " + ("PASS" if not fails else f"FAIL ({len(fails)})")); sys.exit(1 if fails else 0)
if __name__ == "__main__": main()
