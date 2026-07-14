# VO SCRIPT — LUKE RE-VOICE / LOCKED
**Episode:** Dinoverse clone — episode_01 "Omega Rex"  
**Machine-readable twin:** `vo_manifest_v2.json` (same dir) — holds every SHA-256.  
**Extends:** `VO_SCRIPT_FINAL.md` / `vo_manifest.json` (cold open + S89). Those two passes are reproduced here **byte-identical**, same SHAs — they were rebuilt from the TSV by this build and asserted equal to the locked v1. Nothing about them changed.

**Rule:** ONE generation per pass, **no re-rolls** (memory `elevenlabs-one-pass-rule`).  
**Model:** Eleven Multilingual v2 — honours `<break time="3.0s" />`, so several lines ride in one generation and get split at the silences afterward.

> LOCKED. The pre-Generate SHA check is the last chance to change anything.

---

## 0. The decision (settled — this doc implements it)

Grok gave Luke **a different voice in nearly every clip** — F0 128–392 Hz across 27 clips, changing mid-scene (`voice_drift_census.json`). So:

- **Luke is RE-VOICED** across his off-camera body dialogue. **26 body lines.**
- **GF is NOT re-voiced in the body** — she is on camera in ~16 clips, dubbing would break lip-sync. She keeps **only her 3** cold-open/end-card lines.
- Plus the **cold open + S89 end card** (the original Task B, unchanged).
- Plus a clean **RANGER** VO for **S46** to restore the missing "that's a Utahraptor" payoff.

### What is EXCLUDED, and why

| Shot | Speaker | Why excluded |
|---|---|---|
| **S13** | LUKE / GF | **LUKE IS ON CAMERA** (selfie two-shot) — dubbing breaks lip-sync. Verified: `feas/zoom_LUKE_S13.png` |
| **S37** | LUKE | **LUKE IS ON CAMERA** (selfie two-shot) — dubbing breaks lip-sync. Verified: `feas/zoom_LUKE_S37.png` |
| **25 two-speaker rows** | LUKE / GF, GF / LUKE, CLERK / LUKE, RANGER / LUKE | See §9 — **all excluded by default**, one opted back in (S46). |

---

## 1. Typography normalizations (the ONLY changes from the TSV text)

- `N1  '...' -> U+2026 ellipsis (existing convention)`
- `N2  ' - ' -> ' — ' em dash (existing convention)`
- `N3  trailing cut-off hyphen -> U+2014 em dash (NEW - S76, S78 only)`
- `N4  apostrophes stay ASCII U+0027 - never smart-quote`

Every line where a normalization fired:

| Shot | Speaker | TSV | Locked text |
|---|---|---|---|
| S17 | LUKE | `First up - Carnotaurus. The one with the horns.` | `First up — Carnotaurus. The one with the horns.` |
| S21 | LUKE | `Mom and baby together. Fun fact - Carnotaurus used those horns to fight each other for territory.` | `Mom and baby together. Fun fact — Carnotaurus used those horns to fight each other for territory.` |
| S22 | LUKE | `So - who do you think its real rival was? Drop it in the comments. We'll settle it.` | `So — who do you think its real rival was? Drop it in the comments. We'll settle it.` |
| S26 | LUKE | `He just... yep. He's flying. That's terrifying and cute.` | `He just… yep. He's flying. That's terrifying and cute.` |
| S29 | LUKE | `One of its rivals was another giant flyer, Hatzegopteryx. ...you'll want to Google that spelling.` | `One of its rivals was another giant flyer, Hatzegopteryx. …you'll want to Google that spelling.` |
| S35 | LUKE | `Meet Dunkleosteus. No teeth - just self-sharpening bone blades.` | `Meet Dunkleosteus. No teeth — just self-sharpening bone blades.` |
| S40 | LUKE | `Do you think these two could actually live in the same water? ...I genuinely don't know. Tell me.` | `Do you think these two could actually live in the same water? …I genuinely don't know. Tell me.` |
| S43 | LUKE | `Next - and this is the one people always get wrong.` | `Next — and this is the one people always get wrong.` |
| S52 | LUKE | `Styracosaurus - all those spikes are just for show. Mostly.` | `Styracosaurus — all those spikes are just for show. Mostly.` |
| S63 | LUKE | `A single tooth - 30 centimeters, root included.` | `A single tooth — 30 centimeters, root included.` |
| S71 | LUKE | `That's the Indominus. Part T-Rex, part... a lot of things.` | `That's the Indominus. Part T-Rex, part… a lot of things.` |
| S74 | LUKE | `And this - the deepest one - is the D-Rex.` | `And this — the deepest one — is the D-Rex.` |
| S76 | LUKE | `HEY - get away from the-` | `HEY — get away from the—` |
| S78 | LUKE | `RUN. RUN-` | `RUN. RUN—` |
| S81 | LUKE | `This way - go, go!` | `This way — go, go!` |
| S03 | LUKE | `A T-Rex. A raptor pack. Two hybrids that should not exist... and three kids who thought a locked door was a dare.` | `A T-Rex. A raptor pack. Two hybrids that should not exist… and three kids who thought a locked door was a dare.` |
| S89 | LUKE | `Comment which dino you'd survive. Subscribe - part two if this hits.` | `Comment which dino you'd survive. Subscribe — part two if this hits.` |
| S89 | GF | `...we are never coming back.` | `…we are never coming back.` |
| S46 | RANGER | `Here's what the movies got wrong. The famous 'velociraptors'? Real velociraptors were the size of a turkey. What Hollywood actually drew - this size, this build - that's a Utahraptor. They just kept the cooler-sounding name.` | `Here's what the movies got wrong. The famous 'velociraptors'? Real velociraptors were the size of a turkey. What Hollywood actually drew — this size, this build — that's a Utahraptor. They just kept the cooler-sounding name.` |
| S46 | LUKE | `So every raptor you've ever feared... was basically this guy, with a rebrand.` | `So every raptor you've ever feared… was basically this guy, with a rebrand.` |

**Nothing else changed.** No paraphrase, no "improvement", no bracketed stage directions (v2 reads those out loud). Apostrophes stay **ASCII** — a smart quote changes the bytes and breaks the SHA check.

Two verbatim quirks kept on purpose:

- **S32** is `'Aquatic Life Enclosure.'` — Luke is reading a sign, the inner single quotes are in the TSV. TTS does not vocalise quote marks.
- **S59** is `Okay, NOW food.` — the caps are the scripted emphasis; v2 honours caps.

---

## 2. PASS_LUKE_BODY — LUKE, 23 calm body lines

**SHA-256 of the paste text:** `f1e5e0c5d62223748ecb856b5d89c31e4a91c996d1b5dfd70539e6934eb3c6db`  
**Save the download as:** `audio/dinoverse_omega/source_chunks/luke_body_pass.mp3`  
**23 line(s), 1812 chars — expect 22 silence(s) on the split.**

> 1812 chars - under the 5000-char split threshold, so this stays as ONE generation. No scene-boundary split needed.

This is the pass that fixes the episode.

