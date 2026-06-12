# NEXT VIDEO — full pipeline handoff (every claim tool-verified 2026-06-12)

**Paste the block at the bottom into a new session to start video #2.**
This file is the complete, verified state of how a Rexcaped video gets made,
learned the hard way across the pilot. ✓ = verified by tool call on 2026-06-12.

---

## 0 · Channel state (live right now)

- ✓ Channel: **Rexcaped** — https://www.youtube.com/@rexcaped (rebranded from "Watch This",
  handle @rexcaped, T-Rex emblem avatar, orange banner). Channel ID `UCAYP6fzqaCymk_0FFZ9yLJQ`,
  Google profile "Jeff" in Chrome.
- ✓ Video #1 LIVE + public: https://youtu.be/Dmmtwvx7qnE — owner retitled it
  **"I Simulated A T-REX In NYC And It's Terrifying..."** (6:06, 540p full draft:
  hook + rebuilt CH1 + UNCONVERTED CH2/CH3 back half incl. one AP-watermarked clip).
- ✓ Thumbnail on the video = owner's own "Everything Dies" upload (phone verification done —
  custom thumbnails WORK now).
- ⏳ Thumbnail **A/B testing** is gated behind YouTube *advanced-features* verification
  (6-second selfie video / ID / 2 months history). Dialog was left open for the owner.
  Test arms ready: owner's "Everything Dies" + `assets/trex_pilot/thumbnail_inkhorror_trex.jpg`
  ("Run.") + `assets/trex_pilot/thumbnail_variant_survive.jpg` ("Survive?").
- Flywheel: video #1's description runs "NEXT PREDATOR? You pick — top comment wins."
  → **video #2's creature should come from its comments** (or owner picks).

## 1 · What a Rexcaped video IS (the format, measured)

