# QA Plan — how quality is checked at every stage
_Not "I'll review it." Every stage has a concrete check with a pass threshold. Three tiers:
(1) DETERMINISTIC scripts that emit red/green numbers, (2) MY VISION on frames, (3) OWNER eyes +
real post-publish data for the one thing no script can pre-verify (virality)._

## The automated style-gate already exists and is proven
`research/wildbirdsurvival_teardown/gate_style_wbs.py` (built from the teardown; alongside
`extract_forensics.py`) grades any render against the 11 measured winner bands. Proof it
discriminates — run on the 7 reference videos (`gate_run_reference_7videos.txt`):

| Video | Views | Style-gate |
|---|---:|---|
| BEST / WIN2 / WIN3 / WIN4 / WIN5 (all winners) | 654K–1.98M | **11/11 PASS** |
| LOSE2 (flopped near-clone) | 3K | **6/11** — flagged: choppy hook (22 cuts), fast cutting, mid-video music peak |
| WORST (peregrine "life cycle") | 1.9K | **4/11** — flagged: 67% coverage, 3.17 wps, no long wordless gap, too few holds |

All 5 winners pass every gate; both losers fail on real craft metrics. LOSE2 still passes the
coverage/density gates — correct and by design: **the gate checks style, not topic. Its passing
those is the honest reminder that virality lives upstream where no render-checker can reach.**

## Per-stage checks
| # | Stage | What I check | How (tool) | Pass threshold | Arbiter |
|---|---|---|---|---|---|
| 0 | Prototype clip | Does Grok/Sora match the Veo look? | side-by-side vs real Veo frame | you say "close enough" | **you** (subjective look) |
| 1 | Topic/title/thumb | Two-animal curiosity gap? not life-cycle? not a self-clone? | topic gate rubric + `pipeline_v2/topic_scorer.py` | GO on rubric | Claude + me — **not a virality guarantee** |
| 2 | Script | Word budget, banned openers, structure | deterministic linter (word count, regex for "life cycle"/"famous for", first-sentence names animal+threat) | ≤1.5×runtime-s, ~60 lines, no banned phrases | automated |
| 3 | Reference stills | Photoreal, correct anatomy, consistent hero animal | I Read the images (vision) | no deformities; same animal across stills | me (you optional) |
| 4 | **i2v clips (critical)** | Physics/anatomy glitches on **every** clip | extract a frame-strip per clip, I Read each | no limbs-through-barriers, no morphing, correct species behavior → **regenerate any fail** | me — project hard rule ([[feedback_i2v_real_physics]]) |
| 5 | Voice | Transcript matches script; pace; pitch; artifacts | whisper + librosa (scripts I built this session) | words match, ~150 wpm, ~80–90 Hz, no glitches | automated |
| 6 | Music | Level under VO, constant, licensed | ffmpeg RMS diff vs VO track | 12–20 dB under, no auto-duck swells, Pixabay only | automated |
| 7 | Render / edit | 11 style bands + black frames + coverage + narration sync | `gate_style_wbs.py` + `scripts/verify_render.py` | **11/11 style gates green**; not_black=0; narration aligned | automated |
| 8 | Pre-publish | Full 13-gate checklist + contact sheet + watch-through | gate output + I watch + you watch | all green + **you approve** | me + you (project rule: owner watches before publish) |
| 9 | Post-publish | CTR, avg-view-duration, retention curve | YouTube Studio | the **only** virality signal | real data → feeds back to Step 0 |

## The three tiers, honestly
- **Tier 1 — deterministic (stages 2, 5, 6, 7):** I run a script, it prints pass/fail per metric.
  No judgment, no hand-waving. You can see the same red/green I do.
- **Tier 2 — my vision (stages 3, 4, 8):** I read the actual frames — every i2v clip gets a
  frame-strip physics/anatomy check before you ever see it (whisper alone is not enough — hard rule).
- **Tier 3 — you + real data (stages 0, 1, 9):** the subjective "does it look like Veo" call is
  yours; the "did it go viral" answer only exists after publish, as CTR/retention. That becomes the
  iteration loop on topic/title/thumbnail — the layer no pre-publish check can grade.

## What this means for your "100%" question
- **Stages 2–8 are 100% checkable before publish**, and stage 7 is already proven to separate
  winners from losers on this exact channel.
- **Stage 1 (will it click) and stage 9 (did it) are NOT pre-verifiable** — they're a bet measured
  after the fact. That's the ceiling on any honest guarantee, for me or anyone.
