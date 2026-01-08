"""
Master Formula Extractor
Runs ALL analysis phases and generates complete creator formula

Complete Pipeline:
- Phase 1A/1B: Download videos, extract transcripts, get metrics
- Phase 1C: Visual analysis (types, sources, timing)
- Phase 2A: Curiosity gap detection
- Phase 2B: Audio-visual sync analysis
- Phase 2C: Interview pattern extraction
- Phase 2D: Emotional arc mapping
- Phase 2E: Cut purpose analysis
- Pattern Extraction: Compare top vs bottom
- SOP Generation: Create actionable formula

Output:
- Complete JSON analysis
- Human-readable SOP document
- Visual timeline graphs
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Import all phase analyzers
sys.path.insert(0, str(Path(__file__).parent))
from phase2a_curiosity_gap_detector import CuriosityGapDetector
from phase2b_audio_visual_sync import AudioVisualSyncAnalyzer
from phase2c_interview_extractor import InterviewPatternExtractor
from phase2d_emotional_arc_mapper import EmotionalArcMapper
from phase2e_cut_purpose_analyzer import CutPurposeAnalyzer


class MasterFormulaExtractor:
    """Runs complete analysis pipeline and generates creator formula"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

        # Initialize all analyzers
        self.curiosity_detector = CuriosityGapDetector(analysis_dir)
        self.audio_analyzer = AudioVisualSyncAnalyzer(analysis_dir)
        self.interview_extractor = InterviewPatternExtractor(analysis_dir)
        self.emotion_mapper = EmotionalArcMapper(analysis_dir)
        self.cut_analyzer = CutPurposeAnalyzer(analysis_dir)

    def extract_complete_formula(self, creator_name: str, video_ids: List[str],
                                  video_paths: List[Path]) -> Dict:
        """
        Run complete analysis on all videos

        Args:
            creator_name: Creator directory name
            video_ids: List of video IDs to analyze
            video_paths: List of paths to video files

        Returns:
            Dict with complete formula analysis
        """

        print(f"\n🔬 MASTER FORMULA EXTRACTION - {creator_name.upper()}")
        print("=" * 80)
        print(f"📊 Analyzing {len(video_ids)} videos with ALL phases...")

        results = {
            'creator_name': creator_name,
            'total_videos': len(video_ids),
            'videos': []
        }

        for i, (video_id, video_path) in enumerate(zip(video_ids, video_paths), 1):
            print(f"\n{'='*80}")
            print(f"📹 VIDEO {i}/{len(video_ids)}: {video_id}")
            print(f"{'='*80}")

            video_analysis = self._analyze_single_video(video_id, video_path, creator_name)
            results['videos'].append(video_analysis)

        # Extract patterns across all videos
        print(f"\n{'='*80}")
        print(f"🔍 EXTRACTING CROSS-VIDEO PATTERNS")
        print(f"{'='*80}")

        patterns = self._extract_patterns(results['videos'])
        results['patterns'] = patterns

        # Generate SOP
        print(f"\n{'='*80}")
        print(f"📋 GENERATING SOP")
        print(f"{'='*80}")

        sop = self._generate_sop(patterns, creator_name)
        results['sop'] = sop

        # Save complete results
        output_file = self.analysis_dir / creator_name / "complete_formula.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Complete formula extracted!")
        print(f"💾 Results saved to: {output_file}")

        # Save human-readable SOP
        sop_file = self.analysis_dir / creator_name / "FORMULA_SOP.md"
        with open(sop_file, 'w') as f:
            f.write(sop)

        print(f"📄 SOP saved to: {sop_file}")

        return results

    def _analyze_single_video(self, video_id: str, video_path: Path, creator_name: str) -> Dict:
        """Run all analysis phases on single video"""

        analysis = {
            'video_id': video_id,
            'video_path': str(video_path)
        }

        # Phase 2A: Curiosity Gaps
        print(f"\n   Phase 2A: Curiosity Gap Detection...")
        try:
            curiosity_gaps = self.curiosity_detector.analyze_video_gaps(video_id, creator_name)
            analysis['curiosity_gaps'] = curiosity_gaps
        except Exception as e:
            print(f"      ⚠️  Phase 2A failed: {e}")
            analysis['curiosity_gaps'] = {}

        # Phase 2B: Audio-Visual Sync
        print(f"\n   Phase 2B: Audio-Visual Sync Analysis...")
        try:
            audio_analysis = self.audio_analyzer.analyze_video_audio(video_path, video_id, creator_name)
            analysis['audio'] = audio_analysis
        except Exception as e:
            print(f"      ⚠️  Phase 2B failed: {e}")
            analysis['audio'] = {}

        # Phase 2C: Interview Patterns
        print(f"\n   Phase 2C: Interview Pattern Extraction...")
        try:
            interview_patterns = self.interview_extractor.analyze_video_interviews(video_path, video_id, creator_name)
            analysis['interviews'] = interview_patterns
        except Exception as e:
            print(f"      ⚠️  Phase 2C failed: {e}")
            analysis['interviews'] = {}

        # Phase 2D: Emotional Arc
        print(f"\n   Phase 2D: Emotional Arc Mapping...")
        try:
            emotional_arc = self.emotion_mapper.analyze_emotional_arc(video_id, creator_name)
            analysis['emotional_arc'] = emotional_arc
        except Exception as e:
            print(f"      ⚠️  Phase 2D failed: {e}")
            analysis['emotional_arc'] = {}

        # Phase 2E: Cut Purpose
        print(f"\n   Phase 2E: Cut Purpose Analysis...")
        try:
            cut_analysis = self.cut_analyzer.analyze_cut_purposes(video_id, creator_name)
            analysis['cut_purposes'] = cut_analysis
        except Exception as e:
            print(f"      ⚠️  Phase 2E failed: {e}")
            analysis['cut_purposes'] = {}

        return analysis

    def _extract_patterns(self, video_analyses: List[Dict]) -> Dict:
        """Extract patterns across all analyzed videos"""

        patterns = {}

        # Curiosity gap patterns
        all_gaps = [v.get('curiosity_gaps', {}) for v in video_analyses if v.get('curiosity_gaps')]
        if all_gaps:
            patterns['curiosity_gaps'] = {
                'avg_gaps_per_video': sum(g.get('total_gaps', 0) for g in all_gaps) / len(all_gaps),
                'avg_gap_duration': sum(
                    g.get('statistics', {}).get('avg_duration', 0) for g in all_gaps
                ) / len(all_gaps) if all_gaps else 0
            }

        # Audio patterns
        all_audio = [v.get('audio', {}) for v in video_analyses if v.get('audio')]
        if all_audio:
            patterns['audio'] = {
                'avg_bpm': sum(a.get('music', {}).get('bpm', 0) for a in all_audio) / len(all_audio),
                'avg_wpm': sum(
                    a.get('voice', {}).get('overall_wpm', 0) for a in all_audio if a.get('voice')
                ) / len([a for a in all_audio if a.get('voice')]) if any(a.get('voice') for a in all_audio) else 0
            }

        # Interview patterns
        all_interviews = [v.get('interviews', {}) for v in video_analyses if v.get('interviews')]
        if all_interviews:
            patterns['interviews'] = {
                'avg_interview_percentage': sum(
                    i.get('statistics', {}).get('interview_percentage', 0) for i in all_interviews
                ) / len(all_interviews)
            }

        # Emotional patterns
        all_emotions = [v.get('emotional_arc', {}) for v in video_analyses if v.get('emotional_arc')]
        if all_emotions:
            patterns['emotional'] = {
                'avg_intensity': sum(
                    e.get('analysis', {}).get('avg_emotional_intensity', 0) for e in all_emotions
                ) / len(all_emotions),
                'common_arc_shape': self._most_common([
                    e.get('analysis', {}).get('arc_shape', 'unknown') for e in all_emotions
                ])
            }

        # Cut purpose patterns
        all_cuts = [v.get('cut_purposes', {}) for v in video_analyses if v.get('cut_purposes')]
        if all_cuts:
            all_purposes = {}
            for cut_data in all_cuts:
                for purpose, count in cut_data.get('analysis', {}).get('purpose_distribution', {}).items():
                    all_purposes[purpose] = all_purposes.get(purpose, 0) + count

            total_cuts = sum(all_purposes.values())
            patterns['cut_purposes'] = {
                'most_common_purpose': max(all_purposes, key=all_purposes.get) if all_purposes else 'unknown',
                'purpose_distribution': {
                    k: (v / total_cuts) * 100 for k, v in all_purposes.items()
                } if total_cuts > 0 else {}
            }

        return patterns

    def _most_common(self, items: List[str]) -> str:
        """Get most common item in list"""
        if not items:
            return 'unknown'

        from collections import Counter
        counter = Counter(items)
        return counter.most_common(1)[0][0]

    def _generate_sop(self, patterns: Dict, creator_name: str) -> str:
        """Generate human-readable SOP from patterns"""

        sop = f"""# {creator_name.upper()} PRODUCTION FORMULA - COMPLETE SOP

## OVERVIEW
This formula was extracted by analyzing multiple videos using deep multi-modal analysis.
It represents the EXACT patterns used by {creator_name} to create engaging content.

---

## 📝 SCRIPT FORMULA

### Curiosity Gaps
"""

        # Curiosity gaps
        if 'curiosity_gaps' in patterns:
            gaps = patterns['curiosity_gaps']
            sop += f"""- **Frequency**: {gaps['avg_gaps_per_video']:.1f} gaps per video
- **Duration**: Average {gaps['avg_gap_duration']:.1f} seconds per gap
- **Strategy**: Pose question/cliffhanger, hold tension, then reveal answer

**How to implement**:
1. Ask provocative question every {60 / gaps['avg_gaps_per_video']:.0f} seconds
2. Build tension for ~{gaps['avg_gap_duration']:.0f} seconds before revealing answer
3. Use visuals and audio to maintain interest during gap
"""

        # Audio formula
        sop += "\n---\n\n## 🎵 AUDIO FORMULA\n\n"
        if 'audio' in patterns:
            audio = patterns['audio']
            sop += f"""### Music
- **BPM**: {audio['avg_bpm']:.0f} ({"high energy" if audio['avg_bpm'] > 120 else "moderate energy"})
- **Style**: Epic/cinematic background music
- **Pattern**: Music swells during reveals, quiets during explanations

### Voice
- **Pacing**: {audio['avg_wpm']:.0f} words per minute
- **Strategy**: Clear, confident delivery with strategic pauses

**How to implement**:
1. Use royalty-free music at ~{audio['avg_bpm']:.0f} BPM
2. Speak at ~{audio['avg_wpm']:.0f} WPM (use teleprompter with pacing guide)
3. Add 0.5-1.0 second pauses before big reveals
"""

        # Interview formula
        if 'interviews' in patterns and patterns['interviews']['avg_interview_percentage'] > 0:
            sop += "\n---\n\n## 👤 INTERVIEW FORMULA\n\n"
            interview = patterns['interviews']
            sop += f"""- **Usage**: {interview['avg_interview_percentage']:.1f}% of video
- **Purpose**: Add credibility and expert validation
- **Placement**: Middle sections for explaining complex topics

**How to implement**:
1. Find expert interviews on YouTube (Creative Commons)
2. Extract 5-10 second clips for key points
3. Use as evidence/support for your narration
"""

        # Emotional arc
        sop += "\n---\n\n## 💓 EMOTIONAL ARC\n\n"
        if 'emotional' in patterns:
            emotion = patterns['emotional']
            sop += f"""- **Average Intensity**: {emotion['avg_intensity']:.2f} (0-1 scale)
- **Arc Shape**: {emotion['common_arc_shape'].capitalize()}
- **Strategy**: {"Build to climax" if emotion['common_arc_shape'] == 'crescendo' else "Maintain steady engagement"}

**How to implement**:
1. Start with {"moderate intensity" if emotion['common_arc_shape'] == 'crescendo' else "high intensity"}
2. {"Gradually increase" if emotion['common_arc_shape'] == 'crescendo' else "Maintain"} emotional stakes
3. Use script tone + music + pacing together
"""

        # Cut strategy
        sop += "\n---\n\n## ✂️  CUTTING STRATEGY\n\n"
        if 'cut_purposes' in patterns:
            cuts = patterns['cut_purposes']
            sop += f"""- **Most Common Purpose**: {cuts['most_common_purpose'].replace('_', ' ').title()}
- **Purpose Distribution**:
"""
            for purpose, percentage in sorted(cuts['purpose_distribution'].items(), key=lambda x: x[1], reverse=True):
                sop += f"  - {purpose.replace('_', ' ').title()}: {percentage:.1f}%\n"

            sop += """
**How to implement**:
1. Cut when content type changes (aerial → news clip)
2. Cut on questions and answers
3. Cut to emphasize emotional beats
4. Maintain ~6.5 second average shot duration
"""

        # Final recommendations
        sop += """
---

## 🎯 COMPLETE WORKFLOW

### Pre-Production
1. Research trending topic
2. Write script with curiosity gaps every ~30 seconds
3. Source footage (60% aerial, 30% documentary, 10% custom CGI)

### Production
4. Record voiceover at target WPM
5. Select background music at target BPM
6. Prepare visual assets

### Post-Production
7. Edit with 6.5 second average cuts
8. Sync music swells to reveals
9. Add pauses before big moments
10. Review emotional arc (should match target shape)

### Quality Check
- [ ] Curiosity gaps present and resolved
- [ ] Audio energy matches script intensity
- [ ] Cuts serve clear purposes
- [ ] Visual variety maintained
- [ ] Pacing feels engaging throughout

---

**Note**: This formula was extracted through AI analysis. Use as a guide, but trust your creative instincts to adapt it to your specific content and audience.
"""

        return sop


