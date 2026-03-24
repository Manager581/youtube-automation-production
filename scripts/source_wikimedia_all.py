#!/usr/bin/env python3
"""
Source ALL storyboard images from Wikimedia Commons.
NO Pixabay. Wikimedia only. Free API, no key needed.

Groups segments by subject to minimize duplicate downloads,
then maps each image back to all segments that need it.
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

# --- Config ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SB_PATH = PROJECT_ROOT / "storyboards/frank_olson_cia_scientist_lsd_murder_cover_up.json"
MANIFEST_PATH = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/manifest.json"
IMG_DIR = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images"

API_USER_AGENT = "WikimediaDocSourcer/1.0 (documentary-research; educational-use) python-requests/2.31"
DOWNLOAD_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
API_URL = "https://commons.wikimedia.org/w/api.php"
MIN_SIZE_BYTES = 50_000
PREFERRED_EXTS = {".jpg", ".jpeg", ".png"}
SLEEP_BETWEEN = 2.0  # Polite rate limiting to avoid 429s
THUMB_WIDTH = 1920  # Request 1920px thumbnails (enough for 1080p video)

# ============================================================
# IMAGE GROUPS: (label, segment_ids, [search_queries])
# Each group = one image, potentially used by multiple segments.
# Queries tried in order — first successful download wins.
# ============================================================
IMAGE_GROUPS = [
    # === PEOPLE ===
    # Frank Olson — ALREADY HAVE as wiki_Frank_Olsen_1910-1953.jpg.jpg
    # Sidney Gottlieb — ALREADY HAVE as wiki_Sidney_Gottlieb_photo.jpg.jpg
    # Allen Dulles — ALREADY HAVE as wiki_allen_dulles.jpg
    # William Colby — ALREADY HAVE as wiki_william_colby.jpg
    # Gerald Ford — ALREADY HAVE as wiki_gerald_ford.jpg
    # Frank Church — ALREADY HAVE as wiki_frank_church_senator.jpg

    ("eric_olson", [72, 117, 146, 159, 164], [
        "Eric Olson Frank Olson son",
        "Wormwood Frank Olson documentary",
        "Frank Olson family justice",
    ]),
    ("errol_morris", [143], [
        "Errol Morris filmmaker",
        "Errol Morris documentary director",
        "Errol Morris portrait",
    ]),
    ("harold_abramson", [81], [
        "psychiatrist office 1950s",
        "doctor office vintage 1950s",
        "medical office vintage",
    ]),
    ("robert_lashbrook", [5, 89, 139], [
        "CIA officer 1950s portrait",
        "government agent 1950s man suit",
        "man in suit 1950s government",
    ]),

    # === LOCATIONS ===
    # Hotel Statler — ALREADY HAVE as wiki_hotel_statler_entrance.jpg
    # NYC skyline — ALREADY HAVE as wiki_nyc_skyline_1950s_night.jpg
    # CIA HQ — ALREADY HAVE as wiki_cia_headquarters.jpg

    ("fort_detrick_exterior", [16, 17, 22, 65, 167], [
        "Fort Detrick biological",
        "Camp Detrick army",
        "biological defense laboratory army",
        "military base Maryland 1950s",
    ]),
    # Fort Detrick lab — ALREADY HAVE as wiki_bacteriological_laboratory.jpg
    ("pentagon", [28], [
        "Pentagon aerial view",
        "Pentagon building Washington",
        "United States Pentagon",
    ]),
    ("deep_creek_lodge", [48], [
        "Deep Creek Lake Maryland cabin",
        "Deep Creek Lodge Maryland",
        "Maryland mountain cabin 1950s",
        "rustic lodge Maryland",
    ]),
    ("manhattan_da_office", [132], [
        "Manhattan District Attorney",
        "New York County courthouse",
        "Manhattan criminal courts building",
    ]),
    ("washington_dc_station", [84], [
        "Union Station Washington DC",
        "Washington DC train station 1950s",
        "Union Station 1950s",
    ]),
    ("frederick_maryland", [63, 120], [
        "Frederick Maryland",
        "Frederick Maryland 1950s",
        "Frederick Maryland downtown",
        "Frederick Maryland cemetery",
    ]),

    # === DOCUMENTS & EVIDENCE ===
    ("mkultra_document", [8, 29, 33, 105], [
        "MKUltra document",
        "MKULTRA declassified",
        "MKUltra CIA document",
        "Project MKUltra",
    ]),
    ("classified_document", [4, 66, 79, 114, 156, 160], [
        "classified document",
        "top secret document stamp",
        "classified stamp document",
        "redacted document government",
    ]),
    ("rockefeller_commission", [106], [
        "Rockefeller Commission",
        "Rockefeller Commission 1975",
        "Nelson Rockefeller commission CIA",
    ]),
    ("newspaper_headline_1953", [9], [
        "newspaper 1953",
        "newspaper headline Cold War 1950s",
        "New York Times 1953",
    ]),
    ("cold_war_propaganda", [25, 26, 27, 36], [
        "Cold War propaganda poster",
        "Cold War nuclear fallout shelter",
        "Cold War propaganda",
        "Korean War prisoners",
    ]),
    ("korean_war_pow", [26], [
        "Korean War prisoners",
        "Korean War POW",
        "prisoners of war Korea",
        "Korean War captives",
    ]),

    # === SCIENCE & MEDICAL ===
    ("lsd_molecule", [38, 67], [
        "LSD molecule",
        "lysergic acid diethylamide",
        "LSD chemical structure",
        "LSD-25",
    ]),
    ("sandoz_lsd", [39], [
        "Sandoz LSD",
        "Sandoz pharmaceutical",
        "Sandoz laboratory Basel",
        "Albert Hofmann LSD",
    ]),
    ("laboratory_1950s", [20, 35], [
        "chemistry laboratory 1950s",
        "scientific laboratory vintage",
        "laboratory microscope vintage",
        "chemical laboratory university",
    ]),
    ("mental_institution", [42, 43], [
        "mental institution 1950s",
        "psychiatric hospital ward",
        "mental asylum patients",
        "psychiatric hospital 1950s",
    ]),
    ("biological_weapons_test", [70], [
        "biological weapons test",
        "biological warfare testing",
        "chemical warfare test military",
        "Gruinard Island anthrax",
    ]),
    ("mkultra_experiments", [37], [
        "MKUltra experiment",
        "sensory deprivation experiment",
        "CIA experiment human",
        "electroshock therapy 1950s",
    ]),
    ("forensic_examination", [93, 119, 121, 122, 123, 124, 125, 127, 130], [
        "forensic examination",
        "forensic pathology",
        "forensic science laboratory",
        "autopsy forensic",
    ]),
    ("exhumation_cemetery", [119, 120], [
        "exhumation",
        "grave exhumation forensic",
        "cemetery forensic investigation",
    ]),

    # === VISUAL METAPHORS ===
    ("broken_glass", [10, 92, 128], [
        "broken window glass",
        "shattered glass",
        "broken window",
        "smashed window glass shards",
    ]),
    ("dark_hallway", [62, 68, 78, 83], [
        "dark hallway door",
        "dark corridor",
        "ominous hallway",
        "long dark corridor",
    ]),
    ("interrogation_room", [40], [
        "interrogation room",
        "empty chair spotlight",
        "interrogation police room",
    ]),
    ("empty_courtroom", [13, 135], [
        "empty courtroom",
        "courtroom gavel",
        "courtroom judge bench",
        "scales of justice courtroom",
    ]),
    ("fog_mystery", [12, 161, 163, 171], [
        "fog road",
        "foggy path mysterious",
        "fog forest dark",
        "mysterious fog",
    ]),
    ("hotel_room_interior", [88, 89], [
        "hotel room 1950s",
        "vintage hotel room interior",
        "hotel room bed 1950s",
        "old hotel room dark",
    ]),
    ("man_distressed", [58, 59, 76], [
        "man distressed dark room",
        "man alone worried",
        "anxious man shadow",
        "psychological distress",
    ]),
    ("woman_1950s_home", [60, 61, 99], [
        "woman telephone 1950s",
        "1950s housewife telephone",
        "woman worried 1950s home",
        "vintage woman telephone call",
    ]),
    ("suburban_house_1950s", [3, 63], [
        "suburban house 1950s",
        "American suburban house 1950s",
        "1950s house United States",
    ]),
    ("man_at_desk_documents", [118, 133, 147, 172, 173], [
        "man reviewing documents desk",
        "detective cold case files",
        "investigator desk papers",
        "man studying documents office",
    ]),
    ("venetian_blinds_window", [91], [
        "venetian blind window",
        "window venetian blinds interior",
        "venetian blinds light",
    ]),
    ("children_1950s", [100, 101, 102], [
        "children 1950s",
        "American children 1950s",
        "children playing 1950s",
        "family children 1960s",
    ]),
    ("crime_scene_1950s", [6, 90], [
        "crime scene 1950s",
        "police crime scene vintage",
        "crime scene investigation vintage",
        "New York police 1950s",
    ]),
    ("men_meeting_1950s", [49, 50, 54, 55, 56], [
        "men meeting 1950s government",
        "government officials meeting 1950s",
        "men in suits meeting 1950s",
        "conference room 1950s men",
    ]),
    ("liquor_bottle_1950s", [52, 53], [
        "cocktail 1950s",
        "liquor bottles vintage bar",
        "pouring drink 1950s",
        "vintage cocktail bar",
    ]),
    ("consent_form_medical", [41, 44], [
        "medical consent form",
        "medical form document vintage",
        "security clearance document",
        "military medical form",
    ]),
    ("calendar_pages", [47, 98, 148], [
        "calendar pages",
        "vintage calendar",
        "calendar 1953",
        "calendar pages turning time",
    ]),
    ("telephone_call_emotional", [109, 110], [
        "telephone call 1970s",
        "woman telephone receiver emotion",
        "telephone conversation vintage",
    ]),
    ("reading_newspaper_shock", [108], [
        "woman reading newspaper shocked",
        "reading newspaper discovery",
        "newspaper shocking revelation",
    ]),
    ("settlement_payment", [116], [
        "government check payment",
        "compensation settlement document",
        "official check United States Treasury",
    ]),
    ("wormwood_documentary", [142, 144], [
        "Wormwood documentary Netflix",
        "Wormwood Errol Morris",
        "Frank Olson Wormwood",
    ]),
    ("cia_europe_operations", [71], [
        "CIA operations Europe Cold War",
        "Cold War espionage Europe",
        "CIA covert operations",
    ]),
    ("powerful_institution", [166, 168], [
        "government building marble columns",
        "government power institution",
        "marble columns government building",
        "imposing government architecture",
    ]),
    ("man_walking_free", [138, 139], [
        "man walking away freedom",
        "person leaving unpunished",
        "man walking street free",
    ]),
    ("case_closed_file", [96, 134], [
        "case file closed",
        "file folder closed case",
        "closed case folder",
    ]),
    ("silence_suppression", [94, 95, 115, 141, 145], [
        "silence shh finger lips",
        "censorship suppression",
        "official statement government",
        "no comment press",
    ]),
    ("truth_revealed_light", [103, 152, 153, 154], [
        "document revealed light",
        "truth revealed document",
        "evidence pile documents",
        "light truth revelation",
    ]),
    ("man_trapped_shadow", [64, 77, 157, 158], [
        "man trapped shadow",
        "no exit door locked",
        "man cornered no escape",
        "trapped silhouette door",
    ]),
    ("secret_whisper", [73, 74], [
        "man whispering secret",
        "whispering confidential",
        "telling secret whisper",
    ]),
    ("blunt_object_weapon", [126, 129], [
        "forensic evidence weapon",
        "crime weapon evidence",
        "blunt force weapon forensic",
    ]),
]


def search_commons(query: str, limit: int = 10) -> list[dict]:
    """Search Wikimedia Commons for files matching query."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": 6,
        "format": "json",
        "srlimit": limit,
    }
    headers = {"User-Agent": API_USER_AGENT}
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json().get("query", {}).get("search", [])


