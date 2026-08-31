#!/usr/bin/env python3
"""run_gates.py — the single sanctioned gate entrypoint (PIPELINE_OVERHAUL_PLAN, build step 4).

All gates are FAIL-CLOSED: any unwaivered non-OK verdict exits nonzero. Waivers live in
waivers.json (lane, gate, id, reason, date) and are surfaced, never silent.

Subcommands (v0 skeleton — wrapped gates only; `list` shows what is still TODO):
  state         S0 portfolio check on pipeline_state.json (>1 ACTIVE = FAIL, etc.)
  foley         cookies foley verdicts with HISSY/UNSYNCED promoted to hard-fail (S7 rev)
                  --fresh re-runs research/techjoint_cookies/verify_foley_v4.py first
  bank-status   S5 ledger-vs-disk clip count for a lane (the 53-vs-31 inflation, made a check)
                  --require-complete also fails below 100% banked (assembly precondition)
  list          registered gates + wrap status

Usage: python3 run_gates.py <subcommand> [options]
"""
import argparse
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(REPO, "pipeline_state.json")
WAIVERS = os.path.join(REPO, "waivers.json")

VALID_STATUS = {"ACTIVE", "BLOCKED-ON-OWNER", "PARKED", "KILLED", "PUBLISHED", "UNTRIAGED"}

GATES = {
    "state": "wrapped (v0)",
    "foley": "wrapped (v0, cookies lane; HISSY/UNSYNCED hard-fail)",
    "bank-status": "wrapped (v0, wbs_ep02 lane)",
    "render": "TODO — wrap scripts/verify_render.py",
    "thumb": "TODO — wrap research/wildbirdsurvival_teardown/thumb_gate.py",
    "style": "TODO — wrap gate_style_wbs.py (per style profile)",
    "shots": "TODO — wrap research/wildbirdsurvival_teardown/gate_shots.py",
    "vision": "TODO — standing in-session recipe (build step 7; subscription labor, no APIs)",
    "listen": "TODO — listen_gate v0 DSP (build step 8)",
}


def load_waivers(lane, gate):
    if not os.path.exists(WAIVERS):
        return {}
    w = json.load(open(WAIVERS)).get("waivers", [])
    return {x["id"]: x for x in w if x.get("lane") == lane and x.get("gate") == gate}


def cmd_state(args):
    path = args.state_file or STATE
    st = json.load(open(path))
    lanes = st.get("lanes", {})
    fails, warns = [], []
    active = [k for k, v in lanes.items() if v.get("status") == "ACTIVE"]
    if len(active) > 1:
        fails.append(f">1 ACTIVE production lane: {active} (S0 cap is 1)")
    for k, v in lanes.items():
        s = v.get("status")
        if s not in VALID_STATUS:
            fails.append(f"lane '{k}' has invalid status {s!r}")
        if s == "KILLED" and not v.get("reason"):
            fails.append(f"lane '{k}' KILLED without a recorded reason")
        if s == "UNTRIAGED":
            (fails if st.get("triage", {}).get("done") else warns).append(
                f"lane '{k}' UNTRIAGED" + (" after triage" if st.get("triage", {}).get("done") else ""))
        if s == "BLOCKED-ON-OWNER":
            warns.append(f"lane '{k}' awaiting owner ({v.get('next', 'packet pending')}) — blocks NEW lane starts only")
    print(f"state: {len(lanes)} lanes, ACTIVE={active or 'none'}")
    for w in warns:
        print(f"  WARN {w}")
    for f in fails:
        print(f"  FAIL {f}")
    return 1 if fails else 0


def cmd_foley(args):
    lane = "techjoint_cookies_v4"
    verify_json = os.path.join(REPO, "assets", "techjoint_cookies", "foley_v4", "foley_verify.json")
    if args.fresh:
        script = os.path.join(REPO, "research", "techjoint_cookies", "verify_foley_v4.py")
        py = os.path.join(REPO, "venv", "bin", "python")
        r = subprocess.run([py if os.path.exists(py) else sys.executable, script])
        print(f"(fresh verify run exited {r.returncode}; applying promoted policy to its report)")
    d = json.load(open(verify_json))
    waived = load_waivers(lane, "foley")
    hard = {"SPEECH", "MUSIC", "HISSY", "UNSYNCED"}  # S7 rev: hiss/unsync promoted to hard-fail
    fails, ok = [], 0
    for sid, v in sorted(d.items()):
        verdict = v["verdict"]
        if verdict == "OK":
            ok += 1
        elif verdict in hard:
            if sid in waived:
                print(f"  WAIVED {sid} {verdict} — {waived[sid]['reason']} ({waived[sid]['date']})")
            else:
                fails.append((sid, verdict))
        else:
            fails.append((sid, f"unknown verdict {verdict!r}"))
    for sid, verdict in fails:
        print(f"  FAIL {sid}: {verdict}")
    print(f"foley[{lane}]: {ok} OK, {len(fails)} hard-fail, {len(waived)} waived, {len(d)} total")
    return 1 if fails else 0


def cmd_bank_status(args):
    lane = "wbs_ep02_vampire_finch"
    shots_json = os.path.join(REPO, "research", "wildbirdsurvival_teardown", "ep02_shots.json")
    ledger_md = os.path.join(REPO, "research", "wildbirdsurvival_teardown", "EP02_CLIP_LEDGER.md")
    clips_dir = os.path.join(REPO, "assets", "vampire_finch", "clips")
    shots = json.load(open(shots_json))["shots"]
    done = [s["id"] for s in shots
            if os.path.exists(os.path.join(clips_dir, s["id"] + ".mp4"))
            and os.path.exists(os.path.join(clips_dir, s["id"] + "_strip.jpg"))]
    disk = len(done)
    m = re.search(r"\*\*(\d+)\s*/\s*(\d+) clips done", open(ledger_md).read())
    claimed, total = (int(m.group(1)), int(m.group(2))) if m else (None, len(shots))
    print(f"bank-status[{lane}]: disk {disk}/{len(shots)}; ledger claims {claimed}/{total}")
    rc = 0
    if claimed is not None and claimed != disk:
        print(f"  FAIL ledger/disk mismatch: ledger says {claimed}, disk-verified {disk} (re-run gen_clip_ledger.py)")
        rc = 1
    if args.require_complete and disk < len(shots):
        print(f"  FAIL assembly precondition: {len(shots) - disk} shots unbanked (placeholders need per-shot waivers)")
        rc = 1
    return rc


def cmd_list(_):
    for g, s in GATES.items():
        print(f"  {g:12s} {s}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("state"); p.add_argument("--state-file"); p.set_defaults(fn=cmd_state)
    p = sub.add_parser("foley"); p.add_argument("--fresh", action="store_true"); p.set_defaults(fn=cmd_foley)
    p = sub.add_parser("bank-status"); p.add_argument("--require-complete", action="store_true"); p.set_defaults(fn=cmd_bank_status)
    p = sub.add_parser("list"); p.set_defaults(fn=cmd_list)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
