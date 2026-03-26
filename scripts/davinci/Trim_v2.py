#!/usr/bin/env python3
"""
Trim v2 - Use ripple trim to shorten clips
"""
import json
from pathlib import Path

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetCurrentTimeline()
fps = int(timeline.GetSetting("timelineFrameRate") or 30)

# Load manifest
manifest_path = Path("/Users/jefflawrence/Documents/youtube-automation-production/audio/secret_scores/narration_manifest.json")
with open(manifest_path) as f:
    manifest = json.load(f)

speech_durations = [seg.get("duration_sec", 3) for seg in manifest["segments"] if seg["type"] == "speech"]
items = timeline.GetItemListInTrack("video", 1)

print(f"Items: {len(items)}, Target durations: {len(speech_durations)}")

# Try multiple trim methods
trimmed = 0
for i, item in enumerate(items):
    if i >= len(speech_durations):
        break
    
    target_frames = max(fps, int(speech_durations[i] * fps))  # at least 1 second
    current_dur = item.GetDuration()
    
    if current_dur <= target_frames:
        continue  # Already short enough
    
    # Method 1: Try SetDuration directly
    try:
        result = item.SetDuration(target_frames)
        if result:
            trimmed += 1
            continue
    except:
        pass
    
    # Method 2: Try trimming right edge
    try:
        # Get source in/out
        src_in = item.GetSourceStartFrame() or 0
        # Set source end
        item.SetSourceEndFrame(src_in + target_frames)
        trimmed += 1
        continue
    except:
        pass
    
    # Method 3: Modify clip properties
    try:
        props = item.GetProperty()
        if props:
            for k in sorted(props.keys()):
                if i == 0:  # Print properties of first clip to understand structure
                    print(f"  Property: {k} = {props[k]}")
    except:
        pass

print(f"\nTrimmed: {trimmed}")
end = timeline.GetEndFrame()
start = timeline.GetStartFrame() 
print(f"Duration: {(end-start)/fps:.1f}s ({(end-start)/fps/60:.1f} min)")
print("Done!")