def get_image_info(title: str) -> dict | None:
    """Get URL, size, mime, and license info for a Commons file.

    Uses iiurlwidth to request a thumbnail URL (avoids 429 on huge originals).
    """
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata|thumbmime",
        "iiurlwidth": THUMB_WIDTH,  # Request thumbnail URL
        "format": "json",
    }
    headers = {"User-Agent": API_USER_AGENT}
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})
    for page_id, page_data in pages.items():
        if page_id == "-1":
            return None
        ii_list = page_data.get("imageinfo", [])
        if not ii_list:
            return None
        ii = ii_list[0]
        ext = ii.get("extmetadata", {})
        license_short = ext.get("LicenseShortName", {}).get("value", "Unknown")
        artist = ext.get("Artist", {}).get("value", "Unknown")
        artist = re.sub(r"<[^>]+>", "", artist).strip()
        description = ext.get("ImageDescription", {}).get("value", "")
        description = re.sub(r"<[^>]+>", "", description).strip()

        # Prefer thumbnail URL (smaller, won't get 429'd)
        # Fall back to original if image is already small enough
        thumb_url = ii.get("thumburl", "")
        orig_url = ii.get("url", "")
        thumb_w = ii.get("thumbwidth", 0)
        thumb_h = ii.get("thumbheight", 0)

        # Use thumbnail if available and original is larger than we need
        if thumb_url and ii.get("width", 0) > THUMB_WIDTH:
            use_url = thumb_url
            use_w = thumb_w
            use_h = thumb_h
        else:
            use_url = orig_url
            use_w = ii.get("width", 0)
            use_h = ii.get("height", 0)

        return {
            "title": title,
            "url": use_url,
            "orig_url": orig_url,
            "descriptionurl": ii.get("descriptionurl", ""),
            "size": ii.get("size", 0),
            "width": use_w,
            "height": use_h,
            "orig_width": ii.get("width", 0),
            "orig_height": ii.get("height", 0),
            "mime": ii.get("mime", ""),
            "license": license_short,
            "artist": artist,
            "description": description[:300],
        }
    return None


