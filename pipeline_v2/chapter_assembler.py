#!/usr/bin/env python3
"""
Chapter-by-Chapter Assembly for DaVinci Resolve

Builds each chapter as a separate DaVinci timeline using:
  - Python API for V1 clips, A1 narration, A2 music (sequential append)
  - Silent WAV gap-fill for A3/A4 SFX positioning
  - AppleScript UI automation for V2 overlay precise placement

NO FCPXML. NO FFmpeg. Everything directly in DaVinci.

Usage:
  # Build a single chapter:
  python -m pipeline_v2.chapter_assembler --chapter 1

  # Build all chapters:
  python -m pipeline_v2.chapter_assembler --all

  # Just print the chapter plan (dry run):
  python -m pipeline_v2.chapter_assembler --plan
"""

import argparse
import json
import os
import re
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path

# DaVinci Resolve scripting modules
RESOLVE_MODULES = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
if RESOLVE_MODULES not in sys.path:
    sys.path.append(RESOLVE_MODULES)

PROJECT_ROOT = Path(__file__).parent.parent

# ─── Project paths ──────────────────────────────────────────────────────────

DIRECTOR_PATH = PROJECT_ROOT / "storyboards" / "breaking_law_directed_v4.json"
ALIGNMENT_PATH = PROJECT_ROOT / "audio" / "breaking_law" / "narration_alignment.json"
NARRATION_PATH = PROJECT_ROOT / "audio" / "breaking_law" / "narration.wav"
SFX_DIR = PROJECT_ROOT / "assets" / "sfx"
OVERLAY_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "overlays"
CHAPTER_CARD_DIR = PROJECT_ROOT / "assets" / "breaking_law" / "chapters"
MUSIC_DIR = PROJECT_ROOT / "audio" / "breaking_law" / "music_tracks"
FOOTAGE_DIRS = [
    PROJECT_ROOT / "footage" / "breaking_law" / "clips",
    PROJECT_ROOT / "footage" / "breaking_law" / "images",
    PROJECT_ROOT / "footage" / "breaking_law" / "gap_fills" / "images",
]

# Silent WAV for gap-filling SFX tracks
SILENT_WAV_PATH = PROJECT_ROOT / "assets" / "silent_10min.wav"

# ─── Chapter definitions ────────────────────────────────────────────────────

CHAPTERS = [
    {
        "number": 0,
        "name": "COLD OPEN",
        "timeline_name": "Ch0 - COLD OPEN",
        "music": "track_01_tense_ducked.wav",
        "chapter_card": None,  # no card for cold open
    },
    {
        "number": 1,
        "name": "THE FORMULA",
        "timeline_name": "Ch1 - THE FORMULA",
        "music": "track_01_tense_ducked.wav",
        "chapter_card": "chapter_the_formula.mov",
    },
    {
        "number": 2,
        "name": "THE DATA",
        "timeline_name": "Ch2 - THE DATA",
        "music": "track_02_investigative_ducked.wav",
        "chapter_card": "chapter_the_data.mov",
    },
    {
        "number": 3,
        "name": "THE MACHINES",
        "timeline_name": "Ch3 - THE MACHINES",
        "music": "track_04_dark_ducked.wav",
        "chapter_card": None,  # no card file for machines
    },
    {
        "number": 4,
        "name": "THE RENT",
        "timeline_name": "Ch4 - THE RENT",
        "music": "track_03_emotional_ducked.wav",
        "chapter_card": "chapter_the_rent.mov",
    },
    {
        "number": 5,
        "name": "THE RECKONING",
        "timeline_name": "Ch5 - THE RECKONING",
        "music": "track_01_tense_ducked.wav",
        "chapter_card": "chapter_the_reckoning.mov",
    },
]

MAX_SFX_PER_CHAPTER = 2
MAX_VIDEO_CLIP_SEC = 7.0   # fair use for video clips
MAX_IMAGE_HOLD_SEC = 15.0  # images can hold longer (no fair use concern)


# ─── Text normalization for matching ────────────────────────────────────────

def normalize_text(text):
    """Normalize text for fuzzy matching between director and narration.

    Handles the core matching problem: director uses spelled-out numbers
    ("thirteen-year-old") while Whisper transcribes digits ("13 year old").
    """
    t = text.lower()
    # Remove punctuation and hyphens
    t = t.replace('-', ' ').replace('—', ' ').replace("'", "").replace("'", "")
    t = re.sub(r'[^\w\s]', '', t)
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', t).strip()

    # Number word → digit (comprehensive)
    number_words = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
        'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
        'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
        'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
        'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '000',
    }
    words = t.split()
    normalized_words = []
    for w in words:
        if w in number_words:
            normalized_words.append(number_words[w])
        else:
            normalized_words.append(w)
    t = ' '.join(normalized_words)

    # Compound number phrases
    t = t.replace('20 4', '24')
    t = t.replace('13 year old', '13 year old')  # already fine
    t = t.replace('point 5', '.5').replace('point 1', '.1')
    t = t.replace('point 4', '.4').replace('point 7', '.7')

    return t


def text_similarity(a, b):
    """Compute word-overlap similarity between two normalized strings."""
    words_a = set(normalize_text(a).split())
    words_b = set(normalize_text(b).split())
    if not words_a or not words_b:
        return 0.0
    overlap = words_a & words_b
    # Jaccard-like but weighted toward the shorter text
    return len(overlap) / min(len(words_a), len(words_b))


def first_n_words(text, n=6):
    """Extract first N words of text, normalized."""
    words = normalize_text(text).split()
    return ' '.join(words[:n])


