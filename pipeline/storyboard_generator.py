#!/usr/bin/env python3
"""
storyboard_generator.py — Converts an enhanced script into a per-segment visual brief.

This is the context layer that closes the gap between "generically correct footage"
and "the specific image that makes this story beat land."

For each narration segment it produces:
  - what to SHOW (specific object/document/person/place — not a content type)
  - targeted search query (feeds directly into footage_sourcer.py)
  - focal element (what Ken Burns should pull toward)
  - shot type (document_photo / archival_footage / map / person)
  - intensity (tense / neutral / energized / ominous)

This replaces random tag-pool selection with deliberate, story-driven sourcing.

Pipeline position:
    [SCRIPT ENHANCEMENT] → [STORYBOARD GENERATOR] → [FOOTAGE SOURCER] → [ASSEMBLER]
                                       ↓
                             storyboard.json (per-segment brief)
                                       ↓
                        footage_sourcer uses these as search queries
                        assembler uses focal_element for Ken Burns

Usage:
    python pipeline/storyboard_generator.py --script scripts/enhanced_topic.txt
    python pipeline/storyboard_generator.py --script scripts/enhanced.txt --out research/fern_clone/topic/storyboard.json
    python pipeline/storyboard_generator.py --script scripts/enhanced.txt --preview  # print only, no file
    python pipeline/storyboard_generator.py --script scripts/enhanced.txt --model qwen3.5:4b

Requirements:
    Ollama running locally (ollama serve) with any small model.
    Default: qwen3.5:4b (fast), falls back to qwen2.5:7b
    No internet required. Fully local.
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    from pipeline.production_rules import (
        load_playbook,
        playbook_motion,
        playbook_segment_duration,
        playbook_sfx,
    )
except ImportError:
    from production_rules import (  # type: ignore[no-redef]
        load_playbook,
        playbook_motion,
        playbook_segment_duration,
        playbook_sfx,
    )

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_PREFERENCE = [
    "qwen3.5:27b",   # best quality, 17GB
    "qwen3.5:4b",    # fast, 3.4GB
    "qwen2.5:7b",    # fallback
    "llama3.2:3b",   # last resort
]

# Fern-measured content type distribution
# We bias toward these when generating shot types
CONTENT_TYPE_WEIGHTS = {
    "document_photo":    0.62,
    "documentary_photo": 0.13,
    "archival_footage":  0.06,
    "map":               0.05,
    "person_photo":      0.05,
    "news_footage":      0.04,
    "other":             0.05,
}

# Segment target length based on Fern's pacing
SEGMENT_WORDS_MIN = 15   # ~6.5s at 138.7 WPM
SEGMENT_WORDS_MAX = 80   # ~35s — break longer passages

CACHE_DIR = Path(".storyboard_cache")

# Frame rate for timing sheet calculations
TIMING_FPS = 30


# ── Script parsing ─────────────────────────────────────────────────────────────

def parse_script_segments(script_path: Path) -> list[dict]:
    """
    Split enhanced script into segments for visual direction.

    A segment = one visual moment = roughly one sentence or short passage.
    Uses [PAUSE:x] and [BEAT] as natural break points.
    Long passages are broken at sentence boundaries.

    Returns: [{text, emotion, is_chapter_break, chapter_title}, ...]
    """
    text = script_path.read_text(encoding="utf-8")
    current_emotion = "neutral"
    segments = []
    chapter_num = 0

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split by paragraph first (blank lines = natural breaks)
    paragraphs = re.split(r"\n{2,}", text.strip())

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Detect explicit chapter headings (e.g. "CHAPTER 1: FORT DETRICK" or "OUTRO")
        chapter_match = re.match(r"^(?:\[VOICE:[^\]]+\]\s*)?CHAPTER\s+\d+\s*:\s*(.+)$", para, re.IGNORECASE)
        outro_match = re.match(r"^(?:\[VOICE:[^\]]+\]\s*)?OUTRO\s*$", para, re.IGNORECASE)
        if chapter_match or outro_match:
            title_text = chapter_match.group(1).strip() if chapter_match else "OUTRO"
            # Strip any remaining markers from title
            title_text = re.sub(r"\[VOICE:[^\]]+\]|\[BEAT\]|\[BREATH\]|\[PAUSE:[^\]]+\]", "", title_text).strip()
            chapter_num += 1
            segments.append({
                "text": title_text,
                "emotion": current_emotion,
                "is_chapter_break": True,
                "chapter_num": chapter_num,
                "chapter_title": title_text,
            })
            continue

        # Standalone pause markers — just skip (pauses are handled in voice generation)
        if re.match(r"^\[PAUSE:[\d.]+\]\s*$", para):
            continue

        # Detect emotion changes
        voice_match = re.search(r"\[VOICE:(tense|neutral|energized|ominous)\]", para)
        if voice_match:
            current_emotion = voice_match.group(1)

        # Strip control markers from text
        clean = re.sub(r"\[VOICE:[^\]]+\]|\[BEAT\]|\[BREATH\]|\[PAUSE:[^\]]+\]", "", para).strip()
        if not clean:
            continue

        # Break long paragraphs at sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", clean)
        buffer = []
        buffer_words = 0

        for sentence in sentences:
            words = len(sentence.split())
            if buffer_words + words > SEGMENT_WORDS_MAX and buffer:
                segments.append({
                    "text": " ".join(buffer),
                    "emotion": current_emotion,
                    "is_chapter_break": False,
                })
                buffer = [sentence]
                buffer_words = words
            else:
                buffer.append(sentence)
                buffer_words += words

        if buffer:
            segments.append({
                "text": " ".join(buffer),
                "emotion": current_emotion,
                "is_chapter_break": False,
            })

    return segments


# ── Ollama integration ─────────────────────────────────────────────────────────

def _get_available_model() -> str | None:
    """Return first MODEL_PREFERENCE entry that ollama has installed."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        installed = {m["name"] for m in data.get("models", [])}
        for model in MODEL_PREFERENCE:
            # Match with or without :latest
            if model in installed or f"{model}:latest" in installed:
                return model
            # Match base name (e.g. qwen3.5:4b matches qwen3.5:4b-instruct-q4_K_M)
            base = model.split(":")[0]
            for inst in installed:
                if inst.startswith(base + ":"):
                    return inst
    except Exception:
        pass
    return None


