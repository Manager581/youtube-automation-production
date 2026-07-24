# Can we make our own Discovery-style 8–10 min version?

**Written 2026-07-23.** Everything below traces to a measurement in `GROUND_TRUTH.md`
or to the 8 research agents that completed. Where a claim is not verified, it says so.

⚠️ **Incomplete coverage:** the run hit the account's monthly spend limit. The
teardown (5 lenses) and market research (3 lenses) completed. The **capability audit
and the 5 adversarial verifiers did not run.** I did the capability work by hand
instead (repo greps + ffprobe + the EP02 ledger). Nothing here has been through the
refutation pass I planned, so treat the *plan* as unverified even though the
*measurements* are solid.

---

## 1. VERDICT

**Yes — and it is the right move, but not for the reason it looks like.**

The number that decides it: **an 8–10 min long-form needs 59,000–98,000 lifetime
views to hit YPP monetization. The Shorts path needs 10,000,000 views in 90 days.**
Primeval Atlas — with a 3.09M viral hit and 17.3K subs — has 5.93M in 75 days and
**zero long-form, so no watch-hour path at all. They are almost certainly not
earning ad revenue.** Long-form is not the ambitious route here. It is the only
arithmetically reachable one, by a factor of 100–170×.

**Cost to build one episode:**
| | |
|---|---|
| Clips needed | **60–75** at 8–9 s average (not 102–128 — see §5) |
| Generation cost | **$0** on Grok's free tier (their whole 71 s Short cost <$100) |
| Script | **750–820 words** for 9:00 — *not* the 1,620 a YouTube-paleo script would be |
| Realistic solo labour | **60–90 hours**, i.e. 2–3 focused weeks |
| Quality bar needed | **1080p24. Not 4K, not 60 fps.** See §2, finding 5 |

**The catch, stated plainly:** production is not your bottleneck and never was. You
have already shipped an 8:08 prehistoric video — it has **357 views and 2
subscribers.** Cold start is the binding constraint. Any plan that doesn't solve
distribution is a plan to make a second 357-view video.

---

## 2. WHAT ACTUALLY MAKES THE SHORT WORK — ranked, measured

**1. The title is the narration, and it states a violated expectation.**
Across all 13 uploads, the three whose titles state an expectation violation hold
**96% of the channel's 5.73M views**. "Used Gravity to Hunt" / "Even the mighty
Spinosaurus wasn't safe" / "Largest Claws on Earth". The misses are poetic or
encyclopedic — "The Last Hunt", "Giant Stalker of Early North America". In a
wordless film the title is the only sentence, and the film's whole job is to resolve it.

**2. The WORLD → REVEAL hook.** All three hits open on a wide, believable landscape
with the creature small, hidden or ambiguous (0–3 s), then cut or rise to it large
in frame (3–5 s). This is the *opposite* of standard Shorts advice. The first 1.5 s
of the Spinosaurus is functionally motionless. **The patience is the hook** — and it
works because a motionless mud-textured creature is the easiest thing a diffusion
model renders convincingly.

**3. One rule, taught then weaponised.** The film states a law — *what you read as
terrain is alive* — as a delight at 4.2 s, then re-applies the identical mechanic as
horror at 43.5 s. Hook mechanic and kill mechanic are the same mechanic. The
"predator becomes prey" reversal is the logline; the rule is the engine.

**4. Colour saturation IS the story arc.** Muted khaki swamp (12–28% sat) → vivid
cyan underwater (48–81%) → desaturated grey kill (19–33%). The grade does the job a
narrator's tone normally does.

**5. ⭐ Production quality is NOT one of the reasons.** Their 3.09M breakout is
**720×1280 at 24 fps** — the cheapest thing they ever uploaded. Five weeks later
they remade the same story under the same title at 4K60: **26,447 views, a 117×
collapse.** The 4K60 on the Spinosaurus is a Topaz veneer over 24 fps generation.
**Every hour spent on 4K, 60 fps or polish has a measured precedent that returned
nothing.**

