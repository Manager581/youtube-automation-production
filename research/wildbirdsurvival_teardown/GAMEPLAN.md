# @wildbirdsurvival — Reverse-Engineering Teardown + Replication Gameplan
_Analysis date: 2026-07-21 · 26 videos · channel age ~30 days · 13.2K subs_

## TL;DR
This is a **faceless AI wildlife-documentary channel** built on **Google Veo (Gemini)** clips
+ a TTS narrator + a music bed, assembled into 8–13 min "life-cycle / survival-story"
documentaries, shipped **~1 video/day**. Production is **identical** across their best and worst
videos — the visual quality of the 1.9M-view smash and the 1.8K-view flop is the same. **The
entire performance gap is topic + title + thumbnail (the click), not production.** You can
reproduce their exact style with Claude (script/titles) → Grok or Veo (i2v clips) → ElevenLabs
(voice) → your existing FFmpeg renderer. Their Veo look is the one piece your current toolset
only *approximates*; matching it exactly means adding Google Veo access.

---

## 1. How the video is actually made (the pipeline)

Confirmed by frame extraction, scene-cut analysis, transcription, and description scraping of
the top video (`oqC5OVJhSj0`, 1.98M views) and a flop (`E25r4nwHU9A`, 1.9K).

| Layer | What they do | Evidence |
|---|---|---|
| **Visuals** | 100% AI, **Google Veo** image-to-video. ✦ Veo sparkle watermark visible bottom-right of frames. Photoreal "8K nature-doc" look. | Watermark in `hookstrip_best.jpg`; description literally says _"stunning 8K documentary realism"_ |
| **Shot count** | ~60+ distinct clips per 8-min video, each a Veo 8-second generation, trimmed and cut on narration beats (effective ~3–6s on screen). | `contact_best.jpg` = 96 frames @5s, every one a new shot; scene-cut cadence |
| **Consistency** | Same "hero" animal holds across dozens of clips → they seed Veo from a **reference still** (i2v), not text-to-video. | Buffalo identity stable across 480s |
| **Narration** | Single calm male documentary voice, present-tense, continuous over the whole runtime. British spelling in script ("colour", "metres"). TTS-grade smoothness. | Whisper transcript of both videos |
| **On-screen text** | **NONE inside the video.** No captions, no lower-thirds, no chapter cards. Clean cinematic. All the "selling" is in thumbnail + title only. | No text in any of 96+ frames |
| **Music** | Soft orchestral/ambient bed under narration, low mix. | Audio track |
| **Structure** | Cold-open jeopardy → escalation → turn/payoff → relationship/life-cycle exposition → golden-hour sunset outro. | Story arc across contact sheet |
| **Package** | Title + description + hashtags are LLM-generated. The flop's description still contained the raw template header `[VIDEO DESCRIPTION — PASTE INTO YOUTUBE STUDIO]` — proof they batch-generate packages with an LLM and sometimes ship the scaffolding. | `desc/1879_*.description` |

**The story spine (every winner follows it):**
1. **0–15s cold open** — a specific individual animal in visceral distress (ticks, predator, cold). Macro close-ups. No preamble.
2. **Escalation** — "it tried everything… nothing worked."
3. **The turn** — an unexpected savior/partner appears ("Finally, the buffalo walks into a river…").
4. **Payoff** — the remarkable behavior/symbiosis, shown in the middle third (the "money" sequence).
5. **Exposition** — broader life-cycle / relationship facts.
6. **Golden-hour outro** — wide sunset shot, "without a single human intervention," subscribe CTA.

---

## 2. Best 5 vs Worst 5 — what actually differs