Source of truth: ✓ `research/viral_recreation_spec.md` (10 measured laws) +
✓ `research/style_bands.json` (the bands as machine-checkable numbers) +
✓ `research/edit_decision_rulebook.md` (owner's shot-decision logic).

One sentence: *a second-person survival simulation of an extinct apex predator
in a modern place, cut at ≥25 visual events/min over wall-to-wall music, where
every stat plays as an illustrated scene and every creature beat is a moving
layered composite.*

Reference channel = **Spinosnack** (405K subs). Their viral tier (verified by
scraping their feed): Titanoboa 1.6M · T-Rex Africa 1.2M · Deinosuchus 591K ·
Amber 462K · Yutyrannus 286K. Refs on disk: ✓ `research/edit_analysis/ref_thumb_winner.jpg`
(+copycat). Grammar JSONs: ✓ `research/edit_analysis/*_grammar.json`.

## 2 · The pipeline, end to end (exact verified commands)

**Step 1 — Creature + place.** Formula: "I Simulated a {Creature} in {Modern Place},
{Consequence}". Modern collision is mandatory (the copycat died breaking that promise).
Check video #1 comments for the vote first.

**Step 2 — Script.** Second person ("you wake up as..."), chapters (BODY → senses →
hunt → reckoning), every stat noun-literal so it can be illustrated, comedy on failure
beats. The pilot script lives in the paper-edit beat texts (`storyboards/trex_pilot_*.json`).
Playbook: `playbook/scripting.json`. ⚠ Owner rule: no-evolution/no-dates editorial.

**Step 3 — VO.** ElevenLabs voice **"Mark"** (generated on the ElevenLabs site — no in-repo
generator; ✓ grep found none). Save as `audio/<video>/narration_11l_mark_full.wav`.
Then word-level alignment — ✓ `venv/bin/whisperx` exists and imports:
produce `narration_11l_mark_whisperx.json` (same format the engine's `ALIGN` expects).

**Step 4 — Stills.** ChatGPT image gen, ONE conversation per world so creature/street/light
stay consistent (pilot's convo: `chatgpt.com/c/6a298186-4870-83ea-ae09-f065a1ce5568`).
Download via the in-browser conversation-API route (see memory `project_rexcaped_launch.md`),
**never the Share button**. File into `assets/<video>/body_stills/` etc. following the
`c_*` (creature scene) / `i_*` (ink gag) / `g_*` (graphic) convention.
Pilot library for reuse: ✓ 24 body_stills · 15 cutouts · 22 stock clips · 13 dunk footage ·
21 SFX · 21 graphics.

**Step 5 — Cutouts.** `rembg` (✓ importable in venv) on creature stills; when rembg gets
<10% coverage (reflections, macros) use the hand-drawn soft-mask fallback (PIL ellipse +
GaussianBlur — see `c_glass_refl_cut.png` history).

**Step 6 — Composites (the visual engine).** ✓ `scripts/composite_beat.py` — each beat is a
CONFIG: cutout + moving bg (`bg_video`/`bg_still` self-layer) + motion preset
(`lunge/stumble/loom/macro_drift(tune cx,cy,s)/pov_edge`) + camera (`push/slam/handheld`)
+ word-anchored text pops + SFX + devices (`measuring_tape/gauge/speedometer/count/reticle`).
Per-video builder follows ✓ `scripts/build_ch1_composites.py`'s SPLICES pattern (renders
clips, splices into the paper edit, regenerates the chapter slice + narration span).
Shot decisions: ✓ `scripts/beat_director.py` runs the owner's rulebook.
**Owner's locked rule: ZERO Ken-Burns-on-a-still creature beats — composite or footage only**
(gate enforces it).

**Step 7 — Cards.** ✓ `scripts/rexcaped_stat_cards.py` `render_card_orange()` — orange canvas,
ink type, REXCAPED header, emblem. ⚠ Cards must be ≤6/chapter, hold ≤2.2s, and the spec
demands ANIMATED typewriter flashes (~27 chars/s + boiling emblem) — **still unbuilt**;
the pilot's static card holds are its one red style-gate axis.

**Step 8 — Render.**
```
venv/bin/python scripts/ffmpeg_production_render.py \
  --paper-edit storyboards/<video>_ch1_only.json \
  --narration audio/<video>/narration_..._ch1.wav \
  --output output/<video>_ch1_540p.mp4 --preview
```
⚠ GOTCHA (✓ verified at `ffmpeg_production_render.py:994`): unknown chapter names fall back
to the **Breaking-Law bed** `track_01_tense_ducked.wav`. Pick a creature-genre bed (owner
decision, still open) or you ship documentary music again.

**Step 9 — GATES (definition of done; never redefine in prose).**
```
venv/bin/python scripts/gate_ch1.py   --render <mp4> --paper-edit <json> --report out.json
venv/bin/python scripts/gate_style.py --render <mp4> --paper-edit <json>
```
✓ Both run today. gate_style enforces `research/style_bands.json`: events ≥25/min ·
max gap ≤6s · median shot 1.5–4s · static ≤40% · music ≥90% · cards ≤6 & ≤2.2s ·
CREATURE = zero flat stills. Then contact sheet (1 frame/~3.5s), **watch it yourself,
then show the owner a render — never a plan.** ✓ `scripts/preflight_ch1.py` = 33 green today.

**Step 10 — Package (the part that took 8 tries — read carefully).**
- **Title**: `I Simulated a {Creature} in {Modern Place}, {Consequence}` (owner may punch up).
- **Thumbnail — the verified formula** (vs their actual viral pixels, not memory):
  **CLEAN professional pen-and-ink illustration** — bold confident contours, controlled
  crosshatch, instantly readable silhouette. NOT scribble, NOT etching-sepia, NOT photo.
  Bright white creature on PURE BLACK void. Gaunt/hollow-eyed = the creep factor.
  **Plus a story element** (tiny human in peril / prey / scattering birds) — every viral one
  has stakes, creature-only says nothing.
  **Measured bands** (✓ from 8 viral thumbs): red word 33–47%w × 31–44%h, on the void,
  mixed case + period, **Impact font** (slight 1.08 h-stretch), pure red ≈ #E21010, thin black
  stroke; creature 22–32% of pixels, bleeding off 3–4 frame edges; void 48–66%; text-over-art ≤7%.
  Their go-to word is literally **"Run."**
  **Generation recipe**: ChatGPT, words like "clean professional pen-and-ink horror
  illustration, bold confident contour lines, controlled crosshatch, clear readable
  silhouette (NOT scribbly)". Guardrail notes: attaching their gory thumbnail = refusal;
  a text-free CROP of just the creature passes; "dead businessman" = refusal, "fallen/empty
  street" passes; output filter is stochastic — rephrase and retry once.
  Compose text in PIL (control > prompt-text). Template code lives in this chat's history;
  raw arts: ✓ `assets/trex_pilot/thumb_cleanink_raw.png` (+scratchboard, gaunt raws).
- **Description**: hook line → what the simulation covers → "NEXT PREDATOR? You pick —
  top comment wins." → AI-visuals disclosure → 3 hashtags (video #1's is the template).

**Step 11 — Upload (browser route; no API creds).** ✓ Verified working flow in memory
`project_rexcaped_launch.md`: Studio upload page → click Select files → drive the native
picker with AppleScript (`cmd+shift+G` + path + return ×2 into the sheet). Gotchas:
`fetch` to localhost dies on a hidden "local network access" permission bubble;
the `file_upload` MCP tool caps at 10MB and rejects project paths; thumbnails ≤2MB.

## 3 · Open items on video #1 (don't lose these)

1. **CH2/CH3 conversion** — back half is the old static edit + an AP-watermarked crowd clip.
   Same conversion CH1 got. Then re-render/replace the public video.
2. **Animated cards** (typewriter ≤2.2s) — the one red gate axis.
3. **Music bed decision** (owner) — kills the Breaking-Law fallback.
4. **Hook event top-up** (21.6 → ≥25 events/min).
5. **A/B test** — waiting on owner's advanced-features verification.
6. **Thumbnail story element** — owner said the current one feels like it's missing something;
   diagnosis: no stakes element; fix = tiny fleeing human added to the clean-ink art (one
   edit-generation, awaiting owner go).

## 4 · Hard lessons from this chat (each cost real time)

1. **Look at pixels, never at your description of them.** Four thumbnail failures came from
   generating off prose summaries; fixed only by pulling the actual viral images at full res
   and measuring them. Same lesson as render-as-truth.
2. **"Crude/scribbly" prompts produce noise.** Their art is *skilled clean inking*; horror
   lives in the design (gaunt, hollow eyes), not messy lines.
3. **Check the actual viral tier, not the newest uploads.** Recent ≠ most-viewed; sort/scroll
   the feed and rank by views before copying anything.
4. **The gate is the spec.** Every owner approval AND rejection becomes a band/check the same
   day (style_bands.json + gate_style.py); prose handoffs drift, numbers don't.
5. **Provenance beats memory.** Every approved artifact traces to a committed script+config;
   when "approved and rejected elements coexist," diff the build inputs, not vibes.
6. **YouTube gates stack**: phone verify → custom thumbnails; advanced verify (selfie/ID) →
   A/B testing. Surface them to the owner immediately; only he can clear them.

---

## ▶▶▶ PASTE THIS INTO THE NEW SESSION

```
Read NEXT_VIDEO.md, DESIGN.html, research/style_bands.json, and memory files
project_rexcaped_launch.md + feedback_style_gate_is_the_spec.md before doing anything.

We're making Rexcaped video #2 end-to-end: creature from video #1's comments (check
https://youtu.be/Dmmtwvx7qnE — top comment wins; if none, propose 3 on-formula picks
with title + thumbnail concept and let me choose).

Pipeline = NEXT_VIDEO.md section 2, no inventions: script (winner grammar, no-evolution/
no-dates) → my approval → ElevenLabs "Mark" VO → whisperx align → ChatGPT stills (one
conversation, viewer-download route) → rembg cutouts → composite_beat configs → render →
BOTH gates green (gate_ch1 + gate_style vs style_bands.json) → contact sheet you watched
→ only then show me, chapter by chapter.

Rules: the render is the only source of truth; never tell me "done" without both gates
green and a watchable file; never redefine done in prose; zero Ken-Burns creature stills;
cards ≤6 and ≤2.2s; creature-genre music bed (ask me to pick early); package per the
verified formula in NEXT_VIDEO.md step 10 (clean-ink thumbnail + story element, Impact
"Run."-style word, title formula).

Start by showing me the preflight result and the creature options.
```
