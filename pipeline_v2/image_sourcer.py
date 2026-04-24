#!/usr/bin/env python3
"""
Image Sourcer — finds real documentary-quality images from the web.

Sources (in priority order):
  1. Video stills — ffmpeg extracts key frames from existing clips
  2. Wikimedia Commons — free API, great for buildings/landmarks/historical
  3. Google Images — via Chrome MCP or direct search
  4. News/archive screenshots — for headlines and specific events

NO Pexels. NO Pixabay. NO generic stock photos.

Usage:
  python -m pipeline_v2.image_sourcer
  python -m pipeline_v2.image_sourcer --queries queries.json --output footage/breaking_law/images_v2/
  python -m pipeline_v2.image_sourcer --extract-stills  # just extract frames from existing clips
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_CLIPS_DIR = PROJECT_ROOT / "footage" / "breaking_law" / "clips"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "footage" / "breaking_law" / "images_v2"
DEFAULT_STILLS_DIR = PROJECT_ROOT / "footage" / "breaking_law" / "stills"
DEFAULT_PAPER_EDIT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit.json"
DEFAULT_TRANSCRIPTS = PROJECT_ROOT / "media" / "breaking_law" / "transcripts.json"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


# ---------------------------------------------------------------------------
# 1. VIDEO STILLS — extract key frames from existing clips
# ---------------------------------------------------------------------------

def get_video_duration(path):
    """Get video duration in seconds via ffprobe."""
    try:
        result = subprocess.run(
            [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return 0


def extract_stills(clips_dir, output_dir, timestamps_per_clip=6, validate_at_ingest=True):
    """Extract key frames from each video clip at evenly-spaced intervals.

    For a 60s clip with timestamps_per_clip=6, extracts frames at 5s, 15s, 25s, 35s, 45s, 55s.
    Names: {clip_stem}_still_{timestamp}s.jpg

    If validate_at_ingest=True (default), every extracted frame is vision-labeled
    via scripts/label_stills.py — unusable frames (ads, reactions, watermarked AI
    slop, comment screenshots, title cards) are moved to <output_dir>/rejected/
    with their sidecar so downstream code never sees the junk. This fixes the
    filename-lies problem at the source: the filename says "Wells_Fargo..." but
    the frame at 1s was an M&M's ad, so it gets quarantined instead of shipped
    to the director LLM.
    """
    clips_dir = Path(clips_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir = output_dir / "rejected"
    if validate_at_ingest:
        rejected_dir.mkdir(parents=True, exist_ok=True)

    # Lazy-import so image_sourcer can still be imported when label_stills
    # dependencies are unavailable in a minimal environment.
    _label_still = None
    if validate_at_ingest:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
            from label_stills import label_still as _label_still  # type: ignore
        except ImportError as e:
            print(f"  [warn] validate_at_ingest requested but label_stills import failed: {e}")
            _label_still = None

    clips = sorted(clips_dir.glob("*.mp4"))
    if not clips:
        print(f"  No .mp4 files in {clips_dir}")
        return []

    all_stills = []
    rejected = 0
    for clip in clips:
        duration = get_video_duration(clip)
        if duration < 2:
            continue

        stem = clip.stem
        interval = max(1, (duration - 2) / timestamps_per_clip)
        timestamps = [1 + i * interval for i in range(timestamps_per_clip)
                      if 1 + i * interval < duration - 0.5]

        for ts in timestamps:
            out_name = f"{stem}_still_{ts:.0f}s.jpg"
            out_path = output_dir / out_name
            if out_path.exists():
                all_stills.append(str(out_path))
                continue

            try:
                subprocess.run(
                    [FFMPEG, "-ss", f"{ts:.2f}", "-i", str(clip),
                     "-vframes", "1", "-q:v", "2",
                     "-y", str(out_path)],
                    capture_output=True, timeout=30
                )
                if not (out_path.exists() and out_path.stat().st_size > 5000):
                    out_path.unlink(missing_ok=True)
                    continue

                # Vision-validate the just-extracted frame
                if _label_still is not None:
                    label = _label_still(out_path)
                    if "_error" not in label and not label.get("usable_for_documentary", True):
                        # Quarantine the frame + its sidecar so the main pool
                        # only contains frames a documentary editor would use.
                        sidecar = out_path.with_suffix(out_path.suffix + ".content.json")
                        out_path.rename(rejected_dir / out_name)
                        if sidecar.exists():
                            sidecar.rename(rejected_dir / sidecar.name)
                        rejected += 1
                        reason = label.get("notes", "flagged as unusable")
                        print(f"    [reject] {out_name}: {reason[:90]}")
                        continue

                all_stills.append(str(out_path))
            except Exception as e:
                print(f"    Failed to extract {out_name}: {e}")

    msg = f"  Extracted {len(all_stills)} usable stills from {len(clips)} clips"
    if validate_at_ingest:
        msg += f" (rejected {rejected} ads/reactions/watermarked)"
    print(msg)
    return all_stills


# ---------------------------------------------------------------------------
# 2. WIKIMEDIA COMMONS — free API, no key needed
# ---------------------------------------------------------------------------

WIKI_API = "https://commons.wikimedia.org/w/api.php"
WIKI_HEADERS = {"User-Agent": "DocumentaryImageSourcer/1.0 (production pipeline)"}


def search_wikimedia(query, limit=5):
    """Search Wikimedia Commons for images. Returns list of (title, url, desc)."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}",
        "gsrlimit": str(limit),
        "gsrnamespace": "6",  # File namespace
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": "1920",
        "format": "json",
    }
    url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers=WIKI_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"    Wikimedia search failed for '{query}': {e}")
        return []

    results = []
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        title = page.get("title", "")
        info = (page.get("imageinfo") or [{}])[0]
        thumb_url = info.get("thumburl") or info.get("url")
        mime = info.get("mime", "")
        if not thumb_url or "svg" in mime:
            continue
        results.append({
            "title": title,
            "url": thumb_url,
            "width": info.get("thumbwidth", info.get("width", 0)),
            "source": "wikimedia",
        })
    return results


