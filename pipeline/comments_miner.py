#!/usr/bin/env python3
"""
Comments Miner — extracts topic signals and curiosity gaps from YouTube comments.

Three high-value comment sources:
  1. Fern's own videos  → what the audience wants next + curiosity gap patterns
  2. Competitor channels → trending investigative topics
  3. Specific video IDs → deep-dive on a story we're considering

Usage:
    # Mine Fern's channel (uses video IDs from brand config)
    python pipeline/comments_miner.py --brand fern_clone

    # Mine a specific video
    python pipeline/comments_miner.py --brand fern_clone --video VIDEO_ID

    # Mine with YouTube Data API key (faster, more comments)
    YOUTUBE_API_KEY=... python pipeline/comments_miner.py --brand fern_clone

Output:
    research/{brand_id}/comment_signals.json — ranked signals extracted from comments
"""

import json
import re
import os
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict


# ── Config ────────────────────────────────────────────────────────────────────

def load_brand(brand_id: str) -> dict:
    path = Path(f"brand_configs/{brand_id}.json")
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")
    return json.loads(path.read_text())


# ── YouTube API (with key) ─────────────────────────────────────────────────────

def fetch_comments_api(video_id: str, api_key: str, max_results: int = 100) -> list:
    """Fetch top-level comments via YouTube Data API v3. Costs 1 unit per page."""
    comments = []
    page_token = None

    while len(comments) < max_results:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(100, max_results - len(comments)),
            "order": "relevance",  # top comments, not chronological
            "textFormat": "plainText",
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        url = "https://www.googleapis.com/youtube/v3/commentThreads?" + urllib.parse.urlencode(params)

        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  ⚠ API error for {video_id}: {e}")
            break

        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": snippet.get("textDisplay", ""),
                "likes": snippet.get("likeCount", 0),
                "replies": item["snippet"].get("totalReplyCount", 0),
                "published": snippet.get("publishedAt", ""),
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.2)

    return comments


def fetch_video_ids_for_channel(channel_id: str, api_key: str, max_videos: int = 10) -> list:
    """Get recent video IDs from a channel. Costs 100 units per call."""
    params = {
        "part": "id",
        "channelId": channel_id,
        "maxResults": max_videos,
        "order": "viewCount",
        "type": "video",
        "key": api_key,
    }
    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        return [item["id"]["videoId"] for item in data.get("items", [])]
    except Exception as e:
        print(f"  ⚠ Channel search error: {e}")
        return []


# ── yt-dlp fallback (no API key) ──────────────────────────────────────────────

