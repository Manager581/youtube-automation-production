# YouTube Automation Production — Master Plan
**Target channel to replicate:** @fern-tv (4.6M subscribers)
**Goal:** Fully automated pipeline that produces new YouTube videos in Fern's exact style, on new topics, using the owner's cloned voice.
**Brand config:** `brand_configs/fern_clone.json`

---

## IMPORTANT OPERATING RULES

- **No paid APIs without explicit approval.** Ask first — always.
- **Script generation:** Use Claude Code (Claude Max subscription = free) interactively. Do NOT run `research_pipeline.py` from code — it calls the Anthropic API directly and costs money.
- **All analysis/generation runs locally** via Ollama (qwen3.5:4b or qwen3.5:27b) or OpenCV — zero cost.
- **watop brand:** Ignore for now. Everything here is Fern-specific unless it's clearly general-purpose infrastructure.

---

## The End-to-End Pipeline

```
[TOPIC RESEARCH]     ← topic_radar.py (Reddit/News/YouTube, free) + Fern overlap check
       ↓
[COMMENTS MINING]    ← comments_miner.py (yt-dlp, free)
       ↓
[RESEARCH BRIEF]     ← research_brief.py (Wikipedia/RSS, free)
       ↓
[STORY VALIDATION]   ← story_validator.py (5-dim GO/SKIP/NEEDS WORK, free) + overlap check
       ↓
[SCRIPT GENERATION]  ← Claude Code interactively (Claude Max = free)
       ↓
[SCRIPT ENHANCEMENT] ← script_enhancer.py (local Ollama, free)
       ↓
[SCRIPT QA]          ← check_fern_script.py (scores vs Fern benchmarks — must hit 75+)
       ↓
[VOICE NARRATION]    ← voice_generator.py + F5-TTS (local, free) ← BLOCKER: need voice clips
       ↓
[FOOTAGE SOURCING]   ← footage_sourcer.py (yt-dlp/Archive/Wikimedia, free)
       ↓
[VIDEO ASSEMBLY]     ← video_assembler.py (local ffmpeg/moviepy, free) + mix_audio()
       ↓
[PUBLISH]            ← manual upload (YouTube Studio) for now
```

---

## ACTUAL Pipeline Status (as of 2026-03-02)

### Phase 1: Analysis ✅ COMPLETE

All 3 Fern reference videos fully analyzed. All formula files built.

| Script | Output | Status |
|---|---|---|
| `analyze_fern_hybrid_checkpoint.py` | `timeline_hybrid_qwen-vl.json` per video | ✅ Done (1,838 frames) |
| `analyze_fern_motion.py` | `FERN_MOTION_FORMULA.json` | ✅ Done 2026-03-02 |
| `create_master_formula.py` | `FERN_MASTER_FORMULA.json` | ✅ Done 2026-03-02 (1,784 frames) |
| `measure_color_grade.py` | (feeds master formula) | ✅ Done |
| `fingerprint_music.py` | `MUSIC_IDENTITY.json` | ✅ Done |
| `analyze_sound_design.py` | `SOUND_DESIGN_FORMULA.json` | ✅ Done |
| `analyze_fern_sfx.py` | `FERN_SFX_FORMULA.json` | ✅ Done |
| `analyze_fern_text_animation.py` | `FERN_TEXT_ANIMATION_FORMULA.json` | ✅ Done |
| `check_fern_script.py` | `SCRIPT_FORMULA.json` | ✅ Done |
| (manual) | `THUMBNAIL_FORMULA.json` | ✅ Done |
| (manual) | `TITLE_ANGLE_FORMULA.json` | ✅ Done |

**Videos analyzed:** aVA7aXOH1pk (Trump Assassination Attempt), wLFY_Zu_O08 (FBI/KKK, 41 min), wkVygetgeRY (Unabomber, 28 min)

**Known gap — optional motion re-run:**
Current timelines (qwen-vl / Qwen2.5-VL 7B, 2025 model) lack the new dual-frame fields:
`animation_motion`, `animation_easing`, `kinetic_quality`, `subject_motion`, `cut_timestamps`.
As a result, `transition_types` in the motion formula shows all-zeros.
**Fix:** Re-run with `qwen3.5-4b` on M1 overnight — see M1 Setup section.

---

### Phase 2: Research Pipeline ✅ BUILT — ready to run (all free)

| Script | What it does | Cost |
|---|---|---|
| `pipeline/topic_radar.py` | Scans Reddit/Google News/YouTube for viral story candidates scored against Fern's formula | Free (public APIs) |
| `pipeline/comments_miner.py` | Mines YouTube comments for topic signals + audience curiosity gaps. Uses cached `comments.json` for all 3 Fern videos already downloaded. | Free (yt-dlp) |
| `pipeline/research_brief.py` | Wikipedia background + news RSS + footage leads → structured JSON + Markdown brief | Free |
| `pipeline/story_validator.py` | Scores story on 5 dimensions (factual depth, viral hook, arc, visuals, public interest). GO/NEEDS WORK/SKIP verdict. Animation fallback: scores low on visual_assets → sets `visual_strategy = "ANIMATED"` and passes anyway. | Free |