# ─── Data loading ───────────────────────────────────────────────────────────

def load_director():
    """Load director v4 JSON, flatten segments."""
    with open(DIRECTOR_PATH) as f:
        data = json.load(f)
    segments = []
    for scene in data.get("scenes", []):
        segments.extend(scene.get("segments", []))
    return data, segments


def load_alignment():
    """Load Whisper narration alignment."""
    with open(ALIGNMENT_PATH) as f:
        return json.load(f)


def match_segments_to_narration(segments, alignment):
    """Match director segments to narration timing using text similarity + word count.

    Strategy: for each director segment, find the narration sentence that best
    matches its opening words (text similarity). If no good match, fall back to
    word-count consumption. Never go backwards in the sentence list.

    This handles the core problem: director uses "thirteen-year-old" while
    Whisper transcribes "13 year old".

    Returns segments with added `_narr_start` and `_narr_end` fields.
    """
    sentences = alignment["sentences"]
    sent_idx = 0
    matched = []

    for seg in segments:
        seg_text = seg.get("text", "")

        # Skip stage directions
        if not seg_text.strip() or seg_text.strip().startswith("["):
            if matched:
                seg["_narr_start"] = matched[-1]["_narr_end"]
                seg["_narr_end"] = matched[-1]["_narr_end"]
            else:
                seg["_narr_start"] = 0.0
                seg["_narr_end"] = 0.0
            matched.append(seg)
            continue

        seg_word_count = len(seg_text.split())
        seg_norm = normalize_text(seg_text)
        seg_first = ' '.join(seg_norm.split()[:4])

        # ── Step 1: Try text-similarity match ──
        # Search forward from sent_idx for a sentence whose first words match
        best_match = None
        best_score = 0
        search_window = min(20, len(sentences) - sent_idx)

        for j in range(sent_idx, sent_idx + search_window):
            if j >= len(sentences):
                break
            sent_norm = normalize_text(sentences[j]["text"])
            sent_first = ' '.join(sent_norm.split()[:4])

            # Check first-words overlap
            if seg_first and sent_first:
                # Compare first 15 chars of normalized text
                if (seg_first[:12] in sent_first or sent_first[:12] in seg_first):
                    best_match = j
                    best_score = 1.0
                    break
                # Word overlap score
                score = text_similarity(seg_text[:50], sentences[j]["text"][:50])
                if score > best_score and score >= 0.4:
                    best_match = j
                    best_score = score

        if best_match is not None:
            # Found a text match — record start time
            seg["_narr_start"] = sentences[best_match]["start"]
            sent_idx = best_match

            # Consume sentences to cover this segment's word count
            consumed = 0
            end_idx = best_match
            target = max(seg_word_count * 0.8, 3)
            while end_idx < len(sentences) and consumed < target:
                consumed += len(sentences[end_idx]["text"].split())
                end_idx += 1

            seg["_narr_end"] = sentences[end_idx - 1]["end"]
            sent_idx = end_idx
        else:
            # ── Step 2: Fallback — consume by word count ──
            if sent_idx < len(sentences):
                seg["_narr_start"] = sentences[sent_idx]["start"]
            elif matched:
                seg["_narr_start"] = matched[-1]["_narr_end"]
            else:
                seg["_narr_start"] = 0.0

            consumed = 0
            end_idx = sent_idx
            target = max(seg_word_count * 0.8, 3)
            while end_idx < len(sentences) and consumed < target:
                consumed += len(sentences[end_idx]["text"].split())
                end_idx += 1

            if end_idx > sent_idx:
                seg["_narr_end"] = sentences[end_idx - 1]["end"]
            else:
                seg["_narr_end"] = seg["_narr_start"] + (seg_word_count / 3.0)

            sent_idx = end_idx

        matched.append(seg)

    # Sanity: monotonically increasing
    for i in range(1, len(matched)):
        if matched[i]["_narr_start"] < matched[i - 1]["_narr_start"]:
            matched[i]["_narr_start"] = matched[i - 1]["_narr_end"]
        if matched[i]["_narr_end"] < matched[i]["_narr_start"]:
            matched[i]["_narr_end"] = matched[i]["_narr_start"] + 1.0

    return matched


# ─── Chapter splitting ──────────────────────────────────────────────────────

def split_into_chapters(segments):
    """Split segments into chapters based on chapter_card markers.

    Returns dict: {chapter_number: [segments]}
    """
    chapters = {}
    current_chapter = 0  # Cold open

    for seg in segments:
        card = seg.get("chapter_card")
        if card:
            # Map chapter card text to chapter number
            card_upper = card.upper()
            if "FORMULA" in card_upper:
                current_chapter = 1
            elif "DATA" in card_upper:
                current_chapter = 2
            elif "MACHINE" in card_upper:
                current_chapter = 3
            elif "RENT" in card_upper:
                current_chapter = 4
            elif "RECKONING" in card_upper:
                current_chapter = 5

        if current_chapter not in chapters:
            chapters[current_chapter] = []
        chapters[current_chapter].append(seg)

    return chapters


# ─── Media file resolution ──────────────────────────────────────────────────

