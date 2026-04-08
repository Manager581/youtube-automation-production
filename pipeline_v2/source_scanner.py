#!/usr/bin/env python3
"""
Source Scanner — fast pre-check of available footage BEFORE committing to a topic.

Takes a research brief (with entities + footage_leads) and runs lightweight
YouTube/Archive searches to count and score what's available. No downloads.
Returns a source_inventory.json that the story_validator and topic_scorer use.

This runs in ~2-3 minutes (vs 30+ min for full sourcing) and answers:
  - Are there enough clips with usable audio (interviews, news anchors)?
  - Are there diverse sources (not just one outlet)?
  - Is there primary source footage (hearings, press conferences)?
  - What are the best clip audio candidates?

Usage:
  python -m pipeline_v2.source_scanner --brief research/learnbyleo/briefs/breaking_law.json
  python -m pipeline_v2.source_scanner --topic "Why Breaking the Law Is Profitable"
  python -m pipeline_v2.source_scanner --topic "Facebook fine" --entities '{"people_orgs":["Mark Zuckerberg","FTC"]}'
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
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Scoring thresholds (calibrated against successful documentary videos) ──

# Minimum viable sources for a documentary
MIN_CLIPS_WITH_AUDIO = 3    # clips where someone is speaking (interviews, news anchors)
MIN_UNIQUE_SOURCES = 2      # different outlets/channels
MIN_TOTAL_CLIPS = 8         # total video clips found
MIN_IMAGES = 10             # still images (screenshots, charts, photos)

# Ideal targets (for a "source-rich" topic)
IDEAL_CLIPS_WITH_AUDIO = 8
IDEAL_UNIQUE_SOURCES = 5
IDEAL_TOTAL_CLIPS = 20

# YouTube search config
MAX_RESULTS_PER_QUERY = 8
SEARCH_TIMEOUT = 20
MAX_CLIP_DURATION = 600     # 10 min — longer is usually full documentaries, not clips

# News channels that produce reusable footage (same as footage_sourcer.py)
NEWS_CHANNELS = [
    "Reuters", "AP Archive", "BBC News", "CNN", "C-SPAN",
    "ABC News", "NBC News", "CBS News", "PBS NewsHour",
    "Al Jazeera English", "Bloomberg Television", "CNBC",
    "The Guardian", "Vice News", "60 Minutes",
]

# Channel keywords that indicate high-quality primary footage
PRIMARY_SOURCE_CHANNELS = {
    "c-span", "cspan", "senate", "congress", "house",
    "white house", "united nations", "european parliament",
    "ap archive", "reuters", "associated press",
}

# Title keywords indicating interview/testimony footage
INTERVIEW_KEYWORDS = [
    "interview", "testimony", "hearing", "deposition", "press conference",
    "speaks", "explains", "responds", "reacts", "testif",
    "senate hearing", "congressional", "whistleblower",
]


def search_youtube_quick(query, max_results=MAX_RESULTS_PER_QUERY):
    """Quick YouTube search via yt-dlp. Returns metadata without downloading."""
    cmd = [
        "yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings",
        f"ytsearch{max_results}:{query}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=SEARCH_TIMEOUT)
        videos = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                duration = d.get("duration") or 0
                if duration > MAX_CLIP_DURATION or duration < 5:
                    continue
                title = d.get("title", "")
                channel = (d.get("channel") or d.get("uploader", "")).lower()

                # Score this result
                is_news = any(nc.lower() in channel for nc in NEWS_CHANNELS)
                is_primary = any(kw in channel for kw in PRIMARY_SOURCE_CHANNELS)
                has_interview = any(kw in title.lower() for kw in INTERVIEW_KEYWORDS)
                view_count = d.get("view_count") or 0

                videos.append({
                    "id": d.get("id", ""),
                    "title": title,
                    "channel": d.get("channel") or d.get("uploader", ""),
                    "duration_sec": duration,
                    "view_count": view_count,
                    "url": f"https://youtu.be/{d.get('id', '')}",
                    "search_query": query,
                    "is_news": is_news,
                    "is_primary_source": is_primary,
                    "has_interview_keywords": has_interview,
                    "likely_has_speech": is_news or has_interview or duration < 180,
                })
            except json.JSONDecodeError:
                continue
        return videos
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []


def search_internet_archive_quick(query, max_results=5):
    """Quick Internet Archive search for video content."""
    encoded = urllib.parse.quote(f"{query} AND mediatype:movies")
    url = f"https://archive.org/advancedsearch.php?q={encoded}&fl[]=identifier,title,mediatype,year&rows={max_results}&output=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        results = []
        for doc in data.get("response", {}).get("docs", []):
            results.append({
                "id": doc.get("identifier", ""),
                "title": doc.get("title", ""),
                "year": doc.get("year"),
                "source": "internet_archive",
                "url": f"https://archive.org/details/{doc.get('identifier', '')}",
            })
        return results
    except Exception:
        return []


def search_wikimedia_quick(query, max_results=10):
    """Quick Wikimedia Commons image count."""
    encoded = urllib.parse.quote(query)
    url = (f"https://commons.wikimedia.org/w/api.php?action=query&list=search"
           f"&srsearch={encoded}&srnamespace=6&srlimit={max_results}&format=json")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        total = data.get("query", {}).get("searchinfo", {}).get("totalhits", 0)
        results = data.get("query", {}).get("search", [])
        return total, len(results)
    except Exception:
        return 0, 0


def build_search_queries(topic, entities=None, footage_leads=None):
    """Build search queries from topic + entities + footage_leads."""
    queries = []

    # Core topic query
    queries.append({"query": topic, "source": "topic", "priority": "high"})

    # Entity-based queries
    if entities:
        for person in entities.get("people_orgs", [])[:5]:
            queries.append({
                "query": f"{person} {topic.split()[0]}",
                "source": "entity_person",
                "priority": "high",
            })
        for agency in entities.get("agencies", [])[:3]:
            queries.append({
                "query": f"{agency} {topic.split()[0]}",
                "source": "entity_agency",
                "priority": "medium",
            })
        for year in entities.get("years", [])[-3:]:
            queries.append({
                "query": f"{topic.split()[0]} {year}",
                "source": "entity_year",
                "priority": "low",
            })

    # Footage leads (from research brief)
    if footage_leads:
        for lead in footage_leads[:8]:
            if lead.get("type", "").startswith("youtube"):
                queries.append({
                    "query": lead["query"],
                    "source": "footage_lead",
                    "priority": "high",
                })

    # Deduplicate by query text
    seen = set()
    unique = []
    for q in queries:
        key = q["query"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)

    return unique


def score_inventory(all_clips, archive_results, wikimedia_total, wikimedia_found):
    """Score the source inventory. Returns dict with scores and profile."""
    # Count clips with likely speech
    clips_with_speech = [c for c in all_clips if c.get("likely_has_speech")]
    news_clips = [c for c in all_clips if c.get("is_news")]
    primary_clips = [c for c in all_clips if c.get("is_primary_source")]
    interview_clips = [c for c in all_clips if c.get("has_interview_keywords")]

    # Unique sources (channels)
    unique_channels = len(set(c.get("channel", "").lower() for c in all_clips if c.get("channel")))

    # Score components (0-100 each)
    clip_count_score = min(100, (len(all_clips) / IDEAL_TOTAL_CLIPS) * 100)
    speech_score = min(100, (len(clips_with_speech) / IDEAL_CLIPS_WITH_AUDIO) * 100)
    diversity_score = min(100, (unique_channels / IDEAL_UNIQUE_SOURCES) * 100)
    primary_score = min(100, len(primary_clips) * 25)  # 4+ primary = 100
    interview_score = min(100, len(interview_clips) * 20)  # 5+ interviews = 100
    image_score = min(100, (wikimedia_total / 30) * 100)

    # Weighted overall
    overall = (
        clip_count_score * 0.20 +
        speech_score * 0.25 +
        diversity_score * 0.15 +
        primary_score * 0.15 +
        interview_score * 0.15 +
        image_score * 0.10
    )

    # Determine footage profile
    if len(clips_with_speech) >= IDEAL_CLIPS_WITH_AUDIO and unique_channels >= IDEAL_UNIQUE_SOURCES:
        profile = "source-rich"
    elif len(clips_with_speech) >= MIN_CLIPS_WITH_AUDIO and unique_channels >= MIN_UNIQUE_SOURCES:
        profile = "source-moderate"
    else:
        profile = "narration-heavy"

    # Best clip audio candidates (top 8 by view count, must have speech)
    clip_audio_candidates = sorted(
        clips_with_speech,
        key=lambda c: c.get("view_count", 0),
        reverse=True,
    )[:8]

    return {
        "overall_score": round(overall),
        "footage_profile": profile,
        "scores": {
            "clip_count": round(clip_count_score),
            "clips_with_speech": round(speech_score),
            "source_diversity": round(diversity_score),
            "primary_sources": round(primary_score),
            "interview_footage": round(interview_score),
            "images_available": round(image_score),
        },
        "counts": {
            "total_clips": len(all_clips),
            "clips_with_speech": len(clips_with_speech),
            "news_clips": len(news_clips),
            "primary_source_clips": len(primary_clips),
            "interview_clips": len(interview_clips),
            "unique_channels": unique_channels,
            "archive_results": len(archive_results),
            "wikimedia_images": wikimedia_total,
        },
        "clip_audio_candidates": [
            {
                "title": c["title"][:60],
                "channel": c["channel"],
                "duration": c["duration_sec"],
                "views": c["view_count"],
                "url": c["url"],
            }
            for c in clip_audio_candidates
        ],
        "verdict": "GO" if overall >= 60 else ("NEEDS_WORK" if overall >= 35 else "SKIP"),
    }


def scan_sources(topic, entities=None, footage_leads=None, verbose=True):
    """Run the full source scan. Returns inventory dict."""
    queries = build_search_queries(topic, entities, footage_leads)
    if verbose:
        print(f"  Source scan: {len(queries)} search queries")

    all_clips = []
    seen_ids = set()

    # YouTube searches
    yt_queries = [q for q in queries if q["source"] != "entity_year"]
    for i, q in enumerate(yt_queries):
        if verbose:
            print(f"  [{i+1}/{len(yt_queries)}] YouTube: {q['query'][:50]}...")
        results = search_youtube_quick(q["query"])
        for clip in results:
            if clip["id"] not in seen_ids:
                seen_ids.add(clip["id"])
                all_clips.append(clip)
        time.sleep(0.5)  # rate limit

    if verbose:
        print(f"  YouTube: {len(all_clips)} unique clips found")

    # Internet Archive
    archive_results = search_internet_archive_quick(topic)
    if verbose:
        print(f"  Archive.org: {len(archive_results)} results")

    # Wikimedia
    wiki_total, wiki_found = search_wikimedia_quick(topic)
    if verbose:
        print(f"  Wikimedia: {wiki_total} total images ({wiki_found} previewed)")

    # Score everything
    scoring = score_inventory(all_clips, archive_results, wiki_total, wiki_found)

    inventory = {
        "topic": topic,
        "entities_used": entities,
        "queries_run": len(queries),
        "scan_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "clips": all_clips,
        "archive_results": archive_results,
        "wikimedia_total": wiki_total,
        **scoring,
    }

    return inventory


def main():
    parser = argparse.ArgumentParser(description="Source Scanner — fast footage availability check")
    parser.add_argument("--topic", type=str, help="Topic to scan")
    parser.add_argument("--brief", type=str, help="Path to research brief JSON")
    parser.add_argument("--entities", type=str, help="JSON string of entities")
    parser.add_argument("--output", type=str, default=None, help="Output path for inventory JSON")
    args = parser.parse_args()

    topic = args.topic
    entities = None
    footage_leads = None

    # Load from brief if provided
    if args.brief:
        brief_path = Path(args.brief)
        if brief_path.exists():
            with open(brief_path) as f:
                brief = json.load(f)
            topic = topic or brief.get("query", "")
            entities = brief.get("entities")
            footage_leads = brief.get("footage_leads")
        else:
            print(f"ERROR: Brief not found: {brief_path}")
            sys.exit(1)

    if args.entities:
        entities = json.loads(args.entities)

    if not topic:
        print("ERROR: Provide --topic or --brief")
        sys.exit(1)

    print(f"\nSource Scanner")
    print(f"  Topic: {topic}")
    if entities:
        print(f"  Entities: {len(entities.get('people_orgs', []))} people/orgs, "
              f"{len(entities.get('agencies', []))} agencies")
    print()

    inventory = scan_sources(topic, entities, footage_leads)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  SOURCE SCAN RESULTS")
    print(f"{'='*60}")
    print(f"  Overall score:     {inventory['overall_score']}/100")
    print(f"  Footage profile:   {inventory['footage_profile']}")
    print(f"  Verdict:           {inventory['verdict']}")
    print()
    print(f"  Total clips:       {inventory['counts']['total_clips']}")
    print(f"  With speech:       {inventory['counts']['clips_with_speech']}")
    print(f"  News clips:        {inventory['counts']['news_clips']}")
    print(f"  Primary source:    {inventory['counts']['primary_source_clips']}")
    print(f"  Interview footage: {inventory['counts']['interview_clips']}")
    print(f"  Unique channels:   {inventory['counts']['unique_channels']}")
    print(f"  Archive results:   {inventory['counts']['archive_results']}")
    print(f"  Wikimedia images:  {inventory['counts']['wikimedia_images']}")

    if inventory["clip_audio_candidates"]:
        print(f"\n  Top clip audio candidates:")
        for c in inventory["clip_audio_candidates"][:5]:
            print(f"    {c['views']:>8,} views  {c['duration']:>4}s  {c['channel'][:20]:20s}  {c['title']}")

    # Save
    output_path = Path(args.output) if args.output else PROJECT_ROOT / "storyboards" / "source_inventory.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(inventory, f, indent=2)
    print(f"\n  Saved: {output_path}")

    sys.exit(0 if inventory["verdict"] != "SKIP" else 1)


if __name__ == "__main__":
    main()
