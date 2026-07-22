# NEXT SESSION — Wild Bird Survival clone (start here)
_Last updated 2026-07-22. Read this top-to-bottom, then run the kickoff prompt at the bottom._

> ## ✅ UPDATE 2026-07-22 — premise decided + episode built + grit test PASSED
> The decision below is MADE: **premise = vampire finch × Nazca booby.** Episode 02 is cloned from the
> Ep01 spine with the 2 fixes applied, the hero still is locked, and the 10-clip grit test is done
> (6 clips, every distinct shot class PASS; the one artifact — blood-as-thread — is fixed).
> **Current source of truth for Ep02:**
> - Storyboard: `EPISODE_02_VAMPIRE_FINCH_STORYBOARD.md` (all 11 gates pass by design)
> - Seed stills + prompts: `EPISODE_02_HERO_STILL_AND_GROK_TEST.md` · Seeds in `assets/vampire_finch/`
> - Grit-test results + LOCKED RECIPE: `EPISODE_02_GRIT_TEST_RESULTS.md`
> **NEXT = production pass:** make wide-landscape + resolution seeds → ~75 Grok clips from the 3 locked
> seeds using the locked recipe → frame-strip each → ElevenLabs VO → FFmpeg render → gate_style_wbs.py
> 11/11 → owner watch. The material below is the original (pre-decision) handoff, kept for context.

## ⚠️ Two things before anything else
1. **Claude monthly spend limit was hit** at end of last session (workflows failed with
   "hit your monthly spend limit"). Raise/reset at claude.ai/settings/usage before running any
   large Workflow, or work inline. Small tasks are fine.
2. **The premise must change before we build.** The buffalo/oxpecker Episode-01 storyboard is
   production-ready but the PREMISE is a proven underperformer (see below). Pick the new premise
   FIRST thing next session, then the whole pipeline is ready to execute.

## What is already PROVEN / done (don't redo)
- **The look:** Grok Imagine i2v with the **grit recipe** (flies, mud, flat/overcast light, telephoto,
  handheld, "no golden hour") matches their footage. Owner approved it over the clean/Veo look.
  Prototype: `grok_grit.mp4` + `grok_grit_strip.jpg`. Recipe in `PROMPT_TEMPLATES.md`.
- **The editing grammar (measured, adversarially verified):** `FORENSICS.md` + `verified_rules_raw.json`.
  Ship-gate script `gate_style_wbs.py` (11 gates). Key numbers: hook 9–11 cuts/60s; median shot
  3.6–4.7s; coverage ≤55–60%; ≥1 hero hold 15–35s at low words/sec; ≥1 wordless action span >25s;
  music peak in first ~30%; NO SFX on cuts; VO ~150 wpm, ≤1.5 words per second of runtime.
- **Pipeline decided:** ONE locked hero still → ~60 Grok i2v clips → strip all clip audio → FFmpeg
  renderer (`scripts/ffmpeg_production_render.py`) layers 1 music bed + light diegetic ambience +
  ElevenLabs VO → `gate_style_wbs.py` → 11/11. QA in `QA_PLAN.md` (frame-strip every clip).
- **Tools confirmed available:** ChatGPT (stills), Grok Imagine (i2v — clipboard-upload recipe in
  memory `reference_grok_i2v_clipboard_upload.md`), Claude (this), ElevenLabs (VO). All owned. $0 gen.
- **Episode-01 storyboard** (full scene-by-scene, spec-checked): `EPISODE_01_STORYBOARD.md`. Reusable
  as a TEMPLATE — swap the premise/animals, keep the beat structure, timings, and gates.

## THE PREMISE DECISION (do this first)
Their view data proves the winning lever is **violation-of-expectation / gross / combat**, NOT
"a helpful animal." Evidence from their own catalog:
| Their result | Premise type |
|---|---|
| **1.98M** Fish clean a buffalo | anomaly — "fish where no fish should be" |
| **940K** Warthog lets mongooses on its face | bizarre intimacy w/ a near-predator |
| **855K** Mongoose vs spitting cobra, fight to death | combat |
| **674K** Hornbills wake sleeping mongooses each morning | bizarre ritual |
| **654K** Giants depend on a tiny bird | scale-gap |
| **34K** "Can one oxpecker *protect* a buffalo?" | **helpful bird ← our Ep01 premise. BOMBED.** |
| **13K** "Bird drinks blood from live animals" | gross but generic framing |
| **1.9K** Peregrine falcon "full life cycle" | life-cycle format, no gap |

**Ranked new-premise shortlist** (from the premise-ranker workflow; all real behaviors, all fit a
bird-centric channel + the grit look):
1. **★ Vampire finch — "Why Does This Giant Seabird Let a Finch Drink Its Blood?"** — combines their
   TOP three winning ingredients at once: giant+tiny scale gap (654K) + gross blood (their gross lane)
   + violation of expectation (a *finch*, a seed-eater, drinks blood). Real (Galápagos ground finch
   pecks boobies). **Recommended #1.** Alt title: "Everyone Thought This Finch Ate Seeds. It Drinks Blood."
2. **Fish-anomaly, fresh host** — keep the owner's "fish where they shouldn't be" intuition but don't
   1:1 clone their #1. e.g. fish swarming a different land giant / an unexpected freshwater cleaner.
   Safest bet (nearest their proven #1) but most derivative.
3. **Shrike — "Why This Tiny Songbird Impales Mice on Barbed Wire"** — bizarre, gruesome, true, bird.
4. **Combat pick** — a fight-to-the-death pairing (their 855K lane).

Owner's stated instinct (2026-07-22): the bird-helper premise is weak; the *anomaly* (fish in the
savannah) is what creates intrigue. **This is correct.** Decide between #1 (vampire finch) and #2
(fish-anomaly) next session, then execute the pipeline.

## Exact first actions next session
1. Confirm spend limit is cleared (or plan to work inline).
2. Owner picks premise (#1 vampire finch vs #2 fish-anomaly).
3. Clone `EPISODE_01_STORYBOARD.md` → new episode, swap animals into the same beat spine, apply the
   2 fixes already noted (pre-turn pause →~12s, hero hold →~30s).
4. Lock hero still in ChatGPT → generate clips in Grok (grit recipe) → VO in ElevenLabs → FFmpeg render
   → `gate_style_wbs.py` → 11/11 → frame-strip QA → owner review.

## Key files (all in research/wildbirdsurvival_teardown/)
FORENSICS.md · verified_rules_raw.json · gate_style_wbs.py · PROMPT_TEMPLATES.md · QA_PLAN.md ·
GAMEPLAN.md · PLAN_v1.md · EPISODE_01_STORYBOARD.md · COMPARISON_theirs_vs_mine.md ·
grok_grit.mp4 (approved look) · wbs_meta.tsv (all 26 videos + views).
