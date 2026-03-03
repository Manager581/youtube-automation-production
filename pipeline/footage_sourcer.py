#!/usr/bin/env python3
"""
Footage Sourcer — finds and downloads relevant footage for a story.

Sources (NO stock footage, ever):
  1. YouTube news channels — Reuters, AP Archive, BBC, CNN, C-SPAN, etc.
  2. Internet Archive — archival footage, old news broadcasts, gov docs
  3. Wikimedia Commons — free-licensed still images (CC/PD)

Usage:
    # Source footage from a research brief (broad topic search)
    python pipeline/footage_sourcer.py --brand fern_clone --brief cia_mkultra

    # Source from a storyboard (PREFERRED — story-driven targeted searches)
    python pipeline/footage_sourcer.py --brand fern_clone \
        --brief cia_mkultra \
        --storyboard storyboards/cia_mkultra.json

    # Source from a direct query
    python pipeline/footage_sourcer.py --brand fern_clone --query "CIA MKUltra experiments" --download

    # Preview only (no download)
    python pipeline/footage_sourcer.py --brand fern_clone --brief cia_mkultra --preview

Output:
    footage/{brand_id}/{slug}/manifest.json  — all clips with metadata + storyboard_segment_ids
    footage/{brand_id}/{slug}/*.mp4           — downloaded clips (if --download)
    footage/{brand_id}/{slug}/images/         — Wikimedia still images (if downloaded)

Storyboard integration:
    When --storyboard is provided, each clip in the manifest gains:
      "storyboard_segment_ids": [3, 7, 12]   — which story segments this clip serves
      "storyboard_show": "FBI memo 1973..."   — what the storyboard specified to show
    video_assembler.py uses these to pick the right clip for each story moment.
"""

import json
import re
import time
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

# ── Guardrails ────────────────────────────────────────────────────────────────

# Per-query search timeout (seconds). Prevents any single search hanging the run.
SEARCH_TIMEOUT_SEC = 20

# If total found < this, print a warning and flag output for animation fallback
MIN_VIABLE_IMAGES = 10    # Wikimedia images
MIN_VIABLE_CLIPS  = 2     # video clips

# Per-segment: if 0 images AND 0 clips found, flag as NEEDS_ANIMATION
# The assembly step will call animation_generator.py for flagged segments


# ── News channels that produce reusable footage ──────────────────────────────
# These channels upload footage under fair use / news license contexts.
# Format: (channel_name, youtube_search_prefix, priority)
NEWS_CHANNELS = [
    # Tier 1: Best for archival/documentary footage
    ("AP Archive",       "AP Archive",       1),
    ("Reuters",          "Reuters",           1),
    ("C-SPAN",           "C-SPAN",            1),
    ("Internet Archive", None,                1),  # handled separately

    # Tier 2: Good coverage, may have copyright claims
    ("BBC News",         "BBC News",          2),
    ("PBS NewsHour",     "PBS NewsHour",      2),
    ("ABC News",         "ABC News",          2),

    # Tier 3: Use sparingly — heavy copyright enforcement
    ("CNN",              "CNN",               3),
    ("NBC News",         "NBC News",          3),
]

# YouTube search query templates for different content types
_SEARCH_TEMPLATES = [
    "{query} footage",
    "{query} documentary",
    "{query} news report",
    "{query} hearing testimony",
    "{query} archive",
    "{query} {year}",
]

# Hard limits — never download more than this per query
MAX_CLIPS_PER_QUERY = 8
MAX_TOTAL_CLIPS = 40
MAX_CLIP_DURATION_SEC = 1800  # 30 min max — full doc segments are fine


# ── Config ────────────────────────────────────────────────────────────────────

def load_brand(brand_id: str) -> dict:
    path = Path(f"brand_configs/{brand_id}.json")
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")
    return json.loads(path.read_text())


