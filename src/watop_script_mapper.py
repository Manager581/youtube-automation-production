"""
WATOP Script-to-Visual Mapper
Analyzes script and creates visual timeline based on WATOP formula
"""

from pathlib import Path
import json
import re
from typing import List, Dict, Tuple


class WATOPScriptMapper:
    """Maps script text to visuals using WATOP's keyword-based formula"""

    # Visual keywords that trigger specific imagery
    VISUAL_KEYWORDS = {
        # Space objects (literal 10/10 match)
        'star': ['star close-up', 'stellar object', 'star field'],
        'betelgeuse': ['betelgeuse red supergiant', 'red star', 'orion constellation'],
        'supergiant': ['red supergiant star', 'massive star'],
        'supernova': ['supernova explosion', 'stellar explosion'],
        'explosion': ['explosion blast', 'explosive event'],
        'galaxy': ['galaxy spiral', 'galaxy cluster'],
        'planet': ['planet surface', 'exoplanet'],
        'nebula': ['nebula cloud', 'stellar nursery'],
        'black hole': ['black hole accretion', 'event horizon'],

        # NASA/Science (literal match)
        'nasa': ['nasa logo', 'nasa mission control', 'nasa spacecraft'],
        'telescope': ['telescope observatory', 'space telescope', 'hubble'],
        'scientist': ['scientists in lab', 'astronomers working'],
        'observatory': ['observatory dome', 'telescope facility'],
        'satellite': ['satellite orbit', 'space satellite'],

        # Abstract concepts (thematic 8/10 match)
        'energy': ['energy burst', 'power radiation'],
        'radiation': ['radiation waves', 'electromagnetic spectrum'],
        'gravity': ['gravitational waves', 'spacetime curvature'],
        'time': ['clock timelapse', 'cosmic timeline'],
        'distance': ['vast space distance', 'light years visualization'],

        # Scale comparisons (literal 10/10)
        'massive': ['size comparison', 'scale visualization'],
        'giant': ['giant object comparison'],
        'huge': ['huge scale reference'],
        'enormous': ['enormous size chart'],
    }

    def __init__(self):
        self.script_path = None
        self.timeline = []

    def analyze_script(self, script_text: str, audio_duration: float) -> List[Dict]:
        """
        Analyze script and create visual timeline

        Returns timeline with:
        - start_time
        - end_time
        - narration_text
        - visual_keywords
        - visual_type (literal/thematic)
        """

        print("\n📝 ANALYZING SCRIPT FOR WATOP VISUAL MAPPING")
        print("=" * 80)

        # Split into sentences (WATOP uses sentence-based cuts)
        sentences = self._split_into_sentences(script_text)

        # Calculate timing (average speaking pace: 150 words per minute)
        words_per_second = 150 / 60  # 2.5 words per second

        timeline = []
        current_time = 0.0

        for i, sentence in enumerate(sentences):
            # Calculate sentence duration
            word_count = len(sentence.split())
            sentence_duration = word_count / words_per_second

            # Extract visual keywords from sentence
            keywords = self._extract_visual_keywords(sentence)

            # Determine visual type
            visual_type = self._classify_visual(keywords)

            # Create timeline entry
            entry = {
                'index': i,
                'start_time': current_time,
                'end_time': current_time + sentence_duration,
                'duration': sentence_duration,
                'narration': sentence.strip(),
                'keywords': keywords,
                'visual_type': visual_type,
                'trigger_word': self._find_trigger_word(sentence, keywords)
            }

            timeline.append(entry)
            current_time += sentence_duration

            print(f"\n[{entry['start_time']:.1f}s - {entry['end_time']:.1f}s] ({entry['duration']:.1f}s)")
            print(f"   Text: \"{entry['narration'][:60]}...\"")
            print(f"   Keywords: {keywords}")
            print(f"   Trigger: '{entry['trigger_word']}'")

        # Normalize to actual audio duration
        timeline = self._normalize_timing(timeline, audio_duration)

        print(f"\n✅ Created {len(timeline)} visual segments")
        print("=" * 80)

        return timeline

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitter (can be improved)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_visual_keywords(self, sentence: str) -> List[str]:
        """Extract visual keywords from sentence using WATOP mapping"""
        sentence_lower = sentence.lower()
        found_keywords = []

        for keyword, search_terms in self.VISUAL_KEYWORDS.items():
            if keyword in sentence_lower:
                found_keywords.append(keyword)

        # If no specific keywords, use generic space imagery
        if not found_keywords:
            found_keywords = ['space', 'cosmos', 'universe']

        return found_keywords

    def _classify_visual(self, keywords: List[str]) -> str:
        """Classify visual type (literal vs thematic)"""
        literal_keywords = ['betelgeuse', 'star', 'nasa', 'telescope', 'galaxy',
                           'planet', 'supernova', 'scientist']

        for kw in keywords:
            if kw in literal_keywords:
                return 'literal_10/10'

        return 'thematic_8/10'

    def _find_trigger_word(self, sentence: str, keywords: List[str]) -> str:
        """
        Find the EXACT word where visual should change
        (WATOP changes AS the keyword starts)
        """
        sentence_lower = sentence.lower()

        # Find first keyword occurrence
        for keyword in keywords:
            if keyword in sentence_lower:
                # Find the position and extract the actual word
                match = re.search(r'\b' + keyword + r'\w*', sentence_lower)
                if match:
                    return sentence[match.start():match.end()]

        # Fallback to first keyword
        return keywords[0] if keywords else 'START'

    def _normalize_timing(self, timeline: List[Dict], actual_duration: float) -> List[Dict]:
        """Normalize timeline to match actual audio duration"""
        if not timeline:
            return timeline

        # Calculate scaling factor
        estimated_duration = timeline[-1]['end_time']
        scale_factor = actual_duration / estimated_duration

        # Scale all times
        for entry in timeline:
            entry['start_time'] *= scale_factor
            entry['end_time'] *= scale_factor
            entry['duration'] *= scale_factor

        return timeline

    def match_images_to_timeline(self, timeline: List[Dict],
                                 nasa_images_dir: Path) -> List[Dict]:
        """
        Match NASA images to timeline entries based on keywords
        """
        print("\n🖼️  MATCHING NASA IMAGES TO TIMELINE")
        print("=" * 80)

        # Get all NASA images
        nasa_dir = Path(nasa_images_dir)
        images = list(nasa_dir.glob("*.jpg")) + list(nasa_dir.glob("*.png"))

        if not images:
            print("❌ No NASA images found!")
            return timeline

        print(f"📸 Found {len(images)} NASA images")

        # Match images to timeline entries
        for entry in timeline:
            # Try to find best matching image based on keywords
            best_match = self._find_best_image_match(entry['keywords'], images)
            entry['image_path'] = str(best_match)
            entry['image_name'] = best_match.name

            print(f"   [{entry['start_time']:.1f}s] {entry['trigger_word']} → {best_match.name}")

        print("=" * 80)

        return timeline

    def _find_best_image_match(self, keywords: List[str], images: List[Path]) -> Path:
        """Find best matching image for keywords"""
        # Simple matching: look for keyword in filename
        for keyword in keywords:
            for img in images:
                if keyword.lower() in img.stem.lower():
                    return img

        # Fallback: random image (will improve with better matching)
        import random
        return random.choice(images)

    def save_timeline(self, timeline: List[Dict], output_path: Path):
        """Save timeline to JSON for video generation"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(timeline, f, indent=2)

        print(f"\n💾 Timeline saved: {output_path}")


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 3:
        print("\nUsage: python src/watop_script_mapper.py <script_file> <audio_file>")
        print("\nExample:")
        print("  python src/watop_script_mapper.py data/betelgeuse_script.txt assets/voiceovers/betelgeuse_intro.mp3")
        return

    script_file = Path(sys.argv[1])
    audio_file = Path(sys.argv[2])

    # Get audio duration using ffprobe
    import subprocess
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_file)],
        capture_output=True, text=True
    )
    audio_duration = float(result.stdout.strip())

    # Read script
    with open(script_file, 'r') as f:
        script_text = f.read()

    # Create mapper
    mapper = WATOPScriptMapper()

    # Analyze script
    timeline = mapper.analyze_script(script_text, audio_duration)

    # Match images
    timeline = mapper.match_images_to_timeline(timeline, Path("assets/nasa_footage"))

    # Save timeline
    output_file = Path(f"temp/{script_file.stem}_timeline.json")
    mapper.save_timeline(timeline, output_file)

    print(f"\n✅ WATOP timeline created!")
    print(f"   Input: {script_file}")
    print(f"   Audio: {audio_file} ({audio_duration:.1f}s)")
    print(f"   Timeline: {output_file}")
    print(f"   Segments: {len(timeline)}")


if __name__ == "__main__":
    main()
