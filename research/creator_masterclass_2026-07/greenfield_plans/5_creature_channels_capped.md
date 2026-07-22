> **⚠ Read [CRITIQUE_AND_SEQUENCE.md](CRITIQUE_AND_SEQUENCE.md) first — it is authoritative on hours, conflicts, and whether this play runs now, is gated, or is parked.** Individual plans assume they run standalone; the portfolio does not have hours for all five.

# PLAY 5 — Creature/Spectacle Lane: Run the EXISTING Channels Under a Strict Hours Cap

**Operator:** Jeff Lawrence. **Channels:** Rexcaped (live, 1 video + Omega-Rex variant; V2 Spino/Lagos in production — script + Mark VO done) and @Prehistoric_POV (1 video live, 8:07, published 2026-07-13). Neither in YPP.
**What this play is NOT:** a new channel, a new pipeline, or a new technique. Every mechanic below already exists in the repo or in `synthesis/action_plan.md`; this plan sequences them under a hard hours cap and pre-commits the day-90 verdict.
**Framing (from the judges' panel):** this is the capped venture bet. It is ranked #5 because its revenue is YPP-gated and entertainment-RPM; its job in the portfolio is optionality (a viral-format lottery ticket on assets that already exist) — not cash flow. Plays 1–3 outrank it for hours whenever they conflict.

---

## THE HOURS CAP (the defining constraint of this play)

- **Weeks 1–4 (V2 ship window): 5.0 hrs/week hard cap.**
- **Weeks 5–13 (steady state): 4.0 hrs/week hard cap.**
- Total operation budget is 10–15 hrs/week (GREENFIELD_BRIEF), so this leaves **6–11 hrs/week for plays 1–3** at all times. The cap is a ceiling, not a target: an under-cap week is fine; borrowing hours from plays 1–3 is never fine.
- **Accounting rule:** the cap includes EVERYTHING — generation babysitting, QA, uploads, comment replies, analytics reads, ideation. Log hours in a `HOURS_LOG` block at the top of `NEXT_VIDEO.md` (the existing Rexcaped handoff file at repo root) each session. If a week busts the cap twice in a row, the response is *scope reduction inside this play* (see Kill/Scale), never a bigger cap.
- **Honesty note:** 4–5 hrs/week is roughly half the pace a solo operator would normally give one creature channel, and this play runs two. The plan resolves that by (a) one long-form lane in production at a time, (b) Shorts cut only from already-owned rendered beats, and (c) the automated pipeline (`scripts/rexcaped_edit_engine.py`, `scripts/ffmpeg_production_render.py`, `scripts/verify_render.py`) doing the labor that competitors do by hand.

---

## 1. DECISIONS REQUIRED FROM JEFF BEFORE DAY 1

| # | Question | Recommended default |
|---|---|---|
| D1 | **Do you accept the cap and the ranking?** 5 hrs/wk (weeks 1–4) → 4 hrs/wk (weeks 5–13), and plays 1–3 win any scheduling conflict. | **Yes.** Without a pre-committed cap this lane historically absorbs unlimited hours (the repo's own session history is the evidence). |
| D2 | **If the Grok Imagine free tier is dead (Day-1 check), which fallback order?** | **Meta AI frame-to-video first, Google Vids Veo second** (both $0; Qsi9MeLh95Q leads, per `synthesis/action_plan.md` Rexcaped experiments). Local VACE-1.3B (`tools/amber/stage_b_vace.py`, ~22 min/beat, $0) is the always-available third. **No paid gen stack without a separate explicit approval** (hard rule). |
| D3 | **Pre-YPP affiliate on the creature channels — approve desk research?** One high-ticket ($100+/sale) survival/outdoor-gear affiliate fit-check; a link ships only if a genuine fit exists, with FTC disclosure, and only after you see the specific program. | **Yes to desk research (30 min, inside the cap); link placement is a second, separate approval.** This is the ONLY pre-YPP revenue path this lane has (LGYiPA5SKvw, TvJhpOxFRsE — practitioner-claim). |
| D4 | **AdSense/account structure:** run the linkage audit (already a blocking bizdoc checklist item) and decide whether Rexcaped/PPOV stay on one AdSense account. | **Separate where practical** — ban propagation across channels on one AdSense account is practitioner-claimed, unverified, cheap to hedge (YtpQSmu794k). |
| D5 | **Pre-commit to the Day-90 verdict criteria (§6) now?** | **Yes.** Signing the kill/scale numbers before data arrives is the only defense against sunk-cost reasoning on a lane you've already invested months in. |
| D6 | **PPOV published video (2026-07-13):** confirm it stays untouched until at least day 14 post-publish (2026-07-27), packaging changes considered only at the 4–6-week mark, and it is never deleted regardless of performance. | **Yes** — patience doctrine (BePppCvXC-k, ROPkHP8jpW0, 9iP588aMFBc, q0G-FzS6uxk; STRONG, analytics-backed convergence). |

---

## 2. DAY 1–7 CONCRETE SETUP (budget: 5.0 hrs total)

Every action here is a fold-in from `synthesis/action_plan.md` (Rexcaped DO NOW / NEXT VIDEO tables and PPOV DO NOW table) — nothing is new invention.

**Day 1 — the blocking gate (≈45 min)**
1. **Verify Grok Imagine free tier** (action_plan Rexcaped DO NOW #1; Qsi9MeLh95Q flags "free tier killed", description-sourced, unresolved — conflict ledger #5). Tool: the existing clipboard-upload recipe (`reference_grok_i2v_clipboard_upload` memory file) driven from Claude-in-Chrome, on ONE existing Spino/Lagos still. First flip Grok Settings → Behavior → automatic video generation OFF (ylezKJG7rb8). **Output artifact:** one test clip on disk + a `GROK_STATUS` line (working / degraded / dead, with date) written into `NEXT_VIDEO.md`.
2. **If dead/degraded:** run the two 10-minute fallback probes from action_plan — Meta AI frame-to-video and Google Vids Veo (verify i2v support + watermark status FIRST; if t2v-only or watermarked, that fallback is disqualified for creature beats). **Output artifact:** fallback decision appended to the `GROK_STATUS` line + a note in the tool-landscape memory. This decision gates the entire V2 i2v batch — nothing else in the lane proceeds until it's written.

**Day 1 — thumbnail-first gate (≈30 min)**
3. **Produce the V2 thumbnail BEFORE any composite work** (tactic 1.1 — render-first ordering: ipbnR92Elxg, q0G-FzS6uxk, 3MPSrpIOpAo, 8Mx2m0djgTA; STRONG). Tool: ChatGPT/Gemini still-gen with the candid-phone-photo recipe (`feedback_dinoverse_thumbnail_style`) plus the two new realism knobs — "reduce saturation and contrast — natural iPhone photo look", text added in post not in-gen (ipbnR92Elxg, Z5Wn63kLhpI). Check it at feed size on a phone. **Output artifact:** `assets/` thumbnail PNG + a one-line pass/kill note. If the best version doesn't read at feed size, the fix happens NOW, not after 4 weeks of composites.

**Day 2 — channel hygiene, one sitting (≈45 min)**
4. **Rexcaped cold-start seeding** (4xWQ_fHLGAc, 3MPSrpIOpAo): creature-attack keywords into the channel description + Studio Settings → Channel keywords; confirm feature eligibility (custom thumbnails, >15-min uploads) per eF75ZffgsUk. Tool: Claude-in-Chrome on Studio. **Output artifact:** updated channel settings + checklist ticks in `NEXT_VIDEO.md`.
5. **Write the post-upload feedback protocol into `NEXT_VIDEO.md`** by copying it from `synthesis/action_plan.md` (Rexcaped DO NOW row 6): no packaging changes before day 14; first format read at day 14, read-only, to queue V3; 80/20 once a format outliers; never delete/unlist; write-offs only at weeks 4–6 (ZKsldrcO_fU, BePppCvXC-k, ROPkHP8jpW0, 9iP588aMFBc, Oi3nSYYQ6sM, 8KXlxAKOTdE, q0G-FzS6uxk). **Output artifact:** the protocol block in `NEXT_VIDEO.md`, plus the same block in the PPOV project memory file.
6. **PPOV SEO/settings audit** (action_plan PPOV DO NOW #1): keywords, auto-dub on, AI-disclosure=YES standing. **Output artifact:** checklist ticks.

**Days 3–6 — V2 production start (≈2.5 hrs)**
7. **Spino/Lagos still batch begins.** Tool: ChatGPT/Gemini still-gen with per-still style-reference conditioning and the frozen creature descriptor block (tactic 6.8/6.9; STRONG), prompts built with the camera-move rider vocabulary + physics + mouth-closed riders (action_plan camera-preset row; ylezKJG7rb8, Qsi9MeLh95Q, vuo_bPhkD_U), chunked ≤5 prompts/request (zJmYdcvwY1Y). **Output artifact:** timecode-named stills in the V2 assets directory, gated by `gate_style.py`/style bands before any i2v spend.

**Day 7 — Shorts derivative prototype (≈30 min, the capability-build #1 one-sample proof)**
8. **Cut ONE Rexcaped Short + ONE PPOV Short from owned rendered beats.** Tool: `scripts/ffmpeg_production_render.py`-style FFmpeg 9:16 crop pass on the highest-scoring motion-event beats (selected via `scripts/extract_motion_events.py`), vertical caption grammar via FFmpeg/ASS (yellow setup / white body / red shock word, 2–4-word chunks — QfbGKfkGP8U, KxsasFMMPpA, E_CIP98ufto; STRONG), 3-SFX palette. The PPOV one is the **sub-CTA Short** attacking the 1K-sub gate (BePppCvXC-k, Studio-shown). Titles use the transplant: **"POV: you're the [role] when [stakes]"** (tICnK3Qb2k8, Ao_d-uaMJvk). Upload with AI disclosure = YES. **Output artifact:** 2 live Shorts + a gate-reading reminder set for day 7 post-publish (**ship-gates for the format: stayed-to-watch ≥75–80%, AVD ≥100%** — PtO7jd8L2xs; treat thresholds as practitioner-claimed).

---

## 3. WEEKS 2–13 CADENCE PLAN

**Standing weekly rhythm (every week, inside the cap):**
- 2–3 Shorts per channel from owned beats via the derivative pass — **target 3/wk/channel once the week-1 prototypes pass their gates; drop to 2/wk/channel whenever long-form work needs the hours.** Rotate caption styling every ~10 Shorts (PtO7jd8L2xs, 0SPqPnpQsWE — the demonetization-hygiene rotation). (~1.5 hrs)
- Pinned Claude-drafted comment at publish + first-hour replies on anything published that week (YtpQSmu794k). (~0.25 hrs)
- ONE analytics read, Mondays: subs / watch-hours pace / any upload crossing day 14 (manual run of the channel-audit pattern — capability build #2 stays manual until volume justifies automation). Remember watch-hour figures lag ~5 days (BePppCvXC-k, 4xWQ_fHLGAc). (~0.25 hrs)

| Week | Long-form lane (the remaining ~2–3 hrs) | Ships |
|---|---|---|
| 2 | V2 composites: rembg+PIL layered engine, i2v batch on the Day-1-verified engine; frame-strip QA every clip (`feedback_frame_level_qa`, `feedback_i2v_real_physics`); 0.25s head-trim check on Grok clips (TiycelzfzC0, gated per action_plan). | 4–6 Shorts |
| 3 | V2 assembly: `scripts/rexcaped_edit_engine.py` → render → contact-sheet pass → **V1-vs-V2 edit-fingerprint diff via `scripts/extract_motion_events.py`** (0SPqPnpQsWE, PtO7jd8L2xs, 4xWQ_fHLGAc — sameness is the documented YPP trigger). Build the upload package: congruence gate (first ~5s must show the thumbnail's subject/moment — YtpQSmu794k), AI-legible description (first two lines = plain creature+scenario+audience keywords — 9iP588aMFBc), tags mirroring the Spinosnack/Dinoverse sub-niche, end card naming ONE specific next video (Eb8wlFawjTw), AI-disclosure=YES, unlisted-first → public after HD processing (4xWQ_fHLGAc). | 4–6 Shorts |
| 4 | **V2 SHIPS (hard target: end of week 3; hard deadline: end of week 4).** Post-ship: archive the appeal packet (script lineage, VO manifest, `scripts/verify_render.py` HTML report, provenance stamps — ipbnR92Elxg). Attempt the collab-post/cross-link between Rexcaped and PPOV per action_plan (Eb8wlFawjTw). Affiliate desk research (D3). | V2 + 4–6 Shorts |
| 5–6 | Nothing new in long-form — V2 is inside its 14-day no-judgment window. Shorts continue; PPOV episode-2 candidate scored through `pipeline_v2/topic_scorer.py` (GO=85+): "POV: You're the First Human a Raptor Pack Has Ever Hunted" and/or the 24-hours-in-the-Cretaceous frame (action_plan PPOV NEXT VIDEO). Run the competitor velocity check first (Oi3nSYYQ6sM). Cap drops to 4 hrs/wk. | 4–6 Shorts/wk |
| 7 | **V2 day-14 read (read-only) → V3 decision memo.** 80/20 rule (8KXlxAKOTdE, Oi3nSYYQ6sM, BePppCvXC-k, zJmYdcvwY1Y — STRONG): if V2 outliers vs V1 baseline → V3 = direct escalation in the same "creature attacks real city" frame (the 18-still Dunkleosteus set already on disk at `assets/dunkleosteus/sh01–sh18` is the ready-made candidate); if V2 underperforms → next video changes packaging/format per the diagnostic ladder (zero impressions = distribution; impressions-no-clicks = packaging; clicks-no-retention = edit). | Memo + Shorts |
| 8–10 | Produce the week-7 winner (V3 sequel OR the PPOV episode — **one long-form at a time**; the other channel gets Shorts only). Same gates as V2: thumbnail-first, style gate, fingerprint diff vs BOTH prior videos, full upload package. | 1 long-form + Shorts |
| 11–12 | Second day-14 read; sub-CTA Short on whichever channel's watch-hour pace exceeds sub pace (BePppCvXC-k); if any upload passed its gates and outliered, queue its sequel per 80/20. | Shorts + possible 4th long-form started |
| 13 | **Day-90 verdict session (§6): fund / consolidate / dormant.** Write the decision + evidence into `NEXT_VIDEO.md` and memory. | Verdict memo |

**90-day totals under the cap (honest):** V2 + 1–2 more long-forms; ~50–70 Shorts across both channels; 2 day-14 reads and 2 week-4–6 verdicts' worth of format data. That is the realistic maximum at 4–5 hrs/wk — anyone projecting weekly long-form at this budget is lying.

---

## 4. THE FIRST 5 DELIVERABLES (fully specified)

1. **Grok-status decision memo (Day 1).** `GROK_STATUS` line in `NEXT_VIDEO.md`: working/dead, fallback selected (Meta AI f2v → Google Vids Veo → local VACE per D2), test clip path. Blocks everything downstream. (Qsi9MeLh95Q; conflict ledger #5.)
2. **Rexcaped V2 — Spino/Lagos (title already locked in `project_rexcaped_video2_spino_lagos` memory; use as-is).** Full upload package: thumbnail-first PNG (candid-phone + desaturation knob), V1-vs-V2 fingerprint-diff report from `scripts/extract_motion_events.py`, congruence-gated cold open, AI-legible 2-line description, AI-disclosure=YES, unlisted-first, end card naming one specific next video, appeal packet archived. Ships week 3–4.
3. **Shorts derivative engine + first ~12 Shorts.** The FFmpeg/ASS crop-caption pass (new module beside `scripts/rexcaped_edit_engine.py`, per action_plan capability build #1), prototyped week 1, graduated only if the two prototypes clear STW ≥75–80% / AVD ≥100%. Includes one **AVD-hack Short** (6–8s owned loop + 20–25s read-time caption — PtO7jd8L2xs) and one **PPOV sub-CTA Short**. Example working titles from owned beats: "POV: You have 3 seconds before the Dunkleosteus strikes" (sh15 asset), "POV: You're the first thing the Spinosaurus sees in Lagos."
4. **PPOV episode 2 (scored, then produced weeks 8–10 only if it wins the week-7 slot).** Working title: **"POV: You're the First Human a Raptor Pack Has Ever Hunted"** (fallback frame: "Why You Wouldn't Last 24 Hours in the Cretaceous" with POV: prefix). Chain: `pipeline_v2/topic_scorer.py` GO=85+ → ChatGPT still-series (chained references + character lock) → verified i2v engine → FFmpeg assembly, testing the 2.5s static-hold ceiling as a TEST not a rule (Ao_d-uaMJvk; conflict ledger #2).
5. **V3 decision memo + Day-90 verdict memo.** Week 7: sequel-or-pivot per 80/20 with the Dunkleosteus escalation as the pre-staged sequel candidate. Week 13: the §6 verdict with the actual numbers pasted in. Both live in `NEXT_VIDEO.md` + memory.

---

## 5. REVENUE MECHANICS + HONEST MILESTONES

**Where money can come from, in order of arrival:**
1. **High-ticket affiliate (pre-YPP), the only <90-day path.** One survival/outdoor product at $100+/sale, FTC-disclosed, in V2's description (LGYiPA5SKvw shows the terms math; TvJhpOxFRsE's four-layer stack — both **practitioner-claim**). First dollar **day ~35–90 IF a real product fit exists and views materialize**; at creature-channel view counts, expect **$0–150 total by day 90 (analyst estimate)**. Most likely single-sale value $100–150 (practitioner-claim on the commission math, analyst estimate on any conversion happening).
2. **AdSense (post-YPP): almost certainly NOT inside 90 days.** Both channels sit near zero subs against 1K subs + 4K watch hours. Pre-acceptance views pay $0 forever (BePppCvXC-k — **receipted**, revenue tab on screen), which is why the sub-CTA Short and monetize-the-day-thresholds-hit rules are in the cadence. If a video outliers, the practitioner-observed first-upload→monetized floor is ~14 days (4xWQ_fHLGAc — practitioner-claim), but that was an idea-niche channel; for this lane treat YPP inside 90 days as the optimistic tail, not the plan.
3. **Shorts feed the sub gate, not the P&L**: Shorts RPM ≈ $0.05–0.07/1K (QfbGKfkGP8U — practitioner-implied). Never count Shorts views as revenue.

**RPM reality for this lane once monetized (for expectation-setting only):** the only receipted RPM in the 54-video corpus is $3→$6 by runtime in a gaming niche (BePppCvXC-k — **receipted**). Creature spectacle is entertainment-tier; assume **$1–3 RPM (analyst estimate)**. The "finance pays 10x" folklore is why bizdoc (play 2) is the RPM play and this lane is not.

**90-day cases:**
- **Realistic: $0 revenue.** Assets produced instead: 2–3 long-forms, ~50–70 Shorts, two clean day-14/week-4–6 data reads, YPP progress meter, and a validated (or falsified) format. Grade: **analyst estimate**, and stated as the base case on purpose — anyone selling a creature channel as 90-day income is reading the corpus's unverified headline claims ("$35K/31 days", "$1K/day"), all flagged UNVERIFIED in `synthesis/policy_dossier.md` §5.
- **Optimistic: $100–400.** One affiliate sale or two ($100–300, practitioner-claim mechanics × analyst-estimate conversion) + an outlier long-form putting one channel within reach of YPP by day ~120 (the 25–30% capture-of-donor-views heuristic — PtO7jd8L2xs, self-reported — applied to Spinosnack/Dinoverse-scale donors is what "outlier" means here). AdSense dollars themselves land after day 90 even in this case.
- **What would beat both cases:** a Short passing gates and running to millions (the PtO7jd8L2xs 6M-view panel is the existence proof — practitioner-claim, n=1). Not plannable; the 10M-Shorts-views/90d YPP route exists but is a lottery, not a milestone.

---

## 6. METRICS + KILL/SCALE CRITERIA

**Measured weekly (Monday read, ≤15 min):** per-upload impressions/CTR/AVD at day 14 only (never earlier — week-1 data is noise on young channels, BePppCvXC-k); Shorts STW + AVD vs the 75–80%/100% gates; subs + watch-hours pace per channel (5-day lag remembered); hours logged vs cap.

**Day 30 checkpoint (process, not performance):**
- V2 shipped? If NOT: the cap has failed its feasibility test — cut scope (drop to Shorts-only until shipped), do NOT raise the cap. Diagnose which stage ate the hours in the `HOURS_LOG`.
- Shorts engine live at 2–3/wk/channel with gate readings? If the two prototypes failed gates twice, pause Shorts volume and fix the format (caption grammar/loop choice) before resuming — gates are ship-gates, not vanity.
- No performance judgments on any upload yet — everything is inside patience windows.

**Day 60 checkpoint (first real reads):**
- V2 4-week read against V1 baseline: above baseline → 80/20 engaged, V3 sequel in production; below → one deliberate packaging/format change on the next upload (diagnostic ladder), not a rebrand.
- PPOV: episode-2 go/no-go actually executed; published-video verdict now allowed (it passes week 6): if impressions ≈ 0, the single sanctioned repackage test (retitle/rethumbnail mirroring a proven winner's shape — q0G-FzS6uxk, 9iP588aMFBc) may run. Never delete.
- Affiliate: if the link is live, clicks >0? If zero clicks on ~10K+ combined views, the affiliate test is falsified — remove at day 90.

**DAY 90 VERDICT — pre-committed (decision D5). Evaluate both channels, then the lane:**

**FUND (lane keeps its 4 hrs/wk):** ANY of —
1. One long-form ≥25K views at its 4–6-week verdict, or ≥10x the channel's prior-video baseline;
2. Combined net new subs ≥400 across both channels (pace that puts the leading channel at YPP inside ~6 more months);
3. ≥2 Shorts that passed their gates AND exceeded 100K views each (evidence the derivative engine can attack the sub gate at scale).
→ Consequence: 80/20 formalized (4 of 5 uploads repeat the winning frame), hours stay capped at 4, next 90-day plan written for the winning channel only.

**CONSOLIDATE:** exactly one channel shows any of the above → ALL lane hours go to that channel; the other goes dormant (below) immediately rather than at a later review.

**DORMANT (the honest kill):** by day 90, no upload beat 5K views at its 4–6-week verdict AND combined net new subs <150 AND no gate-passing Short broke 50K. → Long-form production stops; channels stay live and untouched (never delete — winners retro-test the back catalog, 9iP588aMFBc); Shorts queue drops to zero or a 30-min/week trickle at Jeff's discretion; all reclaimed hours flow to plays 1–3. **Reactivation trigger (standing, costs one Monday glance):** any back-catalog video suddenly exceeding ~20K views/week — the retro-test signature — reopens the lane for one sequel attempt under the same cap.

The verdict is written as a memo with the actual Studio numbers pasted in, filed in `NEXT_VIDEO.md` + the Rexcaped memory file. No verdict extensions: "one more video will prove it" is the failure mode this section exists to prevent.

---

## 7. RISKS + MITIGATIONS

| Risk | Likelihood/impact | Mitigation (existing system, by name) |
|---|---|---|
| **Grok free tier dead** — primary motion engine lost | Unverified but reported (Qsi9MeLh95Q); high impact | Day-1 blocking verification; pre-approved fallback ladder (D2): Meta AI f2v → Google Vids Veo → local VACE-1.3B (`tools/amber/stage_b_vace.py`). No batch starts before the status line is written. |
| **YPP "inauthentic content" rejection — sameness trigger** (#1 platform risk) | Real; the rejection term is literally "mass-produced," triggered by stylistic sameness even with human voices (4xWQ_fHLGAc; PtO7jd8L2xs, 0SPqPnpQsWE) | Fingerprint diff on every upload (`scripts/extract_motion_events.py` vs all priors); clip-variety rule; caption-template rotation every ~10 Shorts; AI-disclosure=YES always; appeal packet archived per video (`scripts/verify_render.py` reports + provenance stamps) — declines are appealable with a case (ipbnR92Elxg). |
| **Distribution-side squeeze on faceless AI** | Predicted by industry-adjacent sources (ZKsldrcO_fU — opinion) | The lane's architecture is the counter: measured edit grammar (`research/edit_grammar_ruleset.md`), composites into REAL footage (tactic 6.22), locked voices, format identity. If squeeze materializes as zero-impression uploads despite passing gates, that feeds the Day-90 DORMANT criteria — the plan prices this risk in rather than fighting it. |
| **Entertainment RPM makes even success small money** | Certain (analyst estimate: $1–3 RPM) | Judges already priced it: this is play #5, the optionality bet. The Day-90 gate caps total exposure at ~55 hours. Affiliate test is the RPM hedge. |
| **Hours-cap blowout** (the lane's historical failure mode) | High without enforcement | `HOURS_LOG` in `NEXT_VIDEO.md`; two consecutive over-cap weeks → automatic scope cut (Shorts-only until caught up); one long-form lane in production at any time; plays 1–3 own the calendar. |
| **Judging too early / churning packaging** | High (default human behavior) | The written patience protocol: 14-day no-touch, 4–6-week verdicts, never delete (BePppCvXC-k, ROPkHP8jpW0, 9iP588aMFBc, q0G-FzS6uxk — STRONG convergence). Protocol is in the handoff file, not in memory of good intentions. |
| **Shorts engine produces its own sameness fingerprint** | Medium | Caption-style rotation every ~10 uploads (PtO7jd8L2xs); distinct source beats enforced by `scripts/extract_motion_events.py` selection; STW/AVD gates kill low-quality derivatives before they publish. |
| **PPOV drifting kids-classifiable** | Low but catastrophic to RPM (COPPA — lDpOnE3VJVI, sMo5RT_dPxc) | Not-for-kids positioning is locked; no cutesy styling; verify audience setting on every upload. |
| **i2v physics/talking-creature failures reaching the owner** | Known failure class | Frame-strip QA on every clip + physics riders + mouth-closed riders (`feedback_i2v_real_physics`, `feedback_i2v_talking_creature_qa`) — mandatory before Jeff watches anything. |

**Judge-flagged uncertainty carried forward honestly:** every revenue number in this genre except two Studio-verified cases (BePppCvXC-k, YtpQSmu794k) is unreceipted. This plan therefore budgets $0 as the base case and treats the lane's 90-day output as *data and optionality*, not income.

---

## 8. DO-NOT LIST (this play specifically)

1. **Do NOT start any new channel, format, or niche in this lane.** Two channels, one format family each. The Dinoverse-clone/variant machinery already exists — new bets go through `pipeline_v2/topic_scorer.py` in a future quarter, not this one.
2. **Do NOT exceed the cap or borrow hours from plays 1–3** — two over-cap weeks triggers scope reduction, never cap expansion.
3. **Do NOT touch packaging inside day 14, write off anything before week 4–6, or delete/unlist any flop ever** (retro-testing evidence: 9iP588aMFBc).
4. **Do NOT buy anything**: no paid gen stacks (Higgsfield, kie.ai, Kling, Flow paid), no Promotions ($0.53/sub benchmark rejected — ROPkHP8jpW0), no VidIQ/NexLev paid, no aged channels, no ElevenLabs resellers. fal.ai remains back-pocket with explicit owner approval only.
5. **Do NOT publish anything with a visible or cropped-out provider watermark** (SynthID survives; concealment = intent at review — NlfmQpSaYMo, lDpOnE3VJVI), and never answer the AI-disclosure question "No."
6. **Do NOT enter the adjacent template niches** (BeamNG, Roblox, renovation, MS-Paint, pigment ASMR, kids anything) — saturated policy targets per the negative-intel log in `playbook/ideation.json`.
7. **Do NOT run daily-volume cadence or one-continuous-look edits** — quality gates and the clip-variety rule stand; last-frame chaining stays within-beat only (sMo5RT_dPxc, 32DLRsFiXZY).
8. **Do NOT use AI human faces or clone anyone else's voice** — creature/environment gen only; real photos for real people (`feedback_ai_faces_use_real_photos`); locked own-library voices per channel.
9. **Do NOT let Shorts become the product** — they are the sub-gate attack and discovery surface ($0.05–0.07/1K RPM); the moment Shorts hours crowd out a long-form ship date, Shorts drop to 2/wk/channel.
10. **Do NOT re-derive anything this plan folds in** — the mechanics live in `synthesis/action_plan.md`, the gates in `scripts/extract_motion_events.py` + `gate_style.py` + `scripts/verify_render.py`, the grammar in `research/edit_grammar_ruleset.md` and `research/viral_recreation_spec.md`. Hard rule #3: never invent parallel solutions.
