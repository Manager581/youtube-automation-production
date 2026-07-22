# Creator-Advice Deep-Dive — 32 videos, applied to our faceless operation

**Date:** 2026-07-21 · **Requested by:** owner (two URL batches, 26 + 6)
**Method:** full transcript pulled for every video (yt-dlp auto-subs; 2 Hindi-language videos
Whisper-transcribed locally), one dedicated analysis agent per video reading the transcript +
description + our strategy context, then a 4-way synthesis (tactics / actions / policy / hype)
and an independent completeness critique. All 32 videos are cited in the synthesis; the
critique verified none were dropped ([critique.md](critique.md)).

## Read in this order

1. **[action_plan.md](action_plan.md)** — the deliverable. Per-channel (Rexcaped, Prehistoric
   POV, bizdoc, cross-channel) actions in buckets: DO NOW / NEXT VIDEO / EXPERIMENTS /
   CAPABILITY BUILDS / DO NOT DO. Every action names the system it touches and its source videos.
2. **[policy_dossier.md](policy_dossier.md)** — monetization/enforcement intel incl. the Aug 17
   membership-pricing change and the July-2025 "inauthentic content" regime.
3. **[tactic_map.md](tactic_map.md)** — ~45 deduplicated tactics across 8 themes, each with
   evidence strength and NEW/CONFIRM/CONTRADICT status vs our playbook.
4. **[hype_filter.md](hype_filter.md)** — conflicts adjudicated, hype patterns, and all 32
   videos tiered A/B/C.
5. **[videos/](videos/)** — per-video notes (32 files, `<id>.md`); [SOURCES.md](SOURCES.md)
   maps ids → titles/URLs; [INDEX.md](INDEX.md) is the one-line-thesis index.

## The five findings that matter

1. **Sameness — not AI — is the demonetization trigger.** The strongest cross-video signal
   (~8 independent sources, including a verbatim "mass-produced" YPP rejection on a
   human-voiced channel, and two template-farm operators who rotate templates specifically to
   evade detection). Our exposure: the edit engine could stamp identical grammar on every
   upload. Defense (all free): AI-disclosure YES on every upload, inter-video edit-fingerprint
   diff (`scripts/extract_motion_events.py`, V1 vs V2), per-video human-editorial appeal
   packet (script versions + QA reports), and never touching the aged-channel/account market.
2. **Shorts are the biggest structural gap.** 8 videos converge; the one credible analytics
   receipt in the corpus (7s clip, 86% stayed-to-watch, ~400% AVD, 6M views) demonstrates the
   read-time > runtime text-loop format. We can build the whole lane $0 from owned assets
   (FFmpeg 9:16 crops of best motion-event beats). Ship-gates: STW ≥ 75-80%, AVD ≥ 100%.
3. **A pre-upload launch checklist is time-critical for bizdoc.** Cold-start channel-keyword
   seeding, phone/ID feature verification (the 23.4-min video needs the >15-min unlock),
   AI-disclosure stance for the cloned voice, WIPO name check, unlisted-first upload, 72h
   no-evaluation window, no Reddit seeding. Several items only work while the channel is young.
4. **Ideation front-end upgrades for the 9-test scorer** — search-bar supply check (3+
   near-identical treatments forces a differentiated angle), niche-gap thresholds (<60 days /
   <10 channels / views≫subs), monetization-survivor scan, competitor-corpus demand-gap
   clustering with Claude, 80/20 double-down ratio once outlier data exists.
5. **Production-stack upgrades that survive scrutiny** (all $0, prototype-first): SAM 2
   between-layer compositing for the layered-composite engine, creature turnaround-sheet
   reference conditioning, 3-variant best-of-N i2v prompts, 0.25s i2v head-trim (TEST),
   last-frame continuity chaining scoped within-beat, timestamp-conditioned i2v prompts.

## What we explicitly rejected

Aged/pre-monetized channel buying (the hidden engine behind every "monetized in days" claim),
free-credit multi-accounting, watermark hiding, OBS-ripping streaming services, "text overlay =
transformative" folklore, template niches (BeamNG/renovation/Roblox/nursery-rhymes), paid gen
stacks (no-new-paid-APIs rule), and no-script production. Details + the rule each violates:
[action_plan.md](action_plan.md) DO-NOT-DO tables and [hype_filter.md](hype_filter.md).

## Corpus credibility note

Most of the corpus is affiliate/course-funnel content with unverifiable revenue screenshots.
Only PtO7jd8L2xs shows a real analytics panel. Ten videos are genuinely load-bearing (tier A),
sixteen contribute one nugget each, six are noise — but all 32 were read and ruled on.
