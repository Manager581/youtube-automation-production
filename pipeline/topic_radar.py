#!/usr/bin/env python3
"""
Topic Radar — finds viral story candidates matching a brand identity.

Usage:
    python pipeline/topic_radar.py --brand fern_clone
    python pipeline/topic_radar.py --brand fern_clone --limit 20 --since week

Sources (zero API keys required for basic run):
    - Reddit JSON API
    - Google News RSS
    - YouTube competitor channels (via yt-dlp)
    - TikTok accounts (via yt-dlp)
    - pytrends (Google Trends validation)

Output:
    research/{brand_id}/topic_candidates.json  — ranked story list
"""

import json
import time
import re
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ── Config ────────────────────────────────────────────────────────────────────

def load_brand(brand_id: str) -> dict:
    path = Path(f"brand_configs/{brand_id}.json")
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")
    return json.loads(path.read_text())


# ── Reddit ────────────────────────────────────────────────────────────────────

def fetch_reddit(subreddit: str, timeframe: str = "week", limit: int = 25) -> list:
    """Fetch top posts from a subreddit via public JSON API (no key needed)."""
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t={timeframe}&limit={limit}"
    headers = {"User-Agent": "topic-radar/1.0"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        posts = []
        for child in data.get("data", {}).get("children", []):
            p = child["data"]
            posts.append({
                "source": f"reddit/r/{subreddit}",
                "title": p.get("title", ""),
                "text": p.get("selftext", "")[:500],
                "url": p.get("url", ""),
                "score": p.get("score", 0),
                "comments": p.get("num_comments", 0),
                "upvote_ratio": p.get("upvote_ratio", 0),
                "flair": p.get("link_flair_text", ""),
                "created": p.get("created_utc", 0),
            })
        return posts
    except Exception as e:
        print(f"  ⚠ Reddit r/{subreddit}: {e}")
        return []


def scan_reddit(brand: dict, timeframe: str = "week") -> list:
    subreddits = brand["research_sources"]["reddit"]
    all_posts = []
    for sub in subreddits:
        print(f"  Reddit r/{sub}...")
        posts = fetch_reddit(sub, timeframe)
        all_posts.extend(posts)
        time.sleep(1.5)  # polite rate limit
    return all_posts


# ── Google News RSS ───────────────────────────────────────────────────────────

def fetch_google_news(keyword: str) -> list:
    """Fetch Google News RSS for a keyword (no key needed)."""
    query = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "topic-radar/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")

        # Parse RSS without feedparser dependency
        items = []
        entries = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
        for entry in entries[:5]:
            title_m = re.search(r"<title>(.*?)</title>", entry)
            link_m = re.search(r"<link>(.*?)</link>", entry)
            desc_m = re.search(r"<description>(.*?)</description>", entry)
            pub_m = re.search(r"<pubDate>(.*?)</pubDate>", entry)

            if title_m:
                title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                # Strip publication name from Google News titles ("Story - Publication")
                title = re.sub(r"\s+-\s+\w[\w\s]+$", "", title).strip()

                items.append({
                    "source": f"google_news/{keyword}",
                    "title": title,
                    "text": re.sub(r"<[^>]+>", "", desc_m.group(1) if desc_m else "")[:300],
                    "url": link_m.group(1).strip() if link_m else "",
                    "score": 0,  # no engagement score from RSS
                    "comments": 0,
                    "pub_date": pub_m.group(1).strip() if pub_m else "",
                })
        return items
    except Exception as e:
        print(f"  ⚠ Google News '{keyword}': {e}")
        return []


def scan_google_news(brand: dict) -> list:
    keywords = brand["research_sources"]["google_news_keywords"]
    all_items = []
    for kw in keywords:
        print(f"  Google News: '{kw}'...")
        items = fetch_google_news(kw)
        all_items.extend(items)
        time.sleep(1.0)
    return all_items


# ── Google Trends validation ──────────────────────────────────────────────────

def get_trend_score(keyword: str) -> int:
    """Get Google Trends interest score for a keyword (0-100). Returns -1 on failure."""
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        pt.build_payload([keyword], timeframe="now 7-d")
        df = pt.interest_over_time()
        if df.empty:
            return 0
        return int(df[keyword].mean())
    except ImportError:
        return -1  # pytrends not installed, skip
    except Exception:
        return -1


# ── Scoring ───────────────────────────────────────────────────────────────────

def extract_story_keywords(text: str) -> list:
    """Pull key nouns/entities from a title/text."""
    words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    return list(set(words))