def load_brief(brand_id: str, brief_slug: str) -> dict:
    """Load a research brief by slug."""
    # Try exact match first
    path = Path(f"research/{brand_id}/briefs/{brief_slug}.json")
    if not path.exists():
        # Try fuzzy match
        for p in Path(f"research/{brand_id}/briefs").glob("*.json"):
            if brief_slug.lower() in p.stem.lower():
                path = p
                break
    if not path.exists():
        raise FileNotFoundError(f"Brief not found: {brief_slug}")
    return json.loads(path.read_text())


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:60].strip("_")


# ── YouTube search ─────────────────────────────────────────────────────────────

def search_youtube(query: str, channel_prefix: str = "", max_results: int = 5) -> list:
    """Search YouTube via yt-dlp ytsearch. Returns video metadata."""
    search_query = f"{channel_prefix} {query}".strip() if channel_prefix else query
    search_str = f"ytsearch{max_results}:{search_query}"

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        search_str,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        videos = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                duration = d.get("duration") or 0
                # Skip very long videos (full docs) — want news clips
                if duration > MAX_CLIP_DURATION_SEC:
                    continue
                videos.append({
                    "id": d.get("id", ""),
                    "title": d.get("title", ""),
                    "channel": d.get("channel") or d.get("uploader", ""),
                    "duration_sec": duration,
                    "view_count": d.get("view_count") or 0,
                    "upload_date": d.get("upload_date", ""),
                    "url": d.get("url") or f"https://youtu.be/{d.get('id','')}",
                    "source": "youtube",
                    "search_query": search_query,
                })
            except json.JSONDecodeError:
                continue
        return videos
    except subprocess.TimeoutExpired:
        print(f"  ⚠ Search timeout: {search_query[:50]}")
        return []
    except Exception as e:
        print(f"  ⚠ Search error: {e}")
        return []


def get_video_info(url: str) -> dict:
    """Get full metadata for a specific video URL."""
    cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--no-playlist", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.stdout.strip():
            return json.loads(result.stdout.strip())
    except Exception:
        pass
    return {}


# ── Internet Archive search ───────────────────────────────────────────────────

def search_internet_archive(query: str, year_from: int = None, max_results: int = 8) -> list:
    """Search Internet Archive for video content."""
    ia_query = f"{query} AND mediatype:movies"
    if year_from:
        ia_query += f" AND year:[{year_from} TO 9999]"

    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({
        "q": ia_query,
        "fl[]": "identifier,title,year,downloads,description",
        "rows": max_results,
        "output": "json",
        "sort[]": "downloads desc",
    })

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fern-footage-bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        results = []
        for doc in data.get("response", {}).get("docs", []):
            identifier = doc.get("identifier", "")
            results.append({
                "id": identifier,
                "title": doc.get("title", ""),
                "year": str(doc.get("year", "")),
                "downloads": doc.get("downloads", 0),
                "description": str(doc.get("description", ""))[:200],
                "url": f"https://archive.org/details/{identifier}",
                "download_url": f"https://archive.org/download/{identifier}",
                "source": "internet_archive",
                "search_query": query,
            })
        return results
    except Exception as e:
        print(f"  ⚠ Internet Archive: {e}")
        return []


# ── Wikimedia Commons (primary still-image source) ────────────────────────────
# Fern's footage breakdown: 57% document_photo, 20% documentary_photo
# Wikimedia is the best free, legally-clear source for both.

WIKIMEDIA_UA = "fern-footage-bot/1.0 (research pipeline)"