```
First up — Carnotaurus. The one with the horns.

<break time="3.0s" />

There's the grown-up. Look at those horns.

<break time="3.0s" />

Mom and baby together. Fun fact — Carnotaurus used those horns to fight each other for territory.

<break time="3.0s" />

So — who do you think its real rival was? Drop it in the comments. We'll settle it.

<break time="3.0s" />

He just… yep. He's flying. That's terrifying and cute.

<break time="3.0s" />

Imagine looking up and seeing that.

<break time="3.0s" />

One of its rivals was another giant flyer, Hatzegopteryx. …you'll want to Google that spelling.

<break time="3.0s" />

'Aquatic Life Enclosure.'

<break time="3.0s" />

This is the one I wanted.

<break time="3.0s" />

Meet Dunkleosteus. No teeth — just self-sharpening bone blades.

<break time="3.0s" />

Do you think these two could actually live in the same water? …I genuinely don't know. Tell me.

<break time="3.0s" />

Next — and this is the one people always get wrong.

<break time="3.0s" />

They hunt in coordination. That's the scary part.

<break time="3.0s" />

Comment 'Utahraptor' if you learned something. Let's give the internet a quiz.

<break time="3.0s" />

Styracosaurus — all those spikes are just for show. Mostly.

<break time="3.0s" />

Brachiosaurus. That neck's basically a crane.

<break time="3.0s" />

Whole family crossing together.

<break time="3.0s" />

Okay, NOW food.

<break time="3.0s" />

The one everyone's waiting for. T-Rex.

<break time="3.0s" />

A single tooth — 30 centimeters, root included.

<break time="3.0s" />

Strongest bite of any land animal that ever lived. And that's not even the scary one here.

<break time="3.0s" />

That's the Indominus. Part T-Rex, part… a lot of things.

<break time="3.0s" />

And this — the deepest one — is the D-Rex.
```

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S17 | First up — Carnotaurus. The one with the horns. | `audio/dinoverse_omega/luke_s17.wav` |
| 2 | S19 | There's the grown-up. Look at those horns. | `audio/dinoverse_omega/luke_s19.wav` |
| 3 | S21 | Mom and baby together. Fun fact — Carnotaurus used those horns to fight each other for territory. | `audio/dinoverse_omega/luke_s21.wav` |
| 4 | S22 | So — who do you think its real rival was? Drop it in the comments. We'll settle it. | `audio/dinoverse_omega/luke_s22.wav` |
| 5 | S26 | He just… yep. He's flying. That's terrifying and cute. | `audio/dinoverse_omega/luke_s26.wav` |
| 6 | S28 | Imagine looking up and seeing that. | `audio/dinoverse_omega/luke_s28.wav` |
| 7 | S29 | One of its rivals was another giant flyer, Hatzegopteryx. …you'll want to Google that spelling. | `audio/dinoverse_omega/luke_s29.wav` |
| 8 | S32 | 'Aquatic Life Enclosure.' | `audio/dinoverse_omega/luke_s32.wav` |
| 9 | S33 | This is the one I wanted. | `audio/dinoverse_omega/luke_s33.wav` |
| 10 | S35 | Meet Dunkleosteus. No teeth — just self-sharpening bone blades. | `audio/dinoverse_omega/luke_s35.wav` |
| 11 | S40 | Do you think these two could actually live in the same water? …I genuinely don't know. Tell me. | `audio/dinoverse_omega/luke_s40.wav` |
| 12 | S43 | Next — and this is the one people always get wrong. | `audio/dinoverse_omega/luke_s43.wav` |
| 13 | S48 | They hunt in coordination. That's the scary part. | `audio/dinoverse_omega/luke_s48.wav` |
| 14 | S50 | Comment 'Utahraptor' if you learned something. Let's give the internet a quiz. | `audio/dinoverse_omega/luke_s50.wav` |
| 15 | S52 | Styracosaurus — all those spikes are just for show. Mostly. | `audio/dinoverse_omega/luke_s52.wav` |
| 16 | S54 | Brachiosaurus. That neck's basically a crane. | `audio/dinoverse_omega/luke_s54.wav` |
| 17 | S56 | Whole family crossing together. | `audio/dinoverse_omega/luke_s56.wav` |
| 18 | S59 | Okay, NOW food. | `audio/dinoverse_omega/luke_s59.wav` |
| 19 | S61 | The one everyone's waiting for. T-Rex. | `audio/dinoverse_omega/luke_s61.wav` |
| 20 | S63 | A single tooth — 30 centimeters, root included. | `audio/dinoverse_omega/luke_s63.wav` |
| 21 | S67 | Strongest bite of any land animal that ever lived. And that's not even the scary one here. | `audio/dinoverse_omega/luke_s67.wav` |
| 22 | S71 | That's the Indominus. Part T-Rex, part… a lot of things. | `audio/dinoverse_omega/luke_s71.wav` |
| 23 | S74 | And this — the deepest one — is the D-Rex. | `audio/dinoverse_omega/luke_s74.wav` |

---

## 3. PASS_LUKE_SHOUT — LUKE, 3 shouted body lines