**Fern title duplicate checker** (built into both `topic_radar.py` and `story_validator.py`):
- Jaccard similarity on title key terms (title-only, NOT description — descriptions dilute scores)
- Acronym exact-match bonus: FBI, CIA, KKK etc. (+0.15 per match, max +0.30)
- Proper-noun bonus: people/places (+0.10 per match, max +0.20)
- Thresholds: ≥0.60 → HARD_SKIP (returns None immediately), ≥0.30 → WARNING (−15 pts, noted)
- Runs against all `analysis/fern/*/video.info.json` files (28 of 30 videos have this)
- **Catalog gap:** `aVA7aXOH1pk` (Trump) and `wkVygetgeRY` (Unabomber) have no `video.info.json` — visually analyzed but metadata not downloaded. These 2 are NOT in the overlap catalog. Minor gap — add manually if needed.

**Comments already cached:** `analysis/fern/*/comments.json` exists for all 3 analyzed videos.
**Output location:** `research/fern_clone/`

**Full research run:**
```bash
venv/bin/python pipeline/topic_radar.py --brand fern_clone
venv/bin/python pipeline/comments_miner.py --brand fern_clone
venv/bin/python pipeline/research_brief.py --brand fern_clone --query "Your Topic Here"
venv/bin/python pipeline/story_validator.py --query "Your Topic Here" --brand fern_clone
```

---

### Phase 3: Script Generation ✅ READY (via Claude Code — free)

**Do NOT run `research_pipeline.py` from code** — it calls `Anthropic()` API directly = costs money.

**Correct workflow (all free):**
1. Research scripts produce `research/fern_clone/briefs/{topic}.json`
2. Open Claude Code (this terminal — Claude Max subscription)
3. Paste the brief and say: *"Write a full Fern-style script using SCRIPT_FORMULA.json and FERN_MASTER_FORMULA.json"*
4. Claude writes the script interactively — free via Max
5. Save to `scripts/{topic}.txt`

**Key formula stats:**
- Target: ~4,200 words, 25 min @ 138.7 WPM
- Structure: hook (0–30s visceral moment) → context → escalation → revelation → climax → outro
- Sentence rhythm: short declarative → medium explanation → short punchline
- Rhetorical questions every ~45 seconds
- Curiosity gaps: 0.43/min (always close one, open another)
- Chapter breaks: use `[PAUSE:5.0]` in script at chapter markers

---

### Phase 4: Script Enhancement ✅ BUILT — free, local Ollama

Transforms raw script into narration-ready format: emotion markers, strategic pauses, 138.7 WPM pacing.

```bash
venv/bin/python pipeline/script_enhancer.py \
  --input scripts/raw_topic.txt \
  --output scripts/enhanced_topic.txt
```

Adds: `[BEAT]` (0.3s), `[PAUSE:1.2]`, `[BREATH]` (0.15s), `[VOICE:tense/neutral/energized]` markers.
Uses Ollama locally (recommend `qwen2.5:32b` on M5, or `qwen3.5:27b` if installed).

---

### Phase 4.5: Script Quality Check ✅ BUILT — `check_fern_script.py`

Run this after script enhancement to score the script against Fern's measured benchmarks before investing voice time:

```bash
venv/bin/python check_fern_script.py scripts/enhanced_topic.txt
```

Scores 8 dimensions (0–100): duration, hook quality, re-engagement, curiosity gaps (0.43/min), emotional density (0.54%), word choice, title, structure.

**Grading:**
- 85+ = A — Very close to Fern's style. Minor tweaks only.
- 75–84 = B — Good but needs refinement in weak areas.
- 65–74 = C — Several structural issues to fix.
- Below 75 = D/F — Rewrite needed before proceeding to voice.

Reads formulas from: `analysis/fern/SCRIPT_FORMULA.json` + `analysis/fern/FERN_MASTER_FORMULA.json`.

---

### Phase 5: Voice Cloning + Narration ✅ COMPLETE — free, local (F5-TTS v1.1.16)

**Voice reference clips recorded and preprocessed ✅**
All 6 files exist in `assets/voice/`:
- `voice_neutral.wav` + `voice_neutral_ref.wav` (trimmed 10s ref)
- `voice_tense.wav` + `voice_tense_ref.wav`
- `voice_energized.wav` + `voice_energized_ref.wav`

**Step 1: Clean recordings**
```bash
venv/bin/python pipeline/audio_preprocessor.py \
  --input my_raw_recording.wav \
  --output assets/voice/voice_neutral.wav \
  --report
```
Applies: 80Hz high-pass filter, noise reduction, loudness normalization to -23 LUFS, resample to 24kHz.

