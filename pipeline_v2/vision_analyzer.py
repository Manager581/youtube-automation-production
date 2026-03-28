#!/usr/bin/env python3
"""
vision_analyzer.py — Analyze all clips and images using Claude vision.

Builds a structured manifest describing every piece of media so the director
can make informed editorial decisions about what footage to use where.

For VIDEO CLIPS:
  - Extracts frames at 5s intervals via ffmpeg
  - Sends each frame to Claude vision for description
  - Identifies best moments with relevance scoring

For IMAGES:
  - Sends full image to Claude vision
  - Returns description, topics, and mood

Output: JSON manifest of all analyzed media.

Usage:
    python -m pipeline_v2.vision_analyzer --clips footage/clips/ --images images/ --output vision_manifest.json
    python -m pipeline_v2.vision_analyzer --clips footage/clips/ --output clips_only.json
    python -m pipeline_v2.vision_analyzer --images images/ --output images_only.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude, query_claude_vision

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.mov', '.avi', '.m4v'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
FRAME_INTERVAL_SEC = 5.0


# -- Helpers ------------------------------------------------------------------

def get_duration(clip_path):
    """Get video duration in seconds via ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json', str(clip_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return float(json.loads(result.stdout)['format']['duration'])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError):
        return 0.0


def extract_frame(clip_path, timestamp_sec, output_path):
    """Extract a single frame from a clip at the given timestamp."""
    cmd = [
        'ffmpeg', '-y', '-ss', str(timestamp_sec),
        '-i', str(clip_path),
        '-frames:v', '1', '-q:v', '2',
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        return result.returncode == 0 and os.path.exists(output_path)
    except subprocess.TimeoutExpired:
        return False


def collect_files(directories, extensions):
    """Recursively collect files with given extensions from directories."""
    files = []
    for d in directories:
        d = Path(d)
        if not d.exists():
            print(f"  WARNING: directory not found: {d}", file=sys.stderr)
            continue
        if d.is_file():
            if d.suffix.lower() in extensions:
                files.append(d)
            continue
        for root, _, filenames in os.walk(d):
            for fn in sorted(filenames):
                p = Path(root) / fn
                if p.suffix.lower() in extensions:
                    files.append(p)
    return files


# -- Core Analysis Functions --------------------------------------------------

def analyze_clip(clip_path):
    """Analyze a video clip by sampling frames and describing each.

    Args:
        clip_path: Path to a video file.

    Returns:
        dict with keys: filename, path, duration, frame_descriptions,
                        topics, best_moments
    """
    clip_path = Path(clip_path)
    if not clip_path.exists():
        return {"filename": clip_path.name, "error": "file not found"}

    duration = get_duration(clip_path)
    if duration <= 0:
        return {
            "filename": clip_path.name,
            "path": str(clip_path),
            "duration": 0,
            "frame_descriptions": [],
            "topics": [],
            "best_moments": [],
            "error": "could not determine duration",
        }

    # Calculate sample timestamps
    timestamps = []
    t = 0.0
    while t < duration:
        timestamps.append(round(t, 1))
        t += FRAME_INTERVAL_SEC
    # Always include a frame near the end
    if duration > FRAME_INTERVAL_SEC and (duration - timestamps[-1]) > 2.0:
        timestamps.append(round(duration - 0.5, 1))

    print(f"  Clip: {clip_path.name}  ({duration:.1f}s, {len(timestamps)} frames)")

    frame_descriptions = []
    tmp_dir = tempfile.mkdtemp(prefix="vision_frames_")

    for ts in timestamps:
        frame_path = os.path.join(tmp_dir, f"frame_{ts:.1f}s.jpg")
        if not extract_frame(clip_path, ts, frame_path):
            continue

        prompt = (
            "Describe what you see in this video frame. Include: people, "
            "text on screen, setting, documents, actions. One sentence per detail."
        )
        description = query_claude_vision(prompt, frame_path, timeout=60)

        frame_descriptions.append({
            "timestamp": ts,
            "description": description.strip() if description else "",
        })

        # Clean up frame immediately to save disk
        try:
            os.remove(frame_path)
        except OSError:
            pass

    # Clean up temp dir
    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass

    # Derive topics and best moments from descriptions
    topics, best_moments = _extract_topics_and_moments(frame_descriptions, duration)

    return {
        "filename": clip_path.name,
        "path": str(clip_path),
        "duration": round(duration, 2),
        "frame_descriptions": frame_descriptions,
        "topics": topics,
        "best_moments": best_moments,
    }


def analyze_image(image_path):
    """Analyze a single image using Claude vision.

    Args:
        image_path: Path to an image file.

    Returns:
        dict with keys: filename, path, description, topics, mood
    """
    image_path = Path(image_path)
    if not image_path.exists():
        return {"filename": image_path.name, "error": "file not found"}

    print(f"  Image: {image_path.name}")

    prompt = (
        "Analyze this image for use in a documentary. Return ONLY valid JSON:\n"
        '{"description": "one-paragraph description of what the image shows",'
        ' "topics": ["keyword1", "keyword2", ...],'
        ' "mood": "one word mood (e.g. tense, somber, hopeful, neutral)"}'
    )
    response = query_claude_vision(prompt, str(image_path), timeout=60)

    description = ""
    topics = []
    mood = ""

    if response:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group())
                description = data.get("description", "")
                topics = data.get("topics", [])
                mood = data.get("mood", "")
        except (json.JSONDecodeError, AttributeError):
            # Fall back to raw text as description
            description = response.strip()

    return {
        "filename": image_path.name,
        "path": str(image_path),
        "description": description,
        "topics": topics,
        "mood": mood,
    }


