#!/usr/bin/env python3
"""
story_validator.py — Pre-production viability gate.

Answers ONE question before you spend any production time:
"Is there enough here to make a compelling, viral 25-minute Fern-style video?"

Scores 5 dimensions (each 0–100):
  1. Factual Depth     — is there enough verified content to fill 25 min?
  2. Viral Hook        — does the story have the structural hooks that drive views?
  3. Story Arc         — does a complete narrative arc exist (origin → reveal → resolution)?
  4. Visual Assets     — how many real images/footage exist on Wikimedia + Archive?
  5. Public Interest   — current search trend + Reddit interest

Verdict:
  GO          — score ≥ 65, all critical dimensions pass
  NEEDS WORK  — score 45–64, or one critical dimension is weak
  SKIP        — score < 45, or no viral hook exists

Key insight: LOW visual assets ≠ automatic skip.
If factual depth + viral hook are strong, the video is still viable
because animation/AI-generated visuals can fill the gap.
The validator flags this explicitly in production notes.

Usage:
  # Validate a topic directly
  venv/bin/python pipeline/story_validator.py \
    --query "CIA MKUltra drug experiments on civilians" \
    --brand fern_clone

  # Validate from a research brief
  venv/bin/python pipeline/story_validator.py \
    --brief research/fern_clone/briefs/cia_mkultra.json \
    --brand fern_clone

  # Validate all candidates from topic_radar
  venv/bin/python pipeline/story_validator.py \
    --all-candidates --brand fern_clone

Output:
  Prints a scored report. Exits 0 for GO, 1 for SKIP.
  Optionally saves to research/{brand}/validation/{slug}.json
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Fern catalog — duplicate / overlap detection (runs BEFORE all other checks)
# ---------------------------------------------------------------------------

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

_OVERLAP_HARD_SKIP = 0.60
_OVERLAP_WARNING   = 0.30


def _load_fern_catalog() -> list:
    """Load all Fern video titles, descriptions, and view counts."""
    catalog = []
    fern_dir = _PROJECT_ROOT / "analysis" / "fern"
    for info_file in sorted(fern_dir.glob("*/video.info.json")):
        try:
            d = json.loads(info_file.read_text())
            raw_desc = (d.get("description") or "")
            clean_desc = re.sub(r"https?://\S+", "", raw_desc)
            clean_desc = re.sub(
                r"\b(use code|coupon|discount|promo|sponsor)\b.*", "",
                clean_desc, flags=re.IGNORECASE
            )
            catalog.append({
                "video_id":    info_file.parent.name,
                "title":       d.get("title", ""),
                "view_count":  d.get("view_count", 0),
                "description": clean_desc[:400],
            })
        except Exception:
            pass
    return catalog


def _key_terms_overlap(text: str) -> set:
    words = re.findall(r"\b\w+\b", text.lower())
    return {w for w in words if w not in _OVERLAP_STOPWORDS and len(w) > 3}


def _fern_entry_similarity(query: str, entry: dict) -> float:
    """0.0–1.0 similarity: Jaccard on title key terms + acronym + proper-noun bonuses.
    Uses title ONLY for Jaccard (description dilutes with sponsor/source noise)."""
    q_terms = _key_terms_overlap(query)
    f_terms = _key_terms_overlap(entry["title"])   # title only for Jaccard

    if not q_terms or not f_terms:
        return 0.0

    overlap = q_terms & f_terms
    jaccard = len(overlap) / max(len(q_terms | f_terms), 1)

    # Acronym exact-match bonus (FBI, CIA, KKK…)
    q_ents = set(re.findall(r"\b[A-Z]{2,}\b", query))
    f_ents = set(re.findall(r"\b[A-Z]{2,}\b", entry["title"]))
    entity_bonus = min(0.30, len(q_ents & f_ents) * 0.15)

    # Proper-noun bonus (people, places, orgs)
    q_proper = set(re.findall(r"\b[A-Z][a-z]{3,}\b", query))
    f_proper = set(re.findall(r"\b[A-Z][a-z]{3,}\b", entry["title"]))
    proper_bonus = min(0.20, len(q_proper & f_proper) * 0.10)

    return min(1.0, jaccard + entity_bonus + proper_bonus)


def _check_fern_overlap(query: str, catalog: list) -> dict:
    """
    Return the best Fern catalog match and a flag:
      HARD_SKIP  (≥ 0.60) — Fern already made this; saves API calls, returns SKIP immediately
      WARNING    (≥ 0.30) — overlapping topic; continues validation but warns
      CLEAR       (< 0.30) — no significant overlap
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


