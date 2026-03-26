#!/usr/bin/env python3
"""
Fix Soundbites - Remove wrong A3 clips and add the pre-built soundbites WAV
"""
import os

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()
tl = project.GetCurrentTimeline()
fps = int(tl.GetSetting("timelineFrameRate") or 30)

print("=== Fix Soundbites ===")

# Delete track A3 (has wrong clips) and recreate
# Can't easily delete track items, so delete the whole track and recreate
try:
    tl.DeleteTrack("audio", 3)
    print("Deleted old A3 track")
except:
    print("No A3 to delete (or can't delete)")

# Add fresh A3
tl.AddTrack("audio")
print("Added fresh A3 track")

# Import the soundbites WAV
home = os.path.expanduser("~")
sb_path = os.path.join(home, "Desktop", "SecretScores_Media", "soundbites_track.wav")

root = mp.GetRootFolder()
mp.SetCurrentFolder(root)

# Check if already imported
all_clips = root.GetClipList()
sb_clip = None
for clip in all_clips:
    if "soundbites_track" in clip.GetName():
        sb_clip = clip
        break

if not sb_clip:
    items = mp.ImportMedia([sb_path])
    if items:
        sb_clip = items[0]
        print(f"Imported: {sb_clip.GetName()}")
    else:
        print("ERROR: Could not import soundbites_track.wav")

if sb_clip:
    # Add to A3 (audio only)
    result = mp.AppendToTimeline([{
        "mediaPoolItem": sb_clip,
        "mediaType": 2,  # Audio only
        "trackIndex": 3,
    }])
    if result:
        print("Added soundbites track to A3")
    else:
        print("ERROR adding to timeline")

# Summary
print(f"\nTimeline tracks:")
print(f"  V1: {len(tl.GetItemListInTrack('video', 1) or [])} video clips")
print(f"  A1: {len(tl.GetItemListInTrack('audio', 1) or [])} clip audio (MUTE THIS)")
print(f"  A2: {len(tl.GetItemListInTrack('audio', 2) or [])} narration")
a3 = tl.GetItemListInTrack("audio", 3) or []
print(f"  A3: {len(a3)} soundbite track")

print(f"\n=== NEXT STEPS ===")
print(f"1. Right-click A1 track header > Mute Track")
print(f"2. Go to Fairlight tab to duck A2 at soundbite points:")
print(f"   87s (1.5min) for 7s: Screening algorithm flags renters")
print(f"   206s (3.4min) for 6s: Data brokers know more about you")
print(f"   292s (4.9min) for 8s: No laws against algorithmic discrimination")
print(f"   437s (7.3min) for 6s: Raked in $40 billion in profits")
print(f"   600s (10.0min) for 6s: 49 million denials in 2021")
print(f"   800s (13.3min) for 7s: Your car is raising your rates")
print(f"3. Play to preview! A3 soundbites are already at correct positions.")
print(f"\nDone!")
