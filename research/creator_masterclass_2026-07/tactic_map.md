# UNIFIED TACTIC MAP — 32-Video Masterclass Synthesis

Merged, deduplicated tactics from all 32 analyzed videos (see `analysis/COMBINED_INDEX.md`).
Every tactic cites source video ids. Relations map to the operation's existing systems BY NAME:
playbook modules (`playbook/editing.json`, `intros.json`, `scripting.json`, `titles_thumbnails.json`,
`retention_delivery.json`, `ideation.json`, `sources.json`), the measured
`research/edit_grammar_ruleset.md`, and `pipeline_v2/topic_scorer.py` (9 tests, GO=85+, all ≥65).

**Evidence-strength scale:** STRONG = 3+ independent videos and/or on-screen analytics/mechanics shown;
MEDIUM = 2 videos or 1 video with concrete demonstrated proof; WEAK = 1 video, asserted only.
A recurring caveat: most sources are affiliate/coaching funnels — mechanics were shown, revenue almost never was.

---

## 1. PACKAGING — TITLES / THUMBNAILS

### 1.1 Thumbnail-first production gate
- **Mechanics:** Conceive and RENDER the actual title + thumbnail before any production; if the best version is vague or you wouldn't click it, kill the whole video idea (q0G-FzS6uxk). "We always need to do the thumbnails first" as a standing rule (ipbnR92Elxg). Extreme form: generate the thumbnail hook TEXT first, then write the script from it, in one LLM thread carrying idea→script→title→tags→description (3MPSrpIOpAo). Score multiple titles/concepts before scripting (8Mx2m0djgTA).
- **Sources:** (ipbnR92Elxg) (q0G-FzS6uxk) (3MPSrpIOpAo) (8Mx2m0djgTA)
- **Evidence:** STRONG — 4 independent videos; live demos in 3; no retention data but mechanically cheap.
- **Relation:** CONFIRMS `topic_scorer.py` title_thumbnail + five_second_title tests; NEW wrinkle = physically render the real thumbnail pre-production as an ordering change (scorer currently scores the concept, not the artifact).
- **Disposition:** ADOPT the render-first ordering on Rexcaped V3 and bizdoc; kill topics whose thumbnail doesn't read at feed size.

### 1.2 Competitor-thumbnail style transfer via GPT image gen
- **Mechanics:** Screenshot a proven competitor thumbnail → paste into ChatGPT with your own hook text → get a new on-template thumbnail in the competitor's exact composition; iterate by sending the result back (3MPSrpIOpAo, live demo). Variant: meta-prompt from outlier screenshots with "target clickbait and CTR" (ipbnR92Elxg). Add "lower the quality of the image so it looks more realistic" as a prompt line; keep text OUT of the generation and add it later (ipbnR92Elxg).
- **Sources:** (3MPSrpIOpAo) (ipbnR92Elxg) (8KXlxAKOTdE)
- **Evidence:** MEDIUM — live demos in 2 videos; no CTR proof.
- **Relation:** NEW general mechanic vs the existing creature-specific thumbnail recipe (candid real-phone-photo, ONE focal point); quality-degrade line CONFIRMS that recipe. Hard-rule guard: no AI human faces.
- **Disposition:** TEST for bizdoc: 3 ColdFusion/HMW reference thumbnails + "Breaking the Law" hook text vs the hand-built draft.

### 1.3 Packaging adjacency — don't be "too original"
- **Mechanics:** Title/thumbnail/framing must be recognizably adjacent to channels the target audience already watches so the algorithm can classify you; put originality INSIDE the video body. If you can't name the channels your audience watches, the concept is broken (q0G-FzS6uxk). Model packaging only on already-proven winners in-niche (8KXlxAKOTdE). Formula deviation kills videos — a channel's one off-formula video flopped while on-formula ones hit; "squeeze the format" before diversifying (zJmYdcvwY1Y).
- **Sources:** (q0G-FzS6uxk) (8KXlxAKOTdE) (zJmYdcvwY1Y) (KZKFlik4M8I)
- **Evidence:** STRONG — 4 videos converge; zJmYdcvwY1Y shows an actual on/off-formula performance split.
- **Relation:** CONFIRMS `titles_thumbnails.json` (26 tactics) + `research/viral_recreation_spec.md` measured-recreation doctrine.
- **Disposition:** CONFIRM — already the operating method; cite as multi-source validation.

### 1.4 Title formula library: adversarial-curiosity + "POV:" prefix
- **Mechanics:** Legal/corporate stakes formulas: "Why companies pay millions to avoid trial", "What really happens when you get sued", "What your boss hopes you'll never learn" (tICnK3Qb2k8). "POV: you're the [role] when [stakes]" framing for POV channels (tICnK3Qb2k8); explicit "POV:" title prefix + "your life at every level of X" escalation format (Ao_d-uaMJvk). Celebrity/recognizable REAL faces in packaging "really boost click-through rate" (tICnK3Qb2k8).
- **Sources:** (tICnK3Qb2k8) (Ao_d-uaMJvk)
- **Evidence:** MEDIUM — formulas shown on real high-view third-party videos; no controlled data.
- **Relation:** NEW additions to the `titles_thumbnails.json` candidate pool; real-face thumbnail is compatible with the real-photos-only hard rule (bizdoc only).
- **Disposition:** ADOPT formulas into the title pool (bizdoc + Prehistoric POV); TEST one real-executive-photo focal thumbnail vs concept thumbnail on bizdoc.

### 1.5 Single-variable A/B protocol (Test & Compare)
- **Mechanics:** Title-only tests measure impressions/keyword effect; thumbnail-only tests measure CTR; NEVER combined title+thumbnail tests (confounded); sometimes 2 variants not 3 for a clean winner (8N7-vQ9qX4w, Studio walkthrough).
- **Sources:** (8N7-vQ9qX4w)
- **Evidence:** WEAK-MEDIUM — 1 video, but the feature is real and the variable-isolation logic is sound.
- **Relation:** NEW written testing-protocol rule for `titles_thumbnails.json`.
- **Disposition:** ADOPT as a written rule; apply when impressions justify a test.

### 1.6 No baked-in text in generated images
- **Mechanics:** Strip on-screen-text words from every image prompt before batch gen; add all text as editor overlays — human-added layers double as anti-"completely AI" hedge (4xWQ_fHLGAc, ~200 prompts/video cleaning pass). Same practice for thumbnails: text boxes added in Canva post-gen (ipbnR92Elxg).
- **Sources:** (4xWQ_fHLGAc) (ipbnR92Elxg)
- **Evidence:** MEDIUM — demonstrated workflow in both.
- **Relation:** CONFIRMS FFmpeg overlay practice + fair-use transformative-layer rule + thumbnail recipe discipline.
- **Disposition:** CONFIRM — already standard.

### 1.7 ANTI-TACTIC: thumbnails from video frames / "thumbnails don't matter"
- **Mechanics:** Ao_d-uaMJvk teaches picking a significant video frame as the thumbnail; 8N7-vQ9qX4w claims topic+length outrank thumbnails entirely.
- **Sources:** (Ao_d-uaMJvk) (8N7-vQ9qX4w)
- **Evidence:** WEAK — both asserted, contradicted by the broader packaging evidence base.
- **Relation:** CONTRADICTS thumbnail recipe ("gen from scratch, no video frames") and `titles_thumbnails.json`.
- **Disposition:** IGNORE both.

---

## 2. HOOKS & RETENTION

### 2.1 Stakes-first cold-open pattern family (worked examples)
- **Mechanics:** Five concrete shapes, all landing inside the first 10-15s: (a) hard date + forced default + "the wrong choice costs you" for policy-deadline stories (CQWfqKGFoPM); (b) counterfactual-deletion: "imagine waking up tomorrow and X no longer existed" → concrete stakes → direct question (NlfmQpSaYMo); (c) outcome + enumerated reveals ("three shocking hidden documents") + open mystery question (8Mx2m0djgTA); (d) killer-stat stack (200M subs / 9B views) then proof clip at 0:31 (lDpOnE3VJVI); (e) first-person mid-action cold open, 2 beats, twist line last (KxsasFMMPpA).
- **Sources:** (CQWfqKGFoPM) (NlfmQpSaYMo) (8Mx2m0djgTA) (lDpOnE3VJVI) (KxsasFMMPpA)
- **Evidence:** STRONG as pattern (5 videos); each individual shape WEAK (no retention data).
- **Relation:** CONFIRMS `intros.json` 0-15s micro-window; the five shapes are new WORKED EXAMPLES to cite in the module, not rule changes.
- **Disposition:** ADOPT as worked examples in `intros.json`; TEST counterfactual-deletion on the next bizdoc script.

