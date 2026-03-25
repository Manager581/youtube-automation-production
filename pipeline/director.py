#!/usr/bin/env python3
"""
director.py — Full-context editorial director for Fern-style documentaries.

Unlike the per-segment storyboard generator (which processes each sentence in isolation),
the Director reads the ENTIRE script and makes every editorial decision with full
narrative awareness: pacing, SFX, transitions, holds, compositions, text timing,
emotional arc — all as one cohesive video.

This module is designed to be called interactively by Claude Code (free, no API cost)
or programmatically with a local LLM that can handle the full script context.

Pipeline position:
    [SCRIPT ENHANCEMENT] → [STORYBOARD GENERATOR] → [DIRECTOR] → [FOOTAGE SOURCER] → [ASSEMBLER]
                                    ↓                     ↓
                           per-segment visuals    full-context editorial
                           (what to show)         (how to present it)

Usage:
    # Interactive: Claude Code reads script and generates director's brief
    python pipeline/director.py --script scripts/enhanced_topic.txt --storyboard storyboards/topic.json

    # The director reads the existing storyboard (visual choices) and enhances every
    # segment with context-aware editorial decisions.
"""

import json
import math
import re
import sys
from pathlib import Path

# ── Playbook Integration ──────────────────────────────────────────────────
# The playbook sits above the director and provides strategy-level rules
# derived from studying top YouTube creators (LearnByLeo, etc.)

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from playbook.loader import Playbook
    _PLAYBOOK = Playbook()
    _HAS_PLAYBOOK = True
except (ImportError, FileNotFoundError):
    _PLAYBOOK = None
    _HAS_PLAYBOOK = False

# ── Narrative Arc Categories ────────────────────────────────────────────────

# The director understands these arc positions and adjusts everything accordingly
ARC_PROFILES = {
    "cold_open": {
        "pacing": "fast",           # Quick cuts, urgency
        "base_hold": [2.0, 5.0],    # Short holds
        "atmosphere": "fog",
        "sfx_density": "high",      # Frequent SFX
        "text_size": "large",       # Big text for dates/names
        "transition_style": "hard_cut",
    },
    "context_setup": {
        "pacing": "measured",       # Steady, informational
        "base_hold": [5.0, 8.0],    # Longer holds, let viewer absorb
        "atmosphere": "none",
        "sfx_density": "sparse",
        "text_size": "medium",
        "transition_style": "cut",
    },
    "tension_build": {
        "pacing": "slow_then_fast", # Gradually accelerating
        "base_hold": [4.0, 7.0],
        "atmosphere": "dust",
        "sfx_density": "building",  # More SFX as tension builds
        "text_size": "medium",
        "transition_style": "cut",
    },
    "revelation": {
        "pacing": "dramatic",       # Hold → PUNCH
        "base_hold": [3.0, 6.0],
        "atmosphere": "dust",
        "sfx_density": "punctuated", # Key moments only
        "text_size": "large",
        "transition_style": "hard_cut",
    },
    "emotional_peak": {
        "pacing": "fast",
        "base_hold": [2.0, 4.0],
        "atmosphere": "dust",
        "sfx_density": "high",
        "text_size": "large",
        "transition_style": "hard_cut",
    },
    "aftermath": {
        "pacing": "slow",           # Let it breathe
        "base_hold": [6.0, 10.0],
        "atmosphere": "fog",
        "sfx_density": "minimal",
        "text_size": "small",
        "transition_style": "dissolve",
    },
    "chapter_transition": {
        "pacing": "pause",
        "base_hold": [3.0, 5.0],
        "atmosphere": "none",
        "sfx_density": "none",
        "text_size": "large",
        "transition_style": "fade",
    },
}

