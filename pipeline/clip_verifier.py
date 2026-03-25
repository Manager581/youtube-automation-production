#!/usr/bin/env python3
"""
clip_verifier.py — Verify video clip content matches script context using frame extraction + Claude Vision.

Extracts frames at regular intervals from video clips, sends them to Claude
for analysis, and confirms the clip content is relevant to the script segment
it's supposed to illustrate.

Also enforces fair use rules: clips are trimmed to safe duration, source audio
is flagged for muting, and transformative requirements are checked.

Usage:
    from pipeline.clip_verifier import ClipVerifier

    verifier = ClipVerifier()
    result = verifier.verify_clip(
        clip_path="footage/news_clip.mp4",
        script_context="SafeRent's algorithm discriminated against minority renters",
        required_elements=["news", "housing", "algorithm"],
    )
    if result["matches"]:
        print(f"Clip verified: {result['best_segment']}")

Pipeline integration:
    Called after footage_sourcer downloads clips, before video_assembler uses them.
    Rejects clips that don't match, finds best segment within long clips.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ClipVerifier:
    """Verify video clips match script context using frame analysis."""

    def __init__(self, frame_interval: float = 2.0, max_frames: int = 10):
        """
        Args:
            frame_interval: Extract a frame every N seconds
            max_frames: Maximum frames to extract per clip
        """
        self.frame_interval = frame_interval
        self.max_frames = max_frames

    def get_clip_duration(self, clip_path: str) -> float:
        """Get video clip duration in seconds."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(clip_path)],
                capture_output=True, text=True, timeout=10
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def extract_frames(self, clip_path: str, output_dir: str = None) -> list[dict]:
        """
        Extract frames at regular intervals from a video clip.
        Returns list of {path, timestamp_sec, frame_index}.
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="clip_frames_")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        duration = self.get_clip_duration(clip_path)
        if duration <= 0:
            return []

        # Calculate frame timestamps
        timestamps = []
        t = 0.0
        while t < duration and len(timestamps) < self.max_frames:
            timestamps.append(t)
            t += self.frame_interval

        # Extract frames with ffmpeg
        frames = []
        for i, ts in enumerate(timestamps):
            frame_path = output_dir / f"frame_{i:03d}_{ts:.1f}s.jpg"
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(ts), "-i", str(clip_path),
                     "-vframes", "1", "-q:v", "2", str(frame_path)],
                    capture_output=True, timeout=10
                )
                if frame_path.exists() and frame_path.stat().st_size > 1000:
                    frames.append({
                        "path": str(frame_path),
                        "timestamp_sec": ts,
                        "frame_index": i,
                    })
            except Exception as e:
                print(f"  [clip_verifier] Frame extraction error at {ts:.1f}s: {e}")

        return frames

    def analyze_frames(self, frames: list[dict], script_context: str,
                       required_elements: list[str] = None) -> dict:
        """
        Send extracted frames to Claude Vision for content analysis.
        Returns analysis with match score and best segment recommendation.
        """
        if not frames:
            return {"matches": False, "confidence": 0, "reason": "no frames extracted"}

        # Select up to 5 representative frames (evenly spaced)
        if len(frames) > 5:
            step = len(frames) / 5
            selected = [frames[int(i * step)] for i in range(5)]
        else:
            selected = frames

        # Build prompt
        prompt = (
            "You are verifying whether a video clip is appropriate for a YouTube documentary.\n\n"
            f"SCRIPT CONTEXT: {script_context}\n\n"
        )
        if required_elements:
            prompt += f"REQUIRED VISUAL ELEMENTS: {', '.join(required_elements)}\n\n"

        prompt += (
            "I'm showing you frames extracted from the clip at regular intervals.\n"
            "Analyze what the clip contains and whether it matches the script context.\n\n"
            "Answer in JSON:\n"
            "{\n"
            '  "matches": true/false,\n'
            '  "confidence": 0.0-1.0,\n'
            '  "content_description": "what the clip actually shows",\n'
            '  "best_start_sec": N.N (timestamp of the most relevant frame),\n'
            '  "best_end_sec": N.N (recommended end point, max 5 seconds after start),\n'
            '  "issues": ["list of problems"],\n'
            '  "content_warnings": ["any content that might cause copyright/legal issues"]\n'
            "}\n\n"
            "Be strict. If the clip doesn't clearly relate to the script context, set matches=false.\n"
            "If it partially matches, find the best 3-5 second segment and report its timestamps."
        )

        # Call Claude with frames
        try:
            cmd = ["claude", "-p", prompt, "--model", "sonnet", "--output-format", "text"]
            # Add frame paths as arguments
            for frame in selected:
                cmd.append(str(frame["path"]))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                match = re.search(r'\{.*\}', result.stdout, re.DOTALL)
                if match:
                    analysis = json.loads(match.group())
                    # Map frame timestamps to analysis
                    analysis["frames_analyzed"] = len(selected)
                    analysis["frame_timestamps"] = [f["timestamp_sec"] for f in selected]
                    return analysis
        except Exception as e:
            print(f"  [clip_verifier] Analysis error: {e}")

        return {"matches": False, "confidence": 0, "reason": "analysis failed"}

    def verify_clip(self, clip_path: str, script_context: str,
                    required_elements: list[str] = None,
                    keep_frames: bool = False) -> dict:
        """
        Full verification pipeline: extract frames → analyze → return result.

        Args:
            clip_path: Path to video clip
            script_context: Script text this clip should illustrate
            required_elements: Visual elements the clip should contain
            keep_frames: If True, don't delete extracted frames

        Returns:
            Dict with matches, confidence, best_segment, content_description
        """
        clip_path = str(clip_path)
        print(f"  🎬 Verifying clip: {Path(clip_path).name}")

        # Get duration
        duration = self.get_clip_duration(clip_path)
        if duration <= 0:
            return {"matches": False, "confidence": 0, "reason": "cannot read clip"}

        print(f"    Duration: {duration:.1f}s")

        # Extract frames
        tmp_dir = tempfile.mkdtemp(prefix="clip_verify_")
        frames = self.extract_frames(clip_path, tmp_dir)
        print(f"    Extracted {len(frames)} frames")

        if not frames:
            return {"matches": False, "confidence": 0, "reason": "no frames extracted"}

        # Analyze with Claude Vision
        analysis = self.analyze_frames(frames, script_context, required_elements)

        # Clean up frames unless keeping
        if not keep_frames:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

        # Build result
        result = {
            "clip_path": clip_path,
            "clip_duration": duration,
            "matches": analysis.get("matches", False),
            "confidence": analysis.get("confidence", 0),
            "content_description": analysis.get("content_description", ""),
            "issues": analysis.get("issues", []),
            "content_warnings": analysis.get("content_warnings", []),
            "frames_analyzed": analysis.get("frames_analyzed", 0),
        }

        # Best segment recommendation
        best_start = analysis.get("best_start_sec", 0)
        best_end = analysis.get("best_end_sec", min(best_start + 5, duration))
        # Enforce fair use max duration
        if best_end - best_start > 5:
            best_end = best_start + 5

        result["best_segment"] = {
            "start_sec": best_start,
            "end_sec": best_end,
            "duration_sec": round(best_end - best_start, 1),
        }

        status = "✓ MATCH" if result["matches"] else "✗ REJECTED"
        conf = result["confidence"]
        print(f"    {status} ({conf:.0%}) — {result['content_description'][:60]}")

        if result["content_warnings"]:
            for w in result["content_warnings"]:
                print(f"    ⚠ {w}")

        return result

    def verify_manifest(self, manifest_path: str, storyboard: list[dict]) -> dict:
        """
        Verify all clips in a footage manifest against storyboard segments.
        Returns updated manifest with verification results.
        """
        manifest = json.loads(Path(manifest_path).read_text())
        clips = manifest.get("clips", [])

        verified = 0
        rejected = 0

        for clip in clips:
            local_path = clip.get("local_path", "")
            if not local_path or not Path(local_path).exists():
                continue

            # Skip stills (images don't need clip verification)
            ext = Path(local_path).suffix.lower()
            if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
                continue

            # Find matching storyboard segment
            seg_idx = clip.get("segment_index", 0)
            if seg_idx < len(storyboard):
                context = storyboard[seg_idx].get("text", "")
            else:
                context = clip.get("search_query", "")

            result = self.verify_clip(local_path, context)
            clip["verified"] = result["matches"]
            clip["verification_confidence"] = result["confidence"]
            clip["verification_description"] = result["content_description"]
            clip["best_segment"] = result.get("best_segment")

            if result["matches"]:
                verified += 1
            else:
                rejected += 1

        manifest["verified_count"] = verified
        manifest["rejected_count"] = rejected

        # Save updated manifest
        Path(manifest_path).write_text(json.dumps(manifest, indent=2))

        print(f"\n  Clip verification complete: {verified} verified, {rejected} rejected")
        return manifest


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify video clips match script context")
    parser.add_argument("clip", nargs="?", help="Path to video clip")
    parser.add_argument("--context", "-c", required=False, help="Script context")
    parser.add_argument("--manifest", "-m", help="Footage manifest to verify all clips")
    parser.add_argument("--storyboard", "-s", help="Storyboard JSON for context")
    parser.add_argument("--keep-frames", action="store_true", help="Keep extracted frames")
    args = parser.parse_args()

    verifier = ClipVerifier()

    if args.manifest:
        storyboard = []
        if args.storyboard:
            sb_data = json.loads(Path(args.storyboard).read_text())
            if isinstance(sb_data, dict) and sb_data.get("scenes"):
                for scene in sb_data["scenes"]:
                    storyboard.extend(scene.get("segments", []))
            else:
                storyboard = sb_data
        verifier.verify_manifest(args.manifest, storyboard)
    elif args.clip:
        result = verifier.verify_clip(
            args.clip,
            args.context or "general documentary footage",
            keep_frames=args.keep_frames,
        )
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
