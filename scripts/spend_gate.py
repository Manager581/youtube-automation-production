#!/usr/bin/env python3
"""spend_gate.py — Law 0: credits derive from gates, not from a hand-written line. Computes a batch's EXACT totals from its packs
(Grok clips x seconds, ElevenLabs characters), hashes the batch, and refuses unless an owner-go record exists for THAT hash.
  --grok PACK.json [--grok PACK2.json] --vo VO_LINES_MANIFEST.json [--vo ...] --lane lane.json          -> prints totals + batch sha, exit 1 if no go
  --record-go "owner's exact words" --by owner   (same pack args)                                        -> writes output/<lane>/owner_go_<sha8>.json
The generation drivers (Grok/ElevenLabs recipes) must be run only after this prints GO. Re-voicing a line already voiced needs
`--allow-retake` with a reason (one-pass rule)."""
import argparse, hashlib, json, os, sys, datetime
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--grok", action="append", default=[]); ap.add_argument("--vo", action="append", default=[]); ap.add_argument("--lane", required=True); ap.add_argument("--record-go"); ap.add_argument("--by", default="owner"); ap.add_argument("--allow-retake", help="reason")
    a = ap.parse_args(); lane = json.load(open(a.lane)); name = lane["lane"]; items = []; clips = 0; secs = 0; chars = 0; retakes = []
    for p in a.grok:
        for c in json.load(open(p))["clips"]: clips += 1; secs += int(c.get("gen_s", 6)); items.append(("grok", c["shot"], c.get("seed"), int(c.get("gen_s", 6))))
    for p in a.vo:
        m = json.load(open(p))
        for l in m["lines"]:
            if l.get("reuse_audio_from"): continue
            if os.path.exists(os.path.join(os.path.dirname(p), l["id"] + ".mp3")): retakes.append(l["id"])
            chars += l["chars"]; items.append(("vo", l["id"], l["sha256"], l["chars"]))
    if retakes and not a.allow_retake: print(f"spend_gate REFUSED: {retakes} already have audio (one-pass rule); pass --allow-retake 'reason'"); sys.exit(1)
    h = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()[:8]
    out = os.path.join("output", name); os.makedirs(out, exist_ok=True); rec = os.path.join(out, f"owner_go_{h}.json")
    print(f"BATCH {h}: {clips} Grok clips ({secs} gen-seconds) + {chars} ElevenLabs chars" + (f" [retakes: {retakes} — {a.allow_retake}]" if retakes else ""))
    if a.record_go:
        json.dump({"batch": h, "clips": clips, "gen_seconds": secs, "chars": chars, "items": items, "go": a.record_go, "by": a.by, "at": datetime.datetime.now().isoformat(timespec="seconds"), "retakes": retakes, "retake_reason": a.allow_retake}, open(rec, "w"), indent=1); print("recorded", rec); return 0
    if os.path.exists(rec): print(f"GO recorded {json.load(open(rec))['at']} by {json.load(open(rec))['by']}: {json.load(open(rec))['go']!r}"); return 0
    print(f"NO GO for batch {h}: state this line to the owner and record the yes with --record-go"); return 1
if __name__ == "__main__": sys.exit(main())
