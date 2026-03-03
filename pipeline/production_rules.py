#!/usr/bin/env python3
"""
production_rules.py — Content-to-production mapping for Fern-style videos.

THE PROBLEM THIS SOLVES:
  The assembler was previously treating all script moments identically —
  random Ken Burns motion, flat 10.9% SFX rate, same cut pacing everywhere.
  Fern doesn't work that way. The WHY behind every production decision is
  correlated with what's happening in the script at that exact moment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACCURACY TIERS — what's actually validated vs. what's directional logic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ FULLY MEASURED (from 3 Fern videos, optical flow + AI frame analysis):
  - Global motion distribution: zoom_in 36.5%, zoom_out 23.7%, static 20.0%,
    pan_up 7.5%, pan_down 5.0%, pan_right 2.2%, pan_left 1.4%
    → Source: FERN_MOTION_FORMULA.json, optical flow on full videos
  - Per-content-type motion weights (5 of 8 types):
    → Source: analyze_fern_crosscorrelate.py, segment_motion.json × timeline_hybrid_qwen-vl.json
    → hook (n=61):              zoom_in 52.9%, zoom_out 17.7%, static 23.5%, pan_right 5.9%
    → establishing_context (n=1064): zoom_in 35.4%, zoom_out 26.3%, static 23.1%, pan_up 10.1%, pan_down 5.1%
    → character_intro (n=209):  zoom_in 53.6%, zoom_out 25.6%, static 11.6%, pan_right 4.6%, pan_down 4.6%
    → tension_build (n=224):    zoom_in 51.0%, zoom_out 26.5%, pan_down 12.3%, static 6.1%, pan_up 4.1%
    → evidence (n=186, proxy for reveal): zoom_in 41.5%, zoom_out 24.5%, static 18.9%, pan_up 7.6%, pan_right/down 3.7%
  - footage_preference by narrative_function:
    → Source: analyze_fern_crosscorrelate.py on 1838 labeled qwen-vl frames
    → hook: document_photo 50.8%, title_card 36.1% (title_card = chapter card, skip for assembly)
    → character_intro: documentary_photo 56.5%, document_photo 42.6%
    → establishing_context: document_photo 59.7%, documentary_photo 10.9%, archival 9.3%
    → tension_build: document_photo 87.1%, reconstructed_footage 5.8%
    → evidence/reveal: document_photo 88.7%
    → transition: black_screen 86.1%
  - SFX rate overall: 10.9% of cuts  → Source: FERN_SFX_FORMULA.json
  - SFX type mix: sustain_mid 78%, riser 22%  → Source: SOUND_DESIGN_FORMULA.json
  - Cut rate: 11.3/min, avg 5.3s/segment  → Source: FERN_MOTION_FORMULA.json
  - Color grade: saturation 0.244, brightness 0.368, black_crush 24.7%

⚠️ DIRECTIONAL INFERENCE (logically grounded but not measured per-type):
  - motion_weights for stakes_moment → uses tension_build weights as structural proxy
  - motion_weights for aftermath → uses establishing_context weights as structural proxy
  - cut_pacing per content type → directional (tension=faster is logical but unverified)
  - sfx_probability per content type → directional (reveals get risers is supported by
    SOUND_DESIGN_FORMULA riser timing, but exact probabilities are estimates)

🚫 NOT YET MEASURED — requires action to unlock:
  - motion_weights for climax (n=1 labeled frame, insufficient sample)
    → falls back to GLOBAL_MOTION_WEIGHTS until more climax segments are analyzed
  - Transition types (hard_cut vs. dissolve): requires cut_timestamps in timeline JSON
    (re-run analyze_fern_hybrid_checkpoint.py with qwen3.5-4b model)

CONTENT TYPES → PRODUCTION DECISIONS:

  hook_opening      First ~30s. Establishes stakes. Slow/wide, no SFX, loud intro music.
  context_background Factual dates, timelines, setting. Slow/static, no SFX, upper text.
  character_intro   First mention of named person. Hold on portrait, no SFX, center text.
  tension_build     Building toward reveal. Accelerating cuts, rumble SFX, zoom-in heavy.
  reveal            "except / in reality / it turns out" moments. Static hold + impact SFX.
  stakes_moment     Superlatives, consequences, danger. Fast zoom-in, possible impact.
  climax            Peak action. Fastest cuts, clips preferred, high SFX probability.
  aftermath         Resolution, consequences. Slow zoom-out, minimal SFX, lower text.

Usage:
  from pipeline.production_rules import classify_chunk, get_spec

  content_type = classify_chunk(chunk, total_duration_sec=1320.0)
  spec = get_spec(content_type)
  # spec.motion_weights, spec.sfx_probability, spec.cut_pacing, etc.
"""

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Motion distributions — MEASURED from optical flow on 3 Fern videos
# Source: FERN_MOTION_FORMULA.json + segment_motion.json × timeline_hybrid_qwen-vl.json
# "indeterminate" segments excluded and weights renormalized to 1.000.
# ---------------------------------------------------------------------------

