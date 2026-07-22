# Per-Channel Action Plan — synthesized from 32 video analyses

Synthesis date: 2026-07-21. Sources: `analysis/<id>.json` (all 32), `analysis/COMBINED_INDEX.md`, `STRATEGY_CONTEXT.md`.
Every action cites source video ids. Aggressively deduped: ~8 videos converge on Shorts derivatives, ~6 on upload/channel-metadata hygiene, ~5 on "sameness, not AI, is the demonetization trigger," ~5 on ideation-front-end upgrades — each appears once, in the highest-leverage form.

**Bucket definitions**
- **DO NOW** — free, done before/at the next upload; no new tooling.
- **NEXT VIDEO** — folds into the video currently in production (rexcaped V2 Spino/Lagos; bizdoc Breaking-the-Law upload; PPOV next episode).
- **EXPERIMENTS** — cheap tests with a defined success metric; each names its one-sample proof (prototype-before-plan).
- **CAPABILITY BUILDS** — new tooling worth building with Claude Code on the existing FFmpeg pipeline.
- **DO NOT DO** — explicitly rejected, with the rule it violates.

**Top-priority ranking (all channels)**
1. Bizdoc pre-upload launch checklist — the upload is imminent and several items only work pre-launch (4xWQ_fHLGAc, eF75ZffgsUk, q0G-FzS6uxk, 3MPSrpIOpAo, LGYiPA5SKvw).
2. Rexcaped V2 upload-package additions incl. the V1-vs-V2 edit-fingerprint diff (0SPqPnpQsWE, 4xWQ_fHLGAc, PtO7jd8L2xs).
3. Shorts/vertical derivative pipeline — the single biggest gap; 8 videos independently point at it (8N7-vQ9qX4w, PtO7jd8L2xs, QfbGKfkGP8U, KxsasFMMPpA, E_CIP98ufto, KZKFlik4M8I, Ao_d-uaMJvk, 6WDvO0Lu1sY).
4. Policy-posture codification: sameness — not AI voice — is the YPP trigger; disclosure + variation + appeal packet are the defense (4xWQ_fHLGAc, q0G-FzS6uxk, ipbnR92Elxg, eF75ZffgsUk, 0SPqPnpQsWE, zJmYdcvwY1Y).
5. Ideation front-end upgrades feeding `pipeline_v2/topic_scorer.py` (54UTQ2kFhuA, 8KXlxAKOTdE, PtO7jd8L2xs, tICnK3Qb2k8, zJmYdcvwY1Y, LGYiPA5SKvw).

---

## 1. REXCAPED (live; Video 2 Spino/Lagos in production — script + VO done, next = stills → composites → render)

### DO NOW
| Action | What changes | Touches | Sources | Payoff |
|---|---|---|---|---|
| Cold-start channel seeding | Add creature-attack niche keywords to channel description + Studio channel keywords (channel is 1 video old — still in the cold-start window) | `NEXT_VIDEO.md` upload checklist | 4xWQ_fHLGAc | Better cold-start audience matching while the window is open |
| Upload-hygiene rules for V2 | Upload unlisted → flip public after HD/dub processing; AI-disclosure = **YES** (photoreal AI creatures in real footage); no Reddit/social seeding; no packaging changes or judgments for 72h post-upload | `NEXT_VIDEO.md` upload checklist | 4xWQ_fHLGAc, eF75ZffgsUk, q0G-FzS6uxk | First viewers never hit low-res/undisclosed versions; avoids low-intent-click retention poisoning; avoids premature repackaging |
| V1-vs-V2 edit-fingerprint diff | Before publishing V2, diff its motion-event fingerprint (cut density, montage placement, music/SFX pattern) against V1 to confirm the edit engine isn't stamping identical grammar on every upload | `scripts/extract_motion_events.py` output vs both cuts; extends `research/edit_grammar_ruleset.md` clip-variety rule to INTER-video variation | 0SPqPnpQsWE, PtO7jd8L2xs, 4xWQ_fHLGAc | Direct hedge against template-sensitive repetitive-content detection — practitioners on both sides confirm it's real |
| Search-bar supply check as scorer input | Before locking any topic: search its exact framing on YouTube, count near-identical treatments; 3+ hits forces a documented differentiated angle before the scorer can pass it | `pipeline_v2/topic_scorer.py` (originality/fresh_perspective evidence), `playbook/ideation.json` | 8KXlxAKOTdE | Mechanical, free evidence for tests that currently run on judgment |
| 80/20 double-down rule (written now, applied later) | Once V2 has 2+ weeks of data: if a format shows outlier views, 4 of next 5 videos repeat the format (new creature/setting), 1 of 5 tests new | `playbook/ideation.json` | 8KXlxAKOTdE | Explicit portfolio ratio replaces vibes once data exists |
| Prompt-batch degradation guard | Where TSV/i2v prompts are generated conversationally, chunk to ~5 prompts/request and spot-check late-batch prompts for length decay | TSV prompt-build workflow (rider system) | zJmYdcvwY1Y | Prevents silently shrinking prompts in long batches |

