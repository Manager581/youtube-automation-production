# FORMAT LAWS & GATES — v1.1 (2026-09-08, after the adversarial review)
Owner ask: "a real plan to fix these permanently for this video & any future video, and you to build in the checks so this never
gets to me without you verifying each step." v1 was reviewed by 14 adversarial agents (94 findings, 30 verified so far, 4 refuted).
v1.1 = what survived, BUILT and SELF-TESTED tonight, plus the honest list of what is still prose.

## What changed between v1 and v1.1 (the review's verdict on v1, in one line each)
- v1's watch gate graded the SPEC (9 of 11 checks read JSON); v1.1 grades the RENDER: pixels (pHash replay, static runs, density
  per 10 s, sharpness, text height via render-minus-plate) and the rendered STEMS the mixer now exports (VAD speech, dead air that
  must be carried by the non-VO bus, foley level per slot, holes, hits on the sfx bus, raw music arc).
- v1's thresholds were invented (speech ≤0.75, dead air ≤3 s, density "ref/0.8"); the reference itself failed them. v1.1 has ONE
  profile measured on the reference WITH THE SAME CODE, and the reference must PASS its own gate (it does: 8/8).
- v1's deliver.py was an honour-system door (path substrings, no sha, a template WATCH_NOTES would pass, "UNHEARD" allowed);
  v1.1 recomputes every sha, machine-checks the notes against the gate's numbers, requires a LISTEN record, and a PreToolUse
  hook blocks any video that is not a deliver.py output.
- v1's vo_qc floor came from the MIXED reference (music + 3 speakers pooled → 11 st); MrBeast's own lines failed it. v1.1
  calibrates on the demucs vocal stem, per cue: floor = p25 of the reference's own lines (3.09 st / 3.52 dB). Result on our
  17 lines: 3 FAIL (L03, L06, L07) instead of 8. The gate now judges "Helmets off." too (voiced-duration rule, no word-count exemption).
- v1 said "2 takes on hook lines" — contradicts the ONE-pass rule; deleted. Re-takes need a reason at the spend gate.
- v1's density floor divided by 0.8 (stricter than the reference); v1.1 = 0.8 × the reference's per-10 s buckets, measured on the render.
- v1 had no credit totals and no owner-go mechanism; v1.1 has `run_gates spend` (batch hash + owner_go record).
- v1's Law 8 named only a 2 h llama.cpp build; v1.1 tries the subscription route (Gemini app, video+audio) first.
- v1 treated a flash-forward cold open as settled; v1.1 tests the reference-shaped LIVE alternative on the stand-in first ($0).
- v1 had no law for the HOST performing, for REACTIONS, for camera language, for the anchor-wide return; v1.1 adds them.

## Evidence that the machinery bites (all run tonight, files on disk)
| Test | Result |
|---|---|
| Reference through its own render-level gate (`watch_gate --ref-selftest`) | PASS 8/8 (replay 0, static 2 s, density [24,6,11,16,5], cut-on-word 0.48, speech 0.844) |
| v3 through the full gate (`first_minute_v3_watch.json`) | FAIL 12/19: replay 4.0 s, static 15 s, density [10,9,6,4,1] vs floor [19,5,9,13,4], 8 replayed windows, 2 lines off speaker, speaker-change cuts 0.38, foley 0.17, text unmeasurable (no plate), music hole 21.8 s, hits 0/4, music range 3.1 dB |
| `deliver.py --selftest first_minute_v3.mp4` | REFUSED with 6 reasons, no crash |
| `send_guard.py` on `SendUserFile output/.../first_minute_v3.mp4` and on `open output/....mp4` | blocked (exit 2); a .jpg passes |
| `run_gates all --render v3` | list-form `gates_first_minute_v3.json`, render sha inside, verdict FAIL (story, hook, voqc, wordedit, watch) |
| `spend_gate` on the stale reshoot batch | "NO GO for batch 7b6e415a: 5 Grok clips (30 s) + 556 chars" — refused, correctly |
| `story_gate` on SCRIPT_v3 with chars/s unset | REFUSED ("chars/s is not measured yet"); with the measured 15.8: FAIL B01 (12.1 s speech in a 9 s beat; DAY 1 < 26) |
| `clip_bank.subject_motion` on the 9 banked hook clips | only S002 has ≥2 subject events (1.5 s, 4.25 s); S006/S007/S013/S019/S020/S001 = 0 — "nobody moves", in numbers |
| `audio_mix` self-test | mix + stems vo/foley/music/nonvo/music_raw in one ffmpeg run, sha report written |
| `render_edit_spec` text2 + `--no-overlays` plate | 3 s sample rendered both ways; report carries spec sha, out sha, absolute op times |