# Acronyms that must match case-sensitively to avoid pronoun/word false positives
_CASE_SENSITIVE = {"WHO", "UN", "FBI", "CIA", "NSA", "DEA", "ATF", "KGB", "FSB",
                   "MI6", "SEC", "FDA", "CDC", "NATO", "FOIA"}


def _word_match(term: str, text_lower: str, text_original: str = "") -> bool:
    """Match a term with word boundaries. Acronyms match case-sensitively."""
    if term.upper() in _CASE_SENSITIVE:
        # Must appear as uppercase acronym in original text
        return bool(re.search(r'\b' + re.escape(term.upper()) + r'\b', text_original))
    return bool(re.search(r'\b' + re.escape(term.lower()) + r'\b', text_lower))


def score_story(item: dict, brand: dict) -> dict:
    """Score a story candidate against the brand identity. Returns enriched item with score."""
    title = (item.get("title") or "").lower()
    text_orig = (item.get("title") or "") + " " + (item.get("text") or "")
    text = text_orig.lower()

    filters = brand["topic_filters"]
    formula = brand["content_formula"]
    score = 0
    signals = []
    warnings = []

    # ── Hard avoid check ──
    for avoid in filters["hard_avoid"]:
        if any(_word_match(word, text, text_orig) for word in avoid.lower().split("/")):
            return None  # disqualified

    # ── Already covered by Fern ──
    covered = [c.lower() for c in brand.get("already_covered", [])]
    for c in covered:
        if any(_word_match(word, text, text_orig) for word in c.split()[:2] if len(word) > 4):
            warnings.append(f"possibly already covered: {c}")
            score -= 20

    # ── Institution match ──
    # High-value: intelligence agencies and dark institutions (+20)
    # Generic: government, military, court, prison (+8 — reduces routine news noise)
    _HIGH_VALUE_INSTS = {"FBI", "CIA", "NSA", "DEA", "ATF", "Secret Service", "Pentagon",
                         "KGB", "FSB", "Stasi", "Mossad", "MI6", "Interpol",
                         "pharmaceutical", "oil company", "tech giant"}
    matched_institutions = []
    for inst in filters["institutions"]:
        if _word_match(inst, text, text_orig):
            matched_institutions.append(inst)
            score += 20 if inst in _HIGH_VALUE_INSTS else 8
    if matched_institutions:
        signals.append(f"institution: {', '.join(matched_institutions[:3])}")

    # ── Theme match ──
    matched_themes = []
    for theme in filters["themes"]:
        if _word_match(theme, text, text_orig):
            matched_themes.append(theme)
            score += 10
    if matched_themes:
        signals.append(f"theme: {', '.join(matched_themes[:3])}")

    # ── Person archetype match ──
    for archetype in filters["person_archetypes"]:
        words = archetype.lower().split()
        if any(_word_match(w, text, text_orig) for w in words if len(w) > 4):
            score += 12
            signals.append(f"archetype: {archetype}")
            break

    # ── Required elements ──
    required_hits = 0
    if any(w in text for w in ["secret", "classified", "hidden", "cover", "declassified", "reveal"]):
        required_hits += 1
        score += 15
    if any(w in text for w in ["death", "died", "killed", "arrested", "prison", "executed", "murdered"]):
        required_hits += 1
        score += 10
    if required_hits == 0:
        warnings.append("no twist/stakes signals found")

    # ── Title angle match ──
    matched_angle = None
    for angle in formula["title_angles_ranked"]:
        kws = [k.lower() for k in angle.get("keywords", [])]
        if any(kw in title for kw in kws if kw):
            matched_angle = angle["pattern"]
            score += angle["avg_views"] // 500000  # bonus proportional to proven performance
            break

    # ── Reddit engagement bonus ──
    reddit_score = item.get("score", 0)
    if reddit_score > 10000:
        score += 25
        signals.append(f"viral on reddit ({reddit_score:,} upvotes)")
    elif reddit_score > 2000:
        score += 15
        signals.append(f"strong reddit ({reddit_score:,} upvotes)")
    elif reddit_score > 500:
        score += 8

    # ── Minimum signal gate — must have at least one institution or theme match ──
    if not matched_institutions and not matched_themes:
        return None  # viral-only posts with no investigative signal are disqualified

    return {
        **item,
        "viral_score": max(0, score),
        "angle": matched_angle,
        "signals": signals,
        "warnings": warnings,
        "institutions_found": matched_institutions,
        "themes_found": matched_themes,
    }


# ── Deduplication ──────────────────────────────────────────────────────────────

