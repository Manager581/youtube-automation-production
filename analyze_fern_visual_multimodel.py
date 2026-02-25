#!/usr/bin/env python3
"""
Fern Timeline Analyzer - Multi-Model Edition

Supports MULTIPLE AI vision models with cost comparison:

FREE OPTIONS:
  1. Gemini 2.0 Flash (FREE tier: 1,500/day) ⭐ RECOMMENDED
  2. Ollama locally on M1 (llama3.2-vision, llava, moondream)

CHEAP OPTIONS:
  3. GPT-4o-mini ($0.0001/img = $0.18 for 1,800 frames)
  4. Gemini 1.5 Flash ($0.001/img = $1.80 for 1,800 frames)
  5. GPT-4o ($0.002/img = $3.60 for 1,800 frames)

PREMIUM OPTIONS:
  6. Claude Sonnet ($0.01/img = $18 for 1,800 frames)

Usage:
    # FREE: Gemini 2.0 Flash
    export GOOGLE_API_KEY="your-key"
    python analyze_fern_visual_multimodel.py --all --model gemini-flash --interval 2

    # FREE: Ollama locally (must install first: brew install ollama)
    python analyze_fern_visual_multimodel.py --all --model ollama --interval 2

    # CHEAP: GPT-4o-mini
    export OPENAI_API_KEY="your-key"
    python analyze_fern_visual_multimodel.py --all --model gpt-4o-mini --interval 2

    # PREMIUM: Claude
    export ANTHROPIC_API_KEY="your-key"
    python analyze_fern_visual_multimodel.py --all --model claude --interval 2
"""

import subprocess
import json
import re
import sys
import os
import base64
import time
from pathlib import Path
from collections import Counter

# ============================================================================
# MODEL CONFIGS
# ============================================================================

MODELS = {
    'gemini-flash': {
        'provider': 'google',
        'model_id': 'gemini-2.0-flash-exp',
        'cost_per_image': 0.0,  # FREE tier
        'batch_size': 1,  # Gemini doesn't support multi-image well
        'description': 'Google Gemini 2.0 Flash (FREE, 1500/day limit)'
    },
    'gemini-flash-paid': {
        'provider': 'google',
        'model_id': 'gemini-1.5-flash',
        'cost_per_image': 0.001,
        'batch_size': 1,
        'description': 'Google Gemini 1.5 Flash (Paid: $0.001/image)'
    },
    'ollama': {
        'provider': 'ollama',
        'model_id': 'llama3.2-vision',
        'cost_per_image': 0.0,  # FREE (local)
        'batch_size': 1,
        'description': 'Ollama llama3.2-vision (FREE, runs on M1)'
    },
    'gpt-4o-mini': {
        'provider': 'openai',
        'model_id': 'gpt-4o-mini',
        'cost_per_image': 0.0001,
        'batch_size': 1,
        'description': 'OpenAI GPT-4o-mini (Cheap: $0.0001/image)'
    },
    'gpt-4o': {
        'provider': 'openai',
        'model_id': 'gpt-4o',
        'cost_per_image': 0.002,
        'batch_size': 5,
        'description': 'OpenAI GPT-4o (Mid: $0.002/image)'
    },
    'claude': {
        'provider': 'anthropic',
        'model_id': 'claude-3-5-sonnet-20241022',
        'cost_per_image': 0.01,
        'batch_size': 5,
        'description': 'Anthropic Claude Sonnet (Premium: $0.01/image)'
    }
}

# ============================================================================
# SETUP
# ============================================================================

def check_model_available(model_name):
    """Check if model is available and API key is set"""

    if model_name not in MODELS:
        print(f"❌ Unknown model: {model_name}")
        print(f"Available models: {', '.join(MODELS.keys())}")
        return False

    config = MODELS[model_name]
    provider = config['provider']

    if provider == 'google':
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print(f"❌ GOOGLE_API_KEY not set")
            print(f"Get a free key at: https://aistudio.google.com/app/apikey")
            print(f"Then run: export GOOGLE_API_KEY='your-key'")
            return False

    elif provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print(f"❌ OPENAI_API_KEY not set")
            print(f"Get key at: https://platform.openai.com/api-keys")
            print(f"Then run: export OPENAI_API_KEY='your-key'")
            return False

    elif provider == 'anthropic':
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print(f"❌ ANTHROPIC_API_KEY not set")
            print(f"Then run: export ANTHROPIC_API_KEY='your-key'")
            return False

    elif provider == 'ollama':
        # Check if ollama is installed
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, timeout=5)
            if result.returncode != 0:
                print(f"❌ Ollama not installed")
                print(f"Install with: brew install ollama")
                print(f"Then pull model: ollama pull llama3.2-vision")
                return False

            # Check if model is pulled
            if 'llama3.2-vision' not in result.stdout.decode():
                print(f"⚠️  Model not found. Pulling llama3.2-vision...")
                subprocess.run(['ollama', 'pull', 'llama3.2-vision'], timeout=300)

        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return False

    return True

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


