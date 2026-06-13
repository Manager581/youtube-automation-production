# Voice recording spec — for the local "ElevenLabs PVC" clone

This is the single highest-leverage thing you can give me. Zero-shot cloning can
only ever be as good as its reference clip, and the real "ElevenLabs Professional
Voice Clone" quality comes from **fine-tuning on your voice** — which needs a
clean dataset. One recording session feeds both.

## The honest goal
We are **not** trying to make you sound like "Mark" — Mark is a different person
(a pro voice actor in a studio). The goal is to make **your own voice** sound as
studio-polished and natural as ElevenLabs' clone of your voice would. That ceiling
is set almost entirely by the recording below.

## Three tiers — record as far as you have patience for
| Tier | Length | Gets you |
|---|---|---|
| **1 — Better reference** | **3–5 min** | A clean zero-shot clone, noticeably better than today's clips. Do this first, today. |
| **2 — Light fine-tune** | **20–30 min** | A real fine-tune — kills most of the "mechanical", consistent across a video. |
| **3 — Full PVC** | **90–120 min** | The actual ElevenLabs-Professional equivalent. The ceiling. |

Each tier is a superset of the one before — just keep recording. Stop whenever.

## Gear (use the best you have; none of this is mandatory)
- **Mic:** a real condenser (Rode NT1 / AT2020 / any XLR into an interface) is ideal,
  but a good USB mic (Blue Yeti, Rode NT-USB) is fine. Even AirPods are NOT fine —
  the clone will inherit that thin/compressed sound forever.
- **Distance:** ~2 fists from the mic, slightly off-axis. Use a pop filter (or a sock).
- **Room:** the quieter and deader the better. A closet full of clothes, or under a
  duvet, beats a bare echoey room. **No** fan/AC/fridge hum, no traffic, no laptop fan.
- **Format:** 48 kHz (or 44.1), **mono**, 24-bit WAV if you can pick; otherwise highest-
  quality your app allows. (QuickTime, Audacity, Voice Memos→export, your DAW — all OK.)

## How to perform it (this is the part that matters most)
- **Read in the EXACT voice you want out** — your documentary-narration delivery. The
  model learns your *delivery*, not just your timbre. If you read it flat, it narrates flat.
- **One register per file.** If you want separate "energized / neutral / tense" narration
  voices, record a separate file for each (label them). If you only want one, just do your
  main narration voice — simpler and usually enough.
- Read **real channel script** material (the Spinosaurus or Breaking-Law scripts are
  perfect) — varied sentences, numbers, names, questions, dramatic pauses. Don't read a
  word list; read prose the way you'd narrate it.
- Watch your level: aim for peaks around -6 dBFS, **never clipping** (no red). Consistent
  loudness — don't lean in and out.
- Mistakes are fine — just pause and re-read the sentence; I cut and align automatically.
- Leave ~1 s of silence at the very start and end (lets me sample your room tone).

## Deliver
Drop the WAV(s) anywhere in the repo (e.g. `assets/voice/dataset/`) or hand me a path.
Then I run the rest automatically:
1. WhisperX → word-level transcripts (your existing tooling)
2. denoise + segment into 30–60 s clips, level-normalize (the `audio_master.py` chain)
3. zero-shot re-clone immediately (Tier 1), and/or
4. LoRA fine-tune on a rented GPU (~$1–5) or free Colab (Tier 2–3) → inference back on the Mac

**Minimum viable first step:** even a single clean 60-second take of you narrating, in a
quiet closet, will measurably beat the current `assets/voice/*.wav` references. Start there.
