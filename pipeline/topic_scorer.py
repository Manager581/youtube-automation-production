#!/usr/bin/env python3
"""
Topic Scorer — Evaluates video topic ideas against the playbook's ideation criteria.

Slots into run_pipeline.py between topic_radar and story_validator.
Also usable standalone:

    python -m pipeline.topic_scorer "CIA MKULTRA mind control experiments"
    python -m pipeline.topic_scorer --batch topics.txt
    python -m pipeline.topic_scorer --interactive

Scoring dimensions (from playbook/ideation.json):
  1. Breadth        — Is this interesting to MOST of the audience, not just a niche?
  2. Title viability — Can you imagine a compelling title/thumbnail right now?
  3. Originality     — Has this been done to death on YouTube already?
  4. Outlier potential — Could this 5-10x the channel average?
  5. Curiosity hook   — Does it naturally create a "I need to know" feeling?

Uses local Ollama for scoring (no paid APIs). Falls back to heuristic if Ollama unavailable.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playbook.loader import Playbook


OLLAMA_MODEL = "qwen3:4b"  # Fast local model for scoring


def query_ollama(prompt: str, model: str = OLLAMA_MODEL) -> Optional[str]:
    """Query local Ollama. Returns None if unavailable."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, "--nowordwrap"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def youtube_title_search(topic: str) -> list[str]:
    """Search YouTube for existing videos on this topic. Returns titles found."""
    try:
        # Use yt-dlp to search YouTube
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--print", "%(title)s",
             f"ytsearch10:{topic}"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return []


def jaccard_similarity(a: str, b: str) -> float:
    """Word-level Jaccard similarity between two strings."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def score_topic(topic: str, niche: str = "true crime / mystery documentary",
                use_ollama: bool = True) -> dict:
    """Score a topic idea against the playbook ideation criteria.

    Returns dict with scores (0-100), verdict, and recommendations.
    """
    pb = Playbook()
    ideation = pb.module("ideation")
    principles = ideation["principles"]
    four_tests = ideation["checklists"]["four_test_validation"]["tests"]

    scores = {}
    recommendations = []

    # --- 1. BREADTH SCORE ---
    # How broad is the appeal? Use Ollama or heuristic.
    if use_ollama:
        breadth_prompt = f"""/no_think
Score this video topic for BREADTH OF APPEAL in the "{niche}" niche.
Topic: "{topic}"

Breadth means: would MOST people in this niche find this interesting, or only a tiny subset?

Rules:
- A topic about a specific obscure person = low breadth (30-50)
- A topic about a well-known event/person = high breadth (70-90)
- A topic that combines multiple areas of interest = very high breadth (85-100)
- A topic that is too niche/technical = very low breadth (10-30)

Respond with ONLY a JSON object: {{"score": <0-100>, "reason": "<one sentence>"}}"""
        resp = query_ollama(breadth_prompt)
        if resp:
            try:
                # Extract JSON from response
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    scores["breadth"] = data["score"]
                    if data["score"] < 60:
                        recommendations.append(f"Breadth: {data.get('reason', 'Too niche — broaden the angle')}")
            except (json.JSONDecodeError, KeyError):
                pass

    if "breadth" not in scores:
        # Heuristic fallback: longer, more specific topics tend to be narrower
        word_count = len(topic.split())
        scores["breadth"] = max(20, min(90, 100 - (word_count - 4) * 8))

    # --- 2. TITLE VIABILITY ---
    # Can we imagine a compelling title right now?
    if use_ollama:
        title_prompt = f"""/no_think
Given this video topic: "{topic}"
Niche: "{niche}"

Generate 3 potential YouTube titles and rate how compelling each is (0-100).
A good title: front-loads interesting words, uses short common words, frames as a driving question, creates curiosity.

Respond with ONLY a JSON object:
{{"titles": [{{"title": "...", "score": <0-100>}}, ...], "best_score": <0-100>, "viable": true/false}}"""
        resp = query_ollama(title_prompt)
        if resp:
            try:
                match = re.search(r'\{.*\}', resp, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    scores["title_viability"] = data.get("best_score", 50)
                    if not data.get("viable", True):
                        recommendations.append("Title viability: Struggled to create a compelling title — reconsider the angle")
            except (json.JSONDecodeError, KeyError):
                pass

    if "title_viability" not in scores:
        scores["title_viability"] = 60  # Neutral if we can't assess

    # --- 3. ORIGINALITY ---
    # Search YouTube for existing coverage
    existing_titles = youtube_title_search(topic)
    if existing_titles:
        max_similarity = max(jaccard_similarity(topic, t) for t in existing_titles)
        # High similarity = low originality
        scores["originality"] = max(10, int(100 - max_similarity * 120))
        if max_similarity > 0.5:
            recommendations.append(f"Originality: Very similar videos exist. Add a unique twist or angle.")
        elif max_similarity > 0.3:
            recommendations.append(f"Originality: Some overlap with existing videos. Ensure your angle is distinct.")
    else:
        scores["originality"] = 75  # Can't check, assume moderate

    # --- 4. OUTLIER POTENTIAL ---
    # Could this significantly outperform channel average?
    if use_ollama:
        outlier_prompt = f"""/no_think
Rate the VIRAL POTENTIAL of this video topic (0-100):
Topic: "{topic}"
Niche: "{niche}"