def _print_overlap_result(overlap: dict):
    sim_pct = f"{overlap['similarity']:.0%}"
    if overlap["flag"] == "HARD_SKIP":
        print(f"  ❌ DUPLICATE: {sim_pct} match → '{overlap['matched_title']}'")
        print(f"     {overlap['matched_views']:,} views — Fern's audience already knows this story")
        print(f"     Skipping remaining checks to save time.")
    elif overlap["flag"] == "WARNING":
        print(f"  ⚠  WARNING: {sim_pct} overlap → '{overlap['matched_title']}' ({overlap['matched_views']:,} views)")
        print(f"     Continuing validation — ensure your angle is meaningfully different.")
        if len(overlap.get("top_3", [])) > 1:
            for m in overlap["top_3"][1:]:
                if m["similarity"] > 0.15:
                    print(f"     Also similar: '{m['title']}' ({m['similarity']:.0%})")
    else:
        best = overlap["top_3"][0] if overlap.get("top_3") else None
        if best:
            print(f"  ✓  CLEAR (closest Fern match: '{best['title'][:45]}' at {best['similarity']:.0%})")
        else:
            print(f"  ✓  CLEAR — no significant Fern catalog overlap")


# ---------------------------------------------------------------------------
# Scoring weights — tuned to Fern's formula
# ---------------------------------------------------------------------------

WEIGHTS = {
    "factual_depth":   0.30,   # content is king — most important
    "viral_hook":      0.30,   # no hook = no views, doesn't matter how good the content is
    "story_arc":       0.20,   # narrative completeness
    "visual_assets":   0.10,   # nice to have, not blocking (animation fills gap)
    "public_interest": 0.10,   # trending is a bonus, not a requirement
}

GO_THRESHOLD   = 65   # overall weighted score
SKIP_THRESHOLD = 45

# A topic MUST pass these dimensions regardless of overall score
CRITICAL_DIMS = ["factual_depth", "viral_hook"]
CRITICAL_MIN  = 40   # minimum score per critical dimension


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DimensionResult:
    score: int           # 0–100
    verdict: str         # STRONG / MODERATE / WEAK
    evidence: list       # supporting data points
    notes: list          # human-readable observations


@dataclass
class ValidationResult:
    query: str
    overall_score: int
    verdict: str         # GO / NEEDS_WORK / SKIP
    dimensions: dict     # dimension_name → DimensionResult
    production_notes: list
    visual_strategy: str  # how to fill the visual gap


# ---------------------------------------------------------------------------
# Wikipedia depth check
# ---------------------------------------------------------------------------

def _wiki_search(query: str) -> dict:
    """Quick Wikipedia fetch — returns full article text and metadata."""
    ua = "fern-story-validator/1.0"

    # Step 1: find best matching article title
    search_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": query,
        "srlimit": 3, "format": "json", "utf8": 1,
    })
    try:
        with urllib.request.urlopen(
            urllib.request.Request(search_url, headers={"User-Agent": ua}), timeout=8
        ) as r:
            results = json.loads(r.read()).get("query", {}).get("search", [])
        if not results:
            return {}

        title = results[0]["title"]

        # Step 2: fetch full plain-text via action=parse (avoids exintro truncation)
        parse_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "parse", "page": title,
            "prop": "wikitext|sections", "format": "json", "utf8": 1,
        })
        with urllib.request.urlopen(
            urllib.request.Request(parse_url, headers={"User-Agent": ua}), timeout=10
        ) as r:
            parse_data = json.loads(r.read())

        wikitext = parse_data.get("parse", {}).get("wikitext", {}).get("*", "")
        sections = parse_data.get("parse", {}).get("sections", [])
        section_count = len(sections)

        # Strip wikitext markup for word counting and hook detection
        clean = re.sub(r"\{\{[^}]*\}\}", " ", wikitext)       # templates
        clean = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", clean)  # links
        clean = re.sub(r"={2,}[^=]+=+", " ", clean)           # headings
        clean = re.sub(r"<[^>]+>", " ", clean)                 # HTML tags
        clean = re.sub(r"\s+", " ", clean).strip()

        # Also get article URL
        info_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "titles": title, "prop": "info",
            "inprop": "url", "format": "json", "utf8": 1,
        })
        with urllib.request.urlopen(
            urllib.request.Request(info_url, headers={"User-Agent": ua}), timeout=8
        ) as r:
            info_data = json.loads(r.read())
        page = list(info_data.get("query", {}).get("pages", {}).values())[0]
        url = page.get("fullurl", f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}")

        return {
            "title": title,
            "url": url,
            "word_count": len(clean.split()),
            "section_count": section_count,
            "sections": [s["line"] for s in sections if s.get("toclevel", 0) <= 2],
            "extract": clean,
        }
    except Exception as e:
        return {"error": str(e)}


