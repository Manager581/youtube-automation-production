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

## What's LEFT to a finished video
1. **Tune asset ratios** in `rexcaped_edit_engine.py` (assign_assets) to hit ~20/40/25/10. (no-decision, quick)
2. **Build a stat-card generator** — orange/black branded cards w/ the spoken number. (no-decision, buildable now)
3. **Asset library** — creature (our i2v pipeline, proven), **stock footage** (needs a sourcing decision),
   **memes** (needs the COPYRIGHT decision — the ref channel uses copyrighted clips; risky monetized).
4. **The pilot** — T-Rex script (no-evolution) → F5 voice → engine → assets → render → ink thumbnail.

## 🔑 Two decisions only the owner can make
- **Meme strategy**: copyrighted clips like the ref channel (fair-use risk) vs. freely-usable/original cutaways.
- **Stock sourcing**: which library/approach (project rule historically = no Pexels/Pixabay images; real stock video TBD).

## Gotchas / conventions (still true)
- Direct venv paths (iCloud renames symlinks): `venv.nosync/bin/python`, LTX `tools/ltx-video/ltx_env.nosync/bin/python`.
- Renderer: `scripts/ffmpeg_production_render.py --paper-edit X --narration Y --output Z [--preview]`.
- Reference videos were downloaded to `/tmp/edit_deep/` (EPHEMERAL — re-download via the IDs in `scripts/extract_edit_grammar`/the engine if needed; the *measured* data is preserved in `research/edit_analysis/`).
- F5-TTS on CPU + short single-register voice ref; one MPS torch job at a time.
- The 18 Dunkleosteus creature clips (`footage/dunkleosteus/`) + stills (`assets/dunkleosteus/`) remain — the Dunk is a ready **video #2**, just strip its evolution lines.