**Step 2: Generate narration**
```bash
venv/bin/python pipeline/voice_generator.py \
  --ref-neutral   assets/voice/voice_neutral_ref.wav \
  --ref-tense     assets/voice/voice_tense_ref.wav \
  --ref-energized assets/voice/voice_energized_ref.wav \
  --auto-transcribe \
  --script scripts/enhanced_topic.txt \
  --out audio/topic/narration.wav
```
Note: use `*_ref.wav` files (trimmed to 10s) — F5-TTS clips anything longer than 12s which causes erratic output speed.
Output: `narration.wav` + word-level timestamps for video sync.

---

### Phase 6: Audio Mix ✅ BUILT — inside video_assembler.py

Audio mixing is fully implemented inside `pipeline/video_assembler.py` via the `mix_audio()` function (line ~934). A separate `mix_audio.py` is not needed.

**What's built:**
- Narration + music mixing via ffmpeg `amix` filter
- Music volume envelope: louder for first 3s intro, then ducks under narration
- Looping music track for full video duration
- AAC output at 192k

**Audio analysis complete (3 videos):**
- `aVA7aXOH1pk_audio_analysis.json`, `wLFY_Zu_O08_audio_analysis.json`, `wkVygetgeRY_audio_analysis.json` — BPM, beat timing, music change points
- `aVA7aXOH1pk_audio_full.json`, `wLFY_Zu_O08_audio_full.json`, `wkVygetgeRY_audio_full.json` — full demucs stem separation results
- `FERN_SFX_FORMULA.json` — SFX spec: 10.9% of cuts have SFX, dominant type `impact_thud`, verdict: "minimal SFX — cuts are mostly clean audio transitions"
- `MUSIC_IDENTITY.json` — per-video music fingerprint
- `SOUND_DESIGN_FORMULA.json` — ambient + music layer spec

**Measured Fern audio spec:**
- BPM: ~117 (measured from Trump video; dark cinematic tempo)
- SFX: minimal (only 10.9% of cuts), impact_thud dominant — no heavy SFX layer needed
- Assembler guidance from formula: "No SFX layer needed — cuts are clean audio transitions"

**SFX available in `assets/sfx/` (committed):**
`rumble_01–03.mp3`, `impact_01–02.mp3`, `tension_01.mp3`, `shimmer_01–03.mp3`, `whoosh_01–05.mp3`

**To mix:** `video_assembler.py --music assets/music/track.mp3` handles it automatically.

---

### Phase 6.5: Storyboard Generation ✅ BUILT — free, local Ollama

**Closes the single biggest quality gap: footage is now story-driven, not tag-pool random.**

For each narration segment, tells the assembler:
- What SPECIFIC visual to show (not "a document" — "the 1973 FBI memo with CONFIDENTIAL stamp")
- Exact search query for footage_sourcer (targeted, not generic tags)
- What focal element Ken Burns pulls toward (the date, the name, the building)
- Shot type + intensity

```bash
venv/bin/python pipeline/storyboard_generator.py \
  --script scripts/enhanced_topic.txt \
  --out storyboards/topic.json
```

Runs fully locally via Ollama (qwen3.5:27b recommended on M5 24GB — 17GB fits, much better story comprehension; falls back to qwen3.5:4b → rule-based extraction). Results cached per segment — re-run is fast.

**Story-aware chain:** every downstream choice is now story-aware:
- Storyboard → footage search query (story-specific)
- Storyboard focal_element → Ken Burns target (story-specific)
- Narration emotion → music intensity (story-specific)
- [PAUSE:5.0] chapter markers → music swells + chapter cards (story-specific)

**When footage doesn't exist → animate it:** If footage_sourcer returns nothing for a storyboard entry, the assembler currently falls back to black screen + Ken Burns on any available image. The storyboard `shot_type` field is designed to trigger animation generation when that pipeline is built (e.g. "no archival footage found → generate with Blender/After Effects"). This is the bridge to the animation layer.

---

### Phase 7: Video Assembly ✅ BUILT — free, local

**Step 1 — Source footage (now storyboard-driven):**
```bash
venv/bin/python pipeline/storyboard_generator.py --script scripts/enhanced_topic.txt --out storyboards/topic.json
venv/bin/python pipeline/footage_sourcer.py \
  --brand fern_clone \
  --brief research/fern_clone/briefs/topic.json \
  --out footage/fern_clone/topic/
```
Sources from: YouTube (yt-dlp), Internet Archive, Wikimedia Commons images (all free).

**Storyboard integration — FULLY WIRED (2026-03-02):**

```bash
# Step 1: Generate storyboard (after script enhancement)
venv/bin/python pipeline/storyboard_generator.py \
  --script scripts/enhanced_topic.txt \
  --out storyboards/topic.json

# Step 2: Source footage using storyboard queries (story-specific searches)
venv/bin/python pipeline/footage_sourcer.py \
  --brand fern_clone \
  --brief research/fern_clone/briefs/topic.json \
  --storyboard storyboards/topic.json \
  --download

# Step 3: Assemble with storyboard-aware clip selection
venv/bin/python pipeline/video_assembler.py \
  --brand fern_clone \
  --narration audio/topic/narration_manifest.json \
  --footage footage/fern_clone/topic/manifest.json \
  --music assets/music/track.mp3 \
  --storyboard storyboards/topic.json \
  --out output/topic/final.mp4
```

