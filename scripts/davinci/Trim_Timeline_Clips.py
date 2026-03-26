#!/usr/bin/env python3
"""
Trim Timeline Clips to match narration timing
Run AFTER Build_Secret_Scores_Timeline
Workspace > Scripts > Edit > Trim_Timeline_Clips
"""
import json
from pathlib import Path

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetCurrentTimeline()

if not timeline:
    print("ERROR: No timeline open!")
else:
    print(f"Timeline: {timeline.GetName()}")
    fps = int(timeline.GetSetting("timelineFrameRate") or 30)
    
    # Load manifest for segment durations
    manifest_path = Path("/Users/jefflawrence/Documents/youtube-automation-production/audio/secret_scores/narration_manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Get speech segment durations
    speech_durations = []
    for seg in manifest["segments"]:
        if seg["type"] == "speech":
            speech_durations.append(seg.get("duration_sec", 3))
    
    print(f"Speech segments: {len(speech_durations)}")
    
    # Get all timeline items on V1
    items = timeline.GetItemListInTrack("video", 1)
    print(f"Timeline items on V1: {len(items)}")
    
    # Trim each item to match narration duration
    trimmed = 0
    for i, item in enumerate(items):
        if i < len(speech_durations):
            target_dur = speech_durations[i]
            target_frames = max(1, int(target_dur * fps))
            
            current_dur = item.GetDuration()
            
            if current_dur > target_frames:
                # Trim by setting the end to start + target
                start = item.GetStart()
                new_end = start + target_frames
                
                # Use SetDuration or trim
                result = item.SetProperty("End", new_end)
                if not result:
                    # Try alternative: change clip end
                    src_end = item.GetLeftOffset() + target_frames
                    item.SetProperty("RightOffset", current_dur - target_frames + item.GetRightOffset())
                
                trimmed += 1
                if i < 5:
                    print(f"  [{i}] {item.GetName()[:30]}: {current_dur} -> {target_frames} frames ({target_dur:.1f}s)")
    
    print(f"\nTrimmed {trimmed} clips")
    
    # Check new duration
    end = timeline.GetEndFrame()
    start = timeline.GetStartFrame()
    print(f"New timeline duration: {(end-start)/fps:.1f}s ({(end-start)/fps/60:.1f} min)")

print("\nDone!")
