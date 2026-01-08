"""
Check Analysis Status
Quick utility to see what analysis data already exists

Usage:
    python src/check_analysis_status.py watop
"""

import json
from pathlib import Path
import sys


def check_status(creator_name: str):
    """Check what analysis data exists for a creator"""

    print(f"\n📊 ANALYSIS STATUS - {creator_name.upper()}")
    print("=" * 80)

    analysis_dir = Path(f"analysis/{creator_name}")

    if not analysis_dir.exists():
        print(f"❌ No analysis directory found: {analysis_dir}")
        print(f"\n💡 Run Phase 1 first to download videos and extract data:")
        print(f"   python src/phase1_analyzer.py {creator_name}")
        return

    print(f"✅ Analysis directory exists: {analysis_dir}\n")

    # Count different file types
    transcripts = list(analysis_dir.glob("*_transcript.json"))
    visual_files = list(analysis_dir.glob("*_visual.json"))
    curiosity_files = list(analysis_dir.glob("*_curiosity.json"))
    audio_files = list(analysis_dir.glob("*_audio.json"))
    interview_files = list(analysis_dir.glob("*_interviews.json"))
    emotion_files = list(analysis_dir.glob("*_emotions.json"))
    cut_files = list(analysis_dir.glob("*_cuts.json"))

    # Check for formula
    formula_file = analysis_dir / "complete_formula.json"
    sop_file = analysis_dir / "FORMULA_SOP.md"

    # Print status
    print("📝 PHASE 1 - Data Extraction:")
    print(f"   Transcripts: {len(transcripts)} files")
    print(f"   Visual Analysis: {len(visual_files)} files")

    if transcripts:
        print(f"\n   Sample transcripts:")
        for t in transcripts[:3]:
            print(f"   - {t.name}")
        if len(transcripts) > 3:
            print(f"   ... and {len(transcripts) - 3} more")

    print(f"\n📊 PHASE 2 - Deep Analysis:")
    print(f"   Curiosity Gaps: {len(curiosity_files)} files")
    print(f"   Audio Analysis: {len(audio_files)} files")
    print(f"   Interviews: {len(interview_files)} files")
    print(f"   Emotional Arcs: {len(emotion_files)} files")
    print(f"   Cut Purposes: {len(cut_files)} files")

    print(f"\n🎯 MASTER FORMULA:")
    if formula_file.exists():
        print(f"   ✅ Complete formula extracted!")
        print(f"      File: {formula_file}")

        # Load and show summary
        with open(formula_file, 'r') as f:
            data = json.load(f)
            print(f"      Videos analyzed: {data.get('total_videos', 0)}")

    else:
        print(f"   ❌ Not yet extracted")

    if sop_file.exists():
        print(f"   ✅ SOP document generated!")
        print(f"      File: {sop_file}")
    else:
        print(f"   ❌ SOP not yet generated")

    # Determine what to do next
    print(f"\n{'='*80}")
    print("🎯 NEXT STEPS:")
    print("=" * 80)

    if not transcripts:
        print("\n1️⃣  Run Phase 1 to download videos and extract transcripts:")
        print(f"   python src/phase1_analyzer.py {creator_name}")

    elif not visual_files:
        print("\n1️⃣  Run Phase 1C to analyze visuals:")
        print(f"   python src/phase1c_visual_analyzer.py {creator_name}")

    elif not formula_file.exists():
        print("\n1️⃣  Run Master Formula Extractor to get complete analysis:")
        print(f"   python src/master_formula_extractor.py {creator_name}")
        print(f"\n   This will analyze all {len(transcripts)} videos and extract the formula")

    else:
        print("\n✅ Analysis complete! Check your results:")
        print(f"   cat {sop_file}")
        print(f"\n💡 To analyze more videos, add them to the videos directory and re-run:")
        print(f"   python src/master_formula_extractor.py {creator_name}")

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n📊 Check Analysis Status")
        print("\nUsage:")
        print("  python src/check_analysis_status.py <creator_name>")
        print("\nExample:")
        print("  python src/check_analysis_status.py watop")
        sys.exit(1)

    check_status(sys.argv[1])