How it works end-to-end:
1. `storyboard_generator.py` → per-segment: `show`, `search_query`, `focal_element`, `shot_type`
2. `footage_sourcer.py --storyboard` → runs targeted search per storyboard query → tags each clip with `storyboard_segment_ids`
3. `video_assembler.py --storyboard` → for each narration chunk, text-matches to storyboard entry → picks the tagged clip first → falls back to round-robin if none found
4. `focal_element` from storyboard → Ken Burns target (positional description → coordinates, no vision model needed for explicit descriptions)

**Assemble video:**
```bash
venv/bin/python pipeline/video_assembler.py \
  --brand fern_clone \
  --narration audio/topic/narration_manifest.json \
  --footage footage/fern_clone/topic/manifest.json \
  --music assets/music/track.mp3 \
  --out output/topic/final.mp4 \
  [--dry-run]   # preview timeline without rendering
```

**Production constants (from Fern analysis, hardcoded):**
- Ken Burns: 5%/sec zoom, 40% zoom-in / 25% zoom-out / 26% static
- Color grade: 0.46× saturation, 7% black crush, 0.90 gamma
- Cuts: content-driven, avg 4–6s per segment
- Text: slide_reveal 511ms, held ~9s
- Chapter cards: white serif typewriter text on black

**Footage guardrails (built 2026-03-02):**
`footage_sourcer.py` now enforces:
- `SEARCH_TIMEOUT_SEC = 20` — each search terminates after 20s so the pipeline never hangs
- `MIN_VIABLE_IMAGES = 10` / `MIN_VIABLE_CLIPS = 2` — thresholds for "sufficient footage"
- `needs_animation` list — after searching, segments with zero image AND zero clip coverage are flagged in the manifest so the animation layer can fill them

**Clip pivotal moment detection — `pipeline/clip_analyzer.py` ✅ BUILT:**
The pipeline previously always started clips from position 0 — taking the first 5s of a 3-minute AP Archive clip. `clip_analyzer.py` solves this:
- Samples frames every 2s throughout the clip
- Scores each window against the storyboard `show` description using a local vision model (qwen3.5:4b)
- Falls back to scene-change activity score if no vision model available
- Returns `(start_sec, duration_sec)` — the best 5-second window in the clip
- Results cached in `.clip_moment_cache/`
- Adds `clip_start_sec` to manifest; `video_assembler.py` passes this to `prepare_clip()`

```bash
# Analyze one clip
venv/bin/python pipeline/clip_analyzer.py clip \
  --clip footage/topic/ap_archive.mp4 \
  --show "FBI director testifying at Senate hearing" \
  --duration 5.0

# Batch process all clips in a footage manifest
venv/bin/python pipeline/clip_analyzer.py manifest \
  --manifest footage/fern_clone/topic/manifest.json
```

---

### Phase 7.5: Final Video QA ✅ BUILT — `check_fern_video.py`

Run after assembly, before upload. Validates against Fern's measured benchmarks.

```bash
venv/bin/python check_fern_video.py output/topic/final.mp4
# Auto-detects output/topic/timeline.json and assets/music/track.mp3
# Or explicitly:
venv/bin/python check_fern_video.py output/topic/final.mp4 \
  --timeline output/topic/timeline.json \
  --music assets/music/track.mp3
```

**Checks (8 total):**
| Check | Target | Fail condition |
|---|---|---|
| Duration | 22–27 min | <18 min or >32 min = FAIL |
| Cut rate | 11.3 cuts/min | <8 or >15 = WARN |
| Audio levels | -14 to -18 LUFS | <-23 or >-10 = WARN |
| Color grade | Saturation <0.35 | >0.40 = WARN (ungraded) |
| A/V sync | <0.5s drift | >2.0s = FAIL |
| Chapter cards | ~5 per video | 0 = WARN |
| Footage variety | No clip >3× | >3× = WARN |
| Beat sync | ~39% on-beat | <25% = WARN |

Exit code 0 = PASS/WARN, exit code 1 = FAIL. Pipeline can gate on this: `if check_fern_video.py fails → do not upload`.

Note: `video_assembler.py` now saves `output/topic/timeline.json` alongside the final video automatically. check_fern_video.py picks it up without any flags.

---

### Phase 8: Thumbnail + Title ❌ NOT YET BUILT as scripts

**Title (use Claude Code — free):**
Paste `TITLE_ANGLE_FORMULA.json` + video topic into Claude Code, ask for 3 title options ranked by formula score.

**Top title patterns by performance:**
1. `How [Institution] [Shocking Action]` — avg 11.2M views
2. `[Country]'s [Most/Hidden] [Dark Reality]` — avg 5.6M views
3. `The [Person] Who [Achievement] (and [Dark Consequence])` — avg 4.2M views

**Thumbnail (manual for now):** Follow `THUMBNAIL_FORMULA.json`. Ask before using DALL-E 3 or any paid image API.

---

### Phase 8.5: Interactive Pipeline Runner ✅ BUILT — `run_pipeline.py`

