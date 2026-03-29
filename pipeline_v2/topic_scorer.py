#!/usr/bin/env python3
"""
topic_scorer.py — Score topic viability using Claude + LearnByLeo ideation.json.

7-Test Validation Framework (calibrated against 10 proven hits with 1.8M-5.4M views):

  ORIGINAL 4 (from LearnByLeo playbook):
  1. Fresh Perspective Test — does the idea still feel good after reflection?
  2. Originality Test — has this been done on YouTube? Can we add a twist?
  3. Best Option Test — is this a 5-10x outlier candidate?
  4. Title/Thumbnail Test — can we create a compelling title+thumbnail?

  NEW 3 (from competitor calibration, March 2026):
  5. Blind Spot Test — does the viewer already assume this exists? (9-10/10 = 3.7M+, 5-6/10 = 2.4M)
  6. Timeliness Test — is there a current news wave to ride?
  7. Killer Stat Test — is there ONE shareable number that IS the video?

Verdict thresholds:
  - GO: overall 85+ AND all 7 tests score 65+
  - NEEDS_WORK: 60-84
  - SKIP: below 60

Usage:
    from pipeline_v2.topic_scorer import score_topic
    result = score_topic("The Secret Algorithm That Controls Your Life")
"""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude

# Calibration data from competitor analysis (March 2026)
# Used in the prompt to anchor scoring against real-world performance
CALIBRATION_EXAMPLES = """
CALIBRATION — these are PROVEN hits. Use them to anchor your scoring:
- "We Had 400 People Shop For Groceries" (3.7M views): Blind Spot 9/10 — nobody knew stores charge different people different prices simultaneously. Killer stat: "same cart, 7 different prices, same store, same moment"
- "The $16 TRILLION Race to Mine the Ocean" (5.4M views): Blind Spot 9/10 — nobody knew $16T in metal nodules sit on the ocean floor. Killer stat: "$16 trillion"
- "What Sam Altman Doesn't Want You To Know" (3.8M views): Blind Spot 8/10 — documented pattern of lies assembled for first time. Killer stat: "$1.4T committed on $13B revenue"
- "How the Trucking Industry Got So Terrible" (3.5M views): Blind Spot 7/10 — invisible pay structure nobody outside trucking knows. Killer stat: "paid by mile only — waiting, inspections, traffic = $0"
- "Gold Explained, Finally" (4.9M views): Blind Spot 4/10 BUT Timeliness 10/10 — gold hit $4,000/oz that week. Proves timeliness can compensate for lower novelty.
- "The Downfall of Southwest Airlines" (2.7M views): Blind Spot 6/10 — named villain (Elliott Management PE) behind a beloved brand's destruction.

PATTERN: Blind Spot 9+ = 3.7M+. Blind Spot 5-6 = 2.4-3.6M. Timeliness multiplies everything.
Topics where the audience already assumes "yeah someone's doing that" score 3-4/10 on Blind Spot and underperform.
"""


def load_ideation_playbook() -> dict:
    """Load the LearnByLeo ideation playbook."""
    path = os.path.join(PROJECT_ROOT, "playbook/ideation.json")
    with open(path) as f:
        return json.load(f)


def load_titles_playbook() -> dict:
    """Load the LearnByLeo titles/thumbnails playbook."""
    path = os.path.join(PROJECT_ROOT, "playbook/titles_thumbnails.json")
    with open(path) as f:
        return json.load(f)