**Best 5 (by views):**
| Views | Age | Title | Thumbnail text |
|---:|---:|---|---|
| 1,984,363 | 13d | Hundreds of Fish And Oxpecker Clean Thousands of Parasites Off This Buffalo | **1000+ PARASITES GONE!** |
| 939,961 | 10d | Why This Warthog Lets Mongooses Crawl All Over Its Face | **TOO MANY TICKS!** |
| 855,377 | 7d | Survival of the Fittest \| Mongoose vs. Spitting Cobra – Fight to the Death | **FATAL MISTAKE** |
| 674,534 | 5d | Why Do Hornbills Wake Sleeping Mongooses Every Morning? | (curiosity Q) |
| 653,959 | 20d | What Happens When Africa's Biggest Giants Depend on a Tiny Bird? | **IMPOSSIBLE TEAM** |

**Worst 5 (by views):**
| Views | Age | Title | Thumbnail text |
|---:|---:|---|---|
| 1,879 | 28d | The Reaper's Dive at 320 km/h … Peregrine Falcon **Full Life Cycle** | **DEATH STARE** |
| 3,041 | 12d | This Hippo Was Losing the Battle Against Ticks… Until the River **Saved It** | **SAVED BY FISH!** |
| 13,095 | 29d | This Bird Drinks Blood From Live Animals \| **Full Life Cycle Of The Oxpecker** | — |
| 26,720 | 27d | The Tiny Bird That Giant Hippos Owe a Lifetime of Gratitude \| **Full Life Cycle** | — |
| 34,666 | 16d | Can One Tiny Oxpecker Really Protect a Giant Buffalo? | **LIVE IN THE EAR!** |

**The differences that matter (production is NOT one of them):**

1. **Topic novelty / curiosity gap.** Winners pair **two animals in unexpected conflict or
   partnership** — "fish clean a buffalo," "warthog lets mongooses on its face," "mongoose kills
   a cobra," "hornbills wake mongooses." Losers are **single-species portraits** ("Peregrine
   Falcon," a bird everyone already knows is fast → "DEATH STARE" is just a bird looking at camera).

