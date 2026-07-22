# HYPE FILTER & CONFLICT LIST

Synthesized from all 32 analyzed videos (`analysis/<id>.json`). Adjudications use
`STRATEGY_CONTEXT.md` hard rules, `research/edit_grammar_ruleset.md` (measured values), the
7-module playbook (`playbook/{editing,intros,scripting,titles_thumbnails,retention_delivery,ideation,sources}.json`),
and `pipeline_v2/topic_scorer.py` (9 tests, GO=85+) as tiebreakers. Every claim cites video ids.

---

## 1. Recurring hype patterns

### 1.1 Unverifiable / fabricated revenue "proof"
The dominant pattern: revenue numbers that are computed, staged, or third-party — never audited.
- **Currency-toggle theatre**: "$500K/year" proven by switching Studio's revenue currency USD→EUR — proves a dashboard renders a number, nothing else (QfbGKfkGP8U).
- **Arithmetic sold as receipts**: "$27,875" = 4M views × a NexLev RPM estimate the presenter *himself* calls inaccurate (ipbnR92Elxg); "$1,024,937/90 days" in the title while on-screen numbers total ~$130K (E_CIP98ufto); "$400/day" in the description for what the screenshot shows is ~$400 *total* (4xWQ_fHLGAc).
- **Anonymized/obscured dashboards**: channel identity hidden ($5.2K, 54UTQ2kFhuA); anonymized student screenshots (8KXlxAKOTdE); title revenue "shown somewhere on screen," never itemized (zJmYdcvwY1Y); self-reported $35K on a channel he admits was *purchased pre-monetized* (PtO7jd8L2xs).
- **The tool's own marketing dashboard as evidence**: Noodle Tomato's "$8,500/mo niche" numbers are rendered by the product being sold (8Mx2m0djgTA).
- **Other channels' view counts as "proof" of the method**: the presenter shows third-party channels, not their own results (32DLRsFiXZY, 3MPSrpIOpAo, Ao_d-uaMJvk, h6DB0e96GI0, KxsasFMMPpA, lL9gjPw5yjg, NA0AOlCmelQ, NlfmQpSaYMo, sMo5RT_dPxc, LGYiPA5SKvw — whose "proof" is a *different* channel's old views).

**Filter rule**: a revenue claim counts only if it is the presenter's own channel, the channel is named, and the method-to-revenue causality is shown. Zero of 32 videos fully pass. The only credible *mechanism-level* receipt in the corpus is the 7s-video/86%-stayed/28s-AVD analytics panel (PtO7jd8L2xs).

### 1.2 Affiliate / course / lead-magnet funnels
- **Affiliate tool pushes** (VidIQ, NexLev, Abacus, Higgsfield, kie.ai, Kling/DuoPlus, Edimakor, GenAIPro, Printify, Post Planner/Kittl, Noodle Tomato): 8N7-vQ9qX4w (entire video is a VidIQ funnel dressed as "NEW algorithm rules"), 8KXlxAKOTdE, 4xWQ_fHLGAc (title says Claude Code; workflow is Abacus, his affiliate), 8Mx2m0djgTA, E_CIP98ufto, KZKFlik4M8I, KxsasFMMPpA, LGYiPA5SKvw, Dmqz8opSHzE, TiycelzfzC0, r81ImbWaxEE, sMo5RT_dPxc, 32DLRsFiXZY (incl. Pippit, a tool that never appears in the video).
- **Coaching/course/mentorship upsells**: tICnK3Qb2k8, 8KXlxAKOTdE (4 book-a-call CTAs), ipbnR92Elxg, PtO7jd8L2xs, QfbGKfkGP8U, Ao_d-uaMJvk, Xf_J7kBzxvo, 3MPSrpIOpAo, r81ImbWaxEE (the "45-item do/don't list" is paywalled), LGYiPA5SKvw (own software + course).
- **Seller-conflict special**: 54UTQ2kFhuA sells BOTH the research tool (ChannelRecipe) and the aged channels (headstartchannels.com) his method requires — the advice manufactures demand for his own products.
- **Prompt-doc/community lead magnets** (Telegram "Zen_Earn": NlfmQpSaYMo, h6DB0e96GI0, lDpOnE3VJVI, lL9gjPw5yjg; WhatsApp: 0SPqPnpQsWE, 3MPSrpIOpAo, 32DLRsFiXZY; Skool/Discord: Dmqz8opSHzE, TiycelzfzC0, KxsasFMMPpA, 8KXlxAKOTdE; Gumroad: 4xWQ_fHLGAc, E_CIP98ufto; Telegram: zJmYdcvwY1Y).

