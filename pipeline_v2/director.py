#!/usr/bin/env python3
"""
director.py — Full-context editorial director using Claude + LearnByLeo playbook.

Reads the ENTIRE script + storyboard and makes every editorial decision with
full narrative awareness. This replaces statistical/random editorial decisions
with story-motivated ones.

Pipeline position: storyboard -> DIRECTOR -> voice -> footage -> assemble

For each segment, the Director provides:
  - arc_position: cold_open / tension_build / revelation / emotional_peak / aftermath / chapter_transition
  - sfx: content-matched sound effect (whoosh, highlight, impact, riser, hit, drone)
  - transition: hard_cut / fade_from_black / dissolve / fade_to_black
  - zoom_target: WHERE in image to focus (face, document, window, location, person)
  - text_overlay: text to display on screen (names, dates, quotes)
  - text_size: adaptive sizing (dates=72px, names=64px, entities=56px, locations=52px, quotes=44px)
  - tension_level: 0.0-1.0 continuous tension tracking
  - hold_duration_multiplier: 1.8x dramatic reveals, 0.7x punchy lines, 1.4x quotes
  - typewriter_click: flag for sync point text reveals

Uses:
  - playbook/editing.json (cut frequency, chapter transitions, sound design, attention guides)
  - playbook/retention_delivery.json (litmus test, energy variation, vocal delivery)

Usage:
    from pipeline_v2.director import direct
    directed = direct("storyboards/my_storyboard.json", "scripts/my_script.txt")
"""

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude


def load_playbooks() -> dict:
    """Load editing and retention/delivery playbooks."""
    editing_path = os.path.join(PROJECT_ROOT, "playbook/editing.json")
    retention_path = os.path.join(PROJECT_ROOT, "playbook/retention_delivery.json")

    with open(editing_path) as f:
        editing = json.load(f)
    with open(retention_path) as f:
        retention = json.load(f)

    return {"editing": editing, "retention": retention}


def flatten_storyboard(storyboard: dict) -> list[dict]:
    """Flatten storyboard scenes into a flat segment list."""
    segments = []
    if isinstance(storyboard, list):
        return storyboard
    if "scenes" in storyboard:
        for scene in storyboard["scenes"]:
            segments.extend(scene.get("segments", []))
    elif "segments" in storyboard:
        segments = storyboard["segments"]
    return segments


