#!/usr/bin/env python3
"""
Topic Radar — finds viral story candidates matching a brand identity.

Usage:
    python pipeline/topic_radar.py --brand fern_clone
    python pipeline/topic_radar.py --brand fern_clone --min-score 60  # show more candidates
    python pipeline/topic_radar.py --brand fern_clone --timeframe month

Sources (zero API keys required for basic run):
    - Wikipedia dark history categories (best source — pre-validated, documented stories)
    - Reddit JSON API (month timeframe — history/crime/mystery subreddits)
    - Investigative journalism RSS (ProPublica, The Intercept)
    - Google News RSS (historical/declassified keywords)
    - YouTube competitor channels (via yt-dlp)
    - TikTok accounts (via yt-dlp)

Only shows candidates scoring 75+ (pass --min-score to adjust).
Score 75–84 = solid candidate. 85+ = strong candidate.

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


# ── Fern catalog — duplicate / overlap detection ─────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_OVERLAP_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "was", "are", "were", "how", "why", "what",
    "who", "when", "that", "this", "it", "its", "their", "they", "his", "her",
    "our", "your", "my", "did", "does", "has", "had", "have", "not", "no",
    "about", "into", "just", "most", "more", "than", "after", "before", "been",
    "will", "would", "could", "should", "very", "also", "even", "only", "ever",
    "didn", "wasn", "wouldn", "couldn", "isn", "aren",
}

# Thresholds for overlap flag
_OVERLAP_HARD_SKIP = 0.60   # Fern already made this — disqualify
_OVERLAP_WARNING   = 0.30   # Similar topic — warn but allow


def _load_fern_catalog() -> list:
    """Load all Fern video titles, descriptions, and view counts for overlap detection."""
    catalog = []
    fern_dir = _PROJECT_ROOT / "analysis" / "fern"
    for info_file in sorted(fern_dir.glob("*/video.info.json")):
        try:
            d = json.loads(info_file.read_text())
            # Strip URLs and sponsor lines from description to get story keywords
            raw_desc = (d.get("description") or "")
            clean_desc = re.sub(r"https?://\S+", "", raw_desc)
            clean_desc = re.sub(r"\b(use code|coupon|discount|promo|sponsor)\b.*", "", clean_desc, flags=re.IGNORECASE)
            catalog.append({
                "video_id":    info_file.parent.name,
                "title":       d.get("title", ""),
                "view_count":  d.get("view_count", 0),
                "description": clean_desc[:400],
            })
        except Exception:
            pass
    return catalog


def _key_terms(text: str) -> set:
    """Extract significant words (no stopwords, length > 3)."""
    words = re.findall(r"\b\w+\b", text.lower())
    return {w for w in words if w not in _OVERLAP_STOPWORDS and len(w) > 3}


def _fern_entry_similarity(query: str, entry: dict) -> float:
    """
    Return 0.0–1.0 similarity between a query string and a single Fern catalog entry.

    Algorithm:
      1. Jaccard overlap on key terms — TITLE ONLY (description would dilute with
         unrelated sponsor/source words and reduce real topic matches)
      2. Acronym exact-match bonus — FBI, CIA, KKK, NSA, etc. (+0.15 each, max 0.30)
      3. Proper-noun bonus — people, places, orgs (+0.10 each, max 0.20)
    """
    q_terms = _key_terms(query)
    f_terms = _key_terms(entry["title"])   # title only for Jaccard

    if not q_terms or not f_terms:
        return 0.0

    overlap = q_terms & f_terms
    jaccard = len(overlap) / max(len(q_terms | f_terms), 1)

    # Acronym exact-match bonus (each matching 2+-char uppercase token adds 0.15)
    q_ents = set(re.findall(r"\b[A-Z]{2,}\b", query))
    f_ents = set(re.findall(r"\b[A-Z]{2,}\b", entry["title"]))
    entity_bonus = min(0.30, len(q_ents & f_ents) * 0.15)

    # Proper-noun bonus (Title-Cased words: people, places, orgs)
    q_proper = set(re.findall(r"\b[A-Z][a-z]{3,}\b", query))
    f_proper = set(re.findall(r"\b[A-Z][a-z]{3,}\b", entry["title"]))
    proper_bonus = min(0.20, len(q_proper & f_proper) * 0.10)

    return min(1.0, jaccard + entity_bonus + proper_bonus)


def check_fern_overlap(query: str, catalog: list) -> dict:
    """
    Check query against all 30 Fern videos. Returns:
    {
        "flag":             "HARD_SKIP" | "WARNING" | "CLEAR",
        "similarity":       float,          # 0.0–1.0
        "matched_title":    str,
        "matched_video_id": str,
        "matched_views":    int,
        "top_3": [...]                      # top 3 matches with scores
    }
    """
    if not catalog:
        return {"flag": "CLEAR", "similarity": 0.0, "matched_title": "",
                "matched_video_id": "", "matched_views": 0, "top_3": []}

    scored = sorted(
        [(e, _fern_entry_similarity(query, e)) for e in catalog],
        key=lambda x: -x[1]
    )
    best_entry, best_sim = scored[0]

    flag = ("HARD_SKIP" if best_sim >= _OVERLAP_HARD_SKIP
            else "WARNING"   if best_sim >= _OVERLAP_WARNING
            else "CLEAR")

    return {
        "flag":             flag,
        "similarity":       round(best_sim, 3),
        "matched_title":    best_entry["title"],
        "matched_video_id": best_entry["video_id"],
        "matched_views":    best_entry["view_count"],
        "top_3": [
            {"title": e["title"], "video_id": e["video_id"],
             "views": e["view_count"], "similarity": round(s, 3)}
            for e, s in scored[:3] if s > 0.10
        ],
    }


# ── Wikipedia dark history scanner ───────────────────────────────────────────
#
# These Wikipedia categories are literal goldmines for Fern-style topics.
# Every entry is a real story with archival documentation. The API is free,
# no key required, and returns up to 50 articles per category.
#
# Why this beats Google News: News surfaces what's trending NOW. Wikipedia
# categories surface stories that are PROVEN — deep enough to warrant an
# article, already fact-checked, often with primary sources listed.

WIKIPEDIA_DARK_CATEGORIES = [
    "United_States_government_cover-ups",
    "Human_subject_research_scandals",
    "Espionage_scandals_in_the_United_States",
    "Cold_War_espionage",
    "COINTELPRO",
    "Political_scandals_in_the_United_States",
    "FBI_investigations",
    "Unsolved_murders_in_the_United_States",
    "American_whistleblowers",
    "CIA_activities_in_the_United_States",
    "United_States_intelligence_agencies",
    "Human_experimentation_in_the_United_States",
    "Cold_War_propaganda",
    "Classified_information_in_the_United_States",
    "Assassinations_in_the_United_States",
]


def fetch_wikipedia_category(category: str, limit: int = 50) -> list:
    """
    Fetch article titles from a Wikipedia category via the free MediaWiki API.
    Returns items ready for score_story(). No API key required.

    Each Wikipedia article in a dark history category = a real, documented story
    that's already proven interesting enough to have an encyclopedia entry.
    """
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&list=categorymembers"
        f"&cmtitle=Category:{category}"
        f"&cmlimit={limit}&format=json&cmtype=page"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "topic-radar/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        pages = data.get("query", {}).get("categorymembers", [])
        return [
            {
                "source": f"wikipedia/{category.replace('_', ' ')}",
                "title": p["title"],
                # Text = title + category context — feeds keyword scoring
                "text": (
                    f"{p['title']}. "
                    f"Category: {category.replace('_', ' ')}. "
                    f"Documented historical event with primary sources."
                ),
                "url": f"https://en.wikipedia.org/wiki/{p['title'].replace(' ', '_')}",
                "score": 0,
                "comments": 0,
                # Wikipedia bonus: verified real story with documentation
                # Compensates for no Reddit engagement signal on historical content
                "source_bonus": 20,
            }
            for p in pages
        ]
    except Exception as e:
        print(f"  ⚠ Wikipedia/{category}: {e}")
        return []


def scan_wikipedia_dark_history() -> list:
    """Scan all dark history categories. Returns deduplicated article list."""
    all_articles = []
    seen_titles: set[str] = set()

    for category in WIKIPEDIA_DARK_CATEGORIES:
        print(f"  Wikipedia: {category.replace('_', ' ')}...")
        articles = fetch_wikipedia_category(category)
        for a in articles:
            if a["title"] not in seen_titles:
                seen_titles.add(a["title"])
                all_articles.append(a)
        time.sleep(0.5)  # polite rate limit

    return all_articles


# ── Investigative journalism RSS ──────────────────────────────────────────────

INVESTIGATIVE_RSS_FEEDS = [
    # ProPublica — nonprofit investigative journalism, free to use
    "https://feeds.propublica.org/propublica/main",
    # The Intercept — national security / intelligence / government accountability
    "https://theintercept.com/feed/?rss",
]


def fetch_investigative_rss(url: str) -> list:
    """Fetch investigative journalism RSS feed. Returns items for scoring."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "topic-radar/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="replace")

        items = []
        entries = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
        for entry in entries[:10]:
            title_m = re.search(r"<title[^>]*>(.*?)</title>", entry, re.DOTALL)
            link_m  = re.search(r"<link>(.*?)</link>", entry)
            desc_m  = re.search(r"<description[^>]*>(.*?)</description>", entry, re.DOTALL)
            if title_m:
                title = re.sub(r"<[^>]+>|<!\[CDATA\[|\]\]>", "", title_m.group(1)).strip()
                desc  = re.sub(r"<[^>]+>|<!\[CDATA\[|\]\]>", "", desc_m.group(1) if desc_m else "")[:300]
                items.append({
                    "source": f"investigative/{url.split('/')[2]}",
                    "title": title,
                    "text": desc,
                    "url": link_m.group(1).strip() if link_m else "",
                    "score": 0,
                    "comments": 0,
                    # Investigative journalism bonus: professional editorial judgment
                    "source_bonus": 10,
                })
        return items
    except Exception as e:
        print(f"  ⚠ RSS {url}: {e}")
        return []