def fetch_comments_ytdlp(video_id: str, max_comments: int = 200) -> list:
    """Fetch comments via yt-dlp. Slower but requires no API key."""
    import subprocess

    out_path = f"/tmp/ytdlp_cm_{video_id}"
    info_file = f"{out_path}.info.json"

    cmd = [
        "yt-dlp",
        "--write-comments",
        "--skip-download",
        "--no-playlist",
        "--extractor-args", f"youtube:max_comments={max_comments}",
        "--output", out_path,
        f"https://www.youtube.com/watch?v={video_id}",
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if Path(info_file).exists():
            data = json.loads(Path(info_file).read_text())
            raw_comments = data.get("comments", [])
            return [
                {
                    "text": c.get("text", ""),
                    "likes": c.get("like_count", 0),
                    "replies": c.get("reply_count", 0),
                    "published": c.get("timestamp", ""),
                }
                for c in raw_comments
                if c.get("parent") == "root"  # top-level only
            ]
    except subprocess.TimeoutExpired:
        print(f"  ⚠ yt-dlp timeout for {video_id}")
    except Exception as e:
        print(f"  ⚠ yt-dlp error for {video_id}: {e}")

    return []


def check_ytdlp() -> bool:
    """Check if yt-dlp is available."""
    import subprocess
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


# ── Signal extraction ──────────────────────────────────────────────────────────

# Patterns that signal a viewer WANTS MORE on a topic (= curiosity gap / next topic signal)
_WANT_MORE_PATTERNS = [
    r"\bplease\b.{0,50}\b(video|episode|part|cover|do|make)\b",
    r"\b(more|next).{0,40}\b(video|episode|part|story|content)\b",
    r"\bwhat happened to\b",
    r"\bpart\s*2\b",
    r"\bfollow.?up\b",
    r"\bsomeone should\b.{0,40}\b(video|doc|cover|make)\b",
    r"\bcan you (do|make|cover|please).{0,40}",
    r"\bi('d| would) (love|like).{0,50}\b(video|episode|more|part)\b",
    r"\bneed.{0,30}\bvideo\b",
    r"\bdo (a|an|one).{0,30}\b(video|episode|on)\b",
    r"\bwish (you|there).{0,40}\b(video|episode|covered)\b",
]

# Patterns that signal strong emotional engagement (= viral angle confirmed)
_ENGAGEMENT_PATTERNS = [
    r"\bblew my mind\b",
    r"\bnever knew\b",
    r"\bi had no idea\b",
    r"\b(this|that) is (so )?(insane|crazy|wild|unbelievable|mind.?blow)\b",
    r"\bhow is (this|he|she|it|that) not\b.{0,40}(known|talked about|viral)\b",
    r"\b(should be|deserves) (more|bigger|viral|everywhere)\b",
    r"\beveryone (should|needs to) (see|watch|know)\b",
    r"\bwhy (isn't|aren't|don't|doesn't) (more )?people\b",
    r"\bunder(reported|covered|rated)\b",
    r"\bmore people (need|should)\b",
    r"\bso (underrated|unknown|overlooked)\b",
]

# Patterns for topic suggestions in comments (= research leads)
_TOPIC_SUGGESTION_PATTERNS = [
    r"\byou should (do|cover|make|look into).{0,80}",
    r"\bdo (a|an|one).{0,10}(video|episode) (on|about).{0,80}",
    r"\bnext (video|episode).{0,20}(do|cover|make|about|on).{0,80}",
    r"\bi (want|wish|would love).{0,20}(video|episode|part|content).{0,80}",
    r"\bcover.{0,80}(next|please|soon)\b",
    r"\bwhat about.{3,80}\?",
    r"\bhow about.{3,80}\?",
]


def extract_signals(comment: dict, brand: dict) -> dict | None:
    """Extract signals from a single comment. Returns None if no signal found."""
    text = comment["text"].lower().strip()
    if len(text) < 20:
        return None

    signals = []
    signal_types = []

    for pattern in _WANT_MORE_PATTERNS:
        if re.search(pattern, text):
            signals.append("want_more")
            signal_types.append("want_more")
            break

    for pattern in _ENGAGEMENT_PATTERNS:
        if re.search(pattern, text):
            signals.append("high_engagement")
            signal_types.append("high_engagement")
            break

    # Extract topic suggestions (longer, specific comments asking for new content)
    topic_suggestion = None
    for pattern in _TOPIC_SUGGESTION_PATTERNS:
        m = re.search(pattern, text)
        if m:
            topic_suggestion = m.group(0)[:100].strip()
            signal_types.append("topic_suggestion")
            break

    # Check if comment mentions brand-relevant entities
    brand_keywords = []
    filters = brand["topic_filters"]
    text_orig = comment["text"]
    for inst in filters["institutions"]:
        if re.search(r'\b' + re.escape(inst.lower()) + r'\b', text):
            brand_keywords.append(inst)
    for theme in filters["themes"][:10]:  # just check top themes
        if re.search(r'\b' + re.escape(theme.lower()) + r'\b', text):
            brand_keywords.append(theme)

    if not signal_types:
        return None

    return {
        "text": comment["text"][:300],
        "likes": comment["likes"],
        "replies": comment["replies"],
        "signal_types": signal_types,
        "topic_suggestion": topic_suggestion,
        "brand_keywords": brand_keywords[:3],
        "engagement_score": comment["likes"] * 2 + comment["replies"] * 5,
    }


# ── Aggregation ────────────────────────────────────────────────────────────────

def extract_topic_leads(signals: list) -> list:
    """
    From all extracted signals, pull out the most specific topic suggestions.
    Returns deduplicated, sorted list of potential next topics.
    """
    suggestions = []
    for s in signals:
        if s.get("topic_suggestion") and s["engagement_score"] > 0:
            suggestions.append({
                "suggestion": s["topic_suggestion"],
                "engagement_score": s["engagement_score"],
                "full_comment": s["text"][:200],
                "brand_keywords": s["brand_keywords"],
            })

    # Sort by engagement
    suggestions.sort(key=lambda x: x["engagement_score"], reverse=True)

    # Deduplicate similar suggestions
    seen = []
    unique = []
    for s in suggestions:
        words = set(re.findall(r'\b\w{5,}\b', s["suggestion"].lower()))
        is_dup = any(len(words & seen_words) / max(len(words), 1) > 0.5
                     for seen_words in seen)
        if not is_dup:
            seen.append(words)
            unique.append(s)

    return unique[:20]


# ── Main ──────────────────────────────────────────────────────────────────────

def mine_video(video_id: str, source_label: str, brand: dict,
               api_key: str | None, use_ytdlp: bool) -> dict:
    """Mine comments from a single video. Returns signal summary."""
    print(f"  Mining {source_label} ({video_id})...")

    if api_key:
        comments = fetch_comments_api(video_id, api_key, max_results=500)
    elif use_ytdlp:
        comments = fetch_comments_ytdlp(video_id, max_comments=500)
    else:
        print("    ⚠ No API key and yt-dlp not available — skipping")
        return {}

    print(f"    → {len(comments)} comments fetched")
    if not comments:
        return {}

    # Get video metadata if available
    info_path = Path(f"analysis/fern/{video_id}/video.info.json")
    video_title = ""
    if info_path.exists():
        try:
            video_title = json.loads(info_path.read_text()).get("title", "")
        except Exception:
            pass

    # Top 30 most-liked comments (raw — best signal regardless of pattern)
    # Engagement = likes (community consensus) + replies (discussion/controversy)
    top_liked = sorted(
        [c for c in comments if len(c["text"].strip()) > 20],
        key=lambda c: c["likes"] * 2 + c["replies"] * 5,
        reverse=True
    )[:30]

    # Pattern-matched signals
    extracted = []
    for c in comments:
        sig = extract_signals(c, brand)
        if sig:
            extracted.append(sig)

    # Count signal types
    type_counts = Counter(t for s in extracted for t in s["signal_types"])

    # Top pattern-matched signals
    top_signals = sorted(extracted, key=lambda x: x["engagement_score"], reverse=True)[:10]

    return {
        "video_id": video_id,
        "video_title": video_title,
        "source": source_label,
        "total_comments": len(comments),
        "signals_found": len(extracted),
        "signal_type_counts": dict(type_counts),
        "top_liked_comments": [
            {"text": c["text"][:300], "likes": c["likes"], "replies": c["replies"]}
            for c in top_liked
        ],
        "top_signals": top_signals,
    }


def run_miner(brand_id: str, target_video_id: str | None = None) -> dict:
    brand = load_brand(brand_id)
    api_key = os.environ.get("YOUTUBE_API_KEY")
    use_ytdlp = check_ytdlp()

    if not api_key and not use_ytdlp:
        print("⚠ No YOUTUBE_API_KEY and yt-dlp not found.")
        print("  Install yt-dlp: pip install yt-dlp")
        print("  Or set YOUTUBE_API_KEY environment variable")
        return {}

    method = "YouTube API" if api_key else "yt-dlp"
    print(f"\n{'='*60}")
    print(f"COMMENTS MINER — {brand_id}")
    print(f"Method: {method}")
    print(f"{'='*60}\n")

    video_results = []

    if target_video_id:
        # Single video mode
        result = mine_video(target_video_id, f"target/{target_video_id}",
                            brand, api_key, use_ytdlp)
        if result:
            video_results.append(result)
    else:
        # Discover all Fern video IDs from analysis/ directory
        fern_video_dirs = sorted(Path("analysis/fern").glob("*/video.info.json"))
        fern_video_ids = [p.parent.name for p in fern_video_dirs if len(p.parent.name) == 11]

        if not fern_video_ids:
            # Fallback to known IDs
            fern_video_ids = ["aVA7aXOH1pk", "wLFY_Zu_O08", "wkVygetgeRY"]

        # Sort by view count (highest first) — mine the most successful videos
        def get_views(vid_id):
            info_path = Path(f"analysis/fern/{vid_id}/video.info.json")
            if info_path.exists():
                try:
                    return json.loads(info_path.read_text()).get("view_count", 0)
                except Exception:
                    return 0
            return 0

        fern_video_ids.sort(key=get_views, reverse=True)

        print(f"Mining {len(fern_video_ids)} Fern videos (sorted by view count)...")
        for vid_id in fern_video_ids:
            # Check cache first — avoid re-downloading
            cache_file = Path(f"analysis/fern/{vid_id}/comments.json")
            if cache_file.exists():
                print(f"  Loading cached comments for {vid_id}...")
                cached = json.loads(cache_file.read_text())
                result = mine_video.__wrapped__ if hasattr(mine_video, '__wrapped__') else None
                # Process cached comments directly
                comments = cached.get("comments", [])
                if comments:
                    extracted = [s for s in (extract_signals(c, brand) for c in comments) if s]
                    type_counts = Counter(t for s in extracted for t in s["signal_types"])
                    top_signals = sorted(extracted, key=lambda x: x["engagement_score"], reverse=True)[:10]
                    video_results.append({
                        "video_id": vid_id,
                        "source": f"fern/{vid_id}",
                        "total_comments": len(comments),
                        "signals_found": len(extracted),
                        "signal_type_counts": dict(type_counts),
                        "top_signals": top_signals,
                    })
                continue

            result = mine_video(vid_id, f"fern/{vid_id}", brand, api_key, use_ytdlp)
            if result:
                video_results.append(result)
                # Cache the raw comments for future runs
                if use_ytdlp:
                    tmp_info = Path(f"/tmp/ytdlp_cm_{vid_id}.info.json")
                    if tmp_info.exists():
                        raw_data = json.loads(tmp_info.read_text())
                        raw_comments = [
                            {"text": c.get("text", ""), "likes": c.get("like_count", 0),
                             "replies": c.get("reply_count", 0)}
                            for c in raw_data.get("comments", [])
                            if c.get("parent") == "root"
                        ]
                        cache_file.write_text(json.dumps({"comments": raw_comments}, indent=2))
            time.sleep(2.0)  # polite rate limit between videos

        # Mine competitor channels if API key available
        if api_key:
            competitor_channel_ids = {
                "MrBallen":    "UCsYGMsHFIwqp9w2Rixg5FAQ",
                "Newsthink":   "UCddiUEpeqJcYeBxX1IVBKvQ",
                "LEMMiNO":     "UCRcgy6GzDeccI7dkbbBna3Q",
            }
            print("\nMining competitor channels (topic signals)...")
            for name, channel_id in competitor_channel_ids.items():
                print(f"  Fetching recent top videos from {name}...")
                video_ids = fetch_video_ids_for_channel(channel_id, api_key, max_videos=3)
                for vid_id in video_ids:
                    result = mine_video(vid_id, f"competitor/{name}", brand, api_key, use_ytdlp)
                    if result:
                        video_results.append(result)
                    time.sleep(0.5)

    # Aggregate all signals
    all_signals = []
    for vr in video_results:
        all_signals.extend(vr.get("top_signals", []))

    topic_leads = extract_topic_leads(all_signals)

    # Summary stats
    total_comments = sum(vr.get("total_comments", 0) for vr in video_results)
    total_signals = sum(vr.get("signals_found", 0) for vr in video_results)
    all_type_counts = Counter()
    for vr in video_results:
        all_type_counts.update(vr.get("signal_type_counts", {}))

    output = {
        "brand_id": brand_id,
        "generated_at": datetime.now().isoformat(),
        "method": method,
        "summary": {
            "videos_mined": len(video_results),
            "total_comments": total_comments,
            "total_signals": total_signals,
            "signal_type_breakdown": dict(all_type_counts),
        },
        "topic_leads": topic_leads,
        "video_results": video_results,
    }

    # Save
    output_dir = Path(f"research/{brand_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "comment_signals.json"
    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Print summary
    print(f"\n{'='*60}")
    print(f"COMMENT SIGNALS SUMMARY")
    print(f"{'='*60}")
    print(f"Videos mined:    {len(video_results)}")
    print(f"Total comments:  {total_comments:,}")
    print(f"Signals found:   {total_signals}")
    print(f"\nSignal breakdown:")
    for sig_type, count in all_type_counts.most_common():
        print(f"  {sig_type}: {count}")

    if topic_leads:
        print(f"\n📌 PATTERN-MATCHED TOPIC LEADS:")
        for i, lead in enumerate(topic_leads[:10], 1):
            kw_tag = f" [{', '.join(lead['brand_keywords'][:2])}]" if lead["brand_keywords"] else ""
            print(f"\n{i:2}. Score: {lead['engagement_score']:4} | {lead['suggestion'][:80]}{kw_tag}")
            print(f"    → \"{lead['full_comment'][:100]}\"")

    # Print top liked comments across all videos (raw gold)
    all_top_liked = []
    for vr in video_results:
        for c in vr.get("top_liked_comments", []):
            all_top_liked.append({**c, "video": vr.get("video_title", vr.get("video_id", ""))[:40]})
    all_top_liked.sort(key=lambda c: c["likes"] * 2 + c["replies"] * 5, reverse=True)

    if all_top_liked:
        print(f"\n🏆 TOP LIKED COMMENTS (raw — review for topic leads):")
        for i, c in enumerate(all_top_liked[:20], 1):
            replies_tag = f" | {c['replies']}↩" if c.get("replies", 0) > 0 else ""
            print(f"\n{i:2}. [{c['likes']:5} ♥{replies_tag}] from: {c['video']}")
            print(f"    \"{c['text'][:140]}\"")

    print(f"\n✅ Full results: {output_file}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comments Miner — extracts topic signals from YouTube comments")
    parser.add_argument("--brand", required=True, help="Brand config ID (e.g. fern_clone)")
    parser.add_argument("--video", default=None, help="Specific video ID to mine")
    args = parser.parse_args()

    run_miner(args.brand, args.video)
