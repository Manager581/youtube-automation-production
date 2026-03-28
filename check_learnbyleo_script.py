#!/usr/bin/env python3
"""
LearnByLeo Script Checker
Analyzes a script draft against the LearnByLeo playbook benchmarks.
Shows exactly where you match and where you're off.

Usage:
    python check_learnbyleo_script.py <script_file> [title]

Examples:
    python check_learnbyleo_script.py scripts/raw_secret_scores_v4.txt
    python check_learnbyleo_script.py scripts/raw_secret_scores_v4.txt "The Secret Scores Nobody Talks About"
    echo "paste your script" | python check_learnbyleo_script.py -

The script file should be plain text (your narration script).
"""

import json
import re
import sys
import statistics
from pathlib import Path
from collections import Counter

# ============================================================================
# LOAD PLAYBOOK BENCHMARKS
# ============================================================================

PLAYBOOK_PATH = Path(__file__).parent / "playbook" / "scripting.json"


def load_playbook():
    """Load LearnByLeo scripting playbook."""
    try:
        with open(PLAYBOOK_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WARNING: Playbook not found at {PLAYBOOK_PATH}, using defaults")
        return {}


# ============================================================================
# LEARNBYLEO BENCHMARKS
# ============================================================================

BENCHMARKS = {
    # Pacing — general YouTube range, not brand-specific
    'wpm_range': (120, 180),
    'wpm_midpoint': 150,

    # Duration — LearnByLeo educational sweet spot
    'duration_range_min': (10, 25),
    'duration_target_min': 17.5,

    # Green/Purple alternation — from P-SC-01
    'green_purple_max_gap_sentences': 15,

    # Water tank — from P-SC-02
    'value_refill_max_min': 3.0,

    # But/Therefore ratio — from P-SC-03
    'but_therefore_min_ratio': 1.5,

    # Conversational markers — from P-SC-05
    'conversational_markers_per_1000': 3.0,

    # Energy shifts — from energy_variation tactic
    'min_energy_shifts': 3,

    # Curiosity gaps
    'hooks_per_min': 0.3,

    # Word choice
    'you_density_pct': 0.5,
    'questions_per_1000': 2.0,
}


# ============================================================================
# PATTERN DEFINITIONS — LearnByLeo specific
# ============================================================================

# Green section markers (curiosity-building) — from P-SC-01 green_types
GREEN_PATTERNS = [
    (r'\bbut\b.*\bwhat\b', 'mystery'),
    (r'\bwhat\s+if\b', 'mystery'),
    (r'\bhow\s+(?:did|does|can|could|would)\b', 'question'),
    (r'\bwhy\s+(?:did|does|is|are|was|were)\b', 'question'),
    (r'\bwho\s+(?:is|was|would)\b', 'question'),
    (r'\bno\s+one\s+(?:knew|expected|realized|knows)\b', 'mystery'),
    (r'\bsecret\b|\bhidden\b|\bunknown\b', 'mystery'),
    (r'\bcounterinti?uitive\b|\bsurprising\b', 'counterintuitive'),
    (r'\bthere\'?s\s+(?:a|one)\s+(?:catch|problem|twist)\b', 'obstacle'),
    (r'\bbut\s+here\'?s\s+(?:the|where)\b', 'obstacle'),
    (r'\bwhat\s+.*didn\'?t\s+know\b', 'missing_piece'),
    (r'\boverlooki?n?g?\b.*\bobvious\b', 'missing_piece'),
    (r'\bproblem\b|\bchallenge\b|\bobstacle\b', 'problem'),
    (r'\bdidn\'?t\s+(?:add|make)\s+(?:up|sense)\b', 'mystery'),
    (r'\?', 'question'),
]

# Purple section markers (payoff/resolution) — from P-SC-01 purple_types
PURPLE_PATTERNS = [
    (r'\bthe\s+answer\b|\bthe\s+solution\b', 'answer'),
    (r'\bit\s+turns?\s+out\b', 'reveal'),
    (r'\bthey\s+(?:found|discovered|realized|learned)\b', 'reveal'),
    (r'\bfinally\b|\beventually\b|\bin\s+the\s+end\b', 'resolution'),
    (r'\bthe\s+(?:truth|reason|key|secret)\s+(?:was|is|turns)\b', 'reveal'),
    (r'\bso\s+here\'?s\s+(?:what|how|why)\b', 'payoff'),
    (r'\bthat\'?s\s+(?:why|how|when|where)\b', 'payoff'),
    (r'\bthis\s+(?:means?|explains?|shows?)\b', 'payoff'),
    (r'\bthe\s+result\b|\bthe\s+outcome\b', 'resolution'),
    (r'\bwhich\s+(?:means?|explains?)\b', 'payoff'),
]

# But/Therefore connectors — from P-SC-03
BUT_THEREFORE_PATTERNS = [
    r'\bbut\b',
    r'\bhowever\b',
    r'\btherefore\b',
    r'\bso\b',
    r'\bbecause\b',
    r'\bas\s+a\s+result\b',
    r'\bconsequently\b',
    r'\bwhich\s+(?:means?|led)\b',
    r'\bthat\'?s\s+why\b',
]

# And/Then connectors (the bad pattern) — from P-SC-03
AND_THEN_PATTERNS = [
    r'\band\s+then\b',
    r'\bafter\s+that\b',
    r'\bnext\b(?!\s+to)',
    r'\bsubsequently\b',
    r'\band\s+also\b',
    r'\bmoreover\b',
    r'\bfurthermore\b',
    r'\badditionally\b',
]

# Conversational markers — from P-SC-05
CONVERSATIONAL_PATTERNS = [
    (r'\bimagine\b', 'analogy'),
    (r'\bpicture\s+this\b', 'analogy'),
    (r'\bit\'?s\s+(?:like|as\s+if)\b', 'analogy'),
    (r'\bthink\s+(?:of|about)\s+it\b', 'analogy'),
    (r'\bfor\s+example\b|\bfor\s+instance\b', 'example'),
    (r'\blet\s+me\b|\blet\'?s\b', 'conversational'),
    (r'\blook\b.*\bthis\s+way\b', 'analogy'),
    (r'\byou\s+(?:know|see|get)\b', 'direct_address'),
    (r'\bhere\'?s\s+(?:the|a)\s+(?:thing|way|trick)\b', 'conversational'),
    (r'\bhonestly\b|\bfrankly\b|\bseriously\b', 'conversational'),
    (r'\bkind\s+of\b|\bsort\s+of\b', 'conversational'),
    (r'\bright\?\b|\byeah\?\b', 'conversational'),
    (r'\bever\s+(?:wonder|notice|think)\b', 'question'),
    (r'\bstory\b|\banecdote\b|\btale\b', 'story'),
]

# Energy markers — high energy
HIGH_ENERGY_PATTERNS = [
    r'\bincredib(?:le|ly)\b',
    r'\bunbelievab(?:le|ly)\b',
    r'\binsane\b|\bcrazy\b|\bwild\b',
    r'\bmassive\b|\benormous\b|\bhuge\b',
    r'\bexplod(?:e[ds]?|ing)\b',
    r'\bshock(?:ing|ed)?\b',
    r'\b(?:!){2,}',
    r'\bdominant\b|\bpowerful\b|\bunstoppable\b',
    r'\bbreakthrough\b|\brev(?:olution|olutionary)\b',
]

# Low energy markers
LOW_ENERGY_PATTERNS = [
    r'\bquietly\b|\bslowly\b|\bcarefully\b',
    r'\bpause\b|\bstop\b|\bwait\b',
    r'\bconsider\b|\breflect\b|\bthink\b',
    r'\bbut\s+why\b',
    r'\bthe\s+truth\s+is\b',
    r'\bhere\'?s\s+(?:the|what\'?s)\s+(?:interesting|strange|odd)\b',
    r'\bsilence\b|\bstillness\b|\bcalm\b',
]

# Hook / re-engagement patterns
HOOK_PATTERNS = [
    (r'\bwhat\s+if\b', 'what_if'),
    (r'\bimagine\b', 'imagine'),
    (r'\bpicture\s+this\b', 'picture_this'),
    (r'\byou\b.*\bknow\b', 'direct_address'),
    (r'\bin\s+\d{4}\b', 'year_anchor'),
    (r'\bhidden\b|\bsecret\b|\bmysterious\b', 'mystery_opener'),
    (r'\bbut\s+then\b', 'plot_twist'),
    (r'\bhowever\b', 'contrast'),
    (r'\bhere\'?s\s+where\b.*\bgets?\b', 'escalation'),
    (r'\bsuddenly\b', 'sudden_change'),
    (r'\bbut\s+here\'?s\s+the\s+(?:thing|catch|problem)\b', 'but_heres'),
    (r'\bnow\b.*\bgets?\s+(?:interesting|crazy|wild|weird)\b', 'escalation_now'),
    (r'\blittle\s+did\b', 'dramatic_irony'),
    (r'\bthis\s+is\s+where\b', 'turning_point'),
]


# ============================================================================
# SCORING FUNCTIONS
# ============================================================================

def score_range(value, low, high):
    """Score if value falls within range."""
    if low <= value <= high:
        return 100, 'IN RANGE', f'{value:.1f} (range: {low:.1f}-{high:.1f})'
    elif value < low:
        diff = low - value
        pct_off = diff / low * 100 if low > 0 else 50
        return max(20, 80 - int(pct_off)), 'LOW', f'{value:.1f} (range: {low:.1f}-{high:.1f})'
    else:
        diff = value - high
        pct_off = diff / high * 100 if high > 0 else 50
        return max(20, 80 - int(pct_off)), 'HIGH', f'{value:.1f} (range: {low:.1f}-{high:.1f})'


def score_metric(value, target, tolerance_pct=20):
    """Score a metric against target. Returns (score 0-100, status, detail)."""
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


def score_minimum(value, minimum, label=""):
    """Score against a minimum threshold."""
    if value >= minimum:
        return 100, 'GOOD', f'{value:.1f} ({label}min: {minimum:.1f})'
    elif value >= minimum * 0.6:
        return 50, 'LOW', f'{value:.1f} ({label}min: {minimum:.1f})'
    else:
        return 20, 'WAY LOW', f'{value:.1f} ({label}min: {minimum:.1f})'


# ============================================================================
# MAIN CHECKER
# ============================================================================

def check_script(script_text, title=None):
    """Run full LearnByLeo playbook check on a script."""

    playbook = load_playbook()
    B = BENCHMARKS
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
    print("  LEARNBYLEO SCRIPT CHECK")
    print("=" * 70)

    # ---- 1. DURATION & WPM ----
    estimated_duration_min = word_count / B['wpm_midpoint']

    score, status, detail = score_range(
        estimated_duration_min,
        B['duration_range_min'][0],
        B['duration_range_min'][1],
    )
    results['scores']['duration'] = {'score': score, 'status': status, 'detail': detail}

    print(f"\n--- DURATION ---")
    print(f"  Word count: {word_count:,}")
    print(f"  At {B['wpm_midpoint']} WPM = {estimated_duration_min:.1f} min (range: {B['duration_range_min'][0]}-{B['duration_range_min'][1]} min)")
    print(f"  Score: [{status}] {detail}")

    if estimated_duration_min < B['duration_range_min'][0]:
        needed = int((B['duration_range_min'][0] - estimated_duration_min) * B['wpm_midpoint'])
        results['issues'].append(f"Script too short ({estimated_duration_min:.1f} min). Add ~{needed} words to reach {B['duration_range_min'][0]} min.")
    elif estimated_duration_min > B['duration_range_min'][1]:
        excess = int((estimated_duration_min - B['duration_range_min'][1]) * B['wpm_midpoint'])
        results['issues'].append(f"Script too long ({estimated_duration_min:.1f} min). Trim ~{excess} words. (P-SC-04: explain as simply as possible)")

    # ---- 2. GREEN/PURPLE ALTERNATION (P-SC-01) ----
    print(f"\n--- GREEN/PURPLE RATIO (P-SC-01) ---")

    green_hits = []
    purple_hits = []
    for i, sentence in enumerate(sentences):
        s_lower = sentence.lower()
        for pattern, gtype in GREEN_PATTERNS:
            if re.search(pattern, s_lower):
                green_hits.append({'idx': i, 'type': gtype, 'text': sentence[:60]})
                break
        for pattern, ptype in PURPLE_PATTERNS:
            if re.search(pattern, s_lower):
                purple_hits.append({'idx': i, 'type': ptype, 'text': sentence[:60]})
                break

    green_count = len(green_hits)
    purple_count = len(purple_hits)
    total_tagged = green_count + purple_count

    # Check alternation quality: longest gap between green sections
    green_indices = sorted(set(g['idx'] for g in green_hits))
    max_green_gap = 0
    if len(green_indices) > 1:
        for j in range(1, len(green_indices)):
            gap = green_indices[j] - green_indices[j - 1]
            max_green_gap = max(max_green_gap, gap)
    elif green_indices:
        max_green_gap = max(green_indices[0], len(sentences) - green_indices[0])
    else:
        max_green_gap = len(sentences)

    # Score: good ratio + good distribution
    ratio_ok = green_count > 0 and purple_count > 0
    ratio_balance = min(green_count, purple_count) / max(green_count, purple_count, 1)
    gap_ok = max_green_gap <= B['green_purple_max_gap_sentences']

    if ratio_ok and ratio_balance >= 0.3 and gap_ok:
        gp_score = 90
        gp_status = 'GOOD'
    elif ratio_ok and ratio_balance >= 0.2:
        gp_score = 65
        gp_status = 'OK'
    elif ratio_ok:
        gp_score = 45
        gp_status = 'WEAK'
    else:
        gp_score = 20
        gp_status = 'MISSING'

    results['scores']['green_purple'] = {'score': gp_score, 'status': gp_status}

    print(f"  Green (curiosity): {green_count}  |  Purple (payoff): {purple_count}")
    print(f"  Balance: {ratio_balance:.2f} (1.0 = perfect alternation)")
    print(f"  Max gap between green sections: {max_green_gap} sentences (limit: {B['green_purple_max_gap_sentences']})")
    print(f"  Score: [{gp_status}]")

    if green_count == 0:
        results['issues'].append("No curiosity-building (green) sections detected. Every payoff needs a setup first. (P-SC-01)")
    if purple_count == 0:
        results['issues'].append("No payoff (purple) sections detected. Curiosity without resolution frustrates viewers. (P-SC-01)")
    if max_green_gap > B['green_purple_max_gap_sentences']:
        results['suggestions'].append(f"Long stretch ({max_green_gap} sentences) without a curiosity trigger. Add a question or mystery. (P-SC-01)")

    if green_hits[:3]:
        print(f"  Sample green: {[g['type'] for g in green_hits[:5]]}")
    if purple_hits[:3]:
        print(f"  Sample purple: {[p['type'] for p in purple_hits[:5]]}")

    # ---- 3. WATER TANK PACING (P-SC-02) ----
    print(f"\n--- WATER TANK PACING (P-SC-02) ---")

    # Value refills = green + purple hits combined, spread across the script
    all_value_indices = sorted(set(g['idx'] for g in green_hits) | set(p['idx'] for p in purple_hits))

    if len(all_value_indices) > 1 and estimated_duration_min > 0:
        # Convert sentence indices to approximate minutes
        sentences_per_min = len(sentences) / estimated_duration_min if estimated_duration_min > 0 else 1
        gaps_in_min = []
        for j in range(1, len(all_value_indices)):
            gap_sentences = all_value_indices[j] - all_value_indices[j - 1]
            gap_min = gap_sentences / sentences_per_min
            gaps_in_min.append(gap_min)
        max_gap_min = max(gaps_in_min) if gaps_in_min else 0
        avg_gap_min = statistics.mean(gaps_in_min) if gaps_in_min else 0
    else:
        max_gap_min = estimated_duration_min
        avg_gap_min = estimated_duration_min

    if max_gap_min <= B['value_refill_max_min']:
        wt_score = 100
        wt_status = 'GOOD'
    elif max_gap_min <= B['value_refill_max_min'] * 1.5:
        wt_score = 65
        wt_status = 'OK'
    else:
        wt_score = 30
        wt_status = 'DRY'

    results['scores']['water_tank'] = {'score': wt_score, 'status': wt_status}

    print(f"  Value moments found: {len(all_value_indices)}")
    print(f"  Avg gap: {avg_gap_min:.1f} min  |  Max gap: {max_gap_min:.1f} min (limit: {B['value_refill_max_min']:.0f} min)")
    print(f"  Score: [{wt_status}]")

    if max_gap_min > B['value_refill_max_min']:
        results['issues'].append(f"Water tank runs dry: {max_gap_min:.1f} min gap without value. Viewers leave during droughts. (P-SC-02)")

    # ---- 4. BUT/THEREFORE FLOW (P-SC-03) ----
    print(f"\n--- BUT/THEREFORE FLOW (P-SC-03) ---")

    bt_count = sum(
        len(re.findall(p, text_lower))
        for p in BUT_THEREFORE_PATTERNS
    )
    at_count = sum(
        len(re.findall(p, text_lower))
        for p in AND_THEN_PATTERNS
    )

    bt_ratio = bt_count / max(at_count, 1)

    if bt_ratio >= B['but_therefore_min_ratio'] and bt_count >= 5:
        bt_score = 90
        bt_status = 'GOOD'
        results['strengths'].append("Strong causal flow (but/therefore/so) over sequential listing. (P-SC-03)")
    elif bt_ratio >= 1.0:
        bt_score = 65
        bt_status = 'OK'
    elif bt_count >= 3:
        bt_score = 45
        bt_status = 'WEAK'
    else:
        bt_score = 20
        bt_status = 'FLAT'
        results['issues'].append("Script reads like a list (and/then). Rewrite with causal links: but, therefore, so, because. (P-SC-03)")

    results['scores']['but_therefore'] = {'score': bt_score, 'status': bt_status}

    print(f"  But/Therefore connectors: {bt_count}")
    print(f"  And/Then connectors: {at_count}")
    print(f"  Ratio: {bt_ratio:.1f}x (target: >{B['but_therefore_min_ratio']:.1f}x)")
    print(f"  Score: [{bt_status}]")

    # ---- 5. CONVERSATIONAL TONE (P-SC-05) ----
    print(f"\n--- CONVERSATIONAL TONE (P-SC-05) ---")

    conv_hits = []
    for pattern, ctype in CONVERSATIONAL_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for _ in matches:
            conv_hits.append(ctype)

    conv_per_1000 = len(conv_hits) / word_count * 1000 if word_count > 0 else 0
    conv_types = Counter(conv_hits)

    score, status, detail = score_metric(conv_per_1000, B['conversational_markers_per_1000'], tolerance_pct=40)
    results['scores']['conversational'] = {'score': score, 'status': status, 'detail': detail}

    print(f"  Conversational markers: {len(conv_hits)} ({conv_per_1000:.1f}/1000 words, target: {B['conversational_markers_per_1000']:.1f})")
    print(f"  Types: {dict(conv_types.most_common(5))}")
    print(f"  Score: [{status}] {detail}")

    if conv_per_1000 < B['conversational_markers_per_1000'] * 0.5:
        results['issues'].append("Reads like a textbook. Add analogies, questions, examples, 'imagine', 'think of it this way'. (P-SC-05)")

    # Check for analogies specifically
    analogy_count = conv_types.get('analogy', 0)
    example_count = conv_types.get('example', 0)
    if analogy_count == 0 and example_count == 0:
        results['suggestions'].append("No analogies or examples found. Abstract ideas need concrete illustrations. (P-SC-05)")
    elif analogy_count + example_count >= 3:
        results['strengths'].append(f"Good use of analogies ({analogy_count}) and examples ({example_count}). Makes content tangible.")

    # ---- 6. ENERGY VARIATION ----
    print(f"\n--- ENERGY VARIATION ---")

    # Split script into chunks and measure energy per chunk
    chunk_size = max(1, len(sentences) // 8)
    energy_levels = []
    for i in range(0, len(sentences), chunk_size):
        chunk = ' '.join(sentences[i:i + chunk_size]).lower()
        chunk_words = len(chunk.split())
        if chunk_words == 0:
            continue

        high_e = sum(len(re.findall(p, chunk)) for p in HIGH_ENERGY_PATTERNS)
        low_e = sum(len(re.findall(p, chunk)) for p in LOW_ENERGY_PATTERNS)

        if high_e > low_e + 2:
            energy_levels.append('HIGH')
        elif low_e > high_e + 1:
            energy_levels.append('LOW')
        else:
            energy_levels.append('MID')

    # Count energy shifts
    shifts = 0
    for i in range(1, len(energy_levels)):
        if energy_levels[i] != energy_levels[i - 1]:
            shifts += 1

    score, status, detail = score_minimum(shifts, B['min_energy_shifts'], "")
    results['scores']['energy'] = {'score': score, 'status': status}

    print(f"  Energy map: {' -> '.join(energy_levels)}")
    print(f"  Shifts: {shifts} (minimum: {B['min_energy_shifts']})")
    print(f"  Score: [{status}]")

    if shifts < B['min_energy_shifts']:
        results['issues'].append(f"Only {shifts} energy shifts. Vary intensity: hype sections vs calm reflection. Contrast forces viewers back into focus.")
    elif shifts >= 5:
        results['strengths'].append(f"Strong energy variation ({shifts} shifts). Keeps viewers engaged through contrast.")

    # ---- 7. HOOKS & CURIOSITY GAPS ----
    print(f"\n--- HOOKS & CURIOSITY GAPS ---")

    hooks_found = []
    for i, sentence in enumerate(sentences):
        s_lower = sentence.lower()
        for pattern, name in HOOK_PATTERNS:
            if re.search(pattern, s_lower):
                hooks_found.append({'type': name, 'idx': i, 'text': sentence[:70]})
                break

    hooks_per_min = len(hooks_found) / estimated_duration_min if estimated_duration_min > 0 else 0

    score, status, detail = score_metric(hooks_per_min, B['hooks_per_min'], tolerance_pct=50)
    results['scores']['hooks'] = {'score': score, 'status': status, 'detail': detail}

    print(f"  Found: {len(hooks_found)} hooks ({hooks_per_min:.2f}/min, target: {B['hooks_per_min']:.2f}/min)")
    print(f"  Score: [{status}] {detail}")
    if hooks_found:
        hook_types = Counter(h['type'] for h in hooks_found)
        print(f"  Types: {dict(hook_types.most_common(5))}")
        for h in hooks_found[:4]:
            print(f"    - [{h['type']}] \"{h['text']}\"")

    if hooks_per_min < B['hooks_per_min'] * 0.5:
        results['suggestions'].append("Add more re-engagement hooks throughout. Every 3 min the viewer needs a reason to stay.")

    # ---- 8. OPENING HOOK ----
    print(f"\n--- OPENING HOOK ---")
    first_30_words = ' '.join(words[:30]).lower()
    first_sentence = sentences[0] if sentences else ''

    hook_types_found = []
    for pattern, name in HOOK_PATTERNS:
        if re.search(pattern, first_30_words):
            hook_types_found.append(name)

    if hook_types_found:
        hook_score = 90
        hook_status = 'GOOD'
        results['strengths'].append(f"Strong opening hook: {', '.join(hook_types_found)}")
    else:
        hook_score = 40
        hook_status = 'WEAK'
        results['issues'].append("Opening hook is weak. Start with mystery, a provocative question, or a surprising fact.")

    results['scores']['opening'] = {'score': hook_score, 'status': hook_status}
    print(f"  First sentence: \"{first_sentence[:80]}\"")
    print(f"  Hook types: {hook_types_found if hook_types_found else 'NONE DETECTED'}")
    print(f"  Score: [{hook_status}]")

    # ---- 9. WORD CHOICE ----
    print(f"\n--- WORD CHOICE ---")

    you_count = sum(1 for w in words if w.lower() in ('you', 'your', "you're", "you'd", "you'll", "you've"))
    you_density = you_count / word_count * 100 if word_count > 0 else 0

    question_count = script_text.count('?')
    questions_per_1000 = question_count / word_count * 1000 if word_count > 0 else 0

    unique_words = len(set(w.lower() for w in words))
    vocab_richness = unique_words / word_count if word_count > 0 else 0

    avg_sentence_len = word_count / len(sentences) if sentences else 0

    you_score, you_status, you_detail = score_metric(you_density, B['you_density_pct'], tolerance_pct=50)
    q_score, q_status, q_detail = score_metric(questions_per_1000, B['questions_per_1000'], tolerance_pct=40)

    wc_score = int((you_score + q_score) / 2)
    results['scores']['word_choice'] = {'score': wc_score, 'status': 'GOOD' if wc_score >= 70 else 'NEEDS WORK'}

    print(f"  'You/your' density: {you_density:.2f}% (target: {B['you_density_pct']:.2f}%) [{you_status}]")
    print(f"  Questions: {question_count} ({questions_per_1000:.1f}/1000 words, target: {B['questions_per_1000']:.1f}) [{q_status}]")
    print(f"  Vocabulary richness: {vocab_richness:.3f}")
    print(f"  Avg sentence length: {avg_sentence_len:.1f} words")

    if you_density < B['you_density_pct'] * 0.3:
        results['suggestions'].append("Talk TO the viewer more. Use 'you' and 'your' to create a conversation, not a lecture.")

    # ---- 10. ANTI-PATTERN CHECK ----
    print(f"\n--- ANTI-PATTERN CHECK ---")

    ap_issues = 0

    # AP-SC-03: Asking for likes/subs in intro
    first_10_pct = ' '.join(words[:max(1, word_count // 10)]).lower()
    if re.search(r'\bsubscri(?:be|ption)\b|\blike\s+(?:and|&)\b|\bhit\s+(?:the\s+)?(?:bell|like)\b', first_10_pct):
        print(f"  [!] Asks for likes/subs in intro — breaks immersion at the worst moment (AP-SC-03)")
        results['issues'].append("Asking for likes/subs in the intro kills retention. Move mid-video or remove entirely. (AP-SC-03)")
        ap_issues += 1
    else:
        print(f"  [+] No engagement beg in intro")

    # AP-SC-04: Having a wind-down outro
    last_10_pct = ' '.join(words[max(0, word_count - word_count // 10):]).lower()
    if re.search(r'\bthanks?\s+for\s+watch\b|\bsee\s+you\s+(?:in\s+the\s+)?next\b|\bdon\'?t\s+forget\s+to\b|\bgoodbye\b|\bbye\b', last_10_pct):
        print(f"  [!] Has a wind-down outro — viewers sense the ending and leave (AP-SC-04)")
        results['issues'].append("Remove the wind-down outro. Keep the second half just as strong as the first. (AP-SC-04)")
        ap_issues += 1
    else:
        print(f"  [+] No wind-down outro detected")

    # AP-SC-05: Sequential listing (already covered in but/therefore)
    if bt_ratio < 0.8:
        print(f"  [!] Sequential 'and then' listing dominates — feels like a list, not a story (AP-SC-05)")
        ap_issues += 1
    else:
        print(f"  [+] Causal flow dominates over sequential listing")

    if ap_issues == 0:
        results['strengths'].append("No anti-patterns detected. Clean script structure.")

    # ---- TITLE CHECK ----
    if title:
        print(f"\n--- TITLE CHECK ---")
        title_words = len(title.split())
        title_chars = len(title)
        print(f"  Title: \"{title}\"")
        print(f"  Words: {title_words}  |  Chars: {title_chars}")

        if title_chars > 60:
            print(f"  [!] Title may be truncated in search (>60 chars)")
            results['suggestions'].append("Title is long. YouTube may truncate it in search results.")
        if title_words < 3:
            print(f"  [!] Very short title — may lack specificity")
        else:
            print(f"  [+] Title length OK")

    # ---- OVERALL SCORE ----
    all_scores = [v['score'] for v in results['scores'].values()]
    overall = int(statistics.mean(all_scores)) if all_scores else 0
    results['overall_score'] = overall

    print(f"\n{'=' * 70}")
    print(f"  OVERALL LEARNBYLEO SCORE: {overall}/100")
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

    # Grade
    print(f"\n  GRADE: ", end='')
    if overall >= 85:
        print("A  -- Excellent. Ready for production.")
        verdict = "PASS"
    elif overall >= 70:
        print("B  -- Good foundation. Fix the issues above.")
        verdict = "PASS"
    elif overall >= 55:
        print("C  -- Needs work. Address the red flags before proceeding.")
        verdict = "WARN"
    elif overall >= 40:
        print("D  -- Significant gaps. Rewrite recommended.")
        verdict = "FAIL"
    else:
        print("F  -- Does not meet playbook standards. Start over.")
        verdict = "FAIL"

    print(f"\n  VERDICT: {verdict}")
    print()
    return results


# ============================================================================
# CLI
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nQuick test: echo your script text | python check_learnbyleo_script.py -")
        sys.exit(0)

    script_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None

    if script_path == '-':
        script_text = sys.stdin.read()
    else:
        with open(script_path, 'r') as f:
            script_text = f.read()

    if not script_text.strip():
        print("Error: Empty script")
        sys.exit(1)

    results = check_script(script_text, title)

    # Exit code: 0 for PASS/WARN, 1 for FAIL
    if results['overall_score'] < 40:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
