# NEXT SESSION — Rexcaped (the channel formerly known as the Dunkleosteus build)

**This session pivoted hard.** It started as "build the Dunkleosteus video" and became:
fact-check the old "winning formula" → find it was wrong → measure the *real* edit grammar
→ rebrand to **Rexcaped** → build a working **edit-engine**. Read this before touching anything.

## ⚡ SESSION 2026-06-10c/d — Tier-2 DONE, spec written, build-order step 1 DONE
**`research/viral_recreation_spec.md` is the canonical style target** (10 measured laws +
receipts + gap table + build order). Tier-2 frame anatomy is finished (card typewriter ~27
chars/s on brand canvas, boiling 2-3-frame logo loop, bursts = frenetic INSERTS not splices,
puppet-fight composites, noun-rhyme comedy chains, 1.77s median event gap / 91% of runtime
within 4s of an event). Loser control (Chaos Theory, 556 views) confirmed which layers are
load-bearing. **Step 1 shipped (cf9efca)**: `fill_timer_cuts()` in the engine (word-aligned
timer cuts + 6s cap) → `trex_pilot_paper_edit_v2.json` → `output/trex_pilot_v2_540p.mp4`.

**Measured v2 render vs winner band** (tools: extract_motion_events.py + detect_onsets):
cuts 22.5/min ✓ (was 11.1; winner 18.5) · median 2.75s ✓ (winner 2.85) · >5s 2% ✓ ·
music 0.85 (winner 0.91 — nudge bed level/genre) · **sound-on-cut 69% vs 95% target** (SFX
wired on 123/129 beats but onsets don't register — likely soft whoosh attacks / placement
offset; investigate in renderer) · **within-shot events 2 vs winner 274; 76% shots static**
(expected — the EVENT LAYER doesn't exist yet; that's the build).

**▶ PASTE THIS INSTEAD (2026-06-10e — owner rejected the animatic open TWICE; mock-first now):**
> Read `research/viral_recreation_spec.md`, `research/trex_pilot_shot_sheet_hook.md`, and
> `research/NEXT_SESSION.md` (esp. "HOW ON-SCREEN CHOICES GET MADE"). Owner watched
> `output/trex_hook_animatic_540p.mp4` and rejected the first 10s twice: (1) black text cards
> — "ZERO black text in the viral video" → ALL cards re-skin to ORANGE canvas
> (`rexcaped_stat_cards.py render_card_orange()` is built; sample blessed-pending at
> `/tmp/card_orange_sample.png`); (2) "odd shots of New York City … looks NOTHING like the
> viral video" → diagnosis: the winner's open is a SCENE (premise on screen while VO talks,
> stats ride as small overlays); ours was a mood board (stats-first full-frame cards + dark
> creature-less b-roll). Fix structure: frame 1 = creature-in-bright-NYC wide, stats become
> orange OVERLAY chips on world shots (overlay-within-a-beat compositing NOT yet in renderer).
> DONE: still A `assets/trex_pilot/hook_stills/169/ch_trex_avenue_wide.png` (trex mid-avenue,
> bright winter daylight, taxis, fleeing crowd — the money establishing shot). TO GENERATE
> (same ChatGPT convo "T-Rex Skull Landscape Image"; typing into the open image VIEWER's
> "Describe edits" box generates a new chat image USING the open one as style/character ref —
> that's how A stayed consistent): B = "same trex/street/light, LOW-ANGLE from street level
> between two yellow taxis, torso+head looming, breath fog, 16:9"; C = "same trex walking away
> down the avenue toward distant skyscrapers, crowd scattering, 16:9".
> **THE GATE (promised to owner): build ONE mock strip image of the restructured 0–15s
> (new stills + orange overlay chips, timestamps + VO lines under each tile, ≤2000px wide)
> and get veto/bless BEFORE re-rendering anything.**
> Event layer v1 is IN (e1a5cf0): slam enters, per-event SFX, typewriter+boil MOVs, whoosh-hit
> grammar (swell INTO cut 0.5 + impact ON cut 0.4 — whoosh-only reads silent). Animatic v2.3
> measured sound-on-cut 97% ✓, music 0.867 (real fix = trex bed, owner music decision). Still
> to build: overlay pop-ins WITHIN a beat (now required by the restructure), odometer MOV,
> map/clock cards, sway on long stills. Gates after mock-bless: events ≥25/min, static <40%.
> Owner decisions pending: ink-gag comedy lane, stock lane, i2v spend (Kling/Veo/Hailuo).
> ChatGPT gotchas: download ONLY from the image VIEWER (verify Select/Aspect-ratio toolbar)
> — the chat layout's corner button is Share and once created a PUBLIC link (deleted via
> Settings→Data controls→Shared links). Downloads → ~/Downloads "ChatGPT Image <date>.png",
> 1536×1024 → center-crop 1536×864 into `hook_stills/169/`.

