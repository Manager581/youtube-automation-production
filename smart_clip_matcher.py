#!/usr/bin/env python3
"""
Smart Clip Matcher — Matches narration sentences to the best clip moments
using transcript text similarity and natural speech boundaries.

For each narration segment:
1. Find the source clip assigned by editorial map
2. Search that clip's transcript for the passage most relevant to the narration
3. Snap to natural speech boundaries (sentence ends, pauses)
4. Output precise start_sec/end_sec for each segment
"""
import json
import os
import re
from pathlib import Path
from collections import defaultdict

TRANS_DIR = Path(os.path.expanduser("~/Documents/youtube-automation-production/clip_transcripts"))
EDIT_MAP = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map.json"))

# Map clip filenames to transcript filenames
def clip_to_transcript_name(clip_name):
    """Convert clip filename to transcript filename format."""
    name = clip_name.replace(".mp4", "")
    name = name.replace(" ", "_").replace("：", "").replace("＂", "")
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    return name[:50]

def text_similarity(text1, text2):
    """Simple word overlap similarity score."""
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    if not words1 or not words2:
        return 0
    overlap = words1 & words2
    return len(overlap) / min(len(words1), len(words2))

def find_best_match(narration_text, transcript_segments, target_duration=8.0, used_ranges=None):
    """
    Find the transcript passage that best matches the narration text.
    Returns (start_sec, end_sec) snapped to natural speech boundaries.
    """
    if not transcript_segments:
        return 0, target_duration
    
    narration_keywords = set(re.findall(r'\w+', narration_text.lower()))
    # Remove common words
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
                 'could', 'should', 'may', 'might', 'can', 'shall', 'to', 'of',
                 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'that', 'this',
                 'it', 'not', 'but', 'and', 'or', 'if', 'so', 'as', 'you', 'your',
                 'they', 'them', 'their', 'we', 'our', 'he', 'she', 'his', 'her'}
    narration_keywords -= stopwords
    
    best_score = -1
    best_start = 0
    best_end = target_duration
    
    # Sliding window over transcript segments
    for i in range(len(transcript_segments)):
        # Build a window of consecutive segments
        window_text = ""
        window_end_idx = i
        
        for j in range(i, min(i + 5, len(transcript_segments))):
            window_text += " " + transcript_segments[j]["text"]
            window_end_idx = j
            
            window_dur = transcript_segments[j]["end"] - transcript_segments[i]["start"]
            if window_dur >= target_duration * 0.5:
                # Score this window
                window_words = set(re.findall(r'\w+', window_text.lower())) - stopwords
                if not window_words:
                    continue
                overlap = narration_keywords & window_words
                score = len(overlap) / max(len(narration_keywords), 1)
                
                # Bonus for matching key entities
                entity_bonus = 0
                key_entities = ['score', 'algorithm', 'data', 'denied', 'rejected',
                               'insurance', 'screening', 'tenant', 'landlord', 'broker',
                               'lexisnexis', 'saferent', 'cigna', 'realpage', 'hiring',
                               'discriminat', 'bias', 'privacy', 'surveillance', 'tracking']
                for entity in key_entities:
                    if entity in window_text.lower() and entity in narration_text.lower():
                        entity_bonus += 0.3
                
                score += entity_bonus
                
                # Penalty for overlapping with already-used ranges
                start = transcript_segments[i]["start"]
                end = transcript_segments[window_end_idx]["end"]
                if used_ranges:
                    for us, ue in used_ranges:
                        if start < ue and end > us:  # Overlap
                            score *= 0.3  # Heavy penalty
                
                if score > best_score:
                    best_score = score
                    best_start = transcript_segments[i]["start"]
                    best_end = transcript_segments[window_end_idx]["end"]
                
                if window_dur >= target_duration:
                    break
    
    # Ensure minimum duration
    if best_end - best_start < 3:
        best_end = best_start + target_duration
    
    return round(best_start, 1), round(best_end, 1)


def main():
    print("=== Smart Clip Matcher ===\n")
    
    # Load editorial map
    with open(EDIT_MAP) as f:
        edit_data = json.load(f)
    segments = edit_data["segments"]
    
    # Load all transcripts
    transcripts = {}
    for tf in TRANS_DIR.glob("*.json"):
        with open(tf) as f:
            data = json.load(f)
        transcripts[tf.stem] = data.get("segments", [])
    
    print(f"Loaded {len(transcripts)} transcripts")
    print(f"Processing {len(segments)} editorial segments\n")
    
    # Track used ranges per clip to avoid visual repetition
    used_ranges = defaultdict(list)
    
    # Match each segment
    updated_segments = []
    for seg in segments:
        clip_name = seg["source_clip"]
        trans_name = clip_to_transcript_name(clip_name)
        
        # Find matching transcript
        trans_segs = None
        for tname, tsegs in transcripts.items():
            if tname.startswith(trans_name[:20]) or trans_name.startswith(tname[:20]):
                trans_segs = tsegs
                break
        
        if trans_segs is None:
            # Try fuzzy match
            for tname, tsegs in transcripts.items():
                clip_words = set(trans_name.lower().split('_')[:3])
                tname_words = set(tname.lower().split('_')[:3])
                if clip_words & tname_words:
                    trans_segs = tsegs
                    break
        
        if trans_segs:
            narration = seg.get("narration_text_snippet", "")
            target_dur = seg["clip_end_sec"] - seg["clip_start_sec"]
            
            start, end = find_best_match(
                narration, trans_segs, 
                target_duration=max(target_dur, 6),
                used_ranges=used_ranges.get(clip_name)
            )
            
            # Clamp to clip duration
            clip_max = trans_segs[-1]["end"] if trans_segs else 600
            start = min(start, max(0, clip_max - 5))
            end = min(end, clip_max)
            
            used_ranges[clip_name].append((start, end))
            
            old_start = seg["clip_start_sec"]
            old_end = seg["clip_end_sec"]
            seg["clip_start_sec"] = start
            seg["clip_end_sec"] = end
            seg["match_method"] = "transcript_similarity"
            
            if seg["seg_id"] < 10 or seg["seg_id"] % 15 == 0:
                print(f"SEG {seg['seg_id']:02d}: {old_start}-{old_end}s → {start}-{end}s")
                print(f"  Narration: {narration[:60]}")
                if trans_segs:
                    # Show what the clip says at the matched time
                    matched_text = ""
                    for ts in trans_segs:
                        if ts["start"] >= start and ts["end"] <= end + 2:
                            matched_text += ts["text"] + " "
                    print(f"  Clip says: {matched_text[:80]}")
                print()
        else:
            seg["match_method"] = "no_transcript"
            if seg["seg_id"] < 10:
                print(f"SEG {seg['seg_id']:02d}: NO TRANSCRIPT for {clip_name[:40]}")
        
        updated_segments.append(seg)
    
    # Save updated map
    edit_data["segments"] = updated_segments
    edit_data["match_version"] = "smart_v1"
    
    output_path = Path(os.path.expanduser("~/Documents/youtube-automation-production/editorial_clip_map_v2.json"))
    with open(output_path, "w") as f:
        json.dump(edit_data, f, indent=2)
    
    matched = sum(1 for s in updated_segments if s.get("match_method") == "transcript_similarity")
    print(f"\n=== Results ===")
    print(f"Transcript-matched: {matched}/{len(updated_segments)}")
    print(f"Output: {output_path}")

if __name__ == "__main__":
    main()