def download_file(url: str, dest: Path) -> bool:
    """Download file, trying urllib then requests."""
    headers = {
        "User-Agent": DOWNLOAD_USER_AGENT,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
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
        print(f"    [WARN] urllib failed: {e1}")
        try:
            resp = requests.get(url, headers=headers, timeout=60, stream=True)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e2:
            print(f"    [ERROR] requests also failed: {e2}")
            return False


def pick_best(candidates: list[dict]) -> dict | None:
    """Pick best candidate: prefer jpg/png photos, skip PDFs/SVGs/diagrams."""
    good = []
    for c in candidates:
        mime = c.get("mime", "").lower()
        # Skip non-image formats
        if any(bad in mime for bad in ["pdf", "svg", "djvu", "ogg", "video", "audio"]):
            continue
        # Must be image/*
        if not mime.startswith("image/"):
            continue
        # Check original URL extension (not thumbnail)
        orig_url = c.get("orig_url", c.get("url", ""))
        ext = os.path.splitext(urllib.parse.urlparse(orig_url).path)[1].lower()
        if ext not in PREFERRED_EXTS:
            continue
        # Prefer reasonable size originals
        if c.get("orig_width", 0) >= 400 and c.get("orig_height", 0) >= 300:
            good.append(c)

    if not good:
        # Fallback: any image with preferred extension
        for c in candidates:
            mime = c.get("mime", "").lower()
            if mime.startswith("image/") and "svg" not in mime:
                orig_url = c.get("orig_url", c.get("url", ""))
                ext = os.path.splitext(urllib.parse.urlparse(orig_url).path)[1].lower()
                if ext in PREFERRED_EXTS:
                    good.append(c)

    if not good:
        return None
    # Prefer larger original (higher quality source)
    good.sort(key=lambda c: c.get("orig_width", 0) * c.get("orig_height", 0), reverse=True)
    return good[0]


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # Check what we already have
    existing = set()
    for f in IMG_DIR.iterdir():
        existing.add(f.stem)

    # Load storyboard for reference
    with open(SB_PATH) as f:
        sb = json.load(f)

    print(f"Storyboard segments: {len(sb)}")
    print(f"Image groups to source: {len(IMAGE_GROUPS)}")
    print(f"Existing images in dir: {len(existing)}")
    print()

    # Track results
    results = {}  # label -> {path, segment_ids, ...}
    downloaded = 0
    skipped = 0
    failed = 0

    for label, seg_ids, queries in IMAGE_GROUPS:
        # Check if already downloaded
        already = None
        for ext in [".jpg", ".jpeg", ".png"]:
            candidate = f"wiki_{label}"
            if candidate in existing:
                already = candidate + ext
                break
            # Also check without wiki_ prefix
            if label in existing:
                already = label + ext
                break

        if already and (IMG_DIR / already).exists():
            print(f"[SKIP] {label} — already exists as {already}")
            results[label] = {
                "filename": already,
                "segment_ids": seg_ids,
                "status": "existing",
            }
            skipped += 1
            continue

        print(f"[SEARCH] {label} (segments {seg_ids})")
        found = False

        for query in queries:
            if found:
                break
            print(f"  Trying: \"{query}\"")
            time.sleep(SLEEP_BETWEEN)

            try:
                search_results = search_commons(query, limit=10)
            except Exception as e:
                print(f"    Search error: {e}")
                continue

            if not search_results:
                print(f"    No results")
                continue

            # Get image info for candidates
            candidates = []
            for r in search_results:
                title = r.get("title", "")
                if not title:
                    continue
                time.sleep(0.3)
                info = get_image_info(title)
                if info:
                    candidates.append(info)

            if not candidates:
                continue

            best = pick_best(candidates)
            if not best:
                continue

            # Download
            url_path = urllib.parse.urlparse(best["url"]).path
            ext = os.path.splitext(url_path)[1].lower() or ".jpg"
            filename = f"wiki_{label}{ext}"
            dest = IMG_DIR / filename

            print(f"  -> {best['title'][:60]}")
            print(f"     {best['width']}x{best['height']}, {best['size']:,}B, {best['license']}")

            if download_file(best["url"], dest):
                actual_size = dest.stat().st_size
                if actual_size < 1000:
                    print(f"    [WARN] File too small ({actual_size}B), removing")
                    dest.unlink()
                    continue
                print(f"  [OK] {filename} ({actual_size:,}B)")
                found = True
                downloaded += 1
                results[label] = {
                    "filename": filename,
                    "segment_ids": seg_ids,
                    "source": "wikimedia_commons",
                    "source_url": best["url"],
                    "commons_page": best["descriptionurl"],
                    "title": best["title"],
                    "width": best["width"],
                    "height": best["height"],
                    "license": best["license"],
                    "artist": best["artist"],
                    "description": best["description"],
                    "search_query_used": query,
                    "status": "downloaded",
                }

        if not found:
            print(f"  [FAIL] Could not find/download: {label}")
            results[label] = {
                "segment_ids": seg_ids,
                "status": "not_found",
                "queries_tried": queries,
            }
            failed += 1
        print()

    # === Update manifest ===
    print("=" * 60)
    print(f"Downloaded: {downloaded}, Skipped (existing): {skipped}, Failed: {failed}")
    print()

    # Build new images list for manifest
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    # Remove old pixabay images (if any remain)
    manifest["images"] = [img for img in manifest.get("images", [])
                          if img.get("source") != "pixabay"]

    # Add/update wikimedia images
    existing_wiki = {img.get("filename"): i for i, img in enumerate(manifest.get("images", []))}

    for label, info in results.items():
        if info["status"] == "not_found":
            continue
        filename = info.get("filename", "")
        if not filename:
            continue

        img_entry = {
            "filename": f"images/{filename}",
            "source": "wikimedia_commons",
            "storyboard_segment_ids": info["segment_ids"],
        }
        if info["status"] == "downloaded":
            img_entry.update({
                "source_url": info.get("source_url", ""),
                "title": info.get("title", ""),
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "license": info.get("license", ""),
                "artist": info.get("artist", ""),
            })

        key = f"images/{filename}"
        if key in existing_wiki:
            manifest["images"][existing_wiki[key]] = img_entry
        else:
            manifest["images"].append(img_entry)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest updated: {len(manifest['images'])} images")

    # === Coverage report ===
    covered_segs = set()
    for info in results.values():
        if info["status"] != "not_found":
            for sid in info.get("segment_ids", info.get("segment_ids", [])):
                covered_segs.add(sid)

    # Chapter cards don't need images
    card_segs = {i for i, seg in enumerate(sb) if seg.get("shot_type") in ("chapter_card", "title_card")}
    need_image = set(range(len(sb))) - card_segs
    uncovered = need_image - covered_segs

    print(f"\nSegments needing images: {len(need_image)}")
    print(f"Segments covered: {len(covered_segs & need_image)}")
    print(f"Segments uncovered: {len(uncovered)}")
    if uncovered:
        print(f"Uncovered IDs: {sorted(uncovered)}")

    # Save metadata
    meta_path = IMG_DIR / "wikimedia_source_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nMetadata saved to: {meta_path}")

    return 0 if failed < len(IMAGE_GROUPS) // 2 else 1


if __name__ == "__main__":
    sys.exit(main())
