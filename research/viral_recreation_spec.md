# Viral Recreation Spec — the measured anatomy of the top performer (v1, 2026-06-10)

What must be true, all together, for a Rexcaped video to read like DzUKhb2ZSko
("I Simulated A T.Rex In Modern Africa" — 1.25M views, 16,874 views/day).

**Sources of truth** (all measured, not guessed):
`research/edit_analysis/trex_grammar.json` (532 hard cuts) ·
`research/edit_analysis/trex_motion_events.json` (per-frame motion, 274 within-shot
events, onsets, beat grid) · the all-532-shot frame watch + Tier-2 dense-grid anatomy
(2026-06-10 session) · the loser control (`chaostheory_trex_amazon_grammar.json`,
556-view copycat that cloned packaging but none of the below — and died).

## 0. The one-line model
A second-person survival STORY told as a fast collage where **every sentence gets a
literal visual punchline, almost nothing on screen is ever still, every movement has a
sound, and a comedy layer rhymes with the story's failures.** The creature is a
minority garnish (~20-25% of shots); the texture is the star.

## 1. The ten laws (each with its measurement)

1. **Event rate, not cut rate.** Hard cuts 18.5/min are HALF the texture: total visual
   event rate ≈ 28/min (hook: 36/min). Median gap between on-screen changes **1.77s**;
   p99 7.3s; only 5 gaps >8s in 28.8min (deliberate: skit dialogue, CTA). 91% of
   runtime sits within 4s of an event. RULE: nothing >6s without something changing.
2. **Tempo is modulated, not metronomic.** Median shot 2.85s; 15%<1s; 17.5%>5s.
   Bursts are mostly FRENETIC INSERTS (a Looney-Tunes-grade kinetic clip whose internal
   motion reads as 10+ cuts/s), not hand-spliced frames. Cards/skits provide the slow pole.
3. **(Almost) nothing is still.** 76% of shots have continuous internal motion
   (drift/alive/kinetic classes); the 24% "static" shots are brief punched cards/stills
   (median 3.3s). Motion floor in "held" shots ≈ sway/bob/track, not freeze.
4. **Motion is sound-designed.** 90.1% of within-shot motion events land ≤0.15s from a
   percussive onset; ~95% of cuts carry a hit. Cuts do NOT snap to the music beat grid
   (32% within 0.1s ≈ 36% random) — sounds are PLACED ON events, events follow speech.
5. **Music is wall-to-wall.** Bed active 91% of runtime (~108 BPM average across one
   coherent grid, 3,102 beats). Loser matched this (97.6%) and still died — necessary,
   not sufficient.
6. **Script-noun literalism.** The visuals illustrate the script noun-by-noun:
   "shell"→egg cracks, "air…straw"→O₂ molecule graphic bobs in, "math is simple"→man at
   whiteboard, "ferns"→ferns macro, "legs"→legs isolate → SpongeBob fancy-legs gag.
   Every sentence gets its image; b-roll is never mood wallpaper.
7. **Asset mix + comedy clustering.** ≈ stock 40% / comedy 25-30% / creature 20-25% /
   graphics ~10%. Comedy in 3 length classes — flash (<0.5s: emoji, Sonic, Batman),
   GIF (1-3s: WELP/I QUIT/PERFECT/Trump-WRONG), full scene (5-20s+: South Park,
   Forrest Gump, DeVito, a ~20-shot two-actor sketch) — and it CLUSTERS on
   failure/humiliation beats, often rhyming the previous shot's literal noun.
   The 556-view loser shipped 0% comedy. This layer is not optional.
8. **A branded graphics system, animated.**
   - **Logo stamp**: ink-dino in a glowing ring on green halftone, **boiling 2-3-frame
     loop**, snaps in ~1-2s as scene-transition punctuation, ~every 1.5-2.5min + at turns.
   - **Cards**: brand-canvas (green halftone) with bold condensed all-caps white text,
     **typewriter reveal ~25-30 chars/s (~1.2s)**, total hold ~2s, sound-punched.
   - Plus: MAP cards (park/region), CLOCK faces, CALENDAR page-flips (time jumps),
     growth/scale CHARTS with arrows, cartoon ANALOGY cards (crowned lion = "taxes").
9. **Composite literalism for money shots.** The creature is PNG/puppet-composited INTO
   real footage (trex wading in the actual wildebeest river-crossing, blood added;
   trex-vs-ox puppet fight with per-frame wiggle/lunge; egg swaying on a savanna plate;
   suburb/lawn shots = "the world notices you"). Plus dramatic isolates on black.
   Their creature assets are toy-grade up close — the genre tolerates jank at 2.85s.
