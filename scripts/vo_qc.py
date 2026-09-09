#!/usr/bin/env python3
"""vo_qc.py — voice-line quality gate (Law 2). Measures each line against a reference narration's PERFORMANCE profile, not just
its words: pace (words/s), pitch variance (semitone std of voiced F0), energy variance (RMS dB std), and word accuracy (whisper).
  --calibrate REF.wav|mp4 [--t0 --t1] --out profile.json      measure the reference (e.g. the MrBeast hook narration)
  --lines DIR --manifest VO_LINES_MANIFEST.json --profile profile.json [--json OUT]   gate every line; FAIL closed
Flat reads (pitch std below the floor), rushed/slow pace, and wrong words all FAIL. Thresholds = reference * tolerance."""
import argparse, json, os, re, subprocess, sys
import numpy as np, librosa
def load(p, t0=None, t1=None):
    y, sr = librosa.load(p, sr=22050, mono=True, offset=t0 or 0.0, duration=(t1 - t0) if (t0 is not None and t1 is not None) else None); return y, sr
def perf(y, sr):
    f0, vf, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr, frame_length=2048)
    v = f0[~np.isnan(f0)]; st = 12 * np.log2(v / np.median(v)) if len(v) > 10 else np.zeros(1)
    rms = librosa.feature.rms(y=y)[0]; db = 20 * np.log10(rms + 1e-6); db = db[db > db.max() - 40]
    return {"pitch_std_st": round(float(np.std(st)), 2), "pitch_range_st": round(float(np.percentile(st, 95) - np.percentile(st, 5)), 2) if len(st) > 1 else 0.0, "energy_std_db": round(float(np.std(db)), 2), "voiced_frac": round(float(np.mean(vf)), 2)}