def direct(storyboard_path: str, script_path: str = None,
           output_path: str = None) -> dict:
    """
    Run the full-context editorial director pass.

    Reads the ENTIRE script + storyboard, then makes every editorial decision
    with full narrative awareness.

    Args:
        storyboard_path: Path to storyboard JSON (from storyboard_generator.py)
        script_path: Path to enhanced script (optional, text extracted from storyboard if absent)
        output_path: Where to save directed storyboard (optional)

    Returns:
        Directed storyboard dict with editorial decisions per segment
    """
    playbooks = load_playbooks()

    # Load storyboard
    with open(storyboard_path) as f:
        storyboard = json.load(f)

    segments = flatten_storyboard(storyboard)

    # Load script if provided
    full_script = ""
    if script_path and Path(script_path).exists():
        full_script = Path(script_path).read_text()
    else:
        # Extract text from storyboard segments
        full_script = '\n'.join(seg.get("text", "") for seg in segments)

    # Extract playbook rules for the prompt
    sound_design = json.dumps(
        playbooks["editing"]["tactics"].get("sound_design", {}), indent=2
    )
    chapter_transitions = json.dumps(
        playbooks["editing"]["tactics"].get("chapter_transitions", {}), indent=2
    )
    litmus_test = json.dumps(
        playbooks["retention"]["tactics"].get("three_part_litmus_test", {}), indent=2
    )
    energy_variation = json.dumps(
        playbooks["retention"]["tactics"].get("vocal_delivery", {}), indent=2
    )
    editing_rhythm = json.dumps(
        playbooks["editing"]["tactics"].get("editing_rhythm", {}), indent=2
    )

    # Process in batches but provide FULL script context
    batch_size = 20
    all_directed_segments = []

    # Truncate full script for context (keep first + last 2000 chars if too long)
    script_context = full_script
    if len(script_context) > 6000:
        script_context = full_script[:3000] + "\n...[middle omitted]...\n" + full_script[-3000:]

    for batch_start in range(0, len(segments), batch_size):
        batch = segments[batch_start:batch_start + batch_size]

        segments_block = []
        for i, seg in enumerate(batch):
            idx = batch_start + i
            segments_block.append(
                f"[{idx}] ({seg.get('duration_sec', 5)}s): {seg.get('text', '')[:250]}"
            )
        segments_text = '\n'.join(segments_block)

        prompt = f"""You are the editorial director for a YouTube documentary.
You have full context of the ENTIRE script and must make every editorial decision
with narrative awareness — NOT statistical randomness.

FULL SCRIPT CONTEXT (for arc awareness):
{script_context}

LEARNBYLEO SOUND DESIGN RULES:
{sound_design}

CHAPTER TRANSITION SEQUENCE (5 steps):
{chapter_transitions}

LITMUS TEST (every scene must pass):
{litmus_test}

VOCAL DELIVERY / ENERGY VARIATION:
{energy_variation}

EDITING RHYTHM:
{editing_rhythm}

TOTAL SEGMENTS: {len(segments)}
CURRENT BATCH: segments {batch_start} to {batch_start + len(batch) - 1}

For EACH segment, provide editorial decisions. Consider:
1. Where is this in the overall narrative arc?
2. What SFX would SERVE the story here? (not random)
3. Is this a chapter boundary? If so, use the 5-step transition sequence.
4. What zoom target matches what's being DISCUSSED?
5. Should text appear? Only for names, dates, quotes that reinforce narration.
6. Tension: is it rising, falling, or at a peak?
7. Hold duration: dramatic reveals get 1.8x, punchy lines get 0.7x, quotes get 1.4x

SFX RULES (from editing.json):
- whoosh: movement, transitions, visual elements entering/exiting
- highlight: emphasis on key words or visuals
- riser: build tension ONLY before genuinely important moments
- hit/impact: release tension, emphasize major moments (pair with risers)
- drone: mystery and suspense background layer
- ANTI-PATTERN: Using risers before unimportant moments trains viewers to ignore them
- Minimum 3-segment gap between SFX to prevent fatigue

Return valid JSON array:
[
  {{
    "segment_index": {batch_start},
    "arc_position": "cold_open|context|tension_build|revelation|emotional_peak|aftermath|chapter_transition",
    "sfx": {{"type": "whoosh|highlight|impact|riser|hit|drone|none", "trigger": "what triggers it"}},
    "transition": "hard_cut|fade_from_black|dissolve|fade_to_black",
    "zoom_target": "face|document|center|location|person|evidence",
    "text_overlay": {{"text": "Name or date or null", "style": "name|date|entity|location|quote", "size_px": 64}},
    "tension_level": 0.0-1.0,
    "hold_duration_multiplier": 1.0,
    "typewriter_click": false,
    "scene_group": 1,
    "notes": "brief editorial reasoning"
  }}
]

SEGMENTS TO DIRECT:
{segments_text}"""

        result = query_claude(prompt, timeout=180)

        try:
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if match:
                directed = json.loads(match.group())
                all_directed_segments.extend(directed)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"WARNING: Failed to parse director batch at segment {batch_start}: {e}",
                  file=sys.stderr)
            # Create fallback entries
            for i, seg in enumerate(batch):
                idx = batch_start + i
                all_directed_segments.append({
                    "segment_index": idx,
                    "arc_position": "context",
                    "sfx": {"type": "none", "trigger": ""},
                    "transition": "hard_cut",
                    "zoom_target": "center",
                    "text_overlay": {"text": None, "style": None, "size_px": 0},
                    "tension_level": 0.3,
                    "hold_duration_multiplier": 1.0,
                    "typewriter_click": False,
                    "scene_group": 1,
                    "notes": "fallback — director parse failed",
                })

    # Merge director decisions back into storyboard
    directed_storyboard = dict(storyboard)
    directed_storyboard["director_version"] = "2.0"
    directed_storyboard["directed_segments"] = all_directed_segments

    # Also merge into scene segments for convenience
    director_lookup = {d["segment_index"]: d for d in all_directed_segments}
    if "scenes" in directed_storyboard:
        for scene in directed_storyboard["scenes"]:
            for seg in scene.get("segments", []):
                idx = seg.get("segment_index", -1)
                if idx in director_lookup:
                    seg["director"] = director_lookup[idx]

    # Validate: check SFX spacing
    _validate_sfx_spacing(all_directed_segments)

    # Validate: check tension curve
    _validate_tension_curve(all_directed_segments)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(directed_storyboard, indent=2))
        print(f"Directed storyboard saved: {output_path}")
        print(f"  Total segments directed: {len(all_directed_segments)}")

        # Stats
        arc_counts = {}
        sfx_counts = {}
        for d in all_directed_segments:
            arc = d.get("arc_position", "unknown")
            arc_counts[arc] = arc_counts.get(arc, 0) + 1
            sfx_type = d.get("sfx", {}).get("type", "none")
            if sfx_type != "none":
                sfx_counts[sfx_type] = sfx_counts.get(sfx_type, 0) + 1

        print(f"  Arc positions: {arc_counts}")
        print(f"  SFX used: {sfx_counts}")

    return directed_storyboard


def _validate_sfx_spacing(directed_segments: list[dict]):
    """Warn if SFX are too close together (fatigue risk)."""
    last_sfx_idx = -10
    warnings = 0
    for seg in directed_segments:
        sfx_type = seg.get("sfx", {}).get("type", "none")
        if sfx_type != "none":
            gap = seg["segment_index"] - last_sfx_idx
            if gap < 3:
                warnings += 1
            last_sfx_idx = seg["segment_index"]
    if warnings:
        print(f"  WARNING: {warnings} SFX placed within 3 segments of each other (fatigue risk)",
              file=sys.stderr)


def _validate_tension_curve(directed_segments: list[dict]):
    """Check that tension rises and falls (not monotone)."""
    tensions = [seg.get("tension_level", 0.5) for seg in directed_segments]
    if not tensions:
        return

    # Check for variation
    min_t = min(tensions)
    max_t = max(tensions)
    range_t = max_t - min_t

    if range_t < 0.3:
        print(f"  WARNING: Tension range too narrow ({min_t:.2f}-{max_t:.2f}). "
              f"Need more variation for energy shifts.", file=sys.stderr)

    # Check for peaks
    peaks = sum(1 for t in tensions if t >= 0.8)
    if peaks == 0:
        print(f"  WARNING: No tension peaks (>= 0.8) found. Add emotional peaks.",
              file=sys.stderr)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Editorial director pass on storyboard")
    parser.add_argument("storyboard", help="Path to storyboard JSON")
    parser.add_argument("--script", "-s", help="Path to enhanced script")
    parser.add_argument("--output", "-o", help="Output path for directed storyboard")
    args = parser.parse_args()

    if not Path(args.storyboard).exists():
        print(f"ERROR: Storyboard not found: {args.storyboard}", file=sys.stderr)
        sys.exit(1)

    output = args.output or args.storyboard.replace('.json', '_directed.json')
    direct(args.storyboard, script_path=args.script, output_path=output)


if __name__ == "__main__":
    main()
