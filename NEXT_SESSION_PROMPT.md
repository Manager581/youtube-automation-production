# Next Session Prompt

Copy everything below the line into the next Claude Code session.

---

## Pipeline V2 Redesign — "Why Breaking the Law Is Profitable"

Read these files first (in order):
- PIPELINE_REDESIGN.md (what broke, what worked, architecture problems)
- CLAUDE.md (project rules, tool policy, current video state)
- DIAGNOSIS_2026-04-04.md (6 root causes of visual-narration desync)
- MEMORY.md

### Current State
- "FINAL" timeline is in DaVinci ("Breaking Law v2 copy" project). It's the best version but needs manual fixes: delete chapter card at 46.4s on V3, optionally unmute a few key video clips.
- Script v45 DONE (95+ score). Voice DONE (narration.wav, 23.4 min, 175 WPM, clean). All assets ready (23 clips, 447 images, 75 overlays, 18 SFX, 4 music tracks). Do NOT re-source or regenerate.
- Real clip transcripts are at `media/breaking_law/transcripts.json` (23 clips with actual audio content). The file at `footage/breaking_law/transcripts.json` has EMPTY transcripts — never use it.

### TWO GOALS

**Goal 1: Finish THIS video (ship it)**

The "FINAL" timeline needs these specific fixes:
1. No chapter card in the intro (delete from V3 at 46.4s)
2. Intro format: 3 video clips back to back with THEIR OWN AUDIO (5 seconds each, news anchors speaking), then VO starts. The VO narration.wav needs 15s of silence at the start for this.
3. 6-8 clip audio moments throughout the video where source material tells the story (not 31, not 2 — pick the best moments where news footage/interviews support the narration)
4. Create chapter_the_machines.mov (missing chapter card file)
5. Verify EVERY fix plays correctly in DaVinci before claiming it works

**Goal 2: Redesign the pipeline (make it replicable)**

The current pipeline has these architecture problems that caused a full day of going in circles:

1. **No integration tests.** Changes were verified with JSON checks and grep, never by watching the video in DaVinci. Build a 60-second test FCPXML that exercises every feature (muted clip, play_then_mute with keyframes, transition, Ken Burns, narration lane, SFX, overlay). Import and verify in DaVinci BEFORE building the real video.

2. **Voice and director don't talk.** Narration is wall-to-wall with no gaps. Director picks clip audio moments. Neither knows what the other decided. Need: clip_audio_planner sits between them, caps at 8 moments MAX (enforced in code, not prompt), inserts silence gaps.

3. **Intro is special-cased everywhere.** Locked intro spec, apply_locked_intro.py, beat flattening, chapter card filtering — all have conflicting intro logic. Need: intro_builder.py as a first-class pipeline stage. Reads director's intro picks (3 video clips with audio), places them, calculates where VO starts.

4. **Beat expansion happens in TWO places.** chapter_assembler expands beats into segments, then fcpxml_builder tries to expand again. This mangled the intro (video clips became images). Fix: builder reads beats directly from director output. Remove beat expansion from assembler.

5. **Director was blind to clip content.** Real transcripts exist at `media/breaking_law/transcripts.json` but were never wired to the director. The director was picking clips by filename only. Fix: always pass `--transcripts media/breaking_law/transcripts.json` (not the empty footage/ version).

6. **No hard caps in code.** Director prompt says "max 2 SFX per chapter" and "max 2 uses per visual" — Claude ignores both. Code post-processing caps exist now (in validate_decisions) but clip_audio had no cap, which is how we got 31 gaps. Fix: every limit must be enforced in Python, not just asked for in the prompt.

7. **Cross-batch state was missing.** Each batch of 8 segments went to Claude with no knowledge of what previous batches picked. Now fixed (used_visuals Counter in direct_segments), but needs testing.

### Files That Were Modified (check git diff for details)
- pipeline_v2/fcpxml_builder_v2.py — mute fix (-96dB), transitions, Ken Burns keyframes, SFX cap, music state normalization, marker filtering, chapter card validation
- pipeline_v2/director.py — cross-batch state, batch context, clip_audio prompt, chapter card rules, intro format, SFX cap enforcement
- pipeline_v2/chapter_assembler.py — beat flattening (BUGGY — may need revert), DIRECTOR_PATH, ALIGNMENT_PATH, NARRATION_PATH updated
- pipeline_v2/clip_audio_planner.py — NEW, works but needs hard cap
- pipeline_v2/verify_director.py — NEW, works
- pipeline_v2/verify_fcpxml.py — NEW, works
- scripts/fix_director_v5.py — post-processing fixes (currently points to v6)

### Approach for Redesign
1. Build the 60-second test FCPXML first. Verify every feature in DaVinci.
2. Fix one thing at a time. Verify in DaVinci after each fix.
3. Never claim something is fixed without watching it play.
4. The pipeline should produce a watchable video from `run_pipeline_v2.py --topic "Your Topic"` with no manual intervention except final DaVinci polish.
