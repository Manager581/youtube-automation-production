#!/usr/bin/env python3
"""
Fern Script Checker
Analyzes a script draft against the proven Fern Formula benchmarks.
Shows exactly where you match and where you're off.

Usage:
    python check_fern_script.py <script_file> [title]

Examples:
    python check_fern_script.py my_script.txt
    python check_fern_script.py my_script.txt "The Secret Bunker Nobody Knows About"
    echo "paste your script" | python check_fern_script.py -

The script file should be plain text (your narration script).
"""

import json
import re
import sys
import statistics
from pathlib import Path
from collections import Counter, defaultdict

# ============================================================================
# FERN BENCHMARKS (extracted from 30-video analysis)
# ============================================================================

FERN_BENCHMARKS = {
    # Pacing
    'wpm_target': 161,
    'wpm_range': (126, 187),
    'wpm_top_performers': 168,

    # Duration
    'duration_target_min': 24.5,
    'duration_range_min': (20, 30),

    # Re-engagement hooks
    'hooks_per_min': 0.122,
    'hook_interval_sec': 492,

    # Curiosity gaps
    'gaps_per_min': 0.43,
    'gaps_per_min_top': 0.49,
    'gap_duration_sec': 39.8,

    # Emotional language
    'emotional_density_pct': 0.54,
    'emotion_ranking': ['mystery', 'fear', 'power', 'tragedy', 'triumph', 'shock'],

    # Word choice
    'you_density_pct': 0.83,
    'questions_per_1000': 1.83,
    'vocab_richness': 0.381,

    # Title
    'title_word_count': 6.3,
    'title_char_count': 37,
    'title_top_patterns': ['person_reference', 'country_reference', 'the_most', 'superlative', 'negative', 'how_x', 'why_x', 'mystery_word'],

    # Structure
    'intro_pct': 10,  # First 10% is intro
    'body_pct': 75,   # 10-85% is body
    'conclusion_pct': 15,  # Last 15%
}

# ============================================================================
# PATTERN DEFINITIONS (same as in analyze_fern_complete.py)
# ============================================================================

HOOK_PATTERNS = [
    (r'\bwhat\s+if\b', 'what_if'),
    (r'\bimagine\b', 'imagine'),
    (r'\bpicture\s+this\b', 'picture_this'),
    (r'\byou\b.*\bknow\b', 'direct_address'),
    (r'\bin\s+\d{4}\b', 'year_anchor'),
    (r'\bon\s+\w+\s+\d+', 'date_anchor'),
    (r'\bdeep\s+(inside|within|beneath)\b', 'location_reveal'),
    (r'\bhidden\b|\bsecret\b|\bmysterious\b', 'mystery_opener'),
    (r'\bno\s+one\b.*\bknew\b', 'unknown_reveal'),
    (r'\bthe\s+most\b', 'superlative_opener'),
]

REENGAGEMENT_PATTERNS = [
    (r'\bbut\b.*\bwhat\b', 'pivot_question'),
    (r'\bbut\s+then\b', 'plot_twist'),
    (r'\bhowever\b', 'contrast'),
    (r'\bwhat\s+.*\bdidn\'?t\s+know\b', 'hidden_info'),
    (r'\bhere\'?s\s+where\b.*\bgets?\b', 'escalation'),
    (r'\bthis\s+is\s+where\b', 'turning_point'),
    (r'\bsuddenly\b', 'sudden_change'),
    (r'\bbut\s+here\'?s\s+the\s+(?:thing|catch|problem)\b', 'but_heres'),
    (r'\bnow\b.*\bgets?\s+(?:interesting|crazy|wild|weird)\b', 'escalation_now'),
    (r'\blittle\s+did\b', 'dramatic_irony'),
]

CURIOSITY_QUESTION_PATTERNS = [
    r'\bwhat\s+(?:if|would|could|happened|happens)\b',
    r'\bhow\s+(?:did|does|can|could|would)\b',
    r'\bwhy\s+(?:did|does|is|are|was|were)\b',
    r'\bwhen\s+(?:did|does|will)\b',
    r'\bwhere\s+(?:did|does|is|are)\b',
    r'\bwho\s+(?:is|are|was|were|did)\b',
    r'\?',
]