def download_image(url, output_path, timeout=30):
    """Download an image from URL to local path."""
    output_path = Path(output_path)
    if output_path.exists() and output_path.stat().st_size > 5000:
        return True

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if len(data) < 5000:
                return False
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        return False


def source_from_wikimedia(query, output_dir, slug, limit=3):
    """Search Wikimedia and download top results."""
    results = search_wikimedia(query, limit=limit)
    downloaded = []
    for i, r in enumerate(results):
        ext = ".jpg"
        if ".png" in r["url"].lower():
            ext = ".png"
        filename = f"wiki_{slug}_{i}{ext}"
        out_path = Path(output_dir) / filename
        if download_image(r["url"], out_path):
            downloaded.append({
                "path": str(out_path),
                "filename": filename,
                "source": "wikimedia",
                "query": query,
                "title": r["title"],
                "url": r["url"],
            })
    return downloaded


# ---------------------------------------------------------------------------
# 3. GOOGLE IMAGES — build search URLs for Chrome MCP
# ---------------------------------------------------------------------------

def google_image_search_url(query):
    """Build a Google Images search URL."""
    params = urllib.parse.urlencode({
        "q": query,
        "tbm": "isch",
        "tbs": "isz:l",  # large images only
    })
    return f"https://www.google.com/search?{params}"


