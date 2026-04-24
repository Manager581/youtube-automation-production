#!/usr/bin/env python3
"""
Selects Tagger — pre-process source material for the paper edit.

For each clip: classify A-roll/B-roll, extract quotable moments with timestamps,
extract entity mentions, score visual moments. For images: tag entities, mood, value.

Builds an entity_index — content-aware matching that replaces filename guessing.

Usage:
  python -m pipeline_v2.selects_tagger
  python -m pipeline_v2.selects_tagger --transcripts media/breaking_law/transcripts.json
"""

import argparse
import json
import os
import re
from pathlib import Path
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude

DEFAULT_TRANSCRIPTS = PROJECT_ROOT / "media" / "breaking_law" / "transcripts.json"
DEFAULT_VISION = PROJECT_ROOT / "media" / "breaking_law" / "vision_manifest.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "storyboards" / "breaking_law_selects.json"


def classify_roll_type_heuristic(clip_filename, transcript):
    """Quick heuristic classification before Claude call."""
    lower_name = clip_filename.lower()
    lower_text = transcript.lower() if transcript else ""

    # A-roll indicators: someone speaking to camera/hearing/interview
    a_roll_keywords = ["hearing", "testimony", "interview", "press conference",
                       "deposition", "senate", "congress", "speaks", "testif"]
    if any(kw in lower_name for kw in a_roll_keywords):
        return "a_roll"

    # Stock indicators
    stock_keywords = ["stock", "pexels", "generic", "abstract", "background"]
    if any(kw in lower_name for kw in stock_keywords):
        return "stock"

    # If transcript has substantial speech, likely B-roll with voice-over or A-roll
    if transcript and len(transcript.split()) > 50:
        return "b_roll"  # Claude will refine this

    return "b_roll"


def tag_clip_with_claude(clip_filename, transcript, vision_entry):
    """Use Claude to extract editorial intelligence from a clip."""
    vision_desc = ""
    if vision_entry:
        frames = vision_entry.get("frame_descriptions", [])
        # Get the most useful frame descriptions (skip title cards)
        useful_frames = [f for f in frames
                         if not any(x in f.get("description", "").lower()
                                    for x in ["title card", "text-only", "chapter card"])]
        if useful_frames:
            vision_desc = "\n".join(
                f"  @{f['timestamp']:.0f}s: {f['description'][:150]}"
                for f in useful_frames[:5]
            )

    prompt = f"""Analyze this video clip for a documentary editor.

CLIP: {clip_filename}

FULL TRANSCRIPT:
{transcript or '(no transcript available)'}

VISUAL DESCRIPTIONS:
{vision_desc or '(no vision data)'}

Return valid JSON:
{{
  "roll_type": "a_roll" or "b_roll" or "stock",
  "roll_reasoning": "why this classification",
  "quotable_moments": [
    {{
      "text": "exact quote from transcript (8-40 words)",
      "editorial_value": 1-10,
      "reason": "why this is a strong moment (key claim, emotional, shocking stat, etc.)"
    }}
  ],
  "entities": [
    {{
      "name": "Entity Name",
      "type": "person" or "company" or "agency" or "event" or "legislation",
      "context": "how they're mentioned"
    }}
  ],
  "best_for": ["exposition", "evidence", "character_intro", "hook", "revelation"]
}}

RULES:
- a_roll: someone speaking directly to camera, hearing testimony, interview, press conference
- b_roll: footage of events, documents, locations — voice-over narration covers it
- stock: generic footage with no specific editorial value (city streets, generic office)
- quotable_moments: ONLY include moments where the SPEAKER says something compelling. Score 8+ only for truly powerful quotes.
- entities: extract ALL named people, companies, agencies, events mentioned
- best_for: what narrative function this clip serves best (can be multiple)

ONLY output JSON, nothing else."""

    try:
        response = query_claude(prompt, timeout=60)
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"    Claude error for {clip_filename}: {e}")

    # Fallback
    return {
        "roll_type": classify_roll_type_heuristic(clip_filename, transcript),
        "roll_reasoning": "heuristic fallback",
        "quotable_moments": [],
        "entities": [],
        "best_for": ["exposition"],
    }