### NEXT VIDEO (Spino/Lagos)
| Action | What changes | Touches | Sources | Payoff |
|---|---|---|---|---|
| Frame-strip check for static clip heads → 0.25s trim | Run frame-strip QA on V2's Grok i2v clips; if static/artifact first frames are present, add a 0.25s head-trim before concatenation | `scripts/rexcaped_edit_engine.py` (FFmpeg assembly step) | TiycelzfzC0 | Removes the common i2v dead-frame artifact at ~zero cost |
| Thumbnail before render QA | Produce the V2 thumbnail with the existing candid-phone recipe BEFORE final render/watch-through, so packaging can still kill/steer the cut | thumbnail recipe (`feedback_dinoverse_thumbnail_style`), upload package | ipbnR92Elxg, q0G-FzS6uxk | Packaging validated before the expensive last mile |
| Pre-YPP affiliate + FTC disclosure | Add ONE high-ticket affiliate ($100+/sale criterion; survival/outdoor-gear fits "could you survive X") to V2's description with FTC "contains affiliate links" boilerplate; measure clicks | description template in upload package | LGYiPA5SKvw | Only available revenue before YPP; zero production cost |

### EXPERIMENTS (each names its one-sample proof)
| Experiment | One-sample proof | Success metric | Sources |
|---|---|---|---|
| 3 i2v prompt variants per still, best-of-N | ONE Spino/Lagos beat: Claude emits 3 prompt variants (physics/mouth riders baked in), generate all on Grok, keep closest-to-reference | Picked take beats single-shot take on frame-strip QA + consistency gate | r81ImbWaxEE |
| Timestamp-conditioned i2v prompt | ONE cut-on-turn-word beat: WhisperX word time written into the Grok prompt ("at Xs, [motion event]") | `extract_motion_events.py` shows the event landing on the word | TiycelzfzC0 |
| Creature turnaround sheet as reference | ONE approved creature: multi-angle turnaround sheet as Grok upload reference (and future AMBER `reference_images` input) vs current single still | Consistency-gate pass rate improves | 6WDvO0Lu1sY |
| Last-frame chaining, within-beat only | ONE continuous-action pair (strike → aftermath): FFmpeg last-frame extract (`-sseof -0.1`) of clip N feeds clip N+1's gen | Frame-strip QA shows no visible reset; clip-variety rule untouched across beats | 32DLRsFiXZY, sMo5RT_dPxc |
| Gemini "create music" custom bed | ONE script's cut rhythm — but verify commercial/monetized-use rights BEFORE it touches a render | Rights clear AND bed beats the Pixabay pick on the owner's ear | lDpOnE3VJVI |
| Low-volume clip-native SFX under VO | ONE beat mixed at ~-20dB instead of full mute (music stays on top) | Sounds better than mute in the A/B; no VO masking | TiycelzfzC0 |
| Multi-language dub of V1 | ONE ElevenLabs dub track (owner approval for credits first; low priority) | Views from the dubbed track's locale | 3MPSrpIOpAo |
| FB page repost test | Keyword-named FB page, repost existing verticals organic-only, opt into content-monetization waitlist | Kill if 30 days of reposts show negligible reach | KZKFlik4M8I, E_CIP98ufto |
| V3 demand-gap corpus clustering | ONE Claude session on the Spinosnack/Dinoverse corpus (yt-dlp titles+transcripts): cluster creature/scenario supply vs demand | Produces ≥1 candidate that passes the 9-test scorer | 54UTQ2kFhuA |