**SHA-256 of the paste text:** `595dc13b6546cb048e647aaf5c527819ac771ad26115c3c390cefadae692e5ff`  
**Save the download as:** `audio/dinoverse_omega/source_chunks/luke_shout_pass.mp3`  
**3 line(s), 101 chars — expect 2 silence(s) on the split.**

> SHOUTED lines - generate with LOWER stability / HIGHER style than the body pass. Kept out of the body pass because ElevenLabs voice settings are per-generation and one flat setting cannot serve both.

⚠️ **Risk R1 — read this before generating.** These 3 lines are script-shouted. A single flat TTS pass will very likely deliver them **conversationally**, not urgently, and the no-re-rolls rule means you are stuck with what comes out. They are carved into their own pass **precisely so you can dial the voice settings for them** (lower Stability, higher Style) without touching the calm body pass. The caps in `RUN. RUN—` are the scripted emphasis and v2 does respond to caps — but **set expectations: this is the single most likely thing in the whole job to disappoint.** If the take is flat, the honest fallback is to keep Grok's original shouted audio for these 3 shots and accept a voice change on ~5s of a 8:45 episode.

```
HEY — get away from the—

<break time="3.0s" />

RUN. RUN—

<break time="3.0s" />

This way — go, go!
```

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S76 | HEY — get away from the— | `audio/dinoverse_omega/luke_s76.wav` |
| 2 | S78 | RUN. RUN— | `audio/dinoverse_omega/luke_s78.wav` |
| 3 | S81 | This way — go, go! | `audio/dinoverse_omega/luke_s81.wav` |

---

## 4. PASS_LUKE_COLDOPEN — LUKE, 4 lines (UNCHANGED from v1)

**SHA-256 of the paste text:** `276cc9ae441aef8efc109cd4f34d40bf33daff6a21c879cb827704a0468e48ff`  
**Save the download as:** `audio/dinoverse_omega/source_chunks/luke_pass.mp3`  
**4 line(s), 375 chars — expect 3 silence(s) on the split.**

> UNCHANGED from the locked vo_manifest.json PASS_1_LUKE

```
So last time, we barely made it out of the dinosaur zoo alive.

<break time="3.0s" />

A T-Rex. A raptor pack. Two hybrids that should not exist… and three kids who thought a locked door was a dare.

<break time="3.0s" />

Stay till the end. You will not believe how this one ended.

<break time="3.0s" />

Comment which dino you'd survive. Subscribe — part two if this hits.
```

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S01 | So last time, we barely made it out of the dinosaur zoo alive. | `audio/dinoverse_omega/luke_s01.wav` |
| 2 | S03 | A T-Rex. A raptor pack. Two hybrids that should not exist… and three kids who thought a locked door was a dare. | `audio/dinoverse_omega/luke_s03_montage.wav` |
| 3 | S12 | Stay till the end. You will not believe how this one ended. | `audio/dinoverse_omega/luke_s12.wav` |
| 4 | S89 | Comment which dino you'd survive. Subscribe — part two if this hits. | `audio/dinoverse_omega/luke_s89_cta.wav` |

---

## 5. PASS_GF — GF, 3 lines (UNCHANGED from v1)

**SHA-256 of the paste text:** `52fe5a136a1f3621e405a0b70a1faefa582ff032b629aa6c8ac85d8b52657b7b`  
**Save the download as:** `audio/dinoverse_omega/source_chunks/gf_pass.mp3`  
**3 line(s), 152 chars — expect 2 silence(s) on the split.**

> UNCHANGED from the locked vo_manifest.json PASS_2_GF. GF is NOT re-voiced in the body - she is on camera in ~16 clips.

```
This time we found the part they really didn't want us to see.

<break time="3.0s" />

Remember them.

<break time="3.0s" />

…we are never coming back.
```

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S02 | This time we found the part they really didn't want us to see. | `audio/dinoverse_omega/gf_s02.wav` |
| 2 | S11 | Remember them. | `audio/dinoverse_omega/gf_s11.wav` |
| 3 | S89 | …we are never coming back. | `audio/dinoverse_omega/gf_s89_closer.wav` |

---

## 6. PASS_RANGER — RANGER, the S46 myth-bust

