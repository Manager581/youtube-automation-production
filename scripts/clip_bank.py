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

SUBJECT_MASKS = {   # HSV hue ranges (OpenCV 0-179) + min saturation: the cast's locked colours (SEED_LOCK anchors)
    "PIP": [(140, 175, 90)],            # magenta fur/fronds
    "GRUFF": [(85, 105, 90)],           # saturated cyan-blue fur
    "ORB": [(15, 35, 60), (0, 179, 0)], # gold ring; chrome = low-sat bright handled by the fallback below
}
def subject_motion(clip, characters, fps=4, w=320, h=180):
    """Motion INSIDE the subject's colour mask (the reference's energy is bodies/hands on a mostly static camera, not camera drift):
    per-second mean |diff| over masked pixels, the count of motion EVENTS (peak > 3x median) and their times. Returns (mean, events, peaks)."""
    import cv2, numpy as np, subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", f"fps={fps},scale={w}:{h}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h * 3); fr = np.frombuffer(raw[: n * w * h * 3], dtype=np.uint8).reshape(n, h, w, 3)
    if n < 2: return 0.0, 0, []
    hsv = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in fr]); mask = np.zeros((n, h, w), bool)
    for c in characters:
        for (h0, h1, smin) in SUBJECT_MASKS.get(c, []):
            if h1 - h0 >= 170: mask |= (hsv[..., 1] < 40) & (hsv[..., 2] > 200)   # chrome: bright + desaturated
            else: mask |= (hsv[..., 0] >= h0) & (hsv[..., 0] <= h1) & (hsv[..., 1] >= smin) & (hsv[..., 2] > 60)
    g = fr.mean(axis=3).astype(np.float32); d = np.abs(np.diff(g, axis=0)); m = mask[1:] | mask[:-1]
    per = np.array([float(d[i][m[i]].mean()) if m[i].sum() > 50 else 0.0 for i in range(len(d))]); cover = float(mask.mean())
    med = float(np.median(per)) + 1e-3; peaks = [round(i / fps, 2) for i in range(len(per)) if per[i] > 3 * med and per[i] > 4.0]
    events = []; last = -9
    for t in peaks:
        if t - last > 0.5: events.append(t); last = t
    return round(float(per.mean()), 2), len(events), events, round(cover, 3)
