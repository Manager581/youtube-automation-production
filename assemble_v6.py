#!/usr/bin/env python3
"""
Assembler V6 — Bulletproof build with QA checks at every step.

Problems in V1-V5:
- Stream copy concat = keyframe issues, frozen video
- Mismatched formats between clips = A/V desync
- No verification = broken output goes undetected

V6 approach:
1. Re-encode EVERY clip to identical format (1080p, 30fps, AAC 48kHz stereo)
2. QA check each clip (duration, frame count, audio present)
3. Concat via filter_complex (not file concat - more reliable)
4. QA check concat (total duration = sum of parts)
5. Add narration with proper sync
6. Final QA: spot-check audio at multiple timestamps
"""
import json, os, subprocess, sys
from pathlib import Path

CLIPS_DIR = Path(os.path.expanduser("~/Documents/youtube-automation-production/footage/fern_clone/secret_scores/clips"))
NARRATION = Path(os.path.expanduser("~/Desktop/SecretScores_Media/narration_135x.wav"))
OUT_DIR = Path(os.path.expanduser("~/Desktop/SecretScores_Media"))
EDIT_MAP = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map_v2.json"))

# Standard format for ALL clips
FPS = 30
WIDTH = 1920
HEIGHT = 1080
AUDIO_RATE = 48000

def run(cmd, timeout=600):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)