Consider:
- Does it tap into strong emotions (fear, curiosity, outrage, wonder)?
- Is there a shocking revelation or twist?
- Would people share this?
- Does it connect to current events or trends?
- Is there a "there's no way" factor?

Respond with ONLY a JSON object: {{"score": <0-100>, "reason": "<one sentence>"}}"""
        resp = query_ollama(outlier_prompt)
        if resp:
            try:
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    scores["outlier_potential"] = data["score"]
            except (json.JSONDecodeError, KeyError):
                pass

    if "outlier_potential" not in scores:
        scores["outlier_potential"] = 55

    # --- 5. CURIOSITY HOOK ---
    # Does it naturally create "I need to know" feeling?
    if use_ollama:
        curiosity_prompt = f"""/no_think
Rate the NATURAL CURIOSITY this topic creates (0-100):
Topic: "{topic}"

The 4 types of curiosity (from best to worst):
1. Mystery — unanswered question or unsolved case (strongest)
2. Counterintuitive — something that defies expectations
3. Secret — someone is hiding something
4. Missing piece — there's something important we haven't considered

Which types does this topic naturally trigger? Score 0-100.

Respond with ONLY a JSON object: {{"score": <0-100>, "types": ["mystery", ...], "reason": "<one sentence>"}}"""
        resp = query_ollama(curiosity_prompt)
        if resp:
            try:
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    scores["curiosity_hook"] = data["score"]
                    if data["score"] < 60:
                        recommendations.append(f"Curiosity: {data.get('reason', 'Weak curiosity hook — add a mystery or counterintuitive angle')}")
            except (json.JSONDecodeError, KeyError):
                pass

    if "curiosity_hook" not in scores:
        scores["curiosity_hook"] = 55

    # --- COMPOSITE SCORE ---
    weights = {
        "breadth": 0.25,
        "title_viability": 0.20,
        "originality": 0.15,
        "outlier_potential": 0.25,
        "curiosity_hook": 0.15,
    }

    composite = sum(scores[k] * weights[k] for k in weights)

    # --- VERDICT ---
    if composite >= 80:
        verdict = "STRONG GO"
        verdict_detail = "This topic scores well across all dimensions. Proceed to research."
    elif composite >= 65:
        verdict = "GO (with improvements)"
        verdict_detail = "Solid foundation but address the recommendations before committing."
    elif composite >= 50:
        verdict = "NEEDS WORK"
        verdict_detail = "The topic has potential but significant weaknesses. Consider reworking the angle."
    else:
        verdict = "SKIP"
        verdict_detail = "This topic is unlikely to perform well. Find a better idea."

    return {
        "topic": topic,
        "niche": niche,
        "scores": scores,
        "weights": weights,
        "composite_score": round(composite, 1),
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "recommendations": recommendations,
        "existing_videos_found": len(existing_titles),
        "playbook_principles_applied": [p["id"] for p in principles],
    }


def print_report(result: dict):
    """Pretty-print the scoring report."""
    print(f"\n{'='*60}")
    print(f"  TOPIC SCORE: {result['topic']}")
    print(f"{'='*60}\n")

    for dim, score in result["scores"].items():
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        label = dim.replace("_", " ").title()
        weight = result["weights"].get(dim, 0)
        print(f"  {label:20s} {bar} {score:3d}/100  (weight: {weight:.0%})")

    print(f"\n  {'─'*56}")
    composite = result["composite_score"]
    print(f"  COMPOSITE SCORE:   {composite:.1f}/100")
    print(f"  VERDICT:           {result['verdict']}")
    print(f"  {result['verdict_detail']}")

    if result["recommendations"]:
        print(f"\n  RECOMMENDATIONS:")
        for r in result["recommendations"]:
            print(f"    ⚠  {r}")

    if result["existing_videos_found"] > 0:
        print(f"\n  NOTE: Found {result['existing_videos_found']} existing videos on similar topics.")

    print()


def main():
    parser = argparse.ArgumentParser(description="Score a video topic against the playbook")
    parser.add_argument("topic", nargs="?", help="Topic idea to score")
    parser.add_argument("--niche", default="true crime / mystery documentary",
                        help="Channel niche (default: true crime / mystery documentary)")
    parser.add_argument("--batch", help="File with one topic per line")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--no-ollama", action="store_true", help="Skip Ollama (heuristic only)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    use_ollama = not args.no_ollama

    if args.batch:
        topics = Path(args.batch).read_text().strip().split("\n")
        results = []
        for topic in topics:
            topic = topic.strip()
            if not topic:
                continue
            result = score_topic(topic, args.niche, use_ollama)
            results.append(result)
            if not args.json:
                print_report(result)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            # Summary ranking
            results.sort(key=lambda r: r["composite_score"], reverse=True)
            print(f"\n{'='*60}")
            print("  RANKING (best to worst)")
            print(f"{'='*60}")
            for i, r in enumerate(results, 1):
                print(f"  {i}. [{r['composite_score']:.0f}] {r['verdict']:20s} {r['topic']}")
            print()

    elif args.interactive:
        print("\nTopic Scorer — Interactive Mode")
        print("Type a topic idea and press Enter. Type 'quit' to exit.\n")
        while True:
            topic = input("Topic: ").strip()
            if topic.lower() in ("quit", "exit", "q"):
                break
            if not topic:
                continue
            result = score_topic(topic, args.niche, use_ollama)
            print_report(result)

    elif args.topic:
        result = score_topic(args.topic, args.niche, use_ollama)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_report(result)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