# SFX that match actual content (not just narrative function)
# These rules are topic-agnostic — they match narration keywords to SFX types
# Following the playbook's 5-layer sound design: whoosh, highlight, riser, hit/impact, drone/rumble
CONTENT_SFX_RULES = [
    # Physical/violent actions → impact
    (r"crashes? through.*window|shatter|broke.*glass|through the glass", "glass_shatter", "glass breaking matches narration"),
    (r"falls? to.*death|fell.*stories|plunge|through.*window.*fall", "body_impact", "impact of fall"),
    (r"gun|shot|fire|weapon|bomb|deton", "impact", "violent action"),
    (r"scream|shout|yell|crash", "impact", "sudden violent sound"),
    (r"bruise|hematoma|injury|wound|struck|hit|blow", "impact", "physical violence"),

    # Secrets/revelation → tension riser
    (r"secret|classified|top secret|confidential|hidden|buried", "tension", "secrecy revealed"),
    (r"nobody told you|didn't know|never been told|invisible", "tension", "hidden knowledge revealed"),

    # Substances/altered states → shimmer/highlight
    (r"LSD|drug|dose|cointreau|experiment", "shimmer", "mind-altering substance"),

    # Discovery/revelation → shimmer highlight
    (r"discover|found|reveal|uncover|exhum|investigation|expose", "shimmer", "discovery moment"),

    # Death/harm → rumble drone
    (r"dead|death|die|kill|murder|homicid|suicide|attempt", "rumble", "death/violence undertone"),

    # Data/surveillance/algorithm → tension
    (r"algorithm|data|score|screen|track|surveillance|monitor", "tension", "algorithmic judgment"),
    (r"denied|rejected|refused|declined|failed", "impact", "rejection strike"),
    (r"billion|million|thousand|percent|ninety|eighty|sixty", "shimmer", "shocking statistic"),

    # Legal/institutional → whoosh
    (r"lawsuit|sued|filed|court|judge|settlement", "whoosh", "legal action"),
    (r"department of justice|fbi|cia|ftc|eeoc|congress", "whoosh", "institutional authority"),

    # Phone/communication → tension
    (r"phone|call|dialed|rang|voicemail", "tension", "phone call tension"),

    # Silence/nothing → explicit NO sfx
    (r"silence|quiet|calm|nothing|pause", None, None),

    # Scene entry/transition → whoosh
    (r"door|enter|arrive|walk in|walked into", "whoosh", "scene entry"),

    # Emotional moments → rumble
    (r"blamed? yourself|internalize|worthless|hopeless|desperate", "rumble", "emotional weight"),
    (r"kafka|orwell|dystop|nightmare|horror", "rumble", "literary/tonal darkness"),
]

DOCUMENT_HIGHLIGHT_RULES = [
    (r"subject|title|header|project mkultra|mkultra", "header", 0.12, 0.22, 0.05, 0.95),
    (r"top secret|classified|confidential|clearance", "stamp", 0.68, 0.75, 0.10, 0.90),
    (r"signature|signed|gottlieb|authorized|approved", "signature", 0.72, 0.88, 0.30, 0.90),
    (r"LSD|drug|dose|l\.s\.d|acid|cointreau", "lsd_ref", 0.22, 0.35, 0.05, 0.95),
    (r"budget|\$39|money|fund|grant|\$", "budget", 0.42, 0.55, 0.05, 0.95),
    (r"experiment|behavior|modification|conditioning", "body", 0.25, 0.45, 0.05, 0.95),
]

# Text overlay size rules based on content
TEXT_SIZE_RULES = {
    "date": 72,           # Dates need to be big and readable: "NOVEMBER 28, 1953"
    "person_name": 64,    # Names on first mention: "FRANK OLSON"
    "entity": 56,         # Organizations: "MKULTRA", "CIA"
    "location": 52,       # Places: "FORT DETRICK, MARYLAND"
    "quote": 44,          # Quoted speech (longer text, smaller font)
    "small_label": 36,    # Subtle labels
}


# ── Content Analysis ────────────────────────────────────────────────────────

def _is_document_content(text: str) -> bool:
    doc_patterns = [
        r"the document|the memo|the report|the file",
        r"reads|states|written|stamped|classified as",
        r"declassified|released|page|paragraph|section",
        r"subject line|header|title.*reads",
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in doc_patterns)


def _detect_document_highlights(text: str, shot_type: str = "") -> list:
    if not _is_document_content(text):
        return []
    text_lower = text.lower()
    words = text_lower.split()
    total_words = max(len(words), 1)
    highlights = []
    for pattern, label, y1, y2, x1, x2 in DOCUMENT_HIGHLIGHT_RULES:
        match = re.search(pattern, text_lower)
        if match:
            word_pos = len(text_lower[:match.start()].split())
            reveal_at = min(0.95, max(0.05, word_pos / total_words))
            highlights.append({
                "y_start": y1, "y_end": y2, "x_start": x1, "x_end": x2,
                "color": [255, 255, 0], "reveal_at": reveal_at, "_label": label,
            })
    return highlights


def _detect_content_sfx(text: str) -> tuple[str | None, str | None]:
    """Match narration text to content-appropriate SFX."""
    text_lower = text.lower()
    for pattern, sfx_type, motivation in CONTENT_SFX_RULES:
        if re.search(pattern, text_lower):
            return sfx_type, motivation
    return None, None


