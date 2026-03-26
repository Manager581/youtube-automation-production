#!/usr/bin/env python3
"""
Rebuild Final Timeline with ducked narration + soundbites

Creates a clean timeline:
- V1+A1: 215 pre-trimmed segments (A1 muted)
- A2: narration_ducked.wav (volume dips at soundbite points)
- A3: soundbites_track.wav (source audio punch-throughs)
"""

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()
root = mp.GetRootFolder()

print("=== Rebuild Final Timeline ===")

# Get all clips
all_clips = root.GetClipList()

# Separate by type
segments = []
narration_ducked = None
soundbites_track = None
narration_orig = None

for clip in all_clips:
    name = clip.GetName()
    if name.startswith("seg_"):
        segments.append(clip)
    elif "narration_ducked" in name:
        narration_ducked = clip
    elif "soundbites_track" in name:
        soundbites_track = clip
    elif name == "narration.wav":
        narration_orig = clip

segments.sort(key=lambda c: c.GetName())
print(f"Segments: {len(segments)}")
print(f"Narration (ducked): {'YES' if narration_ducked else 'NO'}")
print(f"Soundbites track: {'YES' if soundbites_track else 'NO'}")

# Delete ALL existing timelines
for i in range(20):
    tl = project.GetCurrentTimeline()
    if tl:
        mp.DeleteTimelines([tl])
    else:
        break
print("Deleted old timelines")

# Create timeline from video segments (V1 + A1)
tl = mp.CreateTimelineFromClips("Secret Scores - FINAL", segments)
project.SetCurrentTimeline(tl)

fps = int(tl.GetSetting("timelineFrameRate") or 30)
sf = tl.GetStartFrame()
ef = tl.GetEndFrame()
vid_dur = (ef - sf) / fps
print(f"Created timeline: {vid_dur:.1f}s ({vid_dur/60:.1f}min)")
print(f"V1: {len(segments)} segments")

# Add A2 track and place ducked narration
tl.AddTrack("audio")
if narration_ducked:
    mp.AppendToTimeline([{
        "mediaPoolItem": narration_ducked,
        "mediaType": 2,
        "trackIndex": 2,
    }])
    print("A2: narration_ducked.wav added")

# Add A3 track and place soundbites
tl.AddTrack("audio")
if soundbites_track:
    mp.AppendToTimeline([{
        "mediaPoolItem": soundbites_track,
        "mediaType": 2,
        "trackIndex": 3,
    }])
    print("A3: soundbites_track.wav added")

# Report
print(f"\nFinal timeline: {tl.GetName()}")
print(f"Duration: {vid_dur:.1f}s ({vid_dur/60:.1f}min)")
v1 = tl.GetItemListInTrack("video", 1) or []
a1 = tl.GetItemListInTrack("audio", 1) or []
a2 = tl.GetItemListInTrack("audio", 2) or []
a3 = tl.GetItemListInTrack("audio", 3) or []
print(f"V1: {len(v1)} video clips")
print(f"A1: {len(a1)} clip audio (MUTE THIS)")
print(f"A2: {len(a2)} ducked narration")
print(f"A3: {len(a3)} soundbites")

print(f"\nIMPORTANT: Right-click A1 track header > Mute Track")
print(f"\nSoundbite punch-throughs at:")
print(f"  87s, 206s, 292s, 437s, 600s, 800s")
print(f"\nDone!")
