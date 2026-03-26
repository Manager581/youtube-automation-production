#!/usr/bin/env python3
"""
Soundbite Punch-Through V2

Strategy: Since we can't set per-clip volume in free Resolve,
we keep A1 globally muted and create new audio-only clips on A3
at soundbite punch-through points from the ORIGINAL source clips.

This gives us:
- V1: Pre-trimmed video segments (visual b-roll)
- A1: MUTED (original clip audio, globally muted)  
- A2: narration.wav (voiceover)
- A3: Soundbite punch-throughs (selected moments of source audio)
"""

import os

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()
tl = project.GetCurrentTimeline()
fps = int(tl.GetSetting("timelineFrameRate") or 30)
sf = tl.GetStartFrame()

print("=== Soundbite Punch-Through V2 ===")
print(f"Timeline: {tl.GetName()}")
print(f"Duration: {(tl.GetEndFrame()-sf)/fps:.1f}s")

# Add audio track 3 for soundbites
tl.AddTrack("audio")
a3_count = tl.GetTrackCount("audio")
print(f"Added audio track (now {a3_count} audio tracks)")

# Get all media pool clips (original source clips, not pre-trimmed)
root = mp.GetRootFolder()
all_clips = root.GetClipList()

# Build lookup of original source clips
source_clips = {}
for clip in all_clips:
    name = clip.GetName()
    # Skip pre-trimmed segments
    if name.startswith("seg_"):
        continue
    if name == "narration.wav":
        continue
    source_clips[name] = clip

print(f"\nOriginal source clips: {len(source_clips)}")
for name in sorted(source_clips.keys()):
    frames = source_clips[name].GetClipProperty("Frames")
    dur = int(frames) / fps if frames else 0
    print(f"  {name[:55]} ({dur:.0f}s)")

# Define soundbite punch-throughs
# Each uses the ORIGINAL source clip, placed on A3 at the right timeline position
# Format: (source_name_fragment, timeline_position_sec, clip_start_sec, clip_end_sec, description)
soundbites = [
    # 1. John Oliver on data brokers - "they know more about you"
    ("data_brokers", "last_week", 187, 193, 206, "Data brokers know more about you"),
    
    # 2. Jacksonville housing discrimination lawsuit - news anchor
    ("lawsuit", "jacksonville", 129, 136, 87, "Screening algorithm flags renters"),
    
    # 3. Uber drivers - "is this legal?"
    ("uber", "7_uber", 344, 352, 292, "No laws against algorithmic discrimination"),
    
    # 4. Cigna claim denials
    ("cigna", "exposing", 217, 223, 437, "Raked in $40 billion in profits"),
    
    # 5. Health insurance AI denials - "49 million denials"
    ("algorithms_are_being", "deny_health", 5, 11, 600, "49 million denials in 2021"),
    
    # 6. LexisNexis telematics
    ("lexisnexis_telematics", "telematics", 30, 37, 800, "Your car is raising your rates"),
]

applied = 0
fairlight_ducks = []

for i, (match1, match2, clip_start, clip_end, tl_pos_sec, desc) in enumerate(soundbites):
    print(f"\nSoundbite {i+1}: {desc}")
    
    # Find the source clip
    found_clip = None
    for name, clip in source_clips.items():
        name_lower = name.lower().replace(" ", "_")
        if match1 in name_lower or match2 in name_lower:
            found_clip = clip
            print(f"  Source: {name[:50]}")
            break
    
    if not found_clip:
        print(f"  NO SOURCE CLIP found for '{match1}' / '{match2}'")
        continue
    
    # Place audio-only excerpt on A3 at the target timeline position
    tl_frame = int(tl_pos_sec * fps) + sf
    clip_start_frame = int(clip_start * fps)
    clip_end_frame = int(clip_end * fps)
    
    try:
        result = mp.AppendToTimeline([{
            "mediaPoolItem": found_clip,
            "mediaType": 2,  # Audio only
            "trackIndex": 3,  # A3
            "startFrame": clip_start_frame,
            "endFrame": clip_end_frame,
        }])
        
        if result:
            print(f"  Placed on A3: clip {clip_start}s-{clip_end}s at timeline ~{tl_pos_sec}s")
            applied += 1
            fairlight_ducks.append({
                "pos": tl_pos_sec,
                "dur": clip_end - clip_start,
                "desc": desc,
            })
        else:
            print(f"  FAILED to append to timeline")
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\n=== Results ===")
print(f"Applied {applied} / {len(soundbites)} soundbite punch-throughs on A3")

if fairlight_ducks:
    print(f"\n=== NEXT STEPS ===")
    print(f"1. Go to Fairlight tab")
    print(f"2. Duck A2 (narration) volume at these points:")
    for d in fairlight_ducks:
        print(f"   {d['pos']:.0f}s ({d['pos']/60:.1f}min) for {d['dur']:.0f}s: {d['desc']}")
    print(f"3. A1 should remain muted (right-click A1 header > Mute Track)")
    print(f"4. A3 soundbites play at full volume")

print("\nDone!")