### CAPABILITY BUILDS
- **Vignette-spotlight attention guide** — feathered inverted-circle mask (~70% opacity black layer), position-keyframed to track the subject, as a reusable FFmpeg overlay in the edit engine's attention-guide kit. Touches `scripts/rexcaped_edit_engine.py` + `playbook/editing.json` attention-guides. (QfbGKfkGP8U)
- **SAM 2 between-layer creature placement** — local SAM 2 (open weights, M5, $0) splits real background plates into fg/mid/bg layers so composited creatures sit BETWEEN layers (partial occlusion by foreground objects). Prototype on ONE existing Spino/Lagos composite before adopting. Extends the rembg+PIL layered-composite engine — not a new system. (Dmqz8opSHzE)
- Shorts derivative pipeline — see cross-channel build; Rexcaped supplies the first test assets.

### DO NOT DO
- Chain the whole edit into one continuous look — clip-variety rule (distinct vantage per beat) takes precedence; chaining is within-beat only (sMo5RT_dPxc, 32DLRsFiXZY).
- Enter adjacent template niches (BeamNG crash Shorts, renovation, Roblox) — saturated, watermark-encumbered, July-2025 inauthentic-content targets (32DLRsFiXZY, 6WDvO0Lu1sY, sMo5RT_dPxc).
- Replace Grok/VACE with paid gen stacks (Higgsfield, kie.ai, Kling subscription, Flow paid) — no-new-paid-APIs rule; $0 local path already wins (LGYiPA5SKvw, TiycelzfzC0, Dmqz8opSHzE, r81ImbWaxEE).

---

## 2. PREHISTORIC POV (@Prehistoric_POV; 1 published video, 8:07)

### DO NOW
| Action | What changes | Touches | Sources | Payoff |
|---|---|---|---|---|
| SEO/settings audit vs new checklist | Confirm channel description carries searchable niche keywords (dinosaur POV, first person, survival); add Studio channel keywords if absent; enable auto-dub; AI-disclosure = **YES** on all uploads | channel settings; upload checklist | 4xWQ_fHLGAc, eF75ZffgsUk | Closes gaps the 2026-06-30 branding pass may have missed; POV content dubs cheaply to a global audience |
| Cut 3 verticals from the published video | FFmpeg 9:16 crops of the 3 best first-person moments, hook inside 1s — cheapest possible reach test before producing new long-form | `scripts/ffmpeg_production_render.py` crop pass (manual one-off; full pipeline is the cross-channel build) | 8N7-vQ9qX4w | Shorts surface on homepage/search/Google; his short out-reached long-form ~15x |
| "POV: you're the [role] when [stakes]" title formula | Adopt for uploads (e.g. "POV: You're the first human a raptor pack has ever hunted") | `playbook/titles_thumbnails.json` candidate patterns | tICnK3Qb2k8, Ao_d-uaMJvk | Proven packaging shape on the insider-POV channels shown |
| Explicit test budget + kill criterion | Decide the channel's verdict at 8–10 uploads; diagnose by type: no impressions = distribution, impressions/no clicks = packaging (thumbnail recipe), clicks/no retention = edit | channel plan / `memory` project file | 8KXlxAKOTdE | Keep/kill becomes a data decision, not vibes |
| Stills-driven pacing rules for planning | TEST: 2.5s max hold on static stills (i2v clips exempt) + ~150+ distinct visuals per 8-min video — audit the published 8:07 against these numbers first; promote to standing rule only if the audit supports it | FFmpeg still-hold parameter; extends `research/edit_grammar_ruleset.md` to stills-driven video; `playbook/editing.json` | Ao_d-uaMJvk | Directly targets the stills-format failure mode ("flopping" = overlong holds) |
| Still-series method amendments | Chain: attach the previous downloaded frame as explicit image reference for each next still; ALSO attach one fixed style-reference image to every generation (not just thread memory) | `reference_chatgpt_pov_still_series_method` | 6WDvO0Lu1sY, TiycelzfzC0 | Locks environment/lighting/look continuity across the series |
| 30-day cadence commitment | Generate a ranked backlog + posting calendar (cross-channel batch-scorer session) and defer viability judgment until the window closes | `pipeline_v2/topic_scorer.py` session output; NEXT_VIDEO-style handoff | 54UTQ2kFhuA, LGYiPA5SKvw | The channel's actual gap is cadence, not craft |

