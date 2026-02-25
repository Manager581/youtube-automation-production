#!/usr/bin/env python3
"""
Complete Fern Channel Analysis Pipeline
Extracts the FULL Fern Formula from 30 videos using transcripts, metadata, and engagement data.

Analyzes:
- Script structure (hooks, re-engagement, pacing, word choice)
- Curiosity gap patterns (questions posed → answers delivered)
- Emotional arc (tension/release, sentiment flow)
- Title formulas (patterns, emotional triggers, word count)
- Description structure (links, CTAs, formatting)
- Engagement patterns (YouTube heatmaps, like/view ratios)
- Duration sweet spots
- Upload timing patterns
- Top vs bottom performer comparison
- Tag and topic patterns

Output:
- analysis/fern/FERN_FORMULA.json (complete data)
- analysis/fern/FERN_FORMULA_SOP.md (human-readable playbook)
"""

import json
import re
import os
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import statistics

# ============================================================================
# VTT PARSER - Convert YouTube auto-captions to analyzable format
# ============================================================================

def parse_vtt(vtt_path):
    """Parse VTT subtitle file into word-level data and full text.

    YouTube auto-caption VTTs use a rolling format:
    - Line 1 (plain text): previously accumulated text (REPEATED - skip this)
    - Line 2 (with <c> tags): NEW words being added with inline timestamps

    We only extract the NEW words from lines containing <c> tags,
    plus standalone plain-text cues that don't have a tagged counterpart.
    """
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove header
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)

    # Split into cue blocks (separated by blank lines)
    cues = re.split(r'\n\n+', content.strip())

    words = []
    full_text_parts = []

    for cue in cues:
        cue_lines = cue.strip().split('\n')
        if not cue_lines:
            continue

        # First line should be timestamp
        ts_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})', cue_lines[0].strip())
        if not ts_match:
            continue

        start_sec = _ts_to_seconds(ts_match.group(1))
        end_sec = _ts_to_seconds(ts_match.group(2))

        text_lines = cue_lines[1:]
        if not text_lines:
            continue

        # Check if any line has <c> tags (inline word timestamps) = NEW words
        tagged_lines = [l for l in text_lines if '<c>' in l or ('<00:' in l and '<c>' in l)]

        if tagged_lines:
            for line in tagged_lines:
                # Get the leading word (before first < tag)
                leading = re.match(r'^([^<]+)', line)
                if leading:
                    lead_word = leading.group(1).strip()
                    # Clean HTML entities
                    lead_word = lead_word.replace('&gt;', '').replace('&lt;', '').replace('&amp;', '&')
                    lead_word = lead_word.strip().strip('>').strip()
                    if lead_word:
                        words.append({'word': lead_word, 'start': start_sec, 'end': start_sec})
                        full_text_parts.append(lead_word)

                # Extract words from <c>...</c> tags with timestamps
                # Pattern: <HH:MM:SS.mmm><c> word</c>
                tag_matches = re.findall(r'<(\d{2}:\d{2}:\d{2}\.\d{3})><c>\s*([^<]+)</c>', line)
                for ts_str, word_text in tag_matches:
                    word_text = word_text.strip()
                    if word_text:
                        word_text = word_text.replace('&gt;', '').replace('&lt;', '').replace('&amp;', '&')
                        word_text = word_text.strip().strip('>').strip()
                        if word_text:
                            word_ts = _ts_to_seconds(ts_str)
                            words.append({'word': word_text, 'start': word_ts, 'end': word_ts})
                            full_text_parts.append(word_text)
        else:
            # Plain text cue - skip very short duration cues (repeat/echo cues)
            duration = end_sec - start_sec
            if duration < 0.02:
                continue

            # Genuine standalone text cue
            raw_text = ' '.join(l.strip() for l in text_lines)
            clean_text = raw_text.replace('&gt;', '').replace('&lt;', '').replace('&amp;', '&')
            clean_text = re.sub(r'[>]+\s*', '', clean_text).strip()

            if clean_text:
                word_list = clean_text.split()
                time_per_word = duration / len(word_list) if word_list else 0
                for j, w in enumerate(word_list):
                    words.append({
                        'word': w,
                        'start': start_sec + (j * time_per_word),
                        'end': start_sec + ((j + 1) * time_per_word)
                    })
                    full_text_parts.append(w)

    full_text = ' '.join(full_text_parts)
    return {'words': words, 'text': full_text}


def _ts_to_seconds(ts):
    """Convert HH:MM:SS.mmm to seconds"""
    parts = ts.split(':')
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


# ============================================================================
# SCRIPT STRUCTURE ANALYZER
# ============================================================================