def tag_image(image_filename, vision_entry, image_path=None):
    """Tag an image using (in order of preference):
      1. <image>.content.json sidecar (written by scripts/label_stills.py) — vision-verified truth
      2. vision_entry from the vision manifest
      3. filename heuristics (last-resort, the source of the filename-lies bug)

    Returns None if the sidecar explicitly marks the image as unusable — the
    caller should drop it from the pool instead of showing the director a
    lying description.
    """
    desc = ""
    mood = "neutral"
    topics = []
    sidecar_entities = []
    sidecar_subject = None

    # 1. Trust the content.json sidecar if present
    if image_path is not None:
        sidecar = Path(str(image_path) + ".content.json")
        if sidecar.exists():
            try:
                content = json.loads(sidecar.read_text())
                if not content.get("usable_for_documentary", True):
                    return None  # Quarantine: keep it out of the director's pool
                sidecar_subject = content.get("subject")
                for ent in content.get("entities") or []:
                    sidecar_entities.append({"name": str(ent), "type": "content_verified"})
                if sidecar_subject:
                    desc = sidecar_subject
            except (json.JSONDecodeError, OSError):
                pass  # Fall through to vision_entry / filename

    # 2. Vision manifest as fallback
    if not desc and vision_entry:
        desc = vision_entry.get("description", "")
        mood = vision_entry.get("mood", "neutral")
        topics = vision_entry.get("topics", [])

    # 3. Filename heuristics — last resort (this is the source of the lie,
    # kept only so the pipeline doesn't crash on un-labeled legacy images)
    name_parts = image_filename.replace("_", " ").replace("-", " ").lower()
    entity_keywords = {
        "facebook": "company", "meta": "company", "zuckerberg": "person",
        "wells fargo": "company", "purdue": "company", "sackler": "person",
        "ford": "company", "pinto": "product", "ftc": "agency", "sec": "agency",
        "doj": "agency", "congress": "agency", "capitol": "location",
        "cambridge analytica": "company", "realpage": "company", "gdpr": "legislation",
        "opioid": "event", "whistleblower": "person",
    }

    entities = list(sidecar_entities)  # Start with vision-verified entities
    if not entities:  # Only fall back to filename guessing if no sidecar entities
        for kw, etype in entity_keywords.items():
            if kw in name_parts:
                entities.append({"name": kw.title(), "type": etype})

    # Score editorial value — vision-verified content ranks higher than filename guesses
    value = 3  # base
    if sidecar_subject:
        value += 2  # vision-verified description
    if entities:
        value += 2  # entity-specific is more valuable
    if desc and len(desc) > 50:
        value += 1
    if mood in ("tense", "dramatic", "ominous"):
        value += 1
    value = min(value, 10)

    # Best narrative function
    best_for = ["exposition"]
    if any(e["type"] == "person" for e in entities):
        best_for.append("character_intro")
    if "document" in name_parts or "court" in name_parts or "filing" in name_parts:
        best_for.append("evidence")

    return {
        "roll_type": "b_roll" if entities else "stock",
        "description": desc[:200] if desc else image_filename.replace("_", " "),
        "entities": entities,
        "topics": topics,
        "mood": mood,
        "editorial_value": value,
        "best_for": best_for,
    }


def build_entity_index(clips_tagged, images_tagged):
    """Cross-reference entities to their best clip/image sources."""
    entity_index = defaultdict(lambda: {"clips": [], "images": [], "best_a_roll": None, "best_b_roll": None})

    for filename, clip in clips_tagged.items():
        for entity in clip.get("entities", []):
            name = entity["name"]
            entity_index[name]["clips"].append({
                "filename": filename,
                "roll_type": clip["roll_type"],
                "best_quote": clip["quotable_moments"][0]["text"] if clip.get("quotable_moments") else None,
            })
            if clip["roll_type"] == "a_roll" and not entity_index[name]["best_a_roll"]:
                entity_index[name]["best_a_roll"] = filename
            elif clip["roll_type"] == "b_roll" and not entity_index[name]["best_b_roll"]:
                entity_index[name]["best_b_roll"] = filename

    for filename, img in images_tagged.items():
        for entity in img.get("entities", []):
            name = entity["name"]
            entity_index[name]["images"].append({
                "filename": filename,
                "editorial_value": img.get("editorial_value", 3),
            })
            # Sort images by value, highest first
            entity_index[name]["images"].sort(key=lambda x: -x.get("editorial_value", 0))

    return dict(entity_index)


