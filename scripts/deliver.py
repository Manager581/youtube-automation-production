#!/usr/bin/env python3
"""deliver.py — the ONLY door a render leaves through (FORMAT_LAWS spine). Refuses unless, for THIS file's sha:
  1. <stem>_watch.json exists for this video, verdict PASS, and every strip it lists exists;
  2. WATCH_NOTES_<stem>.md exists with a timestamped observation line for EVERY strip (written after looking);
  3. gates_<lane>.json (run_gates all) verdict PASS with no waivers on hook-window checks;
  4. listen: <stem>_listen.json (model or owner ear-check form) OR the caption is forced to start with "UNHEARD";
  5. every setting in lane.json["prototypes_required"] has a prototype record with verdict PASS.
On PASS it copies the file to deliveries/<lane>/<stem>_<sha8>.mp4 and writes DELIVERY_CHECKLIST_<stem>.json; that path is the
only thing SendUserFile may send (CLAUDE.md rule 8). Usage: deliver.py --render X.mp4 --lane lane.json --caption "..."
"""
import argparse, hashlib, json, os, re, shutil, sys
def sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--render", required=True); ap.add_argument("--lane", required=True); ap.add_argument("--caption", default="")
    a = ap.parse_args(); lane = json.load(open(a.lane)); name = lane["lane"]; stem = os.path.splitext(os.path.basename(a.render))[0]; d = os.path.dirname(a.render); s = sha(a.render); fails = []; ev = {}
    w = os.path.join(d, stem + "_watch.json")
    if not os.path.exists(w): fails.append("watch gate JSON missing")
    else:
        W = json.load(open(w)); ev["watch"] = w
        if os.path.abspath(W.get("video", "")) != os.path.abspath(a.render): fails.append("watch JSON is for a different video")
        if W.get("verdict") != "PASS": fails.append("watch gate verdict is " + str(W.get("verdict")))
        missing = [p for p in W.get("strips", []) if not os.path.exists(p)]
        if missing: fails.append(f"{len(missing)} strips missing")
        notes = os.path.join(d, f"WATCH_NOTES_{stem}.md")
        if not os.path.exists(notes): fails.append("WATCH_NOTES missing (look at every strip, then write one timestamped line per strip)")
        else:
            txt = open(notes).read(); ev["watch_notes"] = notes
            for p in W.get("strips", []):
                if os.path.basename(p) not in txt: fails.append(f"WATCH_NOTES has no line for {os.path.basename(p)}")
            if not re.search(r"first 3 s|first three seconds|0-3 ?s", txt, re.I): fails.append("WATCH_NOTES never answers what the first 3 s show")
    g = os.path.join(d, f"gates_{name}.json")
    if not os.path.exists(g): fails.append("gates JSON missing (run run_gates.py all)")
    else:
        G = json.load(open(g)); ev["gates"] = g
        if G.get("verdict") != "PASS": fails.append("run_gates verdict is " + str(G.get("verdict")))
        if any(x.get("waived") for x in G.get("gates", []) if x.get("hook_window")): fails.append("a hook-window gate was waived")
    L = os.path.join(d, stem + "_listen.json"); unheard = not os.path.exists(L)
    if unheard and not a.caption.startswith("UNHEARD"): fails.append('no listen record: caption must start with "UNHEARD"')
    if not unheard: ev["listen"] = L
    for pr in lane.get("prototypes_required", []):
        p = os.path.join(d, f"prototype_{pr}.json")
        if not os.path.exists(p) or json.load(open(p)).get("verdict") != "PASS": fails.append(f"prototype record for '{pr}' missing or not PASS")
        else: ev[f"prototype_{pr}"] = p
    if fails:
        print("deliver.py REFUSED:\n  " + "\n  ".join(fails)); sys.exit(1)
    out = os.path.join("deliveries", name); os.makedirs(out, exist_ok=True); dst = os.path.join(out, f"{stem}_{s[:8]}.mp4"); shutil.copy(a.render, dst)
    ck = {"render": a.render, "sha256": s, "delivered_as": dst, "caption": a.caption, "unheard": unheard, "evidence": ev}
    json.dump(ck, open(os.path.join(out, f"DELIVERY_CHECKLIST_{stem}.json"), "w"), indent=1); print("DELIVERABLE:", dst); print(json.dumps(ck, indent=1))
if __name__ == "__main__": main()
