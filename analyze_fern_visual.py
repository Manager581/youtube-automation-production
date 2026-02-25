#!/usr/bin/env python3
"""
Fern Visual Analyzer
Extracts visual pacing patterns from Fern videos using ffmpeg scene detection.

Analyzes:
- Cut frequency (average seconds per shot)
- Pacing distribution (intro/body/outro)
- Cut timing relative to script moments
- Pacing correlation with curiosity gaps and hooks

Usage:
    python analyze_fern_visual.py <video_id>
    python analyze_fern_visual.py --all  # Analyze all videos with video.mp4

Examples:
    python analyze_fern_visual.py wLFY_Zu_O08
    python analyze_fern_visual.py --all
"""

import subprocess
import json
import re
import sys
import statistics
from pathlib import Path
from collections import defaultdict

# ============================================================================
# SCENE DETECTION (using ffmpeg)
# ============================================================================

def detect_cuts(video_path, threshold=0.3):
    """
    Detect scene changes (cuts) using ffmpeg.

    Args:
        video_path: Path to video file
        threshold: Scene change sensitivity (0.1-0.9, lower = more sensitive)

    Returns:
        List of cut timestamps in seconds
    """
    print(f"  Detecting cuts with ffmpeg (threshold={threshold})...")

    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-filter:v', f'select=gt(scene\\,{threshold}),showinfo',
        '-f', 'null',
        '-'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        stderr = result.stderr

        # Parse scene change timestamps
        # Format: [Parsed_showinfo_1 @ 0x...] n: 123 pts: 246000 pts_time:2.05
        pattern = r'pts_time:([\d.]+)'
        matches = re.findall(pattern, stderr)

        cut_times = [float(t) for t in matches]
        cut_times = sorted(set(cut_times))  # Remove duplicates

        print(f"  Found {len(cut_times)} cuts")
        return cut_times

    except subprocess.TimeoutExpired:
        print(f"  ⚠️  ffmpeg timeout - video may be too long or corrupted")
        return []
    except FileNotFoundError:
        print(f"  ❌ ffmpeg not found. Install with: brew install ffmpeg")
        return []
    except Exception as e:
        print(f"  ❌ Error detecting cuts: {e}")
        return []


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        duration = float(result.stdout.strip())
        return duration
    except:
        return None


# ============================================================================
# CUT ANALYSIS
# ============================================================================

def analyze_cuts(cut_times, video_duration):
    """Analyze cut frequency and distribution"""

    if not cut_times or video_duration == 0:
        return {}

    # Calculate shot durations (time between cuts)
    shot_durations = []
    for i in range(len(cut_times)):
        if i == 0:
            # First shot: 0 to first cut
            duration = cut_times[0]
        else:
            # Shot duration = current cut - previous cut
            duration = cut_times[i] - cut_times[i-1]
        shot_durations.append(duration)

    # Last shot: last cut to end
    if cut_times:
        last_duration = video_duration - cut_times[-1]
        shot_durations.append(last_duration)

    # Filter outliers (sometimes ffmpeg detects false positives)
    shot_durations = [d for d in shot_durations if 0.5 < d < 60]  # 0.5s - 60s range

    # Overall metrics
    total_cuts = len(cut_times)
    avg_shot_duration = statistics.mean(shot_durations) if shot_durations else 0
    median_shot_duration = statistics.median(shot_durations) if shot_durations else 0
    min_shot = min(shot_durations) if shot_durations else 0
    max_shot = max(shot_durations) if shot_durations else 0

    # Pacing distribution (intro/body/outro)
    intro_end = video_duration * 0.10
    body_end = video_duration * 0.85

    intro_cuts = [c for c in cut_times if c < intro_end]
    body_cuts = [c for c in cut_times if intro_end <= c < body_end]
    outro_cuts = [c for c in cut_times if c >= body_end]

    # Calculate cuts per minute in each section
    intro_duration = intro_end
    body_duration = body_end - intro_end
    outro_duration = video_duration - body_end

    intro_cpm = (len(intro_cuts) / intro_duration) * 60 if intro_duration > 0 else 0
    body_cpm = (len(body_cuts) / body_duration) * 60 if body_duration > 0 else 0
    outro_cpm = (len(outro_cuts) / outro_duration) * 60 if outro_duration > 0 else 0

    return {
        'total_cuts': total_cuts,
        'cuts_per_minute': (total_cuts / video_duration) * 60 if video_duration > 0 else 0,
        'avg_shot_duration_sec': avg_shot_duration,
        'median_shot_duration_sec': median_shot_duration,
        'min_shot_duration_sec': min_shot,
        'max_shot_duration_sec': max_shot,
        'shot_durations': shot_durations,
        'pacing_distribution': {
            'intro_cuts': len(intro_cuts),
            'intro_cuts_per_min': intro_cpm,
            'body_cuts': len(body_cuts),
            'body_cuts_per_min': body_cpm,
            'outro_cuts': len(outro_cuts),
            'outro_cuts_per_min': outro_cpm,
        },
        'cut_times': cut_times,
    }


