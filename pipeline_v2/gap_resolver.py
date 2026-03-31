#!/usr/bin/env python3
"""
gap_resolver.py — Automatically fill footage gaps in the director output.

Coordinates the research agent (web_image_sourcer) and vision analyzer to find,
download, verify, and assign visuals for segments that have no visual_file or
reference a missing file.

Flow:
  1. Load director output
  2. Find segments where visual_file is null or file doesn't exist
  3. For each gap, call web_image_sourcer to download candidates
  4. Run vision_analyzer on downloaded footage
  5. Pick best match using Claude: "narration says X, these images show A, B, C"
  6. Update director output JSON with the picked file
  7. Repeat until all gaps filled or max attempts reached

Usage:
    python -m pipeline_v2.gap_resolver --director storyboards/directed_v3.json --output-dir footage/gap_fills/
    python -m pipeline_v2.gap_resolver --director storyboards/directed_v3.json --output-dir footage/gap_fills/ --max-attempts 3
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude, query_claude_vision
from pipeline_v2.vision_analyzer import analyze_image
from pipeline_v2.web_image_sourcer import search_google_images

# ── ANSI colors ──
GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
BOLD = "\033[1m"; RESET = "\033[0m"; GRAY = "\033[90m"

# Minimum confidence to consider a gap truly resolved
MIN_CONFIDENCE = 0.3

# Directories to search for existing visual files
SEARCH_DIRS = [
    PROJECT_ROOT / "footage",
    PROJECT_ROOT / "images",
    Path.home() / "Desktop",
]


# ── Load Director Output ──────────────────────────────────────────────────

def _load_director(path):
    """Load director v3 JSON, return (raw_data, flat_segments)."""
    with open(path) as f:
        data = json.load(f)

    segments = []
    if "scenes" in data:
        for scene in data["scenes"]:
            segments.extend(scene.get("segments", []))
    else:
        segments = data.get("segments", [])

    return data, segments


# ── Find Gaps ──────────────────────────────────────────────────────────────

def find_gaps(director_output):
    """Identify segments with no visual_file or a missing file on disk.

    Args:
        director_output: flat list of director segment dicts

    Returns:
        list of gap dicts: {segment_idx, text, search_query, visual_file,
                            reason, arc_position}
    """
    gaps = []

    for i, seg in enumerate(director_output):
        visual_file = seg.get("visual_file")
        text = seg.get("text", seg.get("narration", ""))

        reason = None

        if not visual_file:
            reason = "no_visual_assigned"
        else:
            # Check if file exists on disk by searching common dirs
            found = _find_file_on_disk(visual_file)
            if not found:
                reason = "file_not_found"

        if reason:
            # Build or extract search query
            search_query = seg.get("search_query", "")
            if not search_query and text:
                search_query = _generate_search_query(text)

            gaps.append({
                "segment_idx": i,
                "text": text,
                "text_preview": text[:80],
                "search_query": search_query,
                "visual_file": visual_file,
                "reason": reason,
                "arc_position": seg.get("arc_position", ""),
                "tension_level": seg.get("tension_level", 0.5),
            })

    return gaps


def _find_file_on_disk(filename):
    """Search common directories for a file by name. Returns path or None."""
    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for dirpath, _, filenames in os.walk(search_dir):
            if filename in filenames:
                return os.path.join(dirpath, filename)
    return None


def _generate_search_query(narration_text):
    """Use Claude to generate a concise image search query from narration."""
    prompt = (
        f"Generate a concise image search query (5-8 words) for finding a "
        f"documentary-style visual to accompany this narration:\n\n"
        f"\"{narration_text[:300]}\"\n\n"
        f"Return ONLY the search query, nothing else."
    )
    response = query_claude(prompt, timeout=30)
    return response.strip() if response else narration_text[:50]


# ── Resolve Gaps ───────────────────────────────────────────────────────────

def resolve_gaps(gaps, footage_dir, image_dir, max_attempts=2):
    """Full resolution loop: download candidates, analyze, pick best match.

    Args:
        gaps: list of gap dicts from find_gaps()
        footage_dir: directory for downloaded video clips
        image_dir: directory for downloaded images
        max_attempts: max download attempts per gap

    Returns:
        list of resolved dicts: {segment_idx, picked_file, search_query,
                                  confidence, attempt}
    """
    os.makedirs(footage_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    resolved = []
    unresolved = []

    for gap_idx, gap in enumerate(gaps):
        seg_idx = gap["segment_idx"]
        query = gap["search_query"]
        narration = gap["text"]

        print(f"\n  [{gap_idx + 1}/{len(gaps)}] Seg {seg_idx}: \"{query}\"")

        picked_file = None
        confidence = 0

        for attempt in range(1, max_attempts + 1):
            # Vary query on retry
            if attempt > 1:
                query = _refine_query(gap["text"], query, attempt)
                print(f"    Retry {attempt} with: \"{query}\"")

            # Download candidates via web_image_sourcer
            print(f"    Downloading candidates...")
            candidates = _download_candidates(query, image_dir, max_results=5)

            if not candidates:
                print(f"    {YELLOW}No candidates found{RESET}")
                continue

            print(f"    Got {len(candidates)} candidates")

            # Analyze each candidate with vision
            analyzed = []
            for cand in candidates:
                filepath = cand.get("file", "")
                if not filepath or not os.path.exists(filepath):
                    continue

                analysis = analyze_image(filepath)
                analyzed.append({
                    "file": filepath,
                    "filename": os.path.basename(filepath),
                    "description": analysis.get("description", ""),
                    "topics": analysis.get("topics", []),
                    "mood": analysis.get("mood", ""),
                })

            if not analyzed:
                print(f"    {YELLOW}No candidates survived analysis{RESET}")
                continue

            # Pick best match using Claude
            best = _pick_best_match(narration, analyzed)
            if best:
                picked_file = best["file"]
                confidence = best.get("confidence", 0.7)
                print(f"    {GREEN}Picked: {os.path.basename(picked_file)} "
                      f"(confidence: {confidence:.0%}){RESET}")
                break

        if picked_file:
            resolved.append({
                "segment_idx": seg_idx,
                "picked_file": picked_file,
                "picked_filename": os.path.basename(picked_file),
                "search_query": query,
                "confidence": confidence,
                "attempt": attempt,
            })
        else:
            print(f"    {RED}UNRESOLVED after {max_attempts} attempts{RESET}")
            unresolved.append(gap)

    return resolved, unresolved


def _download_candidates(query, output_dir, max_results=5):
    """Download image candidates using web_image_sourcer."""
    try:
        results = search_google_images(query, output_dir, max_results=max_results)
        return results
    except Exception as e:
        print(f"    Download error: {e}")
        return []


def _refine_query(narration, original_query, attempt):
    """Generate a refined search query for retry attempts."""
    prompt = (
        f"The search query \"{original_query}\" didn't find good results "
        f"for this documentary narration:\n\n"
        f"\"{narration[:200]}\"\n\n"
        f"Generate a DIFFERENT search query (5-8 words). "
        f"Try {'broader' if attempt == 2 else 'more specific'} terms.\n"
        f"Return ONLY the search query."
    )
    response = query_claude(prompt, timeout=30)
    return response.strip() if response else original_query


def _pick_best_match(narration, analyzed_candidates):
    """Use Claude to pick the best visual match for the narration.

    Args:
        narration: the narration text for this segment
        analyzed_candidates: list of dicts with file, description, topics, mood

    Returns:
        dict with file, confidence, reason -- or None if no good match
    """
    if not analyzed_candidates:
        return None

    # Build candidate descriptions for Claude
    cand_text = ""
    for idx, cand in enumerate(analyzed_candidates):
        desc = cand.get("description", "No description")
        topics = ", ".join(cand.get("topics", []))
        mood = cand.get("mood", "unknown")
        cand_text += (
            f"  [{idx}] {cand['filename']}: {desc[:150]}. "
            f"Topics: {topics}. Mood: {mood}\n"
        )

    prompt = (
        f"A documentary segment has this narration:\n"
        f"\"{narration[:250]}\"\n\n"
        f"These images are available:\n{cand_text}\n"
        f"Which image BEST matches the narration? Consider:\n"
        f"- Does it show what's being discussed?\n"
        f"- Does the mood fit the tone?\n"
        f"- Would a viewer understand the connection?\n\n"
        f"Reply with ONLY valid JSON:\n"
        f'{{ "pick": <index 0-{len(analyzed_candidates)-1}>, '
        f'"confidence": <0.0-1.0>, "reason": "<one sentence>" }}\n'
        f'If NONE match well, reply: {{ "pick": -1, "confidence": 0, '
        f'"reason": "no match" }}'
    )

    response = query_claude(prompt, timeout=120)
    if not response:
        # Fallback: pick the first candidate
        return {
            "file": analyzed_candidates[0]["file"],
            "confidence": 0.3,
            "reason": "Fallback — Claude unavailable",
        }

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            data = json.loads(match.group())
            pick_idx = data.get("pick", -1)
            confidence = data.get("confidence", 0)

            if pick_idx >= 0 and pick_idx < len(analyzed_candidates):
                return {
                    "file": analyzed_candidates[pick_idx]["file"],
                    "confidence": confidence,
                    "reason": data.get("reason", ""),
                }
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: pick first candidate with low confidence
    return {
        "file": analyzed_candidates[0]["file"],
        "confidence": 0.3,
        "reason": "Fallback — could not parse Claude response",
    }


# ── Update Director Output ────────────────────────────────────────────────

def update_director(director_path, resolved_gaps):
    """Write resolved files back to the director JSON.

    Updates the visual_file and visual_type for each resolved segment.
    Saves to a new file (*_gapfilled.json) to avoid overwriting the original.
    """
    with open(director_path) as f:
        data = json.load(f)

    # Build a flat list of segments AND track their positions in scenes
    segments = []
    scene_map = []  # (scene_idx, seg_within_scene_idx) for each flat segment

    if "scenes" in data:
        for si, scene in enumerate(data["scenes"]):
            for sj, seg in enumerate(scene.get("segments", [])):
                segments.append(seg)
                scene_map.append((si, sj))
    else:
        segments = data.get("segments", [])
        scene_map = [(None, i) for i in range(len(segments))]

    # Apply resolved gaps
    updates = 0
    for res in resolved_gaps:
        seg_idx = res["segment_idx"]
        if seg_idx >= len(segments):
            continue

        picked = res["picked_file"]
        filename = res["picked_filename"]

        # Determine visual type from extension
        ext = os.path.splitext(filename)[1].lower()
        visual_type = "video_clip" if ext in (".mp4", ".mkv", ".mov", ".webm") else "still_image"

        # Update the segment
        segments[seg_idx]["visual_file"] = filename
        segments[seg_idx]["visual_type"] = visual_type
        segments[seg_idx]["_gap_resolved"] = True
        segments[seg_idx]["_resolved_path"] = picked
        segments[seg_idx]["_resolve_confidence"] = res.get("confidence", 0)

        # Write back into scene structure
        si, sj = scene_map[seg_idx]
        if si is not None:
            data["scenes"][si]["segments"][sj] = segments[seg_idx]

        updates += 1

    # Write to new file
    if "scenes" not in data:
        data["segments"] = segments

    output_path = director_path.replace(".json", "_gapfilled.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    return output_path, updates


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gap Resolver — fill footage gaps in director output"
    )
    parser.add_argument(
        "--director", required=True,
        help="Path to director v3 output JSON",
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory for downloaded gap-fill footage/images",
    )
    parser.add_argument(
        "--max-attempts", type=int, default=2,
        help="Max download attempts per gap (default: 2)",
    )
    parser.add_argument(
        "--report", help="Save gap resolution report to JSON file",
    )
    args = parser.parse_args()

    print(f"\n{BOLD}Gap Resolver — Fill Missing Footage{RESET}")
    print("=" * 60)

    # Load director output
    print(f"\n  Loading: {args.director}")
    raw_data, segments = _load_director(args.director)
    print(f"  {len(segments)} segments")

    # Find gaps
    print(f"\n  Scanning for gaps...")
    gaps = find_gaps(segments)

    if not gaps:
        print(f"\n  {GREEN}{BOLD}No gaps found — all segments have visuals{RESET}")
        return 0

    no_visual = sum(1 for g in gaps if g["reason"] == "no_visual_assigned")
    not_found = sum(1 for g in gaps if g["reason"] == "file_not_found")
    print(f"  Found {len(gaps)} gaps: "
          f"{no_visual} unassigned, {not_found} files missing")

    # Print gap details
    for g in gaps:
        reason_label = "NO VISUAL" if g["reason"] == "no_visual_assigned" else "FILE MISSING"
        print(f"    Seg {g['segment_idx']} [{reason_label}]: "
              f"\"{g['search_query'][:50]}\"")

    # Set up directories
    footage_dir = os.path.join(args.output_dir, "clips")
    image_dir = os.path.join(args.output_dir, "images")

    # Resolve gaps
    print(f"\n  Resolving {len(gaps)} gaps (max {args.max_attempts} attempts each)...")
    resolved, unresolved = resolve_gaps(
        gaps, footage_dir, image_dir,
        max_attempts=args.max_attempts,
    )

    # Update director output
    if resolved:
        output_path, updates = update_director(args.director, resolved)
        print(f"\n  {GREEN}Updated {updates} segments in: {output_path}{RESET}")

    # Check confidence threshold — low-confidence resolutions are not truly resolved
    low_confidence = [r for r in resolved if r.get("confidence", 0) < MIN_CONFIDENCE]
    high_confidence = [r for r in resolved if r.get("confidence", 0) >= MIN_CONFIDENCE]

    # Summary
    print(f"\n{'='*60}")
    print(f"  {BOLD}GAP RESOLUTION SUMMARY{RESET}")
    print(f"  Total gaps: {len(gaps)}")
    print(f"  Resolved (confident):   {GREEN}{len(high_confidence)}{RESET}")
    if low_confidence:
        print(f"  Resolved (low conf):    {YELLOW}{len(low_confidence)}{RESET} "
              f"(below {MIN_CONFIDENCE:.0%} threshold)")
    print(f"  Unresolved:             {RED}{len(unresolved)}{RESET}")

    if resolved:
        avg_conf = sum(r["confidence"] for r in resolved) / len(resolved)
        print(f"  Avg confidence: {avg_conf:.0%}")

    if low_confidence:
        print(f"\n  {YELLOW}Low-confidence resolutions (< {MIN_CONFIDENCE:.0%}):{RESET}")
        for lc in low_confidence:
            print(f"    Seg {lc['segment_idx']}: {lc.get('confidence', 0):.0%} — "
                  f"\"{lc['search_query'][:50]}\"")

    if unresolved:
        print(f"\n  {RED}Unresolved segments (need manual sourcing):{RESET}")
        for u in unresolved:
            print(f"    Seg {u['segment_idx']}: \"{u['search_query'][:50]}\"")

    # Save report
    if args.report:
        report = {
            "director_path": args.director,
            "total_gaps": len(gaps),
            "resolved_count": len(resolved),
            "resolved_confident": len(high_confidence),
            "resolved_low_confidence": len(low_confidence),
            "unresolved_count": len(unresolved),
            "min_confidence_threshold": MIN_CONFIDENCE,
            "resolved": resolved,
            "unresolved": [
                {"segment_idx": u["segment_idx"], "search_query": u["search_query"],
                 "text_preview": u["text_preview"]}
                for u in unresolved
            ],
        }
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Report saved: {args.report}")

    # Verdict — fail if any gaps are unresolved OR resolved below confidence threshold
    total_bad = len(unresolved) + len(low_confidence)
    if total_bad > 0:
        print(f"\n  {RED}{BOLD}VERDICT: {total_bad} gaps not confidently resolved — "
              f"{len(unresolved)} unresolved, {len(low_confidence)} below "
              f"{MIN_CONFIDENCE:.0%} confidence{RESET}")
        return 1
    else:
        print(f"\n  {GREEN}{BOLD}VERDICT: All gaps filled with high confidence{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