def generate_sample_timestamps(duration, interval=2.0):
    """Generate timestamps at regular intervals"""
    timestamps = []
    t = 0.0
    while t < duration:
        timestamps.append(t)
        t += interval
    return timestamps


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


def extract_timeline_keyframes(video_path, timestamps, output_dir):
    """Extract keyframes at all sample timestamps"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Extracting {len(timestamps)} keyframes...")

    keyframes = []
    for i, ts in enumerate(timestamps):
        output_path = output_dir / f'frame_{i:04d}_{ts:.2f}s.jpg'

        if extract_keyframe(video_path, ts, output_path):
            keyframes.append({
                'path': output_path,
                'timestamp': ts,
                'index': i
            })

        if (i + 1) % 100 == 0:
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

    # Extract word-level timestamps from <c> tags
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


def get_words_at_time(word_timeline, timestamp, window=2.0):
    """Get words spoken around a timestamp (±window seconds)"""
    words = []
    for entry in word_timeline:
        if abs(entry['time'] - timestamp) <= window:
            words.append(entry['word'])

    return ' '.join(words) if words else '[no speech]'

# ============================================================================
# VISION API CLASSIFIERS
# ============================================================================

CLASSIFICATION_PROMPT = """Analyze this frame from a YouTube video.

Provide a JSON object with this EXACT structure (no other text):

{
  "footage_type": "3D_animation | real_footage | hybrid | graphics | text_overlay",
  "camera_angle": "aerial | close_up | medium | wide | POV | map_view | diagram | graph",
  "shot_type": "static | slow_pan | fast_pan | zoom_in | zoom_out | tracking | handheld",
  "camera_movement": "none | zooming_in | zooming_out | panning_left | panning_right | tracking | shaking",
  "content": "person | multiple_people | landscape | building | map | diagram | text | object | vehicle | crowd | abstract | document",
  "text_on_screen": "yes | no",
  "text_content": "<text if visible, otherwise empty string>",
  "mood": "dark | bright | neutral | dramatic | calm | tense | mysterious",
  "color_grading": "cool | warm | neutral | desaturated | high_contrast",
  "motion_level": "static | slow | medium | fast"
}

