#!/usr/bin/env python3
"""
Build complete image manifest mapping existing Wikimedia images to storyboard segments,
then search Wikimedia Commons ONLY for missing segments.

Phase 1: Map existing good images to segments
Phase 2: Search+download for uncovered segments
Phase 3: Update manifest.json
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SB_PATH = PROJECT_ROOT / "storyboards/frank_olson_cia_scientist_lsd_murder_cover_up.json"
MANIFEST_PATH = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/manifest.json"
IMG_DIR = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images"
WIKI_DIR = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/wikimedia"

API_USER_AGENT = "WikimediaDocSourcer/1.0 (documentary-research; educational-use) python-requests/2.31"
DOWNLOAD_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
API_URL = "https://commons.wikimedia.org/w/api.php"
THUMB_WIDTH = 1920
SLEEP_BETWEEN = 2.5  # Generous rate limit
PREFERRED_EXTS = {".jpg", ".jpeg", ".png"}

# ============================================================
# PHASE 1: Map existing images to segments
# These are VERIFIED good images already on disk.
# ============================================================
EXISTING_MAPPINGS = {
    # People (verified correct)
    "wiki_Frank_Olsen_1910-1953.jpg.jpg": [2, 14, 45, 57, 75, 150, 155, 162, 174],
    "wiki_Sidney_Gottlieb_photo.jpg.jpg": [7, 34, 51, 137],
    "wiki_allen_dulles.jpg": [31],
    "wiki_william_colby.jpg": [113],
    "wiki_gerald_ford.jpg": [111, 112],
    "wiki_frank_church_senator.jpg": [11, 104],

    # Locations (verified correct)
    "wiki_hotel_statler_entrance.jpg": [1, 86, 87, 165],
    "wiki_nyc_skyline_1950s_night.jpg": [0, 80, 85],
    "wiki_cia_headquarters.jpg": [24, 140, 169, 170],
    "wiki_art_deco_building_night.jpg": [80],  # NYC night alternate
    "wiki_building_night.jpg": [85],  # NYC street night
    "wiki_hotel_night.jpg": [88],  # Hotel at night

    # Documents & Science (verified correct)
    "wiki_DeclassifiedMKULTRA.jpg.jpg": [8, 29, 33, 105],
    "wiki_Mkultra-lsd-doc.jpg.jpg": [37, 41, 44, 114],
    "wiki_bacteriological_laboratory.jpg": [19, 23, 70],
    "wiki_scientist_laboratory_1940s.jpg": [20, 35, 38],
    "wiki_lsd_molecule.png": [38, 67],

    # Visual metaphors (verified correct)
    "wiki_broken_window_glass.jpg": [10, 92, 128],
    "wiki_1950s_suburban_house.jpg": [3, 63],
    "wiki_Buffalo_City_Hall_Niagara_Square_Buffalo_NY_-_52685122122.jpg.jpg": [1],
    "wiki_City_College_of_New_York_November_2016.jpg.jpg": [132],
}

# Also check wikimedia/ dir
WIKIMEDIA_DIR_MAPPINGS = {
    "hotel_statler_new_york.jpg": [1, 86, 87],
    "fort_detrick_lab.jpg": [16, 17, 22, 65, 167],
    "american_family_1950s.jpg": [3, 100],
    "allen_dulles_cia.jpg": [31],
    "william_colby_cia.jpg": [113],
    "frank_church_senator.jpg": [11, 104],
    "gerald_ford_president.jpg": [111, 112],
    "korean_war_prisoners.jpg": [26],
    "lsd_molecule.png": [38, 67],
}

# ============================================================
# PHASE 2: Search queries for uncovered segments
# ============================================================
SEARCH_GROUPS = [
    # People we don't have photos for
    ("wiki_eric_olson", [72, 117, 146, 159, 164], [
        "investigator reviewing documents cold case",
        "man searching through files justice",
    ]),
    ("wiki_errol_morris", [143, 144], [
        "Errol Morris filmmaker",
        "Errol Morris documentary director",
    ]),

    # Locations
    ("wiki_pentagon", [28], [
        "Pentagon aerial view",
        "Pentagon building 1950s",
    ]),
    ("wiki_deep_creek_lodge", [48], [
        "rustic cabin retreat 1950s",
        "mountain lodge cabin winter",
    ]),
    ("wiki_frederick_md", [63, 120], [
        "Frederick Maryland downtown",
        "small town Maryland",
    ]),
    ("wiki_washington_union_station", [84], [
        "Union Station Washington interior",
        "train station 1950s",
    ]),
    ("wiki_manhattan_courthouse", [132], [
        "Manhattan criminal court building",
        "New York courthouse",
    ]),
    ("wiki_fort_detrick_exterior", [16, 17, 22, 65, 167], [
        "military base entrance gate",
        "army base 1950s entrance",
    ]),

    # Visual metaphors
    ("wiki_dark_hallway", [62, 68, 78, 83], [
        "dark corridor hallway",
        "long dark hallway",
        "ominous corridor",
    ]),
    ("wiki_interrogation_room", [40], [
        "interrogation room",
        "empty chair spotlight room",
    ]),
    ("wiki_empty_courtroom", [13, 135], [
        "empty courtroom bench",
        "courtroom judge bench",
    ]),
    ("wiki_fog_path", [12, 161, 163, 171], [
        "fog road path",
        "foggy road mysterious",
    ]),
    ("wiki_hotel_room_vintage", [88, 89], [
        "hotel room vintage 1950s",
        "old hotel room interior bed",
    ]),
    ("wiki_man_distressed", [58, 59, 76], [
        "man silhouette window distressed",
        "anxious man shadow",
    ]),
    ("wiki_woman_telephone_1950s", [60, 61, 99], [
        "woman telephone 1950s",
        "housewife telephone vintage",
    ]),
    ("wiki_man_desk_documents", [118, 133, 147, 172, 173], [
        "man desk documents files",
        "investigator desk papers",
    ]),
    ("wiki_venetian_blinds", [91], [
        "venetian blinds window light",
        "window blinds interior",
    ]),
    ("wiki_children_1950s", [100, 101, 102], [
        "children 1950s American",
        "children playing vintage 1950s",
    ]),
    ("wiki_crime_scene_vintage", [6, 90], [
        "crime scene vintage police",
        "police investigation 1950s",
    ]),
    ("wiki_men_meeting_1950s", [49, 50, 54, 55, 56], [
        "men meeting government 1950s",
        "government officials meeting room",
    ]),
    ("wiki_cocktail_1950s", [52, 53], [
        "cocktail party 1950s",
        "vintage cocktail drinks",
    ]),
    ("wiki_classified_stamp", [4, 66, 79, 114, 156, 160], [
        "classified document stamp",
        "top secret stamp document",
        "redacted CIA document",
    ]),
    ("wiki_newspaper_1953", [9], [
        "newspaper 1953 headline",
        "newspaper front page 1950s",
    ]),
    ("wiki_cold_war_propaganda", [25, 27, 36], [
        "Cold War propaganda poster",
        "nuclear fallout shelter sign",
    ]),
    ("wiki_korean_war_pow", [26], [
        "Korean War prisoners",
        "Korean War POW captives",
    ]),
    ("wiki_mental_institution", [42, 43], [
        "psychiatric hospital ward 1950s",
        "mental institution patients",
    ]),
    ("wiki_mkultra_experiments", [37], [
        "sensory deprivation experiment",
        "electroshock therapy 1950s",
    ]),
    ("wiki_forensic_examination", [93, 119, 121, 122, 123, 124, 125, 127, 130], [
        "forensic examination laboratory",
        "forensic pathology",
    ]),
    ("wiki_calendar_vintage", [47, 98, 148], [
        "calendar 1953 vintage",
        "calendar pages time passing",
    ]),
    ("wiki_telephone_1970s", [109, 110], [
        "telephone call emotional",
        "woman telephone receiver 1970s",
    ]),
    ("wiki_reading_newspaper", [108], [
        "reading newspaper shocked",
        "newspaper discovery revelation",
    ]),
    ("wiki_rockefeller_commission", [106], [
        "Rockefeller Commission 1975 CIA",
        "Nelson Rockefeller CIA commission report",
    ]),
    ("wiki_sandoz_lsd", [39], [
        "Sandoz pharmaceutical LSD",
        "Albert Hofmann LSD laboratory",
    ]),
    ("wiki_case_closed", [96, 134], [
        "case closed file folder",
        "closed case folder documents",
    ]),
    ("wiki_silence_censorship", [94, 95, 115, 141, 145], [
        "censorship press freedom",
        "government secrecy classified",
    ]),
    ("wiki_truth_documents", [103, 152, 153, 154], [
        "documents revealed truth",
        "evidence documents pile",
    ]),
    ("wiki_man_trapped", [64, 77, 157, 158], [
        "man silhouette trapped",
        "man cornered shadow",
    ]),
    ("wiki_government_building", [166, 168, 170], [
        "government building marble columns",
        "imposing government architecture",
    ]),
    ("wiki_cemetery_grave", [119, 120], [
        "cemetery grave",
        "graveyard forensic investigation",
    ]),
    ("wiki_settlement_check", [116], [
        "government check United States Treasury",
        "compensation settlement document",
    ]),
    ("wiki_wormwood_documentary", [142, 144], [
        "documentary film production",
        "documentary filmmaker interview",
    ]),
    ("wiki_consent_form", [41, 44], [
        "medical consent form vintage",
        "military security clearance document",
    ]),
    ("wiki_man_walking_free", [138, 139], [
        "man walking away street",
        "person walking freedom",
    ]),
    ("wiki_whisper_secret", [73, 74], [
        "whispering secret confidential",
        "man telling secret",
    ]),
    ("wiki_blunt_weapon", [126, 129], [
        "forensic evidence crime",
        "weapon evidence forensic",
    ]),
    ("wiki_robert_lashbrook", [5, 89, 139], [
        "man suit 1950s government",
        "government agent 1950s portrait",
    ]),
]


def search_commons(query, limit=10):
    params = {
        "action": "query", "list": "search", "srsearch": query,
        "srnamespace": 6, "format": "json", "srlimit": limit,
    }
    resp = requests.get(API_URL, params=params,
                        headers={"User-Agent": API_USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("query", {}).get("search", [])


def get_image_info(title):
    params = {
        "action": "query", "titles": title, "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata|thumbmime",
        "iiurlwidth": THUMB_WIDTH, "format": "json",
    }
    resp = requests.get(API_URL, params=params,
                        headers={"User-Agent": API_USER_AGENT}, timeout=30)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})
    for pid, pdata in pages.items():
        if pid == "-1":
            return None
        ii = (pdata.get("imageinfo") or [None])[0]
        if not ii:
            return None
        mime = ii.get("mime", "")
        # Skip non-photos
        if not mime.startswith("image/") or any(x in mime for x in ["svg", "djvu"]):
            return None
        ext_url = ii.get("url", "")
        ext = os.path.splitext(urllib.parse.urlparse(ext_url).path)[1].lower()
        if ext not in PREFERRED_EXTS:
            return None
        # Use thumbnail if original is large
        thumb_url = ii.get("thumburl", "")
        if thumb_url and ii.get("width", 0) > THUMB_WIDTH:
            url = thumb_url
        else:
            url = ext_url
        return {
            "title": title, "url": url, "orig_url": ext_url,
            "size": ii.get("size", 0),
            "width": ii.get("width", 0), "height": ii.get("height", 0),
            "mime": mime,
        }
    return None


def download_file(url, dest):
    headers = {
        "User-Agent": DOWNLOAD_USER_AGENT,
        "Accept": "image/*,*/*;q=0.8",
        "Referer": "https://commons.wikimedia.org/",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        return True
    except Exception as e1:
        print(f"    urllib failed: {e1}")
        try:
            resp = requests.get(url, headers=headers, timeout=60, stream=True)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e2:
            print(f"    requests failed: {e2}")
            return False


def main():
    with open(SB_PATH) as f:
        sb = json.load(f)

    card_segs = {i for i, seg in enumerate(sb)
                 if seg.get("shot_type") in ("chapter_card", "title_card")}

    # ── Phase 1: Map existing images ──
    print("=" * 60)
    print("PHASE 1: Mapping existing images to segments")
    print("=" * 60)

    covered = {}  # seg_id -> image_path

    # Map from images/ dir
    for filename, seg_ids in EXISTING_MAPPINGS.items():
        path = IMG_DIR / filename
        if path.exists():
            for sid in seg_ids:
                covered[sid] = f"images/{filename}"
            print(f"  [OK] {filename} -> segs {seg_ids}")
        else:
            print(f"  [--] {filename} NOT FOUND on disk")

    # Map from wikimedia/ dir
    for filename, seg_ids in WIKIMEDIA_DIR_MAPPINGS.items():
        path = WIKI_DIR / filename
        if path.exists():
            for sid in seg_ids:
                if sid not in covered:
                    covered[sid] = f"../wikimedia/{filename}"
            print(f"  [OK] wikimedia/{filename} -> segs {seg_ids}")
        else:
            print(f"  [--] wikimedia/{filename} NOT FOUND on disk")

    need_image = set(range(len(sb))) - card_segs
    uncovered = need_image - set(covered.keys())
    print(f"\nPhase 1 coverage: {len(covered)}/{len(need_image)} segments")
    print(f"Still need: {len(uncovered)} segments")
    print(f"Uncovered: {sorted(uncovered)}")

    # ── Phase 2: Search & download missing ──
    print("\n" + "=" * 60)
    print("PHASE 2: Downloading missing images from Wikimedia Commons")
    print("=" * 60)

    downloaded = 0
    failed_groups = []

    for label, seg_ids, queries in SEARCH_GROUPS:
        # Skip if all segments already covered
        needed = [s for s in seg_ids if s in uncovered]
        if not needed:
            continue

        print(f"\n[SEARCH] {label} (need segs {needed})")
        found = False

        for query in queries:
            if found:
                break
            print(f"  Trying: \"{query}\"")
            time.sleep(SLEEP_BETWEEN)

            try:
                results = search_commons(query, limit=8)
            except Exception as e:
                print(f"    Search error: {e}")
                continue

            if not results:
                print(f"    No results")
                continue

            # Check candidates
            for r in results:
                title = r.get("title", "")
                if not title:
                    continue
                time.sleep(0.5)
                info = get_image_info(title)
                if not info:
                    continue
                if info["width"] < 400 or info["height"] < 300:
                    continue

                # Download it
                ext = os.path.splitext(urllib.parse.urlparse(info["orig_url"]).path)[1].lower() or ".jpg"
                filename = f"{label}{ext}"
                dest = IMG_DIR / filename

                print(f"  -> {info['title'][:55]} ({info['width']}x{info['height']})")

                if download_file(info["url"], dest):
                    sz = dest.stat().st_size
                    if sz < 5000:
                        print(f"    Too small ({sz}B), skipping")
                        dest.unlink()
                        continue
                    print(f"  [OK] {filename} ({sz:,}B)")
                    for sid in seg_ids:
                        covered[sid] = f"images/{filename}"
                    found = True
                    downloaded += 1
                    break

        if not found:
            print(f"  [FAIL] {label}")
            failed_groups.append(label)

    # ── Phase 3: Update manifest ──
    print("\n" + "=" * 60)
    print("PHASE 3: Updating manifest")
    print("=" * 60)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    # Remove old pixabay entries
    manifest["images"] = [img for img in manifest.get("images", [])
                          if img.get("source") != "pixabay"]

    # Build image entries grouped by filename
    file_to_segs = {}
    for sid, fpath in covered.items():
        file_to_segs.setdefault(fpath, []).append(sid)

    # Replace all image entries with our verified mappings
    manifest["images"] = []
    for fpath, sids in sorted(file_to_segs.items()):
        manifest["images"].append({
            "filename": fpath,
            "source": "wikimedia_commons",
            "storyboard_segment_ids": sorted(set(sids)),
        })

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    # ── Summary ──
    uncovered_final = need_image - set(covered.keys())
    print(f"\nTotal segments: {len(sb)}")
    print(f"Card segments (no image needed): {len(card_segs)}")
    print(f"Segments needing images: {len(need_image)}")
    print(f"Segments covered: {len(need_image) - len(uncovered_final)}")
    print(f"Segments still uncovered: {len(uncovered_final)}")
    if uncovered_final:
        print(f"Uncovered IDs: {sorted(uncovered_final)}")
    print(f"\nDownloaded: {downloaded}")
    print(f"Failed: {len(failed_groups)}")
    if failed_groups:
        print(f"Failed groups: {failed_groups}")
    print(f"\nManifest: {len(manifest['images'])} image entries")

    return 0


if __name__ == "__main__":
    sys.exit(main())