def score_factual_depth(wiki: dict, news_count: int = 0) -> DimensionResult:
    """
    How much verified factual content exists?
    Proxy: Wikipedia word count + section depth + news coverage.
    """
    word_count = wiki.get("word_count", 0)
    sections   = wiki.get("section_count", 0)
    evidence   = []
    notes      = []

    # Wikipedia depth (primary signal)
    if word_count > 8000:
        wiki_score = 100
        evidence.append(f"Wikipedia: {word_count:,} words ({sections} sections) — deep coverage")
    elif word_count > 4000:
        wiki_score = 80
        evidence.append(f"Wikipedia: {word_count:,} words ({sections} sections) — solid coverage")
    elif word_count > 2000:
        wiki_score = 60
        evidence.append(f"Wikipedia: {word_count:,} words — moderate coverage")
    elif word_count > 500:
        wiki_score = 35
        evidence.append(f"Wikipedia: {word_count:,} words — thin coverage")
        notes.append("May need supplementary sources beyond Wikipedia")
    else:
        wiki_score = 10
        evidence.append("No substantial Wikipedia article found")
        notes.append("CRITICAL: Insufficient documented facts — story may not be fillable")

    # News coverage bonus
    if news_count >= 10:
        news_bonus = 15
        evidence.append(f"News: {news_count} articles found — strong media trail")
    elif news_count >= 5:
        news_bonus = 8
        evidence.append(f"News: {news_count} articles found")
    else:
        news_bonus = 0

    # Estimate fillable minutes (Fern target: 25 min @ 138.7 WPM = 3,467 words of narration)
    # Wikipedia words ≠ script words, but ratio is ~0.4 (script is a curated subset)
    estimated_script_words = int(word_count * 0.4)
    estimated_minutes = estimated_script_words / 138.7
    evidence.append(f"Estimated fillable content: ~{estimated_minutes:.0f} min at 138 WPM")

    if estimated_minutes < 10:
        notes.append(f"Only ~{estimated_minutes:.0f} min of content — will need supplementary research")

    score = min(100, wiki_score + news_bonus)
    verdict = "STRONG" if score >= 70 else "MODERATE" if score >= 45 else "WEAK"

    return DimensionResult(score=score, verdict=verdict, evidence=evidence, notes=notes)


# ---------------------------------------------------------------------------
# Viral hook detection
# ---------------------------------------------------------------------------

