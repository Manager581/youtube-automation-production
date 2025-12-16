"""
Topic Generator for Space Facts YouTube Channel
Generates topic ideas and prompts for manual ChatGPT/Claude usage
"""

import json
import yaml
from datetime import datetime
from pathlib import Path


class TopicGenerator:
    """Generates video topic ideas for space facts channel"""

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.niche = self.config['channel']['niche']
        self.output_dir = Path("prompts/topics")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_chatgpt_prompt(self, num_topics=20):
        """Generate prompt for ChatGPT to create video topics"""

        prompt = f"""You are a YouTube content strategist specializing in viral space and astronomy content.

CONTEXT:
- Channel Niche: Space Facts & Astronomy (similar to WATOP, Bright Side, Kurzgesagt)
- Target Audience: General audience (13-45 years old), curious about space
- Video Style: Faceless educational, 20-minute format
- Goal: High engagement, watch time, and viral potential

TASK:
Generate {num_topics} unique video topic ideas that follow these criteria:

TOPIC REQUIREMENTS:
1. **Curiosity-driven**: Topics should trigger immediate "I need to know this" reaction
2. **Surprising**: Include unexpected facts, mysteries, or mind-blowing revelations
3. **Visual**: Must have strong visual potential (space footage, NASA imagery, AI-generated visuals)
4. **Timeless**: Not dependent on current events (evergreen content)
5. **Searchable**: Include natural keywords people search for
6. **Hook-worthy**: Can create a powerful 5-second hook

TOPIC CATEGORIES (mix across these):
- Mysterious Space Phenomena (black holes, dark matter, anomalies)
- Extreme Cosmic Events (supernovas, collisions, explosions)
- Mind-Bending Scale (size comparisons, distances, time scales)
- Future of Space (colonization, technology, exploration)
- Hidden Space Facts (lesser-known discoveries, secrets)
- Space Survival (what would happen if...)
- Cosmic Mysteries (unsolved questions, theories)

FORMAT YOUR RESPONSE AS:
For each topic, provide:
1. **Video Title** (must include hook/curiosity gap)
2. **Hook** (opening 5-second statement)
3. **Why It Works** (viral potential explanation)
4. **Key Segments** (5-8 main points to cover)
5. **Visual Style** (types of footage/visuals needed)

EXAMPLE:
---
Topic 1:
Title: "Scientists Just Discovered a Black Hole That Breaks Physics"
Hook: "There's a black hole in our universe that shouldn't exist—and it's rewriting everything we know about reality."
Why It Works: Mystery + authority (scientists) + stakes (breaks physics) + curiosity gap
Key Segments:
- What makes this black hole impossible
- How black holes normally work
- The discovery that changed everything
- What this means for our understanding of the universe
- Other impossible cosmic objects
- The future of physics
Visual Style: Dramatic black hole renders, NASA footage, scientific diagrams, scale comparisons

NOW GENERATE {num_topics} TOPICS:
"""

        # Save prompt to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"topic_prompt_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(prompt)

        print(f"✅ Topic generation prompt saved to: {filename}")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Copy the prompt from: {filename}")
        print(f"2. Paste it into ChatGPT or Claude")
        print(f"3. Save the response as: prompts/topics/topic_ideas_{timestamp}.txt")
        print(f"4. Run: python src/content/topic_generator.py parse")

        return str(filename)

    def parse_topics_from_response(self, response_file):
        """Parse topics from ChatGPT/Claude response"""

        with open(response_file, 'r') as f:
            content = f.read()

        # Save structured topics as JSON for later use
        topics_data = {
            "generated_date": datetime.now().isoformat(),
            "raw_content": content,
            "niche": self.niche,
            "status": "pending_selection"
        }

        output_file = self.output_dir / f"topics_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(topics_data, indent=2, fp=f)

        print(f"✅ Topics parsed and saved to: {output_file}")
        return output_file

    def get_competitor_analysis_prompt(self):
        """Generate prompt to analyze successful space channels"""

        prompt = """Analyze the top 10 most successful space facts YouTube channels.

For each channel, provide:
1. **Channel Name** & Subscriber Count
2. **Average Views per Video**
3. **Most Viewed Video Titles** (top 5)
4. **Title Formula** (patterns they use)
5. **Thumbnail Style** (colors, text, images)
6. **Upload Frequency**
7. **Content Gaps** (what they DON'T cover that we could)

Focus on channels like:
- Kurzgesagt
- Space Matters
- SEA (Space & Engineering Academy)
- Astrum
- Cool Worlds
- Launch Pad Astronomy

Then create a competitive strategy that:
1. Identifies underserved topics
2. Recommends title formulas that work
3. Suggests thumbnail approach
4. Recommends optimal upload schedule
"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"competitor_analysis_prompt_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(prompt)

        print(f"✅ Competitor analysis prompt saved to: {filename}")
        return str(filename)


def main():
    """CLI interface for topic generation"""
    import sys

    generator = TopicGenerator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "generate":
            num_topics = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            generator.generate_chatgpt_prompt(num_topics)

        elif command == "parse":
            if len(sys.argv) < 3:
                print("❌ Usage: python src/content/topic_generator.py parse <response_file>")
                return
            generator.parse_topics_from_response(sys.argv[2])

        elif command == "competitors":
            generator.get_competitor_analysis_prompt()

        else:
            print("❌ Unknown command. Use: generate, parse, or competitors")

    else:
        print("🎬 Space Facts Topic Generator")
        print("\nCommands:")
        print("  python src/content/topic_generator.py generate [num_topics]")
        print("  python src/content/topic_generator.py parse <response_file>")
        print("  python src/content/topic_generator.py competitors")
        print("\nExample:")
        print("  python src/content/topic_generator.py generate 20")


if __name__ == "__main__":
    main()
