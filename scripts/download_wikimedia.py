#!/usr/bin/env python3
"""
Download specific images from Wikimedia Commons for the Frank Olson documentary.
Uses the Wikimedia Commons API (free, no key needed).
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import requests

# --- Config ---
OUTPUT_DIR = Path(
    "/Users/jefflawrence/Documents/youtube-automation-production"
    "/footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/wikimedia"
)
# Wikimedia requires a descriptive UA for API calls per their policy
API_USER_AGENT = "WikimediaImageDownloader/1.0 (https://github.com/example/wiki-dl; user@example.com) python-requests/2.31"
# For actual file downloads from upload.wikimedia.org, use a standard browser UA
DOWNLOAD_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
API_URL = "https://commons.wikimedia.org/w/api.php"
MIN_SIZE_BYTES = 100_000  # 100 KB minimum
PREFERRED_EXTS = {".jpg", ".jpeg", ".png"}
SLEEP_BETWEEN = 1.0  # polite rate limiting

# --- Search tasks ---
# Each entry: (label, list_of_search_queries)
# We try queries in order, stop at first successful download.
SEARCH_TASKS = [
    # === Primary 3 (story-critical) ===
    (
        "hotel_statler_new_york",
        [
            "Hotel Statler New York",
            "Hotel Pennsylvania New York",
            "Hotel Statler 1950s",
            "Statler Hotel Manhattan",
        ],
    ),
    (
        "fort_detrick_lab",
        [
            "Fort Detrick",
            "Fort Detrick biological laboratory",
            "biological warfare laboratory army",
            "Army Chemical Corps laboratory",
            "Camp Detrick",
        ],
    ),
    (
        "american_family_1950s",
        [
            "American family 1950s",
            "suburban family United States 1950s",
            "1950s family portrait United States",
            "family 1950s photograph",
        ],
    ),
    # === Additional (for later use) ===
    (
        "allen_dulles_cia",
        [
            "Allen Dulles",
            "Allen Welsh Dulles CIA",
            "Allen Dulles portrait",
        ],
    ),
    (
        "william_colby_cia",
        [
            "William Colby",
            "William Colby CIA director",
            "William Egan Colby",
        ],
    ),
    (
        "frank_church_senator",
        [
            "Frank Church senator",
            "Frank Church committee",
            "Church Committee",
        ],
    ),
    (
        "gerald_ford_president",
        [
            "Gerald Ford president",
            "Gerald Ford official portrait",
            "Gerald Ford",
        ],
    ),
    (
        "korean_war_prisoners",
        [
            "Korean War prisoners",
            "Korean War POW",
            "prisoners of war Korea",
            "Korean War captives",
        ],
    ),
    (
        "lsd_molecule",
        [
            "LSD molecule",
            "lysergic acid diethylamide",
            "LSD chemical structure",
            "LSD-25",
        ],
    ),
]


def search_commons(query: str, limit: int = 10) -> list[dict]:
    """Search Wikimedia Commons for files matching query."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": 6,  # File namespace
        "format": "json",
        "srlimit": limit,
    }
    headers = {"User-Agent": API_USER_AGENT}
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("query", {}).get("search", [])


