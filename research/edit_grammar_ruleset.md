# Rexcaped Edit Grammar — measured from the top 3 (not guessed)

Derived by `scripts/extract_edit_grammar.py`: every hard cut (ffmpeg scene-detect)
fused with the word-timed transcript (.vtt) and audio onsets (librosa), across the
3 top Spinosnack videos — Megalodon (18.7m), Titanoboa (26.6m), T.Rex (28.8m).
Per-cut data in `/tmp/edit_deep/*_grammar.json`.

## 1. The real cut rhythm (kills both the "5s metronome" AND "cut on sentences")

| | cuts/min | median shot | %<1s | %>5s | music active | sound-on-cut |
|---|---|---|---|---|---|---|
| Megalodon | 15.0 | 3.1s | 14% | 23% | 91% | **98%** |
| T.Rex | 18.5 | 2.85s | 15% | 18% | 91% | 95% |
| Titanoboa | 3.9 | 9.6s | 4% | 73% | 99% | 94% |

It is **multi-modal, not an average.** Megalodon/T.Rex run a ~3s collage with
**0.07–0.13s machine-gun bursts** layered on top; Titanoboa runs long branded
**text-cards** where the motion happens *inside* the shot (so few hard cuts ≠ static).
"Avg 3s" is meaningless — the editing modulates from **0.07s to 9s+**.

## 2. The rules (script-feature → edit-action), with receipts

**R1 — A spoken NUMBER/stat → cut to a new visual or stat-card (~within 0.3s).**
11–18% of all cuts land on a number. Receipts (mm:ss / auto-caption):
- Megalodon 02:03 "a grouper that weighs about **30 lbs**, you eat it in two bites"
- Megalodon 06:38 "you're **10 m** long now"
- T.Rex 07:52 "you need **15 to 20 pounds** of…"
- Titanoboa 17:07 "its jaws snap shut **15 cm** from your head"

**R2 — A TURN-WORD (but / then / so / because / suddenly) → hard cut to a new shot.**
12–16% of cuts. The turn in the story = a turn on screen. Receipts:
- Megalodon 05:15 "lions, which are fine, **but** they're whales"
- T.Rex 16:36 "you don't even [notice] it at first. **Then** the flies…"
- Titanoboa 08:36 "your heart stops. You killed [it]. **Then** you smell something else"

**R3 — A LIST or a rhetorical "the math is simple" beat → 0.07–0.13s RAPID-FIRE montage.**
This is the texture you can't fake with a timer. Receipts:
- Megalodon 11:18 — **13 cuts in 1.6s** (every shot ~0.1s) over "plus large fish plus everything else you can catch"
- T.Rex 07:57 — **18 cuts in 1.5s** (~0.07s each) over "the math is simple — you're always hunting or you're always hunted"

**R4 — Sound on (nearly) EVERY cut, over a wall-to-wall music bed.**
94–98% of hard cuts have an audio transient on them; music is active 91–99% of the runtime.
Rule: every hard cut gets a whoosh/impact; never silence.

**R5 — Cut FASTER than the sentence.** 23–40% of cuts land *mid-phrase* (not on a pause).
They punctuate within sentences (B-roll/meme/emphasis flashes), they don't wait for the period.
(Pauses still get cuts too — 41–56% land on a speech pause.)

**R6 — Two tempos, modulated.** Hold for an establish/card (5–10s), then burst for a
list/emphasis (sub-second). The contrast IS the energy.

## 3. Why this is replicable

Every rule is written against a **script feature** (number, turn-word, list, question,
sentence-boundary, emphasis), not a clock. So a generative edit-planner can scan a NEW
script and emit an edit plan: stat-card on every number, hard-cut+whoosh on every
turn-word, rapid-fire montage on every list, sound-on-every-cut, mid-phrase B-roll
punctuation, tempo modulation. That plan becomes the paper-edit the renderer builds — the
same engine, but cuts placed by MEANING instead of a 5-second timer.

## 4. Honest limits (what this pass does NOT yet answer)

- **What each cut goes TO** (creature / stock / meme / stat-card) is not in this pass —
  it needs an asset-type + OCR-text layer. That's required to fully explain the *mid-phrase*
  cuts (R5) and to learn the meme-cutaway cadence.
