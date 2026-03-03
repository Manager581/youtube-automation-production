#!/usr/bin/env python3
"""
script_enhancer.py — Transform a raw script into Fern-style narration with
emotion markers, strategic pauses, and pacing matched to 138.7 WPM.

Uses Ollama (local, 100% free) by default.
No API key needed. No internet required.

TIP: For one-off scripts, just paste the raw text into Claude Code and ask:
     "Enhance this script to Fern style with [BEAT], [PAUSE], [VOICE] markup"
     — that's free via your Max subscription and gives the best quality.

Usage:
  # Enhance with default local model (requires Ollama running)
  venv/bin/python pipeline/script_enhancer.py \
    --input scripts/raw_script.txt \
    --output scripts/enhanced.txt

  # Preview result in terminal
  venv/bin/python pipeline/script_enhancer.py \
    --input scripts/raw_script.txt \
    --preview

  # Specify a different local model
  venv/bin/python pipeline/script_enhancer.py \
    --input scripts/raw_script.txt \
    --model qwen2.5:32b

  # Full pipeline
  venv/bin/python pipeline/script_enhancer.py --input scripts/raw.txt --output scripts/enhanced.txt && \
  venv/bin/python pipeline/voice_generator.py \
    --ref-neutral assets/voice/voice_neutral.wav \
    --ref-tense   assets/voice/voice_tense.wav \
    --auto-transcribe --script scripts/enhanced.txt --out audio/narration.wav

Starting Ollama if not running:
  ollama serve &
  ollama pull qwen3.5:27b   # 17GB — recommended for M5 24GB (best quality)
  ollama pull qwen3.5:4b    # 3.4GB — faster fallback
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Fern production spec (from our measured analysis of 3 videos)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a script editor specialized in transforming documentary narration
into Fern-channel style with emotion markup for a voice synthesis system.

FERN CHANNEL — MEASURED PRODUCTION DATA (3 videos analyzed):
- Target WPM: 138.7 (range 127–151 across sections)
- Emotional tone: 31.5% tense, 15.7% ominous, rest informational
- Topics: dark history, government conspiracies, crimes, historical disasters
- Narrative structure: hook → context → rising tension → reveal → aftermath

FERN SCRIPT STYLE:
- Opens with a dramatic present-tense hook (1–3 sentences, no "hey everyone")
- Uses "In [year]..." transitions for timeline facts
- Short sentences (5–8 words) for key reveals — the reveal line is ALWAYS short
- Longer sentences for background/context
- Never uses "you" (not tutorial tone) — speaks to a wide audience
- Ellipses (...) before reveals and key facts
- Em-dashes (—) for asides and interruptions
- Never ends sections with filler like "let's get into it"

MARKUP TAGS TO INJECT:
  [VOICE:neutral]   — factual background, context, timelines
  [VOICE:tense]     — horror, revelations, consequences
  [VOICE:energized] — opening hook, major payoffs, final lines

  [BEAT]       — 0.3s pause: after a key fact before moving to next thought
  [PAUSE:0.8]  — 0.8s pause: before a major reveal sentence
  [PAUSE:1.2]  — 1.2s pause: after the most shocking line in a section
  [BREATH]     — 0.15s pause: natural breath (use sparingly)

OUTPUT:
- Output ONLY the enhanced script text
- No preamble, no commentary, no markdown code fences
- Preserve ALL factual content — do not add or remove facts
- Every section must start with a [VOICE:register] tag
"""

USER_PROMPT = """Enhance this script for Fern-style narration with emotion markup.
Preserve all facts exactly. Add [VOICE:], [BEAT], [PAUSE:N], [BREATH] tags.
Rewrite sentence structure to match Fern's rhythm.
Output the enhanced script only.

SCRIPT:
{script}"""


# ---------------------------------------------------------------------------
# Ollama backend (free, local)
# ---------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.5:27b"