Return ONLY the JSON object, no other text."""


def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, 'rb') as f:
        return base64.standard_b64encode(f.read()).decode('utf-8')


def classify_with_gemini(image_path, model_id='gemini-2.0-flash-exp'):
    """Classify with Google Gemini"""
    import google.generativeai as genai

    api_key = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(model_id)

    # Load image
    from PIL import Image
    img = Image.open(image_path)

    # Generate
    response = model.generate_content([CLASSIFICATION_PROMPT, img])

    # Parse JSON
    text = response.text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {'error': 'Could not parse response'}


def classify_with_ollama(image_path, model_id='llama3.2-vision'):
    """Classify with Ollama (local)"""

    cmd = [
        'ollama', 'run', model_id,
        CLASSIFICATION_PROMPT
    ]

    # Ollama expects image path in message
    result = subprocess.run(
        cmd,
        input=f"{CLASSIFICATION_PROMPT}\n\nImage: {image_path}",
        capture_output=True,
        text=True,
        timeout=60
    )

    text = result.stdout.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {'error': 'Could not parse response'}


def classify_with_openai(image_path, model_id='gpt-4o-mini'):
    """Classify with OpenAI"""
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Encode image
    img_data = encode_image(image_path)

    response = client.chat.completions.create(
        model=model_id,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": CLASSIFICATION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
                }
            ]
        }],
        max_tokens=500
    )

    text = response.choices[0].message.content.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {'error': 'Could not parse response'}


def classify_with_claude(image_path, model_id='claude-3-5-sonnet-20241022'):
    """Classify with Anthropic Claude"""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    img_data = encode_image(image_path)

    response = client.messages.create(
        model=model_id,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": CLASSIFICATION_PROMPT},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_data
                    }
                }
            ]
        }]
    )

    text = response.content[0].text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {'error': 'Could not parse response'}


def classify_keyframe(keyframe, model_name):
    """Classify a single keyframe using specified model"""

    config = MODELS[model_name]
    provider = config['provider']
    model_id = config['model_id']

    try:
        if provider == 'google':
            result = classify_with_gemini(keyframe['path'], model_id)
        elif provider == 'ollama':
            result = classify_with_ollama(keyframe['path'], model_id)
        elif provider == 'openai':
            result = classify_with_openai(keyframe['path'], model_id)
        elif provider == 'anthropic':
            result = classify_with_claude(keyframe['path'], model_id)
        else:
            result = {'error': f'Unknown provider: {provider}'}

        result['timestamp'] = keyframe['timestamp']
        result['frame_index'] = keyframe['index']
        return result

    except Exception as e:
        return {
            'timestamp': keyframe['timestamp'],
            'frame_index': keyframe['index'],
            'error': str(e)
        }


def classify_all_keyframes(keyframes, model_name):
    """Classify all keyframes"""

    config = MODELS[model_name]
    cost = len(keyframes) * config['cost_per_image']

    print(f"  Classifying {len(keyframes)} frames with {config['description']}")
    print(f"  Estimated cost: ${cost:.2f}")

    classified = []

    for i, kf in enumerate(keyframes):
        result = classify_keyframe(kf, model_name)
        classified.append(result)

        if (i + 1) % 10 == 0:
            print(f"    {i + 1}/{len(keyframes)} frames classified")

        # Rate limiting for free tiers
        if model_name == 'gemini-flash':
            time.sleep(0.05)  # ~20 requests/sec = safe for free tier

    print(f"  ✓ Classification complete")
    return classified

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def analyze_video_timeline(video_id, base_dir='.', interval=2.0, model='gemini-flash'):
    """Complete timeline analysis"""

    fern_dir = Path(base_dir) / 'analysis' / 'fern'
    video_dir = fern_dir / video_id

    video_file = video_dir / 'video.mp4'
    vtt_file = video_dir / 'video.en.vtt'
    info_file = video_dir / 'video.info.json'

    if not video_file.exists():
        print(f"❌ Video not found: {video_file}")
        return None

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

    # Step 1: Generate timestamps
    print(f"Step 1: Generating timestamps (every {interval}s)...")
    timestamps = generate_sample_timestamps(duration, interval)
    print(f"  ✓ {len(timestamps)} sample points")

    # Step 2: Extract keyframes
    print(f"\nStep 2: Extracting keyframes...")
    keyframes_dir = video_dir / f'timeline_keyframes_{model}'
    keyframes = extract_timeline_keyframes(video_file, timestamps, keyframes_dir)

    # Step 3: Load words
    print(f"\nStep 3: Loading word timeline...")
    word_timeline = []
    if vtt_file.exists():
        word_timeline = parse_vtt_word_timeline(vtt_file)
        print(f"  ✓ {len(word_timeline)} words")

    # Step 4: Classify
    print(f"\nStep 4: AI classification...")
    classified = classify_all_keyframes(keyframes, model)

    # Step 5: Build timeline
    print(f"\nStep 5: Building timeline...")
    timeline = []

    for kf in keyframes:
        ts = kf['timestamp']
        classification = next((c for c in classified if c.get('timestamp') == ts), {})
        words = get_words_at_time(word_timeline, ts, window=interval/2)

        timeline.append({
            'timestamp': ts,
            'words_spoken': words,
            'visual': classification,
            'keyframe': str(kf['path'])
        })

    # Save
    output_file = video_dir / f'timeline_analysis_{model}.json'

    result = {
        'video_id': video_id,
        'title': title,
        'duration': duration,
        'interval': interval,
        'model': model,
        'sample_count': len(timeline),
        'timeline': timeline,
        'metadata': metadata
    }

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ Timeline saved to: {output_file}")

    # Sample
    print(f"\nSample:")
    for entry in timeline[:3]:
        print(f"  [{entry['timestamp']:.1f}s] {entry['words_spoken'][:40]}...")
        v = entry['visual']
        print(f"    {v.get('footage_type', '?')} | {v.get('camera_angle', '?')} | {v.get('content', '?')}")

    return result


def analyze_all_videos(base_dir='.', interval=2.0, model='gemini-flash'):
    """Analyze all videos"""

    fern_dir = Path(base_dir) / 'analysis' / 'fern'
    video_dirs = [d for d in fern_dir.iterdir() if d.is_dir() and (d / 'video.mp4').exists()]

    print(f"Found {len(video_dirs)} videos\n")

    results = []
    for i, video_dir in enumerate(video_dirs, 1):
        print(f"[{i}/{len(video_dirs)}] Analyzing {video_dir.name}...")
        result = analyze_video_timeline(video_dir.name, base_dir, interval, model)
        if result:
            results.append(result)

    # Aggregate
    print(f"\n{'='*60}")
    print("AGGREGATING PATTERNS")
    print(f"{'='*60}\n")

    all_footage_types = []
    all_camera_angles = []

    for result in results:
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
        'interval': interval,
        'videos_analyzed': len(results)
    }

    output_file = fern_dir / f'VISUAL_FORMULA_{model}.json'
    with open(output_file, 'w') as f:
        json.dump(formula, f, indent=2)

    print(f"✓ Formula saved to: {output_file}")

    # Summary
    print(f"\nFOOTAGE:")
    for ft, count in sorted(formula['footage_distribution'].items(), key=lambda x: -x[1]):
        pct = count / len(all_footage_types) * 100
        print(f"  {ft}: {pct:.1f}%")

    return formula


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Fern Timeline Analyzer - Multi-Model Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Models:
  gemini-flash      Google Gemini 2.0 Flash (FREE, 1500/day) ⭐ RECOMMENDED
  gemini-flash-paid Google Gemini 1.5 Flash ($0.001/image)
  ollama            Ollama llama3.2-vision (FREE, local on M1)
  gpt-4o-mini       OpenAI GPT-4o-mini ($0.0001/image)
  gpt-4o            OpenAI GPT-4o ($0.002/image)
  claude            Anthropic Claude Sonnet ($0.01/image)

Examples:
  # FREE option (recommended)
  export GOOGLE_API_KEY="your-key"
  python analyze_fern_visual_multimodel.py --all --model gemini-flash --interval 2

  # Local option (no API key needed)
  brew install ollama
  ollama pull llama3.2-vision
  python analyze_fern_visual_multimodel.py --all --model ollama --interval 2
"""
    )

    parser.add_argument('video_id', nargs='?', help='Video ID to analyze')
    parser.add_argument('--all', action='store_true', help='Analyze all videos')
    parser.add_argument('--interval', type=float, default=2.0, help='Sample interval (default: 2.0s)')
    parser.add_argument('--model', default='gemini-flash', choices=MODELS.keys(),
                       help='Model to use (default: gemini-flash)')
    parser.add_argument('--base-dir', default='.', help='Base directory')
    parser.add_argument('--list-models', action='store_true', help='List available models')

    args = parser.parse_args()

    if args.list_models:
        print("Available models:\n")
        for name, config in MODELS.items():
            print(f"  {name:20} {config['description']}")
            print(f"  {'':20} Cost: ${config['cost_per_image']}/image")
            if config['cost_per_image'] == 0:
                print(f"  {'':20} FREE ⭐")
            print()
        sys.exit(0)

    # Check model availability
    if not check_model_available(args.model):
        sys.exit(1)

    # Check dependencies
    try:
        if args.model.startswith('gemini'):
            import google.generativeai
        elif args.model.startswith('gpt'):
            import openai
        elif args.model == 'claude':
            import anthropic
        from PIL import Image
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print(f"\nInstall with:")
        if args.model.startswith('gemini'):
            print(f"  pip install google-generativeai pillow")
        elif args.model.startswith('gpt'):
            print(f"  pip install openai")
        elif args.model == 'claude':
            print(f"  pip install anthropic")
        sys.exit(1)

    # Run analysis
    if args.all:
        analyze_all_videos(args.base_dir, args.interval, args.model)
    elif args.video_id:
        analyze_video_timeline(args.video_id, args.base_dir, args.interval, args.model)
    else:
        parser.print_help()