def scan_investigative_journalism() -> list:
    """Scan ProPublica, The Intercept for investigative story leads."""
    all_items = []
    for feed_url in INVESTIGATIVE_RSS_FEEDS:
        domain = feed_url.split("/")[2].replace("feeds.", "")
        print(f"  {domain}...")
        items = fetch_investigative_rss(feed_url)
        all_items.extend(items)
        time.sleep(1.0)
    return all_items


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


def score_story(item: dict, brand: dict, fern_catalog: list = None) -> dict:
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

    # ── Fern catalog overlap — disqualify if Fern already made this video ──
    if fern_catalog:
        overlap = check_fern_overlap(text_orig, fern_catalog)
        if overlap["flag"] == "HARD_SKIP":
            return None  # Fern already covered this — hard disqualify
        elif overlap["flag"] == "WARNING":
            matched_short = overlap["matched_title"][:55]
            views_k = overlap["matched_views"] // 1000
            warnings.append(
                f"overlaps Fern's '{matched_short}' "
                f"({views_k:,}K views, {overlap['similarity']:.0%} match) — "
                f"verify your angle is meaningfully different"
            )
            score -= 15

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

    # ── Reddit / view engagement bonus ──
    reddit_score = item.get("score", 0)
    if reddit_score > 10000:
        score += 25
        signals.append(f"viral on reddit ({reddit_score:,} upvotes)")
    elif reddit_score > 2000:
        score += 15
        signals.append(f"strong reddit ({reddit_score:,} upvotes)")
    elif reddit_score > 500:
        score += 8

    # ── Source quality bonus ──
    # Wikipedia / investigative journalism sources are pre-validated stories.
    # Compensates for the absence of Reddit engagement on historical content.
    source_bonus = item.get("source_bonus", 0)
    if source_bonus:
        score += source_bonus
        source_name = item.get("source", "").split("/")[0]
        signals.append(f"verified source ({source_name})")

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