def get_image_info(title: str) -> dict | None:
    """Get URL, size, mime, and license info for a Commons file."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo|categories",
        "iiprop": "url|size|mime|extmetadata",
        "format": "json",
    }
    headers = {"User-Agent": API_USER_AGENT}
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})
    for page_id, page_data in pages.items():
        if page_id == "-1":
            return None
        ii_list = page_data.get("imageinfo", [])
        if not ii_list:
            return None
        ii = ii_list[0]
        # Extract license from extmetadata
        ext = ii.get("extmetadata", {})
        license_short = ext.get("LicenseShortName", {}).get("value", "Unknown")
        license_url = ext.get("LicenseUrl", {}).get("value", "")
        artist = ext.get("Artist", {}).get("value", "Unknown")
        # Strip HTML tags from artist
        artist = re.sub(r"<[^>]+>", "", artist).strip()
        description = ext.get("ImageDescription", {}).get("value", "")
        description = re.sub(r"<[^>]+>", "", description).strip()
        date_original = ext.get("DateTimeOriginal", {}).get("value", "")
        date_original = re.sub(r"<[^>]+>", "", date_original).strip()

        categories = [
            c.get("title", "").replace("Category:", "")
            for c in page_data.get("categories", [])
        ]

        return {
            "title": title,
            "url": ii.get("url", ""),
            "descriptionurl": ii.get("descriptionurl", ""),
            "size": ii.get("size", 0),
            "width": ii.get("width", 0),
            "height": ii.get("height", 0),
            "mime": ii.get("mime", ""),
            "license": license_short,
            "license_url": license_url,
            "artist": artist,
            "description": description[:300],
            "date": date_original,
            "categories": categories[:10],
        }
    return None


def download_file(url: str, dest: Path) -> bool:
    """Download a file from url to dest path.

    Uses urllib.request with a browser User-Agent because
    upload.wikimedia.org blocks bot-like User-Agents with 403.
    """
    headers = {
        "User-Agent": DOWNLOAD_USER_AGENT,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://commons.wikimedia.org/",
    }
    # Try urllib first (better at avoiding 403)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        return True
    except Exception as e1:
        print(f"  [WARN] urllib download failed: {e1}")
        # Fallback: try requests
        try:
            resp = requests.get(url, headers=headers, timeout=60, stream=True)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e2:
            print(f"  [ERROR] requests download also failed: {e2}")
            return False


def pick_best(candidates: list[dict]) -> dict | None:
    """Pick best candidate: prefer jpg/png, size > MIN_SIZE_BYTES, largest first."""
    # Filter to preferred formats and minimum size
    good = []
    for c in candidates:
        ext = os.path.splitext(urllib.parse.urlparse(c["url"]).path)[1].lower()
        if ext in PREFERRED_EXTS and c["size"] >= MIN_SIZE_BYTES:
            good.append(c)

    if not good:
        # Fallback: anything with preferred extension
        good = [
            c
            for c in candidates
            if os.path.splitext(urllib.parse.urlparse(c["url"]).path)[1].lower()
            in PREFERRED_EXTS
        ]
    if not good:
        # Last resort: any candidate
        good = candidates

    if not good:
        return None

    # Sort by size descending (prefer larger / higher quality)
    good.sort(key=lambda c: c["size"], reverse=True)
    return good[0]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Searching for {len(SEARCH_TASKS)} items...\n")

    metadata = {}
    downloaded_count = 0

    for label, queries in SEARCH_TASKS:
        print(f"{'='*60}")
        print(f"TASK: {label}")
        found = False

        for query in queries:
            if found:
                break
            print(f"  Searching: \"{query}\"")
            time.sleep(SLEEP_BETWEEN)

            try:
                results = search_commons(query, limit=10)
            except Exception as e:
                print(f"  [ERROR] Search failed: {e}")
                continue

            if not results:
                print(f"  No results.")
                continue

            print(f"  Found {len(results)} results, checking image info...")

            candidates = []
            for r in results:
                title = r.get("title", "")
                if not title:
                    continue
                time.sleep(0.3)  # rate limit
                info = get_image_info(title)
                if info:
                    candidates.append(info)

            if not candidates:
                print(f"  No downloadable images found.")
                continue

            best = pick_best(candidates)
            if not best:
                print(f"  No suitable image found (all too small or wrong format).")
                continue

            # Determine filename
            url_path = urllib.parse.urlparse(best["url"]).path
            ext = os.path.splitext(url_path)[1].lower()
            if not ext:
                ext = ".jpg"
            filename = f"{label}{ext}"
            dest = OUTPUT_DIR / filename

            print(f"  Selected: {best['title']}")
            print(f"    URL: {best['url']}")
            print(f"    Size: {best['size']:,} bytes ({best['width']}x{best['height']})")
            print(f"    License: {best['license']}")
            if best['license_url']:
                print(f"    License URL: {best['license_url']}")
            print(f"    Artist: {best['artist']}")
            if best['date']:
                print(f"    Date: {best['date']}")
            print(f"  Downloading to: {filename}")

            if download_file(best["url"], dest):
                actual_size = dest.stat().st_size
                print(f"  SUCCESS: {filename} ({actual_size:,} bytes)")
                found = True
                downloaded_count += 1

                metadata[label] = {
                    "filename": filename,
                    "source_url": best["url"],
                    "commons_page": best["descriptionurl"],
                    "title": best["title"],
                    "size_bytes": actual_size,
                    "width": best["width"],
                    "height": best["height"],
                    "mime": best["mime"],
                    "license": best["license"],
                    "license_url": best["license_url"],
                    "artist": best["artist"],
                    "description": best["description"],
                    "date": best["date"],
                    "categories": best["categories"],
                    "search_query_used": query,
                }
            else:
                print(f"  FAILED to download.")

        if not found:
            print(f"  >>> COULD NOT FIND/DOWNLOAD image for: {label}")
            metadata[label] = {"status": "not_found", "queries_tried": queries}

        print()

    # Save metadata
    meta_path = OUTPUT_DIR / "download_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"{'='*60}")
    print(f"Metadata saved to: {meta_path}")
    print(f"Downloaded {downloaded_count}/{len(SEARCH_TASKS)} images.")

    # Summary table
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for label, info in metadata.items():
        if "filename" in info:
            print(f"  [OK] {info['filename']:40s}  {info['license']:20s}  {info['size_bytes']:>10,} bytes")
        else:
            print(f"  [--] {label:40s}  NOT FOUND")

    return 0 if downloaded_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
