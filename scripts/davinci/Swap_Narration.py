#!/usr/bin/env python3
"""
Swap narration.wav on A2 with narration_ducked.wav
(has volume dips pre-baked at soundbite punch-through points)
"""
import os

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()
tl = project.GetCurrentTimeline()

print("=== Swap Narration (Ducked Version) ===")

# Import ducked narration
home = os.path.expanduser("~")
ducked_path = os.path.join(home, "Desktop", "SecretScores_Media", "narration_ducked.wav")

root = mp.GetRootFolder()
mp.SetCurrentFolder(root)

# Import
items = mp.ImportMedia([ducked_path])
if items:
    ducked_clip = items[0]
    print(f"Imported: {ducked_clip.GetName()}")
else:
    print("ERROR importing narration_ducked.wav")
    ducked_clip = None

if not ducked_clip:
    # Try finding it if already imported
    for clip in root.GetClipList():
        if "narration_ducked" in clip.GetName():
            ducked_clip = clip
            print(f"Found existing: {ducked_clip.GetName()}")
            break

if ducked_clip:
    # Delete old A2 content
    a2_items = tl.GetItemListInTrack("audio", 2) or []
    print(f"Current A2 items: {len(a2_items)}")
    
    # Delete old narration from A2
    for item in a2_items:
        try:
            tl.DeleteClips([item])
            print(f"  Deleted: {item.GetName()}")
        except Exception as e:
            print(f"  Could not delete: {e}")
    
    # Add ducked narration to A2
    result = mp.AppendToTimeline([{
        "mediaPoolItem": ducked_clip,
        "mediaType": 2,  # Audio only
        "trackIndex": 2,
    }])
    if result:
        print("Added narration_ducked.wav to A2")
    else:
        print("ERROR adding to A2")

# Verify
a2 = tl.GetItemListInTrack("audio", 2) or []
a3 = tl.GetItemListInTrack("audio", 3) or []
print(f"\nFinal state:")
print(f"  A2: {len(a2)} items (ducked narration)")
print(f"  A3: {len(a3)} items (soundbites)")

print(f"\nDuck points baked into narration:")
print(f"  87s (1.5min) - 94s: Screening algorithm")
print(f"  206s (3.4min) - 212s: Data brokers")
print(f"  292s (4.9min) - 300s: Algorithmic discrimination") 
print(f"  437s (7.3min) - 443s: $40B profits")
print(f"  600s (10.0min) - 606s: 49M denials")
print(f"  800s (13.3min) - 807s: Your car raising rates")
print(f"\nDone! Play to preview.")
