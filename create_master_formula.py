#!/usr/bin/env python3
"""Aggregate all Fern analysis into master production formula"""
import json
from pathlib import Path
from collections import Counter

def load_audio_analyses():
    """Load all audio analysis files"""
    audio_files = Path('analysis/fern').glob('*_audio_analysis.json')
    analyses = []
    
    for file in audio_files:
        with open(file) as f:
            analyses.append(json.load(f))
    
    return analyses

def load_visual_analyses():
    """Load all visual timeline files"""
    timeline_files = Path('analysis/fern').glob('*/timeline_hybrid_*.json')
    analyses = []
    
    for file in timeline_files:
        with open(file) as f:
            data = json.load(f)
        # Only include complete analyses
        if data.get('complete') and len(data.get('timeline', [])) > 0:
            analyses.append(data)
        else:
            print(f"  Skipping incomplete: {file.name} ({len(data.get('timeline',[]))} frames)")
    
    return analyses

def aggregate_audio_patterns(audio_analyses):
    """Aggregate audio patterns across all videos"""
    total_videos = len(audio_analyses)
    
    # Music patterns
    bpms = [a['music']['bpm'] for a in audio_analyses if 'music' in a]
    avg_bpm = sum(bpms) / len(bpms) if bpms else 0
    
    # Voice patterns
    wpms = [a['voice']['overall_wpm'] for a in audio_analyses if 'voice' in a and a['voice']]
    avg_wpm = sum(wpms) / len(wpms) if wpms else 0
    
    # Energy patterns
    energy_data = []
    for a in audio_analyses:
        if 'energy' in a and 'avg_energy' in a['energy']:
            energy_data.append(a['energy']['avg_energy'])
    avg_energy = sum(energy_data) / len(energy_data) if energy_data else 0
    
    return {
        'videos_analyzed': total_videos,
        'music': {
            'avg_bpm': avg_bpm,
            'bpm_range': [min(bpms), max(bpms)] if bpms else [0, 0]
        },
        'voice': {
            'avg_wpm': avg_wpm,
            'wpm_range': [min(wpms), max(wpms)] if wpms else [0, 0]
        },
        'energy': {
            'avg_energy': avg_energy
        }
    }

def aggregate_visual_patterns(visual_analyses):
    """Aggregate visual patterns across all videos"""
    total_videos = len(visual_analyses)
    
    footage_types = []
    camera_angles = []
    
    for analysis in visual_analyses:
        for entry in analysis.get('timeline', []):
            visual = entry.get('visual', {})
            if 'visual_category' in visual:
                footage_types.append(visual['visual_category'])
            if 'camera_angle' in visual:
                camera_angles.append(visual['camera_angle'])
    
    return {
        'videos_analyzed': total_videos,
        'total_frames_analyzed': len(footage_types),
        'footage_distribution': dict(Counter(footage_types)),
        'camera_angles': dict(Counter(camera_angles))
    }

def main():
    print("📊 Creating Fern Master Production Formula...")
    
    # Load all analyses
    audio_analyses = load_audio_analyses()
    visual_analyses = load_visual_analyses()
    
    # Load existing script formula
    with open('analysis/fern/FERN_FORMULA.json') as f:
        script_formula = json.load(f)
    
    # Aggregate patterns
    audio_formula = aggregate_audio_patterns(audio_analyses)
    visual_formula = aggregate_visual_patterns(visual_analyses)
    
    # Combine into master formula
    master_formula = {
        'metadata': {
            'channel': '@fern-tv',
            'analysis_date': __import__('datetime').date.today().isoformat(),
            'videos_complete': len(visual_analyses),
            'total_videos_with_complete_analysis': len(audio_analyses)
        },
        'script_patterns': script_formula,
        'visual_patterns': visual_formula,
        'audio_patterns': audio_formula
    }
    
    # Save master formula
    output_file = Path('analysis/fern/FERN_MASTER_FORMULA.json')
    with open(output_file, 'w') as f:
        json.dump(master_formula, f, indent=2)
    
    print(f"✅ Master formula saved: {output_file}")
    print(f"\n📈 Summary:")
    print(f"   Videos with complete analysis: {len(audio_analyses)}")
    print(f"   Total frames analyzed: {visual_formula['total_frames_analyzed']}")
    print(f"   Average BPM: {audio_formula['music']['avg_bpm']:.1f}")
    print(f"   Average WPM: {audio_formula['voice']['avg_wpm']:.1f}")
    
    # Top footage types
    print(f"\n🎬 Top Footage Types:")
    sorted_footage = sorted(visual_formula['footage_distribution'].items(), 
                           key=lambda x: -x[1])[:5]
    for ft, count in sorted_footage:
        pct = count / visual_formula['total_frames_analyzed'] * 100
        print(f"   {ft}: {pct:.1f}%")

if __name__ == '__main__':
    main()