# Fern's 6 viral hook archetypes — measured from his top-performing videos
VIRAL_HOOKS = {
    "secret_revealed": {
        "weight": 3.0,
        "patterns": [
            r"\b(classified|declassified|secret|confidential|cover.?up|hidden|suppressed)\b",
            r"\b(never (knew|told|reported|disclosed))\b",
            r"\bFOIA\b", r"\bleaked?\b", r"\bwhistleblow\w*\b",
        ],
        "description": "Hidden information coming to light",
    },
    "institution_betrayal": {
        "weight": 3.0,
        "patterns": [
            r"\b(CIA|FBI|NSA|government|military|police|church|corporation)\b.{0,60}\b(lied|covered|experimented|killed|tortured|deceived|corrupt)\b",
            r"\b(conspiracy|cover.?up|coverup|scandal)\b",
            r"\bpublic (didn.t|never) know\b",
        ],
        "description": "Powerful institution betraying trust of the public",
    },
    "shocking_scale": {
        "weight": 2.0,
        "patterns": [
            r"\b(\d[\d,]+)\s+(people|civilians|victims|patients|soldiers|children|women|men)\b",
            r"\b\$[\d,.]+\s*(billion|million|trillion)\b",
            r"\b(largest|biggest|most (deadly|dangerous|corrupt|extreme|secretive))\b",
            r"\b(thousands?|millions?|hundreds?) of\b",
        ],
        "description": "Numbers that shock — scale of the event",
    },
    "victim_vs_power": {
        "weight": 2.0,
        "patterns": [
            r"\b(torture(d)?|experiment(ed)? on|forced|coerced|imprisoned|kidnapped|disappeared)\b",
            r"\b(innocent|civilian|victim|family|children)\b",
            r"\b(without (consent|knowledge|trial|charges))\b",
        ],
        "description": "Individual victim vs. powerful institution",
    },
    "twist_revelation": {
        "weight": 2.5,
        "patterns": [
            r"\b(not what (it|they|he|she) seem(s|ed)?|turned out|it was actually|in reality)\b",
            r"\b(decades? later|years? later).{0,40}\b(revealed|discovered|found)\b",
            r"\b(unknown|unaware|didn.t know).{0,30}\b(real(ly)?|actually|truth)\b",
        ],
        "description": "The truth is different from what people believed",
    },
    "still_unresolved": {
        "weight": 1.5,
        "patterns": [
            r"\b(still (unknown|unsolved|classified|a mystery))\b",
            r"\b(to this day|even now|nobody knows|never been explained)\b",
            r"\b(cold case|ongoing investigation|unanswered)\b",
        ],
        "description": "The mystery isn't fully solved — keeps audience thinking",
    },
}