CLIFFHANGER_PATTERNS = [
    r'\bbut\s+then\b',
    r'\bhowever\b',
    r'\bsuddenly\b',
    r'\bshockingly\b',
    r'\bunexpectedly\b',
    r'\bwhat\s+happened\s+next\b',
    r'\blittle\s+did\s+(?:they|he|she|anyone)\s+know\b',
    r'\bno\s+one\s+(?:knew|expected|realized)\b',
]

RESOLUTION_PATTERNS = [
    r'\bthe\s+answer\b',
    r'\bit\s+turned\s+out\b',
    r'\bthey\s+(?:found|discovered|realized)\b',
    r'\bfinally\b',
    r'\bin\s+the\s+end\b',
    r'\beventually\b',
    r'\bthe\s+truth\s+(?:was|is)\b',
]

EMOTIONAL_WORDS = {
    'fear': ['terrifying', 'horrifying', 'feared', 'panic', 'nightmare', 'deadly', 'dangerous', 'threat', 'terror', 'horror'],
    'mystery': ['mysterious', 'unknown', 'secret', 'hidden', 'strange', 'bizarre', 'enigma', 'puzzle', 'unexplained', 'cryptic'],
    'shock': ['shocking', 'unbelievable', 'incredible', 'jaw-dropping', 'mind-blowing', 'insane', 'crazy', 'unprecedented'],
    'power': ['powerful', 'dominant', 'unstoppable', 'massive', 'enormous', 'colossal', 'supreme', 'ruthless'],
    'tragedy': ['devastating', 'heartbreaking', 'tragic', 'catastrophic', 'disaster', 'destroyed', 'loss', 'death', 'killed'],
    'triumph': ['survived', 'escaped', 'overcame', 'breakthrough', 'victory', 'succeeded', 'genius', 'brilliant', 'hero'],
}

TITLE_PATTERNS = {
    'question': r'\?',
    'how_x': r'^how\b',
    'why_x': r'^why\b',
    'the_most': r'\bthe\s+most\b',
    'number': r'\b\d+\b',
    'superlative': r'\b(?:most|biggest|largest|deadliest|smartest|worst|best|greatest|fastest)\b',
    'negative': r'\b(?:didn\'?t|never|no\s+one|nobody|worst|failed|impossible|banned)\b',
    'mystery_word': r'\b(?:secret|hidden|mysterious|unknown|classified|forbidden)\b',
    'danger_word': r'\b(?:dangerous|deadly|terrifying|horrifying|shocking|scary)\b',
    'person_reference': r'\b(?:man|woman|kid|person|agent|killer|genius|hacker)\b',
    'country_reference': r'\b(?:america|russia|china|north\s+korea|japan|india|pentagon|fbi|cia|kgb)\b',
}


# ============================================================================
# SCORING FUNCTIONS
# ============================================================================

def score_metric(value, target, tolerance_pct=20, higher_better=None):
    """Score a metric against target. Returns (score 0-100, status, detail)"""
    if target == 0:
        return 50, 'NEUTRAL', 'No benchmark'

    deviation_pct = abs(value - target) / target * 100

    if deviation_pct <= tolerance_pct * 0.5:
        return 100, 'PERFECT', f'{value:.1f} vs {target:.1f} target'
    elif deviation_pct <= tolerance_pct:
        return 80, 'GOOD', f'{value:.1f} vs {target:.1f} target ({deviation_pct:.0f}% off)'
    elif deviation_pct <= tolerance_pct * 2:
        direction = 'high' if value > target else 'low'
        return 50, 'OFF', f'{value:.1f} vs {target:.1f} target ({deviation_pct:.0f}% {direction})'
    else:
        direction = 'high' if value > target else 'low'
        return 20, 'WAY OFF', f'{value:.1f} vs {target:.1f} target ({deviation_pct:.0f}% {direction})'