### 2.2 Parasocial script stack (intimacy / continuity / reciprocity / persona)
- **Mechanics:** Four components (Xf_J7kBzxvo): (a) coffee-shop rule — flag any narration sentence you'd never say to a friend (demonstrated via MrBeast old-vs-new VO comparison); (b) ~10 direct-address "connection moments" per video (countable, lintable); (c) simulated-reciprocity templates — "So, you're probably thinking...", "you're not going to believe what happens next" — plus referencing real viewer comments in later videos; (d) persona/voice consistency across every video. Claim: task attraction (competence + information density) alone builds parasocial bonds — no face needed.
- **Sources:** (Xf_J7kBzxvo)
- **Evidence:** MEDIUM — 1 video, but the MrBeast VO comparison is directly demonstrated and the framework tracks real PSR literature.
- **Relation:** NEW mechanical adds to `scripting.json` (coffee-shop QA pass, address-density lint, comment referencing); persona-lock CONFIRMS locked-ElevenLabs-voice practice; task-attraction claim CONFIRMS the faceless bizdoc bet.
- **Disposition:** ADOPT the three free script-QA mechanics; run pre-TTS on every bizdoc script.

### 2.3 Stills-driven pacing numbers: 2.5s hold ceiling + 150-200 scene density
- **Mechanics:** In stills-driven long-form, NO static image holds >2.5s (i2v-animated scenes exempt, may hold longer); overlong holds named as the #1 reason POV channels flop (Ao_d-uaMJvk). Norm: 150-200 distinct visuals per 5-20-min video. CONFLICTING density numbers across sources: 1 img/2.5s (Ao_d-uaMJvk) vs 1 img/3s → 100 images per 5 min (zJmYdcvwY1Y) vs 1 img/5-15s (Dmqz8opSHzE — violates the measured grammar unless internal motion adds cuts).
- **Sources:** (Ao_d-uaMJvk) (zJmYdcvwY1Y) (Dmqz8opSHzE)
- **Evidence:** MEDIUM — 3 videos give density budgets; none show retention data; 2.5-3s cluster is consistent, 5-15s is the outlier.
- **Relation:** NEW numeric extension of `edit_grammar_ruleset.md` (measured for clip-driven video) into stills-driven video; the 5-15s figure CONTRADICTS `editing.json` cuts-every-5-7s and is rejected.
- **Disposition:** TEST 2.5s ceiling + ~150-scene budget on Prehistoric POV (audit the published 8:07 video first); ignore the 5-15s density.

### 2.4 Curiosity-loop scripting from blended competitor references
- **Mechanics:** Feed ~5 top-video links across ≥2 channels + target length (8-14 min) to an LLM; get a retention-tactics breakdown of sources plus a hook/context script where every line opens a question answered later (4xWQ_fHLGAc). Variant: attach the top competitor transcript + outlier screenshot; ask for a script "optimized for AVD... that flows the exact same as the reference"; specify exact word count on the second pass because first drafts run short (ipbnR92Elxg).
- **Sources:** (4xWQ_fHLGAc) (ipbnR92Elxg)
- **Evidence:** MEDIUM — live generations shown in both.
- **Relation:** CONFIRMS `scripting.json` (curiosity loops) + `ideation.json` + measured-competitor methodology; ≥2-channel blending rule is a small NEW guard against single-source cloning.
- **Disposition:** CONFIRM; adopt the "blend ≥2 channels" guard when scripting from references.

### 2.5 Hook = most-rewritten section, congruent with packaging
- **Mechanics:** Rewrite the hook many times until it creates curiosity the video resolves; hook must be congruent with title/thumbnail or retention collapses; learn hooks by writing down exactly why YOU kept watching bigger creators (q0G-FzS6uxk).
- **Sources:** (q0G-FzS6uxk)
- **Evidence:** WEAK — asserted practice.
- **Relation:** CONFIRMS `intros.json` + reference deep-watch practice.
- **Disposition:** CONFIRM.