**6. The craft trick worth stealing outright.** Creature-on-creature contact frames
average **64.0 mean luma vs 85.5** for clean single-subject frames — 25% darker,
plus foam and blur. They stage the money moment dark and occluded *because i2v
cannot render coherent multi-creature contact*. The failure is disguised as style.

**7. Cuts hidden inside one colour field.** My first pass measured "15 shots, 4.7 s
average, one 15.1 s unbroken shot". **Wrong** — there are 6 cuts inside that shot
(verified frame-by-frame, `stills/CUT_VERIFY.png`). Real structure is ~17–22 shots
at ~3.0–3.9 s. The detector missed them because the whole act is graded to one
narrow cyan band with one light direction. **This is the single most useful
production finding in the teardown** — see §5.

---

## 3. WHAT SURVIVES THE TRANSLATION, AND WHAT DIES

### Dies
- **Wordlessness as a monetization strategy.** Wordless AI long-form *does* pull huge
  reach — Primal Earth did **19.08M views on an 8:34 wordless AI film** — but it
  converts at **0.19% likes and 0.0029% comments**, and produced only 126K subs off
  19M views. Worse, YouTube's *"unsatisfying or off-putting content"* policy
  (clarified 2026-07-13) explicitly disallows *"disturbing themes without building a
  cohesive narrative."* **Narration is the policy armour, not a style choice.**
- **The 9:16 composition system.** The vertical water-column stratification (bright
  surface band / creature as a horizontal bar / dark void below) is the most
  9:16-native device in the film and has no 16:9 equivalent. Reframing is a
  re-shoot, not a crop.
- **Zero camera movement.** 70 s of locked-off frames reads as composed restraint;
  500 s reads as a slideshow.
- **4.5 s of silent black.** That's a loop device. Long-form has no loop.
- **Character drift.** The sail changes shape and colour across shots. At 3 s cuts
  with no narrator nobody checks. At 9 minutes with a narrator saying "this
  individual", every drift is a defect.

### Survives, and gets stronger
- The **WORLD → REVEAL** hook — budget 0–15 s instead of 0–5 s.
- The **one-rule** spine, paid off 3–5 times at escalating stakes.
- The **saturation arc** as a per-act grade (repo already has `research/style_bands.json`
  + `scripts/gate_style.py`).
- **Dark, occluded, short contact beats** — and they double as the policy fix
  (cap graphic predation at ≤12% of runtime; the Short runs 31%).
- **Dead space is free quality.** The acts with the most flat frame area are the
  best-looking; the busiest act is the ugliest.
- **Keeping the generator's per-clip audio.** They keep Veo's native clip audio and it
  *is* the sound design, for free. Our `EP02_GROK_GRIND_RECIPE.md` says
  *"Strip clip audio (`-an`) at assembly."* **We are throwing away a free layer.**

---

## 4. THE FORMAT — "Discovery Channel style" is a measurable contract

An agent pulled word-level caption timings from 9 broadcast natural-history episodes
(BBC Earth, Nature, Nat Geo, Shark Week) and 8 YouTube-native paleo videos. The two
cohorts **do not overlap on a single narration metric**:

| | Broadcast natural history | YouTube-native paleo |
|---|---|---|
| Narration duty cycle | **50.1%** median | **97.0%** median |
| Delivery rate over runtime | **77 wpm** | **180 wpm** |
| Silences > 10 s per episode | median 33 | **zero** |

**The unoccupied middle is exactly what "Discovery Channel style, 8–10 minutes"
describes.** Nobody makes it because historically 50%-pictures meant a camera crew in
a hide for six weeks; YouTube paleo channels talk continuously because talk is the
only thing they can afford to fill time with.

**We can afford pictures. That is the whole opening.**

