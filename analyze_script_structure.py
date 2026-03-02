#!/usr/bin/env python3
"""
Fern Script Structure Analyzer — no API, pure regex/math.
Extracts: curiosity gap timing, act lengths, sponsor slot, sentence rhythm.
"""
import json, re
from pathlib import Path
from collections import Counter

FERN_DIR = Path("analysis/fern")
VIDEO_IDS = ["aVA7aXOH1pk", "wLFY_Zu_O08", "wkVygetgeRY"]
VIDEO_NAMES = {
    "aVA7aXOH1pk": "Trump_Assassination",
    "wLFY_Zu_O08": "FBI_KKK",
    "wkVygetgeRY": "Unabomber",
}

def ts_to_sec(ts):
    parts = ts.strip("[]").split(":")
    return int(parts[0]) * 60 + float(parts[1])

def load_clean_script(vid):
    path = FERN_DIR / f"{vid}_script_clean.txt"
    segs = []
    for line in path.read_text().splitlines():
        m = re.match(r'\[(\d+:\d+\.\d+)\]\s*(.*)', line)
        if m:
            segs.append({"start": ts_to_sec(m.group(1)), "text": m.group(2).strip()})
    return segs

def analyze(vid, segs):
    name = VIDEO_NAMES[vid]
    total = segs[-1]["start"] if segs else 0
    full_text = " ".join(s["text"] for s in segs)
    words = full_text.split()
    wpm = round(len(words) / (total / 60)) if total else 0

    # ── SENTENCE RHYTHM ─────────────────────────────────────────
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    lens = [len(s.split()) for s in sentences if s.strip()]
    avg_len = round(sum(lens) / len(lens)) if lens else 0
    short = sum(1 for l in lens if l <= 5)
    short_pct = round(short / len(lens) * 100) if lens else 0

    # ── OPENING HOOK ────────────────────────────────────────────
    hook_segs = [s for s in segs if s["start"] < 90]
    hook_text = " ".join(s["text"] for s in hook_segs)
    hook_words = len(hook_text.split())

    # ── CURIOSITY GAPS (unanswered questions / tension phrases) ──
    gap_triggers = [
        r"\bbut\b.*\?",
        r"what (they|he|she|nobody) didn.t know",
        r"what (they|he|she|nobody) (knew|know)",
        r"(except|but here.s|turns out|little did|unknown to|despite)",
        r"why (would|did|does) (he|she|they|it|this)",
        r"\?$",
    ]
    gaps = []
    for seg in segs:
        t = seg["text"].lower()
        for pat in gap_triggers:
            if re.search(pat, t):
                gaps.append({"time": seg["start"], "time_pct": round(seg["start"]/total*100) if total else 0, "text": seg["text"][:80]})
                break

    # ── SPONSOR SLOT ─────────────────────────────────────────────
    sponsor_triggers = ["sponsor", "brought to you", "use code", "discount", "sign up", "download the app", "free trial", "promo code"]
    sponsor = None
    for seg in segs:
        if any(t in seg["text"].lower() for t in sponsor_triggers):
            sponsor = {"time": seg["start"], "time_pct": round(seg["start"]/total*100) if total else 0, "text": seg["text"][:60]}
            break

    # ── ACT STRUCTURE ─────────────────────────────────────────────
    # Act 1: hook (0–15% of video)
    # Act 2: backstory/buildup (15–65%)
    # Act 3: climax/resolution (65–90%)
    # Outro: CTA (90–100%)
    def act_text(pct_start, pct_end):
        s = total * pct_start / 100
        e = total * pct_end / 100
        act_segs = [x for x in segs if s <= x["start"] < e]
        return " ".join(x["text"] for x in act_segs[:3])[:150]

    # ── OPENING PATTERNS ─────────────────────────────────────────
    first_line = segs[0]["text"] if segs else ""
    opens_with_quote = first_line.startswith('"') or first_line.startswith("'") or "motive" in first_line.lower() or "snitches" in first_line.lower()
    opens_with_date = bool(re.search(r"^\w+ \d+,? \d{4}", first_line))
    opens_with_location = bool(re.search(r"(lincoln|alabama|butler|montana|chicago|new york|washington)", first_line.lower()))

    # ── WORD PATTERNS ─────────────────────────────────────────────
    all_words = re.findall(r'\b[a-z]+\b', full_text.lower())
    word_freq = Counter(all_words)
    # Remove stop words
    stops = {"the","a","an","and","or","but","in","on","at","to","for","of","with","his","her","their","he","she","they","it","is","was","are","were","be","been","has","have","had","that","this","from","by","as","at","not","all","we","our","you","i","my","me","him","them","who","what","when","where","how","why","which","so","if","its","into","than","then","just","one","out","up","would","could","will","did","do","does","more","most","about","over","also","some","been","can","after","said","here","there","been","very","get","got","back","even","only","know","time","went","any","each","other","first","last","new","still","way","us","too","now","go","no","yes","take","made","make","see","look","like","down","two","three","four","five","many","well","your","their","may","again","off","before","through","between","these","those","both","few","came","come","people","years","year"}
    content_words = [(w, c) for w, c in word_freq.most_common(30) if w not in stops and len(w) > 3]

    return {
        "video":          name,
        "duration_sec":   round(total),
        "total_words":    len(words),
        "wpm":            wpm,
        "sentence_rhythm": {
            "avg_words_per_sentence": avg_len,
            "short_sentences_pct":    short_pct,
            "note": "Short sentences (<= 5 words) create punch/rhythm"
        },
        "hook": {
            "first_line":           first_line[:100],
            "opens_with_quote":     opens_with_quote,
            "opens_with_date":      opens_with_date,
            "opens_with_location":  opens_with_location,
            "hook_word_count":      hook_words,
            "hook_text":            hook_text[:300],
        },
        "curiosity_gaps": {
            "count":   len(gaps),
            "gaps":    gaps[:8],
            "first_gap_at_sec": gaps[0]["time"] if gaps else None,
            "first_gap_pct":    gaps[0]["time_pct"] if gaps else None,
        },
        "sponsor": sponsor,
        "act_structure": {
            "act1_hook_0_15pct":      act_text(0, 15),
            "act2_buildup_15_65pct":  act_text(15, 65),
            "act3_climax_65_90pct":   act_text(65, 90),
            "outro_90_100pct":        act_text(90, 100),
        },
        "top_content_words": content_words[:15],
    }


