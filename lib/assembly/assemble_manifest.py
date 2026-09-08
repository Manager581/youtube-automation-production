#!/usr/bin/env python3
"""lib/assembly/assemble_manifest.py — shared-library assembler v0 for the manifest_timecodes paradigm (S6).
Places BANKED clips into their manifest slots (t_in..t_out), fail-closed: a shot with no PASS-banked clip is a hard
error unless a logged waiver names it (then a labelled placeholder is used and reported). Writes the preview mp4 and an
ASSEMBLY REPORT (every manifest shot: placed / placeholder-waived / MISSING) — the S6 gate reads the report.
  assemble --manifest M.json --ledger L.json --out preview.mp4 [--vo vo.wav] [--waivers waivers.json --lane NAME]
           [--size 960x540] [--fps 24] [--report report.json]
Trim policy: each clip is trimmed/looped-padded to its slot length (report records any pad >0.5 s as a WARN).
Reuse: concat via lib.assembly.edit_layer.concat; nothing here generates pixels.
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib.assembly.edit_layer import concat
def tc(s):
    m, sec = s.split(":"); return int(m) * 60 + float(sec)
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", required=True); ap.add_argument("--ledger", required=True); ap.add_argument("--out", required=True); ap.add_argument("--vo"); ap.add_argument("--waivers"); ap.add_argument("--lane", default="shrinking_planet"); ap.add_argument("--size", default="960x540"); ap.add_argument("--fps", type=int, default=24); ap.add_argument("--report")
    a = ap.parse_args(); m = json.load(open(a.manifest)); L = json.load(open(a.ledger)) if os.path.exists(a.ledger) else {"clips": {}}
    W, H = map(int, a.size.split("x")); waived = set()
    if a.waivers and os.path.exists(a.waivers):
        for w in json.load(open(a.waivers)).get("waivers", []):
            if w.get("lane") == a.lane and w.get("gate") in ("assembly", "S6"): waived.add(w.get("id"))
    workdir = os.path.splitext(a.out)[0] + "_segs"; os.makedirs(workdir, exist_ok=True); segs = []; rows = []; fails = []
    shots = sorted(m["shots"], key=lambda s: tc(s["t_in"]))
    for s in shots:
        sid = s["id"]; slot = tc(s["t_out"]) - tc(s["t_in"]); row = {"shot": sid, "beat": s.get("beat"), "t_in": s["t_in"], "t_out": s["t_out"], "slot_s": round(slot, 3)}
        src = None; ref = s.get("reuse_of") or sid; clip = L["clips"].get(ref)
        if clip and clip.get("verdict") == "PASS" and os.path.exists(clip["clip"]): src = clip["clip"]; row["status"] = "placed"; row["clip"] = src
        elif sid in waived: row["status"] = "placeholder-waived"
        else: row["status"] = "MISSING"; fails.append(f"{sid}: no PASS-banked clip and no waiver")
        seg = os.path.join(workdir, f"{sid}.mp4")
        if src:
            pr = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]); d = float(pr.stdout.strip() or 0)
            if slot - d > 0.5: row["warn"] = f"padded {slot-d:.2f}s (loop)"
            vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={a.fps}"
            r = run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stream_loop", "-1", "-i", src, "-t", f"{slot:.3f}", "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(a.fps), seg])
        else:
            label = f"{sid} {s.get('beat','')} PLACEHOLDER" if row["status"] != "MISSING" else f"{sid} MISSING"
            r = run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=0x202030:size={W}x{H}:rate={a.fps}:duration={slot:.3f}", "-vf", f"drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf:text='{label}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", seg])
        if r.returncode != 0: fails.append(f"{sid}: segment render failed: {r.stderr[-160:]}")
        segs.append(seg); rows.append(row)
    silent = a.out.replace(".mp4", "_v.mp4"); concat(segs, silent)
    if a.vo and os.path.exists(a.vo): run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", a.vo, "-c:v", "copy", "-c:a", "aac", "-shortest", a.out])
    else: os.replace(silent, a.out)
    rep = {"manifest": a.manifest, "out": a.out, "shots": rows, "placed": sum(r["status"] == "placed" for r in rows), "waived": sum(r["status"] == "placeholder-waived" for r in rows), "missing": sum(r["status"] == "MISSING" for r in rows), "fails": fails}
    json.dump(rep, open(a.report or a.out.replace(".mp4", "_report.json"), "w"), indent=1)
    print(f"assembly: placed={rep['placed']} waived={rep['waived']} missing={rep['missing']} -> {a.out}")
    for f in fails: print("  FAIL", f)
    print("assembly: " + ("PASS" if not fails else f"FAIL ({len(fails)}) — fail-closed: bank the missing shots or log a waiver")); sys.exit(1 if fails else 0)
if __name__ == "__main__": main()