### 2.6 Length strategy — CONFLICTING claims
- **Mechanics:** Four length prescriptions: (a) make it ~1.5x the competitor's length (8KXlxAKOTdE, bare assertion); (b) length ≥90th percentile of topic winners, e.g. 19-40-min range shown (8N7-vQ9qX4w); (c) "longer video = more watch time = win" (ipbnR92Elxg, asserted); (d) length ladder 25-30 min pre-monetization → 2h+ after (3MPSrpIOpAo); (e) 35-40 min in mature niches as an RPM wedge, or stretch 10→12-13 min (zJmYdcvwY1Y, unverified RPM 4-5). All conflate absolute watch time with AVD%.
- **Sources:** (8KXlxAKOTdE) (8N7-vQ9qX4w) (ipbnR92Elxg) (3MPSrpIOpAo) (zJmYdcvwY1Y)
- **Evidence:** STRONG that the genre believes it; WEAK causally — zero retention data in any of the 5.
- **Relation:** Deriving length from measured topic winners CONFIRMS deep-watch practice (bizdoc's 23.4 min sits inside the shown 19-40 winner range); padding-for-length CONTRADICTS `retention_delivery.json` (retention-first pacing).
- **Disposition:** CONFIRM winner-derived length; IGNORE padding prescriptions.

### 2.7 Metaphor / save-share beat for short-form cuts
- **Mechanics:** Script structure Hook(3s) → Message → METAPHOR (a sticky aphorism engineered to be screenshotted/saved — "the video is the metaphor") → conclusion that loops to the opening line so "the video never ends" (E_CIP98ufto). Rationale: FB/engagement-ranked surfaces reward saves/shares over completion.
- **Sources:** (E_CIP98ufto)
- **Evidence:** WEAK-MEDIUM — structure shown in a finished reel; no analytics tying saves to distribution.
- **Relation:** NEW selection lens for shorts cuts (not in `retention_delivery.json`); hook/loop halves CONFIRM `intros.json`.
- **Disposition:** ADOPT as the selection rule when cutting bizdoc shorts: the aphorism beats ("fines are a line item") ARE the shorts, with loop endings.

---

## 3. EDIT GRAMMAR & PACING (long-form)

### 3.1 Cut-cadence convergence: 4-7s clips
- **Mechanics:** Independent convergence on the measured grammar: generation constrained to exactly 4s or 6s clips, 4-8 clips per ~30s chapter (TiycelzfzC0 build prompt); a guru's own "change visuals every 3s" instruction was ignored by his pipeline — output ran 5-7s and shipped anyway (LGYiPA5SKvw); i2v models have a ~5s clip-length floor, so faster pacing must come from cutting generated clips in post (LGYiPA5SKvw).
- **Sources:** (TiycelzfzC0) (LGYiPA5SKvw) (Dmqz8opSHzE — 5-8s shots in demo)
- **Evidence:** STRONG — 3 videos' demos independently land in the 4-7s band.
- **Relation:** CONFIRMS `editing.json` cuts-every-5-7s and `edit_grammar_ruleset.md`; the 3s round number is guru folklore that even its promoter didn't hit.
- **Disposition:** CONFIRM — trust measured grammar over round numbers.

### 3.2 Last-frame continuity chaining for i2v sequences
- **Mechanics:** Feed clip N's FINAL frame as the i2v start image for clip N+1 so multi-clip sequences read as one continuous shot. Three demonstrated variants: Flow "add to prompt" / copy-video-frame + Ctrl+V (32DLRsFiXZY, live); Flow save-frame → three-dots → "animate" (sMo5RT_dPxc, 4 chained demo scenes); chained STILLS — scene N's image generated using scene N-1's output image as reference so accumulated state (damage, renovation progress) carries forward (6WDvO0Lu1sY). Port to our stack: FFmpeg last-frame extract (`-sseof -0.1`) → next Grok Imagine input still via the clipboard-upload recipe.
- **Sources:** (32DLRsFiXZY) (sMo5RT_dPxc) (6WDvO0Lu1sY)
- **Evidence:** STRONG — 3 independent videos, all with live UI demos of working chains.
- **Relation:** NEW capability for the ChatGPT-stills → Grok i2v workflow; scoped guard: overuse on adjacent beats CONTRADICTS the clip-variety rule (distinct vantage per beat) — apply only within continuous-action pairs and POV runs.
- **Disposition:** TEST one 3-clip chained POV sequence (Prehistoric POV) and one within-beat action chain (Rexcaped); frame-strip QA both.

### 3.3 Reference-image conditioning / character consistency stack
- **Mechanics:** Five converging mechanisms: (a) multi-angle character TURNAROUND SHEET as the persistent reference asset, edited via text in ChatGPT (6WDvO0Lu1sY); (b) ONE fixed style-reference image passed explicitly with EVERY still generation for cross-shot style lock (TiycelzfzC0); (c) hero-image re-uploaded as reference on every subsequent stage prompt (lL9gjPw5yjg); (d) verbatim character-description block injected into all 15 scene prompts (NA0AOlCmelQ); (e) style lock extracted FROM a competitor frame — send Claude a frame, have it write the style descriptor, prepend to every prompt (zJmYdcvwY1Y); (f) Flow character-icon anchoring per scene (lDpOnE3VJVI).
- **Sources:** (6WDvO0Lu1sY) (TiycelzfzC0) (lL9gjPw5yjg) (NA0AOlCmelQ) (zJmYdcvwY1Y) (lDpOnE3VJVI)
- **Evidence:** STRONG — 6 videos, multiple live demos with visibly consistent output.
- **Relation:** CONFIRMS the consistency-guarantee/provenance system and style_bands.json + gate_style.py need; NEW details = turnaround-sheet format and explicit per-still reference passing (vs thread-context reliance) — feeds the AMBER reference_images roadmap.
- **Disposition:** TEST turnaround sheet for one approved Rexcaped creature (measure via existing consistency gate); ADOPT explicit per-still style-reference attachment for Prehistoric POV series.

### 3.4 0.25s i2v head-trim
- **Mechanics:** Trim exactly the first 0.25s off every generated i2v clip before concatenation — removes the static/artifact first-frame moment common to i2v models (TiycelzfzC0, specified verbatim in a working build prompt). Cruder cousin: review each clip and cut the broken opening wherever it "starts looking normal" (6WDvO0Lu1sY).
- **Sources:** (TiycelzfzC0) (6WDvO0Lu1sY)
- **Evidence:** MEDIUM — 2 videos; TiycelzfzC0's demo output visibly clean.
- **Relation:** NEW parameter for the FFmpeg assembly step / `rexcaped_edit_engine.py`; complements frame-level QA.
- **Disposition:** ADOPT after a frame-strip check confirms Grok clips show the artifact.

### 3.5 Timestamp-conditioned i2v prompts (motion event on the word)
- **Mechanics:** Embed the second at which a key VO word lands into the video-gen prompt itself ("in a 6s clip, if 'door' is said at 3s, include that in the video prompt") so the motion event fires on the word; use only for prominent events (TiycelzfzC0 — demo shows a money-loop animation landing on "loops in a circle").
- **Sources:** (TiycelzfzC0)
- **Evidence:** MEDIUM — 1 video but demonstrated in output.
- **Relation:** NEW extension of `edit_grammar_ruleset.md` cut-on-turn-words; verifiable with the existing `extract_motion_events.py` ship-gate; word times already available from WhisperX.
- **Disposition:** TEST on one cut-on-turn-word Rexcaped beat — one clip proves whether Grok honors in-clip timing.

### 3.6 SAM 2 multi-element segmentation for layered composites
- **Mechanics:** Send each still to Meta's SAM 2 → folder of separated elements per shot → animate elements individually (slide-ins, staggered entrances, pendulum idle motion so nothing is static); segmentation imperfect — keep key pieces, discard fragments (Dmqz8opSHzE). Open weights run locally on the M5 at $0 (no FAL needed).
- **Sources:** (Dmqz8opSHzE)
- **Evidence:** MEDIUM — per-shot element folders and keyframe animation shown on screen.
- **Relation:** NEW upgrade to the layered-composite engine (rembg = single cutout; SAM 2 = multi-element): parallax Ken Burns for bizdoc, BETWEEN-layer creature placement (partial occlusion by foreground) for Rexcaped.
- **Disposition:** TEST local SAM 2 on 3 breaking_law stills + one Spino/Lagos composite — one afternoon, $0.

### 3.7 Vignette-spotlight tracked attention guide
- **Mechanics:** Full-frame black layer → inverted circle mask → feather ~21, opacity ~70% → keyframe mask position every few frames to track the subject (QfbGKfkGP8U, built live with exact values).
- **Sources:** (QfbGKfkGP8U)
- **Evidence:** MEDIUM — complete on-screen build with settings.
- **Relation:** NEW concrete implementation for `editing.json` "attention guides"; portable to the FFmpeg renderer.
- **Disposition:** ADOPT into the FFmpeg attention-guide kit.

### 3.8 SFX economy: small palette, sound-on-cut confirmed
- **Mechanics:** An entire viral Short used only 3 distinct SFX — whooshes on cuts/zooms (speed-matched to motion, mixed quiet), one flash hit, one end "ding" on the payoff (QfbGKfkGP8U). Also: keep clip-NATIVE model-generated SFX in at low volume (~-20dB) under VO instead of muting, music on top (TiycelzfzC0).
- **Sources:** (QfbGKfkGP8U) (TiycelzfzC0)
- **Evidence:** MEDIUM — both demonstrated in working edits.
- **Relation:** CONFIRMS `edit_grammar_ruleset.md` sound-on-every-cut, with nuance (reused small palette, not variety); low-volume clip audio is NEW and must NOT override bizdoc `clip_audio:"mute"` (fair-use/VO-integrity reasons).
- **Disposition:** TEST 3-SFX palette on shorts cuts; TEST low-volume native SFX on one Rexcaped beat.

### 3.9 Inter-video template rotation (edit-fingerprint variation)
- **Mechanics:** Practitioners in the template-farm trenches independently rotate their edit templates to dodge repetitive-content detection: "try not to work on the same template" per upload (0SPqPnpQsWE); change the caption template (colors/shape/background) roughly every 10 videos because identical templates "could get demonetized" (PtO7jd8L2xs); vary effects between videos to avoid sameness (E_CIP98ufto).
- **Sources:** (0SPqPnpQsWE) (PtO7jd8L2xs) (E_CIP98ufto)
- **Evidence:** STRONG as a practitioner-consensus signal (3 independent operators evading the same enforcement); no controlled data.
- **Relation:** NEW — extends the intra-video clip-variety rule (`edit_grammar_ruleset.md` / `rexcaped_edit_engine.py`) to INTER-video variation; the edit engine could otherwise stamp identical grammar on every upload.
- **Disposition:** TEST: diff Rexcaped V1 vs V2 edit fingerprints with the existing `extract_motion_events.py` (cut density, montage placement, music/SFX pattern) before V2 ships.

### 3.10 VO-first, word-timestamp-driven assembly
- **Mechanics:** Generate VO first; get word-level timestamps (ElevenLabs STT JSON or Whisper); beat boundaries and shot durations come from real audio timing; pass each beat's exact duration into the generation call so clips arrive pre-timed (Dmqz8opSHzE, TiycelzfzC0); files named by timestamp so assembly is sort-by-name (4xWQ_fHLGAc); VO on the timeline first, visuals placed to it (NlfmQpSaYMo, E_CIP98ufto, zJmYdcvwY1Y).
- **Sources:** (Dmqz8opSHzE) (TiycelzfzC0) (4xWQ_fHLGAc) (NlfmQpSaYMo) (E_CIP98ufto) (zJmYdcvwY1Y)
- **Evidence:** STRONG — 6 videos; the genre's entire working method.
- **Relation:** CONFIRMS the WhisperX → `realign_paper_edit.py` → paper-edit → FFmpeg architecture (ours is word-level and automated; theirs are manual approximations). Duration-specified generation CONFIRMS AMBER/VACE frame-count gen.
- **Disposition:** CONFIRM — the operation is ahead of every version shown.

### 3.11 Comedy-via-edit for a dry narrator
- **Mechanics:** A serious narrator can build social attraction purely through comedic editing choices — the edit supplies likability the delivery lacks (Xf_J7kBzxvo, asserted).
- **Sources:** (Xf_J7kBzxvo)
- **Evidence:** WEAK.
- **Relation:** NEW candidate for `editing.json` energy-variation module.
- **Disposition:** TEST one dry-wit gag beat in the next bizdoc video; judge by that segment's retention curve.

---

### 3.X Matched-zoom transition (logged, not adopted)
- **Mechanics:** end clip N on a keyframed zoom-out whose end state matches the zoom-in start state of clip N+1, so consecutive clips read as one continuous camera move (6WDvO0Lu1sY; feasible in the FFmpeg Ken Burns path).
- **Sources:** (6WDvO0Lu1sY)
- **Relation:** NEW — but unmeasured in any reference corpus.
- **Disposition:** IGNORE until measured — the style gate blocks unmeasured transitions by design; revisit only if a top-performer teardown in `research/edit_grammar_ruleset.md` ever shows it.

## 4. SHORTS & SHORT-FORM MECHANICS

### 4.1 AVD hack: loop shorter than its read-time text
- **Mechanics:** Build a Short from a 5-8s visual loop + on-screen text that takes 25-28s to read (+ tweet-reaction UI element); viewers pause/loop to finish reading, pushing AVD past 100%. Shown analytics: 7s video, 6M views, 86% stayed-to-watch, 28s AVD (~400%) (PtO7jd8L2xs).
- **Sources:** (PtO7jd8L2xs)
- **Evidence:** MEDIUM-STRONG — single source but a concrete, internally consistent analytics panel matching known Shorts behavior.
- **Relation:** NEW — no Shorts module exists in any playbook file; would seed a Shorts edit-grammar annex to `edit_grammar_ruleset.md`.
- **Disposition:** TEST one Short per creature channel from OWNED composites (6-8s loop + 20-25s caption); zero copyright exposure.

### 4.2 Shorts ship-gate numbers
- **Mechanics:** Stayed-to-watch ≥75-80% AND AVD ≥100% reliably produce distribution; on Shorts, per-video metrics matter far more than niche competition or channel identity — viewers don't register channel names while scrolling (live scroll demo) (PtO7jd8L2xs).
- **Sources:** (PtO7jd8L2xs)
- **Evidence:** MEDIUM — same analytics panel + demo.
- **Relation:** NEW metric thresholds; same gate-before-ship philosophy as the motion-event ship-gate / style gate.
- **Disposition:** ADOPT as the recorded ship-gate numbers for any Shorts lane.

### 4.3 Shorts as multi-surface distribution (the operation's biggest gap)
- **Mechanics:** Shorts surface on the homepage feed, YouTube search, AND Google SERPs; demonstrated 126K views on a Short vs 8K on the same-topic long-form (~15x) (8N7-vQ9qX4w). Shorts RPM is ~$0.05-0.07/1K (implied by 600M views ≈ $30-40K) — a discovery funnel, not revenue (QfbGKfkGP8U).
- **Sources:** (8N7-vQ9qX4w) (QfbGKfkGP8U)
- **Evidence:** MEDIUM — live surface demos; RPM figure consistent with known rates.
- **Relation:** NEW — none of the 3 channels has a Shorts pipeline despite FFmpeg 9:16 crops being nearly free from existing composites.
- **Disposition:** ADOPT a Shorts-derivative step: crop 2-3 highest-scoring motion-event beats per long-form to 9:16; treat as discovery, not revenue.

### 4.4 Vertical caption grammar (text-commentary style)
- **Mechanics:** Caption hierarchy: first line bold+yellow (setup), body white, shock words red bold; minimal black background block; typewriter animation on reveals; captions tracked to the subject's head (motion-track or manual keyframes) (QfbGKfkGP8U). Two-tone yellow/white auto-caption template (KxsasFMMPpA). 2-4 word caption chunks (E_CIP98ufto). Implement via FFmpeg/ASS, not CapCut.
- **Sources:** (QfbGKfkGP8U) (KxsasFMMPpA) (E_CIP98ufto)
- **Evidence:** STRONG — 3 videos; full on-screen builds in 2.
- **Relation:** NEW — no vertical caption grammar exists in `edit_grammar_ruleset.md` or any playbook module.
- **Disposition:** ADOPT as the vertical caption spec for all Shorts experiments.

### 4.5 Shorts clip rhythm 4-8-8-8-4
- **Mechanics:** ~28s Short = 4s in, three 8s middles, 4s out — short-in/long-middle/short-out (6WDvO0Lu1sY, applied per-clip in duration settings; no retention data).
- **Sources:** (6WDvO0Lu1sY)
- **Evidence:** WEAK.
- **Relation:** NEW (no Shorts pacing module); unmeasured.
- **Disposition:** TEST only if/when Shorts cutdowns are made; zero cost.

### 4.6 First-person 2-beat twist-story vertical format
- **Mechanics:** ~20-40s vertical: cold-open mid-danger in first person, 2 story beats, moral-twist closer; claimed 10-min production (KxsasFMMPpA, real demo clip; @Hisytstory claimed 234M profile views, unverified).
- **Sources:** (KxsasFMMPpA)
- **Evidence:** WEAK-MEDIUM — demo real, traction claims unverified.
- **Relation:** CONFIRMS the Prehistoric POV premise; NEW as a vertical format probe.
- **Disposition:** TEST one POV twist-story Short from existing i2v assets.

### 4.7 Facebook/Meta cross-posting lane
- **Mechanics:** FB content monetization is invite-only; experience-based trigger ≈ 5,000 followers + 60,000 minutes viewed (E_CIP98ufto, from 7 monetized pages); FB ranks on likes/comments/saves/shares, NOT watch time — design for save/share; posting cadence 3-15 reels/day claimed; image-post payout implied ~$0.08/1K views ($393 on a 5M-view post) (KZKFlik4M8I). E_CIP98ufto leaves Meta's AI label OFF — negative example (KZKFlik4M8I's analysis doesn't address the label).
- **Sources:** (E_CIP98ufto) (KZKFlik4M8I)
- **Evidence:** MEDIUM — 2 independent sources agree on invite mechanics; payouts unverified; the $0.08/1K figure independently reconfirms the high-RPM YouTube-long-form bet.
- **Relation:** NEW platform intel — no FB module exists anywhere in the playbook.
- **Disposition:** TEST zero-marginal-cost reposts of existing Rexcaped/POV verticals to one keyword-named FB page (organic only, AI label ON, kill at 30 days if reach is negligible).

---

## 5. NICHE SELECTION & IDEATION

### 5.1 Competitor-corpus → LLM demand-gap clustering
- **Mechanics:** Export titles + transcripts of 2+ proven channels (yt-dlp/DownSub free) → paste into Claude with a structured demand-mapping prompt → output: formats already executed, crowded vs fresh clusters, new topic clusters with high demand / low YouTube supply; more input data = better output (54UTQ2kFhuA, full live run shown). Extension — cross-platform arbitrage: have the LLM cite Wikipedia/news attention with no YouTube supply yet and launch the first video serving it (54UTQ2kFhuA).
- **Sources:** (54UTQ2kFhuA)
- **Evidence:** MEDIUM-STRONG — single source but demonstrated end-to-end on real data; free to replicate.
- **Relation:** NEW ideation FRONT-END for `ideation.json` + `topic_scorer.py` (the scorer scores topics; nothing currently GENERATES candidates systematically) + `sources.json` for the off-platform demand half.
- **Disposition:** TEST one afternoon: run it on the bizdoc calibration set (ColdFusion/HMW/Harris) and on the Spinosnack/Dinoverse corpus before Rexcaped V3; survivors feed the 9-test scorer.

### 5.2 Search-bar supply check (3+ replication threshold)
- **Mechanics:** Before locking a topic, search its exact framing on YouTube and count near-identical treatments; 3+ hits with no differentiated angle = drop it — the niche's hardcore fans have already seen it (8KXlxAKOTdE).
- **Sources:** (8KXlxAKOTdE)
- **Evidence:** MEDIUM — heuristic threshold, but mechanically checkable for free.
- **Relation:** NEW concrete evidence input for the `topic_scorer.py` originality / fresh_perspective / best_option tests.
- **Disposition:** ADOPT as a mandatory pre-scorer check; log the count as test evidence.

### 5.3 Quantified niche-entry thresholds
- **Mechanics:** Merged checklist across sources — enter only if: <5 smaller channels all getting views>subs; no incumbent >100K subs; no smaller channels failing; niche <~6 months old (8KXlxAKOTdE). For long-form cloning specifically: NEW niches <60 days (ideally <30), OR under-saturated (<10 channels posting long-form with real viewership), OR content-gap (creators at 300-500K views/video posting <1x/week) (PtO7jd8L2xs). For Shorts cloning: only clone channels doing 100M+ views/month; expect 25-30% view capture (PtO7jd8L2xs). Demand validation add-ons: Google Trends rising multi-year line + recent spike (tICnK3Qb2k8); Studio Research-tab "very high interest" gate (8N7-vQ9qX4w).
- **Sources:** (8KXlxAKOTdE) (PtO7jd8L2xs) (tICnK3Qb2k8) (8N7-vQ9qX4w)
- **Evidence:** MEDIUM — 4 videos give numbers; none show controlled data, but views>subs outlier logic matches how the Rexcaped niche was actually validated.
- **Relation:** NEW quantitative inputs for `topic_scorer.py` timeliness + blind_spot tests; views>subs CONFIRMS existing `ideation.json` practice.
- **Disposition:** ADOPT the thresholds into topic-scorer notes; Trends pull + Research-tab check as free pre-flight signals.

### 5.4 Monetization-survivor scan (demonetization tell)
- **Mechanics:** Before cloning a format, check 3-5 comparable channels for the pattern: every video hitting, then a sudden 3+ week upload stop = read as YPP denied/removed for that format ("if he wasn't given monetization, you definitely won't be") (zJmYdcvwY1Y).
- **Sources:** (zJmYdcvwY1Y)
- **Evidence:** WEAK-MEDIUM — one source, speculative mechanism, but independently observable field signal aimed at the operation's #1 risk.
- **Relation:** NEW niche-vetting pre-check alongside `topic_scorer.py` source_availability.
- **Disposition:** ADOPT; run retroactively on the Rexcaped creature-attack comp set.

### 5.5 Copy recent outliers, never the all-time #1 + comment mining
- **Mechanics:** Source demand from RECENT outlier videos (relative to channel size), not the competitor's most-cloned all-time hit (8KXlxAKOTdE); filter competitor content by outlier score / views-per-hour / newest, then read the outlier's COMMENTS to learn why it worked before scripting (8N7-vQ9qX4w); outliers-relative-to-subs with a format-feasibility filter — exclude channels whose format you can't execute (LGYiPA5SKvw).
- **Sources:** (8KXlxAKOTdE) (8N7-vQ9qX4w) (LGYiPA5SKvw)
- **Evidence:** STRONG — 3 videos converge; consistent with existing practice.
- **Relation:** CONFIRMS `ideation.json` outlier-first sourcing + reference deep-watch/loser triangulation; comment-mining is a small NEW add.
- **Disposition:** CONFIRM + ADOPT comment-mining into `ideation.json`.

### 5.6 Topic transfer / copy-with-a-twist pivot matrix
- **Mechanics:** Port a proven format across niches: "Why You Wouldn't Last 24 Hours in Medieval Times" → Stone Age; viral cats video → dogs (8KXlxAKOTdE, both pairs shown real). Systematic pivots when direct copying saturates: same topic/new idea, same idea/new topic, same idea/different format (long↔short), same content/different language (Spanish clone claimed 9M views) (PtO7jd8L2xs). Adjacent-topic remix: "How bad is McDonald's really" (4M) → Burger King (tICnK3Qb2k8). Differentiation-by-inversion: flip the protagonist gender in a proven format (3MPSrpIOpAo).
- **Sources:** (8KXlxAKOTdE) (PtO7jd8L2xs) (tICnK3Qb2k8) (3MPSrpIOpAo)
- **Evidence:** STRONG — 4 videos; real video pairs shown in 2.
- **Relation:** CONFIRMS `ideation.json` — this IS the Rexcaped model (Spinosnack/Dinoverse format cloning) and the `topic_scorer.py` fresh_perspective test; the 4-pivot enumeration is a cleaner articulation worth writing down.
- **Disposition:** CONFIRM; add the pivot matrix verbatim to `ideation.json`; TEST "Why You Wouldn't Last 24 Hours in the Cretaceous" on Prehistoric POV.

### 5.7 Portfolio rules: 80/20 double-down + test budget + typed failure diagnosis
- **Mechanics:** Once a format demonstrably works, 80% of uploads repeat it (new subject, same format), 20% test new formats, until it stops working (8KXlxAKOTdE). Test budget: post 10-15 videos per new channel before judging; then diagnose in order — NO impressions = distribution/channel problem; impressions but no clicks = packaging problem; clicks but no retention = edit problem (8KXlxAKOTdE). Judge channels on 30-day sustained-volume windows, never after 2 videos (54UTQ2kFhuA). 72-hour indexing window: 0 views for ~3 days on a new channel is normal classification delay — don't repackage before day 3 (q0G-FzS6uxk, own-analytics screenshot).
- **Sources:** (8KXlxAKOTdE) (54UTQ2kFhuA) (q0G-FzS6uxk)
- **Evidence:** MEDIUM — frameworks stated; the 72h delay has a real analytics screenshot; the diagnosis logic is standard analytics reasoning.
- **Relation:** NEW — no explicit portfolio ratio, kill criterion, or post-upload evaluation window exists in `ideation.json` or upload practice.
- **Disposition:** ADOPT all three: 80/20 rule once Rexcaped V2 has data; explicit kill criteria for Prehistoric POV; 72h no-evaluation rule on all new-channel uploads.

### 5.8 Ranked idea backlog with pre-built posting packages
- **Mechanics:** One batch session: mine competitors for outliers → ~30 ideas ranked by expected views, each with a posting package (title/description/tags/thumbnail brief), a 30-day calendar, and upload checklist — upload day becomes assembly-only (LGYiPA5SKvw, folder output shown on screen).
- **Sources:** (LGYiPA5SKvw)
- **Evidence:** MEDIUM — real generated output shown.
- **Relation:** NEW ops pattern — `topic_scorer.py` currently runs one topic at a time; complements the NEXT_VIDEO.md handoff practice.
- **Disposition:** ADOPT: one batch-scorer session per channel producing a ranked backlog + packages.

### 5.9 High-CPM lane validation (bizdoc thesis)
- **Mechanics:** Finance/legal content pays ~10x general entertainment ("30k views ≈ 300k low-CPM views") (tICnK3Qb2k8); long-form finance/business POV = max RPM (Ao_d-uaMJvk); 35-40-min mature-niche RPM wedge (zJmYdcvwY1Y); vs Shorts ~$0.05-0.07/1K (QfbGKfkGP8U) and FB images ~$0.08/1K (KZKFlik4M8I).
- **Sources:** (tICnK3Qb2k8) (Ao_d-uaMJvk) (zJmYdcvwY1Y) (QfbGKfkGP8U) (KZKFlik4M8I)
- **Evidence:** STRONG directionally (5 videos, two with concrete low-end comparators); exact RPMs unverified.
- **Relation:** CONFIRMS the bizdoc channel identity ($10-25 RPM public-data business stories).
- **Disposition:** CONFIRM — the lane choice is independently validated from five directions.

### 5.10 Negative niche archetypes (auto-fail list)
- **Mechanics:** Template-AI farm niches pitched across the corpus — BeamNG crash Shorts (32DLRsFiXZY), AI renovation (6WDvO0Lu1sY), miniature cooking ASMR (h6DB0e96GI0), wire/twig sculpture (lL9gjPw5yjg), Roblox cartoons + made-for-kids RPM collapse (sMo5RT_dPxc), Cocomelon kids rhymes + COPPA (lDpOnE3VJVI), USA-politics template news (0SPqPnpQsWE), fully-AI space-news slop (ipbnR92Elxg) — all single-variable prompt farms in the July-2025 inauthentic-content crosshairs, all evidenced only by third-party view counts.
- **Sources:** (32DLRsFiXZY) (6WDvO0Lu1sY) (h6DB0e96GI0) (lL9gjPw5yjg) (sMo5RT_dPxc) (lDpOnE3VJVI) (0SPqPnpQsWE) (ipbnR92Elxg)
- **Evidence:** STRONG as a pattern — 8 videos pitch structurally identical demonetization-prone niches.
- **Relation:** CONFIRMS the topic scorer's originality/blind_spot auto-fail logic and the AI-cardboard-DIY niche assessment.
- **Disposition:** ADOPT the archetype list into `ideation.json` notes as auto-reject; treat "monetized in days" claims as aged-channel-purchase proxies (0SPqPnpQsWE).

---

## 6. AI PRODUCTION STACK & TOOLING

### 6.1 Google Flow free-tier reality (conflicting claims resolved)
- **Mechanics:** CONFLICT: "completely free, unlimited images" (NA0AOlCmelQ); "totally free" incl. Omni Flash (NlfmQpSaYMo, h6DB0e96GI0, sMo5RT_dPxc); "no limit" Nano Banana 2 bulk stills at 4 images/request (zJmYdcvwY1Y) — vs the demonstrated 50 credits/day with fresh-browser refill shown on screen (32DLRsFiXZY) and the operation's own 2026-07-20 audit (Flow free = ~50 credits/day, watermarked Veo; Omni Flash = paid Gemini tier). The watermark-hiding steps taught in (NlfmQpSaYMo) (lDpOnE3VJVI) implicitly concede output is watermarked.
- **Sources:** (32DLRsFiXZY) (NA0AOlCmelQ) (NlfmQpSaYMo) (zJmYdcvwY1Y) (h6DB0e96GI0) (sMo5RT_dPxc) (lDpOnE3VJVI) (6WDvO0Lu1sY)
- **Evidence:** STRONG that the audit's numbers are right — the one on-screen credit counter (32DLRsFiXZY) matches it; "unlimited/free" claims are marketing.
- **Relation:** CONFIRMS reference_ai_cardboard_diy_niche tool audit; multi-account credit refills (32DLRsFiXZY, NA0AOlCmelQ, 3MPSrpIOpAo) are ToS abuse — never adopt.
- **Disposition:** Optionally TEST Flow free stills once (watermark/quality check, expect fail); IGNORE as a pipeline engine.

### 6.2 Free/cheap voice alternatives
- **Mechanics:** Google AI Studio TTS — paste script, pick voice, download; $0 with commercial-friendly terms (lL9gjPw5yjg). Gemini "create music" — paste lyrics, get a complete track in seconds (lDpOnE3VJVI, demoed). Gray-market resellers: AI33.pro $5/1M ElevenLabs credits (3MPSrpIOpAo), GenAIPro ~$22/1M (ipbnR92Elxg) — payment/ToS risk, IGNORE. Voice casting: match the incumbent's timbre/age; avoid the most popular stock voices (zJmYdcvwY1Y).
- **Sources:** (lL9gjPw5yjg) (lDpOnE3VJVI) (3MPSrpIOpAo) (ipbnR92Elxg) (zJmYdcvwY1Y)
- **Evidence:** MEDIUM — AI Studio TTS and Gemini music demoed; reseller quality/licensing unverifiable.
- **Relation:** NEW relevance because F5-TTS weights are CC-BY-NC (blocked for monetized use) and ElevenLabs is the paid path; Pixabay-music-only rule would need an explicit rights check before Gemini music ships. Voice-matching CONFIRMS Dinoverse ElevenLabs casting practice.
- **Disposition:** TEST AI Studio TTS A/B vs ElevenLabs on one POV script; TEST one Gemini music bed RIGHTS-GATED; IGNORE resellers.

### 6.3 Paid API aggregators as fallback only
- **Mechanics:** kie.ai one key covers Nano Banana Pro/2, Seedream 4.5, Grok Imagine, Seedance 2 (~$5 = 1,000 credits; ~$3.50 per 35s chapter; generate at 720p for cost control) (Dmqz8opSHzE, TiycelzfzC0). Higgsfield MCP gen backbone ≈ $41/video with motion vs $5-10 stills-only (LGYiPA5SKvw). Kling 2.6 at 5s/9:16 via Higgsfield (r81ImbWaxEE); Kling 3.0 (KxsasFMMPpA).
- **Sources:** (Dmqz8opSHzE) (TiycelzfzC0) (LGYiPA5SKvw) (r81ImbWaxEE) (KxsasFMMPpA)
- **Evidence:** STRONG on mechanics/costs (billing screens shown); irrelevant while $0 paths work.
- **Relation:** Blocked by the no-new-paid-APIs hard rule; local VACE-1.3B (~22min/beat, $0) + Grok i2v cover it. NEW datum: kie.ai exposes Grok Imagine via API — the designated fallback if browser-driven Grok ever breaks (ask owner first).
- **Disposition:** FILE as fallback; no spend.

### 6.4 Prompt-factory hygiene: batch-degradation guard + best-of-N variants
- **Mechanics:** Never generate 100 prompts in one request — prompts progressively compress; generate ~5 per request from pre-split script segments (zJmYdcvwY1Y); storyboards in batches of 5 scenes (NA0AOlCmelQ); scripts in 4 parts (NlfmQpSaYMo). Persistent LLM instruction sets (Claude Projects) emit 3 ready prompt variants per still in 30-60s for best-of-N generation (r81ImbWaxEE); one test video before batching 32 more (LGYiPA5SKvw).
- **Sources:** (zJmYdcvwY1Y) (NA0AOlCmelQ) (NlfmQpSaYMo) (r81ImbWaxEE) (LGYiPA5SKvw)
- **Evidence:** MEDIUM — degradation observed live in one demo; variant workflow shown on screen.
- **Relation:** Degradation guard = small NEW rule for conversational TSV/prompt passes; 3-variant best-of-N CONFIRMS the planned AMBER best-of-N; one-test-first CONFIRMS the PROTOTYPE BEFORE PLAN hard rule.
- **Disposition:** ADOPT the 5-per-request guard; TEST 3-variant best-of-N on one Spino/Lagos beat.

### 6.5 One-click end-to-end generators (category rejection)
- **Mechanics:** Noodle Tomato idea→90-min-video (8Mx2m0djgTA); Abacus AI ChatLLM $7 all-in-one (4xWQ_fHLGAc, E_CIP98ufto); Narration AI script+scenes (Ao_d-uaMJvk); Heclus clone-any-channel SaaS (Dmqz8opSHzE); Opus AI Producer black-box editor (Xf_J7kBzxvo); Edimakor (sMo5RT_dPxc). All affiliate-driven; none demonstrate the headline capability; all produce the templated output the July-2025 policy targets.
- **Sources:** (8Mx2m0djgTA) (4xWQ_fHLGAc) (E_CIP98ufto) (Ao_d-uaMJvk) (Dmqz8opSHzE) (Xf_J7kBzxvo) (sMo5RT_dPxc)
- **Evidence:** STRONG that the category exists and floods the market; zero evidence any of it beats the in-house pipeline.
- **Relation:** CONTRADICTS the FFmpeg engine + measured `edit_grammar_ruleset.md` + QA-gate moat; violates no-new-subscriptions.
- **Disposition:** IGNORE the category; treat the flood as validation that human-QA'd, composited, measured-grammar output is the defensible position.

### 6.6 Weekly AI channel-audit scheduled task
- **Mechanics:** Scheduled prompt (Mondays 9am): full channel audit → executive diagnosis, per-format breakdown, working/underperforming lists, 5-priority weekly action plan (8N7-vQ9qX4w, sample output shown; uses paid VidIQ MCP — clone free with Claude Code scheduled task + Studio browser automation).
- **Sources:** (8N7-vQ9qX4w)
- **Evidence:** MEDIUM — output shown; causal value unproven.
- **Relation:** NEW ops pattern; $0 clone path uses existing browser-automation recipes.
- **Disposition:** ADOPT the free clone once channels have enough data to audit.

### 6.7 Owned mascot / locked persona as commoditization hedge
- **Mechanics:** Consistent non-human character + locked voice as the channel "face" you own; audience connection survives as formats commoditize (LGYiPA5SKvw); persona consistency across videos as a relationship requirement (Xf_J7kBzxvo).
- **Sources:** (LGYiPA5SKvw) (Xf_J7kBzxvo)
- **Evidence:** MEDIUM — 2 videos; example channels shown.
- **Relation:** CONFIRMS Dinoverse-variant host + locked ElevenLabs voices; complies with no-AI-human-faces (non-human mascot).
- **Disposition:** CONFIRM; treat narrator/voice lock as a ship-gate item.

---

## 7. UPLOAD / DISTRIBUTION PRACTICE

### 7.1 Cold-start channel setup bundle (pre-launch window)
- **Mechanics:** Before first upload: pull ~5 high-search-volume niche keywords → LLM writes a keyword-rich channel description → paste the same keywords into Studio Settings > Channel keywords → set country=US → verify phone (4xWQ_fHLGAc; channel hit 1K subs/4K hrs in 9 days, mechanism asserted). Channel-level tags/description via LLM + set video language (3MPSrpIOpAo). Keyword-forward channel/page naming (KZKFlik4M8I, E_CIP98ufto). Feature-eligibility check: enable standard/intermediate/advanced (phone/ID verification) — gates >15-min uploads, custom thumbnails, appeals (eF75ZffgsUk; q0G-FzS6uxk claims advanced verification raises account trust). Trademark diligence: search YouTube name collisions + WIPO Global Brand Database before naming (LGYiPA5SKvw).
- **Sources:** (4xWQ_fHLGAc) (3MPSrpIOpAo) (eF75ZffgsUk) (q0G-FzS6uxk) (LGYiPA5SKvw) (KZKFlik4M8I) (E_CIP98ufto)
- **Evidence:** STRONG that the mechanics exist (Studio walkthroughs in 3 videos); WEAK on causal cold-start claims.
- **Relation:** NEW — no channel-setup/cold-start checklist exists in any of the 7 playbook modules. Directly relevant: bizdoc is pre-launch (the one window where this can matter) and Rexcaped is 1 video old. Note: bizdoc's 23.4-min video REQUIRES the >15-min feature unlock.
- **Disposition:** ADOPT the full bundle as a pre-launch checklist for bizdoc now, Rexcaped retroactively.

### 7.2 Auto-dub + explicit language setting
- **Mechanics:** Studio > Advanced settings > enable auto-dub; after upload set original language per video — YouTube generates translated audio tracks free (4xWQ_fHLGAc, shown on-screen). Related: non-English language arbitrage — Japanese/Korean niches carry high RPM with thin competition (3MPSrpIOpAo) — for this operation that points at dubs/multi-language audio tracks, not foreign-language channels.
- **Sources:** (4xWQ_fHLGAc) (3MPSrpIOpAo)
- **Evidence:** MEDIUM — feature real and shown; reach benefit unmeasured.
- **Relation:** NEW upload-settings item (no module covers it).
- **Disposition:** ADOPT with a quality gate: listen to one dubbed track before leaving it live on bizdoc's cloned voice.

### 7.3 Unlisted-first upload
- **Mechanics:** Upload unlisted → wait for HD processing + dub generation → flip public, so first viewers never hit low-res/dub-less versions (4xWQ_fHLGAc).
- **Sources:** (4xWQ_fHLGAc)
- **Evidence:** WEAK — plausible, unmeasured.
- **Relation:** NEW upload-practice line.
- **Disposition:** ADOPT (free, zero downside); add to the Rexcaped V2 upload package.

### 7.4 AI-disclosure decision per channel
- **Mechanics:** The altered/synthetic-content question appears in the publish/stream flow; "click No if not AI" advice (eF75ZffgsUk) is WRONG for AI-heavy channels; leaving Meta's AI label off fully-AI content (E_CIP98ufto) is the same negative example. Correct: Rexcaped + Prehistoric POV = YES (photoreal AI creatures in real footage); bizdoc documents a stance on cloned-voice VO pre-launch.
- **Sources:** (eF75ZffgsUk) (E_CIP98ufto) (TiycelzfzC0 — public-figure filter evasion as the aggravated case)
- **Evidence:** STRONG that the disclosure surface exists (shown in-UI); the negative examples define the line.
- **Relation:** NEW hard line for upload practice; directly de-risks the #1 platform exposure.
- **Disposition:** ADOPT: per-channel disclosure decision in every upload checklist; never copy the "click No" advice.

### 7.5 Account warm-up before first upload
- **Mechanics:** Never upload from a fresh account; warm with weeks of real watching/liking/commenting (q0G-FzS6uxk — weeks-to-months; 8KXlxAKOTdE — 1-2h/day for 1+ week; both frame it as "trust score", folk theory YouTube has never confirmed). Related dummy-account variant: a throwaway research account trained into a niche-scanner homepage (8KXlxAKOTdE, live demo — real and replicable).
- **Sources:** (q0G-FzS6uxk) (8KXlxAKOTdE) (0SPqPnpQsWE — aged-channel folklore version)
- **Evidence:** WEAK mechanism, STRONG genre consensus; behaviors are free.
- **Relation:** NEW upload-practice ritual; "trust score" itself stays unverified — act on the behavior, not the theory.
- **Disposition:** ADOPT for bizdoc pre-launch (free); TEST the dummy-account niche scanner when planning channel #4.

### 7.6 No low-intent self-promotion
- **Mechanics:** Never seed uploads on Reddit/social: low-intent clickers tank retention now, then ignore the next video in their home feed, dragging CTR later — a two-stage poisoning cascade (q0G-FzS6uxk). No sub4sub/bought views ever.
- **Sources:** (q0G-FzS6uxk)
- **Evidence:** WEAK-MEDIUM — mechanism coherent, no data.
- **Relation:** NEW standing rule (no seeding rule existed in the playbook).
- **Disposition:** ADOPT for all channels.

### 7.7 Never-do list (converging ToS/policy violations)
- **Mechanics:** (a) Buying aged/premonetized channels — the hidden engine behind every "monetized in days" claim; non-transferable accounts, termination risk (0SPqPnpQsWE, 54UTQ2kFhuA, PtO7jd8L2xs, 8KXlxAKOTdE half-warns). (b) Multi-account distribution/cloud-phone farms posting identical videos (KxsasFMMPpA); TikTok bans accounts >~300 videos/30 days that look low-quality (r81ImbWaxEE). (c) Free-tier multi-accounting via fresh browsers/temp mail (32DLRsFiXZY, NA0AOlCmelQ, 3MPSrpIOpAo). (d) Watermark concealment by scale-and-shift — SynthID survives cropping; hiding the visible mark only proves intent (NlfmQpSaYMo, lDpOnE3VJVI). (e) Loop-streaming a pre-recorded video as 24/7 "live" to farm YPP watch hours (eF75ZffgsUk; true fact inside it: live hours DO count toward the 4,000). (f) Delete-and-repost dead videos to a fresh channel — reused-content review risk (8KXlxAKOTdE). (g) Wholesale clip reuse with "transformative" text overlay (QfbGKfkGP8U) and DRM screen-recording of streaming services (PtO7jd8L2xs).
- **Sources:** (0SPqPnpQsWE) (54UTQ2kFhuA) (PtO7jd8L2xs) (8KXlxAKOTdE) (KxsasFMMPpA) (r81ImbWaxEE) (32DLRsFiXZY) (NA0AOlCmelQ) (3MPSrpIOpAo) (NlfmQpSaYMo) (lDpOnE3VJVI) (eF75ZffgsUk) (QfbGKfkGP8U)
- **Evidence:** STRONG — 13 videos independently teach (and half-admit the risks of) the same evasion stack.
- **Relation:** CONTRADICTS hard rules, fair-use armor, and the clean-monetization posture across the board.
- **Disposition:** CODIFY as the standing never-do list; a watermark check joins frame-level QA.

---

## 8. MONETIZATION MECHANICS & POLICY INTEL

### 8.1 "Mass-produced sameness — not AI voice — is the demonetization trigger" (the corpus's strongest convergent finding)
- **Mechanics:** Direct evidence chain: a YPP rejection citing the literal term "mass-produced" hit a channel with a HUMAN voice but identical-style videos; remedy that worked = delete lookalikes, change style, reapply — accepted (4xWQ_fHLGAc). YouTube CEO blog quoted verbatim on "low-quality repetitive content"; community-guidelines originality standard quoted; unverified-but-directional: Gemini reads whole-video context and suppresses low-effort AI pre-algorithm (q0G-FzS6uxk). Banned AI channels share spam patterns, not AI usage; human input + value = the safe recipe (LGYiPA5SKvw). Enforcement targets "AI slop usage patterns, not AI tools" (tICnK3Qb2k8). Practitioners rotate templates specifically to evade it (0SPqPnpQsWE, PtO7jd8L2xs — templates "could get demonetized", small animations added "to get away from Content ID"). Fabricated content = "deceiving the audience" → removal (zJmYdcvwY1Y). Cross-platform: TikTok's ~300/30-day low-quality cap (r81ImbWaxEE), Meta's unoriginal-content crackdown (E_CIP98ufto context).
- **Sources:** (4xWQ_fHLGAc) (q0G-FzS6uxk) (LGYiPA5SKvw) (tICnK3Qb2k8) (0SPqPnpQsWE) (PtO7jd8L2xs) (zJmYdcvwY1Y) (r81ImbWaxEE)
- **Evidence:** STRONG — 8 videos from 4 different angles (rejection anecdote, official quotes, evader behavior, cross-platform), all pointing the same direction.
- **Relation:** CONFIRMS the July-15-2025 inauthentic-content risk posture; ELEVATES the clip-variety rule + human overlays + measured per-video variation from editing preference to the primary YPP defense; motivates the NEW inter-video fingerprint diff (tactic 3.9).
- **Disposition:** ADOPT as doctrine: variety + visible human editorial layers + honest disclosure = the moat; log in the risk register.

### 8.2 YPP appeal path + human-editorial evidence packet
- **Mechanics:** A channel DECLINED at YPP review was monetized after "a banger appeal" (ipbnR92Elxg) — declines are appealable and appeals with a case succeed. Therefore: archive per-video human-editorial evidence (script version history, sourcing docs, verify_render QA reports) as a standing appeal packet.
- **Sources:** (ipbnR92Elxg)
- **Evidence:** WEAK-MEDIUM — one secondhand anecdote, but the appeal mechanism is real and the hedge is free.
- **Relation:** NEW upload/monetization practice; the operation's QA artifacts already exist — they just need archiving per video.
- **Disposition:** ADOPT: archive the paper trail per bizdoc video before launch.

### 8.3 YPP review mechanics (timing data)
- **Mechanics:** YPP review completed ~6 minutes after hitting requirements (suggests automated first pass); watch-hours took ~5 days to register toward eligibility; real first-upload-to-monetized timeline: 14 days (4xWQ_fHLGAc). Live-stream watch hours count toward the 4,000 while public (eF75ZffgsUk). Compliant fallback if hours stall: an honestly-labeled marathon premiere of published videos — never a single-video loop.
- **Sources:** (4xWQ_fHLGAc) (eF75ZffgsUk)
- **Evidence:** MEDIUM — specific enough to be experienced, not shown in-dashboard.
- **Relation:** NEW reference data for the monetization checklist.
- **Disposition:** FILE; plan for a ~5-day watch-hour reporting lag.

### 8.4 Pre-YPP revenue: high-ticket affiliate + FTC disclosure
- **Mechanics:** Pick an affiliate paying $100+/sale before YPP eligibility (worked example: $297 product, 35% commission scaling to 50% = ~$150/sale); always include FTC "this description contains affiliate links" disclosure; keep backup affiliates (LGYiPA5SKvw).
- **Sources:** (LGYiPA5SKvw)
- **Evidence:** MEDIUM — real affiliate terms shown; no conversion data.
- **Relation:** NEW for the creature channels (no pre-YPP revenue plan exists); bizdoc already has the sponsor plan (CONFIRM there). FTC boilerplate is a NEW compliance line for all description templates.
- **Disposition:** TEST one survival/outdoor-gear affiliate in Rexcaped V2's description; ADOPT FTC boilerplate everywhere.

### 8.5 Membership smart-pricing (Aug 17 deadline)
- **Mechanics:** From Aug 17, YouTube auto-applies per-country "smart pricing" to membership tiers for NEW non-US members unless prices are set manually (Studio → Earn → Memberships); existing members grandfathered; normal once-per-12-months-per-tier price lock waived during transition; $499.99/mo cap (description-sourced, unverified). Source: Rene Ritchie, YouTube creator liaison (CQWfqKGFoPM).
- **Sources:** (CQWfqKGFoPM)
- **Evidence:** STRONG — named YouTube source, verifiable in Studio.
- **Relation:** NEW but dormant — no channel has YPP/memberships.
- **Disposition:** FILE one line in the future monetization checklist: set tier prices manually at membership launch.

### 8.6 Facebook monetization surface
- **Mechanics:** Invite-only; experience-based trigger ≈ 5,000 followers + 60,000 minutes viewed (E_CIP98ufto); waitlist via Professional dashboard → Monetization → "express interest" (KZKFlik4M8I); photos monetize too; implied payout ~$0.08/1K views. Engagement-ranked (saves/shares), not watch-time-ranked.
- **Sources:** (E_CIP98ufto) (KZKFlik4M8I)
- **Evidence:** MEDIUM — 2 sources agree on mechanics; payouts unverified.
- **Relation:** NEW platform intel; the low RPM independently CONFIRMS the high-RPM YouTube long-form bet.
- **Disposition:** Covered by the 4.7 cross-posting test; expectations set at ~$0.08/1K.

### 8.7 Real footage beats full-AI as both competitive edge and policy armor
- **Mechanics:** "Instead of using AI images, using real images... you will have a huge competitive advantage" — said by a guru whose own case channel is AI slop (ipbnR92Elxg); the operation's composited-creature-into-real-footage technique simultaneously differentiates on quality and sidesteps the reused-content enforcement the clip-farm genre spends all its effort evading (PtO7jd8L2xs structural takeaway; the 8-video negative-archetype flood in 5.10).
- **Sources:** (ipbnR92Elxg) (PtO7jd8L2xs) + 5.10 corpus
- **Evidence:** STRONG — stated by practitioners AND structurally implied by the whole corpus's evasion behavior.
- **Relation:** CONFIRMS the layered-composite engine thesis and image-sourcing rules as the moat.
- **Disposition:** CONFIRM — do not dilute the differentiation.

---

## CROSS-CUTTING VERDICT SUMMARY

**Highest-confidence ADOPTs (free, this week):** cold-start setup bundle (7.1) before bizdoc launch; AI-disclosure decision (7.4); thumbnail-first gate (1.1); search-bar supply check (5.2); 80/20 + kill criteria + 72h rule (5.7); vertical caption grammar (4.4) + Shorts ship-gates (4.2); parasocial script lints (2.2); FTC boilerplate + appeal packet (8.4, 8.2); never-do list codification (7.7); inter-video fingerprint diff (3.9).

**Best cheap TESTs:** last-frame chaining (3.2); turnaround-sheet reference (3.3); SAM 2 layers (3.6); AVD-hack Short from owned composites (4.1); demand-gap clustering session (5.1); timestamp-conditioned prompts (3.5); AI Studio TTS + Gemini music rights-gated (6.2).

**Systemic CONFIRM:** the operation's existing stack (measured edit grammar, WhisperX paper-edit, topic scorer, viral_recreation_spec, layered composites, QA gates) is ahead of everything demonstrated in all 32 videos; the corpus's main gift is quantified thresholds, upload-practice gaps, a Shorts lane, and multi-source confirmation that variety + human layers is the demonetization moat.

**Blanket IGNOREs:** every paid tool/subscription pitch (all affiliate-driven), aged-channel purchases, multi-accounting, watermark hiding, loop-streaming, reused-content models, AI human faces, and all unverified revenue claims.
