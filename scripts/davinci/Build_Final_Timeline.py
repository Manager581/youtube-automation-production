#!/usr/bin/env python3
"""
Build final timeline from pre-trimmed segments.
Segments are already cut to correct duration and named in order.
"""
import json
from pathlib import Path

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()

# Get all clips
root = mp.GetRootFolder()
all_clips = root.GetClipList()

# Separate segments from other media
segments = []
narration = None
for clip in all_clips:
    name = clip.GetName()
    if name.startswith("seg_"):
        segments.append(clip)
    elif "narration" in name.lower():
        narration = clip

# Sort segments by name (seg_000, seg_001, etc.)
segments.sort(key=lambda c: c.GetName())
print(f"Found {len(segments)} pre-trimmed segments")
print(f"Narration: {'YES' if narration else 'NO'}")

# Delete old timelines
for i in range(10):
    tl = project.GetCurrentTimeline()
    if tl:
        print(f"Deleting timeline: {tl.GetName()}")
        mp.DeleteTimelines([tl])
    else:
        break

# Create new timeline with narration first
if narration:
    tl = mp.CreateTimelineFromClips("Secret Scores - FINAL", [narration])
    print(f"Created timeline with narration: {tl.GetName()}")
else:
    tl = mp.CreateEmptyTimeline("Secret Scores - FINAL")
    print("Created empty timeline (no narration found)")

project.SetCurrentTimeline(tl)

# Append all segments in order
print(f"Appending {len(segments)} video segments...")
batch_size = 20
for i in range(0, len(segments), batch_size):
    batch = segments[i:i+batch_size]
    items = [{"mediaPoolItem": clip} for clip in batch]
    mp.AppendToTimeline(items)
    if (i + batch_size) % 100 == 0:
        print(f"  {i + batch_size} segments added...")

fps = int(tl.GetSetting("timelineFrameRate") or 30)
end = tl.GetEndFrame()
start = tl.GetStartFrame()
dur = (end - start) / fps

print(f"\nTimeline: {tl.GetName()}")
print(f"Duration: {dur:.1f}s ({dur/60:.1f} min)")
print(f"Video tracks: {tl.GetTrackCount('video')}")
print(f"Audio tracks: {tl.GetTrackCount('audio')}")
print("\nDone! Press play to preview.")
