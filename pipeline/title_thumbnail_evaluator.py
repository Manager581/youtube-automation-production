#!/usr/bin/env python3
"""
Title & Thumbnail Evaluator — Scores title/thumbnail pairs against the 26-tactic playbook.

Slots into run_pipeline.py before script generation (gate: don't write a script
for a topic you can't package). Also usable standalone:

    python -m pipeline.title_thumbnail_evaluator --title "The CIA Scientist Who Knew Too Much" --thumbnail desc.txt
    python -m pipeline.title_thumbnail_evaluator --interactive
    python -m pipeline.title_thumbnail_evaluator --title "..." --thumbnail-image thumb.png

Scoring dimensions (from playbook/titles_thumbnails.json):
  1. Tactic coverage   — How many of the 26 clickbait tactics are used?
  2. Synergy           — Do title and thumbnail complement (not repeat)?
  3. 1-second scan     — Is the reason to watch immediately clear?
  4. Curiosity strength — Does it create a strong "I need to know" feeling?
  5. Word quality       — Short, common, dramatic, front-loaded words?
  6. Standalone thumbnail — Does the thumbnail intrigue without the title?
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playbook.loader import Playbook

OLLAMA_MODEL = "qwen3:4b"


def query_ollama(prompt: str, model: str = OLLAMA_MODEL) -> Optional[str]:
    """Query local Ollama. Returns None if unavailable."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, "--nowordwrap"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def analyze_title_words(title: str) -> dict:
    """Heuristic analysis of title word quality."""
    words = title.split()
    word_count = len(words)

    # Short words (<=6 chars) are better
    short_words = sum(1 for w in words if len(w) <= 6)
    short_ratio = short_words / max(word_count, 1)

    # Title length
    char_count = len(title)

    # Front-loading: are the first 3 words interesting?
    # Common filler starts to penalize
    filler_starts = {"how", "what", "why", "the", "a", "an", "this", "my", "i"}
    first_word = words[0].lower().rstrip(",:;") if words else ""
    front_loaded = first_word not in filler_starts

    # Question mark = curiosity
    is_question = "?" in title

    # Power words
    power_words = {
        "secret", "hidden", "banned", "illegal", "forbidden", "deadly",
        "terrifying", "shocking", "insane", "impossible", "dangerous",
        "truth", "exposed", "revealed", "nobody", "never", "worst",
        "scariest", "strangest", "mysterious", "untold", "lost",
        "forgotten", "classified", "disturbing", "unbelievable",
    }
    power_count = sum(1 for w in words if w.lower().rstrip(",:;!?") in power_words)

    return {
        "word_count": word_count,
        "char_count": char_count,
        "short_word_ratio": round(short_ratio, 2),
        "front_loaded": front_loaded,
        "is_question": is_question,
        "power_word_count": power_count,
        "optimal_length": 6 <= word_count <= 12 and char_count <= 60,
    }


def score_title_heuristic(title: str) -> dict:
    """Score title using pure heuristics (no LLM)."""
    analysis = analyze_title_words(title)
    score = 50  # Baseline

    # Word count: 6-10 is ideal
    wc = analysis["word_count"]
    if 6 <= wc <= 10:
        score += 15
    elif 4 <= wc <= 12:
        score += 8
    else:
        score -= 10

    # Short words
    if analysis["short_word_ratio"] >= 0.7:
        score += 10
    elif analysis["short_word_ratio"] >= 0.5:
        score += 5

    # Front-loaded
    if analysis["front_loaded"]:
        score += 10

    # Power words
    score += min(analysis["power_word_count"] * 5, 15)

    # Question = curiosity
    if analysis["is_question"]:
        score += 5

    return {"score": max(0, min(100, score)), "analysis": analysis}