def deduplicate(candidates: list) -> list:
    """Remove near-duplicate stories (same keywords in title)."""
    seen_words = []
    unique = []
    for c in candidates:
        title_words = set(re.findall(r"\b\w{5,}\b", c["title"].lower()))
        is_dup = False
        for seen in seen_words:
            overlap = len(title_words & seen) / max(len(title_words), 1)
            if overlap > 0.5:
                is_dup = True
                break
        if not is_dup:
            seen_words.append(title_words)
            unique.append(c)
    return unique


# ── Title angle suggestion ─────────────────────────────────────────────────────

# ── YouTube competitor channels ────────────────────────────────────────────────

# Channel handles → channel URLs for yt-dlp scraping
_YT_CHANNEL_URLS = {
    # Competitor channels (similar format/audience)
    "Fern":                  "https://www.youtube.com/@fern-tv/videos",
    "MrBallen":              "https://www.youtube.com/@MrBallen/videos",
    "Newsthink":             "https://www.youtube.com/@Newsthink/videos",
    "TLDR News":             "https://www.youtube.com/@TLDRNewsGlobal/videos",
    "Coffeezilla":           "https://www.youtube.com/@Coffeezilla/videos",
    "LEMMiNO":               "https://www.youtube.com/@LEMMiNO/videos",
    "Wendover Productions":  "https://www.youtube.com/@WendoverProductions/videos",
    # News sources (story leads + footage signals)
    "CNN":                   "https://www.youtube.com/@CNN/videos",
    "Daily Mail":            "https://www.youtube.com/@DailyMail/videos",
    "Vice News":             "https://www.youtube.com/@VICENews/videos",
}


def fetch_youtube_channel_videos(channel_name: str, max_videos: int = 15) -> list:
    """Fetch recent video metadata from a YouTube channel via yt-dlp. No API key needed."""
    url = _YT_CHANNEL_URLS.get(channel_name)
    if not url:
        return []

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--playlist-end", str(max_videos),
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        videos = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                videos.append({
                    "source": f"youtube/{channel_name}",
                    "title": d.get("title", ""),
                    "url": d.get("url") or d.get("webpage_url") or f"https://youtu.be/{d.get('id','')}",
                    "score": 0,   # no upvotes
                    "comments": 0,
                    "view_count": d.get("view_count") or 0,
                    "upload_date": d.get("upload_date", ""),
                    "text": "",
                    "channel": channel_name,
                })
            except json.JSONDecodeError:
                continue
        return videos
    except subprocess.TimeoutExpired:
        print(f"  ⚠ yt-dlp timeout for {channel_name}")
        return []
    except Exception as e:
        print(f"  ⚠ YouTube/{channel_name}: {e}")
        return []


def scan_youtube_competitors(brand: dict) -> list:
    """Scan competitor YouTube channels for recent high-performing videos."""
    channels = brand.get("research_sources", {}).get("youtube_competitor_channels", [])
    # Skip Fern itself (already covered)
    channels = [c for c in channels if c.lower() != "fern"]

    all_videos = []
    for channel in channels:
        if channel not in _YT_CHANNEL_URLS:
            continue
        print(f"  YouTube: @{channel}...")
        videos = fetch_youtube_channel_videos(channel, max_videos=15)
        all_videos.extend(videos)
        time.sleep(1.0)

    # Add view_count as a score signal — high views = proven viral interest
    for v in all_videos:
        views = v.get("view_count", 0)
        if views > 1_000_000:
            v["score"] = 20000  # treat as equivalent to very viral Reddit post
        elif views > 500_000:
            v["score"] = 10000
        elif views > 100_000:
            v["score"] = 2000

    return all_videos


# ── TikTok accounts ────────────────────────────────────────────────────────────

