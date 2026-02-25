#!/usr/bin/env python3
"""
Fern Complete Visual Analyzer (with AI)
Extracts comprehensive visual patterns using ffmpeg + Claude Vision API.

Analyzes each shot for:
- 3D animation vs real footage
- Camera angle (aerial, close-up, wide, POV, etc.)
- Shot type (static, pan, zoom, tracking)
- Content (person, map, diagram, landscape, object, text)
- Color/mood (dark, bright, neutral)

Outputs complete visual formula with correlation to script moments.

Usage:
    export ANTHROPIC_API_KEY="your-key-here"
    python analyze_fern_visual_complete.py wLFY_Zu_O08 --max-frames 100
    python analyze_fern_visual_complete.py --all --max-frames 50

Cost: ~$0.50-1.00 per video depending on length (max-frames limits cost)
"""

import subprocess
import json
import re
import sys
import os
import base64
import statistics
from pathlib import Path
from collections import Counter, defaultdict
import anthropic

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get API key from environment
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("❌ ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY='your-key'")
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================================
# SCENE DETECTION & KEYFRAME EXTRACTION
# ============================================================================

def detect_cuts(video_path, threshold=0.3):
    """Detect scene changes using ffmpeg"""
    print(f"  Detecting cuts...")

    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-filter:v', f'select=gt(scene\\,{threshold}),showinfo',
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        pattern = r'pts_time:([\d.]+)'
        matches = re.findall(pattern, result.stderr)
        cut_times = sorted(set(float(t) for t in matches))
        print(f"  Found {len(cut_times)} cuts")
        return cut_times
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def extract_keyframe(video_path, timestamp, output_path):
    """Extract a single frame at timestamp"""
    cmd = [
        'ffmpeg', '-ss', str(timestamp), '-i', str(video_path),
        '-vframes', '1', '-q:v', '2',
        '-y', str(output_path)
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=30, check=True)
        return True
    except:
        return False


def extract_keyframes_at_cuts(video_path, cut_times, output_dir, max_frames=None):
    """Extract keyframes at each cut (or sample if too many)"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sample if too many cuts
    if max_frames and len(cut_times) > max_frames:
        print(f"  Sampling {max_frames} of {len(cut_times)} cuts to save API costs...")
        step = len(cut_times) // max_frames
        sampled_times = [cut_times[i] for i in range(0, len(cut_times), step)][:max_frames]
    else:
        sampled_times = cut_times

    print(f"  Extracting {len(sampled_times)} keyframes...")

    keyframes = []
    for i, timestamp in enumerate(sampled_times):
        output_path = output_dir / f"frame_{i:04d}.jpg"
        if extract_keyframe(video_path, timestamp, output_path):
            keyframes.append({
                'index': i,
                'timestamp': timestamp,
                'path': output_path
            })

        if (i + 1) % 50 == 0:
            print(f"    Extracted {i + 1}/{len(sampled_times)}...")

    print(f"  ✓ Extracted {len(keyframes)} keyframes")
    return keyframes


# ============================================================================
# AI VISUAL CLASSIFICATION
# ============================================================================

def classify_frame_batch(frames_data, video_title):
    """
    Classify multiple frames with Claude Vision API.

    Batch classification is more efficient and provides better context.
    """

    # Prepare images
    image_contents = []
    for frame in frames_data:
        with open(frame['path'], 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        image_contents.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_data
            }
        })

    # Build prompt
    prompt = f"""Analyze these frames from the video "{video_title}".

For EACH frame, provide a JSON object with this exact structure:
{{
  "frame_index": <number>,
  "footage_type": "3D_animation" | "real_footage" | "hybrid" | "graphics",
  "camera_angle": "aerial" | "close_up" | "medium" | "wide" | "POV" | "map_view" | "diagram",
  "shot_type": "static" | "slow_pan" | "fast_pan" | "zoom_in" | "zoom_out" | "tracking" | "handheld",
  "content": "person" | "landscape" | "building" | "map" | "diagram" | "text" | "object" | "vehicle" | "crowd" | "abstract",
  "mood": "dark" | "bright" | "neutral" | "dramatic" | "calm",
  "motion_level": "static" | "slow" | "medium" | "fast"
}}

Return a JSON array with one object per frame, in order.

Key distinctions:
- "3D_animation": Computer-generated, stylized rendering (like Blender/Cinema4D)
- "real_footage": Actual video/photo footage from real world
- "graphics": Text overlays, diagrams, maps, infographics
- "hybrid": Mix of 3D and real (e.g., 3D building on real satellite image)

