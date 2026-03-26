#!/usr/bin/env python3
"""
Assembler V3b — Use clip durations naturally, overlay continuous narration.

Instead of forcing each clip to match narration timing:
1. Extract each clip at its editorial-specified timestamps (natural duration)
2. Concat all clips into a continuous video
3. Overlay narration starting after intro, as one continuous track
4. Intro segments keep their own audio
5. During soundbite segments, the clip audio punches through
"""
import json, os, subprocess
from pathlib import Path

CLIPS_DIR = Path(os.path.expanduser("~/Documents/youtube-automation-production/footage/fern_clone/secret_scores/clips"))
NARRATION = Path(os.path.expanduser("~/Documents/youtube-automation-production/audio/secret_scores/narration.wav"))
OUT_DIR = Path(os.path.expanduser("~/Desktop/SecretScores_Media"))
EDIT_MAP = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map.json"))

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)

def dur(path):
    r = run(f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{path}"')
    return float(r.stdout.strip()) if r.stdout.strip() else 0

def main():
    print("=== Assembler V3b — Natural clip durations + narration overlay ===\n")
    
    with open(EDIT_MAP) as f:
        data = json.load(f)
    segments = data["segments"]
    soundbites = set(data["soundbite_segments"])
    intros = set(data["intro_segments"])
    
    tmp = Path("/tmp/v3b")
    tmp.mkdir(exist_ok=True)
    
    # Step 1: Extract all clip segments at their natural duration
    print("--- Step 1: Extract clips ---")
    concat_lines = []
    intro_total = 0.0
    soundbite_times = []  # (start_in_timeline, duration) for soundbite segments
    timeline_cursor = 0.0
    
    for seg in segments:
        sid = seg["seg_id"]
        clip = CLIPS_DIR / seg["source_clip"]
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        mode = seg["audio_mode"]
        seg_dur = ce - cs
        
        out = tmp / f"s{sid:03d}.mp4"
        
        if mode in ("clip_audio", "soundbite"):
            # Keep source audio
            cmd = (f'ffmpeg -y -ss {cs} -i "{clip}" -t {seg_dur} '
                   f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
                   f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,'
                   f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
                   f'"{out}" 2>/dev/null')
        else:
            # vo_only: strip audio, add silent audio track for concat compatibility
            cmd = (f'ffmpeg -y -ss {cs} -i "{clip}" -t {seg_dur} '
                   f'-c:v libx264 -preset ultrafast -crf 20 '
                   f'-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 '
                   f'-map 0:v -map 1:a -shortest '
                   f'-c:a aac -b:a 192k '
                   f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,'
                   f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
                   f'"{out}" 2>/dev/null')
        
        r = run(cmd)
        actual = dur(str(out))
        
        if actual > 0:
            # Escape single quotes in path for ffmpeg concat
            escaped = str(out).replace("'", "'\\''")
            concat_lines.append(f"file '{escaped}'")
            
            if sid in intros:
                intro_total += actual
            if sid in soundbites and sid not in intros:
                soundbite_times.append((timeline_cursor, actual))
            
            timeline_cursor += actual
        
        if sid % 10 == 0:
            print(f"  {sid:02d}/{len(segments)-1} [{mode:10s}] {actual:.1f}s (total: {timeline_cursor:.1f}s)")
    
    print(f"\n  Total video: {timeline_cursor:.1f}s ({timeline_cursor/60:.1f}min)")
    print(f"  Intro: {intro_total:.1f}s")
    
    # Step 2: Concat all into one video
    print("\n--- Step 2: Concat ---")
    concat_file = tmp / "concat.txt"
    with open(concat_file, "w") as f:
        f.write("\n".join(concat_lines))
    
    video_all = tmp / "all.mp4"
    r = run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" -c copy "{video_all}" 2>&1')
    if r.returncode != 0:
        # If stream copy fails, re-encode
        print("  Stream copy failed, re-encoding...")
        run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
            f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
            f'"{video_all}" 2>/dev/null')
    
    vid_dur = dur(str(video_all))
    print(f"  Video: {vid_dur:.1f}s ({vid_dur/60:.1f}min)")
    
    # Step 3: Build narration track with silence for intro
    print("\n--- Step 3: Narration track ---")
    nar_dur_orig = dur(str(NARRATION))
    print(f"  Original narration: {nar_dur_orig:.1f}s")
    
    # Create silence matching intro duration (24kHz mono to match narration)
    silence = tmp / "silence.wav"
    run(f'ffmpeg -y -f lavfi -i "anullsrc=channel_layout=mono:sample_rate=24000" '
        f'-t {intro_total} -c:a pcm_s16le "{silence}" 2>/dev/null')
    
    # Concat: silence + narration
    nar_concat = tmp / "nar_cat.txt"
    with open(nar_concat, "w") as f:
        f.write(f"file '{silence}'\n")
        f.write(f"file '{NARRATION}'\n")
    
    nar_offset = tmp / "nar_offset.wav"
    run(f'ffmpeg -y -f concat -safe 0 -i "{nar_concat}" -c:a pcm_s16le "{nar_offset}" 2>/dev/null')
    nar_off_dur = dur(str(nar_offset))
    print(f"  Offset narration: {nar_off_dur:.1f}s (intro silence: {intro_total:.1f}s)")
    
    # Step 4: Final mix
    # Strategy: 
    # - Video has audio ONLY for clip_audio and soundbite segments (rest is silent)
    # - Narration track has silence during intro, then continuous VO
    # - Mix both: during intro viewer hears clips, during VO sections viewer hears narration
    # - During soundbites, both play (clip audio + narration - the soundbite clips are loud enough to dominate)
    print("\n--- Step 4: Final mix ---")
    final = OUT_DIR / "Secret_Scores_V3.mp4"
    
    # Use amix with the narration louder than clip audio
    r = run(f'ffmpeg -y -i "{video_all}" -i "{nar_offset}" '
            f'-filter_complex "'
            f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.8[clip];'
            f'[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.3[nar];'
            f'[clip][nar]amix=inputs=2:duration=longest:dropout_transition=0[out]'
            f'" -map 0:v -map "[out]" '
            f'-c:v copy -c:a aac -b:a 192k '
            f'"{final}" 2>&1')
    
    if r.returncode != 0:
        print(f"  Mix error: {r.stderr[-200:]}")
    
    f_dur = dur(str(final))
    f_size = os.path.getsize(str(final)) / (1024*1024)
    
    print(f"\n{'='*50}")
    print(f"  Secret_Scores_V3.mp4")
    print(f"  Duration: {f_dur:.1f}s ({f_dur/60:.1f}min)")
    print(f"  Size: {f_size:.0f}MB")
    print(f"  Intro (clip audio): {intro_total:.1f}s")
    print(f"  Narration: {nar_dur_orig:.1f}s at original pace")
    print(f"  Soundbite punch-throughs: {len(soundbite_times)}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
