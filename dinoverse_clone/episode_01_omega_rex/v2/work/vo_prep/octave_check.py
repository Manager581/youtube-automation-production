#!/usr/bin/env python
"""
Decisive octave test.

pyin reports LUKE median ~187 Hz, which is implausibly high for an adult male, and
the un-filtered run showed a 10th-percentile of ~94.7 Hz (= 187/2). That is the
signature of octave-DOUBLING (pyin locking onto H2 instead of the true fundamental).

Test: for every voiced frame, take pyin's estimate f0 and ask the SPECTRUM directly
whether real harmonic energy exists at f0/2. If the voice truly has fundamental f0,
there must be (near-)nothing at f0/2. If there is a strong peak at f0/2, then f0/2
is the true fundamental and pyin doubled.

Uses a long window (8192 @ 48kHz = 171ms, ~5.9 Hz resolution) so 93 Hz and 187 Hz
are cleanly resolvable. Cross-checks with raw YIN as a second opinion.
"""
import librosa
import numpy as np
import scipy.signal as sps
from faster_whisper import WhisperModel

BASE = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep"
FILES = {
    "LUKE": (f"{BASE}/LUKE_sample.mp3", 60.0, 400.0),
    "GF": (f"{BASE}/GF_sample.mp3", 70.0, 500.0),
    "RANGER_ref": (f"{BASE}/S46_ranger_audio.mp3", 60.0, 400.0),
}

model = WhisperModel("small", device="cpu", compute_type="int8")

# NOTE: deliberately NO high-pass here -- a high-pass could suppress a real low
# fundamental and manufacture the very artifact we're testing for.
NFFT = 8192


def band_energy(mag, freqs, f, halfwidth=12.0):
    """Peak magnitude within +/- halfwidth Hz of f."""
    sel = (freqs >= f - halfwidth) & (freqs <= f + halfwidth)
    return mag[sel].max() if sel.any() else 0.0


for name, (path, fmin, fmax) in FILES.items():
    print(f"\n================ {name} ================")
    segs, _ = model.transcribe(path, word_timestamps=True, language="en")
    words = [
        (w.start, w.end)
        for s in segs
        for w in (s.words or [])
        if any(c.isalnum() for c in w.word)
    ]
    y, sr = librosa.load(path, sr=None, mono=True)

    chunks = []
    for s, e in words:
        i0, i1 = max(0, int(s * sr)), min(len(y), int(e * sr))
        if i1 - i0 > int(0.02 * sr):
            chunks.append(y[i0:i1])
    y_sp = np.concatenate(chunks)

    # pyin (allow a full octave BELOW the suspected value so it *can* find a low F0)
    f0, _, _ = librosa.pyin(y_sp, fmin=fmin, fmax=fmax, sr=sr,
                            frame_length=NFFT, hop_length=512)
    yin = librosa.yin(y_sp, fmin=fmin, fmax=fmax, sr=sr,
                      frame_length=NFFT, hop_length=512)

    # Long-window STFT aligned to the same hop/frame
    S = np.abs(librosa.stft(y_sp, n_fft=NFFT, hop_length=512, win_length=NFFT))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=NFFT)

    n = min(S.shape[1], len(f0))
    ratios, sub_wins = [], 0
    kept = []
    for i in range(n):
        if np.isnan(f0[i]):
            continue
        f = float(f0[i])
        half = f / 2.0
        if half < 55:  # below plausible human fundamental -> can't be the real one
            continue
        mag = S[:, i]
        e_f = band_energy(mag, freqs, f)
        e_h = band_energy(mag, freqs, half)
        # local noise floor near the subharmonic, to avoid calling noise a "peak"
        nb = (freqs >= half - 40) & (freqs <= half + 40)
        floor = np.median(mag[nb]) + 1e-12
        if e_f <= 0:
            continue
        r = e_h / e_f
        ratios.append(r)
        # a REAL subharmonic: comparable to f0's own peak AND well above local floor
        if r > 0.5 and e_h > 4 * floor:
            sub_wins += 1
        kept.append(f)

    ratios = np.array(ratios)
    kept = np.array(kept)
    yv = yin[~np.isnan(yin)]

    print(f"  voiced frames analysed          : {len(ratios)}")
    print(f"  pyin  median F0                 : {np.median(kept):.1f} Hz")
    print(f"  yin   median F0 (cross-check)   : {np.median(yv):.1f} Hz")
    print(f"  median energy ratio  E(f0/2)/E(f0): {np.median(ratios):.3f}")
    print(f"  frames with a STRONG subharmonic : {sub_wins}/{len(ratios)} "
          f"({100*sub_wins/max(1,len(ratios)):.1f}%)")
    verdict = (
        "OCTAVE-DOUBLED -> true F0 is about HALF the pyin value"
        if sub_wins / max(1, len(ratios)) > 0.5
        else "pyin value looks like the TRUE fundamental (no consistent subharmonic)"
    )
    print(f"  VERDICT: {verdict}")