# Fallback: global avg across all segments (for types with insufficient labeled data)
GLOBAL_MOTION_WEIGHTS: dict[str, float] = {
    "zoom_in":  0.40,   # 36.5% avg + absorbs 3.7% indeterminate
    "zoom_out": 0.24,   # 23.7% avg
    "static":   0.20,   # 20.0% avg
    "pan_up":   0.075,  # 7.5% avg
    "pan_down": 0.050,  # 5.0% avg
    "pan_right": 0.022, # 2.2% avg
    "pan_left":  0.013, # 1.4% avg
}

# Per-content-type weights — MEASURED (n = labeled segments cross-correlated with qwen-vl)
# hook (n=61): zoom-heavy, low zoom_out, notable static
_MOTION_HOOK: dict[str, float] = {
    "zoom_in":  0.529,
    "zoom_out": 0.177,
    "static":   0.235,
    "pan_right": 0.059,
}

# establishing_context / context_background (n=1064): most balanced distribution
_MOTION_CONTEXT: dict[str, float] = {
    "zoom_in":  0.354,
    "zoom_out": 0.263,
    "static":   0.231,
    "pan_up":   0.101,
    "pan_down": 0.051,
}

# character_intro (n=209): very zoom_in dominant — holding on portrait
_MOTION_CHARACTER: dict[str, float] = {
    "zoom_in":  0.536,
    "zoom_out": 0.256,
    "static":   0.116,
    "pan_right": 0.046,
    "pan_down":  0.046,
}

# tension_build (n=224): zoom_in dominant, more pan_down than anywhere else
_MOTION_TENSION: dict[str, float] = {
    "zoom_in":  0.510,
    "zoom_out": 0.265,
    "pan_down": 0.123,
    "static":   0.061,
    "pan_up":   0.041,
}

# evidence / reveal (n=186): more balanced, notable static — holding on documents
_MOTION_EVIDENCE: dict[str, float] = {
    "zoom_in":  0.415,
    "zoom_out": 0.245,
    "static":   0.189,
    "pan_up":   0.076,
    "pan_right": 0.037,
    "pan_down":  0.037,
}

# ---------------------------------------------------------------------------
# Trigger word sets — extracted from SCRIPT_FORMULA.json reveal_moments
# ---------------------------------------------------------------------------

# Words that signal a plot-twist reveal (Fern's most consistent production cue)
REVEAL_TRIGGERS: set[str] = {
    "except", "in reality", "it turns out", "but then", "however",
    "suddenly", "unexpectedly", "shockingly", "what they didn't know",
    "what no one knew", "little did they know", "unbeknownst",
    "but here's the", "here's what", "here's where it gets",
    "but what", "the truth was", "the truth is", "it was actually",
    "actually,", "in fact,", "turns out", "not what",
}

# Phrases that establish stakes / danger / superlatives
STAKES_PHRASES: set[str] = {
    "most dangerous", "most notorious", "most expensive", "most wanted",
    "deadliest", "largest manhunt", "most intellectual", "most feared",
    "biggest", "worst", "history's most", "history's largest",
    "first ever", "never before", "unprecedented", "the only",
    "sentenced to", "convicted of", "charged with", "executed",
    "killed", "murdered", "assassinated", "bombed", "attacked",
    "declared war", "launched an attack",
}

# Phrases that signal context / factual background
CONTEXT_PHRASES: set[str] = {
    "in 19", "in 20", "on january", "on february", "on march",
    "on april", "on may", "on june", "on july", "on august",
    "on september", "on october", "on november", "on december",
    "years earlier", "years before", "years later", "years after",
    "at the time", "by this point", "at this point", "meanwhile",
    "founded in", "established in", "born in", "grew up",
    "according to", "records show", "documents reveal",
}