2. **"Full Life Cycle" framing = death.** 3 of the 5 losers use encyclopedia framing ("Full Life
   Cycle Of…"). Zero winners do. Winners use **curiosity questions** ("Why does…", "What happens
   when…", "Who needs who?") or **conflict/stakes** ("Fight to the Death", "Fatal Mistake").

3. **Topic fatigue / self-cannibalization.** The channel opened with **~13 straight oxpecker
   videos** — nearly every loser is an oxpecker video buried in that monotony. Views exploded only
   once they **diversified** into mongoose / warthog / honey badger / cobra. The 3K hippo
   "SAVED BY FISH!" is a **near-clone of the 1.9M buffalo winner published one day apart** — the
   algorithm crowned one and starved the duplicate. _Lesson: don't clone your own hit with a
   weaker animal in the same week._

4. **Engagement paradox proves it's a click problem.** Losers actually have **higher** like-rate
   (14‰ vs 9.7‰) and comment-rate (2.5‰ vs 0.2‰) than winners. The few people who found the flops
   liked them fine — the algorithm just never pushed them because the **title/thumbnail/topic
   didn't earn the click**. This is decisive: fix discovery, not production.

5. **Description quality.** Winner = tight story ("What happens next is one of nature's most
   remarkable cleaning partnerships"). Loser = generic listicle with template scaffolding left in.

**Thumbnail formula (winners):** 2–3 word shock/curiosity text in bold **yellow/white with heavy
black outline or a black bar**, over an **extreme close-up of an animal face, gore, or two-animal
conflict**. High saturation, high contrast. See `best5_thumbs.jpg` vs `worst5_thumbs.jpg`.

---

## 3. The replication gameplan (with YOUR tools)

You have Claude, ChatGPT, Grok, ElevenLabs, and the FFmpeg renderer already built in this repo.
The only gap is Veo's exact photoreal look.

### Step 0 — Topic selection (the highest-leverage step; do NOT skip)
Pick topics that are **two-animal conflict or surprising symbiosis** with a **curiosity-gap
question or stakes**. Bank ideas that pass this gate:
- Two named animals, one relationship, one surprise ("Why does X let Y do Z?").
- Never "Full Life Cycle of [single common animal]."
- Don't repeat the same hero animal more than ~2 videos in a row.
- Don't clone your own recent hit with a weaker stand-in the same week.

### Step 1 — Script (Claude)
Prompt Claude for a 1,100–1,400-word present-tense narration following the 6-beat spine in §1.
Rules: visceral sensory cold open on ONE individual in distress within the first sentence; a
mid-video "turn"; a golden-hour resolution; British doc-narrator register. Output as ~60 shot
lines (one sentence ≈ one clip) so it maps 1:1 to Veo generations.

### Step 2 — Reference stills (Grok Imagine / ChatGPT / Gemini image)
Generate a **hero-animal reference still** + key scene stills. Reuse the hero still as the i2v
seed so the animal stays consistent across clips (matches their consistency trick). This repo
already has the still→i2v workflow (`reference_grok_i2v_clipboard_upload.md`,
`reference_dinoverse_veo3_workflow.md`).

### Step 3 — Clips: image-to-video (~60 × 8s)
- **To match their look EXACTLY:** use **Google Veo** via Gemini / Google Flow (Google AI Pro or
  Ultra). This is the one tool that produces their specific photoreal nature-doc quality and the
  ✦ watermark you spotted. _This is the one paid add-on I'd recommend — prototype 3 clips before
  committing (per your no-spend-without-prototype rule)._
- **To approximate with what you own:** **Grok Imagine i2v** (your proven dino-channel workhorse)
  or **ChatGPT Sora**. Slightly different grain/motion, but same format. Test one 8s clip of a
  buffalo-with-ticks and eyeball it against `hookstrip_best.jpg` before scaling.
- Generate one clip per script line; keep on-theme; favor macro close-ups + conflict moments.

### Step 4 — Narration (ElevenLabs)
One calm male documentary voice, single pass over the locked script (your ElevenLabs one-pass
rule). Match their register: measured, warm, present-tense. Use `--wpm-normalize` per project rule.

### Step 5 — Music (Pixabay only — project rule)
Soft orchestral/ambient bed, mixed low under VO. No Pexels/Pixabay images — **music only**.

### Step 6 — Assemble (your existing FFmpeg renderer)
Use `scripts/ffmpeg_production_render.py`. Cut clips on narration beats (~3–6s effective on
screen), trimming the 8s Veo outputs. **No burned-in captions** — keep it clean like they do.
Golden-hour wide as the final shot. Then QA with `scripts/verify_render.py`.

### Step 7 — Package (Claude)
- **Title:** curiosity question OR conflict/stakes. Never "Full Life Cycle." Front-load the
  surprising pairing.
- **Thumbnail:** generate the close-up in Grok/ChatGPT, then overlay **2–3 words** (yellow/white,
  thick black outline) — "FATAL MISTAKE" energy. This repo has thumbnail recipes
  (`feedback_dinoverse_thumbnail_style.md`).
- **Description:** tight story paragraph + 3 hashtags. **Strip any template scaffolding** before
  upload (their flop shows what happens when you don't).

### Step 8 — Cadence & discipline
Ship frequently (they do ~1/day), but **diversify hero animals** and **kill "life cycle"
framing**. Track which topics broke out; double down on the *format* (two-animal surprise), not
the same *animal*.

---

## 4. One-line verdict
Their moat is **topic selection + packaging + volume**, not secret tech. The tech is Veo + TTS +
FFmpeg — you already run the equivalent of two of those three, and Veo is a cheap, prototype-first
add-on. Win by picking better two-animal curiosity-gap topics and out-packaging them.

_Reference assets in this folder: `best5_thumbs.jpg`, `worst5_thumbs.jpg`, `hookstrip_best.jpg`,
`contact_best.jpg`, `wbs_meta.tsv` (full 26-video metrics)._
