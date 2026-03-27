#!/usr/bin/env python3
"""
Assembler V5 — Smart transcript-matched clips + 1.35x narration.
Uses editorial_clip_map_v2.json where clip timestamps are matched
to narration content using source clip transcripts.
"""
import json, os, subprocess
from pathlib import Path

CLIPS_DIR = Path(os.path.expanduser("~/Documents/youtube-automation-production/footage/fern_clone/secret_scores/clips"))
NARRATION = Path(os.path.expanduser("~/Desktop/SecretScores_Media/narration_135x.wav"))
OUT_DIR = Path(os.path.expanduser("~/Desktop/SecretScores_Media"))
EDIT_MAP = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map_v2.json"))

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)

def dur(path):
    r = run(f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{path}"')
    return float(r.stdout.strip()) if r.stdout.strip() else 0

def main():
    print("=== Assembler V5 — Smart Transcript-Matched ===\n")
    
    with open(EDIT_MAP) as f:
        data = json.load(f)
    segments = data["segments"]
    intros = set(data["intro_segments"])
    
    tmp = Path("/tmp/v5")
    tmp.mkdir(exist_ok=True)
    
    nar_total = dur(str(NARRATION))
    print(f"Narration (1.35x): {nar_total:.1f}s ({nar_total/60:.1f}min)")
    
    # Extract all clips at their smart-matched timestamps
    print("\n--- Extract clips ---")
    concat_lines = []
    intro_total = 0.0
    
    for seg in segments:
        sid = seg["seg_id"]
        clip = CLIPS_DIR / seg["source_clip"]
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        mode = seg["audio_mode"]
        seg_dur = ce - cs
        
        if seg_dur <= 0:
            seg_dur = 8  # default
            ce = cs + seg_dur
        
        out = tmp / f"s{sid:03d}.mp4"
        
        # All clips get extracted with audio (we separate later)
        cmd = (f'ffmpeg -y -ss {cs} -i "{clip}" -t {seg_dur} '
               f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
               f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,'
               f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
               f'"{out}" 2>/dev/null')
        
        run(cmd)
        actual = dur(str(out))
        
        if actual > 0:
            escaped = str(out).replace("'", "'\\''")
            concat_lines.append(f"file '{escaped}'")
            if sid in intros:
                intro_total += actual
        
        if sid % 15 == 0:
            print(f"  {sid:02d}/{len(segments)-1} [{mode:10s}] {cs:.0f}-{ce:.0f}s → {actual:.1f}s")
    
    # Concat all video
    print(f"\n--- Concat {len(concat_lines)} clips ---")
    concat_file = tmp / "concat.txt"
    with open(concat_file, "w") as f:
        f.write("\n".join(concat_lines))
    
    video_all = tmp / "all.mp4"
    r = run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" -c copy "{video_all}" 2>&1')
    if r.returncode != 0:
        # Re-encode if stream copy fails
        run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
            f'-c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 192k '
            f'"{video_all}" 2>/dev/null')
    
    vid_dur = dur(str(video_all))
    print(f"  Video: {vid_dur:.1f}s ({vid_dur/60:.1f}min)")
    
    # Build narration with intro silence
    print("\n--- Narration track ---")
    nar_sr = run(f'ffprobe -v quiet -show_entries stream=sample_rate -of csv=p=0 "{NARRATION}"').stdout.strip() or "24000"
    nar_ch = run(f'ffprobe -v quiet -show_entries stream=channels -of csv=p=0 "{NARRATION}"').stdout.strip() or "1"
    ch_layout = "mono" if nar_ch == "1" else "stereo"
    
    silence = tmp / "silence.wav"
    run(f'ffmpeg -y -f lavfi -i "anullsrc=channel_layout={ch_layout}:sample_rate={nar_sr}" '
        f'-t {intro_total} -c:a pcm_s16le "{silence}" 2>/dev/null')
    
    nar_concat = tmp / "nar_cat.txt"
    with open(nar_concat, "w") as f:
        f.write(f"file '{silence}'\n")
        f.write(f"file '{NARRATION}'\n")
    
    nar_offset = tmp / "nar_offset.wav"
    run(f'ffmpeg -y -f concat -safe 0 -i "{nar_concat}" -c:a pcm_s16le "{nar_offset}" 2>/dev/null')
    
    nar_off_dur = dur(str(nar_offset))
    print(f"  Narration: {nar_off_dur:.1f}s (intro silence: {intro_total:.1f}s)")
    
    # Final mix: during intro use clip audio, rest use narration only
    print("\n--- Final mix ---")
    final = OUT_DIR / "Secret_Scores_V5.mp4"
    
    # Strategy: mix video audio (low volume) + narration (high volume)
    # During intro: clip audio is loud, narration is silent → hear clips
    # During rest: narration is loud, clip audio provides subtle ambience
    r = run(f'ffmpeg -y -i "{video_all}" -i "{nar_offset}" '
            f'-filter_complex "'
            f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.15[clip];'
            f'[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.2[nar];'
            f'[clip][nar]amix=inputs=2:duration=longest:dropout_transition=0[out]'
            f'" -map 0:v -map "[out]" '
            f'-c:v copy -c:a aac -b:a 192k '
            f'"{final}" 2>&1')
    
    if r.returncode != 0:
        print(f"  Error: {r.stderr[-200:]}")
    
    f_dur = dur(str(final))
    f_size = os.path.getsize(str(final)) / (1024*1024) if final.exists() else 0
    
    print(f"\n{'='*50}")
    print(f"  Secret_Scores_V5.mp4")
    print(f"  Duration: {f_dur:.1f}s ({f_dur/60:.1f}min)")
    print(f"  Size: {f_size:.0f}MB")
    print(f"  Narration: 1.35x (~169 WPM)")
    print(f"  Clips: Transcript-matched to narration content")
    print(f"  Audio: Clip at 15% (ambience), VO at 120%")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
