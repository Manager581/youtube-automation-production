# @wildbirdsurvival Replication — Copy-Paste Prompt Templates

These operationalize the forensic findings (see `FORENSICS.md`). Fill the `{{BRACKETS}}`.

---

## A. Topic gate (run before anything else)
A topic qualifies ONLY if it passes all four:
1. **Two animals**, one surprising relationship (conflict OR symbiosis). Not a single-species portrait.
2. **A curiosity gap or stakes** you can put in a title ("Why does X let Y…", "…Fight to the Death").
3. **NOT** framed as "Full Life Cycle of [common animal]" (every loser used this).
4. Not the same hero animal as your last 2 uploads, and not a weak clone of your own recent hit.

---

## B. Script prompt (Claude)
```
You are writing narration for an 8–10 minute faceless AI wildlife documentary in the style of
high-retention YouTube nature channels. Topic: {{TWO-ANIMAL RELATIONSHIP, e.g. "how oxpeckers
clean a tick-covered rhino"}}.

HARD CONSTRAINTS (measured from top-performing videos):
- Total narration ~1,100–1,300 words ONLY. The video is ~50% wordless; music + visuals carry the rest.
- Present tense, cinematic, sensory. British spelling.
- Reading pace ~150 wpm, calm and measured (a deep documentary-narrator voice will read this).
- Follow this 6-beat arc:
  1. COLD OPEN (0–15s): one SPECIFIC individual animal in visceral distress. First sentence names
     the jeopardy. Lead with a shocking sensory detail (parasites, wounds, a predator, the cold).
  2. ESCALATION: "it has tried everything… nothing works."
  3. THE TURN: an unexpected savior/partner appears. Write "[PAUSE 12s]" on its own line BEFORE this.
  4. THE PAYOFF: describe the remarkable behavior slowly; this is where we HOLD one long shot.
  5. EXPOSITION: the wider relationship / why it evolved.
  6. RESOLUTION: a calm philosophical theme line about balance/partnership/survival, then the
     animals depart. No "subscribe" line in the narration itself.

FORMAT: output as a numbered shot list — ONE sentence (or clause) per line = one visual. Mark
wordless music beats as "[MUSIC ONLY — Ns]". Aim for ~60 lines. After each line, in brackets, give
a 1-line VISUAL DIRECTION for the shot (camera + subject + action).
```

## C. Veo / Grok / Sora shot-prompt template (per line)
For each script line, generate an ~8s clip. Template:
```
Photoreal 8K wildlife documentary shot, natural daylight, shallow depth of field, cinematic color
grade. {{SUBJECT}} {{ACTION}}. Camera: {{slow push-in / low tracking / macro close-up / aerial}}.
Setting: {{African savanna / river / cliff}}. No text, no captions, no people. Realistic animal
anatomy and movement.
```
Rules baked in from the teardown:
- **Hook shots:** first shot is the animal's FACE or a MACRO of the distress detail — never a wide
  empty landscape. Get a shocking macro (parasites / wound / teeth) into shot 1–2.
- **Seed for consistency:** generate ONE hero-animal reference still, then use image-to-video from
  that still for every clip of that animal so it stays identical across ~60 shots.
- **Payoff shot:** generate a longer/held take of the remarkable behavior — you'll keep 20–35s of it.
- Keep every clip ON the subject; avoid tiny-animal-in-wide-landscape (a loser tell).

## D. Assembly rules (your FFmpeg renderer)
- Trim the 8s clips: **median 3–4s on screen**, ~40% of shots under 3s (energy), a few held >10s.
- **Do NOT cut on every sentence.** Let shots run across narration; cut when the image changes.
  Keep cutting through the wordless music passages. (Target: only ~45% of cuts near a word.)
- **Narration coverage ~40–50%** of runtime. Insert the scripted [PAUSE] as real silence.
- **One continuous music bed** (Pixabay), swelling under the payoff, falling at the golden-hour
  outro. **No whoosh/impact SFX on cuts.** Diegetic splashes/wingbeats at most.
