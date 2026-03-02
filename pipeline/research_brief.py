#!/usr/bin/env python3
"""
Research Brief Generator — builds a structured story brief for a topic candidate.

Given a story title/query, auto-fetches:
  - Wikipedia background (summary, key people, timeline)
  - Related news articles (Google News RSS)
  - Possible footage leads (YouTube channels, Internet Archive)
  - Curiosity gaps / open questions

Usage:
    # Brief from a specific topic
    python pipeline/research_brief.py --brand fern_clone --query "CIA MKUltra drug experiments"

    # Brief from top topic_candidates.json result
    python pipeline/research_brief.py --brand fern_clone --pick 1

Output:
    research/{brand_id}/briefs/{slug}.json — structured brief
    research/{brand_id}/briefs/{slug}.md   — human-readable version
"""

import json
import re
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime


# ── Config ────────────────────────────────────────────────────────────────────

def load_brand(brand_id: str) -> dict:
    path = Path(f"brand_configs/{brand_id}.json")
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")
    return json.loads(path.read_text())


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:60].strip("_")


# ── Wikipedia ─────────────────────────────────────────────────────────────────

def fetch_wikipedia_summary(query: str) -> dict:
    """Fetch Wikipedia page summary via the REST API (no key needed)."""
    # Try the search endpoint first to get the best matching article title
    search_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 3,
        "format": "json",
        "utf8": 1,
    })
    try:
        req = urllib.request.Request(search_url, headers={"User-Agent": "fern-research-bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get("query", {}).get("search", [])
        if not results:
            return {}
        best_title = results[0]["pageid"]

        # Fetch full extract
        extract_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query",
            "pageids": best_title,
            "prop": "extracts|categories|links|info",
            "exintro": True,
            "explaintext": True,
            "inprop": "url",
            "format": "json",
            "utf8": 1,
        })
        req2 = urllib.request.Request(extract_url, headers={"User-Agent": "fern-research-bot/1.0"})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            page_data = json.loads(resp2.read())

        pages = page_data.get("query", {}).get("pages", {})
        if not pages:
            return {}
        page = list(pages.values())[0]

        extract = page.get("extract", "")
        return {
            "title": page.get("title", ""),
            "url": page.get("fullurl", f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page.get('title',''))}"),
            "summary": extract[:3000],
            "word_count": len(extract.split()),
        }
    except Exception as e:
        print(f"  ⚠ Wikipedia: {e}")
        return {}


def fetch_wikipedia_sections(title: str) -> list:
    """Get section headings from a Wikipedia article — reveals story structure."""
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "parse",
        "page": title,
        "prop": "sections",
        "format": "json",
        "utf8": 1,
    })
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fern-research-bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        sections = data.get("parse", {}).get("sections", [])
        return [s["line"] for s in sections if s.get("toclevel", 0) <= 2]
    except Exception:
        return []


# ── DuckDuckGo news search ─────────────────────────────────────────────────────

def search_ddg_news(query: str, max_results: int = 8) -> list:
    """Search DuckDuckGo news (no API key needed)."""
    params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1", "t": "fern-research"})
    url = f"https://api.duckduckgo.com/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fern-research-bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        results = []
        # RelatedTopics contains useful summaries
        for item in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(item, dict) and "Text" in item:
                results.append({
                    "title": item.get("Text", "")[:100],
                    "url": item.get("FirstURL", ""),
                    "source": "duckduckgo",
                })
        return results
    except Exception as e:
        print(f"  ⚠ DuckDuckGo: {e}")
        return []


def fetch_google_news(keyword: str, max_results: int = 8) -> list:
    """Fetch Google News RSS for a keyword."""
    query = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fern-research-bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")

        items = []
        entries = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
        for entry in entries[:max_results]:
            title_m = re.search(r"<title>(.*?)</title>", entry)
            link_m = re.search(r"<link>(.*?)</link>", entry)
            desc_m = re.search(r"<description>(.*?)</description>", entry)
            pub_m = re.search(r"<pubDate>(.*?)</pubDate>", entry)
            if title_m:
                title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                title = re.sub(r"\s+-\s+\w[\w\s]+$", "", title).strip()
                items.append({
                    "title": title,
                    "url": link_m.group(1).strip() if link_m else "",
                    "snippet": re.sub(r"<[^>]+>", "", desc_m.group(1) if desc_m else "")[:200],
                    "pub_date": pub_m.group(1).strip() if pub_m else "",
                    "source": "google_news",
                })
        return items
    except Exception as e:
        print(f"  ⚠ Google News: {e}")
        return []


# ── Entity extraction ──────────────────────────────────────────────────────────

