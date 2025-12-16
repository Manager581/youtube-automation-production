"""
NASA Footage Downloader
Automatically downloads space footage from NASA public domain sources
"""

import requests
import json
import yaml
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import time


class NASADownloader:
    """Downloads footage from NASA Image and Video Library"""

    NASA_API = "https://images-api.nasa.gov"

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path("assets/nasa_footage")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def search_nasa(self, query, media_type="video", count=30):
        """Search NASA Image Library"""

        print(f"\n🔍 Searching NASA for: '{query}'")

        url = f"{self.NASA_API}/search"
        params = {
            "q": query,
            "media_type": media_type,
            "page_size": count
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'collection' in data and 'items' in data['collection']:
                items = data['collection']['items']
                print(f"✅ Found {len(items)} results")
                return items
            else:
                print(f"⚠️  No results found")
                return []

        except Exception as e:
            print(f"❌ Error searching NASA: {e}")
            return []

    def get_download_url(self, nasa_id):
        """Get actual download URL for a NASA asset"""

        url = f"{self.NASA_API}/asset/{nasa_id}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'collection' in data and 'items' in data['collection']:
                items = data['collection']['items']

                # Find the best quality video
                video_urls = [item['href'] for item in items if 'mp4' in item['href'].lower()]

                if video_urls:
                    # Prefer higher quality (larger files usually better quality)
                    return video_urls[0]

            return None

        except Exception as e:
            print(f"❌ Error getting asset URL: {e}")
            return None

    def download_file(self, url, filename):
        """Download file from URL"""

        output_path = self.output_dir / filename

        if output_path.exists():
            print(f"⏭️  Skipping (already exists): {filename}")
            return str(output_path)

        print(f"⬇️  Downloading: {filename}")

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"   Progress: {progress:.1f}%", end='\r')

            print(f"\n✅ Downloaded: {filename}")
            return str(output_path)

        except Exception as e:
            print(f"❌ Error downloading: {e}")
            if output_path.exists():
                output_path.unlink()  # Remove partial file
            return None

    def download_for_topic(self, topic_keywords, num_videos=10):
        """Download videos for a specific topic"""

        # Split keywords if multiple provided
        keywords = [kw.strip() for kw in topic_keywords.split(',')]

        all_downloads = []

        for keyword in keywords:
            print(f"\n{'='*60}")
            print(f"Searching for: {keyword}")
            print(f"{'='*60}")

            results = self.search_nasa(keyword, media_type="video", count=num_videos)

            for i, item in enumerate(results[:num_videos]):
                try:
                    data = item['data'][0]
                    nasa_id = data['nasa_id']
                    title = data.get('title', 'untitled')

                    print(f"\n[{i+1}/{len(results[:num_videos])}] {title}")

                    # Get download URL
                    download_url = self.get_download_url(nasa_id)

                    if download_url:
                        # Create safe filename
                        safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (' ', '-', '_'))
                        filename = f"{keyword.replace(' ', '_')}_{i+1:02d}_{safe_title}.mp4"

                        # Download
                        filepath = self.download_file(download_url, filename)

                        if filepath:
                            all_downloads.append({
                                "keyword": keyword,
                                "title": title,
                                "nasa_id": nasa_id,
                                "filepath": filepath,
                                "url": download_url,
                                "downloaded_at": datetime.now().isoformat()
                            })

                        # Rate limiting
                        time.sleep(1)

                except Exception as e:
                    print(f"⚠️  Skipping item: {e}")
                    continue

        # Save manifest
        manifest_file = self.output_dir / f"manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(manifest_file, 'w') as f:
            json.dump({
                "topic": topic_keywords,
                "downloaded_at": datetime.now().isoformat(),
                "total_downloads": len(all_downloads),
                "files": all_downloads
            }, f, indent=2)

        print(f"\n{'='*60}")
        print(f"✅ DOWNLOAD COMPLETE")
        print(f"{'='*60}")
        print(f"Total Downloads: {len(all_downloads)}")
        print(f"Saved to: {self.output_dir}")
        print(f"Manifest: {manifest_file}")

        return all_downloads

    def download_from_script(self, script_file):
        """Extract keywords from script and download relevant footage"""

        with open(script_file, 'r') as f:
            script_content = f.read()

        # Extract [SHOW: ...] cues as keywords
        import re
        show_cues = re.findall(r'\[SHOW:(.*?)\]', script_content, re.IGNORECASE)

        # Extract key space-related terms
        space_keywords = [
            "black hole", "nebula", "galaxy", "planet", "star", "asteroid",
            "ISS", "space station", "mars", "moon", "earth from space",
            "supernova", "comet", "meteor", "solar system", "milky way"
        ]

        # Find which keywords appear in script
        keywords_found = []
        script_lower = script_content.lower()

        for kw in space_keywords:
            if kw in script_lower:
                keywords_found.append(kw)

        # Combine with SHOW cues
        all_keywords = list(set(keywords_found + [cue.strip()[:30] for cue in show_cues[:5]]))

        print(f"\n📝 Analyzing script: {Path(script_file).name}")
        print(f"   Keywords found: {', '.join(all_keywords[:10])}")

        if not all_keywords:
            print("⚠️  No space keywords found in script")
            return []

        # Download footage for each keyword (limited amount per keyword)
        downloads = []
        for keyword in all_keywords[:10]:  # Limit to 10 keywords
            results = self.download_for_topic(keyword, num_videos=3)
            downloads.extend(results)
            time.sleep(2)  # Rate limiting between keywords

        return downloads


def main():
    """CLI interface"""
    import sys

    downloader = NASADownloader()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "search":
            if len(sys.argv) < 3:
                print("❌ Usage: python src/production/nasa_downloader.py search '<keywords>'")
                return
            keywords = sys.argv[2]
            num_videos = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            downloader.download_for_topic(keywords, num_videos)

        elif command == "script":
            if len(sys.argv) < 3:
                print("❌ Usage: python src/production/nasa_downloader.py script <script_file>")
                return
            downloader.download_from_script(sys.argv[2])

        else:
            print("❌ Unknown command. Use: search or script")

    else:
        print("🚀 NASA Footage Downloader")
        print("\nCommands:")
        print("  python src/production/nasa_downloader.py search '<keywords>' [num_videos]")
        print("  python src/production/nasa_downloader.py script <script_file>")
        print("\nExamples:")
        print("  python src/production/nasa_downloader.py search 'black hole, nebula' 15")
        print("  python src/production/nasa_downloader.py script scripts/drafts/black_holes.md")
        print("\nPopular keywords:")
        print("  - 'black hole'  - 'nebula'  - 'ISS'")
        print("  - 'mars'        - 'galaxy'  - 'earth from space'")
        print("  - 'asteroid'    - 'moon'    - 'spacewalk'")


if __name__ == "__main__":
    main()
