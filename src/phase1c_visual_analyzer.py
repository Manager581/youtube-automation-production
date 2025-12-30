"""
Phase 1C: Visual-Script Sync Analysis
Analyzes visual content and maps it to script for creator formula extraction

Components:
- Scene detection (segment videos into visual clips)
- Visual classification (classify content type, motion, quality)
- Visual-script mapping (sync visuals to transcript words)
- Content sourcing patterns (identify where creators get footage)
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional
import re
from datetime import datetime
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class VisualAnalyzer:
    """Analyzes visual content and syncs with script"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

    def analyze_creator_visuals(self, creator_name: str, top_n: int = 10, skip_classification: bool = False, analyze_bottom: bool = False, use_openai: bool = False, max_keyframes: int = None):
        """
        Analyze visual-script sync for top N or bottom N videos of a creator

        Args:
            creator_name: Creator directory name (e.g., "watop")
            top_n: Number of videos to analyze (default 10)
            skip_classification: Skip Step 4 (visual classification) to save API quota
            analyze_bottom: If True, analyze bottom N videos instead of top N
            use_openai: Use OpenAI GPT-4o Vision instead of local MLX (costs ~$0.15/video)
            max_keyframes: Max keyframes to analyze per video (None = all keyframes)
        """

        creator_dir = self.analysis_dir / creator_name

        if not creator_dir.exists():
            print(f"❌ Creator directory not found: {creator_dir}")
            return

        # Load complete analysis
        analysis_file = creator_dir / "complete_analysis.json"
        if not analysis_file.exists():
            print(f"❌ Analysis file not found: {analysis_file}")
            return

        with open(analysis_file, 'r') as f:
            data = json.load(f)

        videos = data.get('videos', [])

        # Filter completed videos and sort by views
        valid_videos = [v for v in videos if v.get('status') == 'complete' and v.get('view_count')]
        sorted_videos = sorted(valid_videos, key=lambda x: x.get('view_count', 0), reverse=True)

        # Select top or bottom performers
        if analyze_bottom:
            selected_videos = sorted_videos[-top_n:] if len(sorted_videos) >= top_n else sorted_videos
            performance_label = "BOTTOM"
        else:
            selected_videos = sorted_videos[:top_n]
            performance_label = "TOP"

        print(f"\n🎬 PHASE 1C: VISUAL-SCRIPT SYNC ANALYSIS")
        print("=" * 80)
        print(f"Creator: {creator_name.upper()}")
        print(f"Analyzing {performance_label} {len(selected_videos)} videos by views\n")

        results = {
            'creator': creator_name,
            'analysis_date': datetime.now().isoformat(),
            'videos_analyzed': len(selected_videos),
            'performance_type': performance_label.lower(),
            'videos': []
        }

        for i, video in enumerate(selected_videos, 1):
            video_id = video.get('id', 'unknown')
            title = video.get('title', 'Unknown')
            views = video.get('view_count', 0)

            print(f"\n{'='*80}")
            print(f"🎥 VIDEO {i}/{len(selected_videos)}: {title}")
            print(f"   Views: {views:,} | ID: {video_id}")
            print(f"{'='*80}\n")

            # Find video file
            video_path = self._find_video_file(creator_dir, video_id)
            if not video_path:
                print(f"   ⚠️  Video file not found for {video_id}, skipping...")
                continue

            # Analyze visual segments
            visual_data = self._analyze_video_segments(video_path, video_id, creator_dir)

            if visual_data:
                # Map visuals to script (if transcript exists)
                transcript = video.get('transcript_analysis', {})
                if transcript and transcript.get('words'):
                    # Check if visual_script_map is cached
                    if 'visual_script_map' not in visual_data:
                        visual_script_map = self._map_visuals_to_script(
                            visual_data['segments'],
                            transcript['words']
                        )
                        visual_data['visual_script_map'] = visual_script_map

                        # Update cache with mapping
                        cache_file = creator_dir / f"{video_id}_segments" / "metadata.json"
                        with open(cache_file, 'w') as f:
                            json.dump(visual_data, f, indent=2)
                    else:
                        print("🔗 Step 3: Mapping visuals to script... (using cache)")
                        print(f"   ✅ Loaded {len(visual_data['visual_script_map'])} cached visual-script mappings")
                        visual_script_map = visual_data['visual_script_map']

                    # Classify visual content (unless skipped)
                    if not skip_classification and visual_data.get('keyframes'):
                        classifications = self._classify_keyframes(
                            visual_data['keyframes'],
                            visual_script_map,
                            use_openai=use_openai,
                            max_keyframes=max_keyframes
                        )
                        visual_data['visual_classifications'] = classifications
                    elif skip_classification:
                        print("\n⏭️  Skipping Step 4 (visual classification) to preserve API quota")

                results['videos'].append({
                    'id': video_id,
                    'title': title,
                    'views': views,
                    'visual_analysis': visual_data
                })

        # Save results
        filename = f"visual_analysis_{performance_label.lower()}.json"
        output_file = creator_dir / filename
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Visual analysis complete!")
        print(f"📁 Results saved to: {output_file}")

        return results

    def _find_video_file(self, creator_dir: Path, video_id: str) -> Optional[Path]:
        """Find video file by ID"""
        # Common video extensions
        for ext in ['.mp4', '.webm', '.mkv']:
            video_path = creator_dir / f"{video_id}{ext}"
            if video_path.exists():
                return video_path
        return None

    def _analyze_video_segments(self, video_path: Path, video_id: str, output_dir: Path) -> Dict:
        """
        Detect scenes and extract segments from video

        Uses ffmpeg scene detection to identify visual transitions
        """

        # Create segments directory
        segments_dir = output_dir / f"{video_id}_segments"
        segments_dir.mkdir(exist_ok=True)

        # Check for cached analysis
        cache_file = segments_dir / "metadata.json"
        if cache_file.exists():
            print("🎬 Step 1: Detecting scenes... (using cache)")
            print("📸 Step 2: Extracting keyframes... (using cache)")
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                print(f"   ✅ Loaded {cached_data['total_segments']} cached segments with {len(cached_data['keyframes'])} keyframes")
                return cached_data
            except Exception as e:
                print(f"   ⚠️  Cache corrupted, re-analyzing: {e}")

        print("🎬 Step 1: Detecting scenes...")

        try:
            # Use ffmpeg scene detection
            # Scene detection threshold: 0.3 (lower = more sensitive)
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-filter:v', 'select=\'gt(scene,0.3)\',showinfo',
                '-f', 'null',
                '-'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            # Parse scene timestamps from ffmpeg output
            scene_times = self._parse_scene_times(result.stderr)

            print(f"   ✅ Detected {len(scene_times)} scene changes")

            # Extract keyframes at scene boundaries
            keyframes = self._extract_keyframes(video_path, scene_times, segments_dir)

            # Build segment data
            segments = []
            for i in range(len(scene_times)):
                start_time = scene_times[i]
                end_time = scene_times[i + 1] if i + 1 < len(scene_times) else None

                segments.append({
                    'segment_id': i,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': (end_time - start_time) if end_time else None,
                    'keyframe_path': keyframes.get(i, None)
                })

            result_data = {
                'video_id': video_id,
                'total_segments': len(segments),
                'segments': segments,
                'keyframes': keyframes,  # Dict of segment_id -> keyframe_path
                'segments_dir': str(segments_dir)
            }

            # Save cache
            with open(cache_file, 'w') as f:
                json.dump(result_data, f, indent=2)

            return result_data

        except subprocess.TimeoutExpired:
            print(f"   ❌ Scene detection timed out")
            return None
        except Exception as e:
            print(f"   ❌ Error during scene detection: {e}")
            return None

    def _parse_scene_times(self, ffmpeg_output: str) -> List[float]:
        """Extract scene change timestamps from ffmpeg output"""

        scene_times = [0.0]  # Always start at 0

        # Look for "pts_time" in showinfo output
        pattern = r'pts_time:([\d.]+)'
        matches = re.findall(pattern, ffmpeg_output)

        for match in matches:
            time_val = float(match)
            if time_val > 0:
                scene_times.append(time_val)

        # Remove duplicates and sort
        scene_times = sorted(list(set(scene_times)))

        return scene_times

    def _extract_keyframes(self, video_path: Path, scene_times: List[float],
                          output_dir: Path) -> Dict[int, str]:
        """Extract keyframe images at scene boundaries"""

        print("📸 Step 2: Extracting keyframes...")

        keyframes = {}

        # Sample every Nth scene to avoid extracting too many
        sample_interval = max(1, len(scene_times) // 50)  # Max 50 keyframes

        for i, timestamp in enumerate(scene_times[::sample_interval]):
            keyframe_path = output_dir / f"keyframe_{i:04d}.jpg"

            try:
                cmd = [
                    'ffmpeg',
                    '-ss', str(timestamp),
                    '-i', str(video_path),
                    '-frames:v', '1',
                    '-q:v', '2',  # Quality
                    '-y',
                    str(keyframe_path)
                ]

                subprocess.run(cmd, capture_output=True, timeout=30, check=True)
                keyframes[i * sample_interval] = str(keyframe_path)

            except Exception as e:
                print(f"   ⚠️  Failed to extract keyframe at {timestamp}s: {e}")

        print(f"   ✅ Extracted {len(keyframes)} keyframes")

        return keyframes

    def _map_visuals_to_script(self, segments: List[Dict], words: List[Dict]) -> List[Dict]:
        """
        Map visual segments to transcript words

        Creates timeline showing which visuals play during which words
        """

        print("🔗 Step 3: Mapping visuals to script...")

        visual_script_map = []

        for segment in segments:
            start_time = segment['start_time']
            end_time = segment.get('end_time')
            if end_time is None:
                end_time = float('inf')

            # Find words that overlap with this visual segment
            segment_words = []
            for word in words:
                word_start = word.get('start', 0)
                word_end = word.get('end', 0)

                # Check if word overlaps with segment
                if word_start < end_time and word_end > start_time:
                    segment_words.append(word['word'])

            if segment_words:
                visual_script_map.append({
                    'segment_id': segment['segment_id'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': segment.get('duration'),
                    'words': ' '.join(segment_words),
                    'word_count': len(segment_words),
                    'keyframe': segment.get('keyframe_path')
                })

        print(f"   ✅ Mapped {len(visual_script_map)} visual segments to script")

        return visual_script_map

    def _classify_keyframes_openai(self, keyframes: Dict[int, str], segment_words_map: List[Dict], max_keyframes: int = None) -> List[Dict]:
        """
        Classify visual content using OpenAI GPT-4o Vision

        Cost: ~$0.15 per video (100 keyframes × $0.00150 per image)

        Args:
            keyframes: Dict mapping segment_id to keyframe path
            segment_words_map: Visual-script mapping with words for context
            max_keyframes: Max keyframes to analyze (None = all)

        Returns:
            List of classified segments with content type, subject, source
        """

        try:
            from openai import OpenAI
        except ImportError:
            print("   ❌ openai package not installed.")
            print("   ⚠️  Run: pip install openai")
            return []

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("   ❌ OPENAI_API_KEY not found in environment")
            print("   ⚠️  Add it to your .env file")
            return []

        client = OpenAI(api_key=api_key)

        print("\n🔍 Step 4: Classifying visual content with OpenAI GPT-4o Vision...")

        classifications = []
        words_by_segment = {s['segment_id']: s['words'] for s in segment_words_map}

        # Sample keyframes if max_keyframes specified
        keyframe_items = list(keyframes.items())
        if max_keyframes and len(keyframe_items) > max_keyframes:
            sample_interval = max(1, len(keyframe_items) // max_keyframes)
            sampled_keyframes = keyframe_items[::sample_interval]
            print(f"   📊 Analyzing {len(sampled_keyframes)} of {len(keyframe_items)} keyframes (~${len(sampled_keyframes) * 0.000425:.2f} cost)")
        else:
            sampled_keyframes = keyframe_items
            print(f"   📊 Analyzing all {len(sampled_keyframes)} keyframes (~${len(sampled_keyframes) * 0.000425:.2f} cost)")

        for i, (segment_id, keyframe_path) in enumerate(sampled_keyframes, 1):
            try:
                context_words = words_by_segment.get(segment_id, "")

                # Encode image to base64
                with open(keyframe_path, "rb") as img_file:
                    base64_image = base64.b64encode(img_file.read()).decode('utf-8')

                prompt = f"""Analyze this video frame and classify it. The narrator says: "{context_words}"

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "content_type": "news_clip|space_footage|cgi_animation|chart_graphic|text_overlay|person_talking|aerial_footage|documentary_footage|stock_footage|other",
  "subject": "brief description of what is shown (5-10 words)",
  "source_indicators": "watermarks, logos, or style clues visible",
  "motion_style": "static|slow_pan|zoom|fast_cut|transition",
  "quality": "professional|amateur|stock|ai_generated"
}}"""

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "low"  # Use low-detail mode for cost savings (~$2.50 vs $8.75)
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=300,
                    temperature=0.0
                )

                result_text = response.choices[0].message.content

                # Clean markdown if present
                if result_text.startswith('```json'):
                    result_text = result_text.split('\n', 1)[1].rsplit('\n```', 1)[0]
                elif result_text.startswith('```'):
                    result_text = result_text.split('\n', 1)[1].rsplit('\n```', 1)[0]

                classification = json.loads(result_text.strip())
                classification['segment_id'] = segment_id
                classification['keyframe'] = keyframe_path
                classification['script_context'] = context_words[:100]

                classifications.append(classification)

                print(f"   [{i}/{len(sampled_keyframes)}] Classified: {classification['content_type']} - {classification['subject']}")

            except Exception as e:
                print(f"   ⚠️  Failed to classify keyframe {segment_id}: {e}")
                continue

        print(f"   ✅ Classified {len(classifications)} visual segments")
        print(f"   💰 Total cost: ~${len(classifications) * 0.000425:.2f} (low-detail mode)")

        return classifications

    def _classify_keyframes(self, keyframes: Dict[int, str], segment_words_map: List[Dict], use_openai: bool = False, max_keyframes: int = None) -> List[Dict]:
        """
        Classify visual content using either OpenAI GPT-4o Vision or local Qwen2.5-VL

        Args:
            keyframes: Dict mapping segment_id to keyframe path
            segment_words_map: Visual-script mapping with words for context
            use_openai: Use OpenAI instead of local model
            max_keyframes: Max keyframes to analyze per video (None = all for OpenAI, 20 for local)

        Returns:
            List of classified segments with content type, subject, source
        """

        # Route to OpenAI if requested
        if use_openai:
            return self._classify_keyframes_openai(keyframes, segment_words_map, max_keyframes)

        try:
            from mlx_vlm import load, generate
            from mlx_vlm.prompt_utils import apply_chat_template
            from mlx_vlm.utils import load_config
        except ImportError:
            print("   ⚠️  mlx-vlm not installed.")
            print("   ⚠️  Run: pip install mlx-vlm")
            print("   ⚠️  Skipping visual classification...")
            return []

        print("\n🔍 Step 4: Classifying visual content with Qwen2.5-VL 7B (Local, FREE, Unlimited)...")
        print("   📦 Loading model (first run downloads ~7GB, then cached)...")

        try:
            # Load Qwen2.5-VL 7B (4-bit quantized) - Better than 2.0, safe memory usage
            model_path = "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"
            model, processor = load(model_path)
            config = load_config(model_path)
            print("   ✅ Model loaded successfully")
        except Exception as e:
            import traceback
            print(f"   ❌ Failed to load model: {e}")
            print("   Full traceback:")
            traceback.print_exc()
            print("   ⚠️  Skipping visual classification...")
            return []

        classifications = []

        # Create context map for segments
        words_by_segment = {s['segment_id']: s['words'] for s in segment_words_map}

        # Process keyframes (sample based on max_keyframes parameter)
        keyframe_items = list(keyframes.items())
        if max_keyframes is None:
            max_keyframes = 20  # Default for local inference to avoid long processing times

        if len(keyframe_items) > max_keyframes:
            sample_interval = max(1, len(keyframe_items) // max_keyframes)
            sampled_keyframes = keyframe_items[::sample_interval]
            print(f"   📊 Analyzing {len(sampled_keyframes)} of {len(keyframe_items)} keyframes")
        else:
            sampled_keyframes = keyframe_items
            print(f"   📊 Analyzing all {len(sampled_keyframes)} keyframes")

        for i, (segment_id, keyframe_path) in enumerate(sampled_keyframes, 1):
            try:
                # Get script context for this segment
                context_words = words_by_segment.get(segment_id, "")

                # Classification prompt with context
                prompt = f"""Analyze this video frame and classify it. The narrator says: "{context_words}"

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "content_type": "news_clip|space_footage|cgi_animation|chart_graphic|text_overlay|person_talking|aerial_footage|documentary_footage|stock_footage|other",
  "subject": "brief description of what is shown (5-10 words)",
  "source_indicators": "watermarks, logos, or style clues visible",
  "motion_style": "static|slow_pan|zoom|fast_cut|transition",
  "quality": "professional|amateur|stock|ai_generated"
}}"""

                # Format prompt using apply_chat_template (required for Qwen2-VL)
                formatted_prompt = apply_chat_template(
                    processor, config, prompt, num_images=1
                )

                # Generate classification using Qwen2-VL
                # Image must be passed as a list of paths
                # temp=0.0 for deterministic, consistent JSON formatting
                result = generate(
                    model,
                    processor,
                    formatted_prompt,
                    [keyframe_path],
                    verbose=False,
                    temp=0.0,
                    max_tokens=300
                )

                # Extract text from GenerationResult object
                result_text = result.text

                # Clean markdown formatting if present
                if result_text.startswith('```json'):
                    result_text = result_text.split('\n', 1)[1]
                    result_text = result_text.rsplit('\n```', 1)[0]
                elif result_text.startswith('```'):
                    result_text = result_text.split('\n', 1)[1]
                    result_text = result_text.rsplit('\n```', 1)[0]

                # Parse JSON response
                classification = json.loads(result_text.strip())

                classification['segment_id'] = segment_id
                classification['keyframe'] = keyframe_path
                classification['script_context'] = context_words[:100]

                classifications.append(classification)

                print(f"   [{i}/{len(sampled_keyframes)}] Classified: {classification['content_type']} - {classification['subject']}")

            except Exception as e:
                print(f"   ⚠️  Failed to classify keyframe {segment_id}: {e}")
                continue

        print(f"   ✅ Classified {len(classifications)} visual segments")

        return classifications


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\n🎬 Phase 1C: Visual-Script Sync Analysis")
        print("\nUsage:")
        print("  python src/phase1c_visual_analyzer.py <creator_name> [top_n] [flags]")
        print("\nFlags:")
        print("  --skip-classification  Skip visual classification (build cache only)")
        print("  --bottom              Analyze bottom performers instead of top")
        print("  --use-openai          Use OpenAI GPT-4o Vision (~$0.15/video, all keyframes)")
        print("  --max-keyframes N     Max keyframes per video (default: 20 local, all OpenAI)")
        print("\nExamples:")
        print("  python src/phase1c_visual_analyzer.py watop 10                    # Top 10, local MLX, 20 keyframes/video")
        print("  python src/phase1c_visual_analyzer.py watop 10 --use-openai       # Top 10, OpenAI, ALL keyframes (~$1.50 total)")
        print("  python src/phase1c_visual_analyzer.py watop 10 --use-openai --max-keyframes 50  # Limit to 50 keyframes/video")
        print("  python src/phase1c_visual_analyzer.py watop 10 --bottom           # Bottom 10 videos")
        return

    creator_name = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 10
    skip_classification = '--skip-classification' in sys.argv
    analyze_bottom = '--bottom' in sys.argv
    use_openai = '--use-openai' in sys.argv

    # Parse --max-keyframes
    max_keyframes = None
    for i, arg in enumerate(sys.argv):
        if arg == '--max-keyframes' and i + 1 < len(sys.argv):
            max_keyframes = int(sys.argv[i + 1])
            break

    analyzer = VisualAnalyzer()
    analyzer.analyze_creator_visuals(
        creator_name,
        top_n,
        skip_classification=skip_classification,
        analyze_bottom=analyze_bottom,
        use_openai=use_openai,
        max_keyframes=max_keyframes
    )


if __name__ == "__main__":
    main()