The single command that runs the entire pipeline. Replaces memorizing 13 commands.

```bash
python run_pipeline.py          # start or resume
python run_pipeline.py --list   # see all stages
python run_pipeline.py --status # see where you are
python run_pipeline.py --from footage  # jump to a stage
python run_pipeline.py --reset  # start over
```

**How it works:**
- Runs every automated step with **live terminal output** — you see everything as it happens
- Stops at **your decision points** with a plain-English question box:
  - *Topic selection* — shows scored candidates from topic_radar, you pick 1–8 or type your own
  - *Story validation* — shows GO/SKIP/NEEDS WORK, you confirm or override
  - *Script score* — shows 0–100 score, blocks if <75, warns if <85
  - *Voice QA* — auto-runs `check_fern_voice.py` (LUFS, WPM, silence, clipping). Only stops if FAIL.
  - *Footage verification* — auto-runs `footage_verifier.py` (vision model scores each item vs storyboard). Auto-removes bad items. Only asks if coverage < 40%.
  - *Final upload* — shows QA results, you watch the video, you approve
- **State saved** between runs (`.pipeline_run.json`) — Ctrl+C anytime, resume exactly where you left off
- `monitor.py` still works alongside as a passive background dashboard (separate terminal)

### Phase 9: Publish ○ MANUAL FOR NOW

Manual upload via YouTube Studio is sufficient. `publish_video.py` (YouTube Data API v3) can be built when volume warrants it.

---

## Current State Summary

```
ANALYSIS:    ██████████  100% (3 videos, 1,838 frames; optional qwen3.5 re-run for motion fields)
RESEARCH:    ██████████  100% (30 videos: comments/titles/transcripts; 237 topic signals)
SCRIPT GEN:  ██████████  100% (Claude Code interactive + script_enhancer.py + check_fern_script.py)
STORYBOARD:  ██████████  100% (storyboard_generator.py — story-driven per-segment visual direction)
VOICE:       ██████████  100% (F5-TTS + audio_preprocessor + voice_generator built + voice clips recorded)
AUDIO MIX:   ██████████  100% (mix_audio() inside video_assembler.py; all formulas measured)
MUSIC:       ██████████  100% (music_sourcer.py — mood-matched CC0 track; Pixabay free API)
VIDEO:       ██████████  100% (footage_sourcer + video_assembler; Ken Burns + color grade + text + beat sync)
VIDEO QA:    ██████████  100% (check_fern_video.py — 8-check gate before upload)
CLIP MOMENT: ██████████  100% (clip_analyzer.py — best window via vision model; prepare_clip() uses clip_start_sec)
ANIMATION:   ██████████  100% (animation_generator.py — doc/map/person/text cards via Pillow; auto-triggered; NO black screens)
VOICE QA:    ██████████  100% (check_fern_voice.py — LUFS, WPM, silence, clipping; PASS/WARN auto-proceed, FAIL blocks)
FOOTAGE QA:  ██████████  100% (footage_verifier.py — vision model scores each item vs storyboard; auto-removes bad items)
THUMBNAIL:   ░░░░░░░░░░    0% (use Claude Code + manual — no script needed until volume)
PUBLISH:     ██████████  100% (manual upload works fine)
```

**No blockers for first video.** Everything is ready to run.

**Precision enhancements built (2026-03-02):**
1. ✅ **Beat sync** — `video_assembler.py` now loads beat timestamps from music via librosa. Any cut naturally falling within ±100ms of a beat snaps to it. Produces ~39% beat-synced cuts at 116 BPM — Fern's measured rate. Zero config, automatic.
2. ✅ **Ken Burns focal point** — `video_assembler.py --focal-points` now calls local vision model (qwen3.5:27b preferred) via Ollama REST API. Focal point is **story-driven**: the model is told what the narrator is saying at that moment and finds the story element in the frame (a date on a document, a name, a building — whatever the narration points at). Results cached per (image, narration_hash). Falls back to center if model unavailable.
   - Requires: `ollama pull qwen3.5:27b` (17GB) — not yet downloaded
   - Falls back to: `qwen3.5:4b` → `qwen2.5vl:7b` → center (0.5, 0.5)
