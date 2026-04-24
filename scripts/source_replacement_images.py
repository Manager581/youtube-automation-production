#!/usr/bin/env python3
"""Source replacement images from Wikimedia for mismatched beats.

For each beat with a known wrong visual, search Wikimedia with a purpose-built
query based on the narration, and download the top result.
"""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.image_sourcer import search_wikimedia, download_image, source_from_wikimedia

OUT_DIR = PROJECT_ROOT / "footage" / "breaking_law" / "images_v2" / "web"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Beat ID → (search query, output slug)
# Groups are designed to get a SPECIFIC, real image that matches the narration.
# Multiple beats may share the same sourced image.
REPLACEMENTS = {
    # ── Wells Fargo beats ────────────────────────────────────────
    "beat_0023": ("Wells Fargo bank branch", "wells_fargo_branch"),
    "beat_0033": ("Wells Fargo corporate office", "wells_fargo_office"),

    # ── Purdue/opioid specific ───────────────────────────────────
    "beat_0038": ("opioid crisis pharmacy pill bottle", "opioid_pharmacy"),

    # ── Cambridge Analytica ──────────────────────────────────────
    "beat_0064": ("Cambridge Analytica building", "cambridge_analytica_building"),

    # ── Zuckerberg Senate hearing ────────────────────────────────
    "beat_0083": ("Mark Zuckerberg Senate hearing 2018", "zuck_senate"),
    "beat_0086": ("Zuckerberg testimony Congress", "zuck_testimony"),
    "beat_0087": ("Zuckerberg Senate April 2018", "zuck_senate_2"),

    # ── Congress / FTC / regulators ──────────────────────────────
    "beat_0084": ("FTC Federal Trade Commission building", "ftc_building"),

    # ── EU parliament ────────────────────────────────────────────
    "beat_0118": ("European Parliament Brussels building", "eu_parliament_building"),

    # ── Ford recall / Pinto ──────────────────────────────────────
    "beat_0143": ("Ford Pinto recall 1978 news", "ford_pinto_recall"),

    # ── AI / data centers ────────────────────────────────────────
    "beat_0153": ("AI copyright lawsuit court", "ai_copyright_court"),
    "beat_0197": ("data center servers AI", "data_center_ai"),
    "beat_0198": ("AI model training data center", "ai_training_center"),

    # ── Artist / creator / AI scraping ───────────────────────────
    "beat_0180": ("independent artist studio illustration", "artist_studio"),

    # ── RealPage / rent ──────────────────────────────────────────
    "beat_0217": ("apartment building exterior evening", "apartment_exterior"),
    "beat_0224": ("RealPage software company Texas", "realpage_company"),
    "beat_0225": ("New York State Capitol Albany", "ny_state_capitol"),
    "beat_0226": ("federal courthouse Manhattan exterior", "fed_courthouse"),
    "beat_0227": ("RealPage DOJ lawsuit 2024", "realpage_lawsuit"),

    # ── Facebook / final chapter ─────────────────────────────────
    "beat_0144": ("Facebook data deletion privacy", "fb_privacy"),
    "beat_0237": ("Meta European Union fine press conference", "meta_eu_fine"),
}


def source_one(beat_id, query, slug):
    """Search and download one replacement image."""
    print(f"\n[{beat_id}] '{query}'")
    results = search_wikimedia(query, limit=3)
    if not results:
        print(f"  NO results")
        return None

    for i, r in enumerate(results):
        url = r["url"]
        # Determine extension
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".svg" in url.lower():
            continue  # skip SVGs — not usable as raster

        out_name = f"sourced_{slug}.jpg"  # force .jpg extension for renderer
        out_path = OUT_DIR / out_name

        if download_image(url, out_path):
            size_kb = out_path.stat().st_size / 1024
            print(f"  ✓ Downloaded: {out_name} ({size_kb:.0f} KB)")
            print(f"    from: {r['title'][:60]}")
            return out_name
        else:
            print(f"  ✗ failed to download: {url[:80]}")

    return None


def main():
    results = {}
    for beat_id, (query, slug) in REPLACEMENTS.items():
        filename = source_one(beat_id, query, slug)
        if filename:
            results[beat_id] = filename
        time.sleep(0.5)  # be nice to Wikimedia API

    print(f"\n{'='*60}")
    print(f"SOURCED: {len(results)} / {len(REPLACEMENTS)} replacements")
    print(f"{'='*60}")
    for bid, fname in results.items():
        print(f"  {bid} → {fname}")

    # Save mapping
    with open(PROJECT_ROOT / "storyboards" / "sourced_replacements.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nMapping saved: storyboards/sourced_replacements.json")


if __name__ == "__main__":
    main()
