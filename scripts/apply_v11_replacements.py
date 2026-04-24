#!/usr/bin/env python3
"""Build paper edit v11 from v10 + DDG-sourced replacements + data-chart fallbacks.

Inputs:
  - storyboards/breaking_law_paper_edit_v10.json      (baseline)
  - output/replacement_images/_source_report.json     (DDG+vision results)

Outputs:
  - storyboards/breaking_law_paper_edit_v11.json
  - footage/breaking_law/images_v2/web/replace_*.jpg  (copied winners)
"""

import json
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PE = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v10.json"
DST_PE = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v11.json"
REPORT = PROJECT_ROOT / "output" / "replacement_images" / "_source_report.json"
DEST_DIR = PROJECT_ROOT / "footage" / "breaking_law" / "images_v2" / "web"

# ── Data-chart fallbacks for the 10 beats DDG couldn't verify ──────────────
# Rationale: these beats are either abstract concepts ("recidivism pattern",
# "API data access", "tenant overwhelmed") or stats that are better told with
# a chart than a photo. Charts already exist on disk.
CHART_FALLBACKS = {
    "beat_0020": "data_trillion_in_fines.jpg",        # "boardroom noticed" → the formula at scale
    "beat_0022": "data_trillion_in_fines.jpg",        # "isolated scandal? no — recidivism" → 127 recidivists
    "beat_0038": "data_purdue_opioid_deaths.jpg",     # "Kermit WV, 9M pills" → opioid deaths chart
    "beat_0058": "data_cambridge_analytica.jpg",      # "Facebook API gave the quiz" → CA data flow
    "beat_0087": "data_zuckerberg_gain.jpg",          # "giving a tutorial" → Zuck gained from hearing
    "beat_0143": "data_ford_pinto_math.jpg",          # "Ford got caught, could recall" → Ford math
    "beat_0180": "data_ford_pinto_math.jpg",          # "Elliana can't afford to sue" → the math
    "beat_0213": "data_realpage_rent_spike.jpg",      # "90% landlords follow" → literal stat
    "beat_0217": "data_realpage_rent_spike.jpg",      # "most painful: money I spent" → rent spike
    "beat_0237": "data_us_vs_eu_fine.jpg",            # "shrugged $5B, panicked €1.2B" → exact chart
}


def slugify(text, maxlen=30):
    s = re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_').lower()
    return s[:maxlen].rstrip('_')


def pick_best_candidate(candidates):
    """First verified candidate wins (they're ordered by DDG priority)."""
    for c in candidates:
        if c.get("verified"):
            return c
    return None


def main():
    with open(SRC_PE) as f:
        pe = json.load(f)

    with open(REPORT) as f:
        report = json.load(f)

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Build beat_id → new_filename map
    new_visuals = {}

    # 1) DDG winners — copy the top verified candidate into DEST_DIR under a clean name
    copied, ddg_applied = 0, 0
    for entry in report:
        bid = entry["beat_id"]
        winner = pick_best_candidate(entry["candidates"])
        if not winner:
            continue  # handled by CHART_FALLBACKS below
        src_path = Path(winner["file"])
        if not src_path.is_absolute():
            src_path = PROJECT_ROOT / src_path
        if not src_path.exists():
            print(f"  WARN: candidate missing on disk for {bid}: {src_path}")
            continue
        ext = src_path.suffix.lower()
        new_name = f"replace_{bid}_{slugify(entry['query'])}{ext}"
        dst = DEST_DIR / new_name
        if not dst.exists():
            shutil.copy2(src_path, dst)
            copied += 1
        new_visuals[bid] = new_name
        ddg_applied += 1

    # 2) Chart fallbacks for the 10 zero-verified beats
    chart_applied = 0
    for bid, chart_file in CHART_FALLBACKS.items():
        if bid in new_visuals:
            continue  # DDG already gave us something, don't override
        chart_path = DEST_DIR / chart_file
        if not chart_path.exists():
            print(f"  WARN: chart missing: {chart_path}")
            continue
        new_visuals[bid] = chart_file
        chart_applied += 1

    # 3) Write the replacements into the paper edit
    swapped = 0
    for beat in pe["beats"]:
        bid = beat.get("beat_id")
        if bid in new_visuals:
            old = beat.get("visual_file", "")
            new = new_visuals[bid]
            if old != new:
                beat["visual_file"] = new
                # Reasonable default type if it's a chart
                if new.startswith("data_"):
                    beat["visual_type"] = "data_chart"
                else:
                    beat["visual_type"] = "b_roll"
                swapped += 1

    pe.setdefault("_notes", {})["v11_replacements"] = {
        "ddg_sourced": ddg_applied,
        "chart_fallback": chart_applied,
        "total_swapped": swapped,
        "files_copied": copied,
    }

    with open(DST_PE, "w") as f:
        json.dump(pe, f, indent=2)

    print(f"\n== v11 replacements ==")
    print(f"DDG-sourced winners applied: {ddg_applied}")
    print(f"Data-chart fallbacks applied: {chart_applied}")
    print(f"Total beats updated: {swapped}")
    print(f"Files copied into web/: {copied}")
    print(f"Written: {DST_PE}")


if __name__ == "__main__":
    main()