Respond ONLY with the JSON array, no other text."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": image_contents + [{"type": "text", "text": prompt}]
            }]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON
        # Remove markdown code fences if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json\s*|\s*```$', '', response_text, flags=re.MULTILINE).strip()

        classifications = json.loads(response_text)
        return classifications

    except Exception as e:
        print(f"    ⚠️  Classification error: {e}")
        return []


def classify_all_keyframes(keyframes, video_title, batch_size=5):
    """Classify all keyframes in batches"""

    print(f"  Classifying {len(keyframes)} frames with Claude Vision API...")
    print(f"  Batch size: {batch_size} (cost: ~${len(keyframes) * 0.01:.2f})")

    all_classifications = []

    for i in range(0, len(keyframes), batch_size):
        batch = keyframes[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(keyframes) + batch_size - 1) // batch_size

        print(f"    Batch {batch_num}/{total_batches}...")

        classifications = classify_frame_batch(batch, video_title)

        if classifications:
            # Merge with keyframe metadata
            for j, classification in enumerate(classifications):
                if i + j < len(keyframes):
                    keyframe_data = keyframes[i + j].copy()
                    keyframe_data.update(classification)
                    all_classifications.append(keyframe_data)

    print(f"  ✓ Classified {len(all_classifications)} frames")
    return all_classifications


# ============================================================================
# PATTERN EXTRACTION
# ============================================================================

def extract_visual_patterns(classified_frames, video_duration):
    """Extract visual patterns from classified frames"""

    if not classified_frames:
        return {}

    # Overall distributions
    footage_types = Counter(f['footage_type'] for f in classified_frames)
    camera_angles = Counter(f['camera_angle'] for f in classified_frames)
    shot_types = Counter(f['shot_type'] for f in classified_frames)
    content_types = Counter(f['content'] for f in classified_frames)
    moods = Counter(f['mood'] for f in classified_frames)
    motion_levels = Counter(f['motion_level'] for f in classified_frames)

    total_frames = len(classified_frames)

    # Calculate percentages
    def to_percentages(counter):
        return {k: (v / total_frames * 100) for k, v in counter.items()}

    patterns = {
        'total_frames_analyzed': total_frames,
        'footage_type_distribution': to_percentages(footage_types),
        'camera_angle_distribution': to_percentages(camera_angles),
        'shot_type_distribution': to_percentages(shot_types),
        'content_distribution': to_percentages(content_types),
        'mood_distribution': to_percentages(moods),
        'motion_distribution': to_percentages(motion_levels),
    }

    # Analyze timeline (intro/body/outro)
    intro_end = video_duration * 0.10
    body_end = video_duration * 0.85

    intro_frames = [f for f in classified_frames if f['timestamp'] < intro_end]
    body_frames = [f for f in classified_frames if intro_end <= f['timestamp'] < body_end]
    outro_frames = [f for f in classified_frames if f['timestamp'] >= body_end]

    def section_patterns(frames, section_name):
        if not frames:
            return {}
        n = len(frames)
        return {
            'footage_types': {k: v/n*100 for k, v in Counter(f['footage_type'] for f in frames).items()},
            'camera_angles': {k: v/n*100 for k, v in Counter(f['camera_angle'] for f in frames).items()},
            'moods': {k: v/n*100 for k, v in Counter(f['mood'] for f in frames).items()},
        }

    patterns['by_section'] = {
        'intro': section_patterns(intro_frames, 'intro'),
        'body': section_patterns(body_frames, 'body'),
        'outro': section_patterns(outro_frames, 'outro'),
    }

    return patterns


# ============================================================================
# MAIN ANALYZER
# ============================================================================

