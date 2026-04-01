# Pipeline V2 Audit — What Actually Works vs What's Broken

**Date:** 2026-03-31
**Video:** "Why Breaking the Law Is Profitable"
**Status:** Rendered but not production quality

---

## TL;DR

The pipeline has 28 stages. About 60% actually work end-to-end. The remaining 40% are stubs, partially implemented, or disconnected from each other. The rendered video plays (17.5 min, 1080p24, audio throughout) but has quality issues that stem from stages not being properly connected.

---

## USER-REPORTED ISSUES + ROOT CAUSES

### 1. "VO too fast, repeats itself"
**Root cause:** The user reported this but the audit shows narration.wav is clean (Whisper alignment shows no repeats, 209 WPM average). The perceived speed issue is likely:
- Some F5-TTS chunks generated faster than others (no WPM normalization — flag `--no-wpm-normalize` was used)
- The Whisper alignment timestamps are correct but the FCPXML builder places V1 clips based on these timestamps — if a clip is 5s but the narration for that segment is 3s, there's a visual-audio mismatch
- **FIX NEEDED:** Re-generate narration with WPM normalization, or adjust V1 clip durations to match actual narration timing per segment

### 2. "No text overlays visible"
**Root cause:** 140+ overlay MOVs exist and are properly rendered (ProRes 4444 with alpha, fade effects). But the FCPXML only placed 18 of them. The director assigned 50 overlays but:
- The FCPXML builder searches for overlay files by fuzzy-matching the first 15 chars of the overlay text — many don't match
- The lane clip offset math puts overlays on the trailing gap — DaVinci may render some off-screen
- **FIX NEEDED:** The builder's overlay matching logic needs to be exact (map overlay text → overlay filename directly) instead of fuzzy 15-char prefix matching

### 3. "Cards are just black screen with text, no style"
**Root cause:** Chapter cards ARE styled (ProRes 4444, serif font, subtle underline) but the styling is minimal — just white text on black. The card renderer (`create_chapter_card()` in davinci_helpers.py) doesn't have:
- Motion graphics / animation
- Brand colors or channel identity
- Transition effects between cards and content
- **FIX NEEDED:** Design a card template system — either render more elaborate cards via FFmpeg/Pillow, or create After Effects / Motion templates

