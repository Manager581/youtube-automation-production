#!/usr/bin/env python3
"""run_gates.py — the single sanctioned gate entrypoint (PIPELINE_OVERHAUL_PLAN, build step 4).

All gates are FAIL-CLOSED: any unwaivered non-OK verdict exits nonzero. Waivers live in
waivers.json (lane, gate, id, reason, date) and are surfaced, never silent.

Subcommands (v0 — wrapped gates only; `list` shows what is still TODO):
  state         S0 portfolio check on pipeline_state.json (>1 ACTIVE = FAIL, etc.)
  foley         cookies foley verdicts with HISSY/UNSYNCED promoted to hard-fail (S7 rev)
                  --fresh re-runs research/techjoint_cookies/verify_foley_v4.py first
  bank-status   S5 ledger-vs-disk clip count for a lane (the 53-vs-31 inflation, made a check)
                  --require-complete also fails below 100% banked (assembly precondition)
  render        S8 tier 1: judge a scripts/verify_render.py report fail-closed
                  (--report <verify_*.json>; unwaivered criticals fail; waiver id = beat:check).
                  Report GENERATION stays `scripts/verify_render.py` (needs render+paper-edit+alignment).
  thumb         S2 thumbnail ship gate: --gate-json judges an existing thumb_gate result;
                  --base IMG --outdir DIR runs research/wildbirdsurvival_teardown/thumb_gate.py fresh.
                  Waiver id = tag (ship a RECOMPOSE only by logged waiver).
  style         S8 style conformance vs measured WBS winner bands: runs gate_style_wbs.py on a
                  NAME with forensics_<NAME>.json + compare_metrics.json entry (teardown dir).
                  Fail-closed on missing inputs; passes at >= --min-pass gates (default 10/11,
                  the plan's >=90% separation rule). Whole-name waiver id = NAME.
  shots         S4 shot-manifest craft gate: runs gate_shots.py (ep02 manifest). No waivers —
                  a failing craft law means fix the manifest, not ship around it.
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
    "render": "wrapped (v0; judges an existing verify_render report fail-closed)",
    "thumb": "wrapped (v0; thumb_gate.py fresh-run or existing gate JSON)",
    "style": "wrapped (v0, WBS bands only; per-style profiles = S1 work; forensics_BEST regenerated from refs/)",
    "shots": "wrapped (v0, ep02 manifest; no-waiver by design)",
    "vision": "TODO — standing in-session recipe (build step 7; subscription labor, no APIs)",
    "listen": "TODO — listen_gate v0 DSP (build step 8)",
}

TEARDOWN = os.path.join(REPO, "research", "wildbirdsurvival_teardown")


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


def cmd_render(args):
    """Judge a scripts/verify_render.py report fail-closed (S8 tier 1).

    verify_render's own severity model is kept: entries in the report's `critical`
    list block; `warnings` are surfaced but do not block. Waiver id = "<beat_id>:<check>".
    """
    d = json.load(open(args.report))
    waived = load_waivers(args.lane, "render")
    summ = d.get("summary", {})
    print(f"render[{args.lane}]: {d.get('render')} — {summ.get('total_beats', '?')} beats, "
          f"{summ.get('critical_failures', '?')} critical, {summ.get('warnings', '?')} warnings (report: {args.report})")
    for chk, r in summ.get("by_check", {}).items():
        print(f"    {chk:24s} pass {r.get('pass', 0)} / fail {r.get('fail', 0)}")
    fails = []
    for c in d.get("critical", []):
        wid = f"{c.get('beat_id')}:{c.get('check')}"
        if wid in waived:
            print(f"  WAIVED {wid} — {waived[wid]['reason']} ({waived[wid]['date']})")
        else:
            fails.append((wid, c.get("note", "")))
    for wid, note in fails[: args.show]:
        print(f"  FAIL {wid}: {note}")
    if len(fails) > args.show:
        print(f"  ... {len(fails) - args.show} more unwaivered criticals (raise --show)")
    nwarn = len(d.get("warnings", []))
    if nwarn:
        print(f"  WARN {nwarn} advisory warnings in report (non-blocking)")
    print(f"render verdict: {len(fails)} unwaivered critical, {len(waived)} waived")
    return 1 if fails else 0


def cmd_thumb(args):
    """Thumbnail ship gate (S2). Fresh mode composes+measures via thumb_gate.py;
    --gate-json judges an already-written <tag>_gate.json. Waiver id = tag."""
    waived = load_waivers(args.lane, "thumb")
    if args.gate_json:
        d = json.load(open(args.gate_json))
        tag = d.get("tag") or os.path.basename(args.gate_json).replace("_gate.json", "")
        for c in d.get("checks", []):
            print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']}")
        verdict = d.get("verdict")
        print(f"thumb[{args.lane}] {tag}: {verdict}")
        if verdict == "SHIP":
            return 0
        if tag in waived:
            print(f"  WAIVED {tag} — {waived[tag]['reason']} ({waived[tag]['date']})")
            return 0
        return 1
    if not args.base or not args.outdir:
        print("thumb: need --gate-json, or --base IMG --outdir DIR for a fresh run")
        return 2
    script = os.path.join(TEARDOWN, "thumb_gate.py")
    py = os.path.join(REPO, "venv", "bin", "python")
    cmd = [py if os.path.exists(py) else sys.executable, script, args.base, args.outdir]
    if args.tag:
        cmd += ["--tag", args.tag]
    cmd += args.extra or []
    r = subprocess.run(cmd)
    tag = args.tag or os.path.splitext(os.path.basename(args.base))[0]
    if r.returncode != 0 and tag in waived:
        print(f"  WAIVED {tag} — {waived[tag]['reason']} ({waived[tag]['date']})")
        return 0
    return r.returncode


def cmd_style(args):
    """Style conformance vs measured winner bands (S8), via gate_style_wbs.py.

    v0 grades against the WBS bands only (per-style profiles are S1 work). Needs
    forensics_<NAME>.json + a compare_metrics.json entry in the teardown dir; missing
    inputs FAIL closed with the regeneration recipe. Pass = >= --min-pass of 11 gates
    (default 10, the plan's >=90% separation rule). Waiver id = NAME (whole-verdict).
    """
    name = args.name
    missing = [p for p in (f"forensics_{name}.json",) if not os.path.exists(os.path.join(TEARDOWN, p))]
    cm_path = os.path.join(TEARDOWN, "compare_metrics.json")
    in_cm = os.path.exists(cm_path) and any(r.get("name") == name for r in json.load(open(cm_path)))
    if missing or not in_cm:
        if missing:
            print(f"  FAIL missing {missing[0]} — regenerate: cd research/wildbirdsurvival_teardown && "
                  f"../../venv/bin/python extract_forensics.py '{name}:refs/{name}.mp4'")
        if not in_cm:
            print(f"  FAIL '{name}' has no compare_metrics.json entry — extend compare_all.py VIDS "
                  f"(m-side metrics) before grading a new video")
        print(f"style[{name}]: FAIL (inputs missing — fail-closed)")
        return 1
    py = os.path.join(REPO, "venv", "bin", "python")
    r = subprocess.run([py if os.path.exists(py) else sys.executable, "gate_style_wbs.py", name],
                       cwd=TEARDOWN, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        print(f"style[{name}]: FAIL (gate_style_wbs.py exited {r.returncode})")
        return 1
    m = re.search(r"-->\s*(\d+)/(\d+) style gates passed", r.stdout)
    if not m:
        print(f"style[{name}]: FAIL (could not parse gate_style_wbs.py verdict — fail-closed)")
        return 1
    npass, total = int(m.group(1)), int(m.group(2))
    waived = load_waivers(args.lane, "style")
    ok = npass >= args.min_pass
    if not ok and name in waived:
        print(f"  WAIVED {name} — {waived[name]['reason']} ({waived[name]['date']})")
        ok = True
    print(f"style[{name}]: {npass}/{total} vs min-pass {args.min_pass} -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def cmd_shots(args):
    """Shot-manifest craft gate (S4): gate_shots.py on the ep02 manifest. Exit code
    propagates; deliberately NO waiver path — failing craft laws mean fix the manifest."""
    py = os.path.join(REPO, "venv", "bin", "python")
    r = subprocess.run([py if os.path.exists(py) else sys.executable,
                        os.path.join(TEARDOWN, "gate_shots.py")])
    return r.returncode


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
    p = sub.add_parser("render")
    p.add_argument("--report", required=True, help="a scripts/verify_render.py JSON report")
    p.add_argument("--lane", required=True)
    p.add_argument("--show", type=int, default=10, help="max unwaivered criticals to print")
    p.set_defaults(fn=cmd_render)
    p = sub.add_parser("thumb")
    p.add_argument("--gate-json", help="judge an existing <tag>_gate.json")
    p.add_argument("--base"); p.add_argument("--outdir"); p.add_argument("--tag")
    p.add_argument("--lane", default="wbs_ep02_vampire_finch")
    p.add_argument("extra", nargs="*", help="passed through to thumb_gate.py (e.g. --grade --plate)")
    p.set_defaults(fn=cmd_thumb)
    p = sub.add_parser("style")
    p.add_argument("--name", required=True, help="forensics_<NAME>.json name in the teardown dir")
    p.add_argument("--min-pass", type=int, default=10)
    p.add_argument("--lane", default="wbs_ep02_vampire_finch")
    p.set_defaults(fn=cmd_style)
    p = sub.add_parser("shots"); p.set_defaults(fn=cmd_shots)
    p = sub.add_parser("list"); p.set_defaults(fn=cmd_list)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
