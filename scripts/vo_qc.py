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
    ap = argparse.ArgumentParser(); ap.add_argument("--calibrate"); ap.add_argument("--t0", type=float); ap.add_argument("--t1", type=float); ap.add_argument("--out"); ap.add_argument("--lines"); ap.add_argument("--manifest"); ap.add_argument("--profile"); ap.add_argument("--json"); ap.add_argument("--tol", type=float, default=0.6)
    a = ap.parse_args()
    if a.calibrate:
        import whisper; y, sr = load(a.calibrate, a.t0, a.t1); m = whisper.load_model("base"); r = m.transcribe(a.calibrate, fp16=False)
        segs = [s for s in r["segments"] if (a.t0 is None or s["end"] > a.t0) and (a.t1 is None or s["start"] < a.t1)]
        nwords = sum(len(words(s["text"])) for s in segs); spoken = sum(s["end"] - s["start"] for s in segs)
        prof = {"source": a.calibrate, "window": [a.t0, a.t1], "pace_wps": round(nwords / max(spoken, 1e-6), 2), **perf(y, sr), "speech_frac": round(spoken / (len(y) / sr), 2)}
        json.dump(prof, open(a.out, "w"), indent=1); print("profile:", prof); return
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
        if len(words(l["text"])) >= 6 and not (0.75 * prof["pace_wps"] <= pace <= 1.35 * prof["pace_wps"]): why.append(f"pace {pace:.2f} vs ref {prof['pace_wps']}")
        if len(words(l["text"])) >= 6 and p["pitch_std_st"] < a.tol * prof["pitch_std_st"]: why.append(f"FLAT pitch std {p['pitch_std_st']} < {a.tol * prof['pitch_std_st']:.2f}")
        if len(words(l["text"])) >= 6 and p["energy_std_db"] < a.tol * prof["energy_std_db"]: why.append(f"flat energy {p['energy_std_db']} < {a.tol * prof['energy_std_db']:.2f}")
        row["verdict"] = "PASS" if not why else "FAIL: " + "; ".join(why); rows.append(row)
        if why: fails.append(f"{l['id']}: {row['verdict']}")
        print(f"  {row['verdict'][:4]} {l['id']:10s} {dur:5.1f}s pace {pace:4.2f} pitch_std {p['pitch_std_st']:4.2f} energy_std {p['energy_std_db']:4.2f} acc {acc:.2f}")
    json.dump({"profile": prof, "lines": rows, "verdict": "PASS" if not fails else "FAIL", "fails": fails}, open(a.json or os.path.join(a.lines, "VO_QC.json"), "w"), indent=1)
    print(f"vo_qc: {'PASS' if not fails else 'FAIL'} ({len(fails)} lines)"); sys.exit(0 if not fails else 1)
if __name__ == "__main__": main()
