#!/usr/bin/env python3
"""Apply the locked intro spec to director v5 output.

Replaces the first 3 segments' director decisions with the user-approved
intro from storyboards/intro_spec_locked.json. Preserves beats/timing
from v5 but overrides visual_file, clip_audio, transitions, etc.
"""
import json
import sys

DIRECTOR_PATH = "storyboards/breaking_law_directed_v5.json"
INTRO_PATH = "storyboards/intro_spec_locked.json"

def main():
    with open(DIRECTOR_PATH) as f:
        director = json.load(f)
    with open(INTRO_PATH) as f:
        intro = json.load(f)

    locked_segs = intro["segments"]
    print(f"Locked intro: {len(locked_segs)} segments")

    # Navigate to the flat segment list inside scenes
    all_segs = []
    for scene in director.get("scenes", []):
        all_segs.extend(scene.get("segments", []))

    if len(all_segs) < len(locked_segs):
        print(f"ERROR: Director has {len(all_segs)} segments but intro needs {len(locked_segs)}")
        return 1

    # Apply locked intro overrides
    for i, locked in enumerate(locked_segs):
        seg = all_segs[i]
        seg["visual_file"] = locked["visual_file"]
        seg["visual_type"] = locked["visual_type"]
        seg["clip_audio"] = locked["clip_audio"]
        seg["clip_audio_duration"] = locked.get("clip_audio_duration", 0)
        seg["transition_in"] = locked["transition_in"]
        seg["music_state"] = locked["music_state"]
        # Clear beats for intro segments — they have specific locked visuals
        if locked.get("visual_file"):
            seg["beats"] = None
        if locked.get("sfx"):
            seg["sfx"] = {"file": locked["sfx"], "motivation": "locked intro", "type": "accent"}
        elif locked.get("sfx") is None and "sfx" not in locked:
            pass  # keep director's sfx
        else:
            seg["sfx"] = None

        print(f"  Seg {i}: {locked['visual_file']} ({locked['clip_audio']})")

    # Write back — reconstruct scenes from modified segments
    seg_idx = 0
    for scene in director["scenes"]:
        scene_segs = scene["segments"]
        for j in range(len(scene_segs)):
            scene_segs[j] = all_segs[seg_idx]
            seg_idx += 1

    with open(DIRECTOR_PATH, 'w') as f:
        json.dump(director, f, indent=2)

    print(f"\nSaved with locked intro to {DIRECTOR_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