### 4. "SFX sounds awful"
**Root cause:** SFX files are stock sounds (impact_new.wav, glass_shatter_new.wav) placed mechanically at segment boundaries. Issues:
- SFX may not be normalized (the `normalize_sfx` stage is a no-op)
- SFX placement is at exact segment start — no timing finesse (should be on beats, after pauses)
- Only 2-3 different SFX sounds used repeatedly
- **FIX NEEDED:**
  1. Run `normalize_sfx()` function (it exists but pipeline doesn't call it)
  2. SFX timing should use Whisper word-level alignment to hit on specific words
  3. Source more varied SFX (current: 6 unique sounds for 30 placements)

### 5. "Director assigned pauses but they're not there"
**Root cause:** Actually pauses ARE in the narration.wav — voice_generator.py correctly parses [PAUSE:X] and [BEAT] markers and inserts silence. The perceived issue is likely that V1 clips don't hold/pause during VO pauses — the visual keeps cutting while the narration pauses.
- **FIX NEEDED:** The FCPXML builder should insert gap elements or extend clip durations during `vo_pause_before` / `vo_pause_after` periods from the director JSON

---

## STAGE-BY-STAGE STATUS

### Phase 1: Discovery (stages 1-4) ✅ WORKING
- Topic scorer, comment mining, research, validation — all functional

### Phase 2: Script (stages 5-7) ✅ WORKING
- Script writing, enhancement, QA — all functional, 95+ score

### Phase 3: Audio (stages 8-10)
| Stage | Status | Issue |
|-------|--------|-------|
| voice | ✅ Works | Pauses + voice registers baked in. May need WPM normalization |
| align (NEW) | ✅ Works | Whisper word-level alignment. SSL/tiktoken patched |
| qa_voice | ✅ Works | Passes with warnings (peak near 0dBFS, low vocal variation) |
| music | ⚠️ Stub args | music_sourcer needs --script/--mood args wired in pipeline |

### Phase 4: Visuals (stages 11-15)
| Stage | Status | Issue |
|-------|--------|-------|
| footage | ⚠️ Only 3 clips | MIN_VIABLE_CLIPS raised to 15 but sourcer args broken |
| images | ✅ Works | 276 images sourced |
| transcripts | ✅ Works | 12 clips transcribed |
| vision | ✅ Works | Vision analysis on clips + images |
| verify_footage | ✅ Works | Gate logic functional |

### Phase 5: Editorial (stages 16-19)
| Stage | Status | Issue |
|-------|--------|-------|
| storyboard | ✅ Works | Generates scene structure |
| director | ✅ Works (upgraded) | Vision in prompt, music_state, alignment timestamps, sufficiency check |
| validate_segments | ✅ Works (upgraded) | Auto-fix + re-validate loop |
| fill_gaps | ✅ Works | Downloads replacement images |

### Phase 6: Assembly (stages 20-24)
| Stage | Status | Issue |
|-------|--------|-------|
| pause_insert | ✅ Intentional no-op | Pauses in narration.wav already |
| duck_music | ❌ STUB | Function exists but pipeline never calls it. Music is pre-ducked manually |
| normalize_sfx | ❌ STUB | Function exists but pipeline prints "will normalize during build" |
| exec_producer_pre | ❌ BROKEN | Checks stale DaVinci timeline. Should check director JSON only |
| davinci_build | ✅ Works (fixed) | FCPXML builder with API import (timelineName fix) |

### Phase 7: Verification (stages 25-27)
| Stage | Status | Issue |
|-------|--------|-------|
| director_review | ⚠️ Timing mismatch | Fixed hardcoded timing, but still finds mismatches from fuzzy file matching |
| qa_video | ❌ NOT RUN | Never ran in any pipeline execution |
| exec_producer | ⚠️ Partial | Unicode fixed, but checks stale data and has false positives |

### Phase 8: Publish (stages 28-29)
| Stage | Status | Issue |
|-------|--------|-------|
| render | ✅ Works | DaVinci API render, 458MB output |
| upload | ❌ NOT BUILT | No YouTube upload automation |

---

## DISCONNECTED PIECES (data flows that don't connect)

### 1. Director → FCPXML Builder (file matching)
- Director outputs `visual_file: "pexels_5668473_Facebook_Meta_FTC_5_billion_fi.jpg"`
- Builder searches directories with `find_media_file()` using fuzzy matching
- Builder may find a DIFFERENT file that partially matches the name
- **This causes ~50% of director_review "mismatches"**
- **FIX:** Builder should resolve files using the exact same search logic the director used, or the director should output absolute paths

### 2. Director → FCPXML Builder (music_state)
- Director outputs `music_state: "ducking" | "full" | "silent" | "transition"` per segment
- FCPXML builder ignores this field entirely — places one music WAV at position 0
- **FIX:** Builder needs to read music_state and either:
  - Place multiple music clips with volume automation, OR
  - Pre-build a composite music WAV with volume envelope matching director's states

### 3. Director → FCPXML Builder (vo_pause)
- Director outputs `vo_pause_before: 1.5` and `vo_pause_after: 0.5` per segment
- Pauses ARE in the narration WAV (from voice generator)
- But V1 clips don't account for pause duration — they cut at narration text boundaries, not including silence gaps
- **FIX:** The FCPXML builder should add pause duration to each clip's `_timeline_start_sec` offset

### 4. Director → FCPXML Builder (clip_audio)
- Director outputs `clip_audio: "play" | "play_then_mute" | "mute"`
- Builder only implements `"mute"` (adds adjust-volume 0dB)
- `"play"` and `"play_then_mute"` are ignored — clips get default audio behavior
- **FIX:** Implement all three modes in the FCPXML builder

### 5. Director → Overlay matching
- Director outputs `text_overlay: "$5 BILLION"`
- Builder searches overlay directory for files matching first 15 chars: `_5_billion`
- Overlay files are named `tw_000_5_billion.mov` — the prefix `tw_000_` breaks the match
- **Only 18 of 50 overlays found** because of this naming mismatch
- **FIX:** Build an explicit mapping from overlay text → overlay filename (either in the director JSON or a lookup table)

---

## WHAT NEEDS TO BE BUILT FOR A COHESIVE VIDEO

### Priority 1: Fix the 5 disconnected data flows above
These are the root causes of every quality issue. Each is a 20-50 line code change.

### Priority 2: More footage
3 video clips for a 17-min documentary is not enough. Need:
- footage_sourcer args fixed in pipeline
- 15-20 video clips minimum
- Director re-run after new footage is sourced

### Priority 3: Music coverage
3 min of music for 17 min video. Need:
- Source 3-5 CC0 tracks from Pixabay (different moods)
- Director assigns music_state per segment (already does)
- duck_music stage actually builds composite WAV from director decisions
- FCPXML builder places music segments per music_state

### Priority 4: SFX quality
- Run normalize_sfx() — function exists, just wire it
- Source 10+ varied SFX (currently only 6 unique sounds)
- SFX timing: use Whisper alignment to hit specific words, not segment boundaries

### Priority 5: Card styling
- Design template for chapter cards (beyond white-on-black)
- Motion graphics or at minimum: brand colors, animation, visual identity

### Priority 6: exec_producer_pre
- Should NOT check DaVinci timeline (runs before build)
- Should check director JSON only: asset coverage, timing, music_state, etc.

---

## ESTIMATED EFFORT

| Fix | Lines of code | Time |
|-----|--------------|------|
| Overlay text → filename mapping | ~30 | 15 min |
| Builder: implement clip_audio play/play_then_mute | ~20 | 10 min |
| Builder: music_state → multi-segment music placement | ~80 | 45 min |
| Builder: vo_pause offsets in V1 clip timing | ~30 | 20 min |
| Builder: exact file matching (not fuzzy) | ~40 | 20 min |
| Wire duck_music to actually call create_ducked_music() | ~10 | 5 min |
| Wire normalize_sfx to actually normalize | ~10 | 5 min |
| Fix exec_producer_pre to check director JSON not DaVinci | ~50 | 30 min |
| Source more footage (fix sourcer args + run) | ~20 + runtime | 30 min |
| Source more music tracks | ~20 + runtime | 30 min |
| **Total** | **~310 lines** | **~3.5 hours** |

---

## FILES TO MODIFY (next session)

1. `pipeline_v2/fcpxml_builder.py` — overlay matching, clip_audio, music_state, vo_pause timing
2. `run_pipeline_v2.py` — wire duck_music, normalize_sfx, fix footage/music args
3. `pipeline_v2/executive_producer.py` — exec_producer_pre should check director JSON
4. `pipeline_v2/director_review.py` — file matching should use same logic as builder

## FILES TO CREATE (next session)

1. `pipeline_v2/music_composer.py` — composite music WAV from director's music_state decisions
2. Overlay lookup table (or generate from overlay dir listing)
