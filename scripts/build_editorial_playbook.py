#!/usr/bin/env python3
"""
Build synchronized multi-track editorial analysis for a Fern video.
Correlates: VTT narration, keyframe visuals, motion, audio/beats at 1s windows.
Outputs a unified timeline for editorial playbook extraction.
"""

import json
import re
import sys
from pathlib import Path

VIDEO_ID = "wkVygetgeRY"
BASE = Path("analysis/fern")
WINDOW_SEC = 2.0  # 2-second windows for manageable output


# ── 1. Parse VTT ─────────────────────────────────────────────────────────
def parse_vtt(path: Path) -> list[dict]:
    """Parse VTT into list of {start_sec, end_sec, text}."""
    raw = path.read_text()
    entries = []
    # Match timestamp lines: HH:MM:SS.mmm --> HH:MM:SS.mmm
    pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
    )
    blocks = raw.split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        for i, line in enumerate(lines):
            m = pattern.search(line)
            if m:
                start = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000
                end = int(m[5]) * 3600 + int(m[6]) * 60 + int(m[7]) + int(m[8]) / 1000
                # Get text from remaining lines, strip inline timing tags
                text_lines = lines[i + 1:]
                text = " ".join(text_lines)
                text = re.sub(r"<[\d:.]+>", "", text)  # remove timestamp tags
                text = re.sub(r"</?c>", "", text)  # remove <c> tags
                text = text.strip()
                if text and end - start > 0.01:  # skip empty/duplicate lines
                    entries.append({"start_sec": start, "end_sec": end, "text": text})
    # Deduplicate — VTT has progressive reveals (same text repeated)
    deduped = []
    for e in entries:
        if not deduped or e["text"] != deduped[-1]["text"]:
            deduped.append(e)
    return deduped