3. ✅ **Storyboard generator** — `pipeline/storyboard_generator.py` converts enhanced script into per-segment visual brief. Every downstream choice is now story-aware: footage search queries are specific, Ken Burns focal_element is explicit, intensity matches emotion. Replaces random tag-pool selection.
4. ✅ **Final video QA** — `check_fern_video.py` validates assembled video against Fern benchmarks (8 checks: duration, cut rate, audio levels, color grade, A/V sync, chapter cards, footage variety, beat sync). Run before every upload.
5. ✅ **Timeline saved** — `video_assembler.py` now saves `output/{topic}/timeline.json` automatically. Used by `check_fern_video.py` for chapter card and footage variety checks.
6. ✅ **Music sourcer** — `pipeline/music_sourcer.py` analyzes script mood, downloads free CC0 track. Pixabay API is free (register at pixabay.com → API, no payment). Set `PIXABAY_API_KEY` env var.
7. ✅ **Story-aware animation bridge** — storyboard `shot_type` field carries the intent for animation: when footage_sourcer returns nothing for a story beat, `shot_type` tells the animation layer exactly what to create. Black fallback was old; now `pipeline/animation_generator.py` generates the visual automatically.
8. ✅ **Clip pivotal moment detection** — `pipeline/clip_analyzer.py` finds the best window in a downloaded clip using vision model frame scoring. `prepare_clip()` now uses `clip_start_sec` from the manifest — no more "always take from position 0" gap.
9. ✅ **Animation generator** — `pipeline/animation_generator.py` generates still image frames (document cards, map cards, portrait cards, text cards) using Pillow when real footage is unavailable. Images feed directly into the existing Ken Burns pipeline. Segments tagged `needs_animation` in the manifest automatically get generated visuals — no black screens.
10. ✅ **Footage guardrails** — `footage_sourcer.py` now has `SEARCH_TIMEOUT_SEC = 20` per search, minimum viable footage thresholds, and `needs_animation` detection. The pipeline will not hang and will always report what it found vs. what needs to be generated.
11. ✅ **Automated voice QA** — `check_fern_voice.py` runs immediately after voice_generator. Checks: integrated LUFS (-20 to -16 target), WPM from manifest timestamps (138.7 target), silence ratio (<25% warn, <45% fail), peak level (clipping detection). PASS or WARN auto-proceed — no listening required. Only FAIL stops the pipeline.
12. ✅ **Automated footage verification** — `pipeline/footage_verifier.py` scores every downloaded image/clip against its storyboard description using a vision model. Items scoring <0.10 (completely unrelated) are removed from the manifest automatically. Reports per-segment coverage: ≥60% auto-proceeds, 40–59% warns but proceeds, <40% asks user. Note: clip audio is already stripped by `-an` in `prepare_clip()` — footage verifier doesn't need to handle this.
13. ✅ **No black screens** — `video_assembler.py` final fallback (no footage + no storyboard) now generates a narration text card via `animation_generator.py` instead of black. Content segments never show black. Only the 0.4s chapter card padding intentionally uses black.
15. ✅ **`local_path` vs `path` field bug fixed** — `video_assembler.py` was filtering stills/videos with `c.get("path","")` but `footage_sourcer.py` writes `"local_path"`. All video clips were silently dropped into an empty `videos` list every run. Fixed: `_clip_path_str()` helper checks `local_path` first with `path` fallback. Also added `c.get("downloaded")` guard so undownloaded manifest entries are never counted.
16. ✅ **Voice QA WPM check silently skipped (fixed)** — `check_fern_voice.py` `check_wpm()` was reading `manifest.get("chunks",[])` but `voice_generator.py` writes `"segments"`. WPM check always returned SKIP with no warning. Also reading `"start"/"end"` timestamp fields instead of `"start_sec"/"end_sec"`. Fixed both: falls back to `segments` (speech-only), reads `"start_sec"/"end_sec"` with legacy fallback.
17. ✅ **Story coherence — `pause_before_sec` in voice manifest** — `production_rules.py` reveal detection checks `chunk.get("pause_before_sec", 0.0) >= 0.7` to identify Fern's signature pause-before-reveal. `voice_generator.py` never wrote this field — reveal detection silently fired zero times. Fixed: `voice_generator.py` now tracks accumulated pause duration and writes `"pause_before_sec"` on every speech segment.
18. ✅ **Story coherence — `narrative_function` in storyboard** — `production_rules.py` was guessing content type (reveal/climax/tension) from keyword scans of narration text. The storyboard LLM has full script context — far more accurate. Added `narrative_function` field to `storyboard_generator.py`: LLM labels each segment directly (`hook_opening / context_background / character_intro / tension_build / reveal / stakes_moment / climax / aftermath`). Fallback uses keyword heuristics when model unavailable.
19. ✅ **Story coherence — focal_element default (no flag required)** — `_focal_from_description()` converts storyboard `focal_element` text ("date stamp top-right") to (x, y) coordinates without any model call. Was gated behind `--focal-points` flag. Fixed: text-based focal from storyboard now always applies when available; vision model is fallback only when `--focal-points` flag is set.
20. ✅ **Story coherence — full spec override + window search** — Two related fixes in `video_assembler.py`: (a) storyboard `narrative_function` now overrides the keyword-based `content_type` classification at the chunk level, propagating to motion weights, SFX probability/type, text zone, and cut pacing for ALL inner-loop segments in that chunk. (b) Tagged footage search expanded from exact storyboard index to a 6-entry window (`sb_cursor` to `sb_cursor+5`) — a 150-word chunk spans ~3-5 storyboard segments, so the old single-index search missed adjacent tagged footage. (c) Storyboard match moved before the inner while loop so the spec override affects pacing and motion from the start.
14. ✅ **Full storyboard→voice→assembly integration** — Four bugs fixed / enhancements wired:
    - **`chunks` vs `segments` (CRITICAL BUG FIXED)**: voice_generator outputs `"segments"` in manifest; assembler was reading `"chunks"` → empty timeline. Now reads `segments`, filters to speech-only.
    - **Chapter cards from storyboard**: voice_generator doesn't write chapter data. Assembler now extracts chapter timing from storyboard `is_chapter_break` entries via proportional position mapping → chapter cards appear at the right moments.
    - **Intensity-driven Ken Burns zoom rate**: storyboard `intensity` now modulates `make_ken_burns()` zoom speed per segment. `tense`=7%/sec, `ominous`=2.5%/sec, `energized`=8%/sec, `neutral`=5%/sec. Tense scenes push in faster; ominous scenes drift almost imperceptibly.
    - **Sequential storyboard matching**: was doing full O(n²) rescan per chunk. Now uses windowed sequential search from last match position — correct because narration and storyboard are both in script order.