**Filter rule**: funnel presence doesn't automatically zero a video (Dmqz8opSHzE and TiycelzfzC0 are funnel-backed AND mechanically solid) — but any claim that exists *only* to justify the funneled product (trust scores → aged channels; "new rules" → VidIQ trial) is discarded.

### 1.3 "Free tool" bait that is actually paid, capped, or watermarked
- **"Omni Flash is free"** — it is a paid Gemini-tier model, and Google Flow's free tier is ~50 credits/day of *watermarked* Veo output (per our own 2026-07-20 audit, `reference_ai_cardboard_diy_niche`): NlfmQpSaYMo, h6DB0e96GI0, sMo5RT_dPxc, lDpOnE3VJVI, lL9gjPw5yjg. "Unlimited free Nano Banana" (NA0AOlCmelQ) and "no limit" bulk stills (zJmYdcvwY1Y) contradict the same audit.
- **The tell**: tutorials claiming "100% free" then teaching a *watermark-hiding step* (scale-and-shift or overlay) — the hidden cost admitting itself (NlfmQpSaYMo, lDpOnE3VJVI). SynthID invisible watermarking survives the crop; concealment only adds provenance-obfuscation risk.
- **Free-credit multi-accounting as "hack"**: fresh-browser Flow refills (32DLRsFiXZY), 10-minute-mail accounts (3MPSrpIOpAo), multi-Gmail Wan farming (NA0AOlCmelQ), HeyGen free-account cycling (PtO7jd8L2xs) — all platform ToS abuse.
- **Gray-market credit resellers**: AI33.pro reselling ElevenLabs at $5/1M credits (3MPSrpIOpAo), GenAIPro (ipbnR92Elxg, 8KXlxAKOTdE).

### 1.4 Aged-channel tricks disguised as skill
- **Buying aged/pre-monetized channels is the hidden engine of "monetized in days" claims**: stated openly as "Trick No. 1" (0SPqPnpQsWE); productized as headstartchannels.com behind a "trust score" theory (54UTQ2kFhuA); the "$35K from zero" case started on a purchased pre-monetized channel (PtO7jd8L2xs); normalized with a half-warning (8KXlxAKOTdE); region-registered TikTok accounts sold to viewers (KxsasFMMPpA). Account trading violates YouTube ToS (non-transferable accounts) and carries termination risk.
- **"Trust score" / shadow-ban warming rituals** — folk theory YouTube has never confirmed (8KXlxAKOTdE, 54UTQ2kFhuA, q0G-FzS6uxk). The *behaviors* (warm-up, ID verification) are free and harmless (q0G-FzS6uxk); the *mechanism* is unfalsifiable.

**Filter rule**: any genre claim of "monetized in 2-10 days" is read as an aged-channel purchase in disguise and discarded (0SPqPnpQsWE, 54UTQ2kFhuA, PtO7jd8L2xs).

### 1.5 Other recurring hype
- **False-novelty framing**: "NEW algorithm rules" that are years-old Studio features (8N7-vQ9qX4w); "untapped/0-competition niches" contradicted inside the same video (tICnK3Qb2k8) or evidenced by a single unnamed channel (NlfmQpSaYMo, lL9gjPw5yjg, h6DB0e96GI0, sMo5RT_dPxc).
- **Policy silence as a red flag**: videos teaching exactly the mass-produced template-AI profile that the July-15-2025 "inauthentic content" YPP policy targets, with zero mention of it (8Mx2m0djgTA, 6WDvO0Lu1sY, Ao_d-uaMJvk, h6DB0e96GI0, NA0AOlCmelQ, lDpOnE3VJVI, sMo5RT_dPxc, Dmqz8opSHzE, TiycelzfzC0, KxsasFMMPpA, 8KXlxAKOTdE).
- **Watch-hour farming**: looping a pre-recorded video as a 24/7 "live" stream to hit 4,000 hours (eF75ZffgsUk) — a textbook inauthentic-content trap.

