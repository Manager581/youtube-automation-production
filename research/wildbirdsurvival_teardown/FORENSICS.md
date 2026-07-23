# @wildbirdsurvival — Forensic Edit Teardown (per-beat, not averages)
_Method: downloaded 5 winners + 2 losers at 360p; word-level Whisper transcripts; ffmpeg
scene-cut detection with timestamps; librosa audio (RMS, HPSS harmonic/percussive, onset
detection); cut-to-word and cut-to-audio alignment; frame extraction at every cut. Raw data in
this folder (`forensics_*.json`, `compare_metrics.json`, `timelines/*.txt`)._

## The 7-video measurement table
| Video | Views | dur | cuts | med shot | fast<3s | hold>10s | talk% | wpm | max pause | cuts-on-word | med cut→word | SFX hits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BEST buffalo/fish | 1.98M | 480s | 80 | 3.6s | 44% | 15% | 41% | 157 | 14.9s | 44% | 0.92s | 6 |
| WIN2 warthog | 940K | 611s | 109 | 3.8s | 44% | 13% | 42% | 145 | — | 47% | 0.48s | 8 |
| WIN3 mongoose/cobra | 855K | 609s | 106 | 4.1s | 43% | 13% | 27% | 103 | 54.6s | 21% | 3.91s | 5 |
| WIN4 hornbill | 674K | 591s | 91 | 3.6s | 48% | 21% | 50% | 153 | — | 62% | 0.28s | 3 |
| WIN5 giants | 654K | 562s | 78 | 4.7s | 13% | 18% | 54% | 163 | — | 65% | 0.24s | 12 |
| **LOSE2 hippo/fish** | 3K | 507s | 111 | 2.8s | 54% | 11% | 44% | 140 | — | 57% | 0.30s | 5 |
| **WORST peregrine** | 1.9K | 482s | 95 | 3.0s | 50% | 9% | 67% | 190 | 5.6s | 75% | 0.13s | 8 |

**Winner avg vs Loser avg:** talk-coverage 43% vs 55% · long holds 16% vs 10% · fast cuts 38% vs 52%
· cuts-on-word 48% vs 66% · median cut→word 1.2s vs 0.2s · wpm 144 vs 165.

## What the numbers mean (the real pacing logic)

### 1. Cut philosophy — the single clearest winner/loser split
- **Winners cut on the IMAGE; losers cut on the WORD.** Losers place a cut within 0.4s of a
  narrated word 66% of the time (peregrine 75%, median offset **0.13s**) → "new sentence = new
  slide," a breathless slideshow. Winners are at 48% (buffalo median **0.92s**, cobra **3.91s**)
  → cuts fall where the *visual* wants to change, and they keep cutting through wordless stretches.
- **Directive:** don't hard-cut on every sentence. Let shots run across sentences; cut when the
  image has said what it needs to. Keep cutting during silent music passages.

### 2. Narration density — leave room to breathe
- Winners narrate over **~43%** of runtime; the two biggest hits are the sparsest (buffalo 41%,
  cobra 27%). The worst video talks over **67%** of its runtime — wall-to-wall encyclopedia.
- Winners speak at **~145–160 wpm**; the flop races at **190 wpm**.
- **Directive:** target ~40–50% narration coverage, ~150 wpm. Write less script than you think;
  let the visuals + music carry ~half the video.