## HOW ON-SCREEN CHOICES GET MADE (the decision chain — owner asked 2026-06-10)
Three layers, in order of trustworthiness:
1. **Measured laws (machine-checked):** tempo, event rate, sound-on-cut %, music coverage,
   card flash length, asset-mix ratios — frame-measured from the winner into
   `viral_recreation_spec.md`; our renders are measured against the same bands with
   `extract_motion_events.py`. Never overridden by taste.
2. **Mapping rules (from the winner's grammar):** script noun → literal visual ("bathtub" →
   skull-vs-bathtub), stats → cards (flash 1–2s, overlay-on-world preferred), failure beats →
   comedy, premise plays ON SCREEN while the VO talks. Authored row-by-row in the shot sheet
   (`trex_pilot_shot_sheet_hook.md`: ON SCREEN / MOTION / SOUND per beat).
3. **Taste calls (the weak link):** which exact image fills a slot, palette, composition,
   structure of the open. BOTH owner rejections came from this layer being machine-filled.
   **Rule now: layer-3 choices get a human gate — sheet + ONE cheap mock strip → owner
   veto/bless → only then manufacture/render.** (The professional analog: nobody renders
   finals before the animatic is approved.)

Cull check while testing: `footage/trex_pilot/dunk_trex_stride_avenue.mp4` may read long-necked
on the street shots (eyeballed in the v2 sanity sheet) — review against the jaws/eye/taxi clips;
`_dunk_trex_full_body_street.mp4` is already excluded (underscore prefix).

What today established (details in memory + `research/edit_analysis/`):
- **Deep-watch, winner (DzUKhb2ZSko, all 532 shots)**: 5 pilot gaps — tempo (pilot 11.1 cuts/min
  vs 18.5, median 5.4s vs 2.85s, 60% shots >5s), NO music wired, cards held 5–15s vs 1–2s flashes,
  missing graphics system (logo stamp ~2min cadence / maps / clocks / calendar / charts), dark vs
  golden palette. Comedy = 3 length classes incl. FULL copyrighted scenes, clustering on failure
  beats. Their creature footage is weak — ours wins that layer.
- **Loser triangulation (Chaos Theory "T-Rex in Amazon", 556 views, grammar committed b1f8843)**:
  cloned title/ink-thumbnail/logo/music/2nd-person VO and still died → the viral ingredients are
  the things it skipped: variety engine, burst texture, modern-world collisions (its "modern
  Amazon" shows zero modernity — broken title promise), story dramaturgy, CTA flywheel.
  ⚠ Our engine-cut pilot paces in the loser's quadrant (11.1 vs their 11.7 cuts/min).
- **Frame-event prototype (the egg open, 0–14s)**: the "10s hold" is ~10 visual states (egg sways →
  crack-pop → hatchling jitter → cartoon pop-up → sun SLAM → wipe → O₂-molecule overlay bobs →
  exit → canopy cut → head-bob). Visuals illustrate the script NOUN-BY-NOUN; motion floor never 0;
  87% of within-shot events land ≤0.15s from a percussive onset (motion is sound-designed);
  first-minute visual event rate = 36/min vs 13 hard cuts. Tool: `scripts/extract_motion_events.py`
  (Tier-1 mechanical, validated vs prototype); full-video output → `trex_motion_events.json`.
- **Tool audit (June 2026, memory `reference_tool_landscape_2026-06.md`)**: FFmpeg stays the engine;
  Resolve Studio = scriptable Super-Scale + finishing; Sora is dead → stills stay ChatGPT (GPT Image 2),
  i2v = Kling 3.0 / Veo 3.1 / Hailuo (~$3–25/pilot, owner spend-OK pending); skip Premiere/AE.
- **Renderer/engine implications queued** (after Tier-2): engine timer-fallback cuts + ~6s cap +
  burst preservation; music wiring; card flash timing + logo-stamp + map/clock/chart cards; an
  EVENT layer in the renderer (animated card pop-ins, overlay slide-ins, composited creature-in-
  stock shots); daylight asset pass. Intro (66s hand-cut, 1080p rendered 09:47) already hits body
  tempo (median 2.52s, cards flash, 0 shots >5s) but recycles 5 clips ~12× and is a stats-barrage
  where the winner hooks story-first — owner judgment call.

## ▶ ORIGINAL PASTE BLOCK (pilot pipeline — still valid, now second priority)
> Read `research/NEXT_SESSION.md`, `research/edit_grammar_ruleset.md`, and `scripts/rexcaped_edit_engine.py`.
> We've measured the real edit grammar of the top creature-sim videos and built the Rexcaped edit-engine (script → cut plan). Next: **tune the asset ratios, build the stat-card generator, then run the T-Rex pilot** — script (no-evolution rule) → cloned voice → engine → assets → render. Don't re-derive; build.

## ⚠️ The old "formula" was wrong — do NOT trust `spinosnack_winning_formula.md`
A prior session's analysis (13 videos) had real errors we verified by re-watching:
- It called **video-game footage (Maneater) and borrowed clips "3D CGI."** They don't make original creature visuals — they assemble **game footage + real stock + memes + cards**.
- The "13 analyzed videos" are **≥2 different channels** mashed together (a faceless collage channel + a face-cam reaction creator) → its top-vs-bottom and "face-cam = loser" claims are confounded.
- Its "cut every 5s / 18–26 min" numbers were **averages hiding the truth**.
**The trustworthy artifact is now `research/edit_grammar_ruleset.md`** (measured, with the honest limits).

## What we MEASURED (the real model — `research/edit_grammar_ruleset.md`)
- **Cut rhythm is multi-modal**, not an average: 0.07s machine-gun bursts (lists/"simple math" beats) → ~3s body collage → 9s+ held cards. ~95% of cuts have a sound hit; wall-to-wall music.
- **Cuts are ~80% on a script feature** (stat/turn/pause) BUT — honest caveat — that's only **~7 points above random** once density is matched. **Exact cut placement is NOT script-reproducible** (it's visual/editorial judgment). So the goal is **STYLE-FIT, not cut-cloning.**
- **The creature is only ~20–25% of shots.** Mix ≈ **stock B-roll 40% / memes 25% / creature 20% / cards 10%.** We do NOT need a creature per beat — a few hero creature shots + a stock/meme/card library carries it.