---

## 2. Conflict list — adjudicated

Tiebreakers: measured data (`edit_grammar_ruleset.md`, `viral_recreation_spec`) beats guru round numbers; hard rules beat everything; when two gurus disagree, the one whose claim has an on-screen mechanism wins.

### C1. Cut pacing: 3s vs 2.5s vs 5-15s vs measured 5-7s  ⭐ (top-3)
- "Change visuals every 3 seconds" (LGYiPA5SKvw) — his own generated output ignored the rule (clips ran 5-7s) and he shrugged.
- "2.5s hard ceiling on static-image holds" for stills-driven POV video (Ao_d-uaMJvk).
- "One image per 5-15 seconds" density (Dmqz8opSHzE).
- 4s/6s-only clip lengths, cut every ~4-6s (TiycelzfzC0).
**Verdict: trust the measured grammar.** `playbook/editing.json` (cuts every 5-7s) and `edit_grammar_ruleset.md` (0.07-0.13s rapid-fire montages on lists, cut-on-numbers/turn-words) are *measured from winning competitor videos*, not asserted. TiycelzfzC0's 4-6s discipline independently lands on the same numbers — convergent confirmation. The 3s round number is unfounded (and self-refuted on screen); the 5-15s hold violates the grammar. The 2.5s ceiling survives only as a *narrow, testable parameter for static stills on Prehistoric POV* (a format the longform grammar wasn't measured on), not as a general law.

### C2. Sameness paradox: "double down on the formula" vs "vary or get demonetized"  ⭐ (top-3)
- Squeeze a proven format "until you squeeze out all the juices"; the off-formula video is the one that flops (zJmYdcvwY1Y); 80/20 double-down (8KXlxAKOTdE); clone the winner wholesale because Shorts distribution ignores channel identity (PtO7jd8L2xs).
- vs.: rotate templates "try not to work on the same template" from a practitioner in active community-guideline trouble (0SPqPnpQsWE); rotate the caption template every ~10 videos to dodge repetitious-content demonetization (PtO7jd8L2xs — the *same* video); "mass-produced" stylistic sameness was the literal YPP rejection term, even with a human voice (4xWQ_fHLGAc).
**Verdict: both are right at different layers — repeat the FORMAT, vary the FINGERPRINT.** The concept/packaging formula repeats (that is the whole `viral_recreation_spec` + Dinoverse-clone play, and the topic scorer's fresh_perspective test governs when to deviate); the per-video *edit fingerprint* must vary (extend the `clip_variety_rule` from intra-video to inter-video: diff uploads with `extract_motion_events.py` — cut density, montage placement, music/SFX pattern — before publish, per the 0SPqPnpQsWE application). Sameness at the template/pixel layer is the documented enforcement trigger; sameness at the format layer is the documented growth engine. Four videos independently confirm the enforcement half (0SPqPnpQsWE, PtO7jd8L2xs, 4xWQ_fHLGAc, r81ImbWaxEE's TikTok ~300-videos/30-day low-quality ban).

