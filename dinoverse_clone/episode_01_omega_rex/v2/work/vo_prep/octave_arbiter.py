#!/usr/bin/env python
"""
ARBITER: is the per-shot F0 spread an OCTAVE ARTIFACT, or genuine per-clip voice drift?

The coordinator is right that a narrow fmin/fmax alone cannot settle this: clamping
LUKE to <=200 Hz would FORCE a low answer whether or not it is true. So the arbiter
is the HARMONIC COMB, which does not share pyin's failure mode:

  If pyin reports f0 but the TRUE fundamental is f0/2 (pyin doubled), then real
  energy MUST exist at the ODD half-harmonics: f0/2, 3f0/2, 5f0/2.
  If the true fundamental really IS f0, those bins sit at the noise floor.

  R_half = mean|X| at (0.5, 1.5, 2.5)*f0  /  mean|X| at (1, 2, 3)*f0
    R_half near 0      -> f0 is the TRUE fundamental (no doubling)
    R_half order ~0.3+ -> f0/2 is the TRUE fundamental (pyin DOUBLED)

  Conversely, to catch HALVING we check that f0 itself carries real energy above the
  local floor. If |X(f0)| ~= floor while |X(2f0)| is strong, pyin HALVED.

Independent cross-checks: torchaudio.detect_pitch_frequency (autocorrelation, a
different implementation), plus narrow-range pyin runs, plus the raw low-frequency
spectral peaks so the harmonic structure can be eyeballed directly.

Everything runs on the demucs VOCALS stem, inside whisper word intervals.
"""
import numpy as np
import librosa
import torch
import torchaudio
from faster_whisper import WhisperModel

BASE = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep"
SEP = f"{BASE}/sep/htdemucs"

CFG = {
    "LUKE": {"mix": f"{BASE}/LUKE_sample.mp3", "stem": "LUKE_sample",
             "shots": [("S40", 18), ("S67", 17), ("S21", 16)]},
    "GF": {"mix": f"{BASE}/GF_sample.mp3", "stem": "GF_sample",
           "shots": [("S23", 12), ("S34", 8), ("S66", 8)]},
    "RANGER": {"mix": f"{BASE}/S46_ranger_audio.mp3", "stem": "S46_ranger_audio",
               "shots": [("S46", 32)]},
}
NFFT = 8192  # 171ms @48k -> 5.9 Hz resolution: 120 and 241 Hz cleanly resolved

model = WhisperModel("small", device="cpu", compute_type="int8")


def shot_audio(voc, sr, wl):
    ch = []
    for w in wl:
        i0, i1 = max(0, int(w["s"] * sr)), min(len(voc), int(w["e"] * sr))
        if i1 - i0 > int(0.02 * sr):
            ch.append(voc[i0:i1])
    return np.concatenate(ch) if ch else None


def peak_at(mag, freqs, f, hw=15.0):
    sel = (freqs >= f - hw) & (freqs <= f + hw)
    return float(mag[sel].max()) if sel.any() else 0.0


def floor_at(mag, freqs, f, lo=40.0, hi=60.0):
    sel = ((freqs >= f - hi) & (freqs <= f - lo)) | ((freqs >= f + lo) & (freqs <= f + hi))
    return float(np.median(mag[sel])) + 1e-12 if sel.any() else 1e-12


print("=" * 78)
print("ARBITER: harmonic-comb test (does NOT share pyin's failure mode)")
print("=" * 78)

