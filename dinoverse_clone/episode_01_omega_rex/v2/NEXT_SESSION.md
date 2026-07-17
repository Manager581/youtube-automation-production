# NEXT SESSION — Dinoverse "Omega Rex" — finish to a proper master

## PASTE-TO-RESUME (drop this into a fresh session)

> Continue the Dinoverse "Omega Rex" episode. Read
> `dinoverse_clone/episode_01_omega_rex/v2/NEXT_SESSION.md` fully first — it has the
> verified state, the build pipeline, and the hard-won gotchas.
>
> Current best cut = `dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix/EPISODE_MASTER_v6.mp4`
> (7:59.6, 720p; branch `spinosnack-dunkleosteus` @ `1f604bf`, all pushed). It already has:
> recut Sik-style intro (fast cuts + cold-open VO + a CC0 T-Rex roar + dark music), a
> motivated body recut of all 81 clips (dead-air trims + aimed punch-ins + holds, dialogue
> 100% preserved), park-crowd ambience, per-zone music, real dino SFX (roars/alarm/crash),
> and the S89 end-card VO.
>
> **Do these, in order (midroll marker = SKIP, owner dropped it):**
> 1. AUDIO — dialogue-forward master. The real fix for the repeated "music too loud": our
>    native dialogue is −18.8 LUFS vs Sik's −9.6; raise+compress the dialogue to broadcast
>    level so the voice dominates and the beds recede. Set this at MIX time in
>    `build_remix_real.py` (raise the `[nmix]` native path), not just as a post master.
> 2. AUDIO — apply the S46 ranger VO. `audio/dinoverse_omega/ranger_s46.wav` (Brian) exists
>    but NO build uses it, so S46 still plays its garbled native line. Lay the ranger VO over
>    the shipped S46 clip (duck/strip the native under it) so "that's a Utahraptor" lands.
> 3. Ask the owner the body-voice decision (keep native Grok dialogue w/ its shot-to-shot
>    drift = format-native, OR drop in the ready Liam dub). Then rebuild → **v7**.
> 4. Get the owner to LISTEN to v7 and confirm the balance — you CANNOT hear audio, so their
>    ear is ground truth. Ask for a timestamp if anything's still off.
> 5. S02 selfie still (only real missing shot) — owner green-light needed; ChatGPT gen w/ the
>    S13 face-lock, framed POV not selfie, then Grok i2v.
> 6. Real DINO ZOO logo card (S01 is drawtext; no logo image in repo) — create/source, round
>    green `#2ecc40`.
> 7. Loudness master to ~−14 LUFS + fix peak clipping (`scripts/audio_master.py`).
> 8. 1080p upscale (segments are 1264×720).
>
> Use `venv/bin/python`. Commit + push when work lands. DO NOT re-litigate re-voicing the
> body (the drift is in Sik's own hit video too — see below).

---

## VERIFIED STATE (2026-07-15, branch `spinosnack-dunkleosteus`, HEAD `1f604bf`, all pushed)

**Current master:** `v2/work/proto_mix/EPISODE_MASTER_v6.mp4` — 7:59.6, 1264×720, ~520 MB
(gitignored — rebuild from scripts). Tightened from 8:52 by trimming 53s of dead air.

**Three real gaps still in v6 (verified):**
- **S02** — `clips/S02.mp4` + `stills/S02.png` both MISSING; the intro uses stand-in shots
  for the selfie beat.
- **S46 ranger** — `audio/dinoverse_omega/ranger_s46.wav` exists but is referenced by NO
  build script → S46 still plays garbled native audio (whisper hears "otter-raptor",
  "Utahraptor" absent). The ranger VO must be laid in.
- **Body voice** — the master uses `body_native.m4a` (Grok dialogue), which has shot-to-shot
  voice drift. The **Liam dub** (`audio/dinoverse_omega/luke_s*.wav`) was generated but is
  NOT in the cut. Open decision.

## THE BUILD PIPELINE (all in `v2/work/proto_mix/`)
Run order to regenerate the master from scratch:
1. `build_intro_recut.py` → `intro_RECUT.mp4` (cold open: VO + T-Rex roar + dark music).
2. `build_master.py` → motivated body from `motivated_recipes.json` (+ `body_pauses.json`);
   writes per-clip segments to `_master/` (video `body_v.mp4`, native `body_native.m4a`,
   end card `ec_n.mp4`) that the next script REUSES.
3. `build_remix_real.py` → the full master: body mix (native + ambience + music + SFX) +
   intro + end card → `EPISODE_MASTER_v6.mp4`. **This is where audio balance lives.**
   (`build_remix_audio.py` = an earlier placeholder-music variant; `proto_mix_climax.py`,
   `build_carno_*.py` = the validated prototypes.)

Key data: `motivated_recipes.json` (81-clip cut recipes: trim/punch/hold + aim), 23 punches
/ 58 holds. `body_pauses.json` (per-clip speech pauses + dead-tail map).

## AUDIO — where it's at + the real fix
Music level history (owner kept saying too loud): **−23.5 → −30.7 → −35.7 LUFS**, now
hard-ducked. Ambience −34.6 (subtle). Dialogue −18.8.
- Sik reference (`v2/work/vo_prep/sik_voice_control.json`, `_sikmusic/`): dialogue **−9.6**,
  combined bed (music+ambience+crowd, demucs can't split music alone) **−15.8**.
- **Root cause = the dialogue, not the music.** Ours is ~9 dB quieter than Sik's and it dips,
  so any bed feels exposed. Fix = dialogue-forward (raise+compress the voice), NOT more music
  cuts. THIS IS THE NEXT AUDIO STEP.

## HARD-WON GOTCHAS — do not repeat these
- **You cannot hear audio.** Every mix call is blind — that's how a looping bird chirp AND
  repeatedly-too-loud music slipped through. Owner's ear is truth; ask for timestamps.
- **Ambience:** use `assets/dino_ambience/crowd_a.mp3` + `crowd_b.mp3` (human murmur, NO
  zoo/nature = no birds), rotated, subtle. Never loop ONE clip that has a distinctive event.
- **Voice-drift is format-native.** Sik's own 764K-view video drifts the same way
  (`sik_voice_control.json`). Do NOT re-derive "the hosts sound inconsistent" as a defect or
  re-launch a re-voice unless the owner explicitly asks.
- **NO copyrighted audio.** Owner wanted the "classic Jurassic Park T-Rex roar" — that's
  Universal's copyrighted sound design; used a CC0 roar that evokes it instead. Keep it CC0.
- **Audio sourcing:** Pixabay CC0 via claude-in-chrome downloads clean (no login/block).
  Assets committed (force-added past `assets/*.mp3` ignore) in `assets/dino_{ambience,sfx,
  music}/`. Shopping list + P2/P3 remainder: `work/proto_mix/SOUND_SHOPPING_LIST.md`.
- **ffmpeg concat:** copy-concat inflates AAC audio duration by tens of seconds. Concat
  AUDIO via the concat FILTER, VIDEO via copy-concat, then mux. (Bit us on the first master.)
- **iCloud:** the repo is in ~/Documents (iCloud) — freshly-written temp files occasionally
  time out on first open ("Operation timed out"); just retry the build.
- `sed`/`awk`/`echo` and `Date.now()`/`Math.random()` caveats aside — use `venv/bin/python`.

## STILL-OPEN DECISIONS FOR THE OWNER
- Body voice: native drift (format-native) vs Liam dub.
- S02: green-light to generate.
- Optional: cutaway inserts (dropped from the auto pass for reliability); re-roll the 3 worst
  drift clips S20/S45/S33; S13/S37 POV re-rolls (only if applying the Liam dub).

## Full running log
`v2/PIVOT_PLAN.md` §I2V TRACK; memory `project_dinoverse_production.md`. Reference deep-dive
+ voice control: `v2/work/vo_prep/`. Sik cut analysis: `work/sik_analysis/`.
