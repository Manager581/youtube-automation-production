#!/usr/bin/env python3
"""spend_gate.py — Law 0: credits derive from gates, not from a hand-written line. Computes a batch's EXACT totals from its packs
(Grok clips x seconds, ElevenLabs characters), hashes the batch, and refuses unless an owner-go record exists for THAT hash.
  --grok PACK.json [--grok PACK2.json] --vo VO_LINES_MANIFEST.json [--vo ...] --lane lane.json          -> prints totals + batch sha, exit 1 if no go
  --record-go "owner's exact words" --by owner   (same pack args)                                        -> writes output/<lane>/owner_go_<sha8>.json
The generation drivers (Grok/ElevenLabs recipes) must be run only after this prints GO. Re-voicing a line already voiced needs
`--allow-retake` with a reason (one-pass rule).
PROTOTYPE BINDING (rule 10, previously declared and unenforced): a pack that is not marked `"prototype": true` may only be bought
once every name in lane.prototypes_required has a PASS record in output/<lane>/prototypes/, and no prototype for the lane has
FAILED. A prototype pack is exempt from the first rule — that is how a new setting earns its one sample — but never from the
second: a contradicting prototype stops the build until the owner says otherwise."""
import argparse, glob, hashlib, json, os, sys, datetime

def prototypes(lane_name):
    """Every prototype record for the lane, newest wins per (setting_hash, name)."""
    out = {}
    for p in sorted(glob.glob(os.path.join("output", lane_name, "prototypes", "prototype_*.json"))):
        try: r = json.load(open(p))
        except Exception: continue
        r["_path"] = p; out[(r.get("setting_hash"), r.get("name"))] = r
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--grok", action="append", default=[]); ap.add_argument("--vo", action="append", default=[]); ap.add_argument("--lane", required=True); ap.add_argument("--record-go"); ap.add_argument("--by", default="owner"); ap.add_argument("--allow-retake", help="reason")
    a = ap.parse_args(); lane = json.load(open(a.lane)); name = lane["lane"]; items = []; clips = 0; secs = 0; chars = 0; retakes = []; proto_batch = True; batch_settings = set()
    for p in a.grok:
        pack = json.load(open(p))
        if not pack.get("prototype"): proto_batch = False
        for c in pack["clips"]:
            clips += 1; secs += int(c.get("gen_s", 6)); items.append(("grok", c["shot"], c.get("seed"), int(c.get("gen_s", 6))))
            batch_settings |= {c[k] for k in ("setting", "setting_hash") if c.get(k)}
    for p in a.vo:
        m = json.load(open(p))
        if not m.get("prototype"): proto_batch = False
        batch_settings |= {m[k] for k in ("setting", "setting_hash") if m.get(k)}
        for l in m["lines"]:
            if l.get("reuse_audio_from"): continue
            if os.path.exists(os.path.join(os.path.dirname(p), l["id"] + ".mp3")): retakes.append(l["id"])
            chars += l["chars"]; items.append(("vo", l["id"], l["sha256"], l["chars"]))
            batch_settings |= {l[k] for k in ("setting", "setting_hash") if l.get(k)}
    if retakes and not a.allow_retake: print(f"spend_gate REFUSED: {retakes} already have audio (one-pass rule); pass --allow-retake 'reason'"); sys.exit(1)
    # RULE 10, enforced: a contradicting prototype stops the build, and only a prototype batch may buy an unproven setting.
    # A FAIL blocks the batch that would buy THAT setting again — not every later batch, or the FAIL that batch C exists to
    # supersede would deadlock the lane forever. Settings are named per item (`setting`/`setting_hash`) in the packs.
    P = prototypes(name)
    failed = {}
    for r in P.values():
        if r.get("verdict") == "FAIL":
            for k in (r.get("setting_hash"), r.get("name")):
                if k: failed[k] = r
    hit = sorted({f"{failed[s]['name']} ({(failed[s].get('setting_hash') or '')[:12]}) bought again by {s}" for s in batch_settings if s in failed})
    if hit: print(f"spend_gate REFUSED: this batch re-buys a setting whose prototype FAILED: {hit} — a contradicting prototype stops the build; the owner decides"); sys.exit(1)
    if not proto_batch:
        passed = {r.get("name") for r in P.values() if r.get("verdict") == "PASS"}
        missing = [n for n in lane.get("prototypes_required", []) if n not in passed]
        if missing:
            print(f"spend_gate REFUSED: lane.prototypes_required {missing} have no PASS prototype record in output/{name}/prototypes/.")
            print("  This batch is not marked \"prototype\": true, so it may only buy settings that already survived one gated sample.")
            print(f"  Prototype records present: {sorted(r.get('name','?') for r in P.values()) or 'none'}")
            sys.exit(1)
    h = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()[:8]
    out = os.path.join("output", name); os.makedirs(out, exist_ok=True); rec = os.path.join(out, f"owner_go_{h}.json")
    print(f"BATCH {h}: {clips} Grok clips ({secs} gen-seconds) + {chars} ElevenLabs chars" + (f" [retakes: {retakes} — {a.allow_retake}]" if retakes else ""))
    if a.record_go:
        json.dump({"batch": h, "clips": clips, "gen_seconds": secs, "chars": chars, "items": items, "go": a.record_go, "by": a.by, "at": datetime.datetime.now().isoformat(timespec="seconds"), "retakes": retakes, "retake_reason": a.allow_retake}, open(rec, "w"), indent=1); print("recorded", rec); return 0
    if os.path.exists(rec): print(f"GO recorded {json.load(open(rec))['at']} by {json.load(open(rec))['by']}: {json.load(open(rec))['go']!r}"); return 0
    print(f"NO GO for batch {h}: state this line to the owner and record the yes with --record-go"); return 1
if __name__ == "__main__": sys.exit(main())
