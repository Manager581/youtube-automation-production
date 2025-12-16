"""
Thumbnail Generator
Creates prompts for AI thumbnail generation (DALL-E, Midjourney, etc.)
"""

import json
import yaml
from pathlib import Path
from datetime import datetime


class ThumbnailGenerator:
    """Generates thumbnail prompts for manual AI generation"""

    WATOP_THUMBNAIL_STYLE = """
WATOP Thumbnail Style Guide:
- **High Contrast**: Dramatic lighting, vibrant colors
- **Bold Text**: Large, readable text overlay (yellow/white on dark background)
- **Single Focus**: One main subject (planet, black hole, galaxy)
- **Emotional**: Awe-inspiring, mysterious, dramatic
- **Professional**: Clean composition, not cluttered
- **Colors**: Deep blues, purples, oranges, yellows (space colors)
- **Text Position**: Usually top or bottom third
- **Font**: Bold, sans-serif, with slight glow/outline
"""

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path("prompts/thumbnails")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnail_prompts(self, title, script_file=None):
        """Generate thumbnail prompts for AI image generation"""

        print(f"\n🎨 GENERATING THUMBNAIL PROMPTS")
        print(f"{'='*60}")
        print(f"Video Title: {title}")

        # Extract key visual elements from title
        key_elements = self._extract_key_elements(title)

        prompts = []

        # Generate 3 variations
        templates = [
            {
                "name": "Dramatic Close-up",
                "style": "cinematic close-up of {subject}, dramatic lighting, deep space background, volumetric effects, 4K photorealistic, WATOP YouTube thumbnail style",
                "text_overlay": title[:40]
            },
            {
                "name": "Epic Wide Shot",
                "style": "epic wide angle shot of {subject}, cosmic scale, dramatic composition, vibrant space colors, professional space documentary thumbnail, high contrast",
                "text_overlay": title[:40]
            },
            {
                "name": "Mystery/Intrigue",
                "style": "{subject} with mysterious atmosphere, moody dramatic lighting, deep blacks and vibrant highlights, YouTube thumbnail style, cinematic",
                "text_overlay": title[:40]
            }
        ]

        for i, template in enumerate(templates):
            prompt_text = template['style'].format(subject=key_elements)

            prompts.append({
                "variant": i + 1,
                "name": template['name'],
                "dalle_prompt": prompt_text,
                "midjourney_prompt": prompt_text + " --ar 16:9 --v 6 --style raw",
                "text_overlay": template['text_overlay'],
                "text_style": "Bold white text with black outline and yellow glow",
                "dimensions": "1280x720",
                "notes": self.WATOP_THUMBNAIL_STYLE
            })

        # Save prompts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
        output_file = self.output_dir / f"thumbnail_{safe_title}_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump({
                "video_title": title,
                "generated_at": datetime.now().isoformat(),
                "prompts": prompts,
                "style_guide": self.WATOP_THUMBNAIL_STYLE
            }, f, indent=2)

        # Create readable file
        readable_file = self.output_dir / f"thumbnail_{safe_title}_{timestamp}.txt"
        with open(readable_file, 'w') as f:
            f.write(f"THUMBNAIL PROMPTS - {title}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"{self.WATOP_THUMBNAIL_STYLE}\n")
            f.write(f"{'='*80}\n\n")

            for prompt in prompts:
                f.write(f"VARIANT #{prompt['variant']}: {prompt['name']}\n")
                f.write(f"{'-'*80}\n\n")
                f.write(f"DALL-E PROMPT:\n{prompt['dalle_prompt']}\n\n")
                f.write(f"MIDJOURNEY PROMPT:\n{prompt['midjourney_prompt']}\n\n")
                f.write(f"TEXT OVERLAY:\n\"{prompt['text_overlay']}\"\n")
                f.write(f"Style: {prompt['text_style']}\n\n")
                f.write(f"{'='*80}\n\n")

        print(f"✅ Thumbnail prompts saved:")
        print(f"   TXT: {readable_file}")
        print(f"   JSON: {output_file}")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Open: {readable_file}")
        print(f"2. Choose DALL-E 3 or Midjourney")
        print(f"3. Generate 3 thumbnail variations")
        print(f"4. Add text overlay in Photoshop/Canva/Figma")
        print(f"5. Save as: output/thumbnails/{safe_title}_v1.jpg (v2, v3)")
        print(f"6. Test which performs best after upload")

        return output_file

    def _extract_key_elements(self, title):
        """Extract main subject from title"""

        # Common space subjects
        subjects = [
            "black hole", "nebula", "galaxy", "planet", "star", "supernova",
            "asteroid", "comet", "cosmic", "universe", "space", "nasa"
        ]

        title_lower = title.lower()

        for subject in subjects:
            if subject in title_lower:
                return subject

        # Fallback
        words = title.split()[:3]
        return " ".join(words)


def main():
    """CLI interface"""
    import sys

    generator = ThumbnailGenerator()

    if len(sys.argv) < 2:
        print("🎨 Thumbnail Generator")
        print("\nUsage:")
        print("  python src/distribution/thumbnail_generator.py '<video_title>' [script_file]")
        print("\nExample:")
        print('  python src/distribution/thumbnail_generator.py "Black Holes That Break Physics"')
        return

    title = sys.argv[1]
    script_file = sys.argv[2] if len(sys.argv) > 2 else None

    generator.generate_thumbnail_prompts(title, script_file)


if __name__ == "__main__":
    main()
