#!/usr/bin/env python3
"""
Fern Hybrid Analyzer with Checkpoint/Resume

CONTINUITY GUARANTEE:
- Detects ALL cuts first (scene boundaries)
- Samples within each shot at regular intervals
- Ensures no gaps in timeline
- Every important moment is captured

CHECKPOINT SYSTEM:
- Saves progress every 100 frames
- Automatically resumes next day
- Tracks daily API limits (1,500/day for Gemini free)
- Pauses when limit hit, auto-continues next day

Usage:
    export GOOGLE_API_KEY="your-key"
    python analyze_fern_hybrid_checkpoint.py --all --model gemini-flash

    # Resume next day (automatically picks up where it left off)
    python analyze_fern_hybrid_checkpoint.py --all --model gemini-flash --resume
"""

import subprocess
import json
import re
import sys
import os
import base64
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# ============================================================================
# CONFIGURATION
# ============================================================================

MODELS = {
    'gemini-flash': {
        'provider': 'google',
        'model_id': 'gemini-2.0-flash-exp',
        'daily_limit': 1500,  # Free tier
        'cost_per_image': 0.0,
        'description': 'Google Gemini 2.0 Flash (FREE, 1500/day)'
    },
    'gemini-flash-paid': {
        'provider': 'google',
        'model_id': 'gemini-1.5-flash',
        'daily_limit': None,  # No limit (paid)
        'cost_per_image': 0.001,
        'description': 'Google Gemini 1.5 Flash (Paid)'
    },
    'gpt-4o-mini': {
        'provider': 'openai',
        'model_id': 'gpt-4o-mini',
        'daily_limit': None,
        'cost_per_image': 0.0001,
        'description': 'OpenAI GPT-4o-mini'
    }
}

CHECKPOINT_FILE = 'analysis/fern/.checkpoint.json'

# ============================================================================
# CHECKPOINT MANAGEMENT
# ============================================================================

def load_checkpoint():
    """Load checkpoint from previous run"""
    if not Path(CHECKPOINT_FILE).exists():
        return None

    with open(CHECKPOINT_FILE, 'r') as f:
        checkpoint = json.load(f)

    # Check if it's from today
    checkpoint_date = datetime.fromisoformat(checkpoint['date'])
    today = datetime.now().date()

    if checkpoint_date.date() != today:
        # New day, reset counter
        checkpoint['requests_today'] = 0
        checkpoint['date'] = datetime.now().isoformat()

    return checkpoint


def save_checkpoint(checkpoint):
    """Save checkpoint for resume"""
    Path(CHECKPOINT_FILE).parent.mkdir(parents=True, exist_ok=True)

    checkpoint['date'] = datetime.now().isoformat()

    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def init_checkpoint(video_ids, model):
    """Initialize new checkpoint"""
    return {
        'video_ids': video_ids,
        'current_video_index': 0,
        'current_frame_index': 0,
        'requests_today': 0,
        'model': model,
        'date': datetime.now().isoformat(),
        'total_processed': 0
    }

# ============================================================================
# CUT DETECTION
# ============================================================================

def detect_cuts(video_path, threshold=0.3):
    """Detect all scene cuts using ffmpeg"""
    print(f"  Detecting cuts (threshold={threshold})...")

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
        print(f"  ✓ Found {len(cut_times)} cuts")
        return cut_times
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def generate_hybrid_timestamps(duration, cut_times, interval=2.0):
    """
    Generate timestamps using HYBRID approach:
    - Include ALL cuts (scene boundaries)
    - Sample within each shot at regular intervals
    - Ensures complete continuity, no gaps
    """

    # Add start and end
    boundaries = [0.0] + cut_times + [duration]
    boundaries = sorted(set(boundaries))

    timestamps = []

    for i in range(len(boundaries) - 1):
        shot_start = boundaries[i]
        shot_end = boundaries[i + 1]
        shot_duration = shot_end - shot_start

        # Always include shot start (the cut point)
        timestamps.append(shot_start)

        # Sample within shot based on duration
        if shot_duration <= 3.0:
            # Short shot (0-3 sec): start + end
            if shot_duration > 1.0:
                timestamps.append(shot_end - 0.5)

        elif shot_duration <= 6.0:
            # Medium shot (3-6 sec): start + middle + end
            timestamps.append(shot_start + shot_duration / 2)
            timestamps.append(shot_end - 0.5)

        else:
            # Long shot (>6 sec): start + interval samples + end
            t = shot_start + interval
            while t < shot_end - 1.0:
                timestamps.append(t)
                t += interval
            timestamps.append(shot_end - 0.5)

    # Remove duplicates and sort
    timestamps = sorted(set(timestamps))

    print(f"  ✓ Generated {len(timestamps)} sample points")
    print(f"    Cuts: {len(cut_times)}, Intervals: {len(timestamps) - len(cut_times)}")

    return timestamps

