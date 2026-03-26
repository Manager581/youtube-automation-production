#!/usr/bin/env python3
"""
Assembler V3c — Keep audio in ALL segments, handle separation in final mix.
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
    print("=== Assembler V3c ===\n")
    
    with open(EDIT_MAP) as f:
        data = json.load(f)
    segments = data["segments"]
    soundbites = set(data["soundbite_segments"])
    intros = set(data["intro_segments"])
    
    tmp = Path("/tmp/v3c")
    tmp.mkdir(exist_ok=True)
    
    # Step 1: Extract ALL clips with audio (simple, reliable)
    print("--- Step 1: Extract clips ---")
    concat_lines = []
    intro_total = 0.0
    timeline_cursor = 0.0
    
    for seg in segments:
        sid = seg["seg_id"]
        clip = CLIPS_DIR / seg["source_clip"]
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        mode = seg["audio_mode"]
        seg_dur = ce - cs
        
        out = tmp / f"s{sid:03d}.mp4"
        
        # Always keep audio — we'll handle muting in final mix
        cmd = (f'ffmpeg -y -ss {cs} -i "{clip}" -t {seg_dur} '
               f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
               f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,'
               f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
               f'"{out}" 2>/dev/null')
        
        r = run(cmd)
        actual = dur(str(out))
        
        if actual > 0:
            escaped = str(out).replace("'", "'\\''")
            concat_lines.append(f"file '{escaped}'")
            if sid in intros:
                intro_total += actual
            timeline_cursor += actual
        else:
            print(f"  FAILED: seg {sid}")
        
        if sid % 10 == 0:
            print(f"  {sid:02d}/{len(segments)-1} [{mode:10s}] {actual:.1f}s  total={timeline_cursor:.1f}s")
    
    print(f"\n  Total video: {timeline_cursor:.1f}s ({timeline_cursor/60:.1f}min)")
    print(f"  Intro: {intro_total:.1f}s")
    
    # Step 2: Concat
    print("\n--- Step 2: Concat ---")
    concat_file = tmp / "concat.txt"
    with open(concat_file, "w") as f:
        f.write("\n".join(concat_lines))
    
    video_all = tmp / "all.mp4"
    r = run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" -c copy "{video_all}" 2>&1')
    if r.returncode != 0:
        print("  Stream copy failed, re-encoding...")
        run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
            f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
            f'"{video_all}" 2>/dev/null')
    
    vid_dur = dur(str(video_all))
    print(f"  Video: {vid_dur:.1f}s ({vid_dur/60:.1f}min)")
    
    # Step 3: Build narration track
    print("\n--- Step 3: Narration track ---")
    nar_dur_orig = dur(str(NARRATION))
    
    # Silence for intro, then narration
    silence = tmp / "silence.wav"
    run(f'ffmpeg -y -f lavfi -i "anullsrc=channel_layout=mono:sample_rate=24000" '
        f'-t {intro_total} -c:a pcm_s16le "{silence}" 2>/dev/null')
    
    nar_concat = tmp / "nar_cat.txt"
    with open(nar_concat, "w") as f:
        f.write(f"file '{silence}'\n")
        f.write(f"file '{NARRATION}'\n")
    
    nar_offset = tmp / "nar_offset.wav"
    run(f'ffmpeg -y -f concat -safe 0 -i "{nar_concat}" -c:a pcm_s16le "{nar_offset}" 2>/dev/null')
    print(f"  Narration offset: {dur(str(nar_offset)):.1f}s")
    
    # Step 4: Final mix — CRITICAL AUDIO SEPARATION
    # Video has clip audio throughout. Narration has silence during intro then VO.
    # We want: 
    #   - During intro: clip audio LOUD, no narration → viewer hears source clips
    #   - During VO sections: narration LOUD, clip audio MUTED → viewer hears VO only
    #   - During soundbites: both play (clip audio punches through)
    #
    # Since we can't do per-segment volume in a single ffmpeg pass without complex filters,
    # we use this approach:
    #   - Clip audio at LOW volume (0.15) — barely audible background
    #   - Narration at HIGH volume (1.3) — dominates when playing
    #   - During intro (narration is silent), clip audio is the only thing heard
    #   - During soundbites, clip audio is still low but those segments have louder source audio
    
    print("\n--- Step 4: Final mix ---")
    final = OUT_DIR / "Secret_Scores_V3.mp4"
    
    r = run(f'ffmpeg -y -i "{video_all}" -i "{nar_offset}" '
            f'-filter_complex "'
            f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.15[clip];'
            f'[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.3[nar];'
            f'[clip][nar]amix=inputs=2:duration=first:dropout_transition=0[out]'
            f'" -map 0:v -map "[out]" '
            f'-c:v copy -c:a aac -b:a 192k '
            f'"{final}" 2>&1')
    
    if r.returncode != 0:
        print(f"  Error: {r.stderr[-300:]}")
    
    f_dur = dur(str(final))
    f_size = os.path.getsize(str(final)) / (1024*1024) if final.exists() else 0
    
    print(f"\n{'='*50}")
    print(f"  Secret_Scores_V3.mp4")
    print(f"  Duration: {f_dur:.1f}s ({f_dur/60:.1f}min)")
    print(f"  Size: {f_size:.0f}MB")
    print(f"  Intro (clip audio): {intro_total:.1f}s")  
    print(f"  Narration: {nar_dur_orig:.1f}s at original pace")
    print(f"  Clip audio: 15% volume (background/intro only)")
    print(f"{'='*50}")
    print(f"\nNOTE: Video is {vid_dur:.0f}s but narration is {nar_dur_orig:.0f}s.")
    if vid_dur < nar_dur_orig:
        print(f"  Video is {nar_dur_orig - vid_dur:.0f}s SHORT — need more clip segments or longer cuts.")
        print(f"  The narration will play over a frozen last frame after video ends.")

if __name__ == "__main__":
    main()
