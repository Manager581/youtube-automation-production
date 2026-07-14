# NEXT SESSION — Dinoverse "Omega Rex" (episode_01) — resume here

**Paste-to-resume prompt** (put this in a fresh session):
> Read `dinoverse_clone/episode_01_omega_rex/v2/NEXT_SESSION.md` and continue the Dinoverse
> "Omega Rex" episode. All 81 GEN shots are locked and in `rough_cut_v6.mp4` (8:45.2, only
> placeholder = S02). Task A (Dunkleosteus S35/S36 no-teeth regen) is ✅ DONE (commit
> `aefa531`). Now do **Task B — the ElevenLabs one-pass VO** for the cold-open montage +
> the S89 ending card (this is what makes the cold open land and gives the video an ending).
> Rule: ONE generation, no re-rolls — lock the script FINAL, split at paragraph boundaries,
> SHA-verify the textarea before each Generate.
>
> Before generating, ask me three things and wait for my answers:
> 1. **Which ElevenLabs voice for LUKE and which for GF?** (the episode body uses Grok-native
>    voices — do NOT assume the Spino video's "Mark – Natural Conversations", that's a
>    different channel). Offer to cut me short audio samples of Luke + GF from the existing
>    Grok clips so I can compare before I choose.
> 2. **S46 ranger line** — overlay a clean ElevenLabs ranger VO, or leave the Grok audio?
>    (its dense 4-turn take may have slurred "that's a Utahraptor").
> 3. **S02 cold-open selfie still** — green-light me to generate it in ChatGPT with the S13
>    Luke+GF face-lock? (it's the last real still missing; currently a grey slate).
>
> Pull the exact VO lines from `STORYBOARD.tsv` (verify before generating), save the WAVs
> under `audio/dinoverse_omega/`, then have the assembler lay the VO under the cold-open
> flashes + the S01/S89 cards + S02 and TIME the cold open to the narration. Then the final
> assembly pass: music beds + SFX + ambience, real DINO ZOO logo card, midroll marker at
> S60, 1080p master. Use `venv/bin/python`; commit + push when work lands.

---

## STATE (verified 2026-07-13, branch `spinosnack-dunkleosteus`, all pushed → HEAD `aefa531`)
- **Board `STORYBOARD.tsv`: 81 clip / 0 still / 21 todo.** Every GEN (generated) shot is a
  finished clip in `v2/clips/Sxx.mp4`. The 21 "todo" are NOT missing footage — they are:
  cards (S01, S89), the S02 cold-open selfie (only real still still missing), the 10
  cold-open flashes (S03–S12, cut from real clips), and the 8 silent dread-stack trims
  (S65b/S66b/S67b/S67c/S74b/S77b/S77c/S77d) that were **deliberately dropped** from the cut.
- **Current cut: `v2/work/rough_cut/rough_cut_v6.mp4` (8:45.2, 94 shots, 1 placeholder=S02;
  v6 = v5 + the no-teeth Dunkleosteus S35/S36 takes).**
  Built by `v2/work/assemble_rough_cut.py`. mp4 is gitignored (694 MB); rebuild from the .py.
- **What v5 already has:** real cold-open flashes with native audio; audio-safe board-duration
  trims; S88 finale re-rolled (no clip-through); all 6 lip-sync clips re-rolled
  (S69/S39/S65/S72/S46/S28 — creatures/teens no longer mouth the hosts' lines); silent-repeat
  layer removed.
- **Rebuild the cut anytime:** `venv/bin/python v2/work/assemble_rough_cut.py`
  (it reads STORYBOARD.tsv + trim_plan_v2.json + flash_audio_plan.json; ~3 min).

---

## TASK A — Dunkleosteus stills S35/S36 (remove teeth) + re-i2v — ✅ DONE 2026-07-13
Stills regenerated in ChatGPT (no-teeth beak anatomy; S35 mouth closed), re-i2v'd in Grok,
whisper + frame-strip QA'd, installed, `rough_cut_v6.mp4` rebuilt (8:45.2). S36 took 4 rolls —
rolls 1–3 drew teeth whenever the jaws opened; fix = jaws-CLAMPED Move + remove the
'Sound: muffled CLACK' cue (S47 root-cause class). Winning prompt baked into the TSV.
Old takes archived: `stills/S3x_teeth.png`, `clips/S3x_roll_teeth.mp4`,
`clips/S36_regen_roll1-3_teeth.mp4`. OWNER EYEBALL: the new S35/S36 in the v6 cut (2:46–2:58).
Full detail: PIVOT_PLAN.md §I2V TRACK tail entry.

<details><summary>original task text</summary>

**Problem:** S35/S36 render the Dunkleosteus with a mouthful of pointed teeth, but Luke's line
is *"Meet Dunkleosteus. No teeth — just self-sharpening bone blades."* The teeth are baked
into the **source stills** `v2/stills/S35.png` and `v2/stills/S36.png`, so a Grok re-roll alone
won't fix it — the stills must be regenerated first.

1. **Regen the 2 stills in ChatGPT** (method: memory `reference_chatgpt_pov_still_series_method`
   — one thread, one download per fresh tab; no face-lock needed, no humans in these shots).
   The existing still-prompts already say "bone shear-blades" but ChatGPT drew teeth anyway —
   so make the anatomy explicit: *"NO teeth of any kind — a single smooth self-sharpening bony
   beak edge like a giant snapping-turtle's beak / a pair of bony shearing plates, NOT rows of
   pointed teeth."* Keep DINO ZOO brand + thick-glass aquarium look consistent with the rest of
   the Aquatic zone.
   - S35 = adult ~6 m Dunkleosteus gliding past the glass, plated head shield + bone shear-edge visible.
   - S36 = the same animal mid-bite shearing a large fish in half with the bony blades (this one
     shows the open mouth, so the beak anatomy matters most here).
2. Save over `v2/stills/S35.png` / `S36.png`.
3. **Re-i2v both in Grok** (method: memory `reference_grok_i2v_clipboard_upload`; settings
   Video·720p·6s·16:9). Prompts are already in the TSV "Grok video prompt (i2v)" column and are
   correct (S35 keeps jaw CLOSED as it glides; S36 is the bite). Pull them verbatim.
4. QA each: whisper vs the Dialogue column + a 12-frame strip to confirm no teeth. Save to
   `v2/clips/S35.mp4` / `S36.mp4` (archive the old teeth takes as `*_roll_teeth.mp4`).
5. Rebuild the cut, commit.

</details>

---

## TASK B — ElevenLabs one-pass VO (cold-open montage + ending card)
**Problem the owner reported:** the cold open feels thin and "there's no ending" — because none
of the VO/narration lines have a recorded voice yet (only the in-clip Grok dialogue is voiced).
Owner **decided: ElevenLabs one-pass.** Rule (memory `elevenlabs-one-pass-rule`): **ONE
generation, no re-rolls** — lock the script FINAL, split at paragraph boundaries (≤5,000 chars),
SHA-256 verify the textarea before each Generate. Method + textarea-injection mechanics: memory
`project_rexcaped_video2_spino_lagos.md`.

**⚠️ OPEN DECISION before generating — which voices.** The body of the episode uses Grok-native
voices for Luke and GF. The lines below are **LUKE VO** and **GF VO**, so the ElevenLabs voices
should ideally match those Grok clip voices (or be a deliberate distinct narrator framing). The
Spino/Lagos video used "Mark – Natural Conversations" / Eleven Multilingual v2 — that's a
DIFFERENT channel's voice, do NOT assume it. **Confirm the Luke voice + GF voice with the owner
first** (this is the last-chance-before-credits moment).

**The exact VO script (from STORYBOARD.tsv — verify against the TSV before generating):**
- **S01 card** — LUKE VO: "So last time, we barely made it out of the dinosaur zoo alive."
- **S02** (selfie) — GF: "This time we found the part they really didn't want us to see."
- **S03–S10 montage** — LUKE VO (over the whole montage): "A T-Rex. A raptor pack. Two hybrids
  that should not exist… and three kids who thought a locked door was a dare."
- **S11** — GF VO: "Remember them."
- **S12** — LUKE VO: "Stay till the end. You will not believe how this one ended."
- **S89 end card** — GF VO: "…we are never coming back." / LUKE VO: "Comment which dino you'd
  survive. Subscribe — part two if this hits."

Also possibly needed: a clean re-voice of the **S46** ranger line (the Utahraptor myth-bust) —
its dense 4-turn Grok take may have slurred "that's a Utahraptor." Decide with the owner whether
to overlay a clean ranger VO or leave the Grok audio.

**After generating:** put WAVs under a new `audio/dinoverse_omega/` dir (convention: other
videos live in `audio/<name>/`; keep the source MP3 chunks — audio is gitignored). Then have the
assembler lay the VO under the cold-open flashes + the S01/S89 cards + S02, and TIME the cold
open to the narration (the montage VO length sets the flash timings).

---

## THEN — final assembly to master (after A + B)
- **S02 selfie still** — the one real still still missing (needs a ChatGPT gen with the S13
  Luke+GF face-lock; owner green-light). Until then it's a grey slate placeholder.
- **Cold-open flashes** — currently reuse the payoff clips as 1.5–2 s teasers (Sik-style). Owner
  noticed the reuse; decide whether to keep, shorten, or vary.
- **Silent dread beat** — the 8 dropped trims were literal footage repeats. If a silent
  dread stack is still wanted (T-Rex + Hybrid), it needs DISTINCT alt-angle gens, not reuse.
- Music beds + Pixabay SFX + ambience under the (now-empty) silent gaps; real DINO ZOO logo
  card (replace the drawtext S01); midroll marker at S60; 1080p master.

---

## OPEN FLAGS / notes carried in
- **S46** ranger dialogue may drop "that's a Utahraptor" (see Task B) — the raptor's mouth is
  fixed (closed), only the audio is in question.
- Grok weekly cap: ~25% used as of 2026-07-13, resets **July 20** — plenty of headroom for the
  Dunk re-i2v.
- Archived defective takes live next to their clips as `Sxx_roll_talking.mp4` /
  `_roll_teeth.mp4` / `_roll1_*.mp4` (uncommitted, gitignored) if you need to compare.

## Pipeline cheat-sheet
- **Assembler:** `v2/work/assemble_rough_cut.py` → `v2/work/rough_cut/rough_cut_vN.mp4`
  (bump the output name each pass). `DROP_SHOTS` = the dropped trims; `FLASH_PLAN` /
  `TRIM_PLAN` = the audio/trim configs.
- **Grok i2v loop:** `date +%s` before each gen → `osascript` PNG→clipboard (re-set
  IMMEDIATELY before every Cmd+V — it collides with the owner's live clipboard) → New
  Generation → composer → Cmd+V → zoom-verify thumbnail → type prompt (pull verbatim from the
  TSV) → submit ↑ (1105,714) → wait ~50 s → Download (1447,607) →
  `find ~/Downloads -name "grok-video*.mp4" -newermt @<ts>`.
- **QA per clip:** whisper-small vs Dialogue column + `ffmpeg -map 0:v:0 -vf "fps=2,scale=632:-1,tile=4x3"`
  strip; for multi-animal/contact beats use 0.5 s steps (2 fps misses interpenetration — that's
  how the S88 clip-through slipped through the first time).
- Use `venv/bin/python`. Commit + push when work lands. Full running log:
  `v2/PIVOT_PLAN.md` §I2V TRACK (newest entries at the tail before "I2V lessons").