### C3. Length: pad-for-watch-time vs retention-first  ⭐ (top-3)
- "Make yours 1.5x longer than the competitor's" (8KXlxAKOTdE); "longer video = higher chance of beating them on AVD" (ipbnR92Elxg); 25-30min pre-monetization then stretch toward 2h (3MPSrpIOpAo); go 35-40min in mature niches for RPM (zJmYdcvwY1Y).
- vs.: "length ≥ ~90th percentile of *topic winners*" (8N7-vQ9qX4w); story-driven length + hook/retention craft (q0G-FzS6uxk); `playbook/retention_delivery.json`.
**Verdict: derive length from measured topic winners; never pad.** The 8N7-vQ9qX4w formulation is the only defensible one because it is anchored to observed winner runtimes (bizdoc's 23.4-min video sits inside the shown 19-40-min range) — and it is just our deep-watch practice restated. The pad-for-watch-time versions conflate absolute watch time with AVD%, and padding wrecks the retention curve that `retention_delivery.json` optimizes. Length is an *output* of the story and the measured format, not an input.

### C4. Thumbnails: "topic+length outrank thumbnails" vs packaging-first
- Thumbnails/quality downgraded below topic+length (8N7-vQ9qX4w, asserted, no data, inside a VidIQ funnel).
- vs.: thumbnail-text-first ideation (3MPSrpIOpAo), thumbnail-first production gate — kill topics whose thumbnail doesn't read (ipbnR92Elxg, q0G-FzS6uxk); PSR-overrides-packaging applies only to *established* audiences, so new channels have nothing but packaging (Xf_J7kBzxvo).
**Verdict: packaging-first wins for us.** All three of our channels are small/new — precisely the case where Xf_J7kBzxvo's own logic says packaging discipline is everything. The topic scorer already gates title_thumbnail + five_second_title at selection time, and `titles_thumbnails.json` (26 tactics) stays authoritative. Adopt the *ordering* upgrade (render the actual thumbnail before committing production — ipbnR92Elxg); discard the thumbnail dismissal as contrarian funnel bait.

### C5. Thumbnail source: video frame vs gen-from-scratch
- Pick the most significant video frame, have ChatGPT make "a simple thumbnail" from it (Ao_d-uaMJvk).
- vs.: gen from scratch, candid real-phone-photo look, ONE focal point, explicitly NO video frames (our measured thumbnail recipe; independently confirmed by the "lower the image quality so it looks realistic" prompt line in ipbnR92Elxg).
**Verdict: the existing recipe wins** — it is owner-tested and codified (`feedback_dinoverse_thumbnail_style`); Ao_d-uaMJvk's shortcut directly contradicts it and offers no evidence.

### C6. AI-risk theory: "AI voice is fine" vs "AI pipelines don't work anymore"
- AI VO passed YPP across multiple channels; sameness, not voice, is the trigger (4xWQ_fHLGAc); enforcement targets "slop-pattern usage, not AI tools" (tICnK3Qb2k8); banned channels share spammy/no-human-input traits, not AI usage (LGYiPA5SKvw).
- vs.: "ChatGPT script + AI voiceover doesn't work anymore," partial human effort is no safe harbor, Gemini allegedly reads whole-video context (q0G-FzS6uxk).
**Verdict: reconcile, don't pick.** The consistent middle across all four: AI tooling per se is acceptable; *low-effort mass-produced patterns* are the target; the defense is visible human editorial layers, variety, and disclosure. This is already our July-2025 policy read. Operational consequences we adopted: archive per-video human-editorial evidence as a YPP appeal packet — decline-then-appeal-then-monetized is a demonstrated path (ipbnR92Elxg); always set the altered/synthetic disclosure (eF75ZffgsUk shows the flow, gives the *wrong* advice; E_CIP98ufto's leave-the-label-off is the negative example); keep the clip-variety rule as the primary YPP defense (4xWQ_fHLGAc).

### C7. Cadence: volume-play vs quality gates
- 1-2 uploads/day for 30+ days (54UTQ2kFhuA); 3-15/day (E_CIP98ufto); 8-10/day (r81ImbWaxEE); outsource at $15-30/video (8KXlxAKOTdE).
- vs.: our per-video QA gates (frame-level QA, style gate, motion-event ship-gate) and r81ImbWaxEE's *own* datum that TikTok bans accounts near ~300 low-quality videos/30 days.
**Verdict: quality-gated cadence wins.** Volume-at-slop-quality is the demonetization profile on both platforms; the pipeline's ~$0 marginal cost means cadence rises through pipeline efficiency, never by relaxing gates. Keep the salvageable discipline from the volume camp: an explicit N-video test budget + impressions-vs-clicks-vs-retention kill diagnosis (8KXlxAKOTdE) and 30-day judgment windows (54UTQ2kFhuA).

### C8. "Editing cannot be automated" vs the FFmpeg engine
- "You won't be able to automate the editing; everything will have to be done manually" (zJmYdcvwY1Y); manual CapCut assembly recommended because AI sync is imperfect (Dmqz8opSHzE, Ao_d-uaMJvk, E_CIP98ufto, 4xWQ_fHLGAc).
**Verdict: disproven in-house.** `scripts/ffmpeg_production_render.py` + WhisperX word-level alignment + `verify_render.py` already automate exactly what these videos do by hand, with a narration-transcription QA check none of them has. This conflict is a capability gap on *their* side.

