#!/usr/bin/env python3
"""
Fern Research Pipeline — Topic Discovery + Deep Content Research

Given the FERN formula, this script:
  1. Finds viral-worthy topics (mystery/danger/power/tragedy)
  2. Ranks them by Fern formula match score
  3. Researches the chosen topic deeply using Claude
  4. Outputs structured research ready to feed into script generator

Usage:
    python research_pipeline.py                    # discover + rank topics
    python research_pipeline.py --topic "Unabomber"  # research specific topic
    python research_pipeline.py --full              # discover + research #1 topic automatically
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

FERN_DIR   = Path("analysis/fern")
OUTPUT_DIR = Path("research/fern")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = Anthropic()


# ============================================================================
# LOAD FERN FORMULA
# ============================================================================

def load_formula():
    formula_path = FERN_DIR / "FERN_FORMULA_SOP.md"
    formula_json = FERN_DIR / "FERN_FORMULA.json"

    sop = ""
    if formula_path.exists():
        with open(formula_path) as f:
            sop = f.read()

    # Extract key metrics
    metrics = {}
    if formula_json.exists():
        d = json.load(open(formula_json))
        sf = d.get("script_formula", {})
        metrics = {
            "avg_wpm": round(sf.get("pacing", {}).get("avg_wpm", 161)),
            "duration_minutes": round(d.get("duration_formula", {}).get("median_minutes", 24.5), 1),
            "top_emotions": ["mystery", "fear", "power", "tragedy"],
            "title_patterns": ["Person reference", "Country reference", "Superlative", "How X"],
            "curiosity_gaps_per_min": 0.43,
            "reengagement_every_sec": 492,
        }

    return sop, metrics


# ============================================================================
# TOPIC DISCOVERY
# ============================================================================

def discover_topics(n=10):
    """Use Claude to generate Fern-formula-matched topic ideas"""
    sop, metrics = load_formula()

    print(f"\n🔍 Discovering {n} viral topic ideas matching Fern formula...")

    prompt = f"""You are a YouTube research specialist analyzing the channel FERN (@fern-tv, 4.6M subscribers).

FERN'S FORMULA (extracted from 30 top videos):
{sop[:3000]}

KEY METRICS:
- Duration: {metrics.get('duration_minutes', 24.5)} minutes
- Pacing: {metrics.get('avg_wpm', 161)} WPM
- Top emotions: mystery, fear, power, tragedy
- Best title patterns: Person reference, Country reference, Superlative, "How X"
- Top performing title words: Korea, North, most, how, why, secret, hunt

TOP PERFORMING TITLES FOR REFERENCE:
- "How an FBI Agent Infiltrated the KKK" → 11.2M views
- "The Kid Who Hacked the Pentagon" → 5.4M views
- "The Most Secret Building in Manhattan" → 5.1M views
- "Why Otto Warmbier Didn't Survive North Korea" → 4.7M views
- "Camp 14: The Most Horrible Place in North Korea" → 4.5M views
- "Russia's Most Wanted Hackers" → 4.4M views
- "The Hunt for the Charlie Kirk Shooter" → 4.3M views

Generate {n} unique, viral-worthy YouTube video topics that match Fern's formula exactly.

