"""
Phase 2A: Curiosity Gap Detector
Identifies when questions are posed and answered to measure tension/release patterns

Analyzes:
- When curiosity is created (questions, cliffhangers, "but then...")
- How long the gap lasts
- What happens during the gap (visuals, audio, pacing)
- When and how the question is answered
- Emotional payoff patterns
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import re
from datetime import timedelta


class CuriosityGapDetector:
    """Detects and analyzes curiosity gap patterns in video scripts"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

        # Curiosity gap trigger patterns
        self.question_patterns = [
            r'\bwhat\s+(?:if|would|could|happened|happens)\b',
            r'\bhow\s+(?:did|does|can|could|would)\b',
            r'\bwhy\s+(?:did|does|is|are|was|were)\b',
            r'\bwhen\s+(?:did|does|will)\b',
            r'\bwhere\s+(?:did|does|is|are)\b',
            r'\bwho\s+(?:is|are|was|were|did)\b',
            r'\?$',  # Ends with question mark
        ]

        # Cliffhanger patterns
        self.cliffhanger_patterns = [
            r'\bbut\s+then\b',
            r'\bhowever\b',
            r'\bsuddenly\b',
            r'\bshockingly\b',
            r'\bunexpectedly\b',
            r'\bthe\s+result\s+was\b',
            r'\bwhat\s+happened\s+next\b',
            r'\byou\s+won\'?t\s+believe\b',
            r'\bthey\s+didn\'?t\s+know\b',
            r'\blittle\s+did\s+they\s+know\b',
        ]

        # Answer/resolution patterns
        self.resolution_patterns = [
            r'\bthe\s+answer\b',
            r'\bit\s+turned\s+out\b',
            r'\bthey\s+(?:found|discovered|realized)\b',
            r'\bthe\s+result\b',
            r'\bfinally\b',
            r'\bin\s+the\s+end\b',
            r'\beventually\b',
        ]

    def analyze_video_gaps(self, video_id: str, creator_name: str) -> Dict:
        """
        Analyze curiosity gaps in a single video

        Args:
            video_id: Video ID
            creator_name: Creator directory name

        Returns:
            Dict with curiosity gap analysis
        """

        # Load transcript
        creator_dir = self.analysis_dir / creator_name
        transcript_file = creator_dir / f"{video_id}_transcript.json"

        if not transcript_file.exists():
            print(f"❌ Transcript not found: {transcript_file}")
            return {}

        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)

        words = transcript_data.get('words', [])
        full_text = transcript_data.get('text', '')

        if not words:
            print(f"❌ No word-level timestamps in transcript")
            return {}

        print(f"\n🔍 Analyzing curiosity gaps for video {video_id}...")

        # Find all curiosity gaps
        gaps = self._find_gaps(words, full_text)

        # Analyze gap characteristics
        gap_analysis = self._analyze_gaps(gaps, words)

        print(f"   ✅ Found {len(gaps)} curiosity gaps")
        if gaps:
            avg_duration = sum(g['duration'] for g in gaps) / len(gaps)
            print(f"   📊 Average gap duration: {avg_duration:.1f} seconds")

        return {
            'video_id': video_id,
            'total_gaps': len(gaps),
            'gaps': gaps,
            'statistics': gap_analysis
        }

    def _find_gaps(self, words: List[Dict], full_text: str) -> List[Dict]:
        """Find all curiosity gaps in transcript"""

        gaps = []

        # Split into sentences
        sentences = self._split_sentences(words)

        for i, sentence in enumerate(sentences):
            # Check if this sentence creates curiosity
            gap_type = self._is_curiosity_trigger(sentence['text'])

            if gap_type:
                # Find when it's resolved (look ahead)
                resolution_idx = self._find_resolution(sentences, i + 1)

                if resolution_idx:
                    # Found a gap!
                    gap_start = sentence['start_time']
                    gap_end = sentences[resolution_idx]['start_time']
                    duration = gap_end - gap_start

                    gaps.append({
                        'gap_id': len(gaps),
                        'type': gap_type,
                        'trigger_sentence': sentence['text'],
                        'trigger_time': gap_start,
                        'resolution_sentence': sentences[resolution_idx]['text'],
                        'resolution_time': gap_end,
                        'duration': duration,
                        'words_during_gap': self._get_words_in_range(words, gap_start, gap_end)
                    })

        return gaps

    def _split_sentences(self, words: List[Dict]) -> List[Dict]:
        """Split word list into sentences with timestamps"""

        sentences = []
        current_sentence = {
            'words': [],
            'text': '',
            'start_time': None,
            'end_time': None
        }

        for word in words:
            word_text = word.get('word', '')
            word_start = word.get('start', 0)
            word_end = word.get('end', 0)

            if current_sentence['start_time'] is None:
                current_sentence['start_time'] = word_start

            current_sentence['words'].append(word)
            current_sentence['text'] += word_text + ' '
            current_sentence['end_time'] = word_end

            # End of sentence?
            if word_text.endswith('.') or word_text.endswith('?') or word_text.endswith('!'):
                sentences.append({
                    'text': current_sentence['text'].strip(),
                    'start_time': current_sentence['start_time'],
                    'end_time': current_sentence['end_time'],
                    'words': current_sentence['words']
                })
                current_sentence = {
                    'words': [],
                    'text': '',
                    'start_time': None,
                    'end_time': None
                }

        # Add final sentence if exists
        if current_sentence['text']:
            sentences.append({
                'text': current_sentence['text'].strip(),
                'start_time': current_sentence['start_time'],
                'end_time': current_sentence['end_time'],
                'words': current_sentence['words']
            })

        return sentences

    def _is_curiosity_trigger(self, text: str) -> Optional[str]:
        """Check if sentence creates curiosity"""

        text_lower = text.lower()

        # Check for questions
        for pattern in self.question_patterns:
            if re.search(pattern, text_lower):
                return 'question'

        # Check for cliffhangers
        for pattern in self.cliffhanger_patterns:
            if re.search(pattern, text_lower):
                return 'cliffhanger'

        return None

    def _find_resolution(self, sentences: List[Dict], start_idx: int) -> Optional[int]:
        """Find when curiosity is resolved (look ahead max 10 sentences)"""

        max_lookahead = min(start_idx + 10, len(sentences))

        for i in range(start_idx, max_lookahead):
            sentence_text = sentences[i]['text'].lower()

            # Check for resolution patterns
            for pattern in self.resolution_patterns:
                if re.search(pattern, sentence_text):
                    return i

        return None

    def _get_words_in_range(self, words: List[Dict], start_time: float, end_time: float) -> List[str]:
        """Get all words spoken during a time range"""

        range_words = []
        for word in words:
            word_start = word.get('start', 0)
            if start_time <= word_start <= end_time:
                range_words.append(word.get('word', ''))

        return range_words

    def _analyze_gaps(self, gaps: List[Dict], words: List[Dict]) -> Dict:
        """Analyze characteristics of all gaps"""

        if not gaps:
            return {
                'avg_duration': 0,
                'min_duration': 0,
                'max_duration': 0,
                'gap_frequency': 0,
                'gaps_per_minute': 0
            }

        durations = [g['duration'] for g in gaps]
        total_video_duration = words[-1].get('end', 0) if words else 0

        # Calculate statistics
        stats = {
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'gap_frequency': len(gaps),
            'gaps_per_minute': (len(gaps) / total_video_duration) * 60 if total_video_duration > 0 else 0,
            'total_gap_time': sum(durations),
            'gap_time_percentage': (sum(durations) / total_video_duration) * 100 if total_video_duration > 0 else 0,
            'gap_types': {
                'question': len([g for g in gaps if g['type'] == 'question']),
                'cliffhanger': len([g for g in gaps if g['type'] == 'cliffhanger'])
            }
        }

        return stats

    def compare_top_vs_bottom(self, creator_name: str, top_video_ids: List[str], bottom_video_ids: List[str]) -> Dict:
        """
        Compare curiosity gap patterns between top and bottom performers

        Args:
            creator_name: Creator directory name
            top_video_ids: List of top performer video IDs
            bottom_video_ids: List of bottom performer video IDs

        Returns:
            Dict with comparison analysis
        """

        print(f"\n📊 CURIOSITY GAP COMPARISON - Top vs Bottom")
        print("=" * 80)

        # Analyze top videos
        top_analyses = []
        for vid_id in top_video_ids:
            analysis = self.analyze_video_gaps(vid_id, creator_name)
            if analysis:
                top_analyses.append(analysis)

        # Analyze bottom videos
        bottom_analyses = []
        for vid_id in bottom_video_ids:
            analysis = self.analyze_video_gaps(vid_id, creator_name)
            if analysis:
                bottom_analyses.append(analysis)

        # Calculate averages
        top_stats = self._aggregate_stats(top_analyses)
        bottom_stats = self._aggregate_stats(bottom_analyses)

        # Compare
        comparison = {
            'top_performers': top_stats,
            'bottom_performers': bottom_stats,
            'differences': {
                'gap_frequency_diff': top_stats['avg_gaps_per_video'] - bottom_stats['avg_gaps_per_video'],
                'gap_duration_diff': top_stats['avg_gap_duration'] - bottom_stats['avg_gap_duration'],
                'gaps_per_minute_diff': top_stats['avg_gaps_per_minute'] - bottom_stats['avg_gaps_per_minute']
            }
        }

        # Print results
        print(f"\n🏆 TOP PERFORMERS:")
        print(f"   - Avg gaps per video: {top_stats['avg_gaps_per_video']:.1f}")
        print(f"   - Avg gap duration: {top_stats['avg_gap_duration']:.1f} seconds")
        print(f"   - Gaps per minute: {top_stats['avg_gaps_per_minute']:.2f}")

        print(f"\n📉 BOTTOM PERFORMERS:")
        print(f"   - Avg gaps per video: {bottom_stats['avg_gaps_per_video']:.1f}")
        print(f"   - Avg gap duration: {bottom_stats['avg_gap_duration']:.1f} seconds")
        print(f"   - Gaps per minute: {bottom_stats['avg_gaps_per_minute']:.2f}")

        print(f"\n🔗 DIFFERENCES:")
        print(f"   - Top has {comparison['differences']['gap_frequency_diff']:+.1f} more gaps per video")
        print(f"   - Top gaps are {comparison['differences']['gap_duration_diff']:+.1f} seconds longer")
        print(f"   - Top has {comparison['differences']['gaps_per_minute_diff']:+.2f} more gaps/minute")

        return comparison

    def _aggregate_stats(self, analyses: List[Dict]) -> Dict:
        """Aggregate statistics from multiple video analyses"""

        if not analyses:
            return {
                'avg_gaps_per_video': 0,
                'avg_gap_duration': 0,
                'avg_gaps_per_minute': 0
            }

        total_gaps = sum(a['total_gaps'] for a in analyses)
        all_durations = []
        all_gaps_per_minute = []

        for analysis in analyses:
            if analysis.get('gaps'):
                all_durations.extend([g['duration'] for g in analysis['gaps']])
            if analysis.get('statistics'):
                all_gaps_per_minute.append(analysis['statistics']['gaps_per_minute'])

        return {
            'avg_gaps_per_video': total_gaps / len(analyses),
            'avg_gap_duration': sum(all_durations) / len(all_durations) if all_durations else 0,
            'avg_gaps_per_minute': sum(all_gaps_per_minute) / len(all_gaps_per_minute) if all_gaps_per_minute else 0
        }


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 3:
        print("\n🔍 Curiosity Gap Detector")
        print("\nUsage:")
        print("  python src/phase2a_curiosity_gap_detector.py <creator_name> <video_id>")
        print("\nExample:")
        print("  python src/phase2a_curiosity_gap_detector.py watop 6lfV-K7PtII")
        return

    creator_name = sys.argv[1]
    video_id = sys.argv[2]

    detector = CuriosityGapDetector()
    result = detector.analyze_video_gaps(video_id, creator_name)

    # Save results
    output_file = Path(f"analysis/{creator_name}/{video_id}_curiosity_gaps.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