### NEXT VIDEO (next POV episode)
- Score **"Why You Wouldn't Last 24 Hours in the Cretaceous"** (format shown winning twice across niches) and/or the **"your life at every level of X" escalation format** with a "POV:" title prefix through the 9-test scorer; produce with the existing ChatGPT-stills → Grok i2v → FFmpeg chain (8KXlxAKOTdE, Ao_d-uaMJvk).
- TEST the 2.5s hold ceiling + scene-density budget in the FFmpeg assembly for this episode; keep the retention curve vs the published 8:07 as the promote/revert criterion (Ao_d-uaMJvk).

### EXPERIMENTS
| Experiment | One-sample proof | Success metric | Sources |
|---|---|---|---|
| Repackage video 1 if impressions ≈ 0 | ONE retitle/rethumbnail mirroring a proven dino/creature-channel winner's shape | Impressions move within 2 weeks (separates trust-throttling from too-original packaging) | q0G-FzS6uxk |
| Last-frame chaining for POV sequences | ONE 3-scene chase (walk → turn → encounter): scenes 2–3 generated from FFmpeg-extracted last frames vs current fresh-still method | Frame-strip QA shows scene-boundary jumps eliminated | 32DLRsFiXZY, sMo5RT_dPxc |
| Locked character-block injection | ONE episode's still series with a verbatim creature-anatomy + POV-camera block pasted into every prompt | Less character drift than the single-thread-context episode | NA0AOlCmelQ |
| Google AI Studio TTS as $0 licensed VO fallback | ONE existing script narrated in AI Studio, A/B vs the ElevenLabs take | Quality holds → adopt as fallback where voice identity doesn't matter (F5-TTS is CC-BY-NC-blocked) | lL9gjPw5yjg |
| Flow/Nano Banana bulk stills benchmark | ONE scene's still series (16:9, 4/request) vs the ChatGPT one-download-per-tab method; verify credit caps + watermark first | Beats ChatGPT on throughput with no quality drop and no watermark | zJmYdcvwY1Y, lDpOnE3VJVI |
| First-person twist-story vertical | ONE 20–40s short: cold-open mid-danger, 2 beats, twist line last; two-tone karaoke captions via FFmpeg/ASS (not CapCut) | Shorts gates: stayed-to-watch ≥75-80%, AVD ≥100% | KxsasFMMPpA, PtO7jd8L2xs |
| AVD-hack Short | ONE 6–8s POV loop (e.g. the sh15 "3 seconds before the Dunkleosteus strikes" beat) + a caption block taking 20–25s to read | STW ≥80%, AVD ≥100% in Studio | PtO7jd8L2xs |
| FB cross-post | Include POV verticals in the Rexcaped FB test; add one save/share "held frame" beat per short | FB reach > negligible after 30 days | E_CIP98ufto, KZKFlik4M8I |

### DO NOT DO
- Publish anything carrying a Flow/Veo watermark, or crop/cover it — SynthID persists; concealment is pure policy risk (NlfmQpSaYMo, lDpOnE3VJVI).
- Per-scene t2v pipeline swap (Flow/Omni Flash) — paid model misrepresented as free; contradicts the stills → Grok i2v technique (NlfmQpSaYMo, h6DB0e96GI0).
- Kids-adjacent niches (nursery rhymes, Roblox cartoons) — Made-for-Kids RPM collapse + prime inauthentic-content target (lDpOnE3VJVI, sMo5RT_dPxc).

---

## 3. BIZDOC (pre-launch; "Why Breaking the Law Is Profitable" rendered, near upload)

