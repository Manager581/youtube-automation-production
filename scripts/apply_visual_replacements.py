#!/usr/bin/env python3
"""Apply comprehensive visual replacements to paper edit for v10.

Combines:
- 9 podcast-clip beats → data charts / existing good footage
- 40 egregious mismatches → best available replacement
- 4 Wikimedia-sourced replacements
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v2_with_data_visuals.json"
DST = PROJECT_ROOT / "storyboards" / "breaking_law_paper_edit_v10.json"

# Beat ID → new visual filename
# Choices optimized for: real story relevance, exists on disk, appropriate aspect
REPLACEMENTS = {
    # ── PODCAST CLIP beats (9) ────────────────────────────────────────
    "beat_0022": "data_trillion_in_fines.jpg",          # "single bad company" → fines chart
    "beat_0047": "data_facebook_fine_vs_profit.jpg",    # "number that ends argument" → FB fine bar
    "beat_0088": "Facebook_FTC_5_billion_dollar_fine.mp4",  # "everyone watched and laughed" → news clip
    "beat_0104": "data_fine_settle_cycle.jpg",          # "fine settle move on" → cycle diagram
    "beat_0114": "data_trillion_in_fines.jpg",          # "formula survived five decades"
    "beat_0137": "data_fine_settle_cycle.jpg",          # "speeding ticket donuts"
    "beat_0187": "digital_artist_workspace_still_30s.jpg",  # "fine is fraction of career"
    "beat_0221": "data_realpage_rent_spike.jpg",        # "coordinated rent prices for millions"
    "beat_0230": "Ford_Pinto_fuel_tank_explosion_1977_still_3s.jpg",  # "Grimshaw lost fingers"

    # ── THE FORMULA — Ford section ─────────────────────────────────────
    "beat_0019": "Ford_Pinto_fuel_tank_explosion_1977_still_2s.jpg",  # "Ford kept selling"
    "beat_0020": "corporate_boardroom_commons_0.jpg",   # "boardroom noticed"
    "beat_0021": "Department_of_Justice_building_still_8s.jpg",  # "cost of getting caught"

    # ── Wells Fargo (using sourced Wikimedia) ──────────────────────────
    "beat_0023": "sourced_wells_fargo_branch.jpg",      # "Yesenia Guitron bank teller"
    "beat_0033": "sourced_wells_fargo_office.jpg",      # "Wells Fargo quota and threat"
    "beat_0032": "Wells_Fargo_fake_accounts_scandal_still_30s.jpg",  # "Ford formula required memo" swap

    # ── Purdue ─────────────────────────────────────────────────────────
    "beat_0038": "Purdue_Pharma_opioid_Sackler_family_still_37s.jpg",  # "Kermit WV pharmacy"
    "beat_0041": "data_ford_pinto_math.jpg",            # "Ford $200k, Sacklers $9k" — math comp

    # ── Cambridge Analytica ────────────────────────────────────────────
    "beat_0058": "cambridge_analytica_commons_0.jpg",   # "Facebook API"
    "beat_0064": "cambridge_analytica_commons_0.jpg",   # "voter profiles"

    # ── Zuckerberg Senate ──────────────────────────────────────────────
    "beat_0083": "Mark_Zuckerberg_Senate_hearing_2018_still_30s.jpg",
    "beat_0086": "Mark_Zuckerberg_Senate_hearing_2018_still_52s.jpg",
    "beat_0087": "Mark_Zuckerberg_Senate_hearing_2018_still_37s.jpg",

    # ── Regulators / Congress ──────────────────────────────────────────
    "beat_0084": "sourced_ftc_building.jpg",            # "people who set fines"
    "beat_0099": "data_zuckerberg_gain.jpg",            # "he made more from announcement"

    # ── THE DATA — Europe ──────────────────────────────────────────────
    "beat_0118": "eu_parliament_commons_0.jpg",         # "Europe found off switch"

    # ── THE FORMULA (rest) ─────────────────────────────────────────────
    "beat_0049": "data_trillion_in_fines.jpg",          # "each company added one feature"

    # ── THE MACHINES — AI ──────────────────────────────────────────────
    "beat_0143": "Ford_Pinto_fuel_tank_explosion_1977_still_1s.jpg",  # "Ford got caught, could recall"
    "beat_0144": "Facebook_FTC_5_billion_dollar_fine_still_8s.jpg",   # "Facebook could delete data"
    "beat_0153": "AI_scraping_copyright_training_data_still_16s.jpg",
    "beat_0180": "digital_artist_workspace_still_16s.jpg",
    "beat_0193": "data_fine_comparison.jpg",            # "Ford's formula clumsy, WF structural"
    "beat_0194": "Purdue_Pharma_opioid_Sackler_family_still_45s.jpg",
    "beat_0195": "data_facebook_fine_vs_profit.jpg",    # "FB's mathematical"
    "beat_0197": "AI_scraping_copyright_training_data.mp4",
    "beat_0198": "AI_scraping_copyright_training_data_still_30s.jpg",

    # ── THE RENT — RealPage ────────────────────────────────────────────
    "beat_0199": "chapter_the_rent.mov",                # chapter card
    "beat_0200": "data_fine_comparison.jpg",            # "Ford $3.5M, WF $3B, Purdue $7.4B"
    "beat_0213": "data_realpage_rent_spike.jpg",        # "90% landlords follow recommendation"
    "beat_0214": "data_realpage_rent_spike.jpg",        # "coordinated rent increases"
    "beat_0217": "RealPage_rent_price_fixing_algorithm_still_30s.jpg",
    "beat_0224": "RealPage_rent_price_fixing_algorithm_still_23s.jpg",
    "beat_0225": "US_Capitol_building_Congress_still_23s.jpg",  # "NY banned algorithmic rent"
    "beat_0226": "courtroom_justice_gavel_still_8s.jpg",  # "RealPage response: they sued"
    "beat_0227": "courtroom_justice_gavel_still_16s.jpg",  # "went to court"

    # ── THE RECKONING ──────────────────────────────────────────────────
    "beat_0237": "data_us_vs_eu_fine.jpg",              # "FB shrugged $5B, panicked €1.2B"
}


def main():
    with open(SRC) as f:
        data = json.load(f)

    beats = data["beats"]
    swapped = 0
    for beat in beats:
        bid = beat.get("beat_id")
        if bid in REPLACEMENTS:
            new = REPLACEMENTS[bid]
            old = beat.get("visual_file", "")
            if old != new:
                beat["visual_file"] = new
                swapped += 1

    data.setdefault("_notes", {})["v10_replacements"] = swapped

    with open(DST, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Swapped {swapped} beats")
    print(f"Written: {DST.name}")


if __name__ == "__main__":
    main()