def fetch_tiktok_account(account: str, max_videos: int = 20) -> list:
    """Fetch recent TikToks from an account via yt-dlp. No API key needed."""
    handle = account.lstrip("@")
    url = f"https://www.tiktok.com/@{handle}"

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--playlist-end", str(max_videos),
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        videos = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                views = d.get("view_count") or 0
                videos.append({
                    "source": f"tiktok/{account}",
                    "title": d.get("title", "") or d.get("description", ""),
                    "url": d.get("url") or d.get("webpage_url", ""),
                    "score": min(views // 1000, 30000),  # normalize to reddit-scale
                    "comments": 0,
                    "view_count": views,
                    "text": "",
                })
            except json.JSONDecodeError:
                continue
        return videos
    except subprocess.TimeoutExpired:
        print(f"  ⚠ yt-dlp timeout for TikTok {account}")
        return []
    except Exception as e:
        print(f"  ⚠ TikTok {account}: {e}")
        return []


def scan_tiktok(brand: dict) -> list:
    """Scan TikTok accounts from brand config."""
    accounts = brand.get("research_sources", {}).get("tiktok_accounts", [])
    all_videos = []
    for account in accounts:
        print(f"  TikTok {account}...")
        videos = fetch_tiktok_account(account, max_videos=20)
        all_videos.extend(videos)
        time.sleep(1.5)
    return all_videos


def suggest_title(item: dict, brand: dict) -> str:
    """Suggest a Fern-style title for a story candidate."""
    title = item["title"]
    angle = item.get("angle")
    institutions = item.get("institutions_found", [])
    formula = brand["content_formula"]

    if not angle:
        # Pick highest-performing angle
        angle = formula["title_angles_ranked"][0]["pattern"]

    templates = {t["pattern"]: t["template"] for t in formula["title_angles_ranked"]}
    template = templates.get(angle, "[Topic]: [The Hidden Truth]")

    # Prefer named agencies/orgs over generic terms (avoid "How WHO [Shocking]")
    _generic = {"who", "un", "sec", "court", "prison", "government",
                "bank", "military", "congress", "senate"}
    named = [i for i in institutions if i.lower() not in _generic]
    inst = (named[0] if named else institutions[0]) if institutions else "[Institution]"
    suggested = template.replace("[Institution]", inst)

    return f"{suggested}  [from: {title[:60]}]"


# ── Main ──────────────────────────────────────────────────────────────────────

def run_radar(brand_id: str, timeframe: str = "week", limit: int = 30) -> list:
    brand = load_brand(brand_id)

    print(f"\n{'='*60}")
    print(f"TOPIC RADAR — {brand_id}")
    print(f"Lane: {brand['channel']['lane'][:70]}")
    print(f"{'='*60}\n")

    # Gather from all sources
    all_items = []

    print("Scanning Reddit...")
    all_items.extend(scan_reddit(brand, timeframe))

    print("\nScanning Google News...")
    all_items.extend(scan_google_news(brand))

    print("\nScanning YouTube competitors...")
    yt_items = scan_youtube_competitors(brand)
    all_items.extend(yt_items)
    print(f"  → {len(yt_items)} videos from competitor channels")

    print("\nScanning TikTok accounts...")
    tt_items = scan_tiktok(brand)
    all_items.extend(tt_items)
    print(f"  → {len(tt_items)} TikToks scanned")

    print(f"\nTotal raw items: {len(all_items)}")

    # Score and filter
    print("\nScoring candidates...")
    scored = []
    for item in all_items:
        result = score_story(item, brand)
        if result and result["viral_score"] > 0:
            scored.append(result)

    # Deduplicate and sort
    scored = deduplicate(scored)
    scored.sort(key=lambda x: x["viral_score"], reverse=True)
    top = scored[:limit]

    # Add title suggestions
    for item in top:
        item["suggested_title"] = suggest_title(item, brand)

    # Output
    output_dir = Path(f"research/{brand_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "topic_candidates.json"

    output = {
        "brand_id": brand_id,
        "generated_at": datetime.now().isoformat(),
        "timeframe": timeframe,
        "total_scanned": len(all_items),
        "candidates": top,
    }

    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Print summary
    print(f"\n{'='*60}")
    print(f"TOP {min(10, len(top))} CANDIDATES")
    print(f"{'='*60}")
    for i, c in enumerate(top[:10], 1):
        angle_tag = f"[{c['angle']}]" if c.get("angle") else "[unclassified]"
        source_tag = c["source"].split("/")[0]
        print(f"\n{i:2}. Score: {c['viral_score']:3} | {angle_tag} | {source_tag}")
        print(f"    {c['title'][:80]}")
        if c["signals"]:
            print(f"    ✓ {' | '.join(c['signals'][:3])}")
        if c["warnings"]:
            print(f"    ⚠ {' | '.join(c['warnings'][:2])}")
        print(f"    → {c['suggested_title'][:90]}")

    print(f"\n✅ Full results saved to: {output_file}")
    print(f"   {len(top)} candidates | {len(all_items)} total scanned\n")

    return top


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Topic Radar — finds viral story candidates")
    parser.add_argument("--brand", required=True, help="Brand config ID (e.g. fern_clone)")
    parser.add_argument("--timeframe", default="week", choices=["day", "week", "month"],
                        help="Reddit timeframe (default: week)")
    parser.add_argument("--limit", type=int, default=30, help="Max candidates to return")
    args = parser.parse_args()

    run_radar(args.brand, args.timeframe, args.limit)