def search_wikimedia_images(query: str, max_results: int = 30) -> list:
    """
    Search Wikimedia Commons for freely licensed images and documents.
    Returns list of image dicts with title, url, description, license.
    No API key required.
    """
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": "6",        # namespace 6 = File: (images, PDFs, etc.)
        "srlimit": max_results,
        "format": "json",
        "utf8": 1,
    })
    try:
        req = urllib.request.Request(url, headers={"User-Agent": WIKIMEDIA_UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get("query", {}).get("search", [])
        if not results:
            return []

        # Get image metadata (URL, license) in a batch request
        titles = "|".join(r["title"] for r in results[:20])
        info_url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query",
            "titles": titles,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime|size",
            "format": "json",
            "utf8": 1,
        })
        req2 = urllib.request.Request(info_url, headers={"User-Agent": WIKIMEDIA_UA})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            info_data = json.loads(resp2.read())

        images = []
        pages = info_data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                continue
            ii = page.get("imageinfo", [{}])[0]
            mime = ii.get("mime", "")
            if not mime.startswith("image/"):
                continue   # skip audio, video, PDF (handle separately)

            meta = ii.get("extmetadata", {})
            license_name = meta.get("LicenseShortName", {}).get("value", "")
            description = meta.get("ImageDescription", {}).get("value", "")
            description = re.sub(r"<[^>]+>", "", description)[:200]

            # Only include images with open licenses
            free_licenses = ["CC", "PD", "Public domain", "Copyrighted free use"]
            if not any(fl.lower() in license_name.lower() for fl in free_licenses):
                if license_name:
                    continue   # skip non-free
                # If no license info, include anyway (assume Wikimedia Commons free)

            width  = ii.get("width", 0)
            height = ii.get("height", 0)

            # Skip tiny images (< 400px wide — too small for Ken Burns)
            if width and width < 400:
                continue

            images.append({
                "type": "image",
                "source": "wikimedia_commons",
                "title": page.get("title", "").replace("File:", ""),
                "url": ii.get("url", ""),
                "page_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(page.get('title',''))}",
                "license": license_name,
                "description": description,
                "width": width,
                "height": height,
                "search_query": query,
            })

        return images

    except Exception as e:
        print(f"  ⚠ Wikimedia Commons: {e}")
        return []


