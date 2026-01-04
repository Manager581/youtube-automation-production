"""
Phase 2C: Interview Pattern Extractor
Detects when interviews/talking heads are used and why

Analyzes:
- When interviews appear (intro, middle, end, throughout)
- Duration of interview segments
- Purpose (credibility, emotion, expertise, personal story)
- Visual treatment (full screen, B-roll overlay, split screen)
- Context (what's being discussed when interview appears)
- Effectiveness (correlation with retention)
"""

import cv2
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class InterviewPatternExtractor:
    """Detects and analyzes interview/talking head usage patterns"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

    def analyze_video_interviews(self, video_path: Path, video_id: str, creator_name: str) -> Dict:
        """
        Detect all interview segments in video

        Uses face detection + audio analysis to identify:
        - Person talking to camera
        - Interview segments
        - B-roll with interview audio overlay

        Args:
            video_path: Path to video file
            video_id: Video ID
            creator_name: Creator directory name

        Returns:
            Dict with interview analysis
        """

        print(f"\n👤 Detecting interview segments for video {video_id}...")

        # Detect faces in keyframes (already extracted from Phase 1C)
        face_segments = self._detect_face_segments(video_path, video_id, creator_name)

        # Load transcript to identify interview audio
        interview_audio_segments = self._detect_interview_audio(video_id, creator_name)

        # Combine visual + audio detection
        interview_segments = self._combine_detections(face_segments, interview_audio_segments)

        # Analyze patterns
        analysis = self._analyze_interview_patterns(interview_segments, video_id, creator_name)

        result = {
            'video_id': video_id,
            'interview_segments': interview_segments,
            'statistics': analysis
        }

        print(f"   ✅ Found {len(interview_segments)} interview segments")

        return result

    def _detect_face_segments(self, video_path: Path, video_id: str, creator_name: str) -> List[Dict]:
        """
        Detect segments with human faces (potential talking heads)

        Uses OpenCV Haar Cascade for face detection on keyframes
        """

        print(f"      👁️  Detecting faces in keyframes...")

        # Load OpenCV's pre-trained face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Get keyframes from Phase 1C
        creator_dir = self.analysis_dir / creator_name
        visual_cache_file = creator_dir / f"visual_cache_{video_id}.json"

        if not visual_cache_file.exists():
            print(f"         ⚠️  No visual cache found (run Phase 1C first)")
            return []

        with open(visual_cache_file, 'r') as f:
            visual_data = json.load(f)

        keyframes = visual_data.get('keyframes', {})

        face_segments = []

        for segment_id, keyframe_path in keyframes.items():
            # Read image
            img = cv2.imread(keyframe_path)
            if img is None:
                continue

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(faces) > 0:
                # Found face(s) in this segment
                # Calculate face coverage (what % of frame is face)
                total_face_area = sum(w * h for (x, y, w, h) in faces)
                frame_area = img.shape[0] * img.shape[1]
                face_coverage = total_face_area / frame_area

                # Get timestamp from segments
                segment = next((s for s in visual_data.get('segments', []) if s['segment_id'] == int(segment_id)), None)
                if segment:
                    face_segments.append({
                        'segment_id': int(segment_id),
                        'start_time': segment['start_time'],
                        'end_time': segment.get('end_time'),
                        'face_count': len(faces),
                        'face_coverage': float(face_coverage),
                        'detection_type': 'visual'
                    })

        return face_segments

    def _detect_interview_audio(self, video_id: str, creator_name: str) -> List[Dict]:
        """
        Detect interview segments from audio/transcript patterns

        Indicators:
        - Change in speaker (different voice characteristics)
        - Interview-style language ("I think...", "In my experience...", "We discovered...")
        - Name attribution in transcript
        """

        print(f"      🎤 Analyzing transcript for interview indicators...")

        creator_dir = self.analysis_dir / creator_name
        transcript_file = creator_dir / f"{video_id}_transcript.json"

        if not transcript_file.exists():
            print(f"         ⚠️  No transcript found")
            return []

        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)

        words = transcript_data.get('words', [])
        full_text = transcript_data.get('text', '').lower()

        # Interview language patterns
        interview_patterns = [
            'i think',
            'i believe',
            'in my opinion',
            'in my experience',
            'we found',
            'we discovered',
            'what we saw',
            'according to',
            'dr.',
            'professor',
            'researcher',
            'expert',
            'says',
            'told us',
            'explained'
        ]

        interview_audio_segments = []

        # Split into sentences
        sentences = self._split_into_sentences(words)

        for sentence in sentences:
            sentence_text = sentence['text'].lower()

            # Check for interview indicators
            has_interview_language = any(pattern in sentence_text for pattern in interview_patterns)

            if has_interview_language:
                interview_audio_segments.append({
                    'start_time': sentence['start_time'],
                    'end_time': sentence['end_time'],
                    'text': sentence['text'],
                    'detection_type': 'audio/transcript'
                })

        return interview_audio_segments

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

            # End of sentence?
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

        # Add final sentence
        if current_sentence['text']:
            sentences.append({
                'text': current_sentence['text'].strip(),
                'start_time': current_sentence['start_time'],
                'end_time': current_sentence['end_time']
            })

        return sentences

    def _combine_detections(self, face_segments: List[Dict], interview_audio_segments: List[Dict]) -> List[Dict]:
        """
        Combine visual face detection + audio interview detection

        Segments with BOTH face AND interview language = confirmed interview
        Segments with only face = possible B-roll with person
        Segments with only interview language = possible voice-over interview
        """

        print(f"      🔗 Combining visual + audio detections...")

        combined_segments = []

        # Check each face segment
        for face_seg in face_segments:
            start = face_seg['start_time']
            end = face_seg.get('end_time', start + 5)

            # Find overlapping audio segments
            overlapping_audio = [
                audio for audio in interview_audio_segments
                if not (audio['end_time'] < start or audio['start_time'] > end)
            ]

            interview_type = 'confirmed_interview' if overlapping_audio else 'possible_person'

            combined_segments.append({
                **face_seg,
                'interview_type': interview_type,
                'has_interview_audio': len(overlapping_audio) > 0,
                'audio_segments': overlapping_audio
            })

        # Add audio-only segments (voice-over interviews)
        for audio_seg in interview_audio_segments:
            # Check if already covered by face segment
            overlapping_face = any(
                face['start_time'] <= audio_seg['start_time'] <= face.get('end_time', face['start_time'] + 5)
                for face in face_segments
            )

            if not overlapping_face:
                combined_segments.append({
                    'start_time': audio_seg['start_time'],
                    'end_time': audio_seg['end_time'],
                    'text': audio_seg['text'],
                    'interview_type': 'voice_over_interview',
                    'detection_type': 'audio_only'
                })

        # Sort by time
        combined_segments.sort(key=lambda x: x['start_time'])

        return combined_segments

    def _analyze_interview_patterns(self, interview_segments: List[Dict], video_id: str, creator_name: str) -> Dict:
        """Analyze how and when interviews are used"""

        if not interview_segments:
            return {
                'total_interview_time': 0,
                'interview_percentage': 0,
                'avg_interview_duration': 0,
                'interview_placements': {}
            }

        # Load video duration
        creator_dir = self.analysis_dir / creator_name
        transcript_file = creator_dir / f"{video_id}_transcript.json"

        total_duration = 0
        if transcript_file.exists():
            with open(transcript_file, 'r') as f:
                transcript_data = json.load(f)
                words = transcript_data.get('words', [])
                if words:
                    total_duration = words[-1].get('end', 0)

        # Calculate statistics
        total_interview_time = sum(
            (seg.get('end_time', seg['start_time'] + 5) - seg['start_time'])
            for seg in interview_segments
        )

        # Placement analysis
        intro_interviews = [seg for seg in interview_segments if seg['start_time'] < 30]
        middle_interviews = [seg for seg in interview_segments if 30 <= seg['start_time'] < total_duration - 30]
        outro_interviews = [seg for seg in interview_segments if seg['start_time'] >= total_duration - 30]

        # Type distribution
        type_counts = {}
        for seg in interview_segments:
            seg_type = seg.get('interview_type', 'unknown')
            type_counts[seg_type] = type_counts.get(seg_type, 0) + 1

        return {
            'total_interview_time': total_interview_time,
            'interview_percentage': (total_interview_time / total_duration) * 100 if total_duration > 0 else 0,
            'interview_count': len(interview_segments),
            'avg_interview_duration': total_interview_time / len(interview_segments) if interview_segments else 0,
            'interview_placements': {
                'intro': len(intro_interviews),
                'middle': len(middle_interviews),
                'outro': len(outro_interviews)
            },
            'interview_types': type_counts
        }


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 4:
        print("\n👤 Interview Pattern Extractor")
        print("\nUsage:")
        print("  python src/phase2c_interview_extractor.py <video_path> <video_id> <creator_name>")
        print("\nExample:")
        print("  python src/phase2c_interview_extractor.py analysis/watop/videos/6lfV-K7PtII.mp4 6lfV-K7PtII watop")
        return

    video_path = Path(sys.argv[1])
    video_id = sys.argv[2]
    creator_name = sys.argv[3]

    extractor = InterviewPatternExtractor()
    result = extractor.analyze_video_interviews(video_path, video_id, creator_name)

    # Save results
    output_file = Path(f"analysis/{creator_name}/{video_id}_interview_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
