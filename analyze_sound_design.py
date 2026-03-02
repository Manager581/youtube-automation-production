#!/usr/bin/env python3
"""
Analyze Fern's sound design from the Demucs 'other' stem.
Detects: whooshes, impacts, risers, atmospheric sounds, transition SFX.
No API calls. Uses librosa only.

Usage: python analyze_sound_design.py
"""
import json, os
import numpy as np
from pathlib import Path

STEMS_DIR = Path("analysis/fern/demucs_out/htdemucs")
OUT_FILE  = Path("analysis/fern/SOUND_DESIGN_FORMULA.json")

VIDEO_IDS = ["aVA7aXOH1pk_audio", "wLFY_Zu_O08_audio", "wkVygetgeRY_audio"]
VIDEO_NAMES = {
    "aVA7aXOH1pk_audio": "Trump_Assassination",
    "wLFY_Zu_O08_audio": "FBI_KKK",
    "wkVygetgeRY_audio": "Unabomber",
}


def find_stem(vid_id, stem="other"):
    p = STEMS_DIR / vid_id / f"{stem}.wav"
    return p if p.exists() else None


def load_audio(path, sr=22050, max_duration=None):
    """Load audio using librosa."""
    import librosa
    y, _ = librosa.load(str(path), sr=sr, mono=True, duration=max_duration)
    return y, sr


def detect_transients(y, sr, threshold_db=-30):
    """
    Detect sharp transients (impacts, whooshes, hits).
    Returns list of {time_sec, strength_db, type}.
    """
    import librosa

    # Onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units="frames",
                                               backtrack=True, delta=0.3)
    onset_times  = librosa.frames_to_time(onset_frames, sr=sr)

    # Get energy at each onset
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)

    # Frame to index mapping
    hop = 512
    events = []
    for t in onset_times:
        frame_idx = int(t * sr / hop)
        if frame_idx < len(rms_db):
            db = float(rms_db[frame_idx])
            if db > threshold_db:
                events.append({
                    "time_sec": round(float(t), 2),
                    "energy_db": round(db, 1),
                })

    return events


def classify_sfx(y, sr, time_sec, window=0.3):
    """
    Classify a sound event into whoosh/impact/riser/sustain.
    Uses spectral shape over the window.
    """
    import librosa
    start = int(time_sec * sr)
    end   = min(int((time_sec + window) * sr), len(y))
    chunk = y[start:end]
    if len(chunk) < 512:
        return "too_short"

    # Spectral centroid — high = bright/whoosh, low = deep impact
    centroid = librosa.feature.spectral_centroid(y=chunk, sr=sr)[0].mean()

    # Spectral rolloff — how much energy is in high freqs
    rolloff  = librosa.feature.spectral_rolloff(y=chunk, sr=sr)[0].mean()

    # Attack vs decay — is it impulsive (impact) or swelling (riser)?
    rms_frames = librosa.feature.rms(y=chunk, frame_length=256, hop_length=128)[0]
    if len(rms_frames) >= 3:
        peak_idx  = np.argmax(rms_frames)
        peak_norm = peak_idx / len(rms_frames)
        is_impulsive = peak_norm < 0.25  # energy peaks early = impact
        is_rising    = peak_norm > 0.70  # energy peaks late = riser
    else:
        is_impulsive = False
        is_rising    = False

    # Classify
    if centroid > 4000 and is_impulsive:
        return "impact_bright"   # snap, click, high hit
    elif centroid < 500 and is_impulsive:
        return "impact_deep"     # thud, boom, low hit
    elif centroid > 3000 and not is_impulsive:
        return "whoosh"          # sweeping high-freq sound
    elif is_rising:
        return "riser"           # tension buildup
    elif centroid < 800:
        return "sustain_low"     # ambient drone, bass rumble
    else:
        return "sustain_mid"     # general atmosphere