if __name__ == "__main__":
    results = []
    for vid in VIDEO_IDS:
        path = FERN_DIR / f"{vid}_script_clean.txt"
        if not path.exists():
            print(f"[SKIP] {vid} — no clean script")
            continue

        segs = load_clean_script(vid)
        if not segs:
            print(f"[SKIP] {vid} — empty")
            continue

        print(f"\n{'='*60}")
        r = analyze(vid, segs)
        results.append(r)

        print(f"{r['video']}  ({r['duration_sec']}s  {r['wpm']} WPM)")
        print(f"  Sentence rhythm: avg {r['sentence_rhythm']['avg_words_per_sentence']} words, {r['sentence_rhythm']['short_sentences_pct']}% short (<= 5w)")
        print(f"  Hook opens with quote: {r['hook']['opens_with_quote']}")
        print(f"  First line: \"{r['hook']['first_line']}\"")
        print(f"  Curiosity gaps: {r['curiosity_gaps']['count']} found")
        if r['curiosity_gaps']['first_gap_at_sec']:
            print(f"  First gap at: {r['curiosity_gaps']['first_gap_at_sec']:.0f}s ({r['curiosity_gaps']['first_gap_pct']}% in)")
        for g in r['curiosity_gaps']['gaps'][:3]:
            print(f"    [{g['time']:.0f}s / {g['time_pct']}%] \"{g['text']}\"")
        if r['sponsor']:
            print(f"  Sponsor at: {r['sponsor']['time']:.0f}s ({r['sponsor']['time_pct']}%)")
        print(f"  Top words: {[w for w, _ in r['top_content_words'][:8]]}")

    # Cross-video summary
    if results:
        print(f"\n{'='*60}")
        print("CROSS-VIDEO FORMULA")
        print(f"{'='*60}")
        avg_wpm = round(sum(r['wpm'] for r in results) / len(results))
        avg_sent = round(sum(r['sentence_rhythm']['avg_words_per_sentence'] for r in results) / len(results))
        avg_short = round(sum(r['sentence_rhythm']['short_sentences_pct'] for r in results) / len(results))
        gap_pcts = [r['curiosity_gaps']['first_gap_pct'] for r in results if r['curiosity_gaps']['first_gap_pct']]
        avg_gap = round(sum(gap_pcts) / len(gap_pcts)) if gap_pcts else None
        sponsor_pcts = [r['sponsor']['time_pct'] for r in results if r['sponsor']]
        avg_sponsor = round(sum(sponsor_pcts) / len(sponsor_pcts)) if sponsor_pcts else None

        print(f"  Narration WPM:       {avg_wpm}")
        print(f"  Avg sentence length: {avg_sent} words")
        print(f"  Short sentences:     {avg_short}%")
        print(f"  First curiosity gap: ~{avg_gap}% into video" if avg_gap else "  First gap: varies")
        print(f"  Sponsor placement:   ~{avg_sponsor}% into video" if avg_sponsor else "  No sponsors detected")

    out = FERN_DIR / "SCRIPT_STRUCTURE_FORMULA.json"
    with open(out, "w") as f:
        json.dump({"videos": results}, f, indent=2)
    print(f"\nSaved: {out}")
