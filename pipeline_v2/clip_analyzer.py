#!/usr/bin/env python3
"""
clip_analyzer.py — Find the best moment in video clips using Claude vision.

Extracts frames from a video clip at regular intervals, scores each frame
using Claude vision, and returns the timestamp of the best frame. This
determines clip_start_sec in the footage manifest so the assembler uses
the most relevant/compelling portion of each clip.

Usage:
    from pipeline_v2.clip_analyzer import ClipAnalyzer
    analyzer = ClipAnalyzer()
    result = analyzer.find_best_moment("clip.mp4", "FBI agents raiding an office")
    print(result["best_timestamp_sec"])  # e.g., 12.5
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude_vision


class ClipAnalyzer:
    """Find the best moment in video clips using Claude vision."""

    def __init__(self, sample_interval_sec: float = 2.0, max_samples: int = 15):
        """
        Args:
            sample_interval_sec: Seconds between frame samples
            max_samples: Maximum frames to sample from a clip
        """
        self.sample_interval = sample_interval_sec
        self.max_samples = max_samples

    def extract_frames(self, clip_path: str, output_dir: str = None) -> list[dict]:
        """
        Extract frames from a video clip at regular intervals.

        Args:
            clip_path: Path to video file
            output_dir: Directory for extracted frames (temp if not specified)

        Returns:
            List of {path, timestamp_sec} for each extracted frame
        """
        if not os.path.exists(clip_path):
            print(f"ERROR: Clip not found: {clip_path}", file=sys.stderr)
            return []

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="clip_frames_")
        os.makedirs(output_dir, exist_ok=True)

        # Get clip duration
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json', clip_path
        ]
        try:
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            duration = float(json.loads(probe_result.stdout)["format"]["duration"])
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError):
            duration = 60.0  # Assume 60s if probe fails

        # Calculate sample points
        interval = max(self.sample_interval, duration / self.max_samples)
        timestamps = []
        t = 0
        while t < duration and len(timestamps) < self.max_samples:
            timestamps.append(t)
            t += interval

        # Extract frames
        frames = []
        for i, ts in enumerate(timestamps):
            frame_path = os.path.join(output_dir, f"frame_{i:03d}_{ts:.1f}s.jpg")
            cmd = [
                'ffmpeg', '-y', '-ss', str(ts),
                '-i', clip_path,
                '-frames:v', '1',
                '-q:v', '2',
                frame_path,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0 and os.path.exists(frame_path):
                frames.append({
                    "path": frame_path,
                    "timestamp_sec": round(ts, 1),
                })

        return frames

    def score_frame(self, frame_path: str, context: str) -> dict:
        """
        Score a single frame for relevance and visual quality.

        Args:
            frame_path: Path to frame image
            context: Script context describing what the clip should show

        Returns:
            {relevance, visual_quality, overall, description}
        """
        prompt = f"""Score this video frame for use in a YouTube documentary.

SCRIPT CONTEXT (what this clip should illustrate): {context[:300]}

Score 0.0-1.0:
1. RELEVANCE: Does this frame show something related to the context?
2. VISUAL_QUALITY: Is this frame clear, well-composed, visually interesting?
   (Good: clear subject, good lighting, interesting composition)
   (Bad: blurry, dark, boring, text-heavy, black frame, loading screen)

