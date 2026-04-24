#!/usr/bin/env python3
"""Wire the generated data visuals into the paper edit.

Creates `breaking_law_paper_edit_v2_with_data_visuals.json` — a copy of
paper_edit_v2.json with specific beats' visual_file fields swapped for the
real-data charts.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v2.json"
DST = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v2_with_data_visuals.json"

# Beat ID → new visual filename (all in images_v2/)
SWAPS = {
    # Cold open
    "beat_0002": "facebook_stock_july_2019_annotated.jpg",   # "stock went up"
    "beat_0003": "facebook_stock_july_2019_annotated.jpg",   # "market added $6B"
    "beat_0004": "data_zuckerberg_gain.jpg",                  # "Zuckerberg gained $1.1B"

    # THE FORMULA
    "beat_0012": "data_ford_pinto_math.jpg",                  # "$137M fix vs $49M payouts"
    "beat_0030": "data_wells_fargo_accounts.jpg",             # "3.5M fake accounts"
    "beat_0040": "data_purdue_opioid_deaths.jpg",             # "$7.4B settlement"
    "beat_0045": "data_trillion_in_fines.jpg",                # "over $1 trillion in fines"

    # THE DATA
    "beat_0057": "data_cambridge_analytica.jpg",              # "270,000 downloaded"
    "beat_0060": "data_cambridge_analytica.jpg",              # "270k → 87M"
    "beat_0091": "data_facebook_fine_vs_profit.jpg",          # "Revenue: $70.7B"
    "beat_0092": "data_facebook_fine_vs_profit.jpg",          # "fine was 7%"
    "beat_0093": "data_facebook_fine_vs_profit.jpg",          # "27% of profit"
    "beat_0097": "facebook_stock_july_2019_annotated.jpg",    # "stock rose 1%"
    "beat_0098": "data_zuckerberg_gain.jpg",                  # "Zuckerberg net worth +$1.1B"
}


def main():
    with open(SRC) as f:
        data = json.load(f)

    beats = data["beats"]
    swapped = 0
    not_found = []

    for beat in beats:
        bid = beat.get("beat_id")
        if bid in SWAPS:
            old = beat.get("visual_file", "")
            new = SWAPS[bid]
            print(f"  {bid}: {old[:45]:45s} → {new}")
            beat["visual_file"] = new
            swapped += 1

    for bid in SWAPS:
        if not any(b.get("beat_id") == bid for b in beats):
            not_found.append(bid)

    if not_found:
        print(f"\nWARNING: beats not found in paper edit: {not_found}")

    # Preserve the original stats
    data.setdefault("_notes", {})
    data["_notes"]["data_visuals_wired"] = {
        "count": swapped,
        "source_script": "scripts/wire_data_visuals.py",
    }

    with open(DST, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n{swapped} beats updated with real-data visuals")
    print(f"Written: {DST}")


if __name__ == "__main__":
    main()
