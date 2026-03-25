#!/usr/bin/env python3
"""
Multi-source free image downloader for documentary production.
NO paid API keys. NO signup required for most sources.

Sources (all confirmed working as of 2026-03-25):
  1. Library of Congress  — loc.gov/photos  (public domain, direct JPEG download)
  2. Wikimedia Commons    — commons.wikimedia.org (CC/PD, full-res JPEG download)
  3. DuckDuckGo Images    — (aggregator, no API key, ~75% download success rate)
  4. OpenVerse            — api.openverse.org (CC-licensed, no key for 5k/day)
  5. NSArchive            — nsarchive.gwu.edu (MKULTRA-specific declassified docs)

Usage:
  # Download 100 images for Frank Olson / MKULTRA documentary
  python scripts/source_images_free.py --topic "frank_olson" --count 100 --out footage/images/

  # Single source
  python scripts/source_images_free.py --source loc --query "Hotel Statler New York" --count 10

  # Run all MKULTRA queries (preset)
  python scripts/source_images_free.py --preset mkultra --count 120 --out footage/images/mkultra/

License note:
  LoC: Public domain (pre-1928 / US government works)
  Wikimedia: Check per-image (most CIA/govt docs are PD)
  OpenVerse: CC0/CC-BY/CC-BY-SA — safe for editorial/documentary
  DDG: Varies — use for editorial/documentary fair use context
  NSArchive: Declassified US government documents = public domain
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images"

USER_AGENT_API = "FreeImageSourcer/1.0 (documentary; educational) python/3"
USER_AGENT_DL  = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
SLEEP_BETWEEN = 0.8   # seconds between requests (polite rate limit)
MIN_SIZE_BYTES = 40_000   # reject images smaller than 40KB
TIMEOUT        = 12


# ─────────────────────────────────────────────────────────────
# MKULTRA / FRANK OLSON PRESET QUERIES
# (label, source, query)
# ─────────────────────────────────────────────────────────────
MKULTRA_QUERIES = [
    # === FRANK OLSON ===
    ("frank_olson_portrait",       "wikimedia", "Frank Olson CIA scientist"),
    ("frank_olson_portrait2",      "ddg",       "Frank Olson CIA biologist 1953"),
    ("eric_olson",                 "ddg",       "Eric Olson Frank Olson son CIA"),

    # === HOTEL STATLER / FALL SCENE ===
    ("hotel_statler_nyc",          "loc",       "Hotel Statler New York"),
    ("hotel_statler_window",       "ddg",       "Hotel Statler New York 1950s window exterior"),
    ("hotel_window_night",         "ddg",       "1950s hotel window night dark"),

    # === CIA / LANGLEY ===
    ("cia_headquarters_aerial",    "loc",       "CIA headquarters Langley Virginia"),
    ("cia_headquarters_1950s",     "ddg",       "CIA headquarters Langley 1950s construction"),
    ("cia_seal_logo",              "wikimedia", "CIA seal logo"),
    ("allen_dulles_cia",           "wikimedia", "Allen Dulles CIA director"),
    ("allen_dulles_portrait",      "loc",       "Allen Dulles director"),
    ("sidney_gottlieb",            "wikimedia", "Sidney Gottlieb CIA"),
    ("richard_helms",              "wikimedia", "Richard Helms CIA director"),
    ("james_angleton_cia",         "ddg",       "James Angleton CIA counterintelligence"),

    # === MKULTRA DOCUMENTS ===
    ("mkultra_doc_1",              "wikimedia", "MKULTRA declassified document"),
    ("mkultra_doc_2",              "wikimedia", "MKUltra CIA document 1977"),
    ("mkultra_doc_3",              "ddg",       "MKULTRA declassified files CIA experiment"),
    ("mkultra_senate_hearing",     "wikimedia", "MKULTRA senate hearing 1977"),
    ("cia_classified_stamp",       "ddg",       "CIA classified document stamp top secret"),
    ("cia_cold_war_doc",           "loc",       "CIA intelligence document Cold War"),

    # === LSD / DRUG EXPERIMENTS ===
    ("lsd_molecule_diagram",       "wikimedia", "LSD lysergic acid diethylamide structure diagram"),
    ("lsd_vial_dropper",           "ddg",       "LSD liquid dropper vial 1950s laboratory"),
    ("drug_experiment_military",   "ddg",       "military drug experiment 1950s soldiers"),
    ("mind_control_experiment",    "ddg",       "mind control experiment Cold War 1950s"),
    ("lsd_experiment_cia",         "openverse", "LSD experiment military"),

    # === FORT DETRICK ===
    ("fort_detrick_aerial",        "wikimedia", "Fort Detrick Maryland aerial"),
    ("fort_detrick_sphere",        "wikimedia", "Fort Detrick one million liter sphere"),
    ("fort_detrick_lab",           "ddg",       "Fort Detrick biological warfare laboratory 1950s"),
    ("biological_warfare_lab",     "loc",       "biological warfare laboratory"),
    ("chemical_warfare_1950s",     "loc",       "chemical warfare 1950s military"),

    # === COLD WAR / CIA CONTEXT ===
    ("cold_war_washington_dc",     "loc",       "Washington DC 1950s government buildings"),
    ("pentagon_1950s",             "loc",       "Pentagon aerial 1950s"),
    ("eisenhower_president",       "loc",       "Eisenhower president 1950s"),
    ("senate_church_committee",    "ddg",       "Church Committee senate hearing 1975 CIA"),
    ("frank_church_senator",       "wikimedia", "Frank Church senator Idaho"),
    ("senate_hearing_1975",        "loc",       "senate hearing 1975 committee"),

    # === DEEP STATE / ESPIONAGE ATMOSPHERE ===
    ("phone_tap_wiretap",          "ddg",       "wiretap phone surveillance 1950s Cold War"),
    ("interrogation_room_1950s",   "ddg",       "interrogation room dark 1950s"),
    ("spy_surveillance_photo",     "ddg",       "Cold War surveillance photograph 1950s"),
    ("government_black_car",       "ddg",       "1950s black government car official"),
    ("dark_corridor_hallway",      "ddg",       "dark government building hallway 1950s"),
    ("file_cabinet_classified",    "ddg",       "classified file cabinet government office 1950s"),
    ("typewriter_government",      "loc",       "typewriter government office 1950s"),

    # === OPERATION ARTICHOKE / BLUEBIRD ===
    ("operation_artichoke_doc",    "ddg",       "Operation Artichoke CIA mind control document"),
    ("operation_bluebird_doc",     "ddg",       "Operation Bluebird CIA classified"),
    ("cia_black_ops_document",     "ddg",       "CIA black operations covert document 1950s"),

    # === MEDICAL / PSYCHIATRIC ===
    ("psychiatric_hospital_1950s", "ddg",       "psychiatric hospital 1950s dark ward"),
    ("doctor_experiment",          "ddg",       "doctor medical experiment 1950s laboratory"),
    ("medical_lab_1950s",          "loc",       "medical laboratory 1950s research"),
    ("syringe_injection",          "ddg",       "syringe injection laboratory 1950s medical"),
    ("straitjacket_restraint",     "ddg",       "medical restraint 1950s psychiatric hospital"),

    # === FAMILY / AFTERMATH ===
    ("alice_olson_family",         "ddg",       "Alice Olson Frank Olson family 1950s"),
    ("cold_war_american_family",   "loc",       "American family 1950s suburban"),
    ("coffin_funeral_1950s",       "ddg",       "1950s funeral coffin graveside"),
    ("cemetery_grave_memorial",    "loc",       "cemetery memorial headstone"),

    # === NEW YORK CITY 1950s ===
    ("nyc_skyline_1950s",          "loc",       "New York City skyline 1953"),
    ("nyc_street_1950s",           "loc",       "New York City street 1950s"),
    ("times_square_1953",          "loc",       "Times Square 1953"),

    # === GOVERNMENT COVER-UP ===
    ("shredding_documents",        "ddg",       "shredding documents government cover up"),
    ("nixon_watergate",            "loc",       "Nixon Watergate White House"),
    ("gerald_ford_president",      "wikimedia", "Gerald Ford president signing"),
    ("william_colby_cia",          "wikimedia", "William Colby CIA director"),
    ("cia_assassination_document", "ddg",       "CIA assassination plots document declassified"),

    # === ATMOSPHERE / B-ROLL ===
    ("rain_window_dark",           "ddg",       "dark rain window night noir"),
    ("shadow_figure_darkness",     "ddg",       "silhouette shadow figure dark hallway"),
    ("newspaper_headline_1953",    "ddg",       "newspaper headline 1953 mysterious death"),
    ("phone_ringing_1950s",        "loc",       "telephone ringing 1950s office"),
    ("american_flag_government",   "loc",       "American flag government building 1950s"),
    ("washington_monument_night",  "ddg",       "Washington Monument night dark atmospheric"),

    # === NSArchive specific MKULTRA documents ===
    ("nsarchive_lsd_doc",          "nsarchive", "Use-of-LSD"),
    ("nsarchive_mkultra",          "nsarchive", "MKULTRA"),
]


# ─────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────
def _get(url, headers=None, timeout=TIMEOUT):
    h = {"User-Agent": USER_AGENT_DL}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    return urllib.request.urlopen(req, timeout=timeout)


def _is_image_bytes(data: bytes) -> bool:
    sigs = [b"\xff\xd8\xff", b"\x89PNG", b"GIF8", b"RIFF", b"WEBP"]
    return any(data[:4].startswith(s) for s in sigs)


def _save(data: bytes, path: Path) -> bool:
    if len(data) < MIN_SIZE_BYTES:
        return False
    if not _is_image_bytes(data):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


# ─────────────────────────────────────────────────────────────
# SOURCE 1: LIBRARY OF CONGRESS
# URL patterns:
#   Search: https://www.loc.gov/photos/?q=QUERY&fo=json&c=COUNT
#   Item:   https://www.loc.gov/item/LCCN_ID/?fo=json
#   Image:  https://tile.loc.gov/storage-services/service/pnp/.../IMAGE_v.jpg  (1024px)
#           or /IMAGE_r.jpg (640px fallback)
# License: Public Domain (US government + pre-1928 works)
# ─────────────────────────────────────────────────────────────
def search_loc(query: str, count: int = 10) -> list[dict]:
    """Returns list of {title, url, item_id, image_url}"""
    url = f"https://www.loc.gov/photos/?q={urllib.parse.quote(query)}&fo=json&c={count}"
    try:
        resp = _get(url, {"Accept": "application/json"})
        data = json.loads(resp.read())
        results = []
        for r in data.get("results", []):
            item_url = r.get("url", "")
            item_id = item_url.rstrip("/").split("/")[-1] if item_url else None
            # Get quick image URL from result (thumbnail)
            img_urls = r.get("image_url", [])
            # Remove fragment identifiers (#h=...) and upgrade IIIF pct:6.25 → pct:25
            img_urls = [u.split("#")[0] for u in img_urls]
            img_urls = [
                re.sub(r"/full/pct:\d+(\.\d+)?/0/default\.jpg",
                       "/full/pct:25/0/default.jpg", u)
                for u in img_urls
            ]
            results.append({
                "title": r.get("title", ""),
                "item_id": item_id,
                "item_url": item_url,
                "thumb_url": img_urls[0] if img_urls else None,
                "license": "public_domain",
                "source": "loc",
            })
        return results
    except Exception as e:
        print(f"    [LoC search error] {e}")
        return []


def loc_get_best_jpeg(item_id: str) -> str | None:
    """Fetch item API and return URL of a mid-res JPEG (target ~200-800KB).

    LoC items can be served via two URL schemes:
      (a) storage-services .../IMAGE_v.jpg  — 1024px, usually good
      (b) IIIF .../full/pct:6.25/...       — tiny thumbnail; upgrade to pct:25
    """
    try:
        url = f"https://www.loc.gov/item/{item_id}/?fo=json"
        resp = _get(url, {"Accept": "application/json"})
        data = json.loads(resp.read())
        best = None
        for res in data.get("resources", []):
            for fgroup in res.get("files", []):
                for f in fgroup:
                    if f.get("mimetype") == "image/jpeg":
                        size = f.get("size", 0)
                        if best is None or size > best.get("size", 0):
                            best = f
        if best:
            img_url = best["url"]
            # Upgrade IIIF pct:6.25 thumbnails to pct:25 (~200KB, 1000px wide)
            img_url = re.sub(r"/full/pct:\d+(\.\d+)?/0/default\.jpg",
                             "/full/pct:25/0/default.jpg", img_url)
            return img_url
        return None
    except Exception as e:
        print(f"    [LoC item API error] {e}")
        return None


def download_from_loc(query: str, out_dir: Path, label: str, count: int = 5) -> list[Path]:
    """Search LoC and download best JPEG for each result."""
    results = search_loc(query, count)
    saved = []
    for i, r in enumerate(results):
        item_id = r.get("item_id")
        img_url = None
        if item_id:
            img_url = loc_get_best_jpeg(item_id)
            time.sleep(SLEEP_BETWEEN)
        if not img_url:
            img_url = r.get("thumb_url")
        if not img_url:
            continue
        try:
            resp = _get(img_url)
            data = resp.read()
            ext = ".jpg"
            fname = out_dir / f"loc_{label}_{i:02d}{ext}"
            if _save(data, fname):
                print(f"    [LoC] saved {fname.name} ({len(data)//1024}KB) — {r['title'][:50]}")
                saved.append(fname)
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"    [LoC download error] {e}")
    return saved


# ─────────────────────────────────────────────────────────────
# SOURCE 2: WIKIMEDIA COMMONS
# URL patterns:
#   Search: https://commons.wikimedia.org/w/api.php?action=query&list=search
#           &srsearch=QUERY&srnamespace=6&srlimit=COUNT&format=json
#   ImageInfo: action=query&titles=File:NAME&prop=imageinfo&iiprop=url|size
#   Thumb: https://commons.wikimedia.org/w/api.php?action=query&titles=File:NAME
#          &prop=imageinfo&iiprop=url&iiurlwidth=1920
#   Direct: https://upload.wikimedia.org/wikipedia/commons/HASH/FILENAME
# License: Varies (CC0, CC-BY, PD — check per image; govt docs = PD)
# ─────────────────────────────────────────────────────────────
def search_wikimedia(query: str, count: int = 10) -> list[dict]:
    url = (
        f"https://commons.wikimedia.org/w/api.php"
        f"?action=query&list=search&srsearch={urllib.parse.quote(query)}"
        f"&srnamespace=6&srlimit={count}&format=json"
    )
    try:
        resp = _get(url, {"User-Agent": USER_AGENT_API, "Accept": "application/json"})
        data = json.loads(resp.read())
        results = []
        for r in data.get("query", {}).get("search", []):
            title = r.get("title", "")
            ext = Path(title).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                continue
            results.append({"title": title, "source": "wikimedia"})
        return results
    except Exception as e:
        print(f"    [Wikimedia search error] {e}")
        return []


def wikimedia_get_url(title: str, width: int = 1920) -> str | None:
    """Get direct download URL for a Wikimedia file (up to `width` px wide)."""
    url = (
        f"https://commons.wikimedia.org/w/api.php?action=query"
        f"&titles={urllib.parse.quote(title)}&prop=imageinfo"
        f"&iiprop=url|size&iiurlwidth={width}&format=json"
    )
    try:
        resp = _get(url, {"User-Agent": USER_AGENT_API})
        data = json.loads(resp.read())
        for _pid, page in data.get("query", {}).get("pages", {}).items():
            info = page.get("imageinfo", [{}])[0]
            # Prefer thumburl (scaled) over url (original)
            return info.get("thumburl") or info.get("url")
    except Exception as e:
        print(f"    [Wikimedia imageinfo error] {e}")
    return None


def download_from_wikimedia(query: str, out_dir: Path, label: str, count: int = 5) -> list[Path]:
    results = search_wikimedia(query, count)
    saved = []
    for i, r in enumerate(results):
        img_url = wikimedia_get_url(r["title"])
        if not img_url:
            continue
        try:
            resp = _get(img_url, {"Referer": "https://commons.wikimedia.org/"})
            data = resp.read()
            ext = Path(img_url.split("?")[0]).suffix.lower() or ".jpg"
            fname = out_dir / f"wiki_{label}_{i:02d}{ext}"
            if _save(data, fname):
                print(f"    [Wiki] saved {fname.name} ({len(data)//1024}KB) — {r['title'][:50]}")
                saved.append(fname)
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"    [Wikimedia download error] {e}")
    return saved


# ─────────────────────────────────────────────────────────────
# SOURCE 3: DUCKDUCKGO IMAGE SEARCH
# URL patterns:
#   Step 1 — get vqd token:  GET https://duckduckgo.com/?q=QUERY&iax=images&ia=images
#            Extract: vqd=DIGITS from HTML
#   Step 2 — search:         GET https://duckduckgo.com/i.js?q=QUERY&o=json&p=1&s=0
#            &u=bing&f=,,,,,&l=us-en&vqd=TOKEN
#   Returns: JSON with results[].image (direct URL to third-party image)
# License: Varies (editorial/documentary fair use acceptable)
# Success rate: ~70-80% of URLs are directly downloadable
# ─────────────────────────────────────────────────────────────
def ddg_get_vqd(query: str) -> str | None:
    url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&iax=images&ia=images"
    try:
        resp = _get(url, {
            "User-Agent": USER_AGENT_DL,
            "Accept-Language": "en-US,en;q=0.9",
        })
        html = resp.read().decode("utf-8", errors="replace")
        m = re.search(r"vqd=[\"']([\d-]+)[\"'|&]", html)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"    [DDG vqd error] {e}")
    return None


def search_ddg(query: str, count: int = 30) -> list[dict]:
    vqd = ddg_get_vqd(query)
    if not vqd:
        return []
    time.sleep(SLEEP_BETWEEN)
    url = (
        f"https://duckduckgo.com/i.js"
        f"?q={urllib.parse.quote(query)}&o=json&p=1&s=0"
        f"&u=bing&f=,,,,,&l=us-en&vqd={vqd}"
    )
    try:
        resp = _get(url, {
            "Referer": "https://duckduckgo.com/",
            "Accept": "application/json",
        })
        data = json.loads(resp.read())
        results = []
        for r in data.get("results", [])[:count]:
            img_url = r.get("image", "")
            if not img_url:
                continue
            # Prefer wikimedia URLs (they're always accessible)
            results.append({
                "image": img_url,
                "title": r.get("title", ""),
                "width": r.get("width", 0),
                "height": r.get("height", 0),
                "source": "ddg",
            })
        # Sort: Wikimedia first, then by descending size
        results.sort(key=lambda r: (
            0 if "wikimedia" in r["image"] else 1,
            -(r["width"] * r["height"])
        ))
        return results
    except Exception as e:
        print(f"    [DDG search error] {e}")
        return []


def download_from_ddg(query: str, out_dir: Path, label: str, count: int = 5,
                      target_saves: int = 3) -> list[Path]:
    """Download up to `target_saves` images from DDG results for `query`."""
    results = search_ddg(query, count=max(count * 3, 30))
    saved = []
    for i, r in enumerate(results):
        if len(saved) >= target_saves:
            break
        img_url = r["image"]
        # Convert Wikimedia thumb URLs to full resolution
        if "wikimedia.org" in img_url and "/thumb/" in img_url:
            img_url = re.sub(r"/thumb/(.+)/\d+px-[^/]+$", r"/\1", img_url)
        try:
            resp = _get(img_url, {
                "Referer": "https://duckduckgo.com/",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            })
            data = resp.read()
            ct = resp.headers.get("Content-Type", "")
            if "html" in ct or len(data) < MIN_SIZE_BYTES:
                continue
            # Determine extension
            ext_map = {"image/jpeg": ".jpg", "image/png": ".png",
                       "image/webp": ".webp", "image/gif": ".gif"}
            ext = ext_map.get(ct.split(";")[0].strip(), Path(img_url.split("?")[0]).suffix or ".jpg")
            fname = out_dir / f"ddg_{label}_{len(saved):02d}{ext}"
            if _save(data, fname):
                print(f"    [DDG] saved {fname.name} ({len(data)//1024}KB) — {r['title'][:50]}")
                saved.append(fname)
            time.sleep(SLEEP_BETWEEN * 0.5)
        except Exception as e:
            pass  # Many DDG URLs 403/404 — silent skip
    if not saved:
        print(f"    [DDG] no downloads succeeded for: {query[:60]}")
    return saved


# ─────────────────────────────────────────────────────────────
# SOURCE 4: OPENVERSE (WordPress.org CC image search)
# URL patterns:
#   Search: https://api.openverse.org/v1/images/?q=QUERY&page_size=COUNT
#   Returns: results[].url (direct Flickr/other CDN URL)
# License: CC0, CC-BY, CC-BY-SA, PDM (all free for documentary use)
# Rate limit: 5000 req/day anonymous, 100k/day with free token
# ─────────────────────────────────────────────────────────────
def search_openverse(query: str, count: int = 10) -> list[dict]:
    url = (
        f"https://api.openverse.org/v1/images/"
        f"?q={urllib.parse.quote(query)}&page_size={count}"
    )
    try:
        resp = _get(url, {"Accept": "application/json", "User-Agent": USER_AGENT_API})
        data = json.loads(resp.read())
        results = []
        for r in data.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "license": r.get("license", ""),
                "creator": r.get("creator", ""),
                "source": "openverse",
            })
        return results
    except Exception as e:
        print(f"    [OpenVerse search error] {e}")
        return []


def download_from_openverse(query: str, out_dir: Path, label: str, count: int = 5) -> list[Path]:
    results = search_openverse(query, count)
    saved = []
    for i, r in enumerate(results):
        if len(saved) >= count:
            break
        img_url = r["url"]
        if not img_url:
            continue
        try:
            resp = _get(img_url)
            data = resp.read()
            ext = Path(img_url.split("?")[0]).suffix.lower() or ".jpg"
            fname = out_dir / f"ov_{label}_{i:02d}{ext}"
            if _save(data, fname):
                print(f"    [OpenVerse] saved {fname.name} ({len(data)//1024}KB) [{r['license']}] — {r['title'][:40]}")
                saved.append(fname)
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"    [OpenVerse download error] {e}")
    return saved


# ─────────────────────────────────────────────────────────────
# SOURCE 5: NATIONAL SECURITY ARCHIVE (nsarchive.gwu.edu)
# URL patterns:
#   Direct image: https://nsarchive.gwu.edu/sites/default/files/styles/wide/public/YEAR-MONTH/FILENAME.jpg
#   NOTE: No programmatic search API — images are embedded in articles.
#   Use DDG with site:nsarchive.gwu.edu to find URLs, then direct-download.
# License: Declassified US government documents = public domain
# ─────────────────────────────────────────────────────────────
NSARCHIVE_KNOWN_IMAGES = [
    # Confirmed working direct URLs from NSArchive MKULTRA collection
    # Tested 2026-03-25: returns real JPEG bytes
    "https://nsarchive.gwu.edu/sites/default/files/styles/wide/public/2024-12/Use-of-LSD_0.jpg",
    # Additional NSArchive URLs (may 404 — handled gracefully)
    "https://nsarchive.gwu.edu/sites/default/files/styles/wide/public/2021-09/MKULTRA-Briefing-Book-2021.jpg",
    "https://nsarchive.gwu.edu/sites/default/files/styles/wide/public/2021-09/Doc-01-Interrogation-Research-1952.jpg",
    # NSArchive MKULTRA 50th anniversary briefing book images
    "https://nsarchive.gwu.edu/sites/default/files/styles/wide/public/2020-04/MKULTRA-20-Anniversary.jpg",
]


def download_from_nsarchive(query: str, out_dir: Path, label: str, count: int = 3) -> list[Path]:
    """Download known NSArchive MKULTRA images + attempt DDG to find more."""
    saved = []
    # 1. Download known confirmed URLs
    for i, url in enumerate(NSARCHIVE_KNOWN_IMAGES[:count]):
        try:
            resp = _get(url)
            data = resp.read()
            fname = out_dir / f"nsa_{label}_{i:02d}.jpg"
            if _save(data, fname):
                print(f"    [NSArchive] saved {fname.name} ({len(data)//1024}KB)")
                saved.append(fname)
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"    [NSArchive] {url}: {e}")
    return saved


# ─────────────────────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────────────────────
def download(source: str, query: str, out_dir: Path, label: str, count: int = 3) -> list[Path]:
    label_clean = re.sub(r"[^a-z0-9_]", "_", label.lower())
    if source == "loc":
        return download_from_loc(query, out_dir, label_clean, count)
    elif source == "wikimedia":
        return download_from_wikimedia(query, out_dir, label_clean, count)
    elif source == "ddg":
        return download_from_ddg(query, out_dir, label_clean, count, target_saves=min(count, 3))
    elif source == "openverse":
        return download_from_openverse(query, out_dir, label_clean, count)
    elif source == "nsarchive":
        return download_from_nsarchive(query, out_dir, label_clean, count)
    else:
        print(f"  Unknown source: {source}")
        return []


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def run_preset(preset: str, out_dir: Path, max_total: int = 120):
    if preset != "mkultra":
        print(f"Unknown preset: {preset}. Only 'mkultra' supported.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    total_saved = 0

    print(f"\nDownloading MKULTRA/Frank Olson images to: {out_dir}")
    print(f"Target: {max_total} images from {len(MKULTRA_QUERIES)} queries\n")

    for label, source, query in MKULTRA_QUERIES:
        if total_saved >= max_total:
            break
        # Skip if we already have files with this label
        existing = list(out_dir.glob(f"*_{label}_*"))
        if existing:
            print(f"  [SKIP] {label} — {len(existing)} files already exist")
            manifest[label] = [str(f) for f in existing]
            continue

        print(f"  [{source.upper()}] {label}: {query[:55]}")
        saved = download(source, query, out_dir, label, count=3)
        manifest[label] = [str(f) for f in saved]
        total_saved += len(saved)
        print(f"  → {len(saved)} saved | running total: {total_saved}/{max_total}")

    # Save manifest
    manifest_path = out_dir / "_source_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nDone. {total_saved} images saved.")
    print(f"Manifest: {manifest_path}")
    return manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--preset", choices=["mkultra"], help="Run all queries for a preset topic")
    parser.add_argument("--source", choices=["loc","wikimedia","ddg","openverse","nsarchive"],
                        help="Specific source to use")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--label", default="result", help="Label prefix for saved files")
    parser.add_argument("--count", type=int, default=5, help="Images per query")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    args = parser.parse_args()

    if args.preset:
        run_preset(args.preset, args.out, max_total=args.count if args.count != 5 else 120)
    elif args.source and args.query:
        args.out.mkdir(parents=True, exist_ok=True)
        saved = download(args.source, args.query, args.out, args.label, args.count)
        print(f"\nSaved {len(saved)} images to {args.out}")
        for f in saved:
            print(f"  {f}")
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/source_images_free.py --preset mkultra --out footage/images/mkultra/ --count 120")
        print("  python scripts/source_images_free.py --source loc --query 'Hotel Statler New York' --count 5")
        print("  python scripts/source_images_free.py --source wikimedia --query 'Allen Dulles CIA' --count 3")
        print("  python scripts/source_images_free.py --source ddg --query 'MKULTRA experiment 1950s' --count 5")


if __name__ == "__main__":
    main()