for name, cfg in CFG.items():
    segs, _ = model.transcribe(cfg["mix"], word_timestamps=True, language="en")
    words = [{"s": w.start, "e": w.end} for s in segs for w in (s.words or [])
             if any(c.isalnum() for c in w.word)]
    voc, sr = librosa.load(f"{SEP}/{cfg['stem']}/vocals.wav", sr=None, mono=True)

    print(f"\n############ {name} ############")
    i = 0
    for label, nw in cfg["shots"]:
        wl = words[i:i + nw]
        i += nw
        y = shot_audio(voc, sr, wl)
        if y is None or len(y) < NFFT:
            print(f"  {label}: too short")
            continue

        # ---- pyin: wide, narrow-male, narrow-female --------------------------
        def pyin_med(fmin, fmax):
            f0, _, _ = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=sr,
                                    frame_length=2048, hop_length=256)
            v = f0[~np.isnan(f0)]
            return float(np.median(v)) if v.size >= 10 else float("nan")

        wide = pyin_med(60, 500)
        nmale = pyin_med(70, 250)
        nfem = pyin_med(140, 400)

        # ---- independent estimator: torchaudio autocorrelation ---------------
        try:
            t = torch.tensor(y, dtype=torch.float32).unsqueeze(0)
            ta = torchaudio.functional.detect_pitch_frequency(
                t, sample_rate=sr, frame_time=0.02, freq_low=60, freq_high=500)
            tam = float(np.median(ta.numpy()))
        except Exception as e:
            tam = float("nan")

        # ---- ARBITER: harmonic comb around pyin's wide estimate ---------------
        S = np.abs(librosa.stft(y, n_fft=NFFT, hop_length=512, win_length=NFFT))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=NFFT)
        f0, _, _ = librosa.pyin(y, fmin=60, fmax=500, sr=sr,
                                frame_length=NFFT, hop_length=512)
        n = min(S.shape[1], len(f0))

        Rs, atf0 = [], []
        for k in range(n):
            if np.isnan(f0[k]):
                continue
            f = float(f0[k])
            mag = S[:, k]
            odd = np.mean([peak_at(mag, freqs, m * f) for m in (0.5, 1.5, 2.5)])
            inte = np.mean([peak_at(mag, freqs, m * f) for m in (1.0, 2.0, 3.0)])
            if inte > 0:
                Rs.append(odd / inte)
            atf0.append(peak_at(mag, freqs, f) / floor_at(mag, freqs, f))
        Rs = np.array(Rs)
        atf0 = np.array(atf0)

        R = float(np.median(Rs)) if Rs.size else float("nan")
        snr_f0 = float(np.median(atf0)) if atf0.size else float("nan")

        if R > 0.30:
            verdict = f"OCTAVE-DOUBLED -> true F0 ~= {wide/2:.0f} Hz"
        elif snr_f0 < 2.0:
            verdict = f"possible HALVING -> check {wide*2:.0f} Hz"
        else:
            verdict = f"F0 {wide:.0f} Hz is REAL (no octave error)"

        # ---- raw low-frequency spectral peaks (eyeball the comb) --------------
        avg = np.mean(S, axis=1)
        lo = (freqs >= 60) & (freqs <= 420)
        fl, al = freqs[lo], avg[lo]
        pk_idx = np.argsort(al)[::-1]
        seen, peaks = [], []
        for pi in pk_idx:
            fq = fl[pi]
            if all(abs(fq - s) > 25 for s in seen):
                seen.append(fq)
                peaks.append((fq, al[pi] / al.max()))
            if len(peaks) == 4:
                break
        peaks.sort()
        pk_str = "  ".join(f"{f:.0f}Hz({a:.2f})" for f, a in peaks)

        print(f"\n  --- {label} ---")
        print(f"    pyin wide(60-500)   : {wide:6.1f} Hz")
        print(f"    pyin narrow male    : {nmale:6.1f} Hz   (70-250)")
        print(f"    pyin narrow female  : {nfem:6.1f} Hz   (140-400)")
        print(f"    torchaudio autocorr : {tam:6.1f} Hz   [independent method]")
        print(f"    R_half (odd/int)    : {R:6.3f}        [>0.30 => doubled]")
        print(f"    peak(f0)/local floor: {snr_f0:6.1f}        [<2 => maybe halved]")
        print(f"    LF spectral peaks   : {pk_str}")
        print(f"    VERDICT             : {verdict}")
