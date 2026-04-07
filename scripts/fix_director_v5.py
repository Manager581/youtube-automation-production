#!/usr/bin/env python3
"""Apply all director post-processing fixes to existing v5 output.
Runs validate_decisions() with the new hardening on the saved JSON."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter, defaultdict

DIRECTOR_PATH = "storyboards/breaking_law_directed_v6.json"
INTRO_PATH = "storyboards/intro_spec_locked.json"

# All known asset files
CLIP_DIR = "footage/breaking_law/clips"
IMAGE_DIRS = [f"footage/breaking_law/images/seg_{i:03d}" for i in range(30)] + ["footage/breaking_law/gap_fills/images"]
SFX_DIR = "assets/sfx"

VALID_CHAPTERS = {"THE FORMULA", "THE DATA", "THE MACHINES", "THE RENT", "THE RECKONING"}

def discover_files():
    clips = set()
    images = set()
    sfx = set()
    for f in os.listdir(CLIP_DIR):
        if f.endswith('.mp4'): clips.add(f)
    for d in IMAGE_DIRS:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.lower().endswith(('.jpg', '.jpeg', '.png')): images.add(f)
    if os.path.exists(SFX_DIR):
        for f in os.listdir(SFX_DIR):
            if f.endswith('.wav'): sfx.add(f)
    return clips, images, sfx

def main():
    with open(DIRECTOR_PATH) as f:
        data = json.load(f)

    # Flatten segments
    all_segs = []
    for scene in data["scenes"]:
        all_segs.extend(scene["segments"])

    print(f"Loaded {len(all_segs)} segments")
    clips, images, sfx_files = discover_files()
    all_files = clips | images
    print(f"Assets: {len(clips)} clips, {len(images)} images, {len(sfx_files)} SFX")

    fixed = 0

    # === Fix 1: Strip invented chapter cards ===
    seen_chapters = set()
    for seg in all_segs:
        cc = seg.get("chapter_card")
        if cc:
            if cc not in VALID_CHAPTERS:
                print(f"  Strip invented chapter: '{cc}' on seg with text: {seg['text'][:50]}")
                seg["chapter_card"] = None
                fixed += 1
            elif cc in seen_chapters:
                print(f"  Strip duplicate chapter: '{cc}'")
                seg["chapter_card"] = None
                fixed += 1
            else:
                seen_chapters.add(cc)

    # === Fix 2: Cap visual reuse at 2 ===
    usage = Counter()
    # Count all visuals (segment-level + beats)
    for seg in all_segs:
        vf = seg.get("visual_file", "")
        if vf: usage[vf] += 1
        for beat in (seg.get("beats") or []):
            bvf = beat.get("visual_file", "")
            if bvf: usage[bvf] += 1

    overused = {f: c for f, c in usage.items() if c > 2}
    if overused:
        print(f"\n  {len(overused)} visuals over cap. Fixing beats...")
        # Build alternatives sorted by usage
        all_images_list = sorted(images, key=lambda f: usage.get(f, 0))
        all_clips_list = sorted(clips, key=lambda f: usage.get(f, 0))

        # Reset counter and re-assign
        usage2 = Counter()
        for seg in all_segs:
            for beat in (seg.get("beats") or []):
                bvf = beat.get("visual_file", "")
                if not bvf: continue
                usage2[bvf] += 1
                if usage2[bvf] > 2:
                    # Find alternative
                    is_clip = bvf.endswith('.mp4')
                    pool = all_clips_list if is_clip else all_images_list
                    replacement = None
                    for alt in pool:
                        if usage2.get(alt, 0) < 2:
                            replacement = alt
                            break
                    if replacement:
                        beat["visual_file"] = replacement
                        usage2[replacement] = usage2.get(replacement, 0) + 1
                        fixed += 1
            # Also check segment-level
            vf = seg.get("visual_file", "")
            if vf:
                usage2[vf] = usage2.get(vf, 0) + 1
                if usage2[vf] > 2:
                    is_clip = vf.endswith('.mp4')
                    pool = all_clips_list if is_clip else all_images_list
                    for alt in pool:
                        if usage2.get(alt, 0) < 2:
                            seg["visual_file"] = alt
                            usage2[alt] = usage2.get(alt, 0) + 1
                            fixed += 1
                            break

    # === Fix 3: Cap SFX at 2 per chapter ===
    current_chapter = "COLD OPEN"
    sfx_by_chapter = defaultdict(list)
    for i, seg in enumerate(all_segs):
        cc = seg.get("chapter_card")
        if cc: current_chapter = cc
        sfx = seg.get("sfx")
        if sfx:
            tension = seg.get("tension_level", 0.5)
            sfx_by_chapter[current_chapter].append((i, tension))

    for chapter, sfx_list in sfx_by_chapter.items():
        if len(sfx_list) > 2:
            sfx_list.sort(key=lambda x: -x[1])  # keep highest tension
            for idx, _ in sfx_list[2:]:
                all_segs[idx]["sfx"] = None
                fixed += 1
            print(f"  Capped SFX in '{chapter}': kept 2, removed {len(sfx_list)-2}")

    # === Fix 4: Fix timestamp regression (seg with start < previous end) ===
    for i in range(1, len(all_segs)):
        prev_end = all_segs[i-1].get("_timeline_end_sec", 0)
        curr_start = all_segs[i].get("_timeline_start_sec", 0)
        if curr_start < prev_end - 1 and curr_start < 10:
            # This segment has a near-zero junk timestamp — fix it
            all_segs[i]["_timeline_start_sec"] = prev_end
            all_segs[i]["_timeline_end_sec"] = prev_end + max(
                all_segs[i].get("_timeline_end_sec", 1) - curr_start, 1.0)
            fixed += 1
            print(f"  Fixed timestamp regression at seg {i}: {curr_start:.1f}s -> {prev_end:.1f}s")

    # === Reconstruct scenes from modified segments ===
    seg_idx = 0
    for scene in data["scenes"]:
        scene_segs = scene["segments"]
        for j in range(len(scene_segs)):
            scene_segs[j] = all_segs[seg_idx]
            seg_idx += 1

    # === Re-apply locked intro ===
    with open(INTRO_PATH) as f:
        intro = json.load(f)

    first_segs = []
    for scene in data["scenes"]:
        first_segs.extend(scene["segments"])

    for i, locked in enumerate(intro["segments"]):
        if i >= len(first_segs): break
        seg = first_segs[i]
        seg["visual_file"] = locked["visual_file"]
        seg["visual_type"] = locked["visual_type"]
        seg["clip_audio"] = locked["clip_audio"]
        seg["clip_audio_duration"] = locked.get("clip_audio_duration", 0)
        seg["transition_in"] = locked["transition_in"]
        seg["music_state"] = locked["music_state"]
        if locked.get("sfx"):
            seg["sfx"] = {"file": locked["sfx"], "motivation": "locked intro", "type": "accent"}
        elif locked.get("sfx") is None:
            seg["sfx"] = None

    # Save
    with open(DIRECTOR_PATH, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nTotal fixes: {fixed}")
    print(f"Saved to {DIRECTOR_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
