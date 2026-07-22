# UNIFIED TACTIC MAP — 54-Video Masterclass Synthesis (v2, regenerated from scratch)

Merged, deduplicated tactics from all 54 analyzed videos (see `analysis/COMBINED_INDEX.md`; per-video
detail in `analysis/<id>.json`/`.md`). Supersedes the 32-video map entirely — the corpus grew by 22
videos (notably the Claude Code editing / Remotion / Hyperframes / Higgsfield-MCP cluster, the
Hormozi two-channel funnel, the vidIQ "New Rules" video, the Pay-to-Win experiment, and the WOLF
Money $1K/day case study), and every merge below was rebuilt over the full corpus.

Relations map to the operation's existing systems BY NAME: playbook modules
(`playbook/editing.json`, `intros.json`, `scripting.json`, `titles_thumbnails.json` (26 tactics),
`retention_delivery.json`, `ideation.json`, `sources.json`), the measured
`research/edit_grammar_ruleset.md` + `research/viral_recreation_spec.md` (10 measured laws),
`pipeline_v2/topic_scorer.py` (9 tests, GO=85+ all ≥65), the FFmpeg engine
(`scripts/ffmpeg_production_render.py`) + watcher (`scripts/verify_render.py`), WhisperX alignment +
`scripts/realign_paper_edit.py`, the layered-composite engine (rembg+PIL), the
consistency-guarantee/provenance system, `style_bands.json` + `gate_style.py`,
`scripts/extract_motion_events.py` ship-gate, the frame-level-QA / i2v-real-physics /
talking-creature-QA / clip-variety rules, the thumbnail recipe (candid phone-photo, ONE focal point,
gen from scratch), and the AMBER pipeline (`tools/amber/stage_b_vace.py`, event sheets, TSV riders).

**Evidence-strength scale:** STRONG = 3+ independent videos and/or on-screen analytics/mechanics
demonstrated; MEDIUM = 2 videos, or 1 video with concrete demonstrated proof; WEAK = 1 video,
asserted only. Standing caveat for the whole corpus: most sources are affiliate/coaching funnels —
workflows were usually shown on screen, revenue almost never was. Numbers that are self-reported,
description-sourced, or tool-estimated are labeled as such. ADOPT is only used where the evidence
plus cost profile justify acting without a trial; anything resting on one unproven source is TEST.

---

## 1. PACKAGING — TITLES / THUMBNAILS

### 1.1 Packaging-first production gate (render before you produce)
- **Mechanics:** Conceive — and physically render — title + thumbnail before any production; if the best version is vague or you wouldn't click it yourself, kill the topic (q0G-FzS6uxk). "We always need to do the thumbnails first" as a standing rule (ipbnR92Elxg). Extreme form: generate the thumbnail hook TEXT first, then write the script from it, one LLM thread carrying idea→script→title→tags→description (3MPSrpIOpAo). Score multiple titles/concepts before scripting (8Mx2m0djgTA).
- **Sources:** (ipbnR92Elxg) (q0G-FzS6uxk) (3MPSrpIOpAo) (8Mx2m0djgTA)
- **Evidence:** STRONG — 4 independent videos, live demos in 3; no CTR/retention data, but mechanically free.
- **Relation:** CONFIRMS `topic_scorer.py` title_thumbnail + five_second_title tests. NEW wrinkle: render the actual artifact pre-production (scorer currently grades the concept, not the rendered thumbnail).
- **Disposition:** ADOPT the render-first ordering on Rexcaped video 3+ and bizdoc video 2; kill topics whose thumbnail doesn't read at feed size.

### 1.2 Holy-trifecta congruence (title + thumbnail + intro generated together)
- **Mechanics:** Generate title, thumbnail concept, and intro in ONE pass; congruence beats individual quality ("all 7-8/10 pointing the same direction"); the intro's first seconds must visually look like the thumbnail or viewers click off (YtpQSmu794k — self-demonstrated: thumbnail = Studio $333K screen, title = $333K, intro opens on that same screen). Hook must pay off the thumbnail or retention collapses (q0G-FzS6uxk).
- **Sources:** (YtpQSmu794k) (q0G-FzS6uxk)
- **Evidence:** MEDIUM — 2 sources; the $333,080 AdSense figure was shown live in Studio with a currency sanity-check (rare in this corpus) but comes from a mature 1.5M-sub channel, not a faceless build.
- **Relation:** NEW as a pre-upload gate spanning `intros.json` + `titles_thumbnails.json` — neither module currently checks thumbnail↔first-frame congruence.
- **Disposition:** ADOPT as a checklist line in the upload package: first visible frame must echo the thumbnail composition.

### 1.3 Reference-conditioned thumbnail generation (competitor style transfer)
- **Mechanics:** Screenshot a proven competitor thumbnail → paste into ChatGPT/image gen with your own hook text → new on-template thumbnail in the donor's composition; iterate by resubmitting the result (3MPSrpIOpAo, live demo). Reference-image-guided AI thumbnail preferred over a $60 commissioned design (ROPkHP8jpW0, both shown). Meta-prompt from outlier screenshots "target clickbait and CTR" (ipbnR92Elxg). Packaging must be modeled on what already worked in the niche (8KXlxAKOTdE). Tooling hierarchy: ChatGPT best, Nano Banana second, Claude for concept/text/layout only; Pikzels/1of10 are paid (YtpQSmu794k).
- **Sources:** (3MPSrpIOpAo) (ROPkHP8jpW0) (ipbnR92Elxg) (8KXlxAKOTdE) (YtpQSmu794k)
- **Evidence:** STRONG on mechanics (3 live demos); zero CTR proof anywhere.
- **Relation:** NEW general mechanic alongside the creature-specific thumbnail recipe (candid phone-photo, ONE focal point, gen from scratch — which stays canonical for Rexcaped/Dinoverse). Guard: no AI human faces.
- **Disposition:** TEST on bizdoc: 3 ColdFusion/HMW-referenced generations vs the hand-built draft for "Breaking the Law".

### 1.4 Realism-degrade knobs on AI packaging
- **Mechanics:** Prompt line "lower the quality of the image so it looks more realistic"; keep text OUT of the generation and add it in post (ipbnR92Elxg, live iteration). "Less saturation and contrast" as a repeatable instruction to kill the AI-plastic look; B&W/nostalgic filters to hide it entirely (Z5Wn63kLhpI, shown improving a generated photo).
- **Sources:** (ipbnR92Elxg) (Z5Wn63kLhpI)
- **Evidence:** MEDIUM — both demonstrated on screen.
- **Relation:** CONFIRMS the thumbnail recipe's candid-phone-photo look; the two prompt lines are new concrete knobs for it.
- **Disposition:** ADOPT the two prompt lines into the thumbnail-recipe prompt block (free, additive).

### 1.5 Machine-legible packaging (write for the classifier, not just CTR)
- **Mechanics:** Write title/description so "an AI algorithm can understand who it's for" — front-load plain-keyword audience/subject signals in the first description lines (9iP588aMFBc, no prompt shown). Packaging must be recognizably ADJACENT to channels your audience already watches so YouTube knows who to push it to; "too original" packaging fails classification — put originality inside the video body (q0G-FzS6uxk, community-guidelines quote for half the claim). Description generated from title + 5 keywords + full script (4xWQ_fHLGAc, shown).
- **Sources:** (9iP588aMFBc) (q0G-FzS6uxk) (4xWQ_fHLGAc)
- **Evidence:** MEDIUM — 3 sources, mechanism-level reasoning consistent with the test-impression model (9iP588aMFBc), no A/B data.
- **Relation:** NEW to `titles_thumbnails.json` — all 26 tactics are human-CTR-focused; none target machine legibility.
- **Disposition:** ADOPT as a description-writing rule (first 2 lines = plain audience+subject keywords); costs nothing.

### 1.6 Buyer-intent titling
- **Mechanics:** Title for problem-solvers, not fact-browsers: "Why 90% of people stay broke and how to join the 10%" beats "10 amazing facts about money" at equal views because it attracts high-intent viewers and trains the algorithm toward qualified traffic (TvJhpOxFRsE, hypothetical example only).
- **Sources:** (TvJhpOxFRsE)
- **Evidence:** WEAK — asserted, no test data.
- **Relation:** CONFIRMS `titles_thumbnails.json` intent framing; NEW nuance for bizdoc: privacy-anxious viewers convert better on the Incogni/NordVPN mid-rolls.
- **Disposition:** CONFIRM; keep in mind when titling bizdoc sponsor-adjacent chapters.

