# NEXT SESSION — Dinoverse "Omega Rex" (episode_01) — resume here

**Paste-to-resume prompt** (put this in a fresh session):
> Read `dinoverse_clone/episode_01_omega_rex/v2/NEXT_SESSION.md` and continue the Dinoverse
> "Omega Rex" episode. Task B (ElevenLabs VO) is ✅ DONE — 36 lines generated, SHA-verified,
> in `audio/dinoverse_omega/` (commit `649c392`). The episode had a bigger defect than the
> thin cold open: **Grok gave both hosts a different voice in nearly every clip**, and the
> owner approved a surgical fix (re-voice LUKE only — he's off-camera in 25 of 27 clips).
> The VO is generated and fits. Now do TASK C — the assembly: strip Grok's speech from
> Luke's clips and mix the new VO under them, re-time the cold open, stretch S46, then the
> final pass (music/SFX, logo card, midroll, 1080p master). Use `venv/bin/python`; commit
> + push when work lands.

---

## ⚠️ THE HEADLINE FINDING (2026-07-14) — read this first

Task B was scoped as "a VO for the cold open + end card." Doing it surfaced something worse.

**A full census of every host-dialogue clip (43 solo + 20 two-speaker, 0 failures) proved
Grok i2v rendered each host with a DIFFERENT VOICE in nearly every clip.**

| | range | clips | outliers |
|---|---|---|---|
| **LUKE** | **128 – 392 Hz** | 27 solo | 17 |
| **GF** | **160 – 465 Hz** | 16 solo | 8 |

The killer detail is not the spread but the **mid-scene jumps**: Luke's three consecutive
Aquatic lines run **S32 207 Hz → S33 353 Hz → S35 162 Hz** — three different men in ~20
seconds of one conversation. 10 of Luke's 18 within-scene consecutive line-pairs jump >50 Hz.
The registers even cross over (Luke's S21 at 241 Hz is *higher* than GF's S34 at 149 Hz).

**Ruled out as artifact four ways** — demucs vocal isolation (bed is only 1–3% of vocal RMS),
an independent torchaudio autocorrelation tracker (never lands on 2×/0.5×), a harmonic-comb
test, and a storyboard Speaker-column cross-check. The *in-band* clips cluster tightly
(Luke 41 Hz band, GF 39 Hz), so a "real Luke" (~197 Hz) and "real GF" (~235 Hz) do exist —
the outliers simply aren't them.

Data: `work/vo_prep/voice_drift_census.json`, `voice_acoustics_STEMS.json`, `octave_arbiter.py`.
Hear it yourself: `work/vo_prep/LUKE_voices_isolated.mp3` (dialogue with ambience stripped).

**This — not the thin cold open — is very likely what made the cut feel wrong.**

### OWNER DECISION (locked): surgical fix
Re-voice **LUKE only**. He is off-camera in **25 of 27** clips, so dubbing is clean.
**GF is NOT re-voiced in the body** — she is on camera in ~16 clips and dubbing would break
lip-sync. She keeps her Grok audio and gets only her 3 cold-open/end-card lines.

⚠️ **The board's camera labels are NOT what Grok shot.** 8 rows labelled "walking POV"
(S23/S31/S32/S37/S41/S50/S59/S61) shipped as full-face talking heads. Do not trust the
Camera column — 40 evidence frames are in `work/vo_prep/feas/`.

---

## TASK B — ElevenLabs VO — ✅ DONE 2026-07-14 (commit `649c392`)

**36 lines generated, one-pass, no re-rolls.** Every pass SHA-256 verified in the browser
textarea against `vo_manifest_v2.json` before clicking Generate.

| pass | voice | chars | lines | out |
|---|---|---|---|---|
| PASS_LUKE_BODY | **Liam** | 1812 | 23 | 111.2 s |
| PASS_LUKE_COLDOPEN | Liam | 375 | 4 | 25.6 s |
| PASS_LUKE_SHOUT | Liam (stab 34% / style 29%) | 101 | 3 | 14.2 s |
| PASS_LUKE_EXTRA | Liam | 170 | 2 | 12.9 s (S88 + S46 punchline) |
| PASS_GF | **Jessica** | 152 | 3 | 11.6 s |
| PASS_RANGER | **Brian** | 224 | 1 | 15.8 s |

**Voices** (owner A/B'd Liam vs Chris on real lines): LUKE = **Liam**, GF = **Jessica**,
RANGER = **Brian**. Liam also reads ~172 wpm vs Chris's ~153 (Grok-Luke was 197 wpm), so he
minimises dub overrun. Model = **Eleven Multilingual v2** (honours `<break>` tags; v3 does NOT).

**DUB-FIT: SOLVED.** The conservative 2.6 wps estimate predicted S21/S22 would burst their
6.04 s clips. Measured actuals: **all 23 body lines FIT, zero overruns**, tightest S21 at
+0.91 s headroom. No speed nudges, no time-stretch, no held frames needed.

**Bonus — the dub fixes 4 real Grok script deviations**, two of them genuine content bugs:
Grok said **"YOU TO RAPTOR"** (S50, = "Utahraptor") and **"STARCHOSAURUS"** (S52, =
"Styracosaurus") — in the very scenes about those animals. Plus ad-libs in S28 and S59.

**Whisper QA** (`qa_vo_transcripts.py`, all 36 lines): both content bugs fixed; the S46
ranger now clearly says **"that's a Utahraptor."** The 10 lines the matcher flagged are ASR
artifacts (quote marks, "part 2" vs "part two", dropped articles), not audio defects.
Only genuine imperfection: **S29's "Hatzegopteryx" is approximated** — and that line's own
joke is *"you'll want to Google that spelling"*, so it stays (no-re-rolls rule).

Files: `audio/dinoverse_omega/*.wav` (36, gitignored, 24 MB) + `source_chunks/*.mp3`.
Splitter: `work/vo_prep/split_vo_passes.py` — **note `GAP_MIN=2.0` for the shout pass**
(looser stability made Liam add 1.2–1.5 s dramatic pauses *inside* lines; a 1.2 s threshold
mistakes those for line boundaries).

---

## TASK C — ASSEMBLY (next up)

### C1. Mix the VO into the body — the dub
For each of the 23 Luke body clips + S88: **strip Grok's speech but KEEP the clip's
ambience/SFX**, then lay the new Liam line under it.
```bash
# proven in this dir already (sep/htdemucs/)
venv/bin/demucs --two-stems=vocals -n htdemucs -d cpu clips/Sxx.mp4   # keep no_vocals.wav
# then mix: no_vocals + audio/dinoverse_omega/luke_sXX.wav
```
Align the new line to the clip's existing speech window (`work/vo_prep/speech_spans.json`
has ffprobe + word-timestamp measurements per clip). All lines fit — pad with silence.

### C2. Cold open — re-time to the narration
The boarded durations CANNOT hold the VO. Measured:

| shot | boarded | VO actual | action |
|---|---|---|---|
| S01 card | 2.0 s | 2.98 s | hold ≈3.5 s |
| S02 selfie | 3.0 s | 2.98 s | hold ≈3.5 s |
| S03–S10 montage | 12.0 s (8×1.5) | **6.89 s** | **fits** — 5 s headroom |
| S11 | 1.5 s | 1.27 s | fits |
| S12 hook | 2.0 s | 3.48 s | extend ≈4 s |
| **S89 end card** | **2.0 s** | **7.02 s** (1.80 GF + 5.22 Luke) | **stretch to ≈7.5 s** |

S89 **plays GF first, then Luke** (closer *before* CTA). This card IS the ending the owner
said the video lacked — do not squeeze it back to 2 s.
Also: the S03–S12 flashes currently carry native roar/SFX at full level → **duck them under
the montage VO**. S12's flash borrows S85's roar as temp audio (`flash_audio_plan.json`) →
the final mix replaces it.

### C3. S46 — stretch 6.04 s → ~19 s  ⚠️ OWNER DECIDED: keep the script, extend the clip
The board gives S46 13 s. The shipped clip is **6.04 s** and Grok crushed the exchange into
word-salad — the "that's a Utahraptor" payoff **is not in the episode at all**.
Ranger VO = 15.8 s + Luke's punchline 5.38 s ⇒ needs ≈19–21 s.
**Do NOT swap in `clips/S46_roll_talking.mp4`** — that is the talking-raptor take the owner
personally rejected on Jul 13 (jaw opens and modulates 6.0–9.0 s across the payoff line;
see `work/vo_prep/S46_alt_head_grid.png`), and it mumbles the word as "otteraptor" anyway.
Cover the extra ~13 s with: hold on the raptor / a size-comparison insert / cutaway reactions.

### C4. S13 + S37 — re-roll as POV  ⚠️ OWNER APPROVED
Luke's only 2 on-camera speaking clips. Re-roll both in Grok so he is NOT on camera
(S37's board row *already says* "walking POV" — Grok ignored it). Then Luke is 100% one
consistent voice with zero exceptions. Grok quota ~25% used, resets **Jul 20**.
S13 is the face-lock reference for S02 — the **still** stays, only the clip changes.

### C5. S02 still  ⚠️ OWNER APPROVED (with a change)
Generate in ChatGPT with the S13 Luke+GF face-lock, then Grok i2v to a 3 s clip.
**CHANGE: frame it POV / back-of-head, NOT a gate selfie** — as boarded it becomes an 18th
lip-sync blocker; framed POV it costs nothing. GF's line plays as VO over it either way.

### C6. Final pass
- **Music beds** — library is a corporate-crime-doc palette; nothing covers the dominant
  cues (`light doc bed` ×39, `trailer sting` ×12, upbeat/calm/warm). Needs new Pixabay CC0
  sourcing (project rule: **Pixabay = music only**).
- **SFX** — **zero dino/zoo sounds exist** (no roar, alarm, crowd, splash). Whole TSV col-12
  spotting list is unserviceable with the 38 generic files in `assets/sfx/`.
- **DINO ZOO logo** — **no logo image exists anywhere** in the repo. Must be created (round
  green mark, `#2ecc40`) to replace the S01 drawtext card.
- Midroll marker at S60 · 1080p master (segments are 1264×720 today).
- **No audio-mix stage exists** — `assemble_rough_cut.py` concats with `-c copy`, so nothing
  can be layered. **Adapt `scripts/ffmpeg_production_render.py:build_audio_mix()` (L578)** —
  it already has narration + music + SFX + sidechain-ducked bed. **Do not build a parallel
  mixer** (hard rule #3). `scripts/audio_master.py` = 2-pass loudnorm for the final master.

---

## OPEN / DEFERRED
- **GF still drifts** (160–465 Hz) and is NOT being fixed — she's on camera. Accepted.
- **~10 borderline two-speaker rows** (S15/S30/S41/S42/S49/S55/S57/S58/S68/S69/S75) where
  Luke's turn is last and cleanly separable. Excluded from the dub — mixing TTS-Luke and
  Grok-Luke *inside one clip* is more jarring than a seam between clips. Revisit only if the
  clip-to-clip seams turn out to bother the owner.
- **S79** native audio has an unscripted ad-lib tail beyond the board line.
- **S65** ("BOTH: Whoa") — the one clip whose dialogue no transcript could confirm.
- The 8 dropped dread-stack trims (`DROP_SHOTS`) would need distinct alt-angle gens if ever
  restored — they were literal footage repeats.

## Pipeline cheat-sheet
- **Assembler:** `work/assemble_rough_cut.py` → `work/rough_cut/rough_cut_vN.mp4` (bump N).
  Current: **rough_cut_v6.mp4, 8:45.2, 94 shots, 1 placeholder (S02)**. mp4 gitignored.
- **VO manifest (source of truth):** `work/vo_prep/vo_manifest_v2.json` — per-line SHA,
  target wav, clip duration, measured speech span. `verify_revoice.py` = 182 self-checks.
- **Grok i2v loop / QA:** see `PIVOT_PLAN.md` §I2V TRACK. Clipboard collides with the owner's
  live clipboard — re-set it immediately before every Cmd+V.
- Use `venv/bin/python`. Commit + push when work lands.