## The brand — Rexcaped ✅
- Name: **Rexcaped** (a T-Rex that *escaped* into the modern world — premise baked into the name).
- Mark: **orange T-Rex emblem** → `assets/brand/emblem_trex_orange.png` (also `emblem_trex.png` teal, `emblem_A_creature.png`, `emblem_B_containment.png`). The hand-drawn ink style doubles as the thumbnail base.
- Worldview rule (owner is a young-earth Christian): **no dates, no "evolution," no geologic-epoch dating.** Use "ancient / a world that's gone." Keep physical stats (bite force, size). A rewritten no-evolution Dunk cold open is in this session's transcript.
- Pilot title (proven template): **"I Simulated A T-Rex In Modern New York, It Was Brutal."**

## What's BUILT and committed (branch `spinosnack-dunkleosteus`)
- `scripts/extract_edit_grammar.py` — cuts (ffmpeg scene-detect) ↔ word-timed transcript ↔ moment-type.
- `scripts/analyze_shot_assets.py` — samples shot frames + OCR + contact sheets for asset-typing.
- `scripts/validate_edit_engine.py` — predictability test vs real cuts (+ null model).
- `scripts/rexcaped_edit_engine.py` — **the engine**: script → candidate cuts (stat/turn/pause) → tempo selection (slow-hook/fast-body, rapid-fire bursts) → asset assignment. Self-validates.
- `research/edit_grammar_ruleset.md` — the measured ruleset (THE reference).
- `research/edit_analysis/*_grammar.json` — preserved measured cut data (megalodon/titanoboa/trex).
- **Proof it works end-to-end:** `storyboards/dunk_rexcaped_demo_paper_edit.json` → rendered
  `output/dunk_rexcaped_tempo_demo_540p.mp4` (Dunk footage auto-cut at Rexcaped tempo, 41 cuts incl.
  0.3s bursts). Creature-only (no stock/memes yet) — it proves the RHYTHM, not the full look.

## ✅ Session 2026-06-10b — the pilot PIPELINE is now end-to-end (script → 540p video)
Everything in "what's left" items 1, 2, and most of 4 is DONE and committed. The whole
chain runs from the script with no manual assembly:

```
scripts/trex_pilot.txt                              # the script (906w, no-evolution)
  → pipeline/voice_generator.py (F5_DEVICE=cpu, --auto-transcribe)  → narration.wav + manifest
  → scripts/correct_manifest_crossfade.py           # ⚠ REQUIRED drift fix (see below) → *_aligned.json
  → scripts/rexcaped_edit_engine.py --vtt <aligned> → trex_pilot_plan.json (mix 41/27/21/11 ✓)
  → scripts/rexcaped_stat_cards.py --plan <plan>    → assets/trex_pilot/cards/ (cards + slates)
  → scripts/rexcaped_plan_to_paper_edit.py          → storyboards/trex_pilot_paper_edit.json
  → scripts/ffmpeg_production_render.py --preview    → output/trex_pilot_540p.mp4
```
**Proof:** `output/trex_pilot_540p.mp4` (5.7 min, 540p). QA: 0 black frames, audio OK,
duration 340.65s = the wav EXACTLY (zero drift), stat cards + placeholder slates +
creature clips all composite correctly. Asset mix lands on the measured target.