def score_topic(topic: str, channel_niche: str = "investigative documentary",
                channel_avg_views: int = 50000) -> dict:
    """
    Score a topic against the 7-test validation framework.

    Returns:
        {
            overall_score: 0-100,
            verdict: "GO" | "NEEDS_WORK" | "SKIP",
            tests: {test_name: {score, reasoning, suggestions}},
            title_suggestions: [...],
            thumbnail_concepts: [...],
            killer_stats: [...],
            key_risks: [...],
            key_strengths: [...]
        }
    """
    ideation = load_ideation_playbook()
    titles = load_titles_playbook()

    four_tests = json.dumps(ideation["checklists"]["four_test_validation"], indent=2)
    principles = json.dumps(ideation["principles"], indent=2)
    anti_patterns = json.dumps(ideation["anti_patterns"], indent=2)
    title_tactics = json.dumps(titles["tactics"]["twenty_six_click_tactics"][:10], indent=2)

    prompt = f"""You are a ruthless YouTube topic evaluator for an {channel_niche} channel
with ~{channel_avg_views:,} average views per video. You must be BRUTALLY honest.
A new channel with zero brand equity needs topics that are 2x stronger than
what established creators can get away with.

TOPIC: {topic}

{CALIBRATION_EXAMPLES}

Apply the 7-Test Validation Framework. Score each test 0-100:

TESTS 1-4 (LearnByLeo playbook):
{four_tests}

IDEATION PRINCIPLES:
{principles}

ANTI-PATTERNS:
{anti_patterns}

TEST 5 — BLIND SPOT TEST (most important for new channels):
Does the average viewer already know or assume this exists?
- Score 90+: "I had absolutely NO IDEA this existed" (like personalized grocery pricing)
- Score 70-89: "I vaguely knew but not the specifics" (like trucking pay structure)
- Score 50-69: "I assumed someone was doing this but didn't know who" (like PBMs, organ allocation)
- Score 30-49: "Yeah, everyone knows this" (like 'big pharma is bad', 'military spends a lot')
- Score 0-29: "This is literally common knowledge"
Key question: If you told someone the CORE REVEAL at a dinner party, would they say
"wait, WHAT?" or "yeah, I figured"?

TEST 6 — TIMELINESS TEST:
Is there a current news event, cultural moment, or trending topic that makes this
feel urgent RIGHT NOW (March 2026)?
- Score 90+: Major news event this week/month directly related
- Score 70-89: Ongoing cultural conversation this topic plugs into
- Score 50-69: Loosely related to current events
- Score 30-49: Evergreen only, no current hook
- Score 0-29: Actually feels dated or already covered extensively

TEST 7 — KILLER STAT TEST:
Is there ONE specific, shareable number or fact that IS the entire video?
The kind of stat someone would text a friend or post on social media.
- Score 90+: "95% of AI implementations fail" tier — one number, entire video
- Score 70-89: Strong stat but needs context to be shocking
- Score 50-69: Multiple decent stats but no single knockout
- Score 30-49: Stats exist but aren't surprising
- Score 0-29: No quantifiable shock factor

TITLE/THUMBNAIL TACTICS (first 10 of 26):
{title_tactics}

Return valid JSON:
{{
  "overall_score": 0-100,
  "verdict": "GO|NEEDS_WORK|SKIP",
  "tests": {{
    "fresh_perspective_test": {{
      "score": 0-100,
      "reasoning": "...",
      "suggestions": ["..."]
    }},
    "originality_test": {{
      "score": 0-100,
      "reasoning": "...",
      "suggestions": ["..."]
    }},
    "best_option_test": {{
      "score": 0-100,
      "reasoning": "...",
      "suggestions": ["..."]
    }},
    "title_thumbnail_test": {{
      "score": 0-100,
      "reasoning": "...",
      "suggestions": ["..."]
    }},
    "blind_spot_test": {{
      "score": 0-100,
      "reasoning": "...",
      "dinner_party_reaction": "what someone would say if you told them the core reveal",
      "suggestions": ["..."]
    }},
    "timeliness_test": {{
      "score": 0-100,
      "reasoning": "...",
      "current_news_hook": "specific news event or cultural moment to ride",
      "suggestions": ["..."]
    }},
    "killer_stat_test": {{
      "score": 0-100,
      "reasoning": "...",
      "best_stat": "the single most shareable stat/fact",
      "suggestions": ["..."]
    }}
  }},
  "title_suggestions": [
    "Title 1",
    "Title 2",
    "Title 3"
  ],
  "thumbnail_concepts": [
    "Concept 1 description",
    "Concept 2 description",
    "Concept 3 description"
  ],
  "killer_stats": [
    "Stat 1 — the ONE number someone would text a friend",
    "Stat 2 — backup shareable fact",
    "Stat 3 — backup"
  ],
  "key_risks": ["risk1", "risk2"],
  "key_strengths": ["strength1", "strength2"]
}}

VERDICT RULES (strict — new channel with no brand equity):
- GO (85+): All 7 tests score 65+ AND overall is 85+. This topic will work even without an established audience.
- NEEDS_WORK (60-84): Some tests pass but needs refinement. Could work with a stronger angle or better timing.
- SKIP (below 60): Fundamental problems — audience already knows this, no killer stat, or no personal stakes.

Be HARSH. An established creator can make "Gold Explained" work at 4.9M views because of brand.
We cannot. Our topic must be inherently compelling to a cold audience."""

    response = query_claude(prompt, timeout=180)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            result = json.loads(match.group())
            # Enforce verdict rules
            score = result.get("overall_score", 0)
            tests = result.get("tests", {})
            min_test = min((t.get("score", 0) for t in tests.values()), default=0)

            if score >= 85 and min_test >= 65:
                result["verdict"] = "GO"
            elif score >= 60:
                result["verdict"] = "NEEDS_WORK"
            else:
                result["verdict"] = "SKIP"

            return result
    except (json.JSONDecodeError, AttributeError):
        pass

    return {
        "overall_score": 0,
        "verdict": "SKIP",
        "tests": {},
        "title_suggestions": [],
        "thumbnail_concepts": [],
        "killer_stats": [],
        "key_risks": ["scoring failed"],
        "key_strengths": [],
    }


