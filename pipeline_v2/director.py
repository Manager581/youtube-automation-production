#!/usr/bin/env python3
"""
director.py — Full-context editorial director. Sees EVERYTHING, picks EVERYTHING.

This is the brain of the pipeline. It reads:
- The full script (what's being narrated)
- All available footage clips (with transcripts + visual descriptions)
- All available images (with Claude vision descriptions)
- Available SFX files
- Music track info
- LearnByLeo playbook rules

It outputs a per-segment editorial decision that specifies:
- WHICH EXACT FILE to show (not a search query — an actual filename)
- Whether to use clip audio (and when to mute it)
- Where to pause the VO for dramatic effect
- Which SFX to trigger and when
- Text overlays (what text, when, typewriter or static)
- Transitions between segments
- Zoom/pan direction and target
- Tension level and arc position

Usage:
    python -m pipeline_v2.director \\
        --script scripts/enhanced_secret_scores.txt \\
        --storyboard storyboards/secret_scores_storyboard.json \\
        --footage footage/clips/ \\
        --images ~/Desktop/SecretScores_Media/segment_images/ \\
        --sfx ~/Desktop/SecretScores_Media/sfx/ \\
        --output storyboards/secret_scores_directed_v3.json
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude, query_claude_json


# ── Asset Discovery ───────────────────────────────────────────────────────

def discover_footage(footage_dir):
    """Scan footage directory. Extract transcripts and key moments from each clip."""
    clips = []
    
    if not os.path.exists(footage_dir):
        return clips
    
    for ext in ('*.mp4', '*.mkv', '*.mov'):
        for filepath in sorted(glob.glob(os.path.join(footage_dir, '**', ext), recursive=True)):
            clip = {
                "path": filepath,
                "filename": os.path.basename(filepath),
                "size_mb": os.path.getsize(filepath) / (1024 * 1024),
            }
            
            # Get duration
            try:
                result = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                     '-of', 'csv=p=0', filepath],
                    capture_output=True, text=True, timeout=10
                )
                clip["duration"] = float(result.stdout.strip())
            except:
                clip["duration"] = 0
            
            # Get transcript if subtitle file exists
            srt_path = filepath.rsplit('.', 1)[0] + '.srt'
            vtt_path = filepath.rsplit('.', 1)[0] + '.vtt'
            txt_path = filepath.rsplit('.', 1)[0] + '.txt'
            
            transcript = ""
            for sub_path in [srt_path, vtt_path, txt_path]:
                if os.path.exists(sub_path):
                    with open(sub_path) as f:
                        transcript = f.read()[:2000]
                    break
            
            clip["transcript"] = transcript
            clip["transcript_preview"] = transcript[:200] if transcript else ""
            
            # Extract title from filename
            name = os.path.splitext(os.path.basename(filepath))[0]
            clip["title"] = name.replace('_', ' ').replace('-', ' ')
            
            clips.append(clip)
    
    return clips


def discover_images(image_dirs):
    """Scan image directories. Return list of available images."""
    images = []
    
    for img_dir in image_dirs:
        if not os.path.exists(img_dir):
            continue
        
        for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
            for filepath in sorted(glob.glob(os.path.join(img_dir, '**', ext), recursive=True)):
                size = os.path.getsize(filepath)
                if size < 5000:
                    continue
                
                images.append({
                    "path": filepath,
                    "filename": os.path.basename(filepath),
                    "size_kb": size / 1024,
                    "title": os.path.splitext(os.path.basename(filepath))[0].replace('_', ' '),
                })
    
    return images


def discover_sfx(sfx_dir):
    """Scan SFX directory. Return available sound effects."""
    sfx = []
    
    if not os.path.exists(sfx_dir):
        return sfx
    
    for filepath in sorted(glob.glob(os.path.join(sfx_dir, '*.wav'))):
        name = os.path.splitext(os.path.basename(filepath))[0]
        
        # Skip music files
        if 'music' in name.lower() or 'narration' in name.lower():
            continue
        
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', filepath],
                capture_output=True, text=True, timeout=5
            )
            duration = float(result.stdout.strip())
        except:
            duration = 0
        
        sfx.append({
            "path": filepath,
            "filename": os.path.basename(filepath),
            "name": name,
            "duration": duration,
            "type": categorize_sfx(name),
        })
    
    return sfx


def categorize_sfx(name):
    """Categorize SFX by name."""
    name_lower = name.lower()
    if 'tension' in name_lower: return 'tension'
    if 'shimmer' in name_lower: return 'shimmer'
    if 'hit' in name_lower or 'impact' in name_lower: return 'impact'
    if 'whoosh' in name_lower: return 'whoosh'
    if 'riser' in name_lower: return 'riser'
    if 'rumble' in name_lower or 'drone' in name_lower: return 'rumble'
    if 'typewriter' in name_lower or 'click' in name_lower or 'key' in name_lower: return 'typewriter'
    return 'other'


# ── Script Parsing ────────────────────────────────────────────────────────

def parse_script(script_path):
    """Parse enhanced script into segments with timing markers."""
    with open(script_path) as f:
        content = f.read()
    
    # Split by [VOICE:xxx] markers or paragraphs
    segments = []
    current_voice = "neutral"
    
    # Split on double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', content)
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Extract voice register
        voice_match = re.match(r'\[VOICE:(\w+)\]\s*', para)
        if voice_match:
            current_voice = voice_match.group(1)
            para = para[voice_match.end():]
        
        # Extract beat/pause markers
        beats = []
        for m in re.finditer(r'\[BEAT\]', para):
            word_pos = len(para[:m.start()].split())
            beats.append({"type": "beat", "word_index": word_pos, "duration": 0.5})
        
        for m in re.finditer(r'\[PAUSE:([\d.]+)\]', para):
            word_pos = len(para[:m.start()].split())
            beats.append({"type": "pause", "word_index": word_pos, "duration": float(m.group(1))})
        
        # Clean text
        clean = re.sub(r'\[VOICE:\w+\]\s*', '', para)
        clean = re.sub(r'\[BEAT\]', '', clean)
        clean = re.sub(r'\[PAUSE:[\d.]+\]', '', clean)
        clean = re.sub(r'\[BREATH\]', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        if clean:
            segments.append({
                "text": clean,
                "voice_register": current_voice,
                "word_count": len(clean.split()),
                "beats": beats,
            })
    
    return segments


# ── LearnByLeo Playbook ───────────────────────────────────────────────────

def load_playbook():
    """Load LearnByLeo playbook rules."""
    modules = {}
    pb_dir = PROJECT_ROOT / "playbook"
    for f in pb_dir.glob("*.json"):
        if f.name not in ('index.json', 'sources.json'):
            with open(f) as fh:
                modules[f.stem] = json.load(fh)
    return modules


def get_editing_rules(playbook):
    """Extract key editing rules from LearnByLeo playbook."""
    editing = playbook.get('editing', {})
    retention = playbook.get('retention_delivery', {})
    
    return {
        "cut_frequency": "New visual every 5-7 seconds",
        "energy_variation": "Alternate hype-edited and mellow sections",
        "graphics_animate": "All graphics must animate in/out, never pop",
        "sfx_on_reveals": "SFX only before REAL reveals, not routine moments",
        "pause_before_reveals": "Pause BEFORE big reveals for anticipation",
        "chapter_transition": "5-step: punch → silence → card → new energy → hook",
        "visual_coverage": "Every narration segment must have accompanying visual",
        "no_monotone": "Vary energy — contrast keeps viewers focused",
        "music_duck": "Duck music under narration, raise during transitions",
        "clip_audio_rule": "Use clip audio only when it adds value (interviews, key quotes). Mute during VO.",
    }


# ── Claude-Powered Decision Making ───────────────────────────────────────

def build_director_prompt(segments, clips, images, sfx, playbook_rules):
    """Build the master prompt for Claude to make all editorial decisions."""
    
    # Summarize available assets — include vision descriptions so director
    # can make informed visual choices (not just filename matching)
    clip_summary = "\n".join(
        f"  - {c['filename'][:50]} ({c['duration']:.0f}s)"
        f" [{c.get('vision_description', '')[:80]}]"
        f" Says: {c.get('transcript_preview', '')[:60]}"
        for c in clips[:25]
    )

    image_summary = "\n".join(
        f"  - {img['filename'][:50]}"
        f" [{img.get('vision_description', '')[:60]}]"
        for img in images[:50]
    )
    
    sfx_summary = "\n".join(
        f"  - {s['filename']}: {s['type']} ({s['duration']:.1f}s)"
        for s in sfx
    )
    
    rules_text = "\n".join(f"  - {k}: {v}" for k, v in playbook_rules.items())
    
    # Build segment list
    seg_text = ""
    for i, seg in enumerate(segments):
        beats_str = ""
        if seg["beats"]:
            beats_str = f" [markers: {', '.join(b['type'] for b in seg['beats'])}]"
        seg_text += f"  Seg {i} [{seg['voice_register']}]{beats_str}: {seg['text'][:120]}...\n"
    
    prompt = f"""You are an editorial director for a YouTube documentary. You must make EVERY creative decision for each segment.