### Episode template — 10:30 target (ship 10:00+ for mid-roll slots)
| Time | Act | Narration | Notes |
|---|---|---|---|
| 0:00–0:45 | **Cold open** | **NONE** | WORLD → REVEAL. Teach the rule wordlessly. Audio soft-in from −35 dB over 1.25 s. |
| 0:45–1:15 | Title / thesis | ~60 words | State the checkable claim the film will resolve |
| 1:15–3:30 | Act I — the animal | ~55% duty | Establish scale (see below), anatomy, habitat |
| 3:30–3:45 | Act break | none | Music out, 1.5 s near-silence |
| 3:45–6:00 | Act II — the descent | ~50% duty | **The saturated act.** Deepest lowpass. VO-free at the deepest point |
| 6:00–6:15 | Act break | none | |
| 6:15–8:30 | Act III — the turn | ~45% duty | The hush 5–7 s before the climax; contact beats ≤2.0 s each |
| 8:30–10:00 | Act IV — consequence | ~40% duty | Longest holds on the *best-rendering* shots |
| 10:00–10:30 | Close | ~50 words | Final shot re-composes the opening frame, one variable changed |

**Script: 750–820 words total.** At 46% duty cycle and 178 wpm speaking rate. The
YouTube-paleo default (~1,800 words) is exactly 2× too long and produces an Eons
video, not a Discovery one.

**Silence budget:** ~30–35 pauses ≥1.5 s, of which 6–8 exceed 3 s and 1–2 exceed 10 s.

**Two non-negotiables the teardown surfaced:**
1. **Never narrate over a fully-submerged beat.** The underwater illusion is created
   by pulling 2–12 kHz down ~45 dB; VO intelligibility lives at 1–4 kHz. Narrating
   there destroys the single best effect in the film. Write the script so the
   deepest-filtered passages are VO-free.
2. **Plan a scale reference in every act.** Only 1 of 22 shots has one, and the whole
   open-ocean act has none — the creature reads ~3 m in one shot and ~15 m in the
   next. A Short survives that. A narrator saying "fifteen metres, seven tonnes" over
   a scale-free animal gets called out in the comments.

---

## 5. PRODUCTION PLAN — against tools that already exist

**Do not build anything new.** Per CLAUDE.md hard rule 3, these already exist:

| Need | Existing tool |
|---|---|
| Shot manifest → assembled cut | `research/wildbirdsurvival_teardown/assemble_ep02.py` |
| Style/colour gate | `scripts/gate_style.py` + `research/style_bands.json` |
| Shot gate | `research/wildbirdsurvival_teardown/gate_shots.py` |
| Final render | `scripts/ffmpeg_production_render.py` |
| Auto-QA | `scripts/verify_render.py` |
| Edit grammar | `scripts/rexcaped_edit_engine.py` + `research/edit_grammar_ruleset.md` |
| i2v generation | `research/wildbirdsurvival_teardown/EP02_GROK_GRIND_RECIPE.md` |
| Frame-strip QA | `research/wildbirdsurvival_teardown/make_clip_strip.py` |

### The clip-count solution
Naive math: 600 s ÷ 3.86 s average = **155 clips**. That is the number that kills the
project. Three measured levers cut it to **60–75**:

1. **Design for 8–9 s average, not 3.9 s.** Nature-doc grammar tolerates it; the
   market research confirms 8–9 s is the long-form norm. → ~67–75 clips for 10:00.
2. **Grok yields 6.04 s; retime to 0.7× for 8.6 s** on motion that suits it —
   drifting, sinking, gliding. Nature docs use slow motion constantly.
3. **One colour world per act.** This is the big one. Because Primeval Atlas's cuts
   are invisible inside a single graded hue band, **you do not need shot-to-shot
   continuity — you need one light direction, one hue band and one haze setting per
   act.** Our 6 s no-continuity clips stop being a limitation.

**And 30–50% of runtime should not be generated at all.** ExtinctZoo (1.48M subs) and
Moth Light Media (508K) run almost entirely on credited paleoart stills, museum
photos, masked cut-outs, label bars and a geologic-timescale bar. That layer is
cheap, looks *more* authoritative than i2v, and is where narration breathes. It also
solves the scale-reference problem and the accuracy problem at once.

### Audio architecture
- Master **−15.0 LUFS**, true peak −1.5 dBTP, **LRA 9–11** (the Short's 15.9 is
  unreachable with narration; 5–6 is the crushed look to avoid).
- VO stem inside the mix at **−18 LUFS** (not the −16 standalone default in
  `scripts/audio_master.py`).
