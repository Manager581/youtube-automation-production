#!/usr/bin/env python3
"""
topic_scorer.py — Score topic viability using Claude + LearnByLeo ideation.json.

Applies the 4-test validation from the playbook:
  1. Fresh Perspective Test — does the idea still feel good after reflection?
  2. Originality Test — has this been done on YouTube? Can we add a twist?
  3. Best Option Test — is this a 5-10x outlier candidate?
  4. Title/Thumbnail Test — can we create a compelling title+thumbnail?

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
    Score a topic against the LearnByLeo 4-test validation framework.

    Args:
        topic: The video topic/idea to evaluate
        channel_niche: What kind of channel this is for
        channel_avg_views: Average views per video on the channel

    Returns:
        {
            overall_score: 0-100,
            verdict: "GO" | "NEEDS_WORK" | "SKIP",
            tests: {test_name: {score, reasoning, suggestions}},
            title_suggestions: [...],
            thumbnail_concepts: [...]
        }
    """
    ideation = load_ideation_playbook()
    titles = load_titles_playbook()

    four_tests = json.dumps(ideation["checklists"]["four_test_validation"], indent=2)
    principles = json.dumps(ideation["principles"], indent=2)
    anti_patterns = json.dumps(ideation["anti_patterns"], indent=2)
    title_tactics = json.dumps(titles["tactics"]["twenty_six_click_tactics"][:10], indent=2)

    prompt = f"""You are evaluating a YouTube video topic for an {channel_niche} channel
with ~{channel_avg_views:,} average views per video.

TOPIC: {topic}

Apply the LearnByLeo 4-Test Validation Framework:
{four_tests}

IDEATION PRINCIPLES:
{principles}

ANTI-PATTERNS:
{anti_patterns}

TITLE/THUMBNAIL TACTICS (first 10 of 26):
{title_tactics}

Score each test 0-100 and provide:
1. Your reasoning for the score
2. Specific suggestions to improve if the score is below 80

Also generate:
- 3 title suggestions that apply the clickbait tactics
- 3 thumbnail concept descriptions

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
  "key_risks": ["risk1", "risk2"],
  "key_strengths": ["strength1", "strength2"]
}}

VERDICT RULES:
- GO (80+): All 4 tests score 70+ and overall is 80+
- NEEDS_WORK (50-79): Some tests fail but fixable with adjustments
- SKIP (below 50): Fundamental problems that can't be fixed"""

    response = query_claude(prompt, timeout=120)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return result
    except (json.JSONDecodeError, AttributeError):
        pass

    return {
        "overall_score": 0,
        "verdict": "SKIP",
        "tests": {},
        "title_suggestions": [],
        "thumbnail_concepts": [],
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
        print(f"  Score: {result.get('overall_score', 0)} — {result.get('verdict', '?')}")

    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    return results


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Score topic viability")
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
            print(f"  {i+1}. [{r.get('verdict', '?')}] {r.get('overall_score', 0)}/100 — {r['topic']}")

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