SCRIPT ({len(segments)} segments):
{seg_text}

AVAILABLE VIDEO CLIPS ({len(clips)} clips):
{clip_summary}

AVAILABLE IMAGES ({len(images)} images):
{image_summary}

AVAILABLE SFX ({len(sfx)} files):
{sfx_summary}

LEARNBYLEO EDITING RULES:
{rules_text}

For EACH segment (0 to {len(segments)-1}), output a JSON object with these fields:
- "visual_file": exact filename to show (from clips or images above). PICK THE BEST MATCH for what's being said.
- "visual_type": "video_clip" or "still_image"
- "clip_start_sec": if video_clip, what second to start from (pick the most relevant moment)
- "clip_audio": "mute" (during narration) or "play" (for interview quotes/dramatic moments) or "play_then_mute" (play clip audio for X seconds then mute)
- "clip_audio_duration": if "play_then_mute", how many seconds of clip audio to play
- "vo_pause_before": seconds to pause VO BEFORE this segment starts (0 for none, 0.5-3.0 for dramatic pause)
- "vo_pause_after": seconds to pause VO AFTER this segment ends
- "sfx_file": exact SFX filename to play at segment start, or null
- "sfx_motivation": why this SFX (e.g., "tension before reveal", "impact on rejection")
- "text_overlay": text to show on screen, or null
- "text_style": "typewriter" or "static" or "lower_third"
- "transition_in": "cut" or "dissolve" or "fade_from_black"
- "transition_out": "cut" or "dissolve" or "fade_to_black"
- "arc_position": "cold_open" / "context_setup" / "tension_build" / "revelation" / "emotional_peak" / "aftermath" / "chapter_transition"
- "tension_level": 0.0 to 1.0
- "zoom_target": "face" / "document" / "subject" / "wide" / null
- "chapter_card": if this starts a new chapter, the chapter title (e.g., "THE TENANTS"), otherwise null
- "music_state": "playing" (music audible) / "ducking" (music low under VO) / "silent" (no music) / "rising" (music swelling for impact) / "transition" (music bridges between sections)
- "notes": brief editorial note explaining your choices

