#!/usr/bin/env python3
"""
Fingerprint Fern's music stems via AcoustID (free, open source).
Identifies the actual tracks Fern licenses.

Requirements: brew install chromaprint  (gives us fpcalc)
              pip install requests

Usage: python fingerprint_music.py
"""
import json, subprocess, os, urllib.request, urllib.parse
from pathlib import Path

STEMS_DIR = Path("analysis/fern/demucs_out/htdemucs")
OUT_FILE  = Path("analysis/fern/MUSIC_IDENTITY.json")

# AcoustID public API key (free, rate-limited to 3 req/s)
ACOUSTID_KEY = "8XaBELgH"   # public test key — works for low volume

VIDEO_IDS = ["aVA7aXOH1pk_audio", "wLFY_Zu_O08_audio", "wkVygetgeRY_audio"]
VIDEO_NAMES = {
    "aVA7aXOH1pk_audio": "Trump_Assassination",
    "wLFY_Zu_O08_audio": "FBI_KKK",
    "wkVygetgeRY_audio": "Unabomber",
}


def find_music_stem(vid_id):
    """Find the music.wav stem for this video."""
    # Demucs saves as: demucs_out/htdemucs/{vid_id}/music.wav
    candidates = [
        STEMS_DIR / vid_id / "music.wav",
        STEMS_DIR / vid_id / "other.wav",  # fallback
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def get_fingerprint(audio_path, duration=120):
    """
    Run fpcalc to get AcoustID fingerprint.
    Sample from middle of track (skip intros/outros) for clean music.
    """
    try:
        result = subprocess.run(
            ["fpcalc", "-length", str(duration), str(audio_path)],
            capture_output=True, text=True, timeout=30
        )
        lines = result.stdout.strip().split("\n")
        fp   = next((l.split("=",1)[1] for l in lines if l.startswith("FINGERPRINT=")), None)
        dur  = next((l.split("=",1)[1] for l in lines if l.startswith("DURATION=")), None)
        return fp, dur
    except FileNotFoundError:
        print("ERROR: fpcalc not found. Install with: brew install chromaprint")
        return None, None
    except Exception as e:
        print(f"fpcalc error: {e}")
        return None, None


def acoustid_lookup(fingerprint, duration):
    """Query AcoustID API to identify the track."""
    params = {
        "client":      ACOUSTID_KEY,
        "duration":    duration,
        "fingerprint": fingerprint,
        "meta":        "recordings releases tracks",
    }
    url = "https://api.acoustid.org/v2/lookup?" + urllib.parse.urlencode(params)
    try:
        req  = urllib.request.Request(url, headers={"User-Agent": "FernAnalyzer/1.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data
    except Exception as e:
        return {"error": str(e)}


def parse_result(data):
    """Extract best match from AcoustID response."""
    results = data.get("results", [])
    if not results:
        return None

    best = max(results, key=lambda x: x.get("score", 0))
    score = best.get("score", 0)
    recordings = best.get("recordings", [])

    if not recordings:
        return {"score": score, "match": "fingerprint found but no recording data"}

    rec = recordings[0]
    title    = rec.get("title", "?")
    duration = rec.get("duration", "?")
    artists  = [a.get("name", "") for a in rec.get("artists", [])]
    releases = rec.get("releases", [])
    album    = releases[0].get("title", "?") if releases else "?"
    year     = releases[0].get("date", {}).get("year", "?") if releases else "?"

    return {
        "score":    round(score, 3),
        "title":    title,
        "artists":  artists,
        "album":    album,
        "year":     year,
        "duration": duration,
    }


if __name__ == "__main__":
    print("Checking fpcalc...")
    test = subprocess.run(["which", "fpcalc"], capture_output=True, text=True)
    if not test.stdout.strip():
        print("ERROR: fpcalc not installed. Run: brew install chromaprint")
        import sys; sys.exit(1)
    print(f"  fpcalc found: {test.stdout.strip()}")

    results = {}

    for vid_id in VIDEO_IDS:
        name = VIDEO_NAMES[vid_id]
        music_path = find_music_stem(vid_id)

        if not music_path:
            print(f"\n[SKIP] {name} — no music stem at {STEMS_DIR / vid_id}")
            continue

        print(f"\n{'='*55}")
        print(f"Fingerprinting: {name}")
        print(f"  File: {music_path} ({music_path.stat().st_size // 1024 // 1024}MB)")

        # Sample multiple 2-minute windows from different parts of the track
        import wave, struct
        try:
            with wave.open(str(music_path)) as wf:
                total_sec = wf.getnframes() / wf.getframerate()
        except:
            total_sec = 600  # assume 10 min if can't read

        print(f"  Duration: {total_sec:.0f}s")

        # Try 3 windows: 10%, 40%, 70% into the track
        windows = [
            int(total_sec * 0.10),
            int(total_sec * 0.40),
            int(total_sec * 0.70),
        ]

        vid_results = []
        for start_sec in windows:
            # fpcalc -start doesn't exist, so extract the window with ffmpeg first
            tmp = f"/tmp/fp_window_{start_sec}.wav"
            subprocess.run(
                ["ffmpeg", "-i", str(music_path), "-ss", str(start_sec),
                 "-t", "120", "-ar", "44100", "-ac", "1", tmp, "-y", "-loglevel", "error"],
                capture_output=True
            )

            fp, dur = get_fingerprint(tmp)
            if not fp:
                continue

            print(f"  Querying AcoustID (window at {start_sec}s)...")
            data   = acoustid_lookup(fp, dur)
            parsed = parse_result(data)

            if parsed:
                vid_results.append({**parsed, "window_start_sec": start_sec})
                if parsed.get("title"):
                    print(f"  MATCH [{parsed['score']:.2f}]: \"{parsed['title']}\" by {', '.join(parsed['artists'])}")
                    print(f"         Album: {parsed['album']} ({parsed['year']})")
                else:
                    print(f"  No match at window {start_sec}s")
            else:
                print(f"  No results at window {start_sec}s")

            os.unlink(tmp)

        results[name] = vid_results

    print(f"\n{'='*55}")
    print("SUMMARY")
    print(f"{'='*55}")
    for name, matches in results.items():
        print(f"\n{name}:")
        identified = [m for m in matches if m.get("title") and m["score"] > 0.5]
        if identified:
            for m in identified:
                print(f"  [{m['score']:.2f}] \"{m['title']}\" — {', '.join(m['artists'])} ({m['year']})")
        else:
            print("  No confident matches — likely custom/unlicensed music")

    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {OUT_FILE}")
