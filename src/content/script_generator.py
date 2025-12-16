"""
Script Generator for Space Facts Videos
Generates optimized prompts for ChatGPT/Claude to write WATOP-style scripts
"""

import yaml
import json
from datetime import datetime
from pathlib import Path


class ScriptGenerator:
    """Generates video scripts using WATOP engagement formula"""

    WATOP_STYLE_GUIDE = """
=== WATOP SCRIPT STYLE GUIDE ===

CORE PRINCIPLES:
1. **Curiosity-First**: Every sentence should make the viewer want to hear the next
2. **Pattern Interrupts**: Change pace/topic every 60-90 seconds
3. **Re-engagement Hooks**: Mini-cliffhangers throughout
4. **Conversational Tone**: Write like you're telling a friend an amazing story
5. **Pacing**: Fast-moving, no filler, constant forward momentum

SCRIPT STRUCTURE:

[0-5 seconds] THE HOOK
- Start with the MOST shocking/surprising fact
- Create immediate curiosity gap
- No introduction, no "welcome to my channel"
- Examples:
  ✅ "There's a star 5000 times larger than our sun—and it's about to explode."
  ✅ "Scientists just found something in space that shouldn't exist."
  ❌ "Today we're going to talk about interesting space facts."

[5-30 seconds] SETUP & STAKES
- Why this matters
- What's at stake
- Tease the payoff
- Example: "And when it does explode, the shockwave will be visible from Earth—in the middle of the day."

[30 seconds - 18 minutes] BODY
Structure as 8-12 segments, each with:
- **Mini Hook** (curiosity trigger)
- **Information Delivery** (2-3 key facts)
- **Transition/Cliffhanger** (keep them watching)

SEGMENT FORMULA:
1. Pose a question or mystery
2. Provide surprising answer
3. Add "but here's what's even crazier..."
4. Deliver next surprise
5. Transition with anticipation

[18-20 minutes] PAYOFF & RESOLUTION
- Answer the opening hook's promise
- One final mind-blowing revelation
- Strong CTA (like, subscribe, next video tease)

WRITING TECHNIQUES:

✅ Use These:
- "But here's where it gets crazy..."
- "What scientists discovered next shocked everyone..."
- "You're not going to believe this..."
- "But wait, it gets even weirder..."
- Numbers and scale comparisons (mind-blowing scale)
- "Imagine this..." (help visualize)
- Countdowns ("Here are the top 10...")
- Hypotheticals ("What would happen if...")

❌ Avoid These:
- Long introductions
- Academic language
- Filler phrases
- Slow build-ups
- Asking viewers to like/subscribe mid-video (save for end)
- Breaking the fourth wall too much

PACING RULES:
- Average sentence length: 12-15 words
- Paragraph length: 2-4 sentences max
- Re-engagement hook: Every 60-90 seconds
- Cut all unnecessary words
- Keep momentum constant

ENGAGEMENT TACTICS:
1. **Curiosity Loops**: Open a question, answer it 3 minutes later
2. **Escalation**: Each fact should be MORE impressive than the last
3. **Stakes**: Remind viewers why this matters
4. **Relatability**: Connect cosmic scale to everyday objects
5. **Mystery**: Emphasize what scientists DON'T know yet

VISUAL CUES (for editor):
Throughout script, add these tags:
- [SHOW: description of footage needed]
- [MUSIC: dramatic/tense/wonder]
- [SFX: explosion/whoosh/impact]
- [TEXT OVERLAY: "5,000x bigger than Sun"]

TARGET METRICS:
- Word Count: 5,000 words (~20 min at 250 wpm)
- Hook Success: Should make 90% want to keep watching
- Retention Hooks: 10-15 throughout video
- Watch Time Goal: 70%+ complete rate
"""

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path("prompts/scripts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_script_prompt(self, topic_title, topic_details=""):
        """Generate comprehensive script writing prompt"""

        word_count = self.config['script']['target_word_count']

        prompt = f"""You are an expert YouTube scriptwriter specializing in viral educational content.

Your task: Write a complete, production-ready script for a 20-minute video.

TOPIC: {topic_title}

{self.WATOP_STYLE_GUIDE}

SPECIFIC REQUIREMENTS FOR THIS SCRIPT:

1. TARGET LENGTH: {word_count} words (~20 minutes at 250 words/minute)

2. CONTENT STRUCTURE:
   - Opening Hook (0-5 sec): Most shocking fact from this topic
   - Setup (5-30 sec): Stakes and why it matters
   - Body (30s-18min): 10-12 segments covering:
     {topic_details if topic_details else "* Research and include the most mind-blowing, verified facts about this topic"}
   - Resolution (18-20min): Payoff and final revelation
   - CTA (last 30 sec): Like, subscribe, next video tease

3. RESEARCH DEPTH:
   - Use only verified, accurate scientific information
   - Include specific numbers, dates, discoveries
   - Cite interesting details (scientist names, mission names, dates)
   - Find lesser-known facts that will surprise even space enthusiasts

4. VISUAL PLANNING:
   Throughout the script, add these annotations:
   - [SHOW: specific footage description] - helps editor find right clips
   - [MUSIC: mood] - dramatic, tense, wonder, mysterious, triumphant
   - [SFX: effect type] - explosion, whoosh, impact, etc.
   - [TEXT: "text to display"] - for emphasis on screen

5. ENGAGEMENT OPTIMIZATION:
   - Include re-engagement hook every 60-90 seconds
   - Use curiosity loops (ask question, answer later)
   - Build escalation (each fact more impressive than last)
   - Include "wait, it gets crazier" moments
   - End segments with anticipation for next

6. TONE:
   - Conversational but authoritative
   - Excited but not over-the-top
   - Educational but entertaining
   - Make complex concepts accessible

7. FORMAT YOUR RESPONSE:

   **METADATA**
   Title: [Final optimized YouTube title]
   Hook: [The opening 5-second hook]
   Target Watch Time: 70%+

   **SCRIPT**
   [Write full script with timestamps, visual cues, and all annotations]

   **THUMBNAIL IDEAS**
   [3 thumbnail concepts with text overlay suggestions]

   **TITLE ALTERNATIVES**
   [5 alternative title options for A/B testing]

   **DESCRIPTION**
   [YouTube description with chapters]

   **TAGS**
   [20 optimized tags]

NOW WRITE THE COMPLETE SCRIPT:
"""

        # Save prompt
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in topic_title[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = self.output_dir / f"script_prompt_{safe_title}_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(prompt)

        print(f"✅ Script prompt saved to: {filename}")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Copy the prompt from: {filename}")
        print(f"2. Paste into ChatGPT-4 or Claude (use Claude for longer context)")
        print(f"3. Save the complete script as: scripts/drafts/{safe_title}_{timestamp}.md")
        print(f"4. Review and edit if needed")
        print(f"5. Run: python src/production/veo_generator.py <script_file>")

        return str(filename)

    def validate_script(self, script_file):
        """Validate script meets requirements"""

        with open(script_file, 'r') as f:
            content = f.read()

        word_count = len(content.split())
        target = self.config['script']['target_word_count']

        # Check for required elements
        checks = {
            "Word Count": (word_count, target * 0.9, target * 1.1),
            "Visual Cues [SHOW:]": content.count("[SHOW:"),
            "Music Cues [MUSIC:]": content.count("[MUSIC:"),
            "Hook Present": "hook" in content.lower()[:500],
            "CTA Present": any(x in content.lower()[-500:] for x in ["subscribe", "like", "next video"])
        }

        print(f"\n📊 SCRIPT VALIDATION REPORT")
        print(f"{'='*50}")
        print(f"Word Count: {word_count} (target: {target})")

        if checks["Word Count"][1] <= word_count <= checks["Word Count"][2]:
            print(f"✅ Word count in acceptable range")
        else:
            print(f"⚠️  Word count outside range ({checks['Word Count'][1]:.0f}-{checks['Word Count'][2]:.0f})")

        print(f"\nVisual Cues: {checks['Visual Cues [SHOW:]']} found")
        print(f"Music Cues: {checks['Music Cues [MUSIC:]']} found")
        print(f"Hook Present: {'✅' if checks['Hook Present'] else '❌'}")
        print(f"CTA Present: {'✅' if checks['CTA Present'] else '❌'}")

        # Save validation
        validation_data = {
            "script_file": str(script_file),
            "validated_at": datetime.now().isoformat(),
            "word_count": word_count,
            "checks": checks,
            "status": "approved" if all([
                checks["Word Count"][1] <= word_count <= checks["Word Count"][2],
                checks["Hook Present"],
                checks["CTA Present"]
            ]) else "needs_revision"
        }

        validation_file = Path(script_file).with_suffix('.validation.json')
        with open(validation_file, 'w') as f:
            json.dump(validation_data, indent=2, fp=f)

        return validation_data


def main():
    """CLI interface"""
    import sys

    generator = ScriptGenerator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "generate":
            if len(sys.argv) < 3:
                print("❌ Usage: python src/content/script_generator.py generate <topic_title>")
                return
            topic_title = sys.argv[2]
            topic_details = sys.argv[3] if len(sys.argv) > 3 else ""
            generator.generate_script_prompt(topic_title, topic_details)

        elif command == "validate":
            if len(sys.argv) < 3:
                print("❌ Usage: python src/content/script_generator.py validate <script_file>")
                return
            generator.validate_script(sys.argv[2])

        else:
            print("❌ Unknown command. Use: generate or validate")

    else:
        print("📝 Space Facts Script Generator")
        print("\nCommands:")
        print("  python src/content/script_generator.py generate '<topic_title>' '[topic_details]'")
        print("  python src/content/script_generator.py validate <script_file>")
        print("\nExample:")
        print('  python src/content/script_generator.py generate "Black Holes That Break Physics"')


if __name__ == "__main__":
    main()
