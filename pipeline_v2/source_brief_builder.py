#!/usr/bin/env python3
"""
Source Brief Builder — after full sourcing + transcription, builds the
inventory document that the script writer sees.

Input: transcripts.json + source_inventory.json + downloaded clips manifest
Output: source_brief.md + source_brief.json

The source brief tells the script writer:
  - Every clip with its transcript highlights
  - Best quotable moments (timestamps + text)
  - Clip audio candidates ranked by editorial value
  - Available images categorized by topic
  - What's missing (gaps the writer should work around)

Usage:
  python -m pipeline_v2.source_brief_builder
  python -m pipeline_v2.source_brief_builder --transcripts media/breaking_law/transcripts.json
  python -m pipeline_v2.source_brief_builder --inventory storyboards/source_inventory.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_TRANSCRIPTS = PROJECT_ROOT / "media" / "breaking_law" / "transcripts.json"
DEFAULT_INVENTORY = PROJECT_ROOT / "storyboards" / "source_inventory.json"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "storyboards" / "source_brief.json"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "storyboards" / "source_brief.md"


def find_quotable_moments(transcript_text, min_words=8, max_words=40):
    """Extract quotable moments from a transcript.

    Looks for complete sentences that are strong quotes:
    - Direct statements (not filler)
    - Reasonable length
    - Contains substantive content
    """
    if not transcript_text:
        return []

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', transcript_text)
    moments = []

    filler_words = {'um', 'uh', 'like', 'you know', 'i mean', 'so basically'}

    for sent in sentences:
        sent = sent.strip()
        words = sent.split()
        word_count = len(words)

        if word_count < min_words or word_count > max_words:
            continue

        # Skip filler-heavy sentences
        lower = sent.lower()
        if any(f in lower for f in filler_words):
            continue

        # Score by "quotability" — strong verbs, specific claims, numbers
        score = 0
        if re.search(r'\d', sent):
            score += 2  # contains numbers
        if any(w in lower for w in ['billion', 'million', 'thousand', 'percent']):
            score += 3  # contains scale
        if any(w in lower for w in ['never', 'always', 'every', 'must', 'illegal', 'criminal']):
            score += 2  # strong language
        if any(w in lower for w in ['said', 'told', 'announced', 'revealed', 'admitted']):
            score += 2  # attribution
        if word_count >= 12:
            score += 1  # substantive length

        if score >= 2:
            moments.append({
                "text": sent,
                "word_count": word_count,
                "score": score,
            })

    # Sort by score, keep top 5
    moments.sort(key=lambda m: -m["score"])
    return moments[:5]


def categorize_clips(transcripts, inventory_clips=None):
    """Categorize clips by their content and usefulness."""
    categories = {
        "interviews": [],      # someone speaking directly
        "news_segments": [],   # news anchors covering the story
        "hearings": [],        # congressional/legal proceedings
        "explainers": [],      # analysis/commentary
        "b_roll": [],          # general footage, no speech
    }

    for clip_name, clip_data in transcripts.items():
        text = clip_data.get("full_text") or clip_data.get("transcript", "")
        title = clip_data.get("title", clip_name)
        lower_title = title.lower()

        if any(w in lower_title for w in ["hearing", "testimony", "deposition", "senate", "congress"]):
            cat = "hearings"
        elif any(w in lower_title for w in ["interview", "speaks", "explains", "responds"]):
            cat = "interviews"
        elif any(w in lower_title for w in ["news", "report", "breaking", "update"]):
            cat = "news_segments"
        elif text and len(text.split()) > 30:
            cat = "explainers"
        else:
            cat = "b_roll"

        entry = {
            "filename": clip_name,
            "title": title,
            "category": cat,
            "has_transcript": bool(text and len(text) > 10),
            "word_count": len(text.split()) if text else 0,
            "quotable_moments": find_quotable_moments(text),
        }

        # Add preview
        if text:
            entry["transcript_preview"] = text[:200]

        categories[cat].append(entry)

    return categories


def build_brief(transcripts, inventory=None):
    """Build the full source brief."""
    categories = categorize_clips(transcripts)

    # Count totals
    total_clips = sum(len(v) for v in categories.values())
    clips_with_transcripts = sum(
        1 for cat in categories.values()
        for clip in cat if clip["has_transcript"]
    )

    # All quotable moments across all clips
    all_quotes = []
    for cat_name, clips in categories.items():
        for clip in clips:
            for moment in clip.get("quotable_moments", []):
                all_quotes.append({
                    **moment,
                    "source_clip": clip["filename"],
                    "category": cat_name,
                })

    all_quotes.sort(key=lambda q: -q["score"])
    top_quotes = all_quotes[:15]

    # Clip audio candidates (ranked)
    clip_audio_candidates = []
    for cat_name in ["hearings", "interviews", "news_segments"]:
        for clip in categories.get(cat_name, []):
            if clip["has_transcript"] and clip["word_count"] > 20:
                clip_audio_candidates.append({
                    "filename": clip["filename"],
                    "category": cat_name,
                    "word_count": clip["word_count"],
                    "top_quote": clip["quotable_moments"][0]["text"] if clip["quotable_moments"] else None,
                })

    # Identify gaps
    gaps = []
    if len(categories["hearings"]) == 0:
        gaps.append("No hearing/testimony footage — can't show legal proceedings directly")
    if len(categories["interviews"]) == 0:
        gaps.append("No interview footage — limited first-person perspectives")
    if clips_with_transcripts < 5:
        gaps.append(f"Only {clips_with_transcripts} clips have transcripts — many clips are opaque")
    if len(clip_audio_candidates) < 3:
        gaps.append(f"Only {len(clip_audio_candidates)} clip audio candidates — may need narration-heavy approach")

    # Source inventory data
    inv_data = {}
    if inventory:
        inv_data = {
            "overall_score": inventory.get("overall_score"),
            "footage_profile": inventory.get("footage_profile"),
            "verdict": inventory.get("verdict"),
        }

    brief = {
        "summary": {
            "total_clips": total_clips,
            "clips_with_transcripts": clips_with_transcripts,
            "total_quotable_moments": len(all_quotes),
            "clip_audio_candidates": len(clip_audio_candidates),
            "gaps": gaps,
            **inv_data,
        },
        "categories": {
            cat: [
                {k: v for k, v in clip.items() if k != "quotable_moments"}
                for clip in clips
            ]
            for cat, clips in categories.items()
        },
        "top_quotes": top_quotes,
        "clip_audio_candidates": clip_audio_candidates,
        "gaps": gaps,
    }

    return brief


def brief_to_markdown(brief):
    """Convert brief to readable markdown for the script writer."""
    lines = []
    s = brief["summary"]

    lines.append("# Source Brief")
    lines.append("")
    if s.get("footage_profile"):
        lines.append(f"**Profile:** {s['footage_profile']} | **Score:** {s.get('overall_score', '?')}/100 | **Verdict:** {s.get('verdict', '?')}")
    lines.append(f"**Total clips:** {s['total_clips']} | **With transcripts:** {s['clips_with_transcripts']} | **Clip audio candidates:** {s['clip_audio_candidates']}")
    lines.append("")

    # Gaps
    if s["gaps"]:
        lines.append("## Gaps & Limitations")
        for gap in s["gaps"]:
            lines.append(f"- {gap}")
        lines.append("")

    # Top quotes
    if brief["top_quotes"]:
        lines.append("## Best Quotable Moments")
        lines.append("*These can be used as clip audio moments — the source material tells the story.*")
        lines.append("")
        for q in brief["top_quotes"][:10]:
            lines.append(f'- **"{q["text"]}"** — *{q["source_clip"]}* ({q["category"]})')
        lines.append("")

    # Clip audio candidates
    if brief["clip_audio_candidates"]:
        lines.append("## Clip Audio Candidates")
        lines.append("*Clips where someone is speaking substantively — good for letting source material tell the story.*")
        lines.append("")
        for c in brief["clip_audio_candidates"]:
            quote = f' — "{c["top_quote"][:60]}..."' if c.get("top_quote") else ""
            lines.append(f"- **{c['filename']}** ({c['category']}, {c['word_count']} words){quote}")
        lines.append("")

    # Categories
    for cat_name, cat_label in [
        ("hearings", "Hearing/Testimony Footage"),
        ("interviews", "Interviews"),
        ("news_segments", "News Segments"),
        ("explainers", "Explainers/Commentary"),
        ("b_roll", "B-Roll (no speech)"),
    ]:
        clips = brief["categories"].get(cat_name, [])
        if clips:
            lines.append(f"## {cat_label} ({len(clips)} clips)")
            for clip in clips:
                transcript = f" — *{clip.get('transcript_preview', '')[:80]}...*" if clip.get("has_transcript") else " — no transcript"
                lines.append(f"- **{clip['filename']}**{transcript}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build source brief for script writer")
    parser.add_argument("--transcripts", type=str, default=str(DEFAULT_TRANSCRIPTS))
    parser.add_argument("--inventory", type=str, default=str(DEFAULT_INVENTORY))
    parser.add_argument("--output-json", type=str, default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", type=str, default=str(DEFAULT_OUTPUT_MD))
    args = parser.parse_args()

    # Load transcripts
    transcripts_path = Path(args.transcripts)
    if not transcripts_path.exists():
        print(f"ERROR: Transcripts not found: {transcripts_path}")
        sys.exit(1)

    with open(transcripts_path) as f:
        transcripts_raw = json.load(f)

    # Normalize transcript format (handle various shapes)
    if isinstance(transcripts_raw, dict) and "clips" in transcripts_raw:
        # {clips: [{filename, transcript}, ...]}
        transcripts = {}
        for item in transcripts_raw["clips"]:
            fn = item.get("filename", "")
            transcripts[fn] = item
    elif isinstance(transcripts_raw, list):
        transcripts = {}
        for item in transcripts_raw:
            fn = item.get("filename", "")
            transcripts[fn] = item
    else:
        transcripts = transcripts_raw

    # Load inventory (optional)
    inventory = None
    inv_path = Path(args.inventory)
    if inv_path.exists():
        with open(inv_path) as f:
            inventory = json.load(f)

    print(f"Source Brief Builder")
    print(f"  Transcripts: {len(transcripts)} clips")
    if inventory:
        print(f"  Inventory: {inventory.get('overall_score', '?')}/100 ({inventory.get('footage_profile', '?')})")

    brief = build_brief(transcripts, inventory)
    markdown = brief_to_markdown(brief)

    # Save
    json_path = Path(args.output_json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(brief, f, indent=2)

    md_path = Path(args.output_md)
    with open(md_path, 'w') as f:
        f.write(markdown)

    print(f"\n  Brief: {md_path}")
    print(f"  JSON:  {json_path}")
    print(f"\n{brief['summary']['total_clips']} clips, "
          f"{brief['summary']['clips_with_transcripts']} with transcripts, "
          f"{brief['summary']['clip_audio_candidates']} clip audio candidates")
    if brief["gaps"]:
        print(f"\n  Gaps:")
        for gap in brief["gaps"]:
            print(f"    - {gap}")


if __name__ == "__main__":
    main()