- **Band-split ducking**, not broadband: low bus 20–200 Hz **never ducked**; mid/hi
  bus ducked −6 dB with 80 ms attack, 400–600 ms release. Broadband ducking is what
  destroys the piece.
- Music ~45–55% coverage, **absent by default**. Not wall-to-wall.
- Keep per-clip generated audio; crossfade only the low bus across cuts.

---

## 6. PROVE IT FIRST — the cheapest test of the riskiest assumption

The riskiest assumption is **not** "can we generate clips" (proven) or "can we
assemble" (proven). It is: **does one-colour-world-per-act actually make our 6 s
Grok clips cut together invisibly at 1080p 16:9?** Everything in §5 rests on it.

**The 60-minute test — build ONE act, not one episode:**
1. Pick the underwater act. Generate **6 clips** with an identical grade instruction
   (one hue band, one light direction, one haze depth) and deliberately *unrelated*
   staging.
2. Assemble with `assemble_ep02.py`, retime two of them to 0.7×.
3. Run `gate_style.py` against a single-band `style_bands.json` entry.
4. Watch it. **Can you see the cuts?**

If the cuts disappear → the whole plan holds and clip count is 60–75.
If they don't → we are back to 155 clips and the episode is a 3-month project, not a
3-week one. **Find that out for the price of 6 clips.**

Second cheap test, in parallel: **write the 800-word script first and time it.** If
you can't tell the story in 800 words at 46% duty cycle, the format is wrong before
a single clip is generated.

---

## 7. TOP 5 RISKS

| Risk | Mitigation |
|---|---|
| **Cold start.** 2 subs, 357 views on your last 8:08. Every long-form winner measured had a feeder. | **Cut one clip library two ways.** The 60–72 s wordless cut is the proven reach engine (3 hits, 1.09–3.09M); the 8–11 min narrated cut is the watch-time engine. Same assets, two deliverables. Ship 3–4 Shorts per episode. |
| **"Inauthentic content" enforcement.** Policy clarified 2026-07-13 disallows repeated disturbing themes without cohesive narrative. Primeval Atlas is 13/13 the same predator-kills-prey template. | Narration + one thesis per episode + **vary the outcome across episodes** (not every animal dies). Category = **Education/Science**, not Entertainment (also $5–18 RPM vs $1–5). |
| **Made-for-kids misclassification.** DinoMania (1M+), Blunt Brothers (1.3M), SlicK (825K) were all demonetized 2026-02-11 with dinosaur content — human-made, not AI. | Never self-mark MFK; build adult signal (sourced narration, scientific register). This risk is about *dinosaurs*, not about AI. |
| **Accuracy becomes a liability at length.** The top comment (391 likes) refutes the Short's premise — Spinosaurus and Mosasaurus are separated by tens of millions of years. | **This is our differentiator, and it's free** — it's research time, not render time. Get it right, cite on screen. Drop all franchise hashtags (#JurassicPark, #PrehistoricPlanet — trademark risk that scales with success). |
| **Format half-life ~4–6 uploads.** sacredstuff ran one template six times: 3.1M, 4.3M, 3.9M, 7.6M, then 321K, then 70K. | Don't build a business on one template. And **never re-cut and re-upload a winner** — measured 118× collapse. |

---

## 8. THE DECISION

**Option A — Finish Wild Bird Survival Ep02 first.** 87 clips still to generate, but
the script, VO, packaging and assembler are all locked and proven. Lowest risk to
shipping *something*. Doesn't test the new format.

**Option B — Build the Spinosaurus/marine-reptile 10:30 episode on Prehistoric POV.**
Highest upside: it's the only arithmetically reachable monetization path, it targets a
genuinely unoccupied format gap, and the accuracy angle is a real differentiator.
Costs 2–3 weeks and competes with Ep02 for the same scarce resource — your clip
generation time.

**Option C — Run the 60-minute prove-it test in §6 first, then decide.**

**Recommendation: C, today.** It costs 6 clips and one hour. It resolves the single
assumption that separates "3-week project" from "3-month project," and its answer
changes which of A and B is correct. Committing to either before running it is
guessing at the one number that matters.
