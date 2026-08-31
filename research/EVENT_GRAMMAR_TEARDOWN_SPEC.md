# Event-Grammar Teardown Spec v1 (2026-08-31)

The standing method for reverse-engineering a reference video. Replaces averages-first teardowns.
Born from the owner's critique (2026-08-31): "averages without WHY", "scene detection misses zooms/
text/angle changes stacked with SFX". Proven same day on the Primeval Atlas spino hook:
**51 events in 28s where scene-detect saw ~5 cuts** — ledger + spot-check verdict (RELIABLE) at
`research/primeval_atlas_teardown/EVENT_LEDGER_hook_0-28s.json`.

## The three rules

1. **Events, not scenes.** The unit is the on-screen EVENT: hard_cut, zoom_in/out, camera_move,
   text_on/off/animate, subject_change, motion_spike, speed_ramp, angle_change, color_shift.
   Simultaneous events = separate rows sharing a timestamp (a cut + grade jump + angle change at
   5.0s is THREE rows). Scene-detect lists (run at 3 thresholds, never one) are candidates only —
   vision frames decide. Every event is cross-referenced to the audio onset list (SFX sync is a
   recorded pairing with strength + offset, not a vibe).
2. **Phases, not global averages.** Rates are computed per story phase (cold-open / setup /
   escalation / climax / lull...). Global averages are reported ONLY next to the per-phase table
   with an explicit "averages lie" note. Demo numbers: global 109 ev/min, but adjacent phases run
   288 vs 55 ev/min (5.2×), and the cold open is 0 ev/min for 2.9s then ~170 ev/min for 2.1s —
   the purchased stillness IS the mechanism. A replica built to the averages destroys the video.
3. **WHY is a mandatory column.** Every row: exact words being spoken (or [silence]), audio_sync,
   and the editorial function grounded in observable structure ("biggest movement played QUIET at
   -31 LUFS to preserve headroom for the 5.085 sting"; "cut passes silent because it advances
   geography, not story — stings are reserved for shocks"). A row without a why is incomplete.

## Pipeline (what ran, reusable as-is)

1. Extract: 8fps frames → 2s filmstrip tiles (16 frames, t = 2N + 0.125k); scene-detect at
   0.1/0.2/0.3; librosa onsets w/ strengths; ebur128 momentary loudness ~2/s; whisper words.
2. Ledger: vision agents read every tile, log every event to 0.125s precision (split the window
   across agents; do not collapse simultaneous events).
3. Causal: merge ledger + words + loudness → why per event; segment phases; compute per-phase
   rates; write the averages-lie note; cross-check against any prior per-second docs and record
   discrepancies both directions.
4. **Adversarial spot-check (mandatory):** re-extract native-res 10fps frames around ≥8 sampled
   events; confirm each claim; verify ≥2 audio pairings against RMS. Ledger ships only with a
   verdict. (Demo: RELIABLE; checker found a missed cut at 17.25s and a 60ms audio offset — both
   recorded in the ledger file.)

## What the demo caught that prior methods missed

Frame-level pass found: the beach head-toss beat at 14.125 the per-second docs binned away; three
camera moves + a speed ramp the docs' "camera never moves" rule denies; the loud-on-cut /
quiet-on-action audio strategy (two cuts stung at str 6.5-6.8, two passed silent at the audio
floor, climax peak lands just BEFORE the hero cut); the 3.1s zero-event zero-onset dread hole at
17.5-20.6. None of this is visible in cut lists or medians.

## Cost + scaling (honest)

Demo cost: 5 agents, ~16 min, ~490K subagent tokens for 28s of video (in-session subscription
labor, $0 cash). Full event-density on an 8-minute video is unaffordable and unnecessary.
**Scaling rule:** full event-grammar on the HOOK (first 30-45s) + one representative 20-30s window
per story phase; cut-level + loudness + onset analysis for the remainder; spot-check every window.
The style profile's causal-grammar layer (PIPELINE_OVERHAUL_PLAN S1) is built FROM these ledgers —
rules like "biggest action plays quiet; the cut after it takes the sting" become executable
assembly/mix rules, not statistics.