def _ollama_available() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def _ollama_models() -> list[str]:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as r:
            data = json.loads(r.read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _best_available_model(preferred: str) -> str:
    """Pick the best available model from what's pulled."""
    models = _ollama_models()
    if not models:
        return preferred

    # Preference order for script quality (text-only models, no VL variants)
    candidates = [preferred, "qwen3.5:27b", "qwen3.5:4b", "qwen2.5:32b",
                  "qwen2.5:14b", "qwen2.5:7b", "gpt-oss:20b", "llama3.1:8b"]
    for c in candidates:
        # Check prefix match (model names include :tag)
        for m in models:
            if m.startswith(c.split(":")[0]):
                return m
    return models[0]  # fallback to whatever is available


def enhance_with_ollama(raw_script: str, model: str = DEFAULT_MODEL) -> str:
    """Call local Ollama to enhance the script. Returns enhanced text."""
    if not _ollama_available():
        raise ConnectionError(
            "Ollama is not running.\n"
            "Start it with:  ollama serve\n"
            "Then pull a model:  ollama pull qwen2.5:32b"
        )

    actual_model = _best_available_model(model)
    if actual_model != model:
        print(f"  Model '{model}' not found — using '{actual_model}'")

    print(f"  Enhancing with Ollama ({actual_model})...")

    payload = json.dumps({
        "model": actual_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": USER_PROMPT.format(script=raw_script.strip())},
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 8192,
        }
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read())
    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama request failed: {e}")

    return data["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_markup(script: str) -> list[str]:
    """Check the enhanced script has expected markup. Returns warnings."""
    import re
    warnings = []
    if "[VOICE:" not in script:
        warnings.append("No [VOICE:] tags — emotional register switching won't work")
    if "[BEAT]" not in script and "[PAUSE:" not in script:
        warnings.append("No pause markers — delivery will have no strategic pauses")
    if "..." not in script and "—" not in script:
        warnings.append("No ellipses or em-dashes — rhythm may feel flat")
    return warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Enhance a raw script to Fern-style with emotion markup (free, local via Ollama)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--input",   required=False, help="Raw script .txt file")
    p.add_argument("--output",  default=None,  help="Output path (default: input_enhanced.txt)")
    p.add_argument("--preview", action="store_true", help="Print enhanced script to terminal")
    p.add_argument("--model",   default=DEFAULT_MODEL,
                   help=f"Ollama model (default: {DEFAULT_MODEL})")
    p.add_argument("--list-models", action="store_true",
                   help="List available Ollama models and exit")
    # Make --input optional when just listing models
    p.set_defaults(input=None)
    args = p.parse_args()

    if args.list_models or not args.input:
        models = _ollama_models()
        if models:
            print("Available Ollama models:")
            for m in models:
                print(f"  {m}")
        else:
            print("No models found / Ollama not running. Start with: ollama serve")
        if not args.input:
            print("\nProvide --input <script.txt> to enhance a script.")
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input not found: {input_path}")
        sys.exit(1)

    raw_script = input_path.read_text().strip()
    if not raw_script:
        print("ERROR: Input script is empty")
        sys.exit(1)

    output_path = Path(args.output) if args.output else \
        input_path.parent / (input_path.stem + "_enhanced.txt")

    print(f"\nScript Enhancer (local Ollama — free)")
    print(f"  Input : {input_path} ({len(raw_script.split())} words)")
    print(f"  Output: {output_path}")
    print(f"  Model : {args.model}\n")

    try:
        enhanced = enhance_with_ollama(raw_script, model=args.model)
    except ConnectionError as e:
        print(f"\nERROR: {e}")
        print("\nAlternative: paste your script into Claude Code and ask:")
        print('  "Enhance this script to Fern style with [BEAT], [PAUSE], [VOICE] markup"')
        sys.exit(1)

    warnings = validate_markup(enhanced)
    if warnings:
        print("\n  Warnings:")
        for w in warnings:
            print(f"    ! {w}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(enhanced)
    print(f"\n  Saved: {output_path}")

    if args.preview:
        print("\n" + "=" * 60)
        print("ENHANCED SCRIPT")
        print("=" * 60)
        print(enhanced)
        print("=" * 60)

    print(f"\nNext step:")
    print(f"  venv/bin/python pipeline/voice_generator.py \\")
    print(f"    --ref-neutral  assets/voice/voice_neutral.wav \\")
    print(f"    --ref-tense    assets/voice/voice_tense.wav \\")
    print(f"    --auto-transcribe \\")
    print(f"    --script {output_path} \\")
    print(f"    --out audio/narration.wav")


if __name__ == "__main__":
    main()
