#!/usr/bin/env python3
"""
correct_manifest_crossfade.py — fix the voice-generator manifest timeline so it
matches the ACTUAL narration wav.

pipeline/voice_generator.py records each segment's timestamp on a no-crossfade
cursor (sum of segment durations), but then concatenates the segment wavs with an
80ms acrossfade at every boundary. The wav therefore ends ~0.08s × (n_segments-1)
EARLIER than the manifest claims. Aligning a paper edit to the raw manifest makes
the whole video lead the voice and drops the finale (the same class of bug as the
breaking_law v13e padded/unpadded drift).

This rebuilds the real timeline by subtracting the crossfade overlap that precedes
each segment (overlap_i = min(CROSSFADE, 0.3·dur_i, 0.3·dur_{i+1}), per the
generator's acrossfade clamp), validates the corrected total against the real wav
duration, and writes <manifest>_aligned.json. If the model residual exceeds a
threshold it falls back to a uniform linear scale to the wav duration.

Usage:
  venv.nosync/bin/python scripts/correct_manifest_crossfade.py \
    --manifest audio/trex_pilot/narration_manifest.json \
    --wav audio/trex_pilot/narration.wav \
    --out audio/trex_pilot/narration_manifest_aligned.json
"""
import argparse, json, subprocess
from pathlib import Path

CROSSFADE = 0.08   # CROSSFADE_DURATION in pipeline/voice_generator.py


def wav_dur(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                          'format=duration', '-of', 'csv=p=0', str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--wav', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--crossfade', type=float, default=CROSSFADE)
    a = ap.parse_args()

    m = json.load(open(a.manifest))
    segs = m['segments']
    real = wav_dur(a.wav)
    claimed = float(m['total_duration_sec'])

    durs = [float(s['duration_sec']) for s in segs]
    # overlap that precedes each boundary i (between seg i and i+1)
    overlaps = [min(a.crossfade, 0.3 * durs[i], 0.3 * durs[i + 1])
                for i in range(len(durs) - 1)]
    cum = [0.0]
    for ov in overlaps:
        cum.append(cum[-1] + ov)
    model_total = claimed - cum[-1]

    residual = abs(model_total - real)
    mode = 'crossfade-model'
    if residual > 0.25:                          # model disagrees with the wav -> linear
        mode = 'linear-fallback'
        scale = real / claimed
        cum = [s['start_sec'] * (1 - scale) for s in segs] + [0.0]
        # recompute shifts so corrected = start*scale
        for i, s in enumerate(segs):
            shift = s['start_sec'] * (1 - scale)
            cum[i] = shift

    for i, s in enumerate(segs):
        new_start = round(s['start_sec'] - cum[i], 3)
        s['start_sec'] = max(0.0, new_start)
        if 'end_sec' in s:
            s['end_sec'] = round(s['start_sec'] + s['duration_sec'], 3)

    # clamp the tail exactly to the real wav
    m['total_duration_sec'] = round(real, 3)
    m['_aligned'] = {'mode': mode, 'claimed_total': claimed,
                     'real_wav_dur': round(real, 3),
                     'shift_total': round(cum[-1] if mode == 'crossfade-model'
                                          else claimed - real, 3),
                     'model_residual': round(residual, 3)}
    Path(a.out).write_text(json.dumps(m, indent=2))
    sp = [s for s in segs if s['type'] == 'speech']
    print(f"[{mode}] claimed={claimed}s real_wav={real:.3f}s "
          f"shift={m['_aligned']['shift_total']}s residual={residual:.3f}s")
    print(f"  last speech now ends @ {sp[-1]['end_sec']}s (wav {real:.2f}s) -> "
          f"{'OK' if sp[-1]['end_sec'] <= real + 0.05 else 'STILL PAST END'}")
    print(f"  wrote {a.out}")


if __name__ == '__main__':
    main()