def build_google_queries(beat):
    """Build targeted Google Image search queries from a paper edit beat."""
    text = beat.get("text", "")
    visual = beat.get("visual_file", "")
    chapter = beat.get("chapter", "")

    # Extract named entities and key terms from the beat text
    queries = []

    # Named entities in the beat text
    entity_patterns = [
        r"(Ford Pinto|Richard Grimshaw|Yesenia Guitron|Carrie Tolstedt|"
        r"Wells Fargo|Purdue Pharma|Sackler|Facebook|Meta|Cambridge Analytica|"
        r"Aleksandr Kogan|Mark Zuckerberg|RealPage|Chris Vialpondo|"
        r"Elliana Esquivel|Perplexity AI|Reddit|FTC|DOJ|GDPR|"
        r"HarperCollins|Hulu|Common Crawl|LAION)",
    ]
    for pattern in entity_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            queries.append(m)

    # Visual file gives a hint
    if visual:
        # Convert filename to search query
        stem = Path(visual).stem
        cleaned = re.sub(r'[_\-]+', ' ', stem)
        cleaned = re.sub(r'\b(stock|generic|pexels|wiki|img)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if len(cleaned) > 10:
            queries.append(cleaned)

    # Fall back to first 8 meaningful words of beat text
    if not queries:
        words = [w for w in text.split()[:12]
                 if len(w) > 3 and w.lower() not in
                 {"that", "this", "with", "from", "they", "their", "were", "have", "been", "about"}]
        queries.append(' '.join(words[:8]))

    return queries[:3]  # max 3 queries per beat


# ---------------------------------------------------------------------------
# 4. QUERY PLANNER — figures out what images to search for
# ---------------------------------------------------------------------------

def plan_image_queries(paper_edit_path, transcripts_path=None):
    """Analyze the paper edit and plan image search queries.

    Groups beats by visual need, deduplicates similar queries,
    and prioritizes beats that currently have overused or missing visuals.
    """
    with open(paper_edit_path) as f:
        pe = json.load(f)

    # Count visual usage to find overused files
    from collections import Counter
    usage = Counter()
    for b in pe["beats"]:
        vf = b.get("visual_file", "")
        if vf:
            usage[vf] += 1

    overused = {f for f, c in usage.items() if c > 2}

    # Build query plan
    queries = []
    seen_queries = set()

    for beat in pe["beats"]:
        if beat.get("is_chapter_marker"):
            continue

        vf = beat.get("visual_file", "")
        # Priority: beats with overused visuals, or image references that don't exist
        needs_image = (
            vf in overused
            or vf.endswith(('.jpg', '.png', '.webp'))  # image reference (may not exist)
            or not vf  # no visual assigned
        )
        if not needs_image:
            continue

        beat_queries = build_google_queries(beat)
        for q in beat_queries:
            q_lower = q.lower().strip()
            if q_lower not in seen_queries and len(q_lower) > 5:
                seen_queries.add(q_lower)
                queries.append({
                    "query": q,
                    "beat_id": beat.get("beat_id", ""),
                    "chapter": beat.get("chapter", ""),
                    "start_sec": beat.get("start_sec", 0),
                    "visual_file": vf,
                    "narrative_function": beat.get("narrative_function", ""),
                })

    return queries


# ---------------------------------------------------------------------------
# 5. STILL MATCHER — maps extracted stills to beats by content
# ---------------------------------------------------------------------------

def match_stills_to_beats(stills_dir, paper_edit_path):
    """Create a mapping of which video stills are best for which beats.

    Uses clip filename matching — if beat references Wall_Street_trading_floor.mp4,
    the stills from that clip are candidates.
    """
    stills_dir = Path(stills_dir)
    stills = list(stills_dir.glob("*.jpg"))
    if not stills:
        return {}

    with open(paper_edit_path) as f:
        pe = json.load(f)

    # Build clip -> stills index
    clip_stills = {}
    for s in stills:
        # Parse clip name from still filename: {clip_stem}_still_{ts}s.jpg
        m = re.match(r'(.+)_still_\d+s\.jpg$', s.name)
        if m:
            clip_stem = m.group(1)
            clip_stills.setdefault(clip_stem, []).append(s)

    # For each beat, find matching stills
    matches = {}
    for beat in pe["beats"]:
        vf = beat.get("visual_file", "")
        if not vf:
            continue
        clip_stem = Path(vf).stem
        candidates = clip_stills.get(clip_stem, [])
        if candidates:
            # Pick the still closest to a visually interesting timestamp
            # For now, distribute evenly — later can use Claude vision to rank
            beat_id = beat.get("beat_id", "")
            matches[beat_id] = [str(c) for c in candidates]

    return matches


# ---------------------------------------------------------------------------
# 6. INVENTORY BUILDER — catalog all available images with metadata
# ---------------------------------------------------------------------------

def build_image_inventory(stills_dir, wikimedia_dir, output_path):
    """Build a JSON inventory of all sourced images with metadata."""
    inventory = {"stills": [], "wikimedia": [], "google": [], "stats": {}}

    # Catalog stills
    stills_dir = Path(stills_dir)
    if stills_dir.exists():
        for img in sorted(stills_dir.glob("*.jpg")):
            m = re.match(r'(.+)_still_(\d+)s\.jpg$', img.name)
            if m:
                inventory["stills"].append({
                    "filename": img.name,
                    "path": str(img),
                    "source_clip": m.group(1) + ".mp4",
                    "timestamp": int(m.group(2)),
                    "source": "video_still",
                })

    # Catalog wikimedia downloads
    wiki_dir = Path(wikimedia_dir)
    if wiki_dir.exists():
        for img in sorted(wiki_dir.glob("*")):
            if img.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                inventory["wikimedia"].append({
                    "filename": img.name,
                    "path": str(img),
                    "source": "wikimedia",
                })

    inventory["stats"] = {
        "total_stills": len(inventory["stills"]),
        "total_wikimedia": len(inventory["wikimedia"]),
        "total_google": len(inventory["google"]),
        "total": len(inventory["stills"]) + len(inventory["wikimedia"]) + len(inventory["google"]),
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(inventory, f, indent=2)

    return inventory


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Image Sourcer (no Pexels, no Pixabay)")
    parser.add_argument("--clips-dir", type=str, default=str(DEFAULT_CLIPS_DIR))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--stills-dir", type=str, default=str(DEFAULT_STILLS_DIR))
    parser.add_argument("--paper-edit", type=str, default=str(DEFAULT_PAPER_EDIT))

    sub = parser.add_subparsers(dest="command")

    # Subcommand: extract stills from video clips
    sub_stills = sub.add_parser("stills", help="Extract key frames from video clips")
    sub_stills.add_argument("--frames-per-clip", type=int, default=6)

    # Subcommand: search Wikimedia for specific queries
    sub_wiki = sub.add_parser("wikimedia", help="Search Wikimedia Commons")
    sub_wiki.add_argument("--queries", type=str, help="JSON file of queries or comma-separated list")
    sub_wiki.add_argument("--limit", type=int, default=3, help="Results per query")

    # Subcommand: plan queries from paper edit
    sub_plan = sub.add_parser("plan", help="Plan image queries from paper edit")

    # Subcommand: full run (stills + wikimedia + inventory)
    sub_full = sub.add_parser("full", help="Full sourcing run")
    sub_full.add_argument("--frames-per-clip", type=int, default=6)
    sub_full.add_argument("--wiki-limit", type=int, default=2)

    # Subcommand: inventory
    sub_inv = sub.add_parser("inventory", help="Build image inventory")

    args = parser.parse_args()
    clips_dir = Path(args.clips_dir)
    output_dir = Path(args.output_dir)
    stills_dir = Path(args.stills_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.command == "stills":
        print("Extracting video stills...")
        extract_stills(clips_dir, stills_dir, args.frames_per_clip)

    elif args.command == "wikimedia":
        print("Searching Wikimedia Commons...")
        if args.queries and os.path.isfile(args.queries):
            with open(args.queries) as f:
                queries = json.load(f)
        elif args.queries:
            queries = [{"query": q.strip()} for q in args.queries.split(",")]
        else:
            # Auto-plan from paper edit
            queries = plan_image_queries(args.paper_edit)

        wiki_dir = output_dir / "wikimedia"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        total = 0
        for q in queries:
            query_text = q if isinstance(q, str) else q.get("query", "")
            slug = re.sub(r'[^a-z0-9]+', '_', query_text.lower())[:40]
            results = source_from_wikimedia(query_text, wiki_dir, slug, limit=args.limit)
            if results:
                print(f"    '{query_text}': {len(results)} images")
                total += len(results)
            time.sleep(0.5)  # be polite to Wikimedia API
        print(f"  Total: {total} images from Wikimedia")

    elif args.command == "plan":
        print("Planning image queries from paper edit...")
        queries = plan_image_queries(args.paper_edit)
        print(f"  {len(queries)} unique queries needed")
        for q in queries[:20]:
            print(f"    [{q['chapter'][:15]:15s}] {q['query'][:60]}")
        if len(queries) > 20:
            print(f"    ... and {len(queries) - 20} more")

        # Save query plan
        plan_path = output_dir / "query_plan.json"
        with open(plan_path, 'w') as f:
            json.dump(queries, f, indent=2)
        print(f"  Saved to {plan_path}")

        # Also print Google Image URLs for Chrome
        print("\n  Google Image Search URLs (for Chrome MCP):")
        for q in queries[:10]:
            url = google_image_search_url(q["query"])
            print(f"    {url}")

    elif args.command == "full":
        print("=== Full Image Sourcing Run ===\n")

        # Step 1: Extract stills
        print("Step 1: Extracting video stills...")
        stills = extract_stills(clips_dir, stills_dir, args.frames_per_clip)
        print(f"  {len(stills)} stills ready\n")

        # Step 2: Plan queries
        print("Step 2: Planning queries from paper edit...")
        queries = plan_image_queries(args.paper_edit)
        print(f"  {len(queries)} queries planned\n")

        # Step 3: Wikimedia
        print("Step 3: Searching Wikimedia Commons...")
        wiki_dir = output_dir / "wikimedia"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        wiki_total = 0
        for q in queries:
            query_text = q.get("query", "")
            slug = re.sub(r'[^a-z0-9]+', '_', query_text.lower())[:40]
            results = source_from_wikimedia(query_text, wiki_dir, slug, limit=args.wiki_limit)
            if results:
                wiki_total += len(results)
            time.sleep(0.5)
        print(f"  {wiki_total} images from Wikimedia\n")

        # Step 4: Build inventory
        print("Step 4: Building inventory...")
        inv_path = output_dir / "image_inventory.json"
        inv = build_image_inventory(stills_dir, wiki_dir, inv_path)
        print(f"  Inventory: {inv['stats']['total']} total images")
        print(f"    Stills: {inv['stats']['total_stills']}")
        print(f"    Wikimedia: {inv['stats']['total_wikimedia']}")
        print(f"  Saved to {inv_path}")

        # Step 5: Print remaining queries for Chrome MCP
        remaining = [q for q in queries if q.get("query", "").lower() not in
                     {r.get("query", "").lower() for r in (inv.get("wikimedia") or [])}]
        if remaining:
            print(f"\n  {len(remaining)} queries may need Google Images (Chrome MCP):")
            for q in remaining[:15]:
                print(f"    [{q['chapter'][:12]:12s}] {q['query'][:50]}")

    elif args.command == "inventory":
        wiki_dir = output_dir / "wikimedia"
        inv_path = output_dir / "image_inventory.json"
        inv = build_image_inventory(stills_dir, wiki_dir, inv_path)
        print(f"  Inventory: {inv['stats']['total']} total images")
        print(f"  Saved to {inv_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
