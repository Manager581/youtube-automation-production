#!/usr/bin/env python3
"""
footage_verifier.py — Scores downloaded footage against storyboard using Claude vision.

Verifies that each downloaded image/clip actually matches what the storyboard
calls for. Replaces legacy vision model with Claude vision (via Claude Code CLI).

Scoring:
  - relevance (0-1): Does the image relate to the narration text?
  - quality (0-1): Is the image clear, high-res, not watermarked?
  - composition (0-1): Is the framing suitable for Ken Burns / parallax?
  - overall (0-1): Weighted average

Images scoring below threshold are flagged for replacement.

Usage:
    from pipeline_v2.footage_verifier import FootageVerifier
    verifier = FootageVerifier()
    results = verifier.verify_manifest("footage/manifest.json", "storyboards/directed.json")
"""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude_vision


# Minimum score thresholds
MIN_OVERALL_SCORE = 0.5
MIN_RELEVANCE_SCORE = 0.4


class FootageVerifier:
    """Verify downloaded footage against storyboard requirements."""

    def __init__(self, min_score: float = MIN_OVERALL_SCORE):
        self.min_score = min_score
        self.results = []

    def verify_single(self, image_path: str, segment: dict) -> dict:
        """
        Verify a single image against its storyboard segment.

        Args:
            image_path: Path to the image file
            segment: Storyboard segment dict with text, show, search_query, etc.

        Returns:
            {relevance, quality, composition, overall, pass, issues}
        """
        if not os.path.exists(image_path):
            return {
                "relevance": 0, "quality": 0, "composition": 0,
                "overall": 0, "pass": False,
                "issues": ["file not found"],
            }

        narration = segment.get("text", "")
        show = segment.get("show", "")
        search_query = segment.get("search_query", "")
        content_type = segment.get("content_type", "unknown")

        prompt = f"""Score this image for use in a YouTube documentary segment.

NARRATION TEXT: {narration[:300]}
VISUAL DESCRIPTION NEEDED: {show[:200]}
SEARCH QUERY USED: {search_query}
EXPECTED CONTENT TYPE: {content_type}

Score each criterion 0.0-1.0:

1. RELEVANCE: Does this image relate to the narration and visual description?
   0.0 = completely unrelated, 0.5 = vaguely related, 1.0 = exact match

2. QUALITY: Is the image clear, high-resolution, not watermarked, not blurry?
   0.0 = unusable, 0.5 = acceptable, 1.0 = broadcast quality

3. COMPOSITION: Is the framing suitable for slow zoom / parallax motion?
   Good: clear subject, adequate margins, depth layers
   Bad: too tight, no clear subject, flat/textureless
   0.0 = terrible, 0.5 = workable, 1.0 = ideal

Return ONLY valid JSON:
{{"relevance": 0.0-1.0, "quality": 0.0-1.0, "composition": 0.0-1.0, "description": "what the image actually shows", "issues": ["list any problems"]}}"""

        response = query_claude_vision(prompt, image_path, timeout=60)

        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                scores = json.loads(match.group())
                # Calculate weighted overall score
                overall = (
                    scores.get("relevance", 0) * 0.5 +
                    scores.get("quality", 0) * 0.3 +
                    scores.get("composition", 0) * 0.2
                )
                scores["overall"] = round(overall, 3)
                scores["pass"] = overall >= self.min_score
                return scores
        except (json.JSONDecodeError, AttributeError):
            pass

        return {
            "relevance": 0, "quality": 0, "composition": 0,
            "overall": 0, "pass": False,
            "issues": ["verification failed — could not parse Claude response"],
        }

    def verify_manifest(self, manifest_path: str, storyboard_path: str,
                        auto_remove: bool = False) -> dict:
        """
        Verify all items in a footage manifest against the storyboard.

        Args:
            manifest_path: Path to footage manifest JSON
            storyboard_path: Path to storyboard JSON
            auto_remove: If True, delete files that fail verification

        Returns:
            {total, passed, failed, results, removed_files}
        """
        with open(manifest_path) as f:
            manifest = json.load(f)
        with open(storyboard_path) as f:
            storyboard = json.load(f)

        # Flatten storyboard segments
        segments = []
        if isinstance(storyboard, dict):
            if "scenes" in storyboard:
                for scene in storyboard["scenes"]:
                    segments.extend(scene.get("segments", []))
            elif "segments" in storyboard:
                segments = storyboard["segments"]
        elif isinstance(storyboard, list):
            segments = storyboard

        # Build segment lookup
        seg_lookup = {s.get("segment_index", i): s for i, s in enumerate(segments)}

        # Combine clips + images from manifest
        clips = manifest.get("clips", []) + manifest.get("images", [])
        results = []
        passed = 0
        failed = 0
        removed = []

        for clip in clips:
            local_path = clip.get("path", clip.get("local_path", ""))
            # Extract segment index from path (e.g., .../seg_013/...) or from field
            seg_idx = clip.get("segment_index", 0)
            if seg_idx == 0 and "/seg_" in local_path:
                import re as _re
                m = _re.search(r'/seg_(\d+)/', local_path)
                if m:
                    seg_idx = int(m.group(1))
            segment = seg_lookup.get(seg_idx, {"text": "", "show": ""})

            print(f"  Verifying: {Path(local_path).name} (seg {seg_idx})...", end=" ")

            score = self.verify_single(local_path, segment)
            score["file"] = local_path
            score["segment_index"] = seg_idx

            if score["pass"]:
                passed += 1
                print(f"PASS ({score['overall']:.2f})")
            else:
                failed += 1
                issues = ', '.join(score.get("issues", ["below threshold"]))
                print(f"FAIL ({score['overall']:.2f}) — {issues}")

                if auto_remove and os.path.exists(local_path):
                    os.remove(local_path)
                    removed.append(local_path)
                    print(f"    Removed: {local_path}")

            results.append(score)

        report = {
            "total": len(clips),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed / max(len(clips), 1) * 100:.0f}%",
            "results": results,
            "removed_files": removed,
        }

        self.results = results
        return report

    def save_report(self, report: dict, output_path: str):
        """Save verification report to JSON."""
        Path(output_path).write_text(json.dumps(report, indent=2))
        print(f"Verification report saved: {output_path}")


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify footage against storyboard")
    parser.add_argument("manifest", help="Path to footage manifest JSON")
    parser.add_argument("storyboard", help="Path to storyboard JSON")
    parser.add_argument("--auto-remove", action="store_true",
                        help="Auto-remove failing images")
    parser.add_argument("--min-score", type=float, default=MIN_OVERALL_SCORE,
                        help=f"Minimum overall score (default: {MIN_OVERALL_SCORE})")
    parser.add_argument("--report", "-r", help="Save report to JSON file")
    args = parser.parse_args()

    for path in [args.manifest, args.storyboard]:
        if not Path(path).exists():
            print(f"ERROR: File not found: {path}", file=sys.stderr)
            sys.exit(1)

    verifier = FootageVerifier(min_score=args.min_score)
    print(f"Verifying footage (min score: {args.min_score})...")
    report = verifier.verify_manifest(
        args.manifest, args.storyboard, auto_remove=args.auto_remove
    )

    print(f"\nResults: {report['passed']}/{report['total']} passed ({report['pass_rate']})")
    if report['failed']:
        print(f"  {report['failed']} items failed verification")
    if report['removed_files']:
        print(f"  {len(report['removed_files'])} files removed")

    if args.report:
        verifier.save_report(report, args.report)


if __name__ == "__main__":
    main()