### DO NOW — the pre-upload launch checklist (one session, all free)
| Action | What changes | Touches | Sources | Payoff |
|---|---|---|---|---|
| Feature-eligibility verification | Studio > Settings > Channel > Feature eligibility: phone/advanced verification. **Blocking item: the 23.4-min video needs the >15-min upload unlock; custom thumbnails need intermediate** | channel settings | eF75ZffgsUk, q0G-FzS6uxk | Removes a literal upload-day blocker |
| Cold-start keyword seeding | Keyword-rich channel description from ~5 high-volume niche terms (corporate crime, business documentary, HMW-adjacent); same set into Studio channel keywords; country=US; branding watermark; set video language=English at upload | channel settings; upload checklist | 4xWQ_fHLGAc, 3MPSrpIOpAo | The one window where cold-start seeding can matter is pre-launch |
| Account warm-up | Weeks of real watch/like/comment activity on the account before first upload; never upload from a cold account | launch practice | q0G-FzS6uxk | Free hedge against new-account throttling |
| Name diligence | Run the channel name through YouTube search + WIPO Global Brand Database; skip building a channel trailer | launch checklist | LGYiPA5SKvw | Avoids a trademark collision after brand equity exists |
| AI-disclosure stance documented | Decide and write down the altered/synthetic answer for the cloned-voice VO before first upload | upload checklist | eF75ZffgsUk | The #1 platform risk demands a documented, consistent stance |
| Supply check on the core framing | Search "fines are the cost of doing business / law prices crime" framings; if 3+ near-identical videos exist, sharpen the RealPage-$0 / GDPR-pricing differentiator visibly in title + thumbnail | `pipeline_v2/topic_scorer.py` evidence; `playbook/titles_thumbnails.json` | 8KXlxAKOTdE | Differentiation visible pre-click |
| Research-tab interest check + title-only A/B | Run candidate title keywords through Studio Research/Trends; set up a title-ONLY Test & Compare at upload (never combined title+thumbnail) | upload flow; add the single-variable protocol to `playbook/titles_thumbnails.json` | 8N7-vQ9qX4w | Free interest signal + clean test variables |
| Human-editorial appeal packet | Archive script version history (v45 lineage), sourcing docs, and `verify_render.py` QA reports per video as a YPP appeal packet | archive practice alongside `scripts/verify_render.py` outputs | ipbnR92Elxg, q0G-FzS6uxk | Decline-then-appeal-then-monetized is a documented path; evidence of transformative human work wins it |
| Upload-hygiene rules | Unlisted-first → public after processing; 72h no-evaluation; no Reddit/social seeding | upload checklist | 4xWQ_fHLGAc, q0G-FzS6uxk | Same rationale as Rexcaped |
| Title-pattern pool expansion | Add adversarial-curiosity patterns: "Why companies pay millions to [avoid X]", "What really happens when you [legal event]", "What your [boss/bank/landlord] hopes you'll never learn" | `playbook/titles_thumbnails.json` | tICnK3Qb2k8 | On-lane, high-CPM-validated formulas — near-duplicates of the channel's own first video |
| Metaphor-beats flagged for shorts | When shorts are cut from Breaking-the-Law, the shorts ARE the aphorisms ("fines are a line item", "the law prices crime"), each looping back to its opening line | shorts-cut selection notes; `playbook/scripting.json` | E_CIP98ufto | Save/share-designed beats travel; narrative excerpts don't |

### NEXT VIDEO (the upload itself + the next script)
- **Upload**: execute the checklist above; enable auto-dub only after the dub-quality experiment below (4xWQ_fHLGAc).
- **Next script** (v45 is locked — these apply from the next one):
  - Coffee-shop-rule QA pass pre-TTS: flag lecture-voice sentences you'd never say to a friend; count second-person "you" moments (target 1–2 per chapter) (Xf_J7kBzxvo). Touches `playbook/scripting.json`.
  - Counterfactual-deletion cold-open variant: "imagine waking up and X no longer existed" → concrete stakes → direct question (NlfmQpSaYMo). Touches `playbook/intros.json`.
  - Topic candidates through the 9-test scorer: "Why Companies Pay Millions to Avoid Trial" / "The Real Cost of Getting Sued" (sits on existing RealPage/Purdue/Meta research), the "what happens if you buy an airline/sports team" family (survivor-scan the showcased channel first), and history-of-X/counterfactual seeds (money, credit scores, receipts) (tICnK3Qb2k8, zJmYdcvwY1Y, NlfmQpSaYMo).
  - ONE demand-gap clustering session as candidate generator: yt-dlp titles+transcripts of ~10 recent ColdFusion/HMW/Johnny Harris videos → Claude demand map (crowded vs fresh clusters, off-YouTube demand evidence) → survivors into the scorer (54UTQ2kFhuA). Touches `playbook/ideation.json` + `playbook/sources.json`.
  - Niche-gap thresholds logged as scorer notes: niche <60 days old, <10 competing channels, or creators at 300–500K views/video posting <1x/week (PtO7jd8L2xs). Touches `pipeline_v2/topic_scorer.py` timeliness/blind_spot notes.

