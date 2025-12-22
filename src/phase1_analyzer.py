"""
Phase 1: Creator Analysis Pipeline
Analyzes faceless channels to extract exact formulas

Components:
- Video download (yt-dlp)
- Performance analysis (best vs worst)
- Frame extraction & cut detection
- Source detection (fingerprinting, reverse search)
- Audio-visual sync analysis
- Trend correlation (Google Trends, Reddit, etc.)
- Comment mining & sentiment analysis
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional
import re
from datetime import datetime, timedelta


class CreatorAnalyzer:
    """Analyzes creator videos to extract complete production formula"""

    def __init__(self, output_dir: str = "analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.videos_dir = self.output_dir / "videos"
        self.videos_dir.mkdir(exist_ok=True)

    def analyze_channel_from_url(self, channel_url: str, creator_name: str = "creator",
                                 months_back: int = 6, max_videos: int = 50):
        """
        Complete analysis pipeline - auto-fetch recent videos from channel

        Args:
            channel_url: YouTube channel URL or any video from the channel
            creator_name: Name for this creator (e.g., "watop")
            months_back: How many months back to analyze (default 6)
            max_videos: Maximum videos to analyze (default 50)
        """

        print(f"\n🔬 CREATOR ANALYSIS PIPELINE - {creator_name.upper()}")
        print("=" * 80)

        # Fetch recent videos from channel
        print(f"📥 Fetching last {months_back} months of videos...")
        video_urls = self._fetch_channel_videos(channel_url, months_back, max_videos)
        print(f"📹 Found {len(video_urls)} videos to analyze")

        return self._analyze_videos(video_urls, creator_name)

    def analyze_channel(self, video_urls_file: Path, creator_name: str = "creator"):
        """
        Complete analysis pipeline for a creator (from URL file)

        Args:
            video_urls_file: Path to file with video URLs (one per line)
            creator_name: Name for this creator (e.g., "watop")
        """

        print(f"\n🔬 CREATOR ANALYSIS PIPELINE - {creator_name.upper()}")
        print("=" * 80)

        # Load video URLs
        video_urls = self._load_video_urls(video_urls_file)
        print(f"📹 Found {len(video_urls)} videos to analyze")

        return self._analyze_videos(video_urls, creator_name)

    def _fetch_channel_videos(self, channel_url: str, months_back: int = 6,
                             max_videos: int = 50) -> List[str]:
        """
        Fetch recent videos from a channel using yt-dlp

        Args:
            channel_url: Channel URL or any video from channel
            months_back: How many months back to fetch
            max_videos: Maximum number of videos
        """

        # Calculate date filter
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)
        date_str = cutoff_date.strftime('%Y%m%d')

        try:
            # Use yt-dlp to get video URLs from channel
            cmd = [
                'yt-dlp',
                '--flat-playlist',
                '--print', 'url',
                '--playlist-end', str(max_videos),
                '--dateafter', date_str,
                channel_url
            ]

            print(f"   Fetching videos uploaded after {cutoff_date.strftime('%Y-%m-%d')}...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)

            urls = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

            print(f"   ✅ Found {len(urls)} videos from last {months_back} months")

            return urls

        except Exception as e:
            print(f"   ❌ Error fetching channel videos: {e}")
            print(f"   💡 Try providing a channel URL or video URL from the channel")
            return []

    def _analyze_videos(self, video_urls: List[str], creator_name: str) -> Dict:
        """Analyze a list of video URLs"""

        if not video_urls:
            print("❌ No videos to analyze!")
            return {'error': 'No videos found'}

        # Create creator output directory
        creator_dir = self.output_dir / creator_name
        creator_dir.mkdir(exist_ok=True)

        results = {
            'creator': creator_name,
            'analysis_date': datetime.now().isoformat(),
            'total_videos': len(video_urls),
            'videos': []
        }

        # Analyze each video
        for i, url in enumerate(video_urls, 1):
            print(f"\n{'='*80}")
            print(f"📹 VIDEO {i}/{len(video_urls)}: {url}")
            print(f"{'='*80}")

            try:
                video_data = self._analyze_video(url, creator_dir)
                results['videos'].append(video_data)

                # Save incremental results
                self._save_results(results, creator_dir / "analysis_results.json")

            except Exception as e:
                print(f"❌ Error analyzing {url}: {e}")
                results['videos'].append({
                    'url': url,
                    'error': str(e),
                    'status': 'failed'
                })

        # Phase 1B: Performance comparison
        print(f"\n{'='*80}")
        print("📊 PHASE 1B: PERFORMANCE COMPARISON")
        print(f"{'='*80}")
        performance_insights = self._compare_performance(results['videos'])
        results['performance_insights'] = performance_insights

        # Phase 1C: Trend correlation (will implement after basic analysis works)
        # Phase 1D: Comment mining (will implement after basic analysis works)

        # Save final results
        self._save_results(results, creator_dir / "complete_analysis.json")

        # Generate report
        self._generate_report(results, creator_dir / "REPORT.md")

        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"📁 Results saved to: {creator_dir}")
        print(f"📄 Report: {creator_dir / 'REPORT.md'}")

        return results

    def _load_video_urls(self, file_path: Path) -> List[str]:
        """Load video URLs from file, ignoring comments and blank lines"""
        urls = []
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
        return urls

    def _analyze_video(self, url: str, output_dir: Path) -> Dict:
        """Analyze a single video"""

        video_data = {
            'url': url,
            'status': 'analyzing'
        }

        # Step 1: Download video metadata (fast, no video download yet)
        print("\n📥 Step 1: Fetching metadata...")
        metadata = self._get_video_metadata(url)
        video_data.update(metadata)

        print(f"   Title: {metadata.get('title', 'N/A')}")
        print(f"   Duration: {metadata.get('duration', 'N/A')}s")
        print(f"   Views: {metadata.get('view_count', 'N/A'):,}")
        print(f"   Upload: {metadata.get('upload_date', 'N/A')}")

        # Step 2: Download video (for frame analysis)
        print("\n📥 Step 2: Downloading video...")
        video_path = self._download_video(url, output_dir)
        video_data['local_path'] = str(video_path)

        # Step 3: Extract frames and detect cuts
        print("\n🎞️  Step 3: Analyzing cuts and pacing...")
        cut_analysis = self._analyze_cuts(video_path)
        video_data['cut_analysis'] = cut_analysis

        print(f"   Total cuts: {cut_analysis['total_cuts']}")
        print(f"   Cuts per minute: {cut_analysis['cuts_per_minute']:.1f}")
        print(f"   Avg segment length: {cut_analysis['avg_segment_duration']:.2f}s")

        # Step 4: Download comments
        print("\n💬 Step 4: Downloading comments...")
        comments = self._download_comments(url)
        video_data['comment_count'] = len(comments)
        video_data['comments_sample'] = comments[:20]  # Save sample

        # Save full comments separately
        comments_file = output_dir / f"{metadata.get('id', 'unknown')}_comments.json"
        self._save_results(comments, comments_file)

        print(f"   Downloaded {len(comments)} comments")

        # Step 5: Thumbnail analysis
        print("\n🖼️  Step 5: Analyzing thumbnail...")
        thumbnail_analysis = self._analyze_thumbnail(metadata, output_dir)
        video_data['thumbnail_analysis'] = thumbnail_analysis

        # Step 6: Title analysis
        print("\n📰 Step 6: Analyzing title patterns...")
        title_analysis = self._analyze_title(metadata)
        video_data['title_analysis'] = title_analysis

        # Step 7: Audio transcription (if enabled)
        # Step 8: Visual classification (if enabled)
        # Step 9: Source detection (future)

        video_data['status'] = 'complete'
        return video_data

    def _get_video_metadata(self, url: str) -> Dict:
        """Get video metadata using yt-dlp"""
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-download',
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)

            # Extract key fields
            return {
                'id': metadata.get('id'),
                'title': metadata.get('title'),
                'description': metadata.get('description'),
                'duration': metadata.get('duration'),
                'view_count': metadata.get('view_count'),
                'like_count': metadata.get('like_count'),
                'comment_count': metadata.get('comment_count'),
                'upload_date': metadata.get('upload_date'),
                'uploader': metadata.get('uploader'),
                'channel': metadata.get('channel'),
                'channel_id': metadata.get('channel_id'),
                'thumbnail': metadata.get('thumbnail'),
            }

        except Exception as e:
            print(f"   ⚠️  Error getting metadata: {e}")
            return {'error': str(e)}

    def _download_video(self, url: str, output_dir: Path) -> Path:
        """Download video using yt-dlp"""

        output_template = str(output_dir / "%(id)s.%(ext)s")

        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '-o', output_template,
            url
        ]

        subprocess.run(cmd, check=True)

        # Find the downloaded file
        video_files = list(output_dir.glob("*.mp4"))
        if video_files:
            return video_files[-1]  # Return most recent
        else:
            raise Exception("Video download failed - no file found")

    def _analyze_cuts(self, video_path: Path) -> Dict:
        """
        Analyze video cuts using ffprobe scene detection
        """

        # Use ffprobe to detect scene changes
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'frame=pts_time,pict_type',
            '-of', 'json',
            '-f', 'lavfi',
            f'movie={video_path},select=gt(scene\\,0.3)'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # For now, use simpler method: count I-frames as approximation
            cmd_simple = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'frame=pict_type,pts_time',
                '-of', 'json',
                video_path
            ]

            result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=300)
            data = json.loads(result.stdout)

            # Get video duration
            cmd_duration = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            duration_result = subprocess.run(cmd_duration, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip())

            # Count I-frames (scene changes)
            frames = data.get('frames', [])
            i_frames = [f for f in frames if f.get('pict_type') == 'I']

            total_cuts = len(i_frames)
            cuts_per_minute = (total_cuts / duration) * 60 if duration > 0 else 0
            avg_segment_duration = duration / total_cuts if total_cuts > 0 else 0

            # Get cut timestamps
            cut_times = [float(f.get('pts_time', 0)) for f in i_frames if 'pts_time' in f]

            return {
                'total_cuts': total_cuts,
                'cuts_per_minute': cuts_per_minute,
                'avg_segment_duration': avg_segment_duration,
                'duration': duration,
                'cut_timestamps': cut_times[:50]  # Save first 50 for analysis
            }

        except Exception as e:
            print(f"   ⚠️  Error analyzing cuts: {e}")
            return {
                'error': str(e),
                'total_cuts': 0,
                'cuts_per_minute': 0,
                'avg_segment_duration': 0
            }

    def _download_comments(self, url: str) -> List[Dict]:
        """Download comments using yt-dlp"""

        try:
            cmd = [
                'yt-dlp',
                '--write-comments',
                '--skip-download',
                '--print', '%(comments)j',
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # yt-dlp outputs comments as JSON
            # Try to parse the output
            if result.stdout.strip():
                # Sometimes yt-dlp outputs multiple JSON objects, one per line
                comments = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            comment_data = json.loads(line)
                            if isinstance(comment_data, list):
                                comments.extend(comment_data)
                            else:
                                comments.append(comment_data)
                        except:
                            pass
                return comments

            return []

        except Exception as e:
            print(f"   ⚠️  Error downloading comments: {e}")
            return []

    def _analyze_thumbnail(self, metadata: Dict, output_dir: Path) -> Dict:
        """
        Download and analyze thumbnail
        - Download thumbnail image
        - Detect colors/palette
        - OCR any text
        - Detect faces/objects (basic)
        """

        try:
            import urllib.request
            from collections import Counter

            thumbnail_url = metadata.get('thumbnail')
            if not thumbnail_url:
                return {'error': 'No thumbnail URL'}

            # Download thumbnail
            thumbnail_path = output_dir / f"{metadata.get('id', 'unknown')}_thumbnail.jpg"
            urllib.request.urlretrieve(thumbnail_url, thumbnail_path)

            print(f"   Downloaded thumbnail: {thumbnail_path.name}")

            analysis = {
                'thumbnail_url': thumbnail_url,
                'local_path': str(thumbnail_path),
                'has_text': False,  # Will implement OCR
                'dominant_colors': [],  # Will implement color detection
            }

            # Try basic analysis with PIL if available
            try:
                from PIL import Image
                import colorsys

                img = Image.open(thumbnail_path)

                # Get dominant colors (simple approach - get most common colors)
                img_resized = img.resize((150, 150))  # Reduce size for performance
                pixels = list(img_resized.getdata())

                # Count colors
                color_counts = Counter(pixels)
                top_colors = color_counts.most_common(5)

                # Convert to hex
                dominant_colors = []
                for color, count in top_colors:
                    if isinstance(color, tuple) and len(color) >= 3:
                        hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                        dominant_colors.append({
                            'hex': hex_color,
                            'rgb': color[:3],
                            'frequency': count / len(pixels)
                        })

                analysis['dominant_colors'] = dominant_colors
                analysis['dimensions'] = {'width': img.width, 'height': img.height}

                print(f"   Dominant colors: {[c['hex'] for c in dominant_colors[:3]]}")

            except ImportError:
                print(f"   ⚠️  PIL not available - skipping color analysis")
            except Exception as e:
                print(f"   ⚠️  Color analysis failed: {e}")

            return analysis

        except Exception as e:
            print(f"   ⚠️  Thumbnail analysis failed: {e}")
            return {'error': str(e)}

    def _analyze_title(self, metadata: Dict) -> Dict:
        """
        Analyze title patterns for CTR optimization
        - Length/character count
        - Question marks (curiosity)
        - Numbers
        - Emotional trigger words
        - Capitalization patterns
        """

        title = metadata.get('title', '')

        if not title:
            return {'error': 'No title'}

        # Emotional trigger words (expanded list)
        trigger_words = {
            'shock': ['shocking', 'insane', 'crazy', 'unbelievable', 'incredible', 'terrifying'],
            'urgency': ['finally', 'now', 'urgent', 'breaking', 'just', 'immediately'],
            'curiosity': ['secret', 'hidden', 'revealed', 'truth', 'exposed', 'mystery'],
            'negative': ['worst', 'terrible', 'disaster', 'failure', 'mistake', 'warning'],
            'superlative': ['best', 'ultimate', 'greatest', 'perfect', 'amazing', 'top']
        }

        title_lower = title.lower()

        # Detect triggers
        detected_triggers = {}
        for category, words in trigger_words.items():
            found = [w for w in words if w in title_lower]
            if found:
                detected_triggers[category] = found

        # Detect numbers
        import re
        numbers = re.findall(r'\d+', title)

        # Detect questions
        has_question = '?' in title

        # Detect lists
        has_list_indicator = bool(re.search(r'\b\d+\s+(ways|reasons|things|facts|tips|secrets)', title_lower))

        # Capitalization patterns
        all_caps_words = [w for w in title.split() if w.isupper() and len(w) > 1]

        # Detect brackets/parentheses
        has_brackets = bool(re.search(r'[\[\(].*?[\]\)]', title))

        analysis = {
            'title': title,
            'length': len(title),
            'word_count': len(title.split()),
            'has_question': has_question,
            'has_numbers': len(numbers) > 0,
            'numbers': numbers,
            'emotional_triggers': detected_triggers,
            'trigger_count': sum(len(v) for v in detected_triggers.values()),
            'has_list_indicator': has_list_indicator,
            'all_caps_words': all_caps_words,
            'has_brackets': has_brackets,
            'starts_with_number': title[0].isdigit() if title else False,
        }

        print(f"   Length: {analysis['length']} chars, {analysis['word_count']} words")
        print(f"   Triggers: {analysis['trigger_count']} ({list(detected_triggers.keys())})")
        if numbers:
            print(f"   Numbers: {numbers}")
        if has_question:
            print(f"   Has question mark")

        return analysis

    def _compare_performance(self, videos: List[Dict]) -> Dict:
        """
        Compare best vs worst performing videos to find success patterns
        """

        print("\n   Analyzing performance patterns...")

        # Filter out failed videos
        valid_videos = [v for v in videos if v.get('status') == 'complete' and v.get('view_count')]

        if len(valid_videos) < 2:
            return {'error': 'Not enough videos for comparison'}

        # Sort by views
        sorted_by_views = sorted(valid_videos, key=lambda x: x.get('view_count', 0), reverse=True)

        # Top 30% vs bottom 30%
        top_count = max(1, len(sorted_by_views) // 3)
        top_performers = sorted_by_views[:top_count]
        bottom_performers = sorted_by_views[-top_count:]

        # Calculate averages
        def avg(videos, key):
            values = [v.get('cut_analysis', {}).get(key, 0) for v in videos if v.get('cut_analysis')]
            return sum(values) / len(values) if values else 0

        def title_avg(videos, key):
            values = [v.get('title_analysis', {}).get(key, 0) for v in videos if v.get('title_analysis')]
            return sum(values) / len(values) if values else 0

        def title_pattern_freq(videos, key):
            """Calculate frequency of a boolean pattern in titles"""
            count = sum(1 for v in videos if v.get('title_analysis', {}).get(key, False))
            return count / len(videos) if videos else 0

        insights = {
            'top_performers': {
                'count': len(top_performers),
                'avg_views': sum(v.get('view_count', 0) for v in top_performers) / len(top_performers),
                'avg_cuts_per_minute': avg(top_performers, 'cuts_per_minute'),
                'avg_segment_duration': avg(top_performers, 'avg_segment_duration'),
                'avg_duration': sum(v.get('duration', 0) for v in top_performers) / len(top_performers),
                # Title analysis
                'avg_title_length': title_avg(top_performers, 'length'),
                'avg_trigger_count': title_avg(top_performers, 'trigger_count'),
                'question_frequency': title_pattern_freq(top_performers, 'has_question'),
                'number_frequency': title_pattern_freq(top_performers, 'has_numbers'),
            },
            'bottom_performers': {
                'count': len(bottom_performers),
                'avg_views': sum(v.get('view_count', 0) for v in bottom_performers) / len(bottom_performers),
                'avg_cuts_per_minute': avg(bottom_performers, 'cuts_per_minute'),
                'avg_segment_duration': avg(bottom_performers, 'avg_segment_duration'),
                'avg_duration': sum(v.get('duration', 0) for v in bottom_performers) / len(bottom_performers),
                # Title analysis
                'avg_title_length': title_avg(bottom_performers, 'length'),
                'avg_trigger_count': title_avg(bottom_performers, 'trigger_count'),
                'question_frequency': title_pattern_freq(bottom_performers, 'has_question'),
                'number_frequency': title_pattern_freq(bottom_performers, 'has_numbers'),
            }
        }

        # Calculate differences
        insights['differential'] = {
            'cuts_per_minute_diff': insights['top_performers']['avg_cuts_per_minute'] - insights['bottom_performers']['avg_cuts_per_minute'],
            'segment_duration_diff': insights['top_performers']['avg_segment_duration'] - insights['bottom_performers']['avg_segment_duration'],
            'duration_diff': insights['top_performers']['avg_duration'] - insights['bottom_performers']['avg_duration'],
            'title_length_diff': insights['top_performers']['avg_title_length'] - insights['bottom_performers']['avg_title_length'],
            'trigger_count_diff': insights['top_performers']['avg_trigger_count'] - insights['bottom_performers']['avg_trigger_count'],
            'question_freq_diff': insights['top_performers']['question_frequency'] - insights['bottom_performers']['question_frequency'],
        }

        print(f"\n   📊 PACING:")
        print(f"      Top performers: {insights['top_performers']['avg_cuts_per_minute']:.1f} cuts/min")
        print(f"      Bottom performers: {insights['bottom_performers']['avg_cuts_per_minute']:.1f} cuts/min")
        print(f"      Difference: {insights['differential']['cuts_per_minute_diff']:+.1f} cuts/min")

        print(f"\n   📊 TITLES:")
        print(f"      Top: {insights['top_performers']['avg_title_length']:.0f} chars, {insights['top_performers']['avg_trigger_count']:.1f} triggers")
        print(f"      Bottom: {insights['bottom_performers']['avg_title_length']:.0f} chars, {insights['bottom_performers']['avg_trigger_count']:.1f} triggers")
        print(f"      Questions: {insights['top_performers']['question_frequency']:.0%} (top) vs {insights['bottom_performers']['question_frequency']:.0%} (bottom)")

        return insights

    def _save_results(self, data: Dict, file_path: Path):
        """Save results to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _generate_report(self, results: Dict, output_path: Path):
        """Generate human-readable markdown report"""

        report = f"""# Creator Analysis Report: {results['creator'].upper()}

**Analysis Date:** {results['analysis_date']}
**Videos Analyzed:** {results['total_videos']}

---

## Performance Insights

### Top Performers
- **Average Views:** {results.get('performance_insights', {}).get('top_performers', {}).get('avg_views', 0):,.0f}
- **Cuts Per Minute:** {results.get('performance_insights', {}).get('top_performers', {}).get('avg_cuts_per_minute', 0):.1f}
- **Avg Segment Duration:** {results.get('performance_insights', {}).get('top_performers', {}).get('avg_segment_duration', 0):.2f}s
- **Avg Video Duration:** {results.get('performance_insights', {}).get('top_performers', {}).get('avg_duration', 0):.0f}s

### Bottom Performers
- **Average Views:** {results.get('performance_insights', {}).get('bottom_performers', {}).get('avg_views', 0):,.0f}
- **Cuts Per Minute:** {results.get('performance_insights', {}).get('bottom_performers', {}).get('avg_cuts_per_minute', 0):.1f}
- **Avg Segment Duration:** {results.get('performance_insights', {}).get('bottom_performers', {}).get('avg_segment_duration', 0):.2f}s
- **Avg Video Duration:** {results.get('performance_insights', {}).get('bottom_performers', {}).get('avg_duration', 0):.0f}s

### Key Differences
- **Cuts Per Minute:** {results.get('performance_insights', {}).get('differential', {}).get('cuts_per_minute_diff', 0):+.1f}
- **Segment Duration:** {results.get('performance_insights', {}).get('differential', {}).get('segment_duration_diff', 0):+.2f}s
- **Video Duration:** {results.get('performance_insights', {}).get('differential', {}).get('duration_diff', 0):+.0f}s

---

## Individual Videos

"""

        for i, video in enumerate(results.get('videos', []), 1):
            if video.get('status') == 'complete':
                report += f"""
### {i}. {video.get('title', 'Unknown')}

- **Views:** {video.get('view_count', 0):,}
- **Duration:** {video.get('duration', 0)}s
- **Upload:** {video.get('upload_date', 'N/A')}
- **Cuts:** {video.get('cut_analysis', {}).get('total_cuts', 0)} ({video.get('cut_analysis', {}).get('cuts_per_minute', 0):.1f}/min)
- **Avg Segment:** {video.get('cut_analysis', {}).get('avg_segment_duration', 0):.2f}s
- **Comments:** {video.get('comment_count', 0)}

"""

        with open(output_path, 'w') as f:
            f.write(report)


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\n🔬 Phase 1: Creator Analysis Pipeline")
        print("\nUsage:")
        print("  Option 1 - Auto-fetch from channel:")
        print("    python src/phase1_analyzer.py --channel <channel_url> <creator_name> [months_back] [max_videos]")
        print("\n  Option 2 - From URL file:")
        print("    python src/phase1_analyzer.py <video_urls_file> <creator_name>")
        print("\nExamples:")
        print("  # Auto-fetch WATOP's last 6 months (up to 50 videos)")
        print("  python src/phase1_analyzer.py --channel https://youtube.com/@WATOP watop")
        print("")
        print("  # Auto-fetch last 12 months, max 100 videos")
        print("  python src/phase1_analyzer.py --channel https://youtube.com/@WATOP watop 12 100")
        print("")
        print("  # From file")
        print("  python src/phase1_analyzer.py research/watop_urls.txt watop")
        return

    analyzer = CreatorAnalyzer()

    # Check if using --channel mode
    if sys.argv[1] == '--channel':
        if len(sys.argv) < 4:
            print("❌ Usage: --channel <channel_url> <creator_name> [months_back] [max_videos]")
            return

        channel_url = sys.argv[2]
        creator_name = sys.argv[3]
        months_back = int(sys.argv[4]) if len(sys.argv) > 4 else 6
        max_videos = int(sys.argv[5]) if len(sys.argv) > 5 else 50

        print(f"📡 Auto-fetching from channel: {channel_url}")
        print(f"📅 Date range: Last {months_back} months")
        print(f"📊 Max videos: {max_videos}")

        results = analyzer.analyze_channel_from_url(channel_url, creator_name, months_back, max_videos)

    else:
        # File mode
        urls_file = Path(sys.argv[1])
        creator_name = sys.argv[2] if len(sys.argv) > 2 else "creator"

        if not urls_file.exists():
            print(f"❌ File not found: {urls_file}")
            return

        results = analyzer.analyze_channel(urls_file, creator_name)

    if results and 'error' not in results:
        print(f"\n✅ Analysis complete! Check analysis/{creator_name}/ for results")
    else:
        print(f"\n❌ Analysis failed")


if __name__ == "__main__":
    main()
