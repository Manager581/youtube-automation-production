# Spinosnack Winning Formula — Evidence-Based Teardown
*Top 5 vs Bottom 5 (last 12mo, age-normalized by views/day) + Top 3 recent. 13 videos, 14-agent analysis. Full data: `spinosnack_analysis_report.json`.*

## The one-line finding
**Packaging beats execution ~376×.** Median winner = **16,350 views/day**, median loser = **43**. The gap is driven almost entirely by **three packaging choices — topic, thumbnail style, format — not by in-video craft.** (Losers actually cut *faster* and have *higher* motion than winners.)

## Winners vs losers at a glance
| Lever | WINNERS (8) | LOSERS (5) |
|---|---|---|
| Topic | original prehistoric creature (8/8) | movie/IP creature — "D-Rex", "Movie T-Rexes" (4/5) |
| **Thumbnail** | **hand-drawn pen-&-ink B&W horror + ONE red doom-word (8/8)** | **color cartoon "versus / God-Tier / Pathetic" comparison (5/5)** |
| Format | 2nd-person POV survival-sim (6/8) | countdown listicle + talking-head face-cam |
| Hook | brandless cold-open, 3-4 stacked stats, POV flip <15s | 3rd-person, or self-deprecating hedge in first 15s |
| Production | unified color grade, original AI/3D + real footage | un-graded mix, webcam face-cam, watermarked stock |
| Series | teases NEXT creature in CTA (6/8) | dead-ends (0/5) |
| Cut rate | ~5.9s avg (table stakes, NOT the edge) | ~2.5s avg (faster ≠ better) |

## The 13/13 rule (highest leverage)
**THUMBNAIL is a perfect predictor.** Hand-drawn pen-and-ink / pencil **crosshatch**, near-monochrome **black & white**, creature looming (jaws agape, glowing eye), on near-black, with **exactly 1-4 words of absolute doom, the alarm word in saturated RED** ("Run.", "Death.", "Nothing Survives", "Everything Dies", "We Can't Explain"). Period-punctuation adds finality. It deliberately **pattern-breaks the glossy AI-CGI-shark thumbnails** flooding the niche.
**NEVER** ship a color split-screen "versus", tier-rating ("God Tier" vs "Pathetic"), or judgment thumbnail — that's the 5/5-loser tell.

## Winning title formulas
1. **`I Simulated A [Iconic Extinct Creature] In The Modern [Vivid Place], [Chaos Followed / It Was Brutal]`** — the flagship (4 of the sim winners). Round-number variant: "I Simulated 1000 Megalodons…".
2. `The Deeper You [Go / Look Into ___], The [Creepier/Stranger] It Gets` — reusable, built-in escalation; best for non-creature topics (oceans, amber, eras).
3. `What Happens If You Drop [creature] Into [specific modern place]` / `How It Feels To Die In Every ___` — driving-question + local-threat framing.
Pick the **single most iconic** creature (T.Rex, Megalodon) for 5-second-title legibility. **Avoid obscure/IP creatures.**

## Script architecture
- **Cold open, ZERO branding** — first sentence IS the hook. Stack **3-4 escalating hard stats in 15-25s**.
- **Flip to 2nd-person FAST (<15s, ideally ~5s) and STAY** — "you ARE the creature" (winners: 200-817 "you/your"). Single biggest script differentiator.
- **≥2 open loops** planted in the hook, paid off with explicit verbal callbacks ("a concern for later", "spoiler: it doesn't go well"). Withhold the **title's answer to the final seconds**.
- **Survival-clock spine** with timestamped beats ("Day one", "One year later") — birth→juvenile→hunting→adulthood→death.
- **Relentless concrete numbers** (kg, m, PSI, °C, days) as life-or-death stakes, not lecture = the "simulation" credibility.
- **Tonal whiplash**: dry-comedic asides + 1-2 pop-culture meme cutaways reset attention.
- **~195 WPM** (185-205). **Duration 18-26 min** (winners avg ~25) — earn it with the clock, don't pad.
- **Stacked CTA that feeds the series** — engagement-bait question that doubles as next-creature sourcing (+ optional 10k-like vote). MUST tease the next creature.

## Visual + audio
- **Mixed-media stack** so the screen never goes static: AI/LTX i2v creature + real stock/drone + 3D renders + stat-text cards. The high-end look = **photoreal creature composited into real footage**.
- **Unified color grade** (cold teal-blue underwater OR warm golden-hour). Incoherent grade = loser tell.
- **High motion + music bed are table stakes** (both buckets clear them). Keep screen alive ~75-90% motion via slow pushes/morphs, hard-cut ~3-5s. **Do NOT chase ultra-fast cutting.**
- **Wall-to-wall cinematic doom bed, ~95% active, zero silence** + layered ocean/impact SFX + accent whoosh on reveals.
- **Faceless, original-footage-only.** NO webcam face-cam (4/5-loser tell), NO licensed movie/game clips, NO watermarked stock.

## Current trends (last 3 months — adopt these)
- 3rd-person **"I Simulated 1000 X"** with **named protagonists** (the Matriarch, the Wanderer) + flash-forward loops.
- **Real-news-peg hooks** tied to newly-described species ("they just discovered Spinosaurus mirabilis, 17m").
- **Local/modern settings** ("Florida Everglades, 2026") so the creature feels like a present-day local threat.
- Rising **stat-card overlays** and **photoreal AI-in-real-plate** compositing.
- The **ink-horror thumbnail is the one thing NOT changing** — keep it locked.

## → Dunkleosteus build spec (what to actually do)
- **Title:** ✅ keep `I Simulated A Dunkleosteus In The Modern Ocean, It Was Brutal` (on-formula).
- **Thumbnail:** ❌ SWAP from the glossy composite (loser style) → **hand-drawn ink crosshatch Dunkleosteus, jaws agape, tiny diver in a god-ray for scale, one red word "Brutal." / "Run."** Build the ink hero in Photoshop over an LTX still.
- **Script:** ✅ POV survival arc is right. Tighten: brandless cold-open with 3-4 stacked stats, POV flip ~5-10s, ≥2 open loops, survival-clock with day-markers, ~195 WPM, withhold the "huge catch" to the end, CTA teases the next creature.
- **Visuals:** LTX i2v creature **composited into real cold-ocean stock**, unified teal grade, ~75-90% motion, ~3-5s cuts (don't over-cut), stat-cards. NO face-cam / licensed clips.
- **Audio:** cloned F5 voice (`--wpm-normalize`), wall-to-wall doom bed, layered SFX.
- **Pipeline (proven):** `voice_generator.py` → `tools/ltx-video` i2v → `ffmpeg_production_render.py` → `verify_render.py`.
