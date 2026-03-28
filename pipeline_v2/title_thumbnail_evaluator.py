#!/usr/bin/env python3
"""
title_thumbnail_evaluator.py — Score title/thumbnail pairs using Claude + LearnByLeo.

Evaluates against the 26 clickbait tactics from playbook/titles_thumbnails.json
plus the synergy checklist (one-second scan, complementary info, clarity, etc.).

Usage:
    from pipeline_v2.title_thumbnail_evaluator import evaluate_title_thumbnail
    result = evaluate_title_thumbnail(
        title="The Algorithm That Decides If You Deserve Housing",
        thumbnail_description="Split image: happy family on left, red DENIED stamp on right",
    )
"""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude, query_claude_vision


def load_titles_playbook() -> dict:
    """Load the LearnByLeo titles/thumbnails playbook."""
    path = os.path.join(PROJECT_ROOT, "playbook/titles_thumbnails.json")
    with open(path) as f:
        return json.load(f)


def evaluate_title_thumbnail(title: str,
                              thumbnail_description: str = None,
                              thumbnail_image_path: str = None,
                              channel_niche: str = "investigative documentary") -> dict:
    """
    Score a title/thumbnail pair against the LearnByLeo 26 tactics + checklist.

    Provide either thumbnail_description (text) or thumbnail_image_path (image).

    Args:
        title: The video title
        thumbnail_description: Text description of the thumbnail concept
        thumbnail_image_path: Path to actual thumbnail image (uses vision)
        channel_niche: Channel type for context

    Returns:
        {
            overall_score: 0-100,
            checklist_scores: {criterion: {score, reasoning}},
            tactics_applied: [list of tactic IDs used],
            tactics_missing: [list of easy-to-add tactics],
            improvements: [specific suggestions],
            synergy_score: 0-100
        }
    """
    playbook = load_titles_playbook()
    tactics = json.dumps(playbook["tactics"]["twenty_six_click_tactics"], indent=2)
    checklist = json.dumps(playbook["checklists"]["title_thumbnail_score"], indent=2)
    principles = json.dumps(playbook["principles"], indent=2)
    anti_patterns = json.dumps(playbook["anti_patterns"], indent=2)

    thumbnail_info = thumbnail_description or "No thumbnail description provided"

    # If we have an actual image, use vision
    if thumbnail_image_path and os.path.exists(thumbnail_image_path):
        return _evaluate_with_vision(
            title, thumbnail_image_path, tactics, checklist,
            principles, anti_patterns, channel_niche
        )

    prompt = f"""You are evaluating a YouTube title/thumbnail pair for an {channel_niche} channel.

TITLE: {title}
THUMBNAIL CONCEPT: {thumbnail_info}

26 CLICKBAIT TACTICS:
{tactics}

SCORING CHECKLIST:
{checklist}

PRINCIPLES:
{principles}

ANTI-PATTERNS:
{anti_patterns}

EVALUATION TASKS:
1. Score against the 7-criterion checklist (0-100 each)
2. Identify which of the 26 tactics are being used (by ID number)
3. Identify 3-5 tactics that could EASILY be added
4. Check title-thumbnail SYNERGY: do they complement (good) or repeat (bad)?
5. Provide 3 specific improvement suggestions

Return valid JSON:
{{
  "overall_score": 0-100,
  "checklist_scores": {{
    "one_second_scan": {{"score": 0-100, "reasoning": "..."}},
    "complementary_info": {{"score": 0-100, "reasoning": "..."}},
    "tactic_count": {{"score": 0-100, "reasoning": "..."}},
    "clarity_vs_confusion": {{"score": 0-100, "reasoning": "..."}},
    "curiosity_strength": {{"score": 0-100, "reasoning": "..."}},
    "standalone_thumbnail": {{"score": 0-100, "reasoning": "..."}},
    "word_quality": {{"score": 0-100, "reasoning": "..."}}
  }},
  "tactics_applied": [1, 7, 14],
  "tactics_missing_easy": [2, 4, 10],
  "synergy_score": 0-100,
  "synergy_analysis": "Do they complement or repeat?",
  "improvements": [
    "Specific suggestion 1",
    "Specific suggestion 2",
    "Specific suggestion 3"
  ],
  "alternative_titles": [
    "Better title option 1",
    "Better title option 2"
  ]
}}"""

    response = query_claude(prompt, timeout=120)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    return {
        "overall_score": 0,
        "checklist_scores": {},
        "tactics_applied": [],
        "improvements": ["evaluation failed"],
    }


