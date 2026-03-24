"""
Visual Sequence Templates — multi-shot choreography for dramatic moments.

When narration describes something that can't be shown with a single still image
(e.g., someone falling from a building), sequence templates define a multi-shot
plan: which images to show, what motion to apply, what SFX to play, and for how long.

The Director checks each segment's narration against template triggers and attaches
a `sequence_plan` list of shots. The assembler renders these as choreographed sequences.
"""

from __future__ import annotations

import os
import re


# ── Sequence Templates ──────────────────────────────────────────────────────
# Each template has:
#   triggers: list of regex patterns (case-insensitive) that activate it
#   shots: ordered list of shots to render as a sequence
#     - image_category: pipe-separated keywords to match against image filenames
#     - motion: Ken Burns motion type
#     - duration: target duration in seconds
#     - sfx: SFX type to play at shot start (or None)

SEQUENCE_TEMPLATES = {
    "fall_from_height": {
        "triggers": [
            r"fell\s+\d+\s+stories",
            r"crash(?:es|ed)?\s+through.*window.*fall",
            r"plunge[ds]?\s+(?:to|from|down)",
            r"fall[s]?\s+to\s+(?:his|her|their)?\s*death",
            r"through\s+the\s+(?:glass|window).*(?:fall|plung|drop)",
            r"(?:body|he|she)\s+(?:hit|struck|landed)",
        ],
        "shots": [
            {"image_category": "building|hotel|window|statler|exterior",
             "motion": "zoom_in", "duration": 2.0, "sfx": "glass_shatter"},
            {"image_category": "sky|height|building|hotel|tall|stories",
             "motion": "pan_down", "duration": 2.5, "sfx": None},
            {"image_category": "ground|street|sidewalk|pavement|night",
             "motion": "zoom_in", "duration": 1.5, "sfx": "body_impact"},
            {"image_category": "emergency|ambulance|police|night|street",
             "motion": "static", "duration": 2.0, "sfx": "tension"},
        ],
    },

    "drugging_poisoning": {
        "triggers": [
            r"(?:slip|lace|spike|dose)[dpeds]*\s+(?:his|her|their|the)",
            r"LSD\s+(?:into|in|was)",
            r"cointreau",
            r"unknowing(?:ly)?\s+(?:consum|drink|ingest|dose)",
            r"drugg(?:ed|ing)\s+(?:his|her|them|the)",
        ],
        "shots": [
            {"image_category": "drink|glass|bottle|bar|cointreau|liquid",
             "motion": "zoom_in", "duration": 2.0, "sfx": "shimmer"},
            {"image_category": "face|person|portrait|man|group",
             "motion": "slow_zoom", "duration": 2.5, "sfx": "tension"},
            {"image_category": "blur|distortion|abstract|dark|shadow",
             "motion": "zoom_in", "duration": 2.0, "sfx": "shimmer"},
        ],
    },

    "document_revelation": {
        "triggers": [
            r"document[s]?\s+(?:reveal|show|prove|confirm)",
            r"classified\s+(?:file|memo|report|document|page)",
            r"(?:memo|report|file)\s+(?:show|reveal|confirm|prove)",
            r"pages?\s+(?:show|reveal|detail|describe)",
            r"declassified",
        ],
        "shots": [
            {"image_category": "document|paper|file|folder|stamp|memo|report",
             "motion": "zoom_in", "duration": 3.0, "sfx": "shimmer"},
            {"image_category": "text|typewriter|redacted|stamp|classified",
             "motion": "pan_right", "duration": 2.0, "sfx": None},
        ],
    },

    "violent_confrontation": {
        "triggers": [
            r"struck\s+(?:him|her|them)",
            r"(?:hit|punch|grab|attack|assault)(?:ed|s)?\s+(?:him|her|them|the)",
            r"restrain(?:ed|ing)",
            r"struggle[ds]?\s+(?:with|against|to)",
            r"physical(?:ly)?\s+(?:assault|attack|confront)",
        ],
        "shots": [
            {"image_category": "person|face|figure|shadow|man",
             "motion": "zoom_in", "duration": 1.5, "sfx": "impact"},
            {"image_category": "dark|shadow|silhouette|room|interior",
             "motion": "static", "duration": 2.0, "sfx": "rumble"},
        ],
    },

    "secret_experiment": {
        "triggers": [
            r"(?:secret|covert)\s+(?:experiment|program|project|operation)",
            r"mkultra",
            r"test\s+subject[s]?",
            r"(?:experiment|program)\s+(?:code.?named|called|known\s+as)",
            r"human\s+experiment",
        ],
        "shots": [
            {"image_category": "lab|laboratory|science|medical|facility|fort_detrick",
             "motion": "pan_right", "duration": 2.5, "sfx": "tension"},
            {"image_category": "document|folder|classified|stamp|cia",
             "motion": "zoom_in", "duration": 2.0, "sfx": "shimmer"},
        ],
    },
}


def match_sequence(narration_text: str) -> dict | None:
    """Return the best matching sequence template for narration text, or None.

    Checks each template's triggers (case-insensitive regex) against the text.
    Returns a copy of the first matching template dict, or None.
    Templates are checked in a fixed priority order (most specific first).
    """
    if not narration_text:
        return None

    text_lower = narration_text.lower()

    # Check in priority order: most specific/dramatic first
    priority_order = [
        "fall_from_height",
        "drugging_poisoning",
        "violent_confrontation",
        "secret_experiment",
        "document_revelation",
    ]

    for name in priority_order:
        template = SEQUENCE_TEMPLATES[name]
        for pattern in template["triggers"]:
            if re.search(pattern, text_lower):
                return {
                    "name": name,
                    "shots": [dict(s) for s in template["shots"]],  # deep copy
                }

    return None


def score_image_for_shot(
    still: dict,
    sb_entry: dict | None = None,
    shot_category: str | None = None,
) -> float:
    """Score 0.0-1.0 how well an image matches a shot's requirements.

    Scoring factors:
    - shot_category keywords in filename (+0.4 per match, max 0.8)
    - storyboard 'show' text words in filename (+0.3 per match, max 0.6)
    - storyboard_segment_ids contains current segment index (+0.5)
    - search_query words in filename (+0.2 per match, max 0.4)
    """
    score = 0.0

    # Get filename for keyword matching
    fname = os.path.basename(
        still.get("path") or still.get("local_path") or still.get("filename") or ""
    ).lower()
    # Strip extension for cleaner matching
    fname_stem = os.path.splitext(fname)[0].replace("_", " ").replace("-", " ")

    # 1. Shot category keywords (from sequence template)
    if shot_category:
        cat_hits = 0
        for kw in shot_category.split("|"):
            kw = kw.strip()
            if kw and kw in fname_stem:
                cat_hits += 1
        score += min(0.8, cat_hits * 0.4)

    # 2. Storyboard 'show' text
    if sb_entry:
        show_text = (sb_entry.get("show") or "").lower()
        show_hits = 0
        for word in show_text.split():
            if len(word) > 3 and word in fname_stem:
                show_hits += 1
        score += min(0.6, show_hits * 0.3)

    # 3. Segment ID match — strongest signal
    seg_ids = still.get("storyboard_segment_ids", [])
    sb_idx = sb_entry.get("_segment_index") if sb_entry else None
    if sb_idx is not None and sb_idx in seg_ids:
        score += 0.5

    # 4. Search query keywords
    if sb_entry:
        query = (sb_entry.get("search_query") or "").lower()
        query_hits = 0
        for word in query.split():
            if len(word) > 3 and word in fname_stem:
                query_hits += 1
        score += min(0.4, query_hits * 0.2)

    return min(1.0, score)