def extract_entities(text: str) -> dict:
    """Extract people, places, organizations, dates from text via simple regex."""
    # Named entities (capitalized multi-word phrases)
    people_orgs = re.findall(r"\b[A-Z][a-z]+ (?:[A-Z][a-z]+ )*(?:[A-Z][a-z]+)\b", text)

    # Years
    years = re.findall(r"\b(1[89]\d\d|20[012]\d)\b", text)

    # Looks like an org/agency (all caps 2-5 chars)
    agencies = re.findall(r"\b([A-Z]{2,5})\b", text)
    known_agencies = {"FBI", "CIA", "NSA", "DEA", "ATF", "KGB", "FSB", "MI6",
                      "NATO", "UN", "WHO", "SEC", "FDA", "CDC", "DOJ", "FOIA",
                      "NSC", "DHS", "ICE", "DEA", "INTERPOL", "MOSSAD"}
    found_agencies = list(set(a for a in agencies if a in known_agencies))

    # Countries mentioned
    country_patterns = r"\b(United States|Russia|China|North Korea|Iran|Cuba|Soviet Union|Germany|UK|France|Israel|Ukraine|Afghanistan|Iraq|Syria)\b"
    countries = list(set(re.findall(country_patterns, text)))

    # Deduplicate people/orgs — top 10 most frequent
    from collections import Counter
    entity_counts = Counter(people_orgs)
    top_people = [e for e, _ in entity_counts.most_common(10)]

    return {
        "people_orgs": top_people[:10],
        "agencies": found_agencies,
        "countries": countries[:8],
        "years": sorted(list(set(years)))[-8:],  # most recent years
    }


# ── Footage leads ──────────────────────────────────────────────────────────────

def generate_footage_leads(entities: dict, query: str, brand: dict) -> list:
    """Generate specific footage search queries based on story entities."""
    leads = []

    # YouTube news channel searches
    news_channels = [
        "Reuters", "AP Archive", "BBC", "CNN", "C-SPAN",
        "ABC News", "NBC News", "CBS News", "PBS NewsHour",
    ]

    # Build search queries from entities
    for agency in entities.get("agencies", [])[:3]:
        leads.append({
            "type": "youtube_news",
            "query": f"{agency} {query[:40]}",
            "channels": ["Reuters", "AP Archive", "C-SPAN"],
            "notes": f"Look for {agency} press conferences, hearings, statements",
        })

    for country in entities.get("countries", [])[:2]:
        leads.append({
            "type": "youtube_news",
            "query": f"{country} {query[:40]}",
            "channels": ["Reuters", "AP Archive", "BBC"],
            "notes": f"B-roll of {country}, news reports",
        })

    # Internet Archive search
    leads.append({
        "type": "internet_archive",
        "query": query[:60],
        "url": f"https://archive.org/search?query={urllib.parse.quote(query[:60])}&mediatype=movies",
        "notes": "Archival footage, old news broadcasts, government videos",
    })

    # Specific year-based archive searches
    for year in entities.get("years", [])[-3:]:
        leads.append({
            "type": "internet_archive_news",
            "query": f"{query[:40]} {year}",
            "url": f"https://archive.org/search?query={urllib.parse.quote(query[:40]+' '+year)}&mediatype=movies&and[]=year%3A{year}",
            "notes": f"News footage from {year}",
        })

    # Wikimedia Commons
    leads.append({
        "type": "wikimedia_commons",
        "query": query[:50],
        "url": f"https://commons.wikimedia.org/w/index.php?search={urllib.parse.quote(query[:50])}&title=Special:MediaSearch&type=video",
        "notes": "Public domain photos and videos",
    })

    return leads[:8]


# ── Curiosity gap analysis ─────────────────────────────────────────────────────

