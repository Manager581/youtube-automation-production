#!/usr/bin/env python3
"""
Batch image sourcer — downloads from Wikipedia and Wikimedia Commons.

For each entity/concept, gets the highest-res image from:
1. Wikipedia article main image
2. Wikimedia Commons direct search

Saves to footage/breaking_law/images_v2/web/
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path("footage/breaking_law/images_v2/web")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "DocumentaryImageSourcer/1.0 (production pipeline; contact: jlawrence8712@gmail.com)"}


def download(url, path, timeout=30):
    """Download URL to path. Returns True on success."""
    path = Path(path)
    if path.exists() and path.stat().st_size > 5000:
        return True
    try:
        if url.startswith("//"):
            url = "https:" + url
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if len(data) < 3000:
                return False
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"    FAIL: {e}")
        return False


def get_wikipedia_image(article_title):
    """Get the main image URL from a Wikipedia article via API."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": article_title,
        "prop": "pageimages",
        "piprop": "original",
        "format": "json",
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            orig = page.get("original", {})
            return orig.get("source")
    except Exception:
        pass
    return None


def get_wikipedia_all_images(article_title, limit=5):
    """Get all images from a Wikipedia article."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": article_title,
        "prop": "images",
        "imlimit": str(limit),
        "format": "json",
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        pages = data.get("query", {}).get("pages", {})
        filenames = []
        for page in pages.values():
            for img in page.get("images", []):
                title = img.get("title", "")
                if any(ext in title.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    if not any(skip in title.lower() for skip in ['icon', 'logo.svg', 'flag', 'symbol', 'commons-logo', 'edit-clear', 'ambox', 'crystal']):
                        filenames.append(title)
        return filenames
    except Exception:
        return []


def get_commons_file_url(file_title):
    """Get the direct URL for a Wikimedia Commons file."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": "1920",
        "format": "json",
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            return info.get("thumburl") or info.get("url")
    except Exception:
        return None