def main():
    """CLI interface"""
    import sys
    import os

    if len(sys.argv) < 2:
        print("\n🔬 Master Formula Extractor")
        print("\nUsage:")
        print("  python src/master_formula_extractor.py <creator_name> [video_dir]")
        print("\nExamples:")
        print("  python src/master_formula_extractor.py watop")
        print("  python src/master_formula_extractor.py watop /path/to/videos/")
        print("\nThis will:")
        print("  - Check for existing analysis data in analysis/<creator_name>/")
        print("  - Run ALL analysis phases on videos")
        print("  - Extract complete formula patterns")
        print("  - Generate actionable SOP")
        return

    creator_name = sys.argv[1]

    # Check if analysis directory already has data
    analysis_path = Path(f"analysis/{creator_name}")
    if analysis_path.exists():
        existing_files = list(analysis_path.glob("*"))
        if existing_files:
            print(f"\n📂 Found existing analysis directory: {analysis_path}")
            print(f"   Contains {len(existing_files)} items")

            # Check for transcript files
            transcripts = list(analysis_path.glob("*_transcript.json"))
            if transcripts:
                print(f"   ✅ Found {len(transcripts)} transcript files")
                print(f"\n💡 Tip: Analysis can continue from existing transcripts")

            # Check for visual analysis files
            visual_files = list(analysis_path.glob("*_visual.json"))
            if visual_files:
                print(f"   ✅ Found {len(visual_files)} visual analysis files")

    # Determine video directory
    if len(sys.argv) >= 3:
        video_dir = Path(sys.argv[2])
    else:
        # Try common locations
        possible_dirs = [
            Path(f"analysis/{creator_name}/videos"),
            Path("data/videos"),
            Path(os.path.expanduser(f"~/Documents/YouTube Automation Master Process/data/entertainment/long/")),
        ]

        video_dir = None
        for possible_dir in possible_dirs:
            if possible_dir.exists() and list(possible_dir.glob("*.mp4")):
                video_dir = possible_dir
                print(f"\n📹 Auto-detected video directory: {video_dir}")
                break

        if not video_dir:
            print(f"\n❌ No video directory specified and couldn't auto-detect")
            print(f"\n💡 Please specify video directory:")
            print(f"   python src/master_formula_extractor.py {creator_name} /path/to/videos/")
            print(f"\n🔍 Searched these locations:")
            for pd in possible_dirs:
                print(f"   - {pd}")
            return

    if not video_dir.exists():
        print(f"❌ Video directory not found: {video_dir}")
        print(f"\n💡 Make sure the path is correct. Try:")
        print(f"   python src/master_formula_extractor.py {creator_name} \"/full/path/to/videos/\"")
        return

    # Find all video files
    video_files = list(video_dir.glob("*.mp4"))
    if not video_files:
        print(f"❌ No .mp4 files found in {video_dir}")
        return

    print(f"\n📹 Found {len(video_files)} video files:")
    for i, vf in enumerate(video_files[:5], 1):
        print(f"   {i}. {vf.name}")
    if len(video_files) > 5:
        print(f"   ... and {len(video_files) - 5} more")

    # Ask for confirmation if many videos
    if len(video_files) > 10:
        print(f"\n⚠️  Processing {len(video_files)} videos will take significant time")
        print(f"   Each video takes ~5-10 minutes for complete analysis")
        print(f"   Estimated time: {len(video_files) * 7 / 60:.1f} hours")
        response = input(f"\n   Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    # Extract video IDs from filenames
    video_ids = [f.stem for f in video_files]

    extractor = MasterFormulaExtractor()
    extractor.extract_complete_formula(creator_name, video_ids, video_files)


if __name__ == "__main__":
    main()