### EXPERIMENTS
| Experiment | One-sample proof | Success metric | Sources |
|---|---|---|---|
| Auto-dub quality on the cloned voice | Enable auto-dub, LISTEN to one dubbed track before leaving it live | Documentary tone survives machine dubbing (reversible per-video) | 4xWQ_fHLGAc |
| Thumbnail style transfer | 3 proven ColdFusion/HMW thumbnails as GPT image-gen style references + our hook text (objects/logos/text only — NO AI faces) vs the hand-built draft | Side-by-side feed-size readability + owner pick | 3MPSrpIOpAo |
| Real-executive-face thumbnail A/B | ONE thumbnail: recognizable real executive's photo (real photo per hard rule) as the single focal point vs concept-led draft | CTR in a thumbnail-only Test & Compare once impressions justify it | tICnK3Qb2k8 |
| SAM 2 parallax Ken Burns | THREE existing breaking_law stills segmented into 2–3 depth layers locally, differential-speed parallax added to the Ken Burns path | Visibly better than flat Ken Burns; renders clean through `verify_render.py` | Dmqz8opSHzE |
| Vox style-block riders on abstract beats | TWO abstract beats of the next video (fine-as-line-item formula, data-flow) with "cutout collage"/"kinetic typography" style blocks appended to still prompts; beat lengths stay at measured 5–7s grammar | Beats read cleaner than generic stills; style gate passes | Dmqz8opSHzE, TiycelzfzC0 |
| Dry-wit edit beat | ONE comedic edit beat (visual gag/ironic cut) in the next video | That segment's retention curve doesn't dip vs neighbors | Xf_J7kBzxvo |
| Google Trends scorer input | ONE lookup per candidate topic (trend direction + spike recency) feeding the timeliness test | Adopt if it changes ≥1 scoring decision in the first batch | tICnK3Qb2k8 |
| Save-the-cat beat in minute one | ONE likability/credibility beat inside the first minute without breaking the 0-15s hook rules | First-minute retention vs previous video | Xf_J7kBzxvo |

### DO NOT DO
- Auto-generated news/story scripts — the channel's moat is verified public-data sourcing; the genre's pipelines have no fact-check step (TiycelzfzC0, 8Mx2m0djgTA).
- Any reused-clip model ("text overlay = transformative") — contradicts fair-use armor (≤7s/clip, ≤30s/source, muted audio) and is the July-2025 policy's explicit target (QfbGKfkGP8U, PtO7jd8L2xs).
- Watch-time padding / "make it 1.5x longer" as a rule — length stays story-driven; padding fights the retention grammar (ipbnR92Elxg, 8KXlxAKOTdE, 3MPSrpIOpAo).
- Competitor-transcript rewriting as a script method — below the 95+ original-script bar; reused-content risk (zJmYdcvwY1Y).

---

## 4. CROSS-CHANNEL