def score_viral_hook(text: str) -> DimensionResult:
    """
    Score how many of Fern's 6 viral hook archetypes are present.
    """
    text_lower = text.lower()
    found_hooks = []
    total_weight = 0
    max_possible_weight = sum(h["weight"] for h in VIRAL_HOOKS.values())

    for hook_name, hook_data in VIRAL_HOOKS.items():
        hit = False
        for pattern in hook_data["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                hit = True
                break
        if hit:
            found_hooks.append(hook_name)
            total_weight += hook_data["weight"]

    score = int((total_weight / max_possible_weight) * 100)
    score = min(100, score)

    evidence = []
    notes = []

    for h in found_hooks:
        evidence.append(f"✓ {h}: {VIRAL_HOOKS[h]['description']}")

    missing = [h for h in VIRAL_HOOKS if h not in found_hooks]
    for h in missing:
        notes.append(f"✗ {h}: {VIRAL_HOOKS[h]['description']} — not detected")

    if "secret_revealed" not in found_hooks and "institution_betrayal" not in found_hooks:
        notes.append("WARNING: Neither 'secret revealed' nor 'institution betrayal' detected — Fern's two strongest hooks are both missing")

    verdict = "STRONG" if score >= 60 else "MODERATE" if score >= 35 else "WEAK"

    return DimensionResult(score=score, verdict=verdict, evidence=evidence, notes=notes)


# ---------------------------------------------------------------------------
# Story arc completeness
# ---------------------------------------------------------------------------

ARC_ELEMENTS = {
    "origin": {
        "patterns": [r"\b(began|started|founded|established|in \d{4})\b",
                     r"\b(originally|at first|initially|early)\b"],
        "label": "Origin — how/when it started",
    },
    "escalation": {
        "patterns": [r"\b(grew|expanded|escalated|increased|spread|intensified)\b",
                     r"\b(by \d{4}|within \d+ years|over the next)\b"],
        "label": "Escalation — how it grew or got worse",
    },
    "revelation": {
        "patterns": [r"\b(revealed|discovered|exposed|leaked|declassified|uncovered|found out)\b",
                     r"\b(investigation|hearing|report|inquiry)\b"],
        "label": "Revelation — the moment of discovery",
    },
    "consequence": {
        "patterns": [r"\b(result(ed)?|consequence|aftermath|following|after|led to)\b",
                     r"\b(charged|convicted|sentenced|fired|resigned|apologized)\b"],
        "label": "Consequence — what happened as a result",
    },
    "legacy": {
        "patterns": [r"\b(today|still|legacy|impact|changed|reform|law|policy)\b",
                     r"\b(to this day|remains|continues|ongoing)\b"],
        "label": "Legacy — why it still matters today",
    },
}


def score_story_arc(text: str, sections: list = None) -> DimensionResult:
    """Does a complete narrative arc exist in the source material?"""
    found = {}
    evidence = []
    notes = []

    for element, data in ARC_ELEMENTS.items():
        for pattern in data["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                found[element] = True
                evidence.append(f"✓ {data['label']}")
                break
        if element not in found:
            notes.append(f"✗ {data['label']} — may need supplementary sources")

    # Bonus if Wikipedia has many sections (structural richness)
    if sections and len(sections) >= 5:
        evidence.append(f"Wikipedia has {len(sections)} sections — good structural depth")

    completeness = len(found) / len(ARC_ELEMENTS)
    score = int(completeness * 100)

    # Penalize if revelation is missing — it's the core of Fern's format
    if "revelation" not in found:
        score = max(0, score - 20)
        notes.append("WARNING: No 'revelation' detected — the 'reveal' is Fern's core hook structure")

    verdict = "STRONG" if score >= 80 else "MODERATE" if score >= 50 else "WEAK"

    return DimensionResult(score=score, verdict=verdict, evidence=evidence, notes=notes)


# ---------------------------------------------------------------------------
# Visual asset count (Wikimedia Commons)
# ---------------------------------------------------------------------------

def count_wikimedia_assets(query: str, entities: list = None) -> DimensionResult:
    """
    Search Wikimedia Commons for available images/documents.
    This tells us how much real visual evidence exists.
    Low count ≠ skip — animation/AI can fill the gap.
    """
    ua = "fern-story-validator/1.0"
    total_images = 0
    search_queries = [query]

    # Also search for key people/orgs mentioned
    if entities:
        search_queries.extend(entities[:3])

    all_files = []
    for q in search_queries[:3]:
        try:
            url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
                "action": "query", "list": "search",
                "srsearch": q, "srnamespace": "6",  # namespace 6 = Files
                "srlimit": 20, "format": "json", "utf8": 1,
            })
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": ua}), timeout=8
            ) as r:
                data = json.loads(r.read())
            results = data.get("query", {}).get("search", [])
            for r in results:
                title = r.get("title", "")
                # Filter to images/PDFs only (skip audio/video for now)
                if any(title.lower().endswith(ext) for ext in
                       [".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".pdf", ".svg"]):
                    all_files.append(title)
            time.sleep(0.3)
        except Exception:
            pass

    total_images = len(set(all_files))

    evidence = []
    notes = []

    if total_images >= 50:
        img_score = 100
        evidence.append(f"Wikimedia Commons: {total_images} images/documents found — rich visual library")
    elif total_images >= 20:
        img_score = 75
        evidence.append(f"Wikimedia Commons: {total_images} images found — good visual coverage")
    elif total_images >= 8:
        img_score = 50
        evidence.append(f"Wikimedia Commons: {total_images} images found — moderate visual assets")
    elif total_images >= 2:
        img_score = 25
        evidence.append(f"Wikimedia Commons: {total_images} images found — limited real imagery")
    else:
        img_score = 5
        evidence.append("Wikimedia Commons: No images found for this topic")

    # Always note the animation path
    if img_score < 60:
        notes.append(
            f"Only {total_images} real images found. "
            "This does NOT block production — Fern's style can be replicated with:"
        )
        notes.append("  • Ken Burns on document photos/text cards (free, already built)")
        notes.append("  • AI-generated period-accurate visuals (Midjourney/SDXL)")
        notes.append("  • Future: Blender animation pipeline")

    verdict = "STRONG" if img_score >= 70 else "MODERATE" if img_score >= 40 else "WEAK (animatable)"

    return DimensionResult(score=img_score, verdict=verdict, evidence=evidence, notes=notes)


# ---------------------------------------------------------------------------
# Public interest proxy (Google Trends via pytrends)
# ---------------------------------------------------------------------------

def score_public_interest(query: str) -> DimensionResult:
    """Check search interest via pytrends. Low interest ≠ skip for historical topics."""
    evidence = []
    notes = []

    try:
        from pytrends.request import TrendReq  # type: ignore
        pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        kw = query[:50]
        pt.build_payload([kw], timeframe="today 12-m")
        data = pt.interest_over_time()

        if data.empty:
            score = 30
            evidence.append("Google Trends: No data (topic may be too niche or historical)")
            notes.append("Low search volume is normal for historical/dark-history topics — Fern's audience finds these via YouTube recommendations, not search")
        else:
            avg_interest = int(data[kw].mean())
            peak_interest = int(data[kw].max())
            recent = int(data[kw].tail(4).mean())  # last 4 weeks

            trend = "RISING" if recent > avg_interest * 1.2 else \
                    "STABLE" if recent >= avg_interest * 0.8 else "DECLINING"

            evidence.append(f"Google Trends: avg={avg_interest}/100, peak={peak_interest}/100, trend={trend}")

            if avg_interest >= 50:
                score = 100
            elif avg_interest >= 25:
                score = 75
            elif avg_interest >= 10:
                score = 50
                notes.append("Moderate search interest — YouTube algorithm discovery will matter more than direct search")
            else:
                score = 25
                notes.append("Low current search volume — this may be an evergreen/historical topic (still viable for Fern format)")

    except ImportError:
        score = 40
        evidence.append("pytrends not installed — skipping trend check")
        notes.append("Install with: venv/bin/pip install pytrends")
    except Exception as e:
        score = 35
        evidence.append(f"Trends unavailable: {str(e)[:60]}")

    verdict = "STRONG" if score >= 70 else "MODERATE" if score >= 35 else "WEAK"
    return DimensionResult(score=score, verdict=verdict, evidence=evidence, notes=notes)


# ---------------------------------------------------------------------------
# News coverage quick-check
# ---------------------------------------------------------------------------

def count_news_articles(query: str) -> int:
    """Quick count of Google News results for the query."""
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fern-story-validator/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            content = r.read().decode("utf-8")
        return len(re.findall(r"<item>", content))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Master validation
# ---------------------------------------------------------------------------

def validate_story(query: str, brand_id: str = "fern_clone",
                   brief: dict = None) -> ValidationResult:
    """
    Run all 5 dimension checks and return a ValidationResult with verdict.

    If brief is provided, reuses its Wikipedia/news data (avoids redundant fetches).
    """
    print(f"\n{'='*60}")
    print(f"STORY VALIDATION: {query[:55]}")
    print(f"{'='*60}\n")

    # --- [0] Fern catalog overlap check — runs first, can short-circuit ---
    print("[0/5] Checking Fern catalog overlap...")
    fern_catalog = _load_fern_catalog()
    overlap = _check_fern_overlap(query, fern_catalog)
    _print_overlap_result(overlap)
    print()

    if overlap["flag"] == "HARD_SKIP":
        dim_overlap = DimensionResult(
            score=0,
            verdict="DUPLICATE",
            evidence=[
                f"Fern already covered: '{overlap['matched_title']}'",
                f"Views: {overlap['matched_views']:,} | Similarity: {overlap['similarity']:.0%}",
            ],
            notes=["Pick a different topic, or find an angle Fern has not taken."],
        )
        prod_notes = [
            f"FERN DUPLICATE ({overlap['similarity']:.0%} similar): '{overlap['matched_title']}'",
            f"  That video has {overlap['matched_views']:,} views — Fern's audience already knows this story.",
            f"  Produce a different angle or pick a new topic entirely.",
        ]
        if len(overlap.get("top_3", [])) > 1:
            for m in overlap["top_3"][1:]:
                if m["similarity"] > 0.15:
                    prod_notes.append(
                        f"  Also overlaps: '{m['title']}' ({m['similarity']:.0%})"
                    )
        result = ValidationResult(
            query=query,
            overall_score=0,
            verdict="SKIP",
            dimensions={"fern_overlap": dim_overlap},
            production_notes=prod_notes,
            visual_strategy="N/A — topic skipped (Fern duplicate)",
        )
        _print_summary(result)
        return result

    # --- Fetch data (or use brief) ---
    if brief:
        wiki_brief = brief.get("wikipedia", {})
        news_count = len(brief.get("news_coverage", []))
        # Brief only stores a short intro summary — fetch full article for accurate scoring
        if wiki_brief.get("word_count", 0) < 500:
            print(f"  (Brief has {wiki_brief.get('word_count', 0)}-word summary — fetching full Wikipedia article...)")
            wiki = _wiki_search(wiki_brief.get("title", "") or query)
        else:
            wiki = wiki_brief
        # Google News RSS snippets are often just encoded URLs — use titles instead
        news_titles = "\n".join(n.get("title", "") for n in brief.get("news_coverage", []))
        all_text = wiki.get("extract", wiki.get("summary", "")) + "\n" + news_titles
        entities = brief.get("entities", {}).get("people_orgs", [])[:4]
    else:
        print("[1/5] Fetching Wikipedia...")
        wiki = _wiki_search(query)
        time.sleep(0.4)
        print("[2/5] Counting news articles...")
        news_count = count_news_articles(query)
        all_text = wiki.get("extract", "")
        entities = []

    # --- Score each dimension ---
    print("[1/5] Scoring factual depth...")
    dim_depth = score_factual_depth(wiki, news_count)
    _print_dim("Factual Depth", dim_depth)

    print("[2/5] Scoring viral hooks...")
    dim_hooks = score_viral_hook(all_text)
    _print_dim("Viral Hooks", dim_hooks)

    print("[3/5] Scoring story arc...")
    dim_arc = score_story_arc(all_text, wiki.get("sections", []))
    _print_dim("Story Arc", dim_arc)

    print("[4/5] Counting Wikimedia images...")
    dim_visuals = count_wikimedia_assets(query, entities)
    _print_dim("Visual Assets", dim_visuals)

    print("[5/5] Checking public interest...")
    dim_interest = score_public_interest(query)
    _print_dim("Public Interest", dim_interest)

    # --- Compute overall score ---
    dims = {
        "factual_depth":   dim_depth,
        "viral_hook":      dim_hooks,
        "story_arc":       dim_arc,
        "visual_assets":   dim_visuals,
        "public_interest": dim_interest,
    }

    overall = int(sum(
        dims[k].score * WEIGHTS[k] for k in dims
    ))

    # --- Critical dimension check ---
    critical_fail = [
        d for d in CRITICAL_DIMS
        if dims[d].score < CRITICAL_MIN
    ]

    # --- Verdict ---
    if critical_fail:
        verdict = "SKIP"
    elif overall >= GO_THRESHOLD:
        verdict = "GO"
    elif overall >= SKIP_THRESHOLD:
        verdict = "NEEDS_WORK"
    else:
        verdict = "SKIP"

    # --- Production notes ---
    prod_notes = []

    # Fern overlap warning (if any)
    if overlap["flag"] == "WARNING":
        prod_notes.append(
            f"⚠  Overlaps Fern's '{overlap['matched_title']}' "
            f"({overlap['matched_views']:,} views, {overlap['similarity']:.0%} match) — "
            f"ensure your angle is meaningfully different before producing"
        )

    if verdict == "GO":
        prod_notes.append(f"Overall score {overall}/100 — proceed to full research brief")
    elif verdict == "NEEDS_WORK":
        prod_notes.append(f"Overall score {overall}/100 — strengthen weak dimensions before producing")
        for d in dims:
            if dims[d].verdict == "WEAK":
                prod_notes.append(f"  Weak: {d} ({dims[d].score}/100)")
    else:
        prod_notes.append(f"Overall score {overall}/100 — not viable for Fern format")
        for d in critical_fail:
            prod_notes.append(f"  Critical fail: {d} ({dims[d].score}/100 — minimum {CRITICAL_MIN})")

    # Visual strategy note
    vis_score = dim_visuals.score
    if vis_score >= 70:
        visual_strategy = "REAL_ASSETS: Enough Wikimedia images to fill the video. Use Ken Burns on real photos."
    elif vis_score >= 30:
        visual_strategy = "MIXED: Use available real images + fill gaps with text cards, document overlays, and maps."
    else:
        visual_strategy = "ANIMATED: Low real images — use Ken Burns on text/document cards + AI-generated period visuals. Blender pipeline when ready."

    result = ValidationResult(
        query=query,
        overall_score=overall,
        verdict=verdict,
        dimensions=dims,
        production_notes=prod_notes,
        visual_strategy=visual_strategy,
    )

    _print_summary(result)
    return result


def _print_dim(name: str, d: DimensionResult):
    bar = "█" * (d.score // 10) + "░" * (10 - d.score // 10)
    print(f"  {name:<18} [{bar}] {d.score:3d}/100  {d.verdict}")


def _print_summary(r: ValidationResult):
    verdict_color = {"GO": "✅", "NEEDS_WORK": "⚠️", "SKIP": "❌"}
    print(f"\n{'─'*60}")
    print(f"VERDICT: {verdict_color.get(r.verdict, '')} {r.verdict}  (score: {r.overall_score}/100)")
    print(f"{'─'*60}")
    for note in r.production_notes:
        print(f"  {note}")
    print(f"\nVisual Strategy:")
    print(f"  {r.visual_strategy}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _result_to_dict(r: ValidationResult) -> dict:
    return {
        "query": r.query,
        "overall_score": r.overall_score,
        "verdict": r.verdict,
        "visual_strategy": r.visual_strategy,
        "production_notes": r.production_notes,
        "dimensions": {
            k: {
                "score": v.score,
                "verdict": v.verdict,
                "evidence": v.evidence,
                "notes": v.notes,
            }
            for k, v in r.dimensions.items()
        },
    }


def main():
    p = argparse.ArgumentParser(
        description="Pre-production viability gate — GO / NEEDS_WORK / SKIP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--query", help='Topic to validate, e.g. "CIA MKUltra"')
    g.add_argument("--brief", help="Path to existing research brief JSON")
    g.add_argument("--all-candidates", action="store_true",
                   help="Validate all topics in research/{brand}/topic_candidates.json")
    p.add_argument("--brand", default="fern_clone")
    p.add_argument("--save", action="store_true",
                   help="Save validation report to research/{brand}/validation/")
    args = p.parse_args()

    results = []

    if args.query:
        r = validate_story(args.query, args.brand)
        results.append(r)

    elif args.brief:
        brief_path = Path(args.brief)
        if not brief_path.exists():
            print(f"ERROR: Brief not found: {brief_path}")
            sys.exit(1)
        brief = json.loads(brief_path.read_text())
        query = brief.get("query", brief_path.stem)
        r = validate_story(query, args.brand, brief=brief)
        results.append(r)

    elif args.all_candidates:
        candidates_path = Path(f"research/{args.brand}/topic_candidates.json")
        if not candidates_path.exists():
            print(f"ERROR: No topic_candidates.json — run topic_radar.py first")
            sys.exit(1)
        candidates = json.loads(candidates_path.read_text()).get("candidates", [])
        print(f"\nValidating {len(candidates)} topic candidates...\n")
        for c in candidates:
            query = c.get("title", "")
            if not query:
                continue
            r = validate_story(query, args.brand)
            results.append(r)
            time.sleep(1)

        # Summary table
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        go      = [r for r in results if r.verdict == "GO"]
        needs   = [r for r in results if r.verdict == "NEEDS_WORK"]
        skip    = [r for r in results if r.verdict == "SKIP"]
        print(f"  GO:          {len(go)}")
        print(f"  NEEDS WORK:  {len(needs)}")
        print(f"  SKIP:        {len(skip)}")
        if go:
            print(f"\n  Best candidates:")
            for r in sorted(go, key=lambda x: -x.overall_score)[:5]:
                print(f"    [{r.overall_score}/100] {r.query[:55]}")

    if args.save:
        out_dir = Path(f"research/{args.brand}/validation")
        out_dir.mkdir(parents=True, exist_ok=True)
        for r in results:
            slug = re.sub(r"[^\w]+", "_", r.query.lower())[:60].strip("_")
            out_file = out_dir / f"{slug}.json"
            out_file.write_text(json.dumps(_result_to_dict(r), indent=2))
            print(f"\nSaved: {out_file}")

    # Exit code: 0 for GO, 1 for anything else (useful in shell scripts)
    if results and results[-1].verdict != "GO":
        sys.exit(1)


if __name__ == "__main__":
    main()