def identify_curiosity_gaps(wiki_summary: str, news_items: list) -> list:
    """
    Identify open questions and curiosity gaps in the story.
    These become the 'plants' in the Fern script structure.
    """
    gaps = []

    # Questions implied by the story that aren't immediately answered
    question_triggers = [
        (r"\bwhy\b.{5,80}\?", "Why question"),
        (r"\bhow\b.{5,80}\?", "How question"),
        (r"\bwho\b.{5,80}\?", "Who question"),
        (r"\bwhat\b.{5,80}\?", "What question"),
        (r"\bnever.{5,60}(known|revealed|explained|disclosed)\b", "Unknown fact"),
        (r"\bstill.{5,40}(unknown|unclear|unresolved|mystery)\b", "Unresolved"),
        (r"\b(secret|classified|hidden|undisclosed)\b.{5,60}", "Hidden info"),
    ]

    text = wiki_summary + " ".join(item.get("snippet", "") for item in news_items)
    for pattern, gap_type in question_triggers:
        matches = re.findall(pattern, text[:5000], re.IGNORECASE)
        for m in matches[:2]:
            gaps.append({"type": gap_type, "text": str(m)[:100]})

    # Narrative tension points — events that imply a "what happened next"
    tension_patterns = [
        r"\b(disappeared|vanished|went missing)\b",
        r"\b(was never (found|solved|explained))\b",
        r"\b(controversy|scandal|cover.?up)\b",
        r"\b(died (mysteriously|under suspicious|unexpectedly))\b",
        r"\b(investigation (was|is) (still|ongoing|open))\b",
    ]
    for pattern in tension_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            m = re.search(r".{0,30}" + pattern + r".{0,50}", text, re.IGNORECASE)
            if m:
                gaps.append({"type": "tension", "text": m.group(0)[:100]})

    return gaps[:8]


# ── Fern angle scoring ─────────────────────────────────────────────────────────