def download_wikimedia_image(img: dict, output_dir: Path) -> dict:
    """Download a single Wikimedia image. Returns updated dict with local_path."""
    url = img.get("url", "")
    if not url:
        return {**img, "downloaded": False, "error": "no url"}

    # Derive filename from title
    safe = re.sub(r"[^\w\s.-]", "", img.get("title", "image"))
    safe = re.sub(r"\s+", "_", safe)[:80]
    ext = Path(url).suffix.lower() or ".jpg"
    out_path = output_dir / f"wiki_{safe}{ext}"

    if out_path.exists():
        return {**img, "downloaded": True, "local_path": str(out_path), "cached": True}

    try:
        req = urllib.request.Request(url, headers={"User-Agent": WIKIMEDIA_UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            out_path.write_bytes(resp.read())
        size_kb = out_path.stat().st_size // 1024
        return {**img, "downloaded": True, "local_path": str(out_path),
                "size_kb": size_kb}
    except Exception as e:
        return {**img, "downloaded": False, "error": str(e)}


def source_wikimedia_for_story(query: str, entities: dict,
                                output_dir: Path, download: bool = False,
                                max_images: int = 40) -> list:
    """
    Search Wikimedia for a story query + key entities.
    Deduplicates, scores by resolution, optionally downloads.
    Returns list of image dicts.
    """
    searches = [query]
    # Also search for key people, agencies by name
    for person in entities.get("people_orgs", [])[:3]:
        if len(person.split()) >= 2:
            searches.append(person)
    for agency in entities.get("agencies", [])[:2]:
        searches.append(agency)

    all_images = []
    seen_urls = set()

    for q in searches:
        print(f"  Wikimedia: searching '{q[:50]}'...")
        imgs = search_wikimedia_images(q, max_results=20)
        for img in imgs:
            if img["url"] not in seen_urls:
                seen_urls.add(img["url"])
                all_images.append(img)
        time.sleep(0.4)

    # Sort by resolution (largest first — best for Ken Burns zooms)
    all_images.sort(key=lambda i: i.get("width", 0) * i.get("height", 0), reverse=True)
    all_images = all_images[:max_images]

    print(f"  Wikimedia: {len(all_images)} unique images found")

    if download and all_images:
        img_dir = output_dir / "images"
        img_dir.mkdir(exist_ok=True)
        print(f"  Downloading {len(all_images)} images → {img_dir}")
        downloaded = []
        for img in all_images:
            result = download_wikimedia_image(img, img_dir)
            downloaded.append(result)
            if result.get("downloaded") and not result.get("cached"):
                time.sleep(0.2)   # be polite to Wikimedia servers
        ok = sum(1 for r in downloaded if r.get("downloaded"))
        print(f"  Downloaded: {ok}/{len(all_images)}")
        return downloaded

    return all_images


# ── Storyboard integration ───────────────────────────────────────────────────

def load_storyboard(storyboard_path: str) -> list:
    """Load storyboard JSON and return list of segment dicts."""
    path = Path(storyboard_path)
    if not path.exists():
        raise FileNotFoundError(f"Storyboard not found: {path}")
    return json.loads(path.read_text())


def _group_storyboard_by_query(storyboard: list) -> dict:
    """
    Group storyboard segments by search_query.
    Returns: {search_query: [segment_dicts]}
    Skips chapter cards and segments with no search_query.
    """
    groups: dict[str, list] = {}
    for i, seg in enumerate(storyboard):
        if seg.get("shot_type") == "chapter_card":
            continue
        query = seg.get("search_query", "").strip()
        if not query:
            continue
        seg = {**seg, "segment_index": i}
        if query not in groups:
            groups[query] = []
        groups[query].append(seg)
    return groups


def source_footage_from_storyboard(
    storyboard: list,
    broad_query: str,
    entities: dict,
    brand_id: str,
    output_dir: Path,
    download: bool = False,
    preview_only: bool = False,
) -> dict:
    """
    Story-driven footage sourcing using a storyboard.

    For each unique search_query in the storyboard:
      - Searches YouTube + Internet Archive + Wikimedia
      - Tags results with which segment_ids they serve
      - Prefers Wikimedia images for document_photo/documentary_photo shot types
      - Prefers YouTube/Archive for archival_footage/news_footage shot types

    Also runs the broad topic search as a fallback pool.
    """
    slug = slugify(broad_query)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"FOOTAGE SOURCER (storyboard-driven): {broad_query[:50]}")
    print(f"{'='*60}\n")

    groups = _group_storyboard_by_query(storyboard)
    print(f"Storyboard: {len(storyboard)} segments → {len(groups)} unique search queries\n")

    # Track all clips and images with their storyboard tags
    all_clips: list[dict] = []
    all_images: list[dict] = []

    # ── 1. Per-segment targeted searches ──
    for query, segs in groups.items():
        seg_indices = [s["segment_index"] for s in segs]
        shot_types = list({s.get("shot_type", "") for s in segs})
        show_desc = segs[0].get("show", "")

        print(f"  [{', '.join(str(i) for i in seg_indices[:3])}{'...' if len(seg_indices)>3 else ''}] "
              f"{query[:50]}  ({shot_types[0]})")

        needs_video = any(st in ("archival_footage", "news_footage") for st in shot_types)
        needs_image = any(st in ("document_photo", "documentary_photo", "person_photo", "map") for st in shot_types)

        # Video sources (YouTube + Archive)
        if needs_video or not needs_image:
            yt_clips = search_youtube(query, max_results=4)
            for c in yt_clips:
                c["storyboard_segment_ids"] = seg_indices
                c["storyboard_show"] = show_desc
            all_clips.extend(yt_clips)
            time.sleep(0.3)

            ia_clips = search_internet_archive(query, max_results=3)
            for c in ia_clips:
                c["storyboard_segment_ids"] = seg_indices
                c["storyboard_show"] = show_desc
            all_clips.extend(ia_clips)

        # Image sources (Wikimedia Commons)
        if needs_image or not needs_video:
            imgs = search_wikimedia_images(query, max_results=15)
            for img in imgs:
                img["storyboard_segment_ids"] = seg_indices
                img["storyboard_show"] = show_desc
            all_images.extend(imgs)
            time.sleep(0.3)

    # ── 2. Broad fallback search (covers any untagged segments) ──
    print(f"\nBroad fallback: '{broad_query[:50]}'...")
    fallback_clips = search_youtube(broad_query, max_results=8)
    all_clips.extend(fallback_clips)  # no storyboard_tags — fallback only

    fallback_images = source_wikimedia_for_story(
        broad_query, entities, output_dir,
        download=False, max_images=20,
    )
    all_images.extend(fallback_images)

    # ── Score, deduplicate ──
    print(f"\nScoring {len(all_clips)} video clips + {len(all_images)} images...")
    seen_urls = set()
    unique_clips = []
    for c in all_clips:
        url = c.get("url", c.get("id", ""))
        if url not in seen_urls:
            seen_urls.add(url)
            c["relevance_score"] = score_clip(c, broad_query, entities)
            unique_clips.append(c)
    unique_clips.sort(key=lambda c: (
        len(c.get("storyboard_segment_ids", [])) > 0,  # tagged clips first
        c["relevance_score"]
    ), reverse=True)
    top_clips = unique_clips[:MAX_TOTAL_CLIPS]

    seen_img_urls = set()
    unique_images = []
    for img in all_images:
        url = img.get("url", "")
        if url and url not in seen_img_urls:
            seen_img_urls.add(url)
            unique_images.append(img)
    unique_images = unique_images[:60]

    # ── Guardrail: flag segments with zero coverage ──
    needs_animation = []
    if storyboard:
        for i, seg in enumerate(storyboard):
            if seg.get("shot_type") == "chapter_card":
                continue
            has_clip  = any(i in c.get("storyboard_segment_ids", []) for c in unique_clips)
            has_image = any(i in img.get("storyboard_segment_ids", []) for img in unique_images)
            if not has_clip and not has_image:
                needs_animation.append({
                    "segment_index": i,
                    "show": seg.get("show", ""),
                    "shot_type": seg.get("shot_type", "documentary_photo"),
                    "focal_element": seg.get("focal_element", ""),
                    "search_query": seg.get("search_query", ""),
                    "text": seg.get("text", ""),
                })

    # ── Summary ──
    tagged_clips  = sum(1 for c in top_clips  if c.get("storyboard_segment_ids"))
    tagged_images = sum(1 for i in unique_images if i.get("storyboard_segment_ids"))
    print(f"\n{'='*60}")
    print(f"ASSET SUMMARY")
    print(f"{'='*60}")
    print(f"  Video clips: {len(top_clips)} ({tagged_clips} story-tagged)")
    print(f"  Images:      {len(unique_images)} ({tagged_images} story-tagged)")
    if needs_animation:
        print(f"  NEEDS ANIMATION: {len(needs_animation)} segment(s) have no footage found")
        print(f"    Run: python pipeline/animation_generator.py --manifest footage/{{brand}}/{{topic}}/manifest.json")
    else:
        print(f"  Coverage: all story segments have footage ✓")

    if preview_only:
        print("\n[Preview — use --download to fetch assets]")
        return _save_manifest(top_clips, unique_images, broad_query, slug, brand_id, output_dir,
                              needs_animation=needs_animation)

    # ── Download ──
    if download:
        print(f"\nDownloading top {min(12, len(top_clips))} clips...")
        for i, clip in enumerate(top_clips[:12]):
            tag = f"segs {clip['storyboard_segment_ids']}" if clip.get("storyboard_segment_ids") else "fallback"
            print(f"  [{i+1}/12] [{tag}] {clip['title'][:50]}...")
            updated = download_clip(clip, output_dir)
            top_clips[i] = updated
            status = f"✅ {updated.get('file_size_mb','?')}MB" if updated.get("downloaded") else f"⚠ {updated.get('error','')[:40]}"
            print(f"    {status}")
            time.sleep(1.0)

        print(f"\nDownloading {len(unique_images)} images...")
        img_dir = output_dir / "images"
        img_dir.mkdir(exist_ok=True)
        downloaded_imgs = []
        for img in unique_images:
            result = download_wikimedia_image(img, img_dir)
            downloaded_imgs.append(result)
            if result.get("downloaded") and not result.get("cached"):
                time.sleep(0.2)
        ok = sum(1 for r in downloaded_imgs if r.get("downloaded"))
        print(f"  Images downloaded: {ok}/{len(unique_images)}")
        unique_images = downloaded_imgs

    return _save_manifest(top_clips, unique_images, broad_query, slug, brand_id, output_dir,
                          needs_animation=needs_animation)


# ── Relevance scoring ──────────────────────────────────────────────────────────

def score_clip(clip: dict, query: str, entities: dict) -> int:
    """Score a clip for relevance to the story."""
    title = clip.get("title", "").lower()
    channel = clip.get("channel", "").lower()
    score = 0

    # Title relevance
    query_words = set(w.lower() for w in query.split() if len(w) > 3)
    title_words = set(re.findall(r"\b\w{4,}\b", title))
    overlap = len(query_words & title_words) / max(len(query_words), 1)
    score += int(overlap * 30)

    # Entity matches in title
    for agency in entities.get("agencies", []):
        if agency.lower() in title:
            score += 15
    for person in entities.get("people_orgs", [])[:5]:
        if any(w.lower() in title for w in person.split() if len(w) > 4):
            score += 10
    for year in entities.get("years", []):
        if year in title:
            score += 5

    # Channel quality bonus (Tier 1 channels get priority)
    tier1 = {"ap archive", "reuters", "c-span", "cspan"}
    tier2 = {"bbc", "pbs", "abc news"}
    if any(t in channel for t in tier1):
        score += 20
    elif any(t in channel for t in tier2):
        score += 10

    # Duration sweet spot: 30s–3min = ideal news clips
    duration = clip.get("duration_sec", 0)
    if 30 <= duration <= 180:
        score += 10
    elif duration <= 30:
        score -= 5

    # Internet Archive: high downloads = proven quality
    if clip.get("source") == "internet_archive":
        score += min(clip.get("downloads", 0) // 1000, 15)

    return max(0, score)


def deduplicate_clips(clips: list) -> list:
    """Remove near-duplicate clips (same title keywords)."""
    seen = []
    unique = []
    for clip in clips:
        words = set(re.findall(r"\b\w{5,}\b", clip.get("title", "").lower()))
        is_dup = any(
            len(words & seen_words) / max(len(words), 1) > 0.6
            for seen_words in seen
        )
        if not is_dup:
            seen.append(words)
            unique.append(clip)
    return unique


# ── Download ──────────────────────────────────────────────────────────────────

def download_clip(clip: dict, output_dir: Path, quality: str = "720") -> dict:
    """
    Download a single clip. Returns updated clip dict with local path.
    quality: "480", "720", "1080" — we want 720p max for storage efficiency.
    """
    url = clip.get("url") or clip.get("download_url", "")
    if not url:
        return {**clip, "downloaded": False, "error": "no url"}

    # Safe filename from title
    safe_name = re.sub(r"[^\w\s-]", "", clip.get("title", clip.get("id", "unknown")))
    safe_name = re.sub(r"\s+", "_", safe_name)[:60]
    output_path = output_dir / f"{safe_name}.%(ext)s"

    if clip.get("source") == "internet_archive":
        # Internet Archive: get the best available video file
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--no-playlist",
            f"--format", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "--output", str(output_path),
            url,
        ]
    else:
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--no-playlist",
            f"--format", f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best",
            "--merge-output-format", "mp4",
            "--output", str(output_path),
            url,
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        # Find the actual output file
        downloaded_files = list(output_dir.glob(f"{safe_name}.*"))
        if downloaded_files:
            local_path = str(downloaded_files[0])
            file_size_mb = downloaded_files[0].stat().st_size / 1_048_576
            return {**clip, "downloaded": True, "local_path": local_path,
                    "file_size_mb": round(file_size_mb, 1)}
        else:
            return {**clip, "downloaded": False, "error": result.stderr[-200:]}
    except subprocess.TimeoutExpired:
        return {**clip, "downloaded": False, "error": "download timeout"}
    except Exception as e:
        return {**clip, "downloaded": False, "error": str(e)}


# ── Main sourcing logic ───────────────────────────────────────────────────────

def source_footage(query: str, entities: dict, brand_id: str,
                   download: bool = False, preview_only: bool = False) -> dict:
    """
    Find (and optionally download) footage for a story query.
    Returns manifest of all found clips.
    """
    slug = slugify(query)
    output_dir = Path(f"footage/{brand_id}/{slug}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"FOOTAGE SOURCER: {query[:55]}")
    print(f"{'='*60}\n")

    all_clips = []
    years = entities.get("years", [])
    agencies = entities.get("agencies", [])
    countries = entities.get("countries", [])

    # ── 1. Tier 1 news channels (AP Archive, Reuters, C-SPAN) ──
    print("Searching AP Archive, Reuters, C-SPAN...")
    for channel_name, channel_prefix, tier in NEWS_CHANNELS:
        if tier > 1 or channel_prefix is None:
            continue
        clips = search_youtube(query, channel_prefix, max_results=5)
        all_clips.extend(clips)
        time.sleep(0.5)

    # Also search without channel prefix to cast wider net
    print("Searching YouTube (broad)...")
    broad_clips = search_youtube(query, max_results=8)
    all_clips.extend(broad_clips)
    time.sleep(0.5)

    # ── 2. Internet Archive ──
    print("Searching Internet Archive...")
    ia_clips = search_internet_archive(query, max_results=10)
    all_clips.extend(ia_clips)

    # Also search by year for archival footage
    if years:
        oldest_year = int(years[0])
        if oldest_year < 2000:  # Old enough to have archive footage
            print(f"  Searching Archive for {oldest_year}s footage...")
            ia_year_clips = search_internet_archive(
                f"{query} {oldest_year}s", year_from=oldest_year - 5, max_results=5
            )
            all_clips.extend(ia_year_clips)
    time.sleep(0.5)

    # ── 3. Agency-specific searches (only if agency not already in query) ──
    for agency in agencies[:2]:
        if agency.lower() not in query.lower():
            print(f"Searching '{agency} {query[:30]}' on YouTube...")
            clips = search_youtube(f"{agency} {query}", max_results=3)
            all_clips.extend(clips)
            time.sleep(0.5)

    # ── 4. Tier 2 channels (BBC, PBS) ──
    print("Searching BBC, PBS NewsHour...")
    for channel_name, channel_prefix, tier in NEWS_CHANNELS:
        if tier != 2:
            continue
        clips = search_youtube(query, channel_prefix, max_results=2)
        all_clips.extend(clips)
        time.sleep(0.5)

    # ── Score, deduplicate, rank video clips ──
    print(f"\nScoring {len(all_clips)} video clips...")
    for clip in all_clips:
        clip["relevance_score"] = score_clip(clip, query, entities)

    all_clips.sort(key=lambda c: c["relevance_score"], reverse=True)
    all_clips = deduplicate_clips(all_clips)
    top_clips = all_clips[:MAX_TOTAL_CLIPS]

    # ── 5. Wikimedia Commons still images (57% of Fern's visual mix) ──
    print("\nSearching Wikimedia Commons for still images...")
    wiki_images = source_wikimedia_for_story(
        query, entities, output_dir,
        download=download,
        max_images=40,
    )

    # ── Print summary ──
    print(f"\n{'='*60}")
    print(f"ASSET SUMMARY")
    print(f"{'='*60}")
    print(f"  Video clips found:    {len(top_clips)}")
    print(f"  Still images found:   {len(wiki_images)} (Wikimedia Commons)")
    print(f"\nTop video candidates:")
    for i, clip in enumerate(top_clips[:8], 1):
        duration = int(clip.get("duration_sec") or 0)
        dur_str = f"{duration//60}:{duration%60:02d}" if duration else "?:??"
        source_tag = clip.get("source", "youtube")[:2].upper()
        print(f"  {i:2}. [{clip['relevance_score']:3}] [{source_tag}] {clip['title'][:60]}")
        print(f"      {clip.get('channel','')[:30]} | {dur_str}")

    if wiki_images:
        print(f"\nTop still images (Wikimedia):")
        for img in wiki_images[:5]:
            w, h = img.get("width", 0), img.get("height", 0)
            print(f"  • {img['title'][:60]}")
            print(f"    {w}×{h}px | {img.get('license','?')} | {img.get('description','')[:60]}")

    if preview_only:
        print("\n[Preview only — use --download to fetch assets]")
        manifest = _save_manifest(top_clips, wiki_images, query, slug, brand_id, output_dir)
        return manifest

    # ── Download top video clips ──
    if download:
        print(f"\nDownloading top {min(10, len(top_clips))} video clips...")
        for i, clip in enumerate(top_clips[:10]):
            print(f"  [{i+1}/10] {clip['title'][:55]}...")
            updated = download_clip(clip, output_dir)
            top_clips[i] = updated
            if updated.get("downloaded"):
                print(f"    ✅ {updated.get('file_size_mb', '?')}MB → {Path(updated['local_path']).name}")
            else:
                print(f"    ⚠ Failed: {updated.get('error', '')[:60]}")
            time.sleep(1.0)

    manifest = _save_manifest(top_clips, wiki_images, query, slug, brand_id, output_dir)
    return manifest


def _save_manifest(clips: list, images: list, query: str, slug: str,
                   brand_id: str, output_dir: Path,
                   needs_animation: list | None = None) -> dict:
    """Save footage manifest to disk — includes both video clips and still images."""
    downloaded_clips  = [c for c in clips  if c.get("downloaded")]
    downloaded_images = [i for i in images if i.get("downloaded")]

    # video_assembler expects a flat "clips" list with type field
    all_assets = []
    for c in clips:
        all_assets.append({**c, "asset_type": "video"})
    for img in images:
        all_assets.append({**img, "asset_type": "image",
                           "type": "image"})   # assembler key

    manifest = {
        "query": query,
        "brand_id": brand_id,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "video_clips_found":    len(clips),
            "video_clips_downloaded": len(downloaded_clips),
            "images_found":         len(images),
            "images_downloaded":    len(downloaded_images),
            "needs_animation_count": len(needs_animation) if needs_animation else 0,
        },
        "needs_animation": needs_animation or [],
        "visual_mix_note": (
            "Fern target: 57% document_photo, 20% documentary_photo, "
            "6% news_screenshot, 4% archival. Wikimedia images cover the first two. "
            "Low image count → use animated text cards + AI-generated visuals."
        ),
        "output_dir": str(output_dir),
        "clips": all_assets,
    }
    manifest_file = output_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\n✅ Manifest: {manifest_file}")
    print(f"   {len(clips)} video clips | {len(images)} images | "
          f"{len(downloaded_clips)+len(downloaded_images)} downloaded")
    return manifest


# ── Entry point ───────────────────────────────────────────────────────────────

def run_from_brief(brief_slug: str, brand_id: str, download: bool, preview: bool):
    """Run footage sourcing using entities from a research brief."""
    brief = load_brief(brand_id, brief_slug)
    query = brief.get("query", brief_slug)
    entities = brief.get("entities", {})

    print(f"Loading brief: {query[:60]}")
    print(f"Entities: agencies={entities.get('agencies')}, "
          f"years={entities.get('years')}, "
          f"people={entities.get('people_orgs', [])[:2]}")

    return source_footage(query, entities, brand_id, download=download, preview_only=preview)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Footage Sourcer — finds and downloads story footage")
    parser.add_argument("--brand", required=True, help="Brand config ID (e.g. fern_clone)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brief", help="Research brief slug (from research/{brand}/briefs/)")
    group.add_argument("--query", help="Direct search query")
    parser.add_argument("--storyboard", help="Path to storyboard.json — enables story-driven targeted searches")
    parser.add_argument("--download", action="store_true", help="Download top clips and images")
    parser.add_argument("--preview", action="store_true", help="Preview only, no download")
    args = parser.parse_args()

    if args.brief:
        brief = load_brief(args.brand, args.brief)
        query = brief.get("query", args.brief)
        entities = brief.get("entities", {})
    else:
        query = args.query
        entities = {}

    if args.storyboard:
        storyboard = load_storyboard(args.storyboard)
        slug = slugify(query)
        out_dir = Path(f"footage/{args.brand}/{slug}")
        source_footage_from_storyboard(
            storyboard, query, entities, args.brand, out_dir,
            download=args.download, preview_only=args.preview,
        )
    else:
        source_footage(query, entities, args.brand,
                       download=args.download, preview_only=args.preview)
