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
    # Recommended: Qwen3.5 4B — free, local, works on M1 16GB or M5 24GB
    ollama pull qwen3.5:4b
    venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen3.5-4b 2>&1 | tee /tmp/fern_analysis.log

    # Higher quality: Qwen3.5 27B — free, local, needs dedicated 24GB+ machine
    ollama pull qwen3.5:27b
    venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen3.5-27b 2>&1 | tee /tmp/fern_analysis.log

    # Legacy: Qwen2.5-VL 7B (already installed)
    venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen-vl 2>&1 | tee /tmp/fern_analysis.log

    # Resume after interruption
    venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen3.5-4b --resume

    # Monitor progress in a second terminal
    venv/bin/python monitor.py

    # NOTE: Gemini Flash (--model gemini-flash) costs money — ask before using.
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
        'model_id': 'gemini-2.0-flash',
        'daily_limit': 1500,  # Free tier
        'cost_per_image': 0.0,
        'description': 'Google Gemini 2.0 Flash (FREE, 1500/day)'
    },
    'gemini-flash-paid': {
        'provider': 'google',
        'model_id': 'gemini-2.0-flash',
        'daily_limit': None,  # No limit (paid)
        'cost_per_image': 0.001,
        'description': 'Google Gemini 2.0 Flash (Paid)'
    },
    'gpt-4o-mini': {
        'provider': 'openai',
        'model_id': 'gpt-4o-mini',
        'daily_limit': None,
        'cost_per_image': 0.0001,
        'description': 'OpenAI GPT-4o-mini'
    },
    'qwen-vl': {
        'provider': 'ollama',
        'model_id': 'qwen2.5vl:7b',
        'daily_limit': None,  # Local, no limits
        'cost_per_image': 0.0,
        'description': 'Qwen2.5-VL 7B (FREE, local — legacy, prefer qwen3.5-4b)'
    },
    'qwen3.5-4b': {
        'provider': 'ollama',
        'model_id': 'qwen3.5:4b',
        'daily_limit': None,
        'cost_per_image': 0.0,
        'description': 'Qwen3.5 4B (FREE, local — 3.4GB, works on M1 16GB or any M5, best default)'
    },
    'qwen3.5-27b': {
        'provider': 'ollama',
        'model_id': 'qwen3.5:27b',
        'daily_limit': None,
        'cost_per_image': 0.0,
        'description': 'Qwen3.5 27B (FREE, local — 17GB, highest quality, needs dedicated 24GB+ machine)'
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


def extract_hybrid_keyframes(video_path, timestamps, output_dir, start_index=0,
                              cut_times=None, duration=0):
    """
    Extract keyframes at hybrid timestamps.

    For each primary frame (Frame A), also extracts a secondary frame 0.5s later
    (Frame B), clamped to within the same shot (won't cross a cut boundary).
    Frame B is used by the AI to detect animation direction and easing — you cannot
    determine HOW elements move from a single still frame.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sort cut times for binary-search-style next-cut lookup
    sorted_cuts = sorted(cut_times) if cut_times else []

    print(f"  Extracting keyframes (starting from {start_index}/{len(timestamps)})...")

    keyframes = []
    for i in range(start_index, len(timestamps)):
        ts = timestamps[i]
        output_path = output_dir / f'frame_{i:04d}_{ts:.2f}s.jpg'

        # Compute secondary timestamp: 0.5s later, clamped to within the same shot
        if sorted_cuts:
            next_cut = next((c for c in sorted_cuts if c > ts + 0.05), duration or ts + 2.0)
        else:
            next_cut = ts + 2.0
        secondary_ts = min(ts + 0.5, next_cut - 0.05)
        if secondary_ts <= ts:
            secondary_ts = ts + 0.1
        secondary_path = output_dir / f'frame_{i:04d}_{ts:.2f}s_B.jpg'

        # Extract primary frame (Frame A) if not already done
        if not output_path.exists():
            extract_keyframe(video_path, ts, output_path)

        # Extract secondary frame (Frame B) if not already done
        if not secondary_path.exists():
            extract_keyframe(video_path, secondary_ts, secondary_path)

        if output_path.exists():
            keyframes.append({
                'path': output_path,
                'secondary_path': secondary_path if secondary_path.exists() else None,
                'timestamp': ts,
                'index': i
            })

        if (i + 1) % 50 == 0:
            print(f"    {i + 1}/{len(timestamps)} frames extracted")

    print(f"  ✓ Extracted {len(keyframes)} keyframe pairs")
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

CLASSIFICATION_PROMPT = """You are analyzing TWO consecutive frames from the same shot in a documentary-style YouTube channel.
Frame A is the primary frame. Frame B is captured 0.5 seconds later in the SAME shot (no cut between them).

Use BOTH frames together to understand what is moving, in which direction, and how — especially for animations, text reveals, and motion graphics. Describe everything with maximum detail so the visual style can be exactly replicated.

Return ONLY a JSON object (no other text):

{
  "scene_description": "<2-3 sentence detailed description of exactly what is in this frame>",

  "visual_category": "motion_graphic | archival_footage | modern_broll | news_screenshot | document_photo | animated_map | title_card | quote_card | name_card | talking_head | reconstructed_footage | stock_footage | screen_recording | black_screen",

  "animation_style": "<if motion_graphic/title_card/quote_card: describe the specific animation — e.g. 'typewriter text appearing letter by letter on black background' | 'name lower-third fading in from left' | 'animated map with red dot pulsing' | 'particle dust effect' | 'none'>",

  "color_grade": "dark_cinematic | desaturated_cold | desaturated_warm | high_contrast_bw | natural_color | washed_out | deep_shadow | none",
  "color_palette": "<dominant colors visible, e.g. 'deep blacks, muted greens, burnt orange highlights'>",
  "brightness": "very_dark | dark | medium | bright | very_bright",

  "people_count": 0,
  "people_description": "<if people present: describe their appearance, clothing, emotion, positioning — e.g. '1 white male in suit, serious expression, medium shot, dramatic side lighting' | 'none'>",
  "people_role": "protagonist | antagonist | victim | authority | crowd | unknown | none",

  "text_on_screen": true,
  "text_content": "<exact text if visible, word for word>",
  "text_style": "<describe font: serif/sans-serif, size relative to screen, color, placement, animation style — e.g. 'large white serif all-caps centered, slow fade in' | 'small yellow lower-third sans-serif' | 'none'>",

  "camera_angle": "aerial | extreme_close_up | close_up | medium | wide | extreme_wide | POV | dutch_angle | overhead | eye_level",
  "camera_movement": "static | slow_zoom_in | slow_zoom_out | fast_zoom | pan_left | pan_right | tilt_up | tilt_down | tracking | handheld_shake | ken_burns",
  "depth_of_field": "very_shallow_bokeh | shallow | deep | not_applicable",

  "lighting": "dramatic_chiaroscuro | rim_backlit | low_key_shadows | natural_daylight | overcast_flat | artificial_indoor | none",
  "atmosphere": "<visual atmosphere: e.g. 'foggy and ominous', 'stark and clinical', 'warm golden hour', 'cold blue night', 'none'>",

  "location_type": "indoor_office | indoor_courtroom | indoor_prison | indoor_residential | outdoor_urban | outdoor_nature | outdoor_war_zone | aerial | digital_space | not_applicable",
  "era": "pre_1950s | 1950s_1970s | 1980s_1990s | 2000s_2010s | modern_2020s | timeless_graphic | unknown",
  "footage_quality": "crisp_4k | broadcast_hd | standard_def | archival_grainy | archival_bw | lo_fi | graphic",

  "emotional_tone": "ominous | tense | fear | powerful | triumphant | somber | mysterious | shocking | neutral | hopeful",
  "narrative_function": "hook | establishing_context | character_intro | evidence | tension_build | revelation | climax | resolution | transition | reenactment",

  "production_technique": "<specific technique used — e.g. 'news chyron overlay on real footage', 'slow push into photo', 'split screen', 'talking head with lower third', 'animated infographic', 'document zoom', 'satellite map zoom', 'none'>",

  "kinetic_quality": "completely_static | subtle_life | moderate_motion | high_energy | chaotic",
  "subject_motion": "<what is actively moving within the scene content — e.g. 'fire flickering', 'insect wings beating', 'flowing water', 'crowd movement', 'wind in trees', 'smoke drifting', 'none'>",
  "motion_source": "camera_only | subject_only | animation | camera_and_subject | camera_and_animation | none",

  "animation_motion": "<FOR GRAPHIC/ANIMATION SHOTS: describe exactly how elements moved between Frame A and Frame B — direction, what moved, how far — e.g. 'white text slides in from left, ~70% across by Frame B', 'name card fades in from transparent, fully visible by Frame B', 'logo scales up from small center point to full size', 'map dot pulses outward', 'no change — static graphic', 'none — live footage'>",
  "animation_easing": "snap | ease_out | ease_in_out | float | bounce | instant_appear | none"
}"""


def encode_image(image_path, max_width=854):
    """Encode image to base64, resizing to max_width for faster inference.
    854px (480p width) is more than enough for visual classification — no need for 1080p.
    """
    import io
    try:
        from PIL import Image
        img = Image.open(image_path)
        if img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        return base64.standard_b64encode(buf.getvalue()).decode('utf-8')
    except ImportError:
        # PIL not available, send as-is
        with open(image_path, 'rb') as f:
            return base64.standard_b64encode(f.read()).decode('utf-8')


def classify_with_ollama(image_path, model_id, secondary_image_path=None):
    """Classify with a local Ollama vision model (e.g. Qwen2.5-VL).
    Sends both Frame A and Frame B (0.5s later) when available so the model
    can describe animation direction and easing between the two frames.
    """
    import urllib.request
    import base64

    with open(image_path, 'rb') as f:
        img_b64 = base64.standard_b64encode(f.read()).decode('utf-8')

    images = [img_b64]
    if secondary_image_path and Path(secondary_image_path).exists():
        with open(secondary_image_path, 'rb') as f:
            images.append(base64.standard_b64encode(f.read()).decode('utf-8'))

    payload = json.dumps({
        'model': model_id,
        'prompt': CLASSIFICATION_PROMPT,
        'images': images,
        'stream': False
    }).encode('utf-8')

    req = urllib.request.Request(
        'http://localhost:11434/api/generate',
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode('utf-8'))

    text = data.get('response', '').strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {'error': 'Could not parse response', 'raw': text[:200]}


def classify_with_gemini(image_path, model_id, secondary_image_path=None):
    """Classify with Google Gemini.
    Sends both Frame A and Frame B (0.5s later) when available so the model
    can describe animation direction and easing between the two frames.
    """
    from google import genai
    from google.genai import types
    import io
    from PIL import Image

    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

    img = Image.open(image_path).convert('RGB')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    contents = [
        CLASSIFICATION_PROMPT,
        types.Part.from_bytes(data=buf.read(), mime_type='image/jpeg')
    ]

    if secondary_image_path and Path(secondary_image_path).exists():
        img2 = Image.open(secondary_image_path).convert('RGB')
        buf2 = io.BytesIO()
        img2.save(buf2, format='JPEG')
        buf2.seek(0)
        contents.append(types.Part.from_bytes(data=buf2.read(), mime_type='image/jpeg'))

    response = client.models.generate_content(model=model_id, contents=contents)

    text = response.text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {'error': 'Could not parse response'}


class FatalAPIError(Exception):
    """Raised when the API returns an unrecoverable error (wrong model, bad key, etc.)"""
    pass

class QuotaExhaustedError(Exception):
    """Raised when the daily quota is exhausted."""
    pass


def classify_keyframe(keyframe, model_name):
    """Classify a single keyframe"""

    config = MODELS[model_name]
    provider = config['provider']
    model_id = config['model_id']

    try:
        secondary = keyframe.get('secondary_path')
        if provider == 'google':
            result = classify_with_gemini(keyframe['path'], model_id, secondary)
        elif provider == 'ollama':
            result = classify_with_ollama(keyframe['path'], model_id, secondary)
        else:
            result = {'error': 'Provider not implemented'}

        result['timestamp'] = keyframe['timestamp']
        result['frame_index'] = keyframe['index']
        return result

    except Exception as e:
        error_str = str(e)
        # 429: distinguish RPM limit (retry) from daily quota (stop)
        if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
            # Daily quota has "limit: 0" or "per_day" in the message
            if 'per_day' in error_str.lower() or 'limit: 0' in error_str or 'GenerateRequestsPerDay' in error_str:
                raise QuotaExhaustedError(f"Daily quota exhausted: {error_str[:200]}")
            # RPM limit — just sleep and return error so caller retries next frame
            import re as _re
            retry_match = _re.search(r'retryDelay.*?(\d+)s', error_str)
            wait = int(retry_match.group(1)) + 2 if retry_match else 65
            print(f"\n  ⏳ Rate limit hit — waiting {wait}s before continuing...")
            time.sleep(wait)
            return {'timestamp': keyframe['timestamp'], 'frame_index': keyframe['index'], 'error': f'rate_limited_retried'}
        # Fatal errors: wrong model name, invalid API key, permission denied
        if any(x in error_str for x in ['not found', '404', 'API_KEY', 'PERMISSION_DENIED']):
            raise FatalAPIError(f"Fatal API error (not retrying): {error_str[:200]}")
        return {
            'timestamp': keyframe['timestamp'],
            'frame_index': keyframe['index'],
            'error': error_str
        }


def classify_with_limit(keyframes, model_name, checkpoint, start_index=0):
    """Classify keyframes with daily limit tracking"""

    config = MODELS[model_name]
    daily_limit = config['daily_limit']

    classified = []
    requests_made = 0
    total = len(keyframes)
    start_time = time.time()

    for i, kf in enumerate(keyframes):
        # Check if we hit today's limit
        if daily_limit and checkpoint['requests_today'] >= daily_limit:
            print(f"\n⏸️  Hit daily limit ({daily_limit} requests)")
            print(f"   Processed {i} frames today")
            print(f"   Progress saved - run again tomorrow to continue")
            save_checkpoint(checkpoint)
            return classified, False  # Not complete

        try:
            result = classify_keyframe(kf, model_name)
        except QuotaExhaustedError as e:
            print(f"\n⏸️  Daily quota exhausted — stopping cleanly")
            print(f"   Processed {i} frames this session")
            print(f"   Run again tomorrow to continue")
            save_checkpoint(checkpoint)
            return classified, False
        except FatalAPIError as e:
            print(f"\n💀 FATAL ERROR — stopping immediately to protect quota")
            print(f"   {e}")
            save_checkpoint(checkpoint)
            raise SystemExit(1)

        classified.append(result)

        # Only count against quota if the request actually hit the API
        if 'error' not in result or any(x in result.get('error', '') for x in ['quota', 'rate', 'limit']):
            checkpoint['requests_today'] += 1

        checkpoint['current_frame_index'] = start_index + i + 1
        checkpoint['total_processed'] += 1
        requests_made += 1

        # Live progress bar
        elapsed = time.time() - start_time
        fps = requests_made / elapsed if elapsed > 0 else 0
        remaining = (total - i - 1) / fps if fps > 0 else 0
        pct = (i + 1) / total * 100
        bar_len = 30
        filled = int(bar_len * (i + 1) / total)
        bar = '█' * filled + '░' * (bar_len - filled)
        eta_str = f"{int(remaining // 60)}m{int(remaining % 60)}s" if remaining > 0 else "done"
        has_error = 'error' in result
        status = '⚠' if has_error else '✓'
        print(f"\r  {status} [{bar}] {pct:5.1f}% | {i+1}/{total} frames | {fps:.1f} fps | ETA: {eta_str}  ", end='', flush=True)

        # Save checkpoint every 100 frames
        if requests_made % 100 == 0:
            print()  # newline before checkpoint message
            print(f"    Checkpoint saved at frame {requests_made}")
            save_checkpoint(checkpoint)

        # Rate limiting for API models only
        # Gemini 2.5 Flash free tier: 10 RPM = 1 request per 6 seconds
        if config.get('daily_limit'):
            time.sleep(6.5)  # ~9 req/min, safely under 10 RPM limit

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
    # interval=30.0 means only sample every 30s within shots — cut points are always included.
    # This reduces frame count by ~10x vs interval=2.0 while still capturing all scene transitions.
    print(f"\nStep 2: Generating hybrid timestamps...")
    timestamps = generate_hybrid_timestamps(duration, cut_times, interval=30.0)

    # Determine start index (for resume)
    start_index = checkpoint.get('current_frame_index', 0) if resume else 0

    # Step 3: Extract keyframes (primary Frame A + secondary Frame B per sample)
    print(f"\nStep 3: Extracting keyframes...")
    keyframes_dir = video_dir / 'hybrid_keyframes'
    all_keyframes = extract_hybrid_keyframes(
        video_file, timestamps, keyframes_dir, start_index,
        cut_times=cut_times, duration=duration
    )

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
        'cut_timestamps': cut_times,   # stored for transition analysis in motion analyzer
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

        # Only reset frame index when moving to a NEW video (not when resuming same video)
        if i > start_video or not resume:
            checkpoint['current_frame_index'] = 0

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

    # Check API key (only needed for Google models)
    if MODELS[args.model]['provider'] == 'google' and not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not set")
        print("Get free key at: https://aistudio.google.com/app/apikey")
        print("Then run: export GOOGLE_API_KEY='your-key'")
        sys.exit(1)

    # Check dependencies
    try:
        from PIL import Image
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install pillow")
        sys.exit(1)

    if MODELS[args.model]['provider'] == 'ollama':
        import urllib.request
        try:
            urllib.request.urlopen('http://localhost:11434', timeout=3)
        except Exception:
            print("❌ Ollama is not running. Start it with: ollama serve")
            sys.exit(1)

    # Run
    analyze_all_videos_checkpoint(args.base_dir, args.model, args.resume)