def score_for_fern(wiki_summary: str, entities: dict, brand: dict) -> dict:
    """Score how well this topic fits the Fern formula."""
    text = wiki_summary.lower()
    formula = brand["content_formula"]
    filters = brand["topic_filters"]

    institution_hits = [i for i in filters["institutions"] if i.lower() in text]
    theme_hits = [t for t in filters["themes"] if t.lower() in text]

    # Suggest best matching title angle
    best_angle = None
    best_score = 0
    for angle in formula["title_angles_ranked"]:
        score = angle["avg_views"] / 1_000_000
        kws = [k.lower() for k in angle.get("keywords", [])]
        if any(kw in text for kw in kws if kw):
            score += 3
        if score > best_score:
            best_score = score
            best_angle = angle

    # Human angle — is there a specific person at the center?
    has_human_angle = len(entities.get("people_orgs", [])) > 0
    has_institutional_angle = len(institution_hits) > 0

    return {
        "institutions_found": institution_hits[:5],
        "themes_found": theme_hits[:5],
        "has_human_angle": has_human_angle,
        "has_institutional_angle": has_institutional_angle,
        "suggested_angle": best_angle["pattern"] if best_angle else None,
        "suggested_template": best_angle["template"] if best_angle else None,
        "fern_fit_score": len(institution_hits) * 2 + len(theme_hits) * 1 + (3 if has_human_angle else 0),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def build_brief(query: str, brand_id: str) -> dict:
    brand = load_brand(brand_id)

    print(f"\n{'='*60}")
    print(f"RESEARCH BRIEF: {query[:60]}")
    print(f"{'='*60}\n")

    brief = {
        "query": query,
        "brand_id": brand_id,
        "generated_at": datetime.now().isoformat(),
    }

    # 1. Wikipedia
    print("Fetching Wikipedia...")
    wiki = fetch_wikipedia_summary(query)
    if wiki:
        print(f"  → Found: \"{wiki['title']}\" ({wiki['word_count']} words)")
        brief["wikipedia"] = wiki
        sections = fetch_wikipedia_sections(wiki["title"])
        if sections:
            brief["wikipedia"]["sections"] = sections
            print(f"  → Sections: {', '.join(sections[:5])}")
    else:
        print("  → No Wikipedia article found")
        brief["wikipedia"] = {}
    time.sleep(0.5)

    # 2. News coverage
    print("\nFetching news coverage...")
    news_items = fetch_google_news(query, max_results=10)
    # Also search for the exact Wikipedia title if different
    if wiki and wiki.get("title") and wiki["title"].lower() not in query.lower():
        extra_news = fetch_google_news(wiki["title"], max_results=5)
        news_items = (news_items + extra_news)[:12]
    print(f"  → {len(news_items)} news items found")
    brief["news_coverage"] = news_items
    time.sleep(0.5)

    # 3. Entity extraction
    all_text = wiki.get("summary", "") + " ".join(n.get("snippet", "") for n in news_items)
    entities = extract_entities(all_text)
    brief["entities"] = entities
    print(f"  → People/orgs: {', '.join(entities['people_orgs'][:4])}")
    if entities["agencies"]:
        print(f"  → Agencies: {', '.join(entities['agencies'])}")
    if entities["years"]:
        print(f"  → Timeline: {entities['years'][0]} – {entities['years'][-1]}")

    # 4. Footage leads
    print("\nGenerating footage leads...")
    footage_leads = generate_footage_leads(entities, query, brand)
    brief["footage_leads"] = footage_leads
    print(f"  → {len(footage_leads)} footage search leads")

    # 5. Curiosity gaps
    gaps = identify_curiosity_gaps(wiki.get("summary", ""), news_items)
    brief["curiosity_gaps"] = gaps
    if gaps:
        print(f"\n  Curiosity gaps found: {len(gaps)}")
        for g in gaps[:3]:
            print(f"    · [{g['type']}] {g['text'][:80]}")

    # 6. Fern fit score
    fern_fit = score_for_fern(wiki.get("summary", ""), entities, brand)
    brief["fern_fit"] = fern_fit
    print(f"\n  Fern fit score: {fern_fit['fern_fit_score']}/10")
    if fern_fit["suggested_template"]:
        print(f"  Best angle: {fern_fit['suggested_template']}")

    # 7. Script seed — key facts for script writer
    brief["script_seed"] = {
        "hook_options": _generate_hooks(query, wiki, entities, fern_fit, brand),
        "key_facts": _extract_key_facts(wiki.get("summary", "")),
        "open_questions": [g["text"] for g in gaps[:5]],
        "suggested_structure": _suggest_structure(entities, wiki, brand),
    }

    # Save outputs
    output_dir = Path(f"research/{brand_id}/briefs")
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(query)
    json_file = output_dir / f"{slug}.json"
    md_file = output_dir / f"{slug}.md"

    json_file.write_text(json.dumps(brief, indent=2, ensure_ascii=False))
    md_file.write_text(_render_markdown(brief))

    print(f"\n✅ Brief saved:")
    print(f"   JSON: {json_file}")
    print(f"   MD:   {md_file}")

    return brief


def _generate_hooks(query: str, wiki: dict, entities: dict, fern_fit: dict, brand: dict) -> list:
    """Generate 3 Fern-style opening hook options."""
    template = fern_fit.get("suggested_template", "How [Institution] [Shocking Action/Method]")
    agencies = entities.get("agencies", [])
    countries = entities.get("countries", [])
    years = entities.get("years", [])

    hooks = []

    # Hook 1: The reveal hook (start with the most shocking fact)
    wiki_summary = wiki.get("summary", "")
    first_sentence = wiki_summary.split(".")[0] if wiki_summary else query
    hooks.append({
        "type": "reveal",
        "text": f"[SHOCKING FACT]. This is the story of {query[:60]}.",
        "note": "Open on the most disturbing fact, then pull back to explain how we got here",
    })

    # Hook 2: The date hook (grounds the viewer in time)
    if years:
        hooks.append({
            "type": "date_anchor",
            "text": f"In {years[0]}, [PERSON/EVENT] [DID SOMETHING THAT CHANGED EVERYTHING]. What happened next was never supposed to come out.",
            "note": "Lock the viewer in a specific moment in time — creates urgency",
        })

    # Hook 3: The institution hook (Fern's signature opening)
    if agencies:
        agency = agencies[0]
        hooks.append({
            "type": "institution",
            "text": f"The {agency} has a problem. A problem they spent [X years] trying to make sure you'd never find out about.",
            "note": "Opens with institutional credibility + conspiracy of silence = immediate tension",
        })
    elif countries:
        hooks.append({
            "type": "country_dark",
            "text": f"[COUNTRY] has a secret. And the people who discovered it paid with everything.",
            "note": "COUNTRY_DARK angle — strong for authoritarian regime stories",
        })

    return hooks


def _extract_key_facts(text: str) -> list:
    """Pull key sentences from Wikipedia summary — these become script facts."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Filter to substantive sentences (not too short, not too long)
    facts = [s.strip() for s in sentences
             if 40 < len(s) < 300 and not s.startswith("==")]
    return facts[:15]


def _suggest_structure(entities: dict, wiki: dict, brand: dict) -> list:
    """Suggest a Fern-style 25-minute segment structure."""
    sections = wiki.get("sections", [])
    people = entities.get("people_orgs", [])
    years = entities.get("years", [])

    structure = [
        {"segment": "HOOK", "duration_min": 2, "purpose": "Plant the central mystery. Do NOT explain yet."},
        {"segment": "ORIGIN", "duration_min": 4, "purpose": f"Who/what is at the center. Context for {years[0] if years else 'the period'}."},
        {"segment": "ESCALATION_1", "duration_min": 5, "purpose": "First major revelation. Raise the stakes."},
        {"segment": "MIDPOINT_TWIST", "duration_min": 3, "purpose": "The story turns — what the audience assumed was wrong."},
        {"segment": "ESCALATION_2", "duration_min": 5, "purpose": "Deepest point of the story. Darkest moment."},
        {"segment": "RESOLUTION", "duration_min": 4, "purpose": "How it ended / what we know now. Leave some threads open."},
        {"segment": "CODA", "duration_min": 2, "purpose": "Bigger implication. Why this matters TODAY. Next curiosity gap."},
    ]

    # Overlay Wikipedia sections if available
    if sections:
        for i, section in enumerate(sections[:5]):
            if i + 1 < len(structure):
                structure[i + 1]["wiki_section"] = section

    return structure


def _render_markdown(brief: dict) -> str:
    """Render the brief as a human-readable Markdown document."""
    lines = [
        f"# Research Brief: {brief['query']}",
        f"\n**Generated:** {brief['generated_at'][:10]}  ",
        f"**Brand:** {brief['brand_id']}",
        "",
    ]

    # Wikipedia
    wiki = brief.get("wikipedia", {})
    if wiki:
        lines += [
            "## Background (Wikipedia)",
            f"**Article:** [{wiki.get('title', '')}]({wiki.get('url', '')})",
            "",
            wiki.get("summary", "")[:1500],
            "",
        ]
        if wiki.get("sections"):
            lines += ["**Sections:** " + " → ".join(wiki["sections"][:6]), ""]

    # Fern fit
    fern_fit = brief.get("fern_fit", {})
    if fern_fit:
        lines += [
            "## Fern Fit Analysis",
            f"**Score:** {fern_fit.get('fern_fit_score', 0)}/10",
            f"**Best angle:** {fern_fit.get('suggested_template', 'N/A')}",
            f"**Institutions:** {', '.join(fern_fit.get('institutions_found', []))}",
            f"**Themes:** {', '.join(fern_fit.get('themes_found', []))}",
            "",
        ]

    # Entities
    entities = brief.get("entities", {})
    if entities:
        lines += [
            "## Key Entities",
            f"**People/Orgs:** {', '.join(entities.get('people_orgs', [])[:8])}",
            f"**Agencies:** {', '.join(entities.get('agencies', []))}",
            f"**Countries:** {', '.join(entities.get('countries', []))}",
            f"**Timeline:** {' → '.join(entities.get('years', []))}",
            "",
        ]

    # Script seed
    seed = brief.get("script_seed", {})
    if seed:
        lines += ["## Hook Options", ""]
        for h in seed.get("hook_options", []):
            lines += [
                f"**[{h['type'].upper()}]** {h['text']}",
                f"> _{h['note']}_",
                "",
            ]

        lines += ["## Suggested Structure (25 min)", ""]
        for s in seed.get("suggested_structure", []):
            wiki_note = f" ← _{s.get('wiki_section', '')}_" if s.get("wiki_section") else ""
            lines.append(f"- **{s['segment']}** ({s['duration_min']} min): {s['purpose']}{wiki_note}")
        lines.append("")

        if seed.get("key_facts"):
            lines += ["## Key Facts (from Wikipedia)", ""]
            for fact in seed["key_facts"][:10]:
                lines.append(f"- {fact}")
            lines.append("")

        if seed.get("open_questions"):
            lines += ["## Open Questions / Curiosity Gaps", ""]
            for q in seed["open_questions"]:
                lines.append(f"- {q}")
            lines.append("")

    # Footage leads
    footage = brief.get("footage_leads", [])
    if footage:
        lines += ["## Footage Leads", ""]
        for f in footage:
            lines.append(f"- **[{f['type']}]** `{f['query']}` — {f['notes']}")
            if f.get("url"):
                lines.append(f"  → {f['url']}")
        lines.append("")

    # News coverage
    news = brief.get("news_coverage", [])
    if news:
        lines += ["## Recent News", ""]
        for n in news[:8]:
            lines.append(f"- [{n['title']}]({n['url']}) _{n.get('pub_date', '')[:16]}_")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research Brief Generator")
    parser.add_argument("--brand", required=True, help="Brand config ID (e.g. fern_clone)")
    parser.add_argument("--query", default=None, help="Story topic/query to research")
    parser.add_argument("--pick", type=int, default=None,
                        help="Pick topic #N from research/{brand}/topic_candidates.json")
    args = parser.parse_args()

    query = args.query
    if args.pick:
        candidates_file = Path(f"research/{args.brand}/topic_candidates.json")
        if not candidates_file.exists():
            print(f"No topic_candidates.json found. Run topic_radar.py first.")
            exit(1)
        candidates = json.loads(candidates_file.read_text())["candidates"]
        if args.pick > len(candidates):
            print(f"Only {len(candidates)} candidates available.")
            exit(1)
        picked = candidates[args.pick - 1]
        query = picked["title"]
        print(f"Picked topic #{args.pick}: {query}")

    if not query:
        print("Provide --query or --pick N")
        exit(1)

    build_brief(query, args.brand)