### 1.7 Niche title formulas (portable patterns)
- **Mechanics:** "POV: you're the [role] when [stakes]" insider framing (tICnK3Qb2k8; Ao_d-uaMJvk's "POV:" prefix + "your life at every level of X" escalation). Adversarial-curiosity legal titles: "Why companies pay millions to avoid trial", "What your boss hopes you'll never learn" (tICnK3Qb2k8). "The REAL reason [common behavior]" + emotion word, myth-busting frame (LGYiPA5SKvw, extracted by live competitor analysis). Recognizable real faces in packaging boost CTR (tICnK3Qb2k8, asserted).
- **Sources:** (tICnK3Qb2k8) (Ao_d-uaMJvk) (LGYiPA5SKvw)
- **Evidence:** MEDIUM — patterns visible on real high-view videos shown on screen; no controlled data.
- **Relation:** CONFIRMS `titles_thumbnails.json` formula bank + Prehistoric POV packaging; celebrity-faces nuance is NEW and compatible with the real-photos-only hard rule (bizdoc only).
- **Disposition:** ADOPT into the title-formula bank as candidates for scoring; nothing structural changes.

### 1.8 Single-variable A/B protocol
- **Mechanics:** In Studio Test & Compare: run title-only tests (measures impressions/keyword effect) or thumbnail-only tests (measures CTR) — NEVER combined title+thumbnail tests (confounded); sometimes 2 variants beats 3 for a clean winner (8N7-vQ9qX4w, feature walkthrough shown).
- **Sources:** (8N7-vQ9qX4w)
- **Evidence:** WEAK-MEDIUM — one source, but the protocol is standard experimental hygiene on a real Studio feature.
- **Relation:** NEW written testing-protocol rule for `titles_thumbnails.json`.
- **Disposition:** ADOPT as a written rule, dormant until any channel has enough impressions to power a test.

### 1.9 Template rotation / inter-video packaging variation (demonetization hygiene)
- **Mechanics:** Change the caption/design template (colors, shape, background) roughly every 10 videos so uploads don't read as identical (PtO7jd8L2xs, template shown; he rotates specifically because identical templates "could get demonetized"). A template-farm practitioner independently warns "try not to work on the same template" while admitting community-guideline trouble (0SPqPnpQsWE). YPP rejection reported with the literal term "mass-produced" for stylistically identical videos — with a HUMAN voice; fix that worked: delete lookalikes, change style, reapply (4xWQ_fHLGAc, secondhand anecdote). Vary effects between videos to avoid sameness (E_CIP98ufto).
- **Sources:** (PtO7jd8L2xs) (0SPqPnpQsWE) (4xWQ_fHLGAc) (E_CIP98ufto)
- **Evidence:** STRONG — 4 independent operators, two of them speaking from enforcement contact; all self-reported.
- **Relation:** NEW — extends the intra-video clip-variety rule (`feedback_clip_variety_rule`) to INTER-video variation; touches `titles_thumbnails.json` and the edit-grammar template layer.
- **Disposition:** ADOPT: schedule a deliberate style-band refresh every ~8-10 uploads per channel (colors/caption styling/card design), logged in the provenance system.

---

## 2. HOOKS & RETENTION

### 2.1 Hook shapes bank (0-15s)
- **Mechanics:** Counterfactual-deletion open: "imagine waking up tomorrow and X no longer existed" → concrete stakes → direct question (NlfmQpSaYMo, sample script shown). "What if X…" hypothetical premise (lL9gjPw5yjg — same family as Rexcaped's "what if you faced X"). Big-number social proof stack in first 10s (lDpOnE3VJVI). Stakes summary → enumerated reveals → open mystery question (8Mx2m0djgTA, generated demo played). News/policy deadline hook: hard date + forced default + binary decision + promise of exact guidance (CQWfqKGFoPM — the video's own clean structure). First-person mid-action cold open with a moral twist closer (KxsasFMMPpA). Instant promise, no warm-up, then re-hook every 20-40s with a new twist/rule/stake (oWkUwno6b0E, MrBeast-structure demo script).
- **Sources:** (NlfmQpSaYMo) (lL9gjPw5yjg) (lDpOnE3VJVI) (8Mx2m0djgTA) (CQWfqKGFoPM) (KxsasFMMPpA) (oWkUwno6b0E)
- **Evidence:** STRONG on convergence (7 sources), though each shape individually is genre-standard; no retention curves shown anywhere.
- **Relation:** CONFIRMS `intros.json` 0-15s micro-window (killer stat, stakes-first). The 20-40s re-hook cadence is a NEW number for `retention_delivery.json`.
- **Disposition:** CONFIRM; ADD the 20-40s re-hook interval as an explicit script-QA check for bizdoc chapters.

### 2.2 Parasocial mechanics toolkit (faceless-compatible)
- **Mechanics:** Coffee-shop rule: flag any narration line you'd never say to a friend as lecture-voice (Xf_J7kBzxvo — MrBeast old-vs-new VO played as the one demonstrated proof). ~10 direct-address "connection moments" per video, countable/lintable (Xf_J7kBzxvo, stated interpretation of unnamed studies). Simulated-reciprocity templates: "So, you're probably thinking…", "After watching this you probably feel…" + referencing real viewer comments in later videos (Xf_J7kBzxvo). Persona/tone consistency across every video (Xf_J7kBzxvo). Save-the-cat likability beat in minute one (Xf_J7kBzxvo, analogy only). Task attraction (competence + information density) suffices for educational channels — no face needed (Xf_J7kBzxvo, unlabeled chart).
- **Sources:** (Xf_J7kBzxvo)
- **Evidence:** WEAK-MEDIUM — single source; the parasocial literature is real but the specific numbers ("~10 moments") are uncited.
- **Relation:** NEW mechanical lenses for `scripting.json` (coffee-shop pass, second-person-address density lint); persona-consistency CONFIRMS the locked-ElevenLabs-voice practice; task-attraction CONFIRMS the faceless bizdoc bet.
- **Disposition:** TEST: run the coffee-shop lint + a direct-address density count on the next bizdoc script; keep if it improves the read-aloud.

### 2.3 Curiosity-loop density scripting
- **Mechanics:** Every line opens a question answered later (4xWQ_fHLGAc, generated script shown); scripts built to "flow the exact same" as a proven reference transcript, optimized for AVD (ipbnR92Elxg, live meta-prompt demo — specify exact word count on the second pass because first drafts run short); every first second opens a loop like a movie trailer; transformation/before-after formats force watch-to-end (Z5Wn63kLhpI); hooks + open/close loops as template inputs (TvJhpOxFRsE).
- **Sources:** (4xWQ_fHLGAc) (ipbnR92Elxg) (Z5Wn63kLhpI) (TvJhpOxFRsE)
- **Evidence:** STRONG on convergence; all mechanism-level, no data.
- **Relation:** CONFIRMS `scripting.json` (curiosity loops) + `retention_delivery.json` (pauses before reveals).
- **Disposition:** CONFIRM — already the standard; keep the word-count-explicit regeneration trick for LLM script passes.

### 2.4 Pre-publish retention-drop prediction pass
- **Mechanics:** Drop the rough cut's timestamped transcript into Claude; ask where retention will most likely drop and how to fix each point (B-roll, on-screen text per section). Advanced variant frame-samples the video every ~3s so the model sees visuals + words (YtpQSmu794k, described as their standard step, no demo).
- **Sources:** (YtpQSmu794k)
- **Evidence:** WEAK — single source, described not shown.
- **Relation:** NEW — extends `verify_render.py` (currently technical QA only) with a creative-retention pass; all ingredients exist (WhisperX transcript, contact-sheet frames).
- **Disposition:** TEST once on the finished Breaking-the-Law render: one Claude pass over transcript + contact sheet; compare its flagged drop points against actual retention after upload.

### 2.5 End-screen handoff to ONE named deeper video
- **Mechanics:** End every broad video with a verbal pitch to a single named video that "goes way deeper" — end-reachers are the highest-intent segment (Eb8wlFawjTw: 130K-view broad video ending on a pitch to the deep-dive that allegedly drove $100K+, self-reported). Same shape as the "money video" funnel: end-screen every upload to one on-channel converter (TvJhpOxFRsE, asserted).
- **Sources:** (Eb8wlFawjTw) (TvJhpOxFRsE)
- **Evidence:** MEDIUM — 2 sources, revenue attribution unverifiable in both.
- **Relation:** CONFIRMS `retention_delivery.json` session-chaining intent; NEW refinement of Rexcaped's existing sh18_cta_next end card, which is currently generic.
- **Disposition:** ADOPT: make every end card name ONE specific next video instead of "watch more" (free change in the edit engine).

### 2.6 Jab-before-hook: no early asks
- **Mechanics:** Repeated early asks (subscribe, "my journey") make viewers duck; deliver value jabs with no strings before any CTA (ZKsldrcO_fU, metaphor only).
- **Sources:** (ZKsldrcO_fU)
- **Evidence:** WEAK — no data.
- **Relation:** CONFIRMS `intros.json` + `retention_delivery.json` (no early CTAs).
- **Disposition:** CONFIRM.

### 2.7 Static-hold ceilings for stills-driven video (conflicting numbers — shown as found)
- **Mechanics:** CONFLICT across sources: ≤2.5s per static image, i2v-animated scenes exempt; POV-channel "flopping" attributed to overlong holds; 150-200 distinct visuals per 5-20-min video (Ao_d-uaMJvk). 1 image per 3s (zJmYdcvwY1Y). One image per ~7-8s (f-ufEhGtVpw). One image per 5-15s "density range" (Dmqz8opSHzE — 15s violates our measured grammar). Scene switch every 3s instructed but the output ran 5-7s anyway (LGYiPA5SKvw — i2v models floor at ~5s, so faster pacing must come from cutting generated clips, not shorter generations).
- **Sources:** (Ao_d-uaMJvk) (zJmYdcvwY1Y) (f-ufEhGtVpw) (Dmqz8opSHzE) (LGYiPA5SKvw)
- **Evidence:** MEDIUM — 5 sources but mutually inconsistent (2.5s vs 3s vs 7-8s vs 5-15s); none show retention data.
- **Relation:** Extends `edit_grammar_ruleset.md` (measured for composited footage, not stills) and the FFmpeg renderer's still-hold parameter; the ≥5s i2v clip floor CONFIRMS existing trim practice.
- **Disposition:** TEST, don't adopt a number: measure actual still-hold durations in the top Prehistoric-POV competitor videos (same measurement method as the Rexcaped grammar) before setting a ceiling; until then Ken Burns motion on any hold >3s.

---

## 3. EDIT GRAMMAR & PACING

### 3.1 Recreate-the-winner beat-for-beat (reference-track editing)
- **Mechanics:** Import the exact viral video into the timeline as a reference track; rebuild shot order, effects, captions, SFX placement one beat at a time (QfbGKfkGP8U, full live rebuild). "Editor brain": transcribe 10 best-in-style references, have Claude deduce what is shown for each thing said and why, save as a reusable skill that plans scenes for any new script (PaXuebdY75U, applied to 6 scenes on screen). Learn hooks by writing down exactly why you kept watching bigger creators, then replicate the mechanic (q0G-FzS6uxk).
- **Sources:** (QfbGKfkGP8U) (PaXuebdY75U) (q0G-FzS6uxk)
- **Evidence:** STRONG — two full on-screen implementations.
- **Relation:** CONFIRMS the operation's core method (`viral_recreation_spec.md`, `edit_grammar_ruleset.md`, reference deep-watch); the skill-encapsulated "editor brain" is the same idea packaged as a Claude skill.
- **Disposition:** CONFIRM — this is the moat; nothing to change.

### 3.2 Cut-cadence numbers for long-form
- **Mechanics:** 4s/6s-only generated clips, 4-8 clips per 30-40s chapter (TiycelzfzC0, build prompt + demos cut every 4-6s). ~7-8s per visual segment (f-ufEhGtVpw). Holds must never exceed boredom onset — the 2.5s stills-ceiling family (see 2.7).
- **Sources:** (TiycelzfzC0) (f-ufEhGtVpw) (Ao_d-uaMJvk)
- **Evidence:** MEDIUM.
- **Relation:** CONFIRMS `playbook/editing.json` (cuts every 5-7s) and the measured Rexcaped grammar (0.07-0.13s montage bursts on lists, cut-on-numbers/turn-words).
- **Disposition:** CONFIRM — measured grammar stays authoritative over any guru number.

### 3.3 SFX economy: small reused palette, sound on every cut
- **Mechanics:** An entire viral Short runs on exactly 3 distinct SFX: whooshes on cuts/zooms (speed-matched to motion, mixed quiet), one flash hit, one end "ding" on the payoff (QfbGKfkGP8U, identified and rebuilt live). Whoosh bracketing at the start AND end of each graphic section + music bed (oWkUwno6b0E, shown in assembly). Keep i2v clip-native SFX at low volume under VO instead of muting (TiycelzfzC0, build-prompt rule — does NOT override bizdoc's `clip_audio:"mute"`, which exists for fair-use and VO integrity).
- **Sources:** (QfbGKfkGP8U) (oWkUwno6b0E) (TiycelzfzC0)
- **Evidence:** STRONG — all three demonstrated in real edits.
- **Relation:** CONFIRMS `edit_grammar_ruleset.md` "sound on every cut"; NEW nuance: small REUSED palette (3 sounds), not SFX variety, plus the low-volume clip-audio blend for creature channels.
- **Disposition:** ADOPT the 3-sound-palette discipline in `rexcaped_edit_engine.py` SFX selection; TEST low-volume clip audio on one Rexcaped beat.

### 3.4 Attention-guide overlay pack
- **Mechanics:** Vignette spotlight: full black layer → inverted circle mask, feather ~21, opacity ~70, position keyframed to track the subject (QfbGKfkGP8U, exact values shown). Punch-in zooms keyframed a few frames apart exactly on reaction/reveal moments (QfbGKfkGP8U). Matched-zoom transition: zoom-in keyframe at end of clip N = identical zoom level at start of clip N+1, plus per-clip motion blur (6WDvO0Lu1sY, keyframe workflow shown).
- **Sources:** (QfbGKfkGP8U) (6WDvO0Lu1sY)
- **Evidence:** MEDIUM-STRONG — all built on screen with values visible.
- **Relation:** `playbook/editing.json` names "attention guides"; these are NEW concrete implementable specs for the FFmpeg renderer. Matched-zoom is NOT in the measured `viral_recreation_spec.md`, so the style gate blocks main-video use without measurement.
- **Disposition:** ADOPT vignette-spotlight + reveal punch-ins as renderer capabilities; TEST matched-zoom only in a Shorts lane where no measured grammar exists yet.

### 3.5 Vertical caption grammar (none exists in the playbook today)
- **Mechanics:** Color/emphasis hierarchy: first line bold yellow (setup), body white, shock words red bold; minimal black block behind text; typewriter animation on reveal captions; captions position-tracked to the subject's head (QfbGKfkGP8U, every element built on screen). Two-tone yellow/white auto-caption template (KxsasFMMPpA). 2-4 word caption chunks, centered, "freehand" style (E_CIP98ufto, settings shown).
- **Sources:** (QfbGKfkGP8U) (KxsasFMMPpA) (E_CIP98ufto)
- **Evidence:** STRONG — 3 sources, all demonstrated.
- **Relation:** NEW — no vertical caption grammar exists in `edit_grammar_ruleset.md`; implement via FFmpeg/ASS subtitles, not CapCut.
- **Disposition:** ADOPT as the default caption spec for any Shorts experiment (pairs with tactics 4.1-4.3).

### 3.6 i2v artifact-head trimming + regenerate-don't-ship
- **Mechanics:** Trim exactly the first 0.25s off every generated i2v clip before concatenation (TiycelzfzC0, build-prompt rule; demo output clean). Review each clip, split off the broken opening where it "starts looking normal" (6WDvO0Lu1sY, real physics-breaking clip fixed on screen). Never upload a clip that looks even slightly off; regenerate (~2 min each) — framed as THE difference between 300 views and millions (32DLRsFiXZY, claim undemonstrated; QA practice sound). Regenerate any off outputs before proceeding — "check every output carefully" (ylezKJG7rb8, replacements shown).
- **Sources:** (TiycelzfzC0) (6WDvO0Lu1sY) (32DLRsFiXZY) (ylezKJG7rb8)
- **Evidence:** STRONG — 4 sources, 3 demonstrated.
- **Relation:** CONFIRMS the frame-level-QA and i2v-real-physics rules; the fixed 0.25s auto-head-trim is a NEW mechanical default for the FFmpeg assembly step.
- **Disposition:** TEST the 0.25s head-trim against 3 existing Grok clips first (one-hour frame-strip prototype); make it a renderer default only if the artifact shows up in our clips (aligns with action_plan's conditional).

### 3.7 Edit polish as the top quality lever
- **Mechanics:** In a paired-channel experiment, the editor was the largest cost line ($1,600 vs $250) and the visible difference ("whips, zooms, text"); expensive channel 1M views vs 10K (ROPkHP8jpW0). CAVEAT: experiment fatally confounded — the expensive channel was a rebranded AGED account, the cheap one fresh; and the cheap channel later jumped to 44K+ views with no changes.
- **Sources:** (ROPkHP8jpW0)
- **Evidence:** WEAK as causal proof (confounded n=4); directionally consistent with the corpus.
- **Relation:** CONFIRMS the investment in `edit_grammar_ruleset.md` + `editing.json`; contradicted by (54UTQ2kFhuA) and (4xWQ_fHLGAc), who claim ideation/packaging >> edit polish. Both can be true at different margins.
- **Disposition:** CONFIRM current split: measured-grammar edit floor is non-negotiable, but topic/packaging remain the growth lever (topic scorer stays the top gate).

### 3.8 Comedy-via-edit for a dry narrator
- **Mechanics:** A serious/dry narrator can build likability purely through comedic editing choices — the edit supplies what delivery lacks (Xf_J7kBzxvo, asserted only).
- **Sources:** (Xf_J7kBzxvo)
- **Evidence:** WEAK.
- **Relation:** NEW candidate for `editing.json` energy-variation section.
- **Disposition:** TEST one dry-wit visual gag in a bizdoc chapter; keep if comments react.

---

## 4. SHORTS & SHORT-FORM MECHANICS

### 4.1 AVD>100% read-time hack (loop shorter than its text)
- **Mechanics:** Build a Short from a 5-8s visual loop; overlay text that takes 25-28s to read; viewers pause/loop to finish reading, pushing AVD past 100%. Shown analytics: 7s video, 6M views, 86% stayed-to-watch, 28s AVD (~400%) (PtO7jd8L2xs — the one concrete analytics panel in that video; self-reported dashboard but internally consistent).
- **Sources:** (PtO7jd8L2xs)
- **Evidence:** MEDIUM — single source, but with the most concrete Shorts analytics in the corpus.
- **Relation:** NEW — no Shorts module exists in any playbook file; would seed a Shorts edit-grammar variant.
- **Disposition:** TEST: one Rexcaped Short (6-8s owned composite loop + 20-25s read-time fact caption) and one Prehistoric-POV equivalent; all assets owned, zero copyright exposure.

### 4.2 Shorts ship-gate numbers
- **Mechanics:** Stayed-to-watch ≥75-80% and AVD ≥100% reliably precede millions of views; on Shorts, per-video metrics dominate niche competition (PtO7jd8L2xs, stated + the 86%/400% panel). Distribution keys on per-video AVD/STW + viewer-profile matching, not channel identity — Shorts viewers don't even register channel names while scrolling (PtO7jd8L2xs, live scroll demo).
- **Sources:** (PtO7jd8L2xs)
- **Evidence:** MEDIUM — single source; thresholds plausible and cheaply checkable in Studio.
- **Relation:** NEW metric thresholds in the spirit of the `extract_motion_events.py` ship-gate / style gate (gate-before-ship philosophy).
- **Disposition:** ADOPT as the recorded ship-gate for the 4.1 experiments (a gate for a test, not a production commitment).

### 4.3 Shorts as multi-surface distribution for long-form channels
- **Mechanics:** Upload Shorts alongside long-form: they dominate the homepage feed, surface in YouTube search AND Google SERPs; his short did 126K views vs 8K for the long-form on the same topic (~15x) (8N7-vQ9qX4w, live homepage/search demos on his own videos).
- **Sources:** (8N7-vQ9qX4w)
- **Evidence:** MEDIUM — demonstrated on one channel, n=1.
- **Relation:** NEW — no Shorts pipeline exists for any of the 3 channels; FFmpeg 9:16 crops of existing composites make this nearly free.
- **Disposition:** TEST alongside 4.1: each long-form upload gets one 9:16 cutdown; measure browse impressions.

### 4.4 Short-form clip rhythm 4-8-8-8-4
- **Mechanics:** ~28s transformation Short: first clip 4s, three middle clips 8s, final clip 4s — short-in/long-middle/short-out (6WDvO0Lu1sY, applied per-clip in duration settings; no retention data).
- **Sources:** (6WDvO0Lu1sY)
- **Evidence:** WEAK.
- **Relation:** NEW — no Shorts pacing module; unmeasured.
- **Disposition:** File as a candidate rhythm for the Shorts lane; measure competitor Shorts before committing (same method as edit grammar).

### 4.5 Sub-CTA Short to clear the 1K-subscriber gate
- **Mechanics:** Viral long-form banks watch hours faster than subs accrue; a dedicated "subscribe" Short converts well and closes the sub gap before revenue is lost (BePppCvXC-k — he sat at 999 subs with 4,000+ hours banked; uploaded a sub-CTA Short; analytics shown in Studio).
- **Sources:** (BePppCvXC-k)
- **Evidence:** MEDIUM — real Studio walkthrough, single case.
- **Relation:** NEW upload-practice item for pre-monetization channels (prehistoric_pov, bizdoc).
- **Disposition:** ADOPT into the pre-YPP checklist: when watch-hours pace exceeds sub pace, ship a sub-CTA Short.

### 4.6 Text-commentary "transformation" shield for reused clips
- **Mechanics:** Claim: replacing VO with per-second text commentary makes wholesale-reused TikTok clips "transformative" and YPP-monetizable (QfbGKfkGP8U — backed only by a currency-toggle dashboard trick).
- **Sources:** (QfbGKfkGP8U)
- **Evidence:** WEAK and high-risk — asserted; no policy citation.
- **Relation:** CONTRADICTS the operation's fair-use rules (≤7s/clip, ≤30s/source, transformative layers) and the July-2025 inauthentic-content posture; low-value overlays on reused clips are the policy's explicit target.
- **Disposition:** IGNORE (the caption craft from the same video survives as 3.5; the licensing theory does not).

### 4.7 Facebook Reels / cross-platform short-form intel
- **Mechanics:** FB ranking is engagement-weighted (likes/comments/saves/shares), explicitly not watch-time — design a screenshot-bait "metaphor" beat as the shareable product; structure Hook→Message→Metaphor→looping conclusion (E_CIP98ufto, finished reel shown; claimed $37-49K/mo unverifiable). FB content monetization is invite-only; experience-based trigger ≈5,000 followers + 60,000 minutes viewed (E_CIP98ufto, self-reported across 7 pages; KZKFlik4M8I: waitlist path via Professional dashboard, ~$0.08/1K-view implied payout on an image post, asserted). $2/day interest-targeted ad seeding to teach FB the audience (KZKFlik4M8I, described, no ads dashboard). 3-15 posts/day volume floor (E_CIP98ufto).
- **Sources:** (E_CIP98ufto) (KZKFlik4M8I)
- **Evidence:** MEDIUM on mechanics, WEAK on revenue — nothing verifiable.
- **Relation:** NEW platform surface; no FB module exists anywhere in the playbook. The ad-seeding conflicts with the no-spend-without-prototype rule.
- **Disposition:** TEST at $0 only: cross-post 3-5 already-rendered Rexcaped/POV verticals to a FB page and observe; no ad spend, no volume commitment.

---

## 5. NICHE SELECTION & IDEATION

### 5.1 Outlier scanning relative to baseline (the corpus's most repeated tactic)
- **Mechanics:** Find videos/channels overperforming their OWN baseline: views≫subs on young channels (Oi3nSYYQ6sM: 4-signal scan — oldest-video date for true channel age, last-7-day views vs subs, outlier ratio, cadence vs growth; applied on screen to 12 channels). Views>subs small-channel scan (8KXlxAKOTdE; 4xWQ_fHLGAc with vidIQ screenshots: 1.1K subs/40K views, 6K subs/4M views). Rank competitor outliers by views-per-hour, newest-first; mine their comments for WHY it outliered (8N7-vQ9qX4w). Paste 3-4 channels into Claude, surface videos massively outperforming each channel's average ("icon method"; rank by revenue if data allows) (YtpQSmu794k). Trend filter: a format is real only if it (1) repeats in feed, (2) beats the posting account's own baseline (1M on a 2K-avg account = signal; 1M on 3M-avg = noise), (3) replicates across MULTIPLE small accounts; never infer from big creators (Z5Wn63kLhpI, worked examples). Copy recent outliers, never the all-time #1 (already cloned to death) (8KXlxAKOTdE). Exclude formats you cannot execute (needs on-camera expert → pivot) (LGYiPA5SKvw, shown in Claude's analysis).
- **Sources:** (Oi3nSYYQ6sM) (8KXlxAKOTdE) (4xWQ_fHLGAc) (8N7-vQ9qX4w) (YtpQSmu794k) (Z5Wn63kLhpI) (LGYiPA5SKvw)
- **Evidence:** STRONG — 7 independent sources; the stats scanned are public and real even where the narrators' revenue claims are not.
- **Relation:** CONFIRMS `ideation.json` + the Rexcaped deep-watch/loser-triangulation practice; NEW crisp additions = own-baseline test, multi-small-account replication test, recent-not-alltime rule, comment mining, format-feasibility filter.
- **Disposition:** ADOPT the four NEW sub-rules into `ideation.json`'s competitor-scan procedure (pure text change, no tooling).

### 5.2 Quantified niche-gap entry thresholds
- **Mechanics:** Enter only: niches <60 days old (ideally <30); OR under-saturated (<10 channels posting long-form with real viewership); OR content-gap (incumbents at 300-500K views/video posting <1x/week) (PtO7jd8L2xs, stated, no data shown). Checklist variant: <5 smaller channels all getting views>subs; no incumbent >100K subs; no smaller channels failing; niche <~6 months old; you can make better/longer content; monetizable RPM (8KXlxAKOTdE). Channels <3 months old with views≫subs = untapped-format signal; when a 4-day-old channel already pulls 100K/video, start the clone SAME DAY — the window closes (Oi3nSYYQ6sM, on-screen stats).
- **Sources:** (PtO7jd8L2xs) (8KXlxAKOTdE) (Oi3nSYYQ6sM)
- **Evidence:** MEDIUM-STRONG — 3 sources converging on the same shape; thresholds are heuristics, not measured.
- **Relation:** NEW quantitative inputs for `topic_scorer.py` timeliness + blind_spot tests (which currently score qualitatively).
- **Disposition:** ADOPT as written notes/inputs in the scorer prompt (free); treat numbers as screening heuristics, not gates.

### 5.3 Format transplantation / niche transfer
- **Mechanics:** Move a proven format wholesale to an adjacent market: car→motorbike/boat; "Japan Genius"→Germany/China clones (Oi3nSYYQ6sM, donor + clone channels shown with view counts). Medieval→Stone Age; cats→dogs (8KXlxAKOTdE, real video pairs shown). Import formats proven elsewhere into a niche that lacks them — mythbusting, "surviving 24 hours in X" (BePppCvXC-k: both his breakout and his 3.5M-view hit were transplanted mythbusting; Studio analytics shown). Copy-with-a-twist matrix: same topic/new idea, same idea/new topic, long↔short, same content/different language (PtO7jd8L2xs; Spanish clone claimed 9M views). Title remix onto adjacent subject: "How bad is McDonald's really" → Burger King (tICnK3Qb2k8).
- **Sources:** (Oi3nSYYQ6sM) (8KXlxAKOTdE) (BePppCvXC-k) (PtO7jd8L2xs) (tICnK3Qb2k8)
- **Evidence:** STRONG — 5 sources; BePppCvXC-k is the closest to a documented causal case.
- **Relation:** CONFIRMS the entire Rexcaped model (Spinosnack/Dinoverse clone) + `ideation.json`; the transplant-INTO-a-lazy-niche variant (BePppCvXC-k) is the sharpest articulation.
- **Disposition:** CONFIRM; add "transplant a proven foreign format into this niche" as an explicit idea-generator prompt in `ideation.json`.

### 5.4 Outlier-clone at 100x effort in a low-effort niche
- **Mechanics:** Pick a niche where all competitors do low-effort daily uploads; remake the outlier far better — weeks of work per video, 20-34 min runtime, ~5 videos in ~100 days instead of churn (BePppCvXC-k: video 5 hit 3.5M views, $965/day shown in revenue tab; channel unnamed so unverifiable). The polish-differentiation logic is echoed by the Pay-to-Win experiment despite its confound (ROPkHP8jpW0).
- **Sources:** (BePppCvXC-k) (ROPkHP8jpW0)
- **Evidence:** MEDIUM — detailed Studio walkthrough but anonymous channel; n=1.
- **Relation:** CONFIRMS the operation's quality-bars-over-volume strategy (95+ script, style gate) against the corpus's volume chorus (5.9).
- **Disposition:** CONFIRM — this is already the bet; keep it.

### 5.5 LLM demand-gap clustering (cross-platform arbitrage)
- **Mechanics:** Export titles+transcripts of 2+ proven channels (yt-dlp/DownSub free), paste into Claude with a "blue ocean" demand-mapping prompt → clusters: formats already executed, crowded vs fresh, and topic clusters with demand visible on Wikipedia/news but absent on YouTube; launch the first video serving that demand (54UTQ2kFhuA, full live run shown with output clusters). LLM market research for neglected sub-audiences (9iP588aMFBc, Claude session briefly shown). Meta-prompt ideation from outlier screenshots → ~100 ideas with title/thumbnail/hook/predicted CTR (ipbnR92Elxg, live demo — treat predicted-CTR as decoration).
- **Sources:** (54UTQ2kFhuA) (9iP588aMFBc) (ipbnR92Elxg)
- **Evidence:** MEDIUM-STRONG — live demos in all 3; outcome data absent.
- **Relation:** NEW candidate-generation layer feeding `topic_scorer.py` (blind_spot/fresh_perspective currently score topics you already have) + `sources.json` for the Wikipedia/news demand signal.
- **Disposition:** TEST once for bizdoc video 3: run the demand-map prompt over ColdFusion+HMW transcripts; score the top clusters through the 9-test scorer as usual.

### 5.6 Free pre-flight demand/supply checks
- **Mechanics:** Search-bar supply check: search the exact topic; if done 3+ times with no differentiated angle, drop it — the niche's hardcore fans have seen it (8KXlxAKOTdE, workflow shown). Search-and-see gap check: small faceless channels getting decent views on the query = gap (tICnK3Qb2k8). Studio Research/Trends tab: proceed only on "very high" topic interest (8N7-vQ9qX4w, live demo). Google Trends: rising multi-year line + recent spike = validated demand (tICnK3Qb2k8, one chart shown).
- **Sources:** (8KXlxAKOTdE) (tICnK3Qb2k8) (8N7-vQ9qX4w)
- **Evidence:** MEDIUM-STRONG — all free, mechanical, demonstrated; thresholds are heuristics.
- **Relation:** NEW free evidence inputs for `topic_scorer.py` originality / fresh_perspective / timeliness tests (scorer currently has no live search-volume input).
- **Disposition:** ADOPT as a 5-minute pre-scorer checklist (search count, Research-tab interest, Trends line) logged with each scored topic.

### 5.7 Monetization-survivor scan (the sudden-stop tell)
- **Mechanics:** Before cloning a format, check whether niche channels with hit videos abruptly stopped uploading (every video hitting, then 3 weeks of silence) — read as high-probability YPP denial/removal for that format: "if he wasn't given monetization, you definitely won't be." Scan 3-5 comparable channels (zJmYdcvwY1Y, one on-screen example).
- **Sources:** (zJmYdcvwY1Y)
- **Evidence:** WEAK-MEDIUM — single source; inference not confirmation; cheap to run.
- **Relation:** NEW pre-flight for `topic_scorer.py` alongside source_availability — nothing currently checks the format's monetization survivorship.
- **Disposition:** ADOPT as a manual niche pre-check (5 min): upload-cadence continuity of the 3-5 nearest format-comparables.

### 5.8 Mashup ideation (two proven parents, one child)
- **Mechanics:** Merge two separately-proven high-view formats into one new title: celebrity car tier list (4.8M) + streamer car collection (7.8M) = streamer car tier list; each parent de-risks the child (ROPkHP8jpW0, source videos + view counts shown on screen).
- **Sources:** (ROPkHP8jpW0)
- **Evidence:** MEDIUM — derivation shown; outcome confounded (see 3.7).
- **Relation:** NEW explicit generator for `ideation.json`; feeds the scorer as normal candidates.
- **Disposition:** ADOPT as an ideation prompt pattern (free); the scorer still gates.

### 5.9 Volume-as-feedback vs quality-bar tension (both sides shown)
- **Mechanics:** Volume chorus: 1-2 uploads/day, never skip 30+ days, ~$5/video, diagnose only after sustained volume (54UTQ2kFhuA, case channel's gap-free upload history shown); 10-15-video test budget per new channel, then diagnose in order niche→topics→packaging→length→"bad channel" (= zero impressions, distribution failure, distinct from impressions-but-no-clicks packaging failure) (8KXlxAKOTdE); post a lot because every upload is DATA, not algorithm juice — breakthrough typically video 10/50/100 (ZKsldrcO_fU, host's own ~300-video history); judge a new channel after ~5 uploads minimum (9iP588aMFBc, secret-channel walkthrough); upload frequency as the wedge vs slow incumbents — 12-min videos every other day (zJmYdcvwY1Y); 3/day claims (ylezKJG7rb8, no evidence). Counter-position: 100x-effort low-frequency wins (BePppCvXC-k, see 5.4); Oi3nSYYQ6sM's 1-2/day advice CONTRADICTS the operation's quality bars.
- **Sources:** (54UTQ2kFhuA) (8KXlxAKOTdE) (ZKsldrcO_fU) (9iP588aMFBc) (zJmYdcvwY1Y) (ylezKJG7rb8) (BePppCvXC-k) (Oi3nSYYQ6sM)
- **Evidence:** STRONG that repetition-count matters before judging; UNRESOLVED on optimal cadence — the corpus splits.
- **Relation:** Partially CONFIRMS the bizdoc "frequent uploads" thesis and volume-as-data framing; indicts Prehistoric POV's stalled 1-video state (ZKsldrcO_fU's point lands there).
- **Disposition:** ADOPT the diagnostic ladder (don't judge a channel before ~5-10 uploads; distinguish zero-impressions from impressions-no-clicks) as channel-ops doctrine; keep per-channel cadence set by pipeline throughput, not guru numbers.

### 5.10 80/20 double-down + sequel-on-steroids
- **Mechanics:** Once a format demonstrably works, 80% of uploads repeat it (new subject, same format), 20% test new things (8KXlxAKOTdE, student anecdote unverified). Stop rotating concepts while one is outliering (Oi3nSYYQ6sM, pointed at Terra Mira's mixed thumbnails). Immediately remake your own winner bigger while the audience is hot: 34 min vs 25, packaged from what viewers clicked (BePppCvXC-k: sequel did 600K views in 2 days, drove the $965 day — Studio shown). Formula adherence: the one off-formula video flops while on-formula videos hit; "squeeze the format until all the juice is out" (zJmYdcvwY1Y, three-video channel example).
- **Sources:** (8KXlxAKOTdE) (Oi3nSYYQ6sM) (BePppCvXC-k) (zJmYdcvwY1Y)
- **Evidence:** STRONG — 4 sources, one with analytics.
- **Relation:** NEW as an explicit portfolio ratio — the operation currently plans new creatures/cities rather than doubling down on proven winners; touches `ideation.json` and NEXT_VIDEO planning.
- **Disposition:** ADOPT the principle: if Spino/Lagos outliers, video 3 is its direct escalation, not a new concept; formalize 80/20 only after a first genuine outlier exists.

### 5.11 Niche-down for algorithmic classification
- **Mechanics:** Hyper-specific niches let the bandit pick correct test cohorts (step-parent Notion template vs generic) — keep early uploads tightly clustered in ONE sub-niche so cohorts converge (9iP588aMFBc). Big topics are not niches; sub-niche inside a huge topic (rare anomalies within Roblox) (q0G-FzS6uxk, example channel shown). Problem-rich sub-niches: money/health/relationships/travel/tech, always one level down (calisthenics not health) (TvJhpOxFRsE).
- **Sources:** (9iP588aMFBc) (q0G-FzS6uxk) (TvJhpOxFRsE)
- **Evidence:** MEDIUM — consistent mechanism-level reasoning, no experiments.
- **Relation:** CONFIRMS `topic_scorer.py` (fresh_perspective/best_option) + all three channel identities (already sub-niched).
- **Disposition:** CONFIRM; keep early bizdoc uploads inside one story family (corporate-crime economics) until the audience cluster stabilizes.

### 5.12 Dummy-account niche scanner
- **Mechanics:** Throwaway YouTube account used ONLY for research: search an interest, engage only with faceless videos, ride the sidebar; within days the homepage becomes a curated feed of faceless-niche candidates to scan for small-channel outliers (8KXlxAKOTdE, live demo of his trained account).
- **Sources:** (8KXlxAKOTdE)
- **Evidence:** MEDIUM — real and replicable demo.
- **Relation:** NEW cheap input for `ideation.json` scouting.
- **Disposition:** TEST: one training session (~30 min), check the feed a week later; drop if noise.

### 5.13 Language-market arbitrage
- **Mechanics:** Japanese/Korean AI-story channels as high-RPM low-competition lanes; set channel country + video language; differentiate by inverting the protagonist (3MPSrpIOpAo — third-party monetized badges shown, everything else unverified). Spanish-language clone of a proven Short format, claimed 9M views (PtO7jd8L2xs, self-reported).
- **Sources:** (3MPSrpIOpAo) (PtO7jd8L2xs)
- **Evidence:** WEAK — badges prove YPP passage at recording time, nothing else.
- **Relation:** For this operation the real mapping is NOT foreign-language channels (un-QA-able) but YouTube's free auto-dubbing (see 7.4) — same arbitrage, zero marginal cost.
- **Disposition:** IGNORE new-language channels; capture the value via auto-dub (7.4).

---

## 6. AI PRODUCTION STACK & TOOLING

### 6.1 VO-first, word-timestamp-driven assembly (the corpus's unanimous architecture)
- **Mechanics:** Generate VO first; transcribe to word/segment timestamps; derive every scene boundary and asset duration from real audio timing; name generated files by timecode so assembly is sort-by-name. Variants: FoziScribe pause-timestamps → scene cuts (WVT2FCjhDDY); ElevenLabs STT JSON with per-word times → beat durations passed INTO the gen request so clips arrive pre-timed (Dmqz8opSHzE); ElevenLabs API word timestamps → 4-8 clips per chapter (TiycelzfzC0); TurboScribe segments → one image per timestamp, files renamed to timecodes (f-ufEhGtVpw) (CxwFu1nEsZQ — ~20-min assembly shown); audioconverter.ai transcript → per-segment prompts (4xWQ_fHLGAc); VO-led CapCut assembly trimming TTS pauses (E_CIP98ufto); VO runtime → equal-split into N segments at 1 img/3s (zJmYdcvwY1Y); VO-first timeline with slow-stretch fitting (NlfmQpSaYMo).
- **Sources:** (WVT2FCjhDDY) (Dmqz8opSHzE) (TiycelzfzC0) (f-ufEhGtVpw) (CxwFu1nEsZQ) (4xWQ_fHLGAc) (E_CIP98ufto) (zJmYdcvwY1Y) (NlfmQpSaYMo)
- **Evidence:** STRONG — 9 independent implementations, most shown on screen.
- **Relation:** CONFIRMS the pipeline architecture wholesale: WhisperX word-level alignment → `realign_paper_edit.py` → paper-edit JSON → `ffmpeg_production_render.py` is a strictly finer-grained, automated version of every variant above. Zero adoption needed.
- **Disposition:** CONFIRM — the operation is ahead of the entire corpus on this axis; treat as external validation, not input.

### 6.2 Claude Code as pipeline driver + skill packaging
- **Mechanics:** Package repeatable video workflows as project-local slash-command skills: /vox-video builds script→TTS→stills→i2v→FFmpeg for ~$3.50/35s chapter, supports "regenerate video two" then auto-recombine (TiycelzfzC0, invoked live twice, full build prompt public). /long-form-edit + brand.md (fonts/hex) + raw/→output/ folder convention for talking-head edits (vI4RdXMSq8c, live demo). Rule-docs folder read into memory at session start (text style, scene composition, revision behavior) (oWkUwno6b0E). Claude-as-director via MCP connectors executing gen calls (PaXuebdY75U, f-ufEhGtVpw, CxwFu1nEsZQ, LGYiPA5SKvw, r81ImbWaxEE — all shown). One-off pipeline utilities built on demand (custom crop tool, KLswOquhsM8).
- **Sources:** (TiycelzfzC0) (vI4RdXMSq8c) (oWkUwno6b0E) (PaXuebdY75U) (f-ufEhGtVpw) (CxwFu1nEsZQ) (LGYiPA5SKvw) (r81ImbWaxEE) (KLswOquhsM8)
- **Evidence:** STRONG — 9 sources, most with live sessions.
- **Relation:** CONFIRMS the existing Claude-Code-driven pipeline (run_pipeline.py, rexcaped_edit_engine.py, owner's `~/.claude/skills` practice). The per-clip "regenerate N then recombine" ergonomic and the brand.md pattern are NEW small conveniences.
- **Disposition:** CONFIRM; optionally ADOPT a per-beat regen convenience command — no architecture change.

### 6.3 Remotion as a Claude-driven motion-graphics generator (new-batch cluster)
- **Mechanics:** `npx create-video@latest` installed as a skill; "read the script, draft scenes" (20 drafted) → "build the first five scenes" → 1080p/4K MP4s in out/; ~1 hour for a 2.5-min demo; free for individuals/≤3-person companies (oWkUwno6b0E, full on-screen workflow incl. Remotion Studio). Creative-direction lock per 5-scene batch (named aesthetic per batch, re-rolled on command). Region-reorient revision prompt ("scene 13, left 35% of screen" — logic-aware reflow; also top/bottom-50% for vertical). Revisions always create v2, never edit the original. Render native alpha rather than green-screen keying (his green-screen workaround CONTRADICTS the known H.264-kills-alpha rule — use ProRes/alpha-capable output instead).
- **Sources:** (oWkUwno6b0E)
- **Evidence:** MEDIUM — single source but fully demonstrated end-to-end; framework is established/free.
- **Relation:** NEW asset TYPE for the existing engine: Remotion output feeds `ffmpeg_production_render.py` as overlay/B-roll clips — do NOT let it become a parallel assembler. Creative-direction lock maps to the clip-variety rule; v2-never-edit CONFIRMS the provenance/approval-ledger pattern.
- **Disposition:** TEST: one bizdoc stat-graphic scene (e.g. the fines-vs-revenue chart) built via the Remotion skill, rendered with alpha, composited by the FFmpeg renderer; adopt if it beats the static card in under an hour of work.

### 6.4 Hyperframes for programmatic charts/captions (new-batch cluster)
- **Mechanics:** Free open-source HeyGen framework (github.com/heygen-com/hyperframes): Claude CODES motion graphics, chart animations, styled captions instead of burning gen credits; preview studio + storyboard; downloadable pre-made skills in the repo; rated above Remotion for fully-automatic editing by the one user shown (vI4RdXMSq8c, overlays visible in her own video + demo preview).
- **Sources:** (vI4RdXMSq8c)
- **Evidence:** MEDIUM — single source, working output shown; "better than Remotion" is one person's take.
- **Relation:** NEW — fills a real gap: bizdoc stat beats are currently static cards + Ken Burns with no animated charts. Same integration rule as 6.3: output feeds the FFmpeg renderer.
- **Disposition:** TEST head-to-head with 6.3 on the same bizdoc stat scene; keep whichever wins, file the loser.

### 6.5 Model tiering: expensive model plans, cheap model executes
- **Mechanics:** Opus for designing/setting up workflows, switch to Sonnet via /model for mechanical runs; she kills a run that auto-switched to Fable ("way too expensive to do this"), reserving it for high-ROI setup work; subscription usage is token-limited, so the plan fee is the whole edit cost (vI4RdXMSq8c, on-screen switch). Same conclusion independently: Fable-max was overkill for a full channel build; per-task cheaper Opus models, single tasks not mega-prompts (LGYiPA5SKvw).
- **Sources:** (vI4RdXMSq8c) (LGYiPA5SKvw)
- **Evidence:** MEDIUM — 2 sources, both from real sessions.
- **Relation:** NEW ops rule for the Claude-Code pipeline (no existing model-tier doctrine for long render/QA batches on the capped plan).
- **Disposition:** ADOPT: planning/spec sessions on the strongest model; batch execution (renders, QA sweeps, file ops) on the cheaper tier.

### 6.6 SAM 2 multi-element layer segmentation
- **Mechanics:** Send each still to Segment Anything Model 2 → folder of separated elements per shot → animate elements individually (slide-ins, staggered entrances, pendulum idle motion so nothing is static); segmentation imperfect — keep key pieces, discard fragments (Dmqz8opSHzE, per-shot element folders + keyframe animation shown; he used fal.ai, but SAM 2 weights are open → candidate for local $0 run on the M5, unverified).
- **Sources:** (Dmqz8opSHzE)
- **Evidence:** MEDIUM — demonstrated; local-run claim is an inference from open weights.
- **Relation:** NEW — multi-element upgrade to the layered-composite engine's single-cutout rembg step; feeds the same PIL/FFmpeg compositing.
- **Disposition:** TEST: prototype SAM 2 locally on one existing bizdoc still (10-min rule); adopt into the composite toolbox if it runs clean on MPS.

### 6.7 Vox-style codified "brains" (design system + animation scaffold)
- **Mechanics:** Design brain: ~100 Pinterest references → Figma board → PDF → Claude derives a design system (colors, fonts, shapes, text treatment, textures) governing every generated scene (PaXuebdY75U, output visibly matches Vox's cutout style). Animator brain: every motion-graphics scene = 5 assets with fixed roles — text (minimal pop), main object (paper-unfold/position pop), background (static), secondary objects (subtle idle), camera (zoom/pan) — plus "rough, choppy, jittery" style riders (PaXuebdY75U, 6 scenes generated with it). One-screenshot design-system variant: feed Claude a single reference screenshot once, reuse every video (1ywvAeaFojo, deck visibly on-brand). Style vocabulary assigned per shot from a small named library (cutout collage / kinetic typography / map animation), style block appended to every prompt (Dmqz8opSHzE, assignment screen shown).
- **Sources:** (PaXuebdY75U) (1ywvAeaFojo) (Dmqz8opSHzE)
- **Evidence:** STRONG — 3 sources, all with on-screen outputs.
- **Relation:** Editor-brain half CONFIRMS the measured-recreation method (see 3.1). Design-system extraction and the 5-layer scene scaffold are NEW — `editing.json` covers cuts/pacing, not visual design language; the scaffold is the infographic analog of the existing TSV physics riders.
- **Disposition:** ADOPT the 5-layer scaffold as the prompt template for any bizdoc animated-infographic beat (pairs with 6.3/6.4); TEST a one-time design-system extraction from ColdFusion/HMW reference frames.

### 6.8 Style-reference conditioning on every still
- **Mechanics:** One pre-made style-reference image passed as input to EVERY still generation guarantees cross-frame consistency (TiycelzfzC0, build-prompt rule, demos visibly consistent). Style lock from a competitor frame: have Claude write out the style as a fixed descriptor prepended to every prompt (zJmYdcvwY1Y, demoed). Screenshot-a-style into the brand kit: "I like this style but swap the color to my brand gold" (vI4RdXMSq8c). Whole-script-first entity bible: read the entire script, extract recurring characters/locations/objects BEFORE generating any beat (CxwFu1nEsZQ, 11-page master prompt scrolled on screen; f-ufEhGtVpw's whole-script-context batch variant).
- **Sources:** (TiycelzfzC0) (zJmYdcvwY1Y) (vI4RdXMSq8c) (CxwFu1nEsZQ) (f-ufEhGtVpw)
- **Evidence:** STRONG — 5 sources with visible outputs.
- **Relation:** CONFIRMS `style_bands.json` + `gate_style.py` (bands as the arbiter); NEW practice = explicit per-still reference-image conditioning in the ChatGPT/Gemini still workflows, and the read-whole-script-first entity-bible pre-pass for batch prompt generation.
- **Disposition:** ADOPT the entity-bible pre-pass in the storyboard prompt builder; ADOPT per-still style-reference attachment where the gen tool supports it.

### 6.9 Character-consistency cluster (locks, turnarounds, chaining)
- **Mechanics:** Character lock: approved design image + frozen LLM-maintained descriptor block prepended verbatim to every scene prompt, reference image attached to every gen (zq_Yi1gK6Fc, demoed; NA0AOlCmelQ's prompt-only variant). A/B pre-lock pair: generate exactly two variants (faithful vs composition-optimized), pick, lock (zq_Yi1gK6Fc). Multi-angle turnaround sheet as the persistent reference asset, edited via text (6WDvO0Lu1sY). Chained-still generation: scene N uses scene N-1's IMAGE as reference so accumulated state carries forward (6WDvO0Lu1sY, scenes 2-5 chained on screen). Master reference images explicitly MAPPED per prompt — single-character shots only get that character's reference (Qsi9MeLh95Q). Named reference images in batch tools, inconsistent-then-consistent before/after shown (ylezKJG7rb8). Reference-anchored subject consistency across 5 stills (lL9gjPw5yjg). Previous-clip-as-reference in-tool chaining (sMo5RT_dPxc). Consistency collapses across separate generations — prefer one continuous gen with sliding windows for multi-beat character shots (KLswOquhsM8, failed 10-15s scene described).
- **Sources:** (zq_Yi1gK6Fc) (NA0AOlCmelQ) (6WDvO0Lu1sY) (Qsi9MeLh95Q) (ylezKJG7rb8) (KLswOquhsM8) (sMo5RT_dPxc) (lL9gjPw5yjg)
- **Evidence:** STRONG — 8 sources; the strongest-converging production tactic in the corpus.
- **Relation:** CONFIRMS the consistency-guarantee/provenance system and AMBER's queued reference_images work. NEW specifics worth taking: A/B pre-lock intake, turnaround-sheet format, state-carry chaining for progressive sequences, per-prompt character mapping, one-continuous-gen preference.
- **Disposition:** TEST A/B pre-lock + per-prompt reference mapping on one AMBER reference_images beat first (source evidence is demo-grade); TEST state-carry chaining on one Prehistoric-POV progressive sequence.

### 6.10 Last-frame continuity chaining for i2v
- **Mechanics:** Use clip N's final frame as clip N+1's i2v start image so multi-clip sequences read as one continuous shot; FFmpeg `-sseof -0.1` extracts the frame, feeding the existing Grok clipboard-upload recipe (32DLRsFiXZY, demonstrated in Flow incl. a credits-low copy-frame variant; sMo5RT_dPxc's save-frame-then-animate variant, 4 chained demo scenes shown).
- **Sources:** (32DLRsFiXZY) (sMo5RT_dPxc)
- **Evidence:** MEDIUM — 2 sources, both demonstrated in-tool.
- **Relation:** NEW portable technique for the Grok i2v workflow (`reference_grok_i2v_clipboard_upload`). GUARD: overuse CONTRADICTS the clip-variety rule — scope to continuous-action pairs and POV runs only.
- **Disposition:** ADOPT scoped: allowed only on beat pairs tagged continuous-action in the storyboard.

### 6.11 Timestamp-conditioned i2v prompts (motion event on the word)
- **Mechanics:** Embed the second at which a key word lands into the video-gen prompt itself: "in a 6s clip, if 'door' is said at 3s, that goes in the video prompt" — the generated motion event fires on the word; use sparingly, only for prominent events (TiycelzfzC0, verbatim in the public build prompt; demo motion beats land on VO words).
- **Sources:** (TiycelzfzC0)
- **Evidence:** MEDIUM — single source, but written spec + visible result.
- **Relation:** NEW — extends `edit_grammar_ruleset.md` cut-on-turn-words upstream into generation, and gives `extract_motion_events.py` a generation-side counterpart (the gate can then check what the prompt requested).
- **Disposition:** TEST on 3 Rexcaped beats where the VO names the action (e.g. "strikes" at a known timestamp); compare motion-event alignment against unconditioned gens.

### 6.12 Audio-conditioned talking-character gen + per-second direction (Relay Prompts)
- **Mechanics:** WAN2GP + LTX 2.3 22B Distill: upload character start frame + finished voice track; the model acts the performance FROM the audio (mouth, timing, gestures). Relay Prompt = timestamped action directives inside the generator ("points at camera as she talks, then waves") (KLswOquhsM8, UI walkthrough + on-cue result clip). Masked-crop discipline: crop only the character region; swap image, gen output, and paste-back region must be the EXACT same resolution; feathered rectangle-mask composite hides seams (KLswOquhsM8, resolution-mismatch failure demonstrated). Best-of-N with visible rejects: 10-20 gens for one composite scene (KLswOquhsM8).
- **Sources:** (KLswOquhsM8)
- **Evidence:** MEDIUM-STRONG for one source — everything self-evidencing on screen, honest costs (~8h R&D for 5s), no revenue claims.
- **Relation:** Audio-conditioning attacks the ROOT CAUSE the talking-creature-QA rule (`feedback_i2v_talking_creature_qa`) currently catches after the fact. Masked-crop CONFIRMS `tools/amber/stage_b_vace.py` architecture — adopt an explicit crop==gen==composite resolution assertion. Relay Prompts are the in-generator analog of AMBER's event sheets. Human-character swaps stay banned (no-AI-faces rule); creature application only.
- **Disposition:** TEST audio-conditioned gen on ONE creature dialogue beat (local, $0); ADOPT the resolution assertion in stage_b_vace.py regardless.

### 6.13 Controlled camera-movement vocabulary as a prompt rider
- **Mechanics:** Maintain a cheat-sheet of named camera movements (38 in the example); upload with the scene script so the LLM assigns one specific movement per scene instead of inventing motion ad hoc (ylezKJG7rb8, per-scene assignments + varied clips shown; Qsi9MeLh95Q's camera-movements doc variant). Structured preset parameters (camera/lens/aperture/lighting/movement dropdowns compiled into the prompt) as the same idea productized (vuo_bPhkD_U, preset panels shown).
- **Sources:** (ylezKJG7rb8) (Qsi9MeLh95Q) (vuo_bPhkD_U)
- **Evidence:** MEDIUM-STRONG — 3 sources, 2 demonstrated.
- **Relation:** NEW rider block for the TSV/i2v prompt system — exact same pattern as the existing physics and creature-mouth-closed riders; also serves the clip-variety rule (distinct vantage per beat becomes assignable).
- **Disposition:** ADOPT: add a camera-move rider column to the TSV prompt build, populated from a fixed vocabulary doc.

### 6.14 Clay-to-photoreal motion authorship
- **Mechanics:** Animate a crude clay/blocked 3D pass for exact motion control, then have an AI model re-render it photoreal — separating motion authorship from surface quality (vuo_bPhkD_U, results-only demo).
- **Sources:** (vuo_bPhkD_U)
- **Evidence:** WEAK — brief results-only demo from a plugin seller.
- **Relation:** NEW idea mapping onto local VACE-1.3B (crude motion pass as the driving video). Physics control at the source serves the i2v-real-physics rule.
- **Disposition:** TEST as a $0 one-beat VACE experiment on the M5 when a hard-physics shot next fails QA.

### 6.15 Free-tool intel (verified against the operation's own audits)
- **Mechanics:** Google Flow free tier = 50 credits/day, watermarked, Nano Banana models; "unlimited free" claims are FALSE (NA0AOlCmelQ, NlfmQpSaYMo, lDpOnE3VJVI, JpvaUUgtTVk, h6DB0e96GI0 all CONTRADICT the operation's 2026-07-20 audit `reference_ai_cardboard_diy_niche`; multi-account/temp-mail refills = ToS abuse, rejected — NA0AOlCmelQ, 3MPSrpIOpAo, WVT2FCjhDDY's free-account churn). Omni Flash lacks first/last-frame conditioning — two-image "ingredients" mode is the workaround (JpvaUUgtTVk, stated on screen; validates AMBER's two-keyframe pattern). Meta AI frame-to-video as $0 i2v fallback; Google Vids ≈10-12 free daily Veo 3.1 gens as a high-motion escape hatch (Qsi9MeLh95Q, partial demos — image-input support and watermark status UNVERIFIED). Google AI Studio TTS free (Gemini voice models) for scratch-VO/timing drafts (ylezKJG7rb8, lL9gjPw5yjg, Qsi9MeLh95Q — never a final-voice replacement given locked channel voices). Gemini music gen matched to an emotional arc (lDpOnE3VJVI, Qsi9MeLh95Q — Content-ID status of generated music unverified; Pixabay-music rule stands). Watermark hiding by scale-shift/overlay (NlfmQpSaYMo, lDpOnE3VJVI) — CONTRADICTS provenance/disclosure posture, never adopt. CRITICAL UNVERIFIED CLAIM: "Grok killed their free tier" (Qsi9MeLh95Q, description-sourced, no screenshot) — directly threatens the PRIMARY i2v engine.
- **Sources:** (NA0AOlCmelQ) (NlfmQpSaYMo) (lDpOnE3VJVI) (JpvaUUgtTVk) (Qsi9MeLh95Q) (ylezKJG7rb8) (lL9gjPw5yjg) (32DLRsFiXZY) (3MPSrpIOpAo) (WVT2FCjhDDY)
- **Evidence:** MIXED — free-tier inflation systematically debunked by the operation's own audit; the fallback-tool leads are MEDIUM.
- **Relation:** Maps to `reference_tool_landscape_2026-06` + the no-new-paid-APIs hard rule.
- **Disposition:** ADOPT one action: verify Grok Imagine free-tier status BEFORE the Spino/Lagos i2v batch. FILE Meta AI + Google Vids as fallback slots pending a 10-min test each.

### 6.16 Paid aggregator/MCP economy (blocked, but file the pattern)
- **Mechanics:** MCP connectors let Claude drive gen platforms natively: Higgsfield MCP (f-ufEhGtVpw, CxwFu1nEsZQ, PaXuebdY75U, vI4RdXMSq8c at $2-7/video B-roll, r81ImbWaxEE, Z5Wn63kLhpI — setup shown repeatedly; ~$20 per 6-scene edit PaXuebdY75U; ~$41 full video with motion vs $5-10 stills-only LGYiPA5SKvw). Pay-per-use aggregators: kie.ai (one key → Omni Flash/Seedance 2.0 Fast/GPT-Image-2, ~$3.50/35s chapter at 720p — TiycelzfzC0, Dmqz8opSHzE), fal.ai (per-clip frontier-model access, no subscription — vuo_bPhkD_U). Pre-spend gates and refund-on-failure patterns shown (Z5Wn63kLhpI: 16/20, 17/20 success with refunds).
- **Sources:** (f-ufEhGtVpw) (CxwFu1nEsZQ) (PaXuebdY75U) (vI4RdXMSq8c) (r81ImbWaxEE) (TiycelzfzC0) (Dmqz8opSHzE) (vuo_bPhkD_U) (LGYiPA5SKvw) (Z5Wn63kLhpI)
- **Evidence:** STRONG that the plumbing works (10 sources, live setups); costs are the sellers' own numbers.
- **Relation:** ALL blocked by the no-new-paid-APIs/subscriptions hard rule; local VACE-1.3B + Grok i2v cover the need at $0. The MCP-connector PATTERN (replacing fragile browser automation like the clipboard-upload recipe) is the real intel.
- **Disposition:** FILE as known options with observed price points; revisit only if a $0 path breaks and the owner approves spend (fal.ai pay-per-clip is the cheapest prototype-compatible entry).

### 6.17 One-tool end-to-end generators
- **Mechanics:** Noodle Tomato idea→"90-120-min video" claims (8Mx2m0djgTA — 90-min never demonstrated; 5-min demo only); Abacus AI as the $7-10 all-model workhorse (4xWQ_fHLGAc, E_CIP98ufto — affiliate-driven); Narration AI topic→script→scenes→prompts (Ao_d-uaMJvk); Opus AI Producer black-box editor (Xf_J7kBzxvo, sponsor beta); DaVinci-integrated gen plugin (vuo_bPhkD_U — also CONTRADICTS the FFmpeg-is-the-engine tool policy).
- **Sources:** (8Mx2m0djgTA) (4xWQ_fHLGAc) (E_CIP98ufto) (Ao_d-uaMJvk) (Xf_J7kBzxvo) (vuo_bPhkD_U)
- **Evidence:** WEAK for the headline claims; demos show mediocre template output.
- **Relation:** CONTRADICTS the pipeline moat (measured grammar, QA gates, FFmpeg engine) — a black-box editor cannot pass the motion-event ship-gate or style gate.
- **Disposition:** IGNORE.

### 6.18 Voice strategy: distinct or own, never the crowd's stock voice
- **Mechanics:** AI voices per se are not blocked (as of mid-2026), but overused stock voices carry the "heard on 50 AI channels" fingerprint — clone your own or pick obscure library voices (CxwFu1nEsZQ; TvJhpOxFRsE; YtpQSmu794k — whose slop definition includes "robot voice"; all asserted). Casting-to-format nuance: pick a voice matching the proven incumbent's timbre/age (zJmYdcvwY1Y — mild tension; resolve as "distinct from the crowd, congruent with the genre"). CONTRADICTED practices: cloning a competitor's/real person's voice "no issue" (3MPSrpIOpAo — flat wrong under impersonation/inauthentic-content policy; Oi3nSYYQ6sM flags ban risk on a streamer-clone channel).
- **Sources:** (CxwFu1nEsZQ) (TvJhpOxFRsE) (YtpQSmu794k) (zJmYdcvwY1Y) (3MPSrpIOpAo) (Oi3nSYYQ6sM)
- **Evidence:** MEDIUM — consistent practitioner opinion; no measurements.
- **Relation:** CONFIRMS the F5-TTS own-voice roadmap for bizdoc; flags a real gap: Rexcaped/PPOV/Dinoverse use POPULAR ElevenLabs library voices (Liam/Jessica/Brian).
- **Disposition:** TEST: audit how many top faceless channels use the same Liam/Jessica/Brian voices; if overlap is high, trial one lesser-known voice on a non-canonical upload.

### 6.19 Scripting augmentations (interview pass, overage-prune, conciseness)
- **Mechanics:** Interview/YAP pass: voice-dictate a brain dump, have Claude interview you for stances/opinions before drafting — the owner becomes the source of truth, reducing rewrite churn (YtpQSmu794k, described; 1ywvAeaFojo, demonstrated live with voice mode — claim: extracts non-copyable opinions that also differentiate the video). Anti-fragile overage: generate 15 list items, cut the 5 weakest ("every format is secretly a listicle") (YtpQSmu794k). AI scripts are near-parity with $250 human scripts; the human edge is conciseness — so add a ramble-cutting pass to AI drafts (ROPkHP8jpW0, side-by-side shown). Blend ≥2 competitor videos as structure reference so the skeleton transfers but output stays unique (4xWQ_fHLGAc, live generation). Scope-locked outline: define scope first, refuse side-topics, end with 2 hook options (1ywvAeaFojo).
- **Sources:** (YtpQSmu794k) (1ywvAeaFojo) (ROPkHP8jpW0) (4xWQ_fHLGAc)
- **Evidence:** MEDIUM-STRONG — 4 sources, 2 demonstrated.
- **Relation:** CONFIRMS `scripting.json` + the 95+ script bar (one-thesis discipline, reference-driven structure); interview-pass and overage-prune are NEW cheap steps.
- **Disposition:** ADOPT overage-prune for any list-structured bizdoc segment; TEST the interview pass on bizdoc video 2 (owner voice-dictates stances before Claude drafts).

### 6.20 Approval gates before any paid/lossy step
- **Mechanics:** Pipeline pauses for human approval at shot list, image prompts, generated images, video prompts — before ANY credit spend; failed calls auto-retry (Dmqz8opSHzE, gates shown). Pre-spend question gate: Claude must ask clarifying questions before generating paid B-roll (vI4RdXMSq8c, shown). One test video before batch-generating 32 more (LGYiPA5SKvw).
- **Sources:** (Dmqz8opSHzE) (vI4RdXMSq8c) (LGYiPA5SKvw)
- **Evidence:** STRONG — 3 sources, all shown.
- **Relation:** CONFIRMS the consistency-guarantee approval ledger + PROTOTYPE-BEFORE-PLAN + no-spend-without-prototype rules.
- **Disposition:** CONFIRM.

### 6.21 Prompt-batch degradation guard
- **Mechanics:** Never ask an LLM for 100 image prompts in one request — prompts progressively compress and shrink; generate ~5 per request from pre-split script segments (zJmYdcvwY1Y, stated from experience); 15-scene storyboard emitted in 3 batches for the same reason (NA0AOlCmelQ).
- **Sources:** (zJmYdcvwY1Y) (NA0AOlCmelQ)
- **Evidence:** MEDIUM — 2 sources, consistent with known long-output behavior.
- **Relation:** NEW minor guard for conversational prompt-gen passes (the scripted TSV builder is unaffected).
- **Disposition:** ADOPT as a note in the prompt-builder docs.

### 6.22 Real footage + composited AI beats pure-AI visuals
- **Mechanics:** "Instead of AI images, using real images… you will have a huge competitive advantage" over the AI-slop incumbent (ipbnR92Elxg, on-screen comparison). "Trust recession": visible realness converts; AI slop floods feeds (Eb8wlFawjTw, anecdotal buyer quotes). Barbell: bleeding-edge AI production + radically human identity; undifferentiated "say-nothing faceless" content gets squeezed out (ZKsldrcO_fU, vidIQ prediction, no data). 2D/AI character over REAL photo backgrounds as a channel look (zq_Yi1gK6Fc — independent validation of mixed-media compositing).
- **Sources:** (ipbnR92Elxg) (Eb8wlFawjTw) (ZKsldrcO_fU) (zq_Yi1gK6Fc)
- **Evidence:** MEDIUM — convergent opinion including an industry-adjacent source; no experiments.
- **Relation:** CONFIRMS the layered-composite engine thesis (AI creature INTO real footage) and the no-AI-human-faces rule; the inverse (AI backgrounds behind real subjects, vuo_bPhkD_U) CONTRADICTS the measured Rexcaped formula and is rejected for main videos.
- **Disposition:** CONFIRM — this is the moat; cite it when tempted by full-gen pipelines.

### 6.23 AI-face techniques (banned lane, catalogued for awareness)
- **Mechanics:** HeyGen avatar reactions/presenters (PtO7jd8L2xs, ipbnR92Elxg, TvJhpOxFRsE); face-swap with identity-preserving edit prompt (Z5Wn63kLhpI, demoed); real-performer-driven character swap via SCAIL-2/Flux (KLswOquhsM8). Counter-testimony from inside the genre: avatar presenters fail "99.9% of the time" (uncanny valley) and risk demonetization/shadowban; use a persona/cartoon + real voice instead (YtpQSmu794k). Owned non-human mascot + locked voice as the AI-commoditization hedge (LGYiPA5SKvw — consistent 2D mascot shown across videos).
- **Sources:** (PtO7jd8L2xs) (ipbnR92Elxg) (TvJhpOxFRsE) (Z5Wn63kLhpI) (KLswOquhsM8) (YtpQSmu794k) (LGYiPA5SKvw)
- **Evidence:** n/a — catalogued, not evaluated for adoption.
- **Relation:** CONTRADICTS the no-AI-human-faces hard rule (`feedback_ai_faces_use_real_photos`); YtpQSmu794k independently CONFIRMS the rule; the mascot hedge CONFIRMS existing Dinoverse-host practice. Creature applications of the same tech route through 6.12.
- **Disposition:** IGNORE for humans, permanently.

---

## 7. UPLOAD & DISTRIBUTION PRACTICE

### 7.1 Cold-start channel seeding checklist
- **Mechanics:** Before first upload: pull ~5 high-search-volume niche keywords, LLM-write a keyword-rich channel description, paste the same keywords into Studio Settings→Channel keywords, set country, verify phone — claimed to guide cold-start audience matching so early videos aren't shown to random viewers (4xWQ_fHLGAc — his channel hit 1K subs/4K hours in 9 days with 5 videos, screenshot shown; mechanism asserted, not measured). Channel tags/description via LLM + set target country and video language (3MPSrpIOpAo). Keyword-forward channel naming (KZKFlik4M8I — FB-side but same logic).
- **Sources:** (4xWQ_fHLGAc) (3MPSrpIOpAo) (KZKFlik4M8I)
- **Evidence:** MEDIUM — one supporting outcome screenshot, mechanism unproven.
- **Relation:** NEW — no playbook module covers channel-level setup; Prehistoric POV did branding/SEO ad hoc.
- **Disposition:** ADOPT as the pre-launch checklist for the bizdoc channel (10 minutes, zero risk).

### 7.2 Feature-eligibility + verification pre-flight
- **Mechanics:** Studio→Settings→Channel→Feature eligibility: standard/intermediate/advanced all enabled (advanced = phone/ID verification; gates streaming, >15-min uploads, custom thumbnails, appeals) (eF75ZffgsUk, shown in Studio; q0G-FzS6uxk claims advanced verification raises account trust). Account warm-up before first upload: weeks of real watching/liking/commenting; never automate the account (q0G-FzS6uxk, 8KXlxAKOTdE — folk theory, harmless; 8KXlxAKOTdE concedes "does not work 100% of the time").
- **Sources:** (eF75ZffgsUk) (q0G-FzS6uxk) (8KXlxAKOTdE)
- **Evidence:** MEDIUM for the eligibility mechanics (real Studio settings); WEAK for warm-up trust effects.
- **Relation:** NEW upload-practice checklist items; bizdoc's 23.4-min video literally requires the >15-min unlock.
- **Disposition:** ADOPT eligibility verification into the pre-launch checklist; treat warm-up as costless hygiene, not a lever.

### 7.3 Cold-start patience doctrine (don't judge, don't delete, don't repackage early)
- **Mechanics:** ~72h indexing window: zero views/impressions for ~3 days on a new channel is normal (q0G-FzS6uxk, own analytics screenshot). ~14-day window: videos can sit at ~10 impressions for 10-12 days then explode around day 14; early recommendations are MIS-TARGETED (his Roblox video went to MrBeast-Minecraft audiences first — "broccoli to a kid who loves donuts"), so week-1 CTR/retention is noise (BePppCvXC-k, impression-source breakdown shown in Studio). Delayed push: a 4-video channel jumped 10K→44K+ views weeks later with zero changes — wait ~4-6 weeks before repackaging (ROPkHP8jpW0, analytics update shown). Never delete/unlist early flops: after one video passes its test, the algorithm RETRO-TESTS old videos on the new audience cluster; her weeks-old flop went viral after video 5 passed and monetized the channel (9iP588aMFBc, secret-channel walkthrough). Judge after ~5 uploads minimum (9iP588aMFBc). CONTRADICTED: delete-and-repost dead videos to a fresh channel (8KXlxAKOTdE) — rejected; conflicts with retro-testing evidence and reused-content risk.
- **Sources:** (q0G-FzS6uxk) (BePppCvXC-k) (ROPkHP8jpW0) (9iP588aMFBc) (8KXlxAKOTdE)
- **Evidence:** STRONG — 4 independent analytics-backed accounts converging; the counter-tactic is evidence-free.
- **Relation:** NEW — no playbook module covers post-upload analytics interpretation; becomes channel-ops doctrine next to the QA watcher.
- **Disposition:** ADOPT: 72h no-read, 14-day no-judgment, 4-6-week no-repackage, never-delete. Write into NEXT_VIDEO/channel-ops notes for all three channels.

### 7.4 Post-upload feature stack: unlisted-first, auto-dub, disclosure
- **Mechanics:** Upload unlisted, wait for HD processing + dub generation, then flip public so first viewers never hit low-res (4xWQ_fHLGAc, stated practice). Enable auto-dubbing (Studio→Advanced settings) + set original language per video — free translated audio tracks (4xWQ_fHLGAc, shown; captures the 5.13 language arbitrage at $0). Answer the altered/synthetic-content question HONESTLY on AI-heavy channels (eF75ZffgsUk shows the toggle; E_CIP98ufto's leave-the-AI-label-off reasoning is a CONTRADICT — never copy).
- **Sources:** (4xWQ_fHLGAc) (eF75ZffgsUk) (E_CIP98ufto)
- **Evidence:** MEDIUM — real Studio features shown; reach effects unmeasured.
- **Relation:** NEW upload-checklist items; disclosure decision maps to the operation's #1-risk posture.
- **Disposition:** ADOPT all three into the per-upload checklist (unlisted-first, auto-dub on, per-channel disclosure decision recorded).

### 7.5 Launch-window engagement micro-habits
- **Mechanics:** Pin a prepared comment at publish; reply to comments in the first hour (YtpQSmu794k, described). LLM-generated description/tags/chapters from the final script; tags low-value but take 20 seconds (YtpQSmu794k; WVT2FCjhDDY's metadata package). Keyword-named export file + subscribe-watermark PNG set to "entire video" (4xWQ_fHLGAc — filename-SEO is folklore with no evidence; watermark real but minor).
- **Sources:** (YtpQSmu794k) (WVT2FCjhDDY) (4xWQ_fHLGAc)
- **Evidence:** WEAK-MEDIUM — practice descriptions, no measurements.
- **Relation:** CONFIRMS the existing Rexcaped upload-package practice (title/desc/tags/chapters already Claude-built); pin-at-publish + first-hour replies are the NEW sliver.
- **Disposition:** ADOPT pin-at-publish + first-hour reply window; skip filename SEO.

### 7.6 Subscriber-drag audit + notify toggle
- **Mechanics:** Studio→Audience: check new/casual/regular split, bell-notification % (his: 17% combined), and subscriber vs non-subscriber CTR/watch time via the metric picker; if subscriber engagement is poor, uncheck "Publish to subscriptions feed and notify subscribers" on upload to avoid early-velocity drag (8N7-vQ9qX4w, live walkthrough; causal claim overstated — the box only affects feed/notifications, not Browse).
- **Sources:** (8N7-vQ9qX4w)
- **Evidence:** WEAK-MEDIUM — real diagnostics, speculative remedy.
- **Relation:** NEW analytics diagnostic; low signal at current sub counts on all three channels.
- **Disposition:** FILE — revisit when any channel passes ~10K subs.

### 7.7 Cross-channel collab-post seeding
- **Mechanics:** Seed a smaller sibling channel by collab-posting its first video with the big channel, exposing main-channel fans without requiring subscription (Eb8wlFawjTw, describing Hormozi's second-channel launch, Sept 2025). Homepage flooding: enough sibling-channel volume that a fan's home feed saturates (Eb8wlFawjTw, observation of the Hormozi ecosystem).
- **Sources:** (Eb8wlFawjTw)
- **Evidence:** WEAK-MEDIUM — observed on Hormozi's ecosystem, not tested by the narrator.
- **Relation:** NEW — no playbook module covers cross-channel seeding; directly usable between Rexcaped and Prehistoric POV (the Omega-Rex-variant practice already moves content between them).
- **Disposition:** TEST: verify the collab-post feature exists on our channels; if yes, use it on the next cross-channel variant upload.

### 7.8 No low-intent self-promotion, no fake engagement
- **Mechanics:** Sharing your videos to Reddit/social is "almost always a net loss": low-intent clickers tank retention now, then ignore the next video in their feed, dragging CTR later; promote only to precisely-targeted niche audiences. Sub4sub/bought views are easily detected and destroy account trust (q0G-FzS6uxk, mechanism argued, no data).
- **Sources:** (q0G-FzS6uxk)
- **Evidence:** WEAK-MEDIUM — mechanism-consistent, unmeasured.
- **Relation:** NEW promotion rule; nothing in the playbook covers seeding.
- **Disposition:** ADOPT as default (don't blast links); niche-targeted shares only.

### 7.9 Scheduled channel-audit automation
- **Mechanics:** A scheduled weekly AI audit (Monday 9am) returning executive diagnosis, per-format breakdown, working/underperforming lists, 5-priority action plan, best video opportunities (8N7-vQ9qX4w, sample output shown via VidIQ's paid plugin — the pattern is clonable free with a Claude Code scheduled task + Studio browser automation).
- **Sources:** (8N7-vQ9qX4w)
- **Evidence:** MEDIUM — output shown; value depends on upload volume.
- **Relation:** NEW ops pattern; the paid tool is blocked by hard rule, the $0 clone is not.
- **Disposition:** FILE until ≥2 channels have steady uploads; then build as a Claude Code scheduled task.

### 7.10 Per-video attribution parameters on description links
- **Mechanics:** Append ?video=<ytid> to every description link so conversions trace to the specific video and revenue-per-view is computable outside Studio (Eb8wlFawjTw — self-demonstrated: all three links in that video's own description carry ?video=Eb8wlFawjTw).
- **Sources:** (Eb8wlFawjTw)
- **Evidence:** MEDIUM — trivially verifiable mechanic.
- **Relation:** NEW for bizdoc sponsor links (Incogni/DeleteMe/Proton/NordVPN descriptions).
- **Disposition:** ADOPT for all bizdoc description links from video 1 (free, compounds later).

### 7.11 Rejected distribution schemes (catalogued, with the decoded tell)
- **Mechanics:** Loop-stream "24/7 live" watch-hour farming with subscribers-only chat and message delay (eF75ZffgsUk — one true fact inside it: live watch hours DO count toward YPP's 4,000 while public); cloud-phone multi-account farms + purchased region-registered accounts (KxsasFMMPpA, DuoPlus sponsor segment); multi-account warm-up/IP-rotation protocols and cloaked deep links (Z5Wn63kLhpI); buying aged/premonetized channels (0SPqPnpQsWE "from the market"; 54UTQ2kFhuA — headstartchannels.com is his own product; PtO7jd8L2xs started on one; 8KXlxAKOTdE partially warns against them) — account trading violates YouTube ToS and purchased channels carry termination risk; @mention-a-big-channel and similar folk levers (eF75ZffgsUk).
- **Sources:** (eF75ZffgsUk) (KxsasFMMPpA) (Z5Wn63kLhpI) (0SPqPnpQsWE) (54UTQ2kFhuA) (PtO7jd8L2xs) (8KXlxAKOTdE)
- **Evidence:** n/a — catalogued for pattern recognition, not adoption.
- **Relation:** CONTRADICTS ToS-compliance posture and the inauthentic-content risk register across the board.
- **Disposition:** IGNORE all; retain one decoded heuristic — treat any "monetized in days" claim as a purchased-channel tell when scoring a source's credibility (0SPqPnpQsWE policy note).

---

## 8. MONETIZATION MECHANICS & CHANNEL ECONOMICS

### 8.1 Runtime → RPM (mid-roll economics)
- **Mechanics:** ~34-min video showed ~$6 RPM vs ~$3 on a ~25-min video, attributed to more mid-roll slots (BePppCvXC-k, revenue tab shown on screen — the corpus's best RPM receipt). Long runtimes raise RPM (Oi3nSYYQ6sM — NexLev ESTIMATES only, his "$15" is a guess; zJmYdcvwY1Y — his own estimates; 8N7-vQ9qX4w's make-it-longer-than-90%-of-topic-winners rule, 19-40-min examples shown; 3MPSrpIOpAo's 25-30-min→2h+ ladder). COUNTERWEIGHT: padding for length conflates absolute watch time with AVD and risks the retention curve (ipbnR92Elxg's "longer than competitors" and 8KXlxAKOTdE's "1.5x competitor length" are CONTRADICTED by `retention_delivery.json`'s retention-first stance; 3MPSrpIOpAo's watch-time padding likewise rejected).
- **Sources:** (BePppCvXC-k) (Oi3nSYYQ6sM) (zJmYdcvwY1Y) (8N7-vQ9qX4w) (3MPSrpIOpAo) (ipbnR92Elxg) (8KXlxAKOTdE)
- **Evidence:** MEDIUM-STRONG for the mid-roll effect (one real revenue tab + consistent estimates); the padding corollary is rejected.
- **Relation:** CONFIRMS the bizdoc format choice (23.4-min doc already exploits mid-roll economics, inside the shown winner range); length remains story-driven per the 95+ script bar.
- **Disposition:** CONFIRM; when two cut lengths are equally strong editorially, prefer the longer.

### 8.2 High-RPM niche positioning
- **Mechanics:** Finance/legal pays ~10x general entertainment — "30K views in this niche could be worth 300K in a low-CPM niche" (tICnK3Qb2k8, asserted); long-form finance/business POV maximizes RPM (Ao_d-uaMJvk, no screenshots); niche RPM dashboards for entry decisions (8Mx2m0djgTA — tool marketing data "from 26 channels"; Oi3nSYYQ6sM, ipbnR92Elxg, 8KXlxAKOTdE — ALL NexLev/tool-ESTIMATED figures like $5-$11 RPM, never verified against real analytics; ipbnR92Elxg's headline $27,875 is views × an estimate its own narrator disowns).
- **Sources:** (tICnK3Qb2k8) (Ao_d-uaMJvk) (8Mx2m0djgTA) (Oi3nSYYQ6sM) (ipbnR92Elxg) (8KXlxAKOTdE)
- **Evidence:** MEDIUM directionally; every specific RPM figure is tool-estimated/unverified — label accordingly wherever reused.
- **Relation:** CONFIRMS the bizdoc thesis ($10-25 RPM public-data business stories); RPM screening already lives in the topic scorer's economics framing.
- **Disposition:** CONFIRM.

### 8.3 Pre-YPP revenue: day-one affiliate with high-ticket criterion
- **Mechanics:** Before YPP, attach an affiliate paying $100+/sale (worked example: $297 product, 35% commission, 50% after 3 sales/mo × 2 months = $150/sale) with FTC "this description contains affiliate links" disclosure; keep backup affiliates (LGYiPA5SKvw, terms + math + generated disclosure shown). Four-layer stack: high-ticket affiliate/course primary ($100-500/sale), recurring software affiliates secondary, AdSense as "extra" ($3-20 RPM), sponsorships volatile bonus (TvJhpOxFRsE, asserted). Revenue-per-view as the metric for conversion content, not views (Eb8wlFawjTw — 7.7M views=$13K AdSense (~$1.7 RPM) vs 20K views="$100K+" claimed, unverified).
- **Sources:** (LGYiPA5SKvw) (TvJhpOxFRsE) (Eb8wlFawjTw)
- **Evidence:** MEDIUM on mechanics; all revenue outcomes self-reported.
- **Relation:** CONFIRMS the bizdoc sponsor plan (Incogni/DeleteMe/Proton/NordVPN mid-rolls); NEW gap it exposes: the creature channels have NO pre-YPP revenue plan.
- **Disposition:** TEST: one compliant high-ticket affiliate fit-check for Rexcaped/PPOV (desk research only; no channel changes until a real fit exists).

### 8.4 YPP threshold mechanics (operational facts)
- **Mechanics:** 4,000 public watch hours + 1,000 subs; the sub gate is the usual bottleneck for viral long-form (BePppCvXC-k, lived on screen at 999 subs). Studio watch-hour analytics lag ~5 days ("I really have like 10,000 hours but it showed 800"). On acceptance you can retroactively "monetize all" existing uploads, but views accrued BEFORE acceptance are never paid — apply the moment thresholds are hit, ideally before an expected hit (BePppCvXC-k: "40K watch hours that are not monetized"). Live/premiere watch hours count while content stays public (eF75ZffgsUk). Promotions benchmark: $200 ≈ 1,419 views + 380 subs ($0.53/sub); the only arguably-justified paid use is buying the final subs when watch hours are already banked (ROPkHP8jpW0, setup + results on screen; conflicts with the no-spend rule → owner decision only).
- **Sources:** (BePppCvXC-k) (eF75ZffgsUk) (ROPkHP8jpW0)
- **Evidence:** STRONG — Studio walkthroughs for the core mechanics; the Promotions benchmark is n=1.
- **Relation:** NEW channel-ops facts; nothing in the playbook covers YPP timing.
- **Disposition:** ADOPT the apply-immediately rule + 5-day-lag awareness for prehistoric_pov and bizdoc; the paid-subs edge case goes to the owner only if a channel strands watch hours behind the sub gate.

### 8.5 Membership smart-pricing (Aug 17 deadline)
- **Mechanics:** From Aug 17, YouTube auto-applies per-country "smart pricing" to channel-membership tiers for NEW non-US members unless prices are set manually (Studio→Earn→Memberships); existing members grandfathered; 12-month price-lock exemption (CQWfqKGFoPM, attributed to YouTube creator liaison Rene Ritchie, Studio path shown). PPP-localized pricing likely grows international member counts (stated reasoning, no data).
- **Sources:** (CQWfqKGFoPM)
- **Evidence:** MEDIUM-STRONG for the factual change (named-source news, verifiable in Studio).
- **Relation:** NEW, dormant — no channel has YPP or memberships yet.
- **Disposition:** FILE in the future monetization checklist.

### 8.6 AI-vs-freelancer production economics + clone-capture planning number
- **Mechanics:** Freelancer stack ≈$190/video ($50 script + $100 edit + $25 VO + $15 thumb; $2,280/mo at 3×/wk) vs ~$10/video AI (TvJhpOxFRsE, on-screen arithmetic); ~$5/video at volume (54UTQ2kFhuA); $15-30 outsourced edits (8KXlxAKOTdE); $40-50 sync-only edits (1ywvAeaFojo — a REGRESSION vs the $0 FFmpeg engine). Expected capture when faithfully cloning a proven format: 25-30% of the original's views; only clone Shorts channels doing 100M+ views/month (PtO7jd8L2xs, self-reported).
- **Sources:** (TvJhpOxFRsE) (54UTQ2kFhuA) (8KXlxAKOTdE) (1ywvAeaFojo) (PtO7jd8L2xs)
- **Evidence:** MEDIUM — consistent price points across sellers; capture rate is one operator's claim.
- **Relation:** CONFIRMS the pipeline's ~$0 marginal-cost advantage; the 25-30% capture expectation is a NEW planning heuristic for clone-format projections (`viral_recreation_spec.md` context).
- **Disposition:** CONFIRM economics; FILE the capture rate labeled self-reported.

### 8.7 Commerce-platform mechanics (off-strategy, catalogued)
- **Mechanics:** TikTok Shop GMV Max routes brand ad budgets to highest-converting videos regardless of account size; product screen: $50-60+ price, ~10% commission, <200 creators/30 days, ad-backed top videos; ~300 videos/30 days spam ceiling (r81ImbWaxEE, Kalodata walkthrough shown, revenue unverified). POD merch dropped into viral-post comments ($14.50-margin journals, "you guys loved this so I put it on a shirt") (KZKFlik4M8I, sponsor segment). Notion-AI vibe-coded Etsy products (9iP588aMFBc).
- **Sources:** (r81ImbWaxEE) (KZKFlik4M8I) (9iP588aMFBc)
- **Evidence:** MEDIUM on mechanics; irrelevant to ad-RPM content channels.
- **Relation:** Maps to nothing in the playbook; possible far-future Rexcaped creature-merch idea only.
- **Disposition:** IGNORE now; revisit merch only post-scale.

---

## 9. PLATFORM RISK / ANTI-SLOP HYGIENE (cross-cutting; full detail in `synthesis/policy_dossier.md`)

### 9.1 Sameness — not AI usage — is the enforcement trigger
- **Mechanics:** Convergent testimony: AI voice/visuals per se pass YPP; "mass-produced" stylistic sameness is the stated rejection term — one rejected channel used a HUMAN voice; remedy that worked = delete lookalikes, change style, reapply (4xWQ_fHLGAc, secondhand but specific). YouTube's line restated accurately: AI as a tool is fine; 100% AI mass-produced zero-effort content → demonetization/ban; bans can PROPAGATE across channels sharing one AdSense account (YtpQSmu794k). Banned channels share spammy no-human-input profiles, not AI usage; safety recipe = own ideas, QC'd scripts, human input, real value (LGYiPA5SKvw). CEO blog quoted verbatim on "low-quality repetitive content"; partial human effort is NOT a safe harbor; unverified claim that Gemini reads whole-video context pre-distribution (q0G-FzS6uxk). "YouTube does not block AI content… it comes down to quality" (f-ufEhGtVpw, unsourced; CxwFu1nEsZQ same claim re AI voices, mid-2026; tICnK3Qb2k8: "some creators… getting demonetized" for slop-style AI use). The genre's own evasion behaviors — template rotation under enforcement pressure, watermark hiding, reused-clip laundering, account farms — are themselves confirmation the policy bites (PtO7jd8L2xs, 0SPqPnpQsWE, NlfmQpSaYMo, QfbGKfkGP8U).
- **Sources:** (4xWQ_fHLGAc) (YtpQSmu794k) (LGYiPA5SKvw) (q0G-FzS6uxk) (f-ufEhGtVpw) (CxwFu1nEsZQ) (tICnK3Qb2k8) (PtO7jd8L2xs) (0SPqPnpQsWE)
- **Evidence:** STRONG on the pattern (9 sources incl. one verbatim primary-source quote); individual anecdotes unverifiable.
- **Relation:** CONFIRMS the operation's #1-risk register and its named mitigations: clip-variety rule, measured edit grammar (variety is structural), 95+ human-directed scripts, owner voice, real-footage composites, template refresh (1.9).
- **Disposition:** CONFIRM posture; ADOPT the one NEW operational detail — keep channels on separate AdSense accounts where practical to contain ban propagation (owner decision).

### 9.2 Human-layer hedges that read as authored
- **Mechanics:** Strip baked-in text from image prompts; add all text as editor overlays — explicit hedge so "everything won't feel completely AI" (4xWQ_fHLGAc, ~200-prompt cleaning pass shown). Distinct/own voice as anti-fingerprint (6.18 cluster). Consistent narrator persona + direct-address intimacy makes faceless output read authored (Xf_J7kBzxvo analysis note). Owned non-human mascot + locked voice (LGYiPA5SKvw).
- **Sources:** (4xWQ_fHLGAc) (Xf_J7kBzxvo) (LGYiPA5SKvw) (CxwFu1nEsZQ) (TvJhpOxFRsE)
- **Evidence:** MEDIUM — practitioner logic, no enforcement counterfactuals.
- **Relation:** CONFIRMS FFmpeg overlay practice, fair-use transformative layers, thumbnail no-baked-text discipline, Dinoverse host-mascot pattern.
- **Disposition:** CONFIRM; text-as-overlay is already how the renderer works.

### 9.3 Fabrication = "deceiving the audience"
- **Mechanics:** Build scripts only on facts that happened; invented content treated as audience deception → demonetization or removal (zJmYdcvwY1Y, stated as a working rule; consistent with the July-2025 policy family — and an argument against his own transcript-rewrite tactic, rejected in 5.x).
- **Sources:** (zJmYdcvwY1Y)
- **Evidence:** WEAK-MEDIUM — one source, policy-consistent.
- **Relation:** CONFIRMS the public-data-only sourcing rule (SEC/DOJ/court filings) + `sources.json`.
- **Disposition:** CONFIRM.

### 9.4 Kids-content trap
- **Mechanics:** Nursery-rhyme/kids AI niches force Made-for-Kids designation (COPPA): personalized ads off, RPM collapses, comments disabled — omitted by every video pitching the niche (lDpOnE3VJVI analysis note; ylezKJG7rb8's 3/day kids-story pitch, same family).
- **Sources:** (lDpOnE3VJVI) (ylezKJG7rb8)
- **Evidence:** MEDIUM — COPPA mechanics are established platform fact; the pitches ignore them.
- **Relation:** CONFIRMS Prehistoric POV's existing not-for-kids positioning.
- **Disposition:** CONFIRM; never drift creature content toward kids-styling.

### 9.5 Distribution-side squeeze prediction
- **Mechanics:** Industry-adjacent prediction that undifferentiated faceless AI content gets "squeezed into oblivion" as feeds flood — identity/brand is the non-commoditizable asset (ZKsldrcO_fU, vidIQ, opinion). Viral AI entertainment as a commoditizing race to the bottom, maximally exposed to policy shocks (TvJhpOxFRsE). "The algorithm smells the AI slop" (Qsi9MeLh95Q, evidence-free).
- **Sources:** (ZKsldrcO_fU) (TvJhpOxFRsE) (Qsi9MeLh95Q)
- **Evidence:** WEAK-MEDIUM — predictions from sources with differing incentives, converging.
- **Relation:** Partially CONTRADICTS a naive faceless model; the operation's counters are already named — measured grammar, composite realism, POV format identity, cloned owner voice.
- **Disposition:** CONFIRM the mitigation path; standing argument for the quality-bar strategy over volume.

---

## APPENDIX — CROSS-CUTTING CONFLICTS LEDGER (both sides, with ids)

1. **Still-hold pacing:** 2.5s ceiling (Ao_d-uaMJvk) vs 1/3s (zJmYdcvwY1Y) vs 3s-instructed-but-5-7s-actual (LGYiPA5SKvw) vs 7-8s (f-ufEhGtVpw) vs 5-15s (Dmqz8opSHzE) vs measured 5-7s cuts (`editing.json`). → Measure competitors; the grammar method wins, not any guru number.
2. **Judgment window:** 24-48h CTR/AVD sequel-or-pivot read (ZKsldrcO_fU) vs week-1-is-noise/14-day patience on NEW channels (BePppCvXC-k, ROPkHP8jpW0, q0G-FzS6uxk, 9iP588aMFBc). → Reconcile: baseline-relative 24-48h reads only make sense on established channels; new channels get the patience doctrine (7.3).
3. **Volume vs craft:** daily uploads/$5 videos (54UTQ2kFhuA, Oi3nSYYQ6sM, ylezKJG7rb8) vs 100x-effort outlier-cloning (BePppCvXC-k) and the operation's quality bars. → Craft-side stands; volume survives only as "reps = data" (5.9).
4. **Length:** longer-raises-RPM with a real receipt (BePppCvXC-k) vs pad-for-length (ipbnR92Elxg, 8KXlxAKOTdE, 3MPSrpIOpAo) vs retention-first (`retention_delivery.json`). → Longer only when editorially equal (8.1).
5. **Voice:** distinct/own voice (CxwFu1nEsZQ, TvJhpOxFRsE, YtpQSmu794k) vs cast-to-match-incumbent (zJmYdcvwY1Y) vs clone-anyone (3MPSrpIOpAo — rejected as impersonation risk, Oi3nSYYQ6sM flags ban risk). → Distinct from the crowd, congruent with the genre (6.18).
6. **Thumbnails:** topic+length outrank thumbnails (8N7-vQ9qX4w) vs packaging-first corpus consensus (1.1) vs PSR-overrides-packaging on ESTABLISHED channels only (Xf_J7kBzxvo). → Keep packaging discipline; new channels have no parasocial capital to lean on.
7. **Editing automation:** "editing can't be automated" (zJmYdcvwY1Y) vs the Claude-Code edit cluster (vI4RdXMSq8c, TiycelzfzC0, oWkUwno6b0E) and the operation's own FFmpeg engine + watcher. → Demonstrably false; already automated here.
8. **Grok free tier:** "killed" (Qsi9MeLh95Q, description-sourced, unverified) vs the operation's working recipes as of last use. → VERIFY before the next i2v batch (6.15) — the highest-priority open check in this map.
9. **Ideation vs edit as growth lever:** ideation-beats-editing (54UTQ2kFhuA, 4xWQ_fHLGAc) vs edit-polish-wins (ROPkHP8jpW0, confounded). → Topic scorer stays the top gate; measured-grammar edit floor stays non-negotiable (3.7).