Return ONLY valid JSON:
{{"relevance": 0.0-1.0, "visual_quality": 0.0-1.0, "description": "brief description"}}"""

        response = query_claude_vision(prompt, frame_path, timeout=30)

        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                scores = json.loads(match.group())
                overall = scores.get("relevance", 0) * 0.6 + scores.get("visual_quality", 0) * 0.4
                scores["overall"] = round(overall, 3)
                return scores
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"relevance": 0, "visual_quality": 0, "overall": 0,
                "description": "scoring failed"}

    def find_best_moment(self, clip_path: str, context: str,
                          cleanup: bool = True) -> dict:
        """
        Find the best moment in a video clip for a given context.

        Args:
            clip_path: Path to video file
            context: Script context describing what the clip should show
            cleanup: Remove extracted frames after analysis

        Returns:
            {best_timestamp_sec, best_score, all_scores, clip_path}
        """
        print(f"  Analyzing clip: {Path(clip_path).name}")

        frames = self.extract_frames(clip_path)
        if not frames:
            return {
                "best_timestamp_sec": 0,
                "best_score": 0,
                "all_scores": [],
                "clip_path": clip_path,
            }

        print(f"    Extracted {len(frames)} frames, scoring...")

        scored_frames = []
        for frame in frames:
            score = self.score_frame(frame["path"], context)
            scored_frames.append({
                "timestamp_sec": frame["timestamp_sec"],
                "score": score,
                "path": frame["path"],
            })

        # Find best frame
        best = max(scored_frames, key=lambda x: x["score"].get("overall", 0))

        print(f"    Best moment: {best['timestamp_sec']}s "
              f"(score: {best['score'].get('overall', 0):.2f})")

        # Cleanup temp frames
        if cleanup:
            for frame in scored_frames:
                try:
                    os.remove(frame["path"])
                except OSError:
                    pass
            # Try to remove the temp directory
            frame_dir = os.path.dirname(frames[0]["path"])
            try:
                os.rmdir(frame_dir)
            except OSError:
                pass

        return {
            "best_timestamp_sec": best["timestamp_sec"],
            "best_score": best["score"].get("overall", 0),
            "best_description": best["score"].get("description", ""),
            "all_scores": [
                {"timestamp_sec": f["timestamp_sec"],
                 "overall": f["score"].get("overall", 0)}
                for f in scored_frames
            ],
            "clip_path": clip_path,
        }

    def analyze_manifest(self, manifest_path: str, storyboard_path: str,
                          output_path: str = None) -> list[dict]:
        """
        Analyze all clips in a manifest and update clip_start_sec.

        Args:
            manifest_path: Path to footage manifest JSON
            storyboard_path: Path to storyboard JSON
            output_path: Where to save updated manifest (overwrites if None)

        Returns:
            List of analysis results
        """
        with open(manifest_path) as f:
            manifest = json.load(f)
        with open(storyboard_path) as f:
            storyboard = json.load(f)

        # Flatten storyboard
        segments = []
        if isinstance(storyboard, dict) and "scenes" in storyboard:
            for scene in storyboard["scenes"]:
                segments.extend(scene.get("segments", []))
        elif isinstance(storyboard, dict) and "segments" in storyboard:
            segments = storyboard["segments"]

        seg_lookup = {s.get("segment_index", i): s for i, s in enumerate(segments)}

        results = []
        clips = manifest.get("clips", [])

        for clip in clips:
            local_path = clip.get("local_path", "")
            if not local_path or not os.path.exists(local_path):
                continue

            # Only analyze video clips (not images)
            ext = Path(local_path).suffix.lower()
            if ext not in ('.mp4', '.mkv', '.webm', '.mov', '.avi'):
                continue

            seg_idx = clip.get("segment_index", 0)
            segment = seg_lookup.get(seg_idx, {"text": ""})
            context = segment.get("text", clip.get("search_query", ""))

            result = self.find_best_moment(local_path, context)
            clip["clip_start_sec"] = result["best_timestamp_sec"]
            clip["clip_score"] = result["best_score"]
            results.append(result)

        # Save updated manifest
        save_path = output_path or manifest_path
        Path(save_path).write_text(json.dumps(manifest, indent=2))
        print(f"\nUpdated manifest saved: {save_path}")
        print(f"  Analyzed {len(results)} clips")

        return results


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find best moments in video clips")
    parser.add_argument("clip", nargs="?", help="Path to a single video clip")
    parser.add_argument("--context", "-c", help="Script context for the clip")
    parser.add_argument("--manifest", "-m", help="Footage manifest JSON")
    parser.add_argument("--storyboard", "-s", help="Storyboard JSON")
    parser.add_argument("--output", "-o", help="Output path for updated manifest")
    args = parser.parse_args()

    analyzer = ClipAnalyzer()

    if args.manifest and args.storyboard:
        results = analyzer.analyze_manifest(args.manifest, args.storyboard, args.output)
        print(f"\nAnalyzed {len(results)} clips")
    elif args.clip:
        context = args.context or "general documentary footage"
        result = analyzer.find_best_moment(args.clip, context)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