# ============================================================================
# VIDEO PROCESSING
# ============================================================================

def get_video_duration(video_path):
    """Get video duration in seconds"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except:
        return 0


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


def extract_hybrid_keyframes(video_path, timestamps, output_dir, start_index=0):
    """Extract keyframes at hybrid timestamps"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Extracting keyframes (starting from {start_index}/{len(timestamps)})...")

    keyframes = []
    for i in range(start_index, len(timestamps)):
        ts = timestamps[i]
        output_path = output_dir / f'frame_{i:04d}_{ts:.2f}s.jpg'

        # Skip if already extracted
        if output_path.exists():
            keyframes.append({
                'path': output_path,
                'timestamp': ts,
                'index': i
            })
            continue

        if extract_keyframe(video_path, ts, output_path):
            keyframes.append({
                'path': output_path,
                'timestamp': ts,
                'index': i
            })

        if (i + 1) % 50 == 0:
            print(f"    {i + 1}/{len(timestamps)} frames extracted")

    print(f"  ✓ Extracted {len(keyframes)} keyframes")
    return keyframes

# ============================================================================
# VTT PARSING
# ============================================================================

def parse_vtt_word_timeline(vtt_path):
    """Parse VTT to get exact word timestamps"""

    if not Path(vtt_path).exists():
        return []

    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'<(\d{2}):(\d{2}):([\d.]+)><c>\s*([^<]+)</c>'
    matches = re.findall(pattern, content)

    word_timeline = []
    for h, m, s, word in matches:
        timestamp = int(h) * 3600 + int(m) * 60 + float(s)
        word_timeline.append({
            'time': timestamp,
            'word': word.strip()
        })

    return word_timeline


def get_words_at_time(word_timeline, timestamp, window=1.5):
    """Get words spoken around a timestamp"""
    words = []
    for entry in word_timeline:
        if abs(entry['time'] - timestamp) <= window:
            words.append(entry['word'])

    return ' '.join(words) if words else '[no speech]'

# ============================================================================
# AI CLASSIFICATION
# ============================================================================

CLASSIFICATION_PROMPT = """Analyze this frame from a YouTube video.

Return ONLY a JSON object (no other text):

{
  "footage_type": "3D_animation | real_footage | hybrid | graphics | text_overlay",
  "camera_angle": "aerial | close_up | medium | wide | POV | map_view | diagram",
  "camera_movement": "none | zooming_in | zooming_out | panning_left | panning_right | tracking",
  "content": "person | people | landscape | building | map | diagram | text | object | vehicle | document",
  "text_on_screen": "yes | no",
  "text_content": "<text if visible>",
  "mood": "dark | bright | neutral | dramatic | mysterious"
}"""


def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, 'rb') as f:
        return base64.standard_b64encode(f.read()).decode('utf-8')


def classify_with_gemini(image_path, model_id):
    """Classify with Google Gemini"""
    import google.generativeai as genai

    api_key = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(model_id)

    from PIL import Image
    img = Image.open(image_path)

    response = model.generate_content([CLASSIFICATION_PROMPT, img])

    text = response.text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {'error': 'Could not parse response'}


def classify_keyframe(keyframe, model_name):
    """Classify a single keyframe"""

    config = MODELS[model_name]
    provider = config['provider']
    model_id = config['model_id']

    try:
        if provider == 'google':
            result = classify_with_gemini(keyframe['path'], model_id)
        else:
            result = {'error': 'Provider not implemented'}

        result['timestamp'] = keyframe['timestamp']
        result['frame_index'] = keyframe['index']
        return result

    except Exception as e:
        return {
            'timestamp': keyframe['timestamp'],
            'frame_index': keyframe['index'],
            'error': str(e)
        }