def evaluate_title_thumbnail(
    title: str,
    thumbnail_description: Optional[str] = None,
    niche: str = "true crime / mystery documentary",
    use_ollama: bool = True,
) -> dict:
    """Score a title/thumbnail pair against the playbook.

    Args:
        title: The proposed video title
        thumbnail_description: Text description of thumbnail concept
            (if no actual image)
        niche: Channel niche for context
        use_ollama: Whether to use local LLM for deeper analysis
    """
    pb = Playbook()
    click_tactics = pb.click_tactics()
    tt_module = pb.module("titles_thumbnails")

    scores = {}
    recommendations = []
    tactics_detected = []

    # --- 1. TITLE WORD QUALITY (heuristic) ---
    title_heuristic = score_title_heuristic(title)
    scores["word_quality"] = title_heuristic["score"]
    analysis = title_heuristic["analysis"]

    if not analysis["front_loaded"]:
        recommendations.append("Move the most compelling word to the START of the title")
    if not analysis["optimal_length"]:
        recommendations.append(f"Title is {analysis['word_count']} words / {analysis['char_count']} chars. Aim for 6-10 words, under 60 chars.")
    if analysis["power_word_count"] == 0:
        recommendations.append("Add a power word (secret, hidden, terrifying, truth, exposed, etc.)")

    # --- 2. TACTIC COVERAGE (LLM or simplified) ---
    if use_ollama and thumbnail_description:
        tactic_list = "\n".join(f"{t['id']}. {t['tactic']}: {t['description']}" for t in click_tactics)
        tactic_prompt = f"""/no_think
Given this YouTube video:
Title: "{title}"
Thumbnail concept: "{thumbnail_description}"
Niche: {niche}

Here are 26 proven clickbait tactics. Which ones does this title/thumbnail pair use?

{tactic_list}

Respond with ONLY a JSON object:
{{"tactics_used": [<list of tactic IDs as integers>], "count": <number>, "strongest_tactic": <ID>, "missing_easy_wins": [<IDs of tactics that could easily be added>]}}"""
        resp = query_ollama(tactic_prompt)
        if resp:
            try:
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    tactics_detected = data.get("tactics_used", [])
                    count = len(tactics_detected)
                    scores["tactic_coverage"] = min(100, count * 15)  # 7+ tactics = 100
                    easy_wins = data.get("missing_easy_wins", [])
                    if easy_wins:
                        win_names = [click_tactics[i-1]["tactic"] for i in easy_wins if 1 <= i <= 26]
                        if win_names:
                            recommendations.append(f"Easy tactic wins: {', '.join(win_names[:3])}")
            except (json.JSONDecodeError, KeyError):
                pass

    if "tactic_coverage" not in scores:
        # Heuristic: check for common tactic signals in title
        tactic_signals = 0
        title_lower = title.lower()
        if any(w in title_lower for w in ["secret", "hidden", "nobody knows"]):
            tactic_signals += 1
        if any(w in title_lower for w in ["dangerous", "deadly", "terrifying", "alarming"]):
            tactic_signals += 1
        if "?" in title:
            tactic_signals += 1
        if any(w in title_lower for w in ["truth", "real", "actually", "really"]):
            tactic_signals += 1
        if any(w in title_lower for w in ["never", "impossible", "no way"]):
            tactic_signals += 1
        scores["tactic_coverage"] = min(100, 30 + tactic_signals * 15)

    # --- 3. SYNERGY (title + thumbnail complement, not repeat) ---
    if use_ollama and thumbnail_description:
        synergy_prompt = f"""/no_think
Rate the SYNERGY between this title and thumbnail (0-100):

Title: "{title}"
Thumbnail: "{thumbnail_description}"

KEY RULE: They must COMPLEMENT each other, not REPEAT the same information.
- 90-100: Each adds a unique hook. Together they create an irresistible package.
- 60-80: Some complementary info, but could be stronger.
- 30-50: They mostly repeat the same message.
- 0-20: They actively work against each other or are confusing together.

Respond with ONLY a JSON object: {{"score": <0-100>, "repeats": true/false, "reason": "<one sentence>"}}"""
        resp = query_ollama(synergy_prompt)
        if resp:
            try:
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    scores["synergy"] = data["score"]
                    if data.get("repeats"):
                        recommendations.append("Title and thumbnail repeat the same info. Make them complementary — each should add a NEW hook.")
            except (json.JSONDecodeError, KeyError):
                pass

    if "synergy" not in scores:
        scores["synergy"] = 50 if thumbnail_description else 0

    # --- 4. 1-SECOND SCAN ---
    if use_ollama:
        scan_prompt = f"""/no_think
Imagine you are scrolling YouTube on your phone. You see this:
Title: "{title}"
{f'Thumbnail: "{thumbnail_description}"' if thumbnail_description else '(no thumbnail described)'}

In LESS THAN 1 SECOND, can you understand:
1. What the video is about?
2. Why you should watch it?

Score the INSTANT CLARITY (0-100):
- 90-100: Immediately obvious what it is and why it's worth watching
- 60-80: You get the gist but need a moment to process
- 30-50: Confusing or vague — requires reading carefully
- 0-20: No idea what this video is about

Respond with ONLY a JSON object: {{"score": <0-100>, "clear_what": true/false, "clear_why": true/false}}"""
        resp = query_ollama(scan_prompt)
        if resp:
            try:
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    scores["one_second_scan"] = data["score"]
                    if not data.get("clear_what"):
                        recommendations.append("Not immediately clear WHAT the video is about. Simplify.")
                    if not data.get("clear_why"):
                        recommendations.append("Not clear WHY someone should watch. Add a stronger reason.")
            except (json.JSONDecodeError, KeyError):
                pass

    if "one_second_scan" not in scores:
        # Heuristic: shorter, punchier titles scan faster
        if analysis["char_count"] <= 50 and analysis["word_count"] <= 8:
            scores["one_second_scan"] = 75
        elif analysis["char_count"] <= 70:
            scores["one_second_scan"] = 55
        else:
            scores["one_second_scan"] = 35

    # --- 5. CURIOSITY STRENGTH ---
    if use_ollama:
        curiosity_prompt = f"""/no_think
Rate how strongly this title creates an "I NEED to know" feeling (0-100):
Title: "{title}"
{f'Thumbnail context: "{thumbnail_description}"' if thumbnail_description else ''}

Consider:
- Does it create a mystery? (strongest)
- Does it challenge beliefs?
- Does it promise something surprising?
- Does it suggest hidden information?
- Is there a puzzle with a missing piece?

Respond with ONLY a JSON object: {{"score": <0-100>, "curiosity_type": "mystery|challenge|surprise|secret|puzzle|weak"}}"""
        resp = query_ollama(curiosity_prompt)
        if resp:
            try:
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    scores["curiosity_strength"] = data["score"]
            except (json.JSONDecodeError, KeyError):
                pass

    if "curiosity_strength" not in scores:
        scores["curiosity_strength"] = 55

    # --- 6. STANDALONE THUMBNAIL ---
    if thumbnail_description and use_ollama:
        standalone_prompt = f"""/no_think
Rate this thumbnail concept on its own, WITHOUT the title (0-100):
Thumbnail: "{thumbnail_description}"

Does it intrigue you? Does it make you want to know more?
A great thumbnail creates curiosity BEFORE you read the title.

Respond with ONLY a JSON object: {{"score": <0-100>, "intriguing_alone": true/false}}"""
        resp = query_ollama(standalone_prompt)
        if resp:
            try:
                match = re.search(r'\{[^}]+\}', resp)
                if match:
                    data = json.loads(match.group())
                    scores["standalone_thumbnail"] = data["score"]
                    if not data.get("intriguing_alone"):
                        recommendations.append("Thumbnail doesn't intrigue on its own. Add a visual mystery or alarming element.")
            except (json.JSONDecodeError, KeyError):
                pass

    if "standalone_thumbnail" not in scores:
        scores["standalone_thumbnail"] = 50 if thumbnail_description else 0

    # --- COMPOSITE ---
    weights = {
        "word_quality": 0.15,
        "tactic_coverage": 0.20,
        "synergy": 0.15,
        "one_second_scan": 0.20,
        "curiosity_strength": 0.20,
        "standalone_thumbnail": 0.10,
    }

    composite = sum(scores.get(k, 50) * weights[k] for k in weights)

    # Verdict
    if composite >= 80:
        verdict = "STRONG — ship it"
        detail = "This title/thumbnail pair is compelling. Proceed to script."
    elif composite >= 65:
        verdict = "GOOD — minor tweaks"
        detail = "Solid package. Address recommendations for maximum CTR."
    elif composite >= 50:
        verdict = "NEEDS WORK"
        detail = "The packaging has significant weaknesses. Rework before committing."
    else:
        verdict = "WEAK — rethink"
        detail = "This won't compete for clicks. Reimagine the angle entirely."

    return {
        "title": title,
        "thumbnail_description": thumbnail_description,
        "scores": scores,
        "weights": weights,
        "composite_score": round(composite, 1),
        "verdict": verdict,
        "verdict_detail": detail,
        "recommendations": recommendations,
        "tactics_detected": tactics_detected,
        "title_analysis": analysis,
    }


