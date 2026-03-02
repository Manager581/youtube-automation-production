#!/usr/bin/env python3
"""
Fern Title Angle Analyzer — 100% rule-based, zero API cost.

Classifies all 30 Fern titles by narrative ANGLE and ranks by avg view count.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

FERN_DIR    = Path("analysis/fern")
OUTPUT_FILE = FERN_DIR / "TITLE_ANGLE_FORMULA.json"

# ── ANGLE RULES ─────────────────────────────────────────────────────────────
# Each rule: (angle_label, [regex patterns])
# First matching rule wins.

RULES = [
    # INSTITUTION_HOW — How FBI/CIA/govt did X
    ("INSTITUTION_HOW", [
        r"\bhow\b.*(fbi|cia|nsa|dea|police|agent|government|pentagon|interpol|secret service)",
        r"(fbi|cia|nsa|interpol|secret service).*(infiltrat|undercover|caught|hunt|investigat)",
    ]),
    # VILLAIN_EXPOSED — named bad actor caught/exposed
    ("VILLAIN_EXPOSED", [
        r"\b(russia|china|north korea|iran|putin|kim jong|cartel|mafia|isis|kkk|nazi|cult)\b.*"
            r"(hack|steal|kill|attack|secret|expose|want|murder|assassin)",
        r"most (evil|dangerous|wanted|notorious)",
        r"(worst|deadliest|most evil) (secret|police|dictator|regime|group)",
        r"russia.s most wanted",
    ]),
    # PERSON_GENIUS_TRAGEDY — single extraordinary person
    ("PERSON_GENIUS_TRAGEDY", [
        r"(genius|prodigy|smartest|brilliant).*(nobody|kid|boy|girl|man|woman|person)",
        r"(kid|boy|girl|man|woman|person).*(genius|prodigy|hacked|stole|built|created|paid with)",
        r"\b(unabomber|kaczynski|warmbier|epstein|madoff)\b",
        r"the (only|last|first) (nazi|person|man|woman|agent|spy)",
        r"indian genius",
    ]),
    # PLACE_HORROR — dangerous/horrifying specific location
    ("PLACE_HORROR", [
        r"(camp 14|north sentine|chernobyl|most secret building|33 thomas)",
        r"(waterpark|disneyland|camp|building|prison).*(kill|horror|horrify|dangerous|deadly|secret|preventable)",
        r"most (horrible|secret|dangerous) (place|building|camp|facility)",
    ]),
    # SECRET_REVEALED — hidden thing/conspiracy exposed
    ("SECRET_REVEALED", [
        r"secret (sons|base|police|weapon|plan|highway|program|building)",
        r"(nobody|no one) (knows|understands|talks about)",
        r"most secret",
        r"secretly (getting|building|planning)",
    ]),
    # PROCESS_HOW — how a criminal/dangerous process works
    ("PROCESS_HOW", [
        r"how (cocaine|fentanyl|meth|drug).*(work|made|destroy|kill|easy|smuggl)",
        r"how .*(smuggl|scam|launder|traffic)",
        r"(easy to smuggle|is destroying|is killing).*(europe|america)",
        r"how egypt",
        r"how a (cult|scammer|minecraft)",
    ]),
    # POWER_MONEY — extreme wealth, power, financial schemes
    ("POWER_MONEY", [
        r"\$[\d,]+(,\d+)*\s*(million|billion|m\b)",
        r"(billion|million).*(steal|scam|machine|scheme|empire)",
        r"(coca.cola|billion dollar) machine",
        r"how trump is secretly",
        r"(thiel|soros).*(destroy|control|power|democracy)",
        r"destroying democracy",
    ]),
    # DISASTER_TRAGEDY — specific catastrophic event
    ("DISASTER_TRAGEDY", [
        r"killed? \d",
        r"(didn.t survive|paid with his life)",
        r"(waterpark|disneyland).*(killed|dead|died|tragedy|preventable)",
        r"most preventable tragedy",
    ]),
    # THREAT_WHY — why something is dangerous to you/society
    ("THREAT_WHY", [
        r"^why\b",
        r"dumb design",
        r"(destroying|killing) (europe|democracy|society|america)",
    ]),
    # COUNTRY_STORY — country as primary subject (catch-all)
    ("COUNTRY_STORY", [
        r"\b(north korea|russia|china|iran|cuba|venezuela|egypt|fiji)\b",
        r"we investigated china",
    ]),
]


def classify_title(title: str) -> str:
    t = title.lower()
    for angle, patterns in RULES:
        for pat in patterns:
            if re.search(pat, t):
                return angle
    return "OTHER"


def load_videos():
    d = json.loads((FERN_DIR / "FERN_FORMULA.json").read_text())
    return [
        {"id": v.get("id", ""), "title": v.get("title", ""), "views": v.get("views", 0)}
        for v in d.get("per_video_data", [])
        if v.get("title")
    ]


def aggregate(classified):
    by_angle = defaultdict(list)
    for item in classified:
        by_angle[item["angle"]].append(item)

    rankings = []
    for angle, items in by_angle.items():
        views = [i["views"] for i in items]
        avg   = round(sum(views) / len(views)) if views else 0
        top   = sorted(items, key=lambda x: x["views"], reverse=True)
        rankings.append({
            "angle":       angle,
            "count":       len(items),
            "avg_views":   avg,
            "max_views":   max(views),
            "total_views": sum(views),
            "top_titles":  [i["title"] for i in top[:3]],
            "all_titles":  [(i["title"], i["views"]) for i in top],
        })
    return sorted(rankings, key=lambda x: x["avg_views"], reverse=True)


if __name__ == "__main__":
    videos = load_videos()
    print(f"Loaded {len(videos)} videos\n")

    classified = []
    for v in videos:
        angle = classify_title(v["title"])
        classified.append({**v, "angle": angle})
        print(f"  {angle:<22}  {v['views']:>10,}v  {v['title']}")

    rankings = aggregate(classified)

    print("\n" + "=" * 65)
    print("ANGLE RANKINGS BY AVG VIEW COUNT")
    print("=" * 65)
    for i, r in enumerate(rankings, 1):
        flag = "  ← USE THIS" if r["avg_views"] > 4_000_000 else ""
        print(f"\n{i}. {r['angle']}{flag}")
        print(f"   Avg: {r['avg_views']:>10,}  |  n={r['count']}  |  Max: {r['max_views']:,}")
        for title, v in r["all_titles"][:2]:
            print(f"   └─ {v:>10,}v  {title}")

    result = {
        "channel":         "fern-tv",
        "videos_analyzed": len(videos),
        "angle_rankings":  rankings,
        "all_classified":  classified,
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {OUTPUT_FILE}")
