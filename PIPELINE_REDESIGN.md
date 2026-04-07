# Pipeline V2 Redesign — Session Handoff

## What Happened (2026-04-07)

Spent an entire session trying to fix 23 bugs across 4 pipeline components. Each fix broke something else. The root problem: the components are tightly coupled and were never tested as a unit.

### Fixes That Actually Worked
- Mute volume: 0dB → -96dB in fcpxml_builder_v2.py (CRITICAL — was playing all clip audio at full volume)
- Whisper medium model: closed the 32s alignment gap (base model dropped 32s of speech)
- Director post-processing: strip invented chapters, cap SFX at 2/chapter
- Real clip transcripts found at `media/breaking_law/transcripts.json` (the file at `footage/breaking_law/transcripts.json` had EMPTY transcripts — director was blind to clip content)

### Fixes That Made Things Worse
- Beat flattening in chapter_assembler: mangled intro video clips into image segments
- 31 clip audio gaps: destroyed pacing, added 115s of silence, made video 31 min
- Lane offset "fix": broke narration positioning (reverted)
- Multiple director re-runs: each produced different problems

### What Was Never Properly Tested
- FCPXML volume keyframes (play_then_mute) — imported but never verified in DaVinci
- Transitions (Cross Dissolve) — generated in FCPXML but never verified
- Ken Burns keyframe animation — generated but never verified
- Beat expansion with video clips preserving clip_audio

## Architecture Problems (Must Fix in Redesign)

### 1. No Integration Tests
Each component was tested in isolation (JSON field checks, grep counts). Nobody verified what actually plays in DaVinci. Need: a 30-second test timeline with known-good clips that verifies every feature before building the full video.

### 2. Voice and Director Don't Talk
The narration WAV has no silence gaps. The director picks clip audio moments. These two systems are independent. The clip_audio_planner was built to bridge them but 31 gaps was too many. Need: director decides 6-8 key moments MAX, planner inserts gaps, both systems agree on the plan before building.

### 3. Intro Is Special-Cased Everywhere
The locked intro spec, the apply_locked_intro.py script, the beat flattening, the chapter card filtering — all have special intro logic that conflicts. Need: intro is a first-class pipeline concept, not a hack layered on top.

### 4. Beat Expansion Destroys Metadata
When chapter_assembler flattens beats into segments, it loses: clip_audio from beats (replaced with parent), visual_file ordering (sorted wrong), and chapter_card association. Need: beats should be the primary unit throughout, not expanded into fake segments.

### 5. Transcripts Were Disconnected
Real transcripts at `media/breaking_law/transcripts.json`. Director was reading empty `footage/breaking_law/transcripts.json`. Director was picking clips by filename only — couldn't match clip audio to narration. This is why clip audio decisions were garbage.

### 6. No Clip Audio Budget
Director prompt said "4-6 moments" but Claude generated 31. No enforcement in code. The planner blindly inserted gaps for all of them. Need: hard cap in code, not just prompt.

## Current State of the Video

### "FINAL" timeline in DaVinci (best version)
- 346 V1 clips, 25.8 min
- Facebook news clip at 0-36s
- Narration at 0-1422s (23.7 min) with 6 silence gaps (18s total)
- 4 chapter cards (THE FORMULA 46s, THE DATA 411s, THE RENT 1216s, THE RECKONING 1457s)
- Mute volume fixed (-96dB)
- Chapter card at 46.4s needs manual deletion (user wants no card in intro)

### Manual fixes needed on FINAL
1. Delete chapter_the_formula.mov from V3 at 46.4s
2. Optionally unmute a few key video clips where their audio would add to the story
3. Create chapter_the_machines.mov (missing file)

### Assets (ALL READY — do not re-source)
- 23 video clips (transcribed in media/breaking_law/transcripts.json)
- 447 images (vision-analyzed)
- 75 overlay MOVs
- 4 chapter card MOVs (THE MACHINES missing)
- 18 SFX (48kHz, normalized)
- 4 music tracks + ducked versions
- narration.wav (23.4 min, 175 WPM, clean)
- narration_gapped.wav (25.3 min, 6 gaps for clip audio)
- narration_alignment.json (Whisper medium, 522 sentences, no gaps >5s)

## Redesign Plan for Next Session

### Phase 1: Test Harness
Build a 60-second test timeline generator that exercises every FCPXML feature:
- 3 video clips (one muted, one play, one play_then_mute with keyframes)
- 3 images (with Ken Burns)
- 1 transition (Cross Dissolve)
- 1 narration WAV
- 1 music track
- 1 SFX
- 1 overlay
Import into DaVinci, play it, verify EVERY feature works before touching the real video.

### Phase 2: Unified Pipeline Runner
Single script that runs all stages in order with verification between each:
1. Director (with real transcripts + cross-batch state)
2. Verify director output (automated checks)
3. Clip audio planner (MAX 8 moments, hardcoded cap)
4. Narration gap insertion
5. Whisper alignment
6. FCPXML build (NO beat expansion — builder reads beats directly)
7. Verify FCPXML
8. Import into DaVinci
9. Read back timeline and verify clip count, duration, audio

Each step gates on the previous. If any step fails, stop and report.

### Phase 3: Intro as First-Class Concept
- `intro_builder.py` — dedicated intro builder
- Reads director's intro picks (3 video clips with audio)
- Places them at 0s with their own audio
- Calculates where VO starts (after intro clips end)
- Passes VO start time to the narration gap planner
- No chapter cards before first [CHAPTER:] marker

### Phase 4: Builder Reads Beats Directly
Remove beat expansion from chapter_assembler. The FCPXML builder already handles beats (lines 213-295). The problem was double-expanding: assembler expanded beats into segments, then builder tried to expand again. Just let the builder read beats directly from the director output.

## Files Modified This Session
- pipeline_v2/fcpxml_builder_v2.py — mute fix, transitions, Ken Burns, lane offsets, SFX cap, music state, marker filtering
- pipeline_v2/director.py — cross-batch state, batch context, clip_audio prompt, chapter card rules, intro format, SFX normalization
- pipeline_v2/chapter_assembler.py — beat flattening (BUGGY — revert for next session), zero-word timestamps, valid chapters, DIRECTOR_PATH
- pipeline_v2/clip_audio_planner.py — NEW (works but needs hard cap)
- pipeline_v2/verify_director.py — NEW (works)
- pipeline_v2/verify_fcpxml.py — NEW (works)
- pipeline_v2/narration_aligner.py — used with medium model (no code changes)
- scripts/fix_director_v5.py — post-processing fixes
- scripts/apply_locked_intro.py — intro lock application
- scripts/generate_chapters.sh — per-chapter voice gen (F5-TTS hallucinated — don't use)
- scripts/align_and_check_chapters.sh — chapter alignment check
- storyboards/breaking_law_directed_v5.json — director v5 output (patched)
- storyboards/breaking_law_directed_v6.json — director v6 output (with real transcripts, but V6 FINAL was worse)
- audio/breaking_law/narration_gapped.wav — narration with silence gaps
- audio/breaking_law/narration_gapped_alignment.json — Whisper alignment on gapped narration

## Key Lessons
1. Never claim something is fixed without verifying it plays correctly in DaVinci
2. Each pipeline change must be tested end-to-end, not just at the JSON level
3. The director MUST have real clip transcripts — it cannot make good decisions without knowing what clips say
4. Clip audio moments must be capped in CODE (max 8), not just in the prompt
5. Beat expansion should happen in ONE place (builder), not in the assembler
6. The intro is structurally different from the rest of the video — treat it as a separate pipeline stage
7. Don't try to fix everything in one session — fix one thing, verify, move on