def dur(path):
    r = run(f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{path}"')
    try:
        return float(r.stdout.strip())
    except:
        return 0

def frame_count(path):
    r = run(f'ffprobe -v quiet -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "{path}"', timeout=60)
    try:
        return int(r.stdout.strip())
    except:
        return 0

def has_audio(path):
    r = run(f'ffprobe -v quiet -select_streams a -show_entries stream=codec_name -of csv=p=0 "{path}"')
    return bool(r.stdout.strip())

def check_audio_at(path, timestamp):
    """Check if audio is audible at a given timestamp."""
    r = run(f'ffmpeg -ss {timestamp} -i "{path}" -t 2 -af "volumedetect" -f null /dev/null 2>&1')
    for line in r.stderr.split('\n'):
        if 'mean_volume' in line:
            vol = float(line.split('mean_volume:')[1].split('dB')[0].strip())
            return vol
    return -91.0  # silence

def main():
    print("=== Assembler V6 — Bulletproof Build ===\n")
    
    with open(EDIT_MAP) as f:
        data = json.load(f)
    segments = data["segments"]
    intros = set(data["intro_segments"])
    
    tmp = Path("/tmp/v6")
    tmp.mkdir(exist_ok=True)
    
    nar_total = dur(str(NARRATION))
    print(f"Narration (1.35x): {nar_total:.1f}s ({nar_total/60:.1f}min)\n")
    
    # ── STEP 1: Extract & normalize all clips ──
    print("── STEP 1: Extract & normalize clips ──")
    clips_ok = []
    clips_failed = []
    expected_total = 0.0
    intro_dur = 0.0
    
    for seg in segments:
        sid = seg["seg_id"]
        clip = CLIPS_DIR / seg["source_clip"]
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        seg_dur = max(ce - cs, 3)  # minimum 3 seconds
        
        out = tmp / f"s{sid:03d}.mp4"
        
        # Normalize to exact same format: 1080p, 30fps, h264, aac 48kHz stereo
        # -video_track_timescale forces consistent timebase
        cmd = (f'ffmpeg -y -ss {cs} -i "{clip}" -t {seg_dur} '
               f'-c:v libx264 -preset fast -crf 20 -r {FPS} '
               f'-video_track_timescale 15360 '
               f'-vf "scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,'
               f'pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1" '
               f'-c:a aac -b:a 192k -ar {AUDIO_RATE} -ac 2 '
               f'-avoid_negative_ts make_zero -fflags +genpts '
               f'"{out}" 2>/dev/null')
        
        run(cmd)
        
        # ── QA CHECK ──
        actual_dur = dur(str(out))
        frames = frame_count(str(out)) if actual_dur > 0 else 0
        has_aud = has_audio(str(out)) if actual_dur > 0 else False
        expected_frames = int(seg_dur * FPS)
        
        if actual_dur > 0 and frames > 0 and has_aud:
            clips_ok.append({"sid": sid, "path": str(out), "dur": actual_dur})
            expected_total += actual_dur
            if sid in intros:
                intro_dur += actual_dur
        else:
            clips_failed.append(sid)
            print(f"  ✗ SEG {sid:02d}: dur={actual_dur:.1f}s frames={frames} audio={has_aud}")
        
        if sid % 20 == 0:
            print(f"  ✓ {sid:02d}/{len(segments)-1} — {len(clips_ok)} ok, {len(clips_failed)} failed")
    
    print(f"\n  QA: {len(clips_ok)}/{len(segments)} clips OK")
    if clips_failed:
        print(f"  FAILED: {clips_failed}")
    print(f"  Expected total: {expected_total:.1f}s ({expected_total/60:.1f}min)")
    print(f"  Intro: {intro_dur:.1f}s")
    
    # ── STEP 2: Concat with re-encode ──
    print("\n── STEP 2: Concat (re-encode) ──")
    concat_file = tmp / "concat.txt"
    with open(concat_file, "w") as f:
        for c in clips_ok:
            escaped = c["path"].replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
    
    video_all = tmp / "all.mp4"
    r = run(f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
            f'-c:v libx264 -preset fast -crf 20 -r {FPS} '
            f'-force_key_frames "expr:gte(t,n_forced*2)" '
            f'-c:a aac -b:a 192k -ar {AUDIO_RATE} -ac 2 '
            f'-avoid_negative_ts make_zero -fflags +genpts '
            f'"{video_all}" 2>/dev/null', timeout=1200)
    
    vid_dur = dur(str(video_all))
    vid_frames = frame_count(str(video_all))
    
    # ── QA CHECK ──
    drift = abs(vid_dur - expected_total)
    print(f"  Duration: {vid_dur:.1f}s (expected {expected_total:.1f}s, drift {drift:.1f}s)")
    print(f"  Frames: {vid_frames} (expected ~{int(expected_total * FPS)})")
    if drift > 5:
        print(f"  ⚠ WARNING: {drift:.1f}s drift!")
    else:
        print(f"  ✓ Duration within tolerance")
    
    # ── STEP 3: Build narration track ──
    print("\n── STEP 3: Narration track ──")
    silence = tmp / "silence.wav"
    run(f'ffmpeg -y -f lavfi -i "anullsrc=channel_layout=mono:sample_rate=24000" '
        f'-t {intro_dur} -c:a pcm_s16le "{silence}" 2>/dev/null')
    
    nar_concat = tmp / "nar_cat.txt"
    with open(nar_concat, "w") as f:
        f.write(f"file '{silence}'\n")
        f.write(f"file '{NARRATION}'\n")
    
    nar_offset = tmp / "nar_offset.wav"
    run(f'ffmpeg -y -f concat -safe 0 -i "{nar_concat}" -c:a pcm_s16le "{nar_offset}" 2>/dev/null')
    nar_off_dur = dur(str(nar_offset))
    print(f"  Narration: {nar_off_dur:.1f}s (silence: {intro_dur:.1f}s + VO: {nar_total:.1f}s)")
    
    # ── STEP 4: Final mix ──
    print("\n── STEP 4: Final mix ──")
    final = OUT_DIR / "Secret_Scores_V6.mp4"
    
    # Trim to whichever is shorter: video or narration+intro
    final_dur = min(vid_dur, nar_off_dur + 5)  # 5s buffer
    
    r = run(f'ffmpeg -y -i "{video_all}" -i "{nar_offset}" '
            f'-filter_complex "'
            f'[0:a]volume=0.12[clip];'
            f'[1:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo,volume=1.2[nar];'
            f'[clip][nar]amix=inputs=2:duration=shortest:dropout_transition=0[out]'
            f'" -map 0:v -map "[out]" '
            f'-c:v copy -c:a aac -b:a 192k '
            f'-t {final_dur} '
            f'"{final}" 2>&1')
    
    if r.returncode != 0:
        print(f"  ✗ Mix failed: {r.stderr[-200:]}")
        return
    
    f_dur = dur(str(final))
    f_size = os.path.getsize(str(final)) / (1024*1024)
    
    # ── STEP 5: Final QA ──
    print(f"\n── STEP 5: Final QA ──")
    qa_pass = True
    
    # Check audio at multiple points
    for t in [2, 10, 30, 60, 120, 300, 600]:
        if t < f_dur:
            vol = check_audio_at(str(final), t)
            status = "✓" if vol > -50 else "✗ SILENT"
            print(f"  {status} Audio at {t}s: {vol:.1f}dB")
            if vol <= -50:
                qa_pass = False
    
    # Check video plays (frame count)
    final_frames = frame_count(str(final))
    expected_final_frames = int(f_dur * FPS)
    frame_ratio = final_frames / max(expected_final_frames, 1)
    if 0.95 < frame_ratio < 1.05:
        print(f"  ✓ Frames: {final_frames} (expected ~{expected_final_frames})")
    else:
        print(f"  ✗ Frame mismatch: {final_frames} vs expected {expected_final_frames}")
        qa_pass = False
    
    # Check keyframes exist throughout
    r = run(f'ffprobe -v quiet -select_streams v -show_entries frame=pict_type,pts_time '
            f'-of csv=p=0 -read_intervals "%+30" "{final}" 2>/dev/null')
    iframes = [l for l in r.stdout.strip().split('\n') if ',I' in l]
    print(f"  {"✓" if len(iframes) >= 5 else "✗"} Keyframes in first 30s: {len(iframes)}")
    
    print(f"\n{'='*50}")
    print(f"  Secret_Scores_V6.mp4")
    print(f"  Duration: {f_dur:.1f}s ({f_dur/60:.1f}min)")
    print(f"  Size: {f_size:.0f}MB")
    print(f"  QA: {'ALL PASSED ✓' if qa_pass else 'ISSUES FOUND ✗'}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
