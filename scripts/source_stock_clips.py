#!/usr/bin/env python3
"""
source_stock_clips.py — fill the asset plan's `stock` lane with real-footage
7s clips per the channel fair-use rules (≤7s/clip, muted, transformed by
narration+zoom+overlays). Searches YouTube (same yt-dlp pattern as
pipeline_v2/source_scanner.py), downloads only a mid-video section, trims,
mutes, and writes a source manifest for on-screen/description credits.

Usage:
  venv/bin/python scripts/source_stock_clips.py [--only slug1,slug2] [--start N] [--end N]
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'footage/trex_pilot/stock'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = ROOT / 'research/trex_pilot_stock_sources.json'

QUERIES = {
    's_city_bus':        'MTA bus arriving bus stop new york street 4k',
    's_wet_concrete':    'rain puddle sidewalk reflection close up city street',
    's_barricade':       'nypd police barricade crowd street',
    's_glass_tower':     'skyscraper glass facade looking up 4k b-roll',
    's_crowd_cross':     'times square crosswalk crowd walking 4k',
    's_hawk_eye':        'hawk eye extreme close up 4k bird',
    's_dawn_canyon':     'new york street canyon sunrise golden 4k b-roll',
    's_taxi_wall':       'yellow taxis fifth avenue traffic new york city 4k street level',
    's_faces_glass':     'crowd looking up pointing at sky city street reaction',
    's_crowd_run':       'crowd running away street panic footage',
    's_crowd_scatter':   'crowd scattering aerial drone street',
    's_herd_scatter':    'wildebeest herd running scattering safari 4k',
    's_phones_up':       'audience holding phones lights up concert crowd filming',
    's_crowd_mass':      'times square new years eve packed crowd 4k',
    's_nypd_lights':     'nypd police cars flashing lights night new york',
    's_heli_armor':      'police helicopter flying low over city 4k',
    's_swat_line':       'riot police line advancing shields street',
    's_diesel_smoke':    'diesel exhaust smoke truck close up slow motion',
    's_rotor_macro':     'helicopter rotor blades spinning close up slow motion',
    's_barricade_night': 'nypd crime scene night police lights street flashing',
    's_hudson_wide':     'hudson river winter manhattan wide 4k',
    's_skyline_river':   'manhattan skyline night from river water 4k',
    's_snow_flurry':     'snow falling streetlight night close up 4k',
    's_ice_concrete':    'icy sidewalk slippery winter close up boots walking',
    's_searchlight':     'searchlight beam night sky city',
    's_miami':           'miami skyline from water boat 4k b-roll',
}


def search(query, n=6):
    r = subprocess.run(
        ['yt-dlp', '--flat-playlist', '--dump-json', '--no-warnings',
         f'ytsearch{n}:{query}'],
        capture_output=True, text=True, timeout=60)
    hits = []
    for line in r.stdout.splitlines():
        try:
            j = json.loads(line)
        except json.JSONDecodeError:
            continue
        dur = j.get('duration') or 0
        # sane horizontal b-roll candidates: 25s–15min, skip Shorts
        if 25 <= dur <= 900 and '/shorts/' not in (j.get('url') or ''):
            hits.append(j)
    return hits


def grab(slug, query):
    final = OUT / f'{slug}.mp4'
    if final.exists():
        return {'slug': slug, 'status': 'exists'}
    for hit in search(query):
        vid = hit.get('id')
        url = f'https://www.youtube.com/watch?v={vid}'
        dur = hit.get('duration') or 60
        t0 = max(int(dur * 0.35), 3)          # mid-video, skip intros
        raw = OUT / f'_{slug}_raw.mp4'
        try:
            dl = subprocess.run(
                ['yt-dlp', '-f', 'bv*[height<=1080][ext=mp4]/bv*[height<=1080]/b',
                 '--download-sections', f'*{t0}-{t0 + 12}',
                 '--no-warnings', '--force-overwrites',
                 '-o', str(raw), url],
                capture_output=True, text=True, timeout=180)
            if not raw.exists() or raw.stat().st_size < 50_000:
                continue
            # trim to exactly 7s, mute, normalize size
            tr = subprocess.run(
                ['ffmpeg', '-y', '-loglevel', 'error', '-i', str(raw),
                 '-t', '7', '-an',
                 '-vf', 'scale=1280:720:force_original_aspect_ratio=increase,'
                        'crop=1280:720',
                 '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                 str(final)],
                capture_output=True, text=True, timeout=120)
            raw.unlink(missing_ok=True)
            if final.exists() and final.stat().st_size > 50_000:
                return {'slug': slug, 'status': 'ok', 'url': url,
                        'title': hit.get('title'),
                        'uploader': hit.get('uploader') or hit.get('channel')}
        except subprocess.TimeoutExpired:
            raw.unlink(missing_ok=True)
            continue
    return {'slug': slug, 'status': 'FAILED'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only')
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=len(QUERIES))
    a = ap.parse_args()
    slugs = list(QUERIES)
    if a.only:
        slugs = [s for s in a.only.split(',') if s in QUERIES]
    else:
        slugs = slugs[a.start:a.end]

    manifest = json.load(open(MANIFEST)) if MANIFEST.exists() else {}
    for slug in slugs:
        res = grab(slug, QUERIES[slug])
        print(res)
        if res['status'] == 'ok':
            manifest[slug] = res
        json.dump(manifest, open(MANIFEST, 'w'), indent=1)


if __name__ == '__main__':
    main()
