# Creator-Advice Deep-Dive — 54 videos, applied to our faceless operation

**Dates:** 2026-07-21/22 · **Requested by:** owner (three URL batches: 26 + 6 + 22)
**Method:** full transcript pulled for every video (yt-dlp auto-subs; 2 Hindi videos local-Whisper
transcribed; 1 Vietnamese via native captions), one dedicated analysis agent per video reading the
transcript + description + our strategy context, then a 4-way synthesis (tactics / actions / policy
/ hype) regenerated over the full 54-video corpus, and an independent completeness critique.
All 54 videos are cited in the synthesis; tier math is script-verified; the seven inter-file
inconsistencies the critique found have been fixed ([critique.md](critique.md)).

## Read in this order

1. **[action_plan.md](action_plan.md)** — the deliverable. Per-channel (Rexcaped, Prehistoric
   POV, bizdoc, cross-channel) actions in buckets: DO NOW / NEXT VIDEO / EXPERIMENTS /
   CAPABILITY BUILDS / DO NOT DO, with [NEW] tags on everything the last 22 videos added.
2. **[policy_dossier.md](policy_dossier.md)** — monetization/enforcement intel: Aug 17
   membership pricing, July-2025 "inauthentic content" regime, Content ID, ToS landmines.
3. **[tactic_map.md](tactic_map.md)** — 62 deduplicated tactics across 9 themes + a 9-item
   conflicts ledger, each with evidence strength and NEW/CONFIRM/CONTRADICT vs our playbook.
4. **[hype_filter.md](hype_filter.md)** — conflicts adjudicated, hype patterns, all 54 videos
   tiered (A=16 load-bearing / B=32 one-nugget / C=6 ignorable).
5. **[videos/](videos/)** — per-video notes (54 files, `<id>.md`); [SOURCES.md](SOURCES.md)
   maps ids → titles/URLs; [INDEX.md](INDEX.md) is the one-line-thesis index.

## The headline findings (54-video corpus)

1. **Sameness — not AI — is the demonetization trigger** (now 9 sources, incl. a verbatim
   "mass-produced" YPP rejection on a human-voiced channel and two template-farm operators who
   rotate templates to evade detection; vidIQ adds that enforcement can arrive via reduced
   recommendations, not just YPP). Defense, all free: AI-disclosure YES on every upload,
   inter-video edit-fingerprint diff (`scripts/extract_motion_events.py`, V1 vs V2), per-video
   human-editorial appeal packet, never touch the aged-channel/account gray market. NEW: audit
   AdSense linkage — bans can cascade across channels sharing one AdSense account.
2. **Shorts remain the biggest structural gap** (now 10 sources). The corpus's best analytics
   receipt: 7s loop + 25s read-time text = 86% stayed-to-watch, ~400% AVD, 6M views. Buildable
   $0 as FFmpeg 9:16 crops of owned assets; ship-gates STW ≥75-80%, AVD ≥100%; sub-CTA Shorts
   also attack the 1K-sub YPP gate.
3. **Upload timing is money (NEW).** Pre-YPP-acceptance views are never paid retroactively, so
   bizdoc's finished video sitting unrendered/unuploaded is unpaid inventory; apply to YPP the
   moment thresholds hit. The bizdoc pre-upload checklist (cold-start keyword seeding, >15-min
   feature unlock, disclosure stance, WIPO check, unlisted-first, no seeding) is time-critical.
4. **Post-upload patience doctrine (NEW).** Reconciled from four conflicting sources: on young
   channels week-1 data is noise — first read at day 14, earliest packaging change day 14,
   write-off verdicts only at week 4-6, never delete flops (winners retro-test the back
   catalog). The 48-72h CTR/AVD read is for established channels only.
5. **A Claude-Code motion-graphics lane opened (NEW).** Remotion and HeyGen's open-source
   Hyperframes both let Claude Code generate animated charts/motion graphics for $0, feeding
   the FFmpeg renderer as overlay clips — fills bizdoc's static-stat-card gap. Bake-off
   prototype on one Breaking-the-Law stat beat is queued in the action plan.
6. **Ideation front-end for the 9-test scorer** (7 sources): search-bar supply check (3+
   near-identical hits forces differentiation), niche-gap thresholds (<60d / <10 channels /
   views≫subs at <1 upload/week), monetization-survivor scan, competitor-corpus demand-gap
   clustering, 80/20 double-down once outlier data exists.
7. **Production-stack upgrades that survive scrutiny** (all $0, prototype-first): SAM 2
   between-layer compositing, character turnaround-sheet + A/B pre-lock + per-prompt reference
   mapping (8 sources converge on AMBER's reference_images direction), 3-variant best-of-N i2v,
   two-keyframe brackets, camera-move vocabulary column for the i2v TSV, 0.25s head-trim (TEST).
8. **One urgent verification:** a single (description-sourced, unverified) claim that Grok
   Imagine's free tier is dead — our primary i2v engine. Check before the next Spino/Lagos
   generation batch; Meta AI f2v and Google Vids Veo are queued as $0 fallbacks.

## What we explicitly rejected

Aged/pre-monetized channel buying, credit multi-accounting/temp-mail refills, watermark hiding,
"click No" on AI disclosure, voice-cloning other people, OBS-ripping streaming services,
"text overlay = transformative" folklore, template niches (BeamNG/renovation/Roblox/nursery
rhymes), paid gen stacks (Higgsfield/kie.ai/Kling — no-new-paid-APIs rule), third-party batch
Chrome extensions (untrusted code), Paid Promotions (~$0.53/sub, tested and not worth it),
no-script production. Each with the rule it violates: [action_plan.md](action_plan.md)
DO-NOT-DO tables and [hype_filter.md](hype_filter.md).

## Corpus credibility note

Most of the corpus is affiliate/course-funnel content with unverifiable revenue screenshots.
Only two videos carry real evidence: PtO7jd8L2xs (analytics panel) and ROPkHP8jpW0 (the only
controlled experiment — edit quality dominates; no AI-suppression observed). BePppCvXC-k adds
the first on-screen RPM-by-runtime receipts. Sixteen videos are load-bearing (tier A), 32
contribute one nugget, 6 are noise — but all 54 were read in full and ruled on.
