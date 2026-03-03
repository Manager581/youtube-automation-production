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

        # Detect chapter breaks
        if re.match(r"^\[PAUSE:\d", para):
            pause_match = re.match(r"^\[PAUSE:([\d.]+)\](.*)$", para, re.DOTALL)
            if pause_match:
                title_text = pause_match.group(2).strip()
                chapter_num += 1
                segments.append({
                    "text": title_text or f"Chapter {chapter_num}",
                    "emotion": current_emotion,
                    "is_chapter_break": True,
                    "chapter_num": chapter_num,
                    "chapter_title": title_text or f"Chapter {chapter_num}",
                })
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
        "options": {"temperature": 0.3, "num_predict": 200},
    }).encode()
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data.get("response", "").strip()
    except Exception:
        return None


# ── Visual brief generation ───────────────────────────────────────────────────

STORYBOARD_PROMPT = """You are a documentary video editor working in the style of @fern-tv on YouTube.
Your job: given one sentence of narration, decide what specific image should appear on screen.

Rules:
- Be SPECIFIC. Not "a document" but "the original 1973 FBI memo with CONFIDENTIAL stamp visible"
- Not "a person" but "Ted Kaczynski's Harvard ID photo, 1958, young face"
- The visual should ILLUSTRATE the exact fact or emotion being stated
- Prefer documents, photos, maps, archival footage over generic stock
- If the narration says a name → show that person's face or their work
- If the narration says a date → show something from that date
- If the narration describes a location → show that location

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
  "narrative_function": "hook_opening | context_background | character_intro | tension_build | reveal | stakes_moment | climax | aftermath"
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
        return {
            **segment,
            "show": "chapter card — black screen with chapter title",
            "search_query": None,
            "focal_element": None,
            "shot_type": "chapter_card",
            "intensity": segment.get("emotion", "neutral"),
            "narrative_function": "chapter_break",
        }

    text = segment["text"]
    emotion = segment.get("emotion", "neutral")

    # Cache check
    if use_cache:
        CACHE_DIR.mkdir(exist_ok=True)
        cache_file = CACHE_DIR / f"{_cache_key(text, emotion, model)}.json"
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text())
                return {**segment, **cached, "_cached": True}
            except json.JSONDecodeError:
                pass

    # Build prompt
    prompt = STORYBOARD_PROMPT.replace("{TEXT}", text).replace("{EMOTION}", emotion)

    response = _ollama_generate(model, prompt)

    if not response:
        brief = _fallback_brief(text, emotion)
    else:
        brief = _parse_ollama_response(response, text, emotion)

    # Cache result
    if use_cache and brief:
        cache_file.write_text(json.dumps(brief))

    return {**segment, **brief}


def _parse_ollama_response(response: str, text: str, emotion: str) -> dict:
    """Parse JSON from ollama response, with fallback."""
    # Extract JSON block
    match = re.search(r"\{[\s\S]*?\}", response)
    if match:
        try:
            data = json.loads(match.group())
            # Validate required fields (narrative_function optional — added field, older caches lack it)
            required = {"show", "search_query", "focal_element", "shot_type", "intensity"}
            if required.issubset(data.keys()):
                result = {k: data[k] for k in required}
                if "narrative_function" in data:
                    result["narrative_function"] = data["narrative_function"]
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

    return {
        "show": show,
        "search_query": query,
        "focal_element": focal,
        "shot_type": shot_type,
        "intensity": emotion,
        "narrative_function": narrative_function,
    }


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
