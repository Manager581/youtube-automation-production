#!/usr/bin/env python3
"""
topic_scorer.py — Score topic viability using Claude + LearnByLeo ideation.json.

8-Test Validation Framework (calibrated against 10 proven hits with 1.8M-5.4M views):

  ORIGINAL 4 (from LearnByLeo playbook):
  1. Fresh Perspective Test — does the idea still feel good after reflection?
  2. Originality Test — has this been done on YouTube? Can we add a twist?
  3. Best Option Test — is this a 5-10x outlier candidate?
  4. Title/Thumbnail Test — can we create a compelling title+thumbnail?

  NEW 4 (from competitor calibration, March 2026):
  5. Blind Spot Test — does the viewer already assume this exists? (9-10/10 = 3.7M+, 5-6/10 = 2.4M)
  6. Timeliness Test — is there a current news wave to ride?
  7. Killer Stat Test — is there ONE shareable number that IS the video?
  8. 5-Second Title Test — can a cold viewer read the title and instantly know what's at stake FOR THEM?

Verdict thresholds:
  - GO: overall 85+ AND all 8 tests score 65+
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
CALIBRATION — these are PROVEN desk-research hits (no original journalism, no on-location,
no interviews). All made from public documents, filings, and existing reporting.
Use them to anchor your scoring:

TIER 1 — desk-research channels (1.5-2.6M views, realistic for new channel):
- "We Don't Know How Epstein Got So Rich" (2.6M, How Money Works): Blind Spot 8/10 — assembled financial trail nobody had combined. Killer stat: specific dollar figures from public records.
- "The INSANE Truth About IKEA" (2.4M, Magnates Media): Blind Spot 7/10 — hidden corporate structure. Killer stat: "IKEA is technically a charity"
- "The Windows 11 Crisis" (2.4M, ColdFusion): Blind Spot 6/10 — deliberate strategy behind universal frustration. Killer stat: "55% of Microsoft revenue is cloud, not Windows"
- "OpenAI is Suddenly in Trouble" (2.1M, ColdFusion): Blind Spot 7/10 — financial collapse data nobody assembled. Killer stat: "$12 billion lost in one quarter"
- "Replacing Humans with AI Going Wrong" (1.8M, ColdFusion): Blind Spot 7/10 — failure data nobody compiled. Killer stat: "95% of AI implementations fail"
- "The $47 Billion Cult" (1.9M, Magnates Media): Blind Spot 8/10 — unknown corporate cult story. Strong narrative.

TIER 2 — bigger channels doing desk research (2.7-3.8M views, brand halo helps):
- "What Sam Altman Doesn't Want You To Know" (3.8M, More Perfect Union): Blind Spot 8/10 — public lies assembled into pattern. Killer stat: "$1.4T committed on $13B revenue"
- "How the Trucking Industry Got So Terrible" (3.5M, Wendover): Blind Spot 7/10 — invisible pay structure. Killer stat: "paid by mile only"
- "The Downfall of Southwest Airlines" (2.7M, Wendover): Blind Spot 6/10 — named villain (PE firm). Killer stat: "20% margins destroyed by one hedge fund"

PATTERNS FOR DESK RESEARCH:
- Realistic ceiling for new channel: 1.5-2.5M views
- Blind Spot 7-8/10 = 2M+ (data assembly or unknown corporate stories)
- Blind Spot 6/10 = 1.5-2.5M (named villain behind known frustration)
- Timeliness is a multiplier — topic + news wave = 2-3x views
- Named villain > abstract system (always)
- ONE killer stat that fits in a text message is required for sharing
- "Corporate expose" and "data assembly" are the two formats that work without original journalism
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

Apply the 8-Test Validation Framework. Score each test 0-100:

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

TEST 8 — 5-SECOND TITLE TEST (critical for cold audiences):
Can someone with ZERO context read the title and instantly understand what's at stake for THEM?
Within 5 seconds of reading the title, the viewer must know: (a) what the thing is,
(b) that it's hidden/secret/unknown, and (c) that it affects THEM personally.
- Score 90+: "The Secret Score That Controls Your Life" — instant clarity, personal stakes, mystery
- Score 70-89: Clear topic + stakes but requires a moment of thought
- Score 50-69: Interesting but viewer might ask "why should I care?"
- Score 30-49: Viewer has to already know the topic to understand the title (like "Broadridge")
- Score 0-29: Title is confusing or requires domain knowledge
Key test: Show the title to a random person on the street. Do they say "tell me more"
or "I don't get it"? If the TOPIC ITSELF requires explanation, the title will always fail.
Examples:
  PASS: "The Secret Score That Controls Your Life" — everyone has a life, everyone fears secret control
  PASS: "Why New Cars Keep Spying on You" — everyone drives, "spying" = instant personal threat
  FAIL: "The Company That Processes 80% of Corporate Votes" — most people don't vote on corporate things
  FAIL: "How PBMs Control Drug Prices" — nobody knows what a PBM is

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
    }},
    "five_second_title_test": {{
      "score": 0-100,
      "reasoning": "...",
      "street_test": "what a random person on the street would say after reading the best title",
      "instant_clarity": true/false,
      "personal_stakes": true/false,
      "requires_domain_knowledge": true/false,
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
- GO (85+): All 8 tests score 65+ AND overall is 85+. This topic will work even without an established audience.
- NEEDS_WORK (60-84): Some tests pass but needs refinement. Could work with a stronger angle or better timing.
- SKIP (below 60): Fundamental problems — audience already knows this, no killer stat, or no personal stakes.

Be HARSH but REALISTIC. We are a desk-research channel — no original journalism, no on-location
filming, no original interviews. All content made from public documents, filings, existing reporting,
and archival footage. The realistic ceiling is 1.5-2.5M views for a new desk-research channel.

Desk-research formats that work: corporate expose (assemble public data into damning narrative),
unknown story (find something massive nobody has covered), named villain (put a face on shared
frustration), and data assembly (compile scattered facts into one shocking picture).

An established creator can make "Gold Explained" work at 4.9M views because of brand + timeliness.
We cannot rely on brand. Our topic must be inherently compelling to a cold audience."""

    response = query_claude(prompt, timeout=180)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            result = json.loads(match.group())
            # Enforce verdict rules
            score = result.get("overall_score", 0)
            tests = result.get("tests", {})
            min_test = min((t.get("score", 0) for t in tests.values()), default=0)

            # Require all 8 tests present and passing
            if score >= 85 and min_test >= 65 and len(tests) >= 8:
                result["verdict"] = "GO"
            elif score >= 60:
                result["verdict"] = "NEEDS_WORK"
            else:
                result["verdict"] = "SKIP"

            # --- Add source availability test (real data, not Claude) ---
            try:
                from pipeline_v2.source_scanner import scan_sources
                print("  Running source availability scan...")
                inventory = scan_sources(topic, verbose=False)
                source_score = inventory.get("overall_score", 50)
                profile = inventory.get("footage_profile", "unknown")
                counts = inventory.get("counts", {})

                result["tests"]["source_availability_test"] = {
                    "score": source_score,
                    "reasoning": (
                        f"Found {counts.get('total_clips', 0)} clips "
                        f"({counts.get('clips_with_speech', 0)} with speech), "
                        f"{counts.get('unique_channels', 0)} unique channels. "
                        f"Profile: {profile}."
                    ),
                    "footage_profile": profile,
                    "counts": counts,
                    "clip_audio_candidates": inventory.get("clip_audio_candidates", [])[:3],
                }

                # Blend source score into overall (10% weight)
                original_score = result["overall_score"]
                blended = int(original_score * 0.90 + source_score * 0.10)
                result["overall_score"] = blended
                result["source_footage_profile"] = profile

                # Re-evaluate verdict with blended score
                tests = result.get("tests", {})
                min_test = min((t.get("score", 0) for t in tests.values()), default=0)
                if blended >= 85 and min_test >= 65 and len(tests) >= 8:
                    result["verdict"] = "GO"
                elif blended >= 60:
                    result["verdict"] = "NEEDS_WORK"
                else:
                    result["verdict"] = "SKIP"

            except Exception as e:
                result["tests"]["source_availability_test"] = {
                    "score": 50,
                    "reasoning": f"Source scan failed: {e}",
                    "footage_profile": "unknown",
                }

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
