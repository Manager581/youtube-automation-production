#!/usr/bin/env python3
"""
Fix corrupted checkpoint from buggy resume.

This script restores current_frame_index to 1500 if it got reset to a low value
during the buggy run that started from frame 0 instead of resuming from 1500.
"""

import json
from pathlib import Path
import shutil
from datetime import datetime

CHECKPOINT_FILE = Path('analysis/fern/.checkpoint.json')

def fix_checkpoint():
    """Fix the checkpoint if it got corrupted"""

    if not CHECKPOINT_FILE.exists():
        print("❌ No checkpoint file found")
        return False

    # Backup first
    backup_file = CHECKPOINT_FILE.parent / f'.checkpoint.json.backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    shutil.copy(CHECKPOINT_FILE, backup_file)
    print(f"✅ Backup created: {backup_file}")

    # Load checkpoint
    with open(CHECKPOINT_FILE, 'r') as f:
        cp = json.load(f)

    print(f"\nCurrent checkpoint state:")
    print(f"  Video index: {cp['current_video_index']}")
    print(f"  Frame index: {cp['current_frame_index']}")
    print(f"  Requests today: {cp['requests_today']}")
    print(f"  Total processed: {cp['total_processed']}")
    print(f"  Date: {cp['date']}")

    # Detect if it needs fixing
    # If we're on video 1 and frame index is low (< 1400), it likely got reset by the bug
    if cp['current_video_index'] == 1 and cp['current_frame_index'] < 1400:
        print(f"\n🔧 Detected corrupted checkpoint!")
        print(f"   Frame index is {cp['current_frame_index']} but should be 1500")
        print(f"   (The buggy script reset it and redid frames 0-{cp['current_frame_index']-1})")

        # Fix it
        cp['current_frame_index'] = 1500

        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(cp, f, indent=2)

        print(f"\n✅ FIXED! Frame index restored to 1500")
        print(f"   You have {1500 - cp['requests_today']} API calls left today")
        print(f"\nNow run:")
        print(f"  python analyze_fern_hybrid_checkpoint.py --all --model gemini-flash --resume")
        return True
    else:
        print(f"\n✅ Checkpoint looks OK, no fix needed")
        return False

if __name__ == '__main__':
    fix_checkpoint()
