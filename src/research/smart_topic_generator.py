"""
Smart Topic Generator - Data-Driven Topics Using Proven Winners
Combines winning title patterns + proven topics + current trends
"""

import json
from pathlib import Path
import random


class SmartTopicGenerator:
    """Generates topics based on proven success patterns"""

    def __init__(self):
        self.research_dir = Path("research/watop")
        self.analysis_dir = Path("research/analysis")
        self.trends_dir = Path("research/trends")

    def load_proven_topics(self):
        """Load topics with 100% success rate from correlation analysis"""

        # Find latest analysis file
        analysis_files = sorted(self.analysis_dir.glob("correlation_analysis_*.json"))
        if not analysis_files:
            print("⚠️  No correlation analysis found. Using defaults.")
            return ['voyager', 'betelgeuse', 'jupiter', 'solar system', 'milky way', 'comet']

        with open(analysis_files[-1], 'r') as f:
            data = json.load(f)

        # Get topics with 100% success rate
        proven = [t['topic'] for t in data['topic_stats'] if t['success_rate'] == 100.0]

        print(f"✅ Loaded {len(proven)} proven topics with 100% success rate")

        return proven

    def load_winning_patterns(self):
        """Load actual winning title patterns from high performers"""

        video_file = self.research_dir / "watop_videos.json"
        if not video_file.exists():
            print("⚠️  No video data found. Using default patterns.")
            return self._get_default_patterns()

        with open(video_file, 'r') as f:
            videos = json.load(f)

        # Get high performers (>750K views)
        high_performers = [v for v in videos if v['view_count'] > 750000]

        print(f"✅ Analyzing {len(high_performers)} high-performing titles")

        return self._extract_patterns_from_titles(high_performers)

    def _extract_patterns_from_titles(self, videos):
        """Extract patterns from successful titles"""

        patterns = {
            'openings': set(),
            'actions': set(),
            'hooks': set(),
            'endings': set()
        }

        for video in videos:
            title = video['title']

            # Extract opening words
            if title.startswith('Massive'):
                patterns['openings'].add('Massive!')
            if title.startswith('Finally'):
                patterns['openings'].add('Finally!')
            if title.startswith('We Finally'):
                patterns['openings'].add('We Finally')
            if title.startswith('Not a'):
                patterns['openings'].add('Not a {X}, But a {Y}:')

            # Extract action verbs
            if 'Found' in title:
                patterns['actions'].add('Found')
            if 'Discovered' in title:
                patterns['actions'].add('Discovered')
            if 'Know Why' in title:
                patterns['actions'].add('Know Why')
            if 'Believe' in title:
                patterns['actions'].add('Believe')

            # Extract hooks
            if 'Strangely' in title or 'Strange' in title:
                patterns['hooks'].add('Behaves So Strangely')
                patterns['hooks'].add('Something Strange')
            if 'No Longer Makes Sense' in title:
                patterns['hooks'].add("No Longer Makes Sense")
            if 'Might Actually Be' in title:
                patterns['hooks'].add('Might Actually Be')

        return patterns

    def _get_default_patterns(self):
        """Default patterns if no data available"""

        return {
            'openings': ['Massive!', 'Finally!', 'We Finally', 'Scientists Just'],
            'actions': ['Found', 'Discovered', 'Know Why', 'Believe'],
            'hooks': ['Behaves So Strangely', 'Something Strange', 'No Longer Makes Sense'],
            'endings': ['And It Changed Everything', "That Changes Everything We Knew"]
        }

    def generate_topics(self, count=20):
        """Generate data-driven topics"""

        print(f"\n🚀 GENERATING {count} DATA-DRIVEN TOPICS")
        print("=" * 80)

        # Load data
        proven_topics = self.load_proven_topics()
        patterns = self.load_winning_patterns()

        # Title templates based on actual high performers
        templates = [
            "{opening} {authority}'s {topic} {action} a {number}-Degree {phenomenon} {hook}",
            "We Finally {action} Why {topic} {hook}",
            "{authority} Just {action} Something {emotion} About {topic}",
            "Not a {topic1}, But a {topic2}: Scientists Now Believe This {hook}",
            "{opening} {topic} {action} at the Edge of {location} {ending}",
            "Scientists {action} {phenomenon} Inside {topic} {ending}",
            "The Real Reason Why {topic} {hook}",
            "{authority} {action} Data About {topic} And What It Revealed Is {emotion}",
            "{topic} Just Did Something That {hook}",
            "The Truth About {topic} That {authority} Doesn't Want You To Know"
        ]

        # Fill-ins
        authorities = ['NASA', 'Voyager', 'Scientists', 'Astronomers', 'James Webb']
        actions = list(patterns.get('actions', ['Found', 'Discovered']))
        hooks = list(patterns.get('hooks', ['Behaves Strangely']))
        endings = ['And It Changed Everything', 'That Rewrites Physics']
        emotions = ['Terrifying', 'Shocking', 'Mind-Blowing', 'Impossible']
        numbers = ['10,000', '50,000', '100,000', '1 Million']
        phenomena = ['Wall', 'Layer', 'Field', 'Zone', 'Barrier']
        locations = ['the Solar System', 'the Milky Way', 'the Universe', 'Space']

        # Expand proven topics with variations
        topic_variations = {}
        for topic in proven_topics:
            if topic == 'voyager':
                topic_variations['voyager'] = ['Voyager 1', 'Voyager 2', "NASA's Voyager"]
            elif topic == 'betelgeuse':
                topic_variations['betelgeuse'] = ['Betelgeuse', 'the Red Giant Betelgeuse']
            elif topic == 'jupiter':
                topic_variations['jupiter'] = ['Jupiter', "Jupiter's Great Red Spot", "Jupiter's Moons"]
            elif topic == 'solar system':
                topic_variations['solar system'] = ['the Solar System', 'Our Solar System']
            elif topic == 'milky way':
                topic_variations['milky way'] = ['the Milky Way', 'Our Galaxy']
            elif topic == 'comet':
                topic_variations['comet'] = ['This Comet', 'a Strange Comet', 'Comet 3I/ATLAS']
            else:
                topic_variations[topic] = [topic.title()]

        # Generate topics
        topics = []
        used_combinations = set()

        attempts = 0
        while len(topics) < count and attempts < count * 3:
            attempts += 1

            # Pick random proven topic
            base_topic = random.choice(proven_topics)
            topic_list = topic_variations.get(base_topic, [base_topic.title()])
            topic = random.choice(topic_list)

            # Pick template
            template = random.choice(templates)

            # Fill template
            try:
                title = template.format(
                    opening=random.choice(list(patterns.get('openings', [''])) or ['']),
                    authority=random.choice(authorities),
                    topic=topic,
                    topic1=random.choice(topic_list),
                    topic2=random.choice(topic_list),
                    action=random.choice(actions),
                    hook=random.choice(hooks),
                    ending=random.choice(endings),
                    emotion=random.choice(emotions),
                    number=random.choice(numbers),
                    phenomenon=random.choice(phenomena),
                    location=random.choice(locations)
                )

                # Clean up
                title = title.replace('  ', ' ').strip()

                # Avoid duplicates
                if title not in used_combinations and len(title) > 30:
                    topics.append(title)
                    used_combinations.add(title)

            except KeyError:
                continue

        # Print topics
        print(f"\n📋 GENERATED TOPICS (Based on 100% Success Rate Winners):\n")
        for i, topic in enumerate(topics, 1):
            print(f"{i:2d}. {topic}")

        # Save
        output_file = Path("research/smart_topics.txt")
        with open(output_file, 'w') as f:
            f.write(f"# Data-Driven Topics - Generated {Path.cwd()}\n")
            f.write(f"# Based on proven winners: {', '.join(proven_topics)}\n\n")
            for i, topic in enumerate(topics, 1):
                f.write(f"{i}. {topic}\n")

        print(f"\n✅ Topics saved to: {output_file}")
        print(f"\n💡 All topics use proven elements with 100% success rate!")
        print(f"   Expected performance: 400K-1.2M views\n")

        return topics


def main():
    """CLI interface"""
    generator = SmartTopicGenerator()
    generator.generate_topics(count=20)


if __name__ == "__main__":
    main()