def summarize_sfx(events_classified, total_sec):
    """Summarize SFX usage patterns."""
    from collections import Counter
    types = Counter(e["type"] for e in events_classified)
    total = len(events_classified)
    rate  = round(total / (total_sec / 60), 1)  # events per minute

    # Spacing — time between events
    times = sorted(e["time_sec"] for e in events_classified)
    gaps  = [times[i+1] - times[i] for i in range(len(times)-1)]
    avg_gap = round(np.mean(gaps), 1) if gaps else 0

    return {
        "total_events":    total,
        "events_per_min":  rate,
        "avg_gap_sec":     avg_gap,
        "type_distribution": dict(types.most_common()),
    }


if __name__ == "__main__":
    try:
        import librosa
    except ImportError:
        print("ERROR: librosa not installed. Run: pip install librosa")
        import sys; sys.exit(1)

    all_results = {}
    SAMPLE_DURATION = 300  # analyze first 5 minutes per video (enough for pattern)

    for vid_id in VIDEO_IDS:
        name = VIDEO_NAMES[vid_id]
        other_path = find_stem(vid_id, "other")
        music_path = find_stem(vid_id, "music")

        if not other_path:
            print(f"[SKIP] {name} — no 'other' stem at {STEMS_DIR / vid_id}")
            continue

        print(f"\n{'='*55}")
        print(f"Analyzing sound design: {name}")
        print(f"  File: {other_path} ({other_path.stat().st_size // 1024 // 1024}MB)")

        # Load 5 minutes of the 'other' stem
        print(f"  Loading audio (first {SAMPLE_DURATION}s)...")
        y, sr = load_audio(other_path, max_duration=SAMPLE_DURATION)
        total_sec = len(y) / sr
        print(f"  Loaded {total_sec:.0f}s at {sr}Hz")

        # Detect all transients
        print(f"  Detecting transients...")
        events = detect_transients(y, sr, threshold_db=-35)
        print(f"  Found {len(events)} transient events")

        # Classify each event
        print(f"  Classifying {len(events)} events...")
        classified = []
        for ev in events[:200]:  # cap at 200 for speed
            sfx_type = classify_sfx(y, sr, ev["time_sec"])
            classified.append({**ev, "type": sfx_type})

        # Show sample
        print(f"\n  Sample events (first 15):")
        for e in classified[:15]:
            print(f"    [{e['time_sec']:6.1f}s] {e['type']:<20} {e['energy_db']:+.0f}dB")

        # Summary
        summary = summarize_sfx(classified, total_sec)
        print(f"\n  Summary:")
        print(f"    {summary['events_per_min']} events/min  |  avg gap: {summary['avg_gap_sec']}s")
        print(f"    Types: {summary['type_distribution']}")

        # Analyze music stem for additional context
        music_note = None
        if music_path:
            y_music, _ = load_audio(music_path, max_duration=60)
            import librosa
            tempo, _ = librosa.beat.beat_track(y=y_music, sr=sr)
            music_note = {"bpm_sample": round(float(tempo), 1)}
            print(f"  Music BPM (first 60s): {music_note['bpm_sample']}")

        all_results[name] = {
            "total_analyzed_sec": round(total_sec),
            "summary": summary,
            "music": music_note,
            "sample_events": classified[:30],
        }

    # Cross-video SFX formula
    if all_results:
        all_rates   = [r["summary"]["events_per_min"] for r in all_results.values()]
        all_gaps    = [r["summary"]["avg_gap_sec"] for r in all_results.values()]
        avg_rate    = round(np.mean(all_rates), 1)
        avg_gap     = round(np.mean(all_gaps), 1)

        # Aggregate type distribution
        from collections import Counter
        all_types = Counter()
        for r in all_results.values():
            all_types.update(r["summary"]["type_distribution"])

        print(f"\n{'='*55}")
        print("FERN SOUND DESIGN FORMULA")
        print(f"{'='*55}")
        print(f"  SFX rate:     {avg_rate} events/min")
        print(f"  Avg spacing:  {avg_gap}s between hits")
        print(f"  SFX types:    {dict(all_types.most_common())}")

    with open(OUT_FILE, "w") as f:
        json.dump({"videos": all_results}, f, indent=2)
    print(f"\nSaved: {OUT_FILE}")
