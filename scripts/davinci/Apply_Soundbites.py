#!/usr/bin/env python3
"""
Apply Soundbite Punch-Throughs to Secret Scores Timeline

Strategy:
1. Mute ALL A1 clip audio by default (set volume to 0)
2. For each soundbite, find the V1 clip at the right timeline position
   that matches the source clip name
3. Unmute that clip's A1 audio
4. Print instructions for manual narration ducking in Fairlight

Run from DaVinci: Workspace > Scripts > Apply_Soundbites
"""

resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
tl = project.GetCurrentTimeline()
fps = int(tl.GetSetting("timelineFrameRate") or 30)
start_frame = tl.GetStartFrame()
end_frame = tl.GetEndFrame()
total_dur = (end_frame - start_frame) / fps

print(f"Timeline: {tl.GetName()}")
print(f"Duration: {total_dur:.1f}s ({total_dur/60:.1f} min)")
print(f"FPS: {fps}")

# Get all V1 and A1 items
v1_items = tl.GetItemListInTrack("video", 1) or []
a1_items = tl.GetItemListInTrack("audio", 1) or []
a2_items = tl.GetItemListInTrack("audio", 2) or []

print(f"V1 clips: {len(v1_items)}")
print(f"A1 clips: {len(a1_items)}")
print(f"A2 clips: {len(a2_items)}")

# Soundbite definitions — source name fragments to match against segment names
# Timeline positions are estimated from script word count, need to scale to actual duration
# Script estimate total ~1700s, actual ~1190s, scale = actual/estimate
SCALE = total_dur / 1700.0

soundbites = [
    {
        "source_match": "data_brokers",  # Last Week Tonight 
        "source_match_alt": "john_oliver",
        "est_pos_sec": 250,
        "duration": 6.1,
        "text": "data brokers know significantly more about you",
    },
    {
        "source_match": "jacksonville",
        "source_match_alt": "lawsuit",
        "est_pos_sec": 475,
        "duration": 7.0,
        "text": "screening platform algorithm flags renters",
    },
    {
        "source_match": "uber_drivers",
        "source_match_alt": "uber",
        "est_pos_sec": 714,
        "duration": 8.0,
        "text": "is this legal? no laws against algorithmic discrimination",
    },
    {
        "source_match": "cigna",
        "source_match_alt": "exposing",
        "est_pos_sec": 1027,
        "duration": 6.2,
        "text": "raked in more than $40 billion in profits",
    },
    {
        "source_match": "jacksonville",
        "source_match_alt": "lawsuit",
        "est_pos_sec": 1273,
        "duration": 8.0,
        "text": "lawsuits against screening companies inaccurate results",
    },
    {
        "source_match": "algorithms",
        "source_match_alt": "deny_health",
        "est_pos_sec": 1505,
        "duration": 6.0,
        "text": "49 million denials in 2021",
    },
]

# Step 1: Mute all A1 clips
print("\n--- Step 1: Muting all A1 clip audio ---")
muted = 0
for item in a1_items:
    try:
        item.SetClipProperty("Volume", "0.0")
        muted += 1
    except:
        pass
print(f"Muted {muted} A1 clips")

# Step 2: For each soundbite, find matching clips and unmute
print("\n--- Step 2: Applying soundbite punch-throughs ---")
applied = 0
fairlight_notes = []

for i, sb in enumerate(soundbites):
    # Scale position to actual timeline
    target_sec = sb["est_pos_sec"] * SCALE
    target_frame = int(target_sec * fps) + start_frame
    search_range = int(30 * fps)  # Search +/- 30 seconds
    
    match_lo = sb["source_match"].lower().replace(" ", "_")
    match_alt = sb["source_match_alt"].lower().replace(" ", "_")
    
    print(f"\n  Soundbite {i+1}: {sb['text'][:50]}...")
    print(f"    Target: {target_sec:.1f}s ({target_sec/60:.1f}min)")
    print(f"    Looking for: '{match_lo}' or '{match_alt}'")
    
    # Search A1 items near the target position
    best_item = None
    best_dist = float("inf")
    
    for item in a1_items:
        item_start = item.GetStart()
        item_end = item.GetEnd()
        item_mid = (item_start + item_end) / 2
        
        # Check if this clip is near the target
        dist = abs(item_mid - target_frame)
        if dist > search_range:
            continue
        
        # Check if the clip name matches the source
        try:
            name = item.GetName().lower().replace(" ", "_")
        except:
            name = ""
        
        if match_lo in name or match_alt in name:
            if dist < best_dist:
                best_dist = dist
                best_item = item
    
    if best_item:
        try:
            best_item.SetClipProperty("Volume", "1.0")
            item_start_sec = (best_item.GetStart() - start_frame) / fps
            item_end_sec = (best_item.GetEnd() - start_frame) / fps
            print(f"    UNMUTED: {best_item.GetName()[:50]} at {item_start_sec:.1f}s - {item_end_sec:.1f}s")
            applied += 1
            
            # Note for Fairlight ducking
            fairlight_notes.append({
                "index": i + 1,
                "duck_start": item_start_sec - 0.5,
                "duck_end": item_end_sec + 0.5,
                "text": sb["text"][:50],
            })
        except Exception as e:
            print(f"    ERROR setting volume: {e}")
    else:
        print(f"    NO MATCH found near {target_sec:.1f}s")

print(f"\n--- Results ---")
print(f"Applied {applied} / {len(soundbites)} soundbite punch-throughs")

if fairlight_notes:
    print(f"\n--- Fairlight Narration Ducking Points ---")
    print(f"Switch to Fairlight tab and lower A2 volume at these points:")
    for note in fairlight_notes:
        print(f"  [{note['index']}] {note['duck_start']:.1f}s - {note['duck_end']:.1f}s: {note['text']}")
    print(f"\nTip: Use volume automation (keyframes) in Fairlight to duck")
    print(f"A2 to -inf dB at each point, with 0.3s fade in and 0.5s fade out.")

print("\nDone!")