class ScriptAnalyzer:
    """Deep analysis of script patterns"""

    def __init__(self):
        self.hook_patterns = [
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

        self.reengagement_patterns = [
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

        self.emotional_words = {
            'fear': ['terrifying', 'horrifying', 'feared', 'panic', 'nightmare', 'deadly', 'dangerous', 'threat', 'terror', 'horror'],
            'mystery': ['mysterious', 'unknown', 'secret', 'hidden', 'strange', 'bizarre', 'enigma', 'puzzle', 'unexplained', 'cryptic'],
            'shock': ['shocking', 'unbelievable', 'incredible', 'jaw-dropping', 'mind-blowing', 'insane', 'crazy', 'unprecedented'],
            'power': ['powerful', 'dominant', 'unstoppable', 'massive', 'enormous', 'colossal', 'supreme', 'ruthless'],
            'tragedy': ['devastating', 'heartbreaking', 'tragic', 'catastrophic', 'disaster', 'destroyed', 'loss', 'death', 'killed'],
            'triumph': ['survived', 'escaped', 'overcame', 'breakthrough', 'victory', 'succeeded', 'genius', 'brilliant', 'hero'],
        }

    def analyze_script(self, transcript_data, video_duration):
        """Complete script analysis"""
        words = transcript_data['words']
        full_text = transcript_data['text']

        if not words:
            return {}

        # Split into sentences
        sentences = self._split_sentences(words)

        # Analyze different aspects
        hook_analysis = self._analyze_hook(sentences[:10], words[:100])
        structure = self._analyze_structure(sentences, video_duration)
        reengagement = self._analyze_reengagement(sentences)
        pacing = self._analyze_pacing(words, video_duration)
        emotional_words = self._analyze_emotional_language(full_text)
        word_patterns = self._analyze_word_patterns(full_text)

        return {
            'hook': hook_analysis,
            'structure': structure,
            'reengagement': reengagement,
            'pacing': pacing,
            'emotional_language': emotional_words,
            'word_patterns': word_patterns,
            'total_words': len(words),
            'total_sentences': len(sentences),
        }

    def _split_sentences(self, words):
        """Split words into sentences with timestamps"""
        sentences = []
        current = {'words': [], 'text': '', 'start': None, 'end': None}

        for w in words:
            word_text = w['word']
            if current['start'] is None:
                current['start'] = w['start']
            current['words'].append(w)
            current['text'] += word_text + ' '
            current['end'] = w['end']

            if word_text.rstrip().endswith(('.', '?', '!')):
                sentences.append({
                    'text': current['text'].strip(),
                    'start': current['start'],
                    'end': current['end'],
                    'word_count': len(current['words'])
                })
                current = {'words': [], 'text': '', 'start': None, 'end': None}

        if current['text']:
            sentences.append({
                'text': current['text'].strip(),
                'start': current['start'],
                'end': current['end'],
                'word_count': len(current['words'])
            })

        return sentences

    def _analyze_hook(self, first_sentences, first_words):
        """Analyze the opening hook (first 30 seconds)"""
        # Get text from first 30 seconds
        hook_words = [w for w in first_words if w['start'] < 30]
        hook_text = ' '.join(w['word'] for w in hook_words).lower()

        hook_types = []
        for pattern, name in self.hook_patterns:
            if re.search(pattern, hook_text, re.IGNORECASE):
                hook_types.append(name)

        # Check if hook uses a quote/dialogue
        has_quote = bool(re.search(r'"[^"]+"|\'[^\']+\'', hook_text))

        # Check if hook starts with action/scene
        first_sentence = first_sentences[0]['text'] if first_sentences else ''

        return {
            'hook_types': hook_types,
            'has_quote': has_quote,
            'first_sentence': first_sentence,
            'hook_word_count': len(hook_words),
            'hook_duration_sec': hook_words[-1]['end'] if hook_words else 0,
        }

    def _analyze_structure(self, sentences, video_duration):
        """Analyze overall script structure: intro/body/conclusion"""
        if not sentences or video_duration == 0:
            return {}

        total_sentences = len(sentences)

        # Define sections (approximate)
        intro_end = video_duration * 0.1  # First 10%
        body_end = video_duration * 0.85  # Until 85%

        intro_sentences = [s for s in sentences if s['start'] < intro_end]
        body_sentences = [s for s in sentences if intro_end <= s['start'] < body_end]
        conclusion_sentences = [s for s in sentences if s['start'] >= body_end]

        return {
            'intro_sentence_count': len(intro_sentences),
            'body_sentence_count': len(body_sentences),
            'conclusion_sentence_count': len(conclusion_sentences),
            'intro_pct': len(intro_sentences) / total_sentences * 100 if total_sentences else 0,
            'body_pct': len(body_sentences) / total_sentences * 100 if total_sentences else 0,
            'conclusion_pct': len(conclusion_sentences) / total_sentences * 100 if total_sentences else 0,
        }

    def _analyze_reengagement(self, sentences):
        """Find re-engagement hooks throughout the script"""
        hooks = []
        for i, s in enumerate(sentences):
            text = s['text'].lower()
            for pattern, name in self.reengagement_patterns:
                if re.search(pattern, text):
                    hooks.append({
                        'type': name,
                        'time': s['start'],
                        'text': s['text'][:120],
                        'sentence_index': i
                    })
                    break

        # Calculate frequency
        if sentences and sentences[-1]['end'] > 0:
            total_duration = sentences[-1]['end']
            hooks_per_minute = (len(hooks) / total_duration) * 60 if total_duration > 0 else 0
        else:
            hooks_per_minute = 0

        # Group by type
        type_counts = Counter(h['type'] for h in hooks)

        return {
            'total_hooks': len(hooks),
            'hooks_per_minute': hooks_per_minute,
            'hook_types': dict(type_counts),
            'hooks': hooks[:20],  # First 20 for reference
        }

    def _analyze_pacing(self, words, video_duration):
        """Analyze speaking pace over time"""
        if not words or video_duration == 0:
            return {}

        # Calculate WPM in 60-second windows
        window_size = 60
        wpm_timeline = []

        for start in range(0, int(video_duration), window_size):
            end = start + window_size
            window_words = [w for w in words if start <= w['start'] < end]
            wpm = len(window_words)  # words per 60 seconds = WPM
            wpm_timeline.append({
                'time': start,
                'wpm': wpm
            })

        wpm_values = [w['wpm'] for w in wpm_timeline if w['wpm'] > 0]

        return {
            'overall_wpm': len(words) / (video_duration / 60) if video_duration > 0 else 0,
            'avg_wpm': statistics.mean(wpm_values) if wpm_values else 0,
            'min_wpm': min(wpm_values) if wpm_values else 0,
            'max_wpm': max(wpm_values) if wpm_values else 0,
            'wpm_variance': statistics.variance(wpm_values) if len(wpm_values) > 1 else 0,
            'wpm_timeline': wpm_timeline,
        }

    def _analyze_emotional_language(self, full_text):
        """Analyze emotional word usage"""
        text_lower = full_text.lower()
        word_count = len(full_text.split())

        emotion_counts = {}
        emotion_examples = {}
        for emotion, word_list in self.emotional_words.items():
            count = sum(text_lower.count(w) for w in word_list)
            emotion_counts[emotion] = count
            # Find example usages
            examples = []
            for w in word_list:
                if w in text_lower:
                    examples.append(w)
            emotion_examples[emotion] = examples

        total_emotional = sum(emotion_counts.values())
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'neutral'

        return {
            'emotion_counts': emotion_counts,
            'dominant_emotion': dominant_emotion,
            'emotional_density': total_emotional / word_count * 100 if word_count > 0 else 0,
            'emotion_examples': emotion_examples,
        }

    def _analyze_word_patterns(self, full_text):
        """Analyze word-level patterns"""
        words = full_text.lower().split()
        word_count = len(words)

        # Common words (excluding stop words)
        stop_words = {'the', 'a', 'an', 'is', 'was', 'were', 'are', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'can', 'shall',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'as', 'into', 'through', 'during', 'before', 'after', 'above',
                      'below', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet',
                      'both', 'either', 'neither', 'each', 'every', 'all', 'any',
                      'few', 'more', 'most', 'other', 'some', 'such', 'no',
                      'that', 'this', 'these', 'those', 'it', 'its', 'he', 'she',
                      'him', 'her', 'his', 'they', 'them', 'their', 'we', 'us',
                      'our', 'you', 'your', 'i', 'me', 'my', 'who', 'which',
                      'what', 'when', 'where', 'how', 'than', 'then', 'just',
                      'about', 'up', 'out', 'if', 'because', 'while', 'also'}

        content_words = [w for w in words if w not in stop_words and len(w) > 2]
        top_words = Counter(content_words).most_common(30)

        # Sentence starters
        sentences = re.split(r'[.!?]+', full_text)
        starters = [s.strip().split()[0].lower() for s in sentences if s.strip() and len(s.strip().split()) > 0]
        top_starters = Counter(starters).most_common(15)

        # Second person usage ("you", "your")
        you_count = sum(1 for w in words if w in ('you', 'your', "you're", "you'd", "you'll", "you've"))
        you_density = you_count / word_count * 100 if word_count > 0 else 0

        # Questions
        question_count = full_text.count('?')

        return {
            'total_words': word_count,
            'unique_words': len(set(words)),
            'vocabulary_richness': len(set(words)) / word_count if word_count > 0 else 0,
            'top_content_words': top_words,
            'top_sentence_starters': top_starters,
            'you_density_pct': you_density,
            'question_count': question_count,
            'questions_per_1000_words': question_count / word_count * 1000 if word_count > 0 else 0,
            'avg_sentence_length': word_count / len(sentences) if sentences else 0,
        }


# ============================================================================
# CURIOSITY GAP DETECTOR (adapted for VTT data)
# ============================================================================

class CuriosityAnalyzer:
    """Detect curiosity gap patterns in transcripts"""

    QUESTION_PATTERNS = [
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

    def analyze(self, transcript_data, video_duration):
        """Find curiosity gaps"""
        words = transcript_data['words']
        if not words:
            return {}

        sentences = self._split_sentences(words)
        gaps = []

        for i, sentence in enumerate(sentences):
            text_lower = sentence['text'].lower()

            # Check for curiosity triggers
            gap_type = None
            for pattern in self.QUESTION_PATTERNS:
                if re.search(pattern, text_lower):
                    gap_type = 'question'
                    break
            if not gap_type:
                for pattern in self.CLIFFHANGER_PATTERNS:
                    if re.search(pattern, text_lower):
                        gap_type = 'cliffhanger'
                        break

            if gap_type:
                # Look for resolution in next 15 sentences
                resolution = None
                for j in range(i + 1, min(i + 15, len(sentences))):
                    res_text = sentences[j]['text'].lower()
                    for pattern in self.RESOLUTION_PATTERNS:
                        if re.search(pattern, res_text):
                            resolution = {
                                'text': sentences[j]['text'][:100],
                                'time': sentences[j]['start'],
                                'sentence_idx': j
                            }
                            break
                    if resolution:
                        break

                gap_duration = (resolution['time'] - sentence['start']) if resolution else None

                gaps.append({
                    'type': gap_type,
                    'trigger_text': sentence['text'][:120],
                    'trigger_time': sentence['start'],
                    'resolution': resolution,
                    'duration': gap_duration,
                })

        # Stats
        resolved_gaps = [g for g in gaps if g['duration'] is not None]
        avg_duration = statistics.mean([g['duration'] for g in resolved_gaps]) if resolved_gaps else 0
        gaps_per_min = (len(gaps) / (video_duration / 60)) if video_duration > 0 else 0

        type_counts = Counter(g['type'] for g in gaps)

        return {
            'total_gaps': len(gaps),
            'resolved_gaps': len(resolved_gaps),
            'unresolved_gaps': len(gaps) - len(resolved_gaps),
            'avg_gap_duration': avg_duration,
            'gaps_per_minute': gaps_per_min,
            'type_distribution': dict(type_counts),
            'gaps': gaps[:30],  # First 30 for reference
        }

    def _split_sentences(self, words):
        """Split into sentences"""
        sentences = []
        current = {'text': '', 'start': None, 'end': None}
        for w in words:
            if current['start'] is None:
                current['start'] = w['start']
            current['text'] += w['word'] + ' '
            current['end'] = w['end']
            if w['word'].rstrip().endswith(('.', '?', '!')):
                sentences.append({
                    'text': current['text'].strip(),
                    'start': current['start'],
                    'end': current['end']
                })
                current = {'text': '', 'start': None, 'end': None}
        if current['text']:
            sentences.append({'text': current['text'].strip(), 'start': current['start'], 'end': current['end']})
        return sentences


# ============================================================================
# TITLE & THUMBNAIL ANALYZER
# ============================================================================

class TitleAnalyzer:
    """Analyze title patterns across all videos"""

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
        'colon_structure': r':',
        'dash_structure': r'\s[-–—]\s',
    }

    def analyze_titles(self, videos):
        """Analyze all video titles"""
        titles = [(v['title'], v['views']) for v in videos]

        pattern_counts = defaultdict(int)
        pattern_views = defaultdict(list)

        for title, views in titles:
            title_lower = title.lower()
            for pattern_name, pattern in self.TITLE_PATTERNS.items():
                if re.search(pattern, title_lower):
                    pattern_counts[pattern_name] += 1
                    pattern_views[pattern_name].append(views)

        # Avg views per pattern
        pattern_performance = {}
        for name, view_list in pattern_views.items():
            pattern_performance[name] = {
                'count': pattern_counts[name],
                'avg_views': statistics.mean(view_list),
                'pct_of_videos': pattern_counts[name] / len(titles) * 100,
            }

        # Word counts
        word_counts = [len(t.split()) for t, _ in titles]
        char_counts = [len(t) for t, _ in titles]

        # Title words that correlate with high views
        all_title_words = []
        for title, views in titles:
            for word in title.lower().split():
                clean = re.sub(r'[^\w]', '', word)
                if clean and len(clean) > 2:
                    all_title_words.append((clean, views))

        word_avg_views = defaultdict(list)
        for word, views in all_title_words:
            word_avg_views[word].append(views)

        high_performing_words = {
            w: statistics.mean(v) for w, v in word_avg_views.items()
            if len(v) >= 2  # Appears in at least 2 titles
        }
        top_title_words = sorted(high_performing_words.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            'pattern_performance': pattern_performance,
            'avg_word_count': statistics.mean(word_counts),
            'avg_char_count': statistics.mean(char_counts),
            'word_count_range': (min(word_counts), max(word_counts)),
            'high_performing_title_words': top_title_words,
            'all_titles': [(t, v) for t, v in sorted(titles, key=lambda x: x[1], reverse=True)],
        }


# ============================================================================
# ENGAGEMENT ANALYZER (heatmaps, like ratios, etc.)
# ============================================================================

class EngagementAnalyzer:
    """Analyze YouTube engagement data"""

    def analyze_video(self, info_data, video_duration):
        """Analyze engagement for a single video"""
        views = info_data.get('view_count', 0)
        likes = info_data.get('like_count', 0)
        comments = info_data.get('comment_count', 0)
        heatmap = info_data.get('heatmap', [])

        result = {
            'views': views,
            'likes': likes,
            'comments': comments,
            'like_ratio': likes / views * 100 if views > 0 else 0,
            'comment_ratio': comments / views * 100 if views > 0 else 0,
            'engagement_rate': (likes + comments) / views * 100 if views > 0 else 0,
        }

        # Heatmap analysis (viewer retention proxy)
        if heatmap:
            values = [h['value'] for h in heatmap]
            result['heatmap'] = {
                'avg_engagement': statistics.mean(values),
                'min_engagement': min(values),
                'max_engagement': max(values),
                'engagement_variance': statistics.variance(values) if len(values) > 1 else 0,

                # Where do viewers engage most?
                'peak_time_pct': values.index(max(values)) / len(values) * 100,
                'valley_time_pct': values.index(min(values)) / len(values) * 100,

                # Intro retention (first 10%)
                'intro_engagement': statistics.mean(values[:max(1, len(values) // 10)]),
                # Mid engagement (40-60%)
                'mid_engagement': statistics.mean(values[len(values) * 4 // 10:len(values) * 6 // 10]) if len(values) > 5 else 0,
                # End engagement (last 10%)
                'end_engagement': statistics.mean(values[-max(1, len(values) // 10):]),

                # Drop-off points (where engagement drops >20% from previous)
                'major_dropoffs': self._find_dropoffs(heatmap, video_duration),

                # Re-engagement spikes
                'spikes': self._find_spikes(heatmap, video_duration),
            }

        return result

    def _find_dropoffs(self, heatmap, duration):
        """Find where viewers drop off significantly"""
        dropoffs = []
        for i in range(1, len(heatmap)):
            prev_val = heatmap[i - 1]['value']
            curr_val = heatmap[i]['value']
            if prev_val > 0 and (curr_val - prev_val) / prev_val < -0.2:
                time_pct = i / len(heatmap) * 100
                time_sec = heatmap[i]['start_time']
                dropoffs.append({
                    'time_pct': time_pct,
                    'time_sec': time_sec,
                    'drop_magnitude': (curr_val - prev_val) / prev_val * 100,
                })
        return dropoffs[:5]  # Top 5

    def _find_spikes(self, heatmap, duration):
        """Find re-engagement spikes"""
        spikes = []
        for i in range(1, len(heatmap)):
            prev_val = heatmap[i - 1]['value']
            curr_val = heatmap[i]['value']
            if prev_val > 0 and (curr_val - prev_val) / prev_val > 0.15:
                time_pct = i / len(heatmap) * 100
                time_sec = heatmap[i]['start_time']
                spikes.append({
                    'time_pct': time_pct,
                    'time_sec': time_sec,
                    'spike_magnitude': (curr_val - prev_val) / prev_val * 100,
                })
        return spikes[:5]  # Top 5


# ============================================================================
# DESCRIPTION ANALYZER
# ============================================================================

class DescriptionAnalyzer:
    """Analyze video description patterns"""

    def analyze(self, descriptions):
        """Analyze description patterns across all videos"""
        results = {
            'avg_length': 0,
            'has_sponsor': 0,
            'has_timestamps': 0,
            'has_social_links': 0,
            'has_credits': 0,
            'common_elements': [],
        }

        lengths = []
        sponsor_count = 0
        timestamp_count = 0
        social_count = 0
        credits_count = 0

        for desc in descriptions:
            if not desc:
                continue
            desc_lower = desc.lower()
            lengths.append(len(desc))

            if any(w in desc_lower for w in ['sponsor', 'ad)', 'discount', 'code ', 'promo', 'incogni', 'surfshark', 'nordvpn', 'brilliant', 'skillshare']):
                sponsor_count += 1
            if re.search(r'\d{1,2}:\d{2}', desc):
                timestamp_count += 1
            if any(w in desc_lower for w in ['twitter', 'instagram', 'tiktok', 'discord', 'patreon', 'x.com']):
                social_count += 1
            if any(w in desc_lower for w in ['thanks to', 'credit', 'sources:', 'references', 'music by', 'footage']):
                credits_count += 1

        total = len(descriptions) if descriptions else 1

        return {
            'avg_length_chars': statistics.mean(lengths) if lengths else 0,
            'sponsor_pct': sponsor_count / total * 100,
            'timestamps_pct': timestamp_count / total * 100,
            'social_links_pct': social_count / total * 100,
            'credits_pct': credits_count / total * 100,
        }


# ============================================================================
# MAIN ANALYSIS PIPELINE
# ============================================================================

def run_complete_analysis():
    """Run the complete Fern analysis pipeline"""

    BASE_DIR = Path('/home/user/youtube-automation/analysis/fern')

    print("=" * 80)
    print("  COMPLETE FERN CHANNEL ANALYSIS")
    print("  Extracting the Fern Formula from 30 videos")
    print("=" * 80)

    # ---- Step 1: Load all video data ----
    print("\n[1/8] Loading all video data...")

    videos = []
    video_dirs = sorted([d for d in BASE_DIR.iterdir() if d.is_dir()])

    for vdir in video_dirs:
        video_id = vdir.name

        # Load metadata
        info_file = vdir / 'video.info.json'
        vtt_file = vdir / 'video.en.vtt'
        meta_file = vdir / 'metadata.json'

        if not info_file.exists():
            print(f"  Skipping {video_id}: no info.json")
            continue

        with open(info_file) as f:
            info = json.load(f)

        # Parse transcript
        transcript = None
        if vtt_file.exists():
            transcript = parse_vtt(vtt_file)

        videos.append({
            'id': video_id,
            'title': info.get('title', ''),
            'views': info.get('view_count', 0),
            'likes': info.get('like_count', 0),
            'comments': info.get('comment_count', 0),
            'duration': info.get('duration', 0),
            'upload_date': info.get('upload_date', ''),
            'description': info.get('description', ''),
            'tags': info.get('tags', []),
            'heatmap': info.get('heatmap', []),
            'info': info,
            'transcript': transcript,
            'dir': vdir,
        })

    # Sort by views
    videos.sort(key=lambda v: v['views'], reverse=True)
    print(f"  Loaded {len(videos)} videos")
    for i, v in enumerate(videos[:5], 1):
        print(f"  #{i}: {v['views']:>10,} views | {v['duration']//60}:{v['duration']%60:02d} | {v['title'][:60]}")
    print(f"  ... and {len(videos) - 5} more")

    # ---- Step 2: Analyze each video's script ----
    print("\n[2/8] Analyzing scripts (hooks, pacing, emotions, re-engagement)...")
    script_analyzer = ScriptAnalyzer()
    curiosity_analyzer = CuriosityAnalyzer()
    engagement_analyzer = EngagementAnalyzer()

    for v in videos:
        if v['transcript']:
            v['script_analysis'] = script_analyzer.analyze_script(v['transcript'], v['duration'])
            v['curiosity_gaps'] = curiosity_analyzer.analyze(v['transcript'], v['duration'])
        else:
            v['script_analysis'] = {}
            v['curiosity_gaps'] = {}

        v['engagement'] = engagement_analyzer.analyze_video(v['info'], v['duration'])

    print(f"  Scripts analyzed for {sum(1 for v in videos if v.get('script_analysis'))} videos")

    # ---- Step 3: Analyze titles ----
    print("\n[3/8] Analyzing title patterns...")
    title_analyzer = TitleAnalyzer()
    title_analysis = title_analyzer.analyze_titles(videos)
    print(f"  Average title: {title_analysis['avg_word_count']:.1f} words, {title_analysis['avg_char_count']:.0f} chars")

    # ---- Step 4: Analyze descriptions ----
    print("\n[4/8] Analyzing description patterns...")
    desc_analyzer = DescriptionAnalyzer()
    desc_analysis = desc_analyzer.analyze([v['description'] for v in videos])
    print(f"  Avg description: {desc_analysis['avg_length_chars']:.0f} chars")
    print(f"  Sponsor rate: {desc_analysis['sponsor_pct']:.0f}%")

    # ---- Step 5: Cross-video patterns ----
    print("\n[5/8] Extracting cross-video patterns...")

    # Duration analysis
    durations = [v['duration'] for v in videos]
    duration_analysis = {
        'avg_duration_sec': statistics.mean(durations),
        'avg_duration_min': statistics.mean(durations) / 60,
        'min_duration_min': min(durations) / 60,
        'max_duration_min': max(durations) / 60,
        'sweet_spot_min': statistics.median(durations) / 60,
    }
    print(f"  Duration sweet spot: {duration_analysis['sweet_spot_min']:.1f} min")

    # Upload timing
    upload_dates = [v['upload_date'] for v in videos if v['upload_date']]
    upload_analysis = _analyze_upload_timing(upload_dates)

    # Tag analysis
    all_tags = []
    for v in videos:
        all_tags.extend(v['tags'])
    tag_counts = Counter(all_tags).most_common(30)

    # ---- Step 6: Top vs Bottom Comparison ----
    print("\n[6/8] Comparing top 30% vs bottom 30% performers...")

    n = len(videos)
    top_n = max(1, n * 30 // 100)
    top_videos = videos[:top_n]
    bottom_videos = videos[-top_n:]

    comparison = _compare_top_bottom(top_videos, bottom_videos)

    # ---- Step 7: Engagement heatmap patterns ----
    print("\n[7/8] Analyzing engagement heatmap patterns...")
    heatmap_analysis = _analyze_heatmap_patterns(videos)

    # ---- Step 8: Generate Formula ----
    print("\n[8/8] Generating Fern Formula...")

    formula = {
        'metadata': {
            'creator': 'fern',
            'channel': '@fern-tv',
            'analysis_date': datetime.now().isoformat(),
            'total_videos_analyzed': len(videos),
            'channel_subscribers': videos[0]['info'].get('channel_follower_count', 0),
        },
        'title_formula': title_analysis,
        'description_formula': desc_analysis,
        'duration_formula': duration_analysis,
        'upload_timing': upload_analysis,
        'tag_patterns': tag_counts,
        'engagement_patterns': {
            'avg_like_ratio': statistics.mean([v['engagement']['like_ratio'] for v in videos]),
            'avg_comment_ratio': statistics.mean([v['engagement']['comment_ratio'] for v in videos]),
            'avg_engagement_rate': statistics.mean([v['engagement']['engagement_rate'] for v in videos]),
        },
        'heatmap_patterns': heatmap_analysis,
        'script_formula': _aggregate_script_patterns(videos),
        'curiosity_gap_formula': _aggregate_curiosity_patterns(videos),
        'emotional_language_formula': _aggregate_emotional_patterns(videos),
        'top_vs_bottom_comparison': comparison,
        'per_video_data': [{
            'id': v['id'],
            'title': v['title'],
            'views': v['views'],
            'likes': v['likes'],
            'duration': v['duration'],
            'upload_date': v['upload_date'],
            'script_analysis': v.get('script_analysis', {}),
            'curiosity_gaps': v.get('curiosity_gaps', {}),
            'engagement': v.get('engagement', {}),
        } for v in videos],
    }

    # Save JSON
    output_json = BASE_DIR / 'FERN_FORMULA.json'
    with open(output_json, 'w') as f:
        json.dump(formula, f, indent=2, default=str)
    print(f"\n  Saved: {output_json}")

    # Generate SOP
    sop = _generate_fern_sop(formula, videos)
    output_sop = BASE_DIR / 'FERN_FORMULA_SOP.md'
    with open(output_sop, 'w') as f:
        f.write(sop)
    print(f"  Saved: {output_sop}")

    print("\n" + "=" * 80)
    print("  ANALYSIS COMPLETE!")
    print(f"  Formula: {output_json}")
    print(f"  SOP: {output_sop}")
    print("=" * 80)

    return formula


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _analyze_upload_timing(upload_dates):
    """Analyze upload frequency and timing"""
    if not upload_dates:
        return {}

    dates = []
    for d in upload_dates:
        try:
            dates.append(datetime.strptime(d, '%Y%m%d'))
        except:
            continue

    if len(dates) < 2:
        return {'dates_parsed': len(dates)}

    dates.sort()
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]

    # Day of week distribution
    day_counts = Counter(d.strftime('%A') for d in dates)

    return {
        'total_videos': len(dates),
        'date_range': f"{dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}",
        'avg_days_between_uploads': statistics.mean(gaps) if gaps else 0,
        'median_days_between_uploads': statistics.median(gaps) if gaps else 0,
        'upload_frequency': f"Every {statistics.median(gaps):.0f} days" if gaps else 'Unknown',
        'day_of_week_distribution': dict(day_counts),
        'most_common_day': day_counts.most_common(1)[0][0] if day_counts else 'Unknown',
    }


def _compare_top_bottom(top_videos, bottom_videos):
    """Compare top 30% vs bottom 30% performers"""
    comparison = {}

    # Views
    top_avg_views = statistics.mean([v['views'] for v in top_videos])
    bottom_avg_views = statistics.mean([v['views'] for v in bottom_videos])
    comparison['views'] = {
        'top_avg': top_avg_views,
        'bottom_avg': bottom_avg_views,
        'ratio': top_avg_views / bottom_avg_views if bottom_avg_views > 0 else 0,
    }

    # Duration
    top_avg_dur = statistics.mean([v['duration'] for v in top_videos])
    bottom_avg_dur = statistics.mean([v['duration'] for v in bottom_videos])
    comparison['duration'] = {
        'top_avg_min': top_avg_dur / 60,
        'bottom_avg_min': bottom_avg_dur / 60,
        'difference_min': (top_avg_dur - bottom_avg_dur) / 60,
    }

    # Script patterns
    top_with_scripts = [v for v in top_videos if v.get('script_analysis')]
    bottom_with_scripts = [v for v in bottom_videos if v.get('script_analysis')]

    if top_with_scripts and bottom_with_scripts:
        # WPM comparison
        top_wpm = [v['script_analysis']['pacing']['overall_wpm'] for v in top_with_scripts if v['script_analysis'].get('pacing')]
        bottom_wpm = [v['script_analysis']['pacing']['overall_wpm'] for v in bottom_with_scripts if v['script_analysis'].get('pacing')]

        if top_wpm and bottom_wpm:
            comparison['pacing'] = {
                'top_avg_wpm': statistics.mean(top_wpm),
                'bottom_avg_wpm': statistics.mean(bottom_wpm),
            }

        # Re-engagement hooks
        top_hooks = [v['script_analysis']['reengagement']['hooks_per_minute'] for v in top_with_scripts if v['script_analysis'].get('reengagement')]
        bottom_hooks = [v['script_analysis']['reengagement']['hooks_per_minute'] for v in bottom_with_scripts if v['script_analysis'].get('reengagement')]

        if top_hooks and bottom_hooks:
            comparison['reengagement'] = {
                'top_hooks_per_min': statistics.mean(top_hooks),
                'bottom_hooks_per_min': statistics.mean(bottom_hooks),
            }

        # Emotional language
        top_density = [v['script_analysis']['emotional_language']['emotional_density'] for v in top_with_scripts if v['script_analysis'].get('emotional_language')]
        bottom_density = [v['script_analysis']['emotional_language']['emotional_density'] for v in bottom_with_scripts if v['script_analysis'].get('emotional_language')]

        if top_density and bottom_density:
            comparison['emotional_density'] = {
                'top_avg': statistics.mean(top_density),
                'bottom_avg': statistics.mean(bottom_density),
            }

        # Dominant emotions
        top_emotions = [v['script_analysis']['emotional_language']['dominant_emotion'] for v in top_with_scripts if v['script_analysis'].get('emotional_language')]
        bottom_emotions = [v['script_analysis']['emotional_language']['dominant_emotion'] for v in bottom_with_scripts if v['script_analysis'].get('emotional_language')]

        comparison['dominant_emotions'] = {
            'top': Counter(top_emotions).most_common(3),
            'bottom': Counter(bottom_emotions).most_common(3),
        }

    # Curiosity gaps
    top_gaps = [v['curiosity_gaps'] for v in top_videos if v.get('curiosity_gaps')]
    bottom_gaps = [v['curiosity_gaps'] for v in bottom_videos if v.get('curiosity_gaps')]

    if top_gaps and bottom_gaps:
        top_gpm = [g['gaps_per_minute'] for g in top_gaps if 'gaps_per_minute' in g]
        bottom_gpm = [g['gaps_per_minute'] for g in bottom_gaps if 'gaps_per_minute' in g]

        if top_gpm and bottom_gpm:
            comparison['curiosity_gaps'] = {
                'top_gaps_per_min': statistics.mean(top_gpm),
                'bottom_gaps_per_min': statistics.mean(bottom_gpm),
            }

    # Engagement
    comparison['engagement'] = {
        'top_avg_like_ratio': statistics.mean([v['engagement']['like_ratio'] for v in top_videos]),
        'bottom_avg_like_ratio': statistics.mean([v['engagement']['like_ratio'] for v in bottom_videos]),
    }

    # Title patterns
    top_title_len = [len(v['title'].split()) for v in top_videos]
    bottom_title_len = [len(v['title'].split()) for v in bottom_videos]
    comparison['title_length'] = {
        'top_avg_words': statistics.mean(top_title_len),
        'bottom_avg_words': statistics.mean(bottom_title_len),
    }

    print(f"  Top 30% avg views: {top_avg_views:,.0f}")
    print(f"  Bottom 30% avg views: {bottom_avg_views:,.0f}")
    print(f"  Performance ratio: {comparison['views']['ratio']:.1f}x")

    return comparison


def _analyze_heatmap_patterns(videos):
    """Analyze engagement heatmap patterns across all videos"""
    all_heatmaps = []
    for v in videos:
        if v.get('heatmap'):
            values = [h['value'] for h in v['heatmap']]
            all_heatmaps.append(values)

    if not all_heatmaps:
        return {}

    # Normalize all to 100 data points
    normalized = []
    for hm in all_heatmaps:
        if len(hm) >= 10:
            step = len(hm) / 100
            norm = [hm[min(int(i * step), len(hm) - 1)] for i in range(100)]
            normalized.append(norm)

    if not normalized:
        return {}

    # Average engagement curve
    avg_curve = []
    for i in range(100):
        vals = [n[i] for n in normalized]
        avg_curve.append(statistics.mean(vals))

    # Find critical moments
    peak_idx = avg_curve.index(max(avg_curve))
    valley_idx = avg_curve.index(min(avg_curve))

    # Intro drop (first 10%)
    intro_avg = statistics.mean(avg_curve[:10])
    # Mid engagement (40-60%)
    mid_avg = statistics.mean(avg_curve[40:60])
    # End engagement (90-100%)
    end_avg = statistics.mean(avg_curve[90:])

    print(f"  Avg intro engagement: {intro_avg:.2f}")
    print(f"  Avg mid engagement: {mid_avg:.2f}")
    print(f"  Avg end engagement: {end_avg:.2f}")
    print(f"  Peak at: {peak_idx}% of video")

    return {
        'avg_engagement_curve': avg_curve,
        'peak_engagement_pct': peak_idx,
        'valley_engagement_pct': valley_idx,
        'intro_engagement': intro_avg,
        'mid_engagement': mid_avg,
        'end_engagement': end_avg,
        'intro_to_mid_retention': mid_avg / intro_avg if intro_avg > 0 else 0,
        'intro_to_end_retention': end_avg / intro_avg if intro_avg > 0 else 0,
        'videos_with_heatmaps': len(normalized),
    }


def _aggregate_script_patterns(videos):
    """Aggregate script patterns across all videos"""
    scripts = [v['script_analysis'] for v in videos if v.get('script_analysis')]
    if not scripts:
        return {}

    # Hook types across all videos
    all_hook_types = []
    for s in scripts:
        if s.get('hook', {}).get('hook_types'):
            all_hook_types.extend(s['hook']['hook_types'])
    hook_type_dist = Counter(all_hook_types)

    # Pacing
    wpm_values = [s['pacing']['overall_wpm'] for s in scripts if s.get('pacing')]

    # Re-engagement
    reengage_values = [s['reengagement']['hooks_per_minute'] for s in scripts if s.get('reengagement')]
    all_reengage_types = []
    for s in scripts:
        if s.get('reengagement', {}).get('hook_types'):
            for hook_type, count in s['reengagement']['hook_types'].items():
                all_reengage_types.extend([hook_type] * count)
    reengage_type_dist = Counter(all_reengage_types)

    # Word patterns
    you_densities = [s['word_patterns']['you_density_pct'] for s in scripts if s.get('word_patterns')]
    question_rates = [s['word_patterns']['questions_per_1000_words'] for s in scripts if s.get('word_patterns')]
    vocab_richness = [s['word_patterns']['vocabulary_richness'] for s in scripts if s.get('word_patterns')]

    # First sentences (hooks)
    first_sentences = [s['hook']['first_sentence'] for s in scripts if s.get('hook', {}).get('first_sentence')]

    return {
        'hook_types': dict(hook_type_dist),
        'top_hook_type': hook_type_dist.most_common(1)[0][0] if hook_type_dist else 'unknown',
        'pacing': {
            'avg_wpm': statistics.mean(wpm_values) if wpm_values else 0,
            'min_wpm': min(wpm_values) if wpm_values else 0,
            'max_wpm': max(wpm_values) if wpm_values else 0,
        },
        'reengagement': {
            'avg_hooks_per_min': statistics.mean(reengage_values) if reengage_values else 0,
            'hook_type_distribution': dict(reengage_type_dist),
            'top_hook_type': reengage_type_dist.most_common(1)[0][0] if reengage_type_dist else 'unknown',
        },
        'word_patterns': {
            'avg_you_density': statistics.mean(you_densities) if you_densities else 0,
            'avg_questions_per_1000': statistics.mean(question_rates) if question_rates else 0,
            'avg_vocab_richness': statistics.mean(vocab_richness) if vocab_richness else 0,
        },
        'example_hooks': first_sentences[:10],
    }


def _aggregate_curiosity_patterns(videos):
    """Aggregate curiosity gap patterns"""
    gaps = [v['curiosity_gaps'] for v in videos if v.get('curiosity_gaps')]
    if not gaps:
        return {}

    gpm = [g['gaps_per_minute'] for g in gaps if 'gaps_per_minute' in g]
    avg_durations = [g['avg_gap_duration'] for g in gaps if 'avg_gap_duration' in g and g['avg_gap_duration'] > 0]
    total_gaps = [g['total_gaps'] for g in gaps if 'total_gaps' in g]

    type_totals = defaultdict(int)
    for g in gaps:
        for t, c in g.get('type_distribution', {}).items():
            type_totals[t] += c

    return {
        'avg_gaps_per_minute': statistics.mean(gpm) if gpm else 0,
        'avg_gap_duration_sec': statistics.mean(avg_durations) if avg_durations else 0,
        'avg_gaps_per_video': statistics.mean(total_gaps) if total_gaps else 0,
        'type_distribution': dict(type_totals),
    }


def _aggregate_emotional_patterns(videos):
    """Aggregate emotional language patterns"""
    emotions = [v['script_analysis']['emotional_language'] for v in videos if v.get('script_analysis', {}).get('emotional_language')]
    if not emotions:
        return {}

    # Aggregate emotion counts
    total_counts = defaultdict(int)
    for e in emotions:
        for emotion, count in e.get('emotion_counts', {}).items():
            total_counts[emotion] += count

    densities = [e['emotional_density'] for e in emotions]
    dominant_emotions = Counter(e['dominant_emotion'] for e in emotions)

    return {
        'total_emotion_counts': dict(total_counts),
        'avg_emotional_density': statistics.mean(densities) if densities else 0,
        'dominant_emotions': dominant_emotions.most_common(5),
        'emotion_ranking': sorted(total_counts.items(), key=lambda x: x[1], reverse=True),
    }


# ============================================================================
# SOP GENERATOR
# ============================================================================

def _generate_fern_sop(formula, videos):
    """Generate human-readable Fern Formula SOP"""

    sop = """# FERN PRODUCTION FORMULA - COMPLETE SOP
## Extracted from {n} videos | {subs:,} subscribers | Channel: @fern-tv

---

""".format(
        n=formula['metadata']['total_videos_analyzed'],
        subs=formula['metadata']['channel_subscribers']
    )

    # ---- TITLE FORMULA ----
    tf = formula['title_formula']
    sop += """## 1. TITLE FORMULA

**Target**: {avg_words:.0f} words, {avg_chars:.0f} characters

### Highest-Performing Title Patterns:
""".format(avg_words=tf['avg_word_count'], avg_chars=tf['avg_char_count'])

    sorted_patterns = sorted(tf['pattern_performance'].items(), key=lambda x: x[1]['avg_views'], reverse=True)
    for pattern, data in sorted_patterns[:10]:
        sop += f"- **{pattern.replace('_', ' ').title()}**: {data['pct_of_videos']:.0f}% of videos, avg {data['avg_views']:,.0f} views\n"

    sop += "\n### Top 10 Titles (by views):\n"
    for title, views in tf['all_titles'][:10]:
        sop += f"- {views:>10,} | {title}\n"

    sop += "\n### High-Performing Title Words:\n"
    for word, avg_views in tf['high_performing_title_words'][:15]:
        sop += f"- \"{word}\" -> avg {avg_views:,.0f} views\n"

    # ---- DURATION FORMULA ----
    df = formula['duration_formula']
    sop += """
---

## 2. DURATION FORMULA

- **Sweet Spot**: {sweet:.1f} minutes (median)
- **Average**: {avg:.1f} minutes
- **Range**: {min:.1f} - {max:.1f} minutes

""".format(
        sweet=df['sweet_spot_min'],
        avg=df['avg_duration_min'],
        min=df['min_duration_min'],
        max=df['max_duration_min']
    )

    # ---- SCRIPT FORMULA ----
    sf = formula['script_formula']
    sop += """---

## 3. SCRIPT FORMULA

### Opening Hook (First 30 seconds)
"""
    if sf.get('hook_types'):
        sop += "**Most common hook types:**\n"
        for hook_type, count in sorted(sf['hook_types'].items(), key=lambda x: x[1], reverse=True):
            sop += f"- {hook_type.replace('_', ' ').title()}: used {count} times\n"

    sop += "\n**Example opening lines:**\n"
    for ex in sf.get('example_hooks', [])[:5]:
        sop += f"- \"{ex[:100]}\"\n"

    sop += """
### Pacing
- **Average WPM**: {wpm:.0f} words per minute
- **Range**: {min_wpm:.0f} - {max_wpm:.0f} WPM

### Re-engagement Hooks
- **Frequency**: {hooks_per_min:.2f} hooks per minute (1 every {secs:.0f} seconds)
""".format(
        wpm=sf['pacing']['avg_wpm'],
        min_wpm=sf['pacing']['min_wpm'],
        max_wpm=sf['pacing']['max_wpm'],
        hooks_per_min=sf['reengagement']['avg_hooks_per_min'],
        secs=60 / sf['reengagement']['avg_hooks_per_min'] if sf['reengagement']['avg_hooks_per_min'] > 0 else 999,
    )

    if sf['reengagement'].get('hook_type_distribution'):
        sop += "\n**Re-engagement hook types:**\n"
        for htype, count in sorted(sf['reengagement']['hook_type_distribution'].items(), key=lambda x: x[1], reverse=True):
            sop += f"- {htype.replace('_', ' ').title()}: {count} uses\n"

    sop += """
### Word Choice
- **Second-person density**: {you:.2f}% (use of "you/your")
- **Questions**: {q:.1f} per 1,000 words
- **Vocabulary richness**: {vr:.3f}
""".format(
        you=sf['word_patterns']['avg_you_density'],
        q=sf['word_patterns']['avg_questions_per_1000'],
        vr=sf['word_patterns']['avg_vocab_richness'],
    )

    # ---- CURIOSITY GAPS ----
    cg = formula['curiosity_gap_formula']
    sop += """
---

## 4. CURIOSITY GAP FORMULA

- **Frequency**: {gpm:.2f} gaps per minute ({per_vid:.0f} gaps per video)
- **Average gap duration**: {dur:.1f} seconds
""".format(
        gpm=cg.get('avg_gaps_per_minute', 0),
        per_vid=cg.get('avg_gaps_per_video', 0),
        dur=cg.get('avg_gap_duration_sec', 0),
    )

    if cg.get('type_distribution'):
        sop += "\n**Gap types:**\n"
        for gtype, count in sorted(cg['type_distribution'].items(), key=lambda x: x[1], reverse=True):
            sop += f"- {gtype.title()}: {count} total\n"

    # ---- EMOTIONAL LANGUAGE ----
    el = formula['emotional_language_formula']
    sop += """
---

## 5. EMOTIONAL LANGUAGE FORMULA

- **Emotional density**: {density:.2f}% of all words are emotional
""".format(density=el.get('avg_emotional_density', 0))

    if el.get('emotion_ranking'):
        sop += "\n**Emotion ranking (most to least used):**\n"
        for emotion, count in el['emotion_ranking']:
            sop += f"- {emotion.title()}: {count} uses\n"

    if el.get('dominant_emotions'):
        sop += "\n**Most common dominant emotion per video:**\n"
        for emotion, count in el['dominant_emotions']:
            sop += f"- {emotion.title()}: dominant in {count} videos\n"

    # ---- ENGAGEMENT PATTERNS ----
    ep = formula['engagement_patterns']
    hp = formula['heatmap_patterns']
    sop += """
---

## 6. ENGAGEMENT PATTERNS

### Ratios
- **Like ratio**: {lr:.2f}% of viewers like
- **Comment ratio**: {cr:.3f}% of viewers comment
- **Total engagement rate**: {er:.2f}%

### Viewer Retention (Heatmap Analysis)
""".format(
        lr=ep['avg_like_ratio'],
        cr=ep['avg_comment_ratio'],
        er=ep['avg_engagement_rate'],
    )

    if hp:
        sop += """- **Intro engagement**: {intro:.2f}
- **Mid engagement**: {mid:.2f}
- **End engagement**: {end:.2f}
- **Mid-to-intro retention**: {m2i:.0f}%
- **End-to-intro retention**: {e2i:.0f}%
- **Peak engagement at**: {peak}% through video
""".format(
            intro=hp['intro_engagement'],
            mid=hp['mid_engagement'],
            end=hp['end_engagement'],
            m2i=hp['intro_to_mid_retention'] * 100,
            e2i=hp['intro_to_end_retention'] * 100,
            peak=hp['peak_engagement_pct'],
        )

    # ---- UPLOAD TIMING ----
    ut = formula.get('upload_timing', {})
    sop += """
---

## 7. UPLOAD TIMING

- **Frequency**: {freq}
- **Most common day**: {day}
""".format(
        freq=ut.get('upload_frequency', 'Unknown'),
        day=ut.get('most_common_day', 'Unknown'),
    )

    if ut.get('day_of_week_distribution'):
        sop += "\n**Day distribution:**\n"
        for day, count in sorted(ut['day_of_week_distribution'].items(), key=lambda x: x[1], reverse=True):
            sop += f"- {day}: {count} uploads\n"

    # ---- DESCRIPTION FORMULA ----
    sop += """
---

## 8. DESCRIPTION FORMULA

- **Average length**: {length:.0f} characters
- **Has sponsor/ad**: {sponsor:.0f}% of videos
- **Has timestamps**: {ts:.0f}% of videos
- **Has social links**: {social:.0f}% of videos
- **Has credits/sources**: {credits:.0f}% of videos
""".format(
        length=formula['description_formula']['avg_length_chars'],
        sponsor=formula['description_formula']['sponsor_pct'],
        ts=formula['description_formula']['timestamps_pct'],
        social=formula['description_formula']['social_links_pct'],
        credits=formula['description_formula']['credits_pct'],
    )

    # ---- TOP VS BOTTOM COMPARISON ----
    comp = formula['top_vs_bottom_comparison']
    sop += """
---

## 9. TOP vs BOTTOM PERFORMERS (30% each)

### Views
- Top 30% avg: {top_views:,.0f}
- Bottom 30% avg: {bot_views:,.0f}
- **Performance ratio**: {ratio:.1f}x
""".format(
        top_views=comp['views']['top_avg'],
        bot_views=comp['views']['bottom_avg'],
        ratio=comp['views']['ratio'],
    )

    if 'duration' in comp:
        sop += """
### Duration
- Top 30% avg: {top:.1f} min
- Bottom 30% avg: {bot:.1f} min
- Difference: {diff:+.1f} min
""".format(
            top=comp['duration']['top_avg_min'],
            bot=comp['duration']['bottom_avg_min'],
            diff=comp['duration']['difference_min'],
        )

    if 'pacing' in comp:
        sop += """
### Pacing
- Top 30% avg WPM: {top:.0f}
- Bottom 30% avg WPM: {bot:.0f}
""".format(top=comp['pacing']['top_avg_wpm'], bot=comp['pacing']['bottom_avg_wpm'])

    if 'reengagement' in comp:
        sop += """
### Re-engagement
- Top 30% hooks/min: {top:.2f}
- Bottom 30% hooks/min: {bot:.2f}
""".format(top=comp['reengagement']['top_hooks_per_min'], bot=comp['reengagement']['bottom_hooks_per_min'])

    if 'emotional_density' in comp:
        sop += """
### Emotional Language
- Top 30% emotional density: {top:.2f}%
- Bottom 30% emotional density: {bot:.2f}%
""".format(top=comp['emotional_density']['top_avg'], bot=comp['emotional_density']['bottom_avg'])

    if 'curiosity_gaps' in comp:
        sop += """
### Curiosity Gaps
- Top 30% gaps/min: {top:.2f}
- Bottom 30% gaps/min: {bot:.2f}
""".format(top=comp['curiosity_gaps']['top_gaps_per_min'], bot=comp['curiosity_gaps']['bottom_gaps_per_min'])

    if 'title_length' in comp:
        sop += """
### Title Length
- Top 30% avg words: {top:.1f}
- Bottom 30% avg words: {bot:.1f}
""".format(top=comp['title_length']['top_avg_words'], bot=comp['title_length']['bottom_avg_words'])

    # ---- TAG PATTERNS ----
    sop += """
---

## 10. TAG PATTERNS

**Most common tags:**
"""
    for tag, count in formula['tag_patterns'][:15]:
        sop += f"- \"{tag}\": {count} videos\n"

    # ---- ACTIONABLE CHECKLIST ----
    sop += """
---

## PRODUCTION CHECKLIST

### Pre-Production
- [ ] Choose topic with mystery/danger/power angle
- [ ] Research deeply - find unique angle not covered elsewhere
- [ ] Write title using proven patterns (superlative + person/place + mystery/danger word)
- [ ] Target {dur:.0f}-minute video length

### Script Writing
- [ ] Open with immersive hook (first 30 seconds are critical)
- [ ] Maintain {wpm:.0f} WPM pacing
- [ ] Insert re-engagement hooks every {hook_sec:.0f} seconds
- [ ] Use curiosity gaps throughout ({gpm:.1f} per minute)
- [ ] Include emotional language ({density:.1f}% density target)
- [ ] Use second-person address ("you/your") at {you:.1f}% density
- [ ] Pose {q:.0f} questions per 1,000 words
- [ ] Build to emotional peaks, especially around {peak}% mark

### Post-Production
- [ ] Match visuals to script tension
- [ ] Add music swells at curiosity gap resolutions
- [ ] Ensure strong intro to maintain {m2i:.0f}% mid-video retention
- [ ] Check end engagement target: {e2i:.0f}% of intro

### Publishing
- [ ] Upload on {day}
- [ ] Include sponsor/ad in description ({sponsor:.0f}% standard)
- [ ] Add credits and sources
- [ ] Upload every {freq} days
""".format(
        dur=formula['duration_formula']['sweet_spot_min'],
        wpm=sf['pacing']['avg_wpm'],
        hook_sec=60 / sf['reengagement']['avg_hooks_per_min'] if sf['reengagement']['avg_hooks_per_min'] > 0 else 60,
        gpm=cg.get('avg_gaps_per_minute', 0),
        density=el.get('avg_emotional_density', 0),
        you=sf['word_patterns']['avg_you_density'],
        q=sf['word_patterns']['avg_questions_per_1000'],
        peak=hp.get('peak_engagement_pct', 50),
        m2i=hp.get('intro_to_mid_retention', 0) * 100,
        e2i=hp.get('intro_to_end_retention', 0) * 100,
        day=ut.get('most_common_day', 'weekday'),
        sponsor=formula['description_formula']['sponsor_pct'],
        freq=ut.get('median_days_between_uploads', 7),
    )

    sop += """
---

*Generated by Fern Analysis Pipeline | {date}*
""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return sop


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    run_complete_analysis()