def score_range(value, low, high):
    """Score if value falls within range"""
    if low <= value <= high:
        return 100, 'IN RANGE', f'{value:.1f} (range: {low:.1f}-{high:.1f})'
    elif value < low:
        diff = low - value
        return max(20, 80 - int(diff / low * 100)), 'LOW', f'{value:.1f} (range: {low:.1f}-{high:.1f})'
    else:
        diff = value - high
        return max(20, 80 - int(diff / high * 100)), 'HIGH', f'{value:.1f} (range: {low:.1f}-{high:.1f})'


# ============================================================================
# MAIN CHECKER
# ============================================================================

def check_script(script_text, title=None):
    """Run full Fern Formula check on a script"""

    B = FERN_BENCHMARKS
    words = script_text.split()
    word_count = len(words)
    sentences = re.split(r'[.!?]+', script_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    text_lower = script_text.lower()

    results = {
        'scores': {},
        'overall_score': 0,
        'issues': [],
        'strengths': [],
        'suggestions': [],
    }

    print("\n" + "=" * 70)
    print("  FERN FORMULA SCRIPT CHECK")
    print("=" * 70)

    # ---- 1. PACING (WPM) ----
    # Estimate duration at Fern's pacing
    estimated_duration_min = word_count / B['wpm_target']
    estimated_wpm = B['wpm_target']  # We can't measure actual delivery, but we check word count

    # Score against the actual target (24.5 min), not just the wide range.
    score, status, detail = score_metric(estimated_duration_min, B['duration_target_min'])
    results['scores']['duration'] = {'score': score, 'status': status, 'detail': detail}

    print(f"\n--- DURATION ---")
    print(f"  Word count: {word_count:,}")
    print(f"  At 161 WPM = {estimated_duration_min:.1f} min (target: {B['duration_target_min']:.1f} min)")
    print(f"  Score: [{status}] {detail}")

    if estimated_duration_min < B['duration_range_min'][0]:
        results['issues'].append(f"Script is too short ({estimated_duration_min:.1f} min). Fern's sweet spot is {B['duration_target_min']:.0f} min. Add {int((B['duration_target_min'] - estimated_duration_min) * B['wpm_target'])} more words.")
    elif estimated_duration_min > B['duration_range_min'][1]:
        results['issues'].append(f"Script is too long ({estimated_duration_min:.1f} min). Consider trimming {int((estimated_duration_min - B['duration_target_min']) * B['wpm_target'])} words.")
    elif score <= 50:
        shortfall = B['duration_target_min'] - estimated_duration_min
        if shortfall > 0:
            results['issues'].append(f"Script is short ({estimated_duration_min:.1f} min vs {B['duration_target_min']:.0f} min target). Add ~{int(shortfall * B['wpm_target'])} words.")

    # ---- 2. OPENING HOOK ----
    print(f"\n--- OPENING HOOK (first ~30 words) ---")
    first_30_words = ' '.join(words[:30]).lower()
    first_sentence = sentences[0] if sentences else ''

    hook_types_found = []
    for pattern, name in HOOK_PATTERNS:
        if re.search(pattern, first_30_words, re.IGNORECASE):
            hook_types_found.append(name)

    if hook_types_found:
        score = 90
        status = 'GOOD'
        results['strengths'].append(f"Strong opening hook using: {', '.join(hook_types_found)}")
    else:
        score = 40
        status = 'WEAK'
        results['issues'].append("Opening hook doesn't match Fern's patterns. Try: mystery opener, superlative, year anchor, or direct address.")
        results['suggestions'].append("Fern's top hooks: start with a dramatic quote, a shocking fact, 'In [year]...', or 'This is [location]...'")

    results['scores']['hook'] = {'score': score, 'status': status}
    print(f"  First sentence: \"{first_sentence[:80]}\"")
    print(f"  Hook types: {hook_types_found if hook_types_found else 'NONE DETECTED'}")
    print(f"  Score: [{status}]")

    # ---- 3. RE-ENGAGEMENT HOOKS ----
    print(f"\n--- RE-ENGAGEMENT HOOKS ---")
    hooks_found = []
    for i, sentence in enumerate(sentences):
        s_lower = sentence.lower()
        for pattern, name in REENGAGEMENT_PATTERNS:
            if re.search(pattern, s_lower):
                hooks_found.append({'type': name, 'sentence_idx': i, 'text': sentence[:80]})
                break

    hooks_per_min = len(hooks_found) / estimated_duration_min if estimated_duration_min > 0 else 0
    target_hooks = B['hooks_per_min']

    # Fern's rate is low (0.12/min) but top performers also use subtle hooks
    # Let's check for a reasonable rate
    score, status, detail = score_metric(hooks_per_min, target_hooks, tolerance_pct=50)
    results['scores']['reengagement'] = {'score': score, 'status': status, 'detail': detail}

    print(f"  Found: {len(hooks_found)} hooks ({hooks_per_min:.2f}/min, target: {target_hooks:.2f}/min)")
    print(f"  Score: [{status}] {detail}")
    if hooks_found:
        hook_type_counts = Counter(h['type'] for h in hooks_found)
        print(f"  Types: {dict(hook_type_counts)}")
        for h in hooks_found[:5]:
            print(f"    - [{h['type']}] \"{h['text']}\"")

    if hooks_per_min < target_hooks * 0.5:
        results['suggestions'].append("Add more re-engagement hooks: 'but then...', 'suddenly...', 'this is where it gets...'")

    # ---- 4. CURIOSITY GAPS ----
    print(f"\n--- CURIOSITY GAPS ---")
    gaps = []
    for i, sentence in enumerate(sentences):
        s_lower = sentence.lower()
        gap_type = None

        for pattern in CURIOSITY_QUESTION_PATTERNS:
            if re.search(pattern, s_lower):
                gap_type = 'question'
                break
        if not gap_type:
            for pattern in CLIFFHANGER_PATTERNS:
                if re.search(pattern, s_lower):
                    gap_type = 'cliffhanger'
                    break

        if gap_type:
            # Check for resolution in next 15 sentences
            resolved = False
            for j in range(i + 1, min(i + 15, len(sentences))):
                for pattern in RESOLUTION_PATTERNS:
                    if re.search(pattern, sentences[j].lower()):
                        resolved = True
                        break
                if resolved:
                    break

            gaps.append({'type': gap_type, 'resolved': resolved, 'sentence_idx': i, 'text': sentence[:80]})

    gaps_per_min = len(gaps) / estimated_duration_min if estimated_duration_min > 0 else 0
    resolved_pct = sum(1 for g in gaps if g['resolved']) / len(gaps) * 100 if gaps else 0

    score, status, detail = score_metric(gaps_per_min, B['gaps_per_min'], tolerance_pct=30)
    results['scores']['curiosity_gaps'] = {'score': score, 'status': status, 'detail': detail}

    print(f"  Found: {len(gaps)} gaps ({gaps_per_min:.2f}/min, target: {B['gaps_per_min']:.2f}/min)")
    print(f"  Resolved: {resolved_pct:.0f}%")
    print(f"  Types: questions={sum(1 for g in gaps if g['type']=='question')}, cliffhangers={sum(1 for g in gaps if g['type']=='cliffhanger')}")
    print(f"  Score: [{status}] {detail}")

    if gaps_per_min < B['gaps_per_min'] * 0.7:
        results['issues'].append(f"Not enough curiosity gaps ({gaps_per_min:.2f}/min vs {B['gaps_per_min']:.2f} target). Pose more questions, add cliffhangers.")
    if gaps_per_min > B['gaps_per_min'] * 1.5:
        results['suggestions'].append("Slightly too many curiosity triggers — may feel exhausting. Fern balances tension with calm explanation sections.")

    # ---- 5. EMOTIONAL LANGUAGE ----
    print(f"\n--- EMOTIONAL LANGUAGE ---")
    emotion_counts = {}
    emotion_examples = {}
    for emotion, word_list in EMOTIONAL_WORDS.items():
        count = sum(text_lower.count(w) for w in word_list)
        emotion_counts[emotion] = count
        found_words = [w for w in word_list if w in text_lower]
        if found_words:
            emotion_examples[emotion] = found_words

    total_emotional = sum(emotion_counts.values())
    emotional_density = total_emotional / word_count * 100 if word_count > 0 else 0
    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if any(emotion_counts.values()) else 'none'

    score, status, detail = score_metric(emotional_density, B['emotional_density_pct'], tolerance_pct=40)
    results['scores']['emotional_language'] = {'score': score, 'status': status, 'detail': detail}

    print(f"  Emotional density: {emotional_density:.2f}% (target: {B['emotional_density_pct']:.2f}%)")
    print(f"  Dominant emotion: {dominant_emotion}")
    print(f"  Breakdown:")
    for emotion in B['emotion_ranking']:
        count = emotion_counts.get(emotion, 0)
        examples = emotion_examples.get(emotion, [])
        bar = '#' * min(count, 30)
        print(f"    {emotion:10s}: {count:3d} {bar} {examples[:3]}")
    print(f"  Score: [{status}] {detail}")

    if dominant_emotion not in ('mystery', 'fear', 'power'):
        results['suggestions'].append(f"Fern's dominant emotions are mystery > fear > power. Your dominant is '{dominant_emotion}'. Consider adding more mystery/fear language.")

    # ---- 6. WORD CHOICE ----
    print(f"\n--- WORD CHOICE ---")

    # Second person
    you_count = sum(1 for w in words if w.lower() in ('you', 'your', "you're", "you'd", "you'll", "you've"))
    you_density = you_count / word_count * 100 if word_count > 0 else 0

    # Questions
    question_count = script_text.count('?')
    questions_per_1000 = question_count / word_count * 1000 if word_count > 0 else 0

    # Vocabulary richness
    unique_words = len(set(w.lower() for w in words))
    vocab_richness = unique_words / word_count if word_count > 0 else 0

    # Average sentence length
    avg_sentence_len = word_count / len(sentences) if sentences else 0

    you_score, you_status, you_detail = score_metric(you_density, B['you_density_pct'], tolerance_pct=50)
    q_score, q_status, q_detail = score_metric(questions_per_1000, B['questions_per_1000'], tolerance_pct=40)
    v_score, v_status, v_detail = score_metric(vocab_richness, B['vocab_richness'], tolerance_pct=30)

    word_choice_score = int((you_score + q_score + v_score) / 3)
    results['scores']['word_choice'] = {'score': word_choice_score, 'status': 'GOOD' if word_choice_score >= 70 else 'NEEDS WORK'}

    print(f"  'You/your' density: {you_density:.2f}% (target: {B['you_density_pct']:.2f}%) [{you_status}]")
    print(f"  Questions: {question_count} ({questions_per_1000:.1f}/1000 words, target: {B['questions_per_1000']:.1f}) [{q_status}]")
    print(f"  Vocabulary richness: {vocab_richness:.3f} (target: {B['vocab_richness']:.3f}) [{v_status}]")
    print(f"  Avg sentence length: {avg_sentence_len:.1f} words")

    if you_density < B['you_density_pct'] * 0.5:
        results['suggestions'].append("Use more second-person language ('you', 'your') to directly address the viewer.")

    # ---- 7. TITLE CHECK (if provided) ----
    if title:
        print(f"\n--- TITLE CHECK ---")
        title_words = len(title.split())
        title_chars = len(title)
        title_lower = title.lower()

        patterns_matched = []
        for pattern_name, pattern in TITLE_PATTERNS.items():
            if re.search(pattern, title_lower):
                patterns_matched.append(pattern_name)

        tw_score, tw_status, tw_detail = score_metric(title_words, B['title_word_count'], tolerance_pct=30)
        tc_score, tc_status, tc_detail = score_metric(title_chars, B['title_char_count'], tolerance_pct=30)

        pattern_score = min(100, len(patterns_matched) * 35)  # Each pattern adds 35 points
        title_score = int((tw_score + tc_score + pattern_score) / 3)
        results['scores']['title'] = {'score': title_score, 'status': 'GOOD' if title_score >= 70 else 'NEEDS WORK'}

        print(f"  Title: \"{title}\"")
        print(f"  Words: {title_words} (target: {B['title_word_count']:.0f}) [{tw_status}]")
        print(f"  Chars: {title_chars} (target: {B['title_char_count']:.0f}) [{tc_status}]")
        print(f"  Patterns matched: {patterns_matched if patterns_matched else 'NONE'}")
        print(f"  Score: [{results['scores']['title']['status']}] {title_score}/100")

        if not patterns_matched:
            results['issues'].append("Title doesn't use any proven Fern patterns. Best performers use: person reference, country reference, or superlative.")
        if 'person_reference' in patterns_matched or 'country_reference' in patterns_matched:
            results['strengths'].append("Title uses high-performing pattern (person/country reference).")

    # ---- 8. STRUCTURE CHECK ----
    print(f"\n--- SCRIPT STRUCTURE ---")
    total_sentences_count = len(sentences)
    intro_end = max(1, int(total_sentences_count * 0.10))
    body_end = max(intro_end + 1, int(total_sentences_count * 0.85))

    intro_sentences = sentences[:intro_end]
    body_sentences = sentences[intro_end:body_end]
    conclusion_sentences = sentences[body_end:]

    print(f"  Total sentences: {total_sentences_count}")
    print(f"  Intro (~first 10%): {len(intro_sentences)} sentences")
    print(f"  Body (~10-85%): {len(body_sentences)} sentences")
    print(f"  Conclusion (~last 15%): {len(conclusion_sentences)} sentences")

    # Check if there are gaps throughout (not front-loaded)
    first_half_gaps = sum(1 for g in gaps if g['sentence_idx'] < total_sentences_count // 2)
    second_half_gaps = sum(1 for g in gaps if g['sentence_idx'] >= total_sentences_count // 2)

    if gaps and first_half_gaps > 0:
        gap_balance = second_half_gaps / first_half_gaps if first_half_gaps > 0 else 0
        print(f"  Curiosity gap distribution: {first_half_gaps} in first half, {second_half_gaps} in second half")
        if gap_balance < 0.5:
            results['suggestions'].append("Curiosity gaps are front-loaded. Distribute them more evenly — the second half needs just as many hooks to maintain retention.")

    # ---- OVERALL SCORE ----
    all_scores = [v['score'] for v in results['scores'].values()]
    overall = int(statistics.mean(all_scores)) if all_scores else 0
    results['overall_score'] = overall

    print(f"\n{'=' * 70}")
    print(f"  OVERALL FERN MATCH SCORE: {overall}/100")
    print(f"{'=' * 70}")

    # Scorecard
    print(f"\n  SCORECARD:")
    for metric, data in results['scores'].items():
        score = data['score']
        bar = '#' * (score // 5)
        spaces = ' ' * (20 - len(bar))
        label = metric.replace('_', ' ').title()
        print(f"    {label:25s} {bar}{spaces} {score:3d}/100 [{data['status']}]")

    # Issues
    if results['issues']:
        print(f"\n  ISSUES TO FIX:")
        for issue in results['issues']:
            print(f"    [!] {issue}")

    # Strengths
    if results['strengths']:
        print(f"\n  STRENGTHS:")
        for strength in results['strengths']:
            print(f"    [+] {strength}")

    # Suggestions
    if results['suggestions']:
        print(f"\n  SUGGESTIONS:")
        for suggestion in results['suggestions']:
            print(f"    [>] {suggestion}")

    # Fern-match grade
    print(f"\n  GRADE: ", end='')
    if overall >= 85:
        print("A  -- Very close to Fern's style. Minor tweaks only.")
    elif overall >= 70:
        print("B  -- Good foundation. Address the issues above.")
    elif overall >= 55:
        print("C  -- Needs work. Focus on the red flags first.")
    elif overall >= 40:
        print("D  -- Significant gaps. Review the Fern Formula SOP.")
    else:
        print("F  -- Doesn't match Fern's style. Start from the SOP template.")

    print()
    return results


# ============================================================================
# CLI
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nQuick test: echo your script text | python check_fern_script.py -")
        return

    script_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None

    if script_path == '-':
        script_text = sys.stdin.read()
    else:
        with open(script_path, 'r') as f:
            script_text = f.read()

    if not script_text.strip():
        print("Error: Empty script")
        return

    check_script(script_text, title)


if __name__ == '__main__':
    main()
