#!/usr/bin/env python3
"""Thumbnail Style Analyzer — matches video thumbnails to reference channel style.

Pipeline:
  1. Download top N thumbnails from each reference channel (yt-dlp)
  2. Re-use already-downloaded thumbnails (WATOP, Fern, Johnny Harris)
  3. Claude vision analyzes each thumbnail for: layout, palette, text, faces,
     visual guides, style keywords
  4. Aggregates patterns across channels in the target genre
  5. Cross-references with playbook/titles_thumbnails.json
  6. Outputs a ChatGPT/DALL-E-ready prompt tuned to the target video's title

Usage:
  python -m pipeline_v2.thumbnail_style_analyzer \\
      --title "Why Breaking the Law Is Profitable" \\
      --output output/thumbnail_prompt.txt

Options:
  --download-missing     Download thumbnails for channels without them yet
  --per-channel N        How many top thumbnails per channel (default 10)
  --reuse-analysis       Use cached thumbnail_analysis.json if exists
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude_vision

# ─── Reference channels ────────────────────────────────────────────────────
# From MEMORY: "Calibration channels: Johnny Harris, Wendover, ColdFusion,
# How Money Works, More Perfect Union"
# Plus existing analysis: Fern, WATOP

CHANNELS = {
    "coldfusion":       {"url": "https://www.youtube.com/@ColdFusion",
                         "dir": "analysis/coldfusion"},
    "how_money_works":  {"url": "https://www.youtube.com/@HowMoneyWorks",
                         "dir": "analysis/how_money_works"},
    "polymatter":       {"url": "https://www.youtube.com/@PolyMatter",
                         "dir": "analysis/polymatter"},
    "wendover":         {"url": "https://www.youtube.com/@Wendoverproductions",
                         "dir": "analysis/wendover"},
    "johnny_harris":    {"url": "https://www.youtube.com/@johnnyharris",
                         "dir": "analysis/johnny_harris",
                         "existing_meta": "analysis/competitor_calibration/competitor_top_videos.json"},
    "more_perfect_union":{"url": "https://www.youtube.com/@MorePerfectUnion",
                          "dir": "analysis/more_perfect_union",
                          "existing_meta": "analysis/competitor_calibration/competitor_top_videos.json"},
    "learnbyleo":       {"url": "https://www.youtube.com/@LearnByLeo",
                         "dir": "analysis/learnbyleo"},
    # Already-analyzed reference sets (no download needed)
    "watop":            {"url": None, "dir": "analysis/watop",
                         "existing_thumbs_pattern": "*_thumbnail.jpg"},
    "fern":             {"url": None, "dir": "analysis/fern/thumbnails",
                         "existing_thumbs_pattern": "*.jpg"},
}

ANALYSIS_OUT = PROJECT_ROOT / "analysis" / "thumbnail_analysis.json"
PLAYBOOK_PATH = PROJECT_ROOT / "playbook" / "titles_thumbnails.json"


# ─── Download helpers ──────────────────────────────────────────────────────

def download_channel_thumbnails(channel_url, out_dir, count=10):
    """Download top N videos' thumbnails from a channel via yt-dlp."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # yt-dlp will download just the thumbnails — skip the video itself
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "--playlist-items", f"1-{count}",
        "-o", str(out_dir / "%(id)s_%(title).80s.%(ext)s"),
        f"{channel_url}/videos",
    ]
    print(f"  yt-dlp → {out_dir}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"    stderr: {result.stderr[-400:]}")
    except subprocess.TimeoutExpired:
        print(f"    timeout after 300s")

    jpgs = list(out_dir.glob("*.jpg"))
    return jpgs


def list_existing_thumbnails(channel_dir, pattern="*.jpg"):
    """List thumbnails already in a channel directory."""
    p = Path(channel_dir)
    if not p.exists():
        return []
    return list(p.glob(pattern))


# ─── Claude vision per-thumbnail ───────────────────────────────────────────

ANALYSIS_PROMPT = """Analyze this YouTube thumbnail and return ONLY a JSON object with these fields:

{
  "layout": "<split-screen|centered-subject|full-bleed-image|chart-foreground|text-dominant>",
  "dominant_colors": ["<hex1>", "<hex2>", "<hex3>"],
  "has_face": <true|false>,
  "face_expression": "<shocked|angry|serious|smiling|none>",
  "text_content": "<exact text visible, or empty string>",
  "text_size": "<huge|large|medium|small|none>",
  "text_color": "<main text color>",
  "has_arrow_or_circle": <true|false>,
  "mood": "<urgent|alarming|analytical|curious|calm|conspiratorial>",
  "subject": "<what or who is the subject, in 5 words>",
  "style_keywords": ["<keyword1>", "<keyword2>", "<keyword3>"]
}

Return ONLY the JSON, no preamble or explanation."""


def analyze_thumbnail(image_path):
    """Call Claude vision on one thumbnail, return parsed JSON dict."""
    response = query_claude_vision(ANALYSIS_PROMPT, str(image_path), timeout=60)
    if not response:
        return None
    # Extract the first JSON object from the response
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


# ─── Aggregation ───────────────────────────────────────────────────────────

def aggregate_patterns(analyses):
    """Extract common patterns from a list of per-thumbnail analyses."""
    n = len(analyses)
    if n == 0:
        return {}

    layouts = Counter(a.get("layout") for a in analyses if a.get("layout"))
    face_rate = sum(1 for a in analyses if a.get("has_face")) / n
    expressions = Counter(a.get("face_expression") for a in analyses
                          if a.get("face_expression") and a.get("face_expression") != "none")
    arrow_rate = sum(1 for a in analyses if a.get("has_arrow_or_circle")) / n
    moods = Counter(a.get("mood") for a in analyses if a.get("mood"))
    text_sizes = Counter(a.get("text_size") for a in analyses if a.get("text_size"))
    text_colors = Counter(a.get("text_color") for a in analyses if a.get("text_color"))

    # Aggregate style keywords
    kw = Counter()
    for a in analyses:
        for k in a.get("style_keywords", []) or []:
            if k:
                kw[k.lower()] += 1

    # Pool colors
    palette = Counter()
    for a in analyses:
        for c in a.get("dominant_colors", []) or []:
            if isinstance(c, str):
                palette[c.upper()] += 1

    return {
        "sample_size": n,
        "layout_distribution": dict(layouts.most_common()),
        "face_presence_rate": round(face_rate, 2),
        "common_expressions": dict(expressions.most_common(3)),
        "arrow_or_circle_rate": round(arrow_rate, 2),
        "common_moods": dict(moods.most_common(3)),
        "text_sizes": dict(text_sizes.most_common()),
        "common_text_colors": dict(text_colors.most_common(3)),
        "top_style_keywords": dict(kw.most_common(8)),
        "top_palette_colors": dict(palette.most_common(6)),
    }


# ─── Prompt generation ────────────────────────────────────────────────────

def build_chatgpt_prompt(title, aggregated, playbook_rules):
    """Compose the final prompt for ChatGPT/DALL-E given aggregated style."""
    top_layouts = list(aggregated["layout_distribution"].keys())[:2]
    top_mood = list(aggregated["common_moods"].keys())[0] if aggregated["common_moods"] else "analytical"
    top_expression = list(aggregated["common_expressions"].keys())[0] if aggregated["common_expressions"] else None
    face_rate = aggregated["face_presence_rate"]
    arrow_rate = aggregated["arrow_or_circle_rate"]
    top_palette = list(aggregated["top_palette_colors"].keys())[:5]
    top_kw = list(aggregated["top_style_keywords"].keys())[:6]
    top_text_size = list(aggregated["text_sizes"].keys())[0] if aggregated["text_sizes"] else "large"
    top_text_color = list(aggregated["common_text_colors"].keys())[0] if aggregated["common_text_colors"] else "white"

    # Playbook rules — pick the top 5-6 that apply to the target video's hook
    tactics = []
    for t in playbook_rules.get("tactics", {}).get("twenty_six_click_tactics", [])[:26]:
        tactics.append(f"{t['tactic']}: {t['description']}")

    face_directive = ""
    if face_rate > 0.5:
        face_directive = f"Include a recognizable human face with a {top_expression or 'serious'} expression."
    else:
        face_directive = "No faces required — focus on iconic objects or data."

    arrow_directive = ""
    if arrow_rate > 0.3:
        arrow_directive = "Use a bold arrow or circle annotation to direct the eye to the key number/fact."

    prompt = f"""Create a YouTube thumbnail for a business/tech documentary titled:
"{title}"

STYLE MATCHED TO REFERENCE CHANNELS: ColdFusion, How Money Works, PolyMatter,
Wendover, Johnny Harris, WATOP. Based on analysis of {aggregated['sample_size']}
real thumbnails from these channels.

=== STYLE DIRECTIVES (derived from analyzed thumbnails) ===
- Layout: {', '.join(top_layouts)}
- Dominant mood: {top_mood}
- Color palette (hex): {', '.join(top_palette)}
- Style keywords: {', '.join(top_kw)}
- Text: {top_text_size} size, color {top_text_color}, ≤3 words
- {face_directive}
- {arrow_directive}

=== PLAYBOOK RULES (from LearnByLeo 26-tactic framework) ===
1. Depict something alarming (bias toward danger)
2. Maximize brightness AND color contrast
3. Show something/someone familiar (recognizable face or brand)
4. Perfect clarity — 1-second scannable on mobile
5. Focus on the 1-2 most intriguing parts (don't describe the whole video)
6. Visual guides (arrows, circles) in a specific order
7. Challenge beliefs / suggest the viewer is misinformed

=== CONTENT INSTRUCTIONS ===
The core insight of this video: corporate fines are smaller than the profits
from breaking the law. The most shareable data points are:
  - Mark Zuckerberg personally GAINED $1.1B the day Facebook was fined $5B
  - Over $1 TRILLION in corporate fines since 2000
  - Ford calculated in 1977 it was cheaper to pay death settlements than fix cars

Pick ONE of these as the thumbnail's central hook. Make the contrast between
punishment and reward visually obvious.

Text on the thumbnail should be 1-3 words only.  Examples that would work:
  - "CRIME PAYS"
  - "+$1.1B" (green, next to a fine stat in red)
  - "$5B FINE = STOCK UP"

Return ONE detailed DALL-E-ready image generation prompt that captures all
of the above. Target 1280×720 aspect ratio. Describe specific visual elements,
not just adjectives.
"""
    return prompt


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="Why Breaking the Law Is Profitable")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "output" / "thumbnail_prompt.txt"))
    parser.add_argument("--download-missing", action="store_true",
                        help="Download thumbnails for channels without them")
    parser.add_argument("--per-channel", type=int, default=8)
    parser.add_argument("--reuse-analysis", action="store_true",
                        help="Reuse cached thumbnail_analysis.json if present")
    parser.add_argument("--max-thumbnails", type=int, default=50,
                        help="Max thumbnails to vision-analyze (limits cost)")
    args = parser.parse_args()

    print("="*60)
    print("  Thumbnail Style Analyzer")
    print("="*60)

    # ── Collect thumbnails from all channels ──────────────────────────────
    all_thumbs = {}  # channel_key → [Path, ...]

    for key, meta in CHANNELS.items():
        channel_dir = PROJECT_ROOT / meta["dir"]
        pattern = meta.get("existing_thumbs_pattern", "*.jpg")

        existing = list_existing_thumbnails(channel_dir, pattern)

        if not existing and args.download_missing and meta.get("url"):
            print(f"\nDownloading {key}...")
            channel_dir.mkdir(parents=True, exist_ok=True)
            existing = download_channel_thumbnails(
                meta["url"], channel_dir, count=args.per_channel)

        all_thumbs[key] = existing
        print(f"  {key:22s} {len(existing)} thumbnails")

    total = sum(len(v) for v in all_thumbs.values())
    print(f"\n  TOTAL: {total} thumbnails")

    # ── Vision analysis ────────────────────────────────────────────────────
    cache_path = ANALYSIS_OUT
    analyses_by_channel = defaultdict(list)

    if args.reuse_analysis and cache_path.exists():
        print(f"\nReusing cached analysis: {cache_path}")
        with open(cache_path) as f:
            cached = json.load(f)
        analyses_by_channel = defaultdict(list, cached.get("per_thumbnail", {}))
    else:
        print(f"\nAnalyzing thumbnails with Claude vision (max {args.max_thumbnails})...")
        analyzed_count = 0
        # Spread across channels fairly
        per_channel_limit = max(3, args.max_thumbnails // max(1, len([c for c in all_thumbs if all_thumbs[c]])))
        for ch, thumbs in all_thumbs.items():
            if analyzed_count >= args.max_thumbnails:
                break
            for tp in thumbs[:per_channel_limit]:
                if analyzed_count >= args.max_thumbnails:
                    break
                analysis = analyze_thumbnail(tp)
                if analysis:
                    analyses_by_channel[ch].append(analysis)
                    analyzed_count += 1
                    print(f"  [{analyzed_count:3d}/{args.max_thumbnails}] {ch:22s} {tp.name[:40]}")

        # Cache
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump({"per_thumbnail": dict(analyses_by_channel)}, f, indent=2)

    # ── Aggregate ──────────────────────────────────────────────────────────
    print(f"\nAggregating patterns...")
    all_analyses = []
    per_channel = {}
    for ch, analyses in analyses_by_channel.items():
        if not analyses:
            continue
        per_channel[ch] = aggregate_patterns(analyses)
        all_analyses.extend(analyses)
    overall = aggregate_patterns(all_analyses)

    # ── Load playbook ──────────────────────────────────────────────────────
    with open(PLAYBOOK_PATH) as f:
        playbook = json.load(f)

    # ── Generate prompt ────────────────────────────────────────────────────
    prompt = build_chatgpt_prompt(args.title, overall, playbook)

    # ── Write outputs ──────────────────────────────────────────────────────
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(prompt)

    # Also save aggregated JSON
    out_json = out_path.with_suffix(".json")
    with open(out_json, "w") as f:
        json.dump({
            "title": args.title,
            "overall_style": overall,
            "per_channel_style": per_channel,
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"OUTPUTS:")
    print(f"  Prompt:    {out_path}")
    print(f"  Style JSON: {out_json}")
    print(f"{'='*60}")
    print(f"\n--- AGGREGATED STYLE ---")
    print(json.dumps(overall, indent=2))
    print(f"\n--- GENERATED PROMPT ---")
    print(prompt)


if __name__ == "__main__":
    main()
