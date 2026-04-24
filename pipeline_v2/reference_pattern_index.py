#!/usr/bin/env python3
"""Reference Pattern Index — fire-and-forget corpus dump.

Extracts structural patterns from WATOP (100 videos) + Fern (32 videos)
transcripts already on disk. No Claude calls — pure text mining.
Output is a searchable JSON the scriptwriter can query later:

  - cold_opens: first 30s of each reference video
  - closers: last 30s of each reference video
  - named_entity_intros: sentences that introduce a named person/company
  - stat_drops: sentences containing specific numbers
  - transition_markers: "But here's the thing", "So what happened was", etc.

Run once, dump to disk, use for v12+ pattern queries.

Usage:
    venv/bin/python -m pipeline_v2.reference_pattern_index
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

WATOP_DIR = PROJECT_ROOT / "analysis" / "watop"
FERN_DIR = PROJECT_ROOT / "analysis" / "fern"
OUT_PATH = PROJECT_ROOT / "storyboards" / "reference_pattern_index.json"


def load_watop_transcript(path):
    """WATOP uses Whisper JSON with word-level timestamps."""
    with open(path) as f:
        data = json.load(f)
    segments = data.get("segments", [])
    words = data.get("words", [])
    return {
        "full_text": data.get("text", "").strip(),
        "segments": [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in segments
        ],
        "duration": segments[-1]["end"] if segments else 0,
        "source": "watop",
        "video_id": path.stem.replace("_transcript", ""),
    }


def load_fern_vtt(path):
    """Fern uses YouTube auto-captions (.vtt)."""
    with open(path) as f:
        content = f.read()

    # Parse VTT: lines are "HH:MM:SS.ms --> HH:MM:SS.ms" then text
    segments = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            try:
                times = line.split(" --> ")
                start = vtt_to_sec(times[0].strip())
                end = vtt_to_sec(times[1].split()[0].strip())
            except Exception:
                i += 1
                continue
            # Collect text lines until blank
            text_parts = []
            j = i + 1
            while j < len(lines) and lines[j].strip():
                # Strip inline timestamps like <00:00:03.600><c>
                clean = re.sub(r"<[^>]+>", "", lines[j])
                text_parts.append(clean.strip())
                j += 1
            text = " ".join(text_parts).strip()
            if text:
                segments.append({"start": start, "end": end, "text": text})
            i = j + 1
        else:
            i += 1

    # Dedupe consecutive repeated lines (VTT has overlap artifacts)
    deduped = []
    last_text = ""
    for s in segments:
        if s["text"] != last_text:
            deduped.append(s)
            last_text = s["text"]

    full_text = " ".join(s["text"] for s in deduped)
    return {
        "full_text": full_text,
        "segments": deduped,
        "duration": deduped[-1]["end"] if deduped else 0,
        "source": "fern",
        "video_id": path.parent.name,
    }


def vtt_to_sec(timestamp):
    """Convert HH:MM:SS.mmm to seconds."""
    parts = timestamp.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    return float(parts[-1])


def segments_in_range(segments, start_sec, end_sec):
    """Return segments falling in [start_sec, end_sec)."""
    return [s for s in segments if s["start"] >= start_sec and s["start"] < end_sec]


# ─── Pattern extractors ───────────────────────────────────────────────────

NAMED_ENTITY_PATTERNS = [
    re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),  # "Mark Zuckerberg"
    re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b"),  # "CamelCase"
]

TRANSITION_MARKERS = [
    "but here's the thing",
    "but here's what",
    "but wait",
    "so what happened",
    "the problem is",
    "here's why",
    "in other words",
    "as it turns out",
    "it turns out",
    "but then",
    "meanwhile",
    "at the same time",
    "the catch",
    "the twist",
    "here's the kicker",
    "and that's when",
    "until",
]

STAT_PATTERNS = [
    re.compile(r"\$[\d,]+\.?\d*\s*(billion|million|trillion|thousand)", re.I),
    re.compile(r"\d+\s*(percent|%)", re.I),
    re.compile(r"\d{4}\b"),  # years
    re.compile(r"\b\d+[\d,]*\b"),  # large numbers
]


def extract_cold_open(transcript, duration=30):
    """First N seconds of the video."""
    segs = segments_in_range(transcript["segments"], 0, duration)
    return " ".join(s["text"] for s in segs).strip()


def extract_closer(transcript, duration=30):
    """Last N seconds of the video."""
    total = transcript["duration"]
    if total < duration:
        return ""
    segs = segments_in_range(transcript["segments"], total - duration, total + 1)
    return " ".join(s["text"] for s in segs).strip()


def extract_transition_lines(transcript):
    """Sentences starting with known transition markers."""
    text = transcript["full_text"].lower()
    found = []
    for marker in TRANSITION_MARKERS:
        for m in re.finditer(r'(?<=[.!?])\s+([^.!?]*' + re.escape(marker) + r'[^.!?]*[.!?])', text, re.I):
            sentence = m.group(1).strip()
            if 10 < len(sentence) < 300:
                found.append(sentence)
    return list(set(found))[:20]


def extract_stat_deliveries(transcript):
    """Sentences containing specific numbers."""
    sentences = re.split(r'(?<=[.!?])\s+', transcript["full_text"])
    with_stats = []
    for s in sentences:
        for pat in STAT_PATTERNS[:2]:  # money or percent (skip generic numbers — too noisy)
            if pat.search(s) and 15 < len(s) < 250:
                with_stats.append(s.strip())
                break
    return with_stats[:30]


def extract_named_entity_intros(transcript):
    """Sentences introducing a named person or company (heuristic: sentence has 'Name Name' pattern + verb)."""
    sentences = re.split(r'(?<=[.!?])\s+', transcript["full_text"])
    intros = []
    for s in sentences:
        if len(s) < 20 or len(s) > 200:
            continue
        if NAMED_ENTITY_PATTERNS[0].search(s):
            # Has "First Last" — likely a person intro
            intros.append(s.strip())
    return intros[:20]


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Reference Pattern Index Builder")
    print("=" * 60)

    transcripts = []

    # Load WATOP
    watop_files = sorted(WATOP_DIR.glob("*_transcript.json"))
    print(f"Loading {len(watop_files)} WATOP transcripts...")
    for p in watop_files:
        try:
            t = load_watop_transcript(p)
            transcripts.append(t)
        except Exception as e:
            print(f"  [skip] {p.name}: {e}")

    # Load Fern
    fern_files = sorted(FERN_DIR.glob("*/video.en.vtt"))
    print(f"Loading {len(fern_files)} Fern VTT transcripts...")
    for p in fern_files:
        try:
            t = load_fern_vtt(p)
            transcripts.append(t)
        except Exception as e:
            print(f"  [skip] {p.parent.name}: {e}")

    print(f"\nTotal reference transcripts loaded: {len(transcripts)}")

    # Extract patterns
    print("\nExtracting patterns...")
    index = {
        "total_videos": len(transcripts),
        "sources": {
            "watop": len([t for t in transcripts if t["source"] == "watop"]),
            "fern": len([t for t in transcripts if t["source"] == "fern"]),
        },
        "cold_opens": [],       # 30s openers
        "closers": [],          # 30s endings
        "transition_lines": [], # "but here's the thing..."
        "stat_deliveries": [],  # sentences with dollars/percentages
        "named_intros": [],     # sentences introducing named people
    }

    for t in transcripts:
        cold = extract_cold_open(t)
        close = extract_closer(t)
        trans = extract_transition_lines(t)
        stats = extract_stat_deliveries(t)
        intros = extract_named_entity_intros(t)

        meta = {"source": t["source"], "video_id": t["video_id"], "duration": t["duration"]}

        if cold and len(cold) > 50:
            index["cold_opens"].append({**meta, "text": cold})
        if close and len(close) > 50:
            index["closers"].append({**meta, "text": close})
        for line in trans:
            index["transition_lines"].append({**meta, "line": line})
        for s in stats[:10]:  # cap per video
            index["stat_deliveries"].append({**meta, "sentence": s})
        for i in intros[:5]:
            index["named_intros"].append({**meta, "sentence": i})

    # Summary
    print(f"\n  Cold opens:          {len(index['cold_opens'])}")
    print(f"  Closers:             {len(index['closers'])}")
    print(f"  Transition lines:    {len(index['transition_lines'])}")
    print(f"  Stat deliveries:     {len(index['stat_deliveries'])}")
    print(f"  Named-entity intros: {len(index['named_intros'])}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(index, f, indent=2)

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"\n  Output: {OUT_PATH}")
    print(f"  Size:   {size_kb:.0f} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()
