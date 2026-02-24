#!/usr/bin/env python3
"""Download Fern videos with browser authentication to bypass 403 errors"""
import subprocess
import json
from pathlib import Path

FERN_CHANNEL = "@fern-tv"
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
        parts = line.split('|')
        if len(parts) == 4:
            vid_id, title, views, duration = parts
            videos.append({
                'id': vid_id,
                'title': title,
                'views': int(views) if views.isdigit() else 0,
                'duration': int(duration) if duration.isdigit() else 0
            })

# Sort by views
videos.sort(key=lambda x: x['views'], reverse=True)

print(f"\nFound {len(videos)} videos. Downloading top 30...")
print("\nTo bypass YouTube's 403 blocking:")
print("1. Open Chrome/Firefox and go to youtube.com")
print("2. Make sure you're logged in")
print("3. Then run this with --cookies-from-browser chrome (or firefox)")
print("\nAttempting download with authentication workarounds...")

for i, video in enumerate(videos[:30], 1):
    print(f"\n[{i}/30] {video['title']} ({video['views']:,} views)")
    video_dir = OUTPUT_DIR / video['id']
    video_dir.mkdir(exist_ok=True)

    # Try multiple methods to bypass 403
    download_methods = [
        # Method 1: Use cookies from browser
        [
            "yt-dlp",
            "--no-check-certificates",
            "--cookies-from-browser", "chrome",
            "--write-auto-sub",
            "--write-info-json",
            "--write-thumbnail",
            "-o", str(video_dir / "video.%(ext)s"),
            f"https://www.youtube.com/watch?v={video['id']}"
        ],
        # Method 2: Different format selection
        [
            "yt-dlp",
            "--no-check-certificates",
            "-f", "18",  # Specific format that often works
            "--write-auto-sub",
            "--write-info-json",
            "--write-thumbnail",
            "-o", str(video_dir / "video.%(ext)s"),
            f"https://www.youtube.com/watch?v={video['id']}"
        ],
        # Method 3: Lower quality if needed
        [
            "yt-dlp",
            "--no-check-certificates",
            "-f", "worst",
            "--write-auto-sub",
            "--write-info-json",
            "--write-thumbnail",
            "-o", str(video_dir / "video.%(ext)s"),
            f"https://www.youtube.com/watch?v={video['id']}"
        ]
    ]

    success = False
    for method_idx, method in enumerate(download_methods, 1):
        print(f"  Trying download method {method_idx}...")
        result = subprocess.run(method, capture_output=True, text=True)

        # Check if video file was created
        video_files = list(video_dir.glob("video.*"))
        video_files = [f for f in video_files if f.suffix not in ['.vtt', '.json', '.webp', '.jpg', '.png']]

        if video_files:
            print(f"  ✓ Downloaded successfully with method {method_idx}")
            success = True
            break
        elif method_idx < len(download_methods):
            print(f"  ✗ Method {method_idx} failed, trying next...")

    if not success:
        print(f"  ✗ All methods failed for this video")

    # Save metadata
    with open(video_dir / "metadata.json", 'w') as f:
        json.dump(video, f, indent=2)

print("\n✓ Download attempt complete. Check", OUTPUT_DIR, "for results")
print("\nIf videos still failed, you may need to:")
print("1. Install browser cookies support: pip install browser-cookie3")
print("2. Make sure you're logged into YouTube in your browser")
print("3. Or manually download a few key videos from YouTube")
