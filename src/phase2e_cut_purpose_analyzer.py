"""
Phase 2E: Cut Purpose Analyzer
Determines WHY each cut was made by analyzing context

Analyzes:
- What changed between shots (subject, emotion, pacing)
- Timing relative to script events (question asked, answer given, new topic)
- Correlation with audio events (music change, SFX, silence)
- Purpose categories (emotional shift, reveal, pacing, subject change, emphasis)
"""

import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class CutPurposeAnalyzer:
    """Analyzes why each cut was made"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

    def analyze_cut_purposes(self, video_id: str, creator_name: str) -> Dict:
        """
        Analyze purpose of each cut in video

        Combines:
        - Visual analysis (what changed visually)
        - Script context (what's being said)
        - Emotional arc (emotion before/after cut)
        - Audio events (music/SFX timing)

        Returns:
            Dict with cut-by-cut analysis
        """

        print(f"\n✂️  Analyzing cut purposes for video {video_id}...")

        creator_dir = self.analysis_dir / creator_name

        # Load necessary data
        visual_segments = self._load_visual_segments(video_id, creator_name)
        script_data = self._load_script_data(video_id, creator_name)
        emotional_timeline = self._load_emotional_timeline(video_id, creator_name)
        audio_events = self._load_audio_events(video_id, creator_name)

        # Analyze each cut
        cut_analyses = []

        for i in range(len(visual_segments) - 1):
            current_segment = visual_segments[i]
            next_segment = visual_segments[i + 1]

            cut_time = next_segment['start_time']

            # Determine cut purpose
            purpose = self._determine_cut_purpose(
                current_segment,
                next_segment,
                cut_time,
                script_data,
                emotional_timeline,
                audio_events
            )

            cut_analyses.append(purpose)

        # Analyze patterns
        analysis = self._analyze_cut_patterns(cut_analyses)

        result = {
            'video_id': video_id,
            'total_cuts': len(cut_analyses),
            'cuts': cut_analyses,
            'analysis': analysis
        }

        print(f"   ✅ Analyzed {len(cut_analyses)} cuts")

        return result

    def _load_visual_segments(self, video_id: str, creator_name: str) -> List[Dict]:
        """Load visual segments from Phase 1C"""

        creator_dir = self.analysis_dir / creator_name
        visual_cache_file = creator_dir / f"visual_cache_{video_id}.json"

        if not visual_cache_file.exists():
            print(f"   ⚠️  No visual cache found (run Phase 1C first)")
            return []

        with open(visual_cache_file, 'r') as f:
            visual_data = json.load(f)

        segments = visual_data.get('segments', [])

        # Load visual classifications if available
        visual_sync_file = creator_dir / f"visual_sync_{video_id}.json"
        classifications = {}

        if visual_sync_file.exists():
            with open(visual_sync_file, 'r') as f:
                sync_data = json.load(f)
                for classification in sync_data.get('visual_classifications', []):
                    seg_id = classification.get('segment_id')
                    classifications[seg_id] = classification

        # Merge classifications into segments
        for segment in segments:
            seg_id = segment['segment_id']
            if seg_id in classifications:
                segment['classification'] = classifications[seg_id]

        return segments

    def _load_script_data(self, video_id: str, creator_name: str) -> Dict:
        """Load script/transcript data"""

        creator_dir = self.analysis_dir / creator_name
        transcript_file = creator_dir / f"{video_id}_transcript.json"

        if not transcript_file.exists():
            return {'words': [], 'text': ''}

        with open(transcript_file, 'r') as f:
            return json.load(f)

    def _load_emotional_timeline(self, video_id: str, creator_name: str) -> List[Dict]:
        """Load emotional timeline from Phase 2D"""

        creator_dir = self.analysis_dir / creator_name
        emotion_file = creator_dir / f"{video_id}_emotional_arc.json"

        if not emotion_file.exists():
            return []

        with open(emotion_file, 'r') as f:
            emotion_data = json.load(f)
            return emotion_data.get('emotional_timeline', [])

    def _load_audio_events(self, video_id: str, creator_name: str) -> Dict:
        """Load audio events from Phase 2B"""

        creator_dir = self.analysis_dir / creator_name
        audio_file = creator_dir / f"{video_id}_audio_analysis.json"

        if not audio_file.exists():
            return {}

        with open(audio_file, 'r') as f:
            return json.load(f)

    def _determine_cut_purpose(self, current_seg: Dict, next_seg: Dict,
                               cut_time: float, script_data: Dict,
                               emotional_timeline: List[Dict],
                               audio_events: Dict) -> Dict:
        """Determine why this specific cut was made"""

        purposes = []
        confidence_scores = []

        # 1. Check for visual change
        visual_change, visual_confidence = self._check_visual_change(current_seg, next_seg)
        if visual_change:
            purposes.append(visual_change)
            confidence_scores.append(visual_confidence)

        # 2. Check for script event
        script_event, script_confidence = self._check_script_event(cut_time, script_data)
        if script_event:
            purposes.append(script_event)
            confidence_scores.append(script_confidence)

        # 3. Check for emotional shift
        emotion_shift, emotion_confidence = self._check_emotional_shift(cut_time, emotional_timeline)
        if emotion_shift:
            purposes.append(emotion_shift)
            confidence_scores.append(emotion_confidence)

        # 4. Check for audio event
        audio_event, audio_confidence = self._check_audio_event(cut_time, audio_events)
        if audio_event:
            purposes.append(audio_event)
            confidence_scores.append(audio_confidence)

        # Determine primary purpose (highest confidence)
        if purposes:
            primary_idx = confidence_scores.index(max(confidence_scores))
            primary_purpose = purposes[primary_idx]
            primary_confidence = confidence_scores[primary_idx]
        else:
            primary_purpose = 'pacing'  # Default: maintaining rhythm
            primary_confidence = 0.5

        return {
            'cut_time': cut_time,
            'from_segment': current_seg['segment_id'],
            'to_segment': next_seg['segment_id'],
            'primary_purpose': primary_purpose,
            'confidence': primary_confidence,
            'all_purposes': purposes,
            'script_context': self._get_script_context(cut_time, script_data)
        }

    def _check_visual_change(self, current_seg: Dict, next_seg: Dict) -> Tuple[Optional[str], float]:
        """Check if visual content type changed"""

        current_type = current_seg.get('classification', {}).get('content_type', 'unknown')
        next_type = next_seg.get('classification', {}).get('content_type', 'unknown')

        if current_type != 'unknown' and next_type != 'unknown' and current_type != next_type:
            # Visual type changed
            return f'visual_change_{current_type}_to_{next_type}', 0.9

        return None, 0.0

    def _check_script_event(self, cut_time: float, script_data: Dict) -> Tuple[Optional[str], float]:
        """Check if cut coincides with script event (question, answer, new topic)"""

        words = script_data.get('words', [])

        # Find words around cut time (±2 seconds)
        nearby_words = [
            w for w in words
            if abs(w.get('start', 0) - cut_time) < 2.0
        ]

        if not nearby_words:
            return None, 0.0

        nearby_text = ' '.join([w.get('word', '') for w in nearby_words]).lower()

        # Check for question
        if '?' in nearby_text:
            return 'question_posed', 0.8

        # Check for answer indicators
        answer_words = ['answer', 'turned out', 'discovered', 'found', 'result']
        if any(word in nearby_text for word in answer_words):
            return 'answer_revealed', 0.8

        # Check for topic transition
        transition_words = ['however', 'but', 'meanwhile', 'then', 'next', 'after']
        if any(word in nearby_text for word in transition_words):
            return 'topic_transition', 0.7

        # Check for emphasis
        emphasis_words = ['shocking', 'incredible', 'amazing', 'terrifying', 'suddenly']
        if any(word in nearby_text for word in emphasis_words):
            return 'emphasis', 0.7

        return None, 0.0

    def _check_emotional_shift(self, cut_time: float, emotional_timeline: List[Dict]) -> Tuple[Optional[str], float]:
        """Check if cut coincides with emotional shift"""

        if not emotional_timeline:
            return None, 0.0

        # Find emotion before and after cut
        before_emotion = None
        after_emotion = None

        for i, moment in enumerate(emotional_timeline):
            if moment['time'] <= cut_time:
                before_emotion = moment
            elif moment['time'] > cut_time and after_emotion is None:
                after_emotion = moment

        if not before_emotion or not after_emotion:
            return None, 0.0

        # Check for significant intensity change
        intensity_change = abs(after_emotion['emotional_intensity'] - before_emotion['emotional_intensity'])

        if intensity_change > 0.3:  # Significant shift
            if after_emotion['emotional_intensity'] > before_emotion['emotional_intensity']:
                return 'emotional_escalation', 0.75
            else:
                return 'emotional_deescalation', 0.75

        return None, 0.0

    def _check_audio_event(self, cut_time: float, audio_events: Dict) -> Tuple[Optional[str], float]:
        """Check if cut coincides with audio event (music change, SFX, etc.)"""

        if not audio_events:
            return None, 0.0

        # Check music changes
        music_changes = audio_events.get('music', {}).get('music_changes', [])
        for change in music_changes:
            if abs(change['time'] - cut_time) < 1.0:  # Within 1 second
                return f'music_{change["type"]}', 0.7

        # Check energy peaks
        energy_peaks = audio_events.get('energy', {}).get('energy_peaks', [])
        for peak in energy_peaks:
            if abs(peak['time'] - cut_time) < 1.0:
                return 'audio_peak', 0.6

        # Check silence
        silence_segments = audio_events.get('silence', {}).get('silence_segments', [])
        for silence in silence_segments:
            if silence['start'] <= cut_time <= silence['end']:
                return 'during_silence', 0.6

        return None, 0.0

    def _get_script_context(self, cut_time: float, script_data: Dict) -> str:
        """Get script text around cut time for context"""

        words = script_data.get('words', [])

        nearby_words = [
            w for w in words
            if abs(w.get('start', 0) - cut_time) < 3.0  # ±3 seconds
        ]

        if nearby_words:
            return ' '.join([w.get('word', '') for w in nearby_words])[:100]

        return ''

    def _analyze_cut_patterns(self, cut_analyses: List[Dict]) -> Dict:
        """Analyze patterns in cut purposes"""

        if not cut_analyses:
            return {}

        # Count purpose types
        purpose_counts = {}
        for cut in cut_analyses:
            purpose = cut['primary_purpose']
            purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1

        # Calculate average confidence
        avg_confidence = np.mean([cut['confidence'] for cut in cut_analyses])

        # Most common purpose
        most_common_purpose = max(purpose_counts, key=purpose_counts.get) if purpose_counts else 'unknown'

        return {
            'total_cuts': len(cut_analyses),
            'purpose_distribution': purpose_counts,
            'most_common_purpose': most_common_purpose,
            'avg_confidence': float(avg_confidence),
            'purpose_percentages': {
                k: (v / len(cut_analyses)) * 100
                for k, v in purpose_counts.items()
            }
        }


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 3:
        print("\n✂️  Cut Purpose Analyzer")
        print("\nUsage:")
        print("  python src/phase2e_cut_purpose_analyzer.py <video_id> <creator_name>")
        print("\nExample:")
        print("  python src/phase2e_cut_purpose_analyzer.py 6lfV-K7PtII watop")
        print("\nRequires:")
        print("  - Phase 1C (visual segments)")
        print("  - Phase 2B (audio analysis)")
        print("  - Phase 2D (emotional arc)")
        return

    video_id = sys.argv[1]
    creator_name = sys.argv[2]

    analyzer = CutPurposeAnalyzer()
    result = analyzer.analyze_cut_purposes(video_id, creator_name)

    # Save results
    output_file = Path(f"analysis/{creator_name}/{video_id}_cut_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
