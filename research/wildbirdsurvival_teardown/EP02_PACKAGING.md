# EP02 — PACKAGING (title · thumbnail · description · tags)
_Recovered 2026-07-23. The title and thumbnail text were already locked in the storyboard; the
**description, tag list and A/B ladder below were written in a prior session and never committed** —
they were reconstructed from that session's transcript. Everything here is ship-ready copy._

---

## TITLE — LOCKED
```
Why This Giant Seabird Lets a Tiny Finch Drink Its Blood
```
56 chars · no suffix · no question mark · no colon.

Character-for-character isomorph of their **#2 all-time (939,961)** — *"Why This Warthog Lets Mongooses
Crawl All Over Its Face"* (55 chars, the only top-8 title with no pipe suffix). Stacks the 654K
scale-gap lever ("Giant"/"Tiny"). **"Lets"** appears in exactly two of their titles: 939,961 and
130,161 (mean 535K).

### Measured constraints behind the lock
| Evidence | Number |
|---|---|
| Winner head-clause lengths | 75 / 55 / 23 / 55 / 64 / 52 / 51 / 60 — median **55** |
| Hard ceiling adopted | **~68 chars** |
| All four colon-bearing titles | 85,402 · 50,263 · 42,432 · 36,296 — none in the top 8, none above median |
| Channel median (26 videos) | **80,506** · published 2026-07-01+ = **117,489** · first five = **26,720** |

### The A/B ladder (with the reasons, which were never written down)
1. **`Why Does a Bird 100 Times Bigger Let This Finch Open a Wound and Drink?`** (71ch) — kept as *the
   scientific counterfactual*: same permission frame, more visceral act, **zero blood keyword**. If you
   ever want to settle whether "blood" helps or hurts on this channel, this is the test.
2. **`…Lets Dozens of Tiny Finches Drink Its Blood`** (66ch) — **GATED.** Ship only if the hero image is
   recomposed to a swarm. "Dozens" is the good number class, but promising dozens over a single-finch
   image breaks the title–thumbnail contract.
3. ~~`Why This Seabird Lets a Seed-Eating Finch Drink Its Blood`~~ — **rejected**: "Seed-Eating" has no
   visual referent in the hero image, so title and thumbnail stop reinforcing each other.
4. ~~`— Standing Up Means Losing Its Egg` suffix~~ — **rejected**: "spends the entire click in the browse
   feed for free."

**Banned from the title** (measured): the betrayal/mutualism framing —
`OXPECKER: HERO OR VILLAIN? The Bird That Saves… and Betrays` did **42,432**, about half the median.
It is fine as an Act II payoff, never as the title. Also banned: spec numbers (`320 km/h` → **1,879**,
the channel's worst ever). *Quantities of the gross thing are the opposite*: `Hundreds`/`Thousands` →
**1,984,363**.

---

## THUMBNAIL — SHIPPED
`assets/vampire_finch/thumbs/FINAL_ep02_thumbnail.png` — passes `thumb_gate.py` **4/4**.
Text-free base for A/B swaps: `FINAL_ep02_base_notext.png`.

- **Text:** `BLOOD` in **#FFD400**, `FOR EGGS` in white, stacked, left third.
- **Type:** heavy condensed sans (Impact/Anton/Montserrat ExtraBold), tight tracking, 8–10px black
  outline **plus a soft drop shadow at 60% opacity**. `BLOOD` set ~**110%** the size of `FOR EGGS`.
  Cap height of `BLOOD` **≥15% of frame height**.
- **Dark plate fallback:** left-edge linear gradient black→transparent, 0–35% of width, ~55% max
  opacity. *Verify with a luminance check, not by eye* — `thumb_gate.py` does this.
- **Grade:** desaturate everything but the blood 10–15%; keep white feather detail **below 250**.
- **Composition:** the finch's eye visible and catchlit. The booby's eye in frame only if it doesn't
  cost tightness — **the blood outranks it**.

### Hard nos (each traced to a measured failure)
- **No egg in the image.** It cannot coexist with the tight framing — the egg lives in the *text* and in
  the first 15 seconds.
- **No text describing an absence or a state** (`WON'T FIGHT BACK`, `IT NEVER FLINCHES`) — the
  `DEATH STARE` failure mode.
- **No text naming something not in frame** (`NO WATER LEFT`, `SEEDS TO BLOOD`, `100X BIGGER`) — the
  `LIVE IN THE EAR!` failure mode, which is exactly what sank their own blood video: its thumbnail
  contained no blood at all.
- **No arrows, circles, emoji, logo or borders** — zero appear in any of their winners.
- **No AI-rendered human, hand or face.**

### ⚠️ Unresolved spec conflict — owner call needed
The spec says **wound ≥12% of frame** *and* **"no gore beyond one bead + smear (advertiser safety)"**.
These cannot both hold. The shipped frame reaches 12.58% only via the spec's own selective grade, and it
reads as a visibly bloodied bird. `ALT_ep02_thumbnail_ungraded.png` is the tamer cut (11.66%, still
reads clearly at 168×94) if advertiser safety outranks the area rule.

### A/B thumbnail (never written down until now)
`BLOOD HOSTAGE` — 2 words, same yellow/white treatment, **48-hour swap, only after the primary has 24h
of clean CTR data.** **Never change title and thumbnail in the same swap.**

---

## DESCRIPTION
First line (the only part that shows in the feed):
> On two islands in the Galápagos, the vampire ground finch drinks the blood of the Nazca booby — and
> the booby lets it happen.

**Ship rule:** strip every template placeholder before upload. Credit any original reporting used.

## TAGS (12)
`vampire finch` · `vampire ground finch` · `Geospiza septentrionalis` · `Nazca booby` · `Galapagos` ·
`Wolf Island` · `Darwin Island` · `Darwin's finches` · `blood drinking bird` · `wildlife documentary` ·
`parasitism` · `symbiosis`

The species names are deliberately kept **out of the title** (every winner used an instantly imageable
animal, and "Booby" invites off-intent search and comment noise) and recovered here in the tags.

## HASHTAGS (3)
`#vampirefinch #galapagos #wildlife`

---

## PUBLISH TIMING — HARD RULE
**Do not publish within 72h of any other blood / parasite / feeding video.** Their 3,041-view video was
a near-clone of their own #1, published one day later — self-cannibalisation is a measured killer on
this channel.

## The premise-risk correction that matters
Their own *"This Bird Drinks Blood From Live Animals"* did 13,095 — but it is **upload #1 of 26**.
Uploads #1/#2/#3 are the three worst ever (13,095 / 1,879 / 26,720); first-five median **26,720** vs
rest-of-channel **117,489** (4.4× cold-start), and their first real hit was upload #8.
**Blood is not disproven — that video was confounded by cold start**, and it also carried two loser
tells we avoid (actor-POV declarative + "Full Life Cycle" suffix).
