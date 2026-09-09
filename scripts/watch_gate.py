#!/usr/bin/env python3
"""watch_gate.py — the render-level WATCH gate (plan S8, rebuilt after the 2026-09-08 first-minute failure).
It measures the assembled cut the way a viewer experiences it and FAILS CLOSED. No delivery without a PASS.
  --video CUT.mp4 --spec EDIT_SPEC.json --mix MIX_SPEC.json --manifest SHOTS.json [--ref REF.mp4] [--json OUT.json]
Checks (each with the number, the threshold and WHY):
  replayed_frac    screen time that replays an already-shown clip (designed <=1.5 s inserts excluded)  <= 0.10
  longest_static_s longest run of seconds with near-zero motion (4 fps frame-diff)                    <= ref*1.5 (default 2.5)
  motion_mean      mean per-second motion energy                                                       >= ref*0.5
  speech_frac      seconds with a VO line / total                                                      <= 0.75
  longest_dead_s   longest gap with no VO inside a dialogue beat                                       <= 3.0
  line_off_speaker VO lines whose speaker is not on screen at line start (non-insert slots)            == 0
  foley_cover      segments whose foley covers >=90% of the slot / segments                            >= 0.90
  text_min_px      smallest text pop size in the hook window                                          >= 110
  card_each_s      archive card hold                                                                   <= 0.6
  music_hole_s     seconds where music is cut (< -40 dB) with no sfx/drone item overlapping             == 0
  text_hits        text pops in the hook window with an sfx item within 0.2 s                          == all
  unheard          always reported: no listening model ran; the owner's ear check is a gate, not a formality
Writes JSON + 4 fps strips (33 s each) that MUST be looked at before any report.
"""
import argparse, json, os, subprocess, sys
import numpy as np
def probe(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)
def motion(video, fps=4, w=160, h=90):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h); fr = np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)) if n > 1 else np.zeros(0)
    per_sec = [float(d[i * fps:(i + 1) * fps].mean()) for i in range(len(d) // fps)] if len(d) >= fps else [float(d.mean()) if len(d) else 0.0]
    return per_sec
def static_run(per_sec, thr):
    best = cur = 0
    for m in per_sec:
        cur = cur + 1 if m < thr else 0; best = max(best, cur)
    return best
def strips(video, outdir, dur, fps=4):
    os.makedirs(outdir, exist_ok=True); paths = []
    for s in range(0, int(dur) + 1, 33):
        p = os.path.join(outdir, f"strip_{s:03d}s.jpg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(s), "-t", "33", "-i", video, "-vf", f"fps={fps},scale=200:-1,tile=8x17", "-frames:v", "1", "-q:v", "4", p]); paths.append(p)
    return paths
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--video", required=True); ap.add_argument("--spec", required=True); ap.add_argument("--mix", required=True); ap.add_argument("--manifest", required=True); ap.add_argument("--ref"); ap.add_argument("--json"); ap.add_argument("--hook-window", type=float, default=45.0)
    a = ap.parse_args(); spec = json.load(open(a.spec)); mix = json.load(open(a.mix)); man = {s["id"]: s for s in json.load(open(a.manifest))["shots"]}
    segs = spec["segments"]; total = segs[-1]["t_out"]; dur = probe(a.video); R = {}; checks = []
    def chk(name, val, ok, thr, why): checks.append({"check": name, "value": val, "threshold": thr, "verdict": "PASS" if ok else "FAIL", "why": why}); R[name] = val
    # 1 replayed screen time (designed inserts <=1.5 s excluded)
    seen = set(); rep = 0.0
    for sg in segs:
        src = sg["src"].split(":", 1)[1]; slot = sg["t_out"] - sg["t_in"]; designed = man.get(sg.get("split_of", sg["shot"]), {}).get("reuse") == "insert" and slot <= 1.5
        if src in seen and not designed: rep += slot
        seen.add(src)
    chk("replayed_frac", round(rep / total, 3), rep / total <= 0.10, "<= 0.10", "a viewer notices the same shot twice; the reference never replays a setup outside designed <=1.5 s inserts")
    # 2/3 motion
    ms = motion(a.video); ref_ms = motion(a.ref) if a.ref else None
    thr = (np.percentile(ref_ms, 15) if ref_ms else 1.0); ref_static = static_run(ref_ms, thr) if ref_ms else None
    chk("longest_static_s", static_run(ms, thr), static_run(ms, thr) <= (max(2.5, ref_static * 1.5) if ref_static is not None else 2.5), f"<= {max(2.5, (ref_static or 0) * 1.5):.1f} (ref {ref_static})", "seconds where almost nothing moves read as a frozen frame")
    chk("motion_mean", round(float(np.mean(ms)), 2), (float(np.mean(ms)) >= 0.5 * float(np.mean(ref_ms))) if ref_ms else True, f">= 0.5*ref ({0.5 * float(np.mean(ref_ms)):.2f})" if ref_ms else "n/a", "energy of the picture vs the reference")
    # 4/5 speech coverage + dead air
    vo = sorted(mix.get("vo", []), key=lambda v: v["t"]); cov = np.zeros(int(total) + 1)
    for v in vo:
        for s in range(int(v["t"]), min(int(total), int(v["t"] + v["dur"])) + 1): cov[s] = 1
    chk("speech_frac", round(float(cov.mean()), 2), float(cov.mean()) <= 0.75, "<= 0.75", "wall-to-wall narration; the reference breathes (music/SFX-led beats)")
    gaps = [round(b["t"] - (x["t"] + x["dur"]), 2) for x, b in zip(vo, vo[1:])]
    chk("longest_dead_s", max(gaps) if gaps else 0, (max(gaps) if gaps else 0) <= 3.0, "<= 3.0", "dead air between lines inside a dialogue run")
    # 6 line on speaker
    off = []
    for v in vo:
        sg = next((s for s in segs if s["t_in"] <= v["t"] < s["t_out"]), None)
        if not sg: continue
        shot = man.get(sg.get("split_of", sg["shot"]), {}); spk = v.get("line", "").split("_")[-1]
        if shot.get("reuse") == "insert": continue
        if spk not in shot.get("characters", []) and spk != "ORB": off.append((v.get("line"), sg["shot"]))
    chk("line_off_speaker", len(off), len(off) == 0, "== 0", f"a character line over a shot without that character: {off[:6]}")
    # 7 foley coverage
    fo = {f["shot"]: f for f in mix.get("foley", [])}; covered = 0
    for sg in segs:
        f = fo.get(sg["shot"]); slot = sg["t_out"] - sg["t_in"]
        if f and probe(f["file"]) >= 0.9 * slot: covered += 1
    chk("foley_cover", round(covered / len(segs), 2), covered / len(segs) >= 0.9, ">= 0.90", "generated foley must cover the slot it was cut for")
    # 8/9 text + cards
    texts = [o for sg in segs if sg["t_in"] < a.hook_window for o in sg.get("ops", []) if o.get("op") == "text"]
    chk("text_min_px", min([o.get("size", 96) for o in texts]) if texts else None, all(o.get("size", 96) >= 110 for o in texts), ">= 110", "hook text must read at phone size; the reference's pops fill ~15% of frame height")
    cards = [o for sg in segs for o in sg.get("ops", []) if o.get("op") == "cards"]
    chk("card_each_s", max([o.get("each", 0.4) for o in cards]) if cards else 0, all(o.get("each", 0.4) <= 0.6 for o in cards), "<= 0.6", "an archive stack is a whoosh, not a slideshow")
    # 10 music hole
    m = mix.get("music", {}); sfx = mix.get("sfx", []); hole = 0.0
    for s in m.get("sections", []):
        if s.get("gain_db", 0) <= -40 and not any(x["t"] < s["t1"] and x["t"] + probe(x["file"]) > s["t0"] for x in sfx): hole += s["t1"] - s["t0"]
    chk("music_hole_s", round(hole, 1), hole == 0, "== 0", "music out must be replaced by a drone/sfx bed, not silence")
    # 11 text hits
    hits = sum(1 for sg in segs if sg["t_in"] < a.hook_window for o in sg.get("ops", []) if o.get("op") == "text" and any(abs((sg["t_in"] + o.get("t_on", 0)) - x["t"]) <= 0.2 for x in sfx))
    chk("text_hits", f"{hits}/{len(texts)}", hits == len(texts), "== all", "every text pop in the hook lands with a hit")
    out = os.path.splitext(a.json or a.video)[0]; paths = strips(a.video, out + "_strips", dur)
    verdict = "PASS" if all(c["verdict"] == "PASS" for c in checks) else "FAIL"
    rep = {"video": a.video, "duration": dur, "verdict": verdict, "unheard": True, "checks": checks, "strips": paths, "rule": "NO delivery without verdict PASS AND every strip looked at AND the owner's ear check recorded"}
    json.dump(rep, open(a.json or out + "_watch.json", "w"), indent=1)
    for c in checks: print(f"  {c['verdict']} {c['check']}: {c['value']} ({c['threshold']}) — {c['why'][:90]}")
    print(f"watch_gate: {verdict}  | UNHEARD (no listening model ran)  | strips: {len(paths)} -> look at them before you say anything")
    sys.exit(0 if verdict == "PASS" else 1)
if __name__ == "__main__": main()
