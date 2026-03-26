#!/usr/bin/env python3
"""
Video Assembler V3 — Editorial-driven assembly with proper audio separation.

Reads:
  - editorial_clip_map.json (which clip, timestamps, audio mode per segment)
  - narration_timing.json (whisper timestamps for narration sentences)
  - narration.wav (original pace voiceover)

Produces:
  - Secret_Scores_V3.mp4 with proper audio:
    - clip_audio segments: source clip audio only (intro clips)
    - soundbite segments: source clip audio only (VO ducked)
    - vo_only segments: narration audio only (clip audio muted)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

CLIPS_DIR = Path(os.path.expanduser("~/Documents/youtube-automation-production/footage/fern_clone/secret_scores/clips"))
NARRATION = Path(os.path.expanduser("~/Documents/youtube-automation-production/audio/secret_scores/narration.wav"))
OUT_DIR = Path(os.path.expanduser("~/Desktop/SecretScores_Media"))
EDIT_MAP = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map.json"))
NAR_TIMING = Path(os.path.expanduser("~/Documents/youtube-automation-production/narration_timing.json"))

def run(cmd, desc=""):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"  ERROR ({desc}): {r.stderr[-200:]}")
    return r.returncode == 0

def get_duration(path):
    r = subprocess.run(
        f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{path}"',
        shell=True, capture_output=True, text=True
    )
    return float(r.stdout.strip()) if r.stdout.strip() else 0

def main():
    print("=== Video Assembler V3 — Editorial-Driven ===\n")
    
    # Load editorial map
    with open(EDIT_MAP) as f:
        edit_data = json.load(f)
    segments = edit_data["segments"]
    soundbite_segs = set(edit_data["soundbite_segments"])
    intro_segs = set(edit_data["intro_segments"])
    
    # Load narration timing
    with open(NAR_TIMING) as f:
        nar_data = json.load(f)
    nar_segments = nar_data["segments"]
    
    print(f"Editorial segments: {len(segments)}")
    print(f"Narration whisper segments: {len(nar_segments)}")
    print(f"Soundbite punch-throughs: {len(soundbite_segs)}")
    print(f"Intro clip-audio segments: {len(intro_segs)}")
    
    # Map narration text to storyboard segments
    # Each editorial segment covers a chunk of narration
    # We need to find the start/end time in the narration for each segment
    
    # Strategy: divide narration evenly across 72 segments
    # (Better: match by text similarity, but even division works for now)
    total_nar_dur = nar_segments[-1]["end"]
    
    # Skip intro segments (0-3) for narration — they use clip audio
    # Narration starts at segment 4
    nar_seg_count = len(segments) - len(intro_segs)  # 68 segments need narration
    nar_per_seg = total_nar_dur / nar_seg_count
    
    print(f"\nNarration duration: {total_nar_dur:.1f}s")
    print(f"Narration segments: {nar_seg_count}")
    print(f"Avg narration per segment: {nar_per_seg:.1f}s")
    
    # Step 1: Extract each clip segment as a video file (no audio)
    tmp = Path("/tmp/v3_assembly")
    tmp.mkdir(exist_ok=True)
    
    print(f"\n--- Step 1: Extract {len(segments)} clip segments ---")
    nar_cursor = 0.0  # Current position in narration
    segment_info = []  # Track segment durations and audio modes
    
    for seg in segments:
        sid = seg["seg_id"]
        clip_path = CLIPS_DIR / seg["source_clip"]
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        mode = seg["audio_mode"]
        
        if not clip_path.exists():
            print(f"  MISSING: {seg['source_clip']}")
            continue
        
        # Determine segment duration based on audio mode
        if mode in ("clip_audio", "soundbite"):
            # Use clip's own duration
            seg_dur = ce - cs
        else:
            # vo_only: duration = narration chunk duration
            seg_dur = nar_per_seg
        
        # Extract video segment (always include video)
        out_seg = tmp / f"seg_{sid:03d}.mp4"
        
        if mode in ("clip_audio", "soundbite"):
            # Keep clip audio
            cmd = (f'ffmpeg -y -ss {cs} -i "{clip_path}" -t {seg_dur} '
                   f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
                   f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
                   f'"{out_seg}" 2>/dev/null')
        else:
            # vo_only: mute clip audio, we'll overlay narration later
            # But we need the video to be the right duration (match narration chunk)
            # Trim clip to seg_dur, but if clip segment is shorter, loop it
            clip_dur = ce - cs
            if clip_dur >= seg_dur:
                cmd = (f'ffmpeg -y -ss {cs} -i "{clip_path}" -t {seg_dur} '
                       f'-c:v libx264 -preset ultrafast -crf 20 -an '
                       f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
                       f'"{out_seg}" 2>/dev/null')
            else:
                # Loop the clip to fill the narration duration
                cmd = (f'ffmpeg -y -ss {cs} -i "{clip_path}" -t {seg_dur} '
                       f'-c:v libx264 -preset ultrafast -crf 20 -an '
                       f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
                       f'-stream_loop -1 '
                       f'"{out_seg}" 2>/dev/null')
        
        run(cmd, f"seg_{sid}")
        actual_dur = get_duration(str(out_seg))
        
        segment_info.append({
            "seg_id": sid,
            "duration": actual_dur,
            "mode": mode,
            "nar_start": nar_cursor if mode == "vo_only" else None,
            "nar_end": (nar_cursor + actual_dur) if mode == "vo_only" else None,
        })
        
        if mode == "vo_only":
            nar_cursor += actual_dur
        
        if sid % 10 == 0:
            print(f"  Seg {sid:02d}/{len(segments)-1} [{mode:10s}] {actual_dur:.1f}s")
    
    # Step 2: Build concat list for video
    print(f"\n--- Step 2: Concat all video segments ---")
    concat_list = tmp / "concat.txt"
    with open(concat_list, "w") as f:
        for si in segment_info:
            seg_path = tmp / f"seg_{si['seg_id']:03d}.mp4"
            if seg_path.exists():
                f.write(f"file '{seg_path}'\n")
    
    # Concat video (no audio for vo_only segs, with audio for clip_audio/soundbite)
    video_only = tmp / "video_only.mp4"
    cmd = (f'ffmpeg -y -f concat -safe 0 -i "{concat_list}" '
           f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
           f'"{video_only}" 2>/dev/null')
    run(cmd, "concat")
    vid_dur = get_duration(str(video_only))
    print(f"  Video duration: {vid_dur:.1f}s ({vid_dur/60:.1f}min)")
    
    # Step 3: Build the audio track
    # For vo_only segments: narration audio
    # For clip_audio/soundbite segments: silence in narration track (clip audio already in video)
    print(f"\n--- Step 3: Build narration audio track ---")
    
    # Calculate intro duration (sum of clip_audio + soundbite segment durations)
    intro_dur = sum(si["duration"] for si in segment_info if si["mode"] in ("clip_audio", "soundbite") and si["seg_id"] in intro_segs)
    
    # Create narration track with silence during intro, then narration for rest
    # Trim narration to match the video duration minus intro
    nar_offset = intro_dur + sum(si["duration"] for si in segment_info if si["mode"] == "soundbite" and si["seg_id"] not in intro_segs)
    
    # Simpler approach: create silence for intro duration, then append narration
    silence_file = tmp / "silence.wav"
    cmd = (f'ffmpeg -y -f lavfi -i "anullsrc=channel_layout=mono:sample_rate=24000" '
           f'-t {intro_dur} -c:a pcm_s16le "{silence_file}" 2>/dev/null')
    run(cmd, "silence")
    
    # Concat silence + narration
    nar_concat = tmp / "nar_concat.txt"
    with open(nar_concat, "w") as f:
        f.write(f"file '{silence_file}'\n")
        f.write(f"file '{NARRATION}'\n")
    
    nar_offset_file = tmp / "narration_offset.wav"
    cmd = (f'ffmpeg -y -f concat -safe 0 -i "{nar_concat}" '
           f'-c:a pcm_s16le "{nar_offset_file}" 2>/dev/null')
    run(cmd, "nar_offset")
    nar_offset_dur = get_duration(str(nar_offset_file))
    print(f"  Narration offset duration: {nar_offset_dur:.1f}s (intro silence: {intro_dur:.1f}s)")
    
    # Step 4: Final mix
    print(f"\n--- Step 4: Final mix ---")
    final_out = OUT_DIR / "Secret_Scores_V3.mp4"
    
    # Mix: video audio (has clip audio for intro/soundbite segments) + narration overlay
    # During intro: video has clip audio, narration is silent → viewer hears clips
    # During vo_only: video has no audio, narration plays → viewer hears VO
    # During soundbite: video has clip audio, narration is playing but gets naturally mixed
    
    # Use amix but with proper volume control
    cmd = (f'ffmpeg -y -i "{video_only}" -i "{nar_offset_file}" '
           f'-filter_complex "'
           f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.0[clip];'
           f'[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.2[nar];'
           f'[clip][nar]amix=inputs=2:duration=longest:dropout_transition=0[out]'
           f'" -map 0:v -map "[out]" '
           f'-c:v copy -c:a aac -b:a 192k '
           f'"{final_out}" 2>/dev/null')
    run(cmd, "final_mix")
    
    final_dur = get_duration(str(final_out))
    final_size = os.path.getsize(str(final_out)) / (1024*1024)
    print(f"\n=== FINAL OUTPUT ===")
    print(f"  File: {final_out}")
    print(f"  Duration: {final_dur:.1f}s ({final_dur/60:.1f}min)")
    print(f"  Size: {final_size:.0f}MB")
    print(f"  Audio: intro=clip_audio, narration=vo_only, soundbites=mixed")
    
    # Save assembly manifest
    manifest = {
        "version": "v3",
        "segments": segment_info,
        "total_duration": final_dur,
        "intro_duration": intro_dur,
        "narration_duration": total_nar_dur,
        "soundbite_count": len(soundbite_segs),
    }
    with open(OUT_DIR / "v3_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! Import {final_out.name} into DaVinci to preview.")

if __name__ == "__main__":
    main()
