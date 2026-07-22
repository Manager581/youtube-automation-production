# Completeness Critique — 32-video synthesis (2026-07-21)

Method: citation-counted all 32 ids across the four synthesis files; spot-checked 9 per-video
analyses, prioritizing the least-cited (CQWfqKGFoPM, h6DB0e96GI0, lL9gjPw5yjg, 8Mx2m0djgTA,
KZKFlik4M8I, NA0AOlCmelQ, KxsasFMMPpA, r81ImbWaxEE, 6WDvO0Lu1sY); verified specific
citations (save-the-cat → Xf_J7kBzxvo; 150–200 scene density → Ao_d-uaMJvk; thumbnail
modeling → 8KXlxAKOTdE) against the source JSONs; checked recommended actions against
STRATEGY_CONTEXT.md / CLAUDE.md hard rules.

## 1. Video ids cited nowhere — NONE

All 32 ids are cited in at least two of the four synthesis files (minimum total: CQWfqKGFoPM
at 13 mentions; maximum: PtO7jd8L2xs at 53). `hype_filter.md` tier-ranks all 32 with a
correct 10+16+6=32 count check. Spot-checks of the least-cited analyses confirm their signal
was captured, not dropped:

- **CQWfqKGFoPM** — membership smart-pricing → tactic 8.5 + policy dossier §1; deadline hook →
  tactic 2.1(a); TubeBuddy Next Ideas → action-plan paid-tools DO-NOT-DO. Fully covered.
- **h6DB0e96GI0** — negative archetype (5.10), Flow free-tier conflict (6.1), Tier C. Covered;
  its only unlisted item (master-prompt variable slot) was a CONFIRM of existing TSV practice.
- **lL9gjPw5yjg** — AI Studio TTS test (6.2, PPOV experiment), hero-reference conditioning
  (3.3), negative archetype (5.10). Covered.
- **8Mx2m0djgTA** — one-click-factory rejection (6.5), enumerated-reveals cold open (2.1c),
  concept scoring (1.1). Covered.
- **KZKFlik4M8I** — FB monetization mechanics (4.7/8.6), $2/day-ads seeding correctly dropped
  (analysis IGNOREd it: needs spend, no YouTube transfer). Covered.
- **NA0AOlCmelQ** — character-block injection (3.3d + PPOV experiment), Flow "unlimited"
  debunk (6.1), Wan multi-Gmail farming never-do (7.7c). Covered.
- **KxsasFMMPpA** — two-tone captions (4.4), twist-story vertical (4.6 + PPOV experiment),
  DuoPlus never-do (7.7b). Covered.
- **r81ImbWaxEE** — 3-variant best-of-N (6.4 + Rexcaped experiment), TikTok ~300/30-day cap
  (7.7b, 8.1, C7). GMV Max / Kalodata / bottom-of-funnel copy justifiably ignored (different
  business model, per the analysis verdicts). Covered.

**One minor genuine drop:** 6WDvO0Lu1sY's **matched-zoom transition** (keyframe zoom-out end
of clip N = zoom-in start of clip N+1; flagged NEW in the analysis, mapped to the FFmpeg Ken
Burns path) appears in no synthesis file — the analysis itself left it out of its verdict
lists, and the style gate would block unmeasured transitions anyway, but it is the one
NEW-flagged mechanic from any spot-checked video that vanished without an explicit ruling.

## 2. Tactics/claims lacking a video-id citation — effectively none

Every tactic in `tactic_map.md`, every action row in `action_plan.md`, every claim in
`policy_dossier.md`, and every ruling in `hype_filter.md` carries video-id citations.
Claims resting on internal sources (2026-07-20 Flow audit; SynthID persistence; FFmpeg
`-sseof` port) are labeled as audit/analyst assessment rather than passed off as video
evidence — correct practice. Verified-by-sample: the less-obvious citations
(Xf_J7kBzxvo save-the-cat; Ao_d-uaMJvk 150–200 density; 8KXlxAKOTdE thumbnail-modeling in
1.2) all trace to real content in the per-video JSONs.