def find_media_file(filename):
    """Search for a media file across all footage directories.

    Handles truncated filenames from director JSON by prefix matching.
    """
    if not filename:
        return None
    # Check absolute path first
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename

    # Strip extension for prefix matching
    name_stem = os.path.splitext(filename)[0]

    for search_dir in FOOTAGE_DIRS:
        # Direct match
        direct = search_dir / filename
        if direct.exists():
            return str(direct)
        # Walk subdirectories — exact then prefix match
        for dirpath, _, filenames in os.walk(search_dir):
            # Exact match
            if filename in filenames:
                return os.path.join(dirpath, filename)
            # Prefix match (handles truncated names from director)
            for f in filenames:
                f_stem = os.path.splitext(f)[0]
                if f_stem.startswith(name_stem) or name_stem.startswith(f_stem):
                    return os.path.join(dirpath, f)
    return None


def _build_overlay_lookup():
    """Build lookup table from overlay directory.

    Returns dict mapping slugified text → filepath for all tw_NNN_*.mov files.
    Also returns indexed lookup: {index: filepath}.
    """
    overlay_dir = OVERLAY_DIR
    if not overlay_dir.exists():
        return {}, {}

    by_slug = {}  # slug → path
    by_index = {}  # int index → path

    for f in sorted(overlay_dir.iterdir()):
        if f.suffix != '.mov':
            continue
        m = re.match(r'tw_(\d+)_(.+)\.mov', f.name)
        if m:
            idx = int(m.group(1))
            slug = m.group(2)
            by_index[idx] = str(f)
            by_slug[slug] = str(f)
            # Also store with underscores removed for fuzzy matching
            by_slug[slug.replace('_', '')] = str(f)

    return by_slug, by_index

# Pre-build overlay lookup
_OVERLAY_BY_SLUG, _OVERLAY_BY_INDEX = _build_overlay_lookup()

# Manual mapping for common overlays that don't fuzzy-match well
_OVERLAY_MANUAL = {
    "HOW?": "tw_001_how_is_that_possible.mov",
    "1977": "tw_002_1977.mov",
    "CRASH TEST DATA, 1977": "tw_003_ford_motor_company___1977.mov",
    "FINE: $3,500,000": "tw_005_3_5_million.mov",
    "TERMINATED": "tw_007_terminated.mov",
    "$10,700,000,000": "tw_009_10_7_billion___withdrawn_befo.mov",
    "PROFIT > FINE": "tw_010_the_fine_is_cheaper_than_the_p.mov",
    "$1,000,000,000,000": "tw_012_1_trillion_in_fines___since_2.mov",
    "FACEBOOK": "tw_015_cambridge_analytica.mov",
    "270,000 → 87,000,000": "tw_016_87_million_people.mov",
    "FEATURE.": "tw_019_the_formula_protects_itself.mov",
    "VOTER PROFILES": "tw_015_cambridge_analytica.mov",
    '"Senator, we run ads."': "tw_018_senator__we_run_ads.mov",
    "$5B = 7% OF ANNUAL REVENUE": "tw_038_4__of_global_revenue.mov",
    "FTC VOTE: 3–2": "tw_038_4__of_global_revenue.mov",
    "STOCK ROSE 1%": "tw_035_the_math_works.mov",
    "BUT SOMETHING HAPPENED IN 2023": "tw_038_4__of_global_revenue.mov",
    "FACEBOOK PANICKED.": "tw_019_the_formula_protects_itself.mov",
    "SAME COMPANY. SAME DATA. DIFFERENT MATH.": "tw_035_the_math_works.mov",
    "ELLIANA ESQUIVEL": "tw_021_elliana_esquivel.mov",
    "Charlotte, North Carolina": "tw_022_charlotte__nc.mov",
    "Have I Been Trained": "tw_023_have_i_been_trained.mov",
    "Almost all of it.": "tw_024_almost_all_of_it.mov",
    '"It\'ll just get put back up."': "tw_025_it_ll_just_get_replaced.mov",
    "70+ active lawsuits": "tw_026_70__lawsuits.mov",
    "$3,000": "tw_027_3_000.mov",
    "IRREVERSIBLE.": "tw_028_irreversible.mov",
    "CHRIS VIALPONDO — Seattle": "tw_045_chris_vialpondo___seattle.mov",
    "REALPAGE": "tw_031_realpage.mov",
    '"The most painful and revolting"': "tw_032_the_most_painful_and_revoltin.mov",
    "DOJ Settlement — November 2025": "tw_033_doj_v__realpage___nov__2025.mov",
    "$0": "tw_034_essentially_nothing.mov",
    "4% OF GLOBAL REVENUE": "tw_038_4__of_global_revenue.mov",
    "RICHARD GRIMSHAW": "tw_036_richard_grimshaw.mov",
    "YESENIA GUITRON": "tw_040_fired_for_calling_the_ethics_h.mov",
    "THE SACKLER NAME": "tw_041_the_sackler_name_is_still_on_t.mov",
    "THE FORMULA": "tw_042_that_s_the_formula.mov",
    "74% STILL DON'T KNOW": "tw_044_74__of_facebook_users_don_t_kn.mov",
    "CHRIS VIALPONDO": "tw_030_chris_vialpondo.mov",
    "$200,000 → $9,000 → $57 →": "tw_046_200_000.mov",
    "$5,000,000,000": "tw_000_5_billion.mov",
    "$3.5M → $3B → $7.4B → $5B": "tw_035_the_math_works.mov",
    "SOURCES": "tw_049_sources.mov",
    "WHAT ARE YOU WORTH?": "tw_048_the_question_is_what_you_re_wo.mov",
    "This is about you.": "tw_048_the_question_is_what_you_re_wo.mov",
    "Sugar dissolved in water.": "tw_028_irreversible.mov",
    "No off switch.": "tw_028_irreversible.mov",
    "I WISH THAT WERE THE END OF IT.": "tw_028_irreversible.mov",
    "YOU'D TAKE EVERYTHING.": "tw_024_almost_all_of_it.mov",
    "THAT'S THE AI INDUSTRY'S ANSWER": "tw_025_it_ll_just_get_replaced.mov",
    "WORD FOR WORD.": "tw_024_almost_all_of_it.mov",
    "THE TRAP WORKED.": "tw_035_the_math_works.mov",
    "AND HERE IS WHAT HAPPENED": "tw_035_the_math_works.mov",
    "40X INCREASE": "tw_035_the_math_works.mov",
    "THE DATA WAS WORTH MORE THAN": "tw_035_the_math_works.mov",
    "THERE IS NO GETTING IT OUT.": "tw_028_irreversible.mov",
    "RealPage sues New York.": "tw_031_realpage.mov",
    "The formula. Fully internal": "tw_042_that_s_the_formula.mov",
    "MARCH 2018": "tw_017_march_2018.mov",
}