## The spine (machine-enforced)
1. `scripts/deliver.py --render R --lane lane.json` is the ONLY door. It recomputes sha256 of the render, spec, mix, manifest, plate,
   stems, strips and profile against `<R>_watch.json`; refuses on any mismatch.
2. `WATCH_NOTES_<R>.md` is machine-checked: written AFTER the strips (mtime), one section per strip citing the strip's sha8 with
   ≥3 timed observations, and an ANSWERS block (`replays:`, `longest_still_s:`, `first_3s:`) that must AGREE with the gate's
   numbers and name the promise proof shot. Disagreement between my notes and the machine = refuse.
3. `gates_<R>.json` from `run_gates.py all lane.json --render R`: list form, render sha, input shas, `hook_window` flag copied from
   lane.json, waivers surfaced; any waiver on a hook-window gate = refuse; NOT-READY at delivery = refuse.
4. `<R>_listen.json` {render_sha, verdict, by: model|owner} is REQUIRED. UNHEARD is not a delivery state.
5. Every clip/line in the render carries `setting_hash` with a PASS `prototype_<hash>_<name>.json`; every batch item has
   `owner_go_<batch>.json`. (`scripts/prototype_record.py hash|record|stamp`, `scripts/spend_gate.py`.)
6. `.claude/hooks/send_guard.py` (PreToolUse on SendUserFile and Bash) blocks any video outside `deliveries/<lane>/` and any
   `open`/copy of a render out of `output/`.

## Law 0 — PROTOTYPE, THEN BATCH; A CONTRADICTION STOPS THE BUILD (built)
Fix: `prototype_record.py hash` gives every generator setting a hash; ONE sample goes through its gate; `record --verdict FAIL`
writes BLOCKED into `pipeline_state.json` so the next session cannot continue the batch. Check: deliver.py item 5.
Credits: `run_gates spend` prints the batch (clips × seconds + chars + hash); generation only after `owner_go_<hash>.json`.

