#!/bin/bash
# Batch audio analysis for Fern videos with visual analysis + subtitles

echo "🔍 Finding Fern videos with visual analysis + subtitles..."
echo ""

analyzed=0
skipped=0

for video_dir in analysis/fern/*/; do
  video_id=$(basename "$video_dir")
  video_file="$video_dir/video.mp4"
  vtt_file="$video_dir/video.en.vtt"
  timeline_file="$video_dir/timeline_hybrid_gemini-flash.json"
  
  # Check if video has BOTH visual analysis AND subtitles
  if [ -f "$video_file" ] && [ -f "$vtt_file" ] && [ -f "$timeline_file" ]; then
    echo "✅ Analyzing: $video_id"
    python src/phase2b_audio_visual_sync.py "$video_file" "$video_id" fern
    ((analyzed++))
    echo ""
  else
    # Show why it was skipped
    if [ ! -f "$timeline_file" ]; then
      echo "⏭️  Skipping $video_id: no visual analysis"
    elif [ ! -f "$vtt_file" ]; then
      echo "⏭️  Skipping $video_id: no subtitles"
    elif [ ! -f "$video_file" ]; then
      echo "⏭️  Skipping $video_id: no video file"
    fi
    ((skipped++))
  fi
done

echo ""
echo "============================================"
echo "✅ Audio analysis complete!"
echo "   Analyzed: $analyzed videos"
echo "   Skipped: $skipped videos"
echo "============================================"