def motion_score(clip, fps=4, w=160, h=90):
    """mean per-second frame-difference energy + longest run of near-static seconds (same metric as scripts/watch_gate.py)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    if n < 2: return 0.0, 0
    fr = np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w).astype(np.float32); d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    per = [float(d[i * fps:(i + 1) * fps].mean()) for i in range(max(1, len(d) // fps))]
    best = cur = 0
    for m in per:
        cur = cur + 1 if m < 1.0 else 0; best = max(best, cur)
    return round(float(np.mean(per)), 2), best
def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("add"); a1.add_argument("--ledger", required=True); a1.add_argument("--shot", required=True); a1.add_argument("--clip", required=True); a1.add_argument("--composite", required=True); a1.add_argument("--fps", type=int, default=8)
    a2 = sub.add_parser("verdict"); a2.add_argument("--ledger", required=True); a2.add_argument("--shot", required=True); g = a2.add_mutually_exclusive_group(required=True); g.add_argument("--pass", dest="ok", action="store_true"); g.add_argument("--fail", dest="ok", action="store_false"); a2.add_argument("--note", default=""); a2.add_argument("--by", default="session"); a2.add_argument("--hook", action="store_true", help="this shot sits in the hook window (<=45 s): static clips are refused"); a2.add_argument("--min-motion", type=float, default=4.0); a2.add_argument("--allow-static", action="store_true"); a2.add_argument("--characters", default="", help="comma list: hook verdict measures motion INSIDE these subjects' colour masks (somebody moves), not the whole frame"); a2.add_argument("--min-events", type=int, default=2, help="subject motion events per 6 s clip (reference: hands/heads move every ~1.5 s)")
    a3 = sub.add_parser("status"); a3.add_argument("--ledger", required=True); a3.add_argument("--manifest"); a3.add_argument("--require-complete", action="store_true"); a3.add_argument("--hook-coverage", action="store_true", help="Law 3: every hook moment (moment_id) needs >= 2 PASS angles from DISTINCT seeds that are visually distinct (pHash) and pass the hook motion rule"); a3.add_argument("--seeds", default="assets/shrinking_planet/seeds/SEEDS_0-3min.json"); a3.add_argument("--hook-s", type=float, default=45.0)
    a = ap.parse_args(); L = load(a.ledger)
    if a.cmd == "add":
        if not os.path.exists(a.clip): print(f"FAIL clip missing: {a.clip}"); sys.exit(1)
        strip = os.path.splitext(a.clip)[0] + "_strip.jpg"
        pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.clip], capture_output=True, text=True)
        dur = float(pr.stdout.strip() or 6.0); n = max(1, int(dur * a.fps + 0.999)); rows = max(1, (n + 7) // 8)
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.clip, "-vf", f"fps={a.fps},scale=240:-1,tile=8x{rows}", "-frames:v", "1", strip], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(strip): print(f"FAIL strip extraction: {r.stderr[-200:]}"); sys.exit(1)
        mm, ms = motion_score(a.clip)
        L["clips"][a.shot] = {"clip": os.path.abspath(a.clip), "sha": sha(a.clip), "strip": os.path.abspath(strip), "composite": a.composite, "added": datetime.datetime.now().isoformat(timespec="seconds"), "verdict": "PENDING", "rolls": L["clips"].get(a.shot, {}).get("rolls", 0) + 1, "motion_mean": mm, "static_run_s": ms}
        save(a.ledger, L); print(f"added {a.shot} (roll {L['clips'][a.shot]['rolls']}) strip={strip} motion={mm} static_run={ms}s verdict=PENDING"); sys.exit(0)
    if a.cmd == "verdict":
        if a.shot not in L["clips"]: print(f"FAIL {a.shot} not in ledger"); sys.exit(1)
        row = L["clips"][a.shot]
        if "motion_mean" not in row: row["motion_mean"], row["static_run_s"] = motion_score(row["clip"])
        # STATIC clips cannot be PASSED for hook slots (2026-09-08: 13/18 first-minute clips were prompted "camera locked" and passed
        # against their own prompt; the assembled hook froze for 15 s). A hook shot needs picture energy, not just prompt fidelity.
        if a.ok and a.hook and a.characters:
            sm, ev, peaks, cover = subject_motion(row["clip"], a.characters.split(",")); row.update(subject_motion_mean=sm, subject_events=ev, subject_peaks=peaks, subject_cover=cover)
            if cover < 0.01: print(f"REFUSED {a.shot}: subject mask covers {cover:.1%} of the frame — the named character is not visibly in this clip (drift or wrong seed)"); save(a.ledger, L); sys.exit(1)
            if ev < a.min_events and not a.allow_static: print(f"REFUSED {a.shot}: {ev} subject motion events (< {a.min_events}) — SOMEBODY must move (reference: a body/hand action every ~1.5 s); camera drift over a frozen creature does not count"); save(a.ledger, L); sys.exit(1)
        if a.ok and a.hook and (row["motion_mean"] < a.min_motion or row["static_run_s"] > 2.0) and not a.allow_static:
            print(f"REFUSED {a.shot}: motion {row['motion_mean']} (< {a.min_motion}) / static run {row['static_run_s']}s — a hook slot needs a moving shot; re-prompt with camera energy (push/whip/snap) or use --allow-static with a reason"); save(a.ledger, L); sys.exit(1)
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
    if a.manifest and a.hook_coverage:
        # LAW 3 — two angles of every hook moment. An angle counts only if: verdict PASS, its seed is a different file from the other angle's,
        # it passes the hook motion rule (subject_events >= 2 when measured, else whole-frame rule), and its first frame is visually distinct
        # (pHash hamming >= 16/63) from the other angle. Punch-in re-crops of the same seed (reuse=insert) never count.
        import numpy as np
        from scipy.fft import dctn
        def first_hash(clip):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", "scale=32:32", "-pix_fmt", "gray", "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True).stdout
            f = np.frombuffer(raw[:1024], dtype=np.uint8).reshape(32, 32).astype(np.float32); d = dctn(f, norm="ortho")[:8, :8].flatten()[1:]; return int.from_bytes(np.packbits(d > np.median(d)).tobytes(), "big")
        seeds = json.load(open(a.seeds)).get("seeds", {}) if os.path.exists(a.seeds) else {}
        moments = {}
        for sh in m.get("shots", []):
            t_in = sh.get("t_in", "99:99"); t = int(t_in.split(":")[0]) * 60 + int(t_in.split(":")[1]) if ":" in str(t_in) else float(t_in)
            if sh.get("moment_id") and sh.get("reuse", "unique") != "insert" and t < a.hook_s: moments.setdefault(sh["moment_id"], []).append((sh["id"], sh.get("composite_seed_id") or sh.get("id")))
        for sid, sd in seeds.items():   # extra angles that live only in the seed ledger (e.g. S002B)
            if sd.get("moment_id") and sid not in [x for v in moments.values() for x, _ in v]: moments.setdefault(sd["moment_id"], []).append((sid, sid))
        short = []
        for mid, rows in sorted(moments.items()):
            ok = []
            for sid, seed in rows:
                r = L["clips"].get(sid)
                if not r or r.get("verdict") != "PASS": continue
                hook_ok = (r["subject_events"] >= 2) if "subject_events" in r else (r.get("motion_mean", 0) >= 4.0 and r.get("static_run_s", 9) <= 2.0)
                if not hook_ok: continue
                ok.append((sid, r.get("composite") or seed, r["clip"]))
            distinct = []
            for sid, seed, clip in ok:
                if any(seed == s2 for _, s2, _ in distinct): continue
                h = first_hash(clip)
                if any(bin(h ^ first_hash(c2)).count("1") < 16 for _, _, c2 in distinct): continue
                distinct.append((sid, seed, clip))
            if len(distinct) < 2: short.append(f"{mid}: {len(distinct)} usable angle(s) {[x for x,_,_ in distinct]} of {[x for x,_ in rows]}")
        if short: fails.append(f"LAW 3: {len(short)} hook moments have < 2 distinct PASS angles that also pass the hook motion rule:\n      " + "\n      ".join(short))
        print(f"clip_bank: hook coverage {len(moments) - len(short)}/{len(moments)} moments with >= 2 usable angles")
    print(f"clip_bank: {banked} banked" + (f" / {total} unique in manifest" if total is not None else "") + f"; {len(L['clips'])} rows")
    for f in fails: print("  FAIL", f)
    print("clip_bank: " + ("PASS" if not fails else f"FAIL ({len(fails)})")); sys.exit(1 if fails else 0)
if __name__ == "__main__": main()
