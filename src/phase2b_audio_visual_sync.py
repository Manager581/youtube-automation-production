"""
Phase 2B: Audio-Visual Sync Analyzer
Maps audio (music, SFX, silence) to visuals and script for pattern extraction

Analyzes:
- When music starts/stops/changes
- Music energy levels (BPM, volume, intensity)
- Sound effects placement and timing
- Silence/pause patterns
- Voice pacing (words per minute, pauses)
- How audio syncs with script moments (reveals, curiosity gaps)
- How audio syncs with visual cuts
"""

import subprocess
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import librosa
import soundfile as sf


class AudioVisualSyncAnalyzer:
    """Analyzes audio patterns and syncs with visual/script timeline"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

    def analyze_video_audio(self, video_path: Path, video_id: str, creator_name: str) -> Dict:
        """
        Complete audio analysis of a video

        Args:
            video_path: Path to video file
            video_id: Video ID
            creator_name: Creator directory name

        Returns:
            Dict with complete audio analysis
        """

        print(f"\n🎵 Analyzing audio for video {video_id}...")

        creator_dir = self.analysis_dir / creator_name
        audio_cache_dir = creator_dir / "audio_cache"
        audio_cache_dir.mkdir(parents=True, exist_ok=True)

        # Extract audio track
        audio_file = audio_cache_dir / f"{video_id}.wav"
        if not audio_file.exists():
            print(f"   📤 Extracting audio track...")
            self._extract_audio(video_path, audio_file)

        # Load audio
        print(f"   📊 Loading audio data...")
        y, sr = librosa.load(str(audio_file), sr=None)

        # Analyze components
        music_analysis = self._analyze_music(y, sr)
        voice_analysis = self._analyze_voice_pacing(y, sr, video_id, creator_name)
        silence_analysis = self._analyze_silence_patterns(y, sr)
        energy_analysis = self._analyze_energy_levels(y, sr)

        result = {
            'video_id': video_id,
            'duration': len(y) / sr,
            'sample_rate': sr,
            'music': music_analysis,
            'voice': voice_analysis,
            'silence': silence_analysis,
            'energy': energy_analysis
        }

        print(f"   ✅ Audio analysis complete")

        return result

    def _extract_audio(self, video_path: Path, output_path: Path):
        """Extract audio track from video using ffmpeg"""

        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # WAV format
            '-ar', '22050',  # 22kHz sample rate (sufficient for analysis)
            '-ac', '1',  # Mono
            '-y',  # Overwrite
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to extract audio: {e}")
            raise

    def _analyze_music(self, y: np.ndarray, sr: int) -> Dict:
        """
        Analyze music characteristics

        Detects:
        - BPM (tempo)
        - Key changes (music transitions)
        - Volume levels over time
        """

        print(f"      🎼 Analyzing music...")

        # Detect tempo (BPM)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

        # Detect onset strength (music changes/transitions)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # RMS energy (volume over time)
        rms = librosa.feature.rms(y=y)[0]
        rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)

        # Identify music changes (big jumps in onset strength)
        music_changes = []
        for i, time in enumerate(onset_times):
            if i > 0:
                # Check if this is a significant change
                strength_change = onset_env[onset_frames[i]] - onset_env[onset_frames[i-1]]
                if abs(strength_change) > np.std(onset_env):
                    music_changes.append({
                        'time': float(time),
                        'strength': float(strength_change),
                        'type': 'increase' if strength_change > 0 else 'decrease'
                    })

        return {
            'bpm': float(tempo),
            'beat_count': len(beats),
            'music_changes': music_changes[:50],  # Limit to 50 most significant
            'avg_energy': float(np.mean(rms)),
            'max_energy': float(np.max(rms)),
            'energy_variance': float(np.var(rms))
        }

    def _analyze_voice_pacing(self, y: np.ndarray, sr: int, video_id: str, creator_name: str) -> Dict:
        """
        Analyze voice pacing patterns

        Requires transcript for word-level timing
        """

        print(f"      🗣️  Analyzing voice pacing...")

        # Load transcript
        creator_dir = self.analysis_dir / creator_name
        transcript_file = creator_dir / f"{video_id}_transcript.json"

        if not transcript_file.exists():
            print(f"         ⚠️  No transcript found, skipping voice analysis")
            return {}

        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)

        words = transcript_data.get('words', [])

        if not words:
            return {}

        # Calculate words per minute
        total_duration = words[-1].get('end', 0) - words[0].get('start', 0)
        word_count = len(words)
        wpm = (word_count / total_duration) * 60 if total_duration > 0 else 0

        # Detect pauses (gaps between words > 0.5 seconds)
        pauses = []
        for i in range(len(words) - 1):
            current_end = words[i].get('end', 0)
            next_start = words[i + 1].get('start', 0)
            gap = next_start - current_end

            if gap > 0.5:  # 0.5 second threshold
                pauses.append({
                    'time': current_end,
                    'duration': gap,
                    'before_word': words[i].get('word', ''),
                    'after_word': words[i + 1].get('word', '')
                })

        # Analyze pacing changes (WPM in 30-second windows)
        window_duration = 30  # seconds
        pacing_changes = []
        for start_time in range(0, int(total_duration), window_duration):
            end_time = start_time + window_duration

            # Count words in window
            window_words = [w for w in words if start_time <= w.get('start', 0) < end_time]
            window_wpm = (len(window_words) / window_duration) * 60 if window_words else 0

            pacing_changes.append({
                'time': start_time,
                'wpm': window_wpm
            })

        return {
            'overall_wpm': float(wpm),
            'total_pauses': len(pauses),
            'long_pauses': [p for p in pauses if p['duration'] > 1.0],  # Pauses > 1 second
            'pacing_over_time': pacing_changes,
            'avg_word_duration': total_duration / word_count if word_count > 0 else 0
        }

    def _analyze_silence_patterns(self, y: np.ndarray, sr: int) -> Dict:
        """
        Detect silence/low-audio segments

        Useful for detecting:
        - Strategic pauses before reveals
        - Music-only sections
        - Dramatic silences
        """

        print(f"      🔇 Detecting silence patterns...")

        # Detect silence using RMS energy
        rms = librosa.feature.rms(y=y)[0]
        silence_threshold = np.percentile(rms, 10)  # Bottom 10% energy = silence

        # Find silent frames
        silent_frames = rms < silence_threshold
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)

        # Group consecutive silent frames into segments
        silence_segments = []
        in_silence = False
        silence_start = 0

        for i, is_silent in enumerate(silent_frames):
            if is_silent and not in_silence:
                # Start of silence
                in_silence = True
                silence_start = times[i]
            elif not is_silent and in_silence:
                # End of silence
                in_silence = False
                silence_end = times[i]
                duration = silence_end - silence_start

                if duration > 0.5:  # Only track silences > 0.5 seconds
                    silence_segments.append({
                        'start': float(silence_start),
                        'end': float(silence_end),
                        'duration': float(duration)
                    })

        return {
            'total_silence_segments': len(silence_segments),
            'silence_segments': silence_segments[:50],  # Limit to 50
            'total_silence_duration': sum(s['duration'] for s in silence_segments),
            'avg_silence_duration': np.mean([s['duration'] for s in silence_segments]) if silence_segments else 0
        }

    def _analyze_energy_levels(self, y: np.ndarray, sr: int) -> Dict:
        """
        Analyze audio energy patterns over time

        Helps identify:
        - Music swells/climaxes
        - Dynamic vs flat audio
        - Energy peaks at key moments
        """

        print(f"      ⚡ Analyzing energy levels...")

        # RMS energy over time
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)

        # Find energy peaks
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(rms, height=np.percentile(rms, 75), distance=sr//512)  # Peaks in top 25% energy

        energy_peaks = [{
            'time': float(times[p]),
            'energy': float(rms[p])
        } for p in peaks]

        # Analyze energy variance in 10-second windows
        window_duration = 10
        energy_windows = []
        for start_idx in range(0, len(rms), sr * window_duration // 512):
            end_idx = min(start_idx + sr * window_duration // 512, len(rms))
            window_rms = rms[start_idx:end_idx]

            if len(window_rms) > 0:
                energy_windows.append({
                    'time': float(times[start_idx]),
                    'avg_energy': float(np.mean(window_rms)),
                    'variance': float(np.var(window_rms))
                })

        return {
            'energy_peaks': energy_peaks[:50],  # Top 50 peaks
            'energy_over_time': energy_windows,
            'overall_variance': float(np.var(rms))
        }

    def sync_audio_to_script(self, audio_analysis: Dict, curiosity_gaps: List[Dict]) -> Dict:
        """
        Sync audio patterns to script events (curiosity gaps, reveals, etc.)

        Identifies patterns like:
        - Music swells during reveals
        - Silence before big moments
        - SFX at key words
        """

        print(f"\n🔗 Syncing audio to script events...")

        synced_patterns = []

        for gap in curiosity_gaps:
            trigger_time = gap['trigger_time']
            resolution_time = gap['resolution_time']

            # Find audio events during this gap
            music_changes_during_gap = [
                mc for mc in audio_analysis['music']['music_changes']
                if trigger_time <= mc['time'] <= resolution_time
            ]

            energy_peaks_during_gap = [
                ep for ep in audio_analysis['energy']['energy_peaks']
                if trigger_time <= ep['time'] <= resolution_time
            ]

            silence_during_gap = [
                s for s in audio_analysis['silence']['silence_segments']
                if trigger_time <= s['start'] <= resolution_time
            ]

            synced_patterns.append({
                'gap_id': gap['gap_id'],
                'gap_type': gap['type'],
                'gap_duration': gap['duration'],
                'music_changes': len(music_changes_during_gap),
                'energy_peaks': len(energy_peaks_during_gap),
                'silence_moments': len(silence_during_gap),
                'pattern': self._identify_audio_pattern(music_changes_during_gap, energy_peaks_during_gap, silence_during_gap, resolution_time)
            })

        return {
            'synced_gaps': synced_patterns,
            'patterns_found': self._summarize_patterns(synced_patterns)
        }

    def _identify_audio_pattern(self, music_changes, energy_peaks, silences, resolution_time) -> str:
        """Identify the audio strategy used during a curiosity gap"""

        patterns = []

        if music_changes:
            # Check if music increases near resolution
            late_changes = [mc for mc in music_changes if mc['time'] > resolution_time - 5]
            if any(mc['type'] == 'increase' for mc in late_changes):
                patterns.append('music_swell_on_reveal')

        if energy_peaks:
            # Energy peak near resolution
            late_peaks = [ep for ep in energy_peaks if ep['time'] > resolution_time - 3]
            if late_peaks:
                patterns.append('energy_peak_on_reveal')

        if silences:
            # Silence before resolution
            late_silences = [s for s in silences if s['start'] > resolution_time - 5]
            if late_silences:
                patterns.append('silence_before_reveal')

        if not patterns:
            return 'no_clear_pattern'

        return ', '.join(patterns)

    def _summarize_patterns(self, synced_patterns: List[Dict]) -> Dict:
        """Summarize common audio-script sync patterns"""

        pattern_counts = {}
        for sp in synced_patterns:
            pattern = sp['pattern']
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        return {
            'most_common_pattern': max(pattern_counts, key=pattern_counts.get) if pattern_counts else 'none',
            'pattern_distribution': pattern_counts
        }


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 4:
        print("\n🎵 Audio-Visual Sync Analyzer")
        print("\nUsage:")
        print("  python src/phase2b_audio_visual_sync.py <video_path> <video_id> <creator_name>")
        print("\nExample:")
        print("  python src/phase2b_audio_visual_sync.py analysis/watop/videos/6lfV-K7PtII.mp4 6lfV-K7PtII watop")
        return

    video_path = Path(sys.argv[1])
    video_id = sys.argv[2]
    creator_name = sys.argv[3]

    analyzer = AudioVisualSyncAnalyzer()
    result = analyzer.analyze_video_audio(video_path, video_id, creator_name)

    # Save results
    output_file = Path(f"analysis/{creator_name}/{video_id}_audio_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