def search_commons(query, limit=3):
    """Search Wikimedia Commons for images."""
    params = urllib.parse.urlencode({
        "action": "query",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}",
        "gsrlimit": str(limit),
        "gsrnamespace": "6",
        "prop": "imageinfo",
        "iiprop": "url|size",
        "iiurlwidth": "1920",
        "format": "json",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = []
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            thumb = info.get("thumburl") or info.get("url")
            if thumb:
                results.append(thumb)
        return results
    except Exception:
        return []


# ---- QUERY LIST ----
# (slug, wikipedia_article, commons_search_query, description)
QUERIES = [
    # People
    ("zuckerberg_senate_hearing", "Facebook–Cambridge_Analytica_data_scandal", "Mark Zuckerberg Senate hearing 2018", "Zuckerberg testifying before Congress"),
    ("zuckerberg_portrait", "Mark_Zuckerberg", None, "Mark Zuckerberg portrait"),
    ("richard_grimshaw", None, "Grimshaw v. Ford Motor Co", "Richard Grimshaw Ford Pinto case"),
    ("aleksandr_kogan", "Aleksandr_Kogan", "Aleksandr Kogan Cambridge", "Cambridge researcher"),
    ("richard_sackler", "Richard_Sackler", "Richard Sackler Purdue", "Sackler family Purdue Pharma"),
    ("senator_orrin_hatch", "Orrin_Hatch", "Orrin Hatch Senate", "Senator who asked 'how do you sustain'"),

    # Companies/Organizations
    ("facebook_hq", "Meta_Platforms", "Facebook headquarters Menlo Park", "Facebook/Meta headquarters"),
    ("wells_fargo", "Wells_Fargo", "Wells Fargo building", "Wells Fargo"),
    ("purdue_pharma", "Purdue_Pharma", "Purdue Pharma OxyContin", "Purdue Pharma"),
    ("cambridge_analytica", "Cambridge_Analytica", "Cambridge Analytica", "Cambridge Analytica"),
    ("realpage", "RealPage", "RealPage software", "RealPage rent algorithm"),
    ("perplexity_ai", "Perplexity.ai", "Perplexity AI", "Perplexity AI"),

    # Buildings/Landmarks
    ("guggenheim_museum", "Solomon_R._Guggenheim_Museum", "Guggenheim Museum New York", "Guggenheim Museum exterior"),
    ("ftc_building", "Federal_Trade_Commission", "Federal Trade Commission building Washington", "FTC building"),
    ("doj_building", "United_States_Department_of_Justice", "Department of Justice building Washington", "DOJ building"),
    ("us_capitol", "United_States_Capitol", "United States Capitol building", "US Capitol"),
    ("eu_parliament", "European_Parliament", "European Parliament Strasbourg", "EU Parliament"),
    ("us_senate_chamber", "United_States_Senate", "United States Senate chamber", "Senate hearing room"),
    ("ny_state_capitol", "New_York_State_Capitol", "New York State Capitol Albany", "NY State Capitol"),

    # Events/Concepts
    ("ford_pinto", "Ford_Pinto", "Ford Pinto", "Ford Pinto car"),
    ("ford_pinto_case", "Grimshaw_v._Ford_Motor_Co.", "Ford Pinto crash fire", "Ford Pinto fuel tank case"),
    ("cambridge_analytica_scandal", "Facebook–Cambridge_Analytica_data_scandal", "Cambridge Analytica data scandal", "Cambridge Analytica scandal"),
    ("wells_fargo_scandal", "Wells_Fargo_account_fraud_scandal", "Wells Fargo fake accounts scandal", "Wells Fargo account fraud"),
    ("opioid_crisis", "Opioid_epidemic_in_the_United_States", "opioid crisis OxyContin", "Opioid epidemic"),
    ("gdpr", "General_Data_Protection_Regulation", "GDPR European Union", "GDPR regulation"),
    ("data_center", None, "data center servers racks", "Data center servers"),
    ("ai_copyright", None, "artificial intelligence copyright lawsuit", "AI copyright"),
    ("wall_street", "Wall_Street", "Wall Street New York", "Wall Street"),
    ("seattle_queen_anne", "Queen_Anne,_Seattle", "Queen Anne Seattle neighborhood", "Seattle neighborhood"),
    ("common_crawl", "Common_Crawl", "Common Crawl dataset", "Common Crawl web archive"),

    # Documentary-specific
    ("courtroom_gavel", None, "courtroom gavel judge", "Courtroom gavel"),
    ("corporate_boardroom", None, "corporate boardroom meeting room", "Corporate boardroom"),
    ("rent_increase_notice", None, "rent increase notice apartment", "Rent increase"),
    ("whistleblower", None, "corporate whistleblower", "Whistleblower"),
    ("artist_illustration", None, "illustrator drawing desk digital art", "Artist at work"),
    ("bookshelf_art", None, "bookshelf book covers art illustration", "Book covers on shelf"),
    ("have_i_been_trained", None, "Have I Been Trained AI art", "Have I Been Trained website"),
    ("laion_dataset", None, "LAION 5B dataset AI training", "LAION training dataset"),
    ("harpercollins", "HarperCollins", "HarperCollins publisher", "HarperCollins"),
    ("hulu_logo", "Hulu", "Hulu streaming logo", "Hulu"),
]


def main():
    total = 0
    manifest = []

    for slug, wiki_article, commons_query, desc in QUERIES:
        print(f"  {slug}: ", end="", flush=True)
        downloaded = []

        # Try Wikipedia main image first
        if wiki_article:
            img_url = get_wikipedia_image(wiki_article)
            if img_url:
                ext = ".jpg"
                if ".png" in img_url.lower():
                    ext = ".png"
                out_path = OUTPUT_DIR / f"{slug}_wiki{ext}"
                if download(img_url, out_path):
                    downloaded.append({"path": str(out_path), "source": "wikipedia", "article": wiki_article})
                    print(f"wiki ", end="", flush=True)

            # Also get other images from the article
            other_files = get_wikipedia_all_images(wiki_article, limit=4)
            for i, fname in enumerate(other_files[:2]):  # max 2 extra
                furl = get_commons_file_url(fname)
                if furl:
                    ext = ".jpg" if ".jpg" in furl.lower() or ".jpeg" in furl.lower() else ".png"
                    out_path = OUTPUT_DIR / f"{slug}_wiki_{i}{ext}"
                    if download(furl, out_path):
                        downloaded.append({"path": str(out_path), "source": "wikipedia", "file": fname})
                        print(f"w{i} ", end="", flush=True)

        # Try Commons search
        if commons_query:
            urls = search_commons(commons_query, limit=3)
            for i, curl in enumerate(urls):
                ext = ".jpg"
                if ".png" in curl.lower():
                    ext = ".png"
                out_path = OUTPUT_DIR / f"{slug}_commons_{i}{ext}"
                if download(curl, out_path):
                    downloaded.append({"path": str(out_path), "source": "commons", "query": commons_query})
                    print(f"c{i} ", end="", flush=True)

        if downloaded:
            total += len(downloaded)
            manifest.extend([{**d, "slug": slug, "description": desc} for d in downloaded])
            print(f"= {len(downloaded)}")
        else:
            print("MISS")

        time.sleep(1.5)  # Wikimedia rate limit is strict

    # Save manifest
    manifest_path = OUTPUT_DIR / "web_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump({"images": manifest, "total": total}, f, indent=2)

    print(f"\n=== TOTAL: {total} images downloaded to {OUTPUT_DIR} ===")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
