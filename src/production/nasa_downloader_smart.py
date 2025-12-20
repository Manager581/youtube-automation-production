"""
Smart NASA Footage Downloader for Scripts
Automatically downloads relevant NASA footage based on script content
"""

import requests
import json
from pathlib import Path
import time
import re


class SmartNASADownloader:
    """Downloads NASA footage based on script keywords"""

    NASA_API = "https://images-api.nasa.gov"

    # Search queries for space topics
    NASA_SEARCH_QUERIES = {
        'betelgeuse': ['betelgeuse star', 'red supergiant', 'orion constellation'],
        'supernova': ['supernova explosion', 'stellar explosion', 'star death'],
        'nebula': ['nebula', 'star formation', 'emission nebula'],
        'galaxy': ['spiral galaxy', 'milky way galaxy', 'andromeda galaxy'],
        'black_hole': ['black hole', 'event horizon', 'accretion disk'],
        'earth': ['earth from space', 'earth orbit', 'ISS earth view'],
        'mars': ['mars surface', 'mars rover', 'mars landscape'],
        'jupiter': ['jupiter', 'jupiter storms', 'great red spot'],
        'sun': ['sun', 'solar flare', 'sun surface'],
        'solar_system': ['solar system', 'planets orbit', 'inner planets'],
        'hubble': ['hubble telescope', 'hubble images', 'hubble deep field'],
        'james_webb': ['james webb telescope', 'jwst', 'webb telescope'],
        'space_general': ['deep space', 'cosmos', 'universe', 'astronomy'],
    }

    def __init__(self):
        self.output_dir = Path("assets/nasa_footage")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.output_dir / "download_metadata.json"
        self.downloaded = self._load_metadata()

    def _load_metadata(self):
        """Load metadata of previously downloaded files"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save download metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.downloaded, f, indent=2)

    def analyze_script_keywords(self, script_file):
        """Analyze script to determine which NASA searches to run"""

        with open(script_file, 'r') as f:
            script_content = f.read().lower()

        relevant_searches = []

        for topic, queries in self.NASA_SEARCH_QUERIES.items():
            # Check if topic keywords appear in script
            topic_keywords = topic.replace('_', ' ').split()
            if any(keyword in script_content for keyword in topic_keywords):
                relevant_searches.extend(queries)

        # Remove duplicates while preserving order
        seen = set()
        unique_searches = []
        for query in relevant_searches:
            if query not in seen:
                seen.add(query)
                unique_searches.append(query)

        return unique_searches[:15]  # Limit to 15 searches

    def search_nasa(self, query, media_type="image", count=20):
        """Search NASA Image Library"""

        print(f"  🔍 Searching: '{query}'")

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
                print(f"     Found {len(items)} results")
                return items
            else:
                print(f"     No results")
                return []

        except Exception as e:
            print(f"     Error: {e}")
            return []

    def get_image_url(self, item):
        """Extract high-res image URL from NASA item"""

        try:
            nasa_id = item['data'][0]['nasa_id']

            # Get asset manifest
            asset_url = f"{self.NASA_API}/asset/{nasa_id}"
            response = requests.get(asset_url, timeout=30)
            data = response.json()

            if 'collection' in data and 'items' in data['collection']:
                # Find highest resolution image
                image_urls = [
                    item['href'] for item in data['collection']['items']
                    if any(ext in item['href'].lower() for ext in ['.jpg', '.png', '.jpeg'])
                ]

                if image_urls:
                    # Prefer medium/large images (orig images often blocked)
                    large = [url for url in image_urls if 'large' in url.lower()]
                    medium = [url for url in image_urls if 'medium' in url.lower()]

                    if large:
                        return large[0]
                    elif medium:
                        return medium[0]
                    else:
                        # Filter out 'orig' as they're often blocked
                        non_orig = [url for url in image_urls if 'orig' not in url.lower()]
                        return non_orig[0] if non_orig else image_urls[0]

            return None

        except Exception as e:
            return None

    def download_image(self, url, filename, metadata):
        """Download image from URL"""

        output_path = self.output_dir / filename

        if output_path.exists():
            return str(output_path)

        try:
            # Convert HTTP to HTTPS (NASA CDN requires HTTPS)
            if url.startswith('http://'):
                url = url.replace('http://', 'https://', 1)

            # Add browser headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://images.nasa.gov/'
            }
            response = requests.get(url, stream=True, timeout=60, headers=headers)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Save metadata
            self.downloaded[filename] = metadata
            self._save_metadata()

            return str(output_path)

        except Exception as e:
            print(f"     ❌ Download failed: {e}")
            return None

    def download_for_script(self, script_file, total_clips=100):
        """Download NASA images for a script"""

        script_name = Path(script_file).stem

        print(f"\n🚀 NASA FOOTAGE DOWNLOADER")
        print("=" * 80)
        print(f"Script: {script_name}")
        print(f"Target: {total_clips} images\n")

        # Analyze script for relevant searches
        searches = self.analyze_script_keywords(script_file)

        print(f"📋 Running {len(searches)} targeted searches:\n")

        downloaded_files = []
        clips_per_search = max(5, total_clips // len(searches))

        for query in searches:
            # Search for images (faster to work with than videos)
            results = self.search_nasa(query, media_type="image", count=clips_per_search)

            for i, item in enumerate(results):
                if len(downloaded_files) >= total_clips:
                    break

                try:
                    # Get metadata
                    title = item['data'][0].get('title', 'Untitled')
                    nasa_id = item['data'][0]['nasa_id']
                    description = item['data'][0].get('description', '')

                    # Get image URL
                    image_url = self.get_image_url(item)

                    if image_url:
                        # Create filename
                        filename = f"nasa_{len(downloaded_files)+1:03d}_{nasa_id}.jpg"

                        # Download
                        filepath = self.download_image(
                            image_url,
                            filename,
                            {
                                'title': title,
                                'description': description[:200],
                                'nasa_id': nasa_id,
                                'query': query,
                                'url': image_url
                            }
                        )

                        if filepath:
                            downloaded_files.append(filepath)
                            print(f"     ✅ {len(downloaded_files)}/{total_clips}: {title[:50]}")

                        time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    continue

            if len(downloaded_files) >= total_clips:
                break

        print(f"\n{'='*80}")
        print(f"✅ DOWNLOAD COMPLETE!")
        print(f"{'='*80}")
        print(f"Downloaded: {len(downloaded_files)} images")
        print(f"Location: {self.output_dir.absolute()}")
        print(f"\n💡 NEXT STEPS:")
        print(f"1. Images will be used with Ken Burns effects (zoom/pan)")
        print(f"2. Each 5-8 second clip = slow zoom on high-res NASA image")
        print(f"3. Creates WATOP-style visual variety without manual Veo work")
        print(f"4. Run: python src/watop_pipeline.py {script_file} <voiceover_file>\n")

        return downloaded_files


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\nUsage: python src/production/nasa_downloader_smart.py <script_file> [clip_count]")
        print("\nExample:")
        print("  python src/production/nasa_downloader_smart.py scripts/drafts/betelgeuse.md 100")
        return

    script_file = sys.argv[1]
    clip_count = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    downloader = SmartNASADownloader()
    downloader.download_for_script(script_file, total_clips=clip_count)


if __name__ == "__main__":
    main()