def tag_selects(transcripts_path, vision_path, output_path):
    """Main entry point: tag all clips and images."""
    # Load transcripts
    with open(transcripts_path) as f:
        raw = json.load(f)
    clips_list = raw.get("clips", raw if isinstance(raw, list) else [])
    transcripts = {c["filename"]: c.get("transcript", "") for c in clips_list}

    # Load vision manifest
    vision_data = {"clips": [], "images": []}
    if Path(vision_path).exists():
        with open(vision_path) as f:
            vision_data = json.load(f)

    # Build vision lookup
    vision_clips = {c["filename"]: c for c in vision_data.get("clips", [])}
    vision_images = {img["filename"]: img for img in vision_data.get("images", [])}

    print(f"  {len(transcripts)} clips, {len(vision_images)} images")

    # Tag clips with Claude
    clips_tagged = {}
    for i, (filename, transcript) in enumerate(transcripts.items()):
        print(f"  [{i+1}/{len(transcripts)}] {filename[:50]}...")
        vision_entry = vision_clips.get(filename)
        result = tag_clip_with_claude(filename, transcript, vision_entry)
        result["full_transcript"] = transcript
        result["filename"] = filename
        clips_tagged[filename] = result

    # Tag images (no Claude — use vision manifest + filename heuristics)
    images_tagged = {}
    # Collect all image files from footage dirs
    image_dirs = [
        PROJECT_ROOT / "footage" / "breaking_law" / "stills",             # ffmpeg key frames from clips
        PROJECT_ROOT / "footage" / "breaking_law" / "images_v2" / "web",  # Wikipedia/Commons downloads
        PROJECT_ROOT / "footage" / "breaking_law" / "images_v2" / "wikimedia",  # Wikimedia search
    ]
    quarantined = 0
    for img_dir in image_dirs:
        if not img_dir.exists():
            continue
        for root, _, files in os.walk(img_dir):
            for f in files:
                if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    continue
                full_path = Path(root) / f
                vision_entry = vision_images.get(f)
                tagged = tag_image(f, vision_entry, image_path=full_path)
                if tagged is None:
                    # Quarantined by content.json (is_ad, watermarked, reaction, etc.)
                    quarantined += 1
                    continue
                images_tagged[f] = tagged

    msg = f"  Tagged {len(images_tagged)} images"
    if quarantined:
        msg += f" ({quarantined} quarantined by content.json sidecar)"
    print(msg)

    # Build entity index
    entity_index = build_entity_index(clips_tagged, images_tagged)
    print(f"  Entity index: {len(entity_index)} entities")

    # Compile output
    selects = {
        "clips": clips_tagged,
        "images": images_tagged,
        "entity_index": entity_index,
        "stats": {
            "total_clips": len(clips_tagged),
            "a_roll_clips": sum(1 for c in clips_tagged.values() if c["roll_type"] == "a_roll"),
            "b_roll_clips": sum(1 for c in clips_tagged.values() if c["roll_type"] == "b_roll"),
            "stock_clips": sum(1 for c in clips_tagged.values() if c["roll_type"] == "stock"),
            "total_images": len(images_tagged),
            "total_entities": len(entity_index),
            "total_quotable_moments": sum(
                len(c.get("quotable_moments", [])) for c in clips_tagged.values()
            ),
        },
    }

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(selects, f, indent=2)

    print(f"\n  Selects saved: {output_path}")
    s = selects["stats"]
    print(f"  {s['total_clips']} clips ({s['a_roll_clips']} A-roll, {s['b_roll_clips']} B-roll, {s['stock_clips']} stock)")
    print(f"  {s['total_images']} images, {s['total_entities']} entities, {s['total_quotable_moments']} quotable moments")

    return selects


def main():
    parser = argparse.ArgumentParser(description="Selects Tagger — pre-process source material")
    parser.add_argument("--transcripts", type=str, default=str(DEFAULT_TRANSCRIPTS))
    parser.add_argument("--vision", type=str, default=str(DEFAULT_VISION))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    print("Selects Tagger")
    tag_selects(args.transcripts, args.vision, args.output)


if __name__ == "__main__":
    main()