10. **Story spine + flywheel.** Birth cold-open (slow CUTS, dense EVENTS: egg sway→
    crack-pop→hatch in the first 4s) → survival clock with timestamped progress →
    failure beats (comedy resets) → constant modern-world collisions (suburbs, police,
    press, fences — the title's PROMISE; the loser showed zero modernity and broke it)
    → finale set-piece composite → next-creature tease/vote CTA. "You/your" ≈ 8.7% of
    all words, flip by ~2.2s.

## 2. Receipts — per-second anatomy (Tier-2 frame grids)

**The egg open (0-14s)** — "10s hold" = 10 states: egg PNG sways on savanna plate
(floor never 0) → cracks POP open 2.1-2.4s on onsets ("the thing you notice") →
hatchling jitters → cartoon dino pops up 3.7s ("very,") → sun SLAMS in 4.4-4.8s, mag
16-22 ("very wrong.") → wipe to sunset palms → O₂-molecule overlay bobs 5.3-9.2s
("air…straw") → exits → canopy cut 10.0s → constant head-bob in grass (mag 29-43) →
ferns macro 13.5s ("ferns").

**Card** (7:53): green canvas snaps in; "YOU NEED 15 TO 20 POUNDS A WEEK" typewrites
char-by-char ~1.2s; holds ~0.8s; out. **Burst** (7:56-7:59.5): whiteboard-math skit →
Elmer Fudd Rabbit-Season clip plays AT FULL MOTION 1.4s (scene-detect reads it as ~15
"cuts") → Tom & Jerry scream 0.6s. **Logo** (0:37.7): snap-in, boiling loop, 1.7s.
**Puppet fight** (24:39): trex + ox cutouts lunging on savanna plate → kinetic forest
chase footage. **Finale chain** (26:37-26:46): river composite → legs-on-black 3.4s →
logo 1s → SpongeBob fancy-legs gag 2.4s → DeVito deadpan 1.2s.

## 3. What must change in OUR pipeline (gap → change, per layer)

| Layer | Now | Must become |
|---|---|---|
| Script | trex_pilot.txt already noun-dense, you-POV, modern collisions ✓ | add an explicit visual-noun pass: every sentence names a filmable noun |
| VO | F5-TTS clone ✓ (crossfade corrector required) | unchanged |
| Music | CORRECTED 2026-06-10: bed IS wired (chapter-field fallback loops `track_01_tense_ducked.wav`; measured 0.82 coverage on the pilot render vs ref 0.91) | creature-genre track(s) + slightly hotter bed → ≥0.90 coverage; per-act tracks later |
| Cut engine | fires only on stat/turn/pause → 11.1 cuts/min, 60% shots >5s (loser quadrant) | timer-fallback cut at body target on nearest word + ~6s hard cap; bursts as frenetic-insert beats, not 18 splices |
| Event layer | doesn't exist (static slates + 1.2%/s Ken Burns) | renderer EVENT layer: animated overlay pop-in/slam/slide (ffmpeg overlay x/y/scale expressions or pre-rendered PNG-sequence MOVs), per-event SFX from the event plan, sway/bob on composited stills |
| Graphics | static orange cards (good brand, wrong behavior) | extend `rexcaped_stat_cards.py` to emit ANIMATED cards: typewriter reveal (~27 chars/s, PNG sequence), boiling emblem stamp loop, NYC map card, survival-clock, calendar flip; cards flash ~2s |
| Creature | 512×288 LTX-2B t2v, repeats heavily | ChatGPT stills → cloud i2v hero set (Kling/Veo/Hailuo — pending spend OK, ~$3-25); Resolve Super-Scale existing clips; 2-3 PNG-puppet composites INTO real NYC footage for money shots |
| Stock | placeholder slates (decision pending) | ~40% of shots; non-Pexels lanes: archive.org/PD, Wikimedia, CC YouTube, original capture; DAYLIGHT-heavy |
| Comedy | 0% rendered (decision pending) | 25-30%, clustered on failure beats, 3 length classes, noun-rhyme placement; lane = owner decision (copyrighted-clip risk vs original/PD gags) — 0% is disproven by the loser |
| Palette | night/winter darkness | daylight pass + warm grade (ffmpeg LUT or Resolve finishing); night reserved for menace beats |
| QA | blackdetect/duration | add event-rate/min, music coverage %, max-gap-without-event (alert >6s) via `extract_motion_events.py` on our own renders |
| Packaging | ink thumbnail ✓ title ✓ | add next-creature vote/tease end card (flywheel) |

## 4. Build order
1. Engine tempo fix (timer-fallback + cap); music genre/level nudge → re-render pilot →
   **measure ourselves with `extract_motion_events.py`** (targets: cuts ≥15/min,
   events ≥25/min after event layer, music ≥90%, max quiet gap ≤6s).
2. Animated graphics pack (typewriter cards, boiling stamp, clock/map/calendar).
3. Renderer event layer (animated overlays + per-event SFX).
4. Owner decisions: comedy lane, stock lane, i2v spend.
5. Hero i2v regen + composites + daylight pass.
6. Full render → watcher + motion-event QA → ship.

**Measure-ourselves rule:** every render gets the same Tier-1 pass as the reference;
we ship when our numbers sit in the winner's band, not the loser's.
