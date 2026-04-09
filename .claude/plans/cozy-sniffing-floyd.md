# Fix: Audio/Video Sync in FCPXML Builder

## Problem Summary

The pipeline has three mismatched timelines:
- `narration.wav` (1404.7s) -- original voiceover
- `narration_gapped.wav` (1519.7s) -- VO with 115s of silence gaps inserted at 31 points
- Paper edit beats -- timecodes derived from Whisper alignment of `narration.wav` (ungapped)

`fcpxml_builder_v2.py` places `narration_gapped.wav` on the audio track but positions
all visuals using paper edit `start_sec`/`end_sec` values, which are aligned to the
ungapped narration. Result: every silence gap shifts all subsequent visuals out of sync.

## Recommendation: Option B -- Remap paper edit timecodes using gap_plan.json

### Why Option B

**Option A (use narration.wav for everything)** is the simplest change (one line) but
sacrifices the clip audio feature entirely. The user specifically built the clip_audio_planner
stage to create silence gaps where source video audio plays. Throwing that away eliminates
a core editorial feature.

**Option C (re-align gapped narration)** requires re-running the paper edit through Claude,
which costs real money and time. The gapped alignment already exists
(`narration_gapped_alignment.json`), but the paper edit was generated against the ungapped
alignment. Re-generating it is expensive and unnecessary.

**Option B (remap timecodes)** is the right balance:
- `gap_plan.json` already exists with the exact mapping (original_position_sec -> gapped_position_sec)
- The remapping is a pure arithmetic operation: for each beat, shift start_sec/end_sec forward by the cumulative gap duration up to that point
- It slots into the pipeline between `paper_edit` and `davinci_build` without changing either stage's internals
- It is fully testable with a standalone script -- no DaVinci needed

### Exactly What Changes

#### File 1: NEW -- `pipeline_v2/remap_paper_edit.py`

A standalone module that:
1. Loads `gap_plan.json` (the 31 gaps with original_position_sec, gapped_position_sec, duration_sec)
2. Loads the approved paper edit JSON
3. For each beat, remaps `start_sec` and `end_sec` from ungapped to gapped timeline:
   - Build a sorted list of gaps from gap_plan.json
   - For a given original time T, find all gaps whose `original_position_sec < T`
   - Sum their durations to get the cumulative offset
   - New time = T + cumulative_offset
4. Writes a new file: `*_remapped.json` (or overwrites with `--in-place`)

The remapping algorithm:

```
def remap_time(original_sec, gaps):
    """Shift a time from ungapped to gapped timeline.
    
    gaps: sorted list of {original_position_sec, duration_sec}
    """
    offset = 0.0
    for gap in gaps:
        if gap["original_position_sec"] <= original_sec:
            offset += gap["duration_sec"]
        else:
            break
    return original_sec + offset
```

CLI interface:
```
python -m pipeline_v2.remap_paper_edit \
    --paper-edit storyboards/breaking_law_paper_edit_approved.json \
    --gap-plan audio/breaking_law/gap_plan.json \
    --output storyboards/breaking_law_paper_edit_remapped.json
```

Validation built into the script:
- Assert last remapped beat end_sec is close to gapped_duration_sec from gap_plan.json
- Assert beat ordering is preserved (no inversions)
- Assert total duration delta equals total_silence_added_sec from gap_plan.json
- Print a summary table: original range, remapped range, delta

#### File 2: MODIFY -- `pipeline_v2/fcpxml_builder_v2.py`

Two changes only:

1. **Line 52**: Change `NARRATION_PATH` default to remain `narration_gapped.wav` (NO CHANGE needed -- this is already correct for the gapped workflow)

2. **In `main()` around line 1020**: After loading the paper edit, if a gap_plan.json exists, auto-remap the beats. This is a safety net so the builder works even if the user forgets to run the remap step manually:

```python
if args.paper_edit:
    all_segments, chapter_map, sfx_by_chapter, music_by_chapter = load_paper_edit(args.paper_edit)
    
    # AUTO-REMAP: if gap_plan exists, shift timecodes to match gapped narration
    gap_plan_path = PROJECT_ROOT / "audio" / "breaking_law" / "gap_plan.json"
    if gap_plan_path.exists():
        from pipeline_v2.remap_paper_edit import remap_segments_in_place
        remap_segments_in_place(all_segments, gap_plan_path)
        # Rebuild chapter_map since timecodes changed
        chapter_map = rebuild_chapter_map(all_segments)
        music_by_chapter = rebuild_music_map(chapter_map)
```

This is ~10 lines of glue code. The actual remapping logic lives in the new module.

#### File 3: MODIFY -- `run_pipeline_v2.py`

Add the remap step to the pipeline stage list and args_map:

In the STAGES list (between `clip_audio_plan` and `ambient_plan`):
```python
("remap_paper_edit", "Remap paper edit timecodes for gapped narration", "pipeline_v2/remap_paper_edit.py"),
```

In `build_stage_args`:
```python
"remap_paper_edit": [
    "--paper-edit", config.get("paper_edit_approved_path", ...),
    "--gap-plan", "audio/breaking_law/gap_plan.json",
    "--output", config.get("paper_edit_remapped_path", ...),
],
```

Update `davinci_build` args to use the remapped paper edit path instead of the approved one.

#### File 4: MODIFY -- `pipeline_v2/verify_fcpxml.py`

Add one new check: "Narration-visual sync check"
- Parse the narration lane duration from A1
- Parse last V1 clip end time
- Assert they are within 30s of each other (allowing for outro)
- This catches the exact bug: if visuals end at ~1450s but narration runs to ~1520s, the check fails

### What Does NOT Change

- `paper_edit_generator.py` -- still generates from ungapped alignment (correct; the remap step adjusts afterward)
- `clip_audio_planner.py` -- still produces gap_plan.json and narration_gapped.wav (correct)
- `narration_aligner.py` -- still aligns narration.wav (correct)
- `chapter_assembler.py` -- legacy path, already uses gapped alignment separately
- All quality gate stages -- unaffected

### Testing Without DaVinci

1. **Unit test the remap function**: Feed known gap_plan.json + sample beats, assert output times match expected values. The gap_plan.json already in the repo has 31 gaps totaling 115s -- the test can verify that a beat at original time 1400s gets remapped to ~1515s.

2. **Integration test**: Run remap on the actual paper edit, then run verify_fcpxml on the resulting FCPXML. The new sync check catches misalignment.

3. **Spot-check**: Print a table of "beat text | original_sec | remapped_sec | delta" for the first and last 5 beats. Verify manually that gaps appear at the right moments.

### Implementation Order

1. Write `remap_paper_edit.py` with the remap function + CLI + self-test
2. Test it standalone against the existing gap_plan.json and paper edit
3. Add the auto-remap hook in `fcpxml_builder_v2.py` main()
4. Add the sync check in `verify_fcpxml.py`
5. Add the pipeline stage in `run_pipeline_v2.py`
6. Run the full build and verify

### Risk Assessment

- **Low risk**: The remap is pure arithmetic on JSON data. It does not touch audio files, does not re-run expensive stages, and produces a new output file (not in-place by default).
- **Rollback**: If the remap breaks something, delete the remapped file and change NARRATION_PATH to `narration.wav` (Option A fallback). The pipeline still works, just without clip audio gaps.
- **Edge case**: Beats that straddle a gap insertion point. The remap handles this correctly because it shifts both start_sec and end_sec by the same cumulative offset. A beat that originally spans a gap point will simply be longer in the gapped timeline, which is correct -- the silence gap expands the time between the narration before and after it.