- No burned-in captions anywhere.
- Final shot: golden-hour wide, animals departing, over the philosophical theme line.

## E. Voice (ElevenLabs)
Deep male documentary voice (fundamental ~80–90 Hz), high Stability (steady, low pitch variance),
speed ~0.9–1.0, ~150 wpm. One pass over the locked script. Not bright or hyped.

## F. Package (Claude)
- **Title:** curiosity question OR conflict stakes. Front-load the surprising pairing. Never "Full Life Cycle."
- **Thumbnail:** extreme close-up of face/gore/conflict + **2–3 words** (yellow/white, thick black
  outline): "FATAL MISTAKE" energy.
- **Description:** one tight story paragraph (problem → struggle → surprising partner → payoff) +
  3 hashtags. STRIP any template scaffolding before upload.

---

## G. Verified 13-step build recipe (from the adversarial pass — exact numeric targets)
0. **LOCK THE CLICK FIRST** (this is where win/loss lives, not pacing): one dramatic single-encounter
   topic + curiosity/stakes title + 2–3-word shock thumbnail. **Ban "full life cycle" / biography
   framings** (the one true flop was a life-cycle peregrine). Don't publish a near-clone of your own
   recent hit within a day or two (that cannibalized a twin to 3K).
1. **Outline 5 beats, one throughline:** cold-open jeopardy → escalation (failed self-help) → the
   turn (ally/predator arrives) → on-screen payoff → one-sentence theme. If it has >1 hunt or the
   word "cycle," cut it down.
2. **Hard word budget:** total script words ≤ ~1.5 × runtime-seconds. 9-min video = ≤~810 spoken
   words, ≤~4.5–5 min of speech; leave 45–55% wordless. If a draft narrates >60%, delete sentences.
3. **First sentence** names one specific animal + what's hurting it. **Ban** encyclopedic openers
   ("famous for…", "one of nature's most extraordinary…") and glamour adjectives in the first 20s.
4. **Voice** slow/calm at 2.3–2.6 wps (~140–155 wpm), never >2.7. Composite density (coverage×wps) ≤~1.5.
5. **Generate ~8s Veo i2v clips**, single TTS narrator, single music bed, NO captions.
6. **Body baseline slow:** median shot 3.6–4.7s, mean 5.6–7.1s, ≤~48% of shots ≤3s. Don't trim
   everything for "energy" (the cleanest winner/loser separator).
7. **Hook (first 0:60) = 9–11 cuts, hook mean-shot ≥5s.** If >11 cuts before 0:60, delete down. If
   first word is delayed past ~15s, hold 1–2 long (12–18s) escalating shots — never oscillate short cuts.
8. **3–5 payoff holds of 15–35s** each, ≤1 sentence over them (ideally near-wordless). ~13–19 total
   holds of 10s+.
9. **One action climax:** stack 6–12 sub-2s cuts bracketed by 5–10s holds (hold→burst→hold); let one
   action beat run wordless 20–30s+. Longest wordless gap >25s; 8–12 more ≥5s gaps between lines.
10. **Time cuts to on-screen action** (peck/lunge/splash), a beat off the narration. Don't gate on
    on-word %; just avoid karaoke-tight cutting over dense wall-to-wall VO.
11. **Mix:** one continuous bed ~12–20 dB under VO at CONSTANT level (no crescendos/auto-ducking).
    3–12 diegetic SFX on real events. **No whooshes/risers/impacts on cuts — every transition silent.**
12. **Energy arc:** loudest music+VO moment in the first ~30% (first ~2.5–3 min), never at/after 50%.
13. **QA gates before publish:** (a) hook 9–11 cuts / mean ≥5s; (b) median shot 3.6–4.7s, ≤48% ≤3s;
    (c) coverage ≤55–60%, ≥45% wordless; (d) wps ≤2.7, density ≤~1.5; (e) ≥1 wordless gap >25s +
    13–19 holds ≥10s; (f) energy peak before 30%; (g) no transition SFX. **These are retention/quality
    gates — they do NOT guarantee views** (a video passing all of them still drew 3K). Views come from Step 0.
```
```
