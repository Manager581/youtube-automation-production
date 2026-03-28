#!/usr/bin/env python3
"""
research_agent.py — On-demand footage sourcer for director-identified gaps.

Searches YouTube (yt-dlp), image APIs (Pexels, Pixabay, Wikimedia), and news
sites to fill footage gaps. Called by the director when segments lack matching
media. Uses Claude vision to verify downloads match the query.

NOT a standalone pipeline stage — it's an on-demand service.

Gap list format:
    [{"segment": 14, "query": "tenant screening court hearing",
      "reason": "no matching footage found"}]

Usage:
    python -m pipeline_v2.research_agent --gaps gaps.json --output footage/new/
    python -m pipeline_v2.research_agent --query "tenant screening discrimination" --output footage/new/
    python -m pipeline_v2.research_agent --query "FBI raid 1950s" --type video --output footage/new/
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude, query_claude_vision


# -- YouTube Search -----------------------------------------------------------

def search_youtube(query, output_dir=None, max_results=5):
    """Search and download YouTube clips using yt-dlp.

    Args:
        query: Search query string.
        output_dir: Directory to save downloaded clips. Defaults to cwd.
        max_results: Maximum number of results to download.

    Returns:
        list[dict]: Each with keys: file, source, query, title, duration, url
    """
    output_dir = Path(output_dir or ".")
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_query = re.sub(r'[^\w\s-]', '', query)[:60].strip().replace(' ', '_')

    # First, search for video URLs
    search_cmd = [
        'yt-dlp', '--flat-playlist', '--no-download',
        '-j', f'ytsearch{max_results}:{query}',
    ]

    results = []
    try:
        proc = subprocess.run(
            search_cmd, capture_output=True, text=True, timeout=30
        )
        if proc.returncode != 0:
            print(f"  yt-dlp search failed: {proc.stderr[:200]}", file=sys.stderr)
            return results
    except FileNotFoundError:
        print("  ERROR: yt-dlp not found. Install with: pip install yt-dlp",
              file=sys.stderr)
        return results
    except subprocess.TimeoutExpired:
        print("  yt-dlp search timed out", file=sys.stderr)
        return results

    entries = []
    for line in proc.stdout.strip().split('\n'):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Download each clip (short clips only, max 5 min)
    for i, entry in enumerate(entries[:max_results]):
        video_id = entry.get('id', entry.get('url', ''))
        title = entry.get('title', f'video_{i}')
        duration = entry.get('duration') or 0
        url = entry.get('url') or entry.get('webpage_url') or ''

        # Build full URL if we only have an ID
        if video_id and not url.startswith('http'):
            url = f"https://www.youtube.com/watch?v={video_id}"

        if not url:
            continue

        # Skip very long videos (> 10 min) to save time/space
        if duration and duration > 600:
            print(f"  Skipping '{title[:40]}' ({duration}s > 600s)")
            continue

        out_template = str(output_dir / f"yt_{safe_query}_{i:02d}.%(ext)s")

        dl_cmd = [
            'yt-dlp',
            '-f', 'mp4[height<=720]/best[height<=720]/mp4/best',
            '--no-playlist',
            '-o', out_template,
            '--max-filesize', '100M',
            url,
        ]

        print(f"  Downloading: {title[:50]}...")
        try:
            dl_proc = subprocess.run(
                dl_cmd, capture_output=True, text=True, timeout=120
            )
        except subprocess.TimeoutExpired:
            print(f"    Download timed out: {title[:40]}")
            continue

        # Find the downloaded file
        downloaded = None
        for ext in ('.mp4', '.mkv', '.webm', '.m4v'):
            candidate = output_dir / f"yt_{safe_query}_{i:02d}{ext}"
            if candidate.exists() and candidate.stat().st_size > 1000:
                downloaded = candidate
                break

        if downloaded:
            results.append({
                "file": str(downloaded),
                "source": "youtube",
                "query": query,
                "title": title,
                "duration": duration,
                "url": url,
            })
            print(f"    Saved: {downloaded.name}")
        else:
            print(f"    Failed to download: {title[:40]}")

    return results


# -- Image Search -------------------------------------------------------------

def search_images(query, output_dir=None, max_results=5):
    """Search multiple image sources: Pexels, Pixabay, Wikimedia.

    Args:
        query: Search query string.
        output_dir: Directory to save downloaded images. Defaults to cwd.
        max_results: Maximum total images to return.

    Returns:
        list[dict]: Each with keys: file, source, query, url
    """
    output_dir = Path(output_dir or ".")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    remaining = max_results

    # 1. Pexels (free, no key needed for direct URLs)
    if remaining > 0:
        pexels = _search_pexels(query, output_dir, min(remaining, 3))
        results.extend(pexels)
        remaining -= len(pexels)

    # 2. Pixabay (needs PIXABAY_API_KEY)
    if remaining > 0:
        pixabay = _search_pixabay(query, output_dir, min(remaining, 3))
        results.extend(pixabay)
        remaining -= len(pixabay)

    # 3. Wikimedia Commons (free, no key needed)
    if remaining > 0:
        wiki = _search_wikimedia(query, output_dir, min(remaining, 3))
        results.extend(wiki)

    return results[:max_results]


def _search_pexels(query, output_dir, max_results=3):
    """Search Pexels API. Works without API key for basic searches."""
    api_key = os.environ.get('PEXELS_API_KEY', '')
    if not api_key:
        return []

    results = []
    encoded = urllib.parse.quote(query[:100])
    url = f"https://api.pexels.com/v1/search?query={encoded}&per_page={max_results}"

    try:
        proc = subprocess.run(
            ['curl', '-s', '-H', f'Authorization: {api_key}', url],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(proc.stdout)
        photos = data.get('photos', [])

        safe_q = re.sub(r'[^\w]', '_', query[:25])
        for i, photo in enumerate(photos[:max_results]):
            img_url = photo.get('src', {}).get('large2x') or photo.get('src', {}).get('original', '')
            if not img_url:
                continue

            filepath = output_dir / f"pexels_{safe_q}_{i:02d}.jpg"
            subprocess.run(
                ['curl', '-sL', '-o', str(filepath), '-m', '15', img_url],
                capture_output=True, timeout=20,
            )
            if filepath.exists() and filepath.stat().st_size > 5000:
                results.append({
                    "file": str(filepath),
                    "source": "pexels",
                    "query": query,
                    "url": img_url,
                })
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return results


def _search_pixabay(query, output_dir, max_results=3):
    """Search Pixabay image API (needs PIXABAY_API_KEY env var)."""
    api_key = os.environ.get('PIXABAY_API_KEY', '')
    if not api_key:
        return []

    results = []
    encoded = urllib.parse.quote(query[:100])
    url = (
        f"https://pixabay.com/api/?key={api_key}&q={encoded}"
        f"&image_type=photo&per_page={max_results}&min_width=1280"
    )

    try:
        proc = subprocess.run(
            ['curl', '-s', url], capture_output=True, text=True, timeout=15
        )
        data = json.loads(proc.stdout)
        hits = data.get('hits', [])

        safe_q = re.sub(r'[^\w]', '_', query[:25])
        for i, hit in enumerate(hits[:max_results]):
            img_url = hit.get('largeImageURL', '')
            if not img_url:
                continue

            filepath = output_dir / f"pixabay_{safe_q}_{i:02d}.jpg"
            subprocess.run(
                ['curl', '-sL', '-o', str(filepath), '-m', '15', img_url],
                capture_output=True, timeout=20,
            )
            if filepath.exists() and filepath.stat().st_size > 5000:
                results.append({
                    "file": str(filepath),
                    "source": "pixabay",
                    "query": query,
                    "url": img_url,
                })
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return results


def _search_wikimedia(query, output_dir, max_results=3):
    """Search Wikimedia Commons (free, no API key needed)."""
    results = []
    encoded = urllib.parse.quote(query[:100])
    url = (
        f"https://commons.wikimedia.org/w/api.php?action=query"
        f"&generator=search&gsrsearch={encoded}&gsrnamespace=6"
        f"&prop=imageinfo&iiprop=url|size&iiurlwidth=1920&format=json"
    )

    try:
        proc = subprocess.run(
            ['curl', '-s', url], capture_output=True, text=True, timeout=15
        )
        data = json.loads(proc.stdout)
        pages = data.get('query', {}).get('pages', {})

        safe_q = re.sub(r'[^\w]', '_', query[:25])
        for i, (_, page) in enumerate(list(pages.items())[:max_results]):
            imageinfo = page.get('imageinfo', [{}])[0]
            thumb_url = imageinfo.get('thumburl', '')
            if not thumb_url:
                continue

            filepath = output_dir / f"wiki_{safe_q}_{i:02d}.jpg"
            subprocess.run(
                ['curl', '-sL', '-o', str(filepath), '-m', '15', thumb_url],
                capture_output=True, timeout=20,
            )
            if filepath.exists() and filepath.stat().st_size > 5000:
                results.append({
                    "file": str(filepath),
                    "source": "wikimedia",
                    "query": query,
                    "url": thumb_url,
                })
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return results


# -- News Search --------------------------------------------------------------

def search_news(query, output_dir=None, max_results=3):
    """Search for news articles and capture screenshots.

    Uses yt-dlp to find news video clips (CNN, BBC, etc.) and falls back
    to searching for news images on Wikimedia.

    Args:
        query: Search query (e.g., "tenant screening lawsuit 2024").
        output_dir: Directory to save results.
        max_results: Maximum results.

    Returns:
        list[dict]: Each with keys: file, source, query, title
    """
    output_dir = Path(output_dir or ".")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    # Search YouTube for news clips specifically
    news_query = f"{query} news report"
    news_clips = search_youtube(news_query, output_dir, max_results=min(max_results, 2))
    results.extend(news_clips)

    # Supplement with Wikimedia news images
    remaining = max_results - len(results)
    if remaining > 0:
        wiki = _search_wikimedia(f"{query} news", output_dir, remaining)
        results.extend(wiki)

    return results[:max_results]


# -- Gap Filling (Director Integration) --------------------------------------

def fill_gaps(gap_list, output_dir=None):
    """Fill footage gaps identified by the director.

    Args:
        gap_list: List of dicts, each with:
            - segment (int): segment index
            - query (str): search query
            - reason (str): why footage is needed
            - type (str, optional): "video", "image", or "any" (default "any")
        output_dir: Base directory for downloaded footage.

    Returns:
        dict: {segment_idx: [list of downloaded items]}
    """
    output_dir = Path(output_dir or "footage_gaps")
    output_dir.mkdir(parents=True, exist_ok=True)

    filled = {}
    total_downloads = 0

    print(f"\nFilling {len(gap_list)} footage gaps...")

    for gap in gap_list:
        seg_idx = gap.get("segment", 0)
        query = gap.get("query", "")
        reason = gap.get("reason", "")
        media_type = gap.get("type", "any")

        if not query:
            print(f"  Segment {seg_idx}: no query provided, skipping")
            continue

        seg_dir = output_dir / f"seg_{seg_idx:03d}"
        seg_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  Segment {seg_idx}: '{query}'")
        if reason:
            print(f"    Reason: {reason}")

        downloads = []

        if media_type in ("video", "any"):
            yt_results = search_youtube(query, seg_dir, max_results=2)
            downloads.extend(yt_results)

        if media_type in ("image", "any"):
            img_results = search_images(query, seg_dir, max_results=3)
            downloads.extend(img_results)

        if not downloads:
            # Try broader query
            broad_query = _broaden_query(query)
            if broad_query != query:
                print(f"    No results. Trying broader: '{broad_query}'")
                img_results = search_images(broad_query, seg_dir, max_results=3)
                downloads.extend(img_results)

        filled[seg_idx] = downloads
        total_downloads += len(downloads)
        print(f"    Found {len(downloads)} items for segment {seg_idx}")

    print(f"\nGap filling complete: {total_downloads} items for "
          f"{len(gap_list)} gaps")

    return filled


def _broaden_query(query):
    """Simplify a query to get more results."""
    words = query.split()
    if len(words) <= 2:
        return query
    # Keep the most important words (nouns/adjectives tend to be longer)
    important = sorted(words, key=lambda w: len(w), reverse=True)
    return ' '.join(important[:3])


# -- Verification -------------------------------------------------------------

def verify_downloads(downloads, queries=None):
    """Verify downloaded media matches the intended queries using Claude vision.

    Args:
        downloads: List of dicts with at least a 'file' key.
        queries: Optional dict mapping file paths to expected queries.
            If not provided, uses the 'query' field from each download.

    Returns:
        list[dict]: Each download dict augmented with 'verified' (bool)
            and 'verification_reason' (str).
    """
    queries = queries or {}
    verified_count = 0

    print(f"\nVerifying {len(downloads)} downloads...")

    for dl in downloads:
        filepath = dl.get("file", "")
        if not filepath or not os.path.exists(filepath):
            dl["verified"] = False
            dl["verification_reason"] = "file not found"
            continue

        expected = queries.get(filepath, dl.get("query", ""))
        if not expected:
            dl["verified"] = True
            dl["verification_reason"] = "no query to verify against"
            verified_count += 1
            continue

        # Check file type — only vision-check images
        ext = Path(filepath).suffix.lower()
        if ext in ('.mp4', '.mkv', '.webm', '.mov', '.avi', '.m4v'):
            # For videos, extract a frame and check that
            frame_path = filepath + ".verify_frame.jpg"
            extracted = extract_frame_for_verify(filepath, frame_path)
            if extracted:
                ok, reason = _vision_verify(frame_path, expected)
                dl["verified"] = ok
                dl["verification_reason"] = reason
                try:
                    os.remove(frame_path)
                except OSError:
                    pass
            else:
                dl["verified"] = False
                dl["verification_reason"] = "could not extract frame for verification"
        else:
            ok, reason = _vision_verify(filepath, expected)
            dl["verified"] = ok
            dl["verification_reason"] = reason

        if dl["verified"]:
            verified_count += 1
        else:
            print(f"  MISMATCH: {Path(filepath).name} — {dl['verification_reason'][:60]}")

    print(f"  Verified: {verified_count}/{len(downloads)} passed")
    return downloads


def extract_frame_for_verify(video_path, output_path, timestamp=5.0):
    """Extract a single frame from a video for verification."""
    cmd = [
        'ffmpeg', '-y', '-ss', str(timestamp),
        '-i', str(video_path),
        '-frames:v', '1', '-q:v', '2',
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0 and os.path.exists(output_path)
    except subprocess.TimeoutExpired:
        return False


def _vision_verify(image_path, expected_query):
    """Check if an image matches an expected query using Claude vision."""
    prompt = (
        f"Does this image match the search query '{expected_query}'? "
        f"Reply with ONLY valid JSON: "
        f'{{"match": true/false, "reason": "one sentence explanation"}}'
    )
    response = query_claude_vision(prompt, image_path, timeout=30)

    if not response:
        return False, "vision check returned empty response"

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            data = json.loads(match.group())
            is_match = data.get("match", False)
            reason = data.get("reason", "")
            return is_match, reason
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fall back to simple text check
    lower = response.lower()
    if 'yes' in lower[:20] or 'match' in lower[:30]:
        return True, response.strip()[:100]
    return False, response.strip()[:100]


# -- CLI ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Research agent — source footage for director-identified gaps"
    )
    parser.add_argument(
        '--gaps', metavar='FILE',
        help='JSON file with gap list: [{"segment": N, "query": "...", "reason": "..."}]',
    )
    parser.add_argument(
        '--query', '-q',
        help='Single search query (for ad-hoc searches)',
    )
    parser.add_argument(
        '--type', choices=['video', 'image', 'any', 'news'], default='any',
        help='Media type to search for (default: any)',
    )
    parser.add_argument(
        '--output', '-o', default='footage/new/',
        help='Output directory for downloads (default: footage/new/)',
    )
    parser.add_argument(
        '--max', type=int, default=5,
        help='Max results per query (default: 5)',
    )
    parser.add_argument(
        '--verify', action='store_true',
        help='Verify downloads match queries using Claude vision',
    )
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.gaps:
        # Fill gaps from a JSON file
        if not os.path.exists(args.gaps):
            print(f"ERROR: gaps file not found: {args.gaps}", file=sys.stderr)
            return 1

        with open(args.gaps) as f:
            gap_list = json.load(f)

        filled = fill_gaps(gap_list, args.output)

        # Optionally verify
        if args.verify:
            all_downloads = []
            for seg_downloads in filled.values():
                all_downloads.extend(seg_downloads)
            verify_downloads(all_downloads)

        # Save results manifest
        manifest_path = Path(args.output) / "research_manifest.json"
        serializable = {
            str(k): v for k, v in filled.items()
        }
        manifest_path.write_text(json.dumps(serializable, indent=2))
        print(f"\nManifest saved: {manifest_path}")

    elif args.query:
        # Single query search
        results = []

        if args.type == 'video':
            results = search_youtube(args.query, args.output, args.max)
        elif args.type == 'image':
            results = search_images(args.query, args.output, args.max)
        elif args.type == 'news':
            results = search_news(args.query, args.output, args.max)
        else:
            # Search everything
            yt = search_youtube(args.query, args.output, max_results=2)
            img = search_images(args.query, args.output, max_results=3)
            results = yt + img

        if args.verify and results:
            results = verify_downloads(results)

        print(f"\nFound {len(results)} items:")
        for r in results:
            status = ""
            if 'verified' in r:
                status = " [OK]" if r['verified'] else " [MISMATCH]"
            print(f"  {r['source']}: {Path(r['file']).name}{status}")

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
