# NEXT SESSION — Rexcaped (the channel formerly known as the Dunkleosteus build)

**This session pivoted hard.** It started as "build the Dunkleosteus video" and became:
fact-check the old "winning formula" → find it was wrong → measure the *real* edit grammar
→ rebrand to **Rexcaped** → build a working **edit-engine**. Read this before touching anything.

## ▶ PASTE THIS TO START
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
