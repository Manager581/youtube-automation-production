#!/usr/bin/env python3
"""
Soundbite Index — the inversion layer.

READS existing transcripts (no Whisper needed — we already have them) and uses
Claude to extract the 1-3 strongest quotes per clip. Output is
soundbite_index.json, the new spine of the pipeline: scripts should be written
AROUND these soundbites, not the other way around.

Existing transcript sources on disk:
  - media/breaking_law/transcripts.json     23 local source clips
  - analysis/watop/*_transcript.json        100 WATOP videos (pattern corpus)
  - analysis/fern/*/video.en.vtt            32 Fern videos (pattern corpus)

Usage:
    cd /Users/jefflawrence/Documents/youtube-automation-production
    venv/bin/python -m pipeline_v2.soundbite_index

    # Only process the local breaking_law clips (default, what renderer uses):
    venv/bin/python -m pipeline_v2.soundbite_index

    # Also include reference-channel transcripts as pattern corpus:
    venv/bin/python -m pipeline_v2.soundbite_index --include-reference-channels
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_CLIPS_DIR = PROJECT_ROOT / "footage" / "breaking_law" / "clips"
EXISTING_TRANSCRIPTS = PROJECT_ROOT / "media" / "breaking_law" / "transcripts.json"
DEFAULT_OUT = PROJECT_ROOT / "storyboards" / "soundbite_index.json"

# Claude CLI path reuse
from pipeline_v2.llm import query_claude


def load_existing_transcripts():
    """Load the already-existing transcripts from media/breaking_law/transcripts.json.

    Returns list of dicts shaped like transcribe_clip() output.
    """
    if not EXISTING_TRANSCRIPTS.exists():
        return []

    with open(EXISTING_TRANSCRIPTS) as f:
        data = json.load(f)

    clips = data.get("clips", [])
    out = []
    for c in clips:
        filename = c.get("filename", "")
        transcript_text = c.get("transcript", "")
        if not transcript_text or len(transcript_text) < 30:
            continue

        clip_path = DEFAULT_CLIPS_DIR / filename

        # Synthesize segments by splitting on sentence boundaries with rough time estimate
        # (the existing transcript doesn't have timestamps — fake them at ~3 chars/sec)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', transcript_text) if s.strip()]
        total_dur = get_duration(clip_path) if clip_path.exists() else len(transcript_text) / 15
        total_chars = sum(len(s) for s in sentences) or 1
        cursor = 0.0
        segments = []
        for s in sentences:
            dur = (len(s) / total_chars) * total_dur
            segments.append({
                "start": round(cursor, 2),
                "end": round(cursor + dur, 2),
                "text": s,
            })
            cursor += dur

        out.append({
            "clip_id": Path(filename).stem,
            "clip_path": str(clip_path),
            "filename": filename,
            "duration_sec": total_dur,
            "full_text": transcript_text,
            "segments": segments,
            "source": "media/breaking_law/transcripts.json",
        })

    return out


def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def transcribe_clip(clip_path, cache_dir, model_size="base"):
    """Transcribe one clip with Whisper, cache to disk.

    Returns dict with segments (text, start, end) and full text.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{clip_path.stem}.json"

    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    import whisper
    # Fix SSL cert for tiktoken
    try:
        import certifi
        os.environ.setdefault('SSL_CERT_FILE', certifi.where())
    except ImportError:
        pass

    print(f"    Loading Whisper {model_size}...")
    model = whisper.load_model(model_size)
    print(f"    Transcribing {clip_path.name}...")
    t0 = time.time()
    result = model.transcribe(
        str(clip_path),
        word_timestamps=False,  # segment-level is enough for soundbites
        language="en",
        verbose=False,
    )

    # Slim down to just what we need
    out = {
        "clip_id": clip_path.stem,
        "clip_path": str(clip_path),
        "duration_sec": get_duration(clip_path),
        "full_text": result.get("text", "").strip(),
        "segments": [
            {
                "start": round(s["start"], 2),
                "end": round(s["end"], 2),
                "text": s["text"].strip(),
            }
            for s in result.get("segments", [])
        ],
        "model": model_size,
        "transcribed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(cache_path, "w") as f:
        json.dump(out, f, indent=2)

    elapsed = time.time() - t0
    print(f"    → {len(out['segments'])} segments, "
          f"{len(out['full_text'])} chars, {elapsed:.0f}s")
    return out


SOUNDBITE_EXTRACTION_PROMPT = """You are analyzing a source clip for a business/tech documentary titled "Why Breaking the Law Is Profitable" — about corporate fines being cheaper than the profits from breaking the law (Facebook, Ford Pinto, Wells Fargo, Purdue Pharma, RealPage, etc.).

Below is a transcript of the clip. Extract the 0-3 STRONGEST SOUNDBITES — quotes that would be EVIDENCE in the documentary. Pick moments where a speaker (news anchor, CEO, official, whistleblower, expert) SAYS something that a narrator cannot replicate. The documentary's viral mechanism is: a CEO saying the quiet part out loud is more shareable than a narrator saying it for them.

SOUNDBITE CRITERIA (must meet all):
1. 3-20 seconds long (short enough to be a clip)
2. Makes a specific factual CLAIM or delivers an admission (not generic commentary)
3. Would work as evidence in the narrative — narrator can set it up and pay off
4. Has a recognizable speaker persona (anchor, official, CEO) — not random filler

For EACH soundbite return:
- quote: the exact text (verbatim from transcript)
- start_sec / end_sec: timestamps (use the segment timestamps)
- speaker_guess: best guess at who's speaking (e.g., "news anchor", "FTC official", "CEO", "reporter", "expert commentator")
- claim: one-sentence summary of what this quote proves (e.g., "Facebook stock rose after fine announcement")
- relevance: one of: high / medium / low for use in this specific documentary

If NO soundbites meet the criteria (clip is music-only, silent, background noise, generic B-roll audio), return an empty soundbites array.

Return ONLY a JSON object with a single key "soundbites" whose value is an array of the extracted soundbite objects (possibly empty). No markdown, no preamble.

TRANSCRIPT:
---
CLIP_ID: __CLIP_ID__
DURATION: __DURATION__s
FULL TEXT: __FULL_TEXT__

SEGMENTS (with timestamps):
__SEGMENTS__
---
"""


def extract_soundbites(transcript):
    """Use Claude to pick the best 0-3 soundbites from a transcript."""
    full_text = transcript.get("full_text", "")
    segments = transcript.get("segments", [])

    # Skip if the transcript is clearly too short to have anything useful
    if len(full_text) < 30:
        return []

    # Format segments for readability
    segments_formatted = "\n".join(
        f"  [{s['start']:.1f}s - {s['end']:.1f}s] {s['text']}"
        for s in segments[:50]  # cap at 50 segments to keep prompt size sane
    )

    prompt = (
        SOUNDBITE_EXTRACTION_PROMPT
        .replace("__CLIP_ID__", str(transcript["clip_id"]))
        .replace("__DURATION__", str(transcript.get("duration_sec", "unknown")))
        .replace("__FULL_TEXT__", full_text[:3000])
        .replace("__SEGMENTS__", segments_formatted[:5000])
    )

    response = query_claude(prompt, timeout=120)
    if not response:
        return []

    # Extract JSON from response
    m = re.search(r'\{.*\}', response, re.DOTALL)
    if not m:
        return []
    try:
        parsed = json.loads(m.group(0))
        return parsed.get("soundbites", [])
    except json.JSONDecodeError:
        return []


def main():
    parser = argparse.ArgumentParser(description="Build soundbite index from source clips")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process first N clips (for testing)")
    args = parser.parse_args()

    output_path = Path(args.output)

    print("=" * 60)
    print(f"  Soundbite Index Builder")
    print(f"=" * 60)
    print(f"  Source:  {EXISTING_TRANSCRIPTS}")
    print(f"  Output:  {output_path}")
    print()

    # ── Phase 1: Load existing transcripts (no Whisper) ─────────────────────
    print(f"[1/2] Loading existing transcripts from disk...")
    transcripts = load_existing_transcripts()
    if args.limit:
        transcripts = transcripts[:args.limit]
    print(f"  Loaded {len(transcripts)} clip transcripts with real speech content")

    if not transcripts:
        print("ERROR: No transcripts found. Is media/breaking_law/transcripts.json present?")
        sys.exit(1)

    # ── Phase 2: Extract soundbites via Claude ──────────────────────────────
    print(f"\n[2/2] Extracting soundbites with Claude...")
    index = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "transcript_source": str(EXISTING_TRANSCRIPTS),
        "total_clips": len(transcripts),
        "clips": [],
    }

    t_total = time.time()
    for i, t in enumerate(transcripts, 1):
        print(f"  [{i}/{len(transcripts)}] {t['clip_id'][:55]}")
        soundbites = extract_soundbites(t)
        print(f"    → {len(soundbites)} soundbite(s)")
        index["clips"].append({
            "clip_id": t["clip_id"],
            "clip_path": t["clip_path"],
            "duration_sec": t.get("duration_sec"),
            "full_text": t["full_text"][:500],  # first 500 chars for context
            "soundbites": soundbites,
        })

    # ── Summary ─────────────────────────────────────────────────────────────
    all_soundbites = []
    for c in index["clips"]:
        for sb in c["soundbites"]:
            sb_full = {**sb, "clip_id": c["clip_id"], "clip_path": c["clip_path"]}
            all_soundbites.append(sb_full)

    # Also flatten all soundbites for easier querying
    index["all_soundbites"] = all_soundbites
    index["total_soundbites"] = len(all_soundbites)
    index["high_relevance_count"] = sum(1 for s in all_soundbites if s.get("relevance") == "high")

    # ── Save ────────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2)

    print()
    print(f"=" * 60)
    print(f"  Summary")
    print(f"=" * 60)
    print(f"  Clips transcribed:  {len(transcripts)}")
    print(f"  Total soundbites:   {index['total_soundbites']}")
    print(f"  High-relevance:     {index['high_relevance_count']}")
    print(f"  Claude time:        {time.time()-t_total:.0f}s")
    print(f"  Output:             {output_path}")
    print(f"=" * 60)

    # Show top soundbites
    if all_soundbites:
        high = [s for s in all_soundbites if s.get("relevance") == "high"]
        print(f"\n  TOP HIGH-RELEVANCE SOUNDBITES:")
        for s in high[:10]:
            q = s.get("quote", "")[:80]
            speaker = s.get("speaker_guess", "?")
            clip = s.get("clip_id", "?")[:40]
            print(f"    [{speaker}] \"{q}...\"  (from {clip})")


if __name__ == "__main__":
    main()
