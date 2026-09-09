# FORMAT LAWS & GATES — v1 (2026-09-08)
Owner ask: "a real plan to fix these permanently for this video & any future video, with checks built in so this never gets to me
without you verifying each step." Scope: the 8 gaps found on Shrinking Planet first_minute_v3. Every law below is (a) a rule
in `CLAUDE.md`, (b) a machine check that FAILS CLOSED in `run_gates.py`, (c) an evidence artifact I must look at, (d) a line in
the delivery checklist that the deliver step refuses without. Lane-generic: every threshold lives in the lane's `style_profile`
(measured from that video's reference), never hard-coded to MrBeast.

## The spine: nothing reaches the owner without a DELIVERY CHECKLIST
`scripts/deliver.py <render>` is the ONLY way a render leaves the machine. It refuses unless, for that exact file (sha):
  1. every stage gate below is PASS in `output/<lane>/gates_<render>.json` (no waivers on hook-window checks);
  2. the watch gate's 4 fps strips exist AND `WATCH_NOTES_<render>.md` records timestamped observations for every strip
     (what moves, what repeats, what the first 3 s show) — the notes are written by me, after looking, before delivery;
  3. the listen line is filled: either a listening-model verdict (item 8) or "UNHEARD" printed in the caption to the owner;
  4. the prototype record exists for every generator setting used (item 2/3): one sample checked before the batch.
The checklist (gates + evidence paths + my notes) is attached to the delivery. Green without evidence is a FAIL.

## Law 1 — THE PROMISE IS ON SCREEN BY 3 s (title claim → cold-open wow)
Gap: v3 opens on two creatures standing on a rock; the planet never shrinks in the first minute.
Fix: `lane.json.promise = {"claim": "<title's impossible thing>", "proof_shots": [ids]}`; the script's B01 carries a
`[WOW ≤3s]` tag; the manifest has a proof shot with t_in ≤ 3 s. For Shrinking Planet: cold open = flash-forward to the 25 m
rock with PIP and GRUFF clinging to it, "DAY 27" chip, smash-cut to "DAY 1 · Helmets off".
Check: `story_gate` (WOW tag in B01 ≤3 s) + `shots` gate (proof shot t_in ≤ 3, planet ≤ 25 m for this lane) + watch gate
strip 0–3 s reviewed with the written question "does frame 1 show the impossible thing?".
Cost: 1–2 seeds (free) + 1–2 clips (credits).

## Law 2 — SOMEBODY PERFORMS (voice direction + on-camera speech)
Gap: flat TTS over creatures that never speak on camera.
Fix: (a) `vo_direction.json` per line: emotion, pace target, stability/style, emphasis words (`**word**` in the script); v3
expressive model or per-line settings; hook lines get 2 takes, chosen by ear (owner) until item 8 exists.
(b) mouth:ON lines are generated as TALKING clips (the engine speaks the line) and the ElevenLabs line replaces the audio;
lip motion must follow the line.
Check: `vo_qc.py`: words verified (whisper), pace within the profile band, pitch-variance and energy-variance ≥ reference
floor (flat read = FAIL) — calibrated on the reference VO. `lipsync_check.py`: mouth-region motion envelope vs speech
envelope cross-correlation ≥ profile floor on every mouth:ON clip. `line_on_speaker` (watch gate) extended: listener
shots must be tagged `reaction_of` and show an expression change (motion in the face region).
Cost: 2 takes on hook lines (credits, small); talking clips replace their silent versions (credits).

## Law 3 — TWO ANGLES OF EVERY HOOK MOMENT (coverage)
Gap: one clip per shot; nothing to cut to inside a moment except a punch-in.
Fix: manifest `moment_id` groups shots; hook-window moments require ≥2 unique PASS-banked angles (A master + B alt/insert)
from 2 seeds of the same moment (same thread, "same moment, other angle"). Outside the hook ≥1.
Check: `bank status --manifest` fails if any hook moment has <2 PASS angles; the assembler's replay refusal stays.
Cost: ~14 seeds (free) + ~14 clips (credits) for this hook.

## Law 4 — THE EDIT IS WORD-DRIVEN AND AS DENSE AS THE REFERENCE
Gap: ~40 ops vs ~120; cuts/text on line starts, not words.
Fix: whisperx word times on every line (existing tool); `lib/assembly/build_edit_from_alignment.py` derives: text pops
leading their word by 0.2–0.5 s, punch-ins on `**emphasis**` words, cuts snapped to word onsets, one text pop per claim.
Check: watch gate `ops_per_10s` in the hook ≥ profile floor (reference ledger / 0.8); `cut_on_onset_rate` (exists);
`text_lead_s` in [0.15, 0.6] for every pop; `claims_with_text` = all (script marks claims with `[TEXT]`, already).
Cost: zero credit.

## Law 5 — TEXT IS A DESIGNED ELEMENT
Gap: plain white sans, static.
Fix: `edit_layer.text_pop` v2: PIL-rendered PNG with stroke + shadow + keyword colour, animated scale-in with overshoot,
optional shake; font/colour/stroke in `style_profile.text`.
Check: watch gate `text_style`: size ≥ floor, stroke present, animated (frame-diff in the text box during pop) — plus the
strip look. Cost: zero credit.

## Law 6 — THE PICTURE IS FINISHED AND CONSISTENT
Gap: 720p upscales, mixed looks, no grade.
Fix: `style_profile.look`: grade (contrast/saturation/curves), sharpen, grain applied in the renderer; consistent upscale.
Check: watch gate `look_consistency`: per-segment luma/contrast/saturation within 1.5σ of the lane median; outliers named.
Cost: zero credit.

## Law 7 — THE SOUND IS LAYERED AND ARCED
Gap: one cue, one cut, thin foley, no ambience.
Fix: ambience bed per set GENERATED (MMAudio on the set plate, looped); design layer (hits/whoosh/riser/sub/drone) on
every text pop and cut in the hook (built 2026-09-08); music ARC: manifest beat.tension (1–5) → cue choice + gain
automation; foley regenerated on FINAL windows only.
Check: watch gate `foley_cover` ≥ 0.9, `music_hole_s` = 0, `text_hits` = all (built); new `music_tension_corr` ≥ 0.5
(music RMS envelope vs tension curve), `ambience_cover` = 1.0. Cost: zero credit (local compute).

## Law 8 — SOMETHING LISTENS BEFORE THE OWNER DOES
Gap: no ears in the loop.
Fix: (a) now: the owner's EAR CHECK is a formal gate with a 6-line form (VO flat? pace? music fit? foley plausible?
balance? one timestamp that bothered you) recorded in the ledger; (b) prototype a local listening model (Qwen2.5-Omni
via llama.cpp; $0) on v3 and on the reference, compare its answers to the owner's form on 3 files; promote to a blocking
gate only when it agrees. Until then every delivery says UNHEARD.
Cost: zero credit; ~2 h setup for (b).

## Law 0 — PROTOTYPE, THEN BATCH; A CONTRADICTION STOPS THE BUILD
Every new generator setting (voice direction, talking clips, angle prompts) produces ONE sample that passes its gate
before the batch is bought; the first sample that breaks a timing/density assumption stops the build and goes to the
owner with the number. Check: `prototype.json` per setting, required by `deliver.py`.

## Order (this video)
1 script: cold-open wow + emphasis marks + tension per beat + moment_ids (zero credit) → story/shots gates PASS
2 word alignment + word-driven edit + text v2 + look + music arc + ambience (zero credit) → rebuild on EXISTING clips → watch gate
3 prototype: one directed line, one talking clip, one alt angle → gates → owner ear check
4 batch: re-voice + talking clips + alt angles → bank → foley → render → watch gate → deliver checklist → owner