def _evaluate_with_vision(title: str, image_path: str,
                           tactics: str, checklist: str,
                           principles: str, anti_patterns: str,
                           channel_niche: str) -> dict:
    """Evaluate with actual thumbnail image using Claude vision."""
    prompt = f"""You are evaluating a YouTube title/thumbnail pair for an {channel_niche} channel.

TITLE: {title}

The attached image is the thumbnail. Evaluate it against:

26 CLICKBAIT TACTICS:
{tactics}

SCORING CHECKLIST:
{checklist}

PRINCIPLES:
{principles}

Return valid JSON:
{{
  "overall_score": 0-100,
  "checklist_scores": {{
    "one_second_scan": {{"score": 0-100, "reasoning": "..."}},
    "complementary_info": {{"score": 0-100, "reasoning": "..."}},
    "tactic_count": {{"score": 0-100, "reasoning": "..."}},
    "clarity_vs_confusion": {{"score": 0-100, "reasoning": "..."}},
    "curiosity_strength": {{"score": 0-100, "reasoning": "..."}},
    "standalone_thumbnail": {{"score": 0-100, "reasoning": "..."}},
    "word_quality": {{"score": 0-100, "reasoning": "..."}}
  }},
  "tactics_applied": [1, 7, 14],
  "tactics_missing_easy": [2, 4, 10],
  "synergy_score": 0-100,
  "synergy_analysis": "...",
  "thumbnail_analysis": "What the thumbnail shows and its strengths/weaknesses",
  "improvements": ["suggestion1", "suggestion2", "suggestion3"],
  "alternative_titles": ["title1", "title2"]
}}"""

    response = query_claude_vision(prompt, image_path, timeout=120)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    return {
        "overall_score": 0,
        "checklist_scores": {},
        "improvements": ["vision evaluation failed"],
    }


def compare_titles(titles: list[str], thumbnail_description: str = None,
                   channel_niche: str = "investigative documentary") -> dict:
    """
    Compare multiple title options and rank them.

    Args:
        titles: List of title options to compare
        thumbnail_description: Common thumbnail concept
        channel_niche: Channel type

    Returns:
        {ranked: [{title, score, reasoning}], winner: str}
    """
    playbook = load_titles_playbook()
    title_rules = json.dumps(playbook["tactics"]["title_optimization"], indent=2)

    titles_block = '\n'.join(f"  {i+1}. {t}" for i, t in enumerate(titles))

    prompt = f"""Compare these YouTube title options for an {channel_niche} channel.

TITLES:
{titles_block}

THUMBNAIL CONCEPT: {thumbnail_description or 'Not specified'}

TITLE OPTIMIZATION RULES:
{title_rules}

Rank all titles from best to worst. For each, explain WHY it works or doesn't.

Return valid JSON:
{{
  "ranked": [
    {{"rank": 1, "title": "...", "score": 0-100, "reasoning": "..."}},
    ...
  ],
  "winner": "the best title",
  "key_factors": ["what made the winner best"]
}}"""

    response = query_claude(prompt, timeout=60)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    return {"ranked": [], "winner": "", "key_factors": ["comparison failed"]}


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate title/thumbnail pairs")
    parser.add_argument("title", nargs="?", help="Video title to evaluate")
    parser.add_argument("--thumbnail", "-t", help="Thumbnail description or image path")
    parser.add_argument("--compare", "-c", nargs="+", help="Compare multiple titles")
    parser.add_argument("--niche", default="investigative documentary",
                        help="Channel niche")
    parser.add_argument("--output", "-o", help="Save results to JSON")
    args = parser.parse_args()

    if args.compare:
        result = compare_titles(
            args.compare,
            thumbnail_description=args.thumbnail,
            channel_niche=args.niche
        )
        print(json.dumps(result, indent=2))
    elif args.title:
        thumbnail_desc = None
        thumbnail_path = None

        if args.thumbnail:
            if os.path.exists(args.thumbnail):
                thumbnail_path = args.thumbnail
            else:
                thumbnail_desc = args.thumbnail

        result = evaluate_title_thumbnail(
            title=args.title,
            thumbnail_description=thumbnail_desc,
            thumbnail_image_path=thumbnail_path,
            channel_niche=args.niche,
        )
        print(json.dumps(result, indent=2))

        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
