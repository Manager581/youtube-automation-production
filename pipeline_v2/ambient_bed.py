#!/usr/bin/env python3
"""
Ambient Bed Layer — source and place ambient audio under B-roll sections.

Matches ambient type to visual content (courtroom → gavel/murmur, office → keyboard,
street → traffic). Ducks under narration. Fades in/out at section boundaries.

Sources from Freesound API (key in .env) or bundled assets.

Usage:
  python -m pipeline_v2.ambient_bed
  python -m pipeline_v2.ambient_bed --paper-edit storyboards/breaking_law_paper_edit_approved.json
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_PAPER_EDIT = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_approved.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "storyboards" / "breaking_law_ambient_plan.json"
DEFAULT_AMBIENT_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "ambient"

# Freesound API
FREESOUND_API_KEY = os.environ.get("FREESOUND_API_KEY", "")
if not FREESOUND_API_KEY:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("FREESOUND_API_KEY="):
                    FREESOUND_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")

# Ambient categories with search queries
AMBIENT_CATEGORIES = {
    "courtroom": {
        "query": "courtroom ambience murmur",
        "keywords": ["court", "legal", "judge", "gavel", "trial", "testimony", "hearing"],
    },
    "office": {
        "query": "office ambience quiet",
        "keywords": ["office", "corporate", "boardroom", "meeting", "business"],
    },
    "city": {
        "query": "city street traffic urban ambience",
        "keywords": ["city", "street", "urban", "building", "downtown", "capitol"],
    },
    "newsroom": {
        "query": "newsroom broadcast ambience",
        "keywords": ["news", "broadcast", "anchor", "reporter", "media"],
    },
    "crowd": {
        "query": "crowd murmur indoor ambience",
        "keywords": ["crowd", "protest", "rally", "public", "congress", "senate"],
    },
    "digital": {
        "query": "computer server room hum ambience",
        "keywords": ["data", "server", "digital", "algorithm", "tech", "computer", "internet"],
    },
    "silence": {
        "query": None,
        "keywords": [],
    },
}

# Audio levels
AMBIENT_VOLUME_UNDER_VO = -24  # dB — very subtle under narration
AMBIENT_VOLUME_DURING_GAP = -18  # dB — slightly louder during VO gaps
FADE_DURATION_MS = 500


def match_ambient_type(beat):
    """Determine which ambient category matches a beat's content."""
    text = beat.get("text", "").lower()
    visual = beat.get("visual_file", "").lower()
    why = beat.get("why", "").lower()
    combined = f"{text} {visual} {why}"

    best_match = "silence"
    best_score = 0

    for category, config in AMBIENT_CATEGORIES.items():
        if category == "silence":
            continue
        score = sum(1 for kw in config["keywords"] if kw in combined)
        if score > best_score:
            best_score = score
            best_match = category

    # Only assign ambient if there's a reasonable match
    if best_score < 1:
        return "silence"

    return best_match


def search_freesound(query, min_duration=20, max_results=3):
    """Search Freesound API for ambient tracks."""
    if not FREESOUND_API_KEY:
        print("  WARNING: No Freesound API key — skipping ambient download")
        return []

    encoded = urllib.parse.urlencode({
        "query": query,
        "filter": f"duration:[{min_duration} TO 120]",
        "fields": "id,name,duration,previews,license",
        "sort": "rating_desc",
        "page_size": max_results,
        "token": FREESOUND_API_KEY,
    })
    url = f"https://freesound.org/apiv2/search/text/?{encoded}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = []
        for sound in data.get("results", []):
            previews = sound.get("previews", {})
            preview_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")
            if preview_url:
                results.append({
                    "id": sound["id"],
                    "name": sound["name"],
                    "duration": sound["duration"],
                    "preview_url": preview_url,
                    "license": sound.get("license", ""),
                })
        return results
    except Exception as e:
        print(f"  Freesound search error: {e}")
        return []


