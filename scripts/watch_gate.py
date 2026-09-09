#!/usr/bin/env python3
"""watch_gate.py v2 — the render-level WATCH gate. It grades the RENDERED PIXELS and the RENDERED AUDIO BUSES (stems), never the
spec, and it FAILS CLOSED: an unmeasurable check is a FAIL, a missing reference is a refusal, and every input is sha-bound.
  calibrate:  --calibrate --video REF.webm --vo-stem REF_vocals.wav [--nonvo-stem REF_no_vocals.wav] --out style_profile.json
              (measures the reference with the SAME code; every threshold below comes from that profile)
  gate:       --video CUT.mp4 --spec EDIT.json --mix MIX.json --manifest SHOTS.json --lane lane.json --profile style_profile.json
              --mix-report CUT_mix_report.json [--plate CUT_plate.mp4] [--json OUT.json]
  ref-selftest: --ref-selftest --video REF --vo-stem ... --profile ... (the reference must PASS its own render-level checks)
Checks (render-measured unless marked spec): replay_s (pHash runs), longest_static_s, motion_mean, speech_frac (VAD on the VO
stem), dead_air (VAD gaps; a designed hold must be CARRIED by the non-VO bus), line_off_speaker (spec+manifest; ORB on-camera
lines included), foley_cover (foley stem level per slot), text_min_px + text_animated (render minus plate), text_count (>=1 in the
hook), card_cadence (scene changes inside the card window), music_hole_s (non-VO stem level), text_hits (sfx stem onsets at each
measured text appearance), look_outliers (MAD within set, look_event segments excluded) + sharpness, density (transitions per
10 s bucket vs the reference buckets), cut_on_word (cuts vs whisper word onsets on the VO stem), speaker_change_cut (spec+manifest),
music_arc (section automation has >=3 levels on the raw music stem). Writes JSON with sha256 of every input + 4 fps strips."""
import argparse, hashlib, json, os, re, subprocess, sys
import numpy as np
from scipy.fft import dctn
def sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def probe(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)
def frames(video, fps, w, h, pix="gray", t0=None, dur=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(t0)] if t0 is not None else []) + (["-t", str(dur)] if dur else []) + ["-i", video, "-vf", f"fps={fps},scale={w}:{h}", "-pix_fmt", pix, "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout; ch = 1 if pix == "gray" else 3; n = len(raw) // (w * h * ch)
    return np.frombuffer(raw[: n * w * h * ch], dtype=np.uint8).reshape(n, h, w, ch).squeeze()
# ---------- picture ----------
def motion_per_sec(video, fps=4, w=160, h=90):
    fr = frames(video, fps, w, h).astype(np.float32); d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)) if len(fr) > 1 else np.zeros(0)
    return [float(d[i * fps:(i + 1) * fps].mean()) for i in range(len(d) // fps)] if len(d) >= fps else [float(d.mean()) if len(d) else 0.0]
def static_run(per_sec, thr):
    best = cur = 0
    for m in per_sec: cur = cur + 1 if m < thr else 0; best = max(best, cur)
    return best
def phashes(video, fps=4):
    fr = frames(video, fps, 32, 32).astype(np.float32); out = []
    for f in fr:
        d = dctn(f, norm="ortho")[:8, :8].flatten()[1:]; out.append(np.packbits(d > np.median(d)).tobytes())
    return out
def hamming(a, b): return int(bin(int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).count("1"))
def replay_runs(hashes, fps=4, min_s=1.5, max_ham=2, min_gap_s=1.0):
    """runs of >= min_s whose frames match (hamming<=max_ham, same offset) an EARLIER stretch of the render = the viewer sees it twice."""
    n = len(hashes); need = int(min_s * fps); hits = []; used = np.zeros(n, bool)
    for i in range(n):
        if used[i]: continue
        for j in range(0, i - int(min_gap_s * fps)):
            if hamming(hashes[i], hashes[j]) > max_ham: continue
            k = 0
            while i + k < n and j + k < i and hamming(hashes[i + k], hashes[j + k]) <= max_ham: k += 1
            if k >= need:
                hits.append({"t": round(i / fps, 2), "dur": round(k / fps, 2), "repeats": round(j / fps, 2)}); used[i:i + k] = True; break
    return hits
def scene_times(video, th, t0=0.0, dur=None):
    cmd = ["ffmpeg", "-hide_banner", "-ss", str(t0)] + (["-t", str(dur)] if dur else []) + ["-i", video, "-vf", f"select='gt(scene,{th})',showinfo", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    return sorted(float(m) for m in re.findall(r"pts_time:\s*([0-9.]+)", err))
def look_stats(video, segs, man, fps=2):
    fr = frames(video, fps, 96, 54, "rgb24").astype(np.float32); luma = fr.mean(axis=(1, 2, 3)) / 255; con = fr.std(axis=(1, 2, 3)) / 255; sat = (fr.max(axis=3) - fr.min(axis=3)).mean(axis=(1, 2)) / 255
    per = []
    for sg in segs:
        i0, i1 = int(sg["t_in"] * fps), max(int(sg["t_in"] * fps) + 1, int(sg["t_out"] * fps)); m = man.get(sg.get("split_of", sg["shot"]), {})
        per.append({"shot": sg["shot"], "set": m.get("set", "?"), "event": bool(m.get("look_event") or sg.get("look_event")), "v": [float(luma[i0:i1].mean()), float(con[i0:i1].mean()), float(sat[i0:i1].mean())]})
    return per
def mad_outliers(per, k=3.5):
    out = []
    for st in set(p["set"] for p in per):
        grp = [p for p in per if p["set"] == st and not p["event"]]
        if len(grp) < 4: continue
        arr = np.array([p["v"] for p in grp]); med = np.median(arr, axis=0); mad = np.median(np.abs(arr - med), axis=0) * 1.4826 + 1e-3
        out += [p["shot"] for p, row in zip(grp, arr) if np.any(np.abs(row - med) / mad > k)]
    return out
def sharpness(video, fps=2):
    import cv2
    fr = frames(video, fps, 480, 270); return [float(cv2.Laplacian(f, cv2.CV_32F).var()) for f in fr]
# ---------- audio ----------
def load_mono(p, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr
def frame_db(y, sr, hop_s=0.05):
    hop = int(sr * hop_s); n = len(y) // hop; f = y[: n * hop].reshape(n, hop); return 20 * np.log10(np.sqrt((f ** 2).mean(axis=1)) + 1e-9)
def vad(stem, hop_s=0.05, min_gap_s=0.3):
    y, sr = load_mono(stem); db = frame_db(y, sr, hop_s); floor = np.percentile(db, 10); thr = max(floor + 15, -50)
    act = db > thr; gap = int(min_gap_s / hop_s); i = 0
    while i < len(act):   # close short gaps (inter-word)
        if not act[i]:
            j = i
            while j < len(act) and not act[j]: j += 1
            if j - i <= gap and i > 0 and j < len(act): act[i:j] = True
            i = j
        else: i += 1
    return act, hop_s
def longest_gaps(act, hop_s):
    gaps = []; i = 0
    while i < len(act):
        if not act[i]:
            j = i
            while j < len(act) and not act[j]: j += 1
            gaps.append((round(i * hop_s, 2), round((j - i) * hop_s, 2))); i = j
        else: i += 1
    return sorted(gaps, key=lambda g: -g[1])
def words_from(stem):
    import whisper; r = whisper.load_model("base").transcribe(stem, fp16=False, word_timestamps=True)
    return [(w["word"].strip(), float(w["start"]), float(w["end"])) for s in r["segments"] for w in s.get("words", [])]
def onsets(stem):
    import librosa; y, sr = load_mono(stem); return [float(t) for t in librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=False)], y, sr
def buckets(times, t1, w=10.0): return [sum(1 for t in times if b <= t < b + w) for b in np.arange(0, t1, w)]
# ---------- calibrate ----------
def calibrate(a):
    dur = probe(a.video); ms = motion_per_sec(a.video); thr = float(np.percentile(ms, 15)); act, hop = vad(a.vo_stem); gaps = longest_gaps(act, hop)
    cuts = scene_times(a.video, 0.30, 0, a.t1); trans = scene_times(a.video, 0.10, 0, a.t1); words = words_from(a.vo_stem); starts = [w[1] for w in words]
    cow = round(sum(1 for c in cuts if any(abs(c - s) <= 0.12 for s in starts)) / len(cuts), 2) if cuts else 0
    hashes = phashes(a.video); rep = replay_runs(hashes); sh = sharpness(a.video)
    per = [{"shot": f"c{i}", "set": "ref", "event": False, "v": None} for i in range(0)]
    prof = {"source": a.video, "video_sha": sha(a.video), "vo_stem": a.vo_stem, "vo_stem_sha": sha(a.vo_stem), "window_s": a.t1, "duration": dur,
            "motion_mean": round(float(np.mean(ms)), 2), "motion_p15": round(thr, 2), "longest_static_s": static_run(ms, thr),
            "speech_frac": round(float(act.mean()), 3), "longest_gap_s": gaps[0][1] if gaps else 0, "gaps_top3": gaps[:3],
            "hard_cuts": len(cuts), "transitions": len(trans), "transitions_per_10s": buckets(trans, a.t1), "cut_on_word_rate": cow,
            "replay_runs": rep, "sharpness_median": round(float(np.median(sh)), 1),
            "text_min_frac_h": 0.15, "text_min_frac_h_source": "hook_event_ledger: pops fill ~15% of frame height (not measurable without a plate)",
            "tolerances": {"static_x": 1.5, "motion_x": 0.5, "speech_x": 1.1, "gap_x": 1.25, "density_x": 0.8, "cut_on_word_x": 0.8, "sharp_x": 0.5, "look_k": 3.5, "foley_under_vo_db": 12, "hole_lu": 20}}
    if a.nonvo_stem:
        y, sr = load_mono(a.nonvo_stem); db = frame_db(y, sr, 0.1); prof["nonvo_dyn_range_db"] = round(float(np.percentile(db, 95) - np.percentile(db, 5)), 1); prof["nonvo_stem_sha"] = sha(a.nonvo_stem)
    json.dump(prof, open(a.out, "w"), indent=1); print(json.dumps(prof, indent=1)); return 0
# ---------- gate ----------
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--calibrate", action="store_true"); ap.add_argument("--ref-selftest", action="store_true"); ap.add_argument("--video", required=True); ap.add_argument("--vo-stem"); ap.add_argument("--nonvo-stem"); ap.add_argument("--out"); ap.add_argument("--t1", type=float, default=45.0)
    ap.add_argument("--spec"); ap.add_argument("--mix"); ap.add_argument("--manifest"); ap.add_argument("--lane"); ap.add_argument("--profile"); ap.add_argument("--mix-report"); ap.add_argument("--plate"); ap.add_argument("--json"); ap.add_argument("--hook-window", type=float, default=45.0)
    a = ap.parse_args()
    if a.calibrate: return calibrate(a)
    if not a.profile or not os.path.exists(a.profile): print("watch_gate REFUSED: --profile (calibrated reference style profile) is required"); return 2
    P = json.load(open(a.profile)); T = P["tolerances"]; checks = []; shas = {"video": sha(a.video), "profile": sha(a.profile)}
    def chk(name, val, ok, thr, why, level="render"): checks.append({"check": name, "value": val, "threshold": thr, "verdict": "PASS" if ok else "FAIL", "level": level, "why": why})
    dur = probe(a.video); hw = min(a.hook_window, dur)
    # --- render-only checks (also what the reference self-test runs) ---
    rep = replay_runs(phashes(a.video)); rs = round(sum(r["dur"] for r in rep), 2)
    chk("replay_s", rs, rs == 0, "== 0", f"seconds the viewer sees frames already shown (pHash runs >=1.5 s): {rep[:5]}")
    ms = motion_per_sec(a.video); thr = P["motion_p15"]; st = static_run(ms, thr); st_max = max(2.5, P["longest_static_s"] * T["static_x"])
    chk("longest_static_s", st, st <= st_max, f"<= {st_max:.1f} (ref {P['longest_static_s']} x{T['static_x']})", "seconds where almost nothing moves read as a frozen frame")
    mm = round(float(np.mean(ms)), 2); chk("motion_mean", mm, mm >= T["motion_x"] * P["motion_mean"], f">= {T['motion_x'] * P['motion_mean']:.2f}", "picture energy vs the reference")
    trans = scene_times(a.video, 0.10, 0, hw); cuts = scene_times(a.video, 0.30, 0, hw); b = buckets(trans, hw); rb = P["transitions_per_10s"][: len(b)]; floor = [round(T["density_x"] * x, 1) for x in rb]
    chk("density_per_10s", b, all(x >= f for x, f in zip(b, floor)), f">= {floor} (ref {rb} x{T['density_x']})", "edit events per 10 s in the hook, bucket by bucket, measured on the render like the reference")
    sh = sharpness(a.video); shm = round(float(np.median(sh)), 1); chk("sharpness_median", shm, shm >= T["sharp_x"] * P["sharpness_median"], f">= {T['sharp_x'] * P['sharpness_median']:.1f} (ref {P['sharpness_median']})", "a soft upscale reads as unfinished")
    # VO stem: either given, or taken from the mix report
    MR = json.load(open(a.mix_report)) if a.mix_report and os.path.exists(a.mix_report) else {}
    stem = lambda k: (MR.get("stems", {}).get(k) or {}).get("path")
    vo_stem = a.vo_stem or stem("vo"); nonvo = a.nonvo_stem or stem("nonvo")
    if vo_stem and os.path.exists(vo_stem):
        shas["vo_stem"] = sha(vo_stem); act, hop = vad(vo_stem); sf = round(float(act[: int(hw / hop)].mean()), 3); sf_max = round(P["speech_frac"] * T["speech_x"], 3)
        chk("speech_frac", sf, sf <= sf_max, f"<= {sf_max} (ref {P['speech_frac']} x{T['speech_x']})", "speech density measured by VAD on the rendered VO stem")
        gaps = [g for g in longest_gaps(act, hop) if g[0] < hw]; gap_max = round(P["longest_gap_s"] * T["gap_x"], 2); bad = []
        if nonvo and os.path.exists(nonvo):
            y, sr = load_mono(nonvo); db = frame_db(y, sr, 0.1); med = float(np.median(db[db > -80])) if np.any(db > -80) else -80
            for t, g in gaps:
                if g <= gap_max: continue
                seg = db[int(t / 0.1): int((t + g) / 0.1)]; carried = float(np.mean(seg > med - T["hole_lu"])) if len(seg) else 0.0
                if carried < 0.9: bad.append({"t": t, "gap": g, "carried_frac": round(carried, 2)})
            chk("dead_air", bad, not bad, f"gaps > {gap_max}s must be carried by the non-VO bus (>= 90% above median-{T['hole_lu']} dB)", "a hold is fine when sound carries it; silence over a hero shot is dead air")
        else: chk("dead_air", None, False, "measured", "no non-VO stem to measure carrying sound: unmeasurable = FAIL")
        words = words_from(vo_stem); starts = [w[1] for w in words if w[1] < hw]
        cow = round(sum(1 for c in cuts if any(abs(c - s) <= 0.12 for s in starts)) / len(cuts), 2) if cuts else 0.0
        chk("cut_on_word_rate", cow, cow >= T["cut_on_word_x"] * P["cut_on_word_rate"], f">= {T['cut_on_word_x'] * P['cut_on_word_rate']:.2f} (ref {P['cut_on_word_rate']})", "cuts land on WORD onsets (whisper on the VO stem), not on design hits the mix builder placed itself")
    else:
        for n in ("speech_frac", "dead_air", "cut_on_word_rate"): chk(n, None, False, "measured", "no VO stem: unmeasurable = FAIL")
    if a.ref_selftest:
        return finish(a, checks, shas, dur, P)
    # --- checks that need the spec / mix / manifest / lane ---
    for n in ("spec", "mix", "manifest", "lane"):
        if not getattr(a, n) or not os.path.exists(getattr(a, n)): print(f"watch_gate REFUSED: --{n} required"); return 2
    spec = json.load(open(a.spec)); mix = json.load(open(a.mix)); man = {s["id"]: s for s in json.load(open(a.manifest))["shots"]}; lane = json.load(open(a.lane))
    shas.update({"spec": sha(a.spec), "mix": sha(a.mix), "manifest": sha(a.manifest), "lane": sha(a.lane)}); segs = spec["segments"]
    if MR: shas["mix_report"] = sha(a.mix_report); shas["stems"] = {k: v["sha"] for k, v in MR.get("stems", {}).items()}
    # spec-level replay twin keyed on (src, window) OVERLAP — a later window of the same rolling take is a designed return, the same seconds are not
    seen = []; rep2 = []
    for sg in segs:
        key = sg["src"]; t0 = sg.get("t0", 0.0); slot = sg["t_out"] - sg["t_in"]; designed = man.get(sg.get("split_of", sg["shot"]), {}).get("reuse") == "insert" and slot <= 1.5
        ov = [s for s in seen if s[0] == key and not (t0 + slot <= s[1] or t0 >= s[2])]
        if ov and not designed: rep2.append(sg["shot"])
        seen.append((key, t0, t0 + slot))
    chk("replay_windows", rep2, not rep2, "== []", "segments re-showing the same seconds of a source (window overlap, not filename)", "spec")
    # line on speaker (ORB on-camera lines included; vo lines pass)
    vo = sorted(mix.get("vo", []), key=lambda v: v["t"]); off = []
    for v in vo:
        sg = next((s for s in segs if s["t_in"] <= v["t"] < s["t_out"]), None)
        if not sg: continue
        shot = man.get(sg.get("split_of", sg["shot"]), {}); spk = v.get("speaker") or v.get("line", "").split("_")[-1]
        if shot.get("reuse") == "insert" or sg.get("reaction_of"): continue
        on_cam = v.get("on_camera") is True or (spk != "ORB")
        if on_cam and spk not in shot.get("characters", []): off.append((v.get("line"), sg["shot"]))
    chk("line_off_speaker", len(off), len(off) == 0, "== 0", f"an on-camera line over a shot without that character: {off[:6]}", "spec")
    # speaker-change cut: a new speaker gets a cut within 0.15 s to a shot that holds them (CU/MCU/ECU/OTS/MS)
    prev = None; need = 0; got = 0; miss = []
    for v in vo:
        spk = v.get("speaker") or v.get("line", "").split("_")[-1]
        if prev is not None and spk != prev:
            need += 1; sg = next((s for s in segs if abs(s["t_in"] - v["t"]) <= 0.15), None); shot = man.get((sg or {}).get("split_of", (sg or {}).get("shot")), {})
            if sg and (spk in shot.get("characters", []) or sg.get("reaction_of")) and shot.get("shot_type") in ("CU", "MCU", "ECU", "OTS", "MS", "INS"): got += 1
            else: miss.append(v.get("line"))
        prev = spk
    rate = round(got / need, 2) if need else 1.0; chk("speaker_change_cut_rate", rate, rate >= 0.8, ">= 0.80 (ref 7/7)", f"speaker changes without a cut to that speaker: {miss[:6]}", "spec")
    # foley cover: rendered foley stem level per slot
    fs = stem("foley")
    if fs and os.path.exists(fs):
        y, sr = load_mono(fs); db = frame_db(y, sr, 0.1); vs = stem("vo"); vdb = frame_db(*load_mono(vs), 0.1) if vs and os.path.exists(vs) else None; cov = 0; weak = []
        for sg in segs:
            i0, i1 = int(sg["t_in"] / 0.1), max(int(sg["t_in"] / 0.1) + 1, int(sg["t_out"] / 0.1)); seg = db[i0:i1]
            if len(seg) == 0: continue
            active = float(np.mean(seg > -45)); ok = active >= 0.9
            if ok and vdb is not None:
                vseg = vdb[i0:i1]; both = (vseg > -45) & (seg > -45)
                if both.any() and float(np.mean((vseg - seg)[both])) > T["foley_under_vo_db"]: ok = False; weak.append(sg["shot"])
            cov += ok
        fc = round(cov / len(segs), 2); chk("foley_cover", fc, fc >= 0.9, f">= 0.90 (present >=90% of slot and within {T['foley_under_vo_db']} dB of VO)", f"foley measured on the rendered foley stem; too quiet under VO: {weak[:6]}")
    else: chk("foley_cover", None, False, "measured", "no foley stem in the mix report: unmeasurable = FAIL")
    # text: count, size, animation — render minus plate
    R = json.load(open(a.video.replace(".mp4", "_report.json"))) if os.path.exists(a.video.replace(".mp4", "_report.json")) else None
    texts = [o for s in (R or {}).get("segments", []) for o in s.get("abs_ops", []) if o["op"] in ("text", "text2") and o["appear"] < hw] if R else [dict(op=o["op"], appear=sg["t_in"] + o["t_on"] - o.get("lead", 0.3), t_off=sg["t_in"] + o.get("t_off", 0), text=o.get("text")) for sg in segs if sg["t_in"] < hw for o in sg.get("ops", []) if o.get("op") in ("text", "text2")]
    chk("text_count", len(texts), len(texts) >= 1, ">= 1 in the hook", "a hook without a single text pop is a Law 4 failure, not a vacuous pass", "spec")
    tb = P.get("text_bands", {"pops_per_45s": [4, 8], "on_screen_s": [0.5, 2.5]}); n45 = round(len(texts) * 45.0 / max(hw, 1), 1)
    chk("text_pops_per_45s", n45, tb["pops_per_45s"][0] <= n45 <= tb["pops_per_45s"][1], f"in {tb['pops_per_45s']} (reference ledger: 5 pops / 45 s)", "text is sparse and designed; a pop per claim reads as captions", "spec")
    longs = [round(o["t_off"] - o["appear"], 2) for o in texts if "t_off" in o and o["t_off"] is not None]
    chk("text_on_screen_s", longs, all(tb["on_screen_s"][0] <= x <= tb["on_screen_s"][1] for x in longs), f"each in {tb['on_screen_s']} s", "the reference's pops hold 0.6-2.2 s: long enough to read, gone before it becomes a caption", "spec")
    if a.plate and os.path.exists(a.plate) and texts:
        shas["plate"] = sha(a.plate); W, H = 1920, 1080; hs = []; anim = []
        for o in texts:
            def bbox_h(t):
                fa = frames(a.video, 24, 480, 270, t0=max(0, t), dur=1 / 24.0); fp = frames(a.plate, 24, 480, 270, t0=max(0, t), dur=1 / 24.0)
                if len(fa) == 0 or len(fp) == 0: return 0
                d = np.abs(fa[0].astype(int) - fp[0].astype(int)) > 40; rows = np.where(d.sum(axis=1) > 3)[0]
                return int((rows.max() - rows.min() + 1) * (H / 270)) if len(rows) else 0
            h1, h2 = bbox_h(o["appear"] + 0.10), bbox_h(o["appear"] + 0.40); hs.append(h2); anim.append(abs(h1 - h2) / max(h2, 1))
        floor = int(P["text_min_frac_h"] * H); chk("text_min_px", min(hs), min(hs) >= floor, f">= {floor} (ref {P['text_min_frac_h']} of frame height)", f"rendered text block height (render minus plate): {hs}")
        chk("text_animated", [round(x, 2) for x in anim], all(x >= 0.05 for x in anim), ">= 0.05 change in the first 0.3 s", "a pop must move; a static chip is not designed text")
    else:
        chk("text_min_px", None, False, "measured", "no --plate render: text size unmeasurable = FAIL"); chk("text_animated", None, False, "measured", "no --plate render: unmeasurable = FAIL")
    # cards: scene changes inside the card window on the render
    cards = [o for s in (R or {}).get("segments", []) for o in s.get("abs_ops", []) if o["op"] == "cards"] if R else []
    if cards:
        bad = []
        for c in cards:
            tr = [t for t in scene_times(a.video, 0.10, c["t0"], c["t1"] - c["t0"])]; pts = [0.0] + tr + [c["t1"] - c["t0"]]; sp = max(b2 - a2 for a2, b2 in zip(pts, pts[1:]))
            if len(tr) < c["n"] - 1 or sp > 0.6: bad.append({"t0": c["t0"], "changes": len(tr), "needed": c["n"] - 1, "max_spacing": round(sp, 2)})
        chk("card_cadence", bad, not bad, "each card <= 0.6 s, measured as scene changes", "an archive stack is a whoosh, not a slideshow")
    # music hole + hits + arc on the rendered buses
    nv = stem("nonvo"); sx = stem("sfx"); mr = stem("music_raw") or stem("music")
    if nv and os.path.exists(nv):
        y, sr = load_mono(nv); db = frame_db(y, sr, 0.1); med = float(np.median(db[db > -80])) if np.any(db > -80) else -80; low = db < med - T["hole_lu"]; hole = 0; run = 0
        for x in low[: int(dur / 0.1)]:
            run = run + 1 if x else 0
            if run >= 5: hole += 1
        chk("music_hole_s", round(hole * 0.1, 1), hole == 0, f"== 0 (non-VO bus < median-{T['hole_lu']} dB for >= 0.5 s)", "music out must be replaced by drone/sfx, not silence — measured on the rendered non-VO bus")
    else: chk("music_hole_s", None, False, "measured", "no non-VO stem: unmeasurable = FAIL")
    if texts:
        if sx and os.path.exists(sx):
            ons, y, sr = onsets(sx); pk = frame_db(y, sr, 0.05); hits = 0; miss = []
            for o in texts:
                near = [t for t in ons if abs(t - o["appear"]) <= 0.2 and pk[min(len(pk) - 1, int(t / 0.05))] > -30]
                if near: hits += 1
                else: miss.append(o.get("text"))
            chk("text_hits", f"{hits}/{len(texts)}", hits == len(texts), "== all (onset in the sfx stem within 0.2 s, > -30 dBFS)", f"text pops without a hit on the rendered sfx bus: {miss[:5]}")
        else: chk("text_hits", f"0/{len(texts)}", False, "== all", "no sfx stem in the mix report: the design bus never reached the mix (v3's failure) = FAIL")
    if mr and os.path.exists(mr):
        y, sr = load_mono(mr); db = frame_db(y, sr, 0.5); lv = db[db > -70]; levels = len(set(np.round(lv / 3.0))) if len(lv) else 0; rng = round(float(np.percentile(lv, 95) - np.percentile(lv, 5)), 1) if len(lv) else 0
        chk("music_arc", {"levels": int(levels), "range_db": rng}, levels >= 3 and rng >= 6, ">= 3 distinct levels and >= 6 dB range on the raw music stem", "the cue must move (sections/hits), measured pre-duck so VO ducking cannot fake it")
    else: chk("music_arc", None, False, "measured", "no music stem: unmeasurable = FAIL")
    # look
    per = look_stats(a.video, segs, man); outl = mad_outliers(per, T["look_k"]); ceil = max(1, len(per) // 10)
    chk("look_outliers", outl, len(outl) <= ceil, f"<= {ceil} (MAD k={T['look_k']}, look_event segments excluded)", "segments far from their own set's look, designed events excluded")
    return finish(a, checks, shas, dur, P, lane)
def strips(video, outdir, dur, fps=4):
    os.makedirs(outdir, exist_ok=True); paths = []
    for s in range(0, int(dur) + 1, 33):
        p = os.path.join(outdir, f"strip_{s:03d}s.jpg"); subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(s), "-t", "33", "-i", video, "-vf", f"fps={fps},scale=200:-1,tile=8x17", "-frames:v", "1", "-q:v", "4", p]); paths.append(p)
    return paths
def finish(a, checks, shas, dur, P, lane=None):
    out = os.path.splitext(a.json or a.video)[0]; paths = strips(a.video, out + "_strips", dur); verdict = "PASS" if all(c["verdict"] == "PASS" for c in checks) else "FAIL"
    rep = {"video": a.video, "duration": dur, "verdict": verdict, "profile": a.profile, "sha256": dict(shas, strips={os.path.basename(p): sha(p) for p in paths}), "checks": checks, "strips": paths, "promise_proof": (lane or {}).get("promise", {}).get("proof_shots"),
           "rule": "deliver.py recomputes every sha above; WATCH_NOTES must name each strip's sha8 and agree with these numbers; a listen record is REQUIRED"}
    json.dump(rep, open(a.json or out + "_watch.json", "w"), indent=1)
    for c in checks: print(f"  {c['verdict']} {c['check']} [{c['level']}]: {str(c['value'])[:70]} ({c['threshold']}) — {c['why'][:80]}")
    print(f"watch_gate v2: {verdict} ({sum(c['verdict']=='FAIL' for c in checks)} FAIL / {len(checks)})  strips: {len(paths)} -> look at them; notes must cite their sha8")
    return 0 if verdict == "PASS" else 1
if __name__ == "__main__": sys.exit(main())
