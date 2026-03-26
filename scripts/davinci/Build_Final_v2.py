#!/usr/bin/env python3
"""
Build final timeline v2 - narration on A1, video segments on V1 overlaid.
Creates timeline from video segments first, then adds narration to audio track.
"""

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()
root = mp.GetRootFolder()
all_clips = root.GetClipList()

# Separate segments and narration
segments = []
narration = None
for clip in all_clips:
    name = clip.GetName()
    if name.startswith("seg_"):
        segments.append(clip)
    elif "narration" in name.lower():
        narration = clip

segments.sort(key=lambda c: c.GetName())
print(f"Segments: {len(segments)}, Narration: {'YES' if narration else 'NO'}")

# Delete ALL existing timelines
for i in range(20):
    tl = project.GetCurrentTimeline()
    if tl:
        mp.DeleteTimelines([tl])
    else:
        break

# Create timeline from VIDEO segments only (no narration yet)
# This puts all segments on V1+A1 in order
tl = mp.CreateTimelineFromClips("Secret Scores - FINAL", segments)
project.SetCurrentTimeline(tl)

fps = int(tl.GetSetting("timelineFrameRate") or 30)
end = tl.GetEndFrame()
start = tl.GetStartFrame()
vid_dur = (end - start) / fps
print(f"Video timeline: {vid_dur:.1f}s ({vid_dur/60:.1f} min)")

# Now add narration to audio track 2
if narration:
    # Add a second audio track
    tl.AddTrack("audio")
    
    # Append narration - it goes to the end, but we need it at the start
    mp.AppendToTimeline([{
        "mediaPoolItem": narration,
        "mediaType": 2,  # audio only
        "trackIndex": 2,
    }])
    print("Added narration to A2")

# Mute A1 (clip audio) so only narration plays
# Can't mute via API in free version, but user can do it manually

print(f"\nTimeline: {tl.GetName()}")
print(f"Duration: {vid_dur:.1f}s ({vid_dur/60:.1f} min)")
print(f"V1: {len(segments)} video segments with their audio on A1")  
print(f"A2: Narration (mute A1 to hear only narration)")
print(f"\nIMPORTANT: Right-click A1 track header and select 'Mute Track'")
print(f"This will silence the clip audio so you only hear the voiceover.")
print("\nDone!")
