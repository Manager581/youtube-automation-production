#!/usr/bin/env python3
"""
transcript_extractor.py — Extract transcripts from video clips for the director.

The director needs to know what's being SAID in each available clip so it can
pick the right moments (e.g., "use this clip at 45s because the reporter says
'tenant screening discrimination'").

Methods (in priority order):
1. yt-dlp subtitles (if clip was downloaded from YouTube — free, fast)
2. Existing .srt/.vtt files alongside the clip
3. Claude audio transcription (extract audio → send to Claude)

Output: JSON manifest mapping each clip to its transcript with timestamps.

Usage:
    python -m pipeline_v2.transcript_extractor --clips footage/clips/ --output transcripts.json
    python -m pipeline_v2.transcript_extractor --clips footage/clips/ --method whisper
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_v2.llm import query_claude


def extract_yt_subtitles(clip_dir):
    """Check for existing YouTube subtitles (.srt, .vtt, .txt) alongside clips."""
    transcripts = {}
    
    for ext in ('*.mp4', '*.mkv', '*.mov'):
        for clip_path in glob.glob(os.path.join(clip_dir, '**', ext), recursive=True):
            filename = os.path.basename(clip_path)
            base = os.path.splitext(clip_path)[0]
            
            # Check for subtitle files
            for sub_ext in ('.srt', '.vtt', '.en.srt', '.en.vtt', '.txt'):
                sub_path = base + sub_ext
                if os.path.exists(sub_path):
                    with open(sub_path, errors='replace') as f:
                        content = f.read()
                    
                    # Parse SRT/VTT into timestamped segments
                    segments = parse_subtitle(content)
                    transcripts[filename] = {
                        "path": clip_path,
                        "method": "subtitle_file",
                        "source": sub_path,
                        "full_text": " ".join(s["text"] for s in segments),
                        "segments": segments,
                    }
                    break
    
    return transcripts


def parse_subtitle(content):
    """Parse SRT/VTT content into timestamped segments."""
    import re
    
    segments = []
    
    # SRT format: index\ntimestamp --> timestamp\ntext\n\n
    srt_pattern = re.compile(
        r'(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n(.+?)(?=\n\n|\n\d+\s*\n|\Z)',
        re.DOTALL
    )
    
    for match in srt_pattern.finditer(content):
        start_str = match.group(2).replace(',', '.')
        end_str = match.group(3).replace(',', '.')
        text = match.group(4).strip()
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'\{[^}]+\}', '', text)  # Remove SSA tags
        
        segments.append({
            "start": timestamp_to_sec(start_str),
            "end": timestamp_to_sec(end_str),
            "text": text,
        })
    
    # If SRT parsing got nothing, try VTT (similar but with WEBVTT header)
    if not segments:
        vtt_pattern = re.compile(
            r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.+?)(?=\n\n|\Z)',
            re.DOTALL
        )
        for match in vtt_pattern.finditer(content):
            segments.append({
                "start": timestamp_to_sec(match.group(1)),
                "end": timestamp_to_sec(match.group(2)),
                "text": match.group(3).strip(),
            })
    
    # Fallback: just return the raw text as one segment
    if not segments:
        clean = re.sub(r'WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
        clean = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}', '', clean)
        clean = re.sub(r'^\d+\s*$', '', clean, flags=re.MULTILINE)
        clean = clean.strip()
        if clean:
            segments.append({"start": 0, "end": 0, "text": clean})
    
    return segments


def timestamp_to_sec(ts):
    """Convert HH:MM:SS.mmm to seconds."""
    parts = ts.replace(',', '.').split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def download_yt_subtitles(clip_dir):
    """Try to download YouTube subtitles for clips using yt-dlp."""
    # Check if clips have YouTube IDs in their metadata
    transcripts = {}
    
    for ext in ('*.mp4', '*.mkv', '*.mov'):
        for clip_path in glob.glob(os.path.join(clip_dir, '**', ext), recursive=True):
            filename = os.path.basename(clip_path)
            base = os.path.splitext(clip_path)[0]
            
            # Already have subtitles?
            if any(os.path.exists(base + e) for e in ('.srt', '.vtt', '.en.srt', '.en.vtt')):
                continue
            
            # Try yt-dlp to download subs (if the file came from YouTube)
            # Look for .info.json which contains the video ID
            info_path = base + '.info.json'
            video_id = None
            
            if os.path.exists(info_path):
                with open(info_path) as f:
                    info = json.load(f)
                video_id = info.get('id')
            
            if video_id:
                try:
                    subprocess.run([
                        'yt-dlp', '--write-auto-sub', '--sub-lang', 'en',
                        '--skip-download', '--sub-format', 'srt',
                        '-o', base + '.%(ext)s',
                        f'https://youtube.com/watch?v={video_id}'
                    ], capture_output=True, timeout=30)
                    print(f"  Downloaded subs for: {filename}")
                except:
                    pass
    
    return transcripts


def extract_audio_for_claude(clip_path, output_dir, max_duration=120):
    """Extract audio from clip for Claude transcription."""
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.basename(clip_path)
    audio_path = os.path.join(output_dir, filename.rsplit('.', 1)[0] + '.wav')
    
    if os.path.exists(audio_path):
        return audio_path
    
    # Extract first max_duration seconds of audio
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', clip_path,
            '-t', str(max_duration),
            '-vn', '-ar', '16000', '-ac', '1',
            audio_path
        ], capture_output=True, timeout=60)
        
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            return audio_path
    except:
        pass
    
    return None


def transcribe_with_claude(audio_path, clip_name):
    """Use Claude to describe/transcribe audio content.
    
    Note: Claude can't directly transcribe audio, but it can analyze
    the clip's title and any available context to infer content.
    For actual transcription, use Whisper (if available) or yt-dlp subs.
    """
    prompt = f"""Based on the video title "{clip_name}", describe what topics 