def correlate_cuts_with_script(cut_times, transcript_data, curiosity_gaps, hooks):
    """
    Find patterns: when do cuts happen relative to script moments?

    Analyzes:
    - Cuts near curiosity gap triggers
    - Cuts near re-engagement hooks
    - Cut clustering during high-tension moments
    """

    if not cut_times or not transcript_data.get('words'):
        return {}

    words = transcript_data['words']

    # Find cuts near curiosity gaps (within ±2 seconds)
    cuts_near_gaps = 0
    if curiosity_gaps:
        for gap in curiosity_gaps:
            gap_time = gap.get('trigger_time', 0)
            # Check if any cut within 2 seconds
            if any(abs(c - gap_time) < 2.0 for c in cut_times):
                cuts_near_gaps += 1

    # Find cuts near hooks
    cuts_near_hooks = 0
    if hooks:
        for hook in hooks:
            hook_time = hook.get('time', 0) if isinstance(hook, dict) else 0
            if any(abs(c - hook_time) < 2.0 for c in cut_times):
                cuts_near_hooks += 1

    # Analyze cut density over time (30-second windows)
    window_size = 30
    video_duration = words[-1]['end'] if words else 0
    cut_density_timeline = []

    for start in range(0, int(video_duration), window_size):
        end = start + window_size
        cuts_in_window = sum(1 for c in cut_times if start <= c < end)
        cut_density_timeline.append({
            'time': start,
            'cuts_in_30sec': cuts_in_window,
            'cuts_per_min': cuts_in_window * 2,  # 30sec * 2 = 60sec
        })

    # Find peak cut density
    if cut_density_timeline:
        peak_window = max(cut_density_timeline, key=lambda x: x['cuts_in_30sec'])
    else:
        peak_window = None

    return {
        'cuts_near_curiosity_gaps': cuts_near_gaps,
        'pct_gaps_with_nearby_cuts': (cuts_near_gaps / len(curiosity_gaps) * 100) if curiosity_gaps else 0,
        'cuts_near_hooks': cuts_near_hooks,
        'pct_hooks_with_nearby_cuts': (cuts_near_hooks / len(hooks) * 100) if hooks else 0,
        'cut_density_timeline': cut_density_timeline,
        'peak_cut_density': peak_window,
    }


# ============================================================================
# MAIN ANALYZER
# ============================================================================

def analyze_video_visuals(video_id, base_dir='/home/user/youtube-automation'):
    """Run complete visual analysis on a Fern video"""

    base_path = Path(base_dir)
    video_dir = base_path / 'analysis' / 'fern' / video_id

    if not video_dir.exists():
        print(f"❌ Video directory not found: {video_dir}")
        return None

    # Check for video file
    video_file = video_dir / 'video.mp4'
    if not video_file.exists():
        print(f"❌ Video file not found: {video_file}")
        return None

    # Load metadata
    info_file = video_dir / 'video.info.json'
    if not info_file.exists():
        print(f"❌ Metadata not found: {info_file}")
        return None

    with open(info_file) as f:
        info = json.load(f)

    title = info.get('title', 'Unknown')
    views = info.get('view_count', 0)
    duration = info.get('duration', 0)

    print(f"\n{'='*70}")
    print(f"  VISUAL ANALYSIS: {title}")
    print(f"  Views: {views:,} | Duration: {duration//60}:{duration%60:02d}")
    print(f"{'='*70}\n")

    # Get actual video duration
    actual_duration = get_video_duration(video_file)
    if actual_duration:
        duration = actual_duration

    # Detect cuts
    cut_times = detect_cuts(video_file, threshold=0.3)

    if not cut_times:
        print("  ⚠️  No cuts detected - trying lower threshold...")
        cut_times = detect_cuts(video_file, threshold=0.2)

    if not cut_times:
        print("  ❌ Cut detection failed")
        return None

    # Analyze cuts
    cut_analysis = analyze_cuts(cut_times, duration)

    print(f"\n  CUT ANALYSIS:")
    print(f"    Total cuts: {cut_analysis['total_cuts']}")
    print(f"    Avg shot duration: {cut_analysis['avg_shot_duration_sec']:.2f} sec")
    print(f"    Median shot duration: {cut_analysis['median_shot_duration_sec']:.2f} sec")
    print(f"    Cuts per minute: {cut_analysis['cuts_per_minute']:.1f}")
    print(f"\n  PACING:")
    pd = cut_analysis['pacing_distribution']
    print(f"    Intro: {pd['intro_cuts_per_min']:.1f} cuts/min")
    print(f"    Body: {pd['body_cuts_per_min']:.1f} cuts/min")
    print(f"    Outro: {pd['outro_cuts_per_min']:.1f} cuts/min")

    # Try to load transcript and correlate
    transcript_data = None
    curiosity_gaps = []
    hooks = []

    # Check if we have transcript analysis
    formula_file = base_path / 'analysis' / 'fern' / 'FERN_FORMULA.json'
    if formula_file.exists():
        with open(formula_file) as f:
            formula = json.load(f)

        # Find this video's data
        for v in formula.get('per_video_data', []):
            if v['id'] == video_id:
                curiosity_gaps = v.get('curiosity_gaps', {}).get('gaps', [])
                # Extract hook times from script analysis
                script_analysis = v.get('script_analysis', {})
                reengagement = script_analysis.get('reengagement', {})
                hooks = reengagement.get('hooks', [])
                break

    # Correlate with script
    correlation = correlate_cuts_with_script(cut_times, {'words': []}, curiosity_gaps, hooks)

    print(f"\n  SCRIPT CORRELATION:")
    print(f"    {correlation['pct_gaps_with_nearby_cuts']:.0f}% of curiosity gaps have cuts within 2sec")
    if correlation['peak_cut_density']:
        peak = correlation['peak_cut_density']
        print(f"    Peak cut density: {peak['cuts_per_min']:.1f} cuts/min at {peak['time']}s")

    # Save results
    result = {
        'video_id': video_id,
        'title': title,
        'views': views,
        'duration': duration,
        'cut_analysis': cut_analysis,
        'script_correlation': correlation,
    }

    output_file = video_dir / 'visual_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n  ✓ Saved: {output_file}")

    return result


