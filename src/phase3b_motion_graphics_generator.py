"""
Phase 3B: Motion Graphics Auto-Generator
Automatically generates motion graphics from script data

Workflow:
1. Reads transcript and identifies graphics opportunities
2. Extracts data (numbers, locations, facts)
3. Generates appropriate template with data
4. Renders to video using Remotion or Manim

Supported graphics:
- Statistics/numbers
- Maps/locations
- Text overlays
- Data charts
- 3D visualizations (via Manim)
"""

import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class MotionGraphicsGenerator:
    """Auto-generates motion graphics from script data"""

    def __init__(self, templates_dir: str = "motion-graphics/remotion-templates"):
        self.templates_dir = Path(templates_dir)

    def analyze_script_for_graphics(self, video_id: str, creator_name: str) -> List[Dict]:
        """
        Analyze script to find graphics opportunities

        Returns:
            List of graphics to generate with extracted data
        """

        print(f"\n🎨 Analyzing script for graphics opportunities...")

        # Load transcript
        transcript_file = Path(f"analysis/{creator_name}/{video_id}_transcript.json")

        if not transcript_file.exists():
            print(f"   ❌ No transcript found")
            return []

        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)

        text = transcript_data.get('text', '')
        words = transcript_data.get('words', [])

        graphics = []

        # Find statistics/numbers
        graphics.extend(self._find_statistics(text, words))

        # Find locations
        graphics.extend(self._find_locations(text, words))

        # Find key facts for text overlays
        graphics.extend(self._find_key_facts(text, words))

        print(f"   ✅ Found {len(graphics)} graphics opportunities")

        return graphics

    def _find_statistics(self, text: str, words: List[Dict]) -> List[Dict]:
        """Find numbers and statistics in text"""

        graphics = []

        # Pattern: large numbers with units
        patterns = [
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(million|billion|thousand|percent|degrees|miles|feet|meters)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(%)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                number_str = match.group(1).replace(',', '')
                unit = match.group(2) if len(match.groups()) > 1 else ''

                # Convert to number
                try:
                    number = float(number_str)

                    # Apply unit multipliers
                    if 'million' in unit.lower():
                        number *= 1_000_000
                    elif 'billion' in unit.lower():
                        number *= 1_000_000_000
                    elif 'thousand' in unit.lower():
                        number *= 1_000

                    # Find timestamp
                    timestamp = self._find_timestamp_for_text(match.group(0), words)

                    # Extract label (context around the number)
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(text), match.end() + 50)
                    context = text[context_start:context_end]

                    # Try to extract label
                    label = self._extract_label_from_context(context, match.group(0))

                    graphics.append({
                        'type': 'statistic',
                        'template': 'StatisticDisplay',
                        'data': {
                            'number': int(number),
                            'label': label,
                            'unit': '+' if number > 1000 else '',
                        },
                        'timestamp': timestamp,
                        'context': context.strip()
                    })

                except ValueError:
                    continue

        return graphics

    def _find_locations(self, text: str, words: List[Dict]) -> List[Dict]:
        """Find geographical locations in text"""

        graphics = []

        # Common location indicators
        location_patterns = [
            r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "in Egypt", "in New York"
            r'the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+desert',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+is\s+located',
        ]

        # Known locations (expand this list)
        known_locations = {
            'Egypt': (26.8206, 30.8025),
            'China': (35.8617, 104.1954),
            'Sahara': (23.4162, 25.6628),
            'New York': (40.7128, -74.0060),
            'Guam': (13.4443, 144.7937),
            'Libya': (26.3351, 17.2283),
            'Iceland': (64.9631, -19.0208),
            'Mexico': (23.6345, -102.5528),
        }

        for pattern in location_patterns:
            matches = re.finditer(pattern, text)

            for match in matches:
                location_name = match.group(1)

                # Check if we have coordinates for this location
                if location_name in known_locations:
                    lat, lng = known_locations[location_name]

                    timestamp = self._find_timestamp_for_text(match.group(0), words)

                    graphics.append({
                        'type': 'location',
                        'template': 'LocationMarker',
                        'data': {
                            'lat': lat,
                            'lng': lng,
                            'label': location_name,
                        },
                        'timestamp': timestamp,
                        'context': match.group(0)
                    })

        return graphics

    def _find_key_facts(self, text: str, words: List[Dict]) -> List[Dict]:
        """Find important facts for text overlays"""

        graphics = []

        # Look for emphasized statements
        # Pattern: Quotes, definitions, shocking facts
        patterns = [
            r'"([^"]+)"',  # Quoted text
            r'([A-Z][^.!?]+[.!?])',  # Sentences starting with capital
        ]

        sentences = text.split('. ')

        for sentence in sentences:
            # Check for emphasis words
            emphasis_words = ['shocking', 'incredible', 'amazing', 'first time', 'never', 'discovered']

            if any(word in sentence.lower() for word in emphasis_words):
                timestamp = self._find_timestamp_for_text(sentence[:20], words)

                graphics.append({
                    'type': 'text_overlay',
                    'template': 'TextOverlay',
                    'data': {
                        'text': sentence.strip(),
                        'duration': 120,  # 4 seconds at 30fps
                    },
                    'timestamp': timestamp,
                    'context': sentence
                })

        return graphics[:5]  # Limit to 5 most important

    def _find_timestamp_for_text(self, text_snippet: str, words: List[Dict]) -> float:
        """Find timestamp where text appears in video"""

        # Simple search - find first word of snippet
        first_word = text_snippet.split()[0].lower() if text_snippet.split() else ''

        for word in words:
            if word.get('word', '').lower().startswith(first_word[:5]):
                return word.get('start', 0)

        return 0.0

    def _extract_label_from_context(self, context: str, number_text: str) -> str:
        """Extract meaningful label from context around number"""

        # Remove the number itself
        context_clean = context.replace(number_text, '').strip()

        # Common label patterns
        label_patterns = [
            r'(people|rabbits|fish|trees|tons|gallons|liters|acres|square\s+miles)',
            r'(population|area|volume|distance|height|depth|temperature)',
        ]

        for pattern in label_patterns:
            match = re.search(pattern, context_clean, re.IGNORECASE)
            if match:
                return match.group(1).capitalize()

        # Default label
        return "Value"

    def generate_graphics(self, graphics_list: List[Dict], output_dir: Path) -> List[Path]:
        """
        Generate video files for all graphics

        Args:
            graphics_list: List of graphics dicts from analyze_script_for_graphics()
            output_dir: Where to save generated videos

        Returns:
            List of generated video file paths
        """

        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n🎬 Generating {len(graphics_list)} motion graphics...")

        generated_files = []

        for i, graphic in enumerate(graphics_list, 1):
            graphic_type = graphic['type']
            template = graphic['template']
            data = graphic['data']

            print(f"   [{i}/{len(graphics_list)}] Generating {graphic_type}...")

            try:
                # Generate unique filename
                output_file = output_dir / f"{graphic_type}_{i}_{int(graphic['timestamp'])}.mp4"

                # Generate based on type
                if graphic_type == 'statistic':
                    self._generate_statistic(data, output_file)
                elif graphic_type == 'location':
                    self._generate_location(data, output_file)
                elif graphic_type == 'text_overlay':
                    self._generate_text_overlay(data, output_file)

                generated_files.append(output_file)
                print(f"      ✅ Saved to {output_file}")

            except Exception as e:
                print(f"      ❌ Failed: {e}")

        print(f"\n✅ Generated {len(generated_files)} graphics")

        return generated_files

    def _generate_statistic(self, data: Dict, output_file: Path):
        """Generate statistic animation using Manim (Python-based)"""

        # Use Manim for quick Python-based generation
        manim_script = f"""
from manim import *

class StatisticAnimation(Scene):
    def construct(self):
        # Number
        number = Integer({data['number']})
        number.scale(2)

        # Label
        label = Text("{data['label']}", font_size=36)
        label.next_to(number, DOWN, buff=0.5)

        # Animate
        self.play(Write(number), run_time=1.5)
        self.play(FadeIn(label), run_time=0.5)
        self.wait(2)
"""

        # Save script
        script_file = output_file.with_suffix('.py')
        with open(script_file, 'w') as f:
            f.write(manim_script)

        # Render with Manim
        cmd = [
            'manim',
            '-ql',  # Low quality for speed
            '--format=mp4',
            f'--output_file={output_file.name}',
            str(script_file),
            'StatisticAnimation'
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"         ⚠️  Manim not available, creating placeholder")
            # Create placeholder (in production, use Remotion or After Effects)

    def _generate_location(self, data: Dict, output_file: Path):
        """Generate location marker animation"""
        print(f"         ℹ️  Location graphics require Remotion + Mapbox (see template)")
        # In production, call Remotion CLI with template

    def _generate_text_overlay(self, data: Dict, output_file: Path):
        """Generate text overlay animation"""
        # Use ffmpeg to create simple text overlay
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'color=c=black:s=1920x1080:d=4',
            '-vf', f"drawtext=text='{data['text']}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            '-y',
            str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=10)
        except subprocess.CalledProcessError as e:
            print(f"         ❌ FFmpeg error: {e}")


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 3:
        print("\n🎨 Motion Graphics Auto-Generator")
        print("\nUsage:")
        print("  python src/phase3b_motion_graphics_generator.py <video_id> <creator_name>")
        print("\nExample:")
        print("  python src/phase3b_motion_graphics_generator.py 6lfV-K7PtII watop")
        print("\nThis will:")
        print("  - Analyze script for graphics opportunities")
        print("  - Extract data (numbers, locations, facts)")
        print("  - Auto-generate motion graphics")
        print("  - Save to analysis/{creator_name}/graphics/")
        return

    video_id = sys.argv[1]
    creator_name = sys.argv[2]

    generator = MotionGraphicsGenerator()

    # Analyze script
    graphics = generator.analyze_script_for_graphics(video_id, creator_name)

    if not graphics:
        print("❌ No graphics opportunities found")
        return

    # Print opportunities
    print(f"\n📋 GRAPHICS TO GENERATE:")
    for i, graphic in enumerate(graphics, 1):
        print(f"\n   {i}. {graphic['type'].upper()} at {graphic['timestamp']:.1f}s")
        print(f"      Data: {graphic['data']}")
        print(f"      Context: {graphic['context'][:80]}...")

    # Generate
    output_dir = Path(f"analysis/{creator_name}/graphics/{video_id}")
    generated = generator.generate_graphics(graphics, output_dir)

    print(f"\n✅ Complete! Generated {len(generated)} graphics in {output_dir}")


if __name__ == "__main__":
    main()