def classify_with_limit(keyframes, model_name, checkpoint, start_index=0):
    """Classify keyframes with daily limit tracking"""

    config = MODELS[model_name]
    daily_limit = config['daily_limit']

    classified = []
    requests_made = 0

    for i, kf in enumerate(keyframes):
        # Check if we hit today's limit
        if daily_limit and checkpoint['requests_today'] >= daily_limit:
            print(f"\n⏸️  Hit daily limit ({daily_limit} requests)")
            print(f"   Processed {i} frames today")
            print(f"   Progress saved - run again tomorrow to continue")
            save_checkpoint(checkpoint)
            return classified, False  # Not complete

        result = classify_keyframe(kf, model_name)
        classified.append(result)

        checkpoint['requests_today'] += 1
        checkpoint['current_frame_index'] = start_index + i + 1
        checkpoint['total_processed'] += 1
        requests_made += 1

        # Save checkpoint every 100 frames
        if requests_made % 100 == 0:
            print(f"    {requests_made} frames classified (checkpoint saved)")
            save_checkpoint(checkpoint)

        # Rate limiting
        time.sleep(0.05)  # ~20 req/sec

    return classified, True  # Complete

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def analyze_video_hybrid(video_id, base_dir, model, checkpoint, resume=False):
    """Analyze video with hybrid sampling and checkpointing"""

    fern_dir = Path(base_dir) / 'analysis' / 'fern'
    video_dir = fern_dir / video_id

    video_file = video_dir / 'video.mp4'
    vtt_file = video_dir / 'video.en.vtt'
    info_file = video_dir / 'video.info.json'

    if not video_file.exists():
        print(f"❌ Video not found: {video_file}")
        return None, False

    # Load metadata
    metadata = {}
    if info_file.exists():
        with open(info_file, 'r') as f:
            metadata = json.load(f)

    title = metadata.get('title', 'Unknown')
    duration = get_video_duration(video_file)

    print(f"\n{'='*60}")
    print(f"Video: {title}")
    print(f"Duration: {duration:.1f}s")
    print(f"Model: {MODELS[model]['description']}")
    print(f"{'='*60}\n")

    # Step 1: Detect cuts
    print(f"Step 1: Detecting cuts...")
    cut_times = detect_cuts(video_file, threshold=0.3)

    # Step 2: Generate hybrid timestamps
    print(f"\nStep 2: Generating hybrid timestamps...")
    timestamps = generate_hybrid_timestamps(duration, cut_times, interval=2.0)

    # Determine start index (for resume)
    start_index = checkpoint.get('current_frame_index', 0) if resume else 0

    # Step 3: Extract keyframes
    print(f"\nStep 3: Extracting keyframes...")
    keyframes_dir = video_dir / 'hybrid_keyframes'
    all_keyframes = extract_hybrid_keyframes(video_file, timestamps, keyframes_dir, start_index)

    # Step 4: Load words
    print(f"\nStep 4: Loading word timeline...")
    word_timeline = []
    if vtt_file.exists():
        word_timeline = parse_vtt_word_timeline(vtt_file)
        print(f"  ✓ {len(word_timeline)} words")

    # Step 5: Classify with limits
    print(f"\nStep 5: AI classification...")
    print(f"  Starting from frame {start_index}/{len(timestamps)}")
    print(f"  Requests used today: {checkpoint['requests_today']}")

    classified, complete = classify_with_limit(all_keyframes, model, checkpoint, start_index)

    # Step 6: Build timeline (include previous results if resuming)
    print(f"\nStep 6: Building timeline...")

    # Load previous results if resuming
    output_file = video_dir / f'timeline_hybrid_{model}.json'
    previous_timeline = []
    if resume and output_file.exists():
        with open(output_file, 'r') as f:
            previous_data = json.load(f)
            previous_timeline = previous_data.get('timeline', [])

    # Add new results
    for kf in all_keyframes:
        ts = kf['timestamp']
        classification = next((c for c in classified if c.get('timestamp') == ts), {})
        words = get_words_at_time(word_timeline, ts, window=1.5)

        # Check if already in previous timeline
        if not any(e['timestamp'] == ts for e in previous_timeline):
            previous_timeline.append({
                'timestamp': ts,
                'words_spoken': words,
                'visual': classification,
                'keyframe': str(kf['path'])
            })

    # Sort by timestamp
    timeline = sorted(previous_timeline, key=lambda x: x['timestamp'])

    # Save
    result = {
        'video_id': video_id,
        'title': title,
        'duration': duration,
        'model': model,
        'sample_count': len(timeline),
        'cut_count': len(cut_times),
        'complete': complete,
        'timeline': timeline,
        'metadata': metadata
    }

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    if complete:
        print(f"\n✅ Analysis complete: {output_file}")
    else:
        print(f"\n⏸️  Analysis paused: {output_file}")
        print(f"   Run again tomorrow to continue")

    return result, complete