def analyze_all_videos(base_dir='/home/user/youtube-automation'):
    """Analyze all Fern videos that have video.mp4 files"""

    base_path = Path(base_dir)
    fern_dir = base_path / 'analysis' / 'fern'

    if not fern_dir.exists():
        print(f"❌ Fern directory not found: {fern_dir}")
        return

    # Find all video directories with video.mp4
    video_dirs = []
    for d in fern_dir.iterdir():
        if d.is_dir() and (d / 'video.mp4').exists():
            video_dirs.append(d.name)

    if not video_dirs:
        print("❌ No videos found with video.mp4")
        return

    print(f"\n{'='*70}")
    print(f"  BATCH VISUAL ANALYSIS - {len(video_dirs)} videos")
    print(f"{'='*70}")

    results = []
    for i, video_id in enumerate(video_dirs, 1):
        print(f"\n[{i}/{len(video_dirs)}] Analyzing {video_id}...")
        result = analyze_video_visuals(video_id, base_dir)
        if result:
            results.append(result)

    # Aggregate patterns
    if results:
        print(f"\n{'='*70}")
        print(f"  VISUAL FORMULA - Aggregated from {len(results)} videos")
        print(f"{'='*70}\n")

        avg_shot_duration = statistics.mean([r['cut_analysis']['avg_shot_duration_sec'] for r in results])
        avg_cuts_per_min = statistics.mean([r['cut_analysis']['cuts_per_minute'] for r in results])

        intro_cpms = [r['cut_analysis']['pacing_distribution']['intro_cuts_per_min'] for r in results]
        body_cpms = [r['cut_analysis']['pacing_distribution']['body_cuts_per_min'] for r in results]
        outro_cpms = [r['cut_analysis']['pacing_distribution']['outro_cuts_per_min'] for r in results]

        print(f"  AVERAGE PACING:")
        print(f"    Shot duration: {avg_shot_duration:.2f} sec")
        print(f"    Cuts per minute: {avg_cuts_per_min:.1f}")
        print(f"\n  PACING BY SECTION:")
        print(f"    Intro: {statistics.mean(intro_cpms):.1f} cuts/min")
        print(f"    Body: {statistics.mean(body_cpms):.1f} cuts/min")
        print(f"    Outro: {statistics.mean(outro_cpms):.1f} cuts/min")

        # Save aggregated formula
        visual_formula = {
            'videos_analyzed': len(results),
            'avg_shot_duration_sec': avg_shot_duration,
            'avg_cuts_per_minute': avg_cuts_per_min,
            'pacing_by_section': {
                'intro_cuts_per_min': statistics.mean(intro_cpms),
                'body_cuts_per_min': statistics.mean(body_cpms),
                'outro_cuts_per_min': statistics.mean(outro_cpms),
            },
            'per_video_results': results,
        }

        output_file = fern_dir / 'VISUAL_FORMULA.json'
        with open(output_file, 'w') as f:
            json.dump(visual_formula, f, indent=2)

        print(f"\n  ✓ Saved aggregated formula: {output_file}\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nQuick start:")
        print("  python analyze_fern_visual.py wLFY_Zu_O08")
        print("  python analyze_fern_visual.py --all")
        return

    if sys.argv[1] == '--all':
        analyze_all_videos()
    else:
        video_id = sys.argv[1]
        analyze_video_visuals(video_id)


if __name__ == '__main__':
    main()
