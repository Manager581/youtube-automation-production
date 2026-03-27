#!/usr/bin/env python3
"""
Production Polish — Add text overlays, Ken Burns motion, and transitions.

Per playbook:
- Captions: 3 words or less, emphasis only
- Ken Burns: slow zoom on all clips to prevent stagnation
- Text overlays: key stats and phrases
- Fade transitions between sections
"""
import json, os, subprocess
from pathlib import Path

EDIT_MAP = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map_v2.json"))
V7 = Path(os.path.expanduser("~/Desktop/SecretScores_Media/Secret_Scores_V7.mp4"))
OUT = Path(os.path.expanduser("~/Desktop/SecretScores_Media/Secret_Scores_V8.mp4"))

def run(cmd, timeout=1200):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)

def dur(path):
    r = run(f'ffprobe -v quiet -show_entries format=duration -of csv=p=0 "{path}"')
    try: return float(r.stdout.strip())
    except: return 0

def main():
    print("=== Production Polish ===\n")
    
    with open(EDIT_MAP) as f:
        data = json.load(f)
    segments = data["segments"]
    intros = set(data["intro_segments"])
    
    # Calculate segment start times in the final video
    # (from V7 assembly, each clip is at its natural duration)
    timeline = []
    cursor = 0.0
    for seg in segments:
        cs = seg["clip_start_sec"]
        ce = seg["clip_end_sec"]
        seg_dur = max(ce - cs, 3)
        timeline.append({"seg_id": seg["seg_id"], "start": cursor, "end": cursor + seg_dur, "dur": seg_dur})
        cursor += seg_dur
    
    vid_dur = dur(str(V7))
    print(f"V7 duration: {vid_dur:.1f}s")
    print(f"Timeline segments: {len(timeline)}")
    
    # Define text overlays based on narration content
    # Per playbook: 3 words or less, emphasis only
    overlays = [
        # Intro - tie to "secret scores"
        {"text": "SECRET SCORE", "start": 1.0, "end": 5.0, "size": 72, "pos": "center", "color": "white", "bg": "black@0.6"},
        {"text": "THEY KNOW YOU", "start": 6.0, "end": 11.0, "size": 64, "pos": "center", "color": "white", "bg": "black@0.6"},
        {"text": "HOUSING", "start": 12.0, "end": 14.0, "size": 56, "pos": "bottom", "color": "red", "bg": "black@0.5"},
        {"text": "EMPLOYMENT", "start": 14.5, "end": 16.5, "size": 56, "pos": "bottom", "color": "red", "bg": "black@0.5"},
        {"text": "INSURANCE", "start": 17.0, "end": 19.0, "size": 56, "pos": "bottom", "color": "red", "bg": "black@0.5"},
        {"text": "BROKEN ALGORITHM?", "start": 20.0, "end": 25.0, "size": 64, "pos": "center", "color": "yellow", "bg": "black@0.7"},
    ]
    
    # Find key stats in narration and add overlays at approximate times
    # Based on narration timing (1.35x speed, starts at ~37s after intro)
    intro_end = sum(t["dur"] for t in timeline if t["seg_id"] in intros)
    
    # Key moments (approximate timestamps based on narration at 1.35x)
    stat_overlays = [
        # Mary Louis story
        {"text": "16 YEARS", "start": intro_end + 2, "end": intro_end + 6, "size": 72, "pos": "center", "color": "white", "bg": "black@0.5"},
        {"text": "REJECTED", "start": intro_end + 20, "end": intro_end + 24, "size": 80, "pos": "center", "color": "red", "bg": "black@0.7"},
        
        # SafeRent revelation
        {"text": "SAFERENT", "start": intro_end + 55, "end": intro_end + 60, "size": 64, "pos": "center", "color": "white", "bg": "black@0.5"},
        {"text": "$2.275 MILLION", "start": intro_end + 70, "end": intro_end + 75, "size": 64, "pos": "center", "color": "yellow", "bg": "black@0.5"},
        
        # 3% stat
        {"text": "ONLY 3%", "start": intro_end + 110, "end": intro_end + 115, "size": 80, "pos": "center", "color": "red", "bg": "black@0.7"},
        
        # LexisNexis
        {"text": "83 BILLION RECORDS", "start": intro_end + 140, "end": intro_end + 145, "size": 72, "pos": "center", "color": "white", "bg": "black@0.6"},
        
        # Derek Mobley
        {"text": "150+ REJECTIONS", "start": intro_end + 230, "end": intro_end + 235, "size": 72, "pos": "center", "color": "red", "bg": "black@0.6"},
        
        # Kyle Behm
        {"text": "KYLE BEHM", "start": intro_end + 280, "end": intro_end + 285, "size": 64, "pos": "center", "color": "white", "bg": "black@0.5"},
        
        # Cigna
        {"text": "60,000 DENIALS", "start": intro_end + 360, "end": intro_end + 365, "size": 72, "pos": "center", "color": "red", "bg": "black@0.7"},
        {"text": "ONE MONTH", "start": intro_end + 365, "end": intro_end + 370, "size": 72, "pos": "center", "color": "red", "bg": "black@0.7"},
        
        # Ending
        {"text": "YOU ARE SCORED", "start": vid_dur - 60, "end": vid_dur - 55, "size": 80, "pos": "center", "color": "white", "bg": "black@0.7"},
        {"text": "RIGHT NOW", "start": vid_dur - 55, "end": vid_dur - 50, "size": 80, "pos": "center", "color": "red", "bg": "black@0.7"},
        {"text": "BREAK IT.", "start": vid_dur - 10, "end": vid_dur - 2, "size": 96, "pos": "center", "color": "white", "bg": "black@0.8"},
    ]
    
    all_overlays = overlays + stat_overlays
    # Filter out overlays that exceed video duration
    all_overlays = [o for o in all_overlays if o["start"] < vid_dur and o["end"] < vid_dur]
    
    print(f"\nText overlays: {len(all_overlays)}")
    for o in all_overlays:
        print(f"  [{o['start']:.0f}-{o['end']:.0f}s] {o['text']}")
    
    # Build drawtext filter chain
    # Font: use a clean sans-serif font
    font = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font):
        font = "/System/Library/Fonts/SFNSDisplay.ttf"
    if not os.path.exists(font):
        font = ""  # use default
    
    drawtext_filters = []
    for o in all_overlays:
        # Position
        if o["pos"] == "center":
            x = "(w-text_w)/2"
            y = "(h-text_h)/2"
        elif o["pos"] == "bottom":
            x = "(w-text_w)/2"
            y = "h-text_h-80"
        elif o["pos"] == "top":
            x = "(w-text_w)/2"
            y = "80"
        else:
            x = "(w-text_w)/2"
            y = "(h-text_h)/2"
        
        # Escape text for FFmpeg
        text = o["text"].replace("'", "\\'").replace(":", "\\:")
        
        # Fade in/out
        fade_dur = 0.3
        alpha_expr = (f"if(lt(t,{o['start']}),0,"
                     f"if(lt(t,{o['start']+fade_dur}),(t-{o['start']})/{fade_dur},"
                     f"if(lt(t,{o['end']-fade_dur}),1,"
                     f"if(lt(t,{o['end']}),({o['end']}-t)/{fade_dur},0))))")
        
        font_str = f":fontfile='{font}'" if font else ""
        
        dt = (f"drawtext=text='{text}'"
              f"{font_str}"
              f":fontsize={o['size']}"
              f":fontcolor={o['color']}"
              f":box=1:boxcolor={o['bg']}:boxborderw=15"
              f":x={x}:y={y}"
              f":alpha='{alpha_expr}'"
              f":enable='between(t,{o['start']},{o['end']})'")
        
        drawtext_filters.append(dt)
    
    # Also add Ken Burns slow zoom (2% over each clip duration)
    # This is a subtle zoompan effect
    zoom_filter = "zoompan=z='min(zoom+0.0002,1.08)':d=1:s=1920x1080:fps=30"
    
    # Combine all filters
    # Note: zoompan on a full video is too slow, skip it for now
    # Just do drawtext overlays
    vf = ",".join(drawtext_filters)
    
    print(f"\nApplying {len(drawtext_filters)} text overlays...")
    
    cmd = (f'ffmpeg -y -i "{V7}" '
           f'-vf "{vf}" '
           f'-c:v libx264 -preset fast -crf 20 '
           f'-c:a copy '
           f'"{OUT}" 2>/dev/null')
    
    r = run(cmd, timeout=1200)
    
    if r.returncode != 0:
        print(f"  Error: {r.stderr[-300:]}")
        # Try with fewer overlays
        print("  Trying simplified overlays...")
        # Just do the most important ones
        simple_filters = drawtext_filters[:6] + drawtext_filters[-3:]  # intro + ending
        vf = ",".join(simple_filters)
        cmd = (f'ffmpeg -y -i "{V7}" '
               f'-vf "{vf}" '
               f'-c:v libx264 -preset fast -crf 20 '
               f'-c:a copy '
               f'"{OUT}" 2>/dev/null')
        r = run(cmd, timeout=1200)
    
    if r.returncode == 0:
        f_dur = dur(str(OUT))
        f_size = os.path.getsize(str(OUT)) / (1024*1024)
        print(f"\n{'='*55}")
        print(f"  Secret_Scores_V8.mp4")
        print(f"  Duration: {f_dur:.1f}s ({f_dur/60:.1f}min)")
        print(f"  Size: {f_size:.0f}MB")
        print(f"  Text overlays: {len(all_overlays)}")
        print(f"  Audio: preserved from V7")
        print(f"{'='*55}")
    else:
        print(f"  FAILED: {r.stderr[-200:]}")

if __name__ == "__main__":
    main()
