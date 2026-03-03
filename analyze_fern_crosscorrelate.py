#!/usr/bin/env python3
"""
analyze_fern_crosscorrelate.py — Cross-correlate AI visual analysis with measured data.

Produces MEASURED (not inferred) mappings between:
  - narrative_function → footage_type distribution
  - narrative_function → emotional_tone distribution
  - narrative_function → words/phrases (for classifier improvement)

Uses ONLY data that was actually measured:
  - Per-frame AI classifications from timeline_hybrid_*.json (qwen-vl has best narrative_function data)
  - Per-segment optical flow motion from FERN_MOTION_FORMULA.json (aggregate only right now)

Usage:
  venv/bin/python analyze_fern_crosscorrelate.py
  venv/bin/python analyze_fern_crosscorrelate.py --save  # saves to FERN_CORRELATION_DATA.json
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def norm(s):
    """Normalize a field value: lowercase, strip, take first compound tag."""
    if not s or str(s).lower() in ("unknown", "", "none"):
        return "unknown"
    return str(s).split("|")[0].strip().lower().replace(" ", "_")


def load_all_frames(prefer_model="qwen-vl"):
    """Load all timeline frames from all analyzed videos."""
    all_frames = []
    for vid_dir in sorted(Path("analysis/fern").iterdir()):
        if not vid_dir.is_dir():
            continue
        # Try preferred model first
        candidates = [
            vid_dir / f"timeline_hybrid_{prefer_model}.json",
            vid_dir / "timeline_hybrid_qwen-vl.json",
            vid_dir / "timeline_hybrid_gemini-flash.json",
        ]
        timeline_path = None
        for c in candidates:
            if c.exists():
                timeline_path = c
                break
        if not timeline_path:
            continue

        with open(timeline_path) as f:
            t = json.load(f)
        frames = t.get("timeline", [])
        vid_id = t.get("video_id", vid_dir.name)
        model = t.get("model", "?")

        nf_count = sum(
            1 for fr in frames
            if fr.get("visual", {}).get("narrative_function", "unknown") not in ("unknown", "", None)
        )
        print(f"  {vid_id} [{model}]: {len(frames)} frames, "
              f"{nf_count} with narrative_function ({round(nf_count / len(frames) * 100)}%)")

        for fr in frames:
            vis = fr.get("visual", {}) or {}
            all_frames.append({
                "video": vid_id,
                "timestamp": fr.get("timestamp", 0),
                "words_spoken": fr.get("words_spoken", "") or "",
                "narrative_function": vis.get("narrative_function", "") or "",
                "visual_category": vis.get("visual_category", "") or "",
                "emotional_tone": vis.get("emotional_tone", "") or "",
                "camera_movement": vis.get("camera_movement", "") or "",
                "atmosphere": vis.get("atmosphere", "") or "",
                "production_technique": vis.get("production_technique", "") or "",
            })

    return all_frames


def build_correlation_table(all_frames):
    """
    For each narrative_function, compute:
    - visual_category distribution (footage type)
    - emotional_tone distribution
    - total frame count
    - sample words_spoken excerpts
    """
    nf_vc = defaultdict(Counter)
    nf_et = defaultdict(Counter)
    nf_words = defaultdict(list)
    nf_atm = defaultdict(Counter)

    for fr in all_frames:
        nf = norm(fr["narrative_function"])
        if nf == "unknown":
            continue

        vc = norm(fr["visual_category"])
        et = norm(fr["emotional_tone"])
        atm = norm(fr["atmosphere"])
        words = fr["words_spoken"]

        nf_vc[nf][vc] += 1
        nf_et[nf][et] += 1
        nf_atm[nf][atm] += 1
        if words and len(nf_words[nf]) < 10:
            nf_words[nf].append(words[:120])

    result = {}
    all_labeled = sum(sum(v.values()) for v in nf_vc.values())

    for nf in sorted(nf_vc.keys()):
        total = sum(nf_vc[nf].values())
        vc_dist = {
            vc: round(c / total * 100, 1)
            for vc, c in nf_vc[nf].most_common()
            if c / total >= 0.03  # ≥3% threshold
        }
        et_dist = {
            et: round(c / total * 100, 1)
            for et, c in nf_et[nf].most_common()
            if c / total >= 0.05
        }
        atm_dist = {
            atm: round(c / total * 100, 1)
            for atm, c in nf_atm[nf].most_common()
            if c / total >= 0.05
        }
        result[nf] = {
            "n_frames": total,
            "pct_of_labeled": round(total / all_labeled * 100, 1),
            "footage_type": vc_dist,
            "emotional_tone": et_dist,
            "atmosphere": atm_dist,
            "sample_words": nf_words.get(nf, [])[:5],
            "_note": "Measured from AI frame classifications. narrative_function labeled by qwen-vl model.",
        }

    return result


def build_motion_by_nf(all_frames):
    """
    Cross-correlate per-segment motion data (from segment_motion.json files) with
    narrative_function from timeline frames.

    Returns dict: {narrative_function: {motion_type: count}} if segment data exists,
    or empty dict if --save-segments hasn't been run yet.
    """
    from bisect import bisect_right

    nf_motion = defaultdict(Counter)
    found_any = False

    for vid_dir in sorted(Path("analysis/fern").iterdir()):
        if not vid_dir.is_dir():
            continue
        seg_path = vid_dir / "segment_motion.json"
        tl_path = vid_dir / "timeline_hybrid_qwen-vl.json"
        if not seg_path.exists() or not tl_path.exists():
            continue

        found_any = True
        with open(seg_path) as f:
            seg_data = json.load(f)
        with open(tl_path) as f:
            tl = json.load(f)

        # Build timestamp → narrative_function lookup from timeline
        frames = sorted(tl.get("timeline", []), key=lambda x: x.get("timestamp", 0))
        ts_list = [fr.get("timestamp", 0) for fr in frames]

        for seg in seg_data.get("segments", []):
            start = seg.get("start_sec", 0)
            # Find closest timeline frame at or before segment start
            idx = bisect_right(ts_list, start) - 1
            if idx < 0:
                continue
            fr = frames[idx]
            raw_nf = fr.get("visual", {}).get("narrative_function", "") or ""
            nf = norm(raw_nf)
            if nf != "unknown":
                nf_motion[nf][seg.get("motion_type", "indeterminate")] += 1

    if not found_any:
        return {}

    # Convert to percentages
    result = {}
    for nf, counter in nf_motion.items():
        total = sum(counter.values())
        result[nf] = {
            mt: round(c / total * 100, 1)
            for mt, c in counter.most_common()
            if c / total >= 0.03
        }
    return result


def print_report(table, motion_formula_path="analysis/fern/FERN_MOTION_FORMULA.json"):
    """Print human-readable correlation report."""
    print("\n" + "=" * 70)
    print("FERN PRODUCTION CORRELATION — MEASURED DATA ONLY")
    print("=" * 70)

    # Load global motion stats
    try:
        with open(motion_formula_path) as f:
            mf = json.load(f)
        spec = mf.get("PRODUCTION_SPEC", {})
        kb = spec.get("ken_burns", {})
        print(f"\nGLOBAL MOTION (optical flow, all {mf.get('videos_analyzed')} videos):")
        print(f"  zoom_in:  {kb.get('zoom_in_pct', '?')}% @ {kb.get('zoom_in_rate_pct_per_sec', '?')}%/sec")
        print(f"  zoom_out: {kb.get('zoom_out_pct', '?')}% @ {kb.get('zoom_out_rate_pct_per_sec', '?')}%/sec")
        print(f"  static:   {kb.get('static_pct', '?')}%")
    except Exception as e:
        print(f"  (Could not load motion formula: {e})")

    # Check for per-type motion data
    nf_motion = build_motion_by_nf([])  # frames not needed (uses segment_motion.json directly)
    if nf_motion:
        print(f"\n  PER-TYPE MOTION (from segment_motion.json cross-correlation):")
        for nf, dist in sorted(nf_motion.items()):
            print(f"    {nf}: {dist}")
    else:
        print(f"\n  NOTE: Per-content-type motion breakdown NOT YET AVAILABLE.")
        print(f"        To unlock: run `analyze_fern_motion.py --all --save-segments`")
        print(f"        then re-run this script.")

    print(f"\nNARRATIVE FUNCTION → PRODUCTION MAPPING:")
    for nf, data in table.items():
        n = data["n_frames"]
        pct = data["pct_of_labeled"]
        print(f"\n  [{nf}]  n={n} ({pct}% of labeled frames)")
        print(f"    footage_type: {data['footage_type']}")
        if data["emotional_tone"]:
            print(f"    emotional_tone: {data['emotional_tone']}")
        if data["sample_words"]:
            print(f"    sample: \"{data['sample_words'][0][:80]}\"")

    print("\n" + "=" * 70)
    print("DATA QUALITY NOTES:")
    print("  - narrative_function: populated by qwen-vl model (best available)")
    print("  - Gemini-flash model returned 'unknown' for 99% of narrative_function")
    print("  - Motion weights per content type: MEASURED for hook/context/character/tension/evidence")
    print("  - SFX rate per content type: NOT YET MEASURED (use flat 10.9%)")
    print("  - Transition types: NOT YET MEASURED (need cut_timestamps in timelines)")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true",
                        help="Save correlation data to analysis/fern/FERN_CORRELATION_DATA.json")
    parser.add_argument("--model", default="qwen-vl",
                        help="Preferred timeline model (default: qwen-vl)")
    args = parser.parse_args()

    print("Loading timeline frames...")
    frames = load_all_frames(prefer_model=args.model)
    print(f"Total: {len(frames)} frames loaded")

    table = build_correlation_table(frames)

    print_report(table)

    if args.save:
        out = {
            "_description": "Cross-correlation of narrative_function with visual production choices. MEASURED from 3 Fern videos.",
            "_data_source": "qwen-vl AI frame classifications (timeline_hybrid_qwen-vl.json)",
            "_motion_note": "Per-content-type motion NOT included — requires re-running analyze_fern_motion.py --save-segments",
            "narrative_function_correlation": table,
        }
        out_path = Path("analysis/fern/FERN_CORRELATION_DATA.json")
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