## Law 1 — THE PROMISE IS ON SCREEN BY 3 s (partly built)
Built: `lane.promise` {claim, proof_shots [S000], by_s 3}; S000 seed PASS (12 m rock, DAY 26, on the ladder); deliver.py forces
`first_3s:` in the notes to name S000. Not built: the `shots` gate check "proof shot t_in ≤ 3 s" for THIS lane (cmd_shots still
runs the ep02 manifest) and a story_gate `[FLASHFWD]` rule (a cold open may precede DAY 1 without tripping the ladder check —
today SCRIPT_v3 FAILs "DAY 1 < 26"). Decision pending on the stand-in: flash-forward (DAY 26 → DAY 1 in 3 s) vs the
reference-shaped LIVE open (the impossible thing visible now: THE COUNT reading 1000 M with the planet small behind them and
ORB's claim spoken ≤3 s). Both get a $0 stand-in strip; the strip decides.

## Law 2 — SOMEBODY PERFORMS (rebuilt)
(a) Voice: `vo_qc.py --calibrate --stem --cues words.json` (vocal stem, per-cue floors); lines judged by voiced duration; pace band
0.75–1.35× ref; `--measure-cps` writes the MEASURED chars/s into `lane.speech` (15.8 today from undirected lines; re-measured on the
directed prototype before the batch). ONE pass; re-take = spend gate `--allow-retake "reason"`.
(b) Mouth:ON lines = Grok TALKING clips with the line IN the prompt (Dinoverse S02b proves the engine speaks when asked); the
ElevenLabs line replaces the audio with its onset matched to the clip's own audio (whisper on the Grok track). HONESTY: the
current `lipsync_check.py` is chance-level (true sync 0.269 vs a 1 s shift 0.286 on ground truth). It stays a prototype, NOT a
gate, until the discrimination test passes on the S010 talking clip (true line must beat the shifted line and the wrong line).
If it cannot, the law is rewritten: hook mouth:ON shots are minimised (S010 only in 0:00–1:00) and judged on the strip.
(c) THE HOST PERFORMS (new): ORB has no mouth; its performance is halo + movement. Every hook shot with ORB carries `host_action`
(dart-in, snap-tilt, orbit, halo flare on the emphasis word, drop-and-stop); ORB on-camera lines require ORB in frame
(`line_off_speaker` no longer exempts ORB). Not built: the halo-luminance-vs-VO-envelope check (the chrome colour mask is
noisy: cover 3–7%, false events); prototype it on S001 before it gates anything.
(d) REACTIONS (new, built in story_gate): every [STAKES]/[REVEAL]/[LOCK] tag needs ≥2 `[REACT <char>]` tags (one per contestant),
silent matched pairs allowed. Seeds: one "expression run" CU per contestant per set (a 6 s clip yields several 1–2 s inserts).

## Law 3 — TWO ANGLES OF EVERY HOOK MOMENT, AND THE ANCHOR WIDE RETURNS (rebuilt)
`moment_id` on all 22 hook shots. Derived from HEAD: M01/M04/M05/M07/M09 already have 2 PASS angles; M00, M03, M06, M08, M10 need
one B-angle each (5 seeds, session-generated, no owner sitting) + 5 clips. Replay is keyed on (source, window) OVERLAP, not filename:
a 10 s anchor wide cut into non-overlapping windows is a designed return (the reference's most common move); the same seconds
twice is a replay (render-level pHash catches it regardless of filename; threshold 0). Not built: the per-moment count in
`clip_bank status` and an angle-distinctness measure (pHash distance between the two seeds' first frames).

## Law 4 — WORD-DRIVEN, AS DENSE AS THE REFERENCE, WITH ITS CAMERA LANGUAGE (partly built)
Built: `build_edit_from_alignment.py` (forced alignment, text anchored to words, punches on **emphasis**; floor 15.8 = 0.8 × the
89 spec-equivalent ops/45 s); watch gate `density_per_10s` measured on the render vs the reference buckets; `cut_on_word_rate`
against whisper word onsets on the VO stem (ref 0.48, floor 0.38); `speaker_change_cut_rate` (a new speaker gets a cut to their
CU/MCU/OTS within 0.15 s; ref 7/7, floor 0.8). Designed silences: `[SILENT Ns]` counted in the budget; dead air > 5.25 s must be
carried by the non-VO bus (≥90% above median −20 dB). Not built: action-on-word (choose the clip's in-point so the subject-motion
peak lands on the word ±0.15 s — the bank now records peak times, the builder does not use them yet); the camera vocabulary as
ops (eased snap-in with directional blur, snap-out ≤2 frames, flash-hidden cut, whip-tilt with blur frames, glow-key, foreground
wipe) — `edit_layer` has linear punch/whiteout/flash/bloom only; per-kind count bands.

## Law 5 — TEXT IS A DESIGNED ELEMENT (built, profile still thin)
Built: `text2` ops (PIL PNG, Impact, stroke 10, shadow, {keyword} yellow, overshoot pop, shake) rendered by the assembler; the
watch gate measures the RENDERED text block (render minus plate): height ≥ 15% of frame (162 px; v3 shipped 72 px) and animation
(≥5% size change in the first 0.3 s); zero text pops in the hook = FAIL (no vacuous pass). Not built: the reference's text
profile as bands (4–7 pops/45 s, 0.6–2.2 s on screen, a colour-change event per pop, name cards in character colours, transform
coupled to the punch curve, a second font register for gags).

## Law 6 — THE PICTURE IS FINISHED AND CONSISTENT (rebuilt)
Look consistency uses MAD (k = 3.5) within a SET, excludes `look_event` segments (flash, bloom, grade snap — the reference has 14
colour shifts in 45 s, they are the style, not defects), ceiling 1 per 10 segments; sharpness (Laplacian variance) ≥ 0.5 × ref
(v3 = 1639 vs ref 806 — sharp enough; the "unfinished" feel is the frozen frames and missing grade, not softness).
Not built: a lane grade LUT applied by the renderer and recorded in the report; source resolution per ledger row.

## Law 7 — THE SOUND IS LAYERED AND ARCED (rebuilt on stems)
`audio_mix.py` exports stems (vo, foley, sfx, ambience, music, music_raw, nonvo) and a sha report in one ffmpeg run; `retime_to_vo.py`
now refuses to drop a bus (v3 lost its whole design bus that way). Gate: foley present ≥90% of each slot and within 12 dB of
VO on the rendered stem (v3: 0.17); music hole = non-VO bus < median −20 dB for ≥0.5 s (v3: 21.8 s); text hits = onset on the
sfx stem within 0.2 s of each MEASURED text appearance (v3: 0/4 — no sfx bus at all); music arc = ≥3 levels and ≥6 dB range on
the RAW (pre-duck) music stem (v3: 3.1 dB; the reference's non-VO range is 19.2 dB). Tension correlation is reported, not
gated (the reference is flat, LRA 2.8; the law is "the cue moves and hits land", not RMS-vs-tension). Not built: the ambience
generator (MMAudio bed per set with a loop-seam check), the Pixabay cue swap (owner download gate).

## Law 8 — SOMETHING LISTENS BEFORE THE OWNER DOES (route changed)
A listen record is REQUIRED for delivery. Route 1 (try first, $0, ~30 min): the Gemini app under the existing subscription —
upload the render, ask the 6-line form (VO flat? pace? music fit? foley plausible? balance? one timestamp that bothers you) on
v3 AND on the reference, compare to the owner's known verdict on v3; if it separates them, it writes `<R>_listen.json` {by: model}.
Route 2: Qwen2.5-Omni via llama.cpp (10-min prototype on ONE file before any 2 h build). Fallback: the owner's form, recorded by
`listen_record.py` (to write) — the owner is the gate only when no model route works, and it is recorded, never repeated per line.

## Cost ledger (the numbers v1 did not have)
| Item | First minute | Whole video (20 min) |
|---|---|---|
| Grok i2v (6 s gens, paid acct) | prototype C: 3; batch D: 8 (4 reshoots S006/S007/S008/S019 + 4 alts M03/M06/M08/M10); re-rolls capped 1 each → ≤ 22 | ~197 unique shots + ~40 alts, × 1.35–1.65 re-roll → 285–350 gens (~8 h driving + ~5 h banking) |
| ElevenLabs (one pass) | C: 60 chars (L04 directed); D: ~496 chars (9 lines) | ~20.3k chars (+ up to 1 re-take per line with a reason) |
| Seeds (identity thread, session-generated, $0) | 5 B-angles + 2 expression runs | ~160 more |
| Foley (MMAudio, CPU) | 25 windows ≈ 25 min, only on FINAL windows | ~258 windows ≈ 4.5 h per pass |
| Whole first minute | ≤ 22 gens + ~556 chars | — |
Rule: no act N+1 generation until act N passes the watch gate; re-rolls are caught at BANK time (subject events), not at render.

## Order (this video) — every step names its check and who says yes
A. $0 — SCRIPT_v4: B01 −77 chars, `[REACT]` beats after `[STAKES]`, `[FLASHFWD]`/live-open decision on the stand-in, emphasis +
   tension, `[SILENT]` where designed → `story_gate` PASS (measured chars/s) → whisper words on the 6 kept lines →
   `build_edit_from_alignment` (floor 15.8) + text2 + look + music arc + ambience bus → STAND-IN render (dry-run flags) + plate
   + stems → `watch_gate` with the DECLARED expected-FAIL set {longest_static_s, motion_mean, foley_cover} (stand-ins are stills)
   and every other check PASS → strips looked at → WATCH_NOTES in the machine format. Verified by: the gate JSON + notes check.
B. $0 — bank re-verdict with `--characters` (subject events; 6 of 9 hook clips will be refused); ORB halo-mask prototype on S001;
   angle-distinctness on S002 vs S002B seeds; Gemini listen test on v3 + reference. Verified by: ledger rows + prototype records.
C. OWNER GO (batch hash printed by `run_gates spend --grok grok_i2v_pack_prototype_C.json --vo vo_lines_prototype_C/...`):
   S000 cold open (6 s), S002B alt (6 s), S010 TALKING clip with the line in the prompt (6 s), L04 directed (60 chars) → each
   through its gate (watch promise/static, bank subject events + distinctness, lipsync discrimination, vo_qc stem + chars/s)
   → `prototype_record`; any FAIL = BLOCKED, owner sees the number. Verified by: 4 prototype records.
D. OWNER GO (second batch hash): 4 reshoots + 4 alts + 9 lines → bank → freeze edit → foley on FINAL windows → render + plate +
   stems → `run_gates all --render` → watch PASS → notes → listen record → `deliver.py` → owner (via the guarded path only).

## Still prose (not built tonight — listed so nobody mistakes them for checks)
story_gate `[FLASHFWD]` + per-lane proof-shot t_in check · action-on-word in-point selection · camera-language ops + per-kind
bands · text profile bands · archive STACK overlay (≥3 photos on screen at peak, alternating sides) · ORB halo check ·
per-moment angle count + distinctness · grade LUT + resolution per row · ambience generator + seam check · `listen_record.py`
· lipsync discrimination test · retroactive `setting_hash` stamping of the 13 kept clips (write their prototype records from the
pack prompts + strip verdicts, marked retroactive) · a foley-vs-motion onset check reused from `verify_foley_v4.py`.
