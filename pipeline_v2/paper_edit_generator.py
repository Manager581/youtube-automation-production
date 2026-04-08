#!/usr/bin/env python3
"""
Paper Edit Generator — replaces the director's filename-matching approach
with a structured horizontal edit board.

Each row is a 5-7 second beat with:
  - Timecode (from Whisper alignment)
  - Full script text
  - Narrative function (exposition/tension/evidence/character_intro/hook/revelation/transition)
  - Visual pick + WHY (mandatory editorial reasoning)
  - Clip audio + the actual quote
  - Overlay, SFX, transition, tension, zoom speed

Uses selects.json (entity index + quotable moments) so Claude matches by
content, not filename.

Usage:
  python -m pipeline_v2.paper_edit_generator
  python -m pipeline_v2.paper_edit_generator --selects storyboards/breaking_law_selects.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude

DEFAULT_SCRIPT = PROJECT_ROOT / "scripts" / "enhanced_breaking_law_v45.txt"
DEFAULT_ALIGNMENT = PROJECT_ROOT / "audio" / "breaking_law" / "narration_alignment.json"
DEFAULT_SELECTS = PROJECT_ROOT / "storyboards" / "breaking_law_selects.json"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit.json"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit.md"

# LearnByLeo narrative-visual mapping (from playbook/editing.json)
NARRATIVE_FUNCTION_RULES = {
    "exposition": {"cut_duration": "8-12s", "zoom_rate": "1-3%/s", "description": "Establishing context, background info"},
    "tension_build": {"cut_duration": "2-4s", "zoom_rate": "3-5%/s", "description": "Building suspense, raising stakes"},
    "evidence": {"cut_duration": "5-7s", "zoom_rate": "1.5-5%/s", "description": "Showing documents, data, proof"},
    "character_intro": {"cut_duration": "5-7s", "zoom_rate": "2-5%/s", "description": "Introducing a person — cut when name spoken"},
    "hook": {"cut_duration": "12-20s", "zoom_rate": "3-5%/s", "description": "Opening hook — HOLD, don't cut"},
    "revelation": {"cut_duration": "2-3s", "zoom_rate": "15-25%/s", "description": "Shocking reveal — extreme zoom, cut at exact moment"},
    "transition": {"cut_duration": "2-4s", "zoom_rate": "0-1%/s", "description": "Chapter transition — fade to black"},
}


def load_alignment(path):
    """Load Whisper narration alignment."""
    with open(path) as f:
        return json.load(f)


def parse_script_into_segments(script_path):
    """Parse the enhanced script into segments with chapter markers."""
    with open(script_path) as f:
        text = f.read()

    segments = []
    current_chapter = "COLD OPEN"
    current_voice = "neutral"

    # Split on chapter markers and voice markers
    lines = text.split('\n')
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Chapter marker
        m = re.match(r'\[CHAPTER:\s*(.+?)\]', line, re.IGNORECASE)
        if m:
            # Flush current text
            if current_text:
                segments.append({
                    "text": ' '.join(current_text),
                    "chapter": current_chapter,
                    "voice": current_voice,
                })
                current_text = []
            current_chapter = m.group(1).strip()
            segments.append({"text": f"[CHAPTER: {current_chapter}]", "chapter": current_chapter, "voice": current_voice, "is_chapter_marker": True})
            continue

        # Voice marker
        m = re.match(r'\[VOICE:(\w+)\]', line, re.IGNORECASE)
        if m:
            if current_text:
                segments.append({"text": ' '.join(current_text), "chapter": current_chapter, "voice": current_voice})
                current_text = []
            current_voice = m.group(1).lower()
            continue

        # Pause/beat markers — flush text before them
        if re.match(r'\[PAUSE[:\d.]*\]|\[BEAT\]|\[BREATH\]', line, re.IGNORECASE):
            if current_text:
                segments.append({"text": ' '.join(current_text), "chapter": current_chapter, "voice": current_voice})
                current_text = []
            continue

        # Regular text
        current_text.append(line)

    # Flush remaining
    if current_text:
        segments.append({"text": ' '.join(current_text), "chapter": current_chapter, "voice": current_voice})

    return [s for s in segments if s.get("text", "").strip()]


def align_segments_to_timestamps(segments, alignment):
    """Match script segments to Whisper alignment timestamps."""
    sentences = alignment.get("sentences", [])
    if not sentences:
        return segments

    sent_idx = 0
    for seg in segments:
        if seg.get("is_chapter_marker"):
            # Chapter markers don't have narration
            if sent_idx > 0:
                seg["start_sec"] = sentences[min(sent_idx, len(sentences) - 1)]["start"]
                seg["end_sec"] = seg["start_sec"] + 3.0  # chapter card duration
            continue

        seg_words = seg["text"].split()
        seg_word_count = len(seg_words)

        # Find the sentence(s) that cover this segment's text
        start = None
        end = None
        words_matched = 0

        while sent_idx < len(sentences) and words_matched < seg_word_count:
            sent = sentences[sent_idx]
            if start is None:
                start = sent["start"]
            end = sent["end"]
            words_matched += len(sent["text"].split())
            sent_idx += 1

        seg["start_sec"] = start or 0
        seg["end_sec"] = end or (start or 0) + 5.0

    return segments


def segment_to_beats(segment):
    """Split a segment into 5-7 second beats based on sentence boundaries."""
    text = segment["text"]
    start = segment.get("start_sec", 0)
    end = segment.get("end_sec", start + 5)
    duration = end - start

    if duration <= 8:
        # Short enough for a single beat
        return [{
            "text": text,
            "start_sec": start,
            "end_sec": end,
            "duration": duration,
            "chapter": segment.get("chapter", "COLD OPEN"),
            "voice": segment.get("voice", "neutral"),
        }]

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= 1:
        return [{
            "text": text,
            "start_sec": start,
            "end_sec": end,
            "duration": duration,
            "chapter": segment.get("chapter", "COLD OPEN"),
            "voice": segment.get("voice", "neutral"),
        }]

    # Distribute time proportionally by word count
    total_words = len(text.split())
    beats = []
    cursor = start

    current_beat_text = []
    current_beat_words = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        wc = len(sent.split())

        if current_beat_words > 0 and current_beat_words + wc > 20:
            # Flush current beat
            beat_dur = (current_beat_words / total_words) * duration
            beats.append({
                "text": ' '.join(current_beat_text),
                "start_sec": round(cursor, 3),
                "end_sec": round(cursor + beat_dur, 3),
                "duration": round(beat_dur, 3),
                "chapter": segment.get("chapter", "COLD OPEN"),
                "voice": segment.get("voice", "neutral"),
            })
            cursor += beat_dur
            current_beat_text = [sent]
            current_beat_words = wc
        else:
            current_beat_text.append(sent)
            current_beat_words += wc

    # Flush last beat
    if current_beat_text:
        beats.append({
            "text": ' '.join(current_beat_text),
            "start_sec": round(cursor, 3),
            "end_sec": round(end, 3),
            "duration": round(end - cursor, 3),
            "chapter": segment.get("chapter", "COLD OPEN"),
            "voice": segment.get("voice", "neutral"),
        })

    return beats


def build_batch_prompt(beats, selects, batch_idx, total_batches, used_visuals):
    """Build the paper edit prompt for a batch of beats."""

    # Compact entity index for the prompt
    entity_summary = ""
    for entity, data in selects.get("entity_index", {}).items():
        clips = data.get("clips", [])
        best_a = data.get("best_a_roll")
        best_b = data.get("best_b_roll")
        quotes = [c.get("best_quote", "")[:80] for c in clips if c.get("best_quote")]
        entity_summary += f"\n  {entity}:"
        if best_a:
            entity_summary += f" A-roll={best_a}"
        if best_b:
            entity_summary += f" B-roll={best_b}"
        if quotes:
            entity_summary += f" Quotes: {'; '.join(quotes[:2])}"

    # Clip summaries with FULL transcripts
    clip_summary = ""
    for filename, clip in selects.get("clips", {}).items():
        roll = clip.get("roll_type", "?")
        transcript = clip.get("full_transcript", "")[:300]
        moments = clip.get("quotable_moments", [])
        best_for = clip.get("best_for", [])
        clip_summary += f"\n  {filename} [{roll}] best_for={best_for}"
        if transcript:
            clip_summary += f"\n    Says: {transcript}"
        for m in moments[:2]:
            clip_summary += f"\n    QUOTE (value {m['editorial_value']}/10): \"{m['text'][:100]}\""

    # Beat texts for this batch
    beats_text = ""
    for i, beat in enumerate(beats):
        beats_text += f"\n  Beat {i}: [{beat['start_sec']:.1f}-{beat['end_sec']:.1f}s] ({beat['chapter']})\n"
        beats_text += f"    \"{beat['text']}\"\n"

    # Used visuals warning
    overused = [f for f, count in used_visuals.items() if count >= 2]
    overused_str = f"\nALREADY USED 2+ TIMES (avoid): {', '.join(overused)}" if overused else ""

    prompt = f"""You are an editorial director for a ColdFusion/How Money Works style documentary.

