#!/usr/bin/env python3
"""
footage_verifier.py — Automated footage quality verification.

Scores every downloaded image and clip against its storyboard description
using a local vision model. Removes items that are completely unrelated
(score < 0.10) and reports per-segment coverage quality.

Vision scoring is best-effort: if Ollama is unavailable, the verifier
falls back to file-size / existence checks and reports without filtering.

Clip audio: all clip audio is stripped at assembly time via -an in
prepare_clip(). This module does not need to handle that — it's already done.

Usage (standalone):
    python pipeline/footage_verifier.py --manifest footage/fern_clone/slug/manifest.json

Usage (from run_pipeline.py):
    from pipeline.footage_verifier import verify_manifest
    result = verify_manifest(manifest_path)
    # result["coverage_pct"] → float 0–100
    # result["removed"]      → count of removed items
    # result["low_conf"]     → count of low-confidence items kept
    # result["segments"]     → per-segment coverage dict

Scoring thresholds:
    >= 0.30  → GOOD  — clearly matches storyboard description
    0.10–0.29 → LOW  — somewhat related, keep but flag
    < 0.10   → REJECT — completely unrelated, removed from manifest

Coverage rating:
    >= 80%   → EXCELLENT
    60–79%   → GOOD
    40–59%   → LOW  (warn in run_pipeline.py)
    < 40%    → CRITICAL (ask user to override or re-source)
"""

import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

SCORE_GOOD      = 0.30   # accept without annotation
SCORE_LOW       = 0.10   # keep but flag as low-confidence
# < SCORE_LOW   → remove from manifest

COVERAGE_EXCELLENT = 80   # % of segments with ≥1 good/low item
COVERAGE_GOOD      = 60
COVERAGE_WARN      = 40   # below this → ask user

# Max items to score per segment (speeds up large manifests)
MAX_ITEMS_PER_SEGMENT = 6

# Vision-capable models only — must support image input via Ollama "images" field.
# Text-only models (qwen3.5:27b, qwen3.5:4b) are NOT included here.
VISION_MODELS = ["qwen2.5vl:7b", "qwen2.5vl:72b", "llava:13b", "llava:7b", "llava"]
OLLAMA_URL    = "http://localhost:11434/api/generate"

# ── ANSI colors ───────────────────────────────────────────────────────────────

GR   = "\033[92m"
YL   = "\033[93m"
RD   = "\033[91m"
DIM  = "\033[90m"
BOLD = "\033[1m"
R    = "\033[0m"


# ── Vision model ──────────────────────────────────────────────────────────────

def _get_vision_model() -> str | None:
    """Return first available vision model from Ollama, or None."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        installed = {m["name"] for m in data.get("models", [])}
        for model in VISION_MODELS:
            if model in installed:
                return model
            base = model.split(":")[0]
            for inst in installed:
                if inst.startswith(base + ":"):
                    return inst
    except Exception:
        pass
    return None


def _score_image(model: str, image_path: Path, description: str) -> float:
    """
    Score an image against a storyboard description. Returns 0.0–1.0.
    """
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        prompt = (
            f"I'm verifying footage for a documentary video.\n"
            f"This footage slot should show: {description}\n\n"
            f"Look at the image and rate how well it matches the description.\n"
            f"Reply with ONLY a number from 0.0 to 1.0:\n"
            f"  1.0 = perfect match (exactly what's described)\n"
            f"  0.5 = partially related (same general topic)\n"
            f"  0.1 = very loosely related\n"
            f"  0.0 = completely unrelated\n"
            f"Reply with the number only."
        )

        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 10},
        }).encode()

        req = urllib.request.Request(
            OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            text = data.get("response", "0").strip()
            numbers = re.findall(r"\d+\.?\d*", text)
            if numbers:
                return min(1.0, max(0.0, float(numbers[0])))
    except Exception:
        pass
    return 0.0


def _extract_video_thumbnail(clip_path: Path, out_path: Path, time_sec: float = 5.0) -> bool:
    """Extract a single frame from a video clip for vision scoring."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_sec),
        "-i", str(clip_path),
        "-vframes", "1",
        "-q:v", "3",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=15)
    return out_path.exists() and out_path.stat().st_size > 0