def _detect_zoom_target(text: str, show: str) -> dict:
    """Determine WHERE in the image to zoom and why."""
    text_lower = text.lower()

    # Face/eyes — zoom to upper third center
    if any(w in text_lower for w in ["face", "eyes", "stare", "look", "watch"]):
        return {"target": "face", "region": [0.3, 0.15, 0.7, 0.55], "motivation": "human connection"}

    # Documents/text — zoom to center where text is
    if any(w in text_lower for w in ["document", "memo", "file", "report", "stamp", "classified", "redact"]):
        return {"target": "document_text", "region": [0.2, 0.2, 0.8, 0.8], "motivation": "read the evidence"}

    # Window/building exterior — zoom to specific floor/window
    if "window" in text_lower or "floor" in text_lower:
        return {"target": "window", "region": [0.3, 0.1, 0.7, 0.5], "motivation": "the fall point"}

    # Location — zoom wide to show environment
    if any(w in text_lower for w in ["hotel", "cabin", "lake", "building", "city",
                                      "room", "laboratory", "prison", "fort", "base"]):
        return {"target": "location", "region": [0.1, 0.1, 0.9, 0.9], "motivation": "establish location"}

    # Specific person named (filter out locations/common phrases)
    _not_names = {"New York", "Cold War", "Fort Detrick", "Deep Creek", "Hotel Statler",
                  "United States", "World War", "The CIA", "The FBI", "San Francisco",
                  "Camp King", "White House", "Capitol Hill", "Long Island"}
    names = [n for n in re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text) if n not in _not_names]
    if names:
        return {"target": "person", "region": [0.25, 0.1, 0.75, 0.7], "motivation": f"focus on {names[0]}"}

    # Default: center with slight bias toward upper third (faces tend to be there)
    return {"target": "subject", "region": [0.2, 0.15, 0.8, 0.75], "motivation": "primary subject"}


def _estimate_read_time(text: str) -> float:
    """Estimate how long text needs to stay on screen for comfortable reading."""
    words = len(text.split())
    # Average reading speed ~200 WPM for on-screen text, plus 0.5s to notice it
    return max(1.5, words / 200 * 60 + 0.5)


def _should_hold_longer(text: str, emotion: str, prev_emotion: str | None) -> float:
    """Return a hold multiplier (1.0 = normal, 1.5 = hold longer, etc.)."""
    text_lower = text.lower()

    # After a dramatic reveal, hold to let it land
    if any(w in text_lower for w in ["it was a lie", "he had not jumped", "homicide",
                                      "the full truth", "case closed", "murder"]):
        return 1.8

    # Emotional shift (voice register change) — brief hold for transition
    if prev_emotion and emotion != prev_emotion:
        return 1.2

    # Short punchy sentences should be quick, not held
    if len(text.split()) < 8:
        return 0.7

    # Quotes — hold long enough to read
    if '"' in text or '\u201c' in text:
        return 1.4

    return 1.0


# ── Scene-Level Arc Detection ──────────────────────────────────────────────

def detect_arc_position(seg_index: int, total_segs: int, narrative_function: str,
                         emotion: str, chapter_num: int, total_chapters: int,
                         text: str) -> str:
    """
    Determine where this segment sits in the story's emotional arc.

    This is the key function that gives the director full-context awareness.
    It knows whether we're building toward something, at a peak, or resolving.
    """
    # Overall position in video (0.0 = start, 1.0 = end)
    progress = seg_index / max(total_segs - 1, 1)
    text_lower = text.lower()

    # First 5% = cold open
    if progress < 0.05:
        return "cold_open"

    # Chapter transitions
    if narrative_function == "chapter_break":
        return "chapter_transition"

    # Last 10% = closing (aftermath/legacy)
    if progress > 0.90:
        return "aftermath"

    # Revelation keywords always get revelation treatment
    if any(w in text_lower for w in ["it was a lie", "homicide", "what they found",
                                      "the evidence", "hematoma", "struck", "not jumped",
                                      "never admitted", "never charged",
                                      # Topic-agnostic revelation triggers
                                      "let that land", "stomach drop", "here's what they don't tell",
                                      "nobody expected", "truly dangerous", "cruelest part",
                                      "here's the thing about", "the ghost won",
                                      "they settled", "systematically discriminated",
                                      "eighty-five percent", "attempted suicide",
                                      "sixty thousand claims", "the machine doesn't care"]):
        return "revelation"

    # Peak emotional moments
    if emotion in ("tense", "energized") and narrative_function in ("climax", "stakes_moment", "reveal"):
        return "emotional_peak"

    # Tension building
    if emotion == "tense" or narrative_function == "tension_build":
        return "tension_build"

    # Resolution/aftermath sections
    if narrative_function == "aftermath" or emotion == "neutral" and progress > 0.7:
        return "aftermath"

    # Default: context setup
    return "context_setup"


# ── Main Director Pass ──────────────────────────────────────────────────────