⚠️ **The crossfade drift bug (don't skip the corrector).** `voice_generator.py` timestamps
segments on a no-crossfade cursor, then concatenates with an 80ms acrossfade at every
boundary → the wav ends ~0.08s × (n_segments−1) EARLIER than the manifest (here 10.08s on
350.7s). Align the engine/paper-edit to the raw manifest and the finale lands past the wav
end and gets dropped — the exact v13e bug. `correct_manifest_crossfade.py` rebuilds the true
timeline (residual 0.000s here). **Always run it between voice gen and the engine.**

## What's LEFT to a finished, uploadable video (the remaining work is ART + 2 decisions)
1. **Creature quality** — this session's 8 hero clips (`footage/trex_pilot/`, gitignored) were
   LTX **t2v** (no still) as a fast proof. Quality is mixed: the jaws/teeth + taxi-hunt shots
   read as a real T-Rex; the full-body shot skewed long-necked. **The quality path is i2v from a
   curated still** (storyboard `storyboards/trex_pilot_storyboard.json` has `still_prompt` per
   shot): make ChatGPT photoreal stills → `gen_dunk_clips.py --i2v --stills-dir <dir>`. ~20–25%
   of shots, so 8–12 good hero clips is plenty.
2. **Fill the placeholder slots** — the render currently shows branded SLATES for every stock
   and meme beat; each slate prints the spoken line + timecode, so it IS the sourcing shot-list.
   Drop real clips in and re-run the converter. Blocked on the 2 decisions below.
3. **Thumbnail** — ink/emblem base in `assets/brand/`; `playbook/titles_thumbnails.json` + the
   existing scorers (`pipeline_v2/title_thumbnail_evaluator.py`). Title is locked.
4. **Then** full 1080p render (drop `--preview`) + upload.

## 🔑 Two decisions only the owner can make (unchanged — now the ONLY blockers to assets)
- **Meme strategy**: copyrighted clips like the ref channel (fair-use risk on a monetized
  channel) vs. freely-usable / original comedic cutaways. ~26% of the cut rides on this.
- **Stock sourcing**: which library/approach for ~42% of shots (NYC: city/people/traffic
  stock). 🚫 **HARD RULE — NO Pexels content EVER (video AND images), and no Pixabay images
  (Pixabay = music only).** So the open decision is *which non-Pexels* source: e.g.
  archive.org / public-domain footage, Wikimedia video, YouTube Creative-Commons clips, or
  original capture. Pexels is off the table regardless of how the decision lands.

## Gotchas / conventions (still true)
- Direct venv paths (iCloud renames symlinks): `venv.nosync/bin/python`, LTX `tools/ltx-video/ltx_env.nosync/bin/python`.
- Renderer: `scripts/ffmpeg_production_render.py --paper-edit X --narration Y --output Z [--preview]`.
- Reference videos were downloaded to `/tmp/edit_deep/` (EPHEMERAL — re-download via the IDs in `scripts/extract_edit_grammar`/the engine if needed; the *measured* data is preserved in `research/edit_analysis/`).
- F5-TTS on CPU + short single-register voice ref; one MPS torch job at a time. **Confirmed
  this session: F5 (CPU) and LTX (MPS) run concurrently fine** — voice gen + 8 clips generated
  in parallel, no deadlock. Voice gen on CPU ≈ real-time-ish (350s audio in a few min); LTX
  t2v ≈ 350s wall per 4s clip at 512×288.
- Pilot voice command:
  `F5_DEVICE=cpu venv.nosync/bin/python pipeline/voice_generator.py --ref-neutral assets/voice/voice_neutral_ref_short.wav --ref-tense assets/voice/voice_tense_ref_short.wav --ref-energized assets/voice/voice_energized_ref_short.wav --auto-transcribe --script scripts/trex_pilot.txt --out audio/trex_pilot/narration.wav`
  (WPM-normalize is ON by default — do NOT pass --no-wpm-normalize; refs have no saved text → use --auto-transcribe.)
- `verify_render.py` is breaking_law-tuned (checks intro_spec/chapters/overlays it won't find on
  a pilot). For creature pilots, QA manually: `blackdetect`, ffprobe audio + duration==wav,
  and eyeball a few extracted frames (what this session did).
- The 18 Dunkleosteus creature clips (`footage/dunkleosteus/`) + stills (`assets/dunkleosteus/`) remain — the Dunk is a ready **video #2**, just strip its evolution lines.