def download_ambient(sound, output_dir):
    """Download a Freesound ambient track."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"ambient_{sound['id']}_{sound['name'][:30].replace(' ', '_')}.mp3"
    filepath = output_dir / filename

    if filepath.exists():
        return str(filepath)

    try:
        urllib.request.urlretrieve(sound["preview_url"], str(filepath))
        return str(filepath)
    except Exception as e:
        print(f"  Download error: {e}")
        return None


def plan_ambient_beds(paper_edit_path, ambient_dir, output_path):
    """Plan ambient beds from paper edit."""
    with open(paper_edit_path) as f:
        paper_edit = json.load(f)

    beats = paper_edit.get("beats", [])

    # Group consecutive beats by ambient type
    sections = []
    current_type = None
    current_start = None
    current_end = None

    for beat in beats:
        if beat.get("is_chapter_marker"):
            # End current section at chapter boundary
            if current_type and current_type != "silence":
                sections.append({
                    "ambient_type": current_type,
                    "start_sec": current_start,
                    "end_sec": current_end,
                    "duration": current_end - current_start,
                })
            current_type = None
            continue

        ambient = match_ambient_type(beat)

        if ambient == current_type:
            current_end = beat.get("end_sec", current_end)
        else:
            # End previous section
            if current_type and current_type != "silence":
                sections.append({
                    "ambient_type": current_type,
                    "start_sec": current_start,
                    "end_sec": current_end,
                    "duration": current_end - current_start,
                })
            current_type = ambient
            current_start = beat.get("start_sec", 0)
            current_end = beat.get("end_sec", 0)

    # Flush last section
    if current_type and current_type != "silence":
        sections.append({
            "ambient_type": current_type,
            "start_sec": current_start,
            "end_sec": current_end,
            "duration": current_end - current_start,
        })

    # Filter out very short sections (< 5s)
    sections = [s for s in sections if s["duration"] >= 5.0]
    print(f"  Found {len(sections)} ambient sections")

    # Download ambient tracks for each unique type
    downloaded = {}
    unique_types = set(s["ambient_type"] for s in sections)

    for ambient_type in unique_types:
        config = AMBIENT_CATEGORIES.get(ambient_type, {})
        query = config.get("query")
        if not query:
            continue

        print(f"  Searching Freesound for '{ambient_type}': {query}")
        results = search_freesound(query, min_duration=20, max_results=1)
        if results:
            filepath = download_ambient(results[0], ambient_dir)
            if filepath:
                downloaded[ambient_type] = filepath
                print(f"    Downloaded: {os.path.basename(filepath)} ({results[0]['duration']:.0f}s)")

    # Build ambient plan
    ambient_plan = []
    for section in sections:
        ambient_file = downloaded.get(section["ambient_type"])
        if not ambient_file:
            continue

        ambient_plan.append({
            "start_sec": round(section["start_sec"], 3),
            "end_sec": round(section["end_sec"], 3),
            "duration": round(section["duration"], 3),
            "ambient_type": section["ambient_type"],
            "ambient_file": ambient_file,
            "volume_db": AMBIENT_VOLUME_UNDER_VO,
            "fade_in_ms": FADE_DURATION_MS,
            "fade_out_ms": FADE_DURATION_MS,
        })

    plan = {
        "sections": ambient_plan,
        "stats": {
            "total_sections": len(ambient_plan),
            "total_duration": sum(s["duration"] for s in ambient_plan),
            "types_used": list(set(s["ambient_type"] for s in ambient_plan)),
            "files_downloaded": len(downloaded),
        },
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(plan, f, indent=2)

    s = plan["stats"]
    print(f"\n  Ambient plan: {s['total_sections']} sections, "
          f"{s['total_duration']:.0f}s total, types: {s['types_used']}")
    print(f"  Saved: {output_path}")

    return plan


def main():
    parser = argparse.ArgumentParser(description="Ambient Bed Layer")
    parser.add_argument("--paper-edit", type=str, default=str(DEFAULT_PAPER_EDIT))
    parser.add_argument("--ambient-dir", type=str, default=str(DEFAULT_AMBIENT_DIR))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    print("Ambient Bed Layer")
    plan_ambient_beds(args.paper_edit, args.ambient_dir, args.output)


if __name__ == "__main__":
    main()