def find_overlay_file(overlay_text, seg_index=None):
    """Find the overlay MOV file matching the given text."""
    if not overlay_text:
        return None

    overlay_dir = OVERLAY_DIR
    if not overlay_dir.exists():
        return None

    # Strategy 1: manual mapping (most reliable)
    # Check exact match first, then prefix match
    for key, filename in _OVERLAY_MANUAL.items():
        if overlay_text.startswith(key[:20]) or key.startswith(overlay_text[:20]):
            path = overlay_dir / filename
            if path.exists():
                return str(path)

    # Strategy 2: match by index
    if seg_index is not None and seg_index in _OVERLAY_BY_INDEX:
        return _OVERLAY_BY_INDEX[seg_index]

    # Strategy 3: slugify overlay text and match
    slug = re.sub(r'[^\w]', '_', overlay_text.lower()).strip('_')
    slug = re.sub(r'_+', '_', slug)[:30]

    # Try exact slug match
    if slug in _OVERLAY_BY_SLUG:
        return _OVERLAY_BY_SLUG[slug]

    # Try partial slug match (first 10 chars)
    slug_prefix = slug[:10]
    for key, path in _OVERLAY_BY_SLUG.items():
        if key.startswith(slug_prefix):
            return path

    # Strategy 4: keyword match
    text_words = set(re.findall(r'[a-z]+', overlay_text.lower()))
    text_words -= {'the', 'a', 'an', 'of', 'in', 'is', 'and', 'for', 'to', 'not'}
    if text_words:
        best_match = None
        best_score = 0
        for slug_key, path in _OVERLAY_BY_SLUG.items():
            slug_words = set(slug_key.split('_'))
            score = len(text_words & slug_words)
            if score > best_score:
                best_score = score
                best_match = path
        if best_score >= 1:
            return best_match

    return None


# ─── Silent WAV generator ──────────────────────────────────────────────────

def ensure_silent_wav():
    """Create a 10-minute silent 48kHz mono 16-bit WAV using pure Python."""
    if SILENT_WAV_PATH.exists():
        return str(SILENT_WAV_PATH)

    print("  Creating 10-minute silent WAV for gap-filling...")
    sample_rate = 48000
    duration_sec = 600  # 10 minutes
    num_samples = sample_rate * duration_sec

    with wave.open(str(SILENT_WAV_PATH), 'w') as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        # Write silence in chunks (64KB at a time to avoid memory issues)
        chunk_size = 32000  # samples per chunk
        silence_chunk = b'\x00\x00' * chunk_size
        full_chunks = num_samples // chunk_size
        remainder = num_samples % chunk_size
        for _ in range(full_chunks):
            wf.writeframes(silence_chunk)
        if remainder:
            wf.writeframes(b'\x00\x00' * remainder)

    print(f"  Created: {SILENT_WAV_PATH} ({os.path.getsize(SILENT_WAV_PATH) / 1e6:.1f} MB)")
    return str(SILENT_WAV_PATH)


# ─── SFX selection ──────────────────────────────────────────────────────────

def pick_chapter_sfx(segments, max_sfx=MAX_SFX_PER_CHAPTER):
    """Pick the best 1-2 SFX for a chapter based on tension_level.

    Returns list of (narr_time_sec, sfx_filename) tuples.
    """
    candidates = []
    for seg in segments:
        sfx = seg.get("sfx")
        if sfx and sfx.get("file"):
            sfx_file = sfx["file"]
            # Verify file exists
            if (SFX_DIR / sfx_file).exists():
                candidates.append({
                    "time": seg["_narr_start"],
                    "file": sfx_file,
                    "tension": seg.get("tension_level", 0.5),
                    "motivation": sfx.get("motivation", ""),
                })

    if not candidates:
        return []

    # Sort by tension level (highest first) and pick top N
    candidates.sort(key=lambda x: x["tension"], reverse=True)

    # Deduplicate SFX types (don't use same sound twice)
    seen_files = set()
    picked = []
    for c in candidates:
        if c["file"] not in seen_files and len(picked) < max_sfx:
            picked.append((c["time"], c["file"]))
            seen_files.add(c["file"])

    # Sort by time for chronological placement
    picked.sort(key=lambda x: x[0])
    return picked


# ─── Visual deduplication ───────────────────────────────────────────────────