### 3. Dramatic pauses before the reveal
- The buffalo hit has a **14.9-second wordless gap** right before the turn ("…refuse to let go.
  ⟨14.9s of music⟩ Finally, the buffalo walks into a river.") and another **14s** before the fish
  reveal. The cobra fight has a **54.6s** wordless music-and-action climax. The flop's longest
  pause is **5.6s** — no anticipation, no drama.
- **Directive:** insert a long (8–15s) music-only beat immediately before each big reveal/turn.
  Silence the narrator and let tension build on visuals alone.

### 4. Fast hook, then HOLD the money shot
- Shot lengths are **bimodal**: many 1–3s cuts (energy) plus a few very long holds. Winners hold
  the payoff far longer — the buffalo's fish-cleaning "money shot" is a single **34.6-second**
  sustained take ("Hundreds of fish press their mouths against the buffalo's body…").
- **Directive:** cut fast to build the problem; when you reach the remarkable behavior, stop
  cutting and hold one shot 20–35s so the viewer can marvel.

### 5. NO SFX-stinger editing (whole-channel style, not a differentiator)
- Only ~3–12 hard audio transients across an entire 8–10 min video, and **~0–2% of cuts land on
  an audio hit** (buffalo: 1 of 80). There are **no whoosh/impact stingers** on cuts. The audio is
  a soft harmonic music bed (HPSS harmonic ≫ percussive) that swells under payoffs and drops for
  the calm resolution.
- **Directive:** do NOT add MrBeast-style whoosh cuts. Use one continuous cinematic music bed;
  let it swell at the payoff and fall at the golden-hour ending. Diegetic-only accents (a splash,
  wingbeat) at most.

## Hook construction — shot-by-shot (buffalo winner, 0–62s)
| Shot | Time | Len | Narration | Visual |
|---|---|---|---|---|
| 0 | 0.0 | 1.6s | "Across the African savannah," | **Opens ON the buffalo's face** (no wide landscape) |
| 1 | 1.6 | 2.2s | "this cave buffalo is" | **EXTREME MACRO of engorged ticks** (shock detail at 1.6s) |
| 2 | 3.9 | 1.6s | "enduring an assault from" | wide: buffalo in savanna |
| 3 | 5.4 | 1.4s | "hundreds of blood-sucking ticks" | buffalo shaking head, droplets flying |
| 4–5 | 6.8 | 5.8/7.1s | body-part list + flies | macro of hide/ticks (holds lengthen) |
| 6–7 | 19.7 | 5.5/12s | "has tried everything… rubbing…" | buffalo kneeling, rubbing in dust |
| 8 | 37.2 | 1.8s | *(wordless)* | buffalo bucking near tree (motion beat) |
| 9 | 39.0 | 9.5s | "against tree trunks, rolling…" | **literal match**: buffalo rubbing a tree trunk |
| 10 | 48.4 | — | *(then 14.9s pause)* | buffalo collapsed, exhausted → river (the turn) |

**Hook rules that separate winners from losers (verified visually):**
- **Open on the subject, not a landscape.** Buffalo = face at frame 1. Peregrine loser = 15
  seconds of pretty mountain/lake/flying-bird beauty shots before anything happens.
- **Shock-detail macro within ~2s** (the tick cluster). The loser never shows a visceral macro —
  just a bird flying and a calm duck on a lake.
- **B-roll literally illustrates the words** ("tree trunks" → a tree trunk).
- **Stay tight on one protagonist in distress.** Losers cut to tiny-animal-in-wide-snowy-landscape
  shots (low impact) and static "family lined up on a rock" life-cycle portraits.

## Narrator voice spec (for ElevenLabs matching)
- **Median fundamental ≈ 82 Hz** (deep male), p10–p90 only 64–95 Hz = **very narrow pitch range**
  → calm, measured, authoritative; almost no theatrical pitch swings.
- **~150 wpm.** British spelling in scripts ("colour", "metres").
- **ElevenLabs setup:** pick a deep male documentary voice; high Stability (steady, low variance),
  moderate Similarity; speed ~0.9–1.0; aim ~150 wpm. Avoid bright/energetic reads (that's the 190-wpm
  flop). One continuous pass over a locked script (project rule).

## Structure arc (all winners)
Cold-open jeopardy on one individual (0–15s, tight + macro) → escalation ("tried everything") →
**long silent pause** → the turn (savior/partner appears) → **held money shot** of the remarkable
behavior (music swells) → life-cycle/relationship exposition → music falls → golden-hour wide outro
+ subscribe line.

---

# ADVERSARIAL VERIFICATION PASS — corrected findings (authoritative; supersedes interpretation above)
_19 candidate rules were derived by 4 independent agents (rhythm, story, audio, hook lenses) and
each was adversarially tested against all 7 videos by a skeptic. Result: 2 CONFIRMED, 15 PARTIAL
(had to be qualified), 2 REFUTED. Raw: `verified_rules_raw.json`._

## THE decisive meta-finding
**The 3K-view flop `LOSE2` (hippo/fish) is a near-clone of the 1.98M-view hit `BEST` (buffalo/fish)
— same template, same production, published one day apart — and it CONFORMED to 10 of the 19
editing rules, yet still flopped.** It has a breathing music bed, wordless climaxes (a 53.5s solo
gap — 2nd longest of all 7), a victim-in-peril cold open, an early named threat ("blood-feeding
ticks" by ~13s), the single-arc structure, even the "Finally… something remarkable begins to
happen" signpost with a clean 2.5s pre-turn pause. It did everything the winners do.

**Conclusion: the editing grammar is the channel's HOUSE STYLE — table stakes for a competent,
watchable AI wildlife doc — NOT the lever that makes a video go viral vs. flop.** The win/loss gap
lives UPSTREAM of the edit: topic novelty, title, thumbnail, and algorithmic timing (don't publish
a near-duplicate of your own hit — the algorithm crowns one twin and starves the other). Every
retention/pacing rule below is necessary-not-sufficient: replicate them to look legit and hold the
viewers you get, but they will not, by themselves, earn the click or the impressions.

## CONFIRMED (holds across all 7, high confidence)
1. **No whoosh/SFX-hit editing — rigorously confirmed.** 3–12 hard transients per whole video;
   only 0.9–2.8% of cuts have any transient within 0.5s = each video's own random-chance baseline
   (binomial tests: no video aligns cuts to audio above chance). Silent, clip-length + phrasing
   driven cuts. **This is channel-wide (losers too) — a style requirement, not a win lever.**
2. **Winners hold a slower cut baseline than the losers** (directional guardrail for this channel):
   winner median shot ≥3.6s and mean ≥5.56s; both losers cut faster on both (median ≤3.0s, mean
   ≤5.0s), non-overlapping. Caveat: rests on only 2 losers, both confounded (LOSE2 = cannibalized
   clone; WORST = a dense "full life cycle"). Real, but not proof that slow cutting *causes* views.

## PARTIAL — corrected to CEILINGS/guardrails (not the bands I first stated)
3. **Narration coverage is a CEILING (~55–60% max), not a 40–55% band, and has NO floor.** WIN3 won
   at ~27% coverage (its 2nd half is a near-wordless music/action climax → ~70%+ silent). Only the
   one video above 60% (WORST, 67%) is a loser. Don't treat 40% as a floor or "half-silent" as a target.
4. **Word density is a CEILING: ≤~2.75 wps AND composite (coverage×wps) ≤~1.5.** Only WORST breaches
   (3.17 wps at 67% coverage = wall-to-wall). Low density is fine (WIN3 = 0.46). ~150 wpm holds for
   winners; the flop races at 190.
5. **On-word cutting does NOT discriminate by itself.** Winners span 21%→65% cuts-on-word; WIN4
   (62%) and WIN5 (65%) weld harder than the flopped clone (57%) and still won 650–675K. The ONLY
   diagnostic loser signal is the *compound extreme* in WORST: ~75% word-welded cuts stacked on
   dense wall-to-wall VO ("karaoke chopping"). Avoid that specific stack; on-word % alone is not a gate.
6. **Give the money shot low-narration breathing room (robust half).** Winners run their single
   longest hold at low words/sec so the image carries it (BEST 34.6s at 44% of avg density; WIN2/WIN3
   essentially wordless). WORST narrates densely over its 41s hero hold. Drop the false specifics
   ("one sentence", "25–45s") — the operative variable is **words-per-second on the hold**, not length
   or sentence count, and the hold-count "13–19" is soft (LOSE2 had 12 and still flopped).
7. **Hook: the only reliable discriminator is a PROHIBITION — never open with the encyclopedic
   "this species is famous for its…" species-card** (only WORST does; it's the worst performer). The
   positive "one animal in immediate jeopardy in the first sentence" fits just 2/5 winners — WIN4
   opened on a calm comedic family beat, WIN3 on the predator, WIN2 on a Lion King pop-culture
   question. Multiple opener styles win; only the species-card open reliably loses. Keep the hook
   un-choppy (~9–11 cuts in the first 60s, mean shot ≥5s); a grossly doubled hook (LOSE2: 22 cuts)
   co-occurs with failure but WORST didn't double its hook and still died, so it's a red flag, not the gate.
8. **Music energy: don't peak dead-center.** All 5 winners peak harmonic energy before mid-video
   (median 0.20 in); the only dead-center peak (LOSE2, 0.55) is a loser. But early-peak is
   necessary-not-sufficient (WORST peaks earliest of all, 0.03, and flopped). Weak hygiene marker.

## REFUTED (do NOT treat as rules)
9. **"A long silent cold open needs predator conflict / scenery is fatal."** REFUTED — WIN4 (674K)
   opened on 18.6s of calm domestic mongoose-family scenery, no threat, and won. A silent cold open
   is survivable regardless of content; what tracks WORST's loss is its breathless high-coverage narration.
10. **"Insert a ~2s pause + 'Finally/something remarkable' signpost before the turn = win lever."**
    REFUTED — the loser LOSE2 executes this most faithfully (2.5s pause + both signpost phrases) and
    flopped. BEST's real pre-turn gap is ~15s, not 2s. An early turn in the first third is a shared
    genre baseline, present in winners AND the near-clone loser.

## Net: the two layers
- **HOUSE STYLE (replicate exactly to look legit + retain):** silent no-SFX cutting, slower holds,
  ≤55–60% narration coverage, ≤2.75 wps / ~150 wpm calm 82 Hz voice, low-density hero holds, no
  species-card open, off-center-early music peak, golden-hour philosophical outro.
- **WHERE THE WIN ACTUALLY IS (upstream of the edit):** novel two-animal curiosity-gap TOPIC,
  title, thumbnail, and not cannibalizing your own hit. The near-clone A/B (BEST 1.98M vs LOSE2 3K)
  proves the edit is not the differentiator.
