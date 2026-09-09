#!/usr/bin/env python3
"""deliver.py v2 — the ONLY door a render leaves through. Everything is sha-bound and machine-checked; nothing is honour-system:
  1. <stem>_watch.json: verdict PASS, and every sha it recorded (video, spec, mix, manifest, plate, stems, strips, profile) still matches;
  2. WATCH_NOTES_<stem>.md: written AFTER the strips (mtime), one section per strip naming the strip's sha8 with >=3 timed observations,
     and an ANSWERS block whose numbers must AGREE with the gate (replays, longest still, what the first 3 s show = the promise shot);
  3. gates_<stem>.json (run_gates all --render): list form, render sha inside, verdict PASS, no waiver on any hook-window gate;
  4. <stem>_listen.json: a listening verdict (model or owner) bound to this render's sha — UNHEARD is NOT a delivery state;
  5. every clip and line in the render carries a setting_hash with a PASS prototype record, and every batch-generated item has an owner-go record.
On PASS: copies to deliveries/<lane>/<stem>_<sha8>.mp4 + DELIVERY_CHECKLIST_<stem>_<sha8>.json (the send guard hook only lets that path out).
Usage: deliver.py --render X.mp4 --lane lane.json --caption "..."   |   --selftest X.mp4 --lane lane.json (must REFUSE with reasons, never crash)"""
import argparse, glob, hashlib, json, os, re, sys, shutil
def sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def check(a):
    lane = json.load(open(a.lane)); name = lane["lane"]; stem = os.path.splitext(os.path.basename(a.render))[0]; d = os.path.dirname(a.render) or "."; s = sha(a.render); fails = []; ev = {"render_sha": s}
    # 1 watch JSON + sha binding
    w = os.path.join(d, stem + "_watch.json"); W = None
    if not os.path.exists(w): fails.append("watch gate JSON missing")
    else:
        W = json.load(open(w)); ev["watch"] = w; S = W.get("sha256", {})
        if S.get("video") != s: fails.append("watch JSON was computed on a different render (video sha mismatch)")
        if W.get("verdict") != "PASS": fails.append(f"watch gate verdict is {W.get('verdict')} ({sum(c.get('verdict') == 'FAIL' for c in W.get('checks', []))} FAIL checks)")
        wcmd = lane.get("gates", {}).get("watch", {}).get("cmd", []); paths = {wcmd[i].lstrip("-"): wcmd[i + 1] for i in range(len(wcmd) - 1) if wcmd[i].startswith("--")}
        for k in ("spec", "mix", "manifest", "plate", "lane", "profile"):   # re-hash the gate's inputs from lane.json's watch command
            pth = paths.get(k) if k != "lane" else a.lane
            if k == "profile": pth = W.get("profile")
            if pth and os.path.exists(pth) and S.get(k) and S.get(k) != sha(pth): fails.append(f"{k} changed since the watch gate ran ({pth})")
        for p in W.get("strips", []):
            if not os.path.exists(p): fails.append(f"strip missing: {p}")
            elif S.get("strips", {}).get(os.path.basename(p)) != sha(p): fails.append(f"strip changed since the gate ran: {os.path.basename(p)}")
        mr = paths.get("mix-report") if 'paths' in dir() else None
        if mr and os.path.exists(mr):
            for k, v in json.load(open(mr)).get("stems", {}).items():
                if os.path.exists(v["path"]) and (S.get("stems") or {}).get(k) != sha(v["path"]): fails.append(f"stem {k} changed since the watch gate ran")
        # 2 notes
        notes = os.path.join(d, f"WATCH_NOTES_{stem}.md")
        if not os.path.exists(notes): fails.append("WATCH_NOTES missing")
        else:
            txt = open(notes).read(); ev["watch_notes"] = notes; nm = os.path.getmtime(notes)
            for p in W.get("strips", []):
                b = os.path.basename(p); s8 = (S.get("strips", {}).get(b) or "")[:8]
                if os.path.exists(p) and nm <= os.path.getmtime(p): fails.append(f"WATCH_NOTES older than {b} (written before looking)")
                sec = re.search(r"^#+.*" + re.escape(b) + r".*$([\s\S]*?)(?=^#+|\Z)", txt, re.M)
                if not sec: fails.append(f"WATCH_NOTES has no section for {b}"); continue
                if s8 and s8 not in sec.group(0): fails.append(f"WATCH_NOTES section for {b} does not cite its sha8 {s8}")
                timed = re.findall(r"^\s*[-*]?\s*(\d+(?:\.\d+)?s|\d{1,2}:\d{2})\b", sec.group(1), re.M)
                if len(timed) < 3: fails.append(f"WATCH_NOTES section for {b} has {len(timed)} timed observations (need >= 3)")
            ans = {m.group(1).lower(): m.group(2).strip() for m in re.finditer(r"^(replays|longest_still_s|first_3s)\s*:\s*(.+)$", txt, re.M | re.I)}
            ck = {c["check"]: c for c in W.get("checks", [])}
            if "replays" not in ans: fails.append("WATCH_NOTES ANSWERS missing 'replays:'")
            else:
                got = ck.get("replay_s", {}).get("value", 0); nums = re.findall(r"\d+(?:\.\d+)?", ans["replays"]); mine = "none" in ans["replays"].lower() or not nums
                if (got == 0) != mine: fails.append(f"WATCH_NOTES replays '{ans['replays']}' disagrees with the gate (replay_s={got})")
            if "longest_still_s" not in ans: fails.append("WATCH_NOTES ANSWERS missing 'longest_still_s:'")
            else:
                try:
                    if abs(float(re.findall(r"\d+(?:\.\d+)?", ans["longest_still_s"])[0]) - float(ck.get("longest_static_s", {}).get("value", -99))) > 1.0: fails.append(f"WATCH_NOTES longest_still_s '{ans['longest_still_s']}' disagrees with the gate ({ck.get('longest_static_s', {}).get('value')})")
                except Exception: fails.append("WATCH_NOTES longest_still_s is not a number")
            proof = lane.get("promise", {}).get("proof_shots", [])
            if "first_3s" not in ans: fails.append("WATCH_NOTES ANSWERS missing 'first_3s:'")
            elif proof and not any(p in ans["first_3s"] for p in proof): fails.append(f"WATCH_NOTES first_3s '{ans['first_3s'][:40]}' does not name a promise proof shot {proof}")
    # 3 gates JSON (list form, sha-bound)
    g = os.path.join(d, f"gates_{stem}.json")
    if not os.path.exists(g): fails.append("gates JSON missing (run_gates.py all lane.json --render <render>)")
    else:
        G = json.load(open(g)); ev["gates"] = g
        if G.get("render_sha") != s: fails.append("gates JSON is for a different render (sha mismatch)")
        if not isinstance(G.get("gates"), list): fails.append("gates JSON is not in list form (old run_gates)")
        else:
            if G.get("verdict") != "PASS": fails.append("run_gates verdict is " + str(G.get("verdict")))
            for x in G["gates"]:
                if x.get("hook_window") and x.get("waivers"): fails.append(f"hook-window gate '{x.get('name')}' has waivers {x.get('waivers')}")
                if x.get("status") == "NOT-READY": fails.append(f"gate '{x.get('name')}' NOT-READY at delivery = FAIL")
    # 4 listen (required)
    L = os.path.join(d, stem + "_listen.json")
    if not os.path.exists(L): fails.append("no listen record: a listening verdict (model or owner form) bound to this render is REQUIRED; UNHEARD is not a delivery state")
    else:
        J = json.load(open(L)); ev["listen"] = L
        if J.get("render_sha") != s: fails.append("listen record is for a different render")
        if J.get("verdict") != "PASS": fails.append(f"listen verdict is {J.get('verdict')}")
        if J.get("by") not in ("model", "owner"): fails.append("listen record must say who listened (model|owner)")
    # 5 prototypes + spend, bound through the render report / mix
    R = a.render.replace(".mp4", "_report.json"); led = json.load(open(a.ledger)) if a.ledger and os.path.exists(a.ledger) else None
    if not os.path.exists(R): fails.append("render report missing (render_edit_spec writes it): cannot bind clips to settings")
    elif led:
        rows = {v.get("sha"): (k, v) for k, v in led.get("clips", {}).items()}; nosetting = []; nogo = []
        for sg in json.load(open(R)).get("segments", []):
            if sg.get("how") != "ledger": continue
            k = sg.get("shot"); row = led["clips"].get(sg.get("shot").split("_")[0], {}) if sg.get("shot") else {}
            if not row.get("setting_hash"): nosetting.append(k)
            elif not (glob.glob(os.path.join("output", name, "prototypes", f"prototype_{row['setting_hash']}*.json")) and any(json.load(open(p)).get("verdict") == "PASS" for p in glob.glob(os.path.join("output", name, "prototypes", f"prototype_{row['setting_hash']}*.json")))): nosetting.append(f"{k} (no PASS prototype for {row['setting_hash'][:8]})")
            if row.get("batch") and not os.path.exists(os.path.join("output", name, f"owner_go_{row['batch']}.json")): nogo.append(k)
            if not row.get("batch") and str(row.get("added", "")) > "2026-09-08T22:00": nogo.append(f"{k} (generated after the spend gate landed with no batch id)")
        if nosetting: fails.append(f"clips without a PASS prototype for their generator setting: {sorted(set(nosetting))[:8]}")
        if nogo: fails.append(f"clips bought without an owner-go record: {nogo[:8]}")
    else: fails.append("no --ledger given: cannot verify prototype/spend binding for the clips")
    return fails, ev, s, name, stem
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--render"); ap.add_argument("--lane", required=True); ap.add_argument("--caption", default=""); ap.add_argument("--ledger", default="assets/shrinking_planet/CLIP_LEDGER.json"); ap.add_argument("--selftest")
    a = ap.parse_args()
    if a.selftest:
        a.render = a.selftest; fails, ev, s, name, stem = check(a)
        print(f"deliver.py SELFTEST on {os.path.basename(a.render)}: {'REFUSED (correct)' if fails else 'WOULD DELIVER'} with {len(fails)} reasons:"); [print("   -", f) for f in fails]; return 0 if fails else 1
    fails, ev, s, name, stem = check(a)
    if fails: print("deliver.py REFUSED:\n  " + "\n  ".join(fails)); return 1
    out = os.path.join("deliveries", name); os.makedirs(out, exist_ok=True); dst = os.path.join(out, f"{stem}_{s[:8]}.mp4"); shutil.copy(a.render, dst)
    ck = {"render": a.render, "sha256": s, "delivered_as": dst, "caption": a.caption, "evidence": ev}
    json.dump(ck, open(os.path.join(out, f"DELIVERY_CHECKLIST_{stem}_{s[:8]}.json"), "w"), indent=1); print("DELIVERABLE:", dst); print(json.dumps(ck, indent=1)); return 0
if __name__ == "__main__": sys.exit(main())