**SHA-256 of the paste text:** `1278bcd6430f7470554204bc8015aaca649377895d4dadec5a507536f7ff20fd`  
**Save the download as:** `audio/dinoverse_omega/source_chunks/ranger_s46_pass.mp3`  
**1 line(s), 224 chars — expect 0 silence(s) on the split.**

> single line - no break tags needed

See §8 — **S46 has a hard timing problem the owner must decide on before this ships.**

```
Here's what the movies got wrong. The famous 'velociraptors'? Real velociraptors were the size of a turkey. What Hollywood actually drew — this size, this build — that's a Utahraptor. They just kept the cooler-sounding name.
```

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S46 | Here's what the movies got wrong. The famous 'velociraptors'? Real velociraptors were the size of a turkey. What Hollywood actually drew — this size, this build — that's a Utahraptor. They just kept the cooler-sounding name. | `audio/dinoverse_omega/ranger_s46.wav` |

---

## 7. PASS_LUKE_EXTRA — LUKE, 2 OPT-IN lines

**SHA-256 of the paste text:** `af28bdb050c16572146b7651d02c68decabc2b466a23847793d8845464dbfd29`  
**Save the download as:** `audio/dinoverse_omega/source_chunks/luke_extra_pass.mp3`  
**2 line(s), 170 chars — expect 1 silence(s) on the split.**

> OPT-IN. Both are off-camera and both are RECOMMENDED, but neither matches the literal 'Speaker == LUKE' filter, so they are isolated here: approving or dropping them does not touch any other SHA.

⚠️ **Neither of these matches the literal `Speaker == LUKE` filter, so they are NOT silently folded into the body pass.** Both are off-camera and both are **RECOMMENDED**. Isolated here so that approving or dropping them **does not touch any other SHA**.

- **F1 — S88** — Speaker is `LUKE VO`, not `LUKE`. It is a pure VO over a wide showdown shot: **zero lip-sync risk, the safest line in the episode.** If you skip it, Luke's voice audibly changes *at the climax*, right after 26 dubbed lines. **Recommend YES.**
- **F2 — S46 Luke punchline** — a two-speaker row, so it is excluded by the conservative default. BUT: the hosts are back-of-head/off-camera in S46, the RANGER half of that same clip is being dubbed anyway, and Luke's turn is at the END of the clip — cleanly separable in time. Grok never delivered this line at all (see §8). **Recommend YES.**

```
Three apex predators. One park. And it started with one unlocked door.

<break time="3.0s" />

So every raptor you've ever feared… was basically this guy, with a rebrand.
```

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S88 | Three apex predators. One park. And it started with one unlocked door. | `audio/dinoverse_omega/luke_s88_vo.wav` |
| 2 | S46 | So every raptor you've ever feared… was basically this guy, with a rebrand. | `audio/dinoverse_omega/luke_s46_punchline.wav` |

---

## 8. ⚠️ S46 — the biggest finding. Read before generating.

The board gives S46 **13s**. **The clip actually in `rough_cut_v6` is 6.04s** — and Grok crushed the whole scripted exchange into it as word-salad. This is the measured transcript of what is in the cut today:

> *"Here's what the movies got wrong. The famous velociraptors, real as raptors the size of a turkey **will how actually drew was ever feared. That's easy like this guy with a rebrand.**"*

The "**that's a Utahraptor**" payoff — the entire point of the scene — **is not in the episode.** Luke's punchline got slurred into the ranger's voice. The clip is junk audio end to end.

**The timing does not work and cannot be made to work by generating alone:**

| | words | est. speech @2.6 wps | clip today |
|---|---|---|---|
| RANGER turn | 36 | **13.85s** | 6.04s |
| LUKE punchline | 13 | 5.0s | (same clip) |
| **total + a beat** | | **≈19s** | **6.04s** |

**S46 must stretch from 6.04s to ≈19s** (hold on the raptor / the size-comparison board / cutaways while the VO plays), **or** the ranger line has to be cut down — which is a *script* change and therefore **the owner's call, not mine.** I did not paraphrase the line to make it fit. The text above is verbatim.

---