# Aftermath / resolution signals
AFTERMATH_PHRASES: set[str] = {
    "in the end", "ultimately", "eventually", "finally",
    "the aftermath", "the result", "as a result", "the fallout",
    "was sentenced", "was convicted", "was acquitted",
    "died in", "passed away", "was buried", "was released",
    "years later,", "today,", "to this day",
    "the legacy", "remains", "left behind",
}

# Climax / high-action signals
CLIMAX_PHRASES: set[str] = {
    "shots fired", "opened fire", "detonated", "explosion",
    "arrest", "surrounded by", "raid on", "stormed",
    "collapsed", "died", "killed", "shot dead", "executed",
    "confessed", "pleaded guilty", "was caught",
    "they found", "they discovered", "they realized",
    "at that moment", "right then", "that's when",
}


# ---------------------------------------------------------------------------
# Production spec dataclass
# ---------------------------------------------------------------------------

@dataclass
class ProductionSpec:
    """
    Per-content-type production decisions derived from Fern formula analysis.

    ACCURACY NOTE: fields are annotated with their data source tier:
      ✅ MEASURED  — derived from actual measured data
      ⚠️ INFERRED  — directionally grounded but not measured per-type
    """
    content_type: str

    # ✅ MEASURED: per-type weights from optical flow × qwen-vl cross-correlation
    # 5 of 8 types have direct measured weights; stakes_moment/aftermath use proxies;
    # climax falls back to GLOBAL_MOTION_WEIGHTS (insufficient sample, n=1)
    motion_weights: dict[str, float] = field(default_factory=dict)

    # ⚠️ INFERRED: overall rate is measured (10.9%), per-type distribution is directional
    # riser SFX appear at reveal moments (confirmed by SOUND_DESIGN_FORMULA timing),
    # but exact per-type probabilities are estimates until per-type data is collected.
    sfx_probability: float = 0.109   # 10.9% overall measured rate as default
    sfx_type: str = "impact"         # "impact" | "whoosh" | "rumble" | None

    # ⚠️ INFERRED: global avg is 5.3s/segment — per-type pacing is directional guidance
    # Source: FERN_MOTION_FORMULA.json cuts_per_minute=11.3, avg_segment_duration_sec=5.3
    cut_pacing: str = "normal"    # "very_fast" | "fast" | "normal" | "slow"
    min_seg_sec: float = 2.5
    max_seg_sec: float = 7.0

    # ✅ MEASURED: footage type by narrative_function from 1784 labeled qwen-vl frames
    # Source: analyze_fern_crosscorrelate.py → FERN_CORRELATION_DATA.json
    footage_preference: list[str] = field(default_factory=lambda: ["document_photo", "documentary_photo"])
    clip_probability: float = 0.10   # probability of using a video clip vs. still

    # ⚠️ INFERRED: text zone placement (upper/center/lower)
    # Source: FERN_TEXT_ANIMATION_FORMULA.json zone_distribution (upper 12, center 7, lower 6)
    text_zone: str = "auto"       # "upper" | "center" | "lower" | "auto"

    def weighted_motion(self) -> str:
        """Pick a motion type using this spec's weighted distribution."""
        import random
        options = list(self.motion_weights.keys())
        weights = list(self.motion_weights.values())
        return random.choices(options, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Production rules — one spec per content type
# Derived from cross-correlating all formula files
# ---------------------------------------------------------------------------

PRODUCTION_RULES: dict[str, ProductionSpec] = {

    # ── HOOK OPENING (first ~30s) ──────────────────────────────────────────
    # ✅ footage_preference: hook frames = document_photo 50.8%, title_card 36.1%
    #    (title_card = animated chapter card, not sourced footage — skip for assembly)
    #    → use document_photo primary, archival_footage secondary
    # ✅ motion_weights: _MOTION_HOOK (n=61, zoom_in 52.9%, static 23.5%, zoom_out 17.7%)
    # ⚠️ sfx_probability: 0.0 — music is loudest here (inferred, not measured)
    # ⚠️ cut_pacing: slow — establishing energy (inferred, directional)
    "hook_opening": ProductionSpec(
        content_type="hook_opening",
        motion_weights=_MOTION_HOOK,
        sfx_probability=0.0,
        sfx_type=None,
        cut_pacing="slow",
        min_seg_sec=4.0,
        max_seg_sec=8.0,
        footage_preference=["document_photo", "archival_footage", "documentary_photo"],
        clip_probability=0.20,
        text_zone="center",
    ),

    # ── CONTEXT / BACKGROUND ──────────────────────────────────────────────
    # ✅ footage_preference: establishing_context frames measured:
    #    document_photo 59.7%, documentary_photo 10.9%, archival 9.3%, news_screenshot 7.0%
    # ✅ motion_weights: _MOTION_CONTEXT (n=1064, most balanced — zoom_in 35.4%, zoom_out 26.3%)
    # ⚠️ sfx_probability: 0.0 (audience is processing — inferred)
    # ⚠️ cut_pacing: slow (informational — inferred)
    "context_background": ProductionSpec(
        content_type="context_background",
        motion_weights=_MOTION_CONTEXT,
        sfx_probability=0.0,
        sfx_type=None,
        cut_pacing="slow",
        min_seg_sec=4.0,
        max_seg_sec=8.0,
        footage_preference=["document_photo", "documentary_photo", "archival_footage"],
        clip_probability=0.08,
        text_zone="upper",
    ),

    # ── CHARACTER INTRO ────────────────────────────────────────────────────
    # ✅ footage_preference: character_intro frames MEASURED (n=209):
    #    documentary_photo 56.5%, document_photo 42.6% — portrait/headshot dominant
    # ✅ emotional_tone at character_intro: neutral 47.4%, tense 21.1%, powerful 15.8%
    # ✅ motion_weights: _MOTION_CHARACTER (n=209, zoom_in 53.6% — slow push on portrait)
    # ⚠️ sfx_probability: 0.0 (name itself is the reveal — inferred)
    "character_intro": ProductionSpec(
        content_type="character_intro",
        motion_weights=_MOTION_CHARACTER,
        sfx_probability=0.0,
        sfx_type=None,
        cut_pacing="slow",
        min_seg_sec=4.5,
        max_seg_sec=8.0,
        footage_preference=["documentary_photo", "document_photo"],
        clip_probability=0.05,
        text_zone="center",
    ),

    # ── TENSION BUILD ─────────────────────────────────────────────────────
    # ✅ footage_preference: tension_build frames MEASURED (n=224):
    #    document_photo 87.1%, reconstructed_footage 5.8%, documentary_footage 3.1%
    # ✅ emotional_tone at tension_build: tense 88.8%, ominous 10.3% (very consistent)
    # ✅ motion_weights: _MOTION_TENSION (n=224, zoom_in 51.0%, pan_down 12.3% notable)
    # ⚠️ sfx_probability: 0.109 (global flat — riser vs. sustain_mid driven by SOUND_DESIGN)
    # ⚠️ cut_pacing: fast (building tension — inferred, directional)
    "tension_build": ProductionSpec(
        content_type="tension_build",
        motion_weights=_MOTION_TENSION,
        sfx_probability=0.109,   # global measured rate; sfx_type drives riser vs sustain
        sfx_type="rumble",
        cut_pacing="fast",
        min_seg_sec=2.5,
        max_seg_sec=5.5,
        footage_preference=["document_photo", "reconstructed_footage"],
        clip_probability=0.10,
        text_zone="upper",
    ),

    # ── REVEAL ────────────────────────────────────────────────────────────
    # ✅ footage_preference: evidence frames MEASURED (n=186, best proxy for reveal):
    #    document_photo 88.7%, reconstructed_footage 4.8%
    #    (revelation-labeled only 3 frames — too few; evidence is structurally similar)
    # ✅ sfx_type: riser confirmed by SOUND_DESIGN_FORMULA timing (riser events correlate
    #    with inflection points: -24 to -14 dB energy spikes at plot-twist moments)
    # ✅ motion_weights: _MOTION_EVIDENCE (n=186, zoom_in 41.5%, static 18.9% — holds on doc)
    #    (revelation n=3 too small; evidence frames are structurally identical)
    # ⚠️ sfx_probability: 0.30 — inferred elevated rate for reveal moments;
    #    actual rate not yet measured per content type
    # ⚠️ cut_pacing: fast (tension into reveal) then hold (inferred)
    "reveal": ProductionSpec(
        content_type="reveal",
        motion_weights=_MOTION_EVIDENCE,
        sfx_probability=0.30,    # ⚠️ INFERRED elevated: riser SFX at reveal triggers
        sfx_type="impact",
        cut_pacing="fast",
        min_seg_sec=2.0,
        max_seg_sec=4.5,
        footage_preference=["document_photo", "news_screenshot"],
        clip_probability=0.05,
        text_zone="center",
    ),

    # ── STAKES MOMENT ─────────────────────────────────────────────────────
    # ✅ footage_preference: evidence + tension frames (nearest structural match):
    #    document_photo dominant (87-89%)
    # ⚠️ motion_weights: _MOTION_TENSION proxy (no stakes_moment label in qwen-vl data)
    #    tension_build is the closest structural match (same high-energy doc footage)
    # ⚠️ sfx_probability: 0.15 — inferred slightly elevated for high-stakes moments
    "stakes_moment": ProductionSpec(
        content_type="stakes_moment",
        motion_weights=_MOTION_TENSION,  # ⚠️ proxy — tension_build closest structural match
        sfx_probability=0.15,    # ⚠️ INFERRED
        sfx_type="impact",
        cut_pacing="fast",
        min_seg_sec=2.0,
        max_seg_sec=5.0,
        footage_preference=["document_photo", "archival_footage"],
        clip_probability=0.15,
        text_zone="center",
    ),

    # ── CLIMAX ────────────────────────────────────────────────────────────
    # ✅ footage_preference: climax only 1 frame labeled (too few to measure);
    #    using establishing_context + archival as best structural proxy
    # 🚫 motion_weights: GLOBAL fallback (climax n=1 — insufficient sample)
    # ⚠️ cut_pacing: very_fast — peak action energy (inferred from Trump video cut rate)
    # ⚠️ sfx_probability: 0.20 — inferred elevated for peak moments
    "climax": ProductionSpec(
        content_type="climax",
        motion_weights=GLOBAL_MOTION_WEIGHTS,  # 🚫 fallback — climax n=1, unmeasurable
        sfx_probability=0.20,    # ⚠️ INFERRED
        sfx_type="impact",
        cut_pacing="very_fast",
        min_seg_sec=1.5,
        max_seg_sec=3.5,
        footage_preference=["archival_footage", "document_photo"],
        clip_probability=0.30,
        text_zone="upper",
    ),

    # ── AFTERMATH ─────────────────────────────────────────────────────────
    # ✅ footage_preference: establishing_context (most structurally similar outro):
    #    document_photo 59.7%, documentary_photo 10.9%
    # ⚠️ motion_weights: _MOTION_CONTEXT proxy (no aftermath label in qwen-vl data)
    #    establishing_context is the most similar — slow, informational, resolving
    # ⚠️ sfx_probability: 0.04 — minimal, resolving energy (inferred)
    "aftermath": ProductionSpec(
        content_type="aftermath",
        motion_weights=_MOTION_CONTEXT,  # ⚠️ proxy — establishing_context closest structural match
        sfx_probability=0.04,    # ⚠️ INFERRED
        sfx_type="whoosh",
        cut_pacing="slow",
        min_seg_sec=4.0,
        max_seg_sec=8.0,
        footage_preference=["document_photo", "documentary_photo"],
        clip_probability=0.08,
        text_zone="lower",
    ),
}


# ---------------------------------------------------------------------------
# Classifier — maps chunk data → content type
# ---------------------------------------------------------------------------

def classify_chunk(
    chunk: dict,
    total_duration_sec: float,
    seen_names: set | None = None,
) -> str:
    """
    Classify a narration chunk into a content type.

    Uses:
      - chunk["start_sec"] / total_duration_sec → narrative position
      - chunk["voice_register"] → "neutral" | "tense" | "energized"
      - chunk["text"] → reveal triggers, stakes language, context markers
      - chunk["pause_before_sec"] → long pause = probable reveal setup
      - seen_names → whether this chunk introduces a new named person

    Returns one of: hook_opening, context_background, character_intro,
                    tension_build, reveal, stakes_moment, climax, aftermath
    """
    text         = chunk.get("text", "").lower()
    register     = chunk.get("voice_register", "neutral")
    start_sec    = float(chunk.get("start_sec", 0.0))
    pause_before = float(chunk.get("pause_before_sec", 0.0))

    # Narrative position (0.0 – 1.0)
    pos = start_sec / max(total_duration_sec, 1.0)

    # ── 1. Hook opening (first 10% of video) ─────────────────────────────
    if pos < 0.10:
        # Energized at start = confident hook opening
        if register == "energized":
            return "hook_opening"
        # Even neutral/tense in the first 10% is still hook territory
        if pos < 0.05:
            return "hook_opening"

    # ── 2. Aftermath (last 10%) ───────────────────────────────────────────
    if pos > 0.90:
        if register == "neutral" or any(p in text for p in AFTERMATH_PHRASES):
            return "aftermath"

    # ── 3. Reveal — highest priority signal ──────────────────────────────
    # Long pause before a chunk = the pause before the reveal (Fern signature)
    has_long_pause = pause_before >= 0.7
    has_reveal_trigger = any(t in text for t in REVEAL_TRIGGERS)
    if has_reveal_trigger or (has_long_pause and register == "tense"):
        return "reveal"

    # ── 4. Climax — energized + action language ───────────────────────────
    has_climax_phrase = any(p in text for p in CLIMAX_PHRASES)
    if register == "energized" and (has_climax_phrase or pos > 0.65):
        return "climax"
    if has_climax_phrase and register in ("tense", "energized"):
        return "climax"

    # ── 5. Stakes moment — superlatives + danger ─────────────────────────
    has_stakes = any(p in text for p in STAKES_PHRASES)
    if has_stakes:
        return "stakes_moment"

    # ── 6. Character intro — new named person ────────────────────────────
    if seen_names is not None:
        new_names = _extract_names(chunk.get("text", ""))
        if new_names and not new_names.issubset(seen_names):
            return "character_intro"

    # ── 7. Tension build — tense register + mid-narrative ────────────────
    if register == "tense" and 0.10 < pos < 0.90:
        return "tension_build"

    # ── 8. Context background — default ──────────────────────────────────
    has_context = any(p in text for p in CONTEXT_PHRASES)
    if has_context or register == "neutral":
        return "context_background"

    # Final fallback
    return "context_background"


def get_spec(content_type: str) -> ProductionSpec:
    """Return the ProductionSpec for a content type. Falls back to context_background."""
    return PRODUCTION_RULES.get(content_type, PRODUCTION_RULES["context_background"])


def classify_all_chunks(
    chunks: list[dict],
    total_duration_sec: float,
) -> list[str]:
    """
    Classify every chunk in a narration manifest at once.
    Tracks seen names across chunks for character_intro detection.

    Returns list of content_type strings (same order as chunks).
    """
    seen_names: set[str] = set()
    classifications = []

    for chunk in chunks:
        ct = classify_chunk(chunk, total_duration_sec, seen_names)
        classifications.append(ct)

        # Track names so next chunk doesn't re-trigger character_intro for same person
        new = _extract_names(chunk.get("text", ""))
        seen_names.update(new)

    return classifications


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b')
_FILLER  = {"The", "A", "An", "In", "On", "At", "Of", "By", "New",
            "United", "North", "South", "East", "West"}
_SKIP    = {"States", "War", "Era", "Act", "Bill", "Case", "Street",
            "Avenue", "Commission", "Committee", "Congress", "Senate",
            "January", "February", "March", "April", "June", "July",
            "August", "September", "October", "November", "December"}


def _extract_names(text: str) -> set[str]:
    """Extract likely proper names from text. Returns set of name strings."""
    names = set()
    for m in _NAME_RE.finditer(text):
        name = m.group(1)
        parts = name.split()
        if parts[0] in _FILLER:
            continue
        if any(p in _SKIP for p in parts):
            continue
        names.add(name)
    return names


# ---------------------------------------------------------------------------
# Cut pacing → segment duration range
# ---------------------------------------------------------------------------

PACING_RANGES: dict[str, tuple[float, float]] = {
    "very_fast": (1.5, 3.5),
    "fast":      (2.0, 5.0),
    "normal":    (3.0, 6.5),
    "slow":      (4.0, 8.0),
}


def pacing_range(cut_pacing: str) -> tuple[float, float]:
    """Return (min_sec, max_sec) for segment duration given a cut_pacing label."""
    return PACING_RANGES.get(cut_pacing, PACING_RANGES["normal"])
