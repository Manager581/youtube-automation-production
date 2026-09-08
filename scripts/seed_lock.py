#!/usr/bin/env python3
"""seed_lock.py — GATE 1 made mechanical (SUBJECT LOCK). The owner picks ONE master per character/plate; this
freezes their sha256 into <lane>/SEED_LOCK.json. `check` verifies every locked file still hashes the same and
that every character required by the manifest has a locked master — spend/generation scripts call `check` first.
  lock  --lane DIR --pick ID=PATH [ID=PATH ...] --by "owner"     (re-lock requires --force; logged)
  check --lane DIR [--manifest shot_manifest.json]                exit 1 on missing/mismatched/unlocked
"""
import argparse, hashlib, json, os, sys, datetime
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("lock"); l.add_argument("--lane", required=True); l.add_argument("--pick", nargs="+", required=True); l.add_argument("--by", default="owner"); l.add_argument("--force", action="store_true")
    c = sub.add_parser("check"); c.add_argument("--lane", required=True); c.add_argument("--manifest")
    a = ap.parse_args(); lf = os.path.join(a.lane, "SEED_LOCK.json")
    if a.cmd == "lock":
        if os.path.exists(lf) and not a.force: print(f"FAIL lock exists ({lf}); re-locking requires --force (and gets logged)"); sys.exit(1)
        prev = json.load(open(lf)) if os.path.exists(lf) else {}
        locked = {}
        for pk in a.pick:
            mid, path = pk.split("=", 1)
            if not os.path.exists(path): print(f"FAIL {mid}: {path} missing"); sys.exit(1)
            locked[mid] = {"path": os.path.abspath(path), "sha256": sha(path)}
        out = {"lane": a.lane, "locked_at": datetime.datetime.now().isoformat(timespec="seconds"), "locked_by": a.by, "masters": locked, "history": prev.get("history", []) + ([{"relocked": prev.get("locked_at"), "masters": list(prev.get("masters", {}))}] if prev else [])}
        os.makedirs(a.lane, exist_ok=True); json.dump(out, open(lf, "w"), indent=1); print(f"locked {len(locked)} masters -> {lf}"); sys.exit(0)
    if not os.path.exists(lf): print(f"FAIL no SEED_LOCK.json in {a.lane} — GATE 1 not passed; no generation may start"); sys.exit(1)
    L = json.load(open(lf)); fails = []
    for mid, rec in L["masters"].items():
        if not os.path.exists(rec["path"]): fails.append(f"{mid}: locked file missing ({rec['path']})")
        elif sha(rec["path"]) != rec["sha256"]: fails.append(f"{mid}: file CHANGED since lock (sha mismatch)")
    if a.manifest:
        m = json.load(open(a.manifest)); need = {r for s in m.get("shots", []) for r in s.get("seed_masters", [])}
        for r in sorted(need):
            if r not in L["masters"]: fails.append(f"manifest needs master {r!r} but it is not locked")
    print(f"seed_lock: {len(L['masters'])} locked by {L.get('locked_by')} at {L.get('locked_at')}")
    for f in fails: print("  FAIL", f)
    print("seed_lock: " + ("PASS" if not fails else f"FAIL ({len(fails)})")); sys.exit(1 if fails else 0)
if __name__ == "__main__": main()