def print_report(result: dict):
    """Pretty-print the evaluation report."""
    print(f"\n{'='*60}")
    print(f"  TITLE/THUMBNAIL EVALUATION")
    print(f"{'='*60}")
    print(f"  Title: {result['title']}")
    if result.get("thumbnail_description"):
        desc = result["thumbnail_description"]
        print(f"  Thumb: {desc[:70]}{'...' if len(desc) > 70 else ''}")
    print()

    for dim, score in result["scores"].items():
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        label = dim.replace("_", " ").title()
        weight = result["weights"].get(dim, 0)
        print(f"  {label:22s} {bar} {score:3d}/100  ({weight:.0%})")

    print(f"\n  {'─'*56}")
    print(f"  COMPOSITE:   {result['composite_score']:.1f}/100")
    print(f"  VERDICT:     {result['verdict']}")
    print(f"  {result['verdict_detail']}")

    if result.get("tactics_detected"):
        print(f"\n  TACTICS DETECTED: {len(result['tactics_detected'])} of 26")

    if result["recommendations"]:
        print(f"\n  RECOMMENDATIONS:")
        for r in result["recommendations"]:
            print(f"    ⚠  {r}")

    # Title word analysis
    a = result["title_analysis"]
    print(f"\n  TITLE ANALYSIS: {a['word_count']} words, {a['char_count']} chars, "
          f"{a['power_word_count']} power words, "
          f"{'front-loaded' if a['front_loaded'] else 'NOT front-loaded'}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Evaluate title/thumbnail pair")
    parser.add_argument("--title", "-t", help="Video title to evaluate")
    parser.add_argument("--thumbnail", help="Text file with thumbnail description")
    parser.add_argument("--thumbnail-desc", "-d", help="Inline thumbnail description")
    parser.add_argument("--niche", default="true crime / mystery documentary")
    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument("--no-ollama", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    use_ollama = not args.no_ollama

    if args.interactive:
        print("\nTitle/Thumbnail Evaluator — Interactive Mode")
        print("Type 'quit' to exit.\n")
        while True:
            title = input("Title: ").strip()
            if title.lower() in ("quit", "exit", "q"):
                break
            thumb = input("Thumbnail concept (or Enter to skip): ").strip() or None
            result = evaluate_title_thumbnail(title, thumb, args.niche, use_ollama)
            print_report(result)

    elif args.title:
        thumb_desc = args.thumbnail_desc
        if args.thumbnail:
            thumb_desc = Path(args.thumbnail).read_text().strip()

        result = evaluate_title_thumbnail(args.title, thumb_desc, args.niche, use_ollama)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_report(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