## 9. Two-speaker rows — analysed, and ALL excluded by default

A two-speaker clip can only be half-dubbed if Luke is **off-camera** in it **AND** his speech is **separable in time**. GF is on camera in most of them and her lip-sync is the thing we are protecting. Per the brief: conservative, flag rather than include.

| Shot | Speaker | Luke's words | Verdict |
|---|---|---|---|
| S13 | LUKE / GF | Okay - we're back at Dino Zoo. | **BLOCKED** — Luke ON CAMERA (selfie two-shot). |
| S13b | LUKE / GF (off-cam) | It's got the best dinos on earth- | Both off-camera; but Luke's half is a **set-up whose punchline is GF's overlapping interruption** — splitting it re-times her line. **Excluded.** |
| S14 | CLERK / LUKE | Any chance of a discount for repeat trauma? | Luke off-camera (POV), but his line sits **between two CLERK turns** — dubbing it alone leaves the clerk in Grok's voice mid-exchange. **Excluded.** |
| S15 | GF / LUKE | Everyone's here for the new exhibit. The one they've been hyping. | GF on camera a step ahead; Luke's turn is second and separable. **Excluded — borderline, flag for owner.** |
| S16 | LUKE / GF | ...'Hybrid Enclosure - Staff Only.' ... / I'm just reading. | **Three turns, Luke on both ends around GF's "Luke. No."** Not cleanly separable. **Excluded.** |
| S24 | LUKE / GF | Okay THAT is huge. / ...oh no. | Luke brackets GF's turn. **Excluded.** |
| S30 | GF / LUKE | Twenty, thirty years, they think. What do you think? | Separable (Luke second). **Excluded — borderline, flag for owner.** |
| S31 | GF / LUKE | Later. Water first. | Separable but tiny. **Excluded.** |
| S38 | RANGER / LUKE | No thank you. | 3 words after the ranger's PA line + a crowd gasp. **Excluded.** |
| S41 | GF / LUKE | ...hey. Look. | Separable. **Excluded — borderline.** |
| S42 | LUKE / GF | Those kids have been by that door twice now. | Luke first, GF second. Separable. **Excluded — borderline, flag for owner.** |
| S46 | RANGER / LUKE | So every raptor you've ever feared... was basically this guy... | **PASS_LUKE_EXTRA (opt-in)** — hosts off-camera, Luke's turn is last, and the RANGER half is being dubbed anyway. See F2. |
| S49 | GF / LUKE | It's definitely looking at you. | Separable. **Excluded — borderline.** |
| S55 | GF / LUKE | Biggest animal to ever walk the earth. Ate 150 kilos of plants a day. | Separable (Luke second, long). **Excluded — borderline, flag for owner.** |
| S57 | GF / LUKE | To grind food in their stomach. No teeth needed. | Separable. **Excluded — borderline.** |
| S58 | GF / LUKE | Yeah. Toward the door. | Separable. **Excluded — borderline.** |
| S59b | GF / LUKE | — (none) | **Luke has NO words in this cell.** Nothing to dub. |
| S59c | GF / LUKE | ...they have a McDonald's? | Luke first, GF second. **Excluded.** |
| S60 | GF / LUKE | ...you don't think those kids actually got in, do you? | Luke's turn is **between two GF turns**. **Excluded.** |
| S62 | RANGER / LUKE | ...is that safe? | Luke's turn is **between two RANGER turns**. **Excluded.** |
| S65 | LUKE / GF | Whoa. (BOTH) | **BOTH speak the same word simultaneously.** Not separable. **Excluded.** |
| S68 | GF / LUKE | ...the hybrid zone. | Separable. **Excluded — borderline.** |
| S69 | GF / LUKE | ...we have to tell someone. | Separable. **Excluded — borderline.** |
| S73 | LUKE / GF | It can camouflage. One second it's there- | GF **completes Luke's sentence** ("-and then it's not."). Splitting breaks the joke's timing. **Excluded.** |
| S75 | GF / LUKE | People think he's a monster. But is he? | Separable (Luke second). **Excluded — borderline, flag for owner.** |

