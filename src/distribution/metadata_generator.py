"""
YouTube Metadata Generator
Generates optimized titles, descriptions, tags, and chapters for YouTube uploads
"""

import re
import yaml
import json
from pathlib import Path
from datetime import datetime


class MetadataGenerator:
    """Generates YouTube upload metadata"""

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path("output/metadata")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_metadata(self, title, script_file):
        """Generate complete YouTube metadata"""

        print(f"\n📊 GENERATING YOUTUBE METADATA")
        print(f"{'='*60}")

        # Load script
        with open(script_file, 'r') as f:
            script_content = f.read()

        # Generate title variations
        titles = self._generate_title_variations(title)

        # Generate description
        description = self._generate_description(title, script_content)

        # Generate tags
        tags = self._generate_tags(title, script_content)

        # Extract chapters from script
        chapters = self._extract_chapters(script_content)

        # Compile metadata
        metadata = {
            "primary_title": titles[0],
            "title_variations": titles,
            "description": description,
            "tags": tags,
            "chapters": chapters,
            "category_id": self.config['youtube']['category_id'],
            "privacy_status": self.config['youtube']['privacy_status'],
            "generated_at": datetime.now().isoformat()
        }

        # Save metadata
        safe_title = "".join(c for c in title[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
        output_file = self.output_dir / f"metadata_{safe_title}_{datetime.now().strftime('%Y%m%d')}.json"

        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create readable format
        readable_file = output_file.with_suffix('.txt')
        with open(readable_file, 'w') as f:
            f.write(f"YOUTUBE METADATA\n")
            f.write(f"{'='*80}\n\n")

            f.write(f"PRIMARY TITLE:\n{metadata['primary_title']}\n\n")

            f.write(f"TITLE VARIATIONS (for A/B testing):\n")
            for i, t in enumerate(metadata['title_variations'], 1):
                f.write(f"{i}. {t}\n")
            f.write(f"\n")

            f.write(f"DESCRIPTION:\n{'-'*80}\n")
            f.write(f"{metadata['description']}\n\n")

            f.write(f"CHAPTERS:\n{'-'*80}\n")
            for chapter in metadata['chapters']:
                f.write(f"{chapter['timestamp']} - {chapter['title']}\n")
            f.write(f"\n")

            f.write(f"TAGS ({len(metadata['tags'])}):\n{'-'*80}\n")
            f.write(f"{', '.join(metadata['tags'])}\n\n")

            f.write(f"SETTINGS:\n{'-'*80}\n")
            f.write(f"Category: Science & Technology (28)\n")
            f.write(f"Privacy: {metadata['privacy_status']}\n")

        print(f"✅ Metadata saved:")
        print(f"   JSON: {output_file}")
        print(f"   TXT:  {readable_file}")

        return output_file

    def _generate_title_variations(self, title):
        """Generate title variations for A/B testing"""

        variations = [title]

        # Add variations with different hooks
        if "?" not in title:
            variations.append(f"{title} (Explained)")

        # Add number if not present
        if not any(char.isdigit() for char in title):
            variations.append(f"10 Facts About {title}")

        # Add emotional triggers
        variations.append(f"{title} - You Won't Believe This")
        variations.append(f"Scientists Discovered {title}")

        return variations[:5]

    def _generate_description(self, title, script_content):
        """Generate YouTube description"""

        # Extract first 2-3 paragraphs from script as description
        paragraphs = [p.strip() for p in script_content.split('\n\n') if len(p.strip()) > 50]
        intro_text = '\n\n'.join(paragraphs[:2])[:400]

        description = f"""{title}

{intro_text}...

🚀 ABOUT THIS CHANNEL
We explore the most mind-blowing facts about space, astronomy, and the universe. From black holes to distant galaxies, we bring you the latest discoveries and mysteries of the cosmos.

📺 SUBSCRIBE for weekly space content!

🔔 Turn on notifications to never miss a video!

---

📚 SOURCES & CREDITS
- NASA Image and Video Library
- ESA/Hubble
- Scientific publications and research papers

---

#space #astronomy #science #nasa #universe #cosmos #spacefacts

---

© {datetime.now().year} All content is used with proper licensing and attribution.
For business inquiries: [your email]

DISCLAIMER: This video is for educational and entertainment purposes. All facts are researched and verified to the best of our ability."""

        return description

    def _generate_tags(self, title, script_content):
        """Generate optimized tags"""

        # Base tags from config
        tags = list(self.config['youtube']['default_tags'])

        # Extract key terms from title
        title_words = [w.lower() for w in title.split() if len(w) > 3]
        tags.extend(title_words[:5])

        # Space-related tags
        space_terms = [
            "space documentary", "astronomy facts", "universe explained",
            "space exploration", "cosmic phenomena", "astrophysics",
            "space mystery", "nasa discoveries", "space science",
            "educational video", "science facts", "space videos"
        ]

        tags.extend(space_terms[:8])

        # Remove duplicates, keep first 20
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)

        return unique_tags[:20]

    def _extract_chapters(self, script_content):
        """Extract chapter markers from script"""

        chapters = []

        # Look for timestamp patterns like [0:00] or [1:23]
        timestamp_pattern = r'\[(\d+:\d+)\]\s*([^\n]+)'
        matches = re.findall(timestamp_pattern, script_content)

        if matches:
            for timestamp, title in matches:
                chapters.append({
                    "timestamp": timestamp,
                    "title": title.strip()[:100]
                })
        else:
            # Generate default chapters
            chapters = [
                {"timestamp": "0:00", "title": "Introduction"},
                {"timestamp": "0:30", "title": "Main Content"},
                {"timestamp": "18:00", "title": "Conclusion"}
            ]

        return chapters


def main():
    """CLI interface"""
    import sys

    generator = MetadataGenerator()

    if len(sys.argv) < 3:
        print("📊 YouTube Metadata Generator")
        print("\nUsage:")
        print("  python src/distribution/metadata_generator.py '<title>' <script_file>")
        print("\nExample:")
        print('  python src/distribution/metadata_generator.py "Black Holes Explained" scripts/drafts/black_holes.md')
        return

    title = sys.argv[1]
    script_file = sys.argv[2]

    generator.generate_metadata(title, script_file)


if __name__ == "__main__":
    main()