def analyze_all(clip_dirs=None, image_dirs=None, output_path=None):
    """Analyze all clips and images, build a complete vision manifest.

    Args:
        clip_dirs: List of directories (or files) containing video clips.
        image_dirs: List of directories (or files) containing images.
        output_path: Where to write the JSON manifest. None = don't write.

    Returns:
        dict: The complete vision manifest.
    """
    manifest = {
        "clips": [],
        "images": [],
        "stats": {"total_clips": 0, "total_images": 0, "total_frames_analyzed": 0},
    }

    # Analyze clips
    if clip_dirs:
        clip_files = collect_files(clip_dirs, VIDEO_EXTENSIONS)
        print(f"\nAnalyzing {len(clip_files)} video clips...")
        for clip in clip_files:
            result = analyze_clip(clip)
            manifest["clips"].append(result)
            manifest["stats"]["total_frames_analyzed"] += len(
                result.get("frame_descriptions", [])
            )
        manifest["stats"]["total_clips"] = len(clip_files)

    # Analyze images
    if image_dirs:
        image_files = collect_files(image_dirs, IMAGE_EXTENSIONS)
        print(f"\nAnalyzing {len(image_files)} images...")
        for img in image_files:
            result = analyze_image(img)
            manifest["images"].append(result)
        manifest["stats"]["total_images"] = len(image_files)

    # Write output
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(manifest, indent=2))
        print(f"\nManifest written: {output_path}")

    total = manifest["stats"]["total_clips"] + manifest["stats"]["total_images"]
    frames = manifest["stats"]["total_frames_analyzed"]
    print(f"Done: {total} media items, {frames} frames analyzed")

    return manifest


# -- Internal Helpers ---------------------------------------------------------

def _extract_topics_and_moments(frame_descriptions, duration):
    """Use Claude to derive topics and best moments from frame descriptions."""
    if not frame_descriptions:
        return [], []

    # Build a summary of all descriptions for Claude to process
    desc_text = "\n".join(
        f"  [{fd['timestamp']}s] {fd['description']}"
        for fd in frame_descriptions
        if fd.get("description")
    )
    if not desc_text.strip():
        return [], []

    prompt = (
        "Given these video frame descriptions (with timestamps), extract:\n"
        "1. TOPICS: A list of 3-8 keywords describing the clip content.\n"
        "2. BEST_MOMENTS: The 1-3 most visually compelling or narratively "
        "important moments, with a relevance_score 0.0-1.0.\n\n"
        f"Clip duration: {duration:.1f}s\n"
        f"Frame descriptions:\n{desc_text}\n\n"
        "Return ONLY valid JSON:\n"
        '{"topics": ["kw1","kw2"], '
        '"best_moments": [{"timestamp": 5.0, "description": "...", '
        '"relevance_score": 0.9}]}'
    )

    response = query_claude(prompt, timeout=60)
    topics = []
    best_moments = []

    if response:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group())
                topics = data.get("topics", [])
                best_moments = data.get("best_moments", [])
        except (json.JSONDecodeError, AttributeError):
            pass

    return topics, best_moments


# -- CLI ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze clips and images with Claude vision"
    )
    parser.add_argument(
        '--clips', nargs='+', metavar='DIR',
        help='Directories (or files) containing video clips',
    )
    parser.add_argument(
        '--images', nargs='+', metavar='DIR',
        help='Directories (or files) containing images',
    )
    parser.add_argument(
        '--output', '-o', default='vision_manifest.json',
        help='Output JSON manifest path (default: vision_manifest.json)',
    )
    args = parser.parse_args()

    if not args.clips and not args.images:
        parser.error("Provide at least one of --clips or --images")

    analyze_all(
        clip_dirs=args.clips,
        image_dirs=args.images,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