**Steps to produce the first video:**

**Automated steps** (run and wait):
1. `python pipeline/topic_radar.py --brand fern_clone` — finds candidates, auto-checks Fern overlap
2. `python pipeline/comments_miner.py --brand fern_clone` — refresh audience signals (already cached)
3. `python pipeline/research_brief.py --brand fern_clone --query "{chosen topic}"`
4. `python pipeline/story_validator.py --query "{chosen topic}" --brand fern_clone` — GO/SKIP + overlap check

**Manual decision:** Pick the topic. High viral score + low Fern overlap. No script saves a bad topic.

5. Claude Code: write script from brief (reference SCRIPT_FORMULA.json + FERN_MASTER_FORMULA.json). Target ~4,200 words / 25 min.
6. `python pipeline/script_enhancer.py --input scripts/raw.txt --output scripts/enhanced.txt`
7. `python check_fern_script.py scripts/enhanced.txt` — **must score 85+ before proceeding**
8. `python pipeline/storyboard_generator.py --script scripts/enhanced_{topic}.txt --out storyboards/{topic}.json` — per-segment visual brief (story-driven)
9. `python pipeline/voice_generator.py --ref-neutral assets/voice/voice_neutral_ref.wav --ref-tense assets/voice/voice_tense_ref.wav --ref-energized assets/voice/voice_energized_ref.wav --auto-transcribe --script scripts/enhanced_topic.txt --out audio/topic/narration.wav`
   → Then immediately: `python check_fern_voice.py audio/{topic}/narration.wav --script scripts/enhanced_{topic}.txt --manifest audio/{topic}/narration_manifest.json`
   → **PASS or WARN = proceed. FAIL = regenerate.** No manual listening needed.

10. `python pipeline/music_sourcer.py --script scripts/enhanced_{topic}.txt` — mood-matched CC0 track → `assets/music/track.mp3`
11. `python pipeline/footage_sourcer.py --brand fern_clone --brief research/fern_clone/briefs/{topic}.json --storyboard storyboards/{topic}.json --download --out footage/fern_clone/{topic}/`
    → Then immediately: `python pipeline/footage_verifier.py --manifest footage/fern_clone/{topic}/manifest.json`
    → Vision model scores each item vs storyboard description. Removes bad items automatically. **No manual review needed** — low coverage (<40%) asks for override.

12. `python pipeline/video_assembler.py --brand fern_clone --narration audio/{topic}/narration_manifest.json --footage footage/fern_clone/{topic}/manifest.json --music assets/music/track.mp3 --storyboard storyboards/{topic}.json --out output/{topic}/final.mp4`
    → Saves `output/{topic}/timeline.json` automatically.
13. `python check_fern_video.py output/{topic}/final.mp4` — **must PASS or WARN before upload**

**Manual:** Watch the full video. Then upload to YouTube Studio.

---

## Hardware Notes

- **M5 24GB** — main machine. Use for everything.
- **M1 16GB** — 16GB only. Do NOT use for model inference or overnight analysis runs. Not enough headroom.

---

## Live Monitor

```bash
# Terminal 1 — run analysis, stream to log
venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen3.5-4b 2>&1 | tee /tmp/fern_analysis.log

# Terminal 2 — live dashboard (shows analysis + full pipeline status + formula files)
venv/bin/python monitor.py
```

---

## Key Files Reference