**Owner decision point:** the ~10 rows marked *borderline* are all "Luke's turn is second and cleanly separable". They could be dubbed in a later pass. I have **not** included them — the brief said be conservative, and each one carries a real risk of a seam between Grok-Luke and TTS-Luke **inside a single clip**, which is more jarring than a seam between clips.

---

## 10. Timing — what the assembler must handle

`est_tts_speech_seconds` = words ÷ 2.6 (the same conservative rate the v1 manifest uses). Measured reality: **Grok's Luke speaks at 3.29 wps** (`speaking_rate_FINAL.json`), so 2.6 over-predicts the length of every line. Both numbers are given.

These are **off-camera** dubs, so the new line does not have to match the old speech window — it only has to fit inside the **clip**.

| Shot | words | est @2.6 | est @3.29 | old speech | clip | headroom @2.6 |
|---|---|---|---|---|---|---|
| S17 | 9 | 3.46s | 2.74s | 3.56s | 6.04s | 2.58s |
| S19 | 7 | 2.69s | 2.13s | 2.3s | 6.04s | 3.35s |
| S21 | 17 | 6.54s | 5.17s | 5.14s | 6.04s | -0.5s **⚠️** |
| S22 | 18 | 6.92s | 5.47s | 5.18s | 6.04s | -0.88s **⚠️** |
| S26 | 9 | 3.46s | 2.74s | 3.88s | 6.04s | 2.58s |
| S28 | 6 | 2.31s | 1.82s | 4.1s | 6.04s | 3.73s |
| S29 | 15 | 5.77s | 4.56s | 4.24s | 6.04s | 0.27s **⚠️** |
| S32 | 3 | 1.15s | 0.91s | 2.28s | 6.04s | 4.89s |
| S33 | 6 | 2.31s | 1.82s | 1.48s | 6.04s | 3.73s |
| S35 | 9 | 3.46s | 2.74s | 3.98s | 6.04s | 2.58s |
| S40 | 18 | 6.92s | 5.47s | 5.64s | 10.04s | 3.12s |
| S43 | 11 | 4.23s | 3.34s | 3.62s | 6.04s | 1.81s |
| S48 | 8 | 3.08s | 2.43s | 3.42s | 6.04s | 2.96s |
| S50 | 12 | 4.62s | 3.65s | 5.58s | 6.04s | 1.42s |
| S52 | 10 | 3.85s | 3.04s | 4.0s | 6.04s | 2.19s |
| S54 | 6 | 2.31s | 1.82s | 2.06s | 6.04s | 3.73s |
| S56 | 4 | 1.54s | 1.22s | 2.68s | 6.04s | 4.5s |
| S59 | 3 | 1.15s | 0.91s | 3.1s | 6.04s | 4.89s |
| S61 | 6 | 2.31s | 1.82s | 3.06s | 6.04s | 3.73s |
| S63 | 8 | 3.08s | 2.43s | 3.48s | 6.04s | 2.96s |
| S67 | 17 | 6.54s | 5.17s | 4.62s | 10.04s | 3.5s |
| S71 | 10 | 3.85s | 3.04s | 2.96s | 6.04s | 2.19s |
| S74 | 10 | 3.85s | 3.04s | 3.16s | 10.04s | 6.19s |
| S76 | 6 | 2.31s | 1.82s | 1.52s | 6.04s | 3.73s |
| S78 | 2 | 0.77s | 0.61s | 1.66s | 10.04s | 9.27s |
| S81 | 5 | 1.92s | 1.52s | 1.78s | 6.04s | 4.12s |
| S88 | 12 | 4.62s | 3.65s | 4.96s | 6.04s | 1.42s |

**⚠️ Risk R3 — three lines overflow their clip at the conservative 2.6 wps:** **S21** (−0.50s), **S22** (−0.88s), **S29** (+0.27s, inside the margin). At the measured 3.29 wps **all three fit comfortably.** So this is most likely an artifact of the conservative estimate — but if the take does come back long, the fixes are free and in this order: (1) ElevenLabs' per-generation **speed** control, (2) hold the last frame of the 6.04s clip for ~1s. **Do not paraphrase the line to make it fit.**

