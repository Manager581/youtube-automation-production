#!/bin/bash
# Run this on your Mac: bash copy_fern_videos.sh

DESKTOP_FERN=~/Desktop/FERN
PROJECT_DIR=$(pwd)

echo "Copying Fern videos to analysis folders..."

cp "$DESKTOP_FERN/YTDown.com_YouTube_How-an-FBI-Agent-Infiltrated-the-KKK_Media_wLFY_Zu_O08_001_1080p.mp4" "$PROJECT_DIR/analysis/fern/wLFY_Zu_O08/video.mp4"
echo "✓ Copied FBI/KKK video"

cp "$DESKTOP_FERN/YTDown.com_YouTube_Mapping-the-Trump-Shooting_Media_aVA7aXOH1pk_001_1080p.mp4" "$PROJECT_DIR/analysis/fern/aVA7aXOH1pk/video.mp4"
echo "✓ Copied Trump Shooting video"

cp "$DESKTOP_FERN/YTDown.com_YouTube_The-Hunt-for-America-s-Smartest-Killer_Media_wkVygetgeRY_001_1080p.mp4" "$PROJECT_DIR/analysis/fern/wkVygetgeRY/video.mp4"
echo "✓ Copied Smartest Killer video"

echo ""
echo "Done! Videos copied to:"
ls -lh "$PROJECT_DIR/analysis/fern/"*/video.mp4