BATCH {batch_idx + 1}/{total_batches}

ENTITY INDEX (match visuals by CONTENT, not filename):
{entity_summary}

AVAILABLE CLIPS (with full transcripts):
{clip_summary}
{overused_str}

BEATS TO EDIT:
{beats_text}

NARRATIVE FUNCTION TYPES:
- exposition: establishing context (8-12s cuts, slow zoom 1-3%/s)
- tension_build: raising stakes (2-4s cuts, faster zoom 3-5%/s)
- evidence: showing proof/data (5-7s cuts, medium zoom)
- character_intro: introducing a person (cut when name spoken)
- hook: opening hook (HOLD 12-20s, don't cut)
- revelation: shocking reveal (2-3s, extreme zoom 15-25%/s)
- transition: chapter boundary (fade to black)

For EACH beat, return a JSON object:
{{
  "beat_index": 0,
  "narrative_function": "exposition|tension_build|evidence|character_intro|hook|revelation|transition",
  "visual_file": "exact_filename.mp4 or .jpg",
  "visual_type": "a_roll|b_roll|stock",
  "why": "MANDATORY: explain WHY this visual supports the narration at this moment",
  "clip_audio": "mute|play|play_then_mute",
  "clip_audio_quote": "the exact words the person says if clip_audio is play/play_then_mute, else null",
  "clip_audio_duration": null,
  "text_overlay": "KEY STAT or null",
  "sfx": null,
  "sfx_motivation": null,
  "transition_in": "cut|dissolve|fade_from_black",
  "tension_level": 0.0-1.0,
  "zoom_target": "wide|face|document"
}}

RULES:
1. WHY column is MANDATORY. "Generic corporate footage" is NOT a valid reason.
2. When narration mentions a named entity, use the entity index to find specific footage.
3. A-roll (interviews/testimony) should be reserved for key moments, not every beat.
4. clip_audio="play" ONLY when the source material's words are MORE powerful than narration.
5. NEVER use the same visual file more than 2 times across the entire video.
6. Text overlays for key stats and names only, not every beat.
7. SFX only at genuine dramatic moments (max 2 per chapter).

Return a JSON array of {len(beats)} objects. ONLY JSON, no other text."""

    return prompt


def generate_paper_edit(script_path, alignment_path, selects_path, output_json, output_md):
    """Generate the full paper edit."""
    print("  Loading inputs...")
    alignment = load_alignment(alignment_path)
    segments = parse_script_into_segments(script_path)
    print(f"  Script: {len(segments)} segments")

    with open(selects_path) as f:
        selects = json.load(f)
    print(f"  Selects: {selects['stats']['total_clips']} clips, {selects['stats']['total_entities']} entities")

    # Align segments to timestamps
    segments = align_segments_to_timestamps(segments, alignment)

    # Split into beats
    all_beats = []
    for seg in segments:
        if seg.get("is_chapter_marker"):
            all_beats.append({
                "text": seg["text"],
                "start_sec": seg.get("start_sec", 0),
                "end_sec": seg.get("end_sec", 3),
                "duration": 3.0,
                "chapter": seg["chapter"],
                "is_chapter_marker": True,
                "narrative_function": "transition",
                "visual_file": f"chapter_{seg['chapter'].lower().replace(' ', '_')}.mov",
                "visual_type": "chapter_card",
                "why": "Chapter card marks new section",
                "clip_audio": "mute",
                "tension_level": 0.5,
            })
            continue
        beats = segment_to_beats(seg)
        all_beats.extend(beats)

    print(f"  Total beats: {len(all_beats)} ({len([b for b in all_beats if not b.get('is_chapter_marker')])} content + "
          f"{len([b for b in all_beats if b.get('is_chapter_marker')])} chapter markers)")

    # Process content beats through Claude in batches
    content_beats = [b for b in all_beats if not b.get("is_chapter_marker")]
    batch_size = 15
    used_visuals = {}
    edited_beats = []

    for batch_idx in range(0, len(content_beats), batch_size):
        batch = content_beats[batch_idx:batch_idx + batch_size]
        total_batches = (len(content_beats) + batch_size - 1) // batch_size
        current_batch = batch_idx // batch_size

        print(f"  Batch [{current_batch + 1}/{total_batches}] ({len(batch)} beats, "
              f"{batch[0]['start_sec']:.0f}-{batch[-1]['end_sec']:.0f}s)...")

        prompt = build_batch_prompt(batch, selects, current_batch, total_batches, used_visuals)
        response = query_claude(prompt, timeout=300)

        # Parse response
        try:
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                decisions = json.loads(match.group())
            else:
                print(f"    WARNING: Could not parse JSON from response")
                decisions = []
        except json.JSONDecodeError as e:
            print(f"    WARNING: JSON parse error: {e}")
            decisions = []

        # Merge decisions into beats
        for i, beat in enumerate(batch):
            if i < len(decisions):
                dec = decisions[i]
                beat["narrative_function"] = dec.get("narrative_function", "exposition")
                beat["visual_file"] = dec.get("visual_file", "")
                beat["visual_type"] = dec.get("visual_type", "b_roll")
                beat["why"] = dec.get("why", "")
                beat["clip_audio"] = dec.get("clip_audio", "mute")
                beat["clip_audio_quote"] = dec.get("clip_audio_quote")
                beat["clip_audio_duration"] = dec.get("clip_audio_duration")
                beat["text_overlay"] = dec.get("text_overlay")
                beat["sfx"] = dec.get("sfx")
                beat["sfx_motivation"] = dec.get("sfx_motivation")
                beat["transition_in"] = dec.get("transition_in", "cut")
                beat["tension_level"] = dec.get("tension_level", 0.5)
                beat["zoom_target"] = dec.get("zoom_target", "wide")

                # Track visual usage
                vf = beat.get("visual_file", "")
                if vf:
                    used_visuals[vf] = used_visuals.get(vf, 0) + 1
            else:
                # No decision — default
                beat["narrative_function"] = "exposition"
                beat["visual_file"] = ""
                beat["visual_type"] = "b_roll"
                beat["why"] = "NO DECISION — batch response too short"
                beat["clip_audio"] = "mute"
                beat["tension_level"] = 0.3

            edited_beats.append(beat)

    # Merge chapter markers back in
    final_beats = []
    chapter_beats = [b for b in all_beats if b.get("is_chapter_marker")]
    content_idx = 0
    chapter_idx = 0

    # Sort all by start_sec
    all_sorted = sorted(
        edited_beats + chapter_beats,
        key=lambda b: b.get("start_sec", 0)
    )

    # Assign beat IDs
    for i, beat in enumerate(all_sorted):
        beat["beat_id"] = f"beat_{i:04d}"

    # Compute zoom speed from tension + narrative function
    for beat in all_sorted:
        tension = beat.get("tension_level", 0.5)
        nf = beat.get("narrative_function", "exposition")
        if nf == "revelation":
            beat["zoom_speed_pct_per_sec"] = 15.0 + tension * 10.0
        elif nf == "tension_build":
            beat["zoom_speed_pct_per_sec"] = 3.0 + tension * 2.0
        elif nf == "hook":
            beat["zoom_speed_pct_per_sec"] = 3.0 + tension * 2.0
        elif nf == "evidence":
            beat["zoom_speed_pct_per_sec"] = 1.5 + tension * 3.5
        else:
            beat["zoom_speed_pct_per_sec"] = 1.0 + tension * 2.0

    # Save JSON
    paper_edit = {
        "beats": all_sorted,
        "stats": {
            "total_beats": len(all_sorted),
            "content_beats": len(edited_beats),
            "chapter_markers": len(chapter_beats),
            "unique_visuals": len(set(b.get("visual_file", "") for b in all_sorted if b.get("visual_file"))),
            "clip_audio_moments": len([b for b in all_sorted if b.get("clip_audio") in ("play", "play_then_mute")]),
            "beats_with_why": len([b for b in all_sorted if b.get("why") and len(b["why"]) > 10]),
        },
    }

    output_json = Path(output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(paper_edit, f, indent=2)

    # Generate markdown
    md = render_markdown(paper_edit)
    output_md = Path(output_md)
    with open(output_md, 'w') as f:
        f.write(md)

    print(f"\n  Paper edit saved:")
    print(f"    JSON: {output_json}")
    print(f"    MD:   {output_md}")
    s = paper_edit["stats"]
    print(f"    {s['total_beats']} beats, {s['unique_visuals']} unique visuals, "
          f"{s['clip_audio_moments']} clip audio moments, {s['beats_with_why']} with WHY")

    return paper_edit


def render_markdown(paper_edit):
    """Render paper edit as human-readable markdown."""
    lines = ["# Paper Edit — Why Breaking the Law Is Profitable\n"]

    current_chapter = None
    beats = paper_edit["beats"]
    s = paper_edit["stats"]

    lines.append(f"**{s['total_beats']} beats** | {s['unique_visuals']} unique visuals | "
                 f"{s['clip_audio_moments']} clip audio | {s['beats_with_why']}/{s['total_beats']} have WHY\n")

    for beat in beats:
        chapter = beat.get("chapter", "?")
        if chapter != current_chapter:
            current_chapter = chapter
            lines.append(f"\n## {chapter}\n")
            lines.append("| TC | Script | Function | Visual | Type | WHY | Audio | T |")
            lines.append("|-----|--------|----------|--------|------|-----|-------|---|")

        if beat.get("is_chapter_marker"):
            lines.append(f"| {beat['start_sec']:.1f}s | *CHAPTER CARD* | transition | {beat.get('visual_file','')} | card | chapter marker | — | — |")
            continue

        tc = f"{beat['start_sec']:.1f}s"
        script = beat.get("text", "")[:60]
        nf = beat.get("narrative_function", "?")[:8]
        visual = beat.get("visual_file", "?")[:30]
        vtype = beat.get("visual_type", "?")[:5]
        why = beat.get("why", "")[:40]
        audio = beat.get("clip_audio", "mute")
        if audio != "mute" and beat.get("clip_audio_quote"):
            audio += f": \"{beat['clip_audio_quote'][:30]}...\""
        tension = f"{beat.get('tension_level', 0):.1f}"

        lines.append(f"| {tc} | {script} | {nf} | {visual} | {vtype} | {why} | {audio} | {tension} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Paper Edit Generator")
    parser.add_argument("--script", type=str, default=str(DEFAULT_SCRIPT))
    parser.add_argument("--alignment", type=str, default=str(DEFAULT_ALIGNMENT))
    parser.add_argument("--selects", type=str, default=str(DEFAULT_SELECTS))
    parser.add_argument("--output-json", type=str, default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", type=str, default=str(DEFAULT_OUTPUT_MD))
    args = parser.parse_args()

    print("Paper Edit Generator")
    generate_paper_edit(args.script, args.alignment, args.selects, args.output_json, args.output_md)


if __name__ == "__main__":
    main()
