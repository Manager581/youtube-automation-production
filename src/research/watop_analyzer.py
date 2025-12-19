"""
WATOP Video Analyzer - Downloads and analyzes successful videos
Extracts title patterns, thumbnails, metadata to replicate success
"""

import json
import os
from pathlib import Path
import subprocess
import re
from datetime import datetime


class WATOPAnalyzer:
    """Analyzes successful videos to extract winning patterns"""

    def __init__(self):
        self.research_dir = Path("research/watop")
        self.research_dir.mkdir(parents=True, exist_ok=True)

    def download_metadata(self, video_urls):
        """Download metadata for multiple videos"""

        print("\n🔍 WATOP VIDEO ANALYZER")
        print("=" * 60)
        print(f"Analyzing {len(video_urls)} videos...\n")

        all_data = []

        for i, url in enumerate(video_urls, 1):
            print(f"[{i}/{len(video_urls)}] Fetching metadata from: {url}")

            try:
                # Download JSON metadata
                result = subprocess.run([
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    url
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    video_data = json.loads(result.stdout)

                    # Extract key data
                    metadata = {
                        'id': video_data.get('id'),
                        'title': video_data.get('title'),
                        'description': video_data.get('description', '')[:500],  # First 500 chars
                        'view_count': video_data.get('view_count', 0),
                        'like_count': video_data.get('like_count', 0),
                        'upload_date': video_data.get('upload_date'),
                        'duration': video_data.get('duration', 0),
                        'thumbnail': video_data.get('thumbnail'),
                        'tags': video_data.get('tags', []),
                        'url': url
                    }

                    all_data.append(metadata)

                    print(f"   ✅ Title: {metadata['title']}")
                    print(f"   👁️  Views: {metadata['view_count']:,}")
                    print(f"   ⏱️  Duration: {metadata['duration'] // 60}m {metadata['duration'] % 60}s")
                    print()

                    # Download thumbnail
                    self._download_thumbnail(metadata['id'], metadata['thumbnail'])

                else:
                    print(f"   ❌ Failed to fetch metadata")
                    print()

            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()

        # Save all metadata
        metadata_file = self.research_dir / "watop_videos.json"
        with open(metadata_file, 'w') as f:
            json.dump(all_data, f, indent=2)

        print(f"\n✅ Metadata saved to: {metadata_file}")

        return all_data

    def _download_thumbnail(self, video_id, thumbnail_url):
        """Download thumbnail for analysis"""
        if not thumbnail_url:
            return

        thumb_dir = self.research_dir / "thumbnails"
        thumb_dir.mkdir(exist_ok=True)

        thumb_path = thumb_dir / f"{video_id}.jpg"

        if thumb_path.exists():
            return

        try:
            subprocess.run([
                'curl', '-s', '-o', str(thumb_path), thumbnail_url
            ], timeout=10, check=True)
        except:
            pass

    def analyze_title_patterns(self, video_data):
        """Analyze title patterns to extract hooks and formulas"""

        print("\n📊 TITLE PATTERN ANALYSIS")
        print("=" * 60)

        titles = [v['title'] for v in video_data]

        # Pattern analysis
        patterns = {
            'questions': [],
            'numbers': [],
            'superlatives': [],
            'curiosity_gaps': [],
            'time_based': [],
            'location_based': []
        }

        # Superlatives to look for
        superlatives = ['most', 'biggest', 'largest', 'smallest', 'rarest', 'deadliest',
                       'strangest', 'weirdest', 'craziest', 'best', 'worst', 'ultimate']

        curiosity_words = ['never', 'nobody', 'secret', 'hidden', 'mystery', 'unknown',
                          'discovered', 'found', 'revealed', 'exposed']

        for title in titles:
            title_lower = title.lower()

            # Question format
            if '?' in title:
                patterns['questions'].append(title)

            # Contains numbers
            if re.search(r'\d+', title):
                patterns['numbers'].append(title)

            # Superlatives
            if any(word in title_lower for word in superlatives):
                patterns['superlatives'].append(title)

            # Curiosity gaps
            if any(word in title_lower for word in curiosity_words):
                patterns['curiosity_gaps'].append(title)

            # Time-based
            if re.search(r'\b(year|month|day|hour|minute|second|ago|until|before|after)\b', title_lower):
                patterns['time_based'].append(title)

            # Location-based
            if re.search(r'\b(in|at|from|near|under|inside|beneath|deep)\b', title_lower):
                patterns['location_based'].append(title)

        # Print results
        print(f"\n📝 TITLE FORMULAS FOUND:\n")

        for pattern_type, examples in patterns.items():
            if examples:
                percentage = (len(examples) / len(titles)) * 100
                print(f"{pattern_type.upper()}: {len(examples)}/{len(titles)} ({percentage:.0f}%)")
                for ex in examples[:3]:  # Show first 3 examples
                    print(f"  • {ex}")
                if len(examples) > 3:
                    print(f"  ... and {len(examples) - 3} more")
                print()

        # Find common words
        print("\n🔤 MOST COMMON WORDS IN TITLES:")
        all_words = ' '.join(titles).lower().split()
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'that', 'this', 'these', 'those', 'is', 'are'}
        filtered_words = [w.strip('.,!?') for w in all_words if w not in stop_words and len(w) > 3]

        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        for word, count in top_words:
            print(f"  {word}: {count}")

        return patterns

    def generate_space_topics(self, title_patterns, count=20):
        """Generate space topics using WATOP's proven patterns"""

        print(f"\n🚀 GENERATING {count} SPACE TOPICS USING WATOP PATTERNS")
        print("=" * 60)

        # Template structures based on WATOP analysis
        templates = [
            # Question format
            "What Would Happen If {space_event}?",
            "What If {space_phenomenon} Hit Earth?",
            "Why Does {space_object} Do This?",

            # Superlatives
            "The Most {adjective} {space_object} in the Universe",
            "The Strangest {space_phenomenon} Scientists Can't Explain",
            "The Deadliest {space_object} That Could End Everything",

            # Curiosity gaps
            "Nobody Knew About This {space_object} Until {time}",
            "The Secret Behind {space_phenomenon} Finally Revealed",
            "Scientists Just Discovered Something Terrifying About {space_object}",

            # Numbers
            "{number} {space_objects} That Could Destroy Earth",
            "{number} Things About {space_object} That Will Blow Your Mind",
            "This {space_object} Is {number} Times Bigger Than You Think",

            # Time-based
            "In {time} This {space_phenomenon} Will Change Everything",
            "What Happened When {space_event} Occurred {time} Ago",

            # Location-based
            "Deep Inside {space_object}: What Scientists Found",
            "Beneath the Surface of {space_object} Lies Something Impossible",
        ]

        # Space-specific fill-ins
        space_objects = ['Black Holes', 'Neutron Stars', 'Pulsars', 'Quasars', 'Supernovas',
                        'Jupiter', 'Saturn', 'Mars', 'The Sun', 'The Moon', 'Asteroids',
                        'Comets', 'Galaxies', 'Dark Matter', 'Exoplanets']

        space_phenomena = ['Solar Flares', 'Gamma Ray Bursts', 'Gravitational Waves',
                          'Time Dilation', 'Wormholes', 'Cosmic Radiation', 'Quantum Tunneling',
                          'Magnetars', 'Fast Radio Bursts']

        space_events = ['Two Black Holes Collided', 'A Star Goes Supernova', 'The Sun Died',
                       'We Entered a Black Hole', 'A Rogue Planet Hit Us']

        adjectives = ['Mysterious', 'Dangerous', 'Strange', 'Massive', 'Terrifying', 'Bizarre']

        numbers = ['7', '10', '13', '15', '20', '100']

        times = ['Million Years Ago', 'Billion Years', 'Tomorrow', 'Next Year', '2030',
                'Last Week', 'Yesterday']

        topics = []
        import random

        # Generate topics
        for i in range(count):
            template = random.choice(templates)

            topic = template.format(
                space_event=random.choice(space_events),
                space_phenomenon=random.choice(space_phenomena),
                space_object=random.choice(space_objects),
                space_objects=random.choice(space_objects),
                adjective=random.choice(adjectives),
                number=random.choice(numbers),
                time=random.choice(times)
            )

            topics.append(topic)

        # Print topics
        for i, topic in enumerate(topics, 1):
            print(f"{i:2d}. {topic}")

        # Save to file
        topics_file = self.research_dir / "generated_topics.txt"
        with open(topics_file, 'w') as f:
            for i, topic in enumerate(topics, 1):
                f.write(f"{i}. {topic}\n")

        print(f"\n✅ Topics saved to: {topics_file}")

        return topics


def main():
    """CLI interface"""
    import sys

    analyzer = WATOPAnalyzer()

    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        # Analyze existing data
        metadata_file = Path("research/watop/watop_videos.json")
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                video_data = json.load(f)

            patterns = analyzer.analyze_title_patterns(video_data)
            analyzer.generate_space_topics(patterns, count=20)
        else:
            print("❌ No metadata found. Run download first.")

    elif len(sys.argv) > 1 and sys.argv[1] == "download":
        # Download from URLs file
        urls_file = Path("research/watop_urls.txt")
        if urls_file.exists():
            with open(urls_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            video_data = analyzer.download_metadata(urls)
            patterns = analyzer.analyze_title_patterns(video_data)
            analyzer.generate_space_topics(patterns, count=20)
        else:
            print(f"❌ Create {urls_file} with one YouTube URL per line")

    else:
        print("\n🎬 WATOP Analyzer - Extract winning video patterns")
        print("=" * 60)
        print("\nUsage:")
        print("  1. Create research/watop_urls.txt with WATOP video URLs (one per line)")
        print("  2. Run: python src/research/watop_analyzer.py download")
        print("  3. Or analyze existing: python src/research/watop_analyzer.py analyze")
        print()


if __name__ == "__main__":
    main()
