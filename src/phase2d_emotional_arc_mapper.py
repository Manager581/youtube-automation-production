"""
Phase 2D: Emotional Arc Mapper
Tracks emotional journey throughout video by combining multiple signals

Analyzes:
- Script tone (questions, reveals, shocking facts, calm explanations)
- Audio energy (music intensity, silence, dramatic swells)
- Visual pacing (cut frequency changes, motion intensity)
- Combined emotional peaks and valleys
- Tension/release patterns
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from textblob import TextBlob


class EmotionalArcMapper:
    """Maps emotional arc throughout video using multi-modal analysis"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

        # Emotional tone indicators in script
        self.high_emotion_words = [
            'shocking', 'incredible', 'terrifying', 'amazing', 'unbelievable',
            'devastating', 'catastrophic', 'miraculous', 'horrifying', 'stunning',
            'extraordinary', 'unprecedented', 'disaster', 'breakthrough', 'crisis'
        ]

        self.mystery_words = [
            'mysterious', 'unknown', 'secret', 'hidden', 'strange',
            'bizarre', 'unexplained', 'enigma', 'puzzle', 'riddle'
        ]

        self.calm_words = [
            'however', 'meanwhile', 'typically', 'generally', 'normally',
            'usually', 'according', 'researchers', 'scientists', 'experts'
        ]

    def analyze_emotional_arc(self, video_id: str, creator_name: str) -> Dict:
        """
        Map complete emotional arc for a video

        Combines:
        - Script emotional tone
        - Audio energy levels
        - Visual pacing
        - Curiosity gaps

        Returns:
            Dict with emotional timeline and analysis
        """

        print(f"\n💓 Mapping emotional arc for video {video_id}...")

        creator_dir = self.analysis_dir / creator_name

        # Load all necessary data
        script_emotions = self._analyze_script_emotions(video_id, creator_name)
        audio_emotions = self._load_audio_emotions(video_id, creator_name)
        visual_pacing = self._analyze_visual_pacing(video_id, creator_name)
        curiosity_gaps = self._load_curiosity_gaps(video_id, creator_name)

        # Combine into unified timeline
        emotional_timeline = self._create_emotional_timeline(
            script_emotions,
            audio_emotions,
            visual_pacing,
            curiosity_gaps
        )

        # Analyze patterns
        analysis = self._analyze_emotional_patterns(emotional_timeline)

        result = {
            'video_id': video_id,
            'emotional_timeline': emotional_timeline,
            'analysis': analysis
        }

        print(f"   ✅ Emotional arc mapped with {len(emotional_timeline)} key moments")

        return result

    def _analyze_script_emotions(self, video_id: str, creator_name: str) -> List[Dict]:
        """
        Analyze emotional tone from script text

        Uses:
        - Emotional keywords
        - Sentence sentiment
        - Question patterns
        - Exclamation usage
        """

        print(f"      📝 Analyzing script emotions...")

        creator_dir = self.analysis_dir / creator_name
        transcript_file = creator_dir / f"{video_id}_transcript.json"

        if not transcript_file.exists():
            print(f"         ⚠️  No transcript found")
            return []

        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)

        words = transcript_data.get('words', [])

        # Split into sentences
        sentences = self._split_into_sentences(words)

        script_emotions = []

        for sentence in sentences:
            text = sentence['text']
            text_lower = text.lower()

            # Detect emotion type
            emotion_type = self._detect_emotion_type(text_lower)

            # Sentiment analysis
            try:
                blob = TextBlob(text)
                sentiment_polarity = blob.sentiment.polarity  # -1 to 1
                sentiment_subjectivity = blob.sentiment.subjectivity  # 0 to 1
            except:
                sentiment_polarity = 0
                sentiment_subjectivity = 0

            # Emotional intensity (0-1 scale)
            intensity = self._calculate_emotional_intensity(
                text_lower,
                emotion_type,
                sentiment_polarity,
                sentiment_subjectivity
            )

            script_emotions.append({
                'time': sentence['start_time'],
                'emotion_type': emotion_type,
                'intensity': intensity,
                'sentiment': sentiment_polarity,
                'subjectivity': sentiment_subjectivity,
                'text': text[:100]  # First 100 chars for context
            })

        return script_emotions

    def _detect_emotion_type(self, text: str) -> str:
        """Detect primary emotion in text"""

        # Check for question (curiosity/mystery)
        if '?' in text:
            return 'curiosity'

        # Check for high emotion words
        if any(word in text for word in self.high_emotion_words):
            return 'high_emotion'

        # Check for mystery
        if any(word in text for word in self.mystery_words):
            return 'mystery'

        # Check for calm/explanatory
        if any(word in text for word in self.calm_words):
            return 'calm_explanation'

        # Check for exclamation
        if '!' in text:
            return 'excitement'

        return 'neutral'

    def _calculate_emotional_intensity(self, text: str, emotion_type: str,
                                      sentiment: float, subjectivity: float) -> float:
        """Calculate 0-1 emotional intensity score"""

        intensity = 0.0

        # Base intensity from emotion type
        emotion_base = {
            'high_emotion': 0.8,
            'excitement': 0.7,
            'mystery': 0.6,
            'curiosity': 0.5,
            'neutral': 0.3,
            'calm_explanation': 0.2
        }
        intensity = emotion_base.get(emotion_type, 0.3)

        # Boost from sentiment extremes
        intensity += abs(sentiment) * 0.2

        # Boost from subjectivity (emotional = subjective)
        intensity += subjectivity * 0.1

        # Cap at 1.0
        return min(intensity, 1.0)

    def _load_audio_emotions(self, video_id: str, creator_name: str) -> List[Dict]:
        """Load audio energy data from Phase 2B"""

        print(f"      🎵 Loading audio energy data...")

        creator_dir = self.analysis_dir / creator_name
        audio_file = creator_dir / f"{video_id}_audio_analysis.json"

        if not audio_file.exists():
            print(f"         ⚠️  No audio analysis found (run Phase 2B first)")
            return []

        with open(audio_file, 'r') as f:
            audio_data = json.load(f)

        # Extract energy timeline
        energy_windows = audio_data.get('energy', {}).get('energy_over_time', [])

        # Normalize energy to 0-1 scale
        if energy_windows:
            max_energy = max(w['avg_energy'] for w in energy_windows)
            min_energy = min(w['avg_energy'] for w in energy_windows)
            energy_range = max_energy - min_energy if max_energy > min_energy else 1

            audio_emotions = []
            for window in energy_windows:
                normalized_energy = (window['avg_energy'] - min_energy) / energy_range
                audio_emotions.append({
                    'time': window['time'],
                    'energy': normalized_energy,
                    'variance': window['variance']
                })

            return audio_emotions

        return []

    def _analyze_visual_pacing(self, video_id: str, creator_name: str) -> List[Dict]:
        """Analyze visual pacing changes (cut frequency over time)"""

        print(f"      🎬 Analyzing visual pacing...")

        creator_dir = self.analysis_dir / creator_name
        visual_cache_file = creator_dir / f"visual_cache_{video_id}.json"

        if not visual_cache_file.exists():
            print(f"         ⚠️  No visual cache found (run Phase 1C first)")
            return []

        with open(visual_cache_file, 'r') as f:
            visual_data = json.load(f)

        segments = visual_data.get('segments', [])

        if not segments:
            return []

        # Calculate cut frequency in 30-second windows
        window_duration = 30
        total_duration = segments[-1].get('end_time', segments[-1]['start_time'] + 5)

        pacing_timeline = []

        for start_time in np.arange(0, total_duration, window_duration):
            end_time = start_time + window_duration

            # Count cuts in this window
            cuts_in_window = sum(
                1 for seg in segments
                if start_time <= seg['start_time'] < end_time
            )

            # Normalize to 0-1 (assume max ~15 cuts per 30 sec window)
            pacing_intensity = min(cuts_in_window / 15.0, 1.0)

            pacing_timeline.append({
                'time': start_time,
                'pacing_intensity': pacing_intensity,
                'cuts_per_30sec': cuts_in_window
            })

        return pacing_timeline

    def _load_curiosity_gaps(self, video_id: str, creator_name: str) -> List[Dict]:
        """Load curiosity gaps from Phase 2A"""

        creator_dir = self.analysis_dir / creator_name
        gaps_file = creator_dir / f"{video_id}_curiosity_gaps.json"

        if not gaps_file.exists():
            return []

        with open(gaps_file, 'r') as f:
            gaps_data = json.load(f)

        return gaps_data.get('gaps', [])

    def _create_emotional_timeline(self, script_emotions: List[Dict],
                                   audio_emotions: List[Dict],
                                   visual_pacing: List[Dict],
                                   curiosity_gaps: List[Dict]) -> List[Dict]:
        """
        Combine all emotional signals into unified timeline

        Creates 10-second windows with combined emotion score
        """

        print(f"      🔗 Combining emotional signals...")

        # Find total duration
        max_time = 0
        if script_emotions:
            max_time = max(max_time, max(e['time'] for e in script_emotions))
        if audio_emotions:
            max_time = max(max_time, max(e['time'] for e in audio_emotions))
        if visual_pacing:
            max_time = max(max_time, max(p['time'] for p in visual_pacing))

        if max_time == 0:
            return []

        # Create timeline in 10-second windows
        window_duration = 10
        timeline = []

        for start_time in np.arange(0, max_time, window_duration):
            end_time = start_time + window_duration

            # Get signals in this window
            script_in_window = [e for e in script_emotions if start_time <= e['time'] < end_time]
            audio_in_window = [e for e in audio_emotions if start_time <= e['time'] < end_time]
            pacing_in_window = [p for p in visual_pacing if start_time <= p['time'] < end_time]
            gaps_in_window = [
                g for g in curiosity_gaps
                if start_time <= g['trigger_time'] < end_time or
                   start_time <= g.get('resolution_time', 0) < end_time
            ]

            # Calculate combined emotion score
            script_score = np.mean([e['intensity'] for e in script_in_window]) if script_in_window else 0.5
            audio_score = np.mean([e['energy'] for e in audio_in_window]) if audio_in_window else 0.5
            pacing_score = np.mean([p['pacing_intensity'] for p in pacing_in_window]) if pacing_in_window else 0.5

            # Weighted combination (script is most important for emotion)
            combined_score = (
                script_score * 0.5 +
                audio_score * 0.3 +
                pacing_score * 0.2
            )

            # Boost for curiosity gaps
            in_curiosity_gap = any(
                g['trigger_time'] <= start_time <= g.get('resolution_time', g['trigger_time'])
                for g in curiosity_gaps
            )

            if in_curiosity_gap:
                combined_score *= 1.2  # 20% boost during curiosity gaps
                combined_score = min(combined_score, 1.0)

            timeline.append({
                'time': start_time,
                'emotional_intensity': combined_score,
                'script_intensity': script_score,
                'audio_intensity': audio_score,
                'pacing_intensity': pacing_score,
                'in_curiosity_gap': in_curiosity_gap,
                'dominant_emotion': script_in_window[0]['emotion_type'] if script_in_window else 'neutral'
            })

        return timeline

    def _analyze_emotional_patterns(self, timeline: List[Dict]) -> Dict:
        """Analyze patterns in emotional arc"""

        if not timeline:
            return {}

        intensities = [t['emotional_intensity'] for t in timeline]

        # Find peaks and valleys
        peaks = []
        valleys = []

        for i in range(1, len(intensities) - 1):
            if intensities[i] > intensities[i-1] and intensities[i] > intensities[i+1]:
                if intensities[i] > 0.7:  # Only significant peaks
                    peaks.append({
                        'time': timeline[i]['time'],
                        'intensity': intensities[i],
                        'emotion': timeline[i]['dominant_emotion']
                    })

            if intensities[i] < intensities[i-1] and intensities[i] < intensities[i+1]:
                if intensities[i] < 0.4:  # Only significant valleys
                    valleys.append({
                        'time': timeline[i]['time'],
                        'intensity': intensities[i]
                    })

        # Calculate arc shape
        avg_intensity = np.mean(intensities)
        intensity_variance = np.var(intensities)

        # Intro vs outro comparison
        intro_intensity = np.mean(intensities[:3]) if len(intensities) >= 3 else 0
        outro_intensity = np.mean(intensities[-3:]) if len(intensities) >= 3 else 0

        return {
            'avg_emotional_intensity': float(avg_intensity),
            'intensity_variance': float(intensity_variance),
            'peak_count': len(peaks),
            'valley_count': len(valleys),
            'peaks': peaks[:10],  # Top 10 peaks
            'valleys': valleys[:10],
            'intro_intensity': float(intro_intensity),
            'outro_intensity': float(outro_intensity),
            'arc_shape': 'crescendo' if outro_intensity > intro_intensity + 0.2 else
                        'decrescendo' if intro_intensity > outro_intensity + 0.2 else
                        'stable'
        }

    def _split_into_sentences(self, words: List[Dict]) -> List[Dict]:
        """Split words into sentences"""

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

            if word_text.endswith('.') or word_text.endswith('?') or word_text.endswith('!'):
                sentences.append({
                    'text': current_sentence['text'].strip(),
                    'start_time': current_sentence['start_time'],
                    'end_time': current_sentence['end_time']
                })
                current_sentence = {
                    'words': [],
                    'text': '',
                    'start_time': None,
                    'end_time': None
                }

        if current_sentence['text']:
            sentences.append({
                'text': current_sentence['text'].strip(),
                'start_time': current_sentence['start_time'],
                'end_time': current_sentence['end_time']
            })

        return sentences


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 3:
        print("\n💓 Emotional Arc Mapper")
        print("\nUsage:")
        print("  python src/phase2d_emotional_arc_mapper.py <video_id> <creator_name>")
        print("\nExample:")
        print("  python src/phase2d_emotional_arc_mapper.py 6lfV-K7PtII watop")
        print("\nRequires:")
        print("  - Phase 1C (visual cache)")
        print("  - Phase 2A (curiosity gaps)")
        print("  - Phase 2B (audio analysis)")
        return

    video_id = sys.argv[1]
    creator_name = sys.argv[2]

    mapper = EmotionalArcMapper()
    result = mapper.analyze_emotional_arc(video_id, creator_name)

    # Save results
    output_file = Path(f"analysis/{creator_name}/{video_id}_emotional_arc.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
