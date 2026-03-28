#!/usr/bin/env python3
"""
storyboard_generator.py — Generate per-segment visual briefs from enhanced scripts.

Uses Claude + LearnByLeo editing.json playbook for visual variety rules:
  - New visual every 5-7 seconds
  - 6 attention guide techniques
  - Narrative-to-visual mapping
  - Scene grouping with composition layers

Output schema (v2.0):
  {
    "schema_version": "2.0",
    "scenes": [
      {
        "scene_id": 1,
        "title": "...",
        "segments": [
          {
            "segment_index": 0,
            "text": "narration text",
            "duration_sec": 5.5,
            "show": "what to show on screen",
            "search_query": "image search query",
            "composition": {"bg": {...}, "fg": {...}},
            "content_type": "document_photo|documentary_photo|...",
            "shot_type": "zoom_in|slow_pan|static|...",
            "focal_point": "face|document|location|...",
            "attention_guide": "animate_important_area|darken_blur|...",
            "sync_points": [{"word": "...", "type": "name|date|quote"}]
          }
        ]
      }
    ]
  }

Usage:
    from pipeline_v2.storyboard_generator import generate_storyboard
    storyboard = generate_storyboard("path/to/enhanced_script.txt")
"""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude


def load_editing_playbook() -> dict:
    """Load the LearnByLeo editing playbook."""
    path = os.path.join(PROJECT_ROOT, "playbook/editing.json")
    with open(path) as f:
        return json.load(f)


def split_into_segments(script_text: str, target_duration_sec: float = 6.0) -> list[dict]:
    """
    Split enhanced script text into timed segments.

    Each segment is approximately target_duration_sec of spoken content
    at 140 WPM. Markers ([BEAT], [PAUSE:X], [VOICE:X]) are preserved
    but excluded from word count.

    Returns list of {text, duration_sec, voice_register, markers}.
    """
    # Strip markers for word counting, keep for output
    marker_pattern = r'\[(BEAT|PAUSE:\d+\.?\d*|VOICE:\w+)\]'

    lines = script_text.strip().split('\n')
    segments = []
    current_text = []
    current_words = 0
    current_voice = "neutral"
    words_per_sec = 140 / 60  # ~2.33 words/sec

    target_words = int(target_duration_sec * words_per_sec)

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Track voice register changes
        voice_match = re.search(r'\[VOICE:(\w+)\]', line)
        if voice_match:
            current_voice = voice_match.group(1)

        # Count actual spoken words (exclude markers)
        clean_line = re.sub(marker_pattern, '', line).strip()
        word_count = len(clean_line.split()) if clean_line else 0

        current_text.append(line)
        current_words += word_count

        if current_words >= target_words:
            text = ' '.join(current_text)
            duration = current_words / words_per_sec

            # Add time for pauses
            for pause_match in re.finditer(r'\[PAUSE:(\d+\.?\d*)\]', text):
                duration += float(pause_match.group(1))
            duration += text.count('[BEAT]') * 0.5

            segments.append({
                "text": text,
                "duration_sec": round(duration, 1),
                "voice_register": current_voice,
            })
            current_text = []
            current_words = 0

    # Flush remaining
    if current_text:
        text = ' '.join(current_text)
        duration = max(2.0, current_words / words_per_sec)
        segments.append({
            "text": text,
            "duration_sec": round(duration, 1),
            "voice_register": current_voice,
        })

    return segments