def batch_score_topics(topics: list[str], **kwargs) -> list[dict]:
    """
    Score multiple topics and rank them.

    Args:
        topics: List of topic strings
        **kwargs: Passed to score_topic()

    Returns:
        List of results sorted by overall_score descending
    """
    results = []
    for i, topic in enumerate(topics):
        print(f"\n[{i+1}/{len(topics)}] Scoring: {topic}")
        result = score_topic(topic, **kwargs)
        result["topic"] = topic
        results.append(result)
        score = result.get('overall_score', 0)
        verdict = result.get('verdict', '?')
        blind = result.get('tests', {}).get('blind_spot_test', {}).get('score', '?')
        killer = result.get('tests', {}).get('killer_stat_test', {}).get('score', '?')
        print(f"  Score: {score} — {verdict} | Blind Spot: {blind} | Killer Stat: {killer}")

    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    return results


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Score topic viability (7-test framework)")
    parser.add_argument("topic", nargs="?", help="Topic to score")
    parser.add_argument("--file", "-f", help="File with one topic per line")
    parser.add_argument("--niche", default="investigative documentary",
                        help="Channel niche")
    parser.add_argument("--avg-views", type=int, default=50000,
                        help="Channel average views")
    parser.add_argument("--output", "-o", help="Save results to JSON")
    args = parser.parse_args()

    if args.file:
        topics = [line.strip() for line in Path(args.file).read_text().splitlines()
                  if line.strip()]
        results = batch_score_topics(
            topics, channel_niche=args.niche, channel_avg_views=args.avg_views
        )

        print(f"\n{'='*60}")
        print(f"RANKED TOPICS:")
        for i, r in enumerate(results):
            bs = r.get('tests', {}).get('blind_spot_test', {}).get('score', '?')
            ks = r.get('tests', {}).get('killer_stat_test', {}).get('score', '?')
            print(f"  {i+1}. [{r.get('verdict', '?'):10s}] {r.get('overall_score', 0):3d}/100 "
                  f"(blind:{bs} kill:{ks}) — {r['topic']}")

        if args.output:
            Path(args.output).write_text(json.dumps(results, indent=2))
            print(f"\nResults saved: {args.output}")

    elif args.topic:
        result = score_topic(
            args.topic, channel_niche=args.niche, channel_avg_views=args.avg_views
        )
        print(json.dumps(result, indent=2))

        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