def deduplicate_visuals(segments):
    """Ensure no visual file is used more than twice per chapter.

    If a visual repeats more than twice, replace with an alternate from
    the gap_fills directory.
    """
    usage_count = {}
    gap_images = []

    # Collect available gap fill images
    gap_dir = PROJECT_ROOT / "footage" / "breaking_law" / "gap_fills" / "images"
    if gap_dir.exists():
        gap_images = [str(f) for f in gap_dir.iterdir()
                      if f.suffix.lower() in ('.jpg', '.jpeg', '.png')]

    gap_idx = 0

    for seg in segments:
        vf = seg.get("visual_file", "")
        if not vf:
            continue

        usage_count[vf] = usage_count.get(vf, 0) + 1
        if usage_count[vf] > 2 and gap_images:
            # Replace with a gap fill image
            seg["visual_file"] = os.path.basename(gap_images[gap_idx % len(gap_images)])
            seg["visual_type"] = "still_image"
            gap_idx += 1

    return segments


# ─── Narration chapter splitter ─────────────────────────────────────────────

def split_narration_for_chapter(chapter_num, start_sec, end_sec):
    """Extract a chapter's narration segment to a new WAV file using pure Python.

    The narration is 24kHz 16-bit mono. We read the sample range for this
    chapter and write it to a new WAV file. No FFmpeg needed.
    """
    out_dir = PROJECT_ROOT / "audio" / "breaking_law" / "chapters"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"narration_ch{chapter_num}.wav"

    if out_path.exists():
        return str(out_path)

    with wave.open(str(NARRATION_PATH), 'r') as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()

        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        num_samples = end_sample - start_sample

        wf.setpos(start_sample)
        frames = wf.readframes(num_samples)

    with wave.open(str(out_path), 'w') as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)

    dur = num_samples / sample_rate
    print(f"  Split narration ch{chapter_num}: {start_sec:.1f}s-{end_sec:.1f}s ({dur:.1f}s) → {out_path.name}")
    return str(out_path)


# ─── DaVinci connection ─────────────────────────────────────────────────────

def connect_resolve():
    """Connect to DaVinci Resolve. Must be running."""
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("ERROR: Cannot connect to DaVinci Resolve. Is it running?")
        sys.exit(1)
    return resolve


def get_pool_lookup(mp):
    """Build filename → MediaPoolItem lookup from entire media pool."""
    root = mp.GetRootFolder()
    pool = {}
    for clip in (root.GetClipList() or []):
        pool[clip.GetName()] = clip
    return pool


# ─── DaVinci timeline building ──────────────────────────────────────────────

def import_chapter_media(mp, chapter_segments, music_file, sfx_picks, chapter_num=0):
    """Import all media needed for a chapter into the media pool."""
    root = mp.GetRootFolder()
    mp.SetCurrentFolder(root)

    files_to_import = set()

    # Visual files
    for seg in chapter_segments:
        vf = seg.get("visual_file")
        path = find_media_file(vf)
        if path:
            files_to_import.add(path)

    # Music
    music_path = MUSIC_DIR / music_file
    if music_path.exists():
        files_to_import.add(str(music_path))

    # SFX
    for _, sfx_file in sfx_picks:
        sfx_path = SFX_DIR / sfx_file
        if sfx_path.exists():
            files_to_import.add(str(sfx_path))

    # Overlays
    for i, seg in enumerate(chapter_segments):
        overlay_text = seg.get("text_overlay")
        if overlay_text:
            overlay_path = find_overlay_file(overlay_text)
            if overlay_path:
                files_to_import.add(overlay_path)

    # Chapter card
    for seg in chapter_segments:
        card = seg.get("chapter_card")
        if card:
            card_name = f"chapter_{card.lower().replace(' ', '_')}.mov"
            card_path = CHAPTER_CARD_DIR / card_name
            if card_path.exists():
                files_to_import.add(str(card_path))

    # Filter out already-imported files
    existing = set(clip.GetName() for clip in (root.GetClipList() or []))
    new_files = [f for f in files_to_import if os.path.basename(f) not in existing]

    if new_files:
        items = mp.ImportMedia(list(new_files))
        count = len(items) if items else 0
        print(f"  Imported {count} new media files")

    return get_pool_lookup(mp)