**One misattribution:** tactic 4.7 says "**Both** sources leave Meta's AI label OFF" citing
E_CIP98ufto + KZKFlik4M8I — the KZKFlik4M8I analysis never mentions the AI label (0 hits);
only E_CIP98ufto documents it. `policy_dossier.md` §2b gets this right (E_CIP98ufto only),
so tactic_map is the outlier. Fix: drop KZKFlik4M8I from that sentence.

## 3. Contradictions between the four synthesis files — none substantive; three disposition drifts

1. **2.5s hold / 150–200 density (Ao_d-uaMJvk):** tactic_map 2.3 says TEST ("audit the
   published 8:07 first"); hype_filter C1 says "survives only as a narrow, *testable*
   parameter"; but action_plan lists it under PPOV **DO NOW** ("written into episode
   planning") and policy_dossier §6.3 already treats it as standing discipline that "doubles
   as anti-repetitive-content evidence." TEST vs ADOPT drift — harmless in practice but the
   files disagree on whether it's proven.
2. **0.25s i2v head-trim (TiycelzfzC0):** hype_filter Tier A row says "(adopted)"; tactic_map
   3.4 and action_plan both condition adoption on a frame-strip check confirming the artifact
   in Grok clips. Hype_filter overstates.
3. **$499.99/mo membership cap (CQWfqKGFoPM):** policy_dossier §1 correctly flags it as
   description-sourced/unverified; tactic_map 8.5 states it unqualified. Evidence-grade
   inconsistency only.

No file recommends what another file rejects; the C2 sameness-paradox resolution (repeat the
FORMAT, vary the FINGERPRINT) is applied consistently across all four.

## 4. Hard-rule violations in recommended actions — none found

Checked every DO NOW / NEXT VIDEO / EXPERIMENT / CAPABILITY BUILD against the hard rules
(no new paid APIs/subscriptions without asking; no Pexels/Pixabay images; no AI human faces /
real photos only; real physics + frame-level QA; no-spend-without-prototype; no original
journalism; prototype-before-plan):

- ElevenLabs V1 dub experiment → explicitly gated on "owner approval for credits first." OK.
- Gemini "create music" bed → explicitly rights-gated before touching a render; note the
  "(Pixabay music only)" phrasing in CLAUDE.md is an exception scope, not an exclusivity rule,
  and tactic_map 6.2 flags the rights check anyway. OK.
- Real-executive-face thumbnail A/B → real photo per `feedback_ai_faces_use_real_photos`;
  thumbnail style-transfer test explicitly excludes AI faces. OK.
- FB repost test → organic only, AI label ON, 30-day kill. The $2/day ad-seeding from the
  same source videos was correctly NOT carried into the plan (no-spend rule). OK.
- SAM 2, AI Studio TTS, Flow-stills benchmark, dummy research account → free, ToS-clean,
  prototype-first. OK.
- Paid stacks (Higgsfield, kie.ai, Kling, Flow paid, VidIQ, etc.) uniformly routed to
  DO-NOT-DO / fallback-with-owner-ask. OK.

## Verdict

Coverage is complete: all 32 videos are represented, the citation discipline holds, no
recommended action violates a hard rule, and the four files agree on every substantive
adjudication. Four small fixes worth making: (1) drop KZKFlik4M8I from the tactic-4.7 AI-label
sentence; (2) reconcile the 2.5s-hold disposition (call it TEST everywhere, or promote it
deliberately); (3) soften hype_filter's "(adopted)" on the head-trim to match the
conditional; (4) qualify the $499.99 cap in tactic_map 8.5 — and optionally log 6WDvO0Lu1sY's
matched-zoom transition with an explicit IGNORE-until-measured ruling so it isn't a silent drop.
