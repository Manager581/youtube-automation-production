"""
Script Prompt Generator for AI (ChatGPT/Claude)
Creates detailed prompts for generating WATOP-style documentary scripts
"""

from pathlib import Path
from datetime import datetime


class ScriptPromptGenerator:
    """Generates AI prompts for script creation"""

    def __init__(self):
        self.prompts_dir = Path("prompts/scripts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def generate_prompt(self, title, niche="space facts", duration_minutes=18):
        """Generate a detailed script prompt for AI"""

        target_words = duration_minutes * 250  # 250 words per minute

        prompt = f"""You are a professional YouTube scriptwriter specializing in high-engagement documentary content. Write a complete script for a {duration_minutes}-minute video.

**VIDEO TITLE:**
"{title}"

**TARGET SPECS:**
- Duration: {duration_minutes} minutes
- Word count: ~{target_words} words
- Style: Documentary/educational with high engagement
- Niche: {niche}
- Tone: Authoritative yet accessible, intriguing without sensationalism

**STRUCTURE REQUIREMENTS:**

**1. HOOK (First 30 seconds - Critical!):**
- Open with the most intriguing claim or question
- Present the central mystery immediately
- Use second-person ("you") to engage viewer
- Example: "Right now, a star is doing something that has NASA scientists alarmed..."

**2. INTRODUCTION (30-90 seconds):**
- Establish what Betelgeuse is (red supergiant, distance, size)
- Why it matters
- What the "claims" are that NASA is responding to
- Set up the journey: "In this video, we'll uncover..."

**3. MAIN CONTENT (Broken into 3-5 major sections):**

Section A: What is Betelgeuse?
- Location in Orion constellation
- Size comparison (if Betelgeuse replaced our Sun, its surface would extend past Mars)
- Age and lifecycle stage
- Historical observations

Section B: The Dimming Event & Claims
- 2019-2020 unprecedented dimming
- Wild speculation that circulated
- Claims of imminent supernova
- Social media theories
- Why people were concerned

Section C: What NASA Actually Found
- Real scientific data from Hubble, James Webb, other observatories
- The dust cloud explanation
- Temperature fluctuations
- Actual timeline for supernova (100,000 years? sooner?)

Section D: Why This Matters
- What happens when Betelgeuse goes supernova
- Will it threaten Earth? (spoiler: no, but explain the science)
- What we'll see in the sky
- Scientific value of observing it

Section E: Current Status & Future
- Latest observations
- What scientists are monitoring
- When might we see changes
- How to observe it yourself

**4. RE-ENGAGEMENT POINTS (Every 90 seconds):**
- Insert mini-hooks to maintain attention
- "But that's not the strangest part..."
- "What scientists discovered next changed everything..."
- "Here's where it gets really interesting..."

**5. CONCLUSION (Final 60 seconds):**
- Summarize key revelations
- Answer the title's promise (what NASA actually says vs claims)
- End with forward-looking statement
- Call to action: "What do you think? Let us know in the comments"

**WRITING STYLE GUIDELINES:**

✅ DO:
- Use vivid, specific descriptions
- Include precise scientific data with context
- Build narrative tension
- Use analogies for scale/complexity
- Address viewer directly ("imagine you're looking up...")
- Create curiosity gaps then resolve them
- Cite sources naturally ("According to NASA's latest data...")

❌ DON'T:
- Use clickbait without payoff
- Include filler or repetitive content
- Overcomplicate explanations
- Use jargon without explanation
- Lose focus on the central mystery
- Rush the ending

**ENGAGEMENT TECHNIQUES:**
- Rhetorical questions: "But how could a star this massive simply dim?"
- Contrast: "While some claimed X, the reality was far more interesting..."
- Specific numbers: "900 times larger than our Sun"
- Visual cues: "Picture this:", "Now imagine..."
- Time markers: "For the first time in recorded history..."

**SCRIPT FORMAT:**
[HOOK]
Your opening hook here...

[INTRO]
Your introduction...

[SECTION: What is Betelgeuse?]
Content...

[RE-ENGAGEMENT 1]
"But what happened next shocked even veteran astronomers..."

[SECTION: The Dimming Event]
Content...

[Continue with remaining sections...]

[CONCLUSION]
Your conclusion...

**SCIENTIFIC ACCURACY:**
- Betelgeuse is ~650 light-years away
- It's a red supergiant in the final stages of its life
- The 2019-2020 dimming was caused by dust/material ejection
- Supernova timeline is uncertain (could be 100,000 years, could be sooner)
- When it goes supernova, it will be visible during daytime for weeks
- No danger to Earth at this distance
- Use NASA, ESO, and peer-reviewed sources

Now write the complete {target_words}-word script following this structure. Make it engaging, scientifically accurate, and worth watching for the full {duration_minutes} minutes.
"""

        return prompt

    def save_prompt(self, title, prompt):
        """Save prompt to file"""

        # Create safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"script_prompt_{safe_title}_{timestamp}.txt"

        filepath = self.prompts_dir / filename

        with open(filepath, 'w') as f:
            f.write(f"# Script Prompt for: {title}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Copy the content below and paste into ChatGPT or Claude\n\n")
            f.write("=" * 80 + "\n\n")
            f.write(prompt)

        return filepath

    def create_for_video(self, title, duration_minutes=18):
        """Create and save prompt for a specific video"""

        print(f"\n📝 SCRIPT PROMPT GENERATOR")
        print("=" * 80)
        print(f"Title: {title}")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Target words: ~{duration_minutes * 250}\n")

        # Generate prompt
        prompt = self.generate_prompt(title, duration_minutes=duration_minutes)

        # Save to file
        filepath = self.save_prompt(title, prompt)

        print(f"✅ Prompt saved to: {filepath}\n")
        print("=" * 80)
        print("NEXT STEPS:")
        print("1. Open the file above")
        print("2. Copy the entire prompt")
        print("3. Paste into ChatGPT (GPT-4) or Claude (Opus/Sonnet)")
        print("4. Save the generated script to scripts/drafts/betelgeuse.md")
        print("5. Then run: python src/production/veo_generator.py generate scripts/drafts/betelgeuse.md")
        print("=" * 80 + "\n")

        return filepath


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\nUsage: python src/content/script_prompt_generator.py \"Video Title\" [duration_minutes]")
        print("\nExample:")
        print('  python src/content/script_prompt_generator.py "Finally! NASA Responds To Claims About Betelgeuse" 18')
        return

    title = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 18

    generator = ScriptPromptGenerator()
    generator.create_for_video(title, duration)


if __name__ == "__main__":
    main()
