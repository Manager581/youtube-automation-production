# Replication Plan v1 — matching @wildbirdsurvival with ChatGPT + Grok + Claude + ElevenLabs
_Honest calibration + the exact pipeline I'd run. Prototype-gated per project hard rules._

## What "100%" actually means (three layers, three different certainties)
| Layer | Can I match it? | Confidence |
|---|---|---|
| **Editing grammar / house style** (cut cadence, holds, narration density, no-SFX mix, voice profile, structure, outro) | Yes — measured to the numeric target and assembled by our existing FFmpeg renderer. | **~95–100%. Proven.** |
| **Visual look** (the photoreal nature-doc frames) | They use **Google Veo**; you have **Sora (ChatGPT)** and **Grok Imagine i2v**. Both make photoreal wildlife, but each has its own signature — not guaranteed pixel-identical to Veo. | **~85–95%, UNPROVEN until we prototype.** Exact Veo match = add Google AI Pro (~$20/mo). |
| **Virality** (best-vs-worst outcome) | **No one can guarantee this.** It's the topic/title/thumbnail/timing bet. Their own near-clone flopped to 3K vs 1.98M. | **Not promisable.** We stack odds, we don't guarantee hits. |

So the honest promise: **I can make videos that are stylistically indistinguishable from theirs (pending one prototype to confirm the visual layer), and I can maximize the odds of virality — but "recreate viral videos 100%" is two claims, and only the "recreate the style" half is a guarantee.**

---

## PHASE 0 — Prototype gate (do this BEFORE any full video; ~1–2 hrs)
Per our hard rule (prototype before plan, no spend before a verified test on real assets):
1. Pick one real winner shot as the target (e.g. the buffalo tick-macro from `BEST`, already on disk).
2. Generate ONE hero reference still (ChatGPT image gen or Grok) of a Cape buffalo covered in ticks.
3. From that still, generate the SAME 8s i2v clip in **both Grok Imagine and Sora**.
4. Compare side-by-side against the real Veo frame (`hookstrip_best.jpg`).
5. **Decision:** if Grok or Sora is "close enough" → we own the whole stack, $0 extra. If neither matches
   and the look matters → prototype 3 Veo clips on Google AI Pro before committing the $20/mo.
6. Assemble a **30-second vertical slice** (4 clips + ElevenLabs VO + Pixabay bed) through
   `scripts/ffmpeg_production_render.py` and run it past the 13 QA gates. This proves the ENTIRE chain
   on one real sample before we scale to a 60-clip video.

**Go/no-go:** only proceed to full production if the vertical slice passes the style gates AND the
visual look is acceptable. This is the guarantee-vs-hope line.

---

## THE PIPELINE (tool-by-tool, once Phase 0 passes)

### Step 0 — Lock the click (Claude) — *this is where the win actually lives*
- Claude generates 10 topic candidates that pass the gate: **two animals, one surprising
  relationship, a curiosity-gap or stakes**. Ban "full life cycle" and single-common-species.
- For each: a curiosity/conflict **title** and a **thumbnail concept** (extreme close-up +
  2–3 shock words). Pick the strongest. Don't clone a recent hit.

### Step 1 — Script (Claude)
- Present-tense narration to the **verified word budget: ≤1.5 × runtime-seconds** (9-min video ≈
  ≤810 words, ≤~4.5 min of speech, 45–55% wordless).
- 5-beat structure: cold-open jeopardy → escalation → the turn → held payoff → one-line theme.
- First sentence names one animal + its threat. **No encyclopedic opener.**
- Output as ~60 shot-lines (1 sentence ≈ 1 clip) + a visual direction per line + marked `[PAUSE]` /
  `[MUSIC ONLY]` beats. (Prompt template in `PROMPT_TEMPLATES.md §B.`)

### Step 2 — Reference stills (ChatGPT image gen or Grok)
- ONE photoreal hero-animal still (locks identity across all clips) + key scene stills.
- Use `PROMPT_TEMPLATES.md §C` recipe. **Real photos for any real human faces** (project rule — AI
  human likenesses get rejected); this content is all animals, so AI is fine.

### Step 3 — i2v clips (Grok Imagine and/or Sora — whichever won Phase 0)
- ~50–60 clips of ~8s, image-to-video seeded from the hero still for consistency.
- Hook shots: open ON the face/macro; shock detail by ~2s; B-roll literally illustrates the words.
- One long held "money shot" of the payoff behavior.
- **Throughput reality:** 60 i2v gens/video is heavy at 1/day. Expect this to be the bottleneck;
  plan cadence around your Grok/Sora generation limits (may mean 2–3 videos/week, not daily, at start).

### Step 4 — Voice (ElevenLabs)
- Deep male documentary voice (~80–90 Hz), **high Stability**, speed ~0.9–1.0, **~150 wpm**.
- One pass over the LOCKED script (project rule). Not bright/hyped (190 wpm = the flop).

### Step 5 — Music (Pixabay only)
- One continuous cinematic bed, 12–20 dB under VO, **constant level — no auto-ducking swells.**

### Step 6 — Assemble (our existing `scripts/ffmpeg_production_render.py`)
Hit the measured edit targets (do NOT invent a new assembler — hard rule):
- Median shot 3.6–4.7s, mean 5.6–7.1s, ≤48% of shots ≤3s.
- Hook = 9–11 cuts in 0:60, mean ≥5s.
- 3–5 payoff holds of 15–35s (near-wordless); 13–19 holds of 10s+.
- One action burst (6–12 sub-2s cuts) bracketed by holds; ≥1 wordless gap >25s.
- **No transition SFX.** Cut on on-screen action, a beat off narration. Energy peak in first 30%.
- No burned-in captions. Golden-hour philosophical outro.

### Step 7 — QA (`scripts/verify_render.py` + the 13 gates)
- Auto-check the numeric gates in `PROMPT_TEMPLATES.md §G.13`. Frame-strip QA every i2v clip for
  physics/anatomy glitches before it ships (project rule). Fail → re-cut/re-gen.

### Step 8 — Thumbnail + package
- Thumbnail: ChatGPT/Grok close-up + 2–3 words (yellow/white, thick black outline).
- Title: curiosity/conflict. Description: one story paragraph + 3 hashtags. **Strip scaffolding.**

---

## Cost & effort (rough)
- **Tools you already have:** ChatGPT Plus (~$20), Grok (~$30 via SuperGrok/X), ElevenLabs (~$22),
  Claude, Pixabay (free). **Marginal cost per video ≈ $0** beyond subscriptions if Phase 0 passes on
  Grok/Sora.
- **Optional:** Google AI Pro (~$20/mo) ONLY if Phase 0 shows we need real Veo for the look.
- **Time per video after prototype:** ~4–8 hrs of mostly-unattended generation + ~1 hr assembly/QA.
  The i2v generation queue is the real constraint, not skill.

## The honest bottom line
- **Style:** I'll match it, and the vertical slice will prove it before you commit real time.
- **Visuals:** ~90% with your current tools; Phase 0 tells us if we need the $20 Veo add-on for exact.
- **Virality:** I'll stack every odd (topic, title, thumbnail, no self-cannibalization), but that's a
  bet every time — theirs included. Anyone who promises you guaranteed viral is lying.
