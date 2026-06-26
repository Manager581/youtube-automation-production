# PRODUCTION HANDOFF — Dinoverse "Omega Rex" episode (resume here)

Last session got us from "study the creator" to a production-ready storyboard. **Next job: generate the ~70 stills.**
Read this + `VERIFIED_PROMPTS.md` + `EDITING.md`, then start generating scene-by-scene.

## STATUS — what's done
- ✅ Full chat archive (WhatsApp "Sik" + Messenger "Dinoverse") → Google Doc + `~/Desktop/dinoverse_archive/`.
- ✅ His **verified prompts** captured (`VERIFIED_PROMPTS.md`): the Image-Prompt-Generator + the Video-Prompt-Generator (his exact reusable system prompts).
- ✅ His **editing** decoded (`EDITING.md`): CapCut, 1080p export, opens with 2 DISCLAIMER cards, freesound.org ambience layers + a music bed, hard cuts, ~8:20 timeline.
- ✅ His **real published video** transcribed + speaker-attributed (`reference/dinoverse_TRANSCRIPT_attributed.md`). Video = "I Found a Dinosaur Zoo | D-Rex Vibes", 8:20, 764K views.
- ✅ **Storyboard built** = Google Sheet "Dinoverse - Omega Rex - Storyboard" (Sheet1), 88 timeline clips, scene-by-scene, columns: Scene/Shot/Time/Dur/Beat/Speaker/On-screen/Camera/**Image prompt**/**Grok video prompt**/Dialogue/SFX/Music/Clip type/Edit/Status. Local copy: `STORYBOARD.tsv` (regenerate via `build_storyboard.py`).
  - Sheet URL: https://docs.google.com/spreadsheets/d/1Jjh54dzgGtjjMuM5jGSn5eVAtPE6Kry48mTnPZ_ADoQ/edit
- ✅ **A/B prompt test** done → tab "A-B Prompt Test" (has the Spino A-vs-B image + both prompt versions).

## DECISIONS LOCKED
1. **Format:** faithful Dinoverse zoo-POV that turns to disaster (Omega/D-Rex hybrid). ~90 clips, ~8 min.
2. **Image prompts = HIS verbose "Version B" style** (chosen via the A/B test). Already applied to all 70 GEN rows in the sheet/`build_storyboard.py` (the `IMG`+`SUF` wrapper).
3. **i2v = Grok Imagine** (6s/720p, native audio).
4. **Dialogue = Grok-native** for the WHOLE body. VERIFIED: his real 6.04s Grok clip's audio = "I don't know why I'm here, whether to enjoy this or suffer through it" — verbatim in his published video. So **only the ~20s intro hook is a separate recorded VO**; everything else (facts, banter, staff, PA) is generated inside each Grok clip from the dialogue line in the Grok-prompt column. Caveat: long fact lines may need re-rolls.
5. **Assembly:** Grok clips (keep native audio) → layer freesound ambience + music bed → 2 disclaimer cards at front → logo bug → 1080p. FFmpeg concat per `ORCHESTRATION.md`, or CapCut.

## NEXT STEP — generate the stills (the actual job)
Counts: **70 unique GEN stills** to make. The 16 intro "flashes" are TRIMS of body clips (no generation). 2 cards are text.

### Batching plan (consistency-first, browser-driven, no paid API)
Work **one scene per image-gen thread** (Gemini recommended — cleaner browser flow than ChatGPT; ChatGPT also fine):
1. From Sheet1, copy the scene's **Image prompt** cells (column I) for its GEN rows.
2. In a fresh Gemini/ChatGPT thread: generate the scene's **establishing shot first**.
3. Curate it (realism is won here), then **feed it back as the reference** ("same Dinoverse Zoo location, same Dee/Maya, keep it consistent") and generate the scene's remaining shots in that same thread.
4. Download each (lightbox → download button), save to `stills/Sxx.png` (per shot id).
5. Mark that row's **Status** column → "still" in the sheet.
- ~12 scenes → ~12 threads. Do 2-3 scenes per session to stay within context.
- **Start with the Spinosaurus scene (S10-S15)** — it's the validated one (A_S10/B_S10 already exist in `ab_test/`).

### Then (separate phase, later): Grok i2v
For each still: upload to grok.com/imagine (Video, 720p, 6s, **set 16:9**), paste the row's **Grok video prompt**, generate, download → `approved/Sxx.mp4`, Status → "clip".

## KEY FILES (all in `dinoverse_clone/episode_01_omega_rex/`)
- `VERIFIED_PROMPTS.md` · `EDITING.md` · `STORYBOARD.tsv` + `build_storyboard.py` · `reference/dinoverse_TRANSCRIPT_attributed.md` · `ab_test/` (A/B images) · `proto_spino/` (early proto) · folders `stills/ gen/ approved/ work/ audio/`
- Hard rules: `../../CLAUDE.md`. Tools: FFmpeg renderer `scripts/ffmpeg_production_render.py`.

## HOW TO RESUME (paste into a fresh session)
"Read dinoverse_clone/episode_01_omega_rex/PRODUCTION_HANDOFF.md and VERIFIED_PROMPTS.md. Decisions are locked. Generate the Spinosaurus scene stills (S10-S15) from the Sheet1 image-prompt column using Gemini in Chrome, one thread, establishing shot first then reference the rest; save to stills/ and mark Status=still."