| File | Purpose |
|---|---|
| `MASTER_PLAN.md` | This file — read first after reconnects |
| `brand_configs/fern_clone.json` | Brand identity, topic filters, title formulas |
| `analysis/fern/FERN_MASTER_FORMULA.json` | THE formula — feeds all generation scripts |
| `analysis/fern/FERN_MOTION_FORMULA.json` | Camera + optical flow + transitions |
| `analysis/fern/SCRIPT_FORMULA.json` | Script writing rules |
| `analysis/fern/MUSIC_IDENTITY.json` | Music selection + BPM (116 BPM, dark cinematic) |
| `analysis/fern/SOUND_DESIGN_FORMULA.json` | SFX + ambient spec |
| `analysis/fern/THUMBNAIL_FORMULA.json` | Thumbnail composition rules |
| `analysis/fern/TITLE_ANGLE_FORMULA.json` | Title patterns ranked by view performance |
| `analysis/fern/FERN_STYLE_GROUND_TRUTH.json` | Ground truth style reference |
| `pipeline/storyboard_generator.py` | Story-driven per-segment visual brief — runs after script enhance, before footage |
| `pipeline/clip_analyzer.py` | Find the pivotal moment in a downloaded clip — vision model frame scoring → clip_start_sec |
| `pipeline/animation_generator.py` | Generate still image frames when real footage unavailable — doc/map/person/text cards via Pillow |
| `check_fern_script.py` | Pre-voice script QA (must score 85+) |
| `check_fern_voice.py` | Post-generation voice QA — LUFS, WPM, silence, clipping. Automated; PASS/WARN auto-proceed |
| `pipeline/footage_verifier.py` | Vision model scores each downloaded item vs storyboard. Auto-removes bad items. |
| `check_fern_video.py` | Post-assembly video QA gate (8 checks vs Fern benchmarks) — run before upload |
| `monitor.py` | Live pipeline dashboard (run in second terminal) |
| `research_pipeline.py` | ⚠️ USES PAID API — do not run; use Claude Code instead |

---

*Last updated: 2026-03-02 (session 3)*
*Videos analyzed: aVA7aXOH1pk (Trump), wLFY_Zu_O08 (FBI/KKK), wkVygetgeRY (Unabomber) — 3 total, 1,838 frames*
*30 Fern videos: comments + titles + transcripts + signals all committed to GitHub*
*All pipeline scripts: topic_radar, comments_miner, research_brief, story_validator, script_enhancer, check_fern_script, storyboard_generator, voice_generator, audio_preprocessor, music_sourcer, footage_sourcer, video_assembler, check_fern_video — ALL COMPLETE*
*Beat sync: built 2026-03-02 — librosa beat_track + snap_to_beat in video_assembler.py*
*Ken Burns focal point: built 2026-03-02 — story-aware detect_focal_point() via Ollama REST API, cached per (image, narration_hash). Needs qwen3.5:27b pulled (17GB).*
*Storyboard generator: built 2026-03-02 — per-segment visual brief, story-driven footage search + Ken Burns focal_element*
*Final video QA: built 2026-03-02 — check_fern_video.py, 8 checks, auto-detects timeline.json and music*
*Music sourcer: built 2026-03-02 — mood analysis + Pixabay CC0 (free API, no payment)*
*Animation bridge: storyboard shot_type field reserved for future Blender/AE pipeline when footage not found*
*Storyboard fully wired 2026-03-02: footage_sourcer --storyboard + video_assembler --storyboard both integrated*
*Full story-aware chain complete: script → storyboard → targeted footage search → tagged clips → story-specific assembly → QA → upload*
*Clip pivotal moment: built 2026-03-02 — clip_analyzer.py, vision model frame scoring, clip_start_sec in manifest*
*Animation generator: built 2026-03-02 — animation_generator.py, Pillow doc/map/person/text cards, auto-triggered from needs_animation*
*Footage guardrails: built 2026-03-02 — SEARCH_TIMEOUT_SEC, MIN_VIABLE thresholds, needs_animation flagging in manifest*
*Bug fix 2026-03-02: video_assembler.py local_path/path field — videos list was always empty; fixed with _clip_path_str() + downloaded guard*
*Bug fix 2026-03-02: check_fern_voice.py WPM always SKIP — chunks→segments fallback + start_sec/end_sec timestamp fields*
*README.md: replaced old WATOP/space-facts content with accurate Fern pipeline setup guide*
*Full story-aware + animation pipeline complete: no black screens, no wrong clip windows, no hanging searches*
*Voice QA automated: check_fern_voice.py — LUFS/WPM/silence/clipping auto-check; PASS+WARN auto-proceed, FAIL regenerates. No manual listening.*
*Footage verification automated: pipeline/footage_verifier.py — vision model scores each item vs storyboard; bad items auto-removed; <40% coverage asks user.*
*run_pipeline.py updated: stage_voice and stage_footage both now fully automated. Manual decision points reduced to: topic, story (GO/SKIP), script, final upload.*
*No-black-screens rule enforced: video_assembler.py final fallback now generates narration text card. Content segments never black.*
*Full storyboard integration: CRITICAL BUG fixed (chunks vs segments field name). Chapter cards from storyboard is_chapter_break. Intensity→KB zoom rate (tense=7%/sec, ominous=2.5%/sec). Sequential storyboard matching.*
*Story coherence fixes (session 3): 4 connective-tissue bugs fixed that were silently breaking Fern-style narrative-driven production. (1) voice_generator.py pause_before_sec: reveal detection now fires. (2) storyboard_generator.py narrative_function: LLM labels each segment directly — no more keyword guessing. (3) video_assembler.py focal_element default: text-based focal always applied from storyboard, no flag. (4) video_assembler.py spec override + window search: narrative_function from storyboard overrides motion/SFX/pacing; window search finds tagged footage across 6 storyboard entries per chunk.*