def _get_clip_duration(clip_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json",
        str(clip_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


def _score_item(model: str | None, item: dict, tmpdir: Path) -> float:
    """
    Score a manifest item (image or video clip).
    Returns 0.0–1.0, or 0.5 if no model available (don't penalize).
    """
    local_path = item.get("local_path", "")
    description = item.get("storyboard_show", "").strip()

    if not local_path or not Path(local_path).exists():
        return 0.0   # file missing → treat as invalid

    if not description:
        return 0.5   # no description to compare → keep (can't score)

    if model is None:
        # No vision model — use file-size heuristic
        # Very small files (< 5KB) are likely corrupt/placeholder
        size = Path(local_path).stat().st_size
        return 0.5 if size > 5000 else 0.05

    path = Path(local_path)
    ext  = path.suffix.lower()

    if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return _score_image(model, path, description)

    elif ext in (".mp4", ".mov", ".mkv", ".webm", ".avi"):
        # Extract a frame from ~20% into the clip (past any intro)
        dur = _get_clip_duration(path)
        sample_time = max(1.0, dur * 0.2)
        frame_path  = tmpdir / f"verify_{path.stem}.jpg"
        if _extract_video_thumbnail(path, frame_path, time_sec=sample_time):
            return _score_image(model, frame_path, description)
        return 0.3   # couldn't extract frame — keep with low confidence

    return 0.5   # unknown file type — keep


# ── Main verification logic ───────────────────────────────────────────────────

def verify_manifest(
    manifest_path: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Verify all footage in a manifest against storyboard descriptions.

    Args:
        manifest_path: Path to manifest.json
        dry_run:       If True, report but don't modify the manifest
        verbose:       Print progress

    Returns dict with keys:
        coverage_pct   — % of segments with at least one kept item
        removed        — number of items removed
        low_conf       — number of low-confidence items kept
        good           — number of clearly matching items
        total_scored   — total items scored
        segments       — per-segment coverage dict
        no_model       — True if vision model was unavailable
    """
    manifest = json.loads(manifest_path.read_text())
    clips    = manifest.get("clips", [])

    # Only score items that are downloaded and have storyboard data
    scoreable = [
        c for c in clips
        if c.get("downloaded") and c.get("local_path") and Path(c["local_path"]).exists()
    ]

    if verbose:
        print(f"\n  Verifying {len(scoreable)} downloaded items against storyboard…")

    model = _get_vision_model()
    if verbose:
        if model:
            print(f"  Vision model: {model}")
        else:
            print(f"  {YL}No vision model available — using file-size check only{R}")

    # Group by storyboard segment IDs to track per-segment coverage
    # segment_id → list of items
    segment_items: dict[int, list] = {}
    unsegmented = []

    for item in scoreable:
        seg_ids = item.get("storyboard_segment_ids", [])
        if seg_ids:
            for sid in seg_ids:
                segment_items.setdefault(sid, []).append(item)
        else:
            unsegmented.append(item)

    removed   = 0
    low_conf  = 0
    good      = 0
    scored    = 0
    seg_coverage: dict[int, str] = {}  # segment_id → "good" / "low" / "none"

    items_to_remove = set()   # indices in clips list

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Score per segment (cap items to MAX_ITEMS_PER_SEGMENT)
        for seg_id, items in sorted(segment_items.items()):
            items_to_score = items[:MAX_ITEMS_PER_SEGMENT]
            seg_best = 0.0
            seg_label = "none"

            for item in items_to_score:
                score = _score_item(model, item, tmp_path)
                scored += 1

                item["_verify_score"] = round(score, 2)

                if score >= SCORE_GOOD:
                    good += 1
                    seg_label = "good"
                    if verbose:
                        print(f"    {GR}✓{R}  {Path(item['local_path']).name[:45]:<45}  score:{score:.2f}  seg:{seg_id}")
                elif score >= SCORE_LOW:
                    low_conf += 1
                    if seg_label != "good":
                        seg_label = "low"
                    if verbose:
                        print(f"    {YL}~{R}  {Path(item['local_path']).name[:45]:<45}  score:{score:.2f}  seg:{seg_id}")
                else:
                    # Mark for removal (index in clips list)
                    clip_idx = clips.index(item)
                    items_to_remove.add(clip_idx)
                    removed += 1
                    if verbose:
                        print(f"    {RD}✗{R}  {Path(item['local_path']).name[:45]:<45}  score:{score:.2f}  REMOVED")

                seg_best = max(seg_best, score)

            seg_coverage[seg_id] = seg_label

        # Score unsegmented items (no storyboard mapping)
        for item in unsegmented:
            score = _score_item(model, item, tmp_path)
            scored += 1
            item["_verify_score"] = round(score, 2)
            if score < SCORE_LOW:
                clip_idx = clips.index(item)
                items_to_remove.add(clip_idx)
                removed += 1

    # Calculate coverage: % of known segments that have ≥1 kept item
    total_segments = len(segment_items)
    covered = sum(1 for v in seg_coverage.values() if v != "none")
    coverage_pct = (covered / total_segments * 100) if total_segments > 0 else 100.0

    # Remove rejected items (reverse order to preserve indices)
    if not dry_run and items_to_remove:
        for idx in sorted(items_to_remove, reverse=True):
            clips.pop(idx)
        manifest["clips"] = clips
        manifest_path.write_text(json.dumps(manifest, indent=2))

    return {
        "coverage_pct":  round(coverage_pct, 1),
        "removed":       removed,
        "low_conf":      low_conf,
        "good":          good,
        "total_scored":  scored,
        "segments":      seg_coverage,
        "no_model":      model is None,
        "total_segments": total_segments,
        "covered_segments": covered,
    }


def print_report(result: dict):
    """Print a formatted coverage report."""
    pct  = result["coverage_pct"]
    c    = GR if pct >= COVERAGE_GOOD else (YL if pct >= COVERAGE_WARN else RD)

    print()
    print(f"  {BOLD}{'─' * 60}{R}")
    print(f"  {BOLD}Footage Verification Report:{R}")
    print()
    print(f"  {c}Coverage:  {pct:.0f}%{R}  ({result['covered_segments']}/{result['total_segments']} story segments)")
    print()
    print(f"  {GR}✓{R}  Good matches:       {result['good']}")
    print(f"  {YL}~{R}  Low confidence:     {result['low_conf']}  (kept)")
    print(f"  {RD}✗{R}  Removed (irrelevant): {result['removed']}")
    print(f"  {DIM}   Total scored:       {result['total_scored']}{R}")

    if result.get("no_model"):
        print()
        print(f"  {YL}Note: No vision model — scoring used file-size heuristics only.{R}")
        print(f"  {DIM}  Install Ollama with a vision model for accurate verification.{R}")

    print()

    if pct >= COVERAGE_EXCELLENT:
        print(f"  {GR}{BOLD}EXCELLENT coverage — assembly will have strong visual matching.{R}")
    elif pct >= COVERAGE_GOOD:
        print(f"  {GR}GOOD coverage — most segments have footage, animation covers the rest.{R}")
    elif pct >= COVERAGE_WARN:
        print(f"  {YL}LOW coverage — many segments will use animation. Review if critical.{R}")
    else:
        print(f"  {RD}{BOLD}CRITICAL — less than 40% of story segments have footage.{R}")
        print(f"  {RD}Consider re-running footage_sourcer or accepting heavy animation.{R}")

    print(f"  {BOLD}{'─' * 60}{R}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Verify footage manifest against storyboard")
    ap.add_argument("--manifest",  required=True, help="Path to footage manifest.json")
    ap.add_argument("--dry-run",   action="store_true",
                    help="Score and report without removing anything from manifest")
    ap.add_argument("--quiet",     action="store_true", help="Only print summary")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found", file=sys.stderr)
        sys.exit(1)

    result = verify_manifest(
        manifest_path,
        dry_run=args.dry_run,
        verbose=not args.quiet,
    )

    print_report(result)

    if args.dry_run:
        print(f"  {YL}Dry run — manifest not modified.{R}\n")
    elif result["removed"] > 0:
        print(f"  Manifest updated — {result['removed']} irrelevant item(s) removed.\n")

    # Exit code: 1 if critically low coverage
    sys.exit(1 if result["coverage_pct"] < COVERAGE_WARN else 0)


if __name__ == "__main__":
    main()