### C9. Ideation: automated AI mining vs operator-graded scoring
- VidIQ-MCP/AI idea mining (8N7-vQ9qX4w); meta-prompt idea factories (ipbnR92Elxg); vs. the same tactic demoed then *disavowed* because manual browsing builds format intuition (zJmYdcvwY1Y).
**Verdict: hybrid, with the scorer as the gate.** Automated mining is allowed only as a *candidate generator* feeding `topic_scorer.py` (the 54UTQ2kFhuA demand-gap clustering front-end is the best version in the corpus); the 9-test GO=85+ decision stays operator-graded. Never outsource the verdict to a tool whose vendor is an affiliate.

### C10. Minor conflicts (fast rulings)
- **Uncheck notify-subscribers to "hide from subs"** (8N7-vQ9qX4w) — factually overstated (skips feed/notifications only) and irrelevant at our sub counts. Ignore.
- **Chaining every clip for continuity** (32DLRsFiXZY, sMo5RT_dPxc) vs the clip-variety rule — chaining is scoped to continuous-action pairs and POV sequences only; the variety rule takes precedence on adjacent list/montage beats.
- **Clip-native SFX at low volume** (TiycelzfzC0) vs bizdoc `clip_audio:"mute"` — test on Rexcaped only; the bizdoc mute exists for fair-use and VO-integrity reasons and stands.
- **"Recognizable faces boost CTR"** (tICnK3Qb2k8) vs no-AI-faces — compatible only via real photos (hard rule `feedback_ai_faces_use_real_photos`); A/B a real executive photo on bizdoc, never a generated face.

---

## 3. Popular in this corpus but WRONG for this operation

Each entry names the hard rule (from `STRATEGY_CONTEXT.md` / CLAUDE.md / memory) it violates.

| Advice (ids) | Why it's wrong for us — rule violated |
|---|---|
| Buy aged/pre-monetized channels (0SPqPnpQsWE, 54UTQ2kFhuA, PtO7jd8L2xs, 8KXlxAKOTdE, KxsasFMMPpA) | YouTube ToS violation (non-transferable accounts) + termination risk on the channels we're building clean; also "no spend without prototype" |
| Multi-account credit farming: fresh browsers, temp mail, multi-Gmail, HeyGen cycling (32DLRsFiXZY, 3MPSrpIOpAo, NA0AOlCmelQ, PtO7jd8L2xs) | Platform ToS abuse; pointless anyway — Grok i2v + local VACE-1.3B/LTX already give $0 generation |
| Gray-market credit resellers AI33.pro/GenAIPro (3MPSrpIOpAo, ipbnR92Elxg, 8KXlxAKOTdE) | Hard rule: no new paid services without asking; payment/ToS risk; ElevenLabs already works |
| New paid subscriptions as the fix: VidIQ, NexLev, Abacus, Higgsfield, kie.ai, Noodle Tomato, Narration AI, Flow paid, Edimakor (8N7-vQ9qX4w, 8KXlxAKOTdE, 4xWQ_fHLGAc, E_CIP98ufto, LGYiPA5SKvw, Dmqz8opSHzE, TiycelzfzC0, 8Mx2m0djgTA, Ao_d-uaMJvk, r81ImbWaxEE, sMo5RT_dPxc) | Hard rule: NO new paid APIs/subscriptions without asking (`feedback_no_spend_without_prototype`); every capability duplicated in-house at $0 |
| AI human faces / HeyGen self-clone avatars / public-figure black-bar filter evasion (ipbnR92Elxg, PtO7jd8L2xs, TiycelzfzC0) | Hard rule: no AI-generated human faces — owner rejects them; real photos only (`feedback_ai_faces_use_real_photos`); black-bar trick adds synthetic-depiction disclosure risk |
| Wholesale clip reuse: OBS-rip Disney+/Netflix, TikTok clip reuse "transformed" by text overlay (PtO7jd8L2xs, QfbGKfkGP8U) | Fair-use hard rules (≤7s/clip, ≤30s/source, mute audio, transformative layers) + copyright exposure + prime July-2025 inauthentic-content target |
| Hide the Veo/Flow watermark (NlfmQpSaYMo, lDpOnE3VJVI) | Provenance/frame-level-QA ethos + disclosure requirement; SynthID persists so concealment only proves intent |
| Leave the AI-content label off (E_CIP98ufto explicitly; eF75ZffgsUk "click no") | Altered/synthetic disclosure requirement; Rexcaped/PPOV publish photoreal AI creatures and must tick YES |
| Loop-stream a video 24/7 as "live" to farm 4,000 hours (eF75ZffgsUk) | July-2025 inauthentic-content policy — our #1 stated platform risk; misleading-metadata exposure |
| Rewrite a competitor's transcript as your script (zJmYdcvwY1Y); no-script "words of the heart" production (0SPqPnpQsWE) | 95+ script quality bar + originality test in `topic_scorer.py`; reused-content risk |
| "Any random looping visuals are fine" (3MPSrpIOpAo); one-token prompt-farm niches — crash Shorts, renovation, miniature cooking, twig sculptures, Roblox cartoons, nursery rhymes (32DLRsFiXZY, 6WDvO0Lu1sY, h6DB0e96GI0, lL9gjPw5yjg, sMo5RT_dPxc, lDpOnE3VJVI) | The measured `edit_grammar_ruleset.md` + clip-variety rule exist precisely to avoid this repetitive-AI profile; kids niches add Made-for-Kids RPM collapse |
| One-click end-to-end video factories (8Mx2m0djgTA Noodle Tomato; Heclus in Dmqz8opSHzE) | The moat IS the opposite: FFmpeg engine + measured grammar + human QA; template output is the demonetization archetype |
| Volume posting 3-15/day with $15-30 freelancers or $3-4/hr VAs (E_CIP98ufto, 8KXlxAKOTdE, r81ImbWaxEE) | Incompatible with frame-level QA / style gate / motion-event ship-gate; in-house pipeline is cheaper AND better |
| Delete-and-repost dead videos to a fresh channel (8KXlxAKOTdE) | Reused-content review risk — the exact enforcement vector we engineer around |
| Multi-account identical-video blasting via cloud phones (KxsasFMMPpA) | YouTube spam/deceptive-practices + inauthentic-content criteria; codified as a standing never-do |
| Launch non-English channels you can't QA (3MPSrpIOpAo) | VERIFY BEFORE CLAIM / frame-level QA culture — un-reviewable output; the salvageable version is auto-dub tracks on existing channels (4xWQ_fHLGAc) |