For each topic provide:
1. Title (using Fern's proven title patterns)
2. Hook (first 2 sentences — must grab immediately)
3. Core angle (what makes this unique/untold)
4. Primary emotion (mystery/fear/power/tragedy/triumph)
5. Fern formula match score (0-100)
6. Estimated viral potential (low/medium/high/very_high)
7. Key research areas (3-5 bullet points of what to research)

Topics must be:
- True stories (not fiction)
- Have a clear villain or danger element
- Have an underdog or redemption angle
- Not widely covered (find the overlooked angle)
- Internationally relevant or US-based with broad appeal

Return as JSON array."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text

    # Extract JSON
    import re
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        topics = json.loads(json_match.group())
    else:
        # Try to parse the whole response
        topics = json.loads(text)

    # Sort by formula match score
    topics.sort(key=lambda x: x.get('fern_formula_match_score', 0), reverse=True)

    return topics


# ============================================================================
# DEEP TOPIC RESEARCH
# ============================================================================

def research_topic(topic_title: str, topic_context: dict = None):
    """Use Claude to deeply research a topic and produce script-ready content"""
    sop, metrics = load_formula()

    print(f"\n📚 Researching: {topic_title}")
    print(f"   This will take ~30 seconds...")

    context_str = ""
    if topic_context:
        context_str = f"""
Topic context:
- Hook: {topic_context.get('hook', '')}
- Core angle: {topic_context.get('core_angle', '')}
- Key research areas: {', '.join(topic_context.get('key_research_areas', []))}
- Primary emotion: {topic_context.get('primary_emotion', 'mystery')}
"""

    prompt = f"""You are a world-class documentary researcher for the YouTube channel FERN.

FERN'S STYLE: Dark, immersive, true-crime/documentary. Uses real events with a cinematic narrative.
Builds mystery through curiosity gaps. Primary emotions: mystery, fear, power, tragedy.

PRODUCTION SPECS:
- Video length: {metrics.get('duration_minutes', 24.5)} minutes
- Script: ~{round(metrics.get('avg_wpm', 161) * metrics.get('duration_minutes', 24.5))} words total
- Pacing: {metrics.get('avg_wpm', 161)} WPM
- Curiosity gaps: every ~{round(1/0.43, 1)} minutes
- Re-engagement hook: every ~8 minutes

TOPIC: {topic_title}
{context_str}

Conduct deep research on this topic and produce:

## 1. EXECUTIVE SUMMARY
- What happened (2-3 sentences)
- Why it's compelling for Fern's audience
- The unique angle no one else has covered this way

## 2. COMPLETE TIMELINE
- Chronological sequence of key events with dates
- Include the moments of highest tension/revelation

## 3. KEY CHARACTERS
For each major person:
- Name + role
- What makes them compelling (hero/villain/victim/survivor)
- Key quotes if known

## 4. CURIOSITY GAPS (12 total, one every ~2 min)
For each gap:
- Setup question (what the narrator teases)
- The answer (revealed later)
- Timestamp suggestion (minute X of the video)

## 5. EMOTIONAL ARC
Map the emotional journey:
- 0-5 min: Hook + setup emotion
- 5-10 min: Building tension
- 10-15 min: Major revelation
- 15-20 min: Crisis/climax
- 20-25 min: Resolution/aftermath

## 6. VISUAL DIRECTIONS
For each major section, suggest:
- Type of footage (archival, recreations, documents, maps, photos)
- Specific visuals to source (be specific)
- Text overlays or graphics needed

## 7. SCRIPT OUTLINE
Section-by-section breakdown:
- Hook (0:00-0:30): First words + visual
- Act 1 (0:30-8:00): Setup — what + who + why it matters
- Re-engagement hook at 8:00
- Act 2 (8:00-16:00): Escalation + major revelations
- Re-engagement hook at 16:00
- Act 3 (16:00-24:00): Climax + resolution
- End card (24:00+): Call to action

## 8. OPENING HOOK (write it fully)
Write the complete first 60 seconds of script (word for word).
Must match Fern's style: immersive, present-tense where possible,
drops the viewer into the action immediately.

## 9. TITLE OPTIONS (5 variants)
Using Fern's proven title patterns. Include:
- Primary recommendation
- 4 alternatives
- Expected view range estimate for each

## 10. SOURCES & VERIFICATION
List key sources to verify facts before production."""

    # Use streaming for long response
    full_response = ""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            full_response += text
            print(text, end='', flush=True)

    print("\n")
    return full_response


# ============================================================================
# SAVE RESEARCH
# ============================================================================

def save_research(topic_title: str, content: str, topics_data: dict = None):
    """Save research to file"""
    safe_name = topic_title.lower().replace(' ', '_').replace('/', '-')[:50]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    out_path = OUTPUT_DIR / f"{safe_name}_{timestamp}.md"

    header = f"""# Research: {topic_title}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Model: claude-opus-4-6
Formula: FERN (@fern-tv)

"""
    if topics_data:
        header += f"""## Formula Match
- Score: {topics_data.get('fern_formula_match_score', 'N/A')}/100
- Viral potential: {topics_data.get('estimated_viral_potential', 'N/A')}
- Primary emotion: {topics_data.get('primary_emotion', 'N/A')}

---

"""

    with open(out_path, 'w') as f:
        f.write(header + content)

    print(f"\n✅ Research saved: {out_path}")
    return out_path


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fern Research Pipeline')
    parser.add_argument('--topic', help='Research a specific topic')
    parser.add_argument('--full', action='store_true', help='Discover topics then auto-research #1')
    parser.add_argument('--discover', action='store_true', help='Just discover and rank topics')
    parser.add_argument('--n', type=int, default=10, help='Number of topics to discover')
    args = parser.parse_args()

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if args.topic:
        # Research specific topic
        content = research_topic(args.topic)
        save_research(args.topic, content)

    elif args.discover or args.full:
        # Discover topics
        topics = discover_topics(args.n)

        print(f"\n{'='*60}")
        print(f"TOP {len(topics)} TOPICS BY FERN FORMULA MATCH")
        print(f"{'='*60}")
        for i, t in enumerate(topics, 1):
            score = t.get('fern_formula_match_score', 0)
            viral = t.get('estimated_viral_potential', '?')
            emotion = t.get('primary_emotion', '?')
            print(f"\n{i}. [{score}/100] [{viral.upper()}] {t.get('title', '?')}")
            print(f"   Emotion: {emotion}")
            print(f"   Hook: {t.get('hook', '')[:100]}...")

        # Save topic list
        topics_path = OUTPUT_DIR / f"topics_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(topics_path, 'w') as f:
            json.dump(topics, f, indent=2)
        print(f"\n✅ Topics saved: {topics_path}")

        if args.full and topics:
            # Auto-research #1
            top = topics[0]
            print(f"\n🎯 Auto-researching top topic: {top.get('title')}")
            content = research_topic(top.get('title', ''), top)
            save_research(top.get('title', 'top_topic'), content, top)

    else:
        parser.print_help()
        print("\nExamples:")
        print("  python research_pipeline.py --discover          # find top 10 topics")
        print("  python research_pipeline.py --full              # find + research #1")
        print("  python research_pipeline.py --topic 'The FBI agent who...'")
