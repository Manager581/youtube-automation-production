"""
Automated SFX Downloader using Freesound API
Downloads royalty-free sound effects for WATOP-style videos
"""

import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv


class AutoSFXDownloader:
    """Automatically downloads SFX from Freesound.org"""

    # SFX categories we need for WATOP-style videos
    SFX_CATEGORIES = {
        "whoosh": {
            "query": "whoosh swish fast",
            "count": 5,
            "tags": ["whoosh", "swish", "transition"]
        },
        "impact": {
            "query": "impact hit boom",
            "count": 5,
            "tags": ["impact", "hit", "boom"]
        },
        "rumble": {
            "query": "bass rumble deep",
            "count": 3,
            "tags": ["bass", "rumble", "low"]
        },
        "shimmer": {
            "query": "chime sparkle magic",
            "count": 3,
            "tags": ["chime", "sparkle", "magic"]
        },
        "tension": {
            "query": "drone suspense dark",
            "count": 2,
            "tags": ["drone", "suspense", "tension"]
        },
        "reveal": {
            "query": "rise crescendo epic",
            "count": 3,
            "tags": ["rise", "crescendo", "reveal"]
        },
        "science": {
            "query": "beep tech digital futuristic",
            "count": 3,
            "tags": ["tech", "digital", "sci-fi"]
        }
    }

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("FREESOUND_API_KEY")

        if not self.api_key:
            raise ValueError("FREESOUND_API_KEY not found in .env file")

        self.output_dir = Path("assets/sfx")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = "https://freesound.org/apiv2"
        self.headers = {"Authorization": f"Token {self.api_key}"}

    def search_sounds(self, query, count=5):
        """Search for sounds on Freesound"""

        url = f"{self.base_url}/search/text/"
        params = {
            "query": query,
            "filter": "duration:[0 TO 3] type:mp3",  # Short clips, MP3 only
            "sort": "downloads_desc",  # Most downloaded = best quality
            "fields": "id,name,previews,download,license,username",
            "page_size": count * 2  # Get extra in case some fail
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            return response.json()['results']
        else:
            print(f"❌ Search failed: {response.status_code}")
            return []

    def download_sound(self, sound_id, sound_name, category, index):
        """Download a specific sound file"""

        # Clean filename
        safe_name = f"{category}_{index:02d}.mp3"
        output_path = self.output_dir / safe_name

        # Skip if already exists
        if output_path.exists():
            print(f"   ⏭️  {safe_name} already exists, skipping")
            return True

        # Get download URL
        url = f"{self.base_url}/sounds/{sound_id}/download/"

        try:
            response = requests.get(url, headers=self.headers, stream=True)

            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"   ✅ Downloaded: {safe_name}")
                return True
            else:
                print(f"   ❌ Download failed for {safe_name}: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ Error downloading {safe_name}: {e}")
            return False

    def download_all(self):
        """Download all required SFX"""

        print(f"\n🔊 AUTOMATED SFX DOWNLOADER")
        print(f"="*60)
        print(f"Downloading to: {self.output_dir.absolute()}\n")

        total_downloaded = 0

        for category, config in self.SFX_CATEGORIES.items():
            print(f"\n📂 Category: {category.upper()}")
            print(f"   Searching for: '{config['query']}'")

            # Search for sounds
            results = self.search_sounds(config['query'], config['count'])

            if not results:
                print(f"   ⚠️  No results found for {category}")
                continue

            # Download sounds
            downloaded = 0
            for i, sound in enumerate(results):
                if downloaded >= config['count']:
                    break

                # Most Freesound content is safe to use - we'll download and check later
                # Only skip obviously restricted licenses
                license_name = sound.get('license', 'Unknown')

                print(f"   📝 Found: {sound['name'][:40]}... (license: {license_name})")

                # Skip only if explicitly non-commercial restricted
                if 'NonCommercial' in license_name or 'Sampling' in license_name:
                    print(f"   ⏭️  Skipping (non-commercial license)")
                    continue

                success = self.download_sound(
                    sound['id'],
                    sound['name'],
                    category,
                    downloaded + 1
                )

                if success:
                    downloaded += 1
                    total_downloaded += 1

                # Rate limiting (Freesound allows 60 requests/min)
                time.sleep(1.5)

        print(f"\n{'='*60}")
        print(f"✅ DOWNLOAD COMPLETE!")
        print(f"{'='*60}")
        print(f"Total SFX downloaded: {total_downloaded}")
        print(f"Location: {self.output_dir.absolute()}\n")

        # Verify library
        self.verify_library()

        return total_downloaded

    def verify_library(self):
        """Verify SFX library is ready"""

        sfx_files = list(self.output_dir.glob("*.mp3")) + list(self.output_dir.glob("*.wav"))

        print(f"\n📊 LIBRARY STATUS:")
        print(f"Total files: {len(sfx_files)}")

        if len(sfx_files) >= 20:
            print(f"✅ Library ready for production!")
        elif len(sfx_files) >= 10:
            print(f"⚠️  Library usable but limited ({len(sfx_files)} files)")
            print(f"   Recommended: 20+ files for variety")
        else:
            print(f"❌ Not enough SFX files ({len(sfx_files)} found)")
            print(f"   Minimum: 10 files, Recommended: 20+")

        # Show breakdown by category
        categories = {}
        for file in sfx_files:
            category = file.stem.split('_')[0]
            categories[category] = categories.get(category, 0) + 1

        print(f"\n📂 BY CATEGORY:")
        for category, count in sorted(categories.items()):
            print(f"   {category}: {count} files")


def main():
    """CLI interface"""
    import sys

    print("\n🎵 Automated SFX Downloader for YouTube Automation")
    print("="*60)

    try:
        downloader = AutoSFXDownloader()

        if len(sys.argv) > 1 and sys.argv[1] == "verify":
            downloader.verify_library()
        else:
            print("\nThis will download 20+ royalty-free sound effects from Freesound.org")
            print("Estimated time: 2-3 minutes")
            print("\nPress Ctrl+C to cancel, or wait 3 seconds to start...\n")

            time.sleep(3)

            downloader.download_all()

            print("\n🎉 SFX library setup complete!")
            print("\nNext steps:")
            print("  1. Run: python src/content/topic_generator.py generate 20")
            print("  2. Pick a topic and generate script")
            print("  3. Continue with video production workflow\n")

    except KeyboardInterrupt:
        print("\n\n❌ Download cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your .env file has FREESOUND_API_KEY")
        print("  2. Verify API key is valid at https://freesound.org/apiv2/apply")
        print("  3. Check internet connection")


if __name__ == "__main__":
    main()