are likely discussed in this clip. List the main subjects, key terms, and 
likely interview quotes or narration topics. Output as a JSON object with 
"topics" (list of strings) and "likely_quotes" (list of strings)."""
    
    response = query_claude(prompt, timeout=30)
    return response


def build_manifest(clip_dir, output_path, methods=None):
    """Build complete transcript manifest for all clips."""
    
    if methods is None:
        methods = ['subtitle_file', 'yt_download', 'title_inference']
    
    all_transcripts = {}
    
    # Method 1: Check existing subtitle files
    if 'subtitle_file' in methods:
        print("  Checking existing subtitle files...")
        subs = extract_yt_subtitles(clip_dir)
        all_transcripts.update(subs)
        print(f"    Found {len(subs)} subtitle files")
    
    # Method 2: Download YouTube subtitles
    if 'yt_download' in methods:
        print("  Downloading YouTube subtitles...")
        download_yt_subtitles(clip_dir)
        # Re-scan for new subtitle files
        new_subs = extract_yt_subtitles(clip_dir)
        for k, v in new_subs.items():
            if k not in all_transcripts:
                all_transcripts[k] = v
        print(f"    Total with subs: {len(all_transcripts)}")
    
    # Method 3: Title-based inference for clips without transcripts
    if 'title_inference' in methods:
        print("  Inferring content from titles...")
        for ext in ('*.mp4', '*.mkv', '*.mov'):
            for clip_path in glob.glob(os.path.join(clip_dir, '**', ext), recursive=True):
                filename = os.path.basename(clip_path)
                if filename not in all_transcripts:
                    title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
                    
                    # Get duration
                    try:
                        result = subprocess.run(
                            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                             '-of', 'csv=p=0', clip_path],
                            capture_output=True, text=True, timeout=10
                        )
                        duration = float(result.stdout.strip())
                    except:
                        duration = 0
                    
                    all_transcripts[filename] = {
                        "path": clip_path,
                        "method": "title_inference",
                        "full_text": f"[Inferred from title: {title}]",
                        "duration": duration,
                        "title": title,
                        "segments": [{"start": 0, "end": duration, "text": title}],
                    }
    
    # Save manifest
    with open(output_path, 'w') as f:
        json.dump(all_transcripts, f, indent=2)
    
    print(f"\n  Manifest saved: {output_path}")
    print(f"  Total clips: {len(all_transcripts)}")
    
    method_counts = {}
    for v in all_transcripts.values():
        m = v.get("method", "unknown")
        method_counts[m] = method_counts.get(m, 0) + 1
    
    for method, count in sorted(method_counts.items()):
        print(f"    {method}: {count}")
    
    return all_transcripts


def main():
    parser = argparse.ArgumentParser(description="Extract transcripts from video clips for the director")
    parser.add_argument('--clips', required=True, nargs='+', help='Clip directories to scan')
    parser.add_argument('--output', default='transcripts.json', help='Output manifest path')
    parser.add_argument('--methods', nargs='+', 
                        default=['subtitle_file', 'yt_download', 'title_inference'],
                        choices=['subtitle_file', 'yt_download', 'title_inference'],
                        help='Transcription methods to use')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"Transcript Extractor")
    print(f"{'='*60}")
    
    for clip_dir in args.clips:
        print(f"\n  Scanning: {clip_dir}")
        build_manifest(clip_dir, args.output, args.methods)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
