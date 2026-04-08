#!/usr/bin/env python3
"""
Build a 60-second integration test FCPXML using real breaking_law assets.

Exercises ALL 10 features the pipeline produces:
  1. Muted video clip (-96dB) on V1
  2. Play video clip (full audio) on V1
  3. Play_then_mute clip (volume keyframes: 0dB→-96dB) on V1
  4. Still image with Ken Burns zoom on V1
  5. Cross Dissolve transition between two V1 clips
  6. Narration excerpt on A1 (lane clip)
  7. Music track on A2 (lane clip)
  8. SFX on A3 and A4 (lane clips)
  9. Overlay MOV on V2 (lane clip)
  10. Chapter card MOV on V3 (lane clip)

Uses fcpxml_builder_v2 helper functions (to_rational, to_dur, file_url)
and the same lane offset math to test actual code paths.

Usage:
  python -m pipeline_v2.build_test_fcpxml
  python -m pipeline_v2.build_test_fcpxml --output test_custom.fcpxml
  python -m pipeline_v2.build_test_fcpxml --verify  # also runs verify_fcpxml
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline_v2.fcpxml_builder_v2 import (
    to_rational, to_dur, file_url, get_duration, is_image, is_video, is_audio,
    FPS, TC_START, WIDTH, HEIGHT,
    LANE_OVERLAY, LANE_CHAPTER, LANE_NARRATION, LANE_MUSIC, LANE_SFX1, LANE_SFX2,
)

PROJECT_ROOT = Path(__file__).parent.parent

# ── Real assets from breaking_law ──
CLIP_1 = PROJECT_ROOT / "footage" / "breaking_law" / "clips" / "Facebook_to_pay_5_billion_fine.mp4"
CLIP_2 = PROJECT_ROOT / "footage" / "breaking_law" / "clips" / "Department_of_Justice_building.mp4"
IMAGE_1 = PROJECT_ROOT / "footage" / "breaking_law" / "images" / "seg_000" / "pexels_5668473_GDPR_European_data_protection_.jpg"
NARRATION = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
MUSIC = PROJECT_ROOT / "audio" / "breaking_law" / "music_tracks" / "track_01_tense_ducked.wav"
OVERLAY_1 = PROJECT_ROOT / "assets" / "breaking_law" / "overlays" / "tw_000_5_billion.mov"
CHAPTER_CARD = PROJECT_ROOT / "assets" / "breaking_law" / "chapters" / "chapter_the_formula.mov"

DEFAULT_OUTPUT = PROJECT_ROOT / "test_integration.fcpxml"


def find_sfx():
    """Find two SFX files."""
    sfx_dir = PROJECT_ROOT / "assets" / "sfx"
    sfx_files = []
    for f in sorted(sfx_dir.iterdir()):
        if f.suffix in ('.wav', '.mp3') and f.stat().st_size > 100:
            sfx_files.append(f)
            if len(sfx_files) >= 2:
                break
    return sfx_files


def check_assets():
    """Verify all required assets exist."""
    required = {
        "Video clip 1": CLIP_1,
        "Video clip 2": CLIP_2,
        "Image": IMAGE_1,
        "Narration": NARRATION,
        "Music": MUSIC,
        "Overlay": OVERLAY_1,
        "Chapter card": CHAPTER_CARD,
    }
    missing = []
    for name, path in required.items():
        if not path.exists():
            missing.append(f"  {name}: {path}")

    sfx = find_sfx()
    if len(sfx) < 2:
        missing.append(f"  SFX: need 2 files in assets/sfx/, found {len(sfx)}")

    if missing:
        print("Missing assets:")
        for m in missing:
            print(m)
        return False
    return True


def build_test_fcpxml(output_path):
    """Build a 60-second test FCPXML exercising all features."""

    if not check_assets():
        print("\nCannot build test FCPXML — missing assets.")
        sys.exit(1)

    sfx = find_sfx()
    main_fmt_id = "r0"
    asset_counter = [1]  # mutable counter for asset IDs
    registered = {}  # path -> (asset_id, fmt_id)

    def register_asset(filepath):
        abspath = os.path.abspath(str(filepath))
        if abspath in registered:
            return registered[abspath]
        aid = f"r{asset_counter[0]}"
        asset_counter[0] += 1
        fid = f"r{asset_counter[0]}"
        asset_counter[0] += 1
        registered[abspath] = (aid, fid)
        return aid, fid

    # Pre-register all assets
    for f in [CLIP_1, CLIP_2, IMAGE_1, NARRATION, MUSIC, OVERLAY_1, CHAPTER_CARD] + sfx:
        register_asset(f)

    # ── Build XML ──
    root = Element("fcpxml", version="1.9")

    # Resources
    resources = SubElement(root, "resources")
    SubElement(resources, "format", {
        "id": main_fmt_id,
        "name": f"FFVideoFormat{HEIGHT}p{FPS}",
        "frameDuration": f"1/{FPS}s",
        "width": str(WIDTH),
        "height": str(HEIGHT),
    })

    for abspath, (aid, fid) in registered.items():
        SubElement(resources, "format", {
            "id": fid,
            "name": "FFVideoFormatRateUndefined",
            "width": str(WIDTH),
            "height": str(HEIGHT),
        })

        attrs = {
            "id": aid,
            "name": os.path.basename(abspath),
            "start": "0/1s",
            "format": fid,
        }

        if is_image(abspath):
            attrs["hasVideo"] = "1"
            attrs["duration"] = "0/1s"
        elif is_video(abspath):
            dur = get_duration(abspath)
            attrs["hasVideo"] = "1"
            attrs["hasAudio"] = "1"
            attrs["audioSources"] = "1"
            attrs["audioChannels"] = "2"
            attrs["duration"] = to_rational(dur) if dur else "0/1s"
        elif is_audio(abspath):
            dur = get_duration(abspath)
            attrs["hasAudio"] = "1"
            attrs["audioSources"] = "1"
            attrs["audioChannels"] = "1"
            attrs["duration"] = to_rational(dur) if dur else "0/1s"

        asset_el = SubElement(resources, "asset", attrs)
        SubElement(asset_el, "media-rep", {
            "kind": "original-media",
            "src": file_url(abspath),
        })

    # Library / Event / Project / Sequence
    total_dur = 65.0  # 60s + 5s trailing
    library = SubElement(root, "library")
    event = SubElement(library, "event", name="Integration Test")
    project = SubElement(event, "project", name="Test Features Timeline")
    sequence = SubElement(project, "sequence", {
        "format": main_fmt_id,
        "duration": to_rational(total_dur),
        "tcStart": to_rational(TC_START),
        "tcFormat": "NDF",
    })
    spine = SubElement(sequence, "spine")

    # ── V1 Spine clips (60s total) ──
    cursor = 0.0

    # Feature 1: MUTED video clip (0-10s)
    clip1_aid, _ = registered[os.path.abspath(str(CLIP_1))]
    el = SubElement(spine, "clip", {
        "name": "Facebook_fine_MUTED",
        "offset": to_rational(TC_START + cursor),
        "duration": to_dur(10.0),
        "start": "0/1s",
        "tcFormat": "NDF",
    })
    SubElement(el, "video", {
        "ref": clip1_aid,
        "offset": "0/1s",
        "duration": to_rational(get_duration(str(CLIP_1)) or 60),
        "start": "0/1s",
    })
    SubElement(el, "adjust-volume", amount="-96dB")
    cursor += 10.0

    # Feature 5: Cross Dissolve transition (between clip 1 and clip 2)
    trans_dur = 1.0
    SubElement(spine, "transition", {
        "name": "Cross Dissolve",
        "offset": to_rational(TC_START + cursor - trans_dur / 2),
        "duration": to_dur(trans_dur),
    })

    # Feature 2: PLAY video clip with audio (10-20s)
    clip2_aid, _ = registered[os.path.abspath(str(CLIP_2))]
    el = SubElement(spine, "clip", {
        "name": "DOJ_building_PLAY",
        "offset": to_rational(TC_START + cursor),
        "duration": to_dur(10.0),
        "start": "0/1s",
        "tcFormat": "NDF",
    })
    SubElement(el, "video", {
        "ref": clip2_aid,
        "offset": "0/1s",
        "duration": to_rational(get_duration(str(CLIP_2)) or 60),
        "start": "0/1s",
    })
    # No adjust-volume = full audio
    cursor += 10.0

    # Feature 3: PLAY_THEN_MUTE clip with volume keyframes (20-30s)
    el = SubElement(spine, "clip", {
        "name": "Facebook_fine_PLAY_THEN_MUTE",
        "offset": to_rational(TC_START + cursor),
        "duration": to_dur(10.0),
        "start": to_rational(10),  # different start point in source
        "tcFormat": "NDF",
    })
    SubElement(el, "video", {
        "ref": clip1_aid,
        "offset": "0/1s",
        "duration": to_rational(get_duration(str(CLIP_1)) or 60),
        "start": "0/1s",
    })
    vol = SubElement(el, "adjust-volume")
    param = SubElement(vol, "param", name="amount")
    SubElement(param, "keyframe", time="0/1s", value="0dB")
    SubElement(param, "keyframe", time=to_rational(3), value="0dB")
    SubElement(param, "keyframe", time=to_rational(3.5), value="-96dB")
    SubElement(param, "keyframe", time=to_dur(10.0), value="-96dB")
    cursor += 10.0

    # Feature 4: Still image with Ken Burns zoom (30-45s)
    img_aid, _ = registered[os.path.abspath(str(IMAGE_1))]
    el = SubElement(spine, "video", {
        "ref": img_aid,
        "name": "GDPR_image_KEN_BURNS",
        "offset": to_rational(TC_START + cursor),
        "duration": to_dur(15.0),
        "start": "0/1s",
    })
    xform = SubElement(el, "adjust-transform")
    SubElement(xform, "param", name="position", value="0 0")
    SubElement(xform, "param", name="anchor", value="0 0")
    scale_param = SubElement(xform, "param", name="scale")
    SubElement(scale_param, "keyframe", time="0/1s", value="1.0 1.0")
    SubElement(scale_param, "keyframe", time=to_dur(15.0), value="1.05 1.05")
    cursor += 15.0

    # Feature 1 again: Another muted clip (45-60s)
    el = SubElement(spine, "clip", {
        "name": "DOJ_building_MUTED",
        "offset": to_rational(TC_START + cursor),
        "duration": to_dur(15.0),
        "start": to_rational(5),
        "tcFormat": "NDF",
    })
    SubElement(el, "video", {
        "ref": clip2_aid,
        "offset": "0/1s",
        "duration": to_rational(get_duration(str(CLIP_2)) or 60),
        "start": "0/1s",
    })
    SubElement(el, "adjust-volume", amount="-96dB")
    cursor += 15.0

    # Trailing gap
    trailing_dur = max(total_dur - cursor, 5.0)
    gap = SubElement(spine, "gap", {
        "name": "Gap",
        "offset": to_rational(TC_START + cursor),
        "duration": to_dur(trailing_dur),
        "start": to_rational(TC_START + cursor),
    })

    # ── Lane clips (attached to FIRST spine element) ──
    # This matches the builder's approach: all lane clips on first spine el
    first_spine_el = list(spine)[0]
    first_start_str = first_spine_el.get("start", "0/1s").rstrip('s')
    if '/' in first_start_str:
        _n, _d = first_start_str.split('/')
        first_content_start = float(_n) / float(_d)
    else:
        first_content_start = float(first_start_str)

    def add_lane_clip(lane, offset, duration, filepath, start=0, name=None, is_audio_clip=False):
        """Add a lane clip to the first spine element."""
        abspath = os.path.abspath(str(filepath))
        aid, _ = registered.get(abspath, (None, None))
        if not aid:
            print(f"  WARNING: asset not registered for {filepath}")
            return

        lane_offset = first_content_start + offset

        attrs = {
            "ref": aid,
            "name": name or os.path.basename(str(filepath)),
            "lane": str(lane),
            "offset": to_rational(lane_offset),
            "duration": to_dur(duration),
            "start": to_rational(start),
        }

        if is_audio_clip:
            attrs["role"] = "dialogue"
            SubElement(first_spine_el, "asset-clip", attrs)
        else:
            vid = SubElement(first_spine_el, "video", attrs)
            if lane == LANE_OVERLAY:
                SubElement(vid, "adjust-transform", {
                    "position": "0 0",
                    "scale": "1 1",
                    "anchor": "0 0",
                })

    # Feature 6: Narration on A1 (first 60s of narration)
    narr_dur = min(get_duration(str(NARRATION)) or 60, 60.0)
    add_lane_clip(LANE_NARRATION, 0, narr_dur, NARRATION, is_audio_clip=True, name="narration.wav")

    # Feature 7: Music on A2 (30s starting at 15s)
    music_dur = min(get_duration(str(MUSIC)) or 30, 30.0)
    add_lane_clip(LANE_MUSIC, 15.0, music_dur, MUSIC, is_audio_clip=True)

    # Feature 8: SFX on A3 at 5s and A4 at 25s
    sfx1_dur = get_duration(str(sfx[0])) or 2.0
    sfx2_dur = get_duration(str(sfx[1])) or 2.0
    add_lane_clip(LANE_SFX1, 5.0, sfx1_dur, sfx[0], is_audio_clip=True)
    add_lane_clip(LANE_SFX2, 25.0, sfx2_dur, sfx[1], is_audio_clip=True)

    # Feature 9: Overlay on V2 at 10s
    ov_dur = get_duration(str(OVERLAY_1)) or 3.0
    add_lane_clip(LANE_OVERLAY, 10.0, ov_dur, OVERLAY_1)

    # Feature 10: Chapter card on V3 at 30s
    card_dur = get_duration(str(CHAPTER_CARD)) or 3.0
    add_lane_clip(LANE_CHAPTER, 30.0, min(card_dur, 4.0), CHAPTER_CARD)

    # Pretty print and write
    indent(root, space="  ")
    tree = ElementTree(root)
    tree.write(str(output_path), xml_declaration=True, encoding="UTF-8")

    # Add DOCTYPE after XML declaration
    with open(output_path, 'r') as f:
        content = f.read()
    content = content.replace(
        "<?xml version='1.0' encoding='UTF-8'?>",
        "<?xml version='1.0' encoding='UTF-8'?>\n<!DOCTYPE fcpxml>"
    )
    with open(output_path, 'w') as f:
        f.write(content)

    print(f"\nTest FCPXML written: {output_path}")
    print(f"  V1: 5 spine clips + 1 transition + trailing gap")
    print(f"  V2: 1 overlay")
    print(f"  V3: 1 chapter card")
    print(f"  A1: narration ({narr_dur:.1f}s)")
    print(f"  A2: music ({music_dur:.1f}s)")
    print(f"  A3: SFX at 5s")
    print(f"  A4: SFX at 25s")
    print(f"  Total: ~60s timeline")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Build 60s integration test FCPXML")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT),
                        help="Output FCPXML path")
    parser.add_argument("--verify", action="store_true",
                        help="Run verify_fcpxml after building")
    args = parser.parse_args()

    output_path = Path(args.output)
    fcpxml_path = build_test_fcpxml(output_path)

    if args.verify:
        print(f"\n{'='*60}")
        print("Running verification...")
        print(f"{'='*60}\n")
        rc = subprocess.run(
            [sys.executable, "-m", "pipeline_v2.verify_fcpxml",
             "--fcpxml", fcpxml_path,
             "--min-v1-clips", "3",
             "--narration-duration", "60"],
            cwd=str(PROJECT_ROOT)
        ).returncode
        if rc == 0:
            print("\nIntegration test PASSED")
        else:
            print("\nIntegration test FAILED")
        sys.exit(rc)


if __name__ == "__main__":
    main()