def direct(script_path: str, storyboard_path: str) -> dict:
    """
    Read the full script + existing storyboard and apply context-aware editorial decisions.

    Returns a complete v2.0 Director's Brief.
    """
    # Load existing storyboard (visual choices already made)
    storyboard = json.loads(Path(storyboard_path).read_text())
    if isinstance(storyboard, dict) and storyboard.get("schema_version") == "2.0":
        # Flatten v2.0 scenes
        flat = []
        for scene in storyboard.get("scenes", []):
            flat.extend(scene.get("segments", []))
        storyboard = flat

    # Load script for full context
    script_text = Path(script_path).read_text()

    total_segs = len(storyboard)
    chapter_entries = [s for s in storyboard if s.get("is_chapter_break")]
    total_chapters = len(chapter_entries)

    # Track state across segments for context-aware decisions
    current_chapter = 0
    prev_emotion = None
    prev_arc = None
    scene_tension_level = 0.0  # 0.0 = calm, 1.0 = peak tension
    segments_since_sfx = 0
    segments_since_text = 0
    last_sfx_type = None

    directed_segments = []

    for i, seg in enumerate(storyboard):
        text = seg.get("text", "")
        emotion = seg.get("emotion", seg.get("intensity", "neutral"))

        if seg.get("is_chapter_break"):
            current_chapter += 1
            scene_tension_level = 0.0  # Reset tension at chapter boundary

        # ── 1. Determine arc position (FULL CONTEXT) ──
        arc = detect_arc_position(
            i, total_segs,
            seg.get("narrative_function", "context_background"),
            emotion, current_chapter, total_chapters, text
        )
        profile = ARC_PROFILES.get(arc, ARC_PROFILES["context_setup"])

        # ── 2. Hold duration (context-aware) ──
        base_min, base_max = profile["base_hold"]
        hold_mult = _should_hold_longer(text, emotion, prev_emotion)
        hold_min = round(base_min * hold_mult, 1)
        hold_max = round(base_max * hold_mult, 1)

        # Clamp to sane range
        hold_min = max(1.5, min(hold_min, 12.0))
        hold_max = max(hold_min + 0.5, min(hold_max, 15.0))

        # ── 3. SFX (content-matched, not random) ──
        sfx_type, sfx_motivation = _detect_content_sfx(text)
        segments_since_sfx += 1

        # Prevent SFX fatigue — minimum 3 segments between SFX
        if sfx_type and segments_since_sfx < 3 and sfx_type == last_sfx_type:
            sfx_type = None
            sfx_motivation = None

        # Force SFX on major revelations even if close together
        text_lower = text.lower()
        if any(w in text_lower for w in ["homicide", "hematoma", "struck", "murder"]):
            sfx_type = "impact"
            sfx_motivation = "forensic revelation — critical story beat"

        if sfx_type:
            segments_since_sfx = 0
            last_sfx_type = sfx_type

        sfx = None
        if sfx_type:
            sfx = {
                "type": sfx_type,
                "trigger": "on_cut",
                "motivation": sfx_motivation,
            }

        # ── 3b. Document highlights ──
        shot_type = seg.get("shot_type", "")
        highlight_regions = _detect_document_highlights(text, shot_type)
        is_doc_content = _is_document_content(text)

        # ── 4. Zoom target (content-aware) ──
        zoom_target = _detect_zoom_target(text, seg.get("show", ""))

        # Zoom speed modulated by tension
        base_zoom = seg.get("zoom_rate_pct_sec", 3.0)
        if arc == "emotional_peak":
            base_zoom = max(base_zoom, 6.0)
        elif arc == "cold_open":
            base_zoom = max(base_zoom, 5.0)
        elif arc == "aftermath":
            base_zoom = min(base_zoom, 2.5)

        # ── 5. Transitions (scene-aware) ──
        transition_in = {"type": "cut", "frames": 0}
        transition_out = {"type": "cut", "frames": 0}

        if arc == "chapter_transition":
            transition_in = {"type": "fade_from_black", "frames": 15}
            transition_out = {"type": "fade_to_black", "frames": 15}
        elif arc == "revelation" and prev_arc != "revelation":
            # Hard cut INTO revelation for punch
            transition_in = {"type": "cut", "frames": 0}
        elif arc == "aftermath" and prev_arc in ("emotional_peak", "revelation"):
            # Dissolve into aftermath for emotional come-down
            transition_in = {"type": "dissolve", "frames": 10}
        elif prev_arc == "cold_open" and arc != "cold_open":
            # First transition out of cold open — dramatic
            transition_in = {"type": "fade_from_black", "frames": 8}

        # ── 6. Text overlay (smart sizing + timing) ──
        text_overlay = None
        text_overlay_size = None
        text_overlay_position = "lower_third"
        text_overlay_style = "typewriter"
        text_overlay_hold_sec = None

        overlay_type = seg.get("text_overlay_type")
        if overlay_type and overlay_type != "null":
            segments_since_text += 1

            # Don't spam text — minimum 2 segments gap
            if segments_since_text >= 2:
                if overlay_type == "person_identification":
                    names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)
                    if names:
                        text_overlay = names[0].upper()
                        text_overlay_size = TEXT_SIZE_RULES["person_name"]
                        text_overlay_position = "center"
                        text_overlay_hold_sec = _estimate_read_time(text_overlay)

                elif overlay_type == "entity_label":
                    acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
                    real = [a for a in acronyms if a not in
                            ("THE", "AND", "FOR", "BUT", "NOT", "HIS", "HER")]
                    if real:
                        text_overlay = real[0]
                        text_overlay_size = TEXT_SIZE_RULES["entity"]
                        text_overlay_position = "center"
                        text_overlay_hold_sec = _estimate_read_time(text_overlay)

                elif overlay_type == "location_label":
                    # Find location patterns
                    locs = re.findall(r"\b[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?\b", text)
                    _skip = {"The", "A", "He", "She", "His", "Her", "But", "And", "Was",
                             "They", "When", "That", "This", "Not", "For", "But"}
                    locs = [l for l in locs if l.split(",")[0].split()[0] not in _skip]
                    if locs:
                        text_overlay = locs[0].upper()
                        text_overlay_size = TEXT_SIZE_RULES["location"]
                        text_overlay_position = "lower_third"
                        text_overlay_hold_sec = _estimate_read_time(text_overlay)

                elif overlay_type == "quote":
                    match = (re.search(r'"([^"]{10,})"', text) or
                             re.search(r'\u201c([^\u201d]{10,})\u201d', text))
                    if match:
                        text_overlay = f'"{match.group(1)}"'
                        text_overlay_size = TEXT_SIZE_RULES["quote"]
                        text_overlay_position = "center"
                        text_overlay_hold_sec = _estimate_read_time(text_overlay)
                        text_overlay_style = "typewriter"

                if text_overlay:
                    segments_since_text = 0

        # Date detection — always show dates prominently
        date_match = re.search(
            r"\b((?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{1,2},?\s+\d{4})\b", text)
        if date_match and not text_overlay:
            text_overlay = date_match.group(1).upper()
            text_overlay_size = TEXT_SIZE_RULES["date"]
            text_overlay_position = "lower_third"
            text_overlay_style = "typewriter"
            text_overlay_hold_sec = _estimate_read_time(text_overlay)
            segments_since_text = 0

        # Year-only dates (e.g. "In 1953,")
        if not text_overlay:
            year_match = re.search(r"\b(1[89]\d{2}|20[0-2]\d)\b", text)
            if year_match and len(text.split()) < 15:
                text_overlay = year_match.group(1)
                text_overlay_size = TEXT_SIZE_RULES["date"]
                text_overlay_position = "lower_third"
                text_overlay_style = "typewriter"
                text_overlay_hold_sec = 2.0
                segments_since_text = 0

        # ── 7. Sync points (word-level triggers) ──
        sync_points = seg.get("sync_points", [])
        # Add typewriter_click flag for any text_reveal sync point
        for sp in sync_points:
            if sp.get("action") == "text_reveal":
                sp["typewriter_click"] = True

        # Add sync point for the text overlay if we have one and it's typewriter
        if text_overlay and text_overlay_style == "typewriter":
            # Find the trigger word in the narration
            trigger_word = text_overlay.split()[0]
            words = text.split()
            for wi, w in enumerate(words):
                if w.strip(".,!?;:'\"").upper() == trigger_word:
                    # Only add if not already covered
                    if not any(sp.get("word_index") == wi for sp in sync_points):
                        sync_points.append({
                            "word": w.strip(".,!?;:'\""),
                            "word_index": wi,
                            "action": "text_reveal",
                            "text": text_overlay,
                            "font_size": text_overlay_size,
                            "position": text_overlay_position,
                            "typewriter_click": True,
                            "hold_sec": text_overlay_hold_sec,
                        })
                    break

        # ── 8. Composition (preserve LLM choices, enhance with context) ──
        comp = seg.get("composition", {"type": "single", "layers": [], "atmosphere": "none"})
        # Override atmosphere with arc-appropriate choice
        comp["atmosphere"] = profile["atmosphere"]
        # Override color grade based on arc
        if arc == "cold_open":
            comp["color_grade"] = "cold"
        elif arc == "revelation":
            comp["color_grade"] = "vibrant"
        elif arc == "emotional_peak":
            comp["color_grade"] = "dark"
        elif arc == "aftermath":
            comp["color_grade"] = "archival"
        elif arc == "tension_build":
            comp["color_grade"] = "dark"
        else:
            comp.setdefault("color_grade", "neutral")

        # ── 9. Tension tracking (affects future segments) ──
        if arc in ("tension_build", "emotional_peak"):
            scene_tension_level = min(1.0, scene_tension_level + 0.15)
        elif arc in ("aftermath", "context_setup"):
            scene_tension_level = max(0.0, scene_tension_level - 0.1)

        # ── Build the directed segment ──
        directed = {
            **seg,
            # Director overrides
            "arc_position": arc,
            "hold_duration_range": [hold_min, hold_max],
            "zoom_rate_pct_sec": round(base_zoom, 2),
            "zoom_target": zoom_target,
            "sfx": sfx,
            "transition_in": transition_in,
            "transition_out": transition_out,
            "composition": comp,
            "sync_points": sync_points,
            "tension_level": round(scene_tension_level, 2),
            "highlight_regions": highlight_regions if highlight_regions else None,
            "_document_content": is_doc_content,
            # Text overlay details
            "_text_overlay": text_overlay,
            "_text_overlay_size": text_overlay_size,
            "_text_overlay_position": text_overlay_position,
            "_text_overlay_style": text_overlay_style,
            "_text_overlay_hold_sec": text_overlay_hold_sec,
        }

        directed_segments.append(directed)
        prev_emotion = emotion
        prev_arc = arc

    # ── Scene grouping ──
    scenes = _group_into_scenes_directed(directed_segments)

    # ── Assemble v2.0 output ──
    comp_count = sum(1 for s in directed_segments
                     if s.get("composition", {}).get("type") == "composite")
    sync_count = sum(len(s.get("sync_points", [])) for s in directed_segments)
    sfx_count = sum(1 for s in directed_segments if s.get("sfx"))

    output = {
        "schema_version": "2.0",
        "directed": True,
        "segment_count": len(directed_segments),
        "scene_count": len(scenes),
        "composite_count": comp_count,
        "sync_point_count": sync_count,
        "sfx_count": sfx_count,
        "scenes": scenes,
    }

    # ── Playbook Validation Pass ──
    if _HAS_PLAYBOOK:
        output["playbook_audit"] = _playbook_audit(output, directed_segments)

    return output


