resolve = app.GetResolve()
project = resolve.GetProjectManager().GetCurrentProject()
tl = project.GetCurrentTimeline()
fps = int(tl.GetSetting("timelineFrameRate") or 30)
sf = tl.GetStartFrame()

print(f"Timeline: {tl.GetName()}")
print(f"Duration: {(tl.GetEndFrame()-sf)/fps:.1f}s ({(tl.GetEndFrame()-sf)/fps/60:.1f}min)")
print(f"V1 items: {len(tl.GetItemListInTrack('video', 1) or [])}")
print(f"A1 items: {len(tl.GetItemListInTrack('audio', 1) or [])}")
print(f"A2 items: {len(tl.GetItemListInTrack('audio', 2) or [])}")

# List first 10 and last 5 V1 clips with names and positions
v1 = tl.GetItemListInTrack("video", 1) or []
print(f"\nFirst 10 V1 clips:")
for item in v1[:10]:
    s = (item.GetStart() - sf) / fps
    e = (item.GetEnd() - sf) / fps
    print(f"  {s:7.1f}s - {e:7.1f}s ({e-s:.1f}s)  {item.GetName()[:60]}")

print(f"\nLast 5 V1 clips:")
for item in v1[-5:]:
    s = (item.GetStart() - sf) / fps
    e = (item.GetEnd() - sf) / fps
    print(f"  {s:7.1f}s - {e:7.1f}s ({e-s:.1f}s)  {item.GetName()[:60]}")

# Also list A1 clips around key time positions
a1 = tl.GetItemListInTrack("audio", 1) or []
print(f"\nFirst 5 A1 clips:")
for item in a1[:5]:
    s = (item.GetStart() - sf) / fps
    e = (item.GetEnd() - sf) / fps
    print(f"  {s:7.1f}s - {e:7.1f}s ({e-s:.1f}s)  {item.GetName()[:60]}")

# Find clips from key sources at various positions
print(f"\nSearching for source clips...")
for keyword in ["data_brokers", "john_oliver", "jacksonville", "lawsuit", 
                 "uber", "cigna", "exposing", "algorithms", "deny_health"]:
    matches = []
    for item in v1:
        name = item.GetName().lower().replace(" ", "_")
        if keyword in name:
            s = (item.GetStart() - sf) / fps
            matches.append(f"{s:.0f}s")
    if matches:
        print(f"  '{keyword}': found at {', '.join(matches[:5])}{'...' if len(matches)>5 else ''} ({len(matches)} total)")

print("\nDone!")
