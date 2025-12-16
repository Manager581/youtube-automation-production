"""
Advanced Effects Timeline Generator for WATOP-Style Editing
Analyzes scripts and generates precise effect timings for hyper-engagement
"""

import re
import json
import yaml
from pathlib import Path
from datetime import datetime
import random


class EffectsTimelineGenerator:
    """Generates WATOP-style effect timeline with sub-second precision"""

    # Effect patterns (in seconds)
    ZOOM_INTERVAL = (2, 4)  # Zoom effect every 2-4 seconds
    TEXT_OVERLAY_KEYWORDS = True  # Show keywords as text
    SFX_INTERVAL = (2, 3)  # Sound effect every 2-3 seconds
    TRANSITION_INTERVAL = (8, 12)  # Transition every 8-12 seconds

    # Text overlay triggers (words that should appear on screen)
    EMPHASIS_WORDS = [
        # Numbers and scale
        r'\d+', r'billion', r'million', r'thousand', r'trillion',
        # Superlatives
        r'biggest', r'largest', r'smallest', r'fastest', r'slowest',
        r'most', r'least', r'first', r'last', r'only', r'never', r'ever',
        # Dramatic words
        r'incredible', r'impossible', r'unbelievable', r'shocking', r'mysterious',
        r'terrifying', r'amazing', r'mind-blowing', r'insane', r'crazy',
        # Space-specific
        r'black hole', r'galaxy', r'planet', r'star', r'universe', r'cosmos',
        r'nasa', r'scientists', r'discovered', r'explode', r'collapse'
    ]

    # Sound effects library (context-based)
    SFX_LIBRARY = {
        "impact": ["explosion", "crash", "destroy", "hit", "smash", "collapse"],
        "whoosh": ["move", "speed", "fast", "flying", "travel", "across"],
        "rumble": ["massive", "huge", "giant", "enormous", "power"],
        "shimmer": ["light", "glow", "bright", "shine", "sparkle"],
        "tension": ["mysterious", "unknown", "secret", "hidden", "waiting"],
        "reveal": ["discovered", "found", "revealed", "scientists", "research"],
        "countdown": [r'\d+', "number", "ranked", "top"],
        "science": ["theory", "physics", "quantum", "energy", "force"]
    }

    # Zoom/pan patterns
    ZOOM_PATTERNS = [
        "zoom_in_slow",
        "zoom_out_slow",
        "zoom_in_fast",
        "pan_right",
        "pan_left",
        "ken_burns_up",
        "ken_burns_down"
    ]

    # Transition types
    TRANSITIONS = [
        "flash_quick",
        "wipe_left",
        "wipe_right",
        "dissolve_fast",
        "zoom_blur",
        "glitch",
        "spin"
    ]

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path("prompts/effects")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_script_timing(self, script_file, voiceover_file=None):
        """Analyze script and create precise timing for all effects"""

        with open(script_file, 'r') as f:
            script_content = f.read()

        # Calculate approximate timing (250 words per minute)
        words = script_content.split()
        word_count = len(words)
        estimated_duration = (word_count / 250) * 60  # seconds

        print(f"\n⏱️  TIMING ANALYSIS")
        print(f"{'='*60}")
        print(f"Words: {word_count}")
        print(f"Estimated Duration: {estimated_duration/60:.1f} minutes")

        # Split into sentences for precise timing
        sentences = re.split(r'[.!?]+', script_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        # Calculate time per sentence
        current_time = 0
        time_per_word = 60 / 250  # seconds per word

        sentence_timings = []
        for sentence in sentences:
            word_count_sentence = len(sentence.split())
            duration = word_count_sentence * time_per_word

            sentence_timings.append({
                "text": sentence,
                "start_time": current_time,
                "end_time": current_time + duration,
                "duration": duration,
                "words": sentence.split()
            })

            current_time += duration

        return sentence_timings, estimated_duration

    def generate_zoom_effects(self, duration):
        """Generate zoom/pan effects every 2-4 seconds"""

        effects = []
        current_time = 0

        while current_time < duration:
            interval = random.uniform(*self.ZOOM_INTERVAL)
            effect_duration = random.uniform(2, 4)

            effects.append({
                "type": "zoom",
                "pattern": random.choice(self.ZOOM_PATTERNS),
                "start_time": current_time,
                "duration": effect_duration,
                "intensity": random.uniform(1.1, 1.3)  # 10-30% zoom
            })

            current_time += interval

        return effects

    def extract_text_overlays(self, sentence_timings):
        """Extract keywords that should appear as text overlays"""

        overlays = []

        for timing in sentence_timings:
            sentence = timing['text'].lower()

            # Check for emphasis words
            for pattern in self.EMPHASIS_WORDS:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)

                for match in matches:
                    keyword = match.group()

                    # Calculate approximate time within sentence
                    words_before = sentence[:match.start()].split()
                    time_offset = len(words_before) * (60 / 250)

                    overlays.append({
                        "type": "text_overlay",
                        "text": keyword.upper(),
                        "start_time": timing['start_time'] + time_offset,
                        "duration": 1.5,  # Show for 1.5 seconds
                        "style": "emphasis",
                        "position": "center",
                        "animation": random.choice(["pop", "slide_up", "fade", "glitch"])
                    })

        return overlays

    def generate_sfx_placements(self, sentence_timings):
        """Generate sound effect placements based on context"""

        sfx_placements = []

        for timing in sentence_timings:
            sentence = timing['text'].lower()

            # Check for contextual SFX triggers
            for sfx_type, triggers in self.SFX_LIBRARY.items():
                for trigger in triggers:
                    if re.search(trigger, sentence, re.IGNORECASE):
                        # Find word position for precise timing
                        words = sentence.split()
                        for i, word in enumerate(words):
                            if re.search(trigger, word, re.IGNORECASE):
                                time_offset = i * (60 / 250)

                                sfx_placements.append({
                                    "type": "sfx",
                                    "sfx_type": sfx_type,
                                    "start_time": timing['start_time'] + time_offset,
                                    "trigger_word": word,
                                    "volume": random.uniform(0.3, 0.6)
                                })

        # Add random SFX every 2-3 seconds to fill gaps
        current_time = 0
        duration = sentence_timings[-1]['end_time'] if sentence_timings else 1200

        while current_time < duration:
            interval = random.uniform(*self.SFX_INTERVAL)

            # Only add if no contextual SFX nearby
            nearby = any(abs(s['start_time'] - current_time) < 1 for s in sfx_placements)

            if not nearby:
                sfx_placements.append({
                    "type": "sfx",
                    "sfx_type": random.choice(["whoosh", "shimmer", "tension"]),
                    "start_time": current_time,
                    "volume": random.uniform(0.2, 0.4)
                })

            current_time += interval

        return sorted(sfx_placements, key=lambda x: x['start_time'])

    def generate_transitions(self, duration, shot_changes):
        """Generate transitions at clip boundaries"""

        transitions = []

        for shot in shot_changes:
            transitions.append({
                "type": "transition",
                "transition_type": random.choice(self.TRANSITIONS),
                "start_time": shot['start_time'],
                "duration": 0.3  # 300ms transition
            })

        return transitions

    def generate_complete_timeline(self, script_file):
        """Generate complete effects timeline"""

        print(f"\n🎬 GENERATING WATOP-STYLE EFFECTS TIMELINE")
        print(f"{'='*60}")

        # Analyze script timing
        sentence_timings, duration = self.analyze_script_timing(script_file)

        # Generate all effects
        zoom_effects = self.generate_zoom_effects(duration)
        text_overlays = self.extract_text_overlays(sentence_timings)
        sfx_placements = self.generate_sfx_placements(sentence_timings)

        # Compile timeline
        timeline = {
            "script_file": str(script_file),
            "generated_at": datetime.now().isoformat(),
            "total_duration": duration,
            "sentence_count": len(sentence_timings),
            "effects_summary": {
                "zoom_effects": len(zoom_effects),
                "text_overlays": len(text_overlays),
                "sfx_placements": len(sfx_placements)
            },
            "sentence_timings": sentence_timings,
            "zoom_effects": zoom_effects,
            "text_overlays": text_overlays,
            "sfx_placements": sfx_placements,
            "engagement_metrics": {
                "effects_per_minute": (len(zoom_effects) + len(text_overlays) + len(sfx_placements)) / (duration / 60),
                "avg_effect_interval": duration / max(len(zoom_effects) + len(text_overlays), 1)
            }
        }

        # Save timeline
        script_name = Path(script_file).stem
        output_file = self.output_dir / f"{script_name}_effects_timeline.json"

        with open(output_file, 'w') as f:
            json.dump(timeline, f, indent=2)

        # Create human-readable guide
        self._create_editing_guide(timeline, script_name)

        print(f"\n✅ Effects Timeline Generated")
        print(f"   Total Effects: {timeline['effects_summary']['zoom_effects'] + timeline['effects_summary']['text_overlays'] + timeline['effects_summary']['sfx_placements']}")
        print(f"   Effects per Minute: {timeline['engagement_metrics']['effects_per_minute']:.1f}")
        print(f"   Avg Effect Interval: {timeline['engagement_metrics']['avg_effect_interval']:.2f}s")
        print(f"\n📁 Saved to: {output_file}")

        return output_file

    def _create_editing_guide(self, timeline, script_name):
        """Create human-readable editing guide for CapCut/DaVinci"""

        guide_file = self.output_dir / f"{script_name}_editing_guide.txt"

        with open(guide_file, 'w') as f:
            f.write(f"WATOP-STYLE EDITING GUIDE - {script_name}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total Duration: {timeline['total_duration']/60:.1f} minutes\n")
            f.write(f"Total Effects: {sum(timeline['effects_summary'].values())}\n")
            f.write(f"Effects per Minute: {timeline['engagement_metrics']['effects_per_minute']:.1f}\n\n")

            f.write(f"ENGAGEMENT PATTERN:\n")
            f.write(f"  - Zoom/Pan effect every 2-4 seconds\n")
            f.write(f"  - Text overlay on keywords (auto-detected)\n")
            f.write(f"  - Sound effect every 2-3 seconds\n\n")

            f.write(f"{'='*80}\n")
            f.write(f"ZOOM EFFECTS ({len(timeline['zoom_effects'])})\n")
            f.write(f"{'='*80}\n\n")

            for i, effect in enumerate(timeline['zoom_effects'][:20]):  # Show first 20
                f.write(f"[{self._format_time(effect['start_time'])}] ")
                f.write(f"{effect['pattern']} ")
                f.write(f"(intensity: {effect['intensity']:.2f}, duration: {effect['duration']:.1f}s)\n")

            f.write(f"\n... and {len(timeline['zoom_effects']) - 20} more\n\n")

            f.write(f"{'='*80}\n")
            f.write(f"TEXT OVERLAYS ({len(timeline['text_overlays'])})\n")
            f.write(f"{'='*80}\n\n")

            for i, overlay in enumerate(timeline['text_overlays'][:30]):
                f.write(f"[{self._format_time(overlay['start_time'])}] ")
                f.write(f'"{overlay["text"]}" ')
                f.write(f"({overlay['animation']})\n")

            f.write(f"\n... and {len(timeline['text_overlays']) - 30} more\n\n")

            f.write(f"{'='*80}\n")
            f.write(f"SOUND EFFECTS ({len(timeline['sfx_placements'])})\n")
            f.write(f"{'='*80}\n\n")

            for i, sfx in enumerate(timeline['sfx_placements'][:30]):
                f.write(f"[{self._format_time(sfx['start_time'])}] ")
                f.write(f"{sfx['sfx_type']}")
                if 'trigger_word' in sfx:
                    f.write(f" (trigger: {sfx['trigger_word']})")
                f.write(f"\n")

            f.write(f"\n... and {len(timeline['sfx_placements']) - 30} more\n\n")

        print(f"   Editing Guide: {guide_file}")

    def _format_time(self, seconds):
        """Format seconds as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"


def main():
    """CLI interface"""
    import sys

    generator = EffectsTimelineGenerator()

    if len(sys.argv) < 2:
        print("🎬 WATOP-Style Effects Timeline Generator")
        print("\nUsage:")
        print("  python src/production/effects_timeline.py <script_file>")
        print("\nExample:")
        print("  python src/production/effects_timeline.py scripts/drafts/black_holes.md")
        return

    script_file = sys.argv[1]
    generator.generate_complete_timeline(script_file)


if __name__ == "__main__":
    main()