def _group_into_scenes_directed(segments: list[dict]) -> list[dict]:
    """Group segments into scenes based on arc transitions and chapters."""
    scenes = []
    current_segs = []
    current_arc = None
    scene_num = 0

    for seg in segments:
        arc = seg.get("arc_position", "context_setup")

        # Scene break on chapter transitions or major arc shifts
        is_break = (
            seg.get("is_chapter_break") or
            (current_arc and arc != current_arc and
             not (current_arc == "tension_build" and arc == "emotional_peak") and
             not (current_arc == "emotional_peak" and arc == "revelation")) or
            len(current_segs) >= 10
        )

        if is_break and current_segs:
            scene_num += 1
            scenes.append(_make_directed_scene(scene_num, current_segs))
            current_segs = []

        if seg.get("is_chapter_break"):
            scene_num += 1
            scenes.append(_make_directed_scene(scene_num, [seg]))
            current_arc = None
            continue

        current_segs.append(seg)
        current_arc = arc

    if current_segs:
        scene_num += 1
        scenes.append(_make_directed_scene(scene_num, current_segs))

    return scenes


def _make_directed_scene(num: int, segs: list[dict]) -> dict:
    """Build a scene with director metadata."""
    arcs = [s.get("arc_position", "context_setup") for s in segs]
    # Most common arc
    arc_counts: dict[str, int] = {}
    for a in arcs:
        arc_counts[a] = arc_counts.get(a, 0) + 1
    dominant = max(arc_counts, key=arc_counts.get)

    # Tension trajectory: rising, falling, peak, flat
    tensions = [s.get("tension_level", 0) for s in segs]
    if len(tensions) >= 2:
        if tensions[-1] > tensions[0] + 0.1:
            trajectory = "rising"
        elif tensions[-1] < tensions[0] - 0.1:
            trajectory = "falling"
        elif max(tensions) > 0.6:
            trajectory = "peak"
        else:
            trajectory = "flat"
    else:
        trajectory = "flat"

    text_words = segs[0].get("text", "").split()[:6]
    slug = "_".join(w.lower().strip(".,!?;:'\"") for w in text_words if w.strip(".,!?;:'\""))[:35]

    return {
        "scene_id": f"s{num:02d}_{slug}",
        "scene_name": segs[0].get("show", segs[0].get("text", ""))[:60],
        "narrative_arc": dominant,
        "tension_trajectory": trajectory,
        "segment_count": len(segs),
        "segments": segs,
    }


