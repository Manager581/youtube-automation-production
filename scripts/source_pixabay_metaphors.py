#!/usr/bin/env python3
"""
Source visual metaphor images from Pixabay for storyboard segments
that don't have real footage yet.

Uses the PIXABAY_API_KEY env var. Downloads high-res images for each
segment's search_query where visual_approach == "visual_metaphor".
"""
import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

API_KEY = os.environ.get("PIXABAY_API_KEY", "")
SB_PATH = Path("storyboards/frank_olson_cia_scientist_lsd_murder_cover_up.json")
MANIFEST_PATH = Path("footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/manifest.json")
IMG_DIR = Path("footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images")

def search_pixabay(query: str, per_page: int = 5) -> list:
    """Search Pixabay for images matching query."""
    params = urllib.parse.urlencode({
        "key": API_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": per_page,
        "safesearch": "true",
        "min_width": 1280,
        "orientation": "horizontal",  # 16:9 friendly
    })
    url = f"https://pixabay.com/api/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("hits", [])
    except Exception as e:
        print(f"    ⚠ Pixabay error: {e}")
        return []


def download_image(url: str, dest: Path) -> bool:
    """Download image from URL to dest path."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    ⚠ Download failed: {e}")
        return False


def main():
    if not API_KEY:
        print("ERROR: PIXABAY_API_KEY not set")
        return

    sb = json.load(open(SB_PATH))
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # Load manifest to check what already has coverage
    manifest = json.load(open(MANIFEST_PATH)) if MANIFEST_PATH.exists() else {}
    existing_images = set()
    for img in manifest.get("images", []):
        for sid in img.get("storyboard_segment_ids", []):
            existing_images.add(sid)
    for clip in manifest.get("clips", []):
        for sid in clip.get("storyboard_segment_ids", []):
            existing_images.add(sid)

    # Find segments needing visual metaphor images
    visual_idx = 0
    to_source = []
    for i, entry in enumerate(sb):
        if entry.get("is_chapter_break"):
            continue
        approach = entry.get("visual_approach", "")
        if visual_idx not in existing_images and approach:
            to_source.append((visual_idx, entry))
        elif visual_idx not in existing_images:
            to_source.append((visual_idx, entry))
        visual_idx += 1

    print(f"Segments needing images: {len(to_source)}")
    print(f"Already covered: {len(existing_images)}")
    print()

    downloaded = 0
    new_manifest_images = []

    for seg_idx, entry in to_source:
        query = entry.get("search_query", "")
        if not query or len(query) < 3:
            continue

        # Simplify query for better Pixabay results
        # Remove very specific terms that won't match stock photos
        simple_q = query.replace("1950s", "").replace("1940s", "").replace("1970s", "").strip()
        if len(simple_q) < 3:
            simple_q = query

        print(f"  [{seg_idx:3d}] {simple_q[:50]}...", end="", flush=True)

        hits = search_pixabay(simple_q, per_page=3)
        if not hits:
            # Try simpler query (first 3 words)
            words = simple_q.split()[:3]
            hits = search_pixabay(" ".join(words), per_page=3)

        if hits:
            hit = hits[0]  # Best match
            img_url = hit.get("largeImageURL", hit.get("webformatURL", ""))
            if img_url:
                fname = f"pixabay_seg_{seg_idx:04d}.jpg"
                dest = IMG_DIR / fname
                if download_image(img_url, dest):
                    downloaded += 1
                    new_manifest_images.append({
                        "filename": f"images/{fname}",
                        "source": "pixabay",
                        "pixabay_id": hit.get("id"),
                        "pixabay_user": hit.get("user", ""),
                        "width": hit.get("imageWidth", 0),
                        "height": hit.get("imageHeight", 0),
                        "storyboard_segment_ids": [seg_idx],
                        "storyboard_show": entry.get("show", ""),
                        "query": simple_q,
                    })
                    print(f" ✓ ({hit['imageWidth']}x{hit['imageHeight']})")
                else:
                    print(f" ✗ download failed")
            else:
                print(f" ✗ no URL")
        else:
            print(f" ✗ no results")

        time.sleep(0.2)  # Rate limit

    # Update manifest with new images
    if new_manifest_images and MANIFEST_PATH.exists():
        manifest = json.load(open(MANIFEST_PATH))
        manifest["images"] = manifest.get("images", []) + new_manifest_images
        manifest["needs_animation_count"] = max(0,
            manifest.get("needs_animation_count", 0) - downloaded)
        json.dump(manifest, open(MANIFEST_PATH, "w"), indent=2)
        print(f"\nManifest updated: +{downloaded} Pixabay images")

    print(f"\nDone: {downloaded} images downloaded to {IMG_DIR}")


if __name__ == "__main__":
    main()