- Auto-captions are slightly mistimed/garbled, so the spoken snippets are rough (but the
  numbers and turn-words are unambiguous, so R1/R2 hold).
- SFX onset count (~290/min) is inflated by music percussion; the reliable claims are
  "sound-on-cut ~95%" and "wall-to-wall music," not "290 discrete SFX/min."
- Scene-detect (thr 0.3) catches hard cuts, not within-card text animation (why Titanoboa
  reads "slow").

**Coverage estimate:** this cracks ~60–70% of the "why" (the cut-timing logic + sound).
The asset-type/OCR pass would take it to ~90%.

## 5. Pass 2 — WHAT each cut goes to (asset composition)

Sampled ~140 shots across the 3 videos and classified by eye (OCR was unreliable at
360p). Approximate, but the pattern is unmistakable and consistent.

**The creature is a MINORITY of the shots (~20–25%).** Most screen time is borrowed
B-roll and comedy. Rough mix for the fast-collage videos (Megalodon, T.Rex):

| Asset type | ~share | examples seen |
|---|---|---|
| **Real stock B-roll** (wildlife/nature/ocean) | **~40%** | hyenas, elephants, lions, vultures, rhinos, giraffes, savanna, sunsets, seals, ocean |
| **Meme / reaction / cartoon cutaways** | **~25–30%** | Looney Tunes "Rabbit Season", Tom & Jerry, SpongeBob, Loki, sunglasses-emoji, "PERFECT" guy, Elon/news, thinking-emojis |
| **CGI / AI / game creature** | **~20–25%** | the actual T.Rex / megalodon shots |
| **Stat-cards / graphics / logo** | **~8–10%** | "7 meters", "5 meters", the channel logo bug, animated scale |

Titanoboa is the **card mode**: a green halftone-card canvas with cut-out animal PNGs +
big text overlays, real jungle stock mixed in, fewer memes. Long-held cards, motion inside.

**Cadences:**
- **Meme/comedy cutaway ≈ every 60–90s** (tonal reset after grim/stat runs).
- **Stat-card on spoken numbers** ("7 meters", "5 meters") — confirms R1.
- **Logo bug** recurs as a transition/brand stamp.

### What this means for Rexcaped production (the big one)
We do **NOT** need a generated creature for every beat. The build model:
- **~20–25% hero creature shots** = our photoreal i2v T-Rex (our visual EDGE — and ours
  already beats their CGI/game footage).
- **~40% real stock B-roll** = the workhorse (for "modern New York": city/people/traffic
  stock; for a wild setting: wildlife stock). Cheap, sourced.
- **~25% meme/comedy cutaways** on a ~60–90s cadence. ⚠️ The reference channel uses
  COPYRIGHTED clips (Looney Tunes, SpongeBob, Loki, Elon) — fair-use-risky for a monetized
  channel. Rexcaped needs a meme strategy (freely-usable reaction images, original comedic
  cutaways, or accept the genre's risk). **Open decision.**
- **~10% stat-cards/graphics** on every number, + the logo stamp.

This is the HYBRID model, now data-backed: a few great creature hero shots carry the brand;
stock + memes + cards carry the runtime and the retention rhythm.

## 6. Validation finding — what is and isn't reproducible (honest)

`scripts/rexcaped_edit_engine.py` generates an edit from the script (cut-lattice +
tempo) and was tested against the real T.Rex cuts:

- Engine recall vs real cuts: **53.9%** | random-at-same-density: **46.6%**.
- So the script-feature lattice beats chance by only **~7 points**.

**Conclusion: exact cut *placement* is NOT script-reproducible.** Once you match the cut
*density*, the precise moments are ~at the random ceiling — they're visual/editorial
judgment (best frame, emphasis) plus genuine editor-to-editor variation. No script-driven
engine recovers them, and cloning them isn't the goal anyway.

**What IS reproducible (and what the engine targets):** cut density/tempo per section,
a modest bias toward meaningful moments (stats/turns), the asset mix, rapid-fire bursts on
lists, sound-on-cut, stat-cards on numbers, the meme cadence, the macro structure. Success
metric = **style-fit** (does it feel like the channel), NOT cut-for-cut match.

Future refinement to push past the ~7pt: visual/emphasis-aware cut SELECTION (cut on the
best frame + audio-stress), not more script rules.

