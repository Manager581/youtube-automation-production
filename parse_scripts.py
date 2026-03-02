#!/usr/bin/env python3
"""
Parse Fern VTT files into clean timestamped scripts.
Outputs both clean text files and structured JSON for analysis.
"""

import re
import json
from pathlib import Path

FERN_DIR = Path("analysis/fern")
VIDEO_IDS = ["aVA7aXOH1pk", "wLFY_Zu_O08", "wkVygetgeRY"]
VIDEO_NAMES = {
    "aVA7aXOH1pk": "Trump_Assassination_Attempt",
    "wLFY_Zu_O08": "FBI_Undercover_KKK",
    "wkVygetgeRY": "Unabomber",
}

def parse_vtt(path):
    """
    Parse VTT into clean timestamped segments.

    Fern's VTTs use incremental word-by-word accumulation:
      Block A: "it's the 13th"
      Block B: "it's the 13th of July"   ← B supersedes A
      Block C: "it's the 13th of July in Butler"   ← C supersedes B

    Strategy: only keep a block if the NEXT block does NOT start with it
    (i.e. it's the final/longest version of that caption line).
    """
    raw = Path(path).read_text(encoding="utf-8")

    # Strip word-level timing tags
    raw = re.sub(r'<\d+:\d+:\d+\.\d+>', '', raw)
    raw = re.sub(r'</?c>', '', raw)
    raw = re.sub(r'<[^>]+>', '', raw)

    # Parse all blocks
    all_blocks = []
    for block in re.split(r'\n\n+', raw.strip()):
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
        time_line = next((l for l in lines if '-->' in l), None)
        if not time_line:
            continue
        m = re.match(r'(\d+:\d+:\d+\.\d+)\s*-->\s*(\d+:\d+:\d+\.\d+)', time_line)
        if not m:
            continue
        start = ts_to_sec(m.group(1))
        end   = ts_to_sec(m.group(2))
        idx   = lines.index(time_line)
        content = " ".join(lines[idx+1:]).strip()
        content = re.sub(r'^>>\s*', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        if content:
            all_blocks.append({"start": start, "end": end, "text": content})

    if not all_blocks:
        return []

    # Fern's VTTs use 0.010s "separator" blocks to mark the final complete
    # text of each displayed caption line. These have end - start == 0.01s.
    # Only keep those — they contain clean, non-duplicated text.
    kept = [b for b in all_blocks if round(b["end"] - b["start"], 3) == 0.01]

    # Fallback: if no separator blocks found, keep all and deduplicate
    if len(kept) < 5:
        seen = set()
        kept = []
        for b in all_blocks:
            key = b["text"].strip().lower()
            if key not in seen:
                seen.add(key)
                kept.append(b)

    # Merge consecutive kept blocks that are close in time into sentences
    merged = []
    current = None
    for blk in kept:
        if current is None:
            current = dict(blk)
        else:
            gap = blk["start"] - current["end"]
            if gap < 1.5:
                current["text"] += " " + blk["text"]
                current["end"] = blk["end"]
            else:
                merged.append(current)
                current = dict(blk)
    if current:
        merged.append(current)

    # Final cleanup
    cleaned = []
    for s in merged:
        t = re.sub(r'\s+', ' ', s["text"]).strip()
        if len(t) > 5:
            cleaned.append({"start": s["start"], "end": s["end"], "text": t})

    return cleaned


def ts_to_sec(ts):
    parts = ts.split(':')
    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s


def sec_to_ts(sec):
    m = int(sec // 60)
    s = sec % 60
    return f"{m:02d}:{s:05.2f}"


def to_plain_text(segments):
    return " ".join(s["text"] for s in segments)


def analyze_structure(segments, video_name):
    """Identify structural markers in the script."""
    full_text = to_plain_text(segments)
    words = full_text.split()
    total_duration = segments[-1]["end"] if segments else 0

    # Opening line (first 25 words)
    opening = " ".join(words[:25])

    # Find first question (curiosity gap)
    first_question = None
    first_q_time = None
    for seg in segments:
        if "?" in seg["text"]:
            first_question = seg["text"]
            first_q_time = seg["start"]
            break

    # Find "what they don't know" / reveal phrases
    reveal_phrases = [
        "what they don't know", "what he didn't know", "what nobody knew",
        "but here's the thing", "but what", "the truth is", "in reality",
        "the real reason", "it turns out", "little did", "unknown to",
        "but unknown", "except", "however",
    ]
    reveals = []
    for seg in segments:
        t = seg["text"].lower()
        for phrase in reveal_phrases:
            if phrase in t:
                reveals.append({"time": seg["start"], "text": seg["text"], "trigger": phrase})
                break

    # Find superlatives / stakes language
    stakes_words = [
        "largest", "biggest", "most", "greatest", "worst", "deadliest",
        "first ever", "history's", "never before", "unprecedented",
        "million", "billion", "years", "decades", "17 years", "longest",
    ]
    stakes = []
    for seg in segments:
        t = seg["text"].lower()
        for w in stakes_words:
            if w in t:
                stakes.append({"time": seg["start"], "text": seg["text"]})
                break

    # Structural acts — divide into thirds
    act1_end = total_duration * 0.25
    act2_end = total_duration * 0.65

    act1 = [s for s in segments if s["end"] <= act1_end]
    act2 = [s for s in segments if s["start"] >= act1_end and s["end"] <= act2_end]
    act3 = [s for s in segments if s["start"] >= act2_end]

    # WPM calculation
    total_words = len(words)
    wpm = round(total_words / (total_duration / 60)) if total_duration else 0

    # Sentence length distribution
    sentence_texts = re.split(r'[.!?]+', full_text)
    sentence_lengths = [len(s.split()) for s in sentence_texts if s.strip()]
    avg_sentence_len = round(sum(sentence_lengths) / len(sentence_lengths)) if sentence_lengths else 0

    # Opening hook — first 30 seconds
    hook_segs = [s for s in segments if s["start"] < 30]
    hook_text = " ".join(s["text"] for s in hook_segs)

    # Find name/person intro
    intro_pattern = re.search(
        r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)[,.]?\s+(?:more commonly known as|known as|also known|nicknamed|alias)',
        full_text
    )

    # Key character name
    character = intro_pattern.group(1) if intro_pattern else None

    return {
        "video": video_name,
        "total_duration_sec": round(total_duration),
        "total_words": total_words,
        "wpm": wpm,
        "avg_sentence_words": avg_sentence_len,
        "opening_25_words": opening,
        "hook_first_30s": hook_text,
        "first_question": {"time": sec_to_ts(first_q_time) if first_q_time else None, "text": first_question},
        "main_character": character,
        "reveal_moments": [{"time": sec_to_ts(r["time"]), "text": r["text"][:100], "trigger": r["trigger"]} for r in reveals[:8]],
        "stakes_moments": [{"time": sec_to_ts(s["time"]), "text": s["text"][:100]} for s in stakes[:8]],
        "act_structure": {
            "act1_hook": {"duration_sec": round(act1_end), "summary": " ".join(s["text"] for s in act1[:3])[:200]},
            "act2_buildup": {"start_sec": round(act1_end), "end_sec": round(act2_end), "summary": " ".join(s["text"] for s in act2[:3])[:200]},
            "act3_climax": {"start_sec": round(act2_end), "summary": " ".join(s["text"] for s in act3[:3])[:200]},
        },
    }


if __name__ == "__main__":
    all_analyses = []

    for vid_id in VIDEO_IDS:
        name = VIDEO_NAMES[vid_id]
        vtt_path = FERN_DIR / vid_id / "video.en.vtt"

        if not vtt_path.exists():
            print(f"[SKIP] {vid_id} — no VTT file")
            continue

        print(f"\nParsing {name} ({vid_id})...")
        segments = parse_vtt(vtt_path)
        print(f"  {len(segments)} segments parsed")

        # Save clean script
        clean_path = FERN_DIR / f"{vid_id}_script_clean.txt"
        with open(clean_path, "w") as f:
            for seg in segments:
                f.write(f"[{sec_to_ts(seg['start'])}] {seg['text']}\n")
        print(f"  Saved: {clean_path}")

        # Analyze
        analysis = analyze_structure(segments, name)
        all_analyses.append(analysis)

        # Print key findings
        print(f"\n  === {name} ===")
        print(f"  Duration: {analysis['total_duration_sec']}s | Words: {analysis['total_words']} | WPM: {analysis['wpm']}")
        print(f"  Avg sentence: {analysis['avg_sentence_words']} words")
        print(f"\n  OPENING 25 WORDS:")
        print(f"  \"{analysis['opening_25_words']}\"")
        print(f"\n  HOOK (first 30s):")
        print(f"  {analysis['hook_first_30s'][:300]}")
        print(f"\n  FIRST QUESTION at {analysis['first_question']['time']}:")
        print(f"  \"{analysis['first_question']['text']}\"")
        if analysis['main_character']:
            print(f"\n  MAIN CHARACTER: {analysis['main_character']}")
        print(f"\n  REVEAL MOMENTS ({len(analysis['reveal_moments'])}):")
        for r in analysis['reveal_moments'][:4]:
            print(f"    [{r['time']}] \"{r['text'][:80]}\"  (trigger: '{r['trigger']}')")
        print(f"\n  STAKES ({len(analysis['stakes_moments'])}):")
        for s in analysis['stakes_moments'][:4]:
            print(f"    [{s['time']}] \"{s['text'][:80]}\"")

    # Save combined formula
    out = FERN_DIR / "SCRIPT_FORMULA.json"
    with open(out, "w") as f:
        json.dump({"scripts": all_analyses}, f, indent=2)
    print(f"\n\nSaved: {out}")