def analyze_all_videos_checkpoint(base_dir, model, resume=False):
    """Analyze all videos with checkpoint/resume"""

    fern_dir = Path(base_dir) / 'analysis' / 'fern'
    video_dirs = [d for d in fern_dir.iterdir() if d.is_dir() and (d / 'video.mp4').exists()]
    video_ids = [d.name for d in video_dirs]

    # Load or create checkpoint
    if resume:
        checkpoint = load_checkpoint()
        if not checkpoint:
            print("⚠️  No checkpoint found, starting fresh")
            checkpoint = init_checkpoint(video_ids, model)
    else:
        checkpoint = init_checkpoint(video_ids, model)

    print(f"\n{'='*60}")
    print(f"ANALYSIS SESSION")
    print(f"{'='*60}")
    print(f"Model: {MODELS[model]['description']}")
    print(f"Videos: {len(video_ids)}")
    print(f"Requests used today: {checkpoint['requests_today']}")
    print(f"Total processed: {checkpoint['total_processed']}")
    print(f"{'='*60}\n")

    # Process videos starting from checkpoint
    results = []
    start_video = checkpoint.get('current_video_index', 0)

    for i in range(start_video, len(video_ids)):
        video_id = video_ids[i]
        checkpoint['current_video_index'] = i
        checkpoint['current_frame_index'] = 0  # Reset for new video

        print(f"\n[{i+1}/{len(video_ids)}] Analyzing {video_id}...")

        result, complete = analyze_video_hybrid(video_id, base_dir, model, checkpoint, resume=resume)

        if result:
            results.append(result)

        if not complete:
            # Hit daily limit
            save_checkpoint(checkpoint)
            print(f"\n⏸️  Session paused at video {i+1}/{len(video_ids)}")
            print(f"   Run with --resume tomorrow to continue")
            return results, False

        # Move to next video
        checkpoint['current_video_index'] = i + 1
        checkpoint['current_frame_index'] = 0
        save_checkpoint(checkpoint)

    # All done
    print(f"\n{'='*60}")
    print(f"✅ ALL VIDEOS ANALYZED!")
    print(f"{'='*60}\n")

    # Aggregate patterns
    all_footage_types = []
    all_camera_angles = []

    for result in results:
        if result.get('complete'):
            for entry in result['timeline']:
                v = entry['visual']
                if 'footage_type' in v:
                    all_footage_types.append(v['footage_type'])
                if 'camera_angle' in v:
                    all_camera_angles.append(v['camera_angle'])

    formula = {
        'footage_distribution': dict(Counter(all_footage_types)),
        'camera_angles': dict(Counter(all_camera_angles)),
        'model': model,
        'videos_analyzed': len(results),
        'total_samples': len(all_footage_types)
    }

    output_file = fern_dir / f'VISUAL_FORMULA_HYBRID_{model}.json'
    with open(output_file, 'w') as f:
        json.dump(formula, f, indent=2)

    print(f"✓ Formula saved: {output_file}")

    # Summary
    print(f"\nFOOTAGE DISTRIBUTION:")
    for ft, count in sorted(formula['footage_distribution'].items(), key=lambda x: -x[1]):
        pct = count / len(all_footage_types) * 100
        print(f"  {ft}: {pct:.1f}% ({count} frames)")

    return results, True

# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Fern Hybrid Analyzer with Checkpoint/Resume',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start fresh analysis
  export GOOGLE_API_KEY="your-key"
  python analyze_fern_hybrid_checkpoint.py --all --model gemini-flash

  # Resume next day (automatically continues)
  python analyze_fern_hybrid_checkpoint.py --all --model gemini-flash --resume
"""
    )

    parser.add_argument('--all', action='store_true', required=True, help='Analyze all videos')
    parser.add_argument('--model', default='gemini-flash', choices=MODELS.keys())
    parser.add_argument('--base-dir', default='.', help='Base directory')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')

    args = parser.parse_args()

    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not set")
        print("Get free key at: https://aistudio.google.com/app/apikey")
        print("Then run: export GOOGLE_API_KEY='your-key'")
        sys.exit(1)

    # Check dependencies
    try:
        import google.generativeai
        from PIL import Image
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install google-generativeai pillow")
        sys.exit(1)

    # Run
    analyze_all_videos_checkpoint(args.base_dir, args.model, args.resume)
