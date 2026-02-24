#!/usr/bin/env python3
"""Direct download of Fern videos using video IDs we already have"""
import subprocess
from pathlib import Path

# Video IDs from our previous scan (already in analysis/fern/)
video_ids = [
    'wLFY_Zu_O08',  # FBI/KKK - 11.2M views
    'I1rzcZWTIjo',  # Pentagon Hacker - 5.4M views
    'qqJSXoa5ZtQ',  # Secret Building - 5.1M views
    'yXdzKqhEA9M',  # Otto Warmbier - 4.7M views
    '8Gm7kSUkBAk',  # Camp 14 - 4.5M views
    'fHRS_NOs24w',  # Indian Genius - 4.4M views
    'ZhfI0EboPU0',  # Russia Hackers - 4.4M views
    'OpUEEr-F5dY',  # Charlie Kirk - 4.3M views
    'HauQtcj7UTM',  # Modern Cars - 4.2M views
    'imCjhNEovL4',  # Minecraft Scammer - 3.5M views
]

OUTPUT_DIR = Path("analysis/fern")

print(f"Downloading top {len(video_ids)} Fern videos...")
print(f"Using proven yt-dlp format from WATOP analyzer")

for i, video_id in enumerate(video_ids, 1):
    print(f"\n[{i}/{len(video_ids)}] Downloading {video_id}...")

    video_dir = OUTPUT_DIR / video_id
    video_dir.mkdir(exist_ok=True, parents=True)

    output_template = str(video_dir / f"{video_id}.%(ext)s")

    # Use the EXACT command from phase1_analyzer that worked for WATOP
    cmd = [
        'yt-dlp',
        '--no-check-certificates',  # Bypass SSL issues
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '-o', output_template,
        f'https://www.youtube.com/watch?v={video_id}'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ Downloaded successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Download failed: {e.stderr[:200]}")
        # Try alternate format
        print(f"  Trying alternate format...")
        cmd_alt = [
            'yt-dlp',
            '--no-check-certificates',
            '-f', '18',  # Standard 360p MP4 that usually works
            '-o', output_template,
            f'https://www.youtube.com/watch?v={video_id}'
        ]
        try:
            result = subprocess.run(cmd_alt, capture_output=True, text=True, check=True)
            print(f"✓ Downloaded with alternate format")
        except Exception as e2:
            print(f"✗ Both formats failed: {str(e2)[:100]}")

print(f"\n✓ Download complete! Videos saved to {OUTPUT_DIR}")