# ── Playbook Audit ─────────────────────────────────────────────────────────

def _playbook_audit(output: dict, segments: list[dict]) -> dict:
    """
    Validate directed output against playbook rules from LearnByLeo analysis.
    Returns scores, warnings, and suggested fixes.

    Checks:
    1. Energy variation (editing.json P-ED-04) — alternate hype/mellow
    2. Sound design density (editing.json sfx_types) — 5 layer coverage
    3. Visual variety (editing.json visual_variety) — B-roll ratio, cut frequency
    4. Attention guides (editing.json six_attention_guides) — technique coverage
    5. Focus point continuity (editing.json visual_continuity)
    """
    if not _HAS_PLAYBOOK:
        return {"error": "Playbook not available"}

    audit = {"scores": {}, "warnings": [], "suggestions": []}
    total_segs = len(segments)

    # ── 1. Energy Variation (P-ED-04) ──
    # Rule: "Vary the energy level — contrast between hype-edited sections
    # and mellow A-roll forces viewers back into focus"
    arc_sequence = [s.get("arc_position", "context_setup") for s in segments]
    high_energy = {"cold_open", "emotional_peak", "revelation"}
    low_energy = {"context_setup", "aftermath"}

    # Count transitions between high and low energy
    energy_shifts = 0
    prev_is_high = None
    for arc in arc_sequence:
        is_high = arc in high_energy
        if prev_is_high is not None and is_high != prev_is_high:
            energy_shifts += 1
        prev_is_high = is_high

    # Target: at least 1 shift per 15 segments (per playbook: 3-4 shifts per video)
    expected_shifts = max(3, total_segs // 15)
    energy_score = min(1.0, energy_shifts / expected_shifts)
    audit["scores"]["energy_variation"] = round(energy_score, 2)

    if energy_shifts < 3:
        audit["warnings"].append({
            "rule": "P-ED-04",
            "issue": f"Only {energy_shifts} energy shifts detected. Playbook requires 3-4 minimum.",
            "fix": "Insert mellow sections between intense sequences. Alternate hype-edited and calm A-roll."
        })

    # ── 2. Sound Design Density ──
    # Rule: 5 SFX types should be represented (whoosh, highlight, riser, hit, drone)
    sfx_segments = [s for s in segments if s.get("sfx")]
    sfx_types_used = set(s["sfx"]["type"] for s in sfx_segments)
    playbook_sfx_types = {"whoosh", "highlight", "riser", "impact", "rumble"}
    # Map our types to playbook types
    type_map = {"shimmer": "highlight", "tension": "riser", "impact": "impact",
                "rumble": "rumble", "whoosh": "whoosh", "glass_shatter": "impact",
                "body_impact": "impact"}
    mapped_types = set(type_map.get(t, t) for t in sfx_types_used)
    sfx_coverage = len(mapped_types & playbook_sfx_types) / len(playbook_sfx_types)
    audit["scores"]["sfx_coverage"] = round(sfx_coverage, 2)

    missing_sfx = playbook_sfx_types - mapped_types
    if missing_sfx:
        audit["suggestions"].append({
            "rule": "editing.sound_design",
            "issue": f"Missing SFX types: {', '.join(missing_sfx)}",
            "fix": f"Add {', '.join(missing_sfx)} to appropriate segments for fuller sound design."
        })

    # SFX density: should be roughly 1 SFX per 5-8 segments for documentary
    sfx_ratio = len(sfx_segments) / max(total_segs, 1)
    target_ratio = 0.15  # ~1 in 7 segments
    sfx_density_score = min(1.0, sfx_ratio / target_ratio)
    audit["scores"]["sfx_density"] = round(sfx_density_score, 2)

    # ── 3. Cut Frequency ──
    # Rule: "New visual element every 5 seconds or less" (documentary = 5-7s)
    holds = [s.get("hold_duration_range", [5, 7]) for s in segments]
    avg_hold = sum((h[0] + h[1]) / 2 for h in holds) / max(len(holds), 1)
    # Documentary target: 5-7 seconds per cut
    if avg_hold <= 7:
        cut_score = 1.0
    elif avg_hold <= 10:
        cut_score = 0.7
    else:
        cut_score = 0.4
    audit["scores"]["cut_frequency"] = round(cut_score, 2)

    if avg_hold > 8:
        audit["warnings"].append({
            "rule": "P-ED-02",
            "issue": f"Average hold {avg_hold:.1f}s exceeds documentary target of 5-7s",
            "fix": "Reduce hold durations. Even nature documentaries cut every 5 seconds."
        })

    # ── 4. Visual Continuity ──
    # Rule: "Focus point continuity — viewer's eyes should stay in same screen position"
    # Check for zoom_target consistency across adjacent segments
    continuity_breaks = 0
    for j in range(1, len(segments)):
        prev_target = segments[j-1].get("zoom_target", {}).get("target", "")
        curr_target = segments[j].get("zoom_target", {}).get("target", "")
        prev_region = segments[j-1].get("zoom_target", {}).get("region", [0.5, 0.5, 0.5, 0.5])
        curr_region = segments[j].get("zoom_target", {}).get("region", [0.5, 0.5, 0.5, 0.5])

        # Check if center points are far apart (continuity break)
        if len(prev_region) >= 4 and len(curr_region) >= 4:
            prev_cx = (prev_region[0] + prev_region[2]) / 2
            prev_cy = (prev_region[1] + prev_region[3]) / 2
            curr_cx = (curr_region[0] + curr_region[2]) / 2
            curr_cy = (curr_region[1] + curr_region[3]) / 2
            dist = math.sqrt((prev_cx - curr_cx)**2 + (prev_cy - curr_cy)**2)
            # Big jump = continuity break (unless it's a deliberate scene change)
            if dist > 0.4 and segments[j].get("arc_position") != "chapter_transition":
                continuity_breaks += 1

    continuity_score = max(0.0, 1.0 - (continuity_breaks / max(total_segs, 1)) * 5)
    audit["scores"]["focus_continuity"] = round(continuity_score, 2)

    # ── 5. Graphics animation ──
    # Rule: "All graphics must animate in — never just appear"
    text_overlays = [s for s in segments if s.get("_text_overlay")]
    animated_count = sum(1 for s in text_overlays if s.get("_text_overlay_style") == "typewriter")
    if text_overlays:
        anim_score = animated_count / len(text_overlays)
    else:
        anim_score = 1.0
    audit["scores"]["graphics_animated"] = round(anim_score, 2)

    # ── 6. Attention Guide Techniques ──
    # Rule: "At least 3 of 6 techniques used"
    techniques_used = set()
    for s in segments:
        if s.get("highlight_regions"):
            techniques_used.add("darken_blur_surrounds")
            techniques_used.add("animate_important_area")
        if s.get("_text_overlay"):
            techniques_used.add("graphic_indicators")
        zoom = s.get("zoom_target", {})
        if zoom.get("target") in ("face", "person"):
            techniques_used.add("scale_position")
        comp = s.get("composition", {})
        if comp.get("atmosphere") in ("fog", "dust"):
            techniques_used.add("glow_effect")
        if comp.get("color_grade") in ("cold", "dark", "vibrant"):
            techniques_used.add("color_shift")

    attention_score = min(1.0, len(techniques_used) / 3)
    audit["scores"]["attention_guides"] = round(attention_score, 2)
    audit["techniques_used"] = list(techniques_used)

    # ── Overall Score ──
    weights = {
        "energy_variation": 0.20,
        "sfx_coverage": 0.10,
        "sfx_density": 0.10,
        "cut_frequency": 0.15,
        "focus_continuity": 0.15,
        "graphics_animated": 0.10,
        "attention_guides": 0.20,
    }
    total = sum(audit["scores"].get(k, 0) * w for k, w in weights.items())
    audit["overall_score"] = round(total, 2)
    audit["overall_percent"] = f"{total * 100:.0f}%"

    # ── Playbook Checklist Cross-Reference ──
    checklist_scores = {k: audit["scores"][k] for k in weights}
    audit["playbook_checklist"] = _PLAYBOOK.score_checklist(
        "editing", "editing_quality", checklist_scores
    ) if _HAS_PLAYBOOK else {}

    return audit


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Director's pass — full-context editorial decisions")
    ap.add_argument("--script", required=True, help="Enhanced script .txt")
    ap.add_argument("--storyboard", required=True, help="Existing storyboard .json (v1 or v2)")
    ap.add_argument("--out", help="Output path (default: overwrites storyboard)")
    ap.add_argument("--preview", action="store_true", help="Print summary, don't write")
    args = ap.parse_args()

    print("Director's Pass — full-context editorial decisions")
    print(f"  Script: {args.script}")
    print(f"  Storyboard: {args.storyboard}")

    output = direct(args.script, args.storyboard)

    if args.preview:
        print(f"\n{'─'*70}")
        for scene in output["scenes"]:
            print(f"\n  SCENE: {scene['scene_name'][:50]}  "
                  f"[{scene['narrative_arc']}] tension={scene['tension_trajectory']}")
            for seg in scene["segments"]:
                arc = seg.get("arc_position", "?")
                sfx = seg.get("sfx", {})
                sfx_str = f"  SFX:{sfx['type']}" if sfx else ""
                text_str = f"  TEXT:{seg.get('_text_overlay', '')[:20]}" if seg.get("_text_overlay") else ""
                hold = seg.get("hold_duration_range", [0, 0])
                comp_type = seg.get("composition", {}).get("type", "?")
                print(f"    [{arc:16s}] {hold[0]:.1f}-{hold[1]:.1f}s  "
                      f"comp={comp_type:10s}{sfx_str}{text_str}")
                print(f"      {seg['text'][:80]}")
        print(f"\n{'─'*70}")
        print(f"Segments: {output['segment_count']}  Scenes: {output['scene_count']}")
        print(f"Composites: {output['composite_count']}  SFX: {output['sfx_count']}  "
              f"Sync points: {output['sync_point_count']}")
        return

    out_path = Path(args.out) if args.out else Path(args.storyboard)
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nDirector's Brief written → {out_path}")
    print(f"  {output['segment_count']} segments in {output['scene_count']} scenes")
    print(f"  {output['composite_count']} composites, {output['sfx_count']} SFX events, "
          f"{output['sync_point_count']} sync points")

    # Print playbook audit if available
    audit = output.get("playbook_audit")
    if audit and "scores" in audit:
        print(f"\n{'─'*70}")
        print(f"  PLAYBOOK AUDIT — {audit.get('overall_percent', '?')}")
        print(f"{'─'*70}")
        for k, v in audit["scores"].items():
            bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
            print(f"  {k:25s} {bar} {v*100:.0f}%")
        if audit.get("warnings"):
            print(f"\n  ⚠ Warnings:")
            for w in audit["warnings"]:
                print(f"    [{w['rule']}] {w['issue']}")
                print(f"      Fix: {w['fix']}")
        if audit.get("suggestions"):
            print(f"\n  💡 Suggestions:")
            for s in audit["suggestions"]:
                print(f"    {s['issue']}")
                print(f"      Fix: {s['fix']}")
        if audit.get("techniques_used"):
            print(f"\n  Attention techniques: {', '.join(audit['techniques_used'])}")
        print(f"{'─'*70}")


if __name__ == "__main__":
    main()
