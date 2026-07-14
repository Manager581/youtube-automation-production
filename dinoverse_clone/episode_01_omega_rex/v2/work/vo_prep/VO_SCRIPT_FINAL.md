# VO SCRIPT — FINAL / LOCKED
**Episode:** Dinoverse clone — episode_01 "Omega Rex"
**Scope:** cold open (S01–S12) + end card (S89). 7 lines, 2 voices.
**Rule:** ONE generation per pass, **no re-rolls** (memory `elevenlabs-one-pass-rule`).
**Source of truth:** `dinoverse_clone/episode_01_omega_rex/STORYBOARD.tsv`, column `Dialogue / VO`.
**Machine-readable twin:** `vo_manifest.json` (same dir) — holds every SHA-256.

> This file is LOCKED. Do not edit a word after the owner blesses it. The pre-Generate
> moment is the last chance to change anything; after that, what comes out is what ships.

---

## 0. TSV verification (done)

All 7 lines were re-read from the TSV with `csv.DictReader(delimiter='\t')`.
**No discrepancies in wording. Nothing was "improved."**

Two things worth knowing:

1. **S89 order.** The TSV puts the GF line **first**, then Luke:
   `GF VO: "...we are never coming back." LUKE VO: "Comment which dino you'd survive. Subscribe - part two if this hits."`
   So the end card plays **GF closer → Luke CTA**, not the other way round.
2. **S03 is one continuous line over 8 flashes.** The TSV says so explicitly
   ("LUKE VO (over the whole montage)"); S04–S10 read `(VO continues)` — they are **not**
   separate lines and must not be generated separately.

### Typography normalizations (the ONLY changes from TSV text — 3 total)

| Shot | TSV | Locked text | Why |
|---|---|---|---|
| S03 | `exist... and` | `exist… and` | single U+2026 ellipsis; identical meaning, more reliable pause rendering than three periods |
| S89 LUKE | `Subscribe - part two` | `Subscribe — part two` | TSV has a lone ASCII hyphen between words. A hyphen there is either swallowed (run-on: "subscribe part two") or read as a compound. An em dash gives the beat the line is written for. |
| S89 GF | `...we are never` | `…we are never` | same U+2026 normalization |

**Nothing else changed.** Apostrophes stay **ASCII** (`didn't`, `you'd` — U+0027, not curly).
Do not let any editor smart-quote them: it changes the bytes and breaks the SHA check.

---

## 1. Recommended split: **2 generations — one per voice**

Not 7. Reasoning:

- **Prosody.** ElevenLabs conditions on the whole submitted text. Lines generated together
  share one performance — same energy, same room tone. Seven separate generations of the
  same cold open will sound like seven different sessions cut together, and with no re-rolls
  allowed there is no fixing that.
- **Blast radius.** Every generation is an irreversible take. 7 generations = 7 chances to
  get a dud you're stuck with. 2 = two.
- **Cost is per character, not per generation**, so splitting into 7 saves nothing.
- **Splitting is the only real cost of the 2-pass approach, and it is zero-risk.** If the
  silence-split lands badly you re-split the same WAV, free, as many times as you like.
  A mis-split is recoverable. A bad take is not. Trade the recoverable risk, never the other one.
- **Verification burden.** 2 SHA checks before 2 clicks, instead of 7 chances to paste the
  wrong chunk.

Long silences are what make the split work, so the lines inside each pass are separated by
**`<break time="3.0s" />`** — far longer than any natural sentence gap, so `silencedetect`
cannot confuse a line boundary with a comma.

### ⚠️ Model requirement (check before pasting)

`<break time="x" />` is honoured by **Eleven Multilingual v2** and **Turbo v2.5**
(the family the Spino/Lagos video used — proven). **Eleven v3 does not honour break tags.**
- Owner picks v2 / Turbo v2.5 → use the 2-pass script below. **This is the plan.**
- Owner insists on v3 → fall back to **7 per-line generations**
  (`generation_passes_fallback_per_line` in `vo_manifest.json`, each with its own SHA).
  Do not paste break tags into v3 — an unhonoured tag can be spoken aloud, and that burns the take.

No bracketed stage directions / audio tags anywhere in the locked text: v2 would **read them out
loud**. The script is deliberately model-agnostic plain text.

---

## 2. PASS 1 — LUKE  (4 lines, 375 chars)

**SHA-256 of the paste text:** `276cc9ae441aef8efc109cd4f34d40bf33daff6a21c879cb827704a0468e48ff`
**Save the download as:** `audio/dinoverse_omega/source_chunks/luke_pass.mp3`

Paste **exactly** this into the ElevenLabs textarea (blank line, break tag, blank line between lines):

```
So last time, we barely made it out of the dinosaur zoo alive.

<break time="3.0s" />

A T-Rex. A raptor pack. Two hybrids that should not exist… and three kids who thought a locked door was a dare.

<break time="3.0s" />

Stay till the end. You will not believe how this one ended.

<break time="3.0s" />

Comment which dino you'd survive. Subscribe — part two if this hits.
```

