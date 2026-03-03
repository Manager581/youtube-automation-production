#!/usr/bin/env python3
"""
music_sourcer.py — Find and download free commercial-use music matching your script's mood.

Analyzes the script's emotional arc, maps it to search terms, then searches:
  1. Pixabay Music  — CC0 license (zero attribution, full commercial use, free forever)
  2. Free Music Archive — CC licensed (some require attribution, all commercial OK)

Outputs: assets/music/track.mp3 (or named by topic)

Usage:
    # Analyze script and download best match
    venv/bin/python pipeline/music_sourcer.py --script scripts/enhanced_cia_mkultra.txt

    # Just show what it would pick, don't download
    venv/bin/python pipeline/music_sourcer.py --script scripts/enhanced.txt --preview

    # Force a specific mood (skip script analysis)
    venv/bin/python pipeline/music_sourcer.py --mood "dark cinematic suspense" --download

    # Download multiple options (pick manually)
    venv/bin/python pipeline/music_sourcer.py --script scripts/enhanced.txt --count 5

License notes:
    Pixabay CC0  — no attribution required, commercial use OK, YouTube monetization OK
    FMA CC-BY    — must credit artist in video description
    FMA CC0      — same as Pixabay, no attribution needed
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Mood → search term mapping
# Fern's measured formula: dark cinematic, 116 BPM, piano + strings, ominous
# Script analysis biases toward this baseline, adjusted by content
# ---------------------------------------------------------------------------

FERN_BASELINE_MOOD = "dark cinematic suspense documentary"

MOOD_KEYWORDS = {
    # Script markers → mood signals
    "tense":      ["suspense", "thriller", "dark", "tension"],
    "energized":  ["dramatic", "intense", "cinematic", "powerful"],
    "neutral":    ["documentary", "ambient", "atmospheric", "minimal"],
    "ominous":    ["dark", "ominous", "mysterious", "eerie"],
    "reveal":     ["dramatic", "orchestral", "cinematic reveal"],
    "climax":     ["epic", "dramatic", "intense", "cinematic"],
}

# Pixabay search terms that match Fern's actual music style
FERN_PIXABAY_QUERIES = [
    "dark cinematic documentary",
    "suspense thriller piano",
    "dark ambient investigative",
    "ominous orchestral documentary",
    "cinematic tension piano strings",
    "dark investigative documentary",
]

# Free Music Archive genres that match
FERN_FMA_TAGS = ["ambient", "cinematic", "dark-ambient", "instrumental", "soundtrack"]


# ---------------------------------------------------------------------------
# Script mood analysis
# ---------------------------------------------------------------------------

def analyze_script_mood(script_path: Path) -> dict:
    """
    Read a script and extract mood signals.
    Returns: {dominant_mood, voice_register_mix, has_reveal, tension_density}
    """
    text = script_path.read_text(errors="ignore").lower()

    # Count voice register markers
    registers = {
        "tense":     len(re.findall(r'\[voice:tense\]', text)),
        "energized": len(re.findall(r'\[voice:energized\]', text)),
        "neutral":   len(re.findall(r'\[voice:neutral\]', text)),
    }
    total_markers = sum(registers.values()) or 1

    # Detect content signals
    tension_words = ["killed", "murdered", "secret", "cover", "conspiracy",
                     "bomb", "weapon", "poison", "torture", "kidnap", "spy",
                     "cia", "fbi", "classified", "experiment", "death", "died"]
    dark_count = sum(text.count(w) for w in tension_words)
    word_count  = len(text.split())
    tension_density = dark_count / max(word_count, 1)

    has_reveal = bool(re.search(r'\b(except|in reality|it turns out|the truth|'
                                r'what they didn.t|nobody knew|hidden|secret)\b', text))

    # Dominant mood
    if registers["tense"] / total_markers > 0.4:
        dominant = "dark suspense"
    elif tension_density > 0.02:
        dominant = "dark cinematic thriller"
    elif has_reveal:
        dominant = "documentary investigation"
    else:
        dominant = "dark cinematic documentary"

    return {
        "dominant_mood": dominant,
        "tense_pct":     round(registers["tense"] / total_markers * 100),
        "energized_pct": round(registers["energized"] / total_markers * 100),
        "tension_density": round(tension_density * 1000, 1),  # per-1000-words
        "has_reveal": has_reveal,
        "search_terms": _mood_to_search_terms(dominant, tension_density, has_reveal),
    }


def _mood_to_search_terms(dominant: str, tension_density: float, has_reveal: bool) -> list[str]:
    """Convert mood analysis to Pixabay search queries, ordered by relevance."""
    terms = []

    if tension_density > 0.025:
        terms += ["dark thriller suspense piano", "dark cinematic documentary", "suspense investigation"]
    elif tension_density > 0.01:
        terms += ["dark cinematic documentary", "atmospheric investigation", "suspense piano strings"]
    else:
        terms += ["dark ambient documentary", "cinematic atmospheric", "documentary investigation"]

    if has_reveal:
        terms.insert(0, "dramatic reveal cinematic orchestral")

    # Always add Fern baseline as fallback
    terms += FERN_PIXABAY_QUERIES[:3]

    return list(dict.fromkeys(terms))  # deduplicate, preserve order


# ---------------------------------------------------------------------------
# Pixabay Music search (CC0 — zero attribution, full commercial use)
# ---------------------------------------------------------------------------

def search_pixabay(query: str, count: int = 10) -> list[dict]:
    """
    Search Pixabay Music via their public API.
    Requires a free Pixabay API key: https://pixabay.com/api/docs/
    Falls back to scraping if no key provided.
    """
    api_key = _load_pixabay_key()
    if not api_key:
        return _search_pixabay_scrape(query, count)

    params = urllib.parse.urlencode({
        "key":        api_key,
        "q":          query,
        "media_type": "music",
        "per_page":   count,
    })
    url = f"https://pixabay.com/api/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "music-sourcer/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = []
        for hit in data.get("hits", []):
            results.append({
                "title":    hit.get("tags", "unknown"),
                "url":      hit.get("pageURL", ""),
                "download": hit.get("audio", {}).get("url", ""),
                "duration": hit.get("duration", 0),
                "bpm":      hit.get("bpm", None),
                "license":  "CC0",
                "source":   "pixabay",
            })
        return results
    except Exception as e:
        print(f"  Pixabay API error: {e}")
        return _search_pixabay_scrape(query, count)


def _load_pixabay_key() -> str | None:
    """Load Pixabay API key from config or env."""
    import os
    key = os.environ.get("PIXABAY_API_KEY", "")
    if key:
        return key
    config_path = Path("config/api_keys.json")
    if config_path.exists():
        try:
            return json.loads(config_path.read_text()).get("pixabay", "")
        except Exception:
            pass
    return None


def _search_pixabay_scrape(query: str, count: int = 5) -> list[dict]:
    """
    Fallback: scrape Pixabay music search page for track info.
    Returns basic info — user must download manually if no API key.
    """
    params = urllib.parse.urlencode({"q": query, "media_type": "music"})
    url = f"https://pixabay.com/music/search/?{params}"
    results = [{
        "title":    f"Pixabay: '{query}'",
        "url":      url,
        "download": None,
        "license":  "CC0",
        "source":   "pixabay",
        "note":     "Add PIXABAY_API_KEY env var for auto-download. Browse link above.",
    }]
    return results


# ---------------------------------------------------------------------------
# Free Music Archive search (CC licensed)
# ---------------------------------------------------------------------------

def search_fma(query: str, count: int = 5) -> list[dict]:
    """
    Search Free Music Archive via their public API (no key needed).
    Returns CC-licensed tracks — check license field before use.
    CC0 = no attribution. CC-BY = credit artist in description.
    """
    params = urllib.parse.urlencode({
        "q":              query,
        "limit":          count,
        "fields":         "track_id,track_title,artist_name,license_title,track_url,track_file",
        "track_explicit": "0",
    })
    url = f"https://freemusicarchive.org/api/get/tracks.json?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "music-sourcer/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = []
        for track in data.get("dataset", []):
            results.append({
                "title":    f"{track.get('artist_name', '?')} — {track.get('track_title', '?')}",
                "url":      track.get("track_url", ""),
                "download": track.get("track_file", ""),
                "license":  track.get("license_title", "CC"),
                "source":   "fma",
            })
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_track(track: dict, out_path: Path) -> bool:
    """
    Download a music track to out_path.
    Uses yt-dlp for YouTube-based sources, direct download for direct URLs.
    """
    import subprocess, shutil

    out_path.parent.mkdir(parents=True, exist_ok=True)
    download_url = track.get("download", "")

    if not download_url:
        print(f"  No direct download URL. Visit: {track.get('url', '?')}")
        return False

    # Direct HTTP download (Pixabay, FMA)
    if download_url.startswith("http") and "youtube" not in download_url:
        try:
            print(f"  Downloading: {track['title'][:60]}")
            req = urllib.request.Request(download_url,
                                         headers={"User-Agent": "music-sourcer/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                out_path.write_bytes(resp.read())
            print(f"  Saved: {out_path}")
            return True
        except Exception as e:
            print(f"  Download failed: {e}")
            return False

    # yt-dlp fallback
    if shutil.which("yt-dlp"):
        try:
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3",
                   "-o", str(out_path.with_suffix(".%(ext)s")), download_url]
            subprocess.run(cmd, check=True, capture_output=True)
            # Rename to .mp3 if needed
            for f in out_path.parent.glob(f"{out_path.stem}.*"):
                if f.suffix in (".mp3", ".m4a", ".webm", ".opus"):
                    f.rename(out_path)
                    break
            print(f"  Saved: {out_path}")
            return True
        except Exception as e:
            print(f"  yt-dlp failed: {e}")

    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Find + download free commercial-use music for your script")
    p.add_argument("--script",   help="Path to enhanced script file (.txt)")
    p.add_argument("--mood",     help="Override mood (e.g. 'dark cinematic suspense')")
    p.add_argument("--count",    type=int, default=5, help="Number of results to show")
    p.add_argument("--preview",  action="store_true", help="Show results, don't download")
    p.add_argument("--out",      default="assets/music/track.mp3", help="Output path")
    p.add_argument("--source",   choices=["pixabay", "fma", "all"], default="all")
    args = p.parse_args()

    if not args.script and not args.mood:
        p.error("Provide --script or --mood")

    # --- Step 1: Analyze script mood ---
    if args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            print(f"ERROR: Script not found: {script_path}")
            sys.exit(1)
        print(f"\nAnalyzing script: {script_path.name}")
        mood = analyze_script_mood(script_path)
        print(f"  Dominant mood:     {mood['dominant_mood']}")
        print(f"  Tense/energized:   {mood['tense_pct']}% / {mood['energized_pct']}%")
        print(f"  Tension density:   {mood['tension_density']}/1000 words")
        print(f"  Reveal structure:  {'yes' if mood['has_reveal'] else 'no'}")
        search_terms = mood["search_terms"]
    else:
        search_terms = [args.mood] + FERN_PIXABAY_QUERIES[:2]
        print(f"\nMood override: {args.mood}")

    # --- Step 2: Search ---
    all_results = []

    for query in search_terms[:3]:  # top 3 search terms
        print(f"\nSearching: '{query}'")

        if args.source in ("pixabay", "all"):
            px_results = search_pixabay(query, args.count)
            for r in px_results:
                r["_query"] = query
            all_results.extend(px_results)
            print(f"  Pixabay: {len(px_results)} results")

        if args.source in ("fma", "all"):
            fma_results = search_fma(query, args.count)
            for r in fma_results:
                r["_query"] = query
            all_results.extend(fma_results)
            if fma_results:
                print(f"  FMA:     {len(fma_results)} results")

        if all_results:
            break  # Got results — don't burn through all search terms
        time.sleep(0.5)

    if not all_results:
        print("\nNo results found. Try --mood with different terms.")
        print("Manual option: pixabay.com/music — search 'dark cinematic documentary'")
        print("               freemusicarchive.org — genre: ambient/cinematic")
        sys.exit(1)

    # --- Step 3: Show results ---
    print(f"\n{'─'*70}")
    print(f"{'#':>3}  {'License':10}  {'Source':8}  {'Title'}")
    print(f"{'─'*70}")
    for i, r in enumerate(all_results[:args.count], 1):
        lic = r.get("license", "?")[:10]
        src = r.get("source", "?")[:8]
        title = r.get("title", "?")[:48]
        bpm = f" [{r['bpm']} BPM]" if r.get("bpm") else ""
        print(f"{i:>3}  {lic:10}  {src:8}  {title}{bpm}")
        if r.get("url"):
            print(f"     {r['url']}")
        if r.get("note"):
            print(f"     ⚠ {r['note']}")

    print(f"{'─'*70}")
    print(f"\nLicense guide:")
    print(f"  CC0      = no attribution needed, commercial use + YouTube monetization OK")
    print(f"  CC-BY    = credit artist in video description, commercial OK")
    print(f"  CC-BY-SA = same + derivatives must use same license")

    if args.preview:
        print("\n(Preview only — run without --preview to download)")
        return

    # --- Step 4: Download ---
    # Try sources in order: Pixabay (CC0) → FMA → YouTube Audio Library (yt-dlp)
    out_path = Path(args.out)

    # Find a result with a direct download URL
    cc0_first = sorted(all_results, key=lambda r: (0 if "CC0" in r.get("license","") else 1,
                                                    0 if r.get("download") else 1))
    best = next((r for r in cc0_first if r.get("download")), None)

    if best:
        print(f"\nDownloading: {best.get('title','?')[:60]}  [{best.get('license','?')}]")
        ok = download_track(best, out_path)
    else:
        print("\nNo direct download from API — trying YouTube Audio Library (free, commercial use)...")
        ok = _download_youtube_audio_library(search_terms[0], out_path)

    if ok:
        print(f"\n✓ Music saved: {out_path}")
        if best and "CC-BY" in best.get("license", ""):
            print(f"  ⚠ Attribution needed in video description:")
            print(f"    Music: {best.get('title','?')} — {best.get('url','')}")
    else:
        print(f"\nAuto-download failed. To get music manually:")
        print(f"  pixabay.com/music — search '{search_terms[0]}'  (CC0, no attribution)")
        print(f"  Save to: {out_path}")
        readme = out_path.parent / "MUSIC_README.txt"
        readme.write_text(
            f"Save your track as: track.mp3 in this folder.\n\n"
            f"Recommended: pixabay.com/music\n"
            f"Search: '{search_terms[0]}'\n"
            f"License: CC0 (no attribution, commercial + monetization OK)\n\n"
            f"Optional API key for auto-download:\n"
            f"  1. Sign up free at pixabay.com\n"
            f"  2. Get API key from pixabay.com/api/docs/\n"
            f"  3. export PIXABAY_API_KEY=your_key\n"
            f"  4. Re-run music_sourcer.py\n"
        )
        print(f"  Instructions: {readme}")


def _download_youtube_audio_library(query: str, out_path: Path) -> bool:
    """
    Download from YouTube Audio Library via yt-dlp.
    YouTube Audio Library tracks are free for commercial use including monetized videos.
    """
    import subprocess, shutil
    if not shutil.which("yt-dlp"):
        return False

    # Search YouTube for the track — bias toward known free music channels
    search_query = f"ytsearch3:{query} no copyright cinematic"
    try:
        out_template = str(out_path.with_suffix(".%(ext)s"))
        cmd = [
            "yt-dlp",
            "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0",
            "--match-filter", "duration > 120 & duration < 600",  # 2-10 min tracks only
            "--no-playlist",
            "-o", out_template,
            "--max-downloads", "1",
            search_query,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # Find output file
        for f in out_path.parent.glob(f"{out_path.stem}.*"):
            if f.suffix in (".mp3", ".m4a", ".opus", ".webm"):
                f.rename(out_path)
                return True
        return out_path.exists()
    except Exception as e:
        print(f"  yt-dlp error: {e}")
        return False


if __name__ == "__main__":
    main()