def build_chapter_timeline(resolve, project, mp, chapter_def, chapter_segments, sfx_picks,
                           no_applescript=False):
    """Build one chapter's timeline in DaVinci.

    CRITICAL: AppendToTimeline always places clips at the END of the timeline
    (not the end of the specific track). Order matters:
      1. Place A1 (chapter narration) + A2 (music) together FIRST
         - Both are full-length clips, no trim → both start at frame 0
      2. Place V1 clips sequentially (they go after audio on video tracks,
         which in DaVinci means they ALSO start at frame 0 on V1)
      3. SFX via AppleScript at exact positions
      4. Overlays via AppleScript at exact positions
    """
    chapter_num = chapter_def["number"]
    tl_name = chapter_def["timeline_name"]
    music_file = chapter_def["music"]

    pool = get_pool_lookup(mp)

    # Get narration timing for this chapter
    ch_start = chapter_segments[0]["_narr_start"]
    ch_end = chapter_segments[-1]["_narr_end"]
    ch_duration = ch_end - ch_start

    print(f"\n{'='*60}")
    print(f"  CHAPTER {chapter_num}: {chapter_def['name']}")
    print(f"  Narration: {ch_start:.1f}s - {ch_end:.1f}s ({ch_duration:.1f}s)")
    print(f"  Segments: {len(chapter_segments)}")
    print(f"  SFX: {len(sfx_picks)}")
    print(f"  Music: {music_file}")
    print(f"{'='*60}")

    fps = int(project.GetSetting("timelineFrameRate") or 24)
    print(f"  Project FPS: {fps}")

    # ── Split narration for this chapter ──
    ch_narr_path = split_narration_for_chapter(chapter_num, ch_start, ch_end)
    ch_narr_name = os.path.basename(ch_narr_path)

    # Import chapter narration if not already in pool
    if ch_narr_name not in pool:
        items = mp.ImportMedia([ch_narr_path])
        if items:
            pool[ch_narr_name] = items[0]
            print(f"  Imported chapter narration: {ch_narr_name}")

    # ── Create timeline ──
    timeline = mp.CreateEmptyTimeline(tl_name)
    if not timeline:
        timeline = mp.CreateEmptyTimeline(tl_name + " v2")
    if not timeline:
        print(f"  ERROR: Could not create timeline '{tl_name}'")
        return None

    project.SetCurrentTimeline(timeline)
    tl_start_frame = timeline.GetStartFrame()

    # Ensure tracks exist
    while timeline.GetTrackCount('video') < 3:
        timeline.AddTrack('video')
    while timeline.GetTrackCount('audio') < 4:
        timeline.AddTrack('audio')

    timeline.SetTrackName('audio', 1, 'Narration')
    timeline.SetTrackName('audio', 2, 'Music')
    timeline.SetTrackName('audio', 3, 'SFX 1')
    timeline.SetTrackName('audio', 4, 'SFX 2')

    # ── STEP 1: Place combined narration+music (stereo) on A1 ──
    # DaVinci API bug: AppendToTimeline places audio sequentially even
    # across tracks. Workaround: mix narration+music into a single
    # stereo WAV (left=narration, right=music). Both start at frame 0.
    from pipeline_v2.audio_mixer import mix_chapter_audio
    mixed_path = mix_chapter_audio(chapter_num, ch_start, ch_end, music_file)
    mixed_name = os.path.basename(mixed_path)

    if mixed_name not in pool:
        items = mp.ImportMedia([mixed_path])
        if items:
            pool[mixed_name] = items[0]

    if mixed_name in pool:
        mp.AppendToTimeline([{
            "mediaPoolItem": pool[mixed_name],
            "mediaType": 2,
            "trackIndex": 1,
        }])
        print(f"  A1: Narration+Music (stereo) placed at 0 ({ch_duration:.1f}s)")

    # ── STEP 2: V1 clips (sequential append) ──
    # For segments longer than the clip cap, place the clip at max duration
    # and the visual holds/loops to fill the segment time.
    # For images, DaVinci holds the frame automatically.
    # For video clips >7s: place full segment duration (user can trim for fair use).
    print(f"\n  V1: Placing {len(chapter_segments)} clips...")
    v1_placed = 0
    v1_total_sec = 0
    source_usage = {}

    for seg in chapter_segments:
        vf = seg.get("visual_file")
        if not vf or vf not in pool:
            path = find_media_file(vf)
            if path:
                vf = os.path.basename(path)

        if not vf or vf not in pool:
            print(f"    SKIP: {vf} not in pool")
            continue

        # Calculate clip duration from narration timing
        seg_dur = seg["_narr_end"] - seg["_narr_start"]
        seg_dur = max(seg_dur, 0.5)  # minimum half second

        # For V1: use FULL narration segment duration for each clip.
        # Images hold naturally. Video clips may extend past source duration
        # (DaVinci will hold the last frame or loop). User can trim for fair use.
        clip_dur = seg_dur

        # Source in-point (only for video clips)
        clip_start_sec = seg.get("clip_start_sec") or 0
        start_frame = int(clip_start_sec * fps)
        dur_frames = int(clip_dur * fps)
        end_frame = start_frame + dur_frames

        source_usage[vf] = source_usage.get(vf, 0) + 1

        mp.AppendToTimeline([{
            "mediaPoolItem": pool[vf],
            "mediaType": 1,
            "trackIndex": 1,
            "startFrame": start_frame,
            "endFrame": end_frame,
        }])
        v1_placed += 1
        v1_total_sec += clip_dur

    print(f"  V1: {v1_placed} clips placed ({v1_total_sec:.1f}s total)")

    # ── STEP 3: Mute V1 clip audio ──
    print(f"  Muting V1 clip audio...")
    v1_clips = timeline.GetItemListInTrack('video', 1) or []
    for i, seg in enumerate(chapter_segments):
        if i < len(v1_clips):
            clip_audio_rule = seg.get("clip_audio", "mute")
            if clip_audio_rule == "mute":
                v1_clips[i].SetProperty("Volume", 0)
            elif clip_audio_rule == "play_then_mute":
                v1_clips[i].SetProperty("Volume", 0.3)  # ducked
            # "play" = leave at full volume

    # ── STEP 4: SFX placement (API sequential on A3/A4) ──
    sfx_placement = []
    if sfx_picks:
        print(f"\n  A3/A4: Placing {len(sfx_picks)} SFX...")
        for idx, (sfx_time, sfx_file) in enumerate(sfx_picks):
            if sfx_file not in pool:
                continue
            track = 3 if idx % 2 == 0 else 4
            rel_time = sfx_time - ch_start
            tc = _sec_to_timecode(rel_time, fps, tl_start_frame)
            sfx_placement.append({
                "file": sfx_file, "track": f"A{track}",
                "timecode": tc, "rel_sec": rel_time,
            })
            mp.AppendToTimeline([{
                "mediaPoolItem": pool[sfx_file],
                "mediaType": 2,
                "trackIndex": track,
            }])
            print(f"    A{track}: {sfx_file} (target: {tc})")

    # ── STEP 5: Overlay placement (API sequential on V2) ──
    overlay_placement = []
    overlay_count = 0
    for seg in chapter_segments:
        overlay_text = seg.get("text_overlay")
        if not overlay_text:
            continue
        overlay_path = find_overlay_file(overlay_text)
        if overlay_path:
            overlay_name = os.path.basename(overlay_path)
            if overlay_name in pool:
                rel_time = max(0, seg["_narr_start"] - ch_start)
                tc = _sec_to_timecode(rel_time, fps, tl_start_frame)
                overlay_placement.append({
                    "file": overlay_name, "track": "V2",
                    "timecode": tc, "rel_sec": rel_time,
                    "text": overlay_text[:40],
                })
                mp.AppendToTimeline([{
                    "mediaPoolItem": pool[overlay_name],
                    "mediaType": 1,
                    "trackIndex": 2,
                }])
                overlay_count += 1

    if overlay_count:
        print(f"\n  V2: {overlay_count} overlays placed (sequential — see sheet for target timecodes)")

    # ── Print placement sheet for manual fine-tuning ──
    if sfx_placement or overlay_placement:
        print(f"\n  ┌─── PLACEMENT SHEET: {chapter_def['name']} ───")
        print(f"  │ NOTE: Overlays/SFX are placed sequentially via API.")
        print(f"  │ Drag each to its target timecode in DaVinci:")
        if sfx_placement:
            print(f"  │")
            print(f"  │ SFX (drag to timecodes):")
            for s in sfx_placement:
                print(f"  │   {s['track']}  →  {s['timecode']}  {s['file']}")
        if overlay_placement:
            print(f"  │")
            print(f"  │ OVERLAYS (drag to timecodes on V2):")
            for o in overlay_placement:
                print(f"  │   V2  →  {o['timecode']}  {o['file'][:35]}  \"{o['text']}\"")
        print(f"  └{'─'*50}")

    # ── Verification ──
    verify_chapter(timeline, chapter_def, chapter_segments, fps, tl_start_frame)

    # Save
    subprocess.run(['osascript', '-e',
        'tell application "System Events" to tell process "DaVinci Resolve" '
        'to keystroke "s" using command down'],
        capture_output=True, timeout=5)

    return timeline


