#!/usr/bin/env python3
"""Download and analyze Fern's top videos"""
import subprocess
import json
from pathlib import Path

FERN_CHANNEL = "@FernTv"
OUTPUT_DIR = Path("analysis/fern")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Fetching Fern's top 30 videos...")
result = subprocess.run([
    "yt-dlp",
    "--no-check-certificates",
    "--flat-playlist",
    "--print", "%(id)s|%(title)s|%(view_count)s|%(duration)s",
    "--playlist-end", "30",
    f"https://www.youtube.com/{FERN_CHANNEL}/videos"
], capture_output=True, text=True)

videos = []
for line in result.stdout.strip().split('\n'):
    if '|' in line:
        vid_id, title, views, duration = line.split('|')
        videos.append({
            'id': vid_id,
            'title': title,
            'views': int(views) if views.isdigit() else 0,
            'duration': int(duration) if duration.isdigit() else 0
        })

# Sort by views
videos.sort(key=lambda x: x['views'], reverse=True)

print(f"\nFound {len(videos)} videos. Downloading top 30...")

for i, video in enumerate(videos[:30], 1):
    print(f"\n[{i}/30] {video['title']} ({video['views']:,} views)")
    video_dir = OUTPUT_DIR / video['id']
    video_dir.mkdir(exist_ok=True)
    
    # Download video + transcript
    subprocess.run([
        "yt-dlp",
        "--no-check-certificates",
        "-f", "best",
        "--write-auto-sub",
        "--write-info-json",
        "--write-thumbnail",
        "-o", str(video_dir / "video.%(ext)s"),
        f"https://www.youtube.com/watch?v={video['id']}"
    ])
    
    # Save metadata
    with open(video_dir / "metadata.json", 'w') as f:
        json.dump(video, f, indent=2)

print("\n✓ All videos downloaded to", OUTPUT_DIR)