Segments, in the order they will come out of the split:

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S01 (card) | So last time, we barely made it out of the dinosaur zoo alive. | `audio/dinoverse_omega/luke_s01.wav` |
| 2 | S03–S10 (montage) | A T-Rex. A raptor pack. Two hybrids that should not exist… and three kids who thought a locked door was a dare. | `audio/dinoverse_omega/luke_s03_montage.wav` |
| 3 | S12 (hook) | Stay till the end. You will not believe how this one ended. | `audio/dinoverse_omega/luke_s12.wav` |
| 4 | S89 (CTA) | Comment which dino you'd survive. Subscribe — part two if this hits. | `audio/dinoverse_omega/luke_s89_cta.wav` |

---

## 3. PASS 2 — GF  (3 lines, 152 chars)

**SHA-256 of the paste text:** `52fe5a136a1f3621e405a0b70a1faefa582ff032b629aa6c8ac85d8b52657b7b`
**Save the download as:** `audio/dinoverse_omega/source_chunks/gf_pass.mp3`

```
This time we found the part they really didn't want us to see.

<break time="3.0s" />

Remember them.

<break time="3.0s" />

…we are never coming back.
```

| # | Shot | Line | → WAV |
|---|---|---|---|
| 1 | S02 (selfie) | This time we found the part they really didn't want us to see. | `audio/dinoverse_omega/gf_s02.wav` |
| 2 | S11 (teens at the door) | Remember them. | `audio/dinoverse_omega/gf_s11.wav` |
| 3 | S89 (closer) | …we are never coming back. | `audio/dinoverse_omega/gf_s89_closer.wav` |

---

## 4. Pre-Generate checklist (per pass — do this, it is the whole point)

1. Voice + model selected (owner's choice; model must be Multilingual v2 or Turbo v2.5).
2. Paste the block. **Do not type it** — typing invites a silent typo.
3. Read the textarea back out of the DOM and SHA-256 it:
   ```js
   // in the browser console / via javascript_tool
   const t = document.querySelector('textarea').value;
   crypto.subtle.digest('SHA-256', new TextEncoder().encode(t))
     .then(b => console.log([...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')));
   ```
4. It must equal the SHA above **exactly**. If it doesn't: clear, re-paste, re-check.
   Common causes — a smart-quoted apostrophe, a trailing newline, the editor eating the blank
   lines around a break tag.
5. Only then click **Generate**. Once.

---

## 5. Splitting the pass WAVs (free, repeat as needed)

```bash
ffmpeg -i audio/dinoverse_omega/source_chunks/luke_pass.mp3 \
  -af silencedetect=noise=-40dB:d=1.2 -f null -
```
Expect **3 silences** in the Luke pass (4 segments) and **2** in the GF pass (3 segments).
If the count is off, loosen to `-45dB:d=0.9` and re-run — re-splitting costs nothing.
Cut at the **midpoint of each silence**, keep ~0.3s handles either side, export 48k WAV to the
filenames in the tables above.

---

## 6. Timing gaps — what the assembler must stretch

`estimated_speech_seconds` = words ÷ 2.6 (conversational). Positive gap = **the shot is too
short for its line and must stretch**.

| Shot(s) | Speaker | Words | Boarded | Est. speech | Gap | Assembler action |
|---|---|---|---|---|---|---|
| S01 (card) | LUKE | 13 | 2.0s | 5.0s | **+3.0s** | hold the DINO ZOO card to ≈5.5s |
| S02 (selfie) | GF | 13 | 3.0s | 5.0s | **+2.0s** | S02 still must hold ≈5.5s |
| S03–S10 (montage) | LUKE | 22 | 12.0s | 8.5s | −3.5s | line **fits** — 8 × 1.5s flashes have ~3.5s headroom; let the flashes breathe / land the last flash on "dare" |
| S11 | GF | 2 | 1.5s | 0.8s | −0.7s | fits |
| S12 (hook) | LUKE | 12 | 2.0s | 4.6s | **+2.6s** | extend the showdown-tease clip to ≈5s (or hold the last frame) |
| **S89 (card)** | **GF + LUKE** | **5 + 11** | **2.0s** | **1.9s + 4.2s = 6.2s** | **+4.2s** | **see below — this is the big one** |

**Cold open total:** boarded **20.5s** → VO needs **≈24s of speech** + inter-line beats, so the
cold open lands around **26–28s**. That is a real re-time, not a nudge: S01, S02 and S12 all grow.

### ⚠️ S89 — flagged
The end card is boarded at **2 seconds** and carries **two lines from two voices**
(GF closer, then Luke's CTA — GF first, per the TSV). 6.2s of speech plus a beat between the
two voices ≈ **7s minimum**. The card must stretch from 2s to **≈7–8s**.
That is the ending the owner said the video doesn't have — do not squeeze it back to 2s.

---

## 7. Output convention

```
audio/dinoverse_omega/
├── luke_s01.wav
├── luke_s03_montage.wav
├── luke_s12.wav
├── luke_s89_cta.wav
├── gf_s02.wav
├── gf_s11.wav
├── gf_s89_closer.wav
└── source_chunks/
    ├── luke_pass.mp3      ← the raw ElevenLabs download (keep it; it is the only copy)
    └── gf_pass.mp3
```
Audio is gitignored — keep the source chunks. They cannot be regenerated for free.
