"""
Sound Effects Library Setup
Downloads free SFX for WATOP-style videos
"""

import requests
from pathlib import Path
import time


class SFXLibrarySetup:
    """Sets up free sound effects library"""

    # Free SFX sources
    FREE_SFX_SOURCES = {
        "freesound.org": "Requires API key (free)",
        "zapsplat.com": "Free with attribution",
        "mixkit.co": "Royalty-free",
        "soundbible.com": "Public domain"
    }

    RECOMMENDED_SFX = {
        "impact": [
            "deep_impact.mp3",
            "explosion.mp3",
            "crash.mp3",
            "thud.mp3"
        ],
        "whoosh": [
            "fast_whoosh.mp3",
            "swish.mp3",
            "flyby.mp3"
        ],
        "rumble": [
            "deep_rumble.mp3",
            "bass_hit.mp3",
            "sub_bass.mp3"
        ],
        "shimmer": [
            "chime.mp3",
            "sparkle.mp3",
            "glitter.mp3"
        ],
        "tension": [
            "drone.mp3",
            "suspense.mp3",
            "build_up.mp3"
        ],
        "reveal": [
            "rise.mp3",
            "crescendo.mp3",
            "reveal.mp3"
        ],
        "countdown": [
            "tick.mp3",
            "beep.mp3",
            "countdown.mp3"
        ],
        "science": [
            "digital_beep.mp3",
            "computer.mp3",
            "tech.mp3"
        ]
    }

    def __init__(self):
        self.output_dir = Path("assets/sfx")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_download_guide(self):
        """Create guide for downloading SFX"""

        guide_file = self.output_dir / "SFX_DOWNLOAD_GUIDE.txt"

        with open(guide_file, 'w') as f:
            f.write("SOUND EFFECTS LIBRARY SETUP GUIDE\n")
            f.write("="*80 + "\n\n")

            f.write("WATOP-style videos need constant sound effects (every 2-3 seconds).\n")
            f.write("This guide helps you build a free SFX library.\n\n")

            f.write("="*80 + "\n")
            f.write("FREE SFX SOURCES\n")
            f.write("="*80 + "\n\n")

            f.write("1. **Mixkit.co** (EASIEST - No signup required)\n")
            f.write("   URL: https://mixkit.co/free-sound-effects/\n")
            f.write("   - Search for each effect type below\n")
            f.write("   - Download MP3 files\n")
            f.write("   - Save to: assets/sfx/\n\n")

            f.write("2. **Zapsplat.com** (Large library)\n")
            f.write("   URL: https://www.zapsplat.com/\n")
            f.write("   - Free signup required\n")
            f.write("   - Must credit in video description (free license)\n\n")

            f.write("3. **Freesound.org** (Massive library)\n")
            f.write("   URL: https://freesound.org/\n")
            f.write("   - Free signup required\n")
            f.write("   - Check license (most are CC0 - public domain)\n\n")

            f.write("="*80 + "\n")
            f.write("REQUIRED SOUND EFFECTS\n")
            f.write("="*80 + "\n\n")

            f.write("Download at least 3-5 variations of each type:\n\n")

            for sfx_type, examples in self.RECOMMENDED_SFX.items():
                f.write(f"## {sfx_type.upper()}\n")
                f.write(f"   Search terms: {sfx_type}, ")
                if sfx_type == "impact":
                    f.write("explosion, crash, thud, hit\n")
                elif sfx_type == "whoosh":
                    f.write("swish, flyby, pass, wind\n")
                elif sfx_type == "rumble":
                    f.write("bass, deep, sub, low frequency\n")
                elif sfx_type == "shimmer":
                    f.write("chime, sparkle, twinkle, magic\n")
                elif sfx_type == "tension":
                    f.write("suspense, drone, build, dark\n")
                elif sfx_type == "reveal":
                    f.write("rise, crescendo, build up, epic\n")
                elif sfx_type == "countdown":
                    f.write("tick, beep, timer, clock\n")
                elif sfx_type == "science":
                    f.write("tech, digital, computer, futuristic\n")

                f.write(f"   Save as: assets/sfx/{sfx_type}_*.mp3\n\n")

            f.write("="*80 + "\n")
            f.write("QUICK START (15 minutes)\n")
            f.write("="*80 + "\n\n")

            f.write("Minimal SFX pack (20 files):\n\n")

            f.write("1. Go to: https://mixkit.co/free-sound-effects/\n\n")

            f.write("2. Search and download:\n")
            f.write("   - 'whoosh' → Download 5 different whoosh sounds\n")
            f.write("   - 'impact' → Download 5 impact/hit sounds\n")
            f.write("   - 'bass drop' → Download 3 bass/rumble sounds\n")
            f.write("   - 'chime' → Download 3 shimmer sounds\n")
            f.write("   - 'rise' → Download 4 rise/reveal sounds\n\n")

            f.write("3. Save all to: assets/sfx/\n\n")

            f.write("4. Rename for clarity:\n")
            f.write("   whoosh_1.mp3, whoosh_2.mp3, ...\n")
            f.write("   impact_1.mp3, impact_2.mp3, ...\n")
            f.write("   etc.\n\n")

            f.write("="*80 + "\n")
            f.write("ADVANCED: YouTube Audio Library (100% Safe)\n")
            f.write("="*80 + "\n\n")

            f.write("YouTube's own library (no copyright issues):\n\n")

            f.write("1. Go to: https://www.youtube.com/audiolibrary\n")
            f.write("2. Click 'Sound Effects' tab\n")
            f.write("3. Filter by 'Genre' → Cinematic, Sci-Fi\n")
            f.write("4. Download sound effects\n")
            f.write("5. Save to assets/sfx/\n\n")

            f.write("="*80 + "\n")
            f.write("VERIFY SETUP\n")
            f.write("="*80 + "\n\n")

            f.write("After downloading, run:\n")
            f.write("  python src/production/sfx_library_setup.py verify\n\n")

            f.write("This will check you have enough SFX for production.\n\n")

            f.write("MINIMUM REQUIREMENT:\n")
            f.write("  - At least 20 SFX files total\n")
            f.write("  - At least 3 files per category\n\n")

        print(f"✅ SFX Download Guide created: {guide_file}")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Open: {guide_file}")
        print(f"2. Follow 'QUICK START' section (15 minutes)")
        print(f"3. Download 20+ SFX files from Mixkit.co")
        print(f"4. Save to: assets/sfx/")
        print(f"5. Run: python src/production/sfx_library_setup.py verify")

        return guide_file

    def verify_library(self):
        """Verify SFX library is set up"""

        sfx_files = list(self.output_dir.glob("*.mp3")) + list(self.output_dir.glob("*.wav"))

        print(f"\n🔊 SFX LIBRARY VERIFICATION")
        print(f"{'='*60}")
        print(f"Location: {self.output_dir}")
        print(f"Total files: {len(sfx_files)}")

        if len(sfx_files) == 0:
            print(f"\n❌ NO SFX FILES FOUND!")
            print(f"\nPlease download SFX:")
            print(f"1. Run: python src/production/sfx_library_setup.py guide")
            print(f"2. Follow the guide to download free SFX")
            return False

        elif len(sfx_files) < 20:
            print(f"\n⚠️  FEW SFX FILES ({len(sfx_files)} found)")
            print(f"   Recommended: 20+ files for variety")
            print(f"   Current files:")
            for f in sfx_files:
                print(f"     - {f.name}")

        else:
            print(f"\n✅ LIBRARY READY!")
            print(f"   {len(sfx_files)} SFX files available")

        # Categorize
        categories = {
            "whoosh": 0,
            "impact": 0,
            "rumble": 0,
            "shimmer": 0,
            "tension": 0,
            "reveal": 0
        }

        for file in sfx_files:
            name_lower = file.name.lower()
            for category in categories:
                if category in name_lower:
                    categories[category] += 1

        print(f"\n📊 BY CATEGORY:")
        for category, count in categories.items():
            status = "✅" if count >= 3 else "⚠️ "
            print(f"   {status} {category}: {count} files")

        return len(sfx_files) >= 20


def main():
    """CLI interface"""
    import sys

    setup = SFXLibrarySetup()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "guide":
            setup.create_download_guide()

        elif command == "verify":
            setup.verify_library()

        else:
            print("❌ Unknown command. Use: guide or verify")

    else:
        print("🔊 SFX Library Setup")
        print("\nCommands:")
        print("  python src/production/sfx_library_setup.py guide   - Create download guide")
        print("  python src/production/sfx_library_setup.py verify  - Verify library setup")
        print("\nQuick start:")
        print("  python src/production/sfx_library_setup.py guide")


if __name__ == "__main__":
    main()