def analyze_video_complete(video_id, base_dir='.', max_frames=100):
    """Run complete visual analysis with AI classification"""

    base_path = Path(base_dir)
    video_dir = base_path / 'analysis' / 'fern' / video_id

    if not video_dir.exists():
        print(f"❌ Video directory not found: {video_dir}")
        return None

    video_file = video_dir / 'video.mp4'
    if not video_file.exists():
        print(f"❌ Video file not found: {video_file}")
        return None

    # Load metadata
    info_file = video_dir / 'video.info.json'
    if info_file.exists():
        with open(info_file) as f:
            info = json.load(f)
        title = info.get('title', 'Unknown')
        views = info.get('view_count', 0)
        duration = info.get('duration', 0)
    else:
        title = video_id
        views = 0
        duration = 0

    print(f"\n{'='*70}")
    print(f"  COMPLETE VISUAL ANALYSIS: {title}")
    print(f"  Views: {views:,} | Duration: {duration//60}:{duration%60:02d}")
    print(f"{'='*70}\n")

    # Step 1: Detect cuts
    cut_times = detect_cuts(video_file, threshold=0.3)
    if not cut_times:
        print("  ⚠️  No cuts detected")
        return None

    # Step 2: Extract keyframes
    keyframes_dir = video_dir / 'keyframes'
    keyframes = extract_keyframes_at_cuts(video_file, cut_times, keyframes_dir, max_frames=max_frames)

    if not keyframes:
        print("  ❌ No keyframes extracted")
        return None

    # Step 3: Classify with AI
    classified = classify_all_keyframes(keyframes, title, batch_size=5)

    if not classified:
        print("  ❌ Classification failed")
        return None

    # Step 4: Extract patterns
    patterns = extract_visual_patterns(classified, duration)

    # Print summary
    print(f"\n  VISUAL PATTERNS:")
    print(f"    Footage types:")
    for ftype, pct in sorted(patterns['footage_type_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"      {ftype}: {pct:.1f}%")

    print(f"\n    Camera angles:")
    for angle, pct in sorted(patterns['camera_angle_distribution'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      {angle}: {pct:.1f}%")

    print(f"\n    Moods:")
    for mood, pct in sorted(patterns['mood_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"      {mood}: {pct:.1f}%")

    # Save results
    result = {
        'video_id': video_id,
        'title': title,
        'views': views,
        'duration': duration,
        'total_cuts': len(cut_times),
        'frames_analyzed': len(classified),
        'patterns': patterns,
        'classified_frames': classified,
    }

    output_file = video_dir / 'visual_analysis_complete.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n  ✓ Saved: {output_file}")
    return result


def analyze_all_complete(base_dir='.', max_frames=50):
    """Analyze all videos with video.mp4 files"""

    base_path = Path(base_dir)
    fern_dir = base_path / 'analysis' / 'fern'

    video_dirs = [d.name for d in fern_dir.iterdir() if d.is_dir() and (d / 'video.mp4').exists()]

    if not video_dirs:
        print("❌ No videos found")
        return

    print(f"\n{'='*70}")
    print(f"  BATCH COMPLETE VISUAL ANALYSIS - {len(video_dirs)} videos")
    print(f"  Max frames per video: {max_frames}")
    print(f"  Estimated cost: ${len(video_dirs) * max_frames * 0.01:.2f}")
    print(f"{'='*70}")

    results = []
    for i, video_id in enumerate(video_dirs, 1):
        print(f"\n[{i}/{len(video_dirs)}] {video_id}")
        result = analyze_video_complete(video_id, base_dir, max_frames)
        if result:
            results.append(result)

    if not results:
        return

    # Aggregate formula
    print(f"\n{'='*70}")
    print(f"  VISUAL FORMULA - Aggregated from {len(results)} videos")
    print(f"{'='*70}\n")

    # Aggregate distributions
    all_footage = Counter()
    all_angles = Counter()
    all_moods = Counter()
    all_content = Counter()

    for r in results:
        p = r['patterns']
        for k, v in p['footage_type_distribution'].items():
            all_footage[k] += v
        for k, v in p['camera_angle_distribution'].items():
            all_angles[k] += v
        for k, v in p['mood_distribution'].items():
            all_moods[k] += v
        for k, v in p['content_distribution'].items():
            all_content[k] += v

    n = len(results)
    visual_formula = {
        'videos_analyzed': n,
        'total_frames_analyzed': sum(r['frames_analyzed'] for r in results),
        'avg_footage_distribution': {k: v/n for k, v in all_footage.items()},
        'avg_camera_angles': {k: v/n for k, v in all_angles.items()},
        'avg_moods': {k: v/n for k, v in all_moods.items()},
        'avg_content': {k: v/n for k, v in all_content.items()},
        'per_video_results': results,
    }

    print("  FOOTAGE TYPE:")
    for ftype, pct in sorted(visual_formula['avg_footage_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {ftype}: {pct:.1f}%")

    print("\n  CAMERA ANGLES:")
    for angle, pct in sorted(visual_formula['avg_camera_angles'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {angle}: {pct:.1f}%")

    print("\n  MOOD:")
    for mood, pct in sorted(visual_formula['avg_moods'].items(), key=lambda x: x[1], reverse=True):
        print(f"    {mood}: {pct:.1f}%")

    output_file = fern_dir / 'VISUAL_FORMULA_COMPLETE.json'
    with open(output_file, 'w') as f:
        json.dump(visual_formula, f, indent=2)

    print(f"\n  ✓ Saved formula: {output_file}\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    max_frames = 100
    if '--max-frames' in sys.argv:
        idx = sys.argv.index('--max-frames')
        max_frames = int(sys.argv[idx + 1])

    if '--all' in sys.argv:
        analyze_all_complete(max_frames=max_frames)
    else:
        video_id = sys.argv[1]
        analyze_video_complete(video_id, max_frames=max_frames)


if __name__ == '__main__':
    main()