def run_radar(brand_id: str, timeframe: str = "month", limit: int = 30,
              min_score: int = 75) -> list:
    brand = load_brand(brand_id)

    print(f"\n{'='*60}")
    print(f"TOPIC RADAR — {brand_id}")
    print(f"Lane: {brand['channel']['lane'][:70]}")
    print(f"Min score: {min_score}+  |  Timeframe: {timeframe}")
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

    # Wikipedia dark history — the best source for Fern-style topics
    print("\nScanning Wikipedia dark history categories...")
    wiki_items = scan_wikipedia_dark_history()
    all_items.extend(wiki_items)
    print(f"  → {len(wiki_items)} Wikipedia articles scanned")

    # Investigative journalism feeds
    print("\nScanning investigative journalism feeds...")
    inv_items = scan_investigative_journalism()
    all_items.extend(inv_items)
    print(f"  → {len(inv_items)} investigative articles scanned")

    print(f"\nTotal raw items: {len(all_items)}")

    # Load Fern catalog once for duplicate detection
    print("\nLoading Fern catalog for overlap detection...")
    fern_catalog = _load_fern_catalog()
    if fern_catalog:
        print(f"  → {len(fern_catalog)} Fern videos loaded for overlap check")
    else:
        print("  ⚠ No Fern catalog found — overlap check skipped")

    # Score and filter
    print("\nScoring candidates...")
    scored = []
    for item in all_items:
        result = score_story(item, brand, fern_catalog)
        if result and result["viral_score"] > 0:
            scored.append(result)

    # Deduplicate and sort
    scored = deduplicate(scored)
    scored.sort(key=lambda x: x["viral_score"], reverse=True)

    # Apply minimum score threshold — only show actionable candidates
    qualifying = [c for c in scored if c["viral_score"] >= min_score]
    top = qualifying[:limit]

    # Safety net: if nothing qualifies, show top 5 with a warning
    if not top and scored:
        print(f"\n⚠  No candidates scored ≥{min_score}.")
        print(f"   Best score: {scored[0]['viral_score']} ({scored[0]['title'][:60]})")
        print(f"   Showing top 5 anyway — lower threshold with --min-score 60\n")
        top = scored[:5]
    elif len(qualifying) < 5:
        print(f"\n⚠  Only {len(qualifying)} candidates scored ≥{min_score}.")
        print(f"   Use --min-score 60 to see more, or re-run with --timeframe month\n")

    # Add title suggestions
    for item in top:
        item["suggested_title"] = suggest_title(item, brand)

    # Output — save ALL qualifying (not just display limit)
    output_dir = Path(f"research/{brand_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "topic_candidates.json"

    output = {
        "brand_id": brand_id,
        "generated_at": datetime.now().isoformat(),
        "timeframe": timeframe,
        "min_score": min_score,
        "total_scanned": len(all_items),
        "qualifying_count": len(qualifying),
        "candidates": qualifying[:limit],
    }

    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Print summary — only qualifying candidates
    display = top[:10]
    print(f"\n{'='*60}")
    print(f"TOP {len(display)} CANDIDATES (score ≥{min_score})")
    print(f"{'='*60}")
    if not display:
        print("  No qualifying candidates. Try --min-score 60 or --timeframe month.")
    for i, c in enumerate(display, 1):
        angle_tag = f"[{c['angle']}]" if c.get("angle") else "[unclassified]"
        source_tag = c["source"].split("/")[0]
        score_color = "✅" if c["viral_score"] >= 85 else "🟡"
        print(f"\n{i:2}. {score_color} Score: {c['viral_score']:3} | {angle_tag} | {source_tag}")
        print(f"    {c['title'][:80]}")
        if c["signals"]:
            print(f"    ✓ {' | '.join(c['signals'][:3])}")
        if c["warnings"]:
            print(f"    ⚠ {' | '.join(c['warnings'][:2])}")
        print(f"    → {c['suggested_title'][:90]}")

    print(f"\n✅ Full results saved to: {output_file}")
    print(f"   {len(qualifying)} qualifying | {len(all_items)} total scanned\n")

    return top


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Topic Radar — finds viral story candidates")
    parser.add_argument("--brand", required=True, help="Brand config ID (e.g. fern_clone)")
    parser.add_argument("--timeframe", default="month", choices=["day", "week", "month", "year", "all"],
                        help="Reddit timeframe (default: month — week is too short for historical stories)")
    parser.add_argument("--limit", type=int, default=30, help="Max candidates to return")
    parser.add_argument("--min-score", type=int, default=75,
                        help="Minimum viral score to show (default: 75). Use 60 to see more candidates.")
    args = parser.parse_args()

    run_radar(args.brand, args.timeframe, args.limit, args.min_score)