def generate_storyboard(script_path: str, output_path: str = None) -> dict:
    """
    Generate a full storyboard from an enhanced script.

    Args:
        script_path: Path to enhanced script (with markers)
        output_path: Where to save storyboard JSON (optional)

    Returns:
        Storyboard dict with schema_version 2.0
    """
    script_text = Path(script_path).read_text()
    segments = split_into_segments(script_text)
    playbook = load_editing_playbook()

    # Extract key rules for the prompt
    visual_variety = json.dumps(playbook["tactics"]["visual_variety"], indent=2)
    attention_guides = json.dumps(playbook["tactics"]["six_attention_guides"], indent=2)
    narrative_mapping = json.dumps(
        playbook["tactics"].get("narrative_visual_mapping", {}), indent=2
    )
    chapter_transitions = json.dumps(
        playbook["tactics"].get("chapter_transitions", {}), indent=2
    )

    # Process in batches of ~15 segments to stay within context limits
    batch_size = 15
    all_scenes = []
    scene_id = 1

    for batch_start in range(0, len(segments), batch_size):
        batch = segments[batch_start:batch_start + batch_size]
        batch_texts = []
        for i, seg in enumerate(batch):
            idx = batch_start + i
            batch_texts.append(
                f"[{idx}] ({seg['duration_sec']}s, {seg['voice_register']}): "
                f"{seg['text'][:300]}"
            )

        segments_block = '\n'.join(batch_texts)

        prompt = f"""You are a storyboard director for a YouTube documentary channel.
Generate visual briefs for each narration segment following the LearnByLeo editing playbook.

VISUAL VARIETY RULES:
{visual_variety}

ATTENTION GUIDE TECHNIQUES:
{attention_guides}

NARRATIVE-TO-VISUAL MAPPING:
{narrative_mapping}

CHAPTER TRANSITION SEQUENCE:
{chapter_transitions}

KEY REQUIREMENTS:
1. New visual every 5-7 seconds (editing.json benchmark)
2. Every segment needs a specific, searchable image query
3. Group segments into scenes (3-8 segments per scene based on narrative continuity)
4. Composition has bg (background) and optional fg (foreground subject) layers
5. Vary shot_type: zoom_in, slow_pan, static, parallax, zoom_out
6. Map content_type to narrative function (document_photo for evidence, documentary_photo for people)
7. Identify sync_points: names, dates, quotes that should appear as text overlays
8. Choose attention_guide technique based on tension level

Return valid JSON:
{{
  "scenes": [
    {{
      "scene_id": {scene_id},
      "title": "Scene title",
      "segments": [
        {{
          "segment_index": 0,
          "text": "original narration text",
          "duration_sec": 5.5,
          "show": "description of what to show on screen",
          "search_query": "specific image search query for Wikimedia/archives",
          "composition": {{
            "bg": {{"search_query": "background image query", "type": "location|document|abstract"}},
            "fg": {{"search_query": "foreground subject query", "type": "person|object|null"}}
          }},
          "content_type": "document_photo|documentary_photo|archival_footage|news_screenshot",
          "shot_type": "zoom_in|slow_pan|static|parallax|zoom_out",
          "focal_point": "face|document|center|location",
          "attention_guide": "animate_important_area|darken_blur_surrounds|color_shift|graphic_indicators|glow_effect|scale_position",
          "sync_points": [{{"word": "John Smith", "type": "name"}}]
        }}
      ]
    }}
  ]
}}

SEGMENTS TO PROCESS:
{segments_block}"""

        result = query_claude(prompt, timeout=180)

        try:
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                batch_scenes = parsed.get("scenes", [])
                for scene in batch_scenes:
                    scene["scene_id"] = scene_id
                    scene_id += 1
                all_scenes.extend(batch_scenes)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"WARNING: Failed to parse batch starting at segment {batch_start}: {e}",
                  file=sys.stderr)
            # Create fallback segments
            for i, seg in enumerate(batch):
                idx = batch_start + i
                all_scenes.append({
                    "scene_id": scene_id,
                    "title": f"Scene {scene_id}",
                    "segments": [{
                        "segment_index": idx,
                        "text": seg["text"],
                        "duration_sec": seg["duration_sec"],
                        "show": seg["text"][:80],
                        "search_query": seg["text"][:50],
                        "composition": {"bg": {"search_query": seg["text"][:50], "type": "document"}},
                        "content_type": "document_photo",
                        "shot_type": "zoom_in",
                        "focal_point": "center",
                        "attention_guide": "scale_position",
                        "sync_points": [],
                    }],
                })
                scene_id += 1

    storyboard = {
        "schema_version": "2.0",
        "total_segments": len(segments),
        "total_scenes": len(all_scenes),
        "scenes": all_scenes,
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(storyboard, indent=2))
        print(f"Storyboard saved: {output_path}")
        print(f"  Scenes: {len(all_scenes)}")
        print(f"  Total segments: {len(segments)}")

    return storyboard


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate visual storyboard from script")
    parser.add_argument("script", help="Path to enhanced script")
    parser.add_argument("--output", "-o", help="Output JSON path")
    args = parser.parse_args()

    if not Path(args.script).exists():
        print(f"ERROR: Script not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    output = args.output or str(
        PROJECT_ROOT / "storyboards" /
        (Path(args.script).stem + "_storyboard.json")
    )

    generate_storyboard(args.script, output)


if __name__ == "__main__":
    main()
