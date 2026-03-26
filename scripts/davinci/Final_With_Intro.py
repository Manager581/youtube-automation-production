#!/usr/bin/env python3
"""
Final Timeline with Intro Montage + Soundbite Punch-Throughs

Structure:
- V1: intro_montage.mp4 → 215 pre-trimmed segments
- A1: MUTED (clip audio from segments)
- A2: narration_ducked.wav (offset by montage, with volume dips)
- A3: soundbites_track.wav (offset, 6 punch-throughs)
"""
import os

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()
root = mp.GetRootFolder()

print("=== Final Timeline with Intro Montage ===")

# Import new files
home = os.path.expanduser("~")
media_dir = os.path.join(home, "Desktop", "SecretScores_Media")

new_files = [
    os.path.join(media_dir, "intro_montage.mp4"),
    os.path.join(media_dir, "narration_ducked.wav"),
    os.path.join(media_dir, "soundbites_track.wav"),
]

mp.SetCurrentFolder(root)
for f in new_files:
    if os.path.exists(f):
        items = mp.ImportMedia([f])
        if items:
            print(f"  Imported: {os.path.basename(f)}")
    else:
        print(f"  NOT FOUND: {f}")

# Get all clips
all_clips = root.GetClipList()
segments = []
intro_clip = None
narration_clip = None
soundbites_clip = None

for clip in all_clips:
    name = clip.GetName()
    if name.startswith("seg_"):
        segments.append(clip)
    elif "intro_montage" in name:
        intro_clip = clip
    elif "narration_ducked" in name:
        narration_clip = clip
    elif "soundbites_track" in name:
        soundbites_clip = clip

segments.sort(key=lambda c: c.GetName())
print(f"\nIntro: {'YES' if intro_clip else 'NO'}")
print(f"Segments: {len(segments)}")
print(f"Narration (ducked): {'YES' if narration_clip else 'NO'}")
print(f"Soundbites: {'YES' if soundbites_clip else 'NO'}")

# Delete old timelines
for i in range(20):
    tl = project.GetCurrentTimeline()
    if tl:
        mp.DeleteTimelines([tl])
    else:
        break

# Build clip list: intro first, then segments
timeline_clips = []
if intro_clip:
    timeline_clips.append(intro_clip)
timeline_clips.extend(segments)

# Create timeline from all video clips (intro + segments)
tl = mp.CreateTimelineFromClips("Secret Scores - FINAL", timeline_clips)
project.SetCurrentTimeline(tl)

fps = int(tl.GetSetting("timelineFrameRate") or 30)
sf = tl.GetStartFrame()
ef = tl.GetEndFrame()
dur = (ef - sf) / fps
print(f"\nTimeline: {dur:.1f}s ({dur/60:.1f}min)")

# Add A2: ducked narration (offset version)
tl.AddTrack("audio")
if narration_clip:
    mp.AppendToTimeline([{
        "mediaPoolItem": narration_clip,
        "mediaType": 2,
        "trackIndex": 2,
    }])
    print("A2: narration (ducked+offset) added")

# Add A3: soundbites (offset version)
tl.AddTrack("audio")
if soundbites_clip:
    mp.AppendToTimeline([{
        "mediaPoolItem": soundbites_clip,
        "mediaType": 2,
        "trackIndex": 3,
    }])
    print("A3: soundbites (offset) added")

# Summary
v1 = tl.GetItemListInTrack("video", 1) or []
a1 = tl.GetItemListInTrack("audio", 1) or []
a2 = tl.GetItemListInTrack("audio", 2) or []
a3 = tl.GetItemListInTrack("audio", 3) or []

print(f"\n=== FINAL TIMELINE ===")
print(f"Duration: {dur:.1f}s ({dur/60:.1f}min)")
print(f"V1: {len(v1)} clips (1 intro + {len(v1)-1} segments)")
print(f"A1: {len(a1)} clip audio (MUTE THIS)")
print(f"A2: {len(a2)} ducked narration")
print(f"A3: {len(a3)} soundbites")
print(f"\nIMPORTANT: Right-click A1 track header > Mute Track")
print(f"\nStructure:")
print(f"  0-25s: INTRO MONTAGE (fast clips with original audio)")
print(f"  25s+: Documentary narration with 6 soundbite punch-throughs")
print(f"\nDone!")