def words(txt): return re.findall(r"[a-z0-9']+", txt.lower())
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--calibrate"); ap.add_argument("--t0", type=float); ap.add_argument("--t1", type=float); ap.add_argument("--out"); ap.add_argument("--lines"); ap.add_argument("--manifest"); ap.add_argument("--profile"); ap.add_argument("--json"); ap.add_argument("--tol", type=float, default=0.6); ap.add_argument("--stem", action="store_true", help="separate vocals with demucs before calibrating (never calibrate on a MIX)"); ap.add_argument("--cues", help="reference cue JSON (words.json) -> per-cue floors"); ap.add_argument("--measure-cps", help="line dir: print chars/s per line from whisper-verified duration (lane speech profile)"); ap.add_argument("--lane"); ap.add_argument("--min-voiced-s", type=float, default=0.8)
    a = ap.parse_args()
    if a.measure_cps:
        import whisper; m = whisper.load_model("base"); man = json.load(open(a.manifest))["lines"]; cps = []
        for l in man:
            f = os.path.join(a.measure_cps, l["id"] + ".mp3")
            if not os.path.exists(f): continue
            y, sr = load(f); dur = len(y) / sr; heard = m.transcribe(f, fp16=False)["text"]; import difflib; acc = difflib.SequenceMatcher(None, " ".join(words(l["text"])), " ".join(words(heard))).ratio()
            cps.append((l["id"], round(l["chars"] / dur, 1), round(dur, 2), round(acc, 2))); print(f"  {l['id']:10s} {l['chars']:4d} chars / {dur:5.2f}s = {l['chars']/dur:4.1f} chars/s (acc {acc:.2f})")
        v = round(float(np.median([c[1] for c in cps])), 1) if cps else None; print(f"chars/s median = {v} over {len(cps)} lines -> lane.speech.chars_per_sec")
        if a.lane and v:
            L = json.load(open(a.lane)); L.setdefault("speech", {})["chars_per_sec"] = v; L["speech"]["source"] = f"measured {a.measure_cps} ({len(cps)} lines, whisper-verified)"; json.dump(L, open(a.lane, "w"), indent=1); print("lane.json speech.chars_per_sec =", v)
        return
    if a.calibrate:
        src = a.calibrate
        if a.stem:
            import subprocess, tempfile; d = os.path.join(os.path.dirname(a.out) or ".", "stems"); os.makedirs(d, exist_ok=True); base = os.path.splitext(os.path.basename(src))[0]; voc = os.path.join(d, "htdemucs", base, "vocals.wav")
            if not os.path.exists(voc): subprocess.run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-o", d, src], check=True)
            src = voc; print("calibrating on the VOCAL STEM:", voc)
        import whisper; y, sr = load(src, a.t0, a.t1); m = whisper.load_model("base"); r = m.transcribe(src, fp16=False)
        segs = [s for s in r["segments"] if (a.t0 is None or s["end"] > a.t0) and (a.t1 is None or s["start"] < a.t1)]
        nwords = sum(len(words(s["text"])) for s in segs); spoken = sum(s["end"] - s["start"] for s in segs)
        prof = {"source": src, "stem": bool(a.stem), "window": [a.t0, a.t1], "pace_wps": round(nwords / max(spoken, 1e-6), 2), **perf(y, sr), "speech_frac": round(spoken / (len(y) / sr), 2)}
        if a.cues:   # per-cue floors: measure every reference LINE like we measure ours; floor = p25 of the reference lines (not a pooled multi-speaker number)
            cues = [c for c in json.load(open(a.cues)).get("cues_0_60s", []) if (a.t1 is None or c["t1"] <= a.t1)]; rows = []
            for c in cues:
                yy = y[int(c["t0"] * sr): int(c["t1"] * sr)]
                if len(yy) < sr * 0.5: continue
                pp = perf(yy, sr); rows.append({"text": c["text"], "dur": round(c["t1"] - c["t0"], 2), **pp})
            voiced = [r_ for r_ in rows if r_["voiced_frac"] * r_["dur"] >= a.min_voiced_s]
            prof["per_cue"] = rows; prof["cue_floor_pitch_std_st"] = round(float(np.percentile([r_["pitch_std_st"] for r_ in voiced], 25)), 2) if voiced else None; prof["cue_floor_energy_std_db"] = round(float(np.percentile([r_["energy_std_db"] for r_ in voiced], 25)), 2) if voiced else None; prof["cue_median_pitch_std_st"] = round(float(np.median([r_["pitch_std_st"] for r_ in voiced])), 2) if voiced else None
            print(f"per-cue: {len(voiced)} voiced cues; pitch_std p25 {prof['cue_floor_pitch_std_st']} median {prof['cue_median_pitch_std_st']}; energy_std p25 {prof['cue_floor_energy_std_db']}")
        json.dump(prof, open(a.out, "w"), indent=1); print("profile:", {k: v for k, v in prof.items() if k != "per_cue"}); return
    import whisper; m = whisper.load_model("base"); prof = json.load(open(a.profile)); man = json.load(open(a.manifest))["lines"]; rows = []; fails = []
    for l in man:
        f = os.path.join(a.lines, l["id"] + ".mp3")
        if not os.path.exists(f): fails.append(f"{l['id']}: missing audio"); continue
        y, sr = load(f); p = perf(y, sr); heard = m.transcribe(f, fp16=False)["text"]
        import difflib; acc = difflib.SequenceMatcher(None, " ".join(words(l["text"])), " ".join(words(heard))).ratio()
        dur = len(y) / sr; pace = len(words(l["text"])) / max(dur, 1e-6)
        row = {"id": l["id"], "dur": round(dur, 2), "pace_wps": round(pace, 2), "acc": round(acc, 2), **p, "heard": heard.strip()[:60]}
        why = []
        if acc < 0.85: why.append(f"words {acc:.2f}")
        judged = p["voiced_frac"] * dur >= a.min_voiced_s   # every line with >= 0.8 s of voiced audio is judged (no word-count exemption)
        pf = prof.get("cue_floor_pitch_std_st") or a.tol * prof["pitch_std_st"]; ef = prof.get("cue_floor_energy_std_db") or a.tol * prof["energy_std_db"]
        if not prof.get("stem"): why.append("PROFILE NOT CALIBRATED ON A VOCAL STEM (vo_qc --calibrate --stem): verdict void")
        if judged and len(words(l["text"])) >= 4 and not (0.75 * prof["pace_wps"] <= pace <= 1.35 * prof["pace_wps"]): why.append(f"pace {pace:.2f} vs ref {prof['pace_wps']}")
        if judged and p["pitch_std_st"] < pf: why.append(f"FLAT pitch std {p['pitch_std_st']} < floor {pf:.2f}")
        if judged and p["energy_std_db"] < ef: why.append(f"flat energy {p['energy_std_db']} < floor {ef:.2f}")
        if not judged: row["note"] = f"too little voiced audio to judge ({p['voiced_frac'] * dur:.2f}s)"
        row["verdict"] = "PASS" if not why else "FAIL: " + "; ".join(why); rows.append(row)
        if why: fails.append(f"{l['id']}: {row['verdict']}")
        print(f"  {row['verdict'][:4]} {l['id']:10s} {dur:5.1f}s pace {pace:4.2f} pitch_std {p['pitch_std_st']:4.2f} energy_std {p['energy_std_db']:4.2f} acc {acc:.2f}")
    json.dump({"profile": prof, "lines": rows, "verdict": "PASS" if not fails else "FAIL", "fails": fails}, open(a.json or os.path.join(a.lines, "VO_QC.json"), "w"), indent=1)
    print(f"vo_qc: {'PASS' if not fails else 'FAIL'} ({len(fails)} lines)"); sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