# ─── AppleScript overlay placement ──────────────────────────────────────────

def _sec_to_timecode(seconds, fps, tl_start_frame):
    """Convert seconds to DaVinci timecode string (HH:MM:SS:FF)."""
    abs_sec = seconds + (tl_start_frame / fps)
    hours = int(abs_sec // 3600)
    minutes = int((abs_sec % 3600) // 60)
    secs = int(abs_sec % 60)
    frames = int((abs_sec % 1) * fps)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"


def _run_applescript(script, timeout=20):
    """Run an AppleScript and return (success, stderr)."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return False, result.stderr[:200]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "timeout"


def place_clip_at_timecode_applescript(timeline, pool_item, clip_name,
                                       target_sec, track_idx, track_type,
                                       fps, tl_start_frame):
    """Place a single clip at exact timecode using AppleScript.

    Uses DaVinci keyboard shortcuts:
    1. Set playhead via API
    2. AppleScript: search media pool, double-click to load in source viewer
    3. AppleScript: press overwrite key (F10) to place at playhead
    """
    tc = _sec_to_timecode(target_sec, fps, tl_start_frame)
    print(f"    Placing {clip_name} on {track_type[0].upper()}{track_idx} at {tc}")

    # All-in-one AppleScript: activate DaVinci, search media pool for clip,
    # and overwrite at current playhead position.
    # NOTE: Playhead positioning via AppleScript is unreliable.
    # The placement sheet provides exact timecodes for manual adjustment.
    applescript = f'''
        tell application "DaVinci Resolve" to activate
        delay 0.3
        tell application "System Events"
            tell process "DaVinci Resolve"
                -- Search media pool for the clip
                keystroke "f" using command down
                delay 0.4
                keystroke "a" using command down
                delay 0.1
                keystroke "{clip_name}"
                delay 0.6
                keystroke return
                delay 0.3
                key code 53
                delay 0.2
                -- F10 = Overwrite at playhead
                key code 109
                delay 0.3
            end tell
        end tell
    '''

    ok, err = _run_applescript(applescript)
    if not ok:
        print(f"      AppleScript failed: {err}")
        print(f"      → Will need manual placement at {tc}")
    time.sleep(0.3)


def place_overlays_applescript(timeline, overlays, fps, tl_start_frame):
    """Place overlays on V2 at exact timecodes using AppleScript UI automation.

    NOTE: Without SetCurrentTimecode API, playhead positioning must be done
    manually. The placement sheet provides exact timecodes for each overlay.
    The AppleScript here attempts to search and place, but position accuracy
    depends on where the playhead is when F10 is pressed.
    """
    # This function is now handled inline in build_chapter_timeline
    pass


# ─── Verification ───────────────────────────────────────────────────────────

def verify_chapter(timeline, chapter_def, segments, fps, tl_start):
    """Verify the built chapter timeline."""
    print(f"\n  VERIFICATION: {chapter_def['name']}")

    for track_type, label in [('video', 'V'), ('audio', 'A')]:
        count = timeline.GetTrackCount(track_type)
        for t in range(1, count + 1):
            clips = timeline.GetItemListInTrack(track_type, t) or []
            if clips:
                first_start = (clips[0].GetStart() - tl_start) / fps
                last_end = (clips[-1].GetEnd() - tl_start) / fps
                print(f"    {label}{t}: {len(clips)} clips, "
                      f"{first_start:.1f}s - {last_end:.1f}s "
                      f"({last_end - first_start:.1f}s)")

    # Check V1 count matches segment count
    v1_clips = timeline.GetItemListInTrack('video', 1) or []
    expected = len([s for s in segments if s.get("visual_file")])
    if len(v1_clips) != expected:
        print(f"    ⚠️  V1 count mismatch: {len(v1_clips)} placed vs {expected} expected")
    else:
        print(f"    ✅ V1 count matches ({len(v1_clips)})")


# ─── Chapter plan (dry run) ─────────────────────────────────────────────────

def print_chapter_plan(chapter_num, chapter_def, segments, sfx_picks):
    """Print what would be built for a chapter (no DaVinci required)."""
    ch_start = segments[0]["_narr_start"]
    ch_end = segments[-1]["_narr_end"]

    print(f"\n{'='*60}")
    print(f"  CHAPTER {chapter_num}: {chapter_def['name']}")
    print(f"  Duration: {ch_start:.1f}s - {ch_end:.1f}s ({ch_end - ch_start:.1f}s)")
    print(f"  Segments: {len(segments)}")
    print(f"  Music: {chapter_def['music']}")
    print(f"{'='*60}")

    # Visual files
    visuals = {}
    for seg in segments:
        vf = seg.get("visual_file", "?")
        visuals[vf] = visuals.get(vf, 0) + 1

    print(f"\n  V1 Visuals ({len(segments)} segments, {len(visuals)} unique files):")
    for vf, count in sorted(visuals.items(), key=lambda x: -x[1]):
        path = find_media_file(vf)
        status = "✅" if path else "❌ NOT FOUND"
        repeat = f" (x{count})" if count > 1 else ""
        print(f"    {status} {vf[:50]}{repeat}")

    # Overlays
    print(f"\n  V2 Overlays:")
    for seg in segments:
        ov = seg.get("text_overlay")
        if ov:
            path = find_overlay_file(ov)
            status = "✅" if path else "❌"
            print(f"    {status} {seg['_narr_start']:6.1f}s: {ov[:40]}")

    # SFX
    print(f"\n  SFX (picked {len(sfx_picks)} of {MAX_SFX_PER_CHAPTER} max):")
    for sfx_time, sfx_file in sfx_picks:
        print(f"    🔊 {sfx_time:6.1f}s: {sfx_file}")

    print()


# ─── Main entry point ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Chapter-by-chapter DaVinci assembly")
    parser.add_argument("--chapter", type=int, help="Build a specific chapter (0-5)")
    parser.add_argument("--all", action="store_true", help="Build all chapters")
    parser.add_argument("--plan", action="store_true", help="Dry run: print plan only")
    parser.add_argument("--no-applescript", action="store_true",
                        help="Skip AppleScript placement; print placement sheet instead")
    args = parser.parse_args()

    if args.chapter is None and not args.all and not args.plan:
        parser.print_help()
        return

    # Load data
    print("Loading director v4...")
    data, raw_segments = load_director()
    print(f"  {len(raw_segments)} segments")

    print("Loading narration alignment...")
    alignment = load_alignment()
    print(f"  {len(alignment['sentences'])} sentences, {alignment['duration_sec']:.1f}s")

    print("Matching segments to narration timing...")
    matched_segments = match_segments_to_narration(raw_segments, alignment)

    print("Splitting into chapters...")
    chapter_map = split_into_chapters(matched_segments)
    for ch_num, ch_segs in sorted(chapter_map.items()):
        ch_start = ch_segs[0]["_narr_start"]
        ch_end = ch_segs[-1]["_narr_end"]
        print(f"  Ch{ch_num}: {len(ch_segs)} segments, {ch_start:.1f}s - {ch_end:.1f}s")

    # Determine which chapters to build
    if args.plan:
        targets = sorted(chapter_map.keys())
    elif args.all:
        targets = sorted(chapter_map.keys())
    elif args.chapter is not None:
        targets = [args.chapter]
    else:
        targets = []

    for ch_num in targets:
        if ch_num not in chapter_map:
            print(f"  ERROR: Chapter {ch_num} not found")
            continue

        ch_def = CHAPTERS[ch_num]
        ch_segments = chapter_map[ch_num]

        # Deduplicate visuals
        ch_segments = deduplicate_visuals(ch_segments)

        # Pick SFX
        sfx_picks = pick_chapter_sfx(ch_segments)

        if args.plan:
            print_chapter_plan(ch_num, ch_def, ch_segments, sfx_picks)
            continue

        # Build in DaVinci
        print(f"\n  Connecting to DaVinci Resolve...")
        resolve = connect_resolve()
        project = resolve.GetProjectManager().GetCurrentProject()
        mp = project.GetMediaPool()

        # Import media
        print(f"  Importing chapter media...")
        pool = import_chapter_media(mp, ch_segments, ch_def["music"], sfx_picks, ch_num)

        # Build timeline
        timeline = build_chapter_timeline(
            resolve, project, mp, ch_def, ch_segments, sfx_picks,
            no_applescript=args.no_applescript
        )

        if timeline:
            print(f"\n  ✅ Chapter {ch_num} ({ch_def['name']}) built successfully!")
        else:
            print(f"\n  ❌ Chapter {ch_num} failed!")


if __name__ == "__main__":
    main()
