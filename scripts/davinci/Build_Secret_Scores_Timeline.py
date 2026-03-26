#!/usr/bin/env python3
"""
Build Secret Scores Timeline v2
Run from: DaVinci Resolve > Workspace > Scripts > Edit > Build_Secret_Scores_Timeline
"""

import json
from pathlib import Path

resolve = app.GetResolve()
pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()
mp = project.GetMediaPool()

print(f"Project: {project.GetName()}")

# Step 1: Delete old timeline and create fresh one
old_tl = project.GetCurrentTimeline()
if old_tl:
    print(f"Deleting old timeline: {old_tl.GetName()}")
    mp.DeleteTimelines([old_tl])

# Step 2: Create new empty timeline
tl = mp.CreateEmptyTimeline("Secret Scores - Final")
project.SetCurrentTimeline(tl)
print(f"Created timeline: {tl.GetName()}")

# Step 3: Get all clips from media pool
root = mp.GetRootFolder()
all_clips = root.GetClipList()
print(f"Media pool: {len(all_clips)} clips")

clip_lookup = {}
narration = None
for clip in all_clips:
    name = clip.GetName()
    clip_lookup[name.lower()] = clip
    if "narration" in name.lower():
        narration = clip

# Step 4: Add narration to audio track
if narration:
    mp.AppendToTimeline([{"mediaPoolItem": narration, "startFrame": 0, "endFrame": narration.GetClipProperty("Frames")}])
    print("Added narration to timeline")
else:
    print("WARNING: No narration found!")

# Step 5: Load manifest
manifest_path = Path("/Users/jefflawrence/Documents/youtube-automation-production/audio/secret_scores/narration_manifest.json")
with open(manifest_path) as f:
    manifest = json.load(f)
print(f"Manifest: {len(manifest['segments'])} segments")

# Step 6: Keyword-to-clip matching (improved)
def match_clip(text):
    t = text.lower()
    
    # Cigna / insurance
    if any(w in t for w in ["cigna", "claim denied", "health insurance", "1.2 second"]):
        for k, v in clip_lookup.items():
            if "cigna" in k or ("insurance" in k and "deny" in k):
                return v
        for k, v in clip_lookup.items():
            if "insurance" in k:
                return v
    
    # Kyle Behm / hiring / personality tests
    if any(w in t for w in ["kyle", "behm", "personality test", "hirevue", "hiring algorithm"]):
        for k, v in clip_lookup.items():
            if "algorithm" in k and "disab" in k:
                return v
    
    # Tenant screening / housing
    if any(w in t for w in ["tenant", "apartment", "evict", "landlord", "saferent", "housing denied", "mary louis"]):
        for k, v in clip_lookup.items():
            if "jacksonville" in k or "lawsuit" in k:
                return v
    
    # LexisNexis
    if any(w in t for w in ["lexisnexis", "telematics", "driving data", "consumer report"]):
        for k, v in clip_lookup.items():
            if "lexisnexis" in k:
                return v
    
    # FTC / Congress / regulation
    if any(w in t for w in ["ftc", "congress", "senator", "regulation", "legislat", "federal trade"]):
        for k, v in clip_lookup.items():
            if "senate" in k or "ftc" in k or "protecting" in k or "transforming" in k:
                return v
    
    # Data brokers general
    if any(w in t for w in ["data broker", "buying data", "selling data", "personal information", "surveillance"]):
        for k, v in clip_lookup.items():
            if "data broker" in k and "last week" in k:
                return v
        for k, v in clip_lookup.items():
            if "60 minutes" in k:
                return v
    
    # Privacy / DeleteMe / Incogni
    if any(w in t for w in ["opt out", "delete", "privacy", "request your data"]):
        for k, v in clip_lookup.items():
            if "incogni" in k or "deleteme" in k:
                return v
    
    # Uber / gig economy
    if any(w in t for w in ["uber", "driver", "gig"]):
        for k, v in clip_lookup.items():
            if "uber" in k:
                return v
    
    # Fallback rotation to avoid repeating same clip
    fallbacks = ["60 minutes", "data broker", "a data broker def"]
    for fb in fallbacks:
        for k, v in clip_lookup.items():
            if fb in k:
                return v
    
    # Last resort: first video clip
    for k, v in clip_lookup.items():
        if not k.endswith(".wav") and not k.endswith(".jpg") and not k.endswith(".webp"):
            return v
    return None

# Step 7: Place video clips per narration segment
fps = int(tl.GetSetting("timelineFrameRate") or 30)
placed = 0
clip_rotation_idx = 0
video_clips = [v for k, v in clip_lookup.items() if not k.endswith(".wav") and not k.endswith(".jpg") and not k.endswith(".webp")]

for seg in manifest["segments"]:
    if seg["type"] != "speech":
        continue
    
    text = seg.get("text", "")
    dur_sec = seg.get("duration_sec", 3)
    dur_frames = max(1, int(dur_sec * fps))
    
    clip = match_clip(text)
    if not clip and video_clips:
        clip = video_clips[clip_rotation_idx % len(video_clips)]
        clip_rotation_idx += 1
    
    if clip:
        clip_frames = int(clip.GetClipProperty("Frames") or dur_frames)
        start = min(clip_frames // 4, clip_frames - dur_frames)  # Start 25% in to skip intros
        start = max(0, start)
        end = min(start + dur_frames, clip_frames)
        
        mp.AppendToTimeline([{
            "mediaPoolItem": clip,
            "startFrame": start,
            "endFrame": end
        }])
        placed += 1

print(f"\nPlaced {placed} video segments")
print(f"Timeline duration: {tl.GetEndFrame() / fps:.1f}s")
print("\nDone! Check the Edit page timeline.")