def _ollama_generate(model: str, prompt: str) -> str | None:
    """Call Ollama text generation, return response text."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,          # disable qwen3.5 thinking mode — output only
        "options": {"temperature": 0.3, "num_predict": 300},
    }).encode()
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
            return data.get("response", "").strip()
    except Exception:
        return None


# ── Visual brief generation ───────────────────────────────────────────────────

STORYBOARD_PROMPT = """You are a documentary video editor working in the style of @fern-tv on YouTube.
Your job: given one sentence of narration, decide what specific image should appear on screen
and HOW it should be presented (motion, zoom speed, cut motivation).

Rules:
- Be SPECIFIC. Not "a document" but "the original 1973 FBI memo with CONFIDENTIAL stamp visible"
- Not "a person" but "Ted Kaczynski's Harvard ID photo, 1958, young face"
- The visual should ILLUSTRATE the exact fact or emotion being stated
- Prefer documents, photos, maps, archival footage over generic stock
- If the narration says a name → show that person's face or their work
- If the narration says a date → show something from that date
- If the narration describes a location → show that location

Motion rules (from Fern's editorial playbook):
- zoom_in = drawing attention to detail, building tension, revealing evidence
- zoom_out = showing scope/scale, pulling back after intense moment, establishing location
- pan_right/left = scanning a document, reading text, timeline progression
- pan_up/pan_down = scrolling archival text, reading newspaper columns
- static = letting viewer read text, brief transitional moment
- zoom speed = narrative intensity: 1-3%/s context, 3-5%/s tension, 5-9%/s peak, 15-25%/s extreme revelation (max 1-2 per video)

cut_motivation = WHY is this a new visual moment:
- narrative_shift: story moves to new topic/person/era
- name_drop: a person is named for the first time
- evidence_intro: a document/proof/artifact is cited
- location_named: a new place is mentioned
- tone_change: emotional register shifts
- visual_freshness: same narrative beat, but current image held too long

text_overlay_type = what text (if any) should reinforce the narration:
- person_identification: show person's FULL NAME on first mention
- entity_label: show organization/program name (e.g., MKULTRA, FBI)
- location_label: show place name to set the scene
- quote: show the subject's own words as they're read
- source_citation: show [source number] on documents
- null: no text overlay needed

narrative_function guide:
- hook_opening: first 30s, establishes stakes
- context_background: factual dates, timelines, background setup
- character_intro: first mention of a named person
- tension_build: pressure building toward a reveal
- reveal: "except / in reality / it turns out" — the twist or discovery
- stakes_moment: consequences, danger, superlatives ("most notorious", "executed")
- climax: peak action — arrest, explosion, confession, the defining moment
- aftermath: resolution, legacy, "to this day"

Respond with ONLY valid JSON, no explanation:
{
  "show": "one specific visual description (15 words max)",
  "search_query": "3-6 word search query to find this on YouTube/Archive.org",
  "focal_element": "what element in the frame to zoom toward (10 words max)",
  "shot_type": "document_photo | archival_footage | person_photo | map | news_footage | documentary_photo",
  "intensity": "tense | neutral | energized | ominous",
  "narrative_function": "hook_opening | context_background | character_intro | tension_build | reveal | stakes_moment | climax | aftermath",
  "motion_direction": "zoom_in | zoom_out | pan_right | pan_left | pan_up | pan_down | static",
  "zoom_rate_pct_sec": 3.0,
  "cut_motivation": "narrative_shift | name_drop | evidence_intro | location_named | tone_change | visual_freshness",
  "text_overlay_type": "person_identification | entity_label | location_label | quote | source_citation | null"
}

Narration: "{TEXT}"
Emotion context: {EMOTION}

JSON:"""


def _cache_key(text: str, emotion: str, model: str) -> str:
    return hashlib.md5(f"{model}|{emotion}|{text}".encode()).hexdigest()[:16]


def generate_visual_brief(
    segment: dict,
    model: str,
    use_cache: bool = True,
) -> dict:
    """Generate visual direction for one segment. Returns enriched segment dict."""

    if segment.get("is_chapter_break"):
        brief = {
            **segment,
            "show": "chapter card — black screen with chapter title",
            "search_query": None,
            "focal_element": None,
            "shot_type": "chapter_card",
            "intensity": segment.get("emotion", "neutral"),
            "narrative_function": "chapter_break",
        }
        return _enrich_from_playbook(brief)

    text = segment["text"]
    emotion = segment.get("emotion", "neutral")

    # Cache check
    if use_cache:
        CACHE_DIR.mkdir(exist_ok=True)
        cache_file = CACHE_DIR / f"{_cache_key(text, emotion, model)}.json"
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text())
                merged = {**segment, **cached, "_cached": True}
                return _enrich_from_playbook(merged)
            except json.JSONDecodeError:
                pass

    # Build prompt
    prompt = STORYBOARD_PROMPT.replace("{TEXT}", text).replace("{EMOTION}", emotion)

    response = _ollama_generate(model, prompt)

    if not response:
        brief = _fallback_brief(text, emotion)
    else:
        brief = _parse_ollama_response(response, text, emotion)

    # Enrich with playbook rules (fills any missing fields)
    brief = _enrich_from_playbook({**segment, **brief})

    # Cache result (strip segment fields to keep cache clean)
    if use_cache:
        cache_fields = {k: v for k, v in brief.items()
                        if k not in ("text", "emotion", "is_chapter_break",
                                     "chapter_num", "chapter_title", "_cached")}
        cache_file.write_text(json.dumps(cache_fields))

    return brief


def _parse_ollama_response(response: str, text: str, emotion: str) -> dict:
    """Parse JSON from ollama response, with fallback."""
    # Extract JSON block
    match = re.search(r"\{[\s\S]*?\}", response)
    if match:
        try:
            data = json.loads(match.group())
            # Validate required fields
            required = {"show", "search_query", "focal_element", "shot_type", "intensity"}
            if required.issubset(data.keys()):
                result = {k: data[k] for k in required}
                # Accept all optional playbook fields
                for opt in ("narrative_function", "motion_direction",
                            "zoom_rate_pct_sec", "cut_motivation",
                            "text_overlay_type"):
                    if opt in data:
                        result[opt] = data[opt]
                return result
        except json.JSONDecodeError:
            pass

    # Fallback if parse fails
    return _fallback_brief(text, emotion)


def _fallback_brief(text: str, emotion: str) -> dict:
    """Rule-based fallback when model is unavailable."""
    text_lower = text.lower()

    # Shot type from keywords
    if any(w in text_lower for w in ["document", "memo", "file", "report", "letter", "classified"]):
        shot_type = "document_photo"
        show = f"official document related to: {text[:60]}"
        focal = "text content of document"
    elif any(w in text_lower for w in ["map", "location", "city", "country", "state"]):
        shot_type = "map"
        show = f"map showing location referenced in: {text[:60]}"
        focal = "key location on map"
    elif any(w in text_lower for w in ["said", "told", "spoke", "arrested", "born", "died"]):
        shot_type = "person_photo"
        show = f"portrait photo of person referenced in: {text[:60]}"
        focal = "face of subject"
    elif any(w in text_lower for w in ["footage", "video", "broadcast", "news", "protest"]):
        shot_type = "archival_footage"
        show = f"archival footage of: {text[:60]}"
        focal = "primary subject"
    else:
        shot_type = "documentary_photo"
        show = f"photo illustrating: {text[:60]}"
        focal = "primary subject"

    # Simple 5-word search query from key nouns
    words = re.findall(r"\b[A-Z][a-z]+|[A-Z]{2,}\b", text)
    query = " ".join(words[:4]) if words else text.split()[:4]
    if isinstance(query, list):
        query = " ".join(query)

    # Derive narrative_function from emotion + keyword signals
    _tl = text_lower
    _reveal_words = {"except", "in reality", "it turns out", "but then", "however",
                     "suddenly", "shockingly", "turns out", "actually,", "in fact,"}
    _stakes_words = {"most dangerous", "most notorious", "executed", "killed", "murdered",
                     "sentenced to", "convicted", "deadliest", "unprecedented", "first ever"}
    _climax_words = {"arrested", "opened fire", "detonated", "stormed", "confessed",
                     "pleaded guilty", "was caught", "they found", "that's when"}
    _aftermath_words = {"ultimately", "in the end", "eventually", "to this day",
                        "the legacy", "years later,", "today,", "the fallout"}
    if any(w in _tl for w in _reveal_words):
        narrative_function = "reveal"
    elif any(w in _tl for w in _climax_words) and emotion in ("tense", "energized"):
        narrative_function = "climax"
    elif any(w in _tl for w in _stakes_words):
        narrative_function = "stakes_moment"
    elif any(w in _tl for w in _aftermath_words):
        narrative_function = "aftermath"
    elif emotion == "energized":
        narrative_function = "climax"
    elif emotion == "tense":
        narrative_function = "tension_build"
    elif emotion == "ominous":
        narrative_function = "tension_build"
    else:
        narrative_function = "context_background"

    # Resolve playbook-driven motion + duration
    direction, zoom_rate = playbook_motion(narrative_function, emotion)
    dur_min, dur_max = playbook_segment_duration(shot_type, narrative_function)

    return {
        "show": show,
        "search_query": query,
        "focal_element": focal,
        "shot_type": shot_type,
        "intensity": emotion,
        "narrative_function": narrative_function,
        "motion_direction": direction,
        "zoom_rate_pct_sec": zoom_rate,
        "hold_duration_range": [dur_min, dur_max],
        "cut_motivation": _infer_cut_motivation(text, narrative_function),
        "text_overlay_type": _infer_text_overlay_type(text, narrative_function),
    }


# ── Playbook enrichment ──────────────────────────────────────────────────────

def _infer_cut_motivation(text: str, narrative_function: str) -> str:
    """Classify WHY this segment is a new visual moment."""
    tl = text.lower()

    # Name drop — proper nouns suggest a person being introduced
    proper_nouns = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)
    if narrative_function == "character_intro" or proper_nouns:
        return "name_drop"

    # Evidence intro — documents, studies, reports being cited
    if any(w in tl for w in ["document", "memo", "file", "report", "letter",
                              "study", "evidence", "investigation", "classified",
                              "according to", "records show", "files reveal"]):
        return "evidence_intro"

    # Location named
    if any(w in tl for w in ["in ", "at ", "from "]) and re.search(
            r"\b[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?\b", text):
        # Check for place-like patterns (City, State)
        if re.search(r"\b[A-Z][a-z]+,\s*[A-Z]", text):
            return "location_named"

    # Tone change
    if narrative_function in ("reveal", "revelation", "climax", "stakes_moment"):
        return "tone_change"

    # Narrative shift — topic/era/person change
    if narrative_function in ("hook_opening", "chapter_break", "transition"):
        return "narrative_shift"

    return "visual_freshness"


def _infer_text_overlay_type(text: str, narrative_function: str) -> str | None:
    """Map text patterns to semantic overlay type."""
    # Person identification — first mention of a full name
    if narrative_function == "character_intro":
        names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)
        if names:
            return "person_identification"

    # Quote — text contains quoted speech
    if re.search(r'"[^"]{10,}"', text) or re.search(r"\u201c[^\u201d]{10,}\u201d", text):
        return "quote"

    # Entity label — ALL CAPS acronyms or org names
    if re.search(r"\b[A-Z]{2,}\b", text):
        acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
        # Filter out common words that happen to be caps
        real_acronyms = [a for a in acronyms if a not in ("THE", "AND", "FOR", "BUT", "NOT", "HIS", "HER")]
        if real_acronyms:
            return "entity_label"

    # Location label — place names (City, State pattern)
    if re.search(r"\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b", text):
        return "location_label"

    return None


def _build_timing_sheet(brief: dict, fps: int = TIMING_FPS) -> dict:
    """
    Build an exposure sheet (X-sheet) for one storyboard segment.

    Maps every editorial decision to exact frame numbers so the assembler
    (or a human animator) knows precisely what happens and when.

    Fields:
        hold_frames:      total frames this segment occupies
        motion:           keyframe spec — type, start/end scale, easing
        text_entry_frame: frame when text overlay starts appearing
        text_exit_frame:  frame when text overlay finishes / fades
        text_content:     the actual overlay string (or None)
        sfx_trigger_frame: frame when SFX fires (None = no SFX)
        sfx_type:         which SFX to use (None = no SFX)
        transition_in:    how this segment enters (cut/fade/dissolve + frame count)
        transition_out:   how this segment exits
        sub_beats:        list of visual sub-divisions within the segment
                          (for segments > 3s that need internal variety)
    """
    # Resolve duration → frame count
    dur_range = brief.get("hold_duration_range", [4.0, 8.0])
    # Use midpoint of range as the nominal duration
    dur_mid = (dur_range[0] + dur_range[1]) / 2.0
    hold_frames = round(dur_mid * fps)

    # ── Motion keyframes ──
    motion_dir = brief.get("motion_direction", "zoom_in")
    zoom_rate = brief.get("zoom_rate_pct_sec", 3.0)
    # Calculate total scale change over the segment
    # zoom_rate is %/sec, so over dur_mid seconds: total_pct = zoom_rate * dur_mid
    total_pct = zoom_rate * dur_mid / 100.0
    if motion_dir == "zoom_in":
        start_scale, end_scale = 1.0, 1.0 + total_pct
    elif motion_dir == "zoom_out":
        start_scale, end_scale = 1.0 + total_pct, 1.0
    else:
        # Pan directions — scale stays 1.0, motion expressed differently
        start_scale, end_scale = 1.0, 1.0

    # Easing: reveals/climax get ease_in (accelerating punch), context gets ease_in_out
    nf = brief.get("narrative_function", "context_background")
    if nf in ("reveal", "revelation", "climax", "stakes_moment"):
        easing = "ease_in"
    elif nf in ("aftermath",):
        easing = "ease_out"
    else:
        easing = "ease_in_out"

    motion_spec = {
        "type": motion_dir,
        "start_scale": round(start_scale, 4),
        "end_scale": round(end_scale, 4),
        "easing": easing,
    }

    # For pan directions, add pan_pixels_per_frame
    if motion_dir.startswith("pan_"):
        # Translate zoom_rate (nominally %/s) into pixel shift per frame
        # At 1920px wide, 3%/s ≈ 57.6 px/s ≈ ~1.9 px/frame at 30fps
        px_per_sec = (zoom_rate / 100.0) * 1920
        motion_spec["pan_px_per_frame"] = round(px_per_sec / fps, 2)

    # ── Text overlay timing ──
    text_type = brief.get("text_overlay_type")
    text_content = None
    text_entry_frame = None
    text_exit_frame = None

    if text_type and text_type != "null":
        text_content = _resolve_text_content(brief, text_type)
        # Text appears 3-5 frames in (not instant — gives eye time to land)
        text_entry_frame = 4
        # Text stays for 70% of segment, then fades
        text_exit_frame = round(hold_frames * 0.85)

        # Special cases:
        if text_type == "quote":
            # Quotes appear later (narrator sets up context first)
            text_entry_frame = round(hold_frames * 0.15)
        elif text_type == "source_citation":
            # Citations flash briefly at bottom
            text_entry_frame = round(hold_frames * 0.6)
            text_exit_frame = hold_frames - 3

    # ── SFX timing ──
    sfx_type = playbook_sfx(nf, brief.get("cut_motivation"))
    sfx_trigger_frame = None
    if sfx_type:
        if sfx_type in ("whoosh",):
            sfx_trigger_frame = 0  # whoosh on the cut itself
        elif sfx_type in ("impact",):
            sfx_trigger_frame = 2  # impact lands 2 frames after cut
        elif sfx_type in ("shimmer", "tension"):
            sfx_trigger_frame = round(hold_frames * 0.1)  # subtle fade-in
        elif sfx_type in ("rumble",):
            sfx_trigger_frame = 0  # rumble starts immediately

    # ── Transitions ──
    is_chapter = nf == "chapter_break"
    intensity = brief.get("intensity", "neutral")

    # Transition in
    if is_chapter:
        transition_in = {"type": "fade_from_black", "frames": round(fps * 0.5)}
    elif nf in ("reveal", "revelation") and intensity in ("tense", "energized"):
        transition_in = {"type": "cut", "frames": 0}  # hard cut for impact
    elif nf == "aftermath":
        transition_in = {"type": "dissolve", "frames": round(fps * 0.4)}
    else:
        transition_in = {"type": "cut", "frames": 0}

    # Transition out
    if is_chapter:
        transition_out = {"type": "fade_to_black", "frames": round(fps * 0.5)}
    elif brief.get("cut_motivation") == "tone_change":
        transition_out = {"type": "dissolve", "frames": round(fps * 0.3)}
    else:
        transition_out = {"type": "cut", "frames": 0}

    # ── Sub-beats (internal variety for segments > 3s) ──
    sub_beats = _generate_sub_beats(brief, hold_frames, fps)

    return {
        "hold_frames": hold_frames,
        "hold_sec": round(dur_mid, 2),
        "fps": fps,
        "motion": motion_spec,
        "text_entry_frame": text_entry_frame,
        "text_exit_frame": text_exit_frame,
        "text_content": text_content,
        "sfx_trigger_frame": sfx_trigger_frame,
        "sfx_type": sfx_type,
        "transition_in": transition_in,
        "transition_out": transition_out,
        "sub_beats": sub_beats,
    }


def _resolve_text_content(brief: dict, text_type: str) -> str | None:
    """Extract the actual text string to display from narration + overlay type."""
    text = brief.get("text", "")

    if text_type == "person_identification":
        # Find full names (First Last)
        names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)
        return names[0].upper() if names else None

    if text_type == "entity_label":
        # Find acronyms / org names
        acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
        real = [a for a in acronyms if a not in ("THE", "AND", "FOR", "BUT", "NOT", "HIS", "HER")]
        return real[0] if real else None

    if text_type == "location_label":
        # Find "City, State" patterns first (highest specificity)
        city_state = re.findall(r"\b([A-Z][a-z]+ [A-Z][a-z]+,\s*[A-Z][a-z]+)\b", text)
        if city_state:
            return city_state[0].upper()
        # Fall back to "Place Name" (two+ capitalized words that aren't person names)
        places = re.findall(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b", text)
        _skip = {"The", "A", "An", "In", "On", "At", "He", "She", "His", "Her",
                 "But", "And", "Was", "Were", "Had", "That", "This", "They"}
        places = [p for p in places if p.split()[0] not in _skip]
        return places[0].upper() if places else None

    if text_type == "quote":
        # Extract quoted text
        match = re.search(r'"([^"]{10,})"', text) or re.search(r'\u201c([^\u201d]{10,})\u201d', text)
        return f'"{match.group(1)}"' if match else None

    if text_type == "source_citation":
        return "SOURCE"

    return None


def _generate_sub_beats(brief: dict, hold_frames: int, fps: int) -> list[dict]:
    """
    Generate internal visual sub-beats for segments that hold too long.

    Based on v4 learnings: any segment > 3s needs internal variety —
    zoom speed changes, text reveals, focal shifts — to keep the viewer
    engaged. This is the X-sheet's frame-by-frame breakdown.

    Returns list of sub-beat dicts, each with:
      - start_frame, end_frame
      - action: what changes at this sub-beat
      - description: human-readable note
    """
    hold_sec = hold_frames / fps
    sub_beats = []

    # Short segments (< 3s) don't need sub-beats
    if hold_sec < 3.0:
        return sub_beats

    nf = brief.get("narrative_function", "context_background")
    text_type = brief.get("text_overlay_type")

    # Medium segments (3-5s): 2 sub-beats
    if hold_sec < 5.0:
        mid = hold_frames // 2
        sub_beats.append({
            "start_frame": 0,
            "end_frame": mid,
            "action": "primary_visual",
            "description": "Main visual + initial motion",
        })
        # Second half: zoom speed change or text entry
        action2 = "text_reveal" if text_type else "zoom_accelerate"
        sub_beats.append({
            "start_frame": mid,
            "end_frame": hold_frames,
            "action": action2,
            "description": "Text overlay appears" if text_type else "Motion accelerates toward focal point",
        })

    # Long segments (5-8s): 3 sub-beats
    elif hold_sec < 8.0:
        third = hold_frames // 3
        sub_beats.append({
            "start_frame": 0,
            "end_frame": third,
            "action": "establish",
            "description": "Wide view, slow initial motion",
        })
        sub_beats.append({
            "start_frame": third,
            "end_frame": third * 2,
            "action": "focus",
            "description": "Tighten to focal element" + (f" + text: {brief.get('text_overlay_type', '')}" if text_type else ""),
        })
        action3 = "resolve" if nf in ("aftermath", "context_background") else "intensify"
        sub_beats.append({
            "start_frame": third * 2,
            "end_frame": hold_frames,
            "action": action3,
            "description": "Push to detail / prepare for next cut" if action3 == "intensify" else "Hold on key detail, ease motion",
        })

    # Very long segments (8s+): 4 sub-beats — needs most internal variety
    else:
        quarter = hold_frames // 4
        sub_beats.append({
            "start_frame": 0,
            "end_frame": quarter,
            "action": "establish",
            "description": "Wide establishing view",
        })
        sub_beats.append({
            "start_frame": quarter,
            "end_frame": quarter * 2,
            "action": "detail_1",
            "description": "First detail / text entry",
        })
        sub_beats.append({
            "start_frame": quarter * 2,
            "end_frame": quarter * 3,
            "action": "detail_2",
            "description": "Second detail or focal shift",
        })
        sub_beats.append({
            "start_frame": quarter * 3,
            "end_frame": hold_frames,
            "action": "resolve",
            "description": "Final push / prepare exit",
        })

    return sub_beats


def _enrich_from_playbook(brief: dict) -> dict:
    """
    Post-processor: fill any missing playbook fields using narrative intent.

    Applied to BOTH Ollama responses and fallback-generated briefs.
    Handles old cached entries gracefully (fills missing fields only).
    """
    nf = brief.get("narrative_function", "context_background")
    intensity = brief.get("intensity", "neutral")
    shot_type = brief.get("shot_type", "document_photo")
    text = brief.get("text", brief.get("show", ""))

    # motion_direction + zoom_rate_pct_sec
    if "motion_direction" not in brief or "zoom_rate_pct_sec" not in brief:
        direction, zoom_rate = playbook_motion(nf, intensity)
        brief.setdefault("motion_direction", direction)
        brief.setdefault("zoom_rate_pct_sec", zoom_rate)

    # hold_duration_range
    if "hold_duration_range" not in brief:
        dur_min, dur_max = playbook_segment_duration(shot_type, nf)
        brief["hold_duration_range"] = [dur_min, dur_max]

    # cut_motivation
    if "cut_motivation" not in brief:
        brief["cut_motivation"] = _infer_cut_motivation(text, nf)

    # text_overlay_type
    if "text_overlay_type" not in brief:
        brief["text_overlay_type"] = _infer_text_overlay_type(text, nf)

    # chapter_break transition_spec
    if nf == "chapter_break" and "transition_spec" not in brief:
        brief["transition_spec"] = {
            "silence_sec": [2, 5],
            "card_duration_sec": [2, 4],
            "style": "white_serif_on_dark",
        }

    # ── Timing sheet (exposure sheet / X-sheet) ──
    # Built AFTER all other fields are resolved so it can read motion, text, SFX, etc.
    if "timing_sheet" not in brief:
        brief["timing_sheet"] = _build_timing_sheet(brief)

    return brief


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Generate storyboard from enhanced script")
    ap.add_argument("--script",   required=True, help="Path to enhanced script .txt")
    ap.add_argument("--out",      help="Output storyboard JSON path (default: auto-derived)")
    ap.add_argument("--model",    help="Force a specific Ollama model")
    ap.add_argument("--preview",  action="store_true", help="Print storyboard, don't write file")
    ap.add_argument("--no-cache", action="store_true", help="Disable segment cache")
    args = ap.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    # Determine model
    if args.model:
        model = args.model
    else:
        model = _get_available_model()
        if model:
            print(f"Using model: {model}")
        else:
            print("WARNING: Ollama not running or no model installed. Using rule-based fallback.")
            model = None

    # Parse script into segments
    print(f"Parsing script: {script_path.name}")
    segments = parse_script_segments(script_path)
    print(f"  {len(segments)} segments identified")

    # Generate visual brief for each segment
    storyboard = []
    visual_count = sum(1 for s in segments if not s.get("is_chapter_break"))
    chapter_count = sum(1 for s in segments if s.get("is_chapter_break"))

    print(f"  {visual_count} visual segments  +  {chapter_count} chapter breaks")
    print(f"\nGenerating visual briefs...")

    for i, seg in enumerate(segments):
        if model:
            brief = generate_visual_brief(seg, model, use_cache=not args.no_cache)
        else:
            brief = {**seg, **_fallback_brief(seg["text"], seg.get("emotion", "neutral"))}
            if seg.get("is_chapter_break"):
                brief["shot_type"] = "chapter_card"
                brief["search_query"] = None

        storyboard.append(brief)

        if not args.preview:
            cached_tag = " (cached)" if brief.get("_cached") else ""
            print(f"  [{i+1:3d}/{len(segments)}]  {brief.get('shot_type','?'):20s}  "
                  f"{brief.get('show','?')[:60]}{cached_tag}")

    # Output
    if args.preview:
        print(f"\n{'─'*70}")
        for i, s in enumerate(storyboard):
            print(f"\n[{i+1:3d}] {s.get('emotion','').upper():<10}  {s.get('shot_type','')}")
            print(f"  NAR: {s['text'][:100]}")
            print(f"  SHOW: {s.get('show','')}")
            print(f"  SEARCH: {s.get('search_query','')}")
            print(f"  FOCUS: {s.get('focal_element','')}")
        print(f"\n{'─'*70}")
        print(f"Total: {len(storyboard)} segments")
        return

    # Write output
    if args.out:
        out_path = Path(args.out)
    else:
        # Derive from script path: scripts/enhanced_topic.txt → storyboard/topic.json
        slug = script_path.stem.replace("enhanced_", "").replace("raw_", "")
        out_path = Path("storyboards") / f"{slug}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(storyboard, indent=2))
    print(f"\nStoryboard written → {out_path}")
    print(f"  {len(storyboard)} entries  ({visual_count} visual + {chapter_count} chapter cards)")
    print(f"\nNext: pass storyboard to footage_sourcer:")
    print(f"  python pipeline/footage_sourcer.py --storyboard {out_path} --out footage/fern_clone/topic/")


if __name__ == "__main__":
    main()