### DO NOW
| Action | What changes | Touches | Sources | Payoff |
|---|---|---|---|---|
| Codify the policy read | Write into the risk notes: "mass-produced" SAMENESS is the documented YPP rejection trigger, NOT AI voice; Gemini whole-video-context detection claim logged as unverified-but-directional. This converts the clip-variety rule + per-video style variation from editing preference into the named YPP defense | `research/edit_grammar_ruleset.md` preamble + memory risk notes | 4xWQ_fHLGAc, q0G-FzS6uxk, LGYiPA5SKvw, tICnK3Qb2k8 | The single most consistent policy signal across all 32 videos |
| Standing never-do rules | Add four one-liners to upload practice: (1) never distribute identical videos across multiple accounts; (2) never hide/crop a provider watermark — disclosed-and-watermarked or unused (add watermark check to frame-level QA); (3) always set the altered/synthetic disclosure honestly; (4) inter-video edit-fingerprint variation is mandatory | upload checklist; frame-level QA pass (`feedback_frame_level_qa`) | KxsasFMMPpA, lDpOnE3VJVI, NlfmQpSaYMo, E_CIP98ufto, eF75ZffgsUk, 0SPqPnpQsWE | Each maps directly onto documented enforcement behavior |
| Monetization-survivor scan as niche pre-check | Before committing to any new format: check 3–5 comparable channels for hit-videos-then-sudden-stop (likely YPP denial). Run retroactively on the Rexcaped comp set | `pipeline_v2/topic_scorer.py` workflow (pre-check next to source_availability) | zJmYdcvwY1Y | Free field signal aimed at the #1 platform risk |
| FTC affiliate boilerplate | "This description contains affiliate links…" added to every channel's description template | description templates in upload packages | LGYiPA5SKvw | Compliance before the first affiliate link ships |
| Single-variable A/B protocol | Written rule: title-only OR thumbnail-only Test & Compare, never combined; 2 variants for a clean winner | `playbook/titles_thumbnails.json` | 8N7-vQ9qX4w | Unconfounded tests when impressions justify them |
| Lock narrator persona per channel | Same ElevenLabs voice + same scripting voice permanently per channel; treat as a ship-gate item alongside creature-consistency QA | consistency-guarantee/approval-ledger ship gate | Xf_J7kBzxvo | PSR + soft inauthentic-content hedge; already learned via the Dinoverse voice-drift fix |
| Direct-address lint + comment referencing | Script-QA count of direct-viewer-address beats (target ~10/video); once comments exist, quote one real comment in each follow-up video | `playbook/scripting.json`, `playbook/retention_delivery.json` | Xf_J7kBzxvo | Cheapest reciprocity/intimacy signals; countable, lintable |
| Negative-intel log | ideation.json notes: "monetized in days" claims = aged-channel purchase (discard); saturated template-AI niche families (cardboard DIY, wire/twig, mini-cooking ASMR, BeamNG, renovation, Roblox) auto-fail without re-analysis | `playbook/ideation.json` | 0SPqPnpQsWE, h6DB0e96GI0, lL9gjPw5yjg, 32DLRsFiXZY, 6WDvO0Lu1sY, sMo5RT_dPxc | Stops re-litigating known-bad niches |
| Future-monetization checklist line | At YPP + memberships: set tier prices manually in Studio → Earn → Memberships before smart-pricing defaults auto-apply (once-per-12-months lock noted) | monetization checklist (dormant) | CQWfqKGFoPM | One line now, avoids a forced default later |

### CAPABILITY BUILDS (Claude Code on the existing FFmpeg pipeline; prototype-first per hard rule #2)
1. **Shorts/vertical derivative pipeline** — the highest-leverage build. After each long-form render: crop 2–3 of the highest-scoring motion-event beats (selected via `scripts/extract_motion_events.py`) to 9:16; render the vertical caption grammar (yellow-setup / white-body / red-shock-word hierarchy, typewriter reveals, subject-tracked) via FFmpeg/ASS; 3-SFX palette (whoosh/hit/ding) from the existing library; support the AVD-hack format (6–8s owned loop + 20–25s read-time caption). **Ship-gates: stayed-to-watch ≥75–80%, AVD ≥100%** — recorded as the Shorts lane's gate numbers. Rotate caption template styling every ~10 uploads. Prototype = ONE Rexcaped short + ONE PPOV short measured against the gates before building the general tool. Touches: new module beside `scripts/rexcaped_edit_engine.py`; Shorts annex to `research/edit_grammar_ruleset.md`. (8N7-vQ9qX4w, PtO7jd8L2xs, QfbGKfkGP8U, KxsasFMMPpA, E_CIP98ufto, 6WDvO0Lu1sY)
2. **Weekly channel-audit scheduled task** — Claude Code scheduled task (Mondays) pulls each channel's Studio analytics via existing browser automation and outputs an executive diagnosis + 5-priority action plan. Clones the VidIQ pattern at $0, no subscription. Prototype = one manual run producing the report format the owner actually reads. (8N7-vQ9qX4w)
3. **Local SAM 2 segmentation layer** — one local install serves two channels: multi-layer parallax Ken Burns for bizdoc (`scripts/ffmpeg_production_render.py` Ken Burns path) and between-layer creature placement for Rexcaped (rembg+PIL composite step). Prototype = 3 bizdoc stills + 1 Rexcaped composite (already listed as channel experiments — build only if both pass). (Dmqz8opSHzE)
4. **Batch ranked-backlog scorer session** — one Claude session per channel: mine named competitors for outliers-relative-to-subs, run ~30 ideas through the 9-test scorer, emit a ranked backlog with posting packages (title/desc/tags/thumbnail brief) so upload day is assembly-only. Touches `pipeline_v2/topic_scorer.py` workflow + NEXT_VIDEO.md handoff pattern. Fixes the cadence gap on PPOV first. (LGYiPA5SKvw, 54UTQ2kFhuA)
5. *(Marginal)* Package each channel's render pipeline as a project-local slash-command skill (`/rexcaped-render`) with per-clip regeneration — convenience only; infra exists. (TiycelzfzC0)

