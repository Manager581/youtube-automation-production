# T-Rex Pilot — CHAPTER ROLLOUT (build/bless in small chunks)

Engine: `scripts/composite_beat.py` (cut-out creature → animated layer over real
footage + camera/blur/graphic/text/SFX). Each creature beat = a config. Build a
chapter's composite beats → splice into the paper edit → render that chapter
only (540p) → owner bless → next chapter.

## Chapters (HOOK already blessed)
| Chapter | Beats | Time | Spine | Composite-beat candidates |
|---|---|---|---|---|
| **HOOK** ✅ | 0–23 | 0–66s | cold open | done/blessed |
| **CH1 · THE BODY** | 24–66 | 66–193s | what you woke up in | stumble (can't-fall) ✓built · statue-loom (patient) · POV-pick (one runner) · nostril-push (smell) |
| **CH2 · DAY ONE** | 67–111 | 193–325s | the hunt flips | strike (one bite) ✓built · phone-wall · swim (the river) · herd-collapse |
| **CH3 · VERDICT+CTA** | 112–128 | 325–365s | yes, but the catch | night-one silhouette · megalodon-gag CTA |

## Script fix (no full rewrite — claims are real, just unattributed)
Carry attribution on the MOTION-GRAPHIC layer, VO untouched (no re-record):
- can't-fall → "A FALL AT SPEED = FATAL — paleontologists" (✓ built, yellow)
- teeth (hook) → "POLYPHYODONT · REGREW FOR LIFE"
- vision → "13× HUMAN ACUITY"
- smell → "SCENT: >1 MILE"
OPTIONAL VO re-record (owner call, costs 1 ElevenLabs regen + realign):
- "falling down is the same as dying" → "a fall at full speed is a death sentence"

## Branding locked
Kinetic text = BIG orange (default) / yellow (alert), heavy ink outline, NO
banner, auto-fit to width. (`composite_beat.py`, owner call 2026-06-10.)

## Per-chapter build checklist
1. List the chapter's creature/still beats that are currently static.
2. For each: cut creature (`rembg`), pick background (stock/existing), choose
   motion preset (lunge/stumble/loom/…), graphic (reticle/card/none/attribution),
   kinetic text @ word times, SFX cues → add to `composite_beat.CONFIGS`.
3. Render beats, contact-sheet QA, splice clips into the paper edit beats.
4. Render the chapter span 540p, owner bless, commit.
