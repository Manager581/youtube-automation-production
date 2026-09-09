#!/usr/bin/env python3
"""prototype_record.py — Law 0 made machine-checkable. A generator SETTING (prompt template + engine + params, or voice + model + settings)
gets a setting_hash; ONE sample is generated and passed through its gate; the record binds hash -> sample sha -> gate json -> verdict.
deliver.py refuses any banked clip/line whose setting_hash has no PASS record; a FAIL record writes BLOCKED into pipeline_state.json.
  hash   --engine grok-imagine-i2v --params '{"dur":6}' --template-file PROMPT.txt            -> prints setting_hash
  record --lane lane.json --setting HASH --name talking_clip --sample FILE --gate-json G.json --verdict PASS|FAIL --numbers '{...}' [--owner "words"]
  stamp  --ledger CLIP_LEDGER.json --shot S001 --setting HASH [--batch 7b6e415a]          (or --lines-manifest M.json --line L01_ORB)"""
import argparse, datetime, hashlib, json, os, sys
def setting_hash(engine, params, template):
    return hashlib.sha256(json.dumps({"engine": engine, "params": params, "template": template}, sort_keys=True).encode()).hexdigest()[:12]
def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hash"); h.add_argument("--engine", required=True); h.add_argument("--params", default="{}"); h.add_argument("--template-file"); h.add_argument("--template", default="")
    r = sub.add_parser("record"); r.add_argument("--lane", required=True); r.add_argument("--setting", required=True); r.add_argument("--name", required=True); r.add_argument("--sample", required=True); r.add_argument("--gate-json", required=True); r.add_argument("--verdict", required=True, choices=["PASS", "FAIL"]); r.add_argument("--numbers", default="{}"); r.add_argument("--owner", default=""); r.add_argument("--state", default="pipeline_state.json")
    st = sub.add_parser("stamp"); st.add_argument("--ledger"); st.add_argument("--shot"); st.add_argument("--lines-manifest"); st.add_argument("--line"); st.add_argument("--setting", required=True); st.add_argument("--batch")
    a = ap.parse_args()
    if a.cmd == "hash":
        t = open(a.template_file).read() if a.template_file else a.template; print(setting_hash(a.engine, json.loads(a.params), t)); return 0
    if a.cmd == "record":
        lane = json.load(open(a.lane))["lane"]; d = os.path.join("output", lane, "prototypes"); os.makedirs(d, exist_ok=True)
        rec = {"setting_hash": a.setting, "name": a.name, "sample": a.sample, "sample_sha": hashlib.sha256(open(a.sample, "rb").read()).hexdigest(), "gate_json": a.gate_json, "gate_sha": hashlib.sha256(open(a.gate_json, "rb").read()).hexdigest(), "verdict": a.verdict, "numbers": json.loads(a.numbers), "owner": a.owner, "at": datetime.datetime.now().isoformat(timespec="seconds")}
        p = os.path.join(d, f"prototype_{a.setting}_{a.name}.json"); json.dump(rec, open(p, "w"), indent=1); print("recorded", p, a.verdict)
        if a.verdict == "FAIL" and os.path.exists(a.state):   # a contradicting prototype STOPS the build for the next session too
            S = json.load(open(a.state)); ln = S.setdefault("lanes", {}).setdefault(lane, {}); ln["BLOCKED"] = f"prototype {a.name} ({a.setting}) FAILED {rec['at']}: {rec['numbers']} — owner decision needed before the batch"; json.dump(S, open(a.state, "w"), indent=1); print("pipeline_state: BLOCKED written")
        return 0
    if a.cmd == "stamp":
        if a.ledger:
            L = json.load(open(a.ledger)); L["clips"][a.shot]["setting_hash"] = a.setting
            if a.batch: L["clips"][a.shot]["batch"] = a.batch
            json.dump(L, open(a.ledger, "w"), indent=1); print(f"stamped {a.shot} setting={a.setting} batch={a.batch}")
        if a.lines_manifest:
            M = json.load(open(a.lines_manifest)); [l.update(setting_hash=a.setting, **({"batch": a.batch} if a.batch else {})) for l in M["lines"] if l["id"] == a.line]; json.dump(M, open(a.lines_manifest, "w"), indent=1); print(f"stamped {a.line}")
        return 0
if __name__ == "__main__": sys.exit(main())