---

## 4. Tier ranking — all 32

### Tier A — genuinely load-bearing (10)
| id | why |
|---|---|
| PtO7jd8L2xs | Only credible mechanism-level receipt in the corpus (7s/86% STW/28s AVD panel): AVD-hack format, STW≥75-80%/AVD≥100% Shorts ship-gates, quantified niche-gap thresholds for the topic scorer — even though its sourcing stack is banned for us. |
| q0G-FzS6uxk | Best-sourced policy intel (verbatim CEO blog + community-guidelines quotes) plus free launch mechanics we adopted: pre-launch warm-up/ID verification, 72h no-evaluation window, no low-intent Reddit seeding. |
| 4xWQ_fHLGAc | Filled the channel-metadata gap none of the 7 playbook modules covered (cold-start keyword seeding, auto-dub, unlisted-first) + the "mass-produced" YPP rejection-term intel that converts the clip-variety rule into our primary YPP defense. |
| 8KXlxAKOTdE | Three adopted mechanics wired into existing systems: search-bar supply check (3+ replications threshold) into the scorer, 80/20 double-down ratio into ideation.json, impressions-based kill diagnosis for the young channels. |
| 8N7-vQ9qX4w | Despite being a VidIQ funnel: exposed the Shorts multi-surface gap, the weekly channel-audit pattern (cloneable at $0), and the single-variable A/B protocol added to titles_thumbnails. |
| LGYiPA5SKvw | Honest costs + real demo: ranked-30-idea backlog with posting packages (batches the topic scorer), FTC affiliate-disclosure boilerplate, WIPO trademark check — all adopted into launch/upload practice. |
| Dmqz8opSHzE | SAM 2 local multi-element segmentation = the single best technical upgrade in the corpus for the rembg layered-composite engine (parallax Ken Burns for bizdoc, between-layer creature placement for Rexcaped), $0. |
| TiycelzfzC0 | Above-genre evidence; four portable mechanics: 0.25s i2v head-trim (TEST — conditional on a frame-strip check confirming the artifact in Grok clips), timestamp-conditioned i2v prompts, per-still style-reference conditioning, low-volume clip-native SFX. |
| Xf_J7kBzxvo | Three free script-QA upgrades mapped to scripting.json: coffee-shop rule pre-TTS pass, ~10 direct-address moments lint, viewer-comment referencing; validates faceless task-attraction thesis. |
| ipbnR92Elxg | The YPP decline-then-appeal precedent → per-video human-editorial appeal packet (aimed squarely at the #1 platform risk) + thumbnail-first production gate; also confirms real-footage-beats-AI-slop = the composite moat. |

### Tier B — one useful nugget (16)
| id | nugget |
|---|---|
| 0SPqPnpQsWE | Practitioner confirmation that repetitive-content detection is template-sensitive → inter-video edit-fingerprint diff via extract_motion_events.py. |
| 32DLRsFiXZY | Last-frame continuity chaining (FFmpeg last-frame → next Grok i2v input), scoped within-beat. |
| 3MPSrpIOpAo | Competitor-thumbnail style transfer via GPT image gen + the bizdoc channel-settings/SEO pre-upload checklist. |
| 54UTQ2kFhuA | Competitor-corpus → Claude demand-gap clustering as a candidate-generating front-end for the 9-test scorer. |
| 6WDvO0Lu1sY | Creature turnaround sheet as reference asset + chained-still state continuity — two cheap consistency-gate experiments. |
| Ao_d-uaMJvk | 2.5s static-hold ceiling + 150-200 scene-density budget for Prehistoric POV stills-driven video. |
| E_CIP98ufto | The save/share-designed "metaphor beat" as the selection lens for shorts cuts (plus FB invite-threshold intel). |
| QfbGKfkGP8U | Vignette-spotlight tracked attention guide + vertical caption color grammar — real FFmpeg-portable mechanics, dormant until a Shorts lane exists. |
| eF75ZffgsUk | Feature-eligibility phone-verification pre-launch check + the per-channel AI-disclosure decision (its core loop-stream method is radioactive). |
| lDpOnE3VJVI | Gemini "create music" as a rights-gated $0 custom music-bed test; also codified the watermark-hiding never-do. |
| lL9gjPw5yjg | Google AI Studio TTS as a licensed $0 VO fallback (matters because F5-TTS is CC-BY-NC-blocked for monetized use). |
| NlfmQpSaYMo | Counterfactual-deletion cold-open hook ("imagine waking up and X no longer existed") as an intros.json variant for bizdoc. |
| r81ImbWaxEE | 3-prompt-variants-per-still best-of-N for Grok i2v + the TikTok ~300/30-day ban as cross-platform repetitive-AI evidence. |
| sMo5RT_dPxc | Save-last-frame-then-animate chaining variant for continuous-action pairs (scoped under the clip-variety rule). |
| tICnK3Qb2k8 | Adversarial-curiosity legal title formulas + "POV: you're the [role] when [stakes]" packaging; independently confirms the bizdoc high-CPM lane. |
| zJmYdcvwY1Y | Monetization-survivor scan (hit channel suddenly stops uploading ⇒ likely YPP denial) as a free niche-vetting pre-check. |

### Tier C — safely ignorable (6)
| id | why ignorable |
|---|---|
| 8Mx2m0djgTA | Pure affiliate demo of a one-click video factory; every real pattern (concept scoring, script briefs, cold opens) already exists here in stronger measured form. |
| CQWfqKGFoPM | Credible but dormant: membership smart-pricing news for channels that have YPP + memberships — we have neither; one future checklist line captured. |
| h6DB0e96GI0 | 103-second Telegram-funnel demo of a one-token prompt farm; sole value is a negative-example log entry in ideation. |
| KZKFlik4M8I | Facebook meme-page + POD funnel; confirms research-first doctrine we already run measured; the FB repost test is marginal. |
| KxsasFMMPpA | 189-view sponsor pitch for cloud-phone account farms; the pipeline it demos is a weaker copy of ours; distribution model is codified as a never-do. |
| NA0AOlCmelQ | Unevidenced sub-farming tutorial; character-block prompt injection is a strictly weaker cousin of the compositing/provenance system. |

**Count check**: 10 A + 16 B + 6 C = 32.