---

## 11. Bonus: the re-voice also fixes 4 Grok script deviations

Dubbing restores the *scripted* line, which silently repairs these:

| Shot | Grok actually said | Scripted line (what the dub restores) |
|---|---|---|
| **S50** | "Comment **you to Raptor** if you learned something… What do you think?" | "Comment 'Utahraptor' if you learned something. Let's give the internet a quiz." |
| **S52** | "**Starchosaurus**… Yeah, looks like it." | "Styracosaurus — all those spikes are just for show. Mostly." (this is the owner's flagged S52 ad-lib) |
| **S28** | "…seeing that. **They're so close.**" | "Imagine looking up and seeing that." |
| **S59** | "Okay, now food. **Come on!**" | "Okay, NOW food." |

S50 and S52 are real content bugs — Grok **mispronounced the dinosaur names the scene is about**. The dub fixes both for free.

---

## 12. Pre-Generate checklist (per pass — this is the whole point)

1. Voice + model selected. Model **must be Eleven Multilingual v2**.
2. **Paste** the block — never type it.
3. Read the textarea back out of the DOM and SHA-256 it:
   ```js
   const t = document.querySelector('textarea').value;
   crypto.subtle.digest('SHA-256', new TextEncoder().encode(t))
     .then(b => console.log([...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')));
   ```
4. It must equal the SHA for that pass **exactly**. If not: clear, re-paste, re-check. Usual culprits — a smart-quoted apostrophe, a trailing newline, the editor eating the blank lines around a break tag.
5. Only then click **Generate**. Once.

> **Clipboard warning** (memory, learned the hard way): pasting collides with the owner's live clipboard. **Re-set the clipboard immediately before every Cmd+V.**

---

## 13. Splitting + dubbing recipe (free, repeat as needed)

```bash
# 1. split a pass at its 3.0s silences
ffmpeg -i audio/dinoverse_omega/source_chunks/luke_body_pass.mp3 \
  -af silencedetect=noise=-40dB:d=1.2 -f null -
# expect n_lines-1 silences. If the count is off, loosen to -45dB:d=0.9 and re-run.
# Cut at the MIDPOINT of each silence, keep ~0.3s handles, export 48k WAV.

# 2. dub a clip: strip Grok's speech, keep the ambience, lay the new line on top.
#    (demucs is already proven in this dir - see sep/htdemucs/)
demucs --two-stems=vocals -n htdemucs -d cpu v2/clips/S17.mp4
#    -> no_vocals.wav = ambience/SFX with the speech removed. Mix luke_s17.wav over it.
```

A mis-split is free to redo. A bad take is not. That asymmetry is why the passes are batched.

---

## 14. Output convention

```
audio/dinoverse_omega/
├── luke_s17.wav
├── luke_s19.wav
├── luke_s21.wav
├── luke_s22.wav
├── luke_s26.wav
├── luke_s28.wav
├── luke_s29.wav
├── luke_s32.wav
├── luke_s33.wav
├── luke_s35.wav
├── luke_s40.wav
├── luke_s43.wav
├── luke_s48.wav
├── luke_s50.wav
├── luke_s52.wav
├── luke_s54.wav
├── luke_s56.wav
├── luke_s59.wav
├── luke_s61.wav
├── luke_s63.wav
├── luke_s67.wav
├── luke_s71.wav
├── luke_s74.wav
├── luke_s76.wav
├── luke_s78.wav
├── luke_s81.wav
├── luke_s01.wav
├── luke_s03_montage.wav
├── luke_s12.wav
├── luke_s89_cta.wav
├── gf_s02.wav
├── gf_s11.wav
├── gf_s89_closer.wav
├── ranger_s46.wav
├── luke_s88_vo.wav
├── luke_s46_punchline.wav
└── source_chunks/
    ├── luke_body_pass.mp3
    ├── luke_shout_pass.mp3
    ├── luke_pass.mp3
    ├── gf_pass.mp3
    ├── ranger_s46_pass.mp3
    └── luke_extra_pass.mp3
```

Audio is gitignored — **keep the source chunks.** They cannot be regenerated for free.