# ── 2. Load timeline (keyframes) ─────────────────────────────────────────
def load_timeline(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    frames = []
    for f in data.get("timeline", []):
        v = f.get("visual", {})
        frames.append({
            "timestamp": f["timestamp"],
            "words_spoken": f.get("words_spoken", ""),
            "visual_category": v.get("visual_category", "unknown"),
            "scene_description": v.get("scene_description", ""),
            "text_on_screen": v.get("text_on_screen", False),
            "text_content": v.get("text_content", "none"),
            "camera_movement": v.get("camera_movement", "static"),
            "camera_angle": v.get("camera_angle", ""),
            "emotional_tone": v.get("emotional_tone", "neutral"),
            "narrative_function": v.get("narrative_function", ""),
            "people_count": v.get("people_count", 0),
            "people_description": v.get("people_description", "none"),
            "era": v.get("era", "unknown"),
            "atmosphere": v.get("atmosphere", ""),
            "production_technique": v.get("production_technique", ""),
        })
    return frames


# ── 3. Load motion segments ──────────────────────────────────────────────
def load_motion(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data.get("segments", [])


# ── 4. Load audio analysis ───────────────────────────────────────────────
def load_audio(path: Path) -> dict:
    data = json.loads(path.read_text())
    return {
        "bpm": data.get("music", {}).get("bpm", 0),
        "beat_count": data.get("music", {}).get("beat_count", 0),
        "silence_segments": data.get("silence", {}).get("silence_segments", []),
        "energy_peaks": data.get("energy", {}).get("energy_peaks", []),
        "music_changes": data.get("music", {}).get("music_changes", []),
    }


# ── 5. Build unified timeline ────────────────────────────────────────────
def build_unified_timeline(vtt, frames, motion, audio, duration, window=WINDOW_SEC):
    """Build windows correlating all tracks."""
    windows = []
    n_windows = int(duration / window) + 1

    for wi in range(n_windows):
        t_start = wi * window
        t_end = t_start + window

        # Narration in this window
        narration_parts = []
        for v in vtt:
            if v["end_sec"] > t_start and v["start_sec"] < t_end:
                narration_parts.append(v["text"])
        narration = " ".join(narration_parts).strip()
        # Collapse duplicated progressive text
        words = narration.split()
        cleaned = []
        for w in words:
            if not cleaned or w != cleaned[-1]:
                cleaned.append(w)
        narration = " ".join(cleaned)

        # Keyframe(s) in this window
        frame_data = []
        for f in frames:
            if t_start <= f["timestamp"] < t_end:
                frame_data.append(f)

        # Motion in this window
        motion_data = []
        for m in motion:
            if m["end_sec"] > t_start and m["start_sec"] < t_end:
                motion_data.append({
                    "type": m["motion_type"],
                    "zoom_rate": m.get("zoom_rate_pct_per_sec", 0),
                    "energy": m.get("total_motion_energy_pct", 0),
                })

        # Silence in this window
        is_silent = False
        for s in audio["silence_segments"]:
            if s["end"] > t_start and s["start"] < t_end:
                overlap = min(s["end"], t_end) - max(s["start"], t_start)
                if overlap > window * 0.5:
                    is_silent = True
                    break

        # Energy peaks in this window
        peaks = [p for p in audio["energy_peaks"]
                 if t_start <= p["time"] < t_end]

        # Music changes
        changes = [c for c in audio["music_changes"]
                   if t_start <= c["time"] < t_end and abs(c["strength"]) > 3.0]

        # Is there a cut? (new keyframe appearing)
        has_cut = len(frame_data) > 0 and any(
            f["timestamp"] > t_start + 0.1 for f in frame_data
        )

        # Primary visual
        primary_visual = None
        if frame_data:
            # Use the first non-black frame, or the first frame
            for f in frame_data:
                if f["visual_category"] != "black_screen":
                    primary_visual = f
                    break
            if not primary_visual:
                primary_visual = frame_data[0]

        w = {
            "time": f"{t_start:.1f}-{t_end:.1f}s",
            "t_start": t_start,
            "narration": narration[:200] if narration else "[silence]",
            "visual_category": primary_visual["visual_category"] if primary_visual else "none",
            "scene": primary_visual["scene_description"][:150] if primary_visual else "",
            "text_on_screen": primary_visual["text_content"] if primary_visual and primary_visual["text_on_screen"] else None,
            "camera": primary_visual["camera_movement"] if primary_visual else "none",
            "emotional_tone": primary_visual["emotional_tone"] if primary_visual else "neutral",
            "narrative_function": primary_visual["narrative_function"] if primary_visual else "",
            "motion": motion_data[0]["type"] if motion_data else "none",
            "zoom_rate": round(motion_data[0]["zoom_rate"], 2) if motion_data else 0,
            "is_silent": is_silent,
            "has_cut": has_cut,
            "energy_peak": round(max(p["energy"] for p in peaks), 3) if peaks else 0,
            "music_change": changes[0]["type"] if changes else None,
            "n_frames": len(frame_data),
        }
        windows.append(w)

    return windows


# ── 6. Detect editorial events ───────────────────────────────────────────
def detect_events(windows):
    """Find notable editorial moments: cuts, transitions, reveals, etc."""
    events = []
    prev_cat = None
    prev_narr = ""

    for i, w in enumerate(windows):
        ev = []

        # Visual category change = CUT
        if prev_cat and w["visual_category"] != prev_cat and w["visual_category"] != "none":
            ev.append(f"CUT: {prev_cat} → {w['visual_category']}")

        # Silence → speech = new section start
        if i > 0 and windows[i - 1]["is_silent"] and not w["is_silent"] and w["narration"] != "[silence]":
            ev.append("SILENCE_BREAK: speech resumes")

        # Speech → silence = section end / dramatic pause
        if i > 0 and not windows[i - 1]["is_silent"] and w["is_silent"]:
            ev.append("DRAMATIC_PAUSE")

        # Energy spike
        if w["energy_peak"] > 0.15:
            ev.append(f"ENERGY_SPIKE: {w['energy_peak']}")

        # Music change
        if w["music_change"]:
            ev.append(f"MUSIC_{w['music_change'].upper()}")

        # Text appears
        if w["text_on_screen"] and w["text_on_screen"] != "none":
            ev.append(f"TEXT_OVERLAY: {w['text_on_screen'][:80]}")

        # Narrative function change
        if i > 0 and w["narrative_function"] != windows[i - 1].get("narrative_function", ""):
            ev.append(f"NARRATIVE_SHIFT: → {w['narrative_function']}")

        if ev:
            events.append({
                "time": w["time"],
                "t_start": w["t_start"],
                "narration": w["narration"][:120],
                "visual": w["visual_category"],
                "motion": w["motion"],
                "events": ev,
            })

        prev_cat = w["visual_category"]
        prev_narr = w["narration"]

    return events


# ── 7. Build editorial segments ──────────────────────────────────────────
def build_editorial_segments(windows, events):
    """Group windows into editorial segments (between cuts) and annotate."""
    segments = []
    current_segment = {
        "start_sec": 0,
        "windows": [],
        "cuts_at": [],
    }

    for w in windows:
        current_segment["windows"].append(w)

        # Check if this window has a cut event
        matching_events = [e for e in events if e["t_start"] == w["t_start"]]
        has_cut_event = any("CUT:" in str(e.get("events", [])) for e in matching_events)

        if has_cut_event and len(current_segment["windows"]) > 1:
            # Close current segment
            current_segment["end_sec"] = w["t_start"]
            current_segment["duration_sec"] = current_segment["end_sec"] - current_segment["start_sec"]

            # Summarize the segment
            cats = [ww["visual_category"] for ww in current_segment["windows"]
                    if ww["visual_category"] not in ("none", "black_screen")]
            narr = " ".join(ww["narration"] for ww in current_segment["windows"]
                           if ww["narration"] != "[silence]")
            motions = [ww["motion"] for ww in current_segment["windows"]
                      if ww["motion"] != "none"]

            current_segment["primary_visual"] = cats[0] if cats else "black_screen"
            current_segment["narration_summary"] = narr[:300]
            current_segment["primary_motion"] = max(set(motions), key=motions.count) if motions else "static"
            current_segment["emotional_tone"] = current_segment["windows"][-1]["emotional_tone"]
            current_segment["narrative_function"] = current_segment["windows"][-1]["narrative_function"]
            current_segment["events"] = [e for e in events
                                        if current_segment["start_sec"] <= e["t_start"] < current_segment["end_sec"]]
            del current_segment["windows"]
            segments.append(current_segment)

            # Start new segment
            current_segment = {
                "start_sec": w["t_start"],
                "windows": [w],
                "cuts_at": [],
            }

    return segments


# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    vid = VIDEO_ID
    print(f"Building editorial playbook for {vid}...")

    # Load all tracks
    vtt_path = BASE / vid / "video.en.vtt"
    timeline_path = BASE / vid / "timeline_hybrid_qwen-vl.json"
    motion_path = BASE / vid / "segment_motion.json"
    audio_path = BASE / f"{vid}_audio_analysis.json"

    print("  Loading VTT subtitles...")
    vtt = parse_vtt(vtt_path)
    print(f"    → {len(vtt)} subtitle entries")

    print("  Loading timeline keyframes...")
    frames = load_timeline(timeline_path)
    print(f"    → {len(frames)} keyframes")

    print("  Loading motion segments...")
    motion = load_motion(motion_path)
    print(f"    → {len(motion)} motion segments")

    print("  Loading audio analysis...")
    audio = load_audio(audio_path)
    print(f"    → {audio['bpm']:.1f} BPM, {len(audio['silence_segments'])} silence segments, {len(audio['energy_peaks'])} energy peaks")

    duration = 1689.37

    # Build unified timeline
    print(f"\n  Building unified timeline ({WINDOW_SEC}s windows)...")
    windows = build_unified_timeline(vtt, frames, motion, audio, duration)
    print(f"    → {len(windows)} windows")

    # Detect events
    print("  Detecting editorial events...")
    events = detect_events(windows)
    print(f"    → {len(events)} event windows")

    # Build editorial segments
    print("  Building editorial segments...")
    segments = build_editorial_segments(windows, events)
    print(f"    → {len(segments)} segments")

    # ── Output detailed analysis for first 5 minutes ──
    print("\n" + "=" * 100)
    print("SYNCHRONIZED EDITORIAL ANALYSIS — First 5 minutes (0-300s)")
    print("=" * 100)

    for w in windows:
        if w["t_start"] > 300:
            break
        line = f"\n[{w['time']}]"
        line += f"  VISUAL: {w['visual_category']}"
        if w["has_cut"]:
            line += " ★CUT"
        line += f"  MOTION: {w['motion']}"
        if w["zoom_rate"]:
            line += f" ({w['zoom_rate']}%/s)"
        line += f"  TONE: {w['emotional_tone']}"
        line += f"  FUNC: {w['narrative_function']}"
        if w["text_on_screen"]:
            line += f"\n         TEXT: \"{w['text_on_screen'][:100]}\""
        line += f"\n         NARR: \"{w['narration'][:150]}\""
        if w["is_silent"]:
            line += " [SILENT]"
        if w["energy_peak"] > 0.1:
            line += f" [ENERGY:{w['energy_peak']}]"

        # Show matching events
        matching = [e for e in events if e["t_start"] == w["t_start"]]
        for e in matching:
            for ev in e["events"]:
                line += f"\n         >>> {ev}"

        print(line)

    # ── Output segment summary for full video ──
    print("\n\n" + "=" * 100)
    print("EDITORIAL SEGMENTS — Full Video Summary")
    print("=" * 100)

    for i, seg in enumerate(segments[:50]):  # First 50 segments
        print(f"\n--- Segment {i+1} [{seg['start_sec']:.1f}s - {seg['end_sec']:.1f}s] ({seg['duration_sec']:.1f}s) ---")
        print(f"  Visual: {seg['primary_visual']}  |  Motion: {seg['primary_motion']}  |  Tone: {seg['emotional_tone']}  |  Function: {seg['narrative_function']}")
        print(f"  Narration: \"{seg['narration_summary'][:200]}\"")
        for ev in seg.get("events", []):
            for e in ev.get("events", []):
                print(f"  >>> {e}")

    # ── Save full data ──
    out_path = BASE / vid / "editorial_analysis.json"
    output = {
        "video_id": vid,
        "duration": duration,
        "window_sec": WINDOW_SEC,
        "total_windows": len(windows),
        "total_events": len(events),
        "total_segments": len(segments),
        "bpm": audio["bpm"],
        "windows": windows[:150],  # First 5 min detailed
        "events": events,
        "segments": segments,
    }
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n\nSaved full analysis to {out_path}")

    # ── Key stats ──
    print("\n" + "=" * 100)
    print("KEY EDITORIAL STATS")
    print("=" * 100)

    # Cut rate by section
    total_cuts = sum(1 for w in windows if w["has_cut"])
    print(f"Total cuts: {total_cuts} in {duration/60:.1f} min = {total_cuts/(duration/60):.1f} cuts/min")

    # Visual category distribution
    from collections import Counter
    cats = Counter(w["visual_category"] for w in windows if w["visual_category"] not in ("none",))
    print(f"\nVisual categories:")
    for cat, count in cats.most_common(10):
        print(f"  {cat}: {count} windows ({count/len(windows)*100:.1f}%)")

    # Motion distribution
    motions = Counter(w["motion"] for w in windows if w["motion"] != "none")
    print(f"\nMotion types:")
    for m, count in motions.most_common():
        print(f"  {m}: {count} ({count/sum(motions.values())*100:.1f}%)")

    # Narrative function distribution
    funcs = Counter(w["narrative_function"] for w in windows if w["narrative_function"])
    print(f"\nNarrative functions:")
    for f, count in funcs.most_common():
        print(f"  {f}: {count} ({count/sum(funcs.values())*100:.1f}%)")

    # Average segment duration by visual type
    seg_by_type = {}
    for seg in segments:
        t = seg["primary_visual"]
        if t not in seg_by_type:
            seg_by_type[t] = []
        seg_by_type[t].append(seg["duration_sec"])
    print(f"\nAvg segment duration by visual type:")
    for t, durs in sorted(seg_by_type.items(), key=lambda x: -len(x[1])):
        print(f"  {t}: {sum(durs)/len(durs):.1f}s avg ({len(durs)} segments)")

    # Cuts near narration events
    print(f"\nNarrative-aligned cuts (cut + narrative shift in same window):")
    aligned = 0
    for e in events:
        has_cut = any("CUT:" in ev for ev in e["events"])
        has_shift = any("NARRATIVE_SHIFT:" in ev for ev in e["events"])
        if has_cut and has_shift:
            aligned += 1
    print(f"  {aligned} / {total_cuts} cuts ({aligned/max(total_cuts,1)*100:.1f}%) aligned with narrative shift")


if __name__ == "__main__":
    main()
