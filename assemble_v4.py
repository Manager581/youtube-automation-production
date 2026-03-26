#!/usr/bin/env python3
"""
Assembler V4 — Full editorial assembly with:
- 1.35x narration speed (169 WPM, documentary sweet spot)
- Fixed intro clip mapping (visuals match narration)
- Proper audio separation (no clip bleed during VO)
- Visual switch every ~4s per playbook
"""
import json, os, subprocess
from pathlib import Path

CLIPS_DIR = Path(os.path.expanduser("~/Documents/youtube-automation-production/footage/fern_clone/secret_scores/clips"))
NARRATION = Path(os.path.expanduser("~/Desktop/SecretScores_Media/narration_135x.wav"))
OUT_DIR = Path(os.path.expanduser("~/Desktop/SecretScores_Media"))
EDIT_MAP = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map.json"))

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)

def dur(path):
    r = run(f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{path}"')
    return float(r.stdout.strip()) if r.stdout.strip() else 0

def main():
    print("=== Assembler V4 — Full Editorial Build ===\n")
    
    with open(EDIT_MAP) as f:
        data = json.load(f)
    segments = data["segments"]
    soundbites = set(data["soundbite_segments"])
    intros = set(data["intro_segments"])
    
    tmp = Path("/tmp/v4")
    tmp.mkdir(exist_ok=True)
    
    nar_dur = dur(str(NARRATION))
    print(f"Narration (1.35x): {nar_dur:.1f}s ({nar_dur/60:.1f}min, ~169 WPM)")
    
    # Calculate target video duration to match narration
    # Intro clips have their own duration, remaining clips need to fill narration time
    intro_clips = [s for s in segments if s["seg_id"] in intros]
    vo_clips = [s for s in segments if s["seg_id"] not in intros]
    
    intro_dur_total = sum(s["clip_end_sec"] - s["clip_start_sec"] for s in intro_clips)
    remaining_dur = nar_dur  # Narration fills the rest
    vo_dur_each = remaining_dur / len(vo_clips)
    
    print(f"Intro: {intro_dur_total:.1f}s ({len(intro_clips)} clips)")
    print(f"VO sections: {remaining_dur:.1f}s / {len(vo_clips)} clips = {vo_dur_each:.1f}s each")
    
    # Extract clips
    print("\n--- Extract clips ---")
    concat_lines = []
    intro_total = 0.0
    
    for seg in segments:
        sid = seg["seg_id"]
        clip = CLIPS_DIR / seg["source_clip"]
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        mode = seg["audio_mode"]
        natural_dur = ce - cs
        
        out = tmp / f"s{sid:03d}.mp4"
        
        if sid in intros:
            # Intro: use natural duration with audio
            target_dur = natural_dur
            audio_flag = "-c:a aac -b:a 192k"
        else:
            # VO: extend clip to fill narration chunk
            target_dur = vo_dur_each
            # Mute clip audio for VO segments (will overlay narration)
            audio_flag = "-an"
        
        # If clip is shorter than target, use -stream_loop
        if natural_dur >= target_dur:
            cmd = (f'ffmpeg -y -ss {cs} -i "{clip}" -t {target_dur} '
                   f'-c:v libx264 -preset ultrafast -crf 20 {audio_flag} '
                   f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,'
                   f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
                   f'"{out}" 2>/dev/null')
        else:
            # Loop the clip segment to fill the time
            # First extract the short clip, then loop it
            short = tmp / f"short_{sid:03d}.mp4"
            cmd1 = (f'ffmpeg -y -ss {cs} -i "{clip}" -t {natural_dur} '
                    f'-c:v libx264 -preset ultrafast -crf 20 -an '
                    f'-vf "scale=1920:1080:force_original_aspect_ratio=decrease,'
                    f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2" '
                    f'"{short}" 2>/dev/null')
            run(cmd1)
            cmd = (f'ffmpeg -y -stream_loop -1 -i "{short}" -t {target_dur} '
                   f'-c:v libx264 -preset ultrafast -crf 20 -an '
                   f'"{out}" 2>/dev/null')
        
        run(cmd)
        actual = dur(str(out))
        
        if actual > 0:
            escaped = str(out).replace("'", "'\\''")
            concat_lines.append(f"file '{escaped}'")
            if sid in intros:
                intro_total += actual
        else:
            print(f"  FAILED: seg {sid} ({seg['source_clip'][:30]})")
        
        if sid % 15 == 0:
            print(f"  {sid:02d}/{len(segments)-1} [{mode:10s}] {actual:.1f}s")
    
    # Concat all video
    print("\n--- Concat ---")
    concat_file = tmp / "concat.txt"
    with open(concat_file, "w") as f:
        f.write("\n".join(concat_lines))
    
    # VO clips have no audio, intro clips have audio — need to handle this
    # Re-encode concat to ensure consistent streams
    video_all = tmp / "all.mp4"
    run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
        f'-c:v libx264 -preset ultrafast -crf 20 '
        f'-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 '
        f'-map 0:v -map 1:a -shortest '
        f'-c:a aac -b:a 192k '
        f'"{video_all}" 2>/dev/null')
    
    vid_dur = dur(str(video_all))
    print(f"  Video: {vid_dur:.1f}s ({vid_dur/60:.1f}min)")
    
    # Build narration track with intro silence
    print("\n--- Narration track ---")
    silence = tmp / "silence.wav"
    nar_sr = "24000"  # Match narration sample rate
    r = run(f'ffprobe -v quiet -show_entries stream=sample_rate -of csv=p=0 "{NARRATION}"')
    if r.stdout.strip():
        nar_sr = r.stdout.strip()
    
    run(f'ffmpeg -y -f lavfi -i "anullsrc=channel_layout=mono:sample_rate={nar_sr}" '
        f'-t {intro_total} -c:a pcm_s16le "{silence}" 2>/dev/null')
    
    nar_concat = tmp / "nar_cat.txt"
    with open(nar_concat, "w") as f:
        f.write(f"file '{silence}'\n")
        f.write(f"file '{NARRATION}'\n")
    
    nar_offset = tmp / "nar_offset.wav"
    run(f'ffmpeg -y -f concat -safe 0 -i "{nar_concat}" -c:a pcm_s16le "{nar_offset}" 2>/dev/null')
    nar_off_dur = dur(str(nar_offset))
    print(f"  Offset narration: {nar_off_dur:.1f}s")
    
    # Also extract intro audio separately (from the intro clip segments)
    print("\n--- Intro audio ---")
    intro_audio_parts = []
    for seg in intro_clips:
        sid = seg["seg_id"]
        clip = CLIPS_DIR / seg["source_clip"]
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        seg_dur = ce - cs
        ia = tmp / f"intro_audio_{sid:03d}.wav"
        run(f'ffmpeg -y -ss {cs} -i "{clip}" -t {seg_dur} -vn '
            f'-ar 48000 -ac 2 -c:a pcm_s16le "{ia}" 2>/dev/null')
        if ia.exists():
            intro_audio_parts.append(str(ia))
    
    # Concat intro audio
    intro_audio = tmp / "intro_audio.wav"
    ia_concat = tmp / "ia_concat.txt"
    with open(ia_concat, "w") as f:
        for p in intro_audio_parts:
            f.write(f"file '{p}'\n")
    run(f'ffmpeg -y -f concat -safe 0 -i "{ia_concat}" -c:a pcm_s16le "{intro_audio}" 2>/dev/null')
    
    # Pad intro audio to full video length with silence
    intro_audio_full = tmp / "intro_audio_full.wav"
    run(f'ffmpeg -y -i "{intro_audio}" -af "apad=pad_dur={vid_dur}" '
        f'-t {vid_dur} -c:a pcm_s16le "{intro_audio_full}" 2>/dev/null')
    
    print(f"  Intro audio: {dur(str(intro_audio)):.1f}s → padded to {vid_dur:.1f}s")
    
    # Final mix: intro_audio_full (loud during intro, silent rest) + narration (silent during intro, loud rest)
    print("\n--- Final mix ---")
    final = OUT_DIR / "Secret_Scores_V4.mp4"
    
    r = run(f'ffmpeg -y -i "{video_all}" '
            f'-i "{intro_audio_full}" '
            f'-i "{nar_offset}" '
            f'-filter_complex "'
            f'[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.0[intro];'
            f'[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.0[nar];'
            f'[intro][nar]amix=inputs=2:duration=first:dropout_transition=0[out]'
            f'" -map 0:v -map "[out]" '
            f'-c:v copy -c:a aac -b:a 192k '
            f'-t {vid_dur} '
            f'"{final}" 2>&1')
    
    if r.returncode != 0:
        print(f"  Error: {r.stderr[-300:]}")
    
    f_dur = dur(str(final))
    f_size = os.path.getsize(str(final)) / (1024*1024) if final.exists() else 0
    
    print(f"\n{'='*50}")
    print(f"  Secret_Scores_V4.mp4")
    print(f"  Duration: {f_dur:.1f}s ({f_dur/60:.1f}min)")
    print(f"  Size: {f_size:.0f}MB")
    print(f"  Narration: 1.35x speed (~169 WPM)")
    print(f"  Intro audio: {intro_total:.1f}s (clip audio)")
    print(f"  VO audio: CLEAN (no clip bleed)")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