CRITICAL RULES:
1. NEVER use the same clip file more than 3 times across all segments
2. Match visuals to narration content (if talking about Mary Louis, show related footage)
3. Use clip audio ONLY for powerful interview quotes — mute during regular narration
4. Pause VO BEFORE reveals (LearnByLeo: anticipation), not after
5. SFX only at genuine dramatic moments — not every segment
6. Chapter cards at major topic shifts (5-step transition)
7. Vary the energy: tension_build → revelation → aftermath cycling

Output a JSON array of {len(segments)} objects. ONLY JSON, no other text."""

    return prompt


def _parse_json_response(response):
    """Parse JSON array from Claude response, handling markdown wrapping."""
    if not response:
        return None
    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except json.JSONDecodeError:
        try:
            clean = re.sub(r'```json\s*', '', response)
            clean = re.sub(r'```\s*', '', clean)
            return json.loads(clean)
        except:
            return None


def direct_segments(segments, clips, images, sfx, playbook):
    """Use Claude to make all editorial decisions, batched to avoid timeouts."""

    playbook_rules = get_editing_rules(playbook)

    # Batch segments into groups of ~30 to avoid Claude CLI timeouts
    BATCH_SIZE = 30
    all_decisions = []

    for batch_start in range(0, len(segments), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(segments))
        batch = segments[batch_start:batch_end]

        print(f"  Batch {batch_start//BATCH_SIZE + 1}: segments {batch_start}-{batch_end-1} ({len(batch)} segs)...")

        prompt = build_director_prompt(batch, clips, images, sfx, playbook_rules)
        # Add batch context
        prompt = prompt.replace(
            f"For EACH segment (0 to {len(batch)-1})",
            f"For EACH segment (segments {batch_start} to {batch_end-1} of {len(segments)} total)"
        )

        response = query_claude(prompt, timeout=300)

        if not response:
            print(f"  ERROR: Batch {batch_start//BATCH_SIZE + 1} returned empty. Retrying...")
            response = query_claude(prompt, timeout=300)

        if not response:
            print(f"  ERROR: Batch {batch_start//BATCH_SIZE + 1} failed twice. Using defaults.")
            for i, seg in enumerate(batch):
                all_decisions.append({
                    "visual_file": None,
                    "visual_type": "still_image",
                    "sfx_file": None,
                    "text_overlay": None,
                    "transition_in": "cut",
                    "transition_out": "cut",
                    "arc_position": "context_setup",
                    "tension_level": 0.3,
                    "zoom_target": "wide",
                    "chapter_card": None,
                    "notes": "DEFAULT — Claude failed to process this batch"
                })
            continue

        decisions = _parse_json_response(response)
        if decisions:
            print(f"  ✅ Got {len(decisions)} decisions")
            all_decisions.extend(decisions)
        else:
            print(f"  ERROR: Could not parse response. Preview: {response[:200]}")
            for seg in batch:
                all_decisions.append({
                    "visual_file": None, "visual_type": "still_image",
                    "arc_position": "context_setup", "tension_level": 0.3,
                    "notes": "PARSE FAILED"
                })

    print(f"  Total decisions: {len(all_decisions)}")
    return all_decisions


# ── Validation ────────────────────────────────────────────────────────────

def validate_decisions(decisions, clips, images, sfx):
    """Validate director decisions and fix common issues."""
    
    clip_names = set(c["filename"] for c in clips)
    image_names = set(img["filename"] for img in images)
    sfx_names = set(s["filename"] for s in sfx)
    all_files = clip_names | image_names
    
    usage_count = {}
    fixed = 0
    
    for i, dec in enumerate(decisions):
        # Validate visual_file exists
        vf = dec.get("visual_file", "")
        if vf and vf not in all_files:
            # Find closest match
            best_match = None
            for name in all_files:
                if any(word in name.lower() for word in vf.lower().split()[:3]):
                    best_match = name
                    break
            if best_match:
                dec["visual_file"] = best_match
                fixed += 1
        
        # Track usage
        vf = dec.get("visual_file", "")
        usage_count[vf] = usage_count.get(vf, 0) + 1
        
        # Cap usage at 3
        if usage_count[vf] > 3:
            # Pick least-used alternative
            least_used = min(all_files, key=lambda f: usage_count.get(f, 0))
            dec["visual_file"] = least_used
            usage_count[least_used] = usage_count.get(least_used, 0) + 1
            fixed += 1
        
        # Validate SFX file
        sf = dec.get("sfx_file")
        if sf and sf not in sfx_names:
            # Find closest SFX type match
            sfx_type = dec.get("sfx_motivation", "")
            for s in sfx:
                if s["type"] in sfx_type.lower():
                    dec["sfx_file"] = s["filename"]
                    break
            else:
                dec["sfx_file"] = None
            fixed += 1
        
        # Ensure required fields exist
        dec.setdefault("arc_position", "context_setup")
        dec.setdefault("tension_level", 0.3)
        dec.setdefault("clip_audio", "mute")
        dec.setdefault("vo_pause_before", 0)
        dec.setdefault("vo_pause_after", 0)
        dec.setdefault("transition_in", "cut")
        dec.setdefault("transition_out", "cut")
    
    if fixed:
        print(f"  Fixed {fixed} invalid references in director output")
    
    return decisions


# ── Output ────────────────────────────────────────────────────────────────

def build_output(segments, decisions, clips, images, sfx, alignment=None):
    """Build the final director output JSON.

    Args:
        alignment: Optional narration alignment JSON (from narration_aligner.py).
                   If provided, uses exact Whisper timestamps instead of estimates.
    """
    total_words = sum(s["word_count"] for s in segments)

    # Use Whisper alignment if available, else estimate at ~150 WPM
    if alignment:
        from pipeline_v2.narration_aligner import match_script_to_alignment
        segments = match_script_to_alignment(segments, alignment)
        narr_duration = alignment.get("duration_sec", total_words / 2.5)
        print(f"  Using Whisper alignment: {narr_duration:.1f}s")
    else:
        narr_duration = total_words / 2.5  # ~150 WPM estimate
        print(f"  WARNING: No alignment — estimating timing at ~150 WPM ({narr_duration:.0f}s)")

    output_segments = []
    cumulative_words = 0

    for i, (seg, dec) in enumerate(zip(segments, decisions)):
        # Prefer Whisper timestamps if available on the segment
        if seg.get("_timeline_start_sec") is not None:
            start_sec = seg["_timeline_start_sec"]
            end_sec = seg.get("_timeline_end_sec", start_sec + seg["word_count"] / 2.5)
        else:
            start_sec = (cumulative_words / total_words) * narr_duration if total_words > 0 else 0
            cumulative_words += seg["word_count"]
            end_sec = (cumulative_words / total_words) * narr_duration if total_words > 0 else 0
        
        output_seg = {
            "text": seg["text"],
            "voice_register": seg["voice_register"],
            "word_count": seg["word_count"],
            
            # Director decisions
            "visual_file": dec.get("visual_file"),
            "visual_type": dec.get("visual_type", "video_clip"),
            "clip_start_sec": dec.get("clip_start_sec", 0),
            "clip_audio": dec.get("clip_audio", "mute"),
            "clip_audio_duration": dec.get("clip_audio_duration", 0),
            
            "vo_pause_before": dec.get("vo_pause_before", 0),
            "vo_pause_after": dec.get("vo_pause_after", 0),
            
            "sfx": {
                "file": dec.get("sfx_file"),
                "motivation": dec.get("sfx_motivation", ""),
                "type": categorize_sfx(dec.get("sfx_file", "") or ""),
            } if dec.get("sfx_file") else None,
            
            "text_overlay": dec.get("text_overlay"),
            "text_style": dec.get("text_style", "static"),
            
            "transition_in": dec.get("transition_in", "cut"),
            "transition_out": dec.get("transition_out", "cut"),
            
            "arc_position": dec.get("arc_position", "context_setup"),
            "tension_level": dec.get("tension_level", 0.3),
            "zoom_target": dec.get("zoom_target"),
            "chapter_card": dec.get("chapter_card"),
            
            "music_state": dec.get("music_state", "ducking"),
            "notes": dec.get("notes", ""),

            # Timing
            "_timeline_start_sec": start_sec,
            "_timeline_end_sec": end_sec,
        }
        
        output_segments.append(output_seg)
    
    # Group into scenes (consecutive segments with same arc)
    scenes = []
    current_scene = {"arc": None, "segments": []}
    
    for seg in output_segments:
        if seg["arc_position"] != current_scene["arc"]:
            if current_scene["segments"]:
                scenes.append(current_scene)
            current_scene = {"arc": seg["arc_position"], "segments": [seg]}
        else:
            current_scene["segments"].append(seg)
    
    if current_scene["segments"]:
        scenes.append(current_scene)
    
    return {
        "schema_version": "3.0",
        "directed": True,
        "director": "pipeline_v2 (Claude + LearnByLeo)",
        "segment_count": len(output_segments),
        "scene_count": len(scenes),
        "total_words": total_words,
        "estimated_duration_sec": narr_duration,
        "assets_used": {
            "clips": len(set(d.get("visual_file", "") for d in decisions if d.get("visual_type") == "video_clip")),
            "images": len(set(d.get("visual_file", "") for d in decisions if d.get("visual_type") == "still_image")),
            "sfx": len(set(d.get("sfx_file", "") for d in decisions if d.get("sfx_file"))),
        },
        "scenes": scenes,
    }


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Director — sees everything, picks everything")
    parser.add_argument('--script', required=True, help='Path to enhanced script')
    parser.add_argument('--storyboard', help='Path to storyboard JSON (optional, for reference)')
    parser.add_argument('--footage', nargs='+', default=[], help='Footage directories to scan')
    parser.add_argument('--images', nargs='+', default=[], help='Image directories to scan')
    parser.add_argument('--sfx', default='', help='SFX directory')
    parser.add_argument('--transcripts', help='Transcripts JSON (from transcript_extractor)')
    parser.add_argument('--vision', help='Vision manifest JSON (from vision_analyzer)')
    parser.add_argument('--alignment', help='Narration alignment JSON (from narration_aligner)')
    parser.add_argument('--output', required=True, help='Output JSON path')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"DIRECTOR — Full Editorial Pass")
    print(f"{'='*60}")
    
    # Parse script
    print(f"\n1. Parsing script: {args.script}")
    segments = parse_script(args.script)
    print(f"   {len(segments)} segments, {sum(s['word_count'] for s in segments)} words")
    
    # Discover assets
    print(f"\n2. Discovering available assets...")
    clips = []
    for footage_dir in args.footage:
        clips.extend(discover_footage(footage_dir))
    print(f"   Clips: {len(clips)}")
    
    images = discover_images(args.images)
    print(f"   Images: {len(images)}")
    
    sfx = discover_sfx(args.sfx) if args.sfx else []
    print(f"   SFX: {len(sfx)}")
    
    if not clips and not images:
        print(f"\n   ERROR: No footage or images found!")
        print(f"   Run footage_sourcer and web_image_sourcer first.")
        return 1

    # Asset sufficiency check — need enough unique assets to avoid repetition
    total_assets = len(clips) + len(images)
    coverage_ratio = total_assets / max(len(segments), 1)
    print(f"   Asset coverage: {total_assets} assets for {len(segments)} segments ({coverage_ratio:.1f}x)")
    if coverage_ratio < 0.8:
        print(f"\n   ERROR: Insufficient assets ({coverage_ratio:.1f}x < 0.8x minimum)")
        print(f"   Need at least {int(len(segments) * 0.8)} assets, have {total_assets}")
        print(f"   Run footage_sourcer and web_image_sourcer to get more.")
        return 1
    if len(clips) < 10:
        print(f"   WARNING: Only {len(clips)} video clips. 15+ recommended for a documentary.")

    # Enrich with transcripts
    if args.transcripts and os.path.exists(args.transcripts):
        with open(args.transcripts) as f:
            transcripts_data = json.load(f)
        transcript_lookup = {}
        for t in transcripts_data.get("clips", transcripts_data if isinstance(transcripts_data, list) else []):
            fname = t.get("filename", "")
            transcript_lookup[fname] = t.get("transcript", t.get("text", ""))
        enriched = 0
        for clip in clips:
            t = transcript_lookup.get(clip.get("filename", ""))
            if t and not clip.get("transcript"):
                clip["transcript"] = t[:2000]
                clip["transcript_preview"] = t[:200]
                enriched += 1
        print(f"   Transcripts enriched: {enriched}/{len(clips)} clips")

    # Enrich with vision descriptions
    if args.vision and os.path.exists(args.vision):
        with open(args.vision) as f:
            vision_data = json.load(f)
        # Enrich clips
        vision_clips = {v.get("filename", ""): v for v in vision_data.get("clips", [])}
        for clip in clips:
            v = vision_clips.get(clip.get("filename", ""))
            if v:
                descs = v.get("frame_descriptions", [])
                clip["vision_description"] = " | ".join(
                    d.get("description", "")[:150] for d in descs[:3]
                )
                clip["topics"] = v.get("topics", [])
                clip["best_moments"] = v.get("best_moments", [])
        # Enrich images
        vision_images = {v.get("filename", ""): v for v in vision_data.get("images", [])}
        for img in images:
            v = vision_images.get(img.get("filename", ""))
            if v:
                img["vision_description"] = v.get("description", "")[:300]
                img["topics"] = v.get("topics", [])
        enriched_clips = sum(1 for c in clips if c.get("vision_description"))
        enriched_imgs = sum(1 for i in images if i.get("vision_description"))
        print(f"   Vision enriched: {enriched_clips}/{len(clips)} clips, {enriched_imgs}/{len(images)} images")
    
    # Load playbook
    playbook = load_playbook()
    print(f"   Playbook: {len(playbook)} modules")
    
    # Make editorial decisions
    print(f"\n3. Claude making editorial decisions...")
    decisions = direct_segments(segments, clips, images, sfx, playbook)
    
    if not decisions:
        print("   FAILED — no decisions returned")
        return 1
    
    print(f"   {len(decisions)} decisions made")
    
    # Validate
    print(f"\n4. Validating decisions...")
    decisions = validate_decisions(decisions, clips, images, sfx)
    
    # Pad or trim decisions to match segments
    while len(decisions) < len(segments):
        decisions.append({"visual_file": None, "arc_position": "context_setup", "tension_level": 0.3})
    decisions = decisions[:len(segments)]
    
    # Load narration alignment if available
    alignment = None
    if args.alignment and os.path.exists(args.alignment):
        with open(args.alignment) as f:
            alignment = json.load(f)
        print(f"   Alignment: {alignment.get('total_words', 0)} words, "
              f"{alignment.get('duration_sec', 0):.1f}s")

    # Build output
    print(f"\n5. Building output...")
    output = build_output(segments, decisions, clips, images, sfx, alignment=alignment)
    
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"   Saved: {args.output}")
    print(f"   Schema: v{output['schema_version']}")
    print(f"   {output['segment_count']} segments in {output['scene_count']} scenes")
    print(f"   Assets: {output['assets_used']}")
    
    # Summary of key decisions
    pauses = sum(1 for d in decisions if d.get('vo_pause_before', 0) > 0)
    clip_audio = sum(1 for d in decisions if d.get('clip_audio') in ('play', 'play_then_mute'))
    sfx_used = sum(1 for d in decisions if d.get('sfx_file'))
    chapters = sum(1 for d in decisions if d.get('chapter_card'))
    
    print(f"\n   Editorial summary:")
    print(f"   VO pauses: {pauses}")
    print(f"   Clip audio moments: {clip_audio}")
    print(f"   SFX triggers: {sfx_used}")
    print(f"   Chapter cards: {chapters}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