### DO NOT DO (consolidated — every one violates a hard rule or documented enforcement)
| Rejected tactic | Why | Sources |
|---|---|---|
| Buy aged/premonetized channels; "trust score" bypass | YouTube ToS violation (non-transferable accounts), termination risk; the hidden engine behind every "monetized in days" claim | 0SPqPnpQsWE, 54UTQ2kFhuA, 8KXlxAKOTdE, PtO7jd8L2xs |
| Multi-accounting / credit farming (temp-mail, fresh-browser Flow refills, Wan Gmail cycling, DuoPlus cloud-phone farms, bought TikTok accounts) | Platform ToS abuse; account-network behavior = inauthentic-content criteria; $0 local gen makes it pointless | 32DLRsFiXZY, 3MPSrpIOpAo, NA0AOlCmelQ, KxsasFMMPpA |
| Loop-stream 24/7 "live" watch-hour farm | Textbook July-2025 inauthentic-content trap + misleading metadata. Only compliant variant: ONE honestly-labeled marathon premiere IF watch hours ever stall | eF75ZffgsUk |
| Watermark hiding (scale/shift/cover) | SynthID survives; concealment only demonstrates intent at manual review | NlfmQpSaYMo, lDpOnE3VJVI |
| Reused-content models (OBS-ripping streamers, TikTok clip reuse, "text overlay = transformative", competitor-transcript rewrites, delete-and-repost to fresh channels) | Copyright exposure + the policy's explicit target; contradicts fair-use armor and the 95+ original-script bar | PtO7jd8L2xs, QfbGKfkGP8U, zJmYdcvwY1Y, 8KXlxAKOTdE |
| AI human faces in any form (HeyGen avatars/clones, public-figure black-bar filter evasion) | Owner's hard no-AI-faces rule + synthetic-depiction disclosure risk | ipbnR92Elxg, PtO7jd8L2xs, TiycelzfzC0 |
| Competitor voice cloning ("no monetization issue") | False and dangerous — impersonation/inauthentic-content policy | 3MPSrpIOpAo |
| New paid subscriptions/tools without asking (Abacus AI, VidIQ paid/MCP, NexLev, Higgsfield, kie.ai+Seedance, Noodle Tomato, Narration AI, TubeBuddy Next Ideas, ChannelRecipe, gray-market ElevenLabs resellers, Opus AI Producer, Edimakor) | No-new-paid-APIs hard rule; every capability exists in-house or replicates free; most are affiliate bait; black-box editors can't pass the style gate / motion-event ship-gate | 4xWQ_fHLGAc, 8N7-vQ9qX4w, 8KXlxAKOTdE, LGYiPA5SKvw, TiycelzfzC0, Dmqz8opSHzE, 8Mx2m0djgTA, Ao_d-uaMJvk, CQWfqKGFoPM, 54UTQ2kFhuA, 3MPSrpIOpAo, Xf_J7kBzxvo, sMo5RT_dPxc, ipbnR92Elxg |
| Community-distributed Claude Code plugins whose connectors spend API credits | Supply-chain risk; all capabilities exist in-house | Dmqz8opSHzE |
| Reddit/social seeding of uploads | Low-intent clicks tank retention now and home-feed CTR later | q0G-FzS6uxk |
| Leaving the AI label off / "any random looping visuals are fine" | Disclosure violation; the exact repetitive profile the policy targets | E_CIP98ufto, 3MPSrpIOpAo |
| "Thumbnails don't matter" / no-script production / 5-15s visual density / guru "3-second rule" | Contradict the 26-tactic packaging module, the 95+ script bar, and the MEASURED 5-7s grammar — trust measurement over round numbers | 8N7-vQ9qX4w, 0SPqPnpQsWE, Dmqz8opSHzE, LGYiPA5SKvw |
| Volume-play cadence (3-15/day templated output) | Matches the inauthentic-content profile on every platform (TikTok's ~300/30-day ban confirms cross-platform); quality gates stay | E_CIP98ufto, r81ImbWaxEE, KZKFlik4M8I |

---

*Prototype-before-plan applies throughout: no EXPERIMENT graduates to standing practice without its named one-sample proof; no CAPABILITY BUILD starts before its prototype passes on real on-disk assets.*
