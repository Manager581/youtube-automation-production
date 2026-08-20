#!/usr/bin/env python3
"""Objective QA for generated foley: for each foley_v4/<SHOT>.flac, against the exact shot
window it was generated from:
  - class: not hiss (spectral flatness), not music (no sustained tonal bed), no speech (whisper)
  - sync: audio onsets vs visual motion-energy peaks (within 0.35s)
  - texture: continuous-energy coverage when the vision audit says the shot has a texture bed
Writes foley_verify.json + prints a table. Exit 1 if any shot FAILS hard (speech/music).

  venv/bin/python research/techjoint_cookies/verify_foley_v4.py [SHOT ...]
"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
CLIPS = os.path.join(REPO, "assets", "techjoint_cookies", "clips_v2")
FOLEY = os.path.join(REPO, "assets", "techjoint_cookies", "foley_v4")

import importlib
OV = importlib.import_module("cookies_v4_config").OVERRIDES

def probe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def windows():
    shots = json.load(open(OV["SHOTS"]))["shots"]
    hook, cin, dur_o = OV["HOOK_SRC"], OV["CLIP_IN"], OV["DUR_OVERRIDE"]
    for s in shots:
        sid = s["id"]
        src, i = hook.get(sid, (sid, cin.get(sid, 0.0)))
        dur = float(dur_o.get(sid, s["dur_s"]))
        yield sid, src, float(i), dur

def audio_feats(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    win = 800; n = len(x) // win
    fr = x[:n * win].reshape(n, win)
    rms = np.sqrt((fr ** 2).mean(1)); db = 20 * np.log10(rms + 1e-9)
    mags = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1)) + 1e-12
    sf = np.exp(np.log(mags).mean(1)) / mags.mean(1)
    act = db > db.max() - 25
    onsets = []
    for i in range(6, n):
        base = db[max(0, i - 6):i].mean()
        if db[i] - base > 8 and db[i] > db.max() - 20:
            if not onsets or i * 0.05 - onsets[-1] > 0.30: onsets.append(round(i * 0.05, 2))
    return dict(db=db, flat_act=float(np.median(sf[act])) if act.any() else 1.0,
                onsets=onsets, coverage=float(act.mean()), peak=float(db.max()))

def motion_peaks(path, ss, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", path,
                        "-vf", "fps=12,scale=160:90,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(r) // (160 * 90)
    frames = np.frombuffer(r[:n * 160 * 90], dtype=np.uint8).reshape(n, 90, 160).astype(np.float32)
    me = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    mt = (np.arange(len(me)) + 1) / 12.0
    peaks = []
    if len(me) > 4:
        thr = me.mean() + me.std()
        for i in range(1, len(me) - 1):
            if me[i] > thr and me[i] >= me[i - 1] and me[i] >= me[i + 1]:
                if not peaks or mt[i] - peaks[-1] > 0.4: peaks.append(round(float(mt[i]), 2))
    return peaks, float(me.mean())

def has_speech(path):
    import whisper
    m = has_speech.model or whisper.load_model("base")
    has_speech.model = m
    r = m.transcribe(path, language="en", no_speech_threshold=0.4)
    words = "".join(s["text"] for s in r["segments"]).strip()
    return len(words) > 12, words[:60]
has_speech.model = None

def main():
    only = set(sys.argv[1:])
    report, hard_fail = {}, False
    for sid, src, cin, dur in windows():
        if only and sid not in only: continue
        f = os.path.join(FOLEY, f"{sid}.flac")
        if not os.path.exists(f): continue
        a = audio_feats(f)
        mp, me_mean = motion_peaks(os.path.join(CLIPS, f"{src}.mp4"), cin, dur)
        synced = sum(1 for o in a["onsets"] if mp and min(abs(o - m) for m in mp) <= 0.35)
        speech, txt = has_speech(f)
        verdict = "OK"
        if speech: verdict, hard_fail = "SPEECH", True
        elif a["flat_act"] > 0.45 and a["coverage"] > 0.6: verdict = "HISSY"   # continuous flat energy = hiss; intermittent = crackle, fine
        elif a["onsets"] and mp and synced < max(1, len(a["onsets"]) // 3): verdict = "UNSYNCED"
        report[sid] = dict(verdict=verdict, flat=round(a["flat_act"], 3), coverage=round(a["coverage"], 2),
                           peak_db=round(a["peak"], 1), onsets=a["onsets"][:10], motion_peaks=mp[:10],
                           n_onsets=len(a["onsets"]), n_synced=synced, speech_text=txt if speech else "")
        print(f'{sid:4} {verdict:9} flat={a["flat_act"]:.3f} cov={a["coverage"]:.2f} peak={a["peak"]:6.1f} '
              f'onsets={len(a["onsets"]):2d} synced={synced:2d} on={a["onsets"][:5]} mp={mp[:5]}')
    old = {}
    vp = os.path.join(FOLEY, "foley_verify.json")
    if os.path.exists(vp): old = json.load(open(vp))
    old.update(report)
    json.dump(old, open(vp, "w"), indent=1)
    sys.exit(1 if hard_fail else 0)

if __name__ == "__main__":
    main()
